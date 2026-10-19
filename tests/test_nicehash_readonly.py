import hashlib
import hmac
import unittest

from nicehash_readonly import (
    NiceHashCredentials, credentials_from_env, make_auth_headers,
    signature_message, get_read_only,
)


class NiceHashReadOnlyTests(unittest.TestCase):
    def test_missing_credentials_returns_none(self):
        self.assertIsNone(credentials_from_env({}))

    def test_partial_credentials_rejected(self):
        with self.assertRaises(ValueError):
            credentials_from_env({"NICEHASH_API_KEY": "key"})

    def test_signature_is_hmac_sha256_over_expected_segments(self):
        creds = NiceHashCredentials("key", "secret", "org")
        headers = make_auth_headers(
            creds, "GET", "/main/api/v2/mining/rigs",
            timestamp="123", nonce="nonce",
        )
        message = signature_message(
            "key", "123", "nonce", "org", "GET", "/main/api/v2/mining/rigs"
        )
        expected = hmac.new(b"secret", message, hashlib.sha256).hexdigest()
        self.assertEqual(headers["X-Auth"], "key:" + expected)
        self.assertEqual(headers["X-Time"], "123")
        self.assertEqual(headers["X-Organization-Id"], "org")

    def test_only_allowlisted_read_only_endpoints(self):
        creds = NiceHashCredentials("key", "secret", "org")
        with self.assertRaises(ValueError):
            get_read_only("/main/api/v2/accounting/withdrawal", creds)
        with self.assertRaises(ValueError):
            get_read_only("/main/api/v2/hashpower/order", creds)


if __name__ == "__main__":
    unittest.main()
