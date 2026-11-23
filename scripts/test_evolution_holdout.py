#!/usr/bin/env python3
"""Independent holdout panel and multiple-testing regression tests."""
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from evolution_holdout import independent_panel


class HoldoutTests(unittest.TestCase):
    def test_different_untouched_opponents(self):
        ordered=[{"legend":f"Opponent{i}"} for i in range(12)]
        originals={r["legend"]:r["legend"] for r in ordered}
        panel,train=independent_panel("Target",ordered,originals)
        self.assertEqual(train,["Opponent0","Opponent1","Opponent2"])
        self.assertEqual(list(panel),[f"Opponent{i}" for i in range(3,9)])
        self.assertFalse(set(train)&set(panel))
        subset,train=independent_panel("Opponent2",ordered,originals)
        self.assertEqual(len(subset),6)
        self.assertNotIn("Opponent2",subset)
        self.assertFalse(set(train)&set(subset))

    def test_incomplete_field_fails_closed(self):
        ordered=[{"legend":"Only"}]
        with self.assertRaises(RuntimeError):
            independent_panel("Target",ordered,{"Only":"Only"})


if __name__=="__main__":
    unittest.main()
