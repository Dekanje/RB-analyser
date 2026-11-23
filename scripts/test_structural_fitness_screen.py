#!/usr/bin/env python3
"""Prevent inflated structural fitness claims and unmatched candidate seeds."""
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from structural_fitness_screen import schedule,score,opponents_for,FITNESS_KINDS


class StructuralFitnessTests(unittest.TestCase):
    def test_two_opponents_both_seats_reproducible_and_self_excluded(self):
        ranked=[{"legend":f"Legend {i:02d}"} for i in range(58)]
        scenarios=schedule("Legend 00",ranked,2026)
        self.assertEqual(len(scenarios),4)
        self.assertEqual([x["opponent"] for x in scenarios],
                         ["Legend 01","Legend 01","Legend 02","Legend 02"])
        self.assertEqual([x["seat"] for x in scenarios],[0,1,0,1])
        self.assertEqual(len(set(x["seed"] for x in scenarios)),4)
        self.assertEqual(scenarios,schedule("Legend 00",ranked,2026))
        self.assertNotEqual(scenarios,schedule("Legend 00",ranked,2027))
        self.assertNotIn("Legend 00",opponents_for("Legend 00",ranked))

    def test_exact_paired_win_difference_and_no_imputation(self):
        paired=[
            {"baseline_win":0,"candidate_win":1},
            {"baseline_win":1,"candidate_win":1},
            {"baseline_win":0,"candidate_win":0},
            {"baseline_win":0,"candidate_win":1},
        ]
        result=score(paired)
        self.assertEqual(result["delta"],2)
        self.assertEqual(result["candidate_wins"],3)
        self.assertEqual(result["baseline_wins"],1)
        self.assertEqual(result["mcnemar_p_unadjusted"],0.5)
        with self.assertRaises(RuntimeError):
            score(paired[:-1]+[{"baseline_win":None,"candidate_win":0}])

    def test_sideboard_not_scored_as_game_one_fitness(self):
        self.assertNotIn("sideboard",FITNESS_KINDS)
        self.assertEqual(set(FITNESS_KINDS),{"rune","battlefield","champion"})


if __name__=="__main__":
    unittest.main()
