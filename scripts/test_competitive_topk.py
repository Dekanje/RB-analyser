#!/usr/bin/env python3
"""Synthetic provenance and fail-closed tests for stronger-agent top-K league."""
import argparse
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from competitive_topk import aggregate, expected_schedule, select_topk
from round_robin_58 import pair_schedule, sha


class CompetitiveTopKTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = pathlib.Path(self.temp.name)
        self.selected = self.root / "selected"
        deck_dir = self.selected / "selected_decks"
        deck_dir.mkdir(parents=True)
        self.decks = {}
        self.rows = []
        trials = []
        for index in range(58):
            legend = f"Test Legend {index:02d}"
            path = deck_dir / f"test_{index:02d}.txt"
            path.write_text(f"Legend:\n1 {legend}\n", encoding="utf-8")
            h = sha(path)
            self.decks[legend] = path
            self.rows.append({
                "legend": legend, "rank_exploratory": index+1,
                "deck_sha256": h
            })
            trials.append({"legend": legend, "effective_sha256": h})
        (self.selected / "all_58_trials.json").write_text(json.dumps(trials))
        self.ranked = self.root / "ranked.json"
        self.ranked.write_text(json.dumps(self.rows), encoding="utf-8")

    def test_selection_requires_untampered_58_roster(self):
        selected, ordered = select_topk(self.selected, self.ranked, 4)
        self.assertEqual(len(selected), 4)
        self.assertEqual(list(selected), [x["legend"] for x in self.rows[:4]])
        path = self.decks[self.rows[3]["legend"]]
        path.write_text(path.read_text() + "tamper")
        with self.assertRaises(RuntimeError):
            select_topk(self.selected, self.ranked, 4)

    def test_pair_schedule_all_seats_and_seeds(self):
        subset = {name: self.decks[name] for name in list(self.decks)[:4]}
        schedule = expected_schedule(subset, 2, 123)
        self.assertEqual(len(schedule), 4*3//2*2*2)
        self.assertEqual(len(set(schedule)), len(schedule))
        for a in subset:
            for b in subset:
                if a >= b:
                    continue
                for rep in (0, 1):
                    self.assertIn((a, b, 0, rep), schedule)
                    self.assertIn((a, b, 1, rep), schedule)
                    self.assertNotEqual(schedule[(a,b,0,rep)],
                                        schedule[(a,b,1,rep)])

    def fake_shards(self):
        chosen, included = select_topk(self.selected, self.ranked, 4)
        folder = self.root / "shards"
        for shard in range(2):
            rows = []
            for s in pair_schedule(chosen, shard, 2, 2, 123):
                rows.append({**s, "complete": True, "status": "complete",
                             "winner": "a" if s["seat"] == 0 else "b",
                             "a_sha256": sha(chosen[s["a"]]),
                             "b_sha256": sha(chosen[s["b"]])})
            path = folder / f"competitive-topk-shard-{shard}"
            path.mkdir(parents=True)
            (path / "shard.json").write_text(json.dumps({
                "top": 4, "shard": shard, "shards": 2, "repetitions": 2,
                "seed": 123, "agent": "ismcts:sims=128",
                "selected_source_sha256": sha(self.ranked),
                "selected_legends": [r["legend"] for r in included],
                "engine_sha256": "same_binary", "sideboard_swaps": False,
                "expected": len(rows), "complete": len(rows), "results": rows
            }))
        return folder

    def test_aggregation_and_corruption_gate(self):
        folders = self.fake_shards()
        options = argparse.Namespace(selected=self.selected, ranked=self.ranked,
                                     top=4, repetitions=2, seed=123, shards=2,
                                     input=folders, output=self.root / "results",
                                     agent="ismcts:sims=128")
        aggregate(options)
        summary = json.loads((options.output / "summary.json").read_text())
        self.assertEqual(summary["total_completed_bo3_series"], 24)
        self.assertFalse(summary["sideboarding"])
        standings = json.loads((options.output / "standings.json").read_text())
        self.assertEqual(len(standings), 4)
        self.assertTrue(all(x["series"] == 12 for x in standings))
        path = folders / "competitive-topk-shard-0" / "shard.json"
        packet = json.loads(path.read_text())
        packet["results"][0]["complete"] = False
        path.write_text(json.dumps(packet))
        with self.assertRaises(RuntimeError):
            aggregate(options)


if __name__ == "__main__":
    unittest.main()
