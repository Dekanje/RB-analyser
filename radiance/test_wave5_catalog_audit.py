"""Regression tests for fail-closed Radiance catalog/registry reconciliation."""
import contextlib
import copy
import io
import json
import unittest
from pathlib import Path
from radiance.audit_wave5_catalog_registry import audit

CATALOG = json.loads(Path("radiance/data/radiance_catalog.json").read_text())

class CatalogAuditTests(unittest.TestCase):
    def setUp(self):
        self.catalog = copy.deepcopy(CATALOG)
        self.registry = {"cards": []}

    def run_audit(self):
        with contextlib.redirect_stdout(io.StringIO()) as out:
            incomplete = audit(self.catalog, self.registry)
        return incomplete, json.loads(out.getvalue())

    def test_empty_compiled_registry_fails_closed_with_all_base_codes(self):
        incomplete, result = self.run_audit()
        self.assertTrue(incomplete)
        self.assertEqual(result["missing_base_count"], 167)
        self.assertEqual(len(result["missing_base_codes"]), 167)
        self.assertFalse(result["all_mechanics_verified"])

    def test_registration_does_not_imply_verified_mechanics(self):
        self.registry["cards"] = [{"public_code": f"RAD-{i:03d}/167", "id": 2000+i}
                                  for i in range(1,168)]
        incomplete, result = self.run_audit()
        self.assertFalse(incomplete)
        self.assertEqual(result["missing_base_count"], 0)
        self.assertFalse(result["all_mechanics_verified"])

    def test_duplicate_catalog_code_rejected(self):
        self.catalog["cards"][1]["public_code"] = self.catalog["cards"][0]["public_code"]
        with self.assertRaises(AssertionError):
            self.run_audit()

    def test_duplicate_compiled_code_rejected(self):
        self.registry["cards"] = [{"public_code":"RAD-001/167","id":100},
                                  {"public_code":"RAD-001/167","id":101}]
        with self.assertRaises(AssertionError):
            self.run_audit()

    def test_duplicate_engine_id_rejected_even_when_codes_differ(self):
        self.registry["cards"] = [{"public_code":"RAD-001/167","id":100},
                                  {"public_code":"RAD-002/167","id":100}]
        with self.assertRaisesRegex(AssertionError, "Duplicate compiled engine IDs"):
            self.run_audit()

    def test_uncatalogued_radiance_code_rejected(self):
        self.registry["cards"] = [{"public_code":"RAD-999/167","id":3000}]
        with self.assertRaisesRegex(AssertionError, "absent from catalog"):
            self.run_audit()

    def test_missing_numbered_catalog_identity_rejected(self):
        self.catalog["cards"] = [c for c in self.catalog["cards"]
                                  if c["public_code"] != "RAD-001/167"]
        with self.assertRaises(AssertionError):
            self.run_audit()

    def test_printing_does_not_satisfy_base_identity(self):
        alt = next(c["public_code"] for c in self.catalog["cards"]
                   if not c["public_code"].endswith("/167"))
        self.registry["cards"] = [{"public_code":alt,"id":3000}]
        incomplete, result = self.run_audit()
        self.assertTrue(incomplete)
        self.assertEqual(result["registered_base_count"], 0)
        self.assertIn(alt,result["extra_printings_requiring_rules_equivalence_review"])

if __name__ == "__main__":
    unittest.main()
