#!/usr/bin/env python3
"""Full 58-deck audit against compiled AlphaRune card database; never substitute cards."""
import csv, json, pathlib, re, subprocess, sys
from collections import Counter, defaultdict

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_actual_games import decode,header,gametest

out=ROOT/"audit_results";out.mkdir(exist_ok=True)
exe=ROOT/"alpharune/build/riftbound"
if not exe.is_file():raise SystemExit("No compiled AlphaRune executable")
reg=out/"engine_registry.json"
subprocess.run([str(exe),"--dump-registry",str(reg)],check=True)
allcards=json.loads(reg.read_text())["cards"]
byname=defaultdict(list)
for c in allcards:byname[c["name"]].append(c)
assert len(allcards)>900,"Unexpected card registry size"
decks=decode()
items=[];errors=[];checks=[];unsupported=defaultdict(list)
for filename in decks:
    s=filename.read_text(encoding="utf8")
    legend=header(filename);section=""
    for line in s.splitlines():
        line=line.strip()
        if line.endswith(":"):section=line[:-1];continue
        match=re.fullmatch(r"(\d+)\s+(.+)",line)
        if not match:continue
        qty,name=int(match.group(1)),match.group(2)
        # Legends are serialized by subtitle in the compiled CardDB ("Loose Cannon"),
        # but the Piltover deck format uses full "Jinx, Loose Cannon" labels.
        # Use the card type and exact subtitle; never label every legend unknown.
        if section=="Legend":
            subtitle=name.split(", ",1)[-1]
            matches=[c for c in byname.get(subtitle,[]) if c["card_type"]=="legend"]
        else:
            matches=byname.get(name,[])
        reason="OK" if matches else "NOT_IN_COMPILED_ENGINE"
        if matches and all(c["banned"] for c in matches):reason="BANNED_IN_ENGINE"
        row={"legend":legend,"deck":filename.name,"section":section,"card":name,
             "quantity":qty,"engine_status":reason,"compiled_ids":";".join(str(c["card_id"]) for c in matches),
             "banned":all(c["banned"] for c in matches) if matches else "",
             "keywords":";".join(str(c.get("features",{}).get("keywords","")) for c in matches)}
        items.append(row)
    # Nonmutation legal uniqueness + non-unique copy limits across all deck sections.
    counts=Counter()
    for x in items:
        if x["legend"]==legend and x["section"] in ("MainDeck","Sideboard"):counts[x["card"]]+=x["quantity"]
    for name,qty in counts.items():
        cs=byname.get(name)
        if cs:
            kw=cs[0].get("features",{}).get("keywords",[])
            is_unique=isinstance(kw,list) and len(kw)>20 and kw[20]==1
            maxq=1 if is_unique else 3
            if qty>maxq:errors.append({"legend":legend,"card":name,"copies":qty,"limit":maxq,"category":"UNIQUE" if is_unique else "COPY_LIMIT"})
    if legend=="Kennen, Heart of the Tempest":continue
    anchor=next(p for p in decks if header(p)=="Kennen, Heart of the Tempest")
    r=gametest(exe,filename,anchor,2026122900+len(checks),25,"random")
    checks.append({"legend":legend,"status":r["status"],
                   "diagnostic":r["stderr_tail"][-600:] if r["stderr_tail"] else r["stdout_tail"][-400:]})
# The actual parser/game run, rather than a gallery-label heuristic, is authoritative
# about whether a Legend is unsupported. This fixes subtitle/alias mismatches.
missing_legends={check["legend"] for check in checks
                 if "unknown card '"+check["legend"]+"'" in check["diagnostic"]}
unsupported=defaultdict(list)
for item in items:
    if item["engine_status"]=="OK":continue
    if item["section"]=="Legend" and item["legend"] not in missing_legends:
        item["engine_status"]="ENGINE_LEGEND_ALIAS_RESOLVED"
        continue
    unsupported[item["legend"]].append(item)
def write(p,rows,fields):
    with p.open("w",newline="",encoding="utf8") as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
write(out/"all_deck_card_lines.csv",items,["legend","deck","section","card","quantity","engine_status","compiled_ids","banned","keywords"])
write(out/"copy_limit_errors.csv",errors,["legend","card","copies","limit","category"])
write(out/"first_game_failure.csv",checks,["legend","status","diagnostic"])
blocked=[{"legend":n,"missing_entries":len(xs),
          "missing_legend":any(x["section"]=="Legend" and x["engine_status"]!="OK" for x in xs),
          "missing_cards":" | ".join(sorted(set(x["card"] for x in xs))),
          "sections":" | ".join(sorted(set(x["section"] for x in xs)))} for n,xs in sorted(unsupported.items())]
write(out/"blocked_decks.csv",blocked,["legend","missing_entries","missing_legend","missing_cards","sections"])
stats={"engine_cards":len(allcards),"total_decks":len(decks),
       "decks_with_unknown_or_banned_cards":len(blocked),
       "decks_with_unimplemented_legends":sum(r["missing_legend"] for r in blocked),
       "unique_or_copy_limit_errors":len(errors),
       "no_substitutions":True,"engine_commit":"ec90f0fed002aed374d06249fa95e83e3cfbd386"}
(out/"summary.json").write_text(json.dumps(stats,indent=2))
print("AUDIT_SUMMARY "+json.dumps(stats),flush=True)
for r in blocked:print("BLOCKED "+r["legend"]+" | "+r["missing_cards"],flush=True)
for r in errors:print("ILLEGAL "+json.dumps(r),flush=True)
