#!/usr/bin/env python3
"""Final-64 identity audit and deliberately separate per-card mechanics gate."""
import argparse
import json
from collections import Counter
from pathlib import Path
import xml.etree.ElementTree as ET

BASE=Path(__file__).resolve().parent
MANIFEST=json.loads((BASE/"final64/manifest.json").read_text())
EXPECTED=MANIFEST["cards"]
assert len(EXPECTED)==64
assert {x["engine_id"] for x in EXPECTED}==set(range(1068,1132))
assert len({x["public_code"] for x in EXPECTED})==64

def registry_check(registry):
    cards=json.loads(Path(registry).read_text())["cards"]
    assert len(cards)==1123,("Expected 1,123 compiled engine cards",len(cards))
    counts=Counter(c.get("public_code") for c in cards if c.get("public_code"))
    dup={k:v for k,v in counts.items() if v!=1}
    assert not dup,("duplicate public codes",dup)
    ids=Counter(c["card_id"] for c in cards)
    assert len(ids)==1123 and all(n==1 for n in ids.values()),"Duplicate engine IDs"
    by_code={c["public_code"]:c for c in cards if c.get("public_code")}
    for x in EXPECTED:
        code=x["public_code"]
        card=by_code.get(code)
        assert card is not None,(code,"missing")
        assert (card["card_id"],card["name"],card["card_type"])==(
            x["engine_id"],x["name"],x["card_type"]),(code,card)
        assert card.get("energy_cost")==x["energy"],(code,"energy_cost")
        assert card.get("power_cost")==x["power"],(code,"power_cost")
        assert card.get("might")==x["might"],(code,"might")
    required={f"RAD-{i:03d}/167" for i in range(1,168)}
    present=required & by_code.keys()
    assert present==required,("Missing base Radiance cards",sorted(required-present))
    result={"compiled_registry_size":len(cards),"radiance_registered_base":len(present),
            "radiance_missing_base":len(required-present),"final64_unique_count":len(EXPECTED),
            "duplicate_public_codes":0,"identity_gate":"PASS",
            "all_mechanics_verified":False}
    print("RADIANCE_FINAL64_REGISTRY_PASS",json.dumps(result,sort_keys=True))
    return result

def mechanics_check(xml_path):
    """Fail closed until 64 distinct, meaningful scenario suites are marked accepted."""
    status=json.loads((BASE/"final64/mechanics_acceptance.json").read_text())
    entries=status["cards"]
    assert len(entries)==64
    codes={c["public_code"] for c in EXPECTED}
    assert set(entries)==codes,("Incomplete coverage tracker",sorted(codes-set(entries)))
    root=ET.parse(xml_path).getroot()
    passed=set()
    for test in root.iter("testcase"):
        name=test.get("classname","")+"."+test.get("name","")
        if test.find("failure") is None and test.find("skipped") is None:
            passed.add(name)
    errors={}
    for code,rec in entries.items():
        tests=rec.get("engine_scenarios",[])
        if rec.get("status")!="accepted" or len(tests)<1:
            errors[code]="Not mechanics-accepted"
        elif any(t not in passed for t in tests):
            errors[code]="Declared scenario absent or failing: "+repr([t for t in tests if t not in passed])
    assert not errors,("Mechanics acceptance incomplete",errors)
    print("RADIANCE_FINAL64_MECHANICS_ACCEPTANCE_PASS: 64 unique cards with passing scenarios")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("registry",type=Path)
    p.add_argument("--output",type=Path,default=Path("results/radiance_final64_registry_audit.json"))
    p.add_argument("--mechanics-xml",type=Path)
    a=p.parse_args()
    result=registry_check(a.registry)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+"\n")
    if a.mechanics_xml is not None:mechanics_check(a.mechanics_xml)
