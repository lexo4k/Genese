"""GÊNESE PAY core: pool connectivity and an evidence-only income ledger.

A URL and transaction reference are not proof of a provider's balance. This module
stores submitted evidence as UNVERIFIED and never reports it as confirmed income.
No mining shares are submitted and no Binance transfer is initiated.
"""
from __future__ import annotations

import json
import os
import re
import socket
import sqlite3
import ssl
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DB_PATH = Path(os.environ.get("GENESE_LEDGER_DB", "genese_pay.sqlite3"))
DEFAULT_POOL_HOST = "nhmp-ssl.eu.nicehash.com"
DEFAULT_POOL_PORT = 443


@dataclass(frozen=True)
class MiningConfig:
    pool_host: str
    pool_port: int
    worker: str
    payout_address: str
    payout_network: str


def load_mining_config(env: dict[str, str] | None = None) -> MiningConfig:
    env = os.environ if env is None else env
    host = env.get("GENESE_POOL_HOST", DEFAULT_POOL_HOST).strip()
    port_text = env.get("GENESE_POOL_PORT", str(DEFAULT_POOL_PORT)).strip()
    worker = env.get("GENESE_WORKER", "").strip()
    address = env.get("BINANCE_DEPOSIT_ADDRESS", "").strip()
    network = env.get("BINANCE_DEPOSIT_NETWORK", "").strip().upper()
    if not host or "/" in host or "://" in host:
        raise ValueError("GENESE_POOL_HOST deve ser apenas um hostname.")
    try:
        port = int(port_text)
    except ValueError as exc:
        raise ValueError("GENESE_POOL_PORT deve ser um número.") from exc
    if not 1 <= port <= 65535:
        raise ValueError("GENESE_POOL_PORT fora do intervalo válido.")
    if worker and not re.fullmatch(r"[A-Za-z0-9._-]{1,64}", worker):
        raise ValueError("GENESE_WORKER aceita somente letras, números, ponto, _ e -.")
    if bool(address) != bool(network):
        raise ValueError("Informe endereço e rede de depósito juntos, ou deixe ambos vazios.")
    return MiningConfig(host, port, worker, address, network)


def probe_pool(config: MiningConfig, timeout: float = 4.0) -> dict[str, Any]:
    """Make a real TLS handshake; connection alone is not mining."""
    start = time.monotonic()
    try:
        context = ssl.create_default_context()
        with socket.create_connection((config.pool_host, config.pool_port), timeout=timeout) as raw:
            with context.wrap_socket(raw, server_hostname=config.pool_host):
                pass
        return {
            "connected": True, "host": config.pool_host, "port": config.pool_port,
            "tls_verified": True, "elapsed_ms": round((time.monotonic() - start) * 1000),
            "mining_active": False, "shares_submitted": 0,
            "note": "Handshake TLS confirmado; não comprova mineração nem ganhos.",
        }
    except (OSError, ssl.SSLError, TimeoutError) as exc:
        return {
            "connected": False, "host": config.pool_host, "port": config.pool_port,
            "tls_verified": False, "elapsed_ms": round((time.monotonic() - start) * 1000),
            "mining_active": False, "shares_submitted": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }


def initialize_ledger(db_path: str | Path = DB_PATH) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS income_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                currency TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                transaction_ref TEXT NOT NULL,
                evidence_url TEXT NOT NULL,
                verification_status TEXT NOT NULL DEFAULT 'UNVERIFIED',
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider, transaction_ref)
            )
        """)
        conn.commit()


def record_income_evidence(
    provider: str, currency: str, amount: float, transaction_ref: str,
    evidence_url: str, db_path: str | Path = DB_PATH,
) -> dict[str, Any]:
    """Store a claim for later manual/provider verification; never mark it confirmed."""
    provider, currency, transaction_ref = provider.strip(), currency.strip().upper(), transaction_ref.strip()
    parsed = urlparse(evidence_url.strip())
    if not provider or not re.fullmatch(r"[A-Z0-9]{2,12}", currency):
        raise ValueError("Provedor e código de moeda são obrigatórios.")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("O valor declarado deve ser positivo.")
    if not transaction_ref or len(transaction_ref) > 200:
        raise ValueError("Referência de transação obrigatória.")
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("A evidência deve ser uma URL HTTPS.")
    initialize_ledger(db_path)
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.execute(
                """INSERT INTO income_evidence
                   (provider, currency, amount, transaction_ref, evidence_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (provider, currency, float(amount), transaction_ref, evidence_url.strip()),
            )
            conn.commit()
            return {"recorded": True, "verification_status": "UNVERIFIED",
                    "id": cursor.lastrowid, "currency": currency, "amount_claimed": float(amount),
                    "transaction_ref": transaction_ref}
    except sqlite3.IntegrityError as exc:
        raise ValueError("Essa referência já foi registrada; duplicação recusada.") from exc


def income_summary(db_path: str | Path = DB_PATH) -> dict[str, Any]:
    """Expose evidence claims separately; confirmed income stays unknown until provider verification exists."""
    initialize_ledger(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            """SELECT currency, ROUND(SUM(amount), 12), COUNT(*)
               FROM income_evidence WHERE verification_status = 'UNVERIFIED'
               GROUP BY currency ORDER BY currency"""
        ).fetchall()
    return {
        "source": "unverified_evidence_ledger",
        "unverified_claims": [
            {"currency": currency, "amount_claimed": amount, "count": count}
            for currency, amount, count in rows
        ],
        "confirmed_income": None,
        "confirmed_external_balance": None,
        "binance_transfer_executed": False,
        "note": "Nenhuma declaração é tratada como receita confirmada; falta validação direta no provedor.",
    }


def status_json(env: dict[str, str] | None = None, timeout: float = 4.0) -> str:
    config = load_mining_config(env)
    result = {
        "service": "GENESE PAY",
        "config": {
            "pool_host": config.pool_host, "pool_port": config.pool_port,
            "worker_configured": bool(config.worker),
            "binance_destination_configured": bool(config.payout_address and config.payout_network),
            "binance_network": config.payout_network or None,
        },
        "pool_probe": probe_pool(config, timeout=timeout),
        "income": income_summary(),
        "warning": "Não há minerador executável nem integração de saldo confirmada neste módulo.",
    }
    return json.dumps(result, ensure_ascii=False, indent=2)
