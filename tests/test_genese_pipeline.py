import json
import tempfile
import unittest
from pathlib import Path

from genese_pipeline import build_report, classify, load_items


class PipelineTests(unittest.TestCase):
    def test_keyword_only_lead_is_not_income(self):
        row = classify({"programa": "Example opportunity", "url": "https://example.org/program", "relevancia": 7})
        self.assertEqual(row["status_pipeline"], "pista_nao_verificada")
        self.assertFalse(row["receita_contabilizavel"])
        self.assertFalse(row["dinheiro_recebido"])

    def test_terms_need_manual_review_before_promotion(self):
        row = classify({
            "programa": "Example work",
            "url": "https://example.org/work",
            "official_evidence_url": "https://example.org/terms",
            "requisitos_verificados": True,
            "deadline_verified": True,
            "payment_terms_verified": True,
        })
        self.assertEqual(row["status_pipeline"], "pista_nao_verificada")
        self.assertFalse(row["receita_contabilizavel"])

    def test_manual_flags_without_details_or_official_source_do_not_promote(self):
        row = classify({
            "programa": "Example work",
            "url": "https://example.org/work",
            "official_evidence_url": "https://example.org/terms",
            "requisitos_verificados": True,
            "deadline_verified": True,
            "payment_terms_verified": True,
            "manual_review_completed": True,
        })
        self.assertEqual(row["status_pipeline"], "pista_nao_verificada")

    def test_reviewed_opportunity_still_needs_authorized_action(self):
        row = classify({
            "programa": "Example work",
            "url": "https://example.org/work",
            "official_evidence_url": "https://example.org/terms",
            "official_source_verified": True,
            "eligibility_verified": True,
            "eligibility_details": "Minimum age 16; Brazil eligible",
            "deadline_verified": True,
            "deadline_at": "2026-11-30",
            "payment_terms_verified": True,
            "payment_terms": "Payment after accepted delivery",
            "manual_review_completed": True,
        })
        self.assertEqual(row["status_pipeline"], "oportunidade_revisada_manual_requer_acao_autorizada")
        self.assertFalse(row["receita_contabilizavel"])

    def test_accepted_work_is_declared_pending_not_received(self):
        row = classify({
            "url": "https://example.org",
            "official_evidence_url": "https://example.org/acceptance",
            "official_source_verified": True,
            "work_accepted": True,
            "manual_review_completed": True,
        })
        self.assertEqual(row["status_pipeline"], "trabalho_aceito_declarado_pagamento_pendente")
        self.assertFalse(row["receita_contabilizavel"])

    def test_claimed_payment_is_not_authenticated_by_json_fields(self):
        report = build_report([
            {
                "url": "https://example.org/a",
                "funds_received": True,
                "payment_confirmed": True,
                "provider_verified": True,
                "provider_evidence_url": "https://provider.example/tx/1",
                "transaction_id": "tx-1",
                "received_amount": 12.5,
                "received_currency": "BRL",
            },
            {"url": "https://example.org/b", "funds_received": True, "received_amount": 999, "received_currency": "BRL"},
            {"url": "https://example.org/c", "relevancia": 100},
        ])
        self.assertEqual(report["confirmed_received_totals_by_currency"], {})
        self.assertEqual(report["confirmed_received_count"], 0)
        self.assertFalse(report["payment_verification_enabled"])
        self.assertEqual(report["items"][0]["status_pipeline"], "recebimento_declarado_nao_autenticado")
        self.assertFalse(report["items"][0]["evidencia_pagador_autenticada"])
        self.assertFalse(report["items"][0]["receita_contabilizavel"])
        self.assertFalse(report["safety"]["active_target_scanning"])
        self.assertFalse(report["safety"]["automatic_transfers"])

    def test_payment_claim_requires_manual_reconciliation(self):
        row = classify({
            "url": "https://example.org",
            "payment_confirmed": True,
            "provider_verified": True,
            "provider_evidence_url": "https://provider.example/tx/1",
            "transaction_id": "tx-1",
        })
        self.assertEqual(row["status_pipeline"], "pagamento_declarado_pendente_de_verificacao")
        self.assertFalse(row["dinheiro_recebido"])

    def test_multiple_sources_are_loaded_and_attributed(self):
        with tempfile.TemporaryDirectory() as directory:
            bounty_file = Path(directory) / "bounties.json"
            jobs_file = Path(directory) / "jobs.json"
            bounty_file.write_text(json.dumps({"oportunidades": [{"programa": "Bounty", "url": "https://example.org/b"}]}), encoding="utf-8")
            jobs_file.write_text(json.dumps({"anuncios": [{"titulo": "Apprentice", "url_oficial": "https://example.org/j"}]}), encoding="utf-8")

            items, errors = load_items([str(bounty_file), str(jobs_file)])
            report = build_report(items)

            self.assertEqual(errors, [])
            self.assertEqual(report["items_reviewed"], 2)
            self.assertEqual(report["items_by_source"], {"bounties.json": 1, "jobs.json": 1})
            self.assertEqual(report["status_counts"], {"pista_nao_verificada": 2})

    def test_missing_source_is_reported_without_discarding_other_source(self):
        with tempfile.TemporaryDirectory() as directory:
            existing = Path(directory) / "jobs.json"
            existing.write_text(json.dumps({"anuncios": [{"titulo": "Apprentice"}]}), encoding="utf-8")
            items, errors = load_items([str(Path(directory) / "missing.json"), str(existing)])

            self.assertEqual(len(items), 1)
            self.assertEqual(len(errors), 1)
            self.assertIn("Arquivo de entrada não encontrado", errors[0])


if __name__ == "__main__":
    unittest.main()
