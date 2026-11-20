#!/usr/bin/env python3
"""Run 49 playable decks, using 10 labeled compatibility variants.
Original optimized deck archive is never changed.
"""
import json,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import bo3.parallel_runner as base
from compat.apply_patches import apply
baseline_decode=base.decode
def candidate_decode():
    return apply(baseline_decode())
base.decode=candidate_decode
if __name__=="__main__":
    code=base.main()
    p=ROOT/"results/metadata.json"
    if not p.exists():raise SystemExit("Missing shard report")
    d=json.loads(p.read_text())
    print("COMPATIBILITY_MATRIX "+json.dumps({"supported":d["supported"],
                                               "attempted_games":d["attempted_games"],
                                               "completed_pairings":d["completed_pairings"],
                                               "expected_pairings":d["all_pairings"],
                                               "compatibility_substitutions":10}),flush=True)
    if d["supported"]!=49 or d["all_pairings"]!=1225:
        raise SystemExit("Playability changed; expected 49 decks / 1,225 pairings; blocking unsuitable results")
    raise SystemExit(code)
