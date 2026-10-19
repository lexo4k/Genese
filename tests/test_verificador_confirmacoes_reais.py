import unittest
from decimal import Decimal
from unittest.mock import patch

import verificador_confirmacoes_reais as vr


class RealVerificationTests(unittest.TestCase):
    def test_validates_cnpj_checksum(self):
        self.assertEqual(vr.normalize_cnpj("11.222.333/0001-81"), "11222333000181")
        with self.assertRaises(ValueError):
            vr.normalize_cnpj("11.222.333/0001-80")

    def test_cnpj_active_status_is_from_external_payload(self):
        result = vr.verify_cnpj(
            "11.222.333/0001-81",
            get_json=lambda url: {
                "razao_social": "EMPRESA EXEMPLO LTDA",
                "descricao_situacao_cadastral": "ATIVA",
            },
        )
        self.assertTrue(result["consulta_externa_concluida"])
        self.assertTrue(result["registro_aparenta_ativo"])
        self.assertEqual(result["status_confirmacao"], "cadastro_publico_ativo")
        self.assertIn("terceiros", result["limite"])

    def test_non_active_cnpj_is_not_marked_active(self):
        result = vr.verify_cnpj(
            "11.222.333/0001-81",
            get_json=lambda url: {
                "razao_social": "EMPRESA EXEMPLO LTDA",
                "descricao_situacao_cadastral": "BAIXADA",
            },
        )
        self.assertFalse(result["registro_aparenta_ativo"])

    def test_cnpj_response_without_legal_name_fails_closed(self):
        with self.assertRaises(vr.VerificationError):
            vr.verify_cnpj("11.222.333/0001-81", get_json=lambda url: {})

    def test_binance_only_status_one_is_confirmed(self):
        payload = [
            {"coin": "USDT", "amount": "12.5", "status": 1, "txId": "tx-success"},
            {"coin": "USDT", "amount": "99", "status": 0, "txId": "tx-pending"},
            {"coin": "BTC", "amount": "0.001", "status": 6, "txId": "tx-locked"},
            {"coin": "USDT", "amount": "-3", "status": 1, "txId": "tx-invalid"},
        ]
        result = vr.get_binance_deposits(
            "test-key", "test-secret", get_json=lambda url, headers: payload,
            timestamp_ms=123456789,
        )
        self.assertEqual(result["depositos_retornados"], 3)
        self.assertEqual(result["depositos_confirmados"], 1)
        self.assertEqual(result["depositos"][0]["status"], "creditado_confirmado")
        self.assertFalse(result["depositos"][1]["creditado_com_sucesso"])
        self.assertIn("não prova que foi receita", result["observacao"])

    def test_missing_binance_credentials_fails_closed(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(vr.VerificationError):
                vr.get_binance_deposits()

    def test_bad_binance_payload_never_confirms(self):
        with self.assertRaises(vr.VerificationError):
            vr.get_binance_deposits(
                "test-key", "test-secret", get_json=lambda url, headers: {"balances": []},
                timestamp_ms=123456789,
            )

    def test_signed_request_contains_read_only_deposit_endpoint(self):
        captured = {}
        def getter(url, headers):
            captured["url"] = url
            captured["headers"] = headers
            return []
        result = vr.get_binance_deposits(
            "my-key", "my-secret", get_json=getter, timestamp_ms=123456789, coin="usdt"
        )
        self.assertIn("/sapi/v1/capital/deposit/hisrec?", captured["url"])
        self.assertIn("signature=", captured["url"])
        self.assertEqual(captured["headers"]["X-MBX-APIKEY"], "my-key")
        self.assertEqual(result["depositos_confirmados"], 0)


if __name__ == "__main__":
    unittest.main()
