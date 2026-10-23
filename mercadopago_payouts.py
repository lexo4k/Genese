"""Mercado Pago readiness check for GÊNESE PAY.

This module NEVER sends money. It verifies whether a server-side access token
can authenticate with Mercado Pago and reports that payout permission must be
confirmed separately in the account/provider contract.

Keep MERCADOPAGO_ACCESS_TOKEN in the hosting provider's encrypted environment
variables. Never commit the token or put it in browser JavaScript.
"""
from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

API_BASE = "https://api.mercadopago.com"


def check_mercadopago_connection(token: str | None = None, timeout: int = 12) -> dict:
    access_token = (token if token is not None else os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")).strip()
    if not access_token:
        return {
            "connected": False,
            "stage": "configuration",
            "status": "missing_credentials",
            "money_moved": False,
            "payouts_enabled": False,
            "message": "Configure MERCADOPAGO_ACCESS_TOKEN como segredo no servidor.",
        }

    request = Request(
        API_BASE + "/users/me",
        headers={"Authorization": "Bearer " + access_token, "Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read(500_000).decode("utf-8"))
        return {
            "connected": True,
            "stage": "authentication",
            "status": "credentials_valid",
            "account_id": payload.get("id"),
            "site_id": payload.get("site_id"),
            "money_moved": False,
            "payouts_enabled": False,
            "message": (
                "Credencial autenticada. Isso não comprova saldo disponível nem permissão "
                "para repasses. Nenhuma transferência foi solicitada."
            ),
        }
    except HTTPError as exc:
        return {
            "connected": False,
            "stage": "authentication",
            "status": "credential_rejected" if exc.code in (401, 403) else "provider_error",
            "http_status": exc.code,
            "money_moved": False,
            "payouts_enabled": False,
            "message": "A API do Mercado Pago não confirmou a conexão.",
        }
    except (URLError, TimeoutError, OSError, ValueError) as exc:
        return {
            "connected": False,
            "stage": "connection",
            "status": "connection_error",
            "error_type": type(exc).__name__,
            "money_moved": False,
            "payouts_enabled": False,
            "message": "Não foi possível consultar a API do Mercado Pago.",
        }


if __name__ == "__main__":
    print(json.dumps(check_mercadopago_connection(), ensure_ascii=False, indent=2))
