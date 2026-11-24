#!/usr/bin/env python3
"""Read-only Riot public-gallery acquisition and identity reconciliation.

No raw card text, art URLs or raw CMS payloads are published by this tool.
Code/name/hash similarities are evidence leads, never equivalence or legality.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata
from urllib.request import Request, urlopen
from urllib.parse import urlencode

SOURCE = "https://content.publishing.riotgames.com/publishing-content/v2.0/public/channel/riftbound_website/list/"
REGISTRY_SHA = "d8102dd0930f466ce16c917035aff15eb21e347879800b08fa334b677f198b89"
PAGE = 200
EXPECTED_SETS = {"OGN","OGS","SFD","UNL","VEN","RAD"}


def digest(raw):
    return sha256(raw).hexdigest()


def stable_hash(value):
    return digest(json.dumps(value,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode())


def fetch(url):
    request = Request(url, headers={"Accept":"application/json","User-Agent":"RB-Analyser catalog audit/1.0"})
    with urlopen(request, timeout=30) as response:
        if not response.geturl().startswith(SOURCE):
            raise ValueError("unexpected gallery redirect")
        data = response.read(16*1024*1024+1)
        if len(data)>16*1024*1024:
            raise ValueError("gallery page exceeded size bound")
        return data


def collect(kind, get=fetch):
    if kind not in {"riftbound_gallery_cards","riftbound_gallery_sets"}:
        raise ValueError("unsupported gallery resource")
    rows={};pages=[];total=None
    for offset in range(0,20000,PAGE):
        url=SOURCE+kind+"?"+urlencode({"locale":"en_US","from":offset,"limit":PAGE})
        raw=get(url);data=json.loads(raw)
        reported=data.get("metadata",{}).get("totalItems")
        if type(reported) is not int or not 0<reported<=20000:
            raise ValueError("invalid or absent totalItems")
        if total is None: total=reported
        if reported!=total:
            raise ValueError("gallery changed during acquisition")
        items=data.get("data")
        if not isinstance(items,list):
            raise ValueError("invalid gallery page")
        pages.append({"url":url,"sha256":digest(raw),"rows":len(items),"offset":offset})
        for row in items:
            key=row.get("id")
            if not isinstance(key,str) or not key or key in rows:
                raise ValueError("missing or repeated gallery identity")
            rows[key]=row
        if offset+PAGE>=total:
            # The CMS can expose fewer visible rows than advertised; never
            # represent such a result as a complete official inventory.
            return list(rows.values()),{"advertised_total":total,"observed_total":len(rows),
                    "advertised_count_matched":len(rows)==total,"pages":pages}
    raise ValueError("pagination safety bound reached")


def norm(value):
    return unicodedata.normalize("NFKC",value or "").replace("’","'").strip().casefold()


def label(obj):
    return obj.get("label") if isinstance(obj,dict) else None


def stat(raw,k):
    value=(raw.get(k) or {}).get("value") or {}
    v=value.get("id")
    if v is None or v=="": return None
    try: return int(v)
    except (TypeError,ValueError): return None


def gallery_record(raw):
    name=raw.get("name");setv=(raw.get("set") or {}).get("value") or {}
    if not isinstance(name,str) or not name or not setv.get("id"):
        raise ValueError("gallery identity lacks name or set")
    subtitle=raw.get("subtitle")
    if isinstance(subtitle,dict):
        subtitle=label(subtitle.get("value")) or label(subtitle)
    if subtitle is not None and not isinstance(subtitle,str):
        raise ValueError("unrecognized subtitle")
    types=raw.get("cardType") or {}
    type_labels=[label(x) for x in types.get("type",[])]
    super_labels=[label(x) for x in types.get("superType",[])]
    rich=((raw.get("text") or {}).get("richText") or {}).get("body")
    if rich is None:
        rich=((raw.get("effect") or {}).get("richText") or {}).get("body")
    # Keep raw rules representation fingerprint, not the underlying text.
    return {"gallery_id":raw["id"],"public_code":raw.get("publicCode") or None,
            "set":setv["id"].upper(),"name":name,"subtitle":subtitle,
            "types":type_labels,"supertypes":super_labels,
            "domains":sorted(label(x) or "" for x in (raw.get("domain") or {}).get("values",[])),
            "stats":{k:stat(raw,k) for k in ("energy","power","might")},
            "collector_number":raw.get("collectorNumber"),
            "flags":[x.get("id") for x in raw.get("flags",[])],
            "rules_repr_sha256":stable_hash(rich) if rich is not None else None}


def reconcile(gallery,registry):
    cards=registry["cards"]
    if len(cards)!=1123 or len({c["card_id"] for c in cards})!=len(cards):
        raise ValueError("unexpected registry identities")
    bycode={c["public_code"]:c for c in cards if c.get("public_code")}
    if len(bycode)!=sum(bool(c.get("public_code")) for c in cards):
        raise ValueError("duplicate engine public code")
    byname=defaultdict(list)
    for c in cards: byname[norm(c["name"])].append(c)
    rows=[];seen=set();code_counts=Counter()
    for raw in gallery:
        r=gallery_record(raw)
        if r["gallery_id"] in seen: raise ValueError("duplicate gallery ID")
        seen.add(r["gallery_id"])
        code=r["public_code"]
        if code: code_counts[code]+=1
        exact=bycode.get(code)
        title=r["name"];subtitle=r["subtitle"]
        keys={norm(title)}
        if subtitle: keys.add(norm(title+", "+subtitle))
        candidates={c["card_id"] for k in keys for c in byname.get(k,[])}
        if exact:
            candidates.add(exact["card_id"])
        r.update({"exact_engine_id":exact["card_id"] if exact else None,
                  "candidate_engine_ids":sorted(candidates),
                  "identity_status":"exact_code_unverified" if exact else
                   "candidate_only_unverified" if candidates else "unmatched",
                  "official_legality_verified":False,"mechanics_verified":False,
                  "printing_equivalence_verified":False})
        rows.append(r)
    matched={r["exact_engine_id"] for r in rows if r["exact_engine_id"] is not None}
    groups=[]
    fields=("card_type","super_type","domains","tags","energy_cost","power_cost","might","features","might_bonus","ability_text","effect_text")
    for name,group in sorted(byname.items()):
        if len(group)<2: continue
        hashes={k:[stable_hash(c.get(k)) for c in group] for k in fields}
        groups.append({"name":group[0]["name"],"engine_ids":[c["card_id"] for c in group],
                       "codes":[c.get("public_code") for c in group],
                       "different_fields":[k for k,vs in hashes.items() if len(set(vs))>1],
                       "equivalence_verified":False})
    absent=[{"engine_id":c["card_id"],"code":c.get("public_code"),"set":c["set"],
             "token":c.get("super_type")=="token"} for c in cards if c["card_id"] not in matched]
    rad_bases={f"RAD-{i:03d}/167" for i in range(1,168)}
    return {"summary":{"gallery_rows":len(rows),"gallery_sets":dict(Counter(r["set"] for r in rows)),
            "missing_expected_gallery_sets":sorted(EXPECTED_SETS-{r["set"] for r in rows}),
            "missing_numbered_radiance":sorted(rad_bases-code_counts.keys()),
            "exact_code_engine_ids":len(matched),"engine_without_exact_gallery_code":len(absent),
            "gallery_identity_status":dict(Counter(r["identity_status"] for r in rows)),
            "missing_gallery_public_code":sum(not r["public_code"] for r in rows),
            "duplicate_gallery_public_codes":sorted(k for k,v in code_counts.items() if v>1),
            "engine_duplicate_name_groups":len(groups)},
            "printings":rows,"unmatched_engine_identities":absent,"duplicate_engine_name_groups":groups}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registry",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    raw=a.registry.read_bytes()
    if digest(raw)!=REGISTRY_SHA: raise ValueError("wrong pinned registry")
    start=datetime.now(timezone.utc).isoformat()
    cards,card_provenance=collect("riftbound_gallery_cards")
    sets,set_provenance=collect("riftbound_gallery_sets")
    result=reconcile(cards,json.loads(raw))
    result.update({"schema_version":1,"source":"Riot public English gallery CMS",
                   "official_gallery_page":"https://playriftbound.com/en-us/card-gallery/",
                   "started_at":start,"finished_at":datetime.now(timezone.utc).isoformat(),
                   "registry_sha256":REGISTRY_SHA,"cards_acquisition":card_provenance,
                   "sets_acquisition":set_provenance,
                   "sets":[{"id":x["id"],"name":x.get("name"),"collector_number_max":x.get("collectorNumberMax")} for x in sets],
                   "official_legal_pool_verified":False,"printing_equivalence_verified":False,
                   "mechanics_verified":False})
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x",encoding="utf-8") as out:
        json.dump(result,out,indent=2,ensure_ascii=False,sort_keys=True)
        out.write("\n")
    print(json.dumps(result["summary"],indent=2))
    print("GALLERY_INVENTORY_CAPTURED_NOT_LEGALITY_CERTIFIED")


if __name__=="__main__":
    main()
