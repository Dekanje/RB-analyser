#!/usr/bin/env python3
"""No-engine provenance checks for all-58 multi-candidate paired exploration."""
import argparse
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from competitive_all58_candidates import (
    aggregate,anchor_names,schedule,score,select_indices
)
from round_robin_58 import sha


class All58EvolutionTests(unittest.TestCase):
    def test_stratified_predeclared_indices(self):
        self.assertEqual(select_indices(list(range(40)),4),[0,10,20,30])
        self.assertEqual(select_indices(list(range(40)),1),[0])
        self.assertEqual(select_indices(list(range(40)),40),list(range(40)))
        with self.assertRaises(ValueError):
            select_indices(list(range(40)),41)

    def test_mirrors_are_distinct_and_self_is_excluded(self):
        ranked=[{"legend":f"Legend {n:02d}"} for n in range(58)]
        games=schedule("Legend 00",ranked,3,2026)
        self.assertEqual(len(games),6)
        self.assertEqual([x["opponent"] for x in games[::2]],
                         ["Legend 01","Legend 02","Legend 03"])
        self.assertEqual([x["seat"] for x in games],[0,1]*3)
        self.assertEqual(len({x["seed"] for x in games}),6)

    def test_paired_mcnemar_scores_only_completions(self):
        values=[
            {"baseline_win":0,"candidate_win":1},
            {"baseline_win":0,"candidate_win":1},
            {"baseline_win":0,"candidate_win":1},
            {"baseline_win":0,"candidate_win":0},
            {"baseline_win":1,"candidate_win":1},
            {"baseline_win":1,"candidate_win":1},
        ]
        calculated=score(values)
        self.assertEqual(calculated["delta"],3)
        self.assertEqual(calculated["mcnemar_p_unadjusted"],0.25)

    def test_58_shard_aggregation_rejects_missing_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            originals={}; records={}; ranked=[]
            proposals=root/"proposals"; proposals.mkdir()
            (proposals/"manifest.json").write_text('{"verified":false}')
            ranked_file=root/"ranked.json"
            ranked_file.write_text('[]')
            for i in range(58):
                name=f"Legend {i:02d}"
                source=root/f"original_{i:02d}.txt"
                prefix=f"Legend:\n1 {name}\n\nChampion:\n1 Champion\n\nMainDeck:\n"
                suffix="\nBattlefields:\n1 A\n1 B\n1 C\n\nRunes:\n12 Rune\n\nSideboard:\n"
                source.write_text(prefix+"39 Base\n"+suffix)
                originals[name]=source
                ranked.append({"legend":name})
                candidates=[]
                for n in range(40):
                    path=proposals/f"candidate_{i:02d}_{n:02d}.txt"
                    path.write_text(prefix+f"36 Base\n3 New {n}\n"+suffix)
                    candidates.append({"sha256":sha(path),
                                       "path":path.name,"changed_main_slots":3,
                                       "mutation_steps":[]})
                records[name]={"candidates":candidates}
            dirs=root/"shards"
            for shard in range(29):
                expected_names=[n for i,n in enumerate(sorted(originals))
                                if i%29==shard]
                processed=[]
                for name in expected_names:
                    games=schedule(name,ranked,3,42)
                    output=[]
                    for n in (0,10,20,30):
                        samples=[
                            {**x,"baseline_win":int(x["seat"]==0),
                             "candidate_win":int(x["seat"]==1),
                             "baseline_complete":True,"candidate_complete":True}
                            for x in games
                        ]
                        row=records[name]["candidates"][n]
                        output.append({
                            "candidate_index":n,"candidate_path":row["path"],
                            "candidate_sha256":row["sha256"],"changed_main_slots":3,
                            "status":"COMPLETED_SCREENING_ONLY",
                            "paired_completed":6,"paired_scenarios":samples,
                            "score":score(samples)
                        })
                    processed.append({
                        "legend":name,"source_sha256":sha(originals[name]),
                        "opponent_panel":[x["opponent"] for x in games[::2]],
                        "baseline_cache_entries":len(games),
                        "candidate_results":output
                    })
                loc=dirs/f"all58-mutation-{shard}"
                loc.mkdir(parents=True)
                (loc/"shard.json").write_text(json.dumps({
                    "schema":1,"status":"ALL58_MUTATION_DISCOVERY_ONLY",
                    "shard":shard,"shards":29,"candidate_count":4,
                    "opponents":3,"agent":"ismcts:sims=24","seed":42,
                    "selected_source_manifest_sha256":sha(proposals/"manifest.json"),
                    "selected_rankings_sha256":sha(ranked_file),
                    "engine_sha256":"samebinary","legends_completed":len(processed),
                    "legends_expected":len(processed),"sideboarding":False,
                    "results":processed
                }))
            args=argparse.Namespace(
                selected=root,proposals=proposals,ranked=ranked_file,
                output=root/"out",input=dirs,shards=29,candidates=4,
                opponents=3,agent="ismcts:sims=24",seed=42
            )
            with patch("competitive_all58_candidates.load_search_sources",
                       return_value=(originals,records,ranked)):
                aggregate(args)
                result=json.loads((args.output/"all58_candidate_screening.json").read_text())
                self.assertEqual(result["legends"],58)
                self.assertEqual(result["completed_candidate_comparisons"],232)
                self.assertEqual(result["blocked_special_deckbuilding"],0)
                self.assertFalse(result["any_confirmed"])
                to_corrupt=dirs/"all58-mutation-0"/"shard.json"
                payload=json.loads(to_corrupt.read_text())
                blocked=payload["results"][0]["candidate_results"][0]
                blocked["status"]="BLOCKED_SPECIAL_DECKBUILDING"
                blocked["reason"]="Neeko requires three registered additional Legends"
                blocked["paired_completed"]=0
                blocked["paired_scenarios"]=[]
                blocked["score"]=None
                name=payload["results"][0]["legend"]
                records[name]["candidates"][0]["mutation_steps"]=[
                    {"add":"Neeko, Blending In"}]
                to_corrupt.write_text(json.dumps(payload))
                aggregate(args)
                partial=json.loads((args.output/"all58_candidate_screening.json").read_text())
                self.assertEqual(partial["blocked_special_deckbuilding"],1)
                self.assertEqual(partial["completed_candidate_comparisons"],231)
                payload["results"][0]["candidate_results"][1]["paired_scenarios"][0]["candidate_win"]=None
                to_corrupt.write_text(json.dumps(payload))
                with self.assertRaises(RuntimeError):
                    aggregate(args)


if __name__=="__main__":
    unittest.main()
