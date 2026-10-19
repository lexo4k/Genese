import unittest

from contratos_recompensa import (
    accept_offer, confirmed_payment, new_offer, record_funding, record_payment,
    review_work, submit_work,
)


def offer_data():
    return {
        "pagador": "Empresa de teste",
        "contato_pagador": "financeiro@example.org",
        "termos_url": "https://example.org/terms",
        "trabalho": "Criar um relatório técnico.",
        "criterios_aceitacao": "Relatório completo e revisado.",
        "valor": 100,
        "moeda": "BRL",
        "prazo_utc": "2026-12-31T23:59:59Z",
        "pagamento_metodo": "Transferência após aprovação",
    }


class RewardContractTests(unittest.TestCase):
    def test_draft_never_claims_guaranteed_payment(self):
        offer = new_offer(offer_data())
        self.assertEqual(offer["status"], "rascunho")
        self.assertIsNone(offer["pagamento"])
        self.assertIsNone(offer["prova_fundos"])

    def test_cannot_accept_without_explicit_payer_consent(self):
        offer = new_offer(offer_data())
        with self.assertRaises(ValueError):
            accept_offer(offer, {"aceitou": False, "evidencia_aceite_url": "https://example.org/accept", "nome_responsavel": "Pessoa"})
    
    def test_full_lifecycle_requires_separate_evidence_steps(self):
        offer = new_offer(offer_data())
        accept_offer(offer, {"aceitou": True, "evidencia_aceite_url": "https://example.org/accept", "nome_responsavel": "Responsável"})
        self.assertEqual(offer["status"], "aceito_sem_fundos_verificados")
        record_funding(offer, {"evidencia_fundos_url": "https://example.org/escrow", "referencia_fundos": "ESCROW-123"})
        submit_work(offer, {"entrega_url": "https://example.org/delivery", "resumo": "Relatório enviado"})
        review_work(offer, {"aprovado": True, "nome_revisor": "Revisor", "evidencia_aprovacao_url": "https://example.org/approved"})
        record_payment(offer, {"comprovante_url": "https://example.org/payment", "referencia_transacao": "TX-1", "valor_pago": 100})
        self.assertEqual(offer["status"], "pagamento_informado_pendente_confirmacao_externa")
        confirmed_payment(offer, {"referencia_confirmacao": "BANK-REF-1", "evidencia_confirmacao_url": "https://example.org/confirmed"})
        self.assertEqual(offer["status"], "pagamento_confirmado_por_evidencia_registrada")

    def test_cannot_submit_work_before_funding_evidence(self):
        offer = new_offer(offer_data())
        with self.assertRaises(ValueError):
            submit_work(offer, {"entrega_url": "https://example.org/work", "resumo": "done"})

    def test_cannot_mark_underpayment_as_paid(self):
        offer = new_offer(offer_data())
        accept_offer(offer, {"aceitou": True, "evidencia_aceite_url": "https://example.org/accept", "nome_responsavel": "Responsável"})
        record_funding(offer, {"evidencia_fundos_url": "https://example.org/escrow", "referencia_fundos": "ESCROW-123"})
        submit_work(offer, {"entrega_url": "https://example.org/delivery", "resumo": "Relatório enviado"})
        review_work(offer, {"aprovado": True, "nome_revisor": "Revisor", "evidencia_aprovacao_url": "https://example.org/approved"})
        with self.assertRaises(ValueError):
            record_payment(offer, {"comprovante_url": "https://example.org/payment", "referencia_transacao": "TX-1", "valor_pago": 50})

    def test_rejects_http_terms(self):
        data = offer_data()
        data["termos_url"] = "http://example.org/terms"
        with self.assertRaises(ValueError):
            new_offer(data)


if __name__ == "__main__":
    unittest.main()
