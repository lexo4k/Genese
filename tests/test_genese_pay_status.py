import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import genese_receita


class GenesePayStatusTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = Path(self.tmp.name) / "test.sqlite3"
        self.db_patch = patch.object(genese_receita, "DB", self.db)
        self.db_patch.start()
        self.original_search = dict(genese_receita.SEARCH)
        genese_receita.SEARCH.update(running=False, progress=0, message="Pronto para buscar", results=[], updated_at=None, error=None)
        genese_receita.db_init()

    def tearDown(self):
        genese_receita.SEARCH.clear()
        genese_receita.SEARCH.update(self.original_search)
        self.db_patch.stop()
        self.tmp.cleanup()

    def test_empty_payment_ledger_never_claims_income(self):
        result = genese_receita.payment_summary()
        self.assertEqual(result["confirmed_total_by_currency"], {})
        self.assertEqual(result["confirmed_payments"], [])
        self.assertIn("receita confirmada = zero", result["note"])

    def test_totals_group_by_currency_without_mixing_units(self):
        rows = [
            ("mercadopago", "1", "BRL", 12.5, "CONFIRMED", "2026-01-01T00:00:00+00:00"),
            ("mercadopago", "2", "BRL", 7.5, "CONFIRMED", "2026-01-02T00:00:00+00:00"),
            ("mercadopago", "3", "USD", 2.0, "CONFIRMED", "2026-01-03T00:00:00+00:00"),
        ]
        self.assertEqual(genese_receita._totals(rows), {"BRL": 20.0, "USD": 2.0})

    def test_diagnostics_do_not_claim_payouts_when_credentials_exist(self):
        env = {
            "MERCADOPAGO_ACCESS_TOKEN": "test-token",
            "MERCADOPAGO_WEBHOOK_SECRET": "test-secret",
        }
        with patch.dict(os.environ, env, clear=True):
            handler = genese_receita.Handler
            self.assertTrue(callable(handler))
            # The route implementation must remain explicit about missing revenue
            # source and automatic payouts until a real provider adapter exists.
            source = Path(genese_receita.__file__).read_text(encoding="utf-8")
            self.assertIn('"revenue_source_connected": False', source)
            self.assertIn('"automatic_payout_enabled": False', source)

    def test_saved_opportunities_are_restored_after_process_state_reset(self):
        url = "https://example.org/program"
        with __import__("sqlite3").connect(self.db) as conn:
            conn.execute(
                "INSERT INTO opportunities(url,title,source,summary,found_at) VALUES(?,?,?,?,?)",
                (url, "Programa público", "Fonte de teste", "Descrição", "2026-01-01T00:00:00+00:00"),
            )
        genese_receita.SEARCH.update(results=[], running=False, updated_at=None)
        state = genese_receita.public_state()
        self.assertEqual(len(state["results"]), 1)
        self.assertEqual(state["results"][0]["url"], url)
        self.assertEqual(state["results"][0]["payment_status"], "Não recebido / não verificado")

    def test_payment_table_is_empty_until_verified_webhook(self):
        with self.db.open("rb"):
            pass
        with __import__("sqlite3").connect(self.db) as conn:
            count = conn.execute("SELECT COUNT(*) FROM payments").fetchone()[0]
        self.assertEqual(count, 0)


if __name__ == "__main__":
    unittest.main()
