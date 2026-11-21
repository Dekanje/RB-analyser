#!/usr/bin/env python3
"""Map nine unmodified original decks to the Riot text and compiled AlphaRune registry.
This is an audit; never infer that source-data presence proves mechanical support.
Full rules text stays in short-lived workflow artifacts, not public git history.
"""
import csv, json, pathlib, re, sys
from collections import defaultdict
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from run_actual_games import decode, header
OUT=ROOT/"radiance_implementation_reports"
OUT.mkdir(exist_ok=True)
source=json.loads((ROOT/"gallery-data/data/cards.json").read_text())
compiled=json.loads((ROOT/"radiance_reports/compiled_engine_registry.json").read_text())["cards"]
engine_code={str(x.get("public_code","")).casefold() for x in compiled}
engine_names={str(x["name"]).casefold() for x in compiled}
allcards=source["cards"]
byname=defaultdict(list)
for c in allcards:
    for k in (c.get("display_name"),c.get("name"),c.get("subtitle")):
        if k:byname[str(k).casefold()].append(c)
nine={"Ekko, Boy Who Shattered Time","Evelynn, Agony's Embrace",
"Jarvan IV, Exemplar of Demacia","K'Sante, Pride of Nazumah",
"Mordekaiser, Iron Revenant","Orianna, Lady of Clockwork",
"Riven, The Exile","Seraphine, Starry-Eyed Songstress",
"Ziggs, Hexplosives Expert"}
rows=[]
details={}
def get_source(name,section):
    candidates=byname.get(name.casefold(),[])
    # engine legend name is only its printed subtitle
    if not candidates and section=="Legend" and ", " in name:
        candidates=byname.get(name.split(", ",1)[1].casefold(),[])
    candidates=[x for x in candidates if str(x.get("set",{}).get("id","")).upper()=="RAD"] or candidates
    if not candidates:return None
    # Prefer non-alternate, ordinary numbered base printing
    candidates.sort(key=lambda x:(str(x.get("public_code","")).upper().split("-")[0]!="RAD",
       bool((x.get("printing") or {}).get("overnumbered")),
       bool((x.get("printing") or {}).get("alternate_art")),
       str(x.get("public_code") or "")))
    return candidates[0]
for f in decode():
    legend=header(f)
    if legend not in nine:continue
    section=None
    for raw in f.read_text().splitlines():
        raw=raw.strip()
        if raw.endswith(":"):
            section=raw[:-1];continue
        m=re.fullmatch(r"(\d+)\s+(.+)",raw)
        if not m:continue
        qty,name=int(m.group(1)),m.group(2)
        lookup=(name.split(", ",1)[-1] if section=="Legend" else name).casefold()
        if lookup in engine_names:continue
        c=get_source(name,section)
        if c is None:
            row={"deck":legend,"section":section,"card":name,"quantity":qty,"code":"",
                 "source_found":False,"type":"","effect_text":"","needs_cpp":True}
        else:
            text=str((c.get("text") or {}).get("plain") or "")
            code=c.get("public_code") or ""
            is_already_compiled=str(code).casefold() in engine_code
            row={"deck":legend,"section":section,"card":name,"quantity":qty,"code":code,
                 "source_found":True,"type":c.get("type"),"effect_text":text,
                 "needs_cpp":not is_already_compiled}
            details[name]={"gallery_id":c.get("gallery_id"),"code":code,
              "name":name,"source_name":c.get("display_name"),"card_type":c.get("type"),
              "supertype":c.get("supertype"),"domains":c.get("domains"),
              "tags":c.get("tags"),"cost":c.get("attributes"),"rarity":c.get("rarity"),
              "rules_text":text,"set":c.get("set"),
              "source_has_card":True}
        rows.append(row)
with (OUT/"nine_deck_missing_cards.csv").open("w",newline="",encoding="utf8") as fd:
    writer=csv.DictWriter(fd,fieldnames=list(rows[0]))
    writer.writeheader();writer.writerows(rows)
(OUT/"needed_card_rules_private.json").write_text(json.dumps(details,ensure_ascii=False,indent=2))
summary={"missing_deck_occurrences":len(rows),"unique_cards":len({r["card"] for r in rows}),
         "source_resolved":len(details),"unresolved":sorted({r["card"] for r in rows if not r["source_found"]}),
         "nine_decks":len(nine),"original_decks_untouched":True,
         "mechanics_implemented":0,"stage":"RULE_TEXT_IDENTIFICATION_ONLY"}
(OUT/"summary.json").write_text(json.dumps(summary,indent=2))
print("RADIANCE_IMPLEMENTATION_AUDIT "+json.dumps(summary),flush=True)
for n in sorted(details):
    d=details[n]
    print("NEEDED_CARD "+n+" "+d["code"]+" "+str(d["card_type"]),flush=True)
if summary["unresolved"]:sys.exit(1)
