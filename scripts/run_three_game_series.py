#!/usr/bin/env python3
"""Engine-played three-game series, with NO sideboard swaps. Not official BO3."""
import argparse, csv, hashlib, itertools, json, pathlib, time
from run_actual_games import ROOT, OUT, decode, header, gametest

ENGINE_COMMIT="ec90f0fed002aed374d06249fa95e83e3cfbd386"

def write_csv(path, rows, fields):
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--engine",default="alpharune/build/riftbound")
    p.add_argument("--agent",default="mcts:sims=10")
    p.add_argument("--seconds",type=int,default=90)
    p.add_argument("--budget-seconds",type=int,default=2400)
    args=p.parse_args()
    OUT.mkdir(exist_ok=True)
    named={header(f):f for f in decode()}
    exe=ROOT/args.engine
    if not exe.exists():
        raise SystemExit("Missing actual AlphaRune engine executable")
    anchor="Kennen, Heart of the Tempest"
    if anchor not in named: raise SystemExit("Missing validation anchor")
    validations=[]
    for i,(legend,deck) in enumerate(sorted(named.items())):
        result=gametest(exe,deck,named[anchor],2026112700+i,min(30,args.seconds),"random")
        validations.append({"legend":legend,"status":result["status"],"error":result["stderr_tail"][-500:]})
    (OUT/"bo3_validation.json").write_text(json.dumps(validations,indent=2),encoding="utf-8")
    ok=sorted(v["legend"] for v in validations if v["status"]=="complete")
    print(f"Engine-supported decks: {len(ok)}/58",flush=True)
    pairs=list(itertools.combinations_with_replacement(ok,2))
    games=[]
    series=[]
    start=time.monotonic()
    for idx,(a,b) in enumerate(pairs):
        if time.monotonic()-start>args.budget_seconds:
            print(f"TIME_BUDGET_REACHED pair={idx}/{len(pairs)}",flush=True)
            break
        for seat,(deck1,deck2) in enumerate(((a,b),(b,a))):
            wins1=wins2=0
            complete=True
            for game_no in range(1,4):
                seed=2026120000+idx*100+seat*10+game_no
                result=gametest(exe,named[deck1],named[deck2],seed,args.seconds,args.agent)
                if result["status"]!="complete" or result["winner"] not in (1,2):
                    complete=False
                elif result["winner"]==1: wins1+=1
                else: wins2+=1
                games.append({"pair":idx,"a":a,"b":b,"deck1":deck1,"deck2":deck2,
                              "seat":seat,"game":game_no,"seed":seed,"agent":args.agent,
                              "status":result["status"],"winner_seat":result["winner"],
                              "error":result["stderr_tail"][-400:]})
            series.append({"pair":idx,"a":a,"b":b,"deck1":deck1,"deck2":deck2,
                           "seat":seat,"agent":args.agent,"complete":complete,
                           "deck1_game_wins":wins1,"deck2_game_wins":wins2,
                           "series_winner":deck1 if complete and wins1>=2 else
                                           deck2 if complete and wins2>=2 else ""})
        if (idx+1)%50==0:
            print(f"Completed pairings {idx+1}/{len(pairs)}; games {len(games)}; elapsed {time.monotonic()-start:.0f}s",flush=True)
    write_csv(OUT/"bo3_games.csv",games,
              ["pair","a","b","deck1","deck2","seat","game","seed","agent","status","winner_seat","error"])
    write_csv(OUT/"bo3_series.csv",series,
              ["pair","a","b","deck1","deck2","seat","agent","complete","deck1_game_wins","deck2_game_wins","series_winner"])
    summaries=[]
    for (a,b) in pairs[:len(series)//2]:
        sub=[x for x in series if x["a"]==a and x["b"]==b]
        if len(sub)!=2 or not all(x["complete"] for x in sub):continue
        summaries.append({"a":a,"b":b,"series":len(sub),"a_wins":sum(x["series_winner"]==a for x in sub),
                          "b_wins":sum(x["series_winner"]==b for x in sub),
                          "note":"Mirror match" if a==b else "No sideboard changes; 3 engine games per series"})
    write_csv(OUT/"bo3_summary.csv",summaries,["a","b","series","a_wins","b_wins","note"])
    meta={"engine_commit":ENGINE_COMMIT,"agent":args.agent,"supported_decks":len(ok),
          "unsupported_decks":58-len(ok),"eligible_pairs":len(pairs),
          "completed_games":sum(x["status"]=="complete" for x in games),
          "attempted_games":len(games),
          "completed_series":sum(x["complete"] for x in series),
          "attempted_series":len(series),
          "tournament_accurate_bo3":False,
          "sideboarding":"none",
          "seating":"two reversed three-game series per pairing",
          "interpretation":"Gameplay engine results; not validated competitive win rates"}
    (OUT/"bo3_metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print("RESULT "+json.dumps(meta),flush=True)
    return 0 if len(games)>0 and all(x["status"]=="complete" for x in games) else 1

if __name__=="__main__":
    raise SystemExit(main())
