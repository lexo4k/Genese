import csv
import json
import tempfile
import unittest
from pathlib import Path

import motor_receita_inicial as motor


class MotorReceitaInicialTests(unittest.TestCase):
    def test_creates_product_bundle_without_fake_revenue(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = motor.gerar_kit_inicial(Path(tmp))
            self.assertEqual(result["status"], "draft_created")
            self.assertEqual(result["offer"]["sales"], 0)
            self.assertEqual(result["offer"]["confirmed_received_brl"], 0.0)
            for name in result["offer"]["files"]:
                self.assertTrue((Path(tmp) / name).is_file())

    def test_csv_has_headers_and_no_fabricated_transactions(self):
        with tempfile.TemporaryDirectory() as tmp:
            motor.gerar_kit_inicial(Path(tmp))
            path = Path(tmp) / "modelo-movimentacoes-financeiras.csv"
            with path.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
            self.assertEqual(rows[0][0], "data")
            self.assertEqual(len(rows), 1)

    def test_offer_is_not_published(self):
        with tempfile.TemporaryDirectory() as tmp:
            motor.gerar_kit_inicial(Path(tmp))
            offer = json.loads((Path(tmp) / "oferta-kit-controle-financeiro.json").read_text(encoding="utf-8"))
            self.assertEqual(offer["status"], "draft_not_published")
            self.assertIn("não é publicado automaticamente.", " ".join(offer["limitations"]))


if __name__ == "__main__":
    unittest.main()
