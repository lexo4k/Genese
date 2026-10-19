"""Read-only Binance Spot account and deposit verification.

Never initiates withdrawals or transfers. Secrets must be supplied via environment.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import time
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.binance.com"


class BinanceAPIError(RuntimeError):
    pass


def _credentials(env: dict[str, str] | None = None) -> tuple[str, str] | None:
    env = os.environ if env is None else env
    key = env.get("BINANCE_API_KEY", "").strip()
    secret = env.get("BINANCE_API_SECRET", "").strip()
    if bool(key) != bool(secret):
        raise ValueError("Configure BINANCE_API_KEY e BINANCE_API_SECRET juntos.")
    if not key:
        return None
    return key, secret


def _signed_get(path: str, params: dict[str, Any], key: str, secret: str,
                timeout: float = 8.0) -> Any:
    query = dict(params)
    query["timestamp"] = int(time.time() * 1000)
    query["recvWindow"] = 5000
    encoded = urlencode(query)
    signature = hmac.new(secret.encode(), encoded.encode(), hashlib.sha256).hexdigest()
    url = f"{BASE_URL}{path}?{encoded}&signature={signature}"
    request = Request(url, headers={"X-MBX-APIKEY": key, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            import json
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Do not return URLs or headers, which may contain a signature or private metadata.
        detail = exc.read(1024).decode("utf-8", errors="replace")
        raise BinanceAPIError(f"Binance respondeu HTTP {exc.code}: {detail}") from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise BinanceAPIError(f"Falha de conexão com a API Binance: {type(exc).__name__}") from exc


def read_account_and_deposits(env: dict[str, str] | None = None,
                              timeout: float = 8.0) -> dict[str, Any]:
    """Read real balances and recent deposit history, or report missing credentials."""
    creds = _credentials(env)
    if creds is None:
        return {
            "ok": False,
            "status": "credentials_missing",
            "required_environment": ["BINANCE_API_KEY", "BINANCE_API_SECRET"],
            "note": "Nenhuma chamada privada foi feita. Configure uma chave Binance com permissões somente de leitura.",
        }
    key, secret = creds
    account = _signed_get("/api/v3/account", {}, key, secret, timeout)
    deposits = _signed_get("/sapi/v1/capital/deposit/hisrec", {"limit": 20}, key, secret, timeout)
    if not isinstance(account, dict) or not isinstance(account.get("balances"), list):
        raise BinanceAPIError("Resposta de saldo Binance inesperada.")
    if not isinstance(deposits, list):
        raise BinanceAPIError("Resposta de histórico de depósitos Binance inesperada.")
    balances = []
    for item in account["balances"]:
        if not isinstance(item, dict):
            continue
        try:
            free = float(item.get("free", "0"))
            locked = float(item.get("locked", "0"))
        except (TypeError, ValueError):
            continue
        if free or locked:
            balances.append({"asset": str(item.get("asset", "")), "free": free, "locked": locked})
    deposit_rows = []
    for item in deposits:
        if not isinstance(item, dict):
            continue
        deposit_rows.append({
            "coin": item.get("coin"),
            "amount": item.get("amount"),
            "status_code": item.get("status"),
            "network": item.get("network"),
            "tx_id": item.get("txId"),
            "insert_time_ms": item.get("insertTime"),
        })
    return {
        "ok": True,
        "status": "provider_confirmed_read_only",
        "account_balances": balances,
        "recent_deposits": deposit_rows,
        "withdrawals_enabled_by_this_app": False,
        "note": "Dados consultados na API privada Binance. Saldo não é receita criada pelo GÊNESE PAY; depósitos são os registrados pela Binance.",
    }
