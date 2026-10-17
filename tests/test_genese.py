import json
import unittest
from genese_autonomo import parse_programs

class ParseProgramsTests(unittest.TestCase):
    def test_keeps_only_bounty_https_programs_and_deduplicates(self):
        payload = json.dumps([
            {"name": "Alpha", "url": "https://example.com/bounty", "bounty": True, "domains": ["example.com"]},
            {"name": "No bounty", "url": "https://example.com/security", "bounty": False},
            {"name": "Unsafe scheme", "url": "http://example.com/bounty", "bounty": True},
            {"name": "Alpha duplicate", "url": "https://example.com/bounty", "bounty": True},
            {"name": "Bad record", "url": 12, "bounty": True},
        ])
        rows = parse_programs(payload, limit=20)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["programa"], "Alpha")
        self.assertEqual(rows[0]["escopo"], "example.com")

    def test_rejects_invalid_json(self):
        self.assertEqual(parse_programs("{not json"), [])

    def test_accepts_wrapped_data(self):
        payload = json.dumps({"programs": [
            {"name": "Beta", "url": "https://beta.example/security", "bounty": True}
        ]})
        self.assertEqual(len(parse_programs(payload)), 1)

if __name__ == "__main__":
    unittest.main()
