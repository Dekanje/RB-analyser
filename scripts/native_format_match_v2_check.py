#!/usr/bin/env python3
"""Scoped native evidence for ambiguous source identities and declared BO3."""
import argparse
import json
from pathlib import Path
from format_match_v2 import VerifiedGateway, digest, FormatRejected

def main():
    p=argparse.ArgumentParser()
    for n in ("engine","registry","profile","selected","output"):
        p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args()
    g=VerifiedGateway(a.engine,a.registry,a.profile,("OGN","OGS","SFD","UNL","VEN","RAD"))
    files=sorted(a.selected.glob("*.txt"))
    if len(files)!=58:
        raise FormatRejected("roster incomplete")
    replacements={"ahri_nine_tailed_fox.txt":("Ahri, Inquisitive",119),
                  "yasuo_unforgiven.txt":("Yasuo, Windrider",205)}
    out=a.output.parent/"explicit_roster_v2"
    out.mkdir(parents=True,exist_ok=False)
    raws={};manifest=[]
    for path in files:
        raw=path.read_bytes();new=raw
        if path.name in replacements:
            name,i=replacements[path.name]
            old=("1 "+name+"\n").encode()
            if raw.count(old)!=1:
                raise FormatRejected("unexpected ambiguous source layout")
            new=raw.replace(old,("1 "+name+" #"+str(i)+"\n").encode(),1)
        g.gate.validate(new)
        raws[path.name]=new
        (out/path.name).write_bytes(new)
        manifest.append({"file":path.name,"source_sha256":digest(raw),"explicit_sha256":digest(new)})
    opponent=next(n for n in raws if n not in replacements)
    diagnostics=[]
    for j,name in enumerate(replacements):
        raw=(a.selected/name).read_bytes()
        expected=[g.gate.validate(raws[name]),g.gate.validate(raws[opponent])]
        # Historical parser diagnostic only: compare the raw ambiguous historical
        # registration to explicit expected vectors, no accepted fitness result.
        old=g._native((raw,raws[opponent]),expected,2026112410+j,"ismcts:sims=24",180)
        fixed=g.game(raws[name],raws[opponent],2026112410+j)
        if old["native_vectors_sha256"]!=fixed["native_vectors_sha256"]:
            raise FormatRejected("historical identity not preserved")
        diagnostics.append({"file":name,"explicit_id":replacements[name][1],
                            "historical_diagnostic":old,"explicit_control":fixed})
    # Use a legal same-pool declared substitution from the first roster member:
    # any legal active registration is additionally native-validated when played.
    name=next(iter(replacements))
    v=g.gate.validate(raws[name])
    # Select same-domain valid main/side candidates by using an actual known
    # registered non-champion spell/unit swap; native construction checks remain.
    main_id=next(i for i in v["MainDeck"] if g.gate.ids[i]["name"]=="Affectionate Poro")
    side_id=next(i for i in v["Sideboard"] if g.gate.ids[i]["name"]=="Adaptatron")
    plan={"p1":{"swaps":[{"main_out":main_id,"side_in":side_id,"copies":1}]},"loser_chooses_start":"self"}
    policy={"game2":plan,"game3":plan}
    series=g.declared_bo3(out/name,out/opponent,policy,2026112412)
    if not series["sideboarding_applied"] or any(not x["native_ids_verified"] for x in series["games"]):
        raise FormatRejected("missing native sideboard evidence")
    report={**g.provenance(),"status":"PASS_SCOPED_NATIVE_RECEIPTS",
            "roster_preflight":len(raws),"manifest":manifest,"diagnostics":diagnostics,
            "declared_bo3":series,"native_games":4+len(series["games"]),"adopted":0}
    with a.output.open("x") as fp:
        json.dump(report,fp,indent=2)
    print("FORMAT_NATIVE_RECEIPTS",len(raws),report["native_games"])

if __name__=="__main__":
    main()
