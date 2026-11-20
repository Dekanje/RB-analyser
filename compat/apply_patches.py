#!/usr/bin/env python3
"""Engine compatibility variants, preserving exact original 58 optimized decks.

Changed card lists must not be described as the same optimized decks.
This module makes no card aliases and never pretends to implement card effects.
"""
import csv, hashlib, json, pathlib, re, sys
from collections import Counter

ROOT=pathlib.Path(__file__).resolve().parents[1]
PATCHES=ROOT/"compat/replacement_manifest.json"
OUT=ROOT/"compat_results"

def read_parts(text):
    parts={};section=None
    for raw in text.splitlines():
        line=raw.strip()
        if line.endswith(":"):
            section=line[:-1]
            if section in parts:raise ValueError("Duplicate section "+section)
            parts[section]=[]
        elif line:
            m=re.fullmatch(r"(\d+)\s+(.+)",line)
            if not m or section is None:raise ValueError("Bad deck line: "+raw)
            parts[section].append((int(m.group(1)),m.group(2)))
    return parts

def write_parts(parts):
    return "\n\n".join(sec+":\n"+"\n".join(f"{qty} {name}" for qty,name in cards)
                     for sec,cards in parts.items())+"\n"

def apply(files):
    OUT.mkdir(exist_ok=True)
    candidates=ROOT/"compat_decks";candidates.mkdir(exist_ok=True)
    patches=json.loads(PATCHES.read_text(encoding="utf8"))
    original={f.name:f for f in files}
    if len(files)!=58 or len(patches)!=10:raise RuntimeError("Unexpected source list count")
    if any(k not in original for k in patches):raise RuntimeError("Patch references unknown deck")
    change_rows=[]
    newfiles=[]
    for file in files:
        orig=file.read_text(encoding="utf8")
        if file.name not in patches:
            newfiles.append(file);continue
        parts=read_parts(orig)
        for section,edits in patches[file.name].items():
            if section not in parts:raise ValueError("No section "+section+" for "+file.name)
            counters=Counter({name:q for q,name in parts[section]})
            if sum(edits.values())!=0:raise ValueError("Section quantity changed")
            for name,delta in edits.items():
                if counters[name]+delta<0:raise ValueError("Negative copies for "+name)
                counters[name]+=delta
                change_rows.append({"deck":file.name,"section":section,"card":name,
                                    "delta":delta,"before":counters[name]-delta,
                                    "after":counters[name]})
            parts[section]=[(q,n) for n,q in sorted(counters.items()) if q>0]
        assert sum(q for q,_ in parts["MainDeck"])+sum(q for q,_ in parts["Champion"])==40
        assert sum(q for q,_ in parts["Sideboard"])==10
        assert sum(q for q,_ in parts["Battlefields"])==3
        assert sum(q for q,_ in parts["Runes"])==12
        output=candidates/file.name
        output.write_text(write_parts(parts),encoding="utf8")
        if output.read_text()==orig:raise RuntimeError("Patch made no change")
        newfiles.append(output)
    with (OUT/"changes.csv").open("w",newline="",encoding="utf8") as stream:
        w=csv.DictWriter(stream,fieldnames=["deck","section","card","delta","before","after"])
        w.writeheader();w.writerows(change_rows)
    (OUT/"manifest.json").write_text(json.dumps({
        "source_decks":58,"patched_decks":len(patches),"unmodified_decks":58-len(patches),
        "patched_files":sorted(patches),"source_preserved":True,
        "card_effects_reimplemented":False,
        "note":"Card substitutions are exploratory engine-compatible variants, NOT original optimized decks",
        "original_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
        "variant_sha256":{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in newfiles}
    },indent=2))
    return newfiles
