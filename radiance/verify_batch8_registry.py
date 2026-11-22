#!/usr/bin/env python3
"""Strict Batch 8 15-card registry check; not a claim of full-set mechanics."""
import argparse,json
from pathlib import Path
from verify_batch7_registry import BATCH7

NEW={
"RAD-002/167":("Banner of Conquest","gear",1010),
"RAD-025/167":("Consult the Heavens","spell",1011),
"RAD-026/167":("Entrenched Boar","unit",1012),
"RAD-034/167":("Hunker Down","spell",1013),
"RAD-118/167":("Herald of the Emperor","unit",1014),
"RAD-095/167":("Momentary Companion","unit",1015),
"RAD-007/167":("Rally for War","spell",1016),
"RAD-024/167":("Blossoming Dreamroot","gear",1017),
"RAD-027/167":("Iridescent Avian","unit",1018),
"RAD-030/167":("Sanctum Conservator","unit",1019),
"RAD-036/167":("Storm Raptor","unit",1020),
"RAD-039/167":("Ephemeral Ward","gear",1021),
"RAD-052/167":("Resource Extractor","gear",1022),
"RAD-056/167":("Improvised Projectile","spell",1023),
"RAD-100/167":("The Waters' Wage","spell",1024),
}
def check(cards):
    assert len(cards)==1024,(len(cards),"Expected 1024 compiled definitions")
    by={}
    for c in cards:
        if c.get("public_code"):by.setdefault(c["public_code"],[]).append(c)
    for code,(name,typ,id_) in NEW.items():
        rows=by.get(code,[])
        assert len(rows)==1,(code,rows)
        row=rows[0]
        assert (row.get("name"),row.get("card_type"),row.get("card_id"))==(name,typ,id_),row
    for code,(name,typ) in BATCH7.items():
        rows=by.get(code,[])
        assert len(rows)==1,(code,rows)
        assert rows[0].get("name")==name and rows[0].get("card_type")==typ,rows[0]
    base={f"RAD-{n:03d}/167" for n in range(1,168)}
    registered=base&by.keys()
    assert len(registered)==68,(len(registered),"Expected 68 base Radiance cards")
    report={"compiled_registry_size":len(cards),"radiance_base_registered":len(registered),
    "radiance_base_missing":len(base-registered),
    "new_batch8_codes":sorted(NEW),"new_batch8_count":len(NEW),
    "all_radiance_mechanics_certified":False}
    return report
if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("registry",type=Path)
    p.add_argument("--output",type=Path,default=Path("results/radiance_batch8_coverage.json"))
    a=p.parse_args()
    d=json.loads(a.registry.read_text())
    result=check(d["cards"])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2))
    print("BATCH8_STRICT_REGISTRY_PASS",json.dumps(result))
