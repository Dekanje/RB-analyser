#!/usr/bin/env python3
"""Verify native structural coverage never skips, repeats or reuses first samples."""
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from full_structural_native import expected_keys, KINDS


class CompleteRegisteredStructureTests(unittest.TestCase):
    def test_partition_completeness_and_deterministic_order(self):
        rows={}
        for i in range(58):
            name=f"Legend {i:02d}"
            entries=[]
            for kind,count in (("rune",4),("battlefield",3),("sideboard",3),
                               ("champion",1 if i < 3 else 0)):
                for n in range(count):
                    entries.append({"kind":kind,"sha256":f"{name}-{kind}-{n}",
                                    "path":f"{name}/{kind}{n}.txt"})
            if i in (55, 56, 57):
                # 229 actual runes: one fewer than 58*4.
                entries=[x for x in entries
                         if x["sha256"] != f"{name}-rune-3"]
            rows[name]={"variants":entries}
        first=expected_keys(rows,first=True)
        remaining=expected_keys(rows,first=False)
        self.assertEqual(len(first),177)
        self.assertEqual(len(first)+len(remaining),580)
        self.assertFalse(set(first)&set(remaining))
        self.assertEqual(len(set(first+remaining)),580)
        self.assertEqual(first[0][0],"Legend 00")
        self.assertTrue(all(any(x[0]==n for x in first)
                            for n in rows))

    def test_unexpected_variant_family_rejected(self):
        rows={"A":{"variants":[{"kind":"not_constructed",
                                "sha256":"x","path":"x"}]}}
        with self.assertRaises(RuntimeError):
            expected_keys(rows,first=True)


if __name__=="__main__":
    unittest.main()
