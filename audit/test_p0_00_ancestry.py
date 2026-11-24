import unittest
from p0_00_ancestry import parse_tree,changes,classify,workflow_inventory
class Tests(unittest.TestCase):
    def test_tree(self):
        self.assertEqual(parse_tree(b"100644 blob abc\tfile with spaces\0"),{"file with spaces":("100644","blob","abc")})
    def test_changes(self):
        self.assertEqual(changes({"a":1,"b":2},{"b":3,"c":4}),{"only_branch":["c"],"only_integration":["a"],"changed":["b"]})
    def test_relationships(self):
        self.assertEqual([classify(a,b) for a,b in [(0,0),(0,4),(4,0),(2,3)]],["same","contained_in_integration","descendant_of_integration","diverged"])
    def test_workflow(self):
        r=workflow_inventory("on:\n  push:\n    branches: [main]\n  steps:\n    - uses: actions/download-artifact@v4\n      with:\n        run-id: 123\n        name: first\n    - uses: actions/upload-artifact@v4\n      with:\n        name: second\n")
        self.assertEqual(r["literal_run_ids"],[123]);self.assertEqual(r["downloads"][0]["name"],"first");self.assertEqual(r["uploads"][0]["name"],"second")
    def test_dynamic(self):
        r=workflow_inventory("run-id: \${{ inputs.run }}\n")
        self.assertEqual(r["literal_run_ids"],[]);self.assertTrue(r["unresolved_run_ids"])
