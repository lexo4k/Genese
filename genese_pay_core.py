"""GÊNESE PAY core: auditable income ledger and mining readiness checks.

This module never fabricates earnings. A payout is recorded only when an external
provider supplies a transaction reference, currency, positive amount, and evidence
URL. It does not sign into Binance or initiate transfers.
"""
from __future__ import annotations

import json
import os
import re
import socket
import sqlite3
import ssl
import time
from dataclasses import asdict, dataclass
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
    """Load configuration without inventing wallet addresses or credentials."""
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
    """Perform a real TLS TCP handshake to the configured pool; this is NOT mining."""
    start = time.monotonic()
    try:
        context = ssl.create_default_context()
        with socket.create_connection((config.pool_host, config.pool_port), timeout=timeout) as raw:
            with context.wrap_socket(raw, server_hostname=config.pool_host):
                pass
        return {
            "connected": True,
            "host": config.pool_host,
            "port": config.pool_port,
            "tls_verified": True,
            "elapsed_ms": round((time.monotonic() - start) * 1000),
            "mining_active": False,
            "shares_submitted": 0,
            "note": "Conexão TLS confirmada; isso não comprova mineração nem ganhos.",
        }
    except (OSError, ssl.SSLError, TimeoutError) as exc:
        return {
            "connected": False,
            "host": config.pool_host,
            "port": config.pool_port,
            "tls_verified": False,
            "elapsed_ms": round((time.monotonic() - start) * 1000),
            "mining_active": False,
            "shares_submitted": 0,
            "error": f"{type(exc).__name__}: {exc}",
        }


def initialize_ledger(db_path: str | Path = DB_PATH) -> None:
    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS verified_income (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider TEXT NOT NULL,
                currency TEXT NOT NULL,
                amount REAL NOT NULL CHECK(amount > 0),
                transaction_ref TEXT NOT NULL,
                evidence_url TEXT NOT NULL,
                recorded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(provider, transaction_ref)
            )
        """)
        conn.commit()


def record_verified_income(
    provider: str,
    currency: str,
    amount: float,
    transaction_ref: str,
    evidence_url: str,
    db_path: str | Path = DB_PATH,
) -> dict[str, Any]:
    """Record a payout with an external transaction reference; reject unverified claims."""
    provider = provider.strip()
    currency = currency.strip().upper()
    transaction_ref = transaction_ref.strip()
    parsed = urlparse(evidence_url.strip())
    if not provider or not re.fullmatch(r"[A-Z0-9]{2,12}", currency):
        raise ValueError("Provedor e código de moeda são obrigatórios.")
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("O valor comprovado deve ser positivo.")
    if not transaction_ref or len(transaction_ref) > 200:
        raise ValueError("Referência de transação obrigatória.")
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError("A evidência deve ser uma URL HTTPS.")
    initialize_ledger(db_path)
    try:
        with sqlite3.connect(str(db_path)) as conn:
            cursor = conn.execute(
                """INSERT INTO verified_income
                   (provider, currency, amount, transaction_ref, evidence_url)
                   VALUES (?, ?, ?, ?, ?)""",
                (provider, currency, float(amount), transaction_ref, evidence_url.strip()),
            )
            conn.commit()
            return {"recorded": True, "id": cursor.lastrowid, "currency": currency,
                    "amount": float(amount), "transaction_ref": transaction_ref}
    except sqlite3.IntegrityError as exc:
        raise ValueError("Essa transação já foi registrada; saldo não foi duplicado.") from exc


def income_summary(db_path: str | Path = DB_PATH) -> dict[str, Any]:
    """Return totals grouped by currency; never convert unlike currencies into one total."""
    initialize_ledger(db_path)
    with sqlite3.connect(str(db_path)) as conn:
        rows = conn.execute(
            """SELECT currency, ROUND(SUM(amount), 12), COUNT(*)
               FROM verified_income GROUP BY currency ORDER BY currency"""
        ).fetchall()
    return {
        "source": "local_ledger_of_verified_external_transactions",
        "totals": [
            {"currency": currency, "confirmed_amount": amount, "transaction_count": count}
            for currency, amount, count in rows
        ],
        "binance_transfer_executed": False,
        "note": "Registro local não comprova saldo atual na Binance nem inicia transferência.",
    }


def status_json(env: dict[str, str] | None = None, timeout: float = 4.0) -> str:
    config = load_mining_config(env)
    result = {
        "service": "GENESE PAY",
        "config": {
            "pool_host": config.pool_host,
            "pool_port": config.pool_port,
            "worker_configured": bool(config.worker),
            "binance_destination_configured": bool(config.payout_address and config.payout_network),
            "binance_network": config.payout_network or None,
        },
        "pool_probe": probe_pool(config, timeout=timeout),
        "income": income_summary(),
        "warning": "Nenhum saldo é estimado; conectividade não equivale a mineração.",
    }
    return json.dumps(result, ensure_ascii=False, indent=2)
