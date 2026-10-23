import tempfile
import unittest
from pathlib import Path

import motor_receita


class RevenueEngineTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.old_db = motor_receita.DB
        motor_receita.DB = Path(self.tmp.name) / "test.sqlite3"
        motor_receita.init_engine()

    def tearDown(self):
        motor_receita.DB = self.old_db
        self.tmp.cleanup()

    def test_unverified_commission_is_rejected(self):
        with self.assertRaises(PermissionError):
            motor_receita.record_verified_commission(
                "network", "conversion-1", "BRL", 12.5, {"id": "conversion-1"}
            )

    def test_verified_commission_is_idempotent(self):
        args = ("network", "conversion-1", "BRL", 12.5, {"official_status": "approved"})
        first = motor_receita.record_verified_commission(*args, provider_verified=True)
        second = motor_receita.record_verified_commission(*args, provider_verified=True)
        self.assertTrue(first["inserted"])
        self.assertFalse(second["inserted"])
        summary = motor_receita.revenue_summary()
        self.assertEqual(summary["confirmed_commission_by_currency"]["BRL"], 12.5)
        self.assertEqual(summary["confirmed_event_count"], 1)

    def test_draft_asset_is_not_revenue(self):
        result = motor_receita.save_content_asset("Post teste", "Texto de exemplo")
        self.assertEqual(result["status"], "draft")
        self.assertFalse(result["counts_as_revenue"])
        summary = motor_receita.revenue_summary()
        self.assertEqual(summary["confirmed_event_count"], 0)
        self.assertEqual(summary["assets_by_status"]["draft"], 1)

    def test_invalid_amount_rejected(self):
        with self.assertRaises(ValueError):
            motor_receita.record_verified_commission(
                "network", "conversion-2", "BRL", 0, {"approved": True},
                provider_verified=True
            )


if __name__ == "__main__":
    unittest.main()
