#!/usr/bin/env python3
"""Actual AlphaRune best-of-three games on original optimized decks.

Each result is produced by real deterministic C++ engine games. This is a
FIXED-DECK best-of-three: no between-game sideboard choices. Do not mistake
it for a complete tournament match. No synthetic wins, no unsupported cards.
"""
import argparse
import hashlib
import itertools
import json
import pathlib
import sys
import time

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_actual_games import decode, header, gametest

def atomic_write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp=path.with_suffix(path.suffix+".tmp")
    tmp.write_text(json.dumps(obj,indent=2,ensure_ascii=False),encoding="utf-8")
    tmp.replace(path)

def validate_manifest(decks, validation):
    data=json.loads(validation.read_text(encoding="utf-8"))
    if data.get("deck_count")!=58 or data.get("failed")!=0:
        raise RuntimeError("Original 58-deck validation not fully passed")
    if data.get("complete")!=data.get("games") or data.get("games",0)<58:
        raise RuntimeError("Insufficient verified original-game receipts")
    verified={}
    for row in data["records"]:
        if row["status"]!="complete":raise RuntimeError(row["legend"]+" failed")
        name=row["legend"]
        if name in verified and verified[name]!=row["original_sha256"]:
            raise RuntimeError("SHA disagreement for "+name)
        verified[name]=row["original_sha256"]
    if set(verified)!=set(decks):raise RuntimeError("58-legend roster mismatch")
    for name,path in decks.items():
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        if actual!=verified[name]:raise RuntimeError("Original deck content changed: "+name)

def run_series(exe,decks,a,b,index,instance,seconds,agent):
    score={"A":0,"B":0}; games=[]
    for n in range(3):
        first_side="A" if (n+instance)%2==0 else "B"
        second_side="B" if first_side=="A" else "A"
        first=a if first_side=="A" else b
        second=b if second_side=="B" else a
        # Both competitors remain distinct even in same-legend mirror games.
        # Mirrored first-game seat in instance 2, deterministic distinct seeds.
        seed=202611300000 + index*100 + instance*10 + n
        result=gametest(exe,decks[first],decks[second],seed,seconds,agent)
        entry={"number":n+1,"seed":seed,"seat1":first,"seat2":second,
               "status":result["status"],"winner_seat":result["winner"],
               "returncode":result["returncode"],"stderr_tail":result["stderr_tail"][-900:]}
        if result["status"]!="complete" or result["winner"] not in (1,2):
            games.append(entry)
            return {"legend_a":a,"legend_b":b,"instance":instance,"status":"incomplete",
                    "reason":"Failed, timed-out, or tied engine game. No winner assigned.",
                    "games":games}
        winner_side=first_side if result["winner"]==1 else second_side
        winner=first if result["winner"]==1 else second
        entry["winner"]=winner
        entry["winner_side"]=winner_side
        games.append(entry)
        score[winner_side]+=1
        if score[winner_side]==2:
            return {"legend_a":a,"legend_b":b,"instance":instance,"status":"complete",
                    "winner":winner,"winner_side":winner_side,"score":score,
                    "mirror":a==b,"games":games}
    return {"legend_a":a,"legend_b":b,"instance":instance,"status":"incomplete",
            "reason":"No player reached two wins.","games":games}

def main(args):
    original=decode()
    decks={header(p):p for p in original}
    if len(decks)!=58:raise RuntimeError(f"Expected 58, got {len(decks)}")
    validate_manifest(decks,ROOT/args.validation)
    exe=ROOT/args.engine
    if not exe.exists():raise RuntimeError("Missing real C++ executable: "+str(exe))
    if not 0<=args.shard<args.shards:raise RuntimeError("Invalid shard")
    pairings=list(itertools.combinations_with_replacement(sorted(decks),2))
    assert len(pairings)==1711, len(pairings)
    selected=[(i,a,b) for i,(a,b) in enumerate(pairings) if i%args.shards==args.shard]
    report={"schema":1,"engine":"pinned_alpha_rune_plus_radiance_overlay",
            "format":"fixed_deck_best_of_three_NO_SIDEBOARD_CHANGES",
            "agent":args.agent,
            "source":"58 original validated SHA-pinned decks",
            "shard":args.shard,"shards":args.shards,
            "total_pairings":1711,"shard_pairings":len(selected),
            "series_per_pair":args.series_per_pair,"results":[],
            "complete":False}
    output=ROOT/args.output
    start=time.monotonic()
    for index,a,b in selected:
        if args.max_seconds and time.monotonic()-start>args.max_seconds:
            print("BUDGET_REACHED: remaining pairings not evaluated",flush=True)
            break
        for instance in range(args.series_per_pair):
            row=run_series(exe,decks,a,b,index,instance,args.seconds,args.agent)
            report["results"].append(row)
            print(f"PAIR {index+1:04d}/1711 [{instance+1}/{args.series_per_pair}] "
                  f"{a} vs {b}: {row['status']}"
                  + (" winner "+row["winner"] if row["status"]=="complete" else ""),flush=True)
            atomic_write(output,report)
    report["complete"]=len(report["results"])==len(selected)*args.series_per_pair
    report["series_complete"]=sum(x["status"]=="complete" for x in report["results"])
    report["series_incomplete"]=len(report["results"])-report["series_complete"]
    atomic_write(output,report)
    print("ENGINE_BEST_OF_THREE_SUMMARY",json.dumps({k:v for k,v in report.items() if k!="results"}))
    return 0 if report["complete"] and report["series_incomplete"]==0 else 1

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--engine",default="alpharune/build/riftbound")
    p.add_argument("--validation",default="results/all_58_engine_validation.json")
    p.add_argument("--output",default="results/bo3_shard.json")
    p.add_argument("--shards",type=int,default=16)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--series-per-pair",type=int,default=2)
    p.add_argument("--agent",default="random")
    p.add_argument("--seconds",type=int,default=60)
    p.add_argument("--max-seconds",type=int,default=2300)
    a=p.parse_args()
    if a.shards<1 or a.series_per_pair not in (1,2) or a.seconds<1:
        p.error("shards >=1, series-per-pair 1 or 2, seconds >=1")
    sys.exit(main(a))
