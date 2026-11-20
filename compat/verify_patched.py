#!/usr/bin/env python3
"""Validate patched cards against compiled engine, then exercise all 58 real games."""
import csv,json,pathlib,sys,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_actual_games import decode,header,gametest
from apply_patches import apply, read_parts, OUT

def main():
    exe=ROOT/"alpharune/build/riftbound"
    if not exe.is_file():raise SystemExit("No compiled AlphaRune")
    original=decode();variants=apply(original)
    if len(variants)!=58:raise SystemExit("Expected 58 total deck files")
    registry=OUT/"engine_registry.json"
    subprocess.run([str(exe),"--dump-registry",str(registry)],check=True)
    data=json.loads(registry.read_text())["cards"]
    byname={x["name"]:x for x in data}
    candidate_cards=[]
    for deck in variants:
        parts=read_parts(deck.read_text())
        original_parts=read_parts(next(p for p in original if p.name==deck.name).read_text())
        domains={name[:-5].lower() for q,name in parts["Runes"] if name.endswith(" Rune")}
        errors=[]
        for section in ("MainDeck","Sideboard","Champion","Battlefields","Runes"):
            for qty,name in parts[section]:
                c=byname.get(name)
                if not c:errors.append("Unimplemented: "+section+" "+name);continue
                if c["banned"]:errors.append("Banned: "+name)
                if section in ("MainDeck","Sideboard") and not set(c["domains"]).issubset(domains):
                    errors.append("Wrong domain: "+name)
                if section in ("MainDeck","Sideboard"):
                    combined=qty+sum(q for q,n in parts["Sideboard" if section=="MainDeck" else "MainDeck"] if n==name)
                    cap=1 if c["features"]["keywords"][20] else 3
                    if combined>cap:errors.append(f"Too many {name}: {combined}>{cap}")
        candidate_cards.append({"legend":header(deck),"patched":deck.parent.name=="compat_decks",
                                "static_checks":"PASS" if not errors else "FAIL",
                                "errors":"; ".join(sorted(set(errors)))})
    if any(x["static_checks"]=="FAIL" for x in candidate_cards):
        print("Static deck checks failed",flush=True)
    anchor=next(p for p in variants if header(p)=="Kennen, Heart of the Tempest")
    results=[]
    for idx,deck in enumerate(sorted(variants,key=header)):
        result=gametest(exe,deck,anchor,2026112700+idx,30,"random")
        row={"legend":header(deck),"patched":deck.parent.name=="compat_decks",
             "engine_status":result["status"],
             "failure":result["stderr_tail"][-600:] if result["status"]!="complete" else "",
             "static_checks":next(x["static_checks"] for x in candidate_cards if x["legend"]==header(deck))}
        results.append(row)
        print(f"VERIFY {idx+1}/58 {row['legend']}: {row['engine_status']}",flush=True)
    with (OUT/"deck_validation.csv").open("w",newline="",encoding="utf8") as f:
        writer=csv.DictWriter(f,fieldnames=["legend","patched","engine_status","static_checks","failure"])
        writer.writeheader();writer.writerows(results)
    with (OUT/"deck_static_audit.csv").open("w",newline="",encoding="utf8") as f:
        writer=csv.DictWriter(f,fieldnames=["legend","patched","static_checks","errors"])
        writer.writeheader();writer.writerows(candidate_cards)
    ok=sum(x["engine_status"]=="complete" for x in results)
    ok_patched=sum(x["engine_status"]=="complete" and x["patched"] for x in results)
    stats={"engine_playable":ok,"total_decks":58,"patched_playable":ok_patched,
           "patched_total":10,"unchanged_playable":ok-ok_patched,
           "still_unsupported":58-ok,"compatibility_equivalent_to_original":False}
    (OUT/"validation_summary.json").write_text(json.dumps(stats,indent=2))
    print("COMPATIBILITY_RESULT "+json.dumps(stats),flush=True)
    return 0 if ok>=49 and ok_patched==10 and not any(x["static_checks"]=="FAIL" for x in candidate_cards if x["patched"]) else 1
if __name__=="__main__":raise SystemExit(main())
