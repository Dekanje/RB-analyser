#!/usr/bin/env python3
"""Batch 10 identity-only fail-closed audit. Full gameplay certification is separate."""
import argparse,json
from pathlib import Path
from verify_batch7_registry import BATCH7
from verify_batch8_registry import NEW as BATCH8
from verify_batch9_registry import NEW as BATCH9

NEW={
    "RAD-013/167": ("Lost to the Sands", "spell", 1048),
    "RAD-035/167": ("Invigorating Bloom", "gear", 1049),
    "RAD-038/167": ("Ahri, Confident", "unit", 1050),
    "RAD-051/167": ("Parallel Convergence", "spell", 1051),
    "RAD-070/167": ("Hold 'Em", "spell", 1052),
    "RAD-087/167": ("Portable Portal", "gear", 1053),
    "RAD-089/167": ("Titanic Shrine", "gear", 1054),
    "RAD-096/167": ("Satchel Charge", "spell", 1055),
    "RAD-106/167": ("The Good Stuff", "gear", 1056),
    "RAD-107/167": ("Bedeviling Stranger", "unit", 1057),
    "RAD-005/167": ("Lingering Animus", "unit", 1058),
    "RAD-021/167": ("Ekko, Revolutionary", "unit", 1059),
    "RAD-028/167": ("Ki Burst", "spell", 1060),
    "RAD-029/167": ("Life from Stone", "spell", 1061),
    "RAD-040/167": ("Heartening Soul", "unit", 1062),
    "RAD-047/167": ("Fanfare", "spell", 1063),
    "RAD-061/167": ("Ekko, Ingenious", "unit", 1064),
    "RAD-075/167": ("Skystrike Squadron", "unit", 1065),
    "RAD-116/167": ("Concert Poster", "gear", 1066),
    "RAD-121/167": ("One-Two Punch", "spell", 1067),
}
assert len(NEW)==20
assert not (set(NEW)&set(BATCH9)), "Batch 10 duplicates Batch 9"

def verify(rows):
    assert len(rows)==1059,(len(rows),"Expected exactly 1,059 compiled cards")
    from collections import Counter
    collisions={code:n for code,n in Counter(
        x.get("public_code") for x in rows if x.get("public_code")
    ).items() if n>1}
    print("BATCH10_DUPLICATE_DIAGNOSTIC",json.dumps(collisions,sort_keys=True),flush=True)
    observed={x.get("public_code") for x in rows if x.get("public_code")}
    print("BATCH10_PRESENT_BASE_CODES",json.dumps(sorted(observed & {f"RAD-{i:03d}/167" for i in range(1,168)})),flush=True)
    codes={};ids=set()
    for row in rows:
        cid=row["card_id"]
        assert cid not in ids,("Duplicate engine id",cid)
        ids.add(cid)
        code=row.get("public_code")
        if code:
            assert code not in codes,("Duplicate public card code",code)
            codes[code]=row
    for code,(name,kind,id_) in {**BATCH8,**BATCH9,**NEW}.items():
        card=codes.get(code)
        assert card is not None,(code,"Missing")
        assert (card["name"],card["card_type"],card["card_id"])==(name,kind,id_),(code,card)
    for code,(name,kind) in BATCH7.items():
        card=codes.get(code)
        assert card and card["name"]==name and card["card_type"]==kind,(code,card)
    base={f"RAD-{n:03d}/167" for n in range(1,168)}
    present=base&set(codes)
    assert len(present)==103,(len(present),"Expected 103 unique Radiance base cards")
    assert len(base-present)==64
    return {"compiled_registry_size":len(rows),"radiance_base_registered":len(present),
            "radiance_base_missing":len(base-present),"batch10_new_unique_count":len(NEW),
            "batch10_new_codes":sorted(NEW),"full_set_verified":False,
            "all_mechanics_verified":False,
            "note":"This is identity coverage only. Full card mechanics are not certified."}

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("registry",type=Path)
    p.add_argument("--output",type=Path,default=Path("results/radiance_batch10_coverage.json"))
    a=p.parse_args()
    x=verify(json.loads(a.registry.read_text())["cards"])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(x,indent=2))
    print("BATCH10_STRICT_REGISTRY_PASS",json.dumps(x))
