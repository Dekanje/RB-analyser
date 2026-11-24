import unittest
from p0_09_toolchain import cache_values, verify_cache, verify_lock, packages, PIN

class ToolchainTests(unittest.TestCase):
    def flags(self):
        return dict(CMAKE_BUILD_TYPE="Release", CMAKE_GENERATOR="Ninja",
                    RIFTBOUND_BUILD_JOBS="3", RIFTBOUND_BUILD_OPENSPIEL="ON",
                    RIFTBOUND_BUILD_LIBTORCH="OFF", RIFTBOUND_USE_PCH="ON",
                    RIFTBOUND_UNITY_CARDS="ON", RIFTBOUND_CARD_UNITY_BATCH="16",
                    RIFTBOUND_OPT_LEVEL="", RIFTBOUND_CHECK_BOARD_INDEX="OFF",
                    CMAKE_CXX_COMPILER="/usr/bin/g++-13", CMAKE_CXX_FLAGS_RELEASE="-O3 -DNDEBUG")
    def test_cache_parser(self):
        self.assertEqual(cache_values("// comment\nX:STRING=a=b\nY:BOOL=ON\n"), {"X":"a=b","Y":"ON"})
        with self.assertRaises(ValueError):
            cache_values("X:STRING=a\nX:BOOL=ON\n")
    def test_config(self):
        self.assertEqual(verify_cache(self.flags(),3)["RIFTBOUND_BUILD_LIBTORCH"],"OFF")
        for key, value in (("CMAKE_CXX_COMPILER_LAUNCHER","ccache"),("RIFTBOUND_BUILD_LIBTORCH","ON"),("CMAKE_CXX_FLAGS","-O0")):
            with self.assertRaises(ValueError):
                verify_cache({**self.flags(),key:value},3)
    def test_lock_drift(self):
        verify_lock({"a":1},{"a":1})
        with self.assertRaises(ValueError):
            verify_lock({"a":1},{"a":2})
    def test_packages(self):
        raw="g++-13\t13.3\tinstalled\nlibboost-context1.83.0:amd64\t1.83\tinstalled\nunrelated\t5\tinstalled"
        self.assertEqual(len(packages(raw)),2)
        with self.assertRaises(ValueError):
            packages(raw.split("\n")[0])
    def test_source_pins(self):
        self.assertEqual(len(PIN["overlays"]),23)
        self.assertEqual(len(PIN["dependency_git"]),6)
        self.assertTrue(all(len(x)==40 for x in PIN["dependency_git"].values()))
