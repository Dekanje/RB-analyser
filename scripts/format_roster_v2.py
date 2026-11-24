#!/usr/bin/env python3
"""Scoped native roster certification, not a strength comparison."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
from format_match_v2 import VerifiedGateway, FormatRejected, digest
from optimize_58 import stable_seed

MANIFEST_REPORT_SHA="123420b3eae9650b20c2b978d83d3e3a69700115d76afadd88b0ebefad81d934"
REPLACEMENTS={"ahri_nine_tailed_fox.txt":("Ahri, Inquisitive",119),
              "yasuo_unforgiven.txt":("Yasuo, Windrider",205)}
SEED=2026112413
AGENT="ismcts:sims=24"

def load_roster(g, selected, prior):
    raw=prior.read_bytes()
    if digest(raw)!=MANIFEST_REPORT_SHA:
        raise FormatRejected("unapproved prior manifest")
    manifest=json.loads(raw)["manifest"]
    names={r["file"] for r in manifest}
    if len(manifest)!=58 or len(names)!=58 or names!={p.name for p in selected.glob("*.txt")}:
        raise FormatRejected("incomplete roster manifest")
    roster={}
    legend_ids=set()
    for r in manifest:
        name=r["file"]
        raw=(selected/name).read_bytes()
        if digest(raw)!=r["source_sha256"]:
            raise FormatRejected("source hash mismatch: "+name)
        if name in REPLACEMENTS:
            card,i=REPLACEMENTS[name]
            old=("1 "+card+"\n").encode()
            if raw.count(old)!=1:
                raise FormatRejected("ambiguous historical registration changed")
            raw=raw.replace(old,("1 "+card+" #"+str(i)+"\n").encode(),1)
        if digest(raw)!=r["explicit_sha256"]:
            raise FormatRejected("explicit hash mismatch: "+name)
        v=g.gate.validate(raw)
        if v["Legend"][0] in legend_ids:
            raise FormatRejected("duplicate legend identity")
        legend_ids.add(v["Legend"][0])
        roster[name]=raw
    return roster

def schedule(names):
    names=sorted(names)
    if len(names)!=58 or len(set(names))!=58:
        raise FormatRejected("expected 58 distinct names")
    result=[]
    for i in range(0,len(names),2):
        a,b=names[i:i+2]
        seed=stable_seed(SEED,"roster_cert_v2",a,b) or 1
        for flip in (False,True):
            result.append({"index":len(result),"one":b if flip else a,
                           "two":a if flip else b,"seed":seed})
    return result

def verify_coverage(rows, names):
    if len(rows)!=58 or {r["index"] for r in rows}!=set(range(58)):
        raise FormatRejected("incomplete or duplicate game receipts")
    expected=schedule(names)
    for r in rows:
        if any(r[k]!=expected[r["index"]][k] for k in ("one","two","seed")):
            raise FormatRejected("schedule changed")
        game=r["receipt"]
        if game["status"]!="complete" or game["winner"] not in (1,2) or game["native_ids_verified"] is not True:
            raise FormatRejected("incomplete native game")
    for key in ("one","two"):
        if Counter(r[key] for r in rows)!=Counter(names):
            raise FormatRejected("not all legends represented in both seats")

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("engine","registry","profile","selected","prior","output"):
        p.add_argument("--"+n,type=Path,required=True)
    p.add_argument("--workers",type=int,default=2)
    a=p.parse_args()
    if not 1<=a.workers<=4:
        p.error("workers must be 1–4")
    g=VerifiedGateway(a.engine,a.registry,a.profile,("OGN","OGS","SFD","UNL","VEN","RAD"))
    roster=load_roster(g,a.selected,a.prior)
    cases=schedule(roster)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x",encoding="utf-8") as out:
        def run(row):
            try:
                r=g.game(roster[row["one"]],roster[row["two"]],row["seed"],AGENT)
                return {**row,"receipt":r}
            except Exception as exc:
                return {**row,"receipt":{"status":"error","error":str(exc)}}
        with ThreadPoolExecutor(max_workers=a.workers) as workers:
            rows=list(workers.map(run,cases))
        report={**g.provenance(),"status":"FAILED","games":rows,"roster_count":len(roster),
                "source_manifest_report_sha256":MANIFEST_REPORT_SHA,"agent":AGENT,
                "native_games_completed":sum(r["receipt"]["status"]=="complete" for r in rows),
                "adopted":0,"fitness_evaluated":False}
        try:
            verify_coverage(rows,roster)
            report["status"]="PASS_SCOPED_NATIVE_ROSTER"
        finally:
            json.dump(report,out,indent=2)
        print(report["status"],report["native_games_completed"])

if __name__=="__main__":
    main()
