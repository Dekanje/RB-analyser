#!/usr/bin/env python3
"""Fail-closed preregistration and seed-isolation tests for structural holdout."""
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from structural_128_holdout import FAMILY,shortlist,opponent_panel
from full_field_58 import mcnemar_exact,holm


class Structural128HoldoutPreflightTests(unittest.TestCase):
    def setUp(self):
        self.names=[f"Legend {i:02d}" for i in range(58)]
        self.manifest={"records":[{
            "legend":name,"original_sha256":f"baseline_{i}",
            "variants":[{"kind":"rune","sha256":f"rune_{i}","path":f"variant_{i}.txt"},
                        {"kind":"sideboard","sha256":f"sideboard_{i}","path":f"sideboard_{i}.txt"}]
        } for i,name in enumerate(self.names)]}
        self.screen={"best_unconfirmed_by_legend":[{
            "legend":name,"kind":"rune","candidate_sha256":f"rune_{i}",
            "screened_no_independent_confirmation":True,
            "sample_delta":3 if i<3 else 1,
            "paired_wins_candidate":3 if i<3 else 2,
            "paired_wins_baseline":0 if i<3 else 1,
        } for i,name in enumerate(self.names)]}

    def test_frozen_top12_one_legend_each(self):
        chosen=shortlist(self.screen,self.manifest)
        self.assertEqual(len(chosen),FAMILY)
        self.assertEqual([x["index"] for x in chosen],list(range(FAMILY)))
        self.assertEqual([x["legend"] for x in chosen],self.names[:FAMILY])
        self.assertEqual(len({x["candidate_sha256"] for x in chosen}),FAMILY)
        self.assertTrue(all(x["kind"]=="rune" for x in chosen))

    def test_manipulated_source_or_registration_rejected(self):
        self.screen["best_unconfirmed_by_legend"][5]["candidate_sha256"]="wrong"
        with self.assertRaises(RuntimeError):
            shortlist(self.screen,self.manifest)
        self.screen["best_unconfirmed_by_legend"][5]["candidate_sha256"]="rune_5"
        self.screen["best_unconfirmed_by_legend"][5]["kind"]="sideboard"
        with self.assertRaises(RuntimeError):
            shortlist(self.screen,self.manifest)
        self.screen["best_unconfirmed_by_legend"][5]["kind"]="rune"
        self.screen["best_unconfirmed_by_legend"][5]["legend"]="Legend 04"
        with self.assertRaises(RuntimeError):
            shortlist(self.screen,self.manifest)

    def test_holdout_opponents_exclude_training_and_fresh_seeds(self):
        ranked=[{"legend":n} for n in self.names]
        training,held,cases=opponent_panel("Legend 00",ranked,202611261230,2)
        self.assertEqual(len(training),2)
        self.assertEqual(len(held),6)
        self.assertFalse(set(training)&set(held))
        self.assertEqual(len(cases),24)
        self.assertEqual(len({x["seed"] for x in cases}),24)
        self.assertEqual(cases,opponent_panel("Legend 00",ranked,202611261230,2)[2])
        self.assertEqual({x["seat"] for x in cases},{0,1})

    def test_necessary_multiple_testing_correction(self):
        records=[{"legend":str(i),"changed":True,"incomplete":0,
                  "mcnemar_p":mcnemar_exact(i+1,0),
                  "candidate_wins":i+1,"baseline_wins":0}
                 for i in range(FAMILY)]
        holm(records)
        self.assertEqual(len(records),FAMILY)
        self.assertTrue(all(0<=x["holm_adjusted_p"]<=1 for x in records))
        self.assertFalse(any(x["independently_confirmed"] for x in records[:2]))


if __name__=="__main__":
    unittest.main()
