#!/usr/bin/env python3
"""Deterministic next-stage independent holdout selection from 58×8 screen.

The main-deck screening is NOT a performance conclusion. Select only
positive screening deltas for fresh-seed, untouched-opponent strong-agent
validation. No deck is changed merely because it ranked first in discovery.

All 58 Legends remain independently evaluated; an unpromising Legend retains
its original list rather than being weakened to benefit another Legend.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from screen_evolution import load_search_sources,validate_candidate_text
from round_robin_58 import sha
from competitive_all58_candidates import select_indices,has_valid_neeko_registration

PRIORITY={
    "Draven, Glorious Executioner",
    "LeBlanc, Deceiver",
    "Master Yi, Wuju Bladesman",
    "Miss Fortune, Bounty Hunter",
    "Rek'Sai, Void Burrower",
}


def load_and_validate(selected, proposals, ranked, screening, raw):
    originals,manifest,ranked_field=load_search_sources(
        selected,proposals,ranked,10
    )
    summary=json.loads(screening.read_text(encoding="utf-8"))
    detailed=json.loads(raw.read_text(encoding="utf-8"))
    if (summary.get("status") not in (
            "ALL58_CANDIDATE_DISCOVERY_COMPLETE_NO_ADOPTION",
            "ALL58_CANDIDATE_DISCOVERY_PARTIAL_NO_ADOPTION") or
        summary.get("agent")!="ismcts:sims=24" or
        summary.get("legends")!=58 or
        summary.get("candidates_per_legend")!=8 or
        summary.get("total_candidate_slots")!=464 or
        summary.get("paired_samples_per_completed_candidate")!=6 or
        summary.get("every_candidate_attempt_accounted_for") is not True or
        summary.get("all_58_baselines_retained") is not True or
        summary.get("any_confirmed") is not False or
        summary.get("sideboarding") is not False or
        summary.get("holdout_significance_tests")!=0 or
        summary.get("completed_candidate_comparisons",0)+
        summary.get("blocked_special_deckbuilding",0)+
        summary.get("engine_incomplete_excluded",0)!=464 or
        set(detailed)!=set(originals) or
        len(summary.get("best_per_legend",[]))!=58):
        raise RuntimeError("Incorrect or incomplete frozen 58-Legend wave2 source")
    reported={r["legend"]:r for r in summary["best_per_legend"]}
    if set(reported)!=set(originals):
        raise RuntimeError("Duplicate/missing Legend in summary")
    for legend in sorted(originals):
        row=detailed[legend]
        candidates=row["candidate_results"]
        options=manifest[legend]["candidates"]
        if (row["source_sha256"]!=sha(originals[legend]) or
            len(candidates)!=8 or
            [c["candidate_index"] for c in candidates]!=select_indices(options,8) or
            row["baseline_cache_entries"]!=6):
            raise RuntimeError("Wrong candidate or baseline record: "+legend)
        for c in candidates:
            m=options[c["candidate_index"]]
            path=proposals/m["path"]
            if (c["candidate_sha256"]!=m["sha256"] or
                c["candidate_path"]!=m["path"] or
                not has_valid_neeko_registration(m,path)):
                raise RuntimeError("Wrong or unregistered candidate: "+legend)
            validate_candidate_text(originals[legend],path,m["sha256"])
        completed=[c for c in candidates if c["status"]=="COMPLETED_SCREENING_ONLY"]
        expected=sorted(completed,key=lambda c:(
            -c["score"]["delta"],-c["score"]["candidate_wins"],
            c["candidate_index"]))[0] if completed else None
        observed=reported[legend]
        if (observed["baseline_sha256"]!=row["source_sha256"] or
            observed["exploratory_candidate_index"]!=(
                expected["candidate_index"] if expected else None) or
            observed["exploratory_candidate_sha256"]!=(
                expected["candidate_sha256"] if expected else None) or
            observed["candidate_delta"]!=(
                expected["score"]["delta"] if expected else None)):
            raise RuntimeError("Reported best candidate disagrees with detailed engine evidence")
    return originals,manifest,ranked_field,summary,detailed


def choose(original, manifest, ranked, summary, detailed, top_k=12):
    if not 1<=top_k<=30:
        raise ValueError("Shortlist budget must be between 1 and 30")
    positive=[
        x for x in summary["best_per_legend"]
        if x["candidate_delta"] is not None and x["candidate_delta"]>0 and
        x["independently_confirmed"] is False
    ]
    positive.sort(key=lambda r:(
        -r["candidate_delta"],-r["candidate_wins"],
        -r["baseline_wins"],r["legend"]
    ))
    names={r["legend"] for r in positive[:top_k]}
    names|={r["legend"] for r in positive if r["legend"] in PRIORITY}
    chosen=[]
    for item in positive:
        legend=item["legend"]
        if legend not in names:
            continue
        panel=[r["legend"] for r in ranked if r["legend"]!=legend]
        train=panel[:3];holdout=panel[3:9]
        if len(holdout)!=6 or set(holdout)&set(train):
            raise RuntimeError("Training opponents leaked into holdout")
        opt=manifest[legend]["candidates"][item["exploratory_candidate_index"]]
        if (opt["sha256"]!=item["exploratory_candidate_sha256"] or
            detailed[legend]["candidate_results"][
                select_indices(manifest[legend]["candidates"],8).index(
                    item["exploratory_candidate_index"])
            ]["status"]!="COMPLETED_SCREENING_ONLY"):
            raise RuntimeError("Source candidate missing")
        chosen.append({
            "legend":legend,
            "candidate_index":item["exploratory_candidate_index"],
            "candidate_sha256":opt["sha256"],
            "candidate_path":opt["path"],
            "baseline_sha256":sha(original[legend]),
            "screening_delta":item["candidate_delta"],
            "screening_candidate_wins":item["candidate_wins"],
            "screening_baseline_wins":item["baseline_wins"],
            "training_opponents":train,"holdout_opponents":holdout,
            "neeko_additional_legends":opt.get("neeko_additional_legends",[]),
        })
    if len(chosen)!=len(names):
        raise RuntimeError("Positive shortlist selection incomplete")
    return chosen


def build(args):
    original,manifest,ranked,summary,detailed=load_and_validate(
        args.selected,args.proposals,args.ranked,args.screening,args.raw
    )
    selected=choose(original,manifest,ranked,summary,detailed,args.top_k)
    result={
        "status":"PHASE5_PREREGISTERED_STRONG_AGENT_HOLDOUT_NO_ADOPTION",
        "legend_field":58,
        "independently_shortlisted":len(selected),
        "selection_rule":"Top positive discovery gains plus positive improvements for five elite anchors; independent six-opponent holdout",
        "familywise_hypotheses":len(selected),
        "original_wave2_screening_sha256":sha(args.screening),
        "original_wave2_raw_sha256":sha(args.raw),
        "original_proposals_sha256":sha(args.proposals/"manifest.json"),
        "original_ranked_field_sha256":sha(args.ranked),
        "selection_policy_fixed_before_128_matches":True,
        "holdout_agent":"ismcts:sims=128",
        "holdout_repetitions_per_seat":1,
        "holdout_master_seed":202611251505,
        "no_deck_replaced":True,
        "candidates":selected,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2))
    print("WAVE2_HOLDOUT_SELECTION",json.dumps({
        k:v for k,v in result.items() if k!="candidates"
    }),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--proposals",type=pathlib.Path,required=True)
    p.add_argument("--ranked",type=pathlib.Path,required=True)
    p.add_argument("--screening",type=pathlib.Path,required=True)
    p.add_argument("--raw",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--top-k",type=int,default=12)
    args=p.parse_args()
    build(args)


if __name__=="__main__":
    main()
