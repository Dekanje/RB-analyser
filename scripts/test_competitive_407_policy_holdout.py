#!/usr/bin/env python3
"""BO3 policy heldout provenance tests, isolated from game engine binary."""
import argparse
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from competitive_407_policy_holdout import cases_for,test_one,aggregate


class HoldoutSourceIsolationTests(unittest.TestCase):
    def test_unique_seed_and_alternated_source_seat(self):
        a=cases_for("Draven, Glorious Executioner","Miss Fortune, Bounty Hunter",2,7)
        b=cases_for("Draven, Glorious Executioner","Rek'Sai, Void Burrower",2,7)
        self.assertEqual(len(a),4)
        self.assertEqual([r["seat"] for r in a],[0,0,1,1])
        self.assertFalse(set(r["seed"] for r in a)&set(r["seed"] for r in b))
        self.assertEqual(a,cases_for("Draven, Glorious Executioner",
                                      "Miss Fortune, Bounty Hunter",2,7))

    def test_three_independent_candidates_and_corrupted_receipt(self):
        names=["Draven, Glorious Executioner","LeBlanc, Deceiver",
               "Master Yi, Wuju Bladesman"]
        enemies=["Miss Fortune, Bounty Hunter","Rek'Sai, Void Burrower",
                 "Ambessa, Matriarch of War"]
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            decks={}
            for n in names+enemies:
                deck=root/(n.replace(" ","_")+".txt")
                deck.write_text(n)
                decks[n]=deck
            choices=[{
                "legend":names[i],
                "source_matchup":["draven-vs-miss-fortune","leblanc-vs-reksai",
                                  "masteryi-vs-ambessa"][i],
                "policy_index":i,
                "plan":{"swaps":[{"main_out":"Old","side_in":"New","copies":1}]},
                "loser_chooses_start":"self",
                "opponents":[enemies[i],enemies[(i+1)%3]],
            } for i in range(3)]
            selection={
                "choices":choices,"hypotheses":3,"schema":1
            }
            args=argparse.Namespace(
                selection=root/"selection.json",pilot=root/"pilot.json",
                selected=root,registry=root/"registry.json",
                engine=root/"riftbound",input=root/"shards",output=root/"out",
                agent="ismcts:sims=128",repetitions=2,seed=202611250531,
                index=0,timeout=20
            )
            args.engine.write_bytes(b"test only")
            args.selection.write_text(json.dumps(selection))
            args.pilot.write_text("{}")
            args.registry.write_text("{}")
            def fake_play(engine,own,enemy,db,option,case,agent,timeout):
                is_new=bool(option["plan"])
                return {
                    "seat":case["seat"],"rep":case["rep"],
                    "seed":case["seed"],
                    "target_win":int(case["rep"]==0 or is_new),
                    "game1_winner_seat":1,
                    "forced_start_receipts":[{
                        "game":2,"loser":2,"chosen":"self",
                        "requested":2,"actual":2
                    }],
                }
            with patch("competitive_407_policy_holdout.load_inputs",
                       return_value=(selection,{},decks,{})):
                with patch("competitive_407_policy_holdout.play",
                           side_effect=fake_play):
                    for i in range(3):
                        args.index=i
                        args.output=args.input/f"competitive-407-policy-holdout-{i}"
                        test_one(args)
                args.output=root/"combined"
                aggregate(args)
                report=json.loads((args.output/"decision.json").read_text())
                self.assertEqual(report["hypotheses_tested"],3)
                self.assertEqual(report["completed_paired_bo3"],24)
                self.assertEqual(report["statistically_positive"],0)
                self.assertFalse(report["sideboard_policies_automatically_adopted"])
                shard=args.input/"competitive-407-policy-holdout-0"/"holdout.json"
                payload=json.loads(shard.read_text())
                payload["cases"][0]["candidate_407_receipts"][0]["actual"]=1
                shard.write_text(json.dumps(payload))
                with self.assertRaises(RuntimeError):
                    aggregate(args)


if __name__=="__main__":
    unittest.main()
