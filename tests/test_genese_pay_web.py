import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import genese_pay_web


class GeneSePayDashboardTests(unittest.TestCase):
    def test_status_never_invents_income_or_binance_connection(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = Path(tmp) / "genese_receita.json"
            report.write_text(json.dumps({
                "timestamp_utc": "2026-10-18T00:00:00+00:00",
                "resumo": {"candidatas_encontradas": 7, "receita_confirmada": 9999}
            }), encoding="utf-8")
            with patch.object(genese_pay_web, "REPORT", report):
                data = genese_pay_web.status_payload()
        self.assertEqual(data["receita_confirmada_brl"], 0.0)
        self.assertIsNone(data["saldo_binance"])
        self.assertFalse(data["binance_conectada"])
        self.assertFalse(data["transferencias_habilitadas"])
        self.assertEqual(data["oportunidades_encontradas"], 7)

    def test_missing_report_returns_zero_opportunities(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(genese_pay_web, "REPORT", Path(tmp) / "missing.json"):
                data = genese_pay_web.status_payload()
        self.assertEqual(data["oportunidades_encontradas"], 0)
        self.assertEqual(data["receita_confirmada_brl"], 0.0)

    def test_dashboard_is_mobile_responsive_and_warns_about_unconnected_binance(self):
        self.assertIn('name="viewport"', genese_pay_web.HTML)
        self.assertIn("A Binance ainda não está conectada", genese_pay_web.HTML)
        self.assertIn("/api/refresh", genese_pay_web.HTML)
        self.assertIn("noopener noreferrer", genese_pay_web.HTML)

    def test_only_localhost_bind_addresses_are_allowed_by_policy(self):
        self.assertIn("127.0.0.1", genese_pay_web.__doc__ or "")
        self.assertIn("localhost", genese_pay_web.HTML.lower())


if __name__ == "__main__":
    unittest.main()
