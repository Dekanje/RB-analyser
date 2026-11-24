#!/usr/bin/env python3
"""Exact Swiss PMF and sampled meta uncertainty tests."""
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from worlds_swiss_sensitivity import binomial_three,swiss_record_tail,evaluate


class SwissSensitivityTests(unittest.TestCase):
    def test_exact_nine_round_win_tail(self):
        self.assertAlmostEqual(sum(binomial_three(.5)),1.)
        self.assertAlmostEqual(swiss_record_tail(.5,.5,.5,7),46/512)
        self.assertAlmostEqual(swiss_record_tail(.5,.5,.5,6),130/512)
        self.assertAlmostEqual(swiss_record_tail(1,1,1,9),1.)
        self.assertAlmostEqual(swiss_record_tail(0,0,0,1),0.)
        self.assertAlmostEqual(swiss_record_tail(0,0,0,0),1.)
        with self.assertRaises(ValueError):
            swiss_record_tail(.5,.6,1.1,7)
        with self.assertRaises(ValueError):
            swiss_record_tail(.5,.6,.7,10)

    def test_sampled_field_reproducible_no_event_win_claim(self):
        dom={"A":{"fury","chaos"},"B":{"order","mind"},"C":{"body","calm"}}
        anchors=[f"Anchor{i}" for i in range(10)]
        outcomes={(n,o):.5 for n in dom for o in anchors}
        a=evaluate(outcomes,dom,anchors,50,1.,123)
        b=evaluate(outcomes,dom,anchors,50,1.,123)
        self.assertEqual(a,b)
        self.assertEqual(len(a),1)
        row=a[0]
        self.assertEqual(row["illustrative_seven_win_rank"],1)
        self.assertEqual(len(row["lineup"]),3)
        for threshold in (6,7,8):
            rate=row[f"model_probability_at_least_{threshold}_wins_mean"]
            self.assertTrue(0<=rate<=1)
        self.assertGreaterEqual(
            row["model_probability_at_least_6_wins_mean"],
            row["model_probability_at_least_7_wins_mean"])
        self.assertGreaterEqual(
            row["model_probability_at_least_7_wins_mean"],
            row["model_probability_at_least_8_wins_mean"])
        with self.assertRaises(ValueError):
            evaluate(outcomes,dom,anchors,10,1.,123)


if __name__=="__main__":
    unittest.main()
