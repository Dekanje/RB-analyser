#!/usr/bin/env python3
"""Batch 9 tranche-1 strict registry check: three new real engine card identities.

Registration and focused tests are NOT complete-set Radiance certification.
"""
import argparse
import json
from pathlib import Path
from verify_batch7_registry import BATCH7
from verify_batch8_registry import NEW as BATCH8

NEW={
    "RAD-057/167":("Piltovan Guidebot","unit",1025),
    "RAD-126/167":("Mournful Spirit","unit",1026),
    "RAD-073/167":("Pillaged Armory","gear",1027),
}
def verify(cards):
    assert len(cards)==1027, (len(cards),"Expected 1,027 compiled engine definitions")
    codes={}
    ids=set()
    for card in cards:
        cid=card["card_id"]
        assert cid not in ids, ("Duplicate engine ID",cid)
        ids.add(cid)
        code=card.get("public_code")
        if code:
            assert code not in codes, ("Duplicate public code",code)
            codes[code]=card
    for code,(name,kind,id_) in {**BATCH8,**NEW}.items():
        c=codes.get(code)
        assert c is not None and (c["name"],c["card_type"],c["card_id"])==(
            name,kind,id_), (code,c)
    for code,(name,kind) in BATCH7.items():
        c=codes.get(code)
        assert c and c["name"]==name and c["card_type"]==kind,(code,c)
    base={f"RAD-{n:03d}/167" for n in range(1,168)}
    registered=base&set(codes)
    assert len(registered)==71, (len(registered),"Expected 71 Radiance base IDs")
    return {"compiled_registry_size":len(cards),"radiance_base_registered":len(registered),
            "radiance_base_missing":len(base-registered),"batch9_tranche1_count":len(NEW),
            "batch9_new_codes":sorted(NEW),"full_set_verified":False}
if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("registry",type=Path)
    parser.add_argument("--output",type=Path,default=Path("results/radiance_batch9_coverage.json"))
    args=parser.parse_args()
    report=verify(json.loads(args.registry.read_text())["cards"])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2))
    print("BATCH9_TRANCHE1_STRICT_REGISTRY_PASS",json.dumps(report))
