#!/usr/bin/env python3
"""Frozen 12-legend actual-sideboard-policy holdout integrity tests."""
import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sideboard_128_holdout import FAMILY,OPPONENTS_HELD_OUT,cases,shortlist,native_match


class ActualSideboardPolicyHoldoutTests(unittest.TestCase):
    def test_family_is_frozen_one_per_legend_selected_by_positive_delta(self):
        names=[f"Legend {i:02d}" for i in range(15)]
        manifest={"records":[]}
        screen={"best_unconfirmed_by_legend":[]}
        evidence={}
        for i,name in enumerate(names):
            h=f"sha_{i:02d}"
            manifest["records"].append({"legend":name,"variants":[{
                "sha256":h,"kind":"sideboard","changes":{"in":f"Tech {i}"},
            }]})
            score={"delta":3 if i%2 else 2,"candidate_wins":3}
            screen["best_unconfirmed_by_legend"].append({
                "legend":name,"candidate_sha256":h,"score":score
            })
            evidence[name]={"sideboard_proposals":[{
                "candidate_sha256":h,"path":f"legend{i}.txt",
                "sideboard_added_card":f"Tech {i}",
                "registered_original_sha256":f"base_{i}",
                "score":score,
                "baseline_policy":{"plan":{"swaps":[]}},
                "candidate_policy":{"plan":{"swaps":[]}},
            }]}
        got=shortlist(screen,evidence,manifest)
        self.assertEqual(len(got),FAMILY)
        self.assertEqual(len({r["legend"] for r in got}),FAMILY)
        self.assertTrue(all(r["source_screen_delta"]>0 for r in got))
        self.assertEqual([r["index"] for r in got],list(range(FAMILY)))
        self.assertEqual(got[0]["source_screen_delta"],3)
        screen["best_unconfirmed_by_legend"][0]["score"]["delta"]=99
        with self.assertRaises(RuntimeError):
            shortlist(screen,evidence,manifest)

    def test_independent_opponents_seats_and_seeds(self):
        ranked=[{"legend":f"Legend {i}"} for i in range(12)]
        training,held,tests=cases("Legend 0",ranked,456,2)
        self.assertEqual(len(training),2)
        self.assertEqual(len(held),OPPONENTS_HELD_OUT)
        self.assertFalse(set(training)&set(held))
        self.assertEqual(len(tests),24)
        self.assertEqual(len({x["seed"] for x in tests}),24)
        self.assertEqual(set(x["seat"] for x in tests),{0,1})

    def test_actual_cpp_407_swaps_and_receipts_mandatory(self):
        plan={"swaps":[{"main_out":"Card A","side_in":"Card B","copies":1}]}
        row={"plan":plan}
        native={
            "status":"COMPLETE_RULE407_START_POLICY_BO3",
            "rule_407_4_start_choice_verified":True,
            "winner":1,
            "sideboarding_applied":True,
            "source_decks_return_to_registered_state_next_match":True,
            "games":[
                {"game":1,"winner_seat":1,"sideboard_swaps":[[],[]]},
                {"game":2,"winner_seat":1,"sideboard_swaps":[plan["swaps"],[]],
                 "engine_status":"complete",
                 "forced_start_verified":True,
                 "expected_engine_starting_seat":2,
                 "verified_engine_starting_seat":2}
            ]
        }
        a=SimpleNamespace(engine=pathlib.Path("engine"),agent="random",timeout=3)
        sample={"opponent":"Legend 3","seat":0,"seed":126,"repeat":1}
        with patch("sideboard_128_holdout.run_series",return_value=native) as mocked:
            r=native_match(a,pathlib.Path("candidate"),pathlib.Path("opponent"),
                           row,sample,{})
        self.assertEqual(r["win"],1)
        self.assertEqual(r["swapped_games"],1)
        self.assertEqual(mocked.call_args.args[1],pathlib.Path("candidate"))
        native["games"][1]["sideboard_swaps"]=[[],[]]
        with patch("sideboard_128_holdout.run_series",return_value=native):
            with self.assertRaises(RuntimeError):
                native_match(a,pathlib.Path("candidate"),
                             pathlib.Path("opponent"),row,sample,{})


if __name__=="__main__":
    unittest.main()
