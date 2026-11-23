#!/usr/bin/env python3
"""All-58 broad-deck exploration with reused immutable baseline simulations.

Compare 4 preregistered candidates per Legend to each unchanged source list,
against three frozen strong opponents, two seats, one sampled seed.
This is a low-cost discovery filter, NOT statistically validated optimization.
Every successful result carries exact deck, binary, seed, and opponent receipts.
"""
from __future__ import annotations
import argparse
import collections
import concurrent.futures
import json
import os
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from screen_evolution import load_search_sources, validate_candidate_text
from evaluate_radiance_ismcts import engine_bo3
from full_field_58 import mcnemar_exact
from optimize_58 import stable_seed
from round_robin_58 import sha


def has_valid_neeko_registration(record:dict, deck:pathlib.Path)->bool:
    """Require exact 3-Legend metadata and matching candidate source section."""
    adds_neeko=any(step.get("add")=="Neeko, Blending In"
                   for step in record["mutation_steps"])
    extra=record.get("neeko_additional_legends",[])
    if not adds_neeko:
        if extra:
            raise RuntimeError("Unexpected special registration without Neeko mutation")
        return True
    source=deck.read_text(encoding="utf-8")
    delimiter="\\nNeekoLegends:\\n"
    if len(extra)!=3 or len(set(extra))!=3 or source.count(delimiter)!=1:
        return False
    lines=source.split(delimiter,1)[1].strip().splitlines()
    return lines==["1 "+name for name in extra]


