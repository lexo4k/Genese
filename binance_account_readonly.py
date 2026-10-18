#!/usr/bin/env python3
"""Leitura opcional e somente leitura da conta Binance Spot.

Requer uma API key criada com permissão de leitura de dados, sem trading e sem saque.
Não implementa ordens, depósitos, saques ou transferências. Nunca registre segredos.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import sys
import time
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api.binance.com"
USER_AGENT = "GENESE-PAY-ReadOnly/1.0"


class BinanceAccountError(RuntimeError):
    """Falha segura ao consultar a conta privada Binance."""


def _request_json(url: str, api_key: str, timeout: float = 8.0) -> Any:
    req = Request(url, headers={
        "X-MBX-APIKEY": api_key,
        "User-Agent": USER_AGENT,
        "Accept": "application/json",
    })
    try:
        with urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                raise BinanceAccountError(f"Binance respondeu HTTP {response.status}")
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        # Do not expose response bodies, which may contain account/request details.
        raise BinanceAccountError(f"Binance recusou a consulta (HTTP {exc.code}). Confira chave, permissões e horário.") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise BinanceAccountError(f"Falha segura na consulta Binance: {type(exc).__name__}") from exc


def get_spot_balances(
    api_key: str | None = None,
    api_secret: str | None = None,
    *,
    request_json: Callable[[str, str], Any] | None = None,
    timestamp_ms: int | None = None,
) -> dict[str, Any]:
    key = api_key if api_key is not None else os.environ.get("BINANCE_API_KEY", "")
    secret = api_secret if api_secret is not None else os.environ.get("BINANCE_API_SECRET", "")
    if not key.strip() or not secret.strip():
        raise BinanceAccountError("Configure BINANCE_API_KEY e BINANCE_API_SECRET como variáveis de ambiente; nunca as publique.")
    timestamp = int(timestamp_ms if timestamp_ms is not None else time.time() * 1000)
    params = {"recvWindow": 5000, "timestamp": timestamp}
    query = urlencode(params)
    signature = hmac.new(secret.encode("utf-8"), query.encode("utf-8"), hashlib.sha256).hexdigest()
    url = f"{BASE_URL}/api/v3/account?{query}&signature={signature}"
    getter = request_json or (lambda target, key_value: _request_json(target, key_value))
    payload = getter(url, key)
    if not isinstance(payload, dict) or not isinstance(payload.get("balances"), list):
        raise BinanceAccountError("Resposta de conta inesperada; nenhum saldo foi contabilizado.")
    balances: list[dict[str, str]] = []
    for row in payload["balances"]:
        if not isinstance(row, dict) or not isinstance(row.get("asset"), str):
            continue
        try:
            free = float(row.get("free", "0"))
            locked = float(row.get("locked", "0"))
        except (TypeError, ValueError):
            continue
        if free < 0 or locked < 0:
            continue
        if free > 0 or locked > 0:
            balances.append({"asset": row["asset"], "free": format(free, ".16g"), "locked": format(locked, ".16g")})
    return {
        "fonte": "Binance Spot API privada, endpoint somente leitura",
        "consulta_confirmada": True,
        "consultado_em_ms": timestamp,
        "ativos_com_saldo": balances,
        "receita_confirmada": False,
        "transferencia_executada": False,
        "aviso": "Saldo da conta não significa renda gerada pelo GÊNESE PAY. Esta ferramenta não movimenta fundos.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Consultar saldos Spot Binance (somente leitura)")
    parser.add_argument("--show-zero", action="store_true", help="reservado; por padrão só exibe ativos com saldo")
    parser.parse_args()
    try:
        print(json.dumps(get_spot_balances(), ensure_ascii=False, indent=2))
        return 0
    except BinanceAccountError as exc:
        print(json.dumps({"ok": False, "erro": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
