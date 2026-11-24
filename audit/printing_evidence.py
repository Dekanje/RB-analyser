#!/usr/bin/env python3
"""Conservative printing candidate ledger; no aliases, bans or legality changed."""
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path

GALLERY_SHA="87a5a3eb9f17e2d3d4e4ce91ce12cebf379ee68b45f70321ae9e034bdcd801b4"
REGISTRY_SHA="d8102dd0930f466ce16c917035aff15eb21e347879800b08fa334b677f198b89"
PROFILE_SHA="5525a697ec86e792d86fe7f8f418d7ff7dad95b3ee5912ac5efaea344fb790b4"
FIELDS=("name","subtitle","types","supertypes","domains","stats","rules_repr_sha256")

def read_pin(path,expected):
    raw=path.read_bytes()
    if sha256(raw).hexdigest()!=expected: raise ValueError("input hash mismatch: "+str(path))
    return json.loads(raw)

def inventory(report,registry,profile):
    rows=report["printings"]; cards=registry["cards"]
    if len({r["gallery_id"] for r in rows})!=len(rows): raise ValueError("duplicate gallery ID")
    ids={c["card_id"]:c for c in cards}
    if len(ids)!=len(cards): raise ValueError("duplicate engine ID")
    exact={r["exact_engine_id"]:r for r in rows if r["exact_engine_id"] is not None}
    if len(exact)!=sum(r["exact_engine_id"] is not None for r in rows): raise ValueError("duplicate exact mapping")
    for i,r in exact.items():
        if i not in ids or ids[i]["public_code"]!=r["public_code"]: raise ValueError("exact code mismatch")
    bans={r["engine_id"] for r in profile["ban_entries"]}
    if not bans<=ids.keys(): raise ValueError("unknown banned identity")
    result=[]
    for r in rows:
        if r["identity_status"]!="candidate_only_unverified": continue
        candidates=[]
        if not r["candidate_engine_ids"] or len(set(r["candidate_engine_ids"]))!=len(r["candidate_engine_ids"]):
            raise ValueError("invalid candidate list")
        for i in r["candidate_engine_ids"]:
            c=ids[i];e=exact.get(i)
            differences=[k for k in FIELDS if r.get(k)!=e.get(k)] if e else None
            comparable=bool(e and r.get("rules_repr_sha256") and e.get("rules_repr_sha256"))
            equal=bool(comparable and not differences)
            metadata_equal=bool(e and all(r.get(k)==e.get(k) for k in FIELDS[:-1]))
            candidates.append({"engine_id":i,"engine_code":c.get("public_code"),
                 "engine_set":c["set"],"cross_set":r["set"]!=c["set"],
                 "banned_candidate":i in bans or c["banned"],
                 "exact_gallery_comparator":e["public_code"] if e else None,
                 "different_fields":differences,"raw_hash_comparable":comparable,
                 "matching_raw_hash_and_metadata":equal,"matching_metadata":metadata_equal})
        n=sum(c["matching_raw_hash_and_metadata"] for c in candidates)
        classification=("multiple_equal" if n>1 else "one_equal" if n==1 else
            "metadata_only" if any(c["matching_metadata"] for c in candidates) else "metadata_difference_or_no_comparator")
        result.append({"gallery_id":r["gallery_id"],"public_code":r["public_code"],"set":r["set"],
                       "classification":classification,"candidate_count":len(candidates),
                       "candidates":candidates,"any_banned_candidate":any(c["banned_candidate"] for c in candidates),
                       "any_cross_set":any(c["cross_set"] for c in candidates),
                       "printing_equivalence_verified":False,"approved_engine_id":None,
                       "official_legality_verified":False})
    rad=[r for r in result if r["set"]=="RAD"]
    def counts(rs):
        return {"rows":len(rs),"classification":dict(Counter(r["classification"] for r in rs)),
                "multi_candidate":sum(r["candidate_count"]>1 for r in rs),
                "any_banned_candidate":sum(r["any_banned_candidate"] for r in rs),
                "any_cross_set":sum(r["any_cross_set"] for r in rs)}
    return {"all_candidates":counts(result),"radiance":counts(rad),"rows":result,
            "printing_equivalence_verified":False,"official_legal_pool_verified":False,
            "mechanics_verified":False,"aliases_approved":0}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("gallery","registry","profile","output"): p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args()
    report=inventory(read_pin(a.gallery,GALLERY_SHA),read_pin(a.registry,REGISTRY_SHA),read_pin(a.profile,PROFILE_SHA))
    if report["all_candidates"]["rows"]!=285 or report["radiance"]["rows"]!=52:
        raise ValueError("unexpected candidate count")
    report.update({"gallery_sha256":GALLERY_SHA,"registry_sha256":REGISTRY_SHA,"profile_sha256":PROFILE_SHA})
    with a.output.open("x") as fp: json.dump(report,fp,indent=2)
    print(json.dumps({k:report[k] for k in ("all_candidates","radiance","aliases_approved")},indent=2))

if __name__=="__main__": main()
