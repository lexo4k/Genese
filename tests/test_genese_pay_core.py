import tempfile
import unittest
from pathlib import Path

from genese_pay_core import (
    load_mining_config, record_income_evidence, income_summary,
    probe_pool, MiningConfig,
)


class MiningConfigTests(unittest.TestCase):
    def test_defaults_do_not_invent_wallet_or_worker(self):
        cfg = load_mining_config({})
        self.assertEqual(cfg.pool_host, "nhmp-ssl.eu.nicehash.com")
        self.assertEqual(cfg.pool_port, 443)
        self.assertEqual(cfg.worker, "")
        self.assertEqual(cfg.payout_address, "")

    def test_address_requires_network(self):
        with self.assertRaises(ValueError):
            load_mining_config({"BINANCE_DEPOSIT_ADDRESS": "example-address"})

    def test_invalid_port_rejected(self):
        with self.assertRaises(ValueError):
            load_mining_config({"GENESE_POOL_PORT": "99999"})


class IncomeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "ledger.sqlite3"

    def tearDown(self):
        self.tmp.cleanup()

    def test_invalid_or_zero_claim_rejected(self):
        for amount in (0, -1, True):
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    record_income_evidence("pool", "BTC", amount, "tx-1",
                                           "https://example.com/tx/1", self.db)

    def test_claim_is_never_misreported_as_confirmed(self):
        result = record_income_evidence("pool", "BTC", 0.001, "tx-abc",
                                        "https://example.com/tx/abc", self.db)
        self.assertTrue(result["recorded"])
        self.assertEqual(result["verification_status"], "UNVERIFIED")
        summary = income_summary(self.db)
        self.assertEqual(summary["unverified_claims"][0]["amount_claimed"], 0.001)
        self.assertIsNone(summary["confirmed_income"])
        self.assertIsNone(summary["confirmed_external_balance"])
        self.assertFalse(summary["binance_transfer_executed"])

    def test_duplicate_reference_cannot_double_count(self):
        args = ("pool", "BTC", 0.001, "same-tx", "https://example.com/tx/same")
        record_income_evidence(*args, db_path=self.db)
        with self.assertRaises(ValueError):
            record_income_evidence(*args, db_path=self.db)
        self.assertEqual(len(income_summary(self.db)["unverified_claims"]), 1)

    def test_http_evidence_rejected(self):
        with self.assertRaises(ValueError):
            record_income_evidence("pool", "BTC", 0.001, "tx-2",
                                   "http://example.com/tx/2", self.db)

    def test_pool_probe_never_claims_mining_from_connection_alone(self):
        result = probe_pool(MiningConfig("127.0.0.1", 1, "", "", ""), timeout=0.1)
        self.assertFalse(result["mining_active"])
        self.assertEqual(result["shares_submitted"], 0)


if __name__ == "__main__":
    unittest.main()
