import unittest

from binance_readonly import read_account_and_deposits


class BinanceReadOnlyIntegrationTests(unittest.TestCase):
    def test_missing_credentials_never_invents_balance_or_deposit(self):
        result = read_account_and_deposits({})
        self.assertFalse(result["ok"])
        self.assertEqual(result["status"], "credentials_missing")
        self.assertEqual(result["required_environment"], ["BINANCE_API_KEY", "BINANCE_API_SECRET"])
        self.assertNotIn("account_balances", result)
        self.assertNotIn("recent_deposits", result)
        self.assertFalse(result["withdrawals_enabled_by_this_app"])

    def test_partial_credentials_are_rejected(self):
        with self.assertRaises(ValueError):
            read_account_and_deposits({"BINANCE_API_KEY": "only-key", "BINANCE_API_SECRET": ""})


if __name__ == "__main__":
    unittest.main()
