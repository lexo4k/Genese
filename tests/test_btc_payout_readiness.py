import unittest

from btc_payout_readiness import build_report, validate_mainnet_p2wpkh


class BitcoinPayoutReadinessTests(unittest.TestCase):
    def test_valid_mainnet_p2wpkh_address(self):
        # BIP-173 reference vector for a valid v0 20-byte witness program.
        valid, reason = validate_mainnet_p2wpkh(
            "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"
        )
        self.assertTrue(valid, reason)

    def test_rejects_wrong_network(self):
        valid, reason = validate_mainnet_p2wpkh(
            "tb1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "nao_e_endereco_bitcoin_mainnet_bc1")

    def test_rejects_bad_checksum(self):
        valid, reason = validate_mainnet_p2wpkh(
            "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt081"
        )
        self.assertFalse(valid)
        self.assertEqual(reason, "checksum_bech32_invalido")

    def test_report_never_claims_a_withdrawal(self):
        report = build_report(
            "bc1qw508d6qejxtdg4y5r3zarvary0c5xw7kygt080"
        )
        self.assertFalse(report["payout_api_enabled"])
        self.assertFalse(report["withdrawal_executed"])
        self.assertFalse(report["revenue_confirmed"])

    def test_missing_address_is_not_valid(self):
        report = build_report("")
        self.assertFalse(report["destination_configured"])
        self.assertFalse(report["destination_valid"])
        self.assertIsNone(report["destination"])


if __name__ == "__main__":
    unittest.main()
