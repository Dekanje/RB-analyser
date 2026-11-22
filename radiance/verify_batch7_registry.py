#!/usr/bin/env python3
"""Reconcile the compiled playable registry against all 167 base Radiance IDs.

A compiled printing is NOT equivalent to a verified gameplay mechanic.
Use a separate explicit list of cards covered by scenario tests; do not infer
mechanics from the existence of CardDef or a successful game.
"""
import argparse
import json
import pathlib

BATCH7 = {
    "RAD-077/167": ("Wrath of the Freljord","unit"),
    "RAD-088/167": ("Staunch Survivor","unit"),
    "RAD-059/167": ("Supernova","spell"),
    "RAD-079/167": ("Avalanche","spell"),
    "RAD-099/167": ("Suave Negotiator","unit"),
    "RAD-004/167": ("Brawl","spell"),
    "RAD-008/167": ("War Scout","unit"),
    "RAD-049/167": ("Industrious Mechsmith","unit"),
    "RAD-003/167": ("Bilgewater Tracker","unit"),
    "RAD-009/167": ("Antagonistic Apparatus","unit"),
    "RAD-119/167": ("Hunting Dog","unit"),
    "RAD-083/167": ("Stalwart Goatherd","unit"),
    "RAD-058/167": ("Riptide Mage","unit"),
    "RAD-048/167": ("High Note","spell"),
    "RAD-071/167": ("Nazuman Ntofo","gear"),
    "RAD-072/167": ("Overloaded Traveler","unit"),
    "RAD-122/167": ("Party Crasher","unit"),
    "RAD-128/167": ("Steadfast Outrider","unit"),
    "RAD-037/167": ("Watchful Curator","unit"),
    "RAD-076/167": ("Sneaky Zeebles","unit"),
    "RAD-117/167": ("For Demacia!","spell"),
    "RAD-101/167": ("An Offer You Can't Refuse","spell"),
}

def reconcile(cards):
    if len(cards) != 1010:
        raise ValueError(f"Expected 1010 compiled definitions after Batch 7, found {len(cards)}")
    by_code = {}
    for row in cards:
        code = row.get("public_code")
        if not isinstance(code, str) or not code: continue
        by_code.setdefault(code, []).append(row)
    for code,(name,typ) in BATCH7.items():
        matches=by_code.get(code,[])
        if len(matches)!=1:
            raise ValueError(f"Expected exactly one compiled {code}; got {len(matches)}")
        if matches[0].get("name")!=name or matches[0].get("card_type")!=typ:
            raise ValueError(f"Wrong compiled card metadata for {code}: {matches[0]}")
    base_codes=[f"RAD-{num:03d}/167" for num in range(1,168)]
    registered=[code for code in base_codes if code in by_code]
    missing=[code for code in base_codes if code not in by_code]
    return {
        "engine_definitions":len(cards),"base_set_card_count":167,
        "registered_base_radiance_cards":len(registered),
        "missing_base_radiance_card_codes":missing,
        "newly_authored_cplusplus_cards":sorted(BATCH7),
        "newly_authored_cplusplus_count":len(BATCH7),
        "all_radiance_supported":len(missing)==0,
        "mechanics_certified_for_entire_set":False,
        "note":"Registered cards may still have untested/incorrect mechanics; this check only guarantees twenty-two identities and a complete inventory of missing card codes."
    }

def main():
    p=argparse.ArgumentParser()
    p.add_argument("registry",type=pathlib.Path)
    p.add_argument("--output",type=pathlib.Path,default=pathlib.Path("results/radiance_batch7_coverage.json"))
    a=p.parse_args()
    data=json.loads(a.registry.read_text())
    report=reconcile(data["cards"])
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("RADIANCE_BATCH7_REGISTRY_PASS",
          json.dumps({k:v for k,v in report.items() if k!="missing_base_radiance_card_codes"}),flush=True)
    print("MISSING_RADIANCE_CODES",len(report["missing_base_radiance_card_codes"]),flush=True)

if __name__=="__main__":main()
