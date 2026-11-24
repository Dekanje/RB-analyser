"""Read-only branch ancestry and workflow dependency inventory for frozen tips."""
import argparse,collections,hashlib,json,re,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
INTEGRATION="research/competitive-agent-benchmark-v1-2026-11-23"
def require(ok,msg):
    if not ok:raise ValueError(msg)
def git(*args,root=ROOT):
    return subprocess.check_output(["git","-C",str(root),*args])
def sha(b):return hashlib.sha256(b).hexdigest()
def parse_tree(raw):
    out={}
    for row in raw.split(b"\0"):
        if not row:continue
        header,path=row.split(b"\t",1)
        mode,kind,oid=header.decode().split()
        path=path.decode()
        require(path not in out and kind in ("blob","commit"),"unexpected tree member")
        out[path]=(mode,kind,oid)
    return out
def tree(ref,root=ROOT):return parse_tree(git("ls-tree","-r","-z",ref,root=root))
def changes(a,b):
    return {"only_branch":sorted(set(b)-set(a)),"only_integration":sorted(set(a)-set(b)),
            "changed":sorted(k for k in a.keys()&b.keys() if a[k]!=b[k])}
def classify(ahead,behind):
    require(ahead>=0 and behind>=0,"negative ancestry")
    if ahead==behind==0:return "same"
    if ahead==0:return "contained_in_integration"
    if behind==0:return "descendant_of_integration"
    return "diverged"
def workflow_inventory(text):
    # Static lexical inventory, NOT a full YAML/expression evaluator. Preserve
    # the exact file hash, and flag dynamic values rather than resolving them.
    runs=sorted(set(int(x) for x in re.findall(r"(?m)^\s*run-id:\s*['\"]?(\d+)['\"]?\s*(?:#.*)?$",text)))
    dynamic=sorted(set(x.strip() for x in re.findall(r"(?m)^\s*run-id:\s*(.+)$",text) if not re.fullmatch(r"['\"]?\d+['\"]?(?:\s*#.*)?",x.strip())))
    uploads=[];downloads=[]
    lines=text.splitlines()
    for i,line in enumerate(lines):
        m=re.search(r"uses:\s*actions/(upload|download)-artifact@",line)
        if not m:continue
        fields={}
        for following in lines[i+1:]:
            if re.match(r"^\s*-\s",following):break
            f=re.match(r"^\s*(name|pattern|run-id|path|artifact-ids):\s*(.*?)\s*$",following)
            if f:fields[f[1]]=f[2]
        (uploads if m[1]=="upload" else downloads).append(fields)
    return {"literal_run_ids":runs,"unresolved_run_ids":dynamic,"uploads":uploads,"downloads":downloads,
            "trigger_lines":[x.strip() for x in lines if re.match(r"^\s*(on|push|pull_request|workflow_dispatch|schedule|branches|branches-ignore|paths|paths-ignore):",x)],
            "contains_expressions": "\${{" in text}
def run(pins,root=ROOT):
    require(INTEGRATION in pins and "main" in pins,"missing anchor branch")
    base=pins[INTEGRATION];a=tree(base,root)
    rows=[];cache={}
    for name,ref in sorted(pins.items()):
        require(re.fullmatch("[0-9a-f]{40}",ref),"invalid pin")
        if ref not in cache:
            left,right=map(int,git("rev-list","--left-right","--count",base+"..."+ref,root=root).split())
            common=git("merge-base",base,ref,root=root).decode().strip()
            require(re.fullmatch("[0-9a-f]{40}",common),"missing common ancestor")
            b=tree(ref,root);diff=changes(a,b)
            relevant={k:[p for p in v if p.startswith(("radiance/engine_overlay/","scripts/","audit/","rulesets/",".github/workflows/"))] for k,v in diff.items()}
            cache[ref]={"sha":ref,"merge_base":common,"ahead_of_integration":right,"behind_integration":left,
                        "relationship":classify(right,left),"tree_paths":len(b),"tree_diff":diff,"implementation_diff":relevant}
        rows.append({"branch":name,**cache[ref]})
    wf=[]
    # Scan each distinct workflow blob across every frozen branch. No reliance
    # on integration containing isolated feature work.
    locations=collections.defaultdict(list)
    for row in rows:
        for path,(_,kind,oid) in tree(row["sha"],root).items():
            if kind=="blob" and path.startswith(".github/workflows/") and path.endswith((".yml",".yaml")):
                locations[(path,oid)].append(row["branch"])
    for (path,oid),branches in sorted(locations.items()):
        raw=git("cat-file","blob",oid,root=root)
        wf.append({"path":path,"git_blob":oid,"sha256":sha(raw),"branches":branches,**workflow_inventory(raw.decode())})
    return {"status":"PASS_FROZEN_ANCESTRY_INVENTORY_ONLY","integration":base,"main":pins["main"],
            "branch_count":len(rows),"unique_tip_count":len(cache),"relationship_counts":dict(collections.Counter(x["relationship"] for x in rows)),
            "branch_rows":rows,"workflow_blob_count":len(wf),"unique_workflow_paths":len({x["path"] for x in wf}),
            "literal_artifact_run_ids":sorted({v for w in wf for v in w["literal_run_ids"]}),
            "workflow_inventory":wf,"limitations":["lexical workflow scan; expressions, indirect scripts, artifact expiry and trigger semantics need separate review","no merge or deletion authorized","branch snapshot only, later refs not included"]}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pins",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    report=run(json.loads(a.pins.read_text()))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as f:json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
    print(report["status"],report["branch_count"],report["relationship_counts"],report["workflow_blob_count"])
if __name__=="__main__":main()
