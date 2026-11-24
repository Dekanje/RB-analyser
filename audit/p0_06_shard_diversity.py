"""Historical deck lineage and name-multiset diversity; no fitness claims."""
import argparse,base64,gzip,hashlib,itertools,json,re,zipfile
from collections import Counter
from pathlib import Path
def require(ok,msg):
    if not ok:raise ValueError(msg)
def sha(raw):return hashlib.sha256(raw).hexdigest()

SHARDS=(14822422608,14823327101,14823665542,14822826850,14823535034,14821144074,
        14822547707,14822756903,14823970195,14823650727,14822896655,14823340048)
SOURCE_BLOB="937f446ccd16ed79a5da7500cde0b33576c8a5fa"
SECTIONS=("Legend","Champion","MainDeck","Battlefields","Runes","Sideboard")
CORRECTED={"Lucian, Purifier","Miss Fortune, Bounty Hunter","Ornn, Fire Below the Mountain","Rengar, Pridestalker"}

def parse(raw):
    v={};h=None
    for line in raw.decode().splitlines():
        line=line.strip()
        if not line:continue
        if line.endswith(":"):
            h=line[:-1];require(h in SECTIONS and h not in v,"invalid section")
            v[h]=Counter();continue
        m=re.fullmatch(r"([1-9][0-9]*) (.+)",line)
        require(m is not None and h is not None,"invalid deck row")
        v[h][m[2]]+=int(m[1])
    require(tuple(v)==SECTIONS and sum(v["MainDeck"].values())==39,"invalid registration layout")
    return v

def key(v):
    return tuple((h,tuple(sorted(v[h].items()))) for h in SECTIONS)

def distance(a,b):
    require(sum(a.values())==sum(b.values()),"unequal sizes")
    return sum((a-b).values())

def changed(v,steps):
    out={h:c.copy() for h,c in v.items()}
    for s in steps:
        a,b=s["remove"],s["add"]
        require(a!=b and out["MainDeck"][a]>0,"impossible mutation")
        out["MainDeck"][a]-=1
        out["MainDeck"][b]+=1
    out["MainDeck"]=+out["MainDeck"]
    return out

def open_pin(root,i,pins):
    path=root/f"{i}.zip"
    require(sha(path.read_bytes())==pins[str(i)],"archive drift "+str(i))
    return zipfile.ZipFile(path)

def source_payload(path):
    raw=path.read_bytes()
    gitblob=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
    require(gitblob==SOURCE_BLOB,"original source blob drift")
    d=json.loads(gzip.decompress(base64.b64decode(raw.strip(),validate=True)))
    require(len(d)==58 and all(isinstance(v,str) for v in d.values()),"invalid original roster")
    return {k:v.encode() for k,v in d.items()}

def legal_bytes(raw,edits):
    if not edits:return raw
    lines=raw.decode().splitlines()
    lo,hi=lines.index("MainDeck:")+1,lines.index("Battlefields:")
    for e in edits:
        matches=[i for i in range(lo,hi) if lines[i]==e["before"]]
        require(len(matches)==1,"correction anchor drift")
        lines[matches[0]]=None if e["after"]=="<removed>" else e["after"]
    return ("\n".join(l for l in lines if l is not None)+"\n").encode()

