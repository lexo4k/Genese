import unittest

from genese_dashboard import HOST, PAGE


class GeneseDashboardSafetyTests(unittest.TestCase):
    def test_server_is_loopback_only(self):
        self.assertEqual(HOST, "127.0.0.1")

    def test_dashboard_can_start_real_external_miner_without_claiming_income(self):
        self.assertIn("Processo de mineração real", PAGE)
        self.assertIn("Iniciar minerador", PAGE)
        self.assertIn("Parar", PAGE)
        self.assertIn("Receita confirmada", PAGE)
        self.assertIn("Nenhum valor estimado ou alegado será tratado como dinheiro recebido", PAGE)
        self.assertIn("Nenhuma transferência é executada", PAGE)

    def test_dashboard_exposes_local_miner_controls_and_read_only_provider_api(self):
        self.assertIn("fetch('/api/status'", PAGE)
        self.assertIn("fetch('/api/nicehash'", PAGE)
        self.assertIn("fetch('/api/miner/'+action", PAGE)
        self.assertNotIn("withdraw", PAGE.lower())
        self.assertNotIn("transferir agora", PAGE.lower())


if __name__ == "__main__":
    unittest.main()