def select_indices(records:list, count:int)->list[int]:
    if not 1<=count<=len(records):
        raise ValueError("Invalid deterministic candidate budget")
    ids=[i*len(records)//count for i in range(count)]
    if len(set(ids))!=count:
        raise RuntimeError("Selection failed to cover population")
    return ids


def anchor_names(legend:str, ranked:list, number:int)->list[str]:
    result=[row["legend"] for row in ranked if row["legend"]!=legend][:number]
    if len(result)!=number or len(set(result))!=number:
        raise RuntimeError("Insufficient frozen opponent panel")
    return result


def schedule(legend, ranked, opponents, seed):
    return [{
        "opponent":n,"seat":seat,
        "seed":stable_seed(seed,"ALL58_MUTATION_V1",legend,n,seat),
    } for n in anchor_names(legend,ranked,opponents) for seat in (0,1)]


def score(outcomes):
    base=sum(x["baseline_win"] for x in outcomes)
    cand=sum(x["candidate_win"] for x in outcomes)
    a=sum(x["candidate_win"] and not x["baseline_win"] for x in outcomes)
    b=sum(x["baseline_win"] and not x["candidate_win"] for x in outcomes)
    return {"baseline_wins":base,"candidate_wins":cand,"delta":cand-base,
            "candidate_only_wins":a,"baseline_only_wins":b,
            "mcnemar_p_unadjusted":mcnemar_exact(a,b)}


def screen(args):
    originals, records, ranked=load_search_sources(
        args.selected,args.proposals,args.ranked,10
    )
    if not args.engine.is_file():
        raise RuntimeError("Compiled repaired engine binary missing")
    args.output.mkdir(parents=True,exist_ok=True)
    names=[name for i,name in enumerate(sorted(originals))
           if i%args.shards==args.shard]
    env=os.environ.copy()
    output=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for legend in names:
            pairs=schedule(legend,ranked,args.opponents,args.seed)
            candidates=records[legend]["candidates"]
            ids=select_indices(candidates,args.candidates)
            for n in ids:
                c=candidates[n]
                path=args.proposals/c["path"]
                validate_candidate_text(originals[legend],path,c["sha256"])
                if c["changed_main_slots"]<3:
                    raise RuntimeError("Selected change distance unexpectedly small")
            # Baseline results evaluated ONCE per opponent/seat; shared by all
            # candidates. Prevents spending search budget on duplicate games.
            def play(deck,case):
                game=engine_bo3(
                    args.engine.resolve(),deck,originals[case["opponent"]],
                    case["seat"],case["seed"],args.agent,args.timeout,env
                )
                if game["status"]!="complete" or game["winner"] not in (1,2):
                    return {"status":"incomplete","error":game.get("error",""),
                            "win":None}
                return {"status":"complete",
                        "win":int(game["winner"]==case["seat"]+1)}
            baseline=list(pool.map(lambda row:play(originals[legend],row),pairs))
            if any(x["status"]!="complete" for x in baseline):
                raise RuntimeError("Baseline not supported: "+legend)
            candidate_results=[]
            for index in ids:
                c=candidates[index]
                deck=args.proposals/c["path"]
                base_receipt={
                    "candidate_index":index,
                    "candidate_path":c["path"],
                    "candidate_sha256":c["sha256"],
                    "changed_main_slots":c["changed_main_slots"],
                }
                # Earlier archived Neeko proposals omitted mandatory extra
                # Legends; new generations append three actual registered
                # Legends. Validate the source and manifest together.
                if not has_valid_neeko_registration(c,deck):
                    candidate_results.append({
                        **base_receipt,
                        "status":"BLOCKED_SPECIAL_DECKBUILDING",
                        "reason":"Neeko requires three registered additional Legends",
                        "paired_completed":0,"paired_scenarios":[],
                        "score":None,
                    })
                    print("ALL58_BLOCKED_NEKO",legend,index,flush=True)
                    continue
                results=list(pool.map(lambda row:play(deck,row),pairs))
                paired=[
                    {**case,"baseline_win":left["win"],"candidate_win":right["win"],
                     "baseline_complete":True,
                     "candidate_complete":right["status"]=="complete",
                     "candidate_error":right.get("error","")}
                    for case,left,right in zip(pairs,baseline,results)
                ]
                if any(x["status"]!="complete" for x in results):
                    candidate_results.append({
                        **base_receipt,"status":"ENGINE_INCOMPLETE_UNRANKED",
                        "reason":"At least one actual engine game failed; zero imputed wins",
                        "paired_completed":0,
                        "paired_scenarios":paired,
                        "score":None,
                    })
                    print("ALL58_ENGINE_INCOMPLETE",legend,index,
                          [x for x in paired if not x["candidate_complete"]],flush=True)
                    continue
                candidate_results.append({
                    **base_receipt,"status":"COMPLETED_SCREENING_ONLY",
                    "paired_completed":len(paired),
                    "paired_scenarios":paired,
                    "score":score(paired),
                })
                print("ALL58_CANDIDATE",legend,index,
                      candidate_results[-1]["score"]["delta"],flush=True)
            output.append({
                "legend":legend,"source_sha256":sha(originals[legend]),
                "opponent_panel":[x["opponent"] for x in pairs[::2]],
                "baseline_cache_entries":len(baseline),
                "candidate_results":candidate_results,
            })
    payload={
        "schema":1,"status":"ALL58_MUTATION_DISCOVERY_ONLY",
        "shard":args.shard,"shards":args.shards,
        "candidate_count":args.candidates,
        "opponents":args.opponents,"agent":args.agent,"seed":args.seed,
        "selected_source_manifest_sha256":sha(args.proposals/"manifest.json"),
        "selected_rankings_sha256":sha(args.ranked),
        "engine_sha256":sha(args.engine),
        "legends_completed":len(output),
        "legends_expected":len(names),
        "sideboarding":False,
        "results":output,
    }
    (args.output/"shard.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
    if payload["legends_completed"]!=payload["legends_expected"]:
        raise RuntimeError("Missing Legend results")
    print("ALL58_MUTATION_SHARD_PASS",args.shard,len(output),flush=True)


def aggregate(args):
    originals,records,ranked=load_search_sources(
        args.selected,args.proposals,args.ranked,10
    )
    args.output.mkdir(parents=True,exist_ok=True)
    binary_hashes=set();processed={}
    for shard in range(args.shards):
        p=args.input/f"all58-mutation-{shard}"/"shard.json"
        packet=json.loads(p.read_text(encoding="utf-8"))
        if any((
            packet["status"]!="ALL58_MUTATION_DISCOVERY_ONLY",
            packet["schema"]!=1,
            packet["shard"]!=shard,
            packet["shards"]!=args.shards,
            packet["candidate_count"]!=args.candidates,
            packet["opponents"]!=args.opponents,
            packet["agent"]!=args.agent,
            packet["seed"]!=args.seed,
            packet["sideboarding"] is not False,
            packet["selected_source_manifest_sha256"]!=sha(args.proposals/"manifest.json"),
            packet["selected_rankings_sha256"]!=sha(args.ranked),
            packet["legends_completed"]!=packet["legends_expected"],
        )):
            raise RuntimeError("Wrong-source shard evidence: "+str(p))
        binary_hashes.add(packet["engine_sha256"])
        for rec in packet["results"]:
            name=rec["legend"]
            if name not in originals or name in processed:
                raise RuntimeError("Duplicate or unknown Legend")
            if sorted(originals).index(name)%args.shards!=shard:
                raise RuntimeError("Wrong shard assignment")
            if rec["source_sha256"]!=sha(originals[name]):
                raise RuntimeError("Original baseline changed")
            cases=schedule(name,ranked,args.opponents,args.seed)
            if rec["opponent_panel"]!=[x["opponent"] for x in cases[::2]]:
                raise RuntimeError("Opponent panel altered")
            if rec["baseline_cache_entries"]!=len(cases):
                raise RuntimeError("Missing baseline games")
            expected_ids=select_indices(records[name]["candidates"],args.candidates)
            chosen=rec["candidate_results"]
            if [x["candidate_index"] for x in chosen]!=expected_ids:
                raise RuntimeError("Missing candidate or candidate reordering")
            for x in chosen:
                entry=records[name]["candidates"][x["candidate_index"]]
                if (x["candidate_sha256"]!=entry["sha256"] or
                    x["candidate_path"]!=entry["path"] or
                    x["changed_main_slots"]!=entry["changed_main_slots"]):
                    raise RuntimeError("Candidate identity mismatch")
                validate_candidate_text(
                    originals[name],args.proposals/entry["path"],entry["sha256"]
                )
                state=x.get("status")
                paired=x["paired_scenarios"]
                is_neeko=any(step.get("add")=="Neeko, Blending In"
                             for step in entry["mutation_steps"])
                registered=has_valid_neeko_registration(
                    entry,args.proposals/entry["path"]
                )
                if state=="BLOCKED_SPECIAL_DECKBUILDING":
                    if (not is_neeko or registered or paired or
                        x["paired_completed"]!=0 or x["score"] is not None or
                        x.get("reason")!="Neeko requires three registered additional Legends"):
                        raise RuntimeError("Invalid special deckbuilding exclusion")
                    continue
                if not registered:
                    raise RuntimeError("Unregistered Neeko candidate used in simulated outcomes")
                if len(paired)!=len(cases):
                    raise RuntimeError("Missing candidate scenario receipts")
                all_complete=True
                for test,expected in zip(paired,cases):
                    if (any(test[k]!=expected[k] for k in ("opponent","seat","seed")) or
                        test["baseline_complete"] is not True or
                        test["baseline_win"] not in (0,1) or
                        test["candidate_complete"] not in (True,False)):
                        raise RuntimeError("Untrusted baseline or seed")
                    if test["candidate_complete"]:
                        if test["candidate_win"] not in (0,1):
                            raise RuntimeError("Completed candidate has invalid score")
                    else:
                        all_complete=False
                        if test["candidate_win"] is not None or not test.get("candidate_error"):
                            raise RuntimeError("Failed candidate was assigned a win or lost its diagnostic")
                if state=="ENGINE_INCOMPLETE_UNRANKED":
                    if (all_complete or x["paired_completed"]!=0 or
                        x["score"] is not None or
                        x.get("reason")!="At least one actual engine game failed; zero imputed wins"):
                        raise RuntimeError("Untrusted failed candidate status")
                elif state=="COMPLETED_SCREENING_ONLY":
                    if (not all_complete or x["paired_completed"]!=len(cases) or
                        x["score"]!=score(paired)):
                        raise RuntimeError("Inconsistent completed engine evidence")
                else:
                    raise RuntimeError("Unknown candidate status")
            processed[name]=rec
    if len(binary_hashes)!=1 or set(processed)!=set(originals):
        raise RuntimeError("Complete unchanged 58-Legend field required")
    ranking=[]
    all_candidates=[c for r in processed.values() for c in r["candidate_results"]]
    completed_candidates=[c for c in all_candidates
                          if c["status"]=="COMPLETED_SCREENING_ONLY"]
    blocked_candidates=[c for c in all_candidates
                        if c["status"]=="BLOCKED_SPECIAL_DECKBUILDING"]
    engine_incomplete=[c for c in all_candidates
                       if c["status"]=="ENGINE_INCOMPLETE_UNRANKED"]
    for name in sorted(originals):
        candidates=[c for c in processed[name]["candidate_results"]
                    if c["status"]=="COMPLETED_SCREENING_ONLY"]
        best=(sorted(candidates,key=lambda c:(
            -c["score"]["delta"],-c["score"]["candidate_wins"],
            c["candidate_index"]))[0] if candidates else None)
        ranking.append({
            "legend":name, "baseline_sha256":processed[name]["source_sha256"],
            "exploratory_candidate_index":best["candidate_index"] if best else None,
            "exploratory_candidate_sha256":best["candidate_sha256"] if best else None,
            "paired_games_per_candidate":best["paired_completed"] if best else 0,
            "candidate_delta":best["score"]["delta"] if best else None,
            "candidate_wins":best["score"]["candidate_wins"] if best else None,
            "baseline_wins":best["score"]["baseline_wins"] if best else None,
            "mcnemar_p_unadjusted":best["score"]["mcnemar_p_unadjusted"] if best else None,
            "independently_confirmed":False,
        })
    payload={
        "status":("ALL58_CANDIDATE_DISCOVERY_COMPLETE_NO_ADOPTION"
                  if not blocked_candidates and not engine_incomplete
                  else "ALL58_CANDIDATE_DISCOVERY_PARTIAL_NO_ADOPTION"),
        "agent":args.agent,
        "legends":58,
        "candidates_per_legend":args.candidates,
        "total_candidate_slots":58*args.candidates,
        "completed_candidate_comparisons":len(completed_candidates),
        "blocked_special_deckbuilding":len(blocked_candidates),
        "engine_incomplete_excluded":len(engine_incomplete),
        "every_candidate_attempt_accounted_for":(
            len(all_candidates)==58*args.candidates),
        "paired_samples_per_completed_candidate":args.opponents*2,
        "extra_baseline_simulations_reused":True,
        "engine_sha256":next(iter(binary_hashes)),
        "sideboarding":False,"all_58_baselines_retained":True,
        "holdout_significance_tests":0,"any_confirmed":False,
        "uncertainty":"Six paired BO3 per candidate; severe multiple-testing / selection risk",
        "best_per_legend":ranking,
    }
    (args.output/"all58_candidate_screening.json").write_text(
        json.dumps(payload,indent=2),encoding="utf-8"
    )
    (args.output/"raw_by_legend.json").write_text(
        json.dumps(processed,indent=2),encoding="utf-8"
    )
    print("ALL58_MUTATION_DISCOVERY_FINAL",json.dumps({
        k:v for k,v in payload.items() if k!="best_per_legend"}),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--proposals",type=pathlib.Path,required=True)
    p.add_argument("--ranked",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,default=pathlib.Path("engine_build/riftbound"))
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--shards",type=int,default=29)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--candidates",type=int,default=4)
    p.add_argument("--opponents",type=int,default=3)
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--agent",default="ismcts:sims=24")
    p.add_argument("--seed",type=int,default=202611240700)
    p.add_argument("--timeout",type=int,default=120)
    a=p.parse_args()
    if (not 1<=a.shards<=58 or not 0<=a.shard<a.shards or
        not 1<=a.candidates<=40 or not 1<=a.opponents<=9 or
        not 1<=a.workers<=8 or a.timeout<=0):
        p.error("Invalid research budget")
    if a.aggregate:
        if not a.input:
            p.error("--aggregate requires --input")
        aggregate(a)
    else:
        screen(a)


if __name__=="__main__":
    main()
