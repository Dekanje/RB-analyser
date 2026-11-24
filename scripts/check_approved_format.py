#!/usr/bin/env python3
"""Native controls for named configurations; not a fitness campaign."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from approved_format import APPROVED, ApprovedGateway
from format_roster_v2 import load_roster

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("engine","registry","profile","selected","prior","output"):
        p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args()
    ids=("standard-2026-11-23-research-v1","hypothetical-exclude-ogs-v1")
    g=ApprovedGateway(a.engine,a.registry,a.profile,ids[0])
    roster=load_roster(g,a.selected,a.prior)
    n1,n2=sorted(roster)[:2]
    root=a.output.parent/"approved_fixture"
    root.mkdir(parents=True,exist_ok=False)
    d1=root/"one.txt";d2=root/"two.txt"
    d1.write_bytes(roster[n1]);d2.write_bytes(roster[n2])
    cmd=[sys.executable,str(Path(__file__).with_name("run_approved_match.py")),
         "--engine",str(a.engine),"--registry",str(a.registry),"--profile",str(a.profile),
         "--deck1",str(d1),"--deck2",str(d2),"--seed","2026112415","--mode","single"]
    def run(config,out):
        q=subprocess.run(cmd+["--configuration",config,"--output",str(out)],
                         capture_output=True,text=True,timeout=240)
        return q,json.loads(out.read_bytes()) if out.exists() else None
    positive=[]
    for i,config in enumerate(ids):
        q,r=run(config,root/f"positive{i}.json")
        if q.returncode or r["status"]!="complete" or not r["native_ids_verified"] \
                or r["configuration_sha256"]!=APPROVED[config]:
            raise RuntimeError("native configuration control failed: "+q.stderr[-1500:])
        positive.append(r)
    for k in ("winner","turns","reason","deck_sha256","native_vectors_sha256"):
        if positive[0][k]!=positive[1][k]:
            raise RuntimeError("set filter changed identical legal gameplay: "+k)
    # Explicit OGS-only unit, rejected before native launch by restricted profile.
    raw=roster[n1].replace(b"MainDeck:\n",b"MainDeck:\n1 Tibbers #316\n",1)
    if raw==roster[n1]:
        raise RuntimeError("invalid negative fixture")
    d1.write_bytes(raw)
    q,r=run(ids[1],root/"set_reject.json")
    if q.returncode==0 or r.get("winner") is not None or "set excluded" not in r.get("error",""):
        raise RuntimeError("restricted configuration did not fail closed")
    d1.write_bytes(roster[n1].replace(b"Battlefields:\n",b"Battlefields:\n1 Star Spring\n",1))
    q,b=run(ids[0],root/"ban_reject.json")
    if q.returncode==0 or b.get("winner") is not None or "banned" not in b.get("error",""):
        raise RuntimeError("standard configuration ban did not fail closed")
    q,unknown=run("worlds-no-legacy",root/"unknown.json")
    if q.returncode==0 or unknown is not None:
        raise RuntimeError("unapproved configuration accepted")
    report={"status":"PASS_APPROVED_CONFIG_CONTROLS","native_games":2,
            "positive":positive,"negative_set":r,"negative_ban":b,
            "unknown_configuration_rejected":True,"adopted":0}
    with a.output.open("x") as fp:
        json.dump(report,fp,indent=2)
    print(report["status"])

if __name__=="__main__":
    main()
