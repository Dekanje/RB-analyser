"""Cross-check public gallery pagination against immutable prior receipt."""
import argparse,json
from pathlib import Path
from hashlib import sha256
from official_gallery_inventory import collect,gallery_record
import official_gallery_inventory as source

def compare(old, snapshots):
    baseline={r["gallery_id"]:r for r in old["printings"]}
    result=[]
    for size,rows,meta in snapshots:
        current={r["gallery_id"]:r for r in rows}
        if len(current)!=len(rows): raise ValueError("duplicate identity")
        common=baseline.keys() & current.keys()
        fields=("public_code","set","name","subtitle","types","supertypes","domains","stats","rules_repr_sha256")
        result.append({"page_size":size,"acquisition":meta,
          "added":sorted(current.keys()-baseline.keys()),"missing":sorted(baseline.keys()-current.keys()),
          "changed":[k for k in sorted(common) if any(current[k].get(f)!=baseline[k].get(f) for f in fields)],
          "unmatched_controls":[r for r in rows if r["public_code"] in ("UNL-T04","UNL-T08")]})
    return {"comparisons":result,"official_pool_verified":False,"printing_equivalence_verified":False}

def main():
    p=argparse.ArgumentParser();p.add_argument("--prior",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    raw=a.prior.read_bytes()
    if sha256(raw).hexdigest()!="87a5a3eb9f17e2d3d4e4ce91ce12cebf379ee68b45f70321ae9e034bdcd801b4": raise ValueError("wrong prior receipt")
    snapshots=[]
    for size in (100,150):
        source.PAGE=size
        rows,meta=collect("riftbound_gallery_cards")
        snapshots.append((size,[gallery_record(r) for r in rows],meta))
    report=compare(json.loads(raw),snapshots)
    with a.output.open("x") as f: json.dump(report,f,indent=2)
if __name__=="__main__": main()
