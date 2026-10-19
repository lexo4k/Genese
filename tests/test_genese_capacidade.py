import tempfile
import unittest
from pathlib import Path

import genese_capacidade as cap


class CapacityTests(unittest.TestCase):
    def test_initial_state_has_no_fake_entity_credit_or_money(self):
        state = cap.empty_state()
        s = cap.summary(state)
        self.assertEqual(s["legal_entity_status"], "not_registered")
        self.assertIsNone(s["legal_registration_number"])
        self.assertEqual(s["credit_approved_amount"], 0)
        self.assertEqual(s["confirmed_received"], 0)

    def test_checklist_is_not_legal_registration(self):
        state = cap.empty_state()
        for check in cap.LEGAL_CHECKS:
            cap.update_check(state, "legal", check, True)
        self.assertEqual(state["legal_entity"]["status"], "ready_for_external_review")
        self.assertIsNone(state["legal_entity"]["registration_number"])

    def test_user_entered_payment_evidence_does_not_create_confirmed_revenue(self):
        state = cap.empty_state()
        cap.record_confirmed_payment(
            state, 50, "BRL", "ref-example",
            "https://example.org/payment-proof"
        )
        self.assertEqual(state["revenue"]["confirmed_received"], 0)
        self.assertEqual(
            state["revenue"]["payments"][0]["status"],
            "externally_reported_pending_independent_verification",
        )

    def test_rejects_non_https_evidence(self):
        state = cap.empty_state()
        with self.assertRaises(ValueError):
            cap.update_check(state, "legal", "registro_oficial_concluido", True, "http://example.org")
        with self.assertRaises(ValueError):
            cap.record_confirmed_payment(state, 10, "BRL", "ref", "http://example.org")

    def test_rejects_negative_or_zero_amount(self):
        state = cap.empty_state()
        for amount in (0, -1):
            with self.assertRaises(ValueError):
                cap.record_confirmed_payment(
                    state, amount, "BRL", "ref",
                    "https://example.org/payment-proof"
                )

    def test_saves_and_loads_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capacity.json"
            state = cap.empty_state()
            cap.save_state(path, state)
            loaded = cap.load_state(path)
            self.assertEqual(loaded["schema_version"], 1)
            self.assertEqual(cap.summary(loaded)["confirmed_received"], 0)

    def test_invalid_file_is_not_replaced(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "capacity.json"
            path.write_text("{bad json", encoding="utf-8")
            with self.assertRaises(ValueError):
                cap.load_state(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "{bad json")


if __name__ == "__main__":
    unittest.main()
