"""Map dated official errata headings to compiled identities and test leads.

No automatic mechanical equivalence, changes to cards, or correctness claims.
"""
import argparse,json,re,unicodedata
from collections import Counter,defaultdict
from hashlib import sha256
from pathlib import Path
from xml.etree import ElementTree as ET

REGISTRY_SHA="d8102dd0930f466ce16c917035aff15eb21e347879800b08fa334b677f198b89"
XML_SHA="a063b69b50f06a0730bf67c64ac939100b4e1912100d414ed6e0a57c105b9d5c"
EXPECTED=(31,16,8,8,4)
def digest(raw):return sha256(raw).hexdigest()
def norm(s):return unicodedata.normalize("NFKC",s).replace("’","'").casefold().strip()
def compact(s):return re.sub(r"[^a-z0-9]","",norm(s))
def pinned(path,expected):
    raw=path.read_bytes()
    if digest(raw)!=expected: raise ValueError("unapproved input: "+str(path))
    return raw
def inventory(index,registry,xml):
    articles=index["articles"]
    if tuple(len(x["names"]) for x in articles)!=EXPECTED:raise ValueError("errata heading count changed")
    byname=defaultdict(list)
    for c in registry["cards"]:byname[norm(c["name"])].append(c)
    cases=[]
    for case in xml.iter("testcase"):
        name=case.get("name","")
        cases.append({"name":case.get("classname","")+"."+name,"key":compact(name),
                      "enabled_pass":case.get("status")=="run" and case.get("result")=="completed" and case.find("failure") is None and case.find("skipped") is None})
    rows=[]
    for article in articles:
        for name in article["names"]:
            alias=index["explicit_title_aliases"].get(name,name)
            matches=byname[norm(alias)]
            leads=[c["name"] for c in cases if c["enabled_pass"] and any(compact(n) in c["key"] for n in (name,alias) if len(compact(n))>=5)]
            rows.append({"date":article["date"],"source":article["url"],"official_title":name,
                         "lookup_title":alias,"compiled":[{"id":c["card_id"],"code":c.get("public_code"),
                         "ability_text_sha256":digest(c["ability_text"].encode()),
                         "effect_text_sha256":digest(c["effect_text"].encode())} for c in matches],
                         "test_name_leads":sorted(set(leads)),
                         "status":"unresolved_identity" if not matches else "identity_candidates_only",
                         "behavior_verified":False})
    if len({(r["date"],r["official_title"]) for r in rows})!=len(rows):raise ValueError("duplicate errata heading")
    return {"rows":rows,"summary":{"entries":len(rows),"matched":sum(bool(r["compiled"]) for r in rows),
             "multiple_compiled_ids":sum(len(r["compiled"])>1 for r in rows),
             "unmatched":[r["official_title"] for r in rows if not r["compiled"]],
             "with_test_name_leads":sum(bool(r["test_name_leads"]) for r in rows)},
             "all_errata_behavior_verified":False}

def focused_controls(registry,root):
    byid={c["card_id"]:c for c in registry["cards"]}
    overlay=root/"radiance/engine_overlay"
    apply=(overlay/"apply_final64.py").read_text()
    neeko=(overlay/"source/cards/units/1116_radiance_final64_d.cpp").read_text()
    findings=[
        {"id":1131,"code":byid[1131]["public_code"],"official_requirement":"zero through three distinct additional legends",
         "stored_text_exact_three":"choose 3 different legends" in byid[1131]["ability_text"],
         "validator_exact_three":"deck.neeko_legends.size()!=3" in apply,
         "trigger_exact_three":"selected.size()!=3" in neeko,
         "classification":"confirmed_source_discrepancy_needs_native_regression"},
        {"id":986,"code":byid[986]["public_code"],"official_requirement":"self is eligible for friendly-unit bonus",
         "stored_text_excludes_self":"another friendly unit" in byid[986]["ability_text"],
         "classification":"compiled_text_discrepancy_behavior_unverified"},
        {"id":1069,"code":byid[1069]["public_code"],"classification":"compiled_wording_review_behavior_unverified"},
        {"id":962,"code":byid[962]["public_code"],"classification":"compiled_wording_review_behavior_unverified"}]
    # Confirm exact baseline observations; a changed baseline requires a new review.
    if not all(findings[0][k] for k in ("stored_text_exact_three","validator_exact_three","trigger_exact_three")) or not findings[1]["stored_text_excludes_self"]:
        raise ValueError("focused findings changed; review new source")
    return findings

def main():
    p=argparse.ArgumentParser()
    for n in ("registry","xml","index","output"):p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args()
    registry=json.loads(pinned(a.registry,REGISTRY_SHA))
    report=inventory(json.loads(a.index.read_bytes()),registry,ET.fromstring(pinned(a.xml,XML_SHA)))
    report["focused_findings"]=focused_controls(registry,Path(__file__).resolve().parents[1])
    report.update(registry_sha256=REGISTRY_SHA,xml_sha256=XML_SHA,index_sha256=digest(a.index.read_bytes()))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as f:json.dump(report,f,indent=2)
    print(json.dumps(report["summary"]))
if __name__=="__main__":main()
