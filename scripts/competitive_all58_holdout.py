#!/usr/bin/env python3
"""Independent 128-ISMCTS holdout for 12 preregistered all-58 proposals.

No overlap with the first 3 elite training opponents, and no previously
used simulation seeds. Holm family-wise control across all 12 proposals.
No deck replacement or new rankings are published until these gates pass.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from full_field_58 import assess_row,holm
from screen_evolution import load_search_sources,validate_candidate_text
from round_robin_58 import sha

def load(args):
    original,manifest,ranked=load_search_sources(
        args.selected,args.proposals,args.ranked,10
    )
    selection=json.loads(args.selection.read_text(encoding="utf-8"))
    if (selection.get("schema")!=1 or
        selection.get("status")!="PREREGISTERED_INDEPENDENT_HOLDOUT_NO_ADOPTION" or
        selection.get("hypothesis_family_size")!=12 or
        len(selection.get("candidates",[]))!=12 or
        selection.get("holdout_repetitions_per_seat")!=args.repetitions or
        selection.get("holdout_agent")!=args.agent):
        raise RuntimeError("Wrong preregistered hypothesis family")
    seen=set()
    for row in selection["candidates"]:
        name=row["legend"]
        if name not in original or name in seen:
            raise RuntimeError("Repeated/invalid Legend in preregistration")
        seen.add(name)
        i=row["candidate_index"]
        if i not in (0,10,20,30):
            raise RuntimeError("Candidate was not in the preregistered screen")
        if row["candidate_sha256"]!=manifest[name]["candidates"][i]["sha256"]:
            raise RuntimeError("Mutation proposal SHA mismatch")
        if manifest[name]["candidates"][i]["status"]!="UNTESTED_STRUCTURAL_CANDIDATE":
            raise RuntimeError("Unexpected proposal status")
    previous=json.loads(args.prior_screen.read_text(encoding="utf-8"))
    if (previous.get("status")!="ALL58_CANDIDATE_DISCOVERY_PARTIAL_NO_ADOPTION" or
        previous.get("legends")!=58 or
        previous.get("completed_candidate_comparisons")!=230 or
        previous.get("blocked_special_deckbuilding")!=2 or
        previous.get("any_confirmed") is not False):
        raise RuntimeError("Prior 58-Legend screen is not the frozen source")
    by_legend={r["legend"]:r for r in previous["best_per_legend"]}
    if set(by_legend)!=set(original):
        raise RuntimeError("Prior full-field source has missing Legends")
    for row in selection["candidates"]:
        reported=by_legend[row["legend"]]
        if (reported["exploratory_candidate_index"]!=row["candidate_index"] or
            reported["exploratory_candidate_sha256"]!=row["candidate_sha256"]):
            raise RuntimeError("Holdout candidate differs from preregistered screen")
    return original,manifest,ranked,selection

def opponent_split(legend,ranked,original):
    other=[r["legend"] for r in ranked if r["legend"]!=legend]
    training=other[:3]
    held=other[3:9]
    if (len(training)!=3 or len(held)!=6 or set(training)&set(held)
        or legend in training or legend in held):
        raise RuntimeError("Holdout contains training opponent or self")
    return training,{n:original[n] for n in held}

def run(args):
    original,proposals,ranked,selection=load(args)
    choice=selection["candidates"][args.index]
    name=choice["legend"]
    proposal=proposals[name]["candidates"][choice["candidate_index"]]
    path=args.proposals/proposal["path"]
    validate_candidate_text(original[name],path,choice["candidate_sha256"])
    training,held=opponent_split(name,ranked,original)
    if not args.engine.is_file():
        raise RuntimeError("Pinned compiled engine binary not present")
    outcome=assess_row(
        name,original[name],path,held,
        args.engine.resolve(),args.agent,args.timeout,args.repetitions,
        args.seed,args.workers
    )
    expected=len(held)*2*args.repetitions
    if (outcome["incomplete"] or not outcome["changed"] or
        outcome["completed"]!=expected or
        outcome["baseline_sha256"]!=sha(original[name]) or
        outcome["candidate_sha256"]!=choice["candidate_sha256"] or
        len(outcome["per_opponent"])!=len(held) or
        set(x["opponent"] for x in outcome["per_opponent"])!=set(held)):
        raise RuntimeError("Incomplete real-engine holdout game evidence")
    report={
        "status":"PREREGISTERED_HOLDOUT_EXPERIMENT_COMPLETED",
        "index":args.index,
        "legend":name,
        "candidate_index":choice["candidate_index"],
        "candidate_sha256":choice["candidate_sha256"],
        "source_sha256":sha(original[name]),
        "selection_sha256":sha(args.selection),
        "prior_screen_sha256":sha(args.prior_screen),
        "proposals_manifest_sha256":sha(args.proposals/"manifest.json"),
        "frozen_opponent_rankings_sha256":sha(args.ranked),
        "engine_sha256":sha(args.engine),
        "agent":args.agent,"seed":args.seed,"repetitions":args.repetitions,
        "training_opponents":training,"holdout_opponents":list(held),
        "sideboard_swaps":False,"outcome":outcome,
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"holdout.json").write_text(json.dumps(report,indent=2))
    print("ALL58_HOLDOUT_COMPLETED",name,choice["candidate_index"],
          "delta",outcome["candidate_minus_baseline"],
          "p",outcome["mcnemar_p"],flush=True)

def aggregate(args):
    original,proposals,ranked,selection=load(args)
    samples=[]
    engine_hashes=set()
    for i,choice in enumerate(selection["candidates"]):
        path=args.input/f"competitive-58-holdout-{i}"/"holdout.json"
        packet=json.loads(path.read_text(encoding="utf-8"))
        name=choice["legend"]
        training,held=opponent_split(name,ranked,original)
        if any((
            packet["status"]!="PREREGISTERED_HOLDOUT_EXPERIMENT_COMPLETED",
            packet["index"]!=i,packet["legend"]!=name,
            packet["candidate_index"]!=choice["candidate_index"],
            packet["candidate_sha256"]!=choice["candidate_sha256"],
            packet["source_sha256"]!=sha(original[name]),
            packet["selection_sha256"]!=sha(args.selection),
            packet["prior_screen_sha256"]!=sha(args.prior_screen),
            packet["proposals_manifest_sha256"]!=sha(args.proposals/"manifest.json"),
            packet["frozen_opponent_rankings_sha256"]!=sha(args.ranked),
            packet["agent"]!=args.agent,packet["seed"]!=args.seed,
            packet["repetitions"]!=args.repetitions,
            packet["training_opponents"]!=training,
            packet["holdout_opponents"]!=list(held),
            packet["sideboard_swaps"] is not False,
        )):
            raise RuntimeError("Holdout packet or source altered: "+str(path))
        engine_hashes.add(packet["engine_sha256"])
        outcome=packet["outcome"]
        if (not outcome["changed"] or outcome["incomplete"] or
            outcome["completed"]!=len(held)*2*args.repetitions or
            outcome["candidate_sha256"]!=choice["candidate_sha256"] or
            outcome["baseline_sha256"]!=sha(original[name]) or
            len(outcome["scenarios"])!=len(held)*2*args.repetitions or
            set(x["opponent"] for x in outcome["per_opponent"])!=set(held)):
            raise RuntimeError("Incomplete underlying paired engine samples")
        if any(not x["both_complete"] or x["baseline_win"] not in (0,1)
               or x["candidate_win"] not in (0,1) for x in outcome["scenarios"]):
            raise RuntimeError("Invalid individual engine game receipt")
        # Used for Holm utility's original accepted-deck shape.
        outcome["incomplete"]=0
        outcome["legend"]=name
        samples.append(outcome)
    if len(engine_hashes)!=1:
        raise RuntimeError("Mismatched engine binaries in holdout")
    holm(samples)
    summary=[]
    for rec in samples:
        summary.append({
            "legend":rec["legend"],
            "candidate_sha256":rec["candidate_sha256"],
            "wins_candidate":rec["candidate_wins"],
            "wins_baseline":rec["baseline_wins"],
            "delta":rec["candidate_minus_baseline"],
            "paired_bo3_series_each":rec["completed"],
            "candidate_only_wins":rec["candidate_only_wins"],
            "baseline_only_wins":rec["baseline_only_wins"],
            "mcnemar_p":rec["mcnemar_p"],
            "holm_adjusted_p":rec["holm_adjusted_p"],
            "independently_confirmed":rec["independently_confirmed"],
        })
    summary.sort(key=lambda x:(-x["delta"],x["legend"]))
    report={
        "status":"ALL58_PREREGISTERED_128_ISMCTS_HOLDOUT_COMPLETE",
        "hypotheses_tested":12,
        "exact_source_unchanged":True,
        "engine_sha256":next(iter(engine_hashes)),
        "agent":args.agent,
        "per_legend_holdout_opponents":6,
        "per_legend_mirrored_repetitions":args.repetitions,
        "total_completed_paired_series":sum(x["completed"] for x in samples),
        "significance_control":"Holm FWER 0.05 over exactly 12 candidate hypotheses",
        "confirmed_improvements":sum(x["independently_confirmed"] for x in samples),
        "all_58_baselines_automatically_replaced":False,
        "no_unconfirmed_decks_promoted":True,
        "limitations":"No between-game sideboarding, no expert player model, only elite frozen holdout field; absence of significance does not imply no actual improvement.",
        "results":summary,
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"summary.json").write_text(json.dumps(report,indent=2))
    (args.output/"all_paired_receipts.json").write_text(json.dumps(samples,indent=2))
    print("ALL58_HOLDOUT_FINAL",json.dumps({k:v for k,v in report.items()
                                         if k!="results"}),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--proposals",type=pathlib.Path,required=True)
    p.add_argument("--ranked",type=pathlib.Path,required=True)
    p.add_argument("--prior-screen",type=pathlib.Path,required=True)
    p.add_argument("--selection",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,default=pathlib.Path("engine_build/riftbound"))
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--index",type=int,default=0)
    p.add_argument("--repetitions",type=int,default=2)
    p.add_argument("--agent",default="ismcts:sims=128")
    p.add_argument("--seed",type=int,default=202611241212)
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--timeout",type=int,default=240)
    a=p.parse_args()
    if (not 0<=a.index<12 or not 1<=a.repetitions<=10 or
        not 1<=a.workers<=16 or a.timeout<=0):
        p.error("Invalid holdout budget")
    if a.aggregate:
        if not a.input:
            p.error("Aggregate requires --input")
        aggregate(a)
    else:
        run(a)

if __name__=="__main__":
    main()
