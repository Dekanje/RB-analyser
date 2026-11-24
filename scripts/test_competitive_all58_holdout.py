#!/usr/bin/env python3
"""Holdout isolation and multiple-test decision invariants."""
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from competitive_all58_holdout import opponent_split
from full_field_58 import holm


class WorldsCandidateHoldoutTests(unittest.TestCase):
    def test_training_and_holdout_are_disjoint_and_exclude_self(self):
        names=["Draven, Glorious Executioner", "Rek'Sai, Void Burrower"]+[
            f"Other Legend {n}" for n in range(15)
        ]
        ranked=[{"legend":n} for n in names]
        originals={n:n for n in names}
        training,held=opponent_split(names[0],ranked,originals)
        self.assertEqual(training,names[1:4])
        self.assertEqual(list(held),names[4:10])
        self.assertFalse(set(training)&set(held))
        self.assertNotIn(names[0],held)
        training2,held2=opponent_split("Other Legend 03",ranked,originals)
        self.assertFalse(set(training2)&set(held2))
        self.assertNotIn("Other Legend 03",held2)

    def test_holm_does_not_accept_favorable_but_inconclusive_samples(self):
        # Simulate 12 hypotheses with modest apparent advantages.
        rows=[{
            "legend":f"L{i}", "changed":True,
            "incomplete":0,"candidate_wins":14,
            "baseline_wins":11,"mcnemar_p":0.11
        } for i in range(12)]
        holm(rows)
        self.assertTrue(all(x["independently_confirmed"] is False for x in rows))
        self.assertTrue(all(x["holm_adjusted_p"]==1.0 for x in rows))

    def test_holm_can_accept_exceptionally_clear_signal(self):
        rows=[{
            "legend":f"L{i}", "changed":True, "incomplete":0,
            "candidate_wins":24 if i==0 else 13,
            "baseline_wins":0 if i==0 else 11,
            "mcnemar_p":0.00001 if i==0 else 0.2
        } for i in range(12)]
        holm(rows)
        self.assertTrue(rows[0]["independently_confirmed"])
        self.assertTrue(all(not x["independently_confirmed"] for x in rows[1:]))


if __name__=="__main__":
    unittest.main()
