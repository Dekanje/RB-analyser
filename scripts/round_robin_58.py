#!/usr/bin/env python3
"""Complete optimized-vs-optimized 58-legend round robin using real AlphaRune BO3.

Each unordered pair is evaluated in both seating orders, never fabricated from
heuristics. All engine failures are retained and cause fail-closed aggregation.
Fixed decks; neither sideboard swaps nor tournament-optimal play is modeled.
"""
import argparse
import collections
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from optimize_58 import stable_seed
from evaluate_radiance_ismcts import engine_bo3
from run_actual_games import header


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_decks(folder):
    root = folder / "selected_decks"
    cards = list(root.glob("*.txt"))
    decks = {header(p):p for p in cards}
    trials = json.loads((folder / "all_58_trials.json").read_text(encoding="utf-8"))
    if len(cards) != 58 or len(decks) != 58 or len(trials) != 58:
        raise RuntimeError("Expected 58 distinct legend decklists with SHA receipts")
    if {r["legend"] for r in trials} != set(decks):
        raise RuntimeError("Rooster legend names do not match trial manifest")
    for r in trials:
        if sha(decks[r["legend"]]) != r["effective_sha256"]:
            raise RuntimeError("Source SHA mismatch: " + r["legend"])
    return decks, {r["legend"]:r for r in trials}


def pair_schedule(names, shard=0, shards=1, repeats=1, seed=2026112399193):
    """All choose(58,2) pairs, mirrored seats and deterministic blind seeds."""
    sorted_names = sorted(names)
    index = 0
    for i,a in enumerate(sorted_names):
        for b in sorted_names[i+1:]:
            for seat in (0,1):
                for rep in range(repeats):
                    if index % shards == shard:
                        yield {"a":a, "b":b, "seat":seat, "repetition":rep,
                               "seed":stable_seed(seed,a,b,seat,rep,"OPTIMIZED_ROUND_ROBIN")}
            index += 1


def wilson(wins, n, z=1.9599639845):
    if not n:
        return (None,None)
    p=wins/n
    q=z*z
    center=(p+q/(2*n))/(1+q/n)
    half=z*math.sqrt((p*(1-p)+q/(4*n))/n)/(1+q/n)
    return (round(max(0,center-half),4),round(min(1,center+half),4))


def run(args):
    args.output.mkdir(parents=True,exist_ok=True)
    decks,_=load_decks(args.selected)
    scenarios=list(pair_schedule(decks,args.shard,args.shards,args.repetitions,args.seed))
    exe=args.engine.resolve()
    env=os.environ.copy()

    def play(item):
        a=decks[item["a"]];b=decks[item["b"]]
        game=engine_bo3(exe,a,b,item["seat"],item["seed"],args.agent,args.timeout,env)
        complete=game["status"]=="complete" and game["winner"] in (1,2)
        return {**item,"complete":complete,"status":game["status"],
                "winner":("a" if game["winner"]==item["seat"]+1 else "b")
                 if complete else None,
                "error":game.get("error",""),
                "games":game.get("games",[]),
                "a_sha256":sha(a),"b_sha256":sha(b)}
    rows=[]
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures=[pool.submit(play,s) for s in scenarios]
        for i,future in enumerate(concurrent.futures.as_completed(futures),1):
            rows.append(future.result())
            if i%25==0:
                print("OPTIMIZED_ROUND_ROBIN",args.shard,i,len(scenarios),flush=True)
    rows.sort(key=lambda x:(x["a"],x["b"],x["seat"],x["repetition"]))
    data={"shard":args.shard,"shards":args.shards,"repetitions":args.repetitions,
          "expected_scenarios":len(scenarios),"completed_scenarios":sum(r["complete"] for r in rows),
          "scenario_results":rows}
    (args.output/"round_robin.json").write_text(json.dumps(data,indent=2))
    print("ROUND_ROBIN_SHARD_END",args.shard,data["completed_scenarios"],
          "/",data["expected_scenarios"],flush=True)
    if data["completed_scenarios"]!=data["expected_scenarios"]:
        raise RuntimeError("Engine failures in round robin; no fabricated match outcomes")


