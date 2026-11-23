#!/usr/bin/env python3
"""Reproducible and no-Worlds-probability tests for robust lineup sampling."""
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from worlds_robust_lineups import evaluate_robustness,quantile


class WorldsRobustnessTest(unittest.TestCase):
    def test_quantile_and_meta_uncertainty_sampling(self):
        self.assertEqual(quantile([1,2,3],0.5),2)
        self.assertAlmostEqual(quantile([0,10],0.1),1)
        domains={
            "A":{"fury","chaos"},
            "B":{"mind","order"},
            "C":{"calm","body"},
            "D":{"mind","body"},
            "E":{"chaos","calm"},
        }
        anchors=[f"Anchor{i}" for i in range(10)]
        values={"A":1.0,"B":0.5,"C":0.5,"D":0.0,"E":0.5}
        outcomes={(name,a):values[name] for name in domains for a in anchors}
        rows=evaluate_robustness(outcomes,domains,anchors,50,1.,27)
        same=evaluate_robustness(outcomes,domains,anchors,50,1.,27)
        self.assertEqual(rows,same)
        self.assertGreaterEqual(len(rows),1)
        for row in rows:
            self.assertEqual(len(set.union(*(domains[n] for n in row["lineup"]))),6)
            self.assertLessEqual(row["swiss_expected_wins_p10"],
                                 row["swiss_expected_wins_p50"])
            self.assertLessEqual(row["swiss_expected_wins_p50"],
                                 row["swiss_expected_wins_p90"])
            self.assertGreaterEqual(row["swiss_expected_wins_mean"],0)
            self.assertLessEqual(row["swiss_expected_wins_mean"],9)
        self.assertEqual(rows[0]["robust_swiss_rank"],1)

    def test_invalid_observed_matchup_or_world_configuration_fails(self):
        domains={"A":{"fury","chaos"},"B":{"mind","order"},
                 "C":{"calm","body"}}
        anchors=[f"Anchor{i}" for i in range(10)]
        outcomes={(n,a):0.5 for n in domains for a in anchors}
        outcomes["A","Anchor0"]=0.75
        with self.assertRaises(RuntimeError):
            evaluate_robustness(outcomes,domains,anchors,40,1.,1)
        with self.assertRaises(ValueError):
            evaluate_robustness(outcomes,domains,anchors,10,1.,1)


if __name__=="__main__":
    unittest.main()
