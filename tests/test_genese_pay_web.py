import inspect
import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen
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

    def test_server_policy_restricts_binding_to_localhost(self):
        source = inspect.getsource(genese_pay_web.main)
        self.assertIn("GENESE_PAY_HOST", source)
        self.assertIn("127.0.0.1", source)
        self.assertIn('{"127.0.0.1", "localhost", "::1"}', source)
        self.assertIn("autenticação e HTTPS", source)

    def test_http_routes_serve_dashboard_status_and_empty_payer_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(genese_pay_web, "REPORT", Path(tmp) / "missing-report.json"), \
                 patch.object(genese_pay_web, "PAYER_CARDS", Path(tmp) / "missing-payers.json"):
                server = ThreadingHTTPServer(("127.0.0.1", 0), genese_pay_web.Handler)
                thread = threading.Thread(target=server.serve_forever, daemon=True)
                thread.start()
                base = f"http://127.0.0.1:{server.server_port}"
                try:
                    with urlopen(base + "/", timeout=3) as response:
                        html = response.read().decode("utf-8")
                        self.assertEqual(response.status, 200)
                    self.assertIn("GÊNESE PAY", html)
                    with urlopen(base + "/api/status", timeout=3) as response:
                        status = json.loads(response.read().decode("utf-8"))
                    self.assertEqual(status["receita_confirmada_brl"], 0.0)
                    self.assertFalse(status["binance_conectada"])
                    with urlopen(base + "/api/payer-sources", timeout=3) as response:
                        payers = json.loads(response.read().decode("utf-8"))
                    self.assertEqual(payers["fichas"], [])
                    request = Request(base + "/not-a-route")
                    with self.assertRaises(HTTPError) as error:
                        urlopen(request, timeout=3)
                    self.assertEqual(error.exception.code, 404)
                finally:
                    server.shutdown()
                    server.server_close()
                    thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
