"""GÊNESE Pay ledger: internal transfers with an auditable, non-minting ledger.

This module does not connect to Pix or create money. External credits may only be
recorded after a trusted provider integration has independently confirmed a
settled payment. Internal units are not BRL and are not redeemable by default.
"""
from __future__ import annotations

import os
import sqlite3
import uuid
from pathlib import Path
from typing import Any

DB = Path(os.getenv("GENESE_LEDGER_DB", "genese_ledger.sqlite3"))


def _connect() -> sqlite3.Connection:
    DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB, timeout=10, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 10000")
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            label TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE TABLE IF NOT EXISTS transfers (
            transfer_id TEXT PRIMARY KEY,
            idempotency_key TEXT NOT NULL UNIQUE,
            source_account TEXT NOT NULL REFERENCES accounts(account_id),
            destination_account TEXT NOT NULL REFERENCES accounts(account_id),
            amount_units INTEGER NOT NULL CHECK(amount_units > 0),
            memo TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            CHECK(source_account <> destination_account)
        );
        CREATE TABLE IF NOT EXISTS ledger_entries (
            entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id TEXT NOT NULL REFERENCES accounts(account_id),
            event_type TEXT NOT NULL CHECK(event_type IN ('provider_credit','transfer_debit','transfer_credit')),
            amount_units INTEGER NOT NULL CHECK(amount_units <> 0),
            event_ref TEXT NOT NULL,
            provider TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            UNIQUE(event_type, event_ref, account_id)
        );
        CREATE INDEX IF NOT EXISTS ledger_entries_account_idx ON ledger_entries(account_id, entry_id);
        """)


def create_account(label: str, account_id: str | None = None) -> dict[str, str]:
    label = str(label).strip()
    if not label or len(label) > 100:
        raise ValueError("O nome da conta deve ter entre 1 e 100 caracteres.")
    account_id = account_id or ("gen_" + uuid.uuid4().hex[:16])
    with _connect() as conn:
        conn.execute("INSERT INTO accounts(account_id,label) VALUES(?,?)", (account_id, label))
    return {"account_id": account_id, "label": label}


def _account_exists(conn: sqlite3.Connection, account_id: str) -> bool:
    return conn.execute("SELECT 1 FROM accounts WHERE account_id=?", (account_id,)).fetchone() is not None


def balance(account_id: str) -> int:
    with _connect() as conn:
        if not _account_exists(conn, account_id):
            raise KeyError("Conta não encontrada.")
        row = conn.execute("SELECT COALESCE(SUM(amount_units),0) AS total FROM ledger_entries WHERE account_id=?", (account_id,)).fetchone()
        return int(row["total"])


def credit_from_verified_provider(
    account_id: str,
    amount_units: int,
    *,
    provider: str,
    external_reference: str,
    provider_status: str,
) -> dict[str, Any]:
    """Record a credit only when a trusted integration supplies a settled status.

    Calling this function is not itself proof of settlement. Production code must
    call it only after authenticating the provider and fetching the canonical
    transaction from that provider's API.
    """
    if isinstance(amount_units, bool) or not isinstance(amount_units, int) or amount_units <= 0:
        raise ValueError("O valor deve ser um inteiro positivo na unidade interna.")
    provider = str(provider).strip()
    external_reference = str(external_reference).strip()
    if not provider or not external_reference:
        raise ValueError("Provedor e referência externa são obrigatórios.")
    if str(provider_status).lower() not in {"approved", "paid", "settled"}:
        raise PermissionError("Crédito recusado: o provedor não confirmou liquidação.")
    event_ref = provider + ":" + external_reference
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if not _account_exists(conn, account_id):
            conn.rollback()
            raise KeyError("Conta não encontrada.")
        try:
            conn.execute(
                "INSERT INTO ledger_entries(account_id,event_type,amount_units,event_ref,provider) VALUES(?,?,?,?,?)",
                (account_id, "provider_credit", amount_units, event_ref, provider),
            )
        except sqlite3.IntegrityError:
            conn.rollback()
            return {"inserted": False, "reason": "duplicate_external_reference", "balance_units": balance(account_id)}
        conn.commit()
    return {"inserted": True, "balance_units": balance(account_id), "event_ref": event_ref}


def transfer(
    source_account: str,
    destination_account: str,
    amount_units: int,
    *,
    idempotency_key: str,
    memo: str = "",
) -> dict[str, Any]:
    """Move existing internal units atomically; cannot create value from nothing."""
    if isinstance(amount_units, bool) or not isinstance(amount_units, int) or amount_units <= 0:
        raise ValueError("O valor deve ser um inteiro positivo.")
    if source_account == destination_account:
        raise ValueError("A origem e o destino devem ser diferentes.")
    key = str(idempotency_key).strip()
    if not key or len(key) > 200:
        raise ValueError("Chave de idempotência obrigatória (até 200 caracteres).")
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        if not _account_exists(conn, source_account) or not _account_exists(conn, destination_account):
            conn.rollback()
            raise KeyError("Conta de origem ou destino não encontrada.")
        prior = conn.execute("SELECT * FROM transfers WHERE idempotency_key=?", (key,)).fetchone()
        if prior:
            conn.rollback()
            if prior["source_account"] != source_account or prior["destination_account"] != destination_account or prior["amount_units"] != amount_units:
                raise ValueError("A chave de idempotência já foi usada com outros dados.")
            return {"inserted": False, "transfer_id": prior["transfer_id"], "status": "already_processed"}
        row = conn.execute("SELECT COALESCE(SUM(amount_units),0) AS total FROM ledger_entries WHERE account_id=?", (source_account,)).fetchone()
        current = int(row["total"])
        if current < amount_units:
            conn.rollback()
            raise ValueError("Saldo insuficiente. Nenhuma transferência foi registrada.")
        transfer_id = "tr_" + uuid.uuid4().hex
        conn.execute(
            "INSERT INTO transfers(transfer_id,idempotency_key,source_account,destination_account,amount_units,memo) VALUES(?,?,?,?,?,?)",
            (transfer_id, key, source_account, destination_account, amount_units, str(memo)[:240]),
        )
        conn.execute(
            "INSERT INTO ledger_entries(account_id,event_type,amount_units,event_ref) VALUES(?,?,?,?)",
            (source_account, "transfer_debit", -amount_units, transfer_id),
        )
        conn.execute(
            "INSERT INTO ledger_entries(account_id,event_type,amount_units,event_ref) VALUES(?,?,?,?)",
            (destination_account, "transfer_credit", amount_units, transfer_id),
        )
        conn.commit()
    return {
        "inserted": True,
        "transfer_id": transfer_id,
        "status": "internal_transfer_recorded",
        "source_balance_units": balance(source_account),
        "destination_balance_units": balance(destination_account),
        "external_pix_sent": False,
    }


def history(account_id: str, limit: int = 50) -> list[dict[str, Any]]:
    if not 1 <= int(limit) <= 200:
        raise ValueError("O limite deve ficar entre 1 e 200.")
    with _connect() as conn:
        if not _account_exists(conn, account_id):
            raise KeyError("Conta não encontrada.")
        rows = conn.execute(
            "SELECT entry_id,event_type,amount_units,event_ref,provider,created_at FROM ledger_entries WHERE account_id=? ORDER BY entry_id DESC LIMIT ?",
            (account_id, int(limit)),
        ).fetchall()
    return [dict(row) for row in rows]
