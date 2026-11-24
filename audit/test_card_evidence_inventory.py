import unittest
from card_evidence_inventory import executed_tests, explicit_scenarios, literal_mappings, unique


class EvidenceTests(unittest.TestCase):
    def test_disabled_not_passed(self):
        raw = b'<testsuites><testcase classname="S" name="A" status="notrun" result="suppressed"/></testsuites>'
        self.assertEqual(executed_tests(raw), {"S.A": False})

    def test_failed_not_passed(self):
        raw = b'<testsuites><testcase classname="S" name="A" status="run" result="completed"><failure/></testcase></testsuites>'
        self.assertEqual(executed_tests(raw), {"S.A": False})

    def test_explicit_enabled_mapping(self):
        m = {"code": {"status":"accepted", "engine_scenarios":["S.A"]}}
        self.assertEqual(explicit_scenarios(m, {"S.A": True}, {"code"}), {"code":["S.A"]})

    def test_missing_and_disabled_fail_closed(self):
        m = {"code": {"status":"accepted", "engine_scenarios":["S.A"]}}
        for t in ({}, {"S.A": False}):
            with self.assertRaises(ValueError):
                explicit_scenarios(m,t,{"code"})

    def test_duplicate_identity_rejected(self):
        with self.assertRaises(ValueError):
            unique([{"id": 1},{"id":1}], "id")

    def test_literal_mapping_without_executing(self):
        raw = b'WAVE1 = {"c":["x"]}\nKNOWN_GAPS = {"c":["g"]}\nraise RuntimeError("never execute")'
        self.assertEqual(literal_mappings(raw)["KNOWN_GAPS"], {"c":["g"]})


if __name__ == "__main__":
    unittest.main()
