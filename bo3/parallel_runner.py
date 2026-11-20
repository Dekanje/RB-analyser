#!/usr/bin/env python3
"""Parallel three-game AlphaRune series: actual gameplay; never tournament BO3 without sideboarding."""
import argparse, csv, itertools, json, pathlib, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_actual_games import decode, header, gametest
ENGINE="ec90f0fed002aed374d06249fa95e83e3cfbd386"

def csv_out(p, rows, fields):
    with p.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--index",required=True,type=int)
    p.add_argument("--count",default=8,type=int)
    p.add_argument("--agent",default="mcts:sims=10")
    p.add_argument("--seconds",default=90,type=int)
    p.add_argument("--budget",default=1700,type=int)
    a=p.parse_args()
    assert 0<=a.index<a.count
    out=ROOT/"results";out.mkdir(exist_ok=True)
    exe=ROOT/"alpharune/build/riftbound"
    if not exe.is_file():raise SystemExit("Engine binary missing")
    decks={header(f):f for f in decode()}
    anchor="Kennen, Heart of the Tempest"
    checks=[]
    for i,(n,deck) in enumerate(sorted(decks.items())):
        r=gametest(exe,deck,decks[anchor],2026112700+i,30,"random")
        checks.append({"legend":n,"status":r["status"],"error":r["stderr_tail"][-300:]})
    (out/"validation.json").write_text(json.dumps(checks,indent=2))
    ok=sorted(x["legend"] for x in checks if x["status"]=="complete")
    allpairs=list(itertools.combinations_with_replacement(ok,2))
    selection=[(i,left,right) for i,(left,right) in enumerate(allpairs) if i % a.count == a.index]
    print(f"SHARD {a.index}/{a.count}: supported={len(ok)} pairings={len(selection)}/{len(allpairs)}",flush=True)
    games=[];series=[];summaries=[]
    started=time.monotonic()
    for i,na,nb in selection:
        if time.monotonic()-started>a.budget:
            print(f"BUDGET_STOP {i}",flush=True);break
        pair_series=[]
        for seat,(d1,d2) in enumerate(((na,nb),(nb,na))):
            w1=w2=0;complete=True
            for gn in range(1,4):
                seed=2026120000+i*100+seat*10+gn
                r=gametest(exe,decks[d1],decks[d2],seed,a.seconds,a.agent)
                if r["status"]=="complete" and r["winner"]==1:w1+=1
                elif r["status"]=="complete" and r["winner"]==2:w2+=1
                else:complete=False
                games.append({"pair":i,"a":na,"b":nb,"deck1":d1,"deck2":d2,
                              "seat":seat,"game":gn,"seed":seed,"agent":a.agent,
                              "status":r["status"],"winner_seat":r["winner"],
                              "error":r["stderr_tail"][-300:]})
            winner=d1 if complete and w1>=2 else d2 if complete and w2>=2 else ""
            s={"pair":i,"a":na,"b":nb,"deck1":d1,"deck2":d2,"seat":seat,
               "agent":a.agent,"complete":complete,"wins_deck1":w1,
               "wins_deck2":w2,"series_winner":winner}
            series.append(s);pair_series.append(s)
        if all(s["complete"] for s in pair_series):
            summaries.append({"pair":i,"a":na,"b":nb,"a_wins":sum(s["series_winner"]==na for s in pair_series),
                              "b_wins":sum(s["series_winner"]==nb for s in pair_series),
                              "mirror":na==nb})
        if len(summaries)%20==0 and len(summaries)>0:
            print(f"SHARD {a.index}: {len(summaries)}/{len(selection)} pairings; {len(games)} games",flush=True)
    csv_out(out/"games.csv",games,["pair","a","b","deck1","deck2","seat","game","seed","agent","status","winner_seat","error"])
    csv_out(out/"series.csv",series,["pair","a","b","deck1","deck2","seat","agent","complete","wins_deck1","wins_deck2","series_winner"])
    csv_out(out/"summary.csv",summaries,["pair","a","b","a_wins","b_wins","mirror"])
    meta={"shard":a.index,"shards":a.count,"engine":ENGINE,"agent":a.agent,
          "supported":len(ok),"all_pairings":len(allpairs),"selected":len(selection),
          "completed_pairings":len(summaries),"attempted_games":len(games),
          "completed_games":sum(g["status"]=="complete" for g in games),
          "tournament_BO3":False,"sideboarding":False}
    (out/"metadata.json").write_text(json.dumps(meta,indent=2))
    print("RESULT "+json.dumps(meta),flush=True)
    return 0 if len(summaries)==len(selection) and len(games)==len(selection)*6 else 1


if __name__=="__main__":raise SystemExit(main())