def run(root,source,pins):
    originals=source_payload(source)
    with open_pin(root,14823477036,pins) as agg:
        ar={r["legend"]:r for r in json.loads(agg.read("all_58_trials.json"))}
        summary=json.loads(agg.read("summary.json"))
        expected_selected={Path(n).name:agg.read(n) for n in agg.namelist() if n.startswith("selected_decks/") and n.endswith(".txt")}
    require(len(ar)==len(expected_selected)==58,"incomplete aggregate")
    stats=Counter();dist=Counter();manifest=None;seen=set();selected={};shards=[]
    for i in SHARDS:
        with open_pin(root,i,pins) as z:
            raw=z.read("legal_source_manifest.json");m=json.loads(raw)
            require(manifest is None or raw==manifest,"different legal source manifest");manifest=raw
            byname={r["legend"]:r for r in m["decks"]}
            require(len(byname)==58 and set(byname)==set(ar),"bad legal roster")
            require({n for n,r in byname.items() if r["changed"]}==CORRECTED,"unexpected corrections")
            require({e["legend"] for e in m["edits"]}==CORRECTED and m["originals_untouched"] is True,"bad correction manifest")
            legal={}
            for name,r in byname.items():
                fn=r["filename"];o=originals[fn]
                require(sha(o)==r["original_sha256"],"original bytes drift")
                corrected=legal_bytes(o,[e for e in m["edits"] if e["legend"]==name])
                legal[name]=z.read("legal_inputs/"+fn)
                require(corrected==legal[name] and sha(corrected)==r["effective_sha256"] and r["changed"]==(o!=corrected),"legal source mismatch")
                parse(corrected);stats["legal_source_copies_verified"]+=1
            s=json.loads(z.read("summary.json"));rs=json.loads(z.read("results.json"))
            require(s["legends_tested"]==len(rs) and s["failed"]==0 and s["improved"]==sum(r["selected"] for r in rs),"shard summary drift")
            stats["reported_cached_bo3_evaluations"]+=s["simulations"]
            proposal_paths=set()
            for r in rs:
                name=r["legend"];require(name not in seen and r==ar[name],"shard duplicate or aggregate mismatch");seen.add(name)
                orig=parse(legal[name]);inc=orig;inc_raw=legal[name];semantic=set()
                require(sha(inc_raw)==r["original_sha256"],"incumbent hash mismatch")
                for round in r["rounds"]:
                    for p in round["prefilter"]:
                        path=p["file"]
                        require(path.startswith("proposals/") and path not in proposal_paths,"duplicate proposal path")
                        proposal_paths.add(path)
                        v=parse(z.read(path))
                        require(v==changed(inc,p["swap_sequence"]),"proposal mutation mismatch")
                        semantic.add(key(v));dist[distance(orig["MainDeck"],v["MainDeck"])]+=1
                        stats["proposals"]+=1
                    if round["selected"]:
                        inc_raw=z.read(round["selected"]["file"]);inc=parse(inc_raw)
                fn=byname[name]["filename"];actual=z.read("selected_decks/"+fn)
                require(inc_raw==actual==expected_selected[fn] and sha(actual)==r["effective_sha256"],"final selection bytes mismatch")
                selected[name]=actual;stats["unique_name_multisets_per_legend"]+=len(semantic)
            require(proposal_paths=={n for n in z.namelist() if n.startswith("proposals/") and n.endswith(".txt")},"unaccounted proposal files")
            shards.append({"artifact":i,"legends":len(rs),"proposal_files":len(proposal_paths),"reported_cached_bo3_evaluations":s["simulations"]})
    require(seen==set(ar) and stats["reported_cached_bo3_evaluations"]==summary["bo3_evaluations"],"aggregate counts drift")
    with open_pin(root,14876264231,pins) as z:
        m=json.loads(z.read("manifest.json"));syndist=Counter();pairdist=Counter();add=set();remove=set();signals=Counter();unique=0;paths=set();legends=set()
        require(m["source_roster_sha256"]==sha(json.dumps({n:sha(b) for n,b in sorted(selected.items())},sort_keys=True).encode()),"synergy source drift")
        for r in m["records"]:
            name=r["legend"];require(name not in legends and r["original_sha256"]==sha(selected[name]),"synergy legend drift");legends.add(name)
            orig=parse(selected[name]);vs=[]
            require(r["count"]==len(r["candidates"])==6,"synergy count")
            for p in r["candidates"]:
                path=p["path"];require(path not in paths,"duplicate synergy file");paths.add(path)
                raw=z.read(path);v=parse(raw)
                require(sha(raw)==p["sha256"] and v==changed(orig,p["steps"]) and p["native_simulated"] is False,"synergy lineage drift")
                d=distance(orig["MainDeck"],v["MainDeck"])
                require(d==p["depth"]==len(p["steps"]) and d in (2,3),"synergy depth")
                syndist[d]+=1;vs.append(v);add.update(s["add"] for s in p["steps"]);remove.update(s["remove"] for s in p["steps"]);signals.update(p["printed_synergy_signals"])
            unique+=len({key(v) for v in vs})
            pairdist.update(distance(a["MainDeck"],b["MainDeck"]) for a,b in itertools.combinations(vs,2))
        require(legends==set(ar) and len(paths)==348 and paths=={n for n in z.namelist() if n.endswith(".txt")},"synergy coverage drift")
    return {"status":"PASS_HISTORICAL_LINEAGE_ONLY","source_git_blob":SOURCE_BLOB,
            "source_legends":58,"corrected_legends":sorted(CORRECTED),"legal_manifest_sha256":sha(manifest),
            "shards":shards,"optimizer":dict(stats),"optimizer_distance_from_legal_incumbent":dict(dist),
            "synergy":{"unique_name_multisets":unique,"distance_from_incumbent":dict(syndist),
                       "within_legend_pairwise_distance":dict(pairdist),"distinct_added_names":len(add),
                       "distinct_removed_names":len(remove),"printed_signals":dict(signals)},
            "limitations":["name-multiset comparison only, not functional printing equivalence",
                           "reported cached BO3 counts not individual verified game receipts",
                           "original source acquisition or blind discovery not certified"],
            "new_native_games":0,"adopted":0}
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("archives","source","output"):p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args();pins=json.loads(Path(__file__).with_name("p0_06_shard_pins.json").read_text())
    report=run(a.archives,a.source,pins);a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as f:json.dump(report,f,indent=2,sort_keys=True);f.write("\n")
    print(report["status"],report["optimizer"],report["synergy"])
if __name__=="__main__":main()
