#!/usr/bin/env python3
"""Three-matchup cross-artifact integrity tests without engine dependency."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from aggregate_worlds_sideboard import aggregate,MATCHUPS


class WorldsSideboardAggregateTests(unittest.TestCase):
    def test_exact_three_artifacts_and_bad_receipt_fail_closed(self):
        with tempfile.TemporaryDirectory() as td:
            folder=pathlib.Path(td)
            for key,(legend,opponent) in MATCHUPS.items():
                d=folder/f"competitive-worlds-sideboard-{key}"
                d.mkdir()
                cases=[]
                for seat in (0,1):
                    for rep in (0,1):
                        cases.append({"seat":seat,"rep":rep,
                                      "seed":seat*100+rep,
                                      "target_win":int(seat==0),
                                      "forced_start_receipts":[{"game":2,"requested":1,"actual":1}]})
                payload={
                    "status":"SINGLE_MATCHUP_STRATEGIC_BO3_POLICY_SCREEN_ONLY",
                    "legend":legend,"opponent":opponent,
                    "any_deck_changes_adopted":False,
                    "loser_chooses_first_verified":True,
                    "baseline_completed_series":4,
                    "candidate_completed_series":4,
                    "search_candidates":1,
                    "engine_sha256":"pinned-cpp-sha",
                    "deck_sha256":"deck","opponent_sha256":"opponent",
                    "baseline_games":cases,
                    "candidate_results":[{
                        "candidate_index":0,"paired_series":4,
                        "status":"EXPLORATORY_NO_HOLDOUT",
                        "baseline_wins":2,"candidate_wins":2,
                        "delta":0,"mcnemar_p_unadjusted":1.,
                        "option":{"plan":{},"loser_chooses_start":"self"},
                        "cases":cases,
                    }]
                }
                (d/"sideboard_policy_screen.json").write_text(json.dumps(payload))
            report,rows=aggregate(folder)
            self.assertEqual(report["total_candidate_policies"],3)
            self.assertEqual(report["matchups"],3)
            self.assertEqual(report["confirmed_improvements"],0)
            self.assertFalse(report["independent_holdout_performed"])
            broken=folder/"competitive-worlds-sideboard-draven-vs-miss-fortune"/"sideboard_policy_screen.json"
            payload=json.loads(broken.read_text())
            payload["candidate_results"][0]["cases"][0]["forced_start_receipts"][0]["actual"]=2
            broken.write_text(json.dumps(payload))
            with self.assertRaises(RuntimeError):
                aggregate(folder)


if __name__=="__main__":
    unittest.main()
