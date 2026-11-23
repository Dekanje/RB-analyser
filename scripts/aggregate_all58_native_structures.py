#!/usr/bin/env python3
"""Aggregate source-verified native eligibility of structural 58-Legend variants.

The 580 candidates are static Constructed proposals. This gate plays ONLY
one registration per available family/Legend with cheap random agents:
a compatibility check, absolutely not an optimization or win-rate ranking.
"""
from __future__ import annotations
import argparse
import collections
import json
import pathlib
import sys
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from round_robin_58 import load_decks,sha

KINDS=("rune","battlefield","sideboard","champion")


def aggregate(args):
    baseline,_=load_decks(args.selected)
    manifest=json.loads((args.variants/"structural_manifest.json").read_text())
    if (manifest["status"]!="ALL58_REGISTERED_STRUCTURE_PROPOSALS_UNTESTED" or
        manifest["legends"]!=58 or manifest["variants_total"]!=580 or
        manifest["native_registry_sha256"]!=sha(args.registry)):
        raise RuntimeError("Wrong structural proposal source")
    rows={x["legend"]:x for x in manifest["records"]}
    if set(rows)!=set(baseline):
        raise RuntimeError("Missing registered Legend in structural candidates")
    all_records=[]
    engine_hashes=set();seen=set();tested_legends=set()
    for shard in range(args.shards):
        source=args.input/f"structural-native-{shard}"/"smoke.json"
        packet=json.loads(source.read_text(encoding="utf-8"))
        expected_names=[n for i,n in enumerate(sorted(rows))
                        if i%args.shards==shard]
        if any((
            packet["status"]!="STRUCTURAL_NATIVE_PROBE_NOT_FITNESS",
            packet["all58_sharded"] is not True,
            packet["shards"]!=args.shards,
            packet["shard"]!=shard,
            packet["tested_legends"]!=expected_names,
            packet["source_manifest_sha256"]!=sha(args.variants/"structural_manifest.json"),
            packet["completed_games"]!=packet["games_attempted"],
            packet["failed_games"]!=0,
            packet["agent"]!="random",
            packet["main_deck_replacements"]!=0,
            packet["strength_inferences"]!=0,
            packet["all_58_structural_variants_certified"] is not False,
        )):
            raise RuntimeError("Invalid/incomplete actual native C++ shard evidence")
        engine_hashes.add(packet["native_engine_sha256"])
        tested_legends.update(packet["tested_legends"])
        for x in packet["records"]:
            legend=x["legend"];kind=x["kind"]
            if legend not in expected_names or kind not in KINDS:
                raise RuntimeError("Invalid or misplaced structural variant")
            if (legend,kind) in seen:
                raise RuntimeError("Repeated structural native match")
            seen.add((legend,kind))
            choices=[v for v in rows[legend]["variants"] if v["kind"]==kind]
            if (not choices or x["candidate_sha256"]!=choices[0]["sha256"]
                or x["original_sha256"]!=sha(baseline[legend])
                or x["native_status"]!="complete" or
                x["completed"] is not True):
                raise RuntimeError("Missing real C++ completion or wrong candidate hash")
            all_records.append(x)
        if len(packet["records"])!=packet["games_attempted"]:
            raise RuntimeError("Missing game receipt in shard")
    if len(engine_hashes)!=1 or tested_legends!=set(rows):
        raise RuntimeError("All 58 must use exactly one native engine")
    expected={(name,kind) for name in rows for kind in KINDS
              if any(v["kind"]==kind for v in rows[name]["variants"])}
    if seen!=expected:
        raise RuntimeError("At least one Legend/family lacked native verification")
    bykind=collections.Counter(x["kind"] for x in all_records)
    report={
        "status":"ALL58_STRUCTURAL_NATIVE_FIRST_FAMILY_ACCEPTANCE",
        "legends":58,
        "native_games_completed":len(all_records),
        "native_games_expected":len(expected),
        "games_by_family":dict(bykind),
        "structural_variants_generated":580,
        "variants_not_native_playtested":580-len(all_records),
        "complete_full_580_native_certification":False,
        "source_manifest_sha256":sha(args.variants/"structural_manifest.json"),
        "native_engine_sha256":next(iter(engine_hashes)),
        "native_rules_compatibility_sanity":True,
        "sideboard_strategy_optimized":False,
        "fitness_comparisons":0,
        "registered_decks_modified":False,
        "worlds_win_probability_inferred":False,
        "all_records":all_records,
    }
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print("ALL58_NATIVE_STRUCTURAL_SMOKE_FINAL",json.dumps({
        k:v for k,v in report.items() if k!="all_records"
    }),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=pathlib.Path,required=True)
    p.add_argument("--variants",type=pathlib.Path,required=True)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--registry",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--shards",type=int,default=29)
    a=p.parse_args()
    if not 1<=a.shards<=58:
        p.error("Invalid shard count")
    aggregate(a)


if __name__=="__main__":
    main()
