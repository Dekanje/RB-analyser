#!/usr/bin/env python3
"""Direct guarded CLI smoke, including fail-closed bans and output immutability."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
from format_roster_v2 import load_roster
from format_match_v2 import VerifiedGateway, digest

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("engine","registry","profile","selected","prior","output"):
        p.add_argument("--"+name,type=Path,required=True)
    a=p.parse_args()
    sets=("OGN","OGS","SFD","UNL","VEN","RAD")
    g=VerifiedGateway(a.engine,a.registry,a.profile,sets)
    roster=load_roster(g,a.selected,a.prior)
    one,two=sorted(roster)[:2]
    root=a.output.parent/"cli_fixture"
    root.mkdir(parents=True,exist_ok=False)
    d1=root/"p1.txt";d2=root/"p2.txt"
    d1.write_bytes(roster[one]);d2.write_bytes(roster[two])
    policy=root/"policy.json";policy.write_text("{}")
    cmd=[sys.executable,str(Path(__file__).with_name("run_verified_match.py")),
         "--engine",str(a.engine),"--registry",str(a.registry),"--profile",str(a.profile),
         "--sets",*sets,"--deck1",str(d1),"--deck2",str(d2),"--seed","2026112414"]
    def execute(args):
        return subprocess.run(cmd+args,capture_output=True,text=True,timeout=600)
    single=root/"single.json"
    q=execute(["--mode","single","--output",str(single)])
    if q.returncode!=0:
        raise RuntimeError(q.stderr[-2000:])
    r=json.loads(single.read_bytes())
    if r["status"]!="complete" or not r["native_ids_verified"]:
        raise RuntimeError("single receipt incomplete")
    before=digest(single.read_bytes())
    q=execute(["--mode","single","--output",str(single)])
    if q.returncode==0 or digest(single.read_bytes())!=before:
        raise RuntimeError("existing output was not protected")
    bo3=root/"bo3.json"
    q=execute(["--mode","declared-bo3","--policy",str(policy),"--output",str(bo3)])
    if q.returncode!=0:
        raise RuntimeError(q.stderr[-2000:])
    m=json.loads(bo3.read_bytes())
    if m["status"]!="complete_declared_bo3" or not all(x["native_ids_verified"] for x in m["games"]):
        raise RuntimeError("BO3 receipt incomplete")
    # New illegal input; preserve the original registration and fixture receipts.
    raw=roster[one].replace(b"Battlefields:\n",b"Battlefields:\n1 Star Spring\n",1)
    if raw==roster[one]:
        raise RuntimeError("bad negative fixture")
    d1.write_bytes(raw)
    bad=root/"banned.json"
    q=execute(["--mode","single","--output",str(bad)])
    b=json.loads(bad.read_bytes())
    if q.returncode==0 or b.get("status")!="error" or b.get("winner") is not None or "banned" not in b.get("error",""):
        raise RuntimeError("ban did not fail closed")
    report={"status":"PASS_GUARDED_CLI","single":r,"declared_bo3":m,
            "negative_ban":b,"existing_output_unchanged":True,
            "fresh_native_games":1+len(m["games"]),"adopted":0}
    with a.output.open("x") as out:
        json.dump(report,out,indent=2)
    print(report["status"],report["fresh_native_games"])

if __name__=="__main__":
    main()
