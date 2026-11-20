#!/usr/bin/env python3
"""Merge shards and reject missing, duplicate or incompatible simulation results."""
import csv, json, pathlib
from collections import defaultdict
ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=ROOT/"shard_artifacts";DEST=ROOT/"combined_results";DEST.mkdir(exist_ok=True)
def read_csv(p):
    with p.open(newline="",encoding="utf8") as f:return list(csv.DictReader(f))
def write_csv(path,rows,headers):
    with path.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=headers);w.writeheader();w.writerows(rows)
def main():
    folders=sorted(p for p in SRC.glob("bo3-shard-*") if p.is_dir())
    metas=[];games=[];series=[];summary=[]
    for f in folders:
        metas.append(json.loads((f/"metadata.json").read_text()))
        games.extend(read_csv(f/"games.csv"))
        series.extend(read_csv(f/"series.csv"))
        summary.extend(read_csv(f/"summary.csv"))
    if not metas:raise SystemExit("No shards")
    count=metas[0]["shards"]
    if {x["shard"] for x in metas}!=set(range(count)) or len(metas)!=count:
        raise SystemExit("Incomplete or duplicate shards")
    if any((x["engine"],x["agent"],x["supported"],x["all_pairings"]) !=
           (metas[0]["engine"],metas[0]["agent"],metas[0]["supported"],metas[0]["all_pairings"])
           for x in metas):raise SystemExit("Inconsistent configurations")
    ids=[int(x["pair"]) for x in summary]
    expect=metas[0]["all_pairings"]
    good=(len(ids)==expect and set(ids)==set(range(expect))
          and len(games)==expect*6 and len(series)==expect*2
          and all(x["status"]=="complete" for x in games)
          and all(x["complete"]=="True" for x in series))
    games.sort(key=lambda r:(int(r["pair"]),int(r["seat"]),int(r["game"])))
    series.sort(key=lambda r:(int(r["pair"]),int(r["seat"])))
    summary.sort(key=lambda r:int(r["pair"]))
    write_csv(DEST/"all_games.csv",games,list(games[0]) if games else ["pair"])
    write_csv(DEST/"all_series.csv",series,list(series[0]) if series else ["pair"])
    write_csv(DEST/"all_matchups.csv",summary,list(summary[0]) if summary else ["pair"])
    ranks=defaultdict(lambda:[0,0])
    for x in summary:
        if x["a"]==x["b"]:continue
        aw,bw=int(x["a_wins"]),int(x["b_wins"])
        ranks[x["a"]][0]+=aw;ranks[x["a"]][1]+=bw
        ranks[x["b"]][0]+=bw;ranks[x["b"]][1]+=aw
    ranking=[{"legend":n,"series_wins":v[0],"series_losses":v[1],
              "win_fraction":round(v[0]/sum(v),4)} for n,v in ranks.items()]
    ranking.sort(key=lambda x:(-x["win_fraction"],x["legend"]))
    write_csv(DEST/"exploratory_ranking.csv",ranking,
              ["legend","series_wins","series_losses","win_fraction"])
    data={"complete":good,"shards":count,"supported_decks":metas[0]["supported"],
          "pairings":len(summary),"expected_pairings":expect,"actual_engine_games":len(games),
          "series":len(series),"agent":metas[0]["agent"],"engine":metas[0]["engine"],
          "sideboarding":False,"tournament_BO3":False,
          "caution":"Two reversed-seat, fixed three-game series per matchup; not tournament BO3 or robust competitive win probabilities"}
    (DEST/"metadata.json").write_text(json.dumps(data,indent=2))
    print("AGGREGATE "+json.dumps(data),flush=True)
    return 0 if good else 1
if __name__=="__main__":raise SystemExit(main())
