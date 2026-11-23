#!/usr/bin/env python3
"""Native source-hashed structural legality smoke, NEVER a deck-strength test.

Run one representative rune, battlefield, sideboard and alternate Champion
variant for each requested Legend. Evaluate real C++ game to completion using
cheap random agents. No candidate adoption; failures fail closed.
"""
from __future__ import annotations
import argparse
import json
import os
import pathlib
import sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from optimize_58 import benchmark,stable_seed,registry
from round_robin_58 import load_decks,sha
from sideboard_deck import parse_deck
from structural_deck_population import legal_registration

WORLD_TRIO=(
    "Draven, Glorious Executioner",
    "LeBlanc, Deceiver",
    "Master Yi, Wuju Bladesman",
)


def run(args):
    meta=json.loads((args.variants/"structural_manifest.json").read_text())
    original,_=load_decks(args.selected)
    byname=registry(args.registry)
    rows={x["legend"]:x for x in meta["records"]}
    if (meta["status"]!="ALL58_REGISTERED_STRUCTURE_PROPOSALS_UNTESTED" or
        meta["legends"]!=58 or meta["variants_total"]!=580 or
        meta["native_registry_sha256"]!=sha(args.registry) or
        meta["engine_tested"] is not False or set(rows)!=set(original)):
        raise RuntimeError("Wrong original structural proposal source")
    if not args.engine.is_file():
        raise RuntimeError("Exact pinned C++ binary missing")
    if args.all58:
        targets=tuple(n for i,n in enumerate(sorted(original))
                      if i%args.shards==args.shard)
        if args.legend:
            raise ValueError("Cannot mix --all58 with --legend")
    else:
        targets=tuple(args.legend) if args.legend else WORLD_TRIO
    env=os.environ.copy()
    env.pop("RIFTBOUND_FORCE_STARTING_PLAYER",None)
    records=[]
    for legend in targets:
        if legend not in original:
            raise RuntimeError("Legend missing: "+legend)
        original_file=original[legend]
        baseline=parse_deck(original_file.read_text(encoding="utf-8"))
        if rows[legend]["original_sha256"]!=sha(original_file):
            raise RuntimeError("Baseline SHA mismatch")
        for kind in ("rune","battlefield","sideboard","champion"):
            entries=[x for x in rows[legend]["variants"] if x["kind"]==kind]
            if not entries:
                continue
            option=entries[0]
            card_path=args.variants/option["path"]
            if sha(card_path)!=option["sha256"] or option["native_engine_simulated"]:
                raise RuntimeError("Candidate SHA or provenance mismatch")
            mutated=parse_deck(card_path.read_text(encoding="utf-8"))
            legal_registration(baseline,mutated,byname)
            outcome=benchmark(
                args.engine.resolve(),card_path,original_file,
                stable_seed(args.seed,"REGISTERED_STRUCTURE_SMOKE",legend,kind),
                "random",args.timeout,env
            )
            completed=(outcome["status"]=="complete"
                       and outcome["winner"] in (1,2))
            records.append({
                "legend":legend,"kind":kind,
                "candidate_sha256":option["sha256"],
                "original_sha256":sha(original_file),
                "completed":completed,
                "native_status":outcome["status"],
                "engine_error":outcome.get("error",""),
            })
            print("STRUCTURAL_NATIVE_GAME",legend,kind,completed,flush=True)
    payload={
        "status":"STRUCTURAL_NATIVE_PROBE_NOT_FITNESS",
        "all58_sharded":args.all58,
        "shard":args.shard if args.all58 else None,
        "shards":args.shards if args.all58 else None,
        "source_manifest_sha256":sha(args.variants/"structural_manifest.json"),
        "native_engine_sha256":sha(args.engine),
        "tested_legends":list(targets),
        "games_attempted":len(records),
        "completed_games":sum(x["completed"] for x in records),
        "failed_games":sum(not x["completed"] for x in records),
        "agent":"random",
        "main_deck_replacements":0,"strength_inferences":0,
        "all_58_structural_variants_certified":False,
        "records":records,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(payload,indent=2),encoding="utf-8")
    if payload["failed_games"] or not records:
        raise RuntimeError("Native card/registration compatibility unresolved")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--variants",type=pathlib.Path,required=True)
    p.add_argument("--registry",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,required=True)
    p.add_argument("--legend",action="append",default=[])
    p.add_argument("--all58",action="store_true")
    p.add_argument("--shards",type=int,default=29)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--seed",type=int,default=202611251810)
    p.add_argument("--timeout",type=float,default=120)
    p.add_argument("--output",type=pathlib.Path,required=True)
    a=p.parse_args()
    if (a.timeout<=0 or not 1<=a.shards<=58 or
        not 0<=a.shard<a.shards):
        p.error("Invalid engine timeout or shard")
    run(a)


if __name__=="__main__":
    main()
