#!/usr/bin/env python3
"""Generate registered structural variants across all 58 Legends (UNTESTED).

Separate from the 39-card MainDeck population (58×40). Mutates only legal
registered components:
* Runes: redistribute twelve basic runes between the Legend's two domains.
* Battlefields: one distinct, currently legal compiled battlefield replacement.
* Sideboard: one legal non-signature, non-Neeko card replacement, respecting
  main+sideboard+Champion copy limits and exact 10-card sideboard capacity.
* Chosen Champion: choose another compatible champion from the registered
  Main/sideboard while preserving the complete registered pool.

Every proposal is checked against the compiled card data AND structural
constraints, source hashed, and marked UNTESTED. Native game validation
is a separate explicit acceptance gate. No prices/market heuristics, no
automatic main-deck replacement, no claims that structural variants improve
performance. Special Neeko registration remains a dedicated later phase.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import random
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from optimize_58 import BAN_KEYS,effective_domains,is_unique,key,registry,stable_seed
from round_robin_58 import load_decks,sha
from sideboard_deck import DeckState,parse_deck,render_deck,validate_structure
from tournament_bo3_policy import check_final_legality,transition


def clean(counter:collections.Counter):
    return +counter


def legal_registration(original:DeckState, candidate:DeckState, byname:dict)->None:
    if candidate.legend!=original.legend:
        raise ValueError("Registered Legend must remain fixed")
    validate_structure(candidate)
    check_final_legality(candidate,candidate,byname)
    domains=effective_domains(original.legend,byname)
    if len(domains)!=2:
        raise ValueError("Expected two registered domains")
    if any(
        byname.get(name,{}).get("card_type")!="rune"
        or byname[name].get("banned")
        or not set(byname[name].get("domains") or []).issubset(domains)
        or copies<1
        for name,copies in candidate.runes.items()
    ):
        raise ValueError("Illegal rune for registered Legend domain")
    if any(
        byname.get(name,{}).get("card_type")!="battlefield"
        or byname[name].get("banned") or key(name) in BAN_KEYS
        or copies!=1
        for name,copies in candidate.battlefields.items()
    ):
        raise ValueError("Illegal or repeated registered battlefield")
    # Exact copy limits for MAIN + SIDE + chosen Champion where relevant.
    pool=candidate.main+candidate.sideboard+collections.Counter({
        candidate.champion:1
    })
    for name,copies in pool.items():
        card=byname.get(name)
        if card is None or card.get("banned") or key(name) in BAN_KEYS:
            raise ValueError("Unknown/banned registered card")
        if copies>(1 if is_unique(card) else 3):
            raise ValueError("Registered card copies exceed unique/nonunique limit")
    # For structural-only candidates, retain mandatory signature slots.
    for name,n in original.main.items():
        c=byname.get(name,{})
        if "signature" in (c.get("super_type") or "").lower():
            if candidate.main.get(name,0)!=n:
                raise ValueError("Signature Main Deck cards must be retained")
    for name,n in original.sideboard.items():
        c=byname.get(name,{})
        if "signature" in (c.get("super_type") or "").lower():
            if candidate.sideboard.get(name,0)!=n:
                raise ValueError("Signature Sideboard cards must be retained")


def rune_variants(original:DeckState,byname:dict):
    domains=sorted(effective_domains(original.legend,byname))
    names=[f"{x.title()} Rune" for x in domains]
    if any(n not in byname for n in names):
        raise ValueError("Domain rune missing from registry")
    for first in (4,5,7,8):
        candidate=original.clone()
        candidate.runes=collections.Counter({
            names[0]:first,names[1]:12-first,
        })
        if candidate.runes!=original.runes:
            yield f"rune_split_{first}_{12-first}",candidate,{
                "rune_first":names[0],"rune_first_copies":first,
                "rune_second":names[1],"rune_second_copies":12-first
            }


def battlefield_variants(original:DeckState,byname:dict,seed:int,limit:int=3):
    available=sorted(
        name for name,card in byname.items()
        if card.get("card_type")=="battlefield"
        and not card.get("banned") and key(name) not in BAN_KEYS
        and name not in original.battlefields
    )
    if len(available)<limit:
        raise ValueError("Not enough unbanned alternative battlefields")
    rng=random.Random(seed)
    sample=rng.sample(available,min(limit,len(available)))
    old=sorted(original.battlefields)
    for i,new in enumerate(sample):
        candidate=original.clone()
        previous=old[i%len(old)]
        candidate.battlefields[previous]-=1
        candidate.battlefields[new]+=1
        candidate.battlefields=clean(candidate.battlefields)
        yield f"battlefield_{i}",candidate,{
            "out":previous,"in":new
        }


def sideboard_variants(original:DeckState,byname:dict,seed:int,limit:int=3):
    domains=effective_domains(original.legend,byname)
    old_cards=sorted(
        n for n in original.sideboard
        if "signature" not in (byname[n].get("super_type") or "").lower()
        and n!=original.champion
    )
    choices=sorted(
        n for n,card in byname.items()
        if card.get("card_type") in ("unit","spell","gear")
        and n!="Neeko, Blending In"
        and not card.get("banned") and key(n) not in BAN_KEYS
        and "signature" not in (card.get("super_type") or "").lower()
        and "token" not in (card.get("super_type") or "").lower()
        and set(card.get("domains") or []).issubset(domains)
        and (original.main.get(n,0)+original.sideboard.get(n,0)
             +(1 if n==original.champion else 0))
              <(1 if is_unique(card) else 3)
    )
    if not old_cards or not choices:
        return
    rng=random.Random(seed)
    rng.shuffle(choices)
    rng.shuffle(old_cards)
    out=0
    for old in old_cards:
        for new in choices:
            if new==old:
                continue
            candidate=original.clone()
            candidate.sideboard[old]-=1
            candidate.sideboard[new]+=1
            candidate.sideboard=clean(candidate.sideboard)
            try:
                legal_registration(original,candidate,byname)
            except ValueError:
                continue
            yield f"sideboard_{out}",candidate,{"out":old,"in":new}
            out+=1
            if out>=limit:
                return


def chosen_champion_variants(original:DeckState,byname:dict,limit:int=2):
    hero=key(original.legend.split(",",1)[0])
    registered=original.main+original.sideboard
    for n in sorted(registered):
        if n==original.champion or n not in byname:
            continue
        c=byname[n]
        if ("champion" not in (c.get("super_type") or "").lower()
            or hero not in {key(x) for x in c.get("tags",[])}
            or c.get("banned")):
            continue
        try:
            candidate=transition(original,{"chosen_champion":n},
                                 byname,game_no=2)
            legal_registration(original,candidate,byname)
        except ValueError:
            continue
        yield f"chosen_champion_{n}",candidate,{
            "original_champion":original.champion,
            "alternate_champion":n,
        }
        limit-=1
        if limit==0:
            break


def generate_one(
    name:str,deck:pathlib.Path,byname:dict,output:pathlib.Path,seed:int
):
    registered=parse_deck(deck.read_text(encoding="utf-8"))
    legal_registration(registered,registered,byname)
    digest=sha(deck)
    seen={hashlib.sha256(render_deck(registered).encode()).hexdigest()}
    folder=output/deck.stem
    folder.mkdir(parents=True,exist_ok=True)
    generated=[]
    families=[
        ("rune",rune_variants(registered,byname)),
        ("battlefield",battlefield_variants(
            registered,byname,stable_seed(seed,name,"battlefield")
        )),
        ("sideboard",sideboard_variants(
            registered,byname,stable_seed(seed,name,"sideboard")
        )),
        ("champion",chosen_champion_variants(registered,byname)),
    ]
    for family,items in families:
        for variant,candidate,changes in items:
            legal_registration(registered,candidate,byname)
            text=render_deck(candidate)
            h=hashlib.sha256(text.encode()).hexdigest()
            if h in seen:
                continue
            seen.add(h)
            path=folder/f"structural_{len(generated):03d}.txt"
            path.write_text(text,encoding="utf-8")
            generated.append({
                "path":str(path.relative_to(output)),
                "sha256":h,"kind":family,"variant":variant,
                "changes":changes,
                "native_engine_simulated":False,
                "fitness_evaluated":False,
                "registered_legend_unchanged":True,
            })
    if not generated:
        raise RuntimeError("No structural proposals generated: "+name)
    return {
        "legend":name,"original_sha256":digest,
        "variants":generated,"count":len(generated),
        "types":dict(collections.Counter(x["kind"] for x in generated)),
        "status":"STRUCTURAL_CANDIDATES_ONLY_NOT_NATIVE_TESTED",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--registry",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--seed",type=int,default=202611251700)
    args=p.parse_args()
    decks,_=load_decks(args.selected)
    byname=registry(args.registry)
    args.output.mkdir(parents=True,exist_ok=True)
    records=[
        generate_one(name,deck,byname,args.output,args.seed)
        for name,deck in sorted(decks.items())
    ]
    families=collections.Counter(
        x["kind"] for record in records for x in record["variants"]
    )
    manifest={
        "status":"ALL58_REGISTERED_STRUCTURE_PROPOSALS_UNTESTED",
        "source_58_roster_sha256":hashlib.sha256(
            json.dumps({n:sha(d) for n,d in sorted(decks.items())},
                       sort_keys=True).encode()).hexdigest(),
        "native_registry_sha256":sha(args.registry),
        "legends":len(records),
        "variants_total":sum(x["count"] for x in records),
        "families":dict(families),
        "seed":args.seed,
        "no_main_deck_or_legend_intentionally_changed":True,
        "engine_tested":False,"worlds_winner_certified":False,
        "records":records,
    }
    (args.output/"structural_manifest.json").write_text(
        json.dumps(manifest,indent=2),encoding="utf-8"
    )
    if manifest["legends"]!=58 or manifest["variants_total"]<58*4:
        raise RuntimeError("Full 58-Legend structural proposal family incomplete")
    print("ALL58_STRUCTURAL_POPULATION_ONLY",
          {k:v for k,v in manifest.items() if k!="records"},flush=True)


if __name__=="__main__":
    main()
