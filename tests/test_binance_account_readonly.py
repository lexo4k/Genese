import hashlib
import hmac
import unittest
from urllib.parse import parse_qs, urlparse

from binance_account_readonly import BinanceAccountError, get_spot_balances


class BinanceReadonlyTests(unittest.TestCase):
    def test_requires_credentials(self):
        with self.assertRaises(BinanceAccountError):
            get_spot_balances("", "", timestamp_ms=123)

    def test_signs_account_query_and_returns_only_nonzero_assets(self):
        captured = {}
        def fake_request(url, api_key):
            captured["url"] = url
            captured["key"] = api_key
            return {"balances": [
                {"asset": "BTC", "free": "0.125", "locked": "0"},
                {"asset": "USDT", "free": "0", "locked": "0"},
                {"asset": "BAD", "free": "-1", "locked": "0"},
                {"asset": "ETH", "free": "bad", "locked": "0"},
            ]}
        result = get_spot_balances("public-key", "secret-test", request_json=fake_request, timestamp_ms=123456)
        parsed = urlparse(captured["url"])
        params = parse_qs(parsed.query)
        expected = hmac.new(b"secret-test", b"recvWindow=5000&timestamp=123456", hashlib.sha256).hexdigest()
        self.assertEqual(parsed.path, "/api/v3/account")
        self.assertEqual(params["signature"][0], expected)
        self.assertEqual(captured["key"], "public-key")
        self.assertEqual(result["ativos_com_saldo"], [{"asset": "BTC", "free": "0.125", "locked": "0"}])
        self.assertFalse(result["receita_confirmada"])
        self.assertFalse(result["transferencia_executada"])

    def test_rejects_unexpected_payload(self):
        with self.assertRaises(BinanceAccountError):
            get_spot_balances("k", "s", request_json=lambda *_: {"balances": None}, timestamp_ms=1)

    def test_secret_is_not_returned(self):
        result = get_spot_balances("key", "super-secret", request_json=lambda *_: {"balances": []}, timestamp_ms=1)
        self.assertNotIn("super-secret", str(result))
        self.assertNotIn("key", result)


if __name__ == "__main__":
    unittest.main()
