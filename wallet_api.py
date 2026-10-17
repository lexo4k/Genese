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
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

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
        if path == "/health":
            return self.send_json(200, {
                "ok": True, "service": "GÊNESE Wallet API",
                "mode": "ledger-only", "real_money_enabled": False,
                "pix_enabled": False
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

        if path in ("/api/pix/charge", "/api/pix/transfer"):
            return self.send_json(503, {
                "error": "Pix não habilitado",
                "detail": "Nenhum provedor financeiro foi configurado. Esta API não envia Pix nem confirma recebimentos.",
                "required": [
                    "contrato/conta de comerciante com provedor compatível",
                    "credenciais privadas armazenadas como secrets no servidor",
                    "webhook autenticado e validação de assinatura",
                    "testes no sandbox do provedor antes de produção"
                ]
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
