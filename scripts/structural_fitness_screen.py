#!/usr/bin/env python3
"""Native 407 best-of-three fitness screening for rune/battlefield/Champion variants.

All 406 registered proposals whose changes are in play for game ONE are
paired against their exact 58 unchanged baselines. 174 sideboard-only
proposals are explicitly excluded from this evaluation: with no swap policy
they are behaviorally identical to the baseline and must NOT be ranked.

Before screening require exact all-580 native legality receipts. Reuse each
baseline's opponent/seating/seeds, reject incomplete games, and make NO
automatic deck replacements. This is a 24-ISMCTS discovery filter, not proof
of optimality, not an official metagame forecast.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from full_field_58 import mcnemar_exact
from optimize_58 import registry,stable_seed
from round_robin_58 import load_decks,sha
from sideboard_deck import parse_deck
from structural_deck_population import legal_registration
from tournament_bo3_policy import run_series

FITNESS_KINDS=("rune","battlefield","champion")


def load(args):
    originals,_=load_decks(args.selected)
    registered=json.loads((args.variants/"structural_manifest.json").read_text())
    native=json.loads(args.certification.read_text())
    ranked=json.loads(args.ranked.read_text())
    rows={r["legend"]:r for r in registered["records"]}
    roster_hash=sha(args.variants/"structural_manifest.json")
    engine_hash=sha(args.engine) if args.engine else native["native_engine_sha256"]
    if (registered["status"]!="ALL58_REGISTERED_STRUCTURE_PROPOSALS_UNTESTED"
        or registered["legends"]!=58 or registered["variants_total"]!=580
        or registered["native_registry_sha256"]!=sha(args.registry)
        or set(rows)!=set(originals)
        or native["status"]!="ALL_580_REGISTERED_STRUCTURAL_NATIVE_GAMES_PASS"
        or native["all_native_games_completed"]!=580
        or native["native_game_failures"]!=0
        or native["source_manifest_sha256"]!=roster_hash
        or native["native_engine_sha256"]!=engine_hash
        or native["original_decks_modified"] is not False
        or native["strength_assessed"] is not False
        or len(ranked)!=58 or set(x["legend"] for x in ranked)!=set(originals)):
        raise RuntimeError("Cannot score noncertified or altered 580 structure source")
    for legend,rec in rows.items():
        if rec["original_sha256"]!=sha(originals[legend]):
            raise RuntimeError("Registered source baseline changed")
    expected_counts=collections.Counter(v["kind"] for r in rows.values()
                                        for v in r["variants"])
    if (expected_counts!=registered["families"] or
        sum(expected_counts[k] for k in FITNESS_KINDS)!=406 or
        expected_counts["sideboard"]!=174):
        raise RuntimeError("Incorrect 406 fitness / 174 deferred policy partition")
    return originals,registered,native,ranked,rows


def opponents_for(legend,ranked,number=2):
    names=[r["legend"] for r in ranked if r["legend"]!=legend][:number]
    if len(names)!=number or len(set(names))!=number:
        raise RuntimeError("Missing independent frozen opponent panels")
    return names


def schedule(legend,ranked,seed):
    return [{
        "opponent":name,"seat":seat,
        "seed":stable_seed(seed,"REGISTERED_STRUCTURE_407_FITNESS",
                            legend,name,seat)
    } for name in opponents_for(legend,ranked) for seat in (0,1)]


def score(paired):
    if not paired or any(x["candidate_win"] not in (0,1)
                         or x["baseline_win"] not in (0,1) for x in paired):
        raise RuntimeError("Missing real engine BO3 result")
    a=sum(x["candidate_win"] and not x["baseline_win"] for x in paired)
    b=sum(x["baseline_win"] and not x["candidate_win"] for x in paired)
    cand=sum(x["candidate_win"] for x in paired)
    base=sum(x["baseline_win"] for x in paired)
    return {"candidate_wins":cand,"baseline_wins":base,"delta":cand-base,
            "candidate_only":a,"baseline_only":b,
            "mcnemar_p_unadjusted":mcnemar_exact(a,b)}


def screen(args):
    originals,registered,native,ranked,rows=load(args)
    if not args.engine.is_file():
        raise RuntimeError("Missing verified 407 C++ binary")
    byname=registry(args.registry)
    names=[n for i,n in enumerate(sorted(originals))
           if i%args.shards==args.shard]
    result=[]
    for name in names:
        baseline=originals[name]
        registered_orig=parse_deck(baseline.read_text())
        scenarios=schedule(name,ranked,args.seed)
        def play(target,case):
            if case["seat"]==0:
                a,b=target,originals[case["opponent"]]
            else:
                a,b=originals[case["opponent"]],target
            outcome=run_series(args.engine.resolve(),a,b,byname,{},
                               args.agent,case["seed"],args.timeout)
            if (outcome["status"]!="COMPLETE_RULE407_START_POLICY_BO3"
                or outcome["rule_407_4_start_choice_verified"] is not True
                or outcome["winner"] not in (1,2)
                or any(x["engine_status"]!="complete" for x in outcome["games"])):
                raise RuntimeError("Native 407 BO3 incomplete; no outcome imputed: "
                                   +json.dumps(outcome)[-900:])
            return int(outcome["winner"]==case["seat"]+1)
        baseline_games=[play(baseline,case) for case in scenarios]
        candidate_results=[]
        for entry in rows[name]["variants"]:
            if entry["kind"]=="sideboard":
                continue
            if entry["kind"] not in FITNESS_KINDS:
                raise RuntimeError("Unexpected structure family")
            variant=args.variants/entry["path"]
            if sha(variant)!=entry["sha256"]:
                raise RuntimeError("Variant content altered before simulation")
            legal_registration(registered_orig,
                               parse_deck(variant.read_text()),byname)
            candidate_games=[play(variant,case) for case in scenarios]
            paired=[{**case,"baseline_win":bw,"candidate_win":cw,
                     "both_complete":True}
                    for case,bw,cw in zip(scenarios,baseline_games,candidate_games)]
            candidate_results.append({
                "kind":entry["kind"],"path":entry["path"],
                "candidate_sha256":entry["sha256"],
                "registered_baseline_sha256":sha(baseline),
                "paired_completed":len(paired),
                "paired_receipts":paired,
                "score":score(paired),
                "status":"COMPLETE_EXPLORATORY_407_BO3",
            })
            print("STRUCTURE_407_CANDIDATE",name,entry["kind"],
                  entry["sha256"][:10],candidate_results[-1]["score"]["delta"],
                  flush=True)
        result.append({
            "legend":name,"original_sha256":sha(baseline),
            "frozen_opponents":opponents_for(name,ranked),
            "shared_baseline_cases":len(scenarios),
            "candidate_results":candidate_results,
            "deferred_sideboard_only":sum(v["kind"]=="sideboard"
                                          for v in rows[name]["variants"])
        })
    payload={
        "status":"ALL58_REGISTERED_STRUCTURE_407_EXPLORATORY_ONLY",
        "shard":args.shard,"shards":args.shards,
        "source_manifest_sha256":sha(args.variants/"structural_manifest.json"),
        "accepted_native_580_sha256":sha(args.certification),
        "frozen_ranked_58_sha256":sha(args.ranked),
        "engine_sha256":sha(args.engine),
        "agent":args.agent,"seed":args.seed,
        "sideboard_policy":"NONE",
        "legends_expected":len(names),"legends_completed":len(result),
        "paired_bo3_per_candidate":4,
        "registered_decks_modified":False,
        "results":result
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    if len(result)!=len(names):
        raise RuntimeError("Incomplete structural fitness shard")
    print("STRUCTURAL_FITNESS_SHARD_PASS",args.shard,len(result),flush=True)


def aggregate(args):
    originals,registered,native,ranked,rows=load(args)
    engine_hash=set()
    results={}
    for shard in range(args.shards):
        path=args.input/f"fitness-structure-{shard}"/"screen.json"
        packet=json.loads(path.read_text(encoding="utf-8"))
        names=[n for i,n in enumerate(sorted(originals))
               if i%args.shards==shard]
        if (packet["status"]!="ALL58_REGISTERED_STRUCTURE_407_EXPLORATORY_ONLY"
            or packet["shard"]!=shard or packet["shards"]!=args.shards
            or packet["source_manifest_sha256"]!=sha(args.variants/"structural_manifest.json")
            or packet["accepted_native_580_sha256"]!=sha(args.certification)
            or packet["frozen_ranked_58_sha256"]!=sha(args.ranked)
            or packet["agent"]!=args.agent or packet["seed"]!=args.seed
            or packet["sideboard_policy"]!="NONE"
            or packet["legends_expected"]!=len(names)
            or packet["legends_completed"]!=len(names)
            or packet["paired_bo3_per_candidate"]!=4
            or packet["registered_decks_modified"] is not False
            or [x["legend"] for x in packet["results"]]!=names):
            raise RuntimeError("Wrong-source or incomplete candidate shard: "+str(shard))
        engine_hash.add(packet["engine_sha256"])
        for row in packet["results"]:
            name=row["legend"]
            cases=schedule(name,ranked,args.seed)
            expected=[v for v in rows[name]["variants"]
                      if v["kind"] in FITNESS_KINDS]
            if (name in results or row["original_sha256"]!=sha(originals[name])
                or row["frozen_opponents"]!=opponents_for(name,ranked)
                or row["shared_baseline_cases"]!=len(cases)
                or row["deferred_sideboard_only"]!=sum(
                    x["kind"]=="sideboard" for x in rows[name]["variants"])
                or len(row["candidate_results"])!=len(expected)):
                raise RuntimeError("Incomplete Legend source family")
            shared_baseline=None
            for rec,wanted in zip(row["candidate_results"],expected):
                if (rec["kind"]!=wanted["kind"]
                    or rec["candidate_sha256"]!=wanted["sha256"]
                    or rec["path"]!=wanted["path"]
                    or rec["registered_baseline_sha256"]!=sha(originals[name])
                    or rec["paired_completed"]!=4
                    or len(rec["paired_receipts"])!=4
                    or rec["status"]!="COMPLETE_EXPLORATORY_407_BO3"):
                    raise RuntimeError("Structural registration changed in game receipt")
                data=rec["paired_receipts"]
                for q,w in zip(data,cases):
                    if (any(q[k]!=w[k] for k in ("opponent","seat","seed"))
                        or q["both_complete"] is not True
                        or q["baseline_win"] not in (0,1)
                        or q["candidate_win"] not in (0,1)):
                        raise RuntimeError("Incomplete or unpaired 407 game evidence")
                control=[x["baseline_win"] for x in data]
                if shared_baseline is None:
                    shared_baseline=control
                elif control!=shared_baseline:
                    raise RuntimeError("Baseline games were not cached identically")
                if rec["score"]!=score(data):
                    raise RuntimeError("Recalculated paired score mismatch")
            results[name]=row
    if len(engine_hash)!=1 or engine_hash!={native["native_engine_sha256"]}:
        raise RuntimeError("Native engine identity not held constant")
    if set(results)!=set(originals):
        raise RuntimeError("Not all 58 Legends evaluated")
    flat=[{"legend":name,**x}
          for name in sorted(results)
          for x in results[name]["candidate_results"]]
    counts=collections.Counter(x["kind"] for x in flat)
    if (len(flat)!=406 or counts!=collections.Counter({
        "rune":229,"battlefield":174,"champion":3
    }) or sum(x["deferred_sideboard_only"] for x in results.values())!=174):
        raise RuntimeError("Structural family coverage mismatch")
    best=[]
    for name in sorted(results):
        c=sorted(results[name]["candidate_results"],key=lambda x:(
            -x["score"]["delta"],-x["score"]["candidate_wins"],
            x["candidate_sha256"]))[0]
        best.append({
            "legend":name,"kind":c["kind"],"candidate_sha256":c["candidate_sha256"],
            "paired_wins_candidate":c["score"]["candidate_wins"],
            "paired_wins_baseline":c["score"]["baseline_wins"],
            "sample_delta":c["score"]["delta"],
            "screened_no_independent_confirmation":True
        })
    report={
        "status":"ALL58_406_STRUCTURE_VARIANTS_SCREENED_NO_ACCEPTANCE",
        "legends":58,"structural_candidates_scored":406,
        "candidate_families":dict(counts),
        "sideboard_only_deferred_for_real_sideboard_policy":174,
        "paired_series_per_candidate":4,
        "estimated_completed_paired_bo3":406*4,
        "separate_baseline_cases_per_legend":4,
        "agent":args.agent,"source_manifest_sha256":sha(args.variants/"structural_manifest.json"),
        "native_engine_sha256":native["native_engine_sha256"],
        "independent_holdout_count":0,
        "confirmed_deck_upgrades":0,
        "original_registered_decks_changed":False,
        "best_unconfirmed_by_legend":best
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"summary.json").write_text(json.dumps(report,indent=2))
    (args.output/"all_fitness_evidence.json").write_text(json.dumps(results,indent=2))
    print("ALL58_STRUCTURE_407_FITNESS_AGGREGATE_PASS",
          {k:v for k,v in report.items() if k!="best_unconfirmed_by_legend"},
          flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--variants",type=pathlib.Path,required=True)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--registry",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path)
    p.add_argument("--ranked",type=pathlib.Path,required=True)
    p.add_argument("--certification",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--shards",type=int,default=29)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--agent",default="ismcts:sims=24")
    p.add_argument("--seed",type=int,default=202611252235)
    p.add_argument("--timeout",type=float,default=150)
    a=p.parse_args()
    if not 1<=a.shards<=58 or not 0<=a.shard<a.shards or a.timeout<=0:
        p.error("Invalid matched structural screening budget")
    if a.aggregate:
        if not a.input:
            p.error("--aggregate requires --input")
        aggregate(a)
    else:
        if not a.engine:
            p.error("Native 407 engine required")
        screen(a)


if __name__=="__main__":
    main()
