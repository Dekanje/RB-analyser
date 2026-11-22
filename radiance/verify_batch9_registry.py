#!/usr/bin/env python3
"""Batch 9 seven-new-card strict registry check: three new real engine card identities.

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
    "RAD-050/167":("Mysterious Chronomancer","unit",1029),
    "RAD-055/167":("Clanging Sentry","unit",1030),
    "RAD-093/167":("Disposal Expert","unit",1034),
    "RAD-097/167":("Siren of the Shallows","unit",1035),
}
def verify(cards):
    assert len(cards)==1031, (len(cards),"Expected 1,031 compiled engine definitions")
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
    assert len(registered)==75, (len(registered),"Expected 80 Radiance base IDs")
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
