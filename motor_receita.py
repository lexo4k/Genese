"""Motor de receita do GÊNESE PAY.

Este módulo separa atividade produtiva, conversões e dinheiro confirmado.
Não fabrica saldo, não considera clique como ganho e não inicia transferências.
Integrações pagadoras devem implementar um adaptador oficial específico e validar
a resposta do provedor antes de registrar comissão.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB = Path(os.getenv("GENESE_RECEITA_DB", "genese_receita.sqlite3"))


def _connect():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_engine() -> None:
    with _connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS revenue_events (
                provider TEXT NOT NULL,
                external_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                currency TEXT,
                amount REAL,
                status TEXT NOT NULL,
                evidence_sha256 TEXT,
                created_at TEXT NOT NULL,
                PRIMARY KEY(provider, external_id, event_type)
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS revenue_assets (
                asset_id TEXT PRIMARY KEY,
                asset_type TEXT NOT NULL,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                created_at TEXT NOT NULL
            )
        """)
        db.commit()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def source_status() -> dict[str, Any]:
    """Report only real configuration signals; never infer earnings from keys."""
    configured = {
        "affiliate_partner": bool(os.getenv("GENESE_AFFILIATE_PARTNER_ID")),
        "affiliate_api": bool(os.getenv("GENESE_AFFILIATE_API_TOKEN")),
        "publisher_account": bool(os.getenv("GENESE_PUBLISHER_ACCOUNT_ID")),
        "mercadopago_access_token": bool(os.getenv("MERCADOPAGO_ACCESS_TOKEN")),
        "mercadopago_webhook_secret": bool(
            os.getenv("MERCADOPAGO_WEBHOOK_SECRET")
            or os.getenv("GENESE_PAYMENT_WEBHOOK_SECRET")
        ),
    }
    ready = configured["affiliate_partner"] and configured["affiliate_api"]
    return {
        "ok": True,
        "engine": "genese-revenue-engine",
        "mode": "affiliate_commission",
        "source_connected": False,
        "source_ready": ready,
        "automatic_payout_enabled": False,
        "confirmed_revenue": {},
        "activity": "not_started",
        "checks": [
            {
                "key": key,
                "configured": value,
                "detail": "Configured in server environment." if value else "Missing server-side configuration."
            }
            for key, value in configured.items()
        ],
        "note": (
            "A configuração das variáveis não comprova aprovação em programa de afiliados. "
            "É necessário conectar uma rede pagadora real, publicar conteúdo/distribuição "
            "conforme suas regras e validar conversões pela API oficial da rede. "
            "Cliques, rascunhos e vendas não confirmadas não são receita."
        ),
    }


def save_content_asset(title: str, content: str, asset_type: str = "promotional_copy") -> dict[str, Any]:
    """Persist a generated content asset as a draft, never as income."""
    title = " ".join(str(title).split())[:180]
    content = str(content).strip()
    asset_type = " ".join(str(asset_type).split())[:48]
    if not title or not content:
        raise ValueError("title and content are required")
    if len(content) > 100_000:
        raise ValueError("content is too large")
    asset_id = hashlib.sha256((asset_type + "\0" + title + "\0" + content).encode()).hexdigest()[:24]
    with _connect() as db:
        db.execute(
            "INSERT INTO revenue_assets(asset_id,asset_type,title,content,status,created_at) "
            "VALUES(?,?,?,?,?,?) ON CONFLICT(asset_id) DO NOTHING",
            (asset_id, asset_type, title, content, "draft", _now()),
        )
        db.commit()
    return {"asset_id": asset_id, "status": "draft", "counts_as_revenue": False}


def record_verified_commission(
    provider: str,
    external_id: str,
    currency: str,
    amount: float,
    evidence: dict[str, Any],
    *,
    provider_verified: bool = False,
) -> dict[str, Any]:
    """Only internal trusted adapters may call this after official provider verification.

    Public HTTP endpoints must never pass provider_verified=True directly from a
    request body. The adapter must obtain and validate the provider's canonical
    conversion/payment record before calling this function.
    """
    provider = " ".join(str(provider).split())[:64].lower()
    external_id = " ".join(str(external_id).split())[:160]
    currency = str(currency).upper()
    if not provider_verified:
        raise PermissionError("Commission must be verified by an official provider adapter.")
    if not provider or not external_id or len(currency) != 3 or not currency.isalpha():
        raise ValueError("Invalid provider, external ID, or currency")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("Commission amount must be positive")
    evidence_json = json.dumps(evidence, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    evidence_hash = hashlib.sha256(evidence_json.encode()).hexdigest()
    with _connect() as db:
        cursor = db.execute(
            "INSERT INTO revenue_events(provider,external_id,event_type,currency,amount,status,evidence_sha256,created_at) "
            "VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(provider,external_id,event_type) DO NOTHING",
            (provider, external_id, "commission", currency, float(amount), "CONFIRMED", evidence_hash, _now()),
        )
        db.commit()
        inserted = cursor.rowcount == 1
    return {
        "ok": True,
        "inserted": inserted,
        "status": "CONFIRMED" if inserted else "ALREADY_RECORDED",
        "currency": currency,
        "amount": float(amount),
        "evidence_sha256": evidence_hash,
    }


def revenue_summary() -> dict[str, Any]:
    init_engine()
    with _connect() as db:
        totals = db.execute(
            "SELECT currency, ROUND(SUM(amount), 8) AS total, COUNT(*) AS events "
            "FROM revenue_events WHERE status='CONFIRMED' AND event_type='commission' "
            "GROUP BY currency ORDER BY currency"
        ).fetchall()
        assets = db.execute(
            "SELECT status, COUNT(*) AS total FROM revenue_assets GROUP BY status"
        ).fetchall()
        events = db.execute(
            "SELECT provider,external_id,currency,amount,status,created_at,evidence_sha256 "
            "FROM revenue_events WHERE status='CONFIRMED' ORDER BY created_at DESC LIMIT 100"
        ).fetchall()
    return {
        "confirmed_commission_by_currency": {
            row["currency"]: row["total"] for row in totals
        },
        "confirmed_event_count": sum(row["events"] for row in totals),
        "assets_by_status": {row["status"]: row["total"] for row in assets},
        "events": [dict(row) for row in events],
        "source": source_status(),
        "payout": {
            "destination": "Mercado Pago",
            "enabled": False,
            "status": "not_configured",
            "note": "O registro de comissão não transfere dinheiro. O repasse exige integração oficial suportada e confirmação do provedor."
        }
    }


if __name__ == "__main__":
    init_engine()
    print(json.dumps(revenue_summary(), ensure_ascii=False, indent=2))
