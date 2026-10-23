import tempfile
import unittest
from pathlib import Path

import genese_ledger as ledger


class GeneseLedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = ledger.DB
        ledger.DB = Path(self.tmp.name) / "ledger.sqlite3"
        ledger.init_db()
        self.alice = ledger.create_account("Alice")["account_id"]
        self.bob = ledger.create_account("Bob")["account_id"]

    def tearDown(self):
        ledger.DB = self.old_db
        self.tmp.cleanup()

    def test_credit_requires_confirmed_provider_status(self):
        with self.assertRaises(PermissionError):
            ledger.credit_from_verified_provider(
                self.alice, 100, provider="provider", external_reference="p1",
                provider_status="pending"
            )
        self.assertEqual(ledger.balance(self.alice), 0)

    def test_confirmed_credit_is_idempotent(self):
        args = (self.alice, 500)
        kwargs = {"provider": "provider", "external_reference": "payment-1", "provider_status": "approved"}
        self.assertTrue(ledger.credit_from_verified_provider(*args, **kwargs)["inserted"])
        self.assertFalse(ledger.credit_from_verified_provider(*args, **kwargs)["inserted"])
        self.assertEqual(ledger.balance(self.alice), 500)

    def test_transfer_moves_existing_units_and_balances(self):
        ledger.credit_from_verified_provider(
            self.alice, 900, provider="provider", external_reference="payment-2",
            provider_status="settled"
        )
        result = ledger.transfer(self.alice, self.bob, 350, idempotency_key="transfer-1")
        self.assertTrue(result["inserted"])
        self.assertFalse(result["external_pix_sent"])
        self.assertEqual(ledger.balance(self.alice), 550)
        self.assertEqual(ledger.balance(self.bob), 350)

    def test_insufficient_balance_does_not_change_ledger(self):
        with self.assertRaises(ValueError):
            ledger.transfer(self.alice, self.bob, 1, idempotency_key="no-funds")
        self.assertEqual(ledger.balance(self.alice), 0)
        self.assertEqual(ledger.balance(self.bob), 0)

    def test_transfer_idempotency(self):
        ledger.credit_from_verified_provider(
            self.alice, 200, provider="provider", external_reference="payment-3",
            provider_status="approved"
        )
        ledger.transfer(self.alice, self.bob, 100, idempotency_key="once")
        result = ledger.transfer(self.alice, self.bob, 100, idempotency_key="once")
        self.assertFalse(result["inserted"])
        self.assertEqual(ledger.balance(self.alice), 100)
        self.assertEqual(ledger.balance(self.bob), 100)

    def test_reusing_key_with_different_data_fails(self):
        ledger.credit_from_verified_provider(
            self.alice, 300, provider="provider", external_reference="payment-4",
            provider_status="approved"
        )
        ledger.transfer(self.alice, self.bob, 100, idempotency_key="same-key")
        with self.assertRaises(ValueError):
            ledger.transfer(self.alice, self.bob, 150, idempotency_key="same-key")


if __name__ == "__main__":
    unittest.main()
