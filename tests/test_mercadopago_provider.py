import os
import hashlib
import hmac
import unittest
from unittest.mock import patch

import mercadopago_provider as mp


class MercadoPagoAdapterTests(unittest.TestCase):
    def test_webhook_signature_accepts_valid_manifest(self):
        secret = "test-secret"
        request_id = "req-123"
        resource_id = "ORDABC123"
        ts = "1742505638683"
        manifest = f"id:{resource_id.lower()};request-id:{request_id};ts:{ts};"
        digest = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
        self.assertTrue(mp.verify_webhook_signature(f"ts={ts},v1={digest}", request_id, resource_id, secret))

    def test_webhook_signature_rejects_tampering_and_missing_secret(self):
        self.assertFalse(mp.verify_webhook_signature("ts=1,v1=deadbeef", "req", "ord", "secret"))
        self.assertFalse(mp.verify_webhook_signature("ts=1,v1=deadbeef", "req", "ord", ""))

    def test_payment_state_mapping(self):
        self.assertEqual(mp.payment_state({"status": "processed"}), "approved")
        self.assertEqual(mp.payment_state({"status": "rejected"}), "rejected")
        self.assertEqual(mp.payment_state({"status": "action_required"}), "pending")
        self.assertEqual(mp.payment_state({"transactions": {"payments": [{"status": "approved"}]}}), "approved")

    @patch("mercadopago_provider._request")
    def test_pix_order_payload_uses_real_payer_email_and_idempotency_key(self, request):
        request.return_value = {"id": "ord-test", "status": "action_required", "transactions": {"payments": []}}
        result = mp.create_pix_order(1299, "test@example.com", "charge-123", "Teste")
        self.assertEqual(result["id"], "ord-test")
        args = request.call_args.args
        payload = args[2]
        self.assertEqual(args[0], "POST")
        self.assertEqual(args[1], "/v1/orders")
        self.assertEqual(payload["total_amount"], "12.99")
        self.assertEqual(payload["transactions"]["payments"][0]["amount"], "12.99")
        self.assertEqual(payload["payer"]["email"], "test@example.com")
        self.assertNotIn("first_name", payload["payer"])
        self.assertEqual(request.call_args.kwargs["idempotency_key"], hashlib.sha256(b"genese-order:charge-123").hexdigest())

    def test_production_mode_rejects_test_token_before_network(self):
        with patch.dict(os.environ, {"MP_MODE": "production", "MP_ACCESS_TOKEN": "TEST-fake"}):
            with patch("mercadopago_provider.urllib.request.urlopen") as urlopen:
                with self.assertRaises(mp.MercadoPagoError):
                    mp._request("GET", "/v1/orders/123")
                urlopen.assert_not_called()

    def test_sandbox_mode_rejects_production_token_before_network(self):
        with patch.dict(os.environ, {"MP_MODE": "sandbox", "MP_ACCESS_TOKEN": "APP_USR-fake"}):
            with patch("mercadopago_provider.urllib.request.urlopen") as urlopen:
                with self.assertRaises(mp.MercadoPagoError):
                    mp._request("GET", "/v1/orders/123")
                urlopen.assert_not_called()

    def test_invalid_amount_is_rejected_before_network(self):
        with self.assertRaises(mp.MercadoPagoError):
            mp.create_pix_order(0, "test@example.com", "ref", "Teste")


if __name__ == "__main__":
    unittest.main()
