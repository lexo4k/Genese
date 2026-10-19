"""Testes da integração pública e somente leitura da Binance."""
import unittest

from binance_public import BinancePublicError, get_price


class BinancePublicTests(unittest.TestCase):
    def test_returns_price_without_claiming_income(self):
        def fake_get(url):
            self.assertIn("/api/v3/ticker/price?symbol=BTCUSDT", url)
            return {"symbol": "BTCUSDT", "price": "65000.12000000"}

        result = get_price("btcusdt", fetch_json=fake_get)
        self.assertEqual(result["symbol"], "BTCUSDT")
        self.assertEqual(result["price"], "65000.12")
        self.assertFalse(result["saldo_confirmado"])
        self.assertFalse(result["receita_confirmada"])
        self.assertFalse(result["transferencia_executada"])

    def test_rejects_invalid_symbol(self):
        with self.assertRaises(ValueError):
            get_price("../../private")

    def test_rejects_wrong_symbol_response(self):
        with self.assertRaises(BinancePublicError):
            get_price("BTCUSDT", fetch_json=lambda _: {"symbol": "ETHUSDT", "price": "3000"})

    def test_rejects_non_numeric_price(self):
        with self.assertRaises(BinancePublicError):
            get_price("BTCUSDT", fetch_json=lambda _: {"symbol": "BTCUSDT", "price": "unknown"})

    def test_rejects_non_positive_price(self):
        with self.assertRaises(BinancePublicError):
            get_price("BTCUSDT", fetch_json=lambda _: {"symbol": "BTCUSDT", "price": "0"})


if __name__ == "__main__":
    unittest.main()
