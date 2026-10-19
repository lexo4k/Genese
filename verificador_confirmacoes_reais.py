#!/usr/bin/env python3
"""Verificações externas para o GÊNESE PAY.

CNPJ: consulta a BrasilAPI, que replica dados públicos cadastrais; não substitui
certidão oficial da Receita Federal.
Binance: consulta assinada, somente leitura, ao histórico de depósitos Spot.
Só depósitos Binance com status 1 são classificados como creditados com sucesso.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import os
import re
import time
from decimal import Decimal, InvalidOperation
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BRASILAPI_BASE = "https://brasilapi.com.br/api/cnpj/v1"
BINANCE_BASE = "https://api.binance.com"
USER_AGENT = "GENESE-PAY-ExternalVerifier/1.0"


class VerificationError(RuntimeError):
    """Erro seguro de consulta/verificação externa."""


def normalize_cnpj(value: str) -> str:
    digits = re.sub(r"\D", "", value or "")
    if len(digits) != 14 or len(set(digits)) == 1:
        raise ValueError("Informe um CNPJ válido com 14 dígitos.")
    def digit(base: str, weights: list[int]) -> str:
        total = sum(int(n) * w for n, w in zip(base, weights))
        rem = total % 11
        return str(0 if rem < 2 else 11 - rem)
    first = digit(digits[:12], [5,4,3,2,9,8,7,6,5,4,3,2])
    second = digit(digits[:12] + first, [6,5,4,3,2,9,8,7,6,5,4,3,2])
    if digits[-2:] != first + second:
        raise ValueError("Os dígitos verificadores do CNPJ não conferem.")
    return digits


def _get_json(url: str, headers: dict[str, str] | None = None, timeout: float = 10) -> Any:
    req = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json", **(headers or {})})
    try:
        with urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                raise VerificationError(f"Fonte externa respondeu HTTP {response.status}.")
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise VerificationError(f"Fonte externa recusou a consulta (HTTP {exc.code}).") from exc
    except (URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise VerificationError(f"Consulta externa falhou: {type(exc).__name__}.") from exc


def verify_cnpj(cnpj: str, *, get_json: Callable[..., Any] | None = None) -> dict[str, Any]:
    digits = normalize_cnpj(cnpj)
    getter = get_json or _get_json
    payload = getter(f"{BRASILAPI_BASE}/{digits}")
    if not isinstance(payload, dict):
        raise VerificationError("Resposta cadastral inesperada.")
    legal_name = payload.get("razao_social")
    status_text = str(payload.get("descricao_situacao_cadastral") or "").strip().upper()
    status_code = str(payload.get("descricao_situacao_cadastral") or payload.get("situacao_cadastral") or "").strip()
    active = status_text == "ATIVA" or status_code == "2"
    if not legal_name:
        raise VerificationError("A fonte não retornou razão social; não foi possível confirmar o cadastro.")
    return {
        "consulta_externa_concluida": True,
        "cnpj": digits,
        "razao_social": str(legal_name),
        "situacao_cadastral": status_text or status_code or "NAO_INFORMADA",
        "registro_aparenta_ativo": active,
        "status_confirmacao": "cadastro_publico_ativo" if active else "cadastro_encontrado_mas_nao_ativo",
        "fonte": "BrasilAPI (espelho de dados públicos cadastrais)",
        "fonte_url": f"{BRASILAPI_BASE}/{digits}",
        "consultado_em_epoch": int(time.time()),
        "limite": "Confirmação preliminar em base pública de terceiros; para prova jurídica, valide o comprovante oficial da Receita Federal.",
    }


def get_binance_deposits(
    api_key: str | None = None,
    api_secret: str | None = None,
    *,
    get_json: Callable[..., Any] | None = None,
    timestamp_ms: int | None = None,
    coin: str | None = None,
    start_time_ms: int | None = None,
    end_time_ms: int | None = None,
) -> dict[str, Any]:
    key = api_key if api_key is not None else os.environ.get("BINANCE_API_KEY", "")
    secret = api_secret if api_secret is not None else os.environ.get("BINANCE_API_SECRET", "")
    if not key.strip() or not secret.strip():
        raise VerificationError("Configure BINANCE_API_KEY e BINANCE_API_SECRET em variáveis de ambiente; nunca publique as chaves.")
    params: dict[str, Any] = {"timestamp": int(timestamp_ms if timestamp_ms is not None else time.time() * 1000), "recvWindow": 5000}
    if coin:
        if not re.fullmatch(r"[A-Z0-9]{2,20}", coin.upper()):
            raise ValueError("Símbolo de ativo inválido.")
        params["coin"] = coin.upper()
    if start_time_ms is not None:
        params["startTime"] = int(start_time_ms)
    if end_time_ms is not None:
        params["endTime"] = int(end_time_ms)
    query = urlencode(params)
    signature = hmac.new(secret.encode(), query.encode(), hashlib.sha256).hexdigest()
    url = f"{BINANCE_BASE}/sapi/v1/capital/deposit/hisrec?{query}&signature={signature}"
    getter = get_json or (lambda target, headers=None: _get_json(target, headers))
    payload = getter(url, {"X-MBX-APIKEY": key})
    if not isinstance(payload, list):
        raise VerificationError("Histórico de depósitos retornou estrutura inesperada; nada foi confirmado.")
    deposits = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        try:
            amount = Decimal(str(item.get("amount", "0")))
            status = int(item.get("status", -1))
        except (InvalidOperation, TypeError, ValueError):
            continue
        if amount <= 0:
            continue
        # Binance deposit history status 1 means successful. Other states are never counted.
        successful = status == 1
        deposits.append({
            "coin": str(item.get("coin", "")),
            "amount": format(amount, "f"),
            "network": str(item.get("network", "")),
            "txId": str(item.get("txId", "")),
            "insertTime": item.get("insertTime"),
            "status_code": status,
            "creditado_com_sucesso": successful,
            "status": "creditado_confirmado" if successful else "nao_confirmado",
        })
    confirmed = [d for d in deposits if d["creditado_com_sucesso"]]
    return {
        "consulta_externa_concluida": True,
        "fonte": "Binance Spot API oficial, histórico privado de depósitos, somente leitura",
        "consultado_em_epoch": int(time.time()),
        "depositos_retornados": len(deposits),
        "depositos_confirmados": len(confirmed),
        "depositos": deposits,
        "observacao": "Depósito confirmado prova crédito na Binance, não prova que foi receita gerada pelo GÊNESE PAY.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica cadastro CNPJ e depósitos recebidos na Binance")
    sub = parser.add_subparsers(dest="command", required=True)
    cnpj_parser = sub.add_parser("cnpj")
    cnpj_parser.add_argument("cnpj")
    deposit_parser = sub.add_parser("binance-deposits")
    deposit_parser.add_argument("--coin")
    deposit_parser.add_argument("--start-time-ms", type=int)
    deposit_parser.add_argument("--end-time-ms", type=int)
    args = parser.parse_args()
    try:
        if args.command == "cnpj":
            result = verify_cnpj(args.cnpj)
        else:
            result = get_binance_deposits(coin=args.coin, start_time_ms=args.start_time_ms, end_time_ms=args.end_time_ms)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, VerificationError) as exc:
        print(json.dumps({"ok": False, "erro": str(exc)}, ensure_ascii=False))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
