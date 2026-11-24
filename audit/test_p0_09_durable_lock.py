import unittest
from p0_09_durable_lock import madison_versions,verify_files
class Tests(unittest.TestCase):
    def test_madison(self):
        self.assertEqual(madison_versions("pkg | 1.0-2 | http://archive noble/main amd64 Packages\npkg | 2.0 | http://archive noble-updates\n"),{"1.0-2","2.0"})
    def test_empty(self):
        self.assertEqual(madison_versions("error\npkg | 1.0 | \n"),set())
    def test_drift(self):
        with self.assertRaises(ValueError):verify_files(b"{}",b"{}")
