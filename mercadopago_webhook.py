"""Mercado Pago payment notification adapter for GENESE PAY.

Environment:
  MERCADOPAGO_ACCESS_TOKEN: private server-side access token
  MERCADOPAGO_WEBHOOK_SECRET: signing secret from Mercado Pago Webhooks settings

Configure the public HTTPS webhook URL as /api/webhooks/mercadopago only after
this adapter is wired into the server. Never put these values in frontend code.
"""
import hashlib
import hmac
import json
import os
import re
from urllib.request import Request, urlopen


class MercadoPagoWebhookError(ValueError):
    pass


def validate_signature(x_signature: str, x_request_id: str, data_id: str, secret: str) -> bool:
    """Validate Mercado Pago's x-signature manifest (id, request-id, timestamp)."""
    if not all((x_signature, x_request_id, data_id, secret)):
        return False
    parts = {}
    for item in x_signature.split(","):
        if "=" in item:
            key, value = item.strip().split("=", 1)
            parts[key.strip()] = value.strip()
    timestamp, received = parts.get("ts", ""), parts.get("v1", "")
    if not timestamp or not received:
        return False
    manifest = f"id:{data_id};request-id:{x_request_id};ts:{timestamp};"
    expected = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, received)


def fetch_payment(payment_id: str) -> dict:
    """Fetch canonical payment state from Mercado Pago; never trust webhook amount."""
    token = os.getenv("MERCADOPAGO_ACCESS_TOKEN", "")
    if not token:
        raise MercadoPagoWebhookError("MERCADOPAGO_ACCESS_TOKEN is not configured.")
    if not re.fullmatch(r"[0-9]{1,30}", str(payment_id)):
        raise MercadoPagoWebhookError("Invalid payment ID.")
    request = Request(
        f"https://api.mercadopago.com/v1/payments/{payment_id}",
        headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
        method="GET",
    )
    with urlopen(request, timeout=12) as response:
        if response.status != 200:
            raise MercadoPagoWebhookError("Mercado Pago did not confirm the payment.")
        data = json.loads(response.read(1_000_000).decode("utf-8", "replace"))
    if str(data.get("id", "")) != str(payment_id):
        raise MercadoPagoWebhookError("Payment ID mismatch.")
    if data.get("status") != "approved":
        return {"confirmed": False, "status": str(data.get("status", "unknown"))}
    amount, currency = data.get("transaction_amount"), str(data.get("currency_id", "")).upper()
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
        raise MercadoPagoWebhookError("Invalid amount from Mercado Pago.")
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise MercadoPagoWebhookError("Invalid currency from Mercado Pago.")
    return {
        "confirmed": True,
        "provider": "mercadopago",
        "transaction_id": str(data["id"]),
        "status": "approved",
        "amount": float(amount),
        "currency": currency,
    }


def verify_and_fetch(x_signature: str, x_request_id: str, data_id: str) -> dict:
    secret = os.getenv("MERCADOPAGO_WEBHOOK_SECRET", "")
    if not validate_signature(x_signature, x_request_id, data_id, secret):
        raise MercadoPagoWebhookError("Invalid Mercado Pago webhook signature.")
    return fetch_payment(data_id)
