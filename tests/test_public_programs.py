import unittest

from genese_autonomo import parse_programs
from priorizador_recompensas import rank_programs


class PublicProgramParsingTests(unittest.TestCase):
    def test_only_bounty_programs_with_https_urls_are_kept(self):
        payload = """[
          {"name":"Wallet Program","url":"https://example.org/bounty","bounty":true,"domains":["wallet.example.org"]},
          {"name":"No Bounty","url":"https://example.org/no","bounty":false},
          {"name":"Insecure","url":"http://example.org/bounty","bounty":true},
          {"name":"Broken","url":"https://","bounty":true}
        ]"""
        rows = parse_programs(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["programa"], "Wallet Program")

    def test_invalid_json_returns_empty_list(self):
        self.assertEqual(parse_programs("{not json"), [])

    def test_duplicate_urls_are_deduplicated(self):
        payload = """[
          {"name":"One","url":"https://example.org/bounty","bounty":true},
          {"name":"Duplicate","url":"https://example.org/bounty","bounty":true}
        ]"""
        rows = parse_programs(payload)
        self.assertEqual(len(rows), 1)

    def test_limit_is_respected(self):
        payload = """[
          {"name":"One","url":"https://one.example/bounty","bounty":true},
          {"name":"Two","url":"https://two.example/bounty","bounty":true}
        ]"""
        self.assertEqual(len(parse_programs(payload, limit=1)), 1)


class RewardPrioritizationTests(unittest.TestCase):
    def test_crypto_related_programs_rank_first(self):
        rows = [
            {"programa": "General Security", "url": "https://example.org/a", "escopo": "web app"},
            {"programa": "Blockchain Wallet", "url": "https://example.org/b", "escopo": "wallet"},
        ]
        result = rank_programs(rows)
        self.assertEqual(result[0]["programa"], "Blockchain Wallet")
        self.assertEqual(result[0]["tipo"], "cripto/web3")
        self.assertEqual(result[0]["status_financeiro"], "nao_verificado")

    def test_ranking_never_marks_money_as_confirmed(self):
        result = rank_programs([
            {"programa": "Bitcoin wallet", "url": "https://example.org/a", "escopo": ""}
        ])
        self.assertEqual(result[0]["status_financeiro"], "nao_verificado")

    def test_input_is_not_mutated(self):
        original = [{"programa": "Other", "url": "https://example.org", "escopo": ""}]
        rank_programs(original)
        self.assertNotIn("relevancia", original[0])


if __name__ == "__main__":
    unittest.main()
