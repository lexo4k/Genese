import unittest

from contratantes_publicos import build_report, normalize_job


class ContractorCollectorTests(unittest.TestCase):
    def test_rejects_missing_or_non_https_urls(self):
        self.assertIsNone(normalize_job({"title": "Junior Developer", "company_name": "Acme", "url": "http://example.com"}))
        self.assertIsNone(normalize_job({"title": "Junior Developer", "company_name": "Acme"}))

    def test_normalizes_public_listing_without_claiming_payment(self):
        row = normalize_job({
            "title": "Junior Python Developer",
            "company_name": "Example Ltd",
            "url": "https://example.com/jobs/1",
            "location": "Remote",
            "remote": True,
            "tags": ["Python"],
            "salary": None,
        })
        self.assertIsNotNone(row)
        self.assertEqual(row["contratante"], "Example Ltd")
        self.assertEqual(row["status_candidatura"], "não enviada")
        self.assertEqual(row["idade_minima"], "não verificada; conferir no anúncio oficial")
        self.assertIsNone(row["salario_informado"])

    def test_report_never_invents_income_or_submits_applications(self):
        report = build_report([{
            "title": "Junior Web Developer",
            "company_name": "Example Ltd",
            "url": "https://example.com/jobs/2",
        }])
        self.assertEqual(report["ganhos_confirmados"], 0)
        self.assertEqual(report["candidaturas_enviadas"], 0)
        self.assertFalse(report["pagamento_automatico"])
        self.assertIsNone(report["saldo_confirmado"])
        self.assertEqual(report["anuncios_relevantes"], 1)


if __name__ == "__main__":
    unittest.main()
