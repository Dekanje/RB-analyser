#!/usr/bin/env python3
"""Full fresh engine-versioned 580/580 registered deck compatibility gate.

When a C++ card-rule repair changes the compiled binary, previously accepted
native-game evidence is NOT silently transferable. This checks ALL 580
registered structural variants on the NEW exact engine SHA and unchanged
registry/58 source baselines, not a mix of old and new runs. Random-agent
complete games establish engine compatibility only, not competitive fitness.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from full_structural_native import sources
from optimize_58 import benchmark,registry,stable_seed
from round_robin_58 import sha
from sideboard_deck import parse_deck
from structural_deck_population import legal_registration

KINDS=("rune","battlefield","sideboard","champion")
EXPECTED=580


def schedule(rows,legends,shard,shards):
    selected=[n for i,n in enumerate(sorted(legends)) if i%shards==shard]
    entries=[(name,variant)
             for name in selected for variant in rows[name]["variants"]]
    return selected,entries


def run(a):
    manifest,originals,rows,manifest_sha=sources(a.variants,a.selected,a.registry)
    if not a.engine or not a.engine.is_file():
        raise RuntimeError("Missing verified new native engine")
    byname=registry(a.registry)
    selected,entries=schedule(rows,originals,a.shard,a.shards)
    rows_out=[]
    env=__import__("os").environ.copy()
    env.pop("RIFTBOUND_FORCE_STARTING_PLAYER",None)
    for name,entry in entries:
        if entry["kind"] not in KINDS:
            raise RuntimeError("Unknown registration component")
        new=a.variants/entry["path"]
        old=originals[name]
        if sha(new)!=entry["sha256"]:
            raise RuntimeError("Mutated source registration hash")
        legal_registration(parse_deck(old.read_text()),
                           parse_deck(new.read_text()),byname)
        seed=stable_seed(a.seed,"FRESH_580_NATIVE",name,entry["kind"],
                         entry["sha256"])
        r=benchmark(a.engine.resolve(),new,old,seed,"random",a.timeout,env)
        passed=r["status"]=="complete" and r["winner"] in (1,2)
        rows_out.append({
            "legend":name,"kind":entry["kind"],
            "candidate_sha256":entry["sha256"],
            "candidate_path":entry["path"],
            "registered_baseline_sha256":sha(old),
            "seed":seed,"native_status":r["status"],
            "winner":r["winner"],"completed":passed,
            "error":r.get("error","")
        })
        if not passed:
            print("FRESH_580_NATIVE_FAILED",name,entry["kind"],seed,
                  r.get("error",""),flush=True)
            raise RuntimeError("Full native-game compatibility failed; no imputation")
    packet={
        "status":"FRESH_REPAIRED_ENGINE_STRUCTURAL_NATIVE_580_SHARD",
        "shard":a.shard,"shards":a.shards,
        "source_manifest_sha256":manifest_sha,
        "native_engine_sha256":sha(a.engine),
        "registry_sha256":sha(a.registry),
        "tested_legends":selected,"games_expected":len(entries),
        "games_completed":len(rows_out),
        "games_failed":0,
        "fitness_comparisons":0,
        "registered_decks_modified":False,
        "agent":"random",
        "seed":a.seed,
        "records":rows_out
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(packet,indent=2))
    print("FRESH_NATIVE_580_SHARD_PASS",a.shard,len(rows_out),flush=True)


def aggregate(a):
    manifest,originals,rows,manifest_sha=sources(a.variants,a.selected,a.registry)
    if not a.engine or not a.engine.is_file():
        raise RuntimeError("Repaired native C++ binary required for SHA binding")
    expected={(name,entry["kind"],entry["sha256"],entry["path"])
              for name in originals for entry in rows[name]["variants"]}
    if len(expected)!=EXPECTED:
        raise RuntimeError("Not exactly 580 distinct registered candidates")
    received={}
    engine_sha=sha(a.engine)
    for shard in range(a.shards):
        path=a.input/f"fresh580-{shard}"/"native.json"
        d=json.loads(path.read_text())
        names,wanted=schedule(rows,originals,shard,a.shards)
        shard_expected={(name,x["kind"],x["sha256"],x["path"])
                        for name,x in wanted}
        if (d.get("status")!="FRESH_REPAIRED_ENGINE_STRUCTURAL_NATIVE_580_SHARD"
            or d.get("source_manifest_sha256")!=manifest_sha
            or d.get("native_engine_sha256")!=engine_sha
            or d.get("registry_sha256")!=sha(a.registry)
            or d.get("shard")!=shard or d.get("shards")!=a.shards
            or d.get("tested_legends")!=names
            or d.get("games_expected")!=len(shard_expected)
            or d.get("games_completed")!=len(shard_expected)
            or d.get("games_failed")!=0 or d.get("fitness_comparisons")!=0
            or d.get("registered_decks_modified") is not False
            or d.get("agent")!="random" or d.get("seed")!=a.seed
            or len(d.get("records",[]))!=len(shard_expected)):
            raise RuntimeError("Missing/version-mismatched 580 structural shard "
                               +str(shard))
        observed=set()
        for row in d["records"]:
            key=(row["legend"],row["kind"],
                 row["candidate_sha256"],row["candidate_path"])
            correct_seed=stable_seed(a.seed,"FRESH_580_NATIVE",*(
                row[k] for k in ("legend","kind","candidate_sha256")
            ))
            if (key not in shard_expected or key in received or key in observed
                or row["seed"]!=correct_seed
                or row["registered_baseline_sha256"]!=sha(originals[row["legend"]])
                or row["native_status"]!="complete"
                or row["completed"] is not True
                or row["winner"] not in (1,2) or row["error"]):
                raise RuntimeError("Tampered, duplicated or incomplete C++ game receipt")
            observed.add(key)
            received[key]=row
        if observed!=shard_expected:
            raise RuntimeError("Missing registered card-family games")
    if set(received)!=expected or len(received)!=EXPECTED:
        raise RuntimeError("580/580 unique source cards not actually played")
    families=collections.Counter(k[1] for k in received)
    if dict(families)!=manifest["families"]:
        raise RuntimeError("Registered source card-family counts changed")
    report={
        "status":"ALL_580_REGISTERED_STRUCTURAL_NATIVE_GAMES_PASS",
        "legends":58,"structural_variants":580,
        "previously_accepted_first_family_games":0,
        "new_native_games_completed":580,
        "all_native_games_completed":580,
        "native_game_failures":0,
        "native_engine_sha256":engine_sha,
        "source_manifest_sha256":manifest_sha,
        "registry_sha256":sha(a.registry),
        "families":dict(families),
        "native_compatibility_only":True,
        "strength_assessed":False,
        "mechanics_completeness_proven":False,
        "original_decks_modified":False,
        "verified_new_game_receipts":[received[k] for k in sorted(received)],
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2))
    print("ALL580_FRESH_NATIVE_CPP_ENGINE_VERSIONED_PASS",engine_sha,flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("selected","variants","registry","engine","output"):
        p.add_argument("--"+n,type=pathlib.Path,required=True)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--shards",type=int,default=29)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--seed",type=int,default=202611271655)
    p.add_argument("--timeout",type=float,default=120)
    a=p.parse_args()
    if not 1<=a.shards<=58 or not 0<=a.shard<a.shards or a.timeout<=0:
        p.error("Invalid source or shard indices")
    if a.aggregate:
        if a.input is None:
            p.error("Aggregate requires --input")
        aggregate(a)
    else:
        run(a)


if __name__=="__main__":
    main()
