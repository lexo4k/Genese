import hashlib
import hmac
import unittest
from unittest.mock import patch

import binance_readonly
from binance_readonly import BinanceAPIError, read_account_and_deposits, _signed_get


class BinanceReadOnlyTests(unittest.TestCase):
    def test_missing_credentials_does_not_make_private_request(self):
        result = read_account_and_deposits({})
        self.assertEqual(result["status"], "credentials_missing")
        self.assertFalse(result["ok"])

    def test_partial_credentials_rejected(self):
        with self.assertRaises(ValueError):
            read_account_and_deposits({"BINANCE_API_KEY": "key"})

    def test_signed_get_uses_hmac_sha256_and_key_header(self):
        captured = {}

        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"balances": []}'

        def fake_urlopen(request, timeout):
            captured["url"] = request.full_url
            captured["key"] = request.get_header("X-mbx-apikey")
            captured["timeout"] = timeout
            return Response()

        with patch("binance_readonly.urlopen", fake_urlopen), patch("binance_readonly.time.time", return_value=1000):
            result = _signed_get("/api/v3/account", {}, "public-key", "secret", 2)
        self.assertEqual(result, {"balances": []})
        self.assertEqual(captured["key"], "public-key")
        self.assertEqual(captured["timeout"], 2)
        query = captured["url"].split("?", 1)[1]
        unsigned, signature = query.rsplit("&signature=", 1)
        expected = hmac.new(b"secret", unsigned.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(signature, expected)

    def test_account_and_deposit_data_are_provider_results(self):
        account = {"balances": [
            {"asset": "BTC", "free": "0.001", "locked": "0"},
            {"asset": "USDT", "free": "0", "locked": "0"}
        ]}
        deposits = [{"coin": "BTC", "amount": "0.001", "status": 1, "network": "BTC", "txId": "tx123", "insertTime": 123}]
        with patch("binance_readonly._credentials", return_value=("key", "secret")), patch(
            "binance_readonly._signed_get", side_effect=[account, deposits]
        ) as api:
            result = read_account_and_deposits()
        self.assertEqual(api.call_count, 2)
        self.assertEqual(result["status"], "provider_confirmed_read_only")
        self.assertEqual(result["account_balances"], [{"asset": "BTC", "free": 0.001, "locked": 0.0}])
        self.assertEqual(result["recent_deposits"][0]["tx_id"], "tx123")
        self.assertFalse(result["withdrawals_enabled_by_this_app"])

    def test_unexpected_provider_shape_fails_closed(self):
        with patch("binance_readonly._credentials", return_value=("key", "secret")), patch(
            "binance_readonly._signed_get", return_value={}
        ):
            with self.assertRaises(BinanceAPIError):
                read_account_and_deposits()


if __name__ == "__main__":
    unittest.main()
