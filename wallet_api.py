#!/usr/bin/env python3
"""GÊNESE Wallet API: carteira de registros com saldo em centavos.

IMPORTANTE: modo ledger-only. Não guarda dinheiro real, não cria saldo e não
envia/recebe Pix. Essas funções exigem integração e contrato com provedor regulado.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import sqlite3
import time
from urllib.parse import parse_qs, urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from mercadopago_provider import MercadoPagoError, create_pix_order, fetch_order, verify_webhook_signature, payment_state

ROOT = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("GENESE_DB_PATH", ROOT / "genese_wallet.sqlite3"))
HOST = os.environ.get("GENESE_HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8080"))
TOKEN_TTL = 60 * 60 * 12
PBKDF2_ITERATIONS = 310_000
MAX_BODY = 16_384


def connect_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db():
    with connect_db() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE,
            password_salt TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            expires_at INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS ledger (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            amount_cents INTEGER NOT NULL,
            kind TEXT NOT NULL CHECK(kind IN ('credit','debit')),
            status TEXT NOT NULL CHECK(status IN ('pending','confirmed','rejected')),
            reference TEXT UNIQUE,
            description TEXT NOT NULL,
            created_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS ledger_user_time ON ledger(user_id, created_at DESC);
        CREATE TABLE IF NOT EXISTS pix_charges (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            provider_order_id TEXT NOT NULL UNIQUE,
            amount_cents INTEGER NOT NULL CHECK(amount_cents > 0),
            status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected','cancelled','expired','unknown')),
            description TEXT NOT NULL,
            pix_copy_paste TEXT,
            qr_code_base64 TEXT,
            ticket_url TEXT,
            created_at INTEGER NOT NULL,
            updated_at INTEGER NOT NULL
        );
        CREATE INDEX IF NOT EXISTS pix_charges_user_time ON pix_charges(user_id, created_at DESC);
        """)


def password_digest(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)


def public_user(row):
    return {"id": row["id"], "email": row["email"], "created_at": row["created_at"]}


def wallet_summary(db, user_id):
    row = db.execute("""
        SELECT
          COALESCE(SUM(CASE WHEN status='confirmed' AND kind='credit' THEN amount_cents ELSE 0 END),0)
          - COALESCE(SUM(CASE WHEN status='confirmed' AND kind='debit' THEN amount_cents ELSE 0 END),0)
          AS cents,
          COALESCE(SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END),0) AS pending_count
        FROM ledger WHERE user_id=?
    """, (user_id,)).fetchone()
    return {
        "balance_cents": int(row["cents"]),
        "balance_brl": f"{int(row['cents']) / 100:.2f}",
        "pending_transactions": int(row["pending_count"]),
        "currency": "BRL",
        "meaning": "saldo contábil interno; não representa dinheiro custodiado nem saldo bancário",
    }


