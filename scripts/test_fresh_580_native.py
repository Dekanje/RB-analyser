#!/usr/bin/env python3
"""Exact 580 structural native certificate source partition unit tests."""
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from fresh_580_native import EXPECTED,schedule


class Fresh580NativeTests(unittest.TestCase):
    def test_unique_family_shard_partition(self):
        names=[f"Legend-{x:02d}" for x in range(58)]
        rows={n:{"variants":[
            {"kind":f"category_{k}","sha256":f"{n}-{k}-{i}",
             "path":f"v/{n}-{k}-{i}.txt"}
            for k in ("rune","battlefield","sideboard","champion")
            for i in range(3 if k!="champion" else 1)
        ]} for n in names}
        output=[]
        for shard in range(29):
            selected,cards=schedule(rows,names,shard,29)
            self.assertEqual(len(selected),2)
            self.assertEqual(len(cards),len(selected)*10)
            output.extend((n,c["sha256"]) for n,c in cards)
        self.assertEqual(len(output),58*10)
        self.assertEqual(len(set(output)),len(output))
        self.assertEqual(EXPECTED,580)

    def test_input_order_does_not_change_shard_provenance(self):
        names=[f"L-{x}" for x in range(58)]
        rows={n:{"variants":[{"kind":"sideboard","sha256":n,"path":n}]}
              for n in names}
        self.assertEqual(schedule(rows,names,6,29),
                         schedule(rows,list(reversed(names)),6,29))


if __name__=="__main__":
    unittest.main()
