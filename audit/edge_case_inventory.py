"""P0-04 read-only triage. Passing names are leads, never interaction proof."""
import argparse, hashlib, json, re, xml.etree.ElementTree as ET
from pathlib import Path
LEDGER_SHA="3a02ed25f358642f7287b90f1fd7a17874d0d757173a51d600f4687b00a1b7ea"
XML_SHA="27a2b0fdf15dbde33b38b4a2af0438e9676101ab1e0ecd5f5d893938a3c11e53"
BARON="CardTestFixture.DISABLED_BaronNashor_AuraGivesFriendlyUnitsPlus2M"
def sha(raw):return hashlib.sha256(raw).hexdigest()
def norm(s):return re.sub(r"[^a-z0-9]","",s.lower())
def inventory(ledger,xml):
    root=ET.fromstring(xml)
    cases={}
    for t in root.iter("testcase"):
        name=t.attrib["classname"]+"."+t.attrib["name"]
        if name in cases:raise ValueError("duplicate XML test identity")
        if t.get("status")=="run" and t.get("result")=="completed" and not any(t.find(x) is not None for x in ("failure","error","skipped")):
            cases[name]="enabled_pass"
        elif t.get("status")=="notrun" and t.get("result")=="suppressed":
            cases[name]="disabled"
        else:cases[name]="not_passing"
    rows=[]
    for card in ledger["entries"]:
        for gap in card["known_gaps"]:
            historic={n for link in card["historical_test_name_links"] for n in link["enabled_test_matches"]}
            names={n for n in cases if n.startswith("Radiance") and norm(card["name"]) in norm(n.rsplit(".",1)[1])}
            mapped=set(card["scenario_test_ids"])|set(card["interaction_test_ids"])
            leads=sorted(historic|names|mapped)
            rows.append({"engine_id":card["engine_id"],"code":card["print_ids"][0],"name":card["name"],
                "question":gap,"status":"OPEN_SOURCE_REVIEW_REQUIRED",
                "leads":[{"test":n,"result":cases.get(n,"absent"),
                          "historical_link":n in historic,"name_match":n in names,"explicit_mapping":n in mapped} for n in leads],
                "behavior_verified":False,"owner_phase":2})
    return {"questions":sorted(rows,key=lambda r:r["code"]),
            "xml_counts":{s:sum(v==s for v in cases.values()) for s in ("enabled_pass","disabled","not_passing")},
            "baron":{"placeholder":BARON,"status":cases.get(BARON,"absent"),
                     "related_tests":[{"test":n,"result":v} for n,v in sorted(cases.items()) if "baronnashor" in norm(n) and n!=BARON]},
            "closed_questions":0,"all_interactions_verified":False,"fitness_evaluated":False}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for k in ("ledger","xml","output"):p.add_argument("--"+k,type=Path,required=True)
    a=p.parse_args();l=a.ledger.read_bytes();x=a.xml.read_bytes()
    if sha(l)!=LEDGER_SHA or sha(x)!=XML_SHA:raise ValueError("input evidence hash mismatch")
    report=inventory(json.loads(l),x)
    assert len(report["questions"])==37 and len({r["code"] for r in report["questions"]})==37
    assert report["xml_counts"]=={"enabled_pass":3932,"disabled":1,"not_passing":0}
    assert report["baron"]["status"]=="disabled"
    report.update({"source_ledger_sha256":LEDGER_SHA,"source_xml_sha256":XML_SHA,
                   "status":"PASS_TRIAGE_ONLY","phase":"P0-04"})
    a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2))
if __name__=="__main__":main()
