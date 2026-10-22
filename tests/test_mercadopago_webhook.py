import hashlib
import hmac
import unittest

from mercadopago_webhook import validate_signature


class MercadoPagoWebhookTests(unittest.TestCase):
    def test_valid_signature(self):
        secret = "unit-test-secret"
        data_id = "123456789"
        request_id = "request-abc"
        timestamp = "1704908010"
        manifest = f"id:{data_id};request-id:{request_id};ts:{timestamp};"
        signature = hmac.new(secret.encode(), manifest.encode(), hashlib.sha256).hexdigest()
        self.assertTrue(validate_signature(f"ts={timestamp},v1={signature}", request_id, data_id, secret))

    def test_rejects_wrong_secret(self):
        self.assertFalse(validate_signature("ts=1,v1=deadbeef", "req", "123", "not-the-secret"))

    def test_rejects_missing_fields(self):
        self.assertFalse(validate_signature("", "req", "123", "secret"))


if __name__ == "__main__":
    unittest.main()
