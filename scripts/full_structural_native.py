#!/usr/bin/env python3
"""Native game completion for EVERY previously untested structural proposal.

Continues the accepted 177 representative registered-structure probes using
exactly the OTHER variants (not a second arbitrary sample). Validation only:
cheap random-agent matches do not establish strength, tactical competence or
exhaustive card mechanics. Source hashing and all-580 coverage are fail closed.
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from optimize_58 import benchmark, registry, stable_seed
from round_robin_58 import load_decks, sha
from sideboard_deck import parse_deck
from structural_deck_population import legal_registration

KINDS = ("rune", "battlefield", "sideboard", "champion")


def sources(variants, selected, registry_file):
    manifest_path = variants / "structural_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    originals, _ = load_decks(selected)
    rows = {r["legend"]: r for r in manifest["records"]}
    if (manifest["status"] != "ALL58_REGISTERED_STRUCTURE_PROPOSALS_UNTESTED"
        or manifest["legends"] != 58
        or manifest["variants_total"] != 580
        or manifest["native_registry_sha256"] != sha(registry_file)
        or manifest["engine_tested"] is not False
        or set(rows) != set(originals)
        or sum(len(r["variants"]) for r in rows.values()) != 580):
        raise RuntimeError("Wrong or incomplete exact registered structure source")
    for legend, row in rows.items():
        if row["original_sha256"] != sha(originals[legend]):
            raise RuntimeError("A registered baseline changed: " + legend)
        if len({x["path"] for x in row["variants"]}) != len(row["variants"]):
            raise RuntimeError("Duplicate registered structural path")
        if len({x["sha256"] for x in row["variants"]}) != len(row["variants"]):
            raise RuntimeError("Duplicate candidate deck identity")
    return manifest, originals, rows, sha(manifest_path)


def expected_keys(rows, *, first: bool):
    keys = []
    for name in sorted(rows):
        seen = set()
        for row in rows[name]["variants"]:
            kind = row["kind"]
            if kind not in KINDS:
                raise RuntimeError("Unexpected registration component")
            is_first = kind not in seen
            seen.add(kind)
            if is_first == first:
                keys.append((name, kind, row["sha256"], row["path"]))
    return keys


def run(args):
    manifest, originals, rows, source_hash = sources(
        args.variants, args.selected, args.registry
    )
    if not args.engine.is_file():
        raise RuntimeError("Native C++ binary missing")
    byname = registry(args.registry)
    names = [n for i, n in enumerate(sorted(rows))
             if i % args.shards == args.shard]
    all_remaining = expected_keys(rows, first=False)
    targets = [(n,k,h,p) for n,k,h,p in all_remaining if n in names]
    records = []
    env = os.environ.copy()
    env.pop("RIFTBOUND_FORCE_STARTING_PLAYER", None)
    for legend, kind, digest, rel_path in targets:
        original = originals[legend]
        candidate = args.variants / rel_path
        if sha(candidate) != digest:
            raise RuntimeError("Registered variant content SHA mismatch")
        original_state = parse_deck(original.read_text(encoding="utf-8"))
        candidate_state = parse_deck(candidate.read_text(encoding="utf-8"))
        legal_registration(original_state, candidate_state, byname)
        test_seed = stable_seed(args.seed, "STRUCTURAL_FULL_REMAINING", legend,
                                kind, digest)
        result = benchmark(
            args.engine.resolve(), candidate, original,
            test_seed, "random", args.timeout, env
        )
        completed = (result["status"] == "complete"
                     and result["winner"] in (1, 2))
        records.append({
            "legend": legend, "kind": kind, "candidate_sha256": digest,
            "original_sha256": sha(original), "candidate_path": rel_path,
            "seed": test_seed, "native_status": result["status"],
            "engine_winner": result["winner"], "completed": completed,
            "engine_error": result.get("error", "")
        })
        print("FULL_NATIVE_REMAINING", legend, kind, completed, flush=True)
    payload = {
        "status": "REGISTERED_STRUCTURAL_REMAINING_NATIVE_COMPATIBILITY",
        "source_manifest_sha256": source_hash,
        "native_engine_sha256": sha(args.engine),
        "shard": args.shard, "shards": args.shards,
        "tested_legends": names,
        "expected_games": len(targets), "games_attempted": len(records),
        "native_completed": sum(x["completed"] for x in records),
        "native_failed": sum(not x["completed"] for x in records),
        "agent": "random", "mode": "single-game-legality-only",
        "fitness_comparisons": 0, "registered_decks_modified": False,
        "records": records
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    if payload["native_failed"] or payload["native_completed"] != len(targets):
        raise RuntimeError("One or more actual C++ structural games failed")


def aggregate(args):
    manifest, originals, rows, source_hash = sources(
        args.variants, args.selected, args.registry
    )
    first = expected_keys(rows, first=True)
    remaining = expected_keys(rows, first=False)
    if len(first) != 177 or len(remaining) != 403:
        raise RuntimeError("Incorrect frozen 177+403 structural coverage")
    accepted = json.loads(args.first.read_text(encoding="utf-8"))
    if (accepted["status"] != "ALL58_STRUCTURAL_NATIVE_FIRST_FAMILY_ACCEPTANCE"
        or accepted["native_games_completed"] != 177
        or accepted["native_games_expected"] != 177
        or accepted["structural_variants_generated"] != 580
        or accepted["source_manifest_sha256"] != source_hash
        or accepted["fitness_comparisons"] != 0
        or accepted["registered_decks_modified"] is not False):
        raise RuntimeError("Earlier family-first 177 receipts are not accepted")
    first_receipts = {
        (x["legend"], x["kind"], x["candidate_sha256"])
        for x in accepted["all_records"]
    }
    if (len(first_receipts) != 177 or
        first_receipts != {(n,k,h) for n,k,h,_ in first}
        or any(x["native_status"] != "complete" or x["completed"] is not True
               for x in accepted["all_records"])):
        raise RuntimeError("Earlier 177 native games incomplete or duplicated")
    sha_set = {accepted["native_engine_sha256"]}
    complete = {}
    for shard in range(args.shards):
        file = args.input / f"remaining-structural-{shard}" / "remaining.json"
        result = json.loads(file.read_text(encoding="utf-8"))
        names = [n for i,n in enumerate(sorted(rows))
                 if i % args.shards == shard]
        expected = {(n,k,h,p) for n,k,h,p in remaining if n in names}
        if (result["status"] != "REGISTERED_STRUCTURAL_REMAINING_NATIVE_COMPATIBILITY"
            or result["source_manifest_sha256"] != source_hash
            or result["shard"] != shard or result["shards"] != args.shards
            or result["tested_legends"] != names
            or result["expected_games"] != len(expected)
            or result["games_attempted"] != len(expected)
            or result["native_completed"] != len(expected)
            or result["native_failed"] != 0 or result["agent"] != "random"
            or result["fitness_comparisons"] != 0
            or result["registered_decks_modified"] is not False
            or len(result["records"]) != len(expected)):
            raise RuntimeError("Missing or altered native structural shard " + str(shard))
        sha_set.add(result["native_engine_sha256"])
        actual = set()
        for x in result["records"]:
            key = (x["legend"],x["kind"],x["candidate_sha256"],
                   x["candidate_path"])
            if (key not in expected or key in complete or key in actual
                or x["original_sha256"] != sha(originals[x["legend"]])
                or x["native_status"] != "complete" or x["completed"] is not True
                or x["engine_winner"] not in (1,2) or x["engine_error"]):
                raise RuntimeError("Bad/missing native game receipt")
            actual.add(key)
            complete[key] = x
        if actual != expected:
            raise RuntimeError("Missing or duplicated registration variant")
    if len(sha_set) != 1 or len(complete) != 403:
        raise RuntimeError("Full 580 candidate set needs identical pinned engine")
    bykind = collections.Counter(x["kind"] for x in accepted["all_records"])
    bykind.update(x["kind"] for x in complete.values())
    if bykind != manifest["families"]:
        raise RuntimeError("Incorrect family accounting in 580 game completions")
    packet = {
        "status": "ALL_580_REGISTERED_STRUCTURAL_NATIVE_GAMES_PASS",
        "legends": 58, "structural_variants": 580,
        "previously_accepted_first_family_games": 177,
        "new_native_games_completed": 403, "all_native_games_completed": 580,
        "native_game_failures": 0, "native_engine_sha256": next(iter(sha_set)),
        "source_manifest_sha256": source_hash,
        "families": dict(bykind),
        "native_compatibility_only": True, "strength_assessed": False,
        "mechanics_completeness_proven": False,
        "original_decks_modified": False,
        "verified_new_game_receipts": list(complete.values())
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(packet, indent=2), encoding="utf-8")
    print("FULL_580_REGISTERED_STRUCTURAL_NATIVE_PASS",
          {k:v for k,v in packet.items() if k!="verified_new_game_receipts"},
          flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--variants", type=pathlib.Path, required=True)
    p.add_argument("--selected", type=pathlib.Path, required=True)
    p.add_argument("--registry", type=pathlib.Path, required=True)
    p.add_argument("--engine", type=pathlib.Path)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.add_argument("--input", type=pathlib.Path)
    p.add_argument("--first", type=pathlib.Path)
    p.add_argument("--aggregate", action="store_true")
    p.add_argument("--shards", type=int, default=29)
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--seed", type=int, default=202611252130)
    p.add_argument("--timeout", type=float, default=120)
    a = p.parse_args()
    if (not 1 <= a.shards <= 58 or not 0 <= a.shard < a.shards
        or a.timeout <= 0):
        p.error("Invalid native source or shard allocation")
    if a.aggregate:
        if not a.first or not a.input:
            p.error("--aggregate requires --first and --input")
        aggregate(a)
    else:
        if not a.engine:
            p.error("Playing games requires --engine")
        run(a)


if __name__ == "__main__":
    main()
