import json
import tempfile
import unittest
from pathlib import Path

import preparar_negocio as pn


class PreparingBusinessTests(unittest.TestCase):
    def test_creates_product_and_sales_draft_without_fake_sales(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = pn.make_digital_product(
                "Guia de organização financeira", "iniciantes",
                "organizar despesas", "Passo 1: liste despesas fixas e variáveis.",
                9.9, Path(tmp),
            )
            self.assertEqual(result["status"], "draft_created")
            offer = json.loads((Path(tmp) / "guia-de-organizacao-financeira-oferta.json").read_text())
            self.assertEqual(offer["sales"], 0)
            self.assertEqual(offer["confirmed_received"], 0)
            self.assertEqual(offer["status"], "draft_not_published")
            self.assertTrue((Path(tmp) / "guia-de-organizacao-financeira-produto.md").exists())
            self.assertTrue((Path(tmp) / "guia-de-organizacao-financeira-pagina-vendas.md").exists())

    def test_rejects_empty_content_and_negative_price(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                pn.make_digital_product("title", "audience", "problem", "", 1, Path(tmp))
            with self.assertRaises(ValueError):
                pn.make_digital_product("title", "audience", "problem", "content", -1, Path(tmp))

    def test_business_packet_never_claims_registration(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = pn.make_business_readiness_packet(
                "Nome proposto", "desenvolvimento de software", "RS", Path(tmp)
            )
            self.assertEqual(result["status"], "preparation_only_not_registered")
            self.assertEqual(result["packet"]["steps"][0]["status"], "not_done")
            self.assertIn("não é registro oficial", " ".join(result["packet"]["limitations"]))

    def test_requires_business_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ValueError):
                pn.make_business_readiness_packet("", "atividade", "RS", Path(tmp))


if __name__ == "__main__":
    unittest.main()
