#!/usr/bin/env python3
"""Aggregate real fixed-deck BO3 shard results; fail closed on missing games."""
import argparse
import csv
import glob
import itertools
import json
import math
import pathlib
import sys
from collections import defaultdict

def main(args):
    files=sorted(pathlib.Path(x) for pattern in args.inputs for x in glob.glob(pattern))
    if not files:raise RuntimeError("No BO3 shard reports found")
    headers=[];series=[]
    for file in files:
        data=json.loads(file.read_text(encoding="utf-8"))
        if data.get("format")!="fixed_deck_best_of_three_NO_SIDEBOARD_CHANGES":
            raise RuntimeError("Unexpected or unsupported format: "+str(file))
        headers.append(data)
        series.extend(data["results"])
    agent = headers[0].get("agent")
    source = headers[0].get("source")
    if not isinstance(agent,str) or not agent.startswith("ismcts:sims="):
        raise RuntimeError("An ISMCTS-vs-ISMCTS matrix is required, not a random-agent run")
    if not source or any(h.get("agent") != agent or h.get("source") != source for h in headers):
        raise RuntimeError("Inconsistent gameplay agent or source deck roster across shards")
    shard_count=headers[0]["shards"]
    expected_instances=headers[0]["series_per_pair"]
    if not all(x["shards"]==shard_count and x["series_per_pair"]==expected_instances
               for x in headers):
        raise RuntimeError("Inconsistent shard plan")
    if len({x["shard"] for x in headers})!=len(headers):
        raise RuntimeError("Duplicate shard report")
    if len(headers)>shard_count:raise RuntimeError("Too many shards")
    by_matchup=defaultdict(list)
    seen=set()
    for row in series:
        key=(row["legend_a"],row["legend_b"],row["instance"])
        if key in seen:raise RuntimeError("Duplicate matchup instance "+str(key))
        seen.add(key)
        by_matchup[(row["legend_a"],row["legend_b"])].append(row)
    rows=[]
    for (a,b),items in sorted(by_matchup.items()):
        complete=[x for x in items if x["status"]=="complete"]
        wins_a=sum(x.get("winner_side")=="A" for x in complete)
        wins_b=sum(x.get("winner_side")=="B" for x in complete)
        rows.append({
          "legend_a":a,"legend_b":b,"mirror":a==b,
          "series_attempted":len(items),"series_complete":len(complete),
          "series_incomplete":len(items)-len(complete),
          "wins_a_side":wins_a,"wins_b_side":wins_b,
          "a_winrate_fixed_decks":None if a==b or not complete else round(wins_a/len(complete),5)
        })
    # Aggregate each non-mirror pairing equally into exploratory per-legend
    # rates; mirrors have no distinct opponent and must not affect rankings.
    totals=defaultdict(lambda:{"wins":0,"losses":0,"series":0,"opponents":set()})
    for m in rows:
        if m["mirror"]:continue
        a,b=m["legend_a"],m["legend_b"]
        n=m["series_complete"]
        wa,wb=m["wins_a_side"],m["wins_b_side"]
        totals[a]["wins"]+=wa;totals[a]["losses"]+=wb;totals[a]["series"]+=n
        totals[b]["wins"]+=wb;totals[b]["losses"]+=wa;totals[b]["series"]+=n
        totals[a]["opponents"].add(b);totals[b]["opponents"].add(a)
    def wilson(w,n):
        if not n:return (None,None)
        z=1.959963984540054;p=w/n;z2=z*z
        centre=(p+z2/(2*n))/(1+z2/n)
        half=z*math.sqrt(p*(1-p)/n+z2/(4*n*n))/(1+z2/n)
        return (round(max(0,centre-half),5),round(min(1,centre+half),5))
    leaderboard=[]
    for name,m in totals.items():
        low,high=wilson(m["wins"],m["series"])
        leaderboard.append({
           "legend":name,"series_played":m["series"],
           "series_won":m["wins"],"series_lost":m["losses"],
           "win_rate_ismcts":(round(m["wins"]/m["series"],5) if m["series"] else None),
           "mc_wilson95_low":low,"mc_wilson95_high":high,
           "opponents_seen":len(m["opponents"]),
        })
    leaderboard.sort(key=lambda r:(-(r["win_rate_ismcts"] if r["win_rate_ismcts"] is not None else -1),r["legend"]))
    for i,row in enumerate(leaderboard,1):row["rank_ismcts"]=i
    full=(len(headers)==shard_count and
          all(x["complete"] and x.get("series_incomplete",0)==0 for x in headers) and
          len(by_matchup)==1711 and len(series)==1711*expected_instances and
          all(x["series_complete"]==expected_instances for x in rows))
    report={
      "schema":2,
      "engine_based":True,"sideboarding":False,
      "agent":agent,
      "deck_source":source,
      "ismcts_search_budget_per_decision":int(agent.split("sims=",1)[1]),
      "limitations":"ISMCTS against ISMCTS with sampled hidden information; 54 unchanged original lists and four disclosed legal corrections; fixed-deck BO3 without sideboard swaps; provisional rules coverage. Not established tournament odds.",
      "expected_matchups":1711,"observed_matchups":len(by_matchup),
      "expected_series":1711*expected_instances,"observed_series":len(series),
      "complete":full,"shards_expected":shard_count,"shards_found":len(headers),
      "matchups":rows,
      "legend_rankings":leaderboard
    }
    output=pathlib.Path(args.output)
    output.parent.mkdir(exist_ok=True,parents=True)
    output.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    csv_path=output.with_suffix(".csv")
    with csv_path.open("w",newline="",encoding="utf-8") as fp:
        if rows:
            writer=csv.DictWriter(fp,fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    ranks_path=output.with_name("bo3_legend_rankings.csv")
    with ranks_path.open("w",newline="",encoding="utf-8") as fp:
        if leaderboard:
            writer=csv.DictWriter(fp,fieldnames=list(leaderboard[0]))
            writer.writeheader()
            writer.writerows(leaderboard)
    print("BO3_LEADERBOARD",json.dumps({"legends":len(leaderboard),"top5":leaderboard[:5],
                                        "agent":agent,"sideboarding":False}))
    print("BO3_AGGREGATE",json.dumps({k:v for k,v in report.items() if k!="matchups"}))
    return 0 if full else 1

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--inputs",nargs="+",default=["results/bo3_shard_*.json"])
    p.add_argument("--output",default="results/bo3_all_matchups.json")
    sys.exit(main(p.parse_args()))
