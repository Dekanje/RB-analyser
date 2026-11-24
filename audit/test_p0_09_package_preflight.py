import unittest
from p0_09_package_preflight import (
    read_lock, unique_pairs, package_subset, apt_command, mismatches, CORE
)

class PackageTests(unittest.TestCase):
    def packages(self):
        return {**{k:"1.2" for k in CORE},"libboost-context1.83.0:amd64":"1.83.0-2",
                "unrelated":"9"}
    def test_wrong_receipt(self):
        with self.assertRaisesRegex(ValueError,"wrong configuration receipt"):
            read_lock(b"{}")
    def test_duplicates(self):
        with self.assertRaisesRegex(ValueError,"duplicate"):
            unique_pairs([("a",1),("a",2)])
    def test_subset(self):
        x=package_subset(self.packages())
        self.assertEqual(len(x),len(CORE)+1)
        self.assertNotIn("unrelated",x)
        del x["gcc-13"]
        with self.assertRaisesRegex(ValueError,"missing core"):
            package_subset(x)
    def test_unsafe(self):
        for bad in ("1; echo x","1\n2","-y"):
            with self.assertRaisesRegex(ValueError,"unsafe"):
                package_subset({**self.packages(),"gcc-13":bad})
    def test_plan_no_install(self):
        c=apt_command({"g++-13":"13.3","libc6:amd64":"2.39"})
        self.assertEqual(c,["apt-get","-s","install","--no-install-recommends","g++-13=13.3","libc6:amd64=2.39"])
        self.assertNotIn("sudo",c)
    def test_version_drift(self):
        self.assertEqual(mismatches({"a":"1","b":"2"},{"a":"3","c":"4"}),
                         {"a":{"expected":"1","observed":"3"},"b":{"expected":"2","observed":None}})
