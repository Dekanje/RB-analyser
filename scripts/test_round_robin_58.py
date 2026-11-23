#!/usr/bin/env python3
"""Pure-Python tests for all 58 optimized pairings, both seats and final rank audit."""
import collections
import json
import pathlib
import sys
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import round_robin_58 as rr


class RoundRobinTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)
        self.names=[f"Legend {i:02d}" for i in range(58)]
        self.decks={}
        for name in self.names:
            path=self.root/(name.replace(" ","_")+".txt")
            path.write_text(name,encoding="utf8")
            self.decks[name]=path
        self.manifest={name:{"selected":i%2==0} for i,name in enumerate(self.names)}

    def test_schedule_all_pairs_and_each_seat_exactly_once(self):
        scenarios=list(rr.pair_schedule(self.decks))
        self.assertEqual(len(scenarios),58*57)
        self.assertEqual(len({(s["a"],s["b"],s["seat"]) for s in scenarios}),len(scenarios))
        self.assertEqual(len({(s["a"],s["b"]) for s in scenarios}),58*57//2)
        self.assertTrue(all(s["a"]<s["b"] for s in scenarios))
        count=collections.Counter()
        for s in scenarios:
            count[s["a"]]+=1;count[s["b"]]+=1
        self.assertEqual(set(count.values()),{114})
        self.assertEqual(len({s["seed"] for s in scenarios}),len(scenarios))

    def test_shards_cover_exactly_one_of_every_pair_seat(self):
        master={(s["a"],s["b"],s["seat"],s["seed"]) for s in rr.pair_schedule(self.decks)}
        shards=[list(rr.pair_schedule(self.decks,i,29)) for i in range(29)]
        self.assertEqual(sum(len(s) for s in shards),3306)
        actual={(s["a"],s["b"],s["seat"],s["seed"]) for rows in shards for s in rows}
        self.assertEqual(master,actual)
        self.assertEqual(len(actual),3306)

    def test_aggregate_58_complete_round_robin(self):
        inroot=self.root/"shards"
        seed=2026112399193
        for shard in range(29):
            rows=[]
            for s in rr.pair_schedule(self.decks,shard,29,1,seed):
                rows.append({**s,"complete":True,"status":"complete","winner":"a",
                             "a_sha256":rr.sha(self.decks[s["a"]]),
                             "b_sha256":rr.sha(self.decks[s["b"]])})
            folder=inroot/f"optimized-round-robin-shard-{shard}"
            folder.mkdir(parents=True)
            (folder/"round_robin.json").write_text(json.dumps({
                "shard":shard,"shards":29,"repetitions":1,
                "expected_scenarios":len(rows),
                "completed_scenarios":len(rows),"scenario_results":rows
            }))
        args=SimpleNamespace(selected=self.root,input=inroot,output=self.root/"results",
                             shards=29,repetitions=1,seed=seed,agent="ismcts:sims=24")
        with patch.object(rr,"load_decks",return_value=(self.decks,self.manifest)):
            rr.aggregate(args)
        result=json.loads((args.output/"summary.json").read_text())
        self.assertEqual(result["total_engine_bo3_series"],3306)
        ranked=json.loads((args.output/"all_58_ranked.json").read_text())
        self.assertEqual(len(ranked),58)
        self.assertEqual({row["played"] for row in ranked},{114})
        self.assertEqual({len(row["against_57"]) for row in ranked},{57})
        self.assertEqual(sum(row["wins"] for row in ranked),3306)
        self.assertEqual({row["rank_exploratory"] for row in ranked},set(range(1,59)))
        self.assertTrue((args.output/"all_58_ranked.csv").is_file())

    def test_wilson_interval_does_not_claim_certainty(self):
        self.assertEqual(rr.wilson(0,0),(None,None))
        low,high=rr.wilson(60,114)
        self.assertLess(low,60/114)
        self.assertGreater(high,60/114)


if __name__=="__main__":
    unittest.main(verbosity=2)