class APIHandler(BaseHTTPRequestHandler):
    server_version = "GeneseWallet/0.1"

    def log_message(self, fmt, *args):
        # Avoid logging request bodies or credentials.
        print("%s - %s" % (self.client_address[0], fmt % args))

    def send_json(self, status, payload):
        raw = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(raw)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(raw)

    def read_json(self):
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            raise ValueError("Content-Length inválido")
        if length < 1 or length > MAX_BODY:
            raise ValueError("Corpo ausente ou maior que o limite permitido")
        try:
            data = json.loads(self.rfile.read(length).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("JSON inválido")
        if not isinstance(data, dict):
            raise ValueError("O corpo deve ser um objeto JSON")
        return data

    def current_user(self, db):
        header = self.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return None
        token = header[7:].strip()
        if not token or len(token) > 200:
            return None
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        row = db.execute("""
            SELECT u.* FROM sessions s JOIN users u ON u.id=s.user_id
            WHERE s.token_hash=? AND s.expires_at>?
        """, (token_hash, int(time.time()))).fetchone()
        return row

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/" or path == "/index.html":
            try:
                raw = (ROOT / "web" / "index.html").read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(raw)))
                self.send_header("Cache-Control", "no-store")
                self.send_header("X-Content-Type-Options", "nosniff")
                self.end_headers()
                self.wfile.write(raw)
                return
            except OSError:
                return self.send_json(500, {"error": "Interface web não encontrada"})
        if path == "/health":
            return self.send_json(200, {
                "ok": True, "service": "GÊNESE Wallet API",
                "mode": "merchant-checkout-sandbox" if os.environ.get("MP_MODE", "sandbox").lower() == "sandbox" and os.environ.get("MP_ACCESS_TOKEN") else "ledger-only",
                "real_money_enabled": False,
                "pix_enabled": bool(os.environ.get("MP_ACCESS_TOKEN")) and os.environ.get("MP_MODE", "sandbox").lower() == "sandbox",
                "provider": "mercadopago" if os.environ.get("MP_ACCESS_TOKEN") and os.environ.get("MP_MODE", "sandbox").lower() == "sandbox" else None
            })
        with connect_db() as db:
            user = self.current_user(db)
            if not user:
                return self.send_json(401, {"error": "Autenticação necessária"})
            if path == "/api/me":
                return self.send_json(200, {"user": public_user(user)})
            if path == "/api/wallet":
                return self.send_json(200, {"wallet": wallet_summary(db, user["id"])})
            if path == "/api/transactions":
                rows = db.execute("""
                    SELECT id, amount_cents, kind, status, reference, description, created_at
                    FROM ledger WHERE user_id=? ORDER BY created_at DESC LIMIT 100
                """, (user["id"],)).fetchall()
                return self.send_json(200, {"transactions": [dict(row) for row in rows]})
            if path == "/api/pix/charges":
                rows = db.execute("""
                    SELECT id, provider_order_id, amount_cents, status, description,
                           pix_copy_paste, qr_code_base64, ticket_url, created_at, updated_at
                    FROM pix_charges WHERE user_id=? ORDER BY created_at DESC LIMIT 50
                """, (user["id"],)).fetchall()
                return self.send_json(200, {"charges": [dict(row) for row in rows]})
            if path.startswith("/api/pix/charges/"):
                charge_id = path.rsplit("/", 1)[-1]
                charge = db.execute("SELECT * FROM pix_charges WHERE id=? AND user_id=?", (charge_id, user["id"])).fetchone()
                if not charge:
                    return self.send_json(404, {"error": "Cobrança não encontrada"})
                try:
                    remote = fetch_order(charge["provider_order_id"])
                    status = payment_state(remote)
                    db.execute("UPDATE pix_charges SET status=?, updated_at=? WHERE id=?",
                               (status, int(time.time()), charge_id))
                    charge = db.execute("SELECT * FROM pix_charges WHERE id=?", (charge_id,)).fetchone()
                except MercadoPagoError:
                    pass
                return self.send_json(200, {"charge": dict(charge), "wallet_credit": False,
                                            "note": "Cobrança de comerciante; não representa saldo pessoal nem credita a carteira."})
        return self.send_json(404, {"error": "Rota não encontrada"})

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            data = self.read_json()
        except ValueError as exc:
            return self.send_json(400, {"error": str(exc)})

        if path == "/api/register":
            email = str(data.get("email", "")).strip().lower()
            password = data.get("password", "")
            if len(email) > 254 or "@" not in email or email.startswith("@") or email.endswith("@"):
                return self.send_json(400, {"error": "Informe um e-mail válido"})
            if not isinstance(password, str) or len(password) < 12 or len(password) > 256:
                return self.send_json(400, {"error": "A senha deve ter entre 12 e 256 caracteres"})
            salt = secrets.token_bytes(16)
            user_id = secrets.token_urlsafe(18)
            try:
                with connect_db() as db:
                    db.execute("INSERT INTO users VALUES (?,?,?,?,?)", (
                        user_id, email, salt.hex(), password_digest(password, salt).hex(), int(time.time())
                    ))
            except sqlite3.IntegrityError:
                return self.send_json(409, {"error": "Já existe uma conta com esse e-mail"})
            return self.send_json(201, {
                "user": {"id": user_id, "email": email},
                "message": "Conta criada. Nenhum dinheiro foi depositado.",
                "wallet_mode": "ledger-only"
            })

        if path == "/api/login":
            email = str(data.get("email", "")).strip().lower()
            password = data.get("password", "")
            if not isinstance(password, str):
                return self.send_json(400, {"error": "Credenciais inválidas"})
            with connect_db() as db:
                user = db.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
                if not user:
                    # Similar-cost work helps reduce simple account enumeration timing.
                    password_digest(password[:256], b"genese-fixed-salt")
                    return self.send_json(401, {"error": "E-mail ou senha incorretos"})
                expected = bytes.fromhex(user["password_hash"])
                actual = password_digest(password[:256], bytes.fromhex(user["password_salt"]))
                if not hmac.compare_digest(expected, actual):
                    return self.send_json(401, {"error": "E-mail ou senha incorretos"})
                token = secrets.token_urlsafe(32)
                db.execute("INSERT INTO sessions VALUES (?,?,?)", (
                    hashlib.sha256(token.encode()).hexdigest(), user["id"], int(time.time()) + TOKEN_TTL
                ))
                return self.send_json(200, {
                    "token": token, "token_type": "Bearer", "expires_in": TOKEN_TTL,
                    "user": public_user(user),
                    "warning": "Carteira contábil apenas; pagamentos reais não estão conectados."
                })

        if path == "/api/webhooks/mercadopago":
            signature = self.headers.get("x-signature", "")
            request_id = self.headers.get("x-request-id", "")
            query = parse_qs(urlparse(self.path).query)
            resource_id = (query.get("data.id") or query.get("id") or [""])[0]
            if not verify_webhook_signature(signature, request_id, resource_id,
                                            os.environ.get("MP_WEBHOOK_SECRET", "")):
                return self.send_json(401, {"error": "Assinatura de webhook inválida"})
            if str(data.get("type", "")).lower() != "order" and str(data.get("action", "")).lower().startswith("order.") is False:
                return self.send_json(200, {"ok": True, "ignored": True})
            order_id = str((data.get("data") or {}).get("id") or resource_id)
            if not order_id:
                return self.send_json(400, {"error": "ID de ordem ausente"})
            try:
                remote = fetch_order(order_id)
                status = payment_state(remote)
                with connect_db() as db:
                    db.execute("UPDATE pix_charges SET status=?, updated_at=? WHERE provider_order_id=?",
                               (status, int(time.time()), order_id))
                return self.send_json(200, {"ok": True, "status": status})
            except MercadoPagoError:
                return self.send_json(502, {"error": "Não foi possível consultar a ordem no provedor"})

        if path == "/api/pix/charge":
            with connect_db() as db:
                user = self.current_user(db)
                if not user:
                    return self.send_json(401, {"error": "Autenticação necessária"})
                if os.environ.get("MP_MODE", "sandbox").lower() != "sandbox":
                    return self.send_json(503, {"error": "Produção desabilitada nesta versão",
                        "detail": "Somente sandbox está habilitado até revisão de segurança e autorização do titular da conta de comerciante."})
                if not os.environ.get("MP_ACCESS_TOKEN"):
                    return self.send_json(503, {"error": "Provedor não configurado",
                        "detail": "Defina MP_ACCESS_TOKEN como secret no servidor e mantenha MP_MODE=sandbox."})
                amount = data.get("amount_cents")
                description = str(data.get("description", "Cobrança GÊNESE")).strip()[:120]
                if isinstance(amount, bool) or not isinstance(amount, int) or amount < 100 or amount > 1000000:
                    return self.send_json(400, {"error": "amount_cents deve ser um inteiro entre 100 e 1000000 (R$ 1 a R$ 10.000)."})
                charge_id = secrets.token_urlsafe(18)
                try:
                    remote = create_pix_order(amount_cents=amount, email=user["email"],
                                              external_reference=charge_id, description=description)
                except MercadoPagoError as exc:
                    return self.send_json(502, {"error": "O provedor recusou ou não concluiu a cobrança", "detail": str(exc)[:300]})
                payments = ((remote.get("transactions") or {}).get("payments") or [])
                payment = payments[0] if payments else {}
                method = payment.get("payment_method") or {}
                status = payment_state(remote)
                db.execute("""INSERT INTO pix_charges
                    (id,user_id,provider_order_id,amount_cents,status,description,pix_copy_paste,qr_code_base64,ticket_url,created_at,updated_at)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                    (charge_id, user["id"], str(remote.get("id", "")), amount, status, description,
                     method.get("qr_code"), method.get("qr_code_base64"), method.get("ticket_url"),
                     int(time.time()), int(time.time())))
                return self.send_json(201, {"charge": {
                    "id": charge_id, "provider_order_id": remote.get("id"), "amount_cents": amount,
                    "status": status, "description": description, "pix_copy_paste": method.get("qr_code"),
                    "qr_code_base64": method.get("qr_code_base64"), "ticket_url": method.get("ticket_url")
                }, "wallet_credit": False,
                    "note": "Cobrança Pix de comerciante em sandbox. Não é transferência entre usuários nem saldo de carteira."})

        if path == "/api/pix/transfer":
            return self.send_json(503, {
                "error": "Transferências Pix desabilitadas",
                "detail": "Este adaptador Mercado Pago é para cobranças de comerciante. Transferências de carteira exigem produto, autorização e controles separados."
            })

        if path == "/api/logout":
            header = self.headers.get("Authorization", "")
            if not header.startswith("Bearer "):
                return self.send_json(401, {"error": "Autenticação necessária"})
            token_hash = hashlib.sha256(header[7:].strip().encode()).hexdigest()
            with connect_db() as db:
                db.execute("DELETE FROM sessions WHERE token_hash=?", (token_hash,))
            return self.send_json(200, {"ok": True, "message": "Sessão encerrada"})

        return self.send_json(404, {"error": "Rota não encontrada"})

    def do_PUT(self):
        return self.send_json(405, {"error": "Método não permitido"})

    def do_DELETE(self):
        return self.send_json(405, {"error": "Método não permitido"})


def main():
    init_db()
    server = ThreadingHTTPServer((HOST, PORT), APIHandler)
    print(f"GÊNESE Wallet API ouvindo em http://{HOST}:{PORT}")
    print("Modo ledger-only: dinheiro real e Pix estão DESATIVADOS.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
