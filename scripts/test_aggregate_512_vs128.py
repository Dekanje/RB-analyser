#!/usr/bin/env python3
"""512-vs-128 mirrored agent quality validation without compiled engine."""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from aggregate_512_vs128 import PANEL,pool
from benchmark_agent_strength import stable_seed,sha256


class Agent512StrengthAggregationTests(unittest.TestCase):
    def test_all_six_decks_required_and_engine_receipts(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            inp=root/"inputs";decks=root/"decks"
            inp.mkdir();decks.mkdir()
            engine=root/"riftbound";engine.write_bytes(b"synthetic engine bytes")
            for index,filename in enumerate(PANEL):
                deck=decks/filename
                deck.write_text("synthetic-deck "+filename)
                records=[]
                for rep in range(2):
                    for challenger_first in (True,False):
                        winner_seat=1 if challenger_first else 2
                        records.append({
                            "status":"complete","deck_file":filename,
                            "deck_sha256":sha256(deck),"repetition":rep,
                            "seed":stable_seed(202611250900,filename,rep),
                            "challenger_first":challenger_first,
                            "challenger_win":True,"winner_seat":winner_seat,
                        })
                packet={
                    "summary":{
                        "engine_sha256":sha256(engine),
                        "baseline_agent":"ismcts:sims=128",
                        "challenger_agent":"ismcts:sims=512",
                        "decks_tested":1,
                        "repetitions_per_deck":2,
                        "mirrored_agent_seating":True,
                        "identical_deck_on_both_sides":True,
                        "failed_games":0,"completed_games":4,
                        "conclusion":"SAMPLED_ONLY",
                        "challenger_wins":4,
                    },
                    "by_deck":[{"deck_file":filename}],
                    "games":records,
                }
                folder=inp/f"agent-strength-512-{index}"
                folder.mkdir()
                (folder/"strength.json").write_text(json.dumps(packet))
            result=pool(inp,decks,engine,202611250900,2)
            self.assertEqual(result["completed_real_engine_games"],24)
            self.assertEqual(result["512_wins"],24)
            self.assertTrue(result["512_strength_signal_significant"])
            self.assertTrue(result["no_decks_optimized_or_promoted"])
            target=inp/"agent-strength-512-0"/"strength.json"
            packet=json.loads(target.read_text())
            packet["games"][1]["seed"]+=1
            target.write_text(json.dumps(packet))
            with self.assertRaises(RuntimeError):
                pool(inp,decks,engine,202611250900,2)


if __name__=="__main__":
    unittest.main()
