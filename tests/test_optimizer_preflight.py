#!/usr/bin/env python3
"""Regression tests for the failure seen in optimizer run 44947342873."""
import json
import pathlib
import tempfile
import unittest
from validate_optimizer_preflight import validate_registry

class OptimizerPreflightTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = pathlib.Path(self.temp.name) / "registry.json"

    def _write(self, cards):
        self.path.write_text(json.dumps({"cards": cards}), encoding="utf-8")

    def test_exact_ids_pass_even_if_set_code_not_RAD(self):
        # The previous failure relied on an unjustified >=25 RAD set-code count.
        self._write([
            {"public_code": "RAD-149/167", "set_code": "Unspecified"},
            {"public_code": "RAD-041/167", "set_code": "Unspecified"},
        ])
        report = validate_registry(self.path, expected_count=2,
                                   required=("RAD-149/167", "RAD-041/167"))
        self.assertEqual(report["compiled_card_definitions"], 2)
        self.assertFalse(report["full_radiance_supported"])

    def test_missing_required_card_fails_clearly(self):
        self._write([{"public_code": "RAD-149/167"}])
        with self.assertRaisesRegex(ValueError, "Missing pinned Radiance"):
            validate_registry(self.path, expected_count=1,
                              required=("RAD-149/167", "RAD-041/167"))

    def test_wrong_registry_size_fails(self):
        self._write([{"public_code": "RAD-149/167"}])
        with self.assertRaisesRegex(ValueError, "Expected 988 compiled cards"):
            validate_registry(self.path, required=("RAD-149/167",))

    def test_missing_cards_list_fails(self):
        self.path.write_text('{"registry": []}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "cards list"):
            validate_registry(self.path, expected_count=0, required=())

    def test_duplicate_ids_fail(self):
        self._write([{"public_code": "RAD-149/167"},
                     {"public_code": "RAD-149/167"}])
        with self.assertRaisesRegex(ValueError, "Duplicate public_code"):
            validate_registry(self.path, expected_count=2,
                              required=("RAD-149/167",))

if __name__ == "__main__":
    unittest.main()
