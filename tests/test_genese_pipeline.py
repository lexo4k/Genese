import unittest

from genese_pipeline import build_report, classify


class PipelineTests(unittest.TestCase):
    def test_keyword_only_lead_is_not_income(self):
        row = classify({"programa": "Example bounty", "url": "https://example.org/program", "relevancia": 7})
        self.assertEqual(row["status_pipeline"], "pista_nao_verificada")
        self.assertFalse(row["receita_contabilizavel"])
        self.assertFalse(row["pagamento_confirmado"])

    def test_verified_terms_still_need_authorized_action(self):
        row = classify({
            "programa": "Example work",
            "url": "https://example.org/work",
            "official_evidence_url": "https://example.org/terms",
            "requisitos_verificados": True,
            "deadline_verified": True,
            "payment_terms_verified": True,
        })
        self.assertEqual(row["status_pipeline"], "oportunidade_verificada_requer_acao_autorizada")
        self.assertFalse(row["receita_contabilizavel"])

    def test_accepted_work_is_pending_not_received(self):
        row = classify({"url": "https://example.org", "official_evidence_url": "https://example.org/acceptance", "work_accepted": True})
        self.assertEqual(row["status_pipeline"], "trabalho_aceito_pagamento_pendente")
        self.assertFalse(row["receita_contabilizavel"])

    def test_only_explicit_received_amount_counts(self):
        report = build_report([
            {"url": "https://example.org/a", "funds_received": True, "provider_verified": True, "provider_evidence_url": "https://provider.example/tx/1", "transaction_id": "tx-1", "received_amount": 12.5, "received_currency": "BRL"},
            {"url": "https://example.org/b", "funds_received": True, "received_amount": 999, "received_currency": "BRL"},
            {"url": "https://example.org/c", "relevancia": 100},
        ])
        self.assertEqual(report["confirmed_received_totals_by_currency"], {"BRL": 12.5})
        self.assertEqual(report["confirmed_received_count"], 1)
        self.assertFalse(report["safety"]["active_target_scanning"])
        self.assertFalse(report["safety"]["automatic_transfers"])


if __name__ == "__main__":
    unittest.main()
