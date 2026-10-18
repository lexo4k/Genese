import unittest

from genese_value_engine import ValueCandidate, ValueDiscoveryEngine


class ValueDiscoveryEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = ValueDiscoveryEngine()

    def candidate(self, **overrides):
        values = {
            "candidate_id": "candidate-1",
            "source_name": "Fonte oficial de teste",
            "source_url": "https://example.org/opportunity",
            "description": "Crédito confirmado para resgate",
            "amount_minor": 1250,
            "currency": "BRL",
            "evidence_url": "https://example.org/evidence/1",
            "issuer_reference": "ISSUER-123",
            "redemption_method": "resgate autorizado pelo emissor",
            "source_confirmed": True,
            "authorization_confirmed": True,
        }
        values.update(overrides)
        return ValueCandidate(**values)

    def test_fully_evidenced_candidate_is_receivable(self):
        result = self.engine.evaluate(self.candidate())
        self.assertEqual(result.status, "verified_receivable")
        self.assertTrue(result.is_receivable)
        self.assertTrue(self.engine.payout_eligibility(result))

    def test_unconfirmed_amount_is_never_receivable(self):
        result = self.engine.evaluate(self.candidate(amount_minor=None))
        self.assertEqual(result.status, "needs_verification")
        self.assertFalse(result.is_receivable)

    def test_untrusted_http_source_is_not_receivable(self):
        result = self.engine.evaluate(
            self.candidate(source_url="http://example.org/opportunity")
        )
        self.assertEqual(result.status, "needs_verification")
        self.assertFalse(result.is_receivable)
        self.assertIn("source_not_verifiable", result.checks)

    def test_missing_issuer_confirmation_is_not_receivable(self):
        result = self.engine.evaluate(self.candidate(source_confirmed=False))
        self.assertEqual(result.status, "needs_verification")
        self.assertFalse(result.is_receivable)
        self.assertIn("source_not_confirmed", result.checks)

    def test_missing_redemption_path_is_not_receivable(self):
        result = self.engine.evaluate(self.candidate(redemption_method=None))
        self.assertEqual(result.status, "needs_verification")
        self.assertFalse(result.is_receivable)
        self.assertIn("missing_redemption_path", result.checks)


if __name__ == "__main__":
    unittest.main()
