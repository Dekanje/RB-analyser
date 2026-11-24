#!/usr/bin/env python3
"""Native positive controls plus negative preflight for every dated ban."""
import argparse
import json
from pathlib import Path
from format_gateway import NativeGateway, FormatRejected

def main():
    p=argparse.ArgumentParser()
    for n in ("engine","registry","profile","selected","output"):
        p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args()
    g=NativeGateway(a.engine,a.registry,a.profile,("OGN","OGS","SFD","UNL","VEN","RAD"))
    valid=[]
    rejected=[]
    for path in sorted(a.selected.glob("*.txt")):
        try:
            g.gate.validate(path.read_bytes())
        except FormatRejected as exc:
            rejected.append({"file":path.name,"reason":str(exc)})
        else:
            valid.append(path)
    if len(valid)+len(rejected)!=58 or len(valid)<2:
        raise RuntimeError("unexpected roster or insufficient positive controls")
    # Bans are checked before type and construction checks. Inject exactly one
    # banned row into its corresponding section; rejection must name the ban.
    base=valid[0].read_text()
    negative=[]
    for row in g.profile["ban_entries"]:
        section="Battlefields" if row["type"]=="battlefield" else "MainDeck"
        modified=base.replace(section+":\n",section+":\n1 "+row["name"]+"\n",1)
        try:
            g.gate.validate(modified.encode())
        except FormatRejected as exc:
            if "banned" not in str(exc):
                raise
            negative.append({"code":row["code"],"section":section,"reason":str(exc)})
        else:
            raise RuntimeError("ban escaped: "+row["code"])
    positive=[]
    for seat in (0,1):
        one,two=valid[:2] if seat==0 else valid[:2][::-1]
        result=g.game(one,two,2026112403+seat)
        if result["status"]!="complete":
            raise RuntimeError("native positive control failed: "+str(result))
        positive.append(result)
    series=g.fixed_bo3(valid[0],valid[1],2026112405)
    if series["status"]!="complete_fixed_bo3":
        raise RuntimeError("native fixed BO3 failed")
    report={"status":"PASS_SCOPED_FORMAT_GATEWAY",**g.provenance(),
            "roster_accepted":len(valid),"roster_rejected":rejected,
            "ban_negative_controls":negative,"single_games":positive,"fixed_bo3":series,
            "native_games":len(positive)+len(series["games"]),"adopted":0}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as out:
        json.dump(report,out,indent=2)
    print("FORMAT_GATEWAY",len(valid),len(rejected),len(negative),report["native_games"])

if __name__=="__main__":
    main()
