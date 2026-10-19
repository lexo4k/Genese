#!/usr/bin/env python3
"""Consulta dados públicos de mercado da Binance Spot.

Sem API key, login, trading, depósito, saque ou acesso a saldos privados.
Os preços retornados são cotações de mercado, não receita nem saldo do GÊNESE.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "https://api.binance.com"
SYMBOL_RE = re.compile(r"^[A-Z0-9]{5,20}$")
USER_AGENT = "GENESE-Public-Market-Reader/1.0"


class BinancePublicError(RuntimeError):
    """Erro de consulta a endpoint público da Binance."""


def _get_json(url: str, timeout: float = 8.0) -> Any:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    try:
        with urlopen(request, timeout=timeout) as response:
            if response.status != 200:
                raise BinancePublicError(f"HTTP inesperado: {response.status}")
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise BinancePublicError(f"Binance respondeu HTTP {exc.code}") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise BinancePublicError(f"Falha consultando endpoint público: {exc}") from exc


def get_price(symbol: str, fetch_json: Callable[[str], Any] | None = None) -> dict[str, Any]:
    symbol = symbol.strip().upper()
    if not SYMBOL_RE.fullmatch(symbol):
        raise ValueError("Símbolo inválido. Use letras/números, por exemplo BTCUSDT.")
    getter = fetch_json or _get_json
    payload = getter(f"{BASE_URL}/api/v3/ticker/price?symbol={symbol}")
    if not isinstance(payload, dict):
        raise BinancePublicError("Resposta pública inesperada.")
    if payload.get("symbol") != symbol or "price" not in payload:
        raise BinancePublicError("A Binance não retornou o símbolo/preço esperado.")
    try:
        price = float(payload["price"])
    except (TypeError, ValueError) as exc:
        raise BinancePublicError("Preço retornado não é numérico.") from exc
    if price <= 0:
        raise BinancePublicError("Preço retornado fora do intervalo esperado.")
    return {
        "fonte": "Binance Spot API pública",
        "symbol": symbol,
        "price": format(price, ".16g"),
        "unidade": f"por {symbol[:-4] if symbol.endswith('USDT') else symbol}",
        "cotacao_em_tempo_de_consulta": True,
        "saldo_confirmado": False,
        "receita_confirmada": False,
        "transferencia_executada": False,
        "aviso": "Cotação de mercado não é saldo, lucro garantido ou pagamento recebido.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Consultar cotação pública Binance Spot")
    parser.add_argument("--symbol", default="BTCUSDT", help="par de mercado, padrão BTCUSDT")
    args = parser.parse_args(argv)
    try:
        print(json.dumps(get_price(args.symbol), ensure_ascii=False, indent=2))
        return 0
    except (ValueError, BinancePublicError) as exc:
        print(json.dumps({"ok": False, "erro": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
