#!/usr/bin/env python3
"""Run AlphaRune itself. No heuristic win-rate generation."""
import argparse, base64, csv, gzip, hashlib, itertools, json, os, pathlib, re, subprocess, sys, time
ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=ROOT/"data/optimized_58_decks.json.gz.b64"
OUT=ROOT/"results"
def decode():
    blob=base64.b64decode(DATA.read_text().strip())
    payload=json.loads(gzip.decompress(blob))
    if len(payload)!=58: raise RuntimeError("Expected 58 optimized decks; found "+str(len(payload)))
    dest=ROOT/"decks";dest.mkdir(exist_ok=True)
    for name,body in payload.items():
        if "/" in name or ".." in name or not name.endswith(".txt"): raise ValueError(name)
        (dest/name).write_text(body,encoding="utf-8")
    return sorted(dest.glob("*.txt"))
def header(p):
    s=p.read_text(encoding="utf-8")
    m=re.search(r"^Legend:\s*\n1 (.+)$",s,re.M)
    return m.group(1) if m else p.stem
def gametest(exe,a,b,seed,seconds,agent):
    cmd=[str(exe.absolute()),"--deck1",str(a.absolute()),"--deck2",str(b.absolute()),"--agent1",agent,"--agent2",agent,"--game-mode","match","--seed",str(seed),"--web","off","--render-html","off"]
    try:
        p=subprocess.run(cmd,capture_output=True,text=True,timeout=seconds)
        hit=re.search(r"Game over:\s*winner\s*=\s*([012])",p.stdout)
        return {"status":"complete" if p.returncode==0 and hit else "failed","winner":int(hit.group(1)) if hit else None,"returncode":p.returncode,"stdout_tail":p.stdout[-2500:],"stderr_tail":p.stderr[-2500:]}
    except subprocess.TimeoutExpired:
        return {"status":"timeout","winner":None,"returncode":None,"stdout_tail":"","stderr_tail":"Exceeded "+str(seconds)+"s"}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--engine",default="alpharune/build/riftbound")
    p.add_argument("--mode",choices=["check","smoke","one_pair"],default="smoke")
    p.add_argument("--agent",default="random")
    p.add_argument("--seconds",type=int,default=120)
    args=p.parse_args()
    OUT.mkdir(exist_ok=True)
    decks=decode(); named={header(x):x for x in decks}
    manifest=[{"legend":k,"filename":v.name,"sha256":hashlib.sha256(v.read_bytes()).hexdigest()} for k,v in named.items()]
    (OUT/"manifest.json").write_text(json.dumps(manifest,indent=2))
    print(f"Decoded {len(decks)} original decklists, sha256 manifests saved.",flush=True)
    catalog=ROOT/"alpharune/cards/card_index.json"
    if catalog.exists():
        cards=json.loads(catalog.read_text());known=set(c.get("name") for c in cards)
        missing=[]
        for name,file in named.items():
            for line in file.read_text().splitlines():
                mat=re.match(r"^(\\d+) (.+)$",line)
                if mat and mat.group(2) not in known: missing.append((name,mat.group(2)))
        with (OUT/"catalog_missing.csv").open("w",newline="") as f:
            w=csv.writer(f);w.writerow(["Legend","Card missing from catalog"]);w.writerows(missing)
        print(f"Card-name catalog coverage: {len(missing)} missing deck/card occurrences (not implementation validation)",flush=True)
    if args.mode=="check": return 0
    exe=ROOT/args.engine
    if not exe.exists(): print("Missing compiled AlphaRune binary",file=sys.stderr);return 2
    pairs=[("Azir, Emperor of the Sands","Rek'Sai, Void Burrower"),("Vex, Gloomist","Riven, The Exile"),("Kennen, Heart of the Tempest","Irelia, Blade Dancer")]
    if args.mode=="one_pair": pairs=pairs[:1]
    records=[]
    for idx,(name_a,name_b) in enumerate(pairs):
        for seating,(a,b) in enumerate([(name_a,name_b),(name_b,name_a)]):
            if a not in named or b not in named: raise RuntimeError(f"Missing deck: {a} / {b}")
            seed=2026112301+idx*100+seating
            tic=time.monotonic()
            result=gametest(exe,named[a],named[b],seed,args.seconds,args.agent)
            record={"deck1":a,"deck2":b,"seed":seed,"agent":args.agent,"engine_commit":"ec90f0fed002aed374d06249fa95e83e3cfbd386","duration_sec":round(time.monotonic()-tic,2),**result}
            records.append(record)
            print(f"{a} vs {b}: {result['status']} winner seat {result['winner']}; time {record['duration_sec']}s",flush=True)
    with (OUT/"engine_games.jsonl").open("w") as f:
        for record in records: f.write(json.dumps(record)+"\n")
    print(f"Real AlphaRune games completed: {sum(x['status']=='complete' for x in records)} / {len(records)}",flush=True)
    return 0 if any(x["status"]=="complete" for x in records) else 1
if __name__=="__main__":sys.exit(main())
