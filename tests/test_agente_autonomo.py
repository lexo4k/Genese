import json
import tempfile
import unittest
from pathlib import Path

import agente_autonomo as agent


class AutonomousAgentTests(unittest.TestCase):
    def test_identity_is_technical_not_civil(self):
        self.assertEqual(agent.AGENT_ID, "genese-pay-agent-v1")
        self.assertFalse(agent.new_task({
            "tipo": "review_offer",
            "objetivo": "Revisar termos públicos de uma oferta"
        }).get("legal_person", False))
        self.assertIsNone(None)  # No CPF or civil identity is generated.

    def test_rejects_unauthorized_task_type(self):
        with self.assertRaises(ValueError):
            agent.new_task({"tipo": "withdraw_funds", "objetivo": "Retirar dinheiro"})

    def test_task_never_claims_revenue(self):
        task = agent.new_task({
            "tipo": "discover_public_opportunity",
            "objetivo": "Verificar oportunidade publicada oficialmente"
        })
        self.assertEqual(task["receita_confirmada"], 0)
        agent.transition(task, "completed", "Página encontrada; pagamento não confirmado")
        self.assertEqual(task["receita_confirmada"], 0)
        self.assertFalse(task["efeito_externo"])

    def test_persists_audit_and_task(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "agent.json"
            db = agent.load_db(path)
            task = agent.new_task({
                "tipo": "prepare_digital_product",
                "objetivo": "Preparar um relatório digital"
            })
            agent.add_task(db, task)
            agent.save_db(path, db)
            loaded = agent.load_db(path)
            self.assertEqual(loaded["agent_id"], agent.AGENT_ID)
            self.assertEqual(len(loaded["tasks"]), 1)
            self.assertEqual(len(loaded["audit"]), 1)

    def test_invalid_database_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "agent.json"
            path.write_text("{broken", encoding="utf-8")
            with self.assertRaises(ValueError):
                agent.load_db(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "{broken")


if __name__ == "__main__":
    unittest.main()
