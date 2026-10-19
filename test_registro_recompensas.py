"""Testes do livro auditável de recompensas do GÊNESE."""
import tempfile
import unittest
from pathlib import Path

from registro_recompensas import (
    add_reward,
    approve_reward,
    load_db,
    mark_paid,
    save_db,
    summary,
)


class RewardLedgerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp.name) / "rewards.json"
        self.data = load_db(self.db_path)

    def tearDown(self):
        self.temp.cleanup()

    def test_opportunity_does_not_count_as_income(self):
        reward_id = add_reward(
            self.data, "Programa público", "https://example.org/security"
        )
        self.assertEqual(reward_id, "1")
        self.assertEqual(summary(self.data)["pagamentos_confirmados_por_moeda"], {})

    def test_payment_requires_approval(self):
        add_reward(self.data, "Programa público", "https://example.org/security")
        with self.assertRaisesRegex(ValueError, "Só uma recompensa aprovada"):
            mark_paid(self.data, 1, "https://example.org/payment-proof")

    def test_only_paid_reward_counts(self):
        add_reward(self.data, "Programa público", "https://example.org/security")
        approve_reward(
            self.data, 1, 25, "brl", "https://example.org/official-approval"
        )
        self.assertEqual(summary(self.data)["pagamentos_confirmados_por_moeda"], {})
        mark_paid(self.data, 1, "https://example.org/official-payment")
        self.assertEqual(
            summary(self.data)["pagamentos_confirmados_por_moeda"], {"BRL": 25.0}
        )

    def test_rejects_non_https_evidence(self):
        add_reward(self.data, "Programa público", "https://example.org/security")
        with self.assertRaisesRegex(ValueError, "HTTPS"):
            approve_reward(self.data, 1, 25, "BRL", "http://example.org/proof")

    def test_persists_json(self):
        add_reward(self.data, "Programa público", "https://example.org/security")
        save_db(self.data, self.db_path)
        loaded = load_db(self.db_path)
        self.assertEqual(len(loaded["rewards"]), 1)
        self.assertEqual(loaded["rewards"][0]["status"], "encontrada")


if __name__ == "__main__":
    unittest.main()
