import unittest
from overlay_provenance import blob, check_exact, declarations, baron_body, xml_cases

class ProvenanceTests(unittest.TestCase):
    def test_git_blob_hash(self):
        self.assertEqual(blob(b""), "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391")
        with self.assertRaises(ValueError):
            check_exact(b"x", blob(b"y"), "changed")
    def test_declarations(self):
        self.assertEqual(declarations(b"TEST_F(A, B) {}\nTEST_F(A,C) {}"), {"A.B","A.C"})
        with self.assertRaises(ValueError):
            declarations(b"TEST_F(A,B) {}\nTEST_F(A,B) {}")
    def test_baron_body(self):
        raw = b"TEST_F(RadianceFinal64Test, Example){\n  if (true) {\n    f();\n  }\n}\n"
        self.assertEqual(baron_body(raw,"Example"),raw.rstrip())
        with self.assertRaises(ValueError):
            baron_body(raw+raw,"Example")
        with self.assertRaises(ValueError):
            baron_body(raw,"Absent")
    def test_wrong_xml(self):
        with self.assertRaisesRegex(ValueError,"hash mismatch"):
            xml_cases(b"<testsuites/>")

if __name__ == "__main__":
    unittest.main()
