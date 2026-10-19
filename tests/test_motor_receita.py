import json
import unittest
from unittest.mock import patch

import motor_receita


class MotorReceitaTests(unittest.TestCase):
    def test_github_issues_keeps_only_public_reward_signals(self):
        payload = json.dumps({"items": [
            {"title": "Bounty $250 for issue", "html_url": "https://github.com/org/repo/issues/1",
             "repository_url": "https://api.github.com/repos/org/repo", "body": "Web3 bug bounty"},
            {"title": "Ordinary issue", "html_url": "https://github.com/org/repo/issues/2",
             "repository_url": "https://api.github.com/repos/org/repo", "body": "Please fix this"},
            {"title": "Not GitHub", "html_url": "https://example.com/3", "body": "reward $100"},
            {"title": "Pull request bounty $100", "html_url": "https://github.com/org/repo/pull/4",
             "pull_request": {"url": "https://api.github.com/repos/org/repo/pulls/4"}, "body": "bounty"},
        ]})
        rows = motor_receita._github_issues(payload)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["valor_confirmado"], None)
        self.assertEqual(rows[0]["status"], "nao_verificado")
        self.assertTrue(rows[0]["relevancia_cripto"])

    def test_invalid_json_returns_empty_list(self):
        self.assertEqual(motor_receita._github_issues("not-json"), [])

    @patch("motor_receita.fetch")
    def test_collection_keeps_money_unconfirmed(self, mock_fetch):
        catalog = json.dumps([{"name": "Crypto Program", "url": "https://example.org/security",
                               "bounty": True, "domains": ["example.org"]}]).encode()
        github = json.dumps({"items": [
            {"title": "Bounty $100", "html_url": "https://github.com/org/repo/issues/1",
             "repository_url": "https://api.github.com/repos/org/repo", "body": "crypto reward"}
        ]}).encode()
        mock_fetch.side_effect = [(200, catalog), (200, github), (200, github), (200, github)]
        report = motor_receita.collect_opportunities()
        self.assertGreaterEqual(report["resumo"]["candidatas_encontradas"], 2)
        self.assertEqual(report["resumo"]["receita_confirmada"], 0)
        self.assertFalse(report["resumo"]["saldo_binance_consultado"])
        self.assertFalse(report["resumo"]["transferencia_executada"])


if __name__ == "__main__":
    unittest.main()
