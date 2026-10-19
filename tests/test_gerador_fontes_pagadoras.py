import unittest

from gerador_fontes_pagadoras import build_payer_cards


class PayerCardGeneratorTests(unittest.TestCase):
    def test_creates_actionable_card_without_claiming_payment(self):
        result = build_payer_cards({
            "oportunidades": [{
                "titulo": "Security bounty",
                "url": "https://example.org/program",
                "fonte": "Diretório público de bug bounty",
            }]
        })
        self.assertEqual(result["fichas_geradas"], 1)
        self.assertEqual(result["pagadores_confirmados"], 0)
        self.assertEqual(result["receita_confirmada"], 0)
        card = result["fichas"][0]
        self.assertEqual(card["status"], "precisa_validacao")
        self.assertFalse(card["pagador_confirmado"])
        self.assertGreaterEqual(len(card["proximas_acoes"]), 3)

    def test_deduplicates_urls(self):
        item = {"titulo": "Opportunity", "url": "https://example.org/a"}
        result = build_payer_cards({"oportunidades": [item, item]})
        self.assertEqual(result["fichas_geradas"], 1)

    def test_rejects_non_https_urls(self):
        result = build_payer_cards({"oportunidades": [
            {"titulo": "bad", "url": "http://example.org"},
            {"titulo": "also bad", "url": "javascript:alert(1)"},
            {"titulo": "valid", "url": "https://example.org"},
        ]})
        self.assertEqual(result["fichas_geradas"], 1)
        self.assertEqual(result["fichas"][0]["nome"], "valid")

    def test_ignores_malformed_opportunities(self):
        result = build_payer_cards({"oportunidades": [None, "bad", 4]})
        self.assertEqual(result["fichas_geradas"], 0)


if __name__ == "__main__":
    unittest.main()
