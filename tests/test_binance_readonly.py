import hashlib
import hmac
import unittest
from urllib.parse import parse_qs

from scripts.binance_readonly_check import signed_query, validate_read_only_credentials


class BinanceReadOnlyTests(unittest.TestCase):
    def test_signature_is_hmac_sha256_over_query_without_signature(self):
        secret = "unit-test-secret"
        query = signed_query(secret, 1700000000000)
        unsigned, signature = query.rsplit("&signature=", 1)
        expected = hmac.new(secret.encode(), unsigned.encode(), hashlib.sha256).hexdigest()
        self.assertEqual(signature, expected)
        params = parse_qs(unsigned)
        self.assertEqual(params["timestamp"], ["1700000000000"])
        self.assertEqual(params["recvWindow"], ["5000"])

    def test_missing_credentials_fail_before_network(self):
        with self.assertRaisesRegex(ValueError, "BINANCE_API_KEY"):
            validate_read_only_credentials("", "")


if __name__ == "__main__":
    unittest.main()
