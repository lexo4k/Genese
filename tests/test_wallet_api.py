import json
import os
import tempfile
import unittest
from pathlib import Path

import wallet_api


class WalletCoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        wallet_api.DB_PATH = Path(self.tmp.name) / "test.sqlite3"
        wallet_api.init_db()

    def tearDown(self):
        self.tmp.cleanup()

    def test_password_hash_uses_salt_and_verifies(self):
        salt = b"0123456789abcdef"
        one = wallet_api.password_digest("uma senha longa e forte", salt)
        two = wallet_api.password_digest("uma senha longa e forte", salt)
        other = wallet_api.password_digest("uma senha diferente", salt)
        self.assertEqual(one, two)
        self.assertNotEqual(one, other)

    def test_new_wallet_has_zero_confirmed_balance(self):
        with wallet_api.connect_db() as db:
            db.execute(
                "INSERT INTO users VALUES (?,?,?,?,?)",
                ("u1", "teste@example.com", "00" * 16, "00" * 32, 100)
            )
            summary = wallet_api.wallet_summary(db, "u1")
        self.assertEqual(summary["balance_cents"], 0)
        self.assertEqual(summary["balance_brl"], "0.00")
        self.assertEqual(summary["currency"], "BRL")
        self.assertIn("não representa dinheiro", summary["meaning"])

    def test_pending_credit_does_not_increase_balance(self):
        with wallet_api.connect_db() as db:
            db.execute(
                "INSERT INTO users VALUES (?,?,?,?,?)",
                ("u1", "teste@example.com", "00" * 16, "00" * 32, 100)
            )
            db.execute(
                "INSERT INTO ledger VALUES (?,?,?,?,?,?,?,?)",
                ("tx1", "u1", 5000, "credit", "pending", "ref1", "Cobrança pendente", 101)
            )
            summary = wallet_api.wallet_summary(db, "u1")
        self.assertEqual(summary["balance_cents"], 0)
        self.assertEqual(summary["pending_transactions"], 1)

    def test_confirmed_ledger_entries_use_integer_cents(self):
        with wallet_api.connect_db() as db:
            db.execute(
                "INSERT INTO users VALUES (?,?,?,?,?)",
                ("u1", "teste@example.com", "00" * 16, "00" * 32, 100)
            )
            db.execute(
                "INSERT INTO ledger VALUES (?,?,?,?,?,?,?,?)",
                ("tx1", "u1", 1250, "credit", "confirmed", "ref1", "Crédito confirmado", 101)
            )
            db.execute(
                "INSERT INTO ledger VALUES (?,?,?,?,?,?,?,?)",
                ("tx2", "u1", 200, "debit", "confirmed", "ref2", "Débito confirmado", 102)
            )
            summary = wallet_api.wallet_summary(db, "u1")
        self.assertEqual(summary["balance_cents"], 1050)
        self.assertEqual(summary["balance_brl"], "10.50")

    def test_database_rejects_duplicate_reference(self):
        with wallet_api.connect_db() as db:
            db.execute(
                "INSERT INTO users VALUES (?,?,?,?,?)",
                ("u1", "teste@example.com", "00" * 16, "00" * 32, 100)
            )
            db.execute(
                "INSERT INTO ledger VALUES (?,?,?,?,?,?,?,?)",
                ("tx1", "u1", 100, "credit", "pending", "same-ref", "A", 101)
            )
            with self.assertRaises(Exception):
                db.execute(
                    "INSERT INTO ledger VALUES (?,?,?,?,?,?,?,?)",
                    ("tx2", "u1", 100, "credit", "pending", "same-ref", "B", 102)
                )


if __name__ == "__main__":
    unittest.main()
