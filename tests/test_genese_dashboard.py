import unittest

from genese_dashboard import HOST, PAGE


class GeneseDashboardSafetyTests(unittest.TestCase):
    def test_server_is_loopback_only(self):
        self.assertEqual(HOST, "127.0.0.1")

    def test_dashboard_does_not_claim_confirmed_income_or_mining(self):
        self.assertIn("Mineração confirmada", PAGE)
        self.assertIn("Não confirmada", PAGE)
        self.assertIn("Receita confirmada", PAGE)
        self.assertIn("Não disponível", PAGE)
        self.assertIn("Nenhuma transferência é executada", PAGE)

    def test_dashboard_uses_read_only_api_routes(self):
        self.assertIn("fetch('/api/status'", PAGE)
        self.assertIn("fetch('/api/nicehash'", PAGE)
        self.assertNotIn("withdraw", PAGE.lower())
        self.assertNotIn("transferir agora", PAGE.lower())


if __name__ == "__main__":
    unittest.main()
