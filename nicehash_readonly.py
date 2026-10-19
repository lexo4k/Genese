"""Read-only NiceHash API client for GÊNESE PAY.

Only GET endpoints are allowed. No order placement, withdrawals, address changes,
or other financial mutations are implemented. Credentials must be provided via
environment variables and must never be committed to source control.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

BASE_URL = "https://api2.nicehash.com"
READ_ONLY_PATHS = {
    "/main/api/v2/mining/rigs",
    "/main/api/v2/mining/rigs/stats/unpaid",
    "/main/api/v2/mining/rigs/stats/data",
    "/main/api/v2/mining/rigs/stats/history",
    "/main/api/v2/accounting/accounts2",
    "/main/api/v2/accounting/activities",
}


@dataclass(frozen=True)
class NiceHashCredentials:
    api_key: str
    api_secret: str
    organization_id: str


def credentials_from_env(env: dict[str, str] | None = None) -> NiceHashCredentials | None:
    env = os.environ if env is None else env
    key = env.get("NICEHASH_API_KEY", "").strip()
    secret = env.get("NICEHASH_API_SECRET", "").strip()
    org = env.get("NICEHASH_ORGANIZATION_ID", "").strip()
    if not any((key, secret, org)):
        return None
    if not all((key, secret, org)):
        raise ValueError("Configure as três variáveis NICEHASH_API_KEY, NICEHASH_API_SECRET e NICEHASH_ORGANIZATION_ID.")
    return NiceHashCredentials(key, secret, org)


def signature_message(
    api_key: str, timestamp: str, nonce: str, organization_id: str,
    method: str, path: str, query: str = "", body: str = "",
) -> bytes:
    parts = [
        api_key, timestamp, nonce, "", organization_id, "", method.upper(), path, query,
    ]
    message = "\x00".join(parts)
    if body:
        message += "\x00" + body
    return message.encode("utf-8")


def make_auth_headers(
    credentials: NiceHashCredentials, method: str, path: str,
    query: str = "", body: str = "", timestamp: str | None = None,
    nonce: str | None = None,
) -> dict[str, str]:
    timestamp = timestamp or str(int(time.time() * 1000))
    nonce = nonce or str(uuid.uuid4())
    message = signature_message(
        credentials.api_key, timestamp, nonce, credentials.organization_id,
        method, path, query, body,
    )
    digest = hmac.new(
        credentials.api_secret.encode("utf-8"), message, hashlib.sha256
    ).hexdigest()
    return {
        "X-Time": timestamp,
        "X-Nonce": nonce,
        "X-Auth": credentials.api_key + ":" + digest,
        "X-Organization-Id": credentials.organization_id,
        "X-Request-Id": str(uuid.uuid4()),
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "GENESE-PAY-read-only/1.0",
    }


def get_read_only(
    path: str, credentials: NiceHashCredentials,
    params: dict[str, str] | None = None, timeout: float = 8.0,
) -> dict[str, Any]:
    if path not in READ_ONLY_PATHS:
        raise ValueError("Endpoint não permitido: somente rotas GET explicitamente autorizadas.")
    query = urlencode(params or {})
    url = BASE_URL + path + (("?" + query) if query else "")
    headers = make_auth_headers(credentials, "GET", path, query=query)
    request = Request(url, headers=headers, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            payload = json.loads(raw)
            return {
                "ok": True,
                "http_status": response.status,
                "endpoint": path,
                "data": payload,
            }
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1200]
        return {"ok": False, "http_status": exc.code, "endpoint": path, "error": detail}
    except (URLError, TimeoutError, OSError, json.JSONDecodeError) as exc:
        return {
            "ok": False, "http_status": None, "endpoint": path,
            "error": f"{type(exc).__name__}: {exc}",
        }


def collect_read_only_status(
    credentials: NiceHashCredentials, timeout: float = 8.0,
) -> dict[str, Any]:
    results = {
        path: get_read_only(path, credentials, timeout=timeout)
        for path in (
            "/main/api/v2/mining/rigs",
            "/main/api/v2/mining/rigs/stats/unpaid",
            "/main/api/v2/accounting/accounts2",
        )
    }
    return {
        "service": "GENESE PAY",
        "provider": "NiceHash",
        "mode": "read_only",
        "provider_responses": results,
        "all_requests_succeeded": all(item["ok"] for item in results.values()),
        "earnings_confirmed": False,
        "note": (
            "Respostas brutas da API do provedor; nenhum valor é convertido em saldo "
            "confirmado do GÊNESE PAY. Valide os campos da resposta antes de exibir "
            "ganhos e não confunda saldo não pago com pagamento na Binance."
        ),
        "financial_mutations_enabled": False,
    }


def main() -> int:
    try:
        credentials = credentials_from_env()
    except ValueError as exc:
        print(json.dumps({"ok": False, "configuration_error": str(exc)}, ensure_ascii=False))
        return 2
    if credentials is None:
        print(json.dumps({
            "ok": False,
            "status": "credentials_missing",
            "required_environment": [
                "NICEHASH_API_KEY", "NICEHASH_API_SECRET", "NICEHASH_ORGANIZATION_ID"
            ],
            "note": "Nenhuma chamada privada foi feita; configure credenciais localmente, nunca no código.",
        }, ensure_ascii=False, indent=2))
        return 2
    result = collect_read_only_status(credentials)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["all_requests_succeeded"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
