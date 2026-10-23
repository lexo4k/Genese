"""Diagnóstico real da conta Mercado Pago para o GÊNESE PAY.

Este comando verifica a credencial contra a API oficial, sem expor o token.
Não cria saldo, cobrança ou transferência. A API padrão de pagamentos não
autoriza presumir que uma conta possa fazer repasses automáticos.
Uso: MERCADOPAGO_ACCESS_TOKEN=... python teste_repasse_mp.py
"""
from __future__ import annotations

import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


API_BASE = "https://api.mercadopago.com"


def check_account(token: str | None = None, timeout: int = 12) -> dict:
    token = (token if token is not None else os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")).strip()
    if not token:
        return {
            "ok": False,
            "stage": "configuration",
            "status": "blocked_missing_token",
            "real_transfer_attempted": False,
            "message": "MERCADOPAGO_ACCESS_TOKEN não está configurado no ambiente do servidor.",
        }

    request = Request(
        API_BASE + "/users/me",
        headers={"Authorization": "Bearer " + token, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read(500_000).decode("utf-8"))
        return {
            "ok": True,
            "stage": "account_authentication",
            "status": "credential_valid",
            "user_id": payload.get("id"),
            "site_id": payload.get("site_id"),
            "nickname": payload.get("nickname"),
            "real_transfer_attempted": False,
            "message": (
                "A API autenticou a conta. Isso não confirma saldo disponível nem "
                "permissão para transferir dinheiro; nenhum valor foi movimentado."
            ),
        }
    except HTTPError as exc:
        # Do not return provider response bodies, which could contain account details.
        status = "invalid_or_rejected_credential" if exc.code in (401, 403) else "provider_http_error"
        return {
            "ok": False,
            "stage": "account_authentication",
            "status": status,
            "http_status": exc.code,
            "real_transfer_attempted": False,
            "message": "Mercado Pago recusou ou não concluiu a consulta de conta.",
        }
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return {
            "ok": False,
            "stage": "account_authentication",
            "status": "connection_or_response_error",
            "error_type": type(exc).__name__,
            "real_transfer_attempted": False,
            "message": "Não foi possível validar a conta pela API neste momento.",
        }


def main() -> int:
    result = check_account()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