def aggregate(args):
    args.output.mkdir(parents=True,exist_ok=True)
    decks,manifest=load_decks(args.selected)
    expected=set((s["a"],s["b"],s["seat"],s["repetition"]) for
                 s in pair_schedule(decks,0,1,args.repetitions,args.seed))
    all_rows=[]
    for index in range(args.shards):
        folder=args.input/f"optimized-round-robin-shard-{index}"
        packet=json.loads((folder/"round_robin.json").read_text())
        if packet["shard"]!=index or packet["shards"]!=args.shards or packet["repetitions"]!=args.repetitions:
            raise RuntimeError("Wrong shard metadata: "+str(folder))
        if packet["completed_scenarios"] != packet["expected_scenarios"]:
            raise RuntimeError("Incomplete engine outcomes: "+str(folder))
        all_rows.extend(packet["scenario_results"])
    actual=[(r["a"],r["b"],r["seat"],r["repetition"]) for r in all_rows]
    if len(actual)!=len(expected) or set(actual)!=expected:
        raise RuntimeError("Missing, duplicated or extra optimized field matchups")
    for r in all_rows:
        if (not r["complete"] or r["a_sha256"]!=sha(decks[r["a"]]) or
                r["b_sha256"]!=sha(decks[r["b"]]) or r["winner"] not in ("a","b")):
            raise RuntimeError("Invalid match record or source SHA drift")
    by=collections.defaultdict(lambda:{"wins":0,"played":0,"vs":{}})
    for r in all_rows:
        for own,other,won in ((r["a"],r["b"],r["winner"]=="a"),
                              (r["b"],r["a"],r["winner"]=="b")):
            by[own]["played"]+=1
            by[own]["wins"]+=int(won)
            d=by[own]["vs"].setdefault(other,{"wins":0,"played":0})
            d["played"]+=1
            d["wins"]+=int(won)
    summary=[]
    for name in sorted(decks):
        s=by[name]
        expected_matches=57*2*args.repetitions
        if s["played"]!=expected_matches or len(s["vs"])!=57:
            raise RuntimeError("Incomplete per-legend round robin: "+name)
        low,high=wilson(s["wins"],s["played"])
        summary.append({"legend":name,"wins":s["wins"],"played":s["played"],
                        "win_rate":round(s["wins"]/s["played"],6),
                        "wilson95_low":low,"wilson95_high":high,
                        "against_57":s["vs"],"deck_sha256":sha(decks[name]),
                        "candidate_changed":bool(manifest[name]["selected"])})
    ranked=sorted(summary,key=lambda r:(-r["win_rate"],r["legend"]))
    for i,row in enumerate(ranked,1):
        row["rank_exploratory"]=i
    with (args.output/"all_58_ranked.csv").open("w",newline="") as fp:
        writer=csv.writer(fp)
        writer.writerow(["rank","legend","wins","bo3_series","win_rate","wilson95_low",
                         "wilson95_high","candidate_changed","sha256"])
        for r in ranked:
            writer.writerow([r["rank_exploratory"],r["legend"],r["wins"],r["played"],
                             r["win_rate"],r["wilson95_low"],r["wilson95_high"],
                             r["candidate_changed"],r["deck_sha256"]])
    (args.output/"all_58_ranked.json").write_text(json.dumps(ranked,indent=2))
    (args.output/"matchups.json").write_text(json.dumps(sorted(all_rows,
                           key=lambda x:(x["a"],x["b"],x["seat"],x["repetition"])),indent=2))
    meta={"legends":58,"unordered_matchups":1653,"both_seating_orders":True,
          "repetitions_per_seat":args.repetitions,
          "total_engine_bo3_series":len(all_rows),
          "all_scenarios_complete":True,"agent":args.agent,
          "opponent_roster":"the 58 simultaneously selected exploratory decks",
          "field":"all 58 vs all other 57","sideboard_swaps":False,
          "globally_optimal":False,
          "ranking_meaning":"exhaustive sampled fixed-deck BO3 league, not predicted tournament standings"}
    (args.output/"summary.json").write_text(json.dumps(meta,indent=2))
    print("ALL_58_OPTIMIZED_ROUND_ROBIN_FINAL",json.dumps(meta),flush=True)


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,default=pathlib.Path("engine_build/riftbound"))
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--shards",type=int,default=29)
    p.add_argument("--repetitions",type=int,default=1)
    p.add_argument("--agent",default="ismcts:sims=24")
    p.add_argument("--workers",type=int,default=4)
    p.add_argument("--timeout",type=int,default=65)
    p.add_argument("--seed",type=int,default=2026112399193)
    args=p.parse_args()
    if not 0<=args.shard<args.shards<=58 or not 1<=args.repetitions<=10 or not 1<=args.workers<=16:
        p.error("Invalid shard or sample budget")
    if args.aggregate:
        if not args.input:
            p.error("Aggregate mode needs --input")
        aggregate(args)
    else:
        run(args)
