#!/usr/bin/env python3
"""Tests for theoretical Worlds lineup compatibility and uncertainty labeling."""
import pathlib
import sys
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from worlds_lineups import compatible_triples, rank_lineups


class WorldsLineupsTest(unittest.TestCase):
    def test_exact_six_unique_domains(self):
        domains={
            "A": {"fury","chaos"},
            "B": {"mind","order"},
            "C": {"calm","body"},
            "D": {"fury","body"},
            "E": {"order","chaos"},
        }
        got=compatible_triples(domains)
        self.assertIn(("A","B","C"),got)
        for trio in got:
            coverage=set().union(*(domains[n] for n in trio))
            self.assertEqual(len(coverage),6)

    def test_bootstrap_and_playoff_sensitivity(self):
        anchors=[f"Opponent{i}" for i in range(10)]
        domains={
            "A":{"fury","chaos"},
            "B":{"mind","order"},
            "C":{"calm","body"},
            "D":{"fury","body"},
        }
        rates={"A":0.8,"B":0.7,"C":0.6,"D":0.2}
        results={(n,a):rates[n] for n in domains for a in anchors}
        lineups=rank_lineups(results,domains,anchors,100,42)
        self.assertEqual(lineups[0]["legends"],["A","B","C"])
        self.assertEqual(lineups[0]["playoff_candidate"],"A")
        self.assertAlmostEqual(lineups[0]["exploratory_swiss_expected_wins"],6.3)
        self.assertAlmostEqual(lineups[0]["bootstrap_best_lineup_frequency"],1)
        self.assertGreaterEqual(lineups[0]["lowest_member_match_rate"],0.6)


if __name__=="__main__":
    unittest.main()
