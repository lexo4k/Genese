"""Mercado Pago Orders API adapter; sandbox by default, production by explicit server config."""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.parse
import urllib.error
import urllib.request
import uuid


class MercadoPagoError(RuntimeError):
    pass


def _request(method: str, path: str, payload: dict | None = None, idempotency_key: str | None = None) -> dict:
    token = os.environ.get("MP_ACCESS_TOKEN", "").strip()
    mode = os.environ.get("MP_MODE", "sandbox").strip().lower()
    if not token:
        raise MercadoPagoError("MP_ACCESS_TOKEN não configurado no servidor")
    if mode not in ("sandbox", "production"):
        raise MercadoPagoError("MP_MODE deve ser sandbox ou production")
    if mode == "production" and token.startswith("TEST-"):
        raise MercadoPagoError("Token de teste não pode ser usado em MP_MODE=production")
    if mode == "sandbox" and token.startswith("APP_USR-"):
        raise MercadoPagoError("Token de produção não pode ser usado em MP_MODE=sandbox")
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        "https://api.mercadopago.com" + path,
        data=body,
        method=method,
        headers={
            "Authorization": "Bearer " + token,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Idempotency-Key": idempotency_key or str(uuid.uuid4()),
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            result = json.loads(response.read(1_000_000).decode("utf-8"))
    except urllib.error.HTTPError as exc:
        try:
            detail = exc.read(2048).decode("utf-8", "replace")
        except Exception:
            detail = "resposta de erro sem corpo"
        raise MercadoPagoError(f"Mercado Pago HTTP {exc.code}: {detail}") from None
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise MercadoPagoError(f"Falha de conexão/resposta do Mercado Pago: {type(exc).__name__}") from None
    if not isinstance(result, dict):
        raise MercadoPagoError("Resposta inesperada do Mercado Pago")
    return result


def create_pix_order(amount_cents: int, email: str, external_reference: str, description: str) -> dict:
    if isinstance(amount_cents, bool) or not isinstance(amount_cents, int) or amount_cents < 100:
        raise MercadoPagoError("Valor inválido")
    if not isinstance(email, str) or "@" not in email or len(email) > 254:
        raise MercadoPagoError("Informe um e-mail válido do pagador")
    if not isinstance(external_reference, str) or not external_reference or len(external_reference) > 128:
        raise MercadoPagoError("Referência externa inválida")
    # Production requests use the actual payer email; no test fixture is injected.
    payload = {
        "type": "online",
        "processing_mode": "automatic",
        "external_reference": external_reference,
        "total_amount": f"{amount_cents / 100:.2f}",
        "payer": {"email": email},
        "transactions": {
            "payments": [{
                "amount": f"{amount_cents / 100:.2f}",
                "payment_method": {"id": "pix", "type": "bank_transfer"},
            }]
        },
    }
    idempotency_key = hashlib.sha256(("genese-order:" + external_reference).encode("utf-8")).hexdigest()
    result = _request("POST", "/v1/orders", payload, idempotency_key=idempotency_key)
    if not result.get("id"):
        raise MercadoPagoError("A resposta do provedor não contém o ID da ordem")
    return result


def fetch_order(order_id: str) -> dict:
    if not order_id or len(order_id) > 128:
        raise MercadoPagoError("ID de ordem inválido")
    return _request("GET", "/v1/orders/" + urllib.parse.quote(order_id, safe=""))


def payment_state(order: dict) -> str:
    status = str(order.get("status", "")).lower()
    payments = ((order.get("transactions") or {}).get("payments") or [])
    payment_statuses = [str(p.get("status", "")).lower() for p in payments if isinstance(p, dict)]
    all_statuses = [status] + payment_statuses
    if any(s in ("approved", "processed", "completed") for s in all_statuses):
        return "approved"
    if any(s in ("rejected", "failed") for s in all_statuses):
        return "rejected"
    if any(s in ("cancelled", "canceled") for s in all_statuses):
        return "cancelled"
    if any(s in ("expired") for s in all_statuses):
        return "expired"
    return "pending"


def verify_webhook_signature(signature_header: str, request_id: str, resource_id: str, secret: str) -> bool:
    if not signature_header or not request_id or not resource_id or not secret:
        return False
    fields = {}
    for part in signature_header.split(","):
        key, sep, value = part.strip().partition("=")
        if sep:
            fields[key.strip()] = value.strip()
    timestamp = fields.get("ts", "")
    received = fields.get("v1", "")
    if not timestamp or not received:
        return False
    # Mercado Pago requires the resource ID lower-cased in the signed manifest.
    manifest = f"id:{resource_id.lower()};request-id:{request_id};ts:{timestamp};"
    expected = hmac.new(secret.encode("utf-8"), manifest.encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)
