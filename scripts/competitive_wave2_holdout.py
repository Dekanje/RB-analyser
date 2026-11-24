#!/usr/bin/env python3
"""Independent 128-ISMCTS holdout after all-58 eight-candidate screening.

A candidate is selected BEFORE these holdout games. It faces the next six
ranked opponents excluding itself, which never entered its screening panel.
Twelve mirrored, independent-seed BO3 pairs compare the unchanged original
39-card list against one multi-card mutant. A native engine error is NEVER
treated as a loss, and all 58 original decks remain available unchanged.
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
from competitive_all58_candidates import has_valid_neeko_registration
from round_robin_58 import sha


def inputs(args):
    original,manifest,ranked=load_search_sources(
        args.selected,args.proposals,args.ranked,10
    )
    choose=json.loads(args.selection.read_text(encoding="utf-8"))
    if (choose.get("status")!="PHASE5_PREREGISTERED_STRONG_AGENT_HOLDOUT_NO_ADOPTION" or
        choose.get("legend_field")!=58 or
        choose.get("familywise_hypotheses")!=len(choose.get("candidates",[])) or
        not 1<=len(choose["candidates"])<=20 or
        choose.get("holdout_agent")!=args.agent or
        choose.get("holdout_repetitions_per_seat")!=args.repetitions or
        choose.get("holdout_master_seed")!=args.seed or
        choose.get("no_deck_replaced") is not True or
        choose.get("selection_policy_fixed_before_128_matches") is not True or
        choose.get("original_proposals_sha256")!=sha(args.proposals/"manifest.json") or
        choose.get("original_ranked_field_sha256")!=sha(args.ranked)):
        raise RuntimeError("Invalid preregistered phase5 shortlist")
    for index,c in enumerate(choose["candidates"]):
        name=c["legend"]
        if name not in original:
            raise RuntimeError("Unregistered Legend in stronger agent holdout")
        i=c["candidate_index"]
        if i not in range(40):
            raise RuntimeError("Invalid mutant index")
        packet=manifest[name]["candidates"][i]
        if any((
            c["candidate_sha256"]!=packet["sha256"],
            c["candidate_path"]!=packet["path"],
            c["baseline_sha256"]!=sha(original[name]),
            c["neeko_additional_legends"]!=packet.get("neeko_additional_legends",[]),
            c["screening_delta"]<=0,
            c["screening_candidate_wins"]<=c["screening_baseline_wins"],
        )):
            raise RuntimeError("Unverified candidate identity/delta")
        path=args.proposals/packet["path"]
        validate_candidate_text(original[name],path,packet["sha256"])
        if not has_valid_neeko_registration(packet,path):
            raise RuntimeError("Unregistered special Neeko mutation")
        opponents=[x["legend"] for x in ranked if x["legend"]!=name]
        if (c["training_opponents"]!=opponents[:3] or
            c["holdout_opponents"]!=opponents[3:9] or
            len(set(c["training_opponents"])&set(c["holdout_opponents"]))!=0):
            raise RuntimeError("Holdout field leaked training opponents")
    if len({c["legend"] for c in choose["candidates"]})!=len(choose["candidates"]):
        raise RuntimeError("Duplicate Legend experiments")
    return original,manifest,ranked,choose


def run_one(args):
    original,manifest,ranked,choose=inputs(args)
    if not 0<=args.index<len(choose["candidates"]):
        raise RuntimeError("Out-of-range preregistered experiment")
    c=choose["candidates"][args.index]
    name=c["legend"]
    if not args.engine.is_file():
        raise RuntimeError("Pinned verified C++ engine binary missing")
    source=original[name]
    target=args.proposals/c["candidate_path"]
    opponents={name:original[name] for name in c["holdout_opponents"]}
    evidence=assess_row(
        name,source,target,opponents,args.engine.resolve(),
        args.agent,args.timeout,args.repetitions,args.seed,args.workers
    )
    expected=len(opponents)*2*args.repetitions
    if (not evidence["changed"] or evidence["incomplete"] or
        evidence["completed"]!=expected or
        evidence["candidate_sha256"]!=c["candidate_sha256"] or
        evidence["baseline_sha256"]!=c["baseline_sha256"] or
        len(evidence["scenarios"])!=expected or
        set(x["opponent"] for x in evidence["per_opponent"])!=set(opponents)):
        raise RuntimeError("Missing actual holdout BO3 or invalid source SHA")
    receipt={
        "status":"WAVE2_128_AGENT_HOLDOUT_COMPLETED_NOT_ADOPTED",
        "index":args.index,"legend":name,
        "candidate_sha256":c["candidate_sha256"],
        "baseline_sha256":c["baseline_sha256"],
        "selection_sha256":sha(args.selection),
        "engine_sha256":sha(args.engine),
        "proposals_manifest_sha256":sha(args.proposals/"manifest.json"),
        "ranked_source_sha256":sha(args.ranked),
        "agent":args.agent,
        "seed":args.seed,"repetitions":args.repetitions,
        "training_opponents":c["training_opponents"],
        "holdout_opponents":c["holdout_opponents"],
        "sideboard_changes":False,
        "outcomes":evidence,
        "no_deck_replaced":True,
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"holdout.json").write_text(json.dumps(receipt,indent=2))
    print("WAVE2_128_HOLDOUT_COMPLETE",name,
          evidence["candidate_wins"],evidence["baseline_wins"],
          evidence["mcnemar_p"],flush=True)


def aggregate(args):
    original,manifest,ranked,choose=inputs(args)
    evidence=[];engine_hashes=set()
    for index,c in enumerate(choose["candidates"]):
        path=args.input/f"phase5-128-holdout-{index}"/"holdout.json"
        rec=json.loads(path.read_text(encoding="utf-8"))
        name=c["legend"]
        data=rec["outcomes"]
        expected=len(c["holdout_opponents"])*2*args.repetitions
        if any((
            rec["status"]!="WAVE2_128_AGENT_HOLDOUT_COMPLETED_NOT_ADOPTED",
            rec["index"]!=index or rec["legend"]!=name,
            rec["candidate_sha256"]!=c["candidate_sha256"],
            rec["baseline_sha256"]!=c["baseline_sha256"],
            rec["selection_sha256"]!=sha(args.selection),
            rec["proposals_manifest_sha256"]!=sha(args.proposals/"manifest.json"),
            rec["ranked_source_sha256"]!=sha(args.ranked),
            rec["agent"]!=args.agent or rec["seed"]!=args.seed or
            rec["repetitions"]!=args.repetitions,
            rec["training_opponents"]!=c["training_opponents"],
            rec["holdout_opponents"]!=c["holdout_opponents"],
            rec["sideboard_changes"] is not False,
            rec["no_deck_replaced"] is not True,
            not data["changed"] or data["incomplete"],
            data["completed"]!=expected,
            data["candidate_sha256"]!=c["candidate_sha256"],
            data["baseline_sha256"]!=c["baseline_sha256"],
            len(data["scenarios"])!=expected,
            set(x["opponent"] for x in data["per_opponent"])!=set(c["holdout_opponents"]),
        )):
            raise RuntimeError("Incomplete/mismatched independent 128-agent evidence")
        if any(
            x["both_complete"] is not True or
            x["baseline_win"] not in (0,1) or
            x["candidate_win"] not in (0,1)
            for x in data["scenarios"]
        ):
            raise RuntimeError("Untrusted actual game outcome")
        engine_hashes.add(rec["engine_sha256"])
        data["legend"]=name
        data["incomplete"]=0
        evidence.append(data)
    if len(engine_hashes)!=1:
        raise RuntimeError("Different native engine versions inside experiment")
    holm(evidence)
    rows=[]
    for e in evidence:
        rows.append({
            "legend":e["legend"],"baseline_sha256":e["baseline_sha256"],
            "candidate_sha256":e["candidate_sha256"],
            "candidate_wins":e["candidate_wins"],
            "baseline_wins":e["baseline_wins"],
            "completed_paired_bo3":e["completed"],
            "delta":e["candidate_minus_baseline"],
            "mcnemar_p":e["mcnemar_p"],
            "holm_adjusted_p":e["holm_adjusted_p"],
            "statistically_positive_signal":e["independently_confirmed"],
            "tournament_ready":False,
            "baseline_replaced":False,
        })
    rows.sort(key=lambda r:(-r["delta"],r["legend"]))
    result={
        "status":"WAVE2_58_LEGEND_128_STRONG_AGENT_HOLDOUT_COMPLETE",
        "original_58_decks_retained":True,
        "tested_candidates":len(rows),
        "paired_bo3":sum(x["completed_paired_bo3"] for x in rows),
        "verified_engine_sha256":next(iter(engine_hashes)),
        "agent":args.agent,
        "independent_training_vs_holdout_opponents":True,
        "multiple_testing":"Holm FWER 0.05 over entire selected hypothesis family",
        "statistically_positive_signals":sum(x["statistically_positive_signal"] for x in rows),
        "no_automatic_deck_changes":True,
        "limitations":"Only 12 paired BO3 per candidate and no tournament sideboarding; any positive signals still require larger real 407 BO3 validation.",
        "results":rows,
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"holdout_decisions.json").write_text(json.dumps(result,indent=2))
    print("WAVE2_128_HOLDOUT_FINAL",json.dumps({
        k:v for k,v in result.items() if k!="results"
    }),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selection",type=pathlib.Path,required=True)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--proposals",type=pathlib.Path,required=True)
    p.add_argument("--ranked",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,default=pathlib.Path("engine_build/riftbound"))
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--index",type=int,default=0)
    p.add_argument("--repetitions",type=int,default=1)
    p.add_argument("--agent",default="ismcts:sims=128")
    p.add_argument("--seed",type=int,default=202611251505)
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--timeout",type=float,default=240)
    a=p.parse_args()
    if not 1<=a.repetitions<=5 or a.workers not in range(1,9) or a.timeout<=0:
        p.error("Invalid holdout compute budget")
    if a.aggregate:
        if not a.input:
            p.error("--aggregate requires --input")
        aggregate(a)
    else:
        run_one(a)


if __name__=="__main__":
    main()
