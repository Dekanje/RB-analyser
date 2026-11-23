#!/usr/bin/env python3
"""Independent stronger-agent holdout for exploratory Draven/Rek'Sai swaps.

Screening panel: top 3 opponents excluding self, at ISMCTS-24.
Holdout panel: NEXT six opponents excluding self, at ISMCTS-128.
The held-out opponents and seeds are not read from training outcomes.
No automatic adoption of modifications with statistically weak evidence.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from full_field_58 import assess_row
from round_robin_58 import sha
from screen_evolution import PILOT, load_search_sources, validate_candidate_text


def independent_panel(name,ranked,originals,training_count=3,holdout_count=6):
    ordered=[r["legend"] for r in ranked if r["legend"]!=name]
    train=ordered[:training_count]
    held=ordered[training_count:training_count+holdout_count]
    if len(train)!=training_count or len(held)!=holdout_count or set(train)&set(held):
        raise RuntimeError("Training and holdout opponent fields overlap")
    return {n:originals[n] for n in held},train


def sources(args):
    original,records,ranked=load_search_sources(
        args.selected,args.proposals,args.ranked,10
    )
    selection=json.loads(args.selection.read_text(encoding="utf-8"))
    if (selection["schema"]!=1 or selection["status"]!=
        "EXPLORATORY_HOLDOUT_CANDIDATES_NOT_ACCEPTED" or
        set(selection["pilot"])!=set(PILOT)):
        raise RuntimeError("Wrong pinned holdout selection")
    for legend in PILOT:
        candidates=selection["pilot"][legend]
        if len(candidates)!=5 or len({c["id"] for c in candidates})!=5:
            raise RuntimeError("Expected five independently screened options")
        for row in candidates:
            if (row["id"] not in range(40) or
                records[legend]["candidates"][row["id"]]["sha256"]!=row["sha256"]):
                raise RuntimeError("Holdout selection SHA mismatch")
    return original,records,ranked,selection


def run(args):
    original,records,ranked,selection=sources(args)
    name=PILOT[args.legend_index]
    entry=selection["pilot"][name][args.candidate_position]
    cand=records[name]["candidates"][entry["id"]]
    path=args.proposals/cand["path"]
    validate_candidate_text(original[name],path,entry["sha256"])
    opponents,training=independent_panel(name,ranked,original)
    result=assess_row(
        name,original[name],path,opponents,args.engine.resolve(),args.agent,
        args.timeout,args.repetitions,args.seed,args.workers
    )
    expected=len(opponents)*2*args.repetitions
    if (not result["changed"] or result["incomplete"] or
        result["completed"]!=expected or
        result["baseline_sha256"]!=sha(original[name]) or
        result["candidate_sha256"]!=entry["sha256"]):
        raise RuntimeError("Invalid or incomplete heldout engine results")
    args.output.mkdir(parents=True,exist_ok=True)
    payload={
        "status":"INDEPENDENT_128_ISMCTS_HOLDOUT_EXPLORATORY",
        "legend":name,"candidate_index":entry["id"],
        "candidate_position":args.candidate_position,
        "candidate_path":cand["path"],
        "candidate_sha256":entry["sha256"],
        "engine_sha256":sha(args.engine),
        "selection_sha256":sha(args.selection),
        "source_sha256":sha(original[name]),
        "training_opponents":training,
        "holdout_opponents":list(opponents),
        "agent":args.agent,"seed":args.seed,
        "repetitions":args.repetitions,"sideboarding":False,
        "outcomes":result,
    }
    (args.output/"holdout.json").write_text(json.dumps(payload,indent=2))
    print("INDEPENDENT_HOLDOUT",name,entry["id"],
          result["candidate_minus_baseline"],
          result["candidate_wins"],result["baseline_wins"],flush=True)


def aggregate(args):
    originals,records,ranked,selection=sources(args)
    test_records=[]
    engines=set()
    for legend_index,name in enumerate(PILOT):
        expected_held,train=independent_panel(name,ranked,originals)
        for position in range(5):
            cand=selection["pilot"][name][position]
            file=args.input/f"competitive-holdout-{legend_index}-{position}"/"holdout.json"
            packet=json.loads(file.read_text(encoding="utf-8"))
            if any((
                packet["status"]!="INDEPENDENT_128_ISMCTS_HOLDOUT_EXPLORATORY",
                packet["legend"]!=name,packet["candidate_index"]!=cand["id"],
                packet["candidate_position"]!=position,
                packet["candidate_sha256"]!=cand["sha256"],
                packet["selection_sha256"]!=sha(args.selection),
                packet["source_sha256"]!=sha(originals[name]),
                packet["training_opponents"]!=train,
                packet["holdout_opponents"]!=list(expected_held),
                packet["agent"]!=args.agent,packet["seed"]!=args.seed,
                packet["repetitions"]!=args.repetitions,
                packet["sideboarding"] is not False,
            )):
                raise RuntimeError("Wrong-source or mismatched holdout result")
            engines.add(packet["engine_sha256"])
            outcome=packet["outcomes"]
            if (outcome["incomplete"] or not outcome["changed"] or
                outcome["completed"]!=len(expected_held)*2*args.repetitions or
                outcome["candidate_sha256"]!=cand["sha256"] or
                outcome["baseline_sha256"]!=sha(originals[name])):
                raise RuntimeError("Incomplete or invalid heldout game outcomes")
            test_records.append(packet)
    if len(engines)!=1:
        raise RuntimeError("Holdout engine hashes differ")
    summary=[]
    for x in test_records:
        r=x["outcomes"]
        adjusted_p=min(1.0,r["mcnemar_p"]*len(test_records))
        confirmed=(r["candidate_minus_baseline"]>0 and adjusted_p<0.05)
        summary.append({
            "legend":x["legend"],"candidate_index":x["candidate_index"],
            "candidate_sha256":x["candidate_sha256"],
            "holdout_candidate_wins":r["candidate_wins"],
            "holdout_baseline_wins":r["baseline_wins"],
            "holdout_series_per_candidate":r["completed"],
            "holdout_delta":r["candidate_minus_baseline"],
            "mcnemar_p_raw":r["mcnemar_p"],
            "bonferroni_adjusted_p":adjusted_p,
            "holdout_confirmed_after_10_comparisons":confirmed,
        })
    summary.sort(key=lambda z:(z["legend"],-z["holdout_delta"],z["candidate_index"]))
    output={
        "status":"HOLDOUT_COMPLETE_EXPLORATORY_UNLESS_CONFIRMED",
        "engine_sha256":next(iter(engines)),
        "tested_candidates":len(summary),
        "strong_agent":args.agent,
        "independent_opponent_field":True,
        "independent_holdout_seeds":True,
        "sideboarding":False,
        "no_unconfirmed_changes_automatically_adopted":True,
        "any_confirmed":any(x["holdout_confirmed_after_10_comparisons"] for x in summary),
        "adjustment":"Bonferroni across 10 selected candidates; paired same-seat, same-seed McNemar tests",
        "limitations":["Not tournament BO3; no between-game sideboarding",
                       "Heldout agents are not expert-human calibrated",
                       "Even nominal significance is not proof of global deck optimality"],
        "results":summary,
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"holdout_summary.json").write_text(json.dumps(output,indent=2))
    (args.output/"raw_holdout.json").write_text(json.dumps(test_records,indent=2))
    print("HOLDOUT_FINAL",json.dumps({k:v for k,v in output.items()
                                   if k!="results"}),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--proposals",type=pathlib.Path,required=True)
    p.add_argument("--ranked",type=pathlib.Path,required=True)
    p.add_argument("--selection",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,default=pathlib.Path("engine_build/riftbound"))
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--legend-index",type=int,default=0)
    p.add_argument("--candidate-position",type=int,default=0)
    p.add_argument("--repetitions",type=int,default=1)
    p.add_argument("--agent",default="ismcts:sims=128")
    p.add_argument("--seed",type=int,default=202611241505)
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--timeout",type=float,default=180)
    a=p.parse_args()
    if not 0<=a.legend_index<len(PILOT) or not 0<=a.candidate_position<5:
        p.error("Invalid Legend or candidate")
    if not 1<=a.repetitions<=10 or not 1<=a.workers<=16 or a.timeout<=0:
        p.error("Invalid execution parameters")
    if a.aggregate:
        if a.input is None:
            p.error("Need --input for aggregation")
        aggregate(a)
    else:
        run(a)


if __name__=="__main__":
    main()
