#!/usr/bin/env python3
"""Aggregate real fixed-deck BO3 shard results; fail closed on missing games."""
import argparse
import csv
import glob
import itertools
import json
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
    full=(len(headers)==shard_count and
          all(x["complete"] and x.get("series_incomplete",0)==0 for x in headers) and
          len(by_matchup)==1711 and len(series)==1711*expected_instances and
          all(x["series_complete"]==expected_instances for x in rows))
    report={
      "schema":1,
      "engine_based":True,"sideboarding":False,
      "limitations":"Fixed original decklists; no postgame sideboard choice; exploratory agents; do not interpret as tournament BO3 odds.",
      "expected_matchups":1711,"observed_matchups":len(by_matchup),
      "expected_series":1711*expected_instances,"observed_series":len(series),
      "complete":full,"shards_expected":shard_count,"shards_found":len(headers),
      "matchups":rows
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
    print("BO3_AGGREGATE",json.dumps({k:v for k,v in report.items() if k!="matchups"}))
    return 0 if full else 1

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--inputs",nargs="+",default=["results/bo3_shard_*.json"])
    p.add_argument("--output",default="results/bo3_all_matchups.json")
    sys.exit(main(p.parse_args()))
