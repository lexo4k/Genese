import unittest

from genese_pipeline import build_report, classify


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

    def test_reviewed_opportunity_still_needs_authorized_action(self):
        row = classify({
            "programa": "Example work",
            "url": "https://example.org/work",
            "official_evidence_url": "https://example.org/terms",
            "requisitos_verificados": True,
            "deadline_verified": True,
            "payment_terms_verified": True,
            "manual_review_completed": True,
        })
        self.assertEqual(row["status_pipeline"], "oportunidade_verificada_requer_acao_autorizada")
        self.assertFalse(row["receita_contabilizavel"])

    def test_accepted_work_is_pending_not_received(self):
        row = classify({
            "url": "https://example.org",
            "official_evidence_url": "https://example.org/acceptance",
            "work_accepted": True,
            "manual_review_completed": True,
        })
        self.assertEqual(row["status_pipeline"], "trabalho_aceito_pagamento_pendente")
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


if __name__ == "__main__":
    unittest.main()
