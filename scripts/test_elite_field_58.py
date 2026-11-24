#!/usr/bin/env python3
"""Synthetic strict-evidence tests for 58-Legend elite-opponent screening."""
import argparse
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from elite_field_58 import aggregate, roster, schedule
from round_robin_58 import sha


class EliteField58Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root=pathlib.Path(tmp.name)
        self.selected=self.root/"selected"
        card_dir=self.selected/"selected_decks"
        card_dir.mkdir(parents=True)
        rows=[];trials=[]
        for i in range(58):
            name=f"Legend {i:02d}"
            path=card_dir/f"legend_{i:02d}.txt"
            path.write_text(f"Legend:\n1 {name}\n")
            h=sha(path)
            rows.append({"legend":name,"rank_exploratory":i+1,
                         "deck_sha256":h})
            trials.append({"legend":name,"effective_sha256":h})
        self.ranked=self.root/"ranked.json"
        self.ranked.write_text(json.dumps(rows))
        (self.selected/"all_58_trials.json").write_text(json.dumps(trials))

    def test_full_sharded_schedule(self):
        targets,anchors,_=roster(self.selected,self.ranked,10)
        full=list(schedule(targets,anchors,0,1,1,42))
        shards=sum(len(list(schedule(targets,anchors,s,29,1,42)))
                   for s in range(29))
        self.assertEqual(len(full),1140)
        self.assertEqual(shards,len(full))
        self.assertEqual(len(set((x["target"],x["anchor"],x["seat"],
                                  x["repetition"]) for x in full)),1140)
        self.assertTrue(all(x["target"]!=x["anchor"] for x in full))

    def write_shards(self):
        targets,anchors,rows=roster(self.selected,self.ranked,10)
        dirname=self.root/"shards"
        for shard in range(29):
            scenarios=[]
            for row in schedule(targets,anchors,shard,29,1,42):
                scenarios.append({**row,"status":"complete","complete":True,
                                  "target_win":row["seat"]==0,
                                  "target_sha256":sha(targets[row["target"]]),
                                  "anchor_sha256":sha(anchors[row["anchor"]])})
            path=dirname/f"elite-58-shard-{shard}"
            path.mkdir(parents=True)
            packet={
                "shard":shard,"shards":29,"repetitions":1,"anchors":10,
                "anchor_names":[r["legend"] for r in rows],
                "source_sha256":sha(self.ranked),"engine_sha256":"pinnedhash",
                "agent":"ismcts:sims=128","seed":42,"sideboarding":False,
                "expected":len(scenarios),"finished":len(scenarios),
                "scenarios":scenarios
            }
            (path/"shard.json").write_text(json.dumps(packet))
        return dirname

    def test_fail_closed_full_58_aggregation(self):
        dirs=self.write_shards()
        args=argparse.Namespace(selected=self.selected, ranked=self.ranked,
              anchors=10,shards=29,repetitions=1,seed=42,
              agent="ismcts:sims=128",input=dirs,output=self.root/"results")
        aggregate(args)
        meta=json.loads((args.output/"summary.json").read_text())
        self.assertEqual(meta["completed_bo3_series"],1140)
        self.assertEqual(meta["legends"],58)
        ranked=json.loads((args.output/"standings.json").read_text())
        self.assertEqual(len(ranked),58)
        self.assertEqual({r["series"] for r in ranked},{18,20})
        self.assertTrue(all(r["win_rate"]==0.5 for r in ranked))
        file=dirs/"elite-58-shard-0"/"shard.json"
        packet=json.loads(file.read_text())
        packet["scenarios"][0]["target_win"]=None
        file.write_text(json.dumps(packet))
        with self.assertRaises(RuntimeError):
            aggregate(args)


if __name__=="__main__":
    unittest.main()
