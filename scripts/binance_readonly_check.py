#!/usr/bin/env python3
"""Read-only Binance Spot account credential check. Never submits orders or withdrawals."""
from __future__ import annotations

import hashlib
import hmac
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request


BASE_URL = "https://api.binance.com"
TIMEOUT_SECONDS = 10


def signed_query(api_secret: str, timestamp_ms: int) -> str:
    """Return a signed, read-only account query; never log the signature or secret."""
    query = urllib.parse.urlencode({"recvWindow": 5000, "timestamp": timestamp_ms})
    signature = hmac.new(api_secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
    return query + "&signature=" + signature


def validate_read_only_credentials(api_key: str, api_secret: str) -> dict:
    if not api_key or not api_secret:
        raise ValueError("Defina BINANCE_API_KEY e BINANCE_API_SECRET no ambiente.")
    query = signed_query(api_secret, int(time.time() * 1000))
    request = urllib.request.Request(
        BASE_URL + "/api/v3/account?" + query,
        headers={"X-MBX-APIKEY": api_key, "Accept": "application/json", "User-Agent": "GENESE-PAY-readonly-check/1.0"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            import json
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        # Do not expose request URL, signature, API key, or raw response to logs.
        if exc.code in (401, 403):
            raise RuntimeError("Binance recusou a autenticação. Confira chave, segredo, IP permitido e permissões somente leitura.") from None
        if exc.code == 429 or exc.code == 418:
            raise RuntimeError("Binance aplicou limite temporário de requisições; tente mais tarde.") from None
        raise RuntimeError(f"Binance respondeu HTTP {exc.code}; nenhuma ordem ou saque foi enviado.") from None
    except (urllib.error.URLError, TimeoutError, OSError):
        raise RuntimeError("Não foi possível alcançar a API Binance por HTTPS.") from None
    if not isinstance(data, dict) or "accountType" not in data or "balances" not in data:
        raise RuntimeError("Resposta da Binance inesperada; validação não confirmada.")
    # Deliberately do not print balances, account identifiers, keys, or the signed URL.
    return {
        "ok": True,
        "provider": "Binance Spot",
        "authenticated": True,
        "account_type": str(data.get("accountType", "unknown")),
        "can_trade": bool(data.get("canTrade", False)),
        "can_withdraw": bool(data.get("canWithdraw", False)),
        "withdrawals_permitted_by_this_tool": False,
        "money_moved": False,
        "balances_disclosed": False,
    }


def main() -> int:
    try:
        result = validate_read_only_credentials(
            os.environ.get("BINANCE_API_KEY", ""),
            os.environ.get("BINANCE_API_SECRET", ""),
        )
    except (ValueError, RuntimeError) as exc:
        print("FAIL: " + str(exc), file=sys.stderr)
        return 1
    for key, value in result.items():
        print(f"{key}={value}")
    print("PASS: credenciais autenticadas; este teste é somente leitura e não movimenta fundos.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
