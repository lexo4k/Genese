import tempfile
import unittest
from pathlib import Path

import auditoria_etapas as auditoria


class AuditoriaEtapasTests(unittest.TestCase):
    def test_files_do_not_claim_real_revenue_or_deposit(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in (
                "wallet_api.py", "genese_pay_web.py", "motor_receita.py",
                "binance_account_readonly.py",
                "produto_inicial/kit-controle-financeiro-autonomos.md",
            ):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text("test", encoding="utf-8")
            report = auditoria.build_report(root, {})
            stages = {x["id"]: x for x in report["etapas"]}
            self.assertEqual(stages["codigo_base"]["status"], "concluida")
            self.assertEqual(stages["binance_codigo"]["status"], "concluida")
            self.assertEqual(stages["receita"]["status"], "pendente")
            self.assertEqual(stages["binance_deposito"]["status"], "pendente")
            self.assertEqual(report["resumo"]["receita_confirmada_brl"], 0)

    def test_ci_flags_only_mark_the_steps_run_by_workflow(self):
        env = {
            "GITHUB_ACTIONS": "true",
            "GITHUB_REPOSITORY": "lexo4k/Genese",
            "GITHUB_RUN_ID": "12345",
            "GENESE_CI_TESTS_PASSED": "true",
            "GENESE_CI_HEALTH_PASSED": "true",
            "GITHUB_SHA": "abc123",
        }
        report = auditoria.build_report(Path("."), env)
        stages = {x["id"]: x for x in report["etapas"]}
        self.assertEqual(stages["testes"]["status"], "concluida")
        self.assertEqual(stages["api_health"]["status"], "concluida")
        self.assertEqual(stages["integracao"]["status"], "pendente")
        self.assertEqual(stages["hospedagem"]["status"], "pendente")
        self.assertEqual(stages["android"]["status"], "pendente")
        self.assertIn("/actions/runs/12345", stages["testes"]["evidencia"]["workflow"])

    def test_report_writes_json_and_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            report = auditoria.write_report(tmp, {})
            self.assertTrue((Path(tmp) / "evidencias/status_etapas.json").is_file())
            md = (Path(tmp) / "evidencias/STATUS_ETAPAS.md").read_text(encoding="utf-8")
            self.assertIn("Receita confirmada: R$ 0,00", md)
            self.assertEqual(report["resumo"]["etapas_total"], 10)


if __name__ == "__main__":
    unittest.main()
