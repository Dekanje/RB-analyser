#!/usr/bin/env python3
"""Fail-closed aggregation of 58 AlphaRune ISMCTS optimization shards.

A card swap is a provisional proposal only if paired training and disjoint
holdout games passed. Full Radiance coverage and statistically certified
optimal decklists are NOT claimed.
"""
import argparse
import hashlib
import json
import pathlib
import shutil
from collections import Counter

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main(args):
    roots = sorted(p for p in args.source.glob("optimizer-shard-*") if p.is_dir())
    if len(roots) != args.shards:
        raise RuntimeError(f"Expected {args.shards} shard artifacts, got {len(roots)}")
    dest = args.output / "selected_decks"
    dest.mkdir(parents=True, exist_ok=True)
    seen = {}
    row_count = 0
    for root in roots:
        results_file = root / "results.json"
        summary_file = root / "summary.json"
        if not results_file.exists() or not summary_file.exists():
            raise RuntimeError("Shard missing provenance: " + str(root))
        results = json.loads(results_file.read_text(encoding="utf-8"))
        summary = json.loads(summary_file.read_text(encoding="utf-8"))
        if summary["failed"] or summary["legends_tested"] != len(results):
            raise RuntimeError("Incomplete optimizer results: " + str(root))
        if summary["agent"] != args.agent:
            raise RuntimeError("Inconsistent optimizer policy: " + str(root))
        byfile = {p.name: p for p in (root / "selected_decks").glob("*.txt")}
        if len(byfile) != len(results):
            raise RuntimeError("Missing selected deck file: " + str(root))
        for row in results:
            name = row["legend"]
            if name in seen:
                raise RuntimeError("Repeated legend: " + name)
            if row["agent"] != args.agent:
                raise RuntimeError("Unexpected per-legend search agent")
            matches = [p for p in byfile.values()
                       if p.stem == row.get("filename", "").replace(".txt", "")]
            # Match on sha instead of assuming a filename's legend text.
            matching = [p for p in byfile.values()
                        if sha(p) == row["effective_sha256"]]
            if not matching:
                raise RuntimeError("Selected SHA missing from output: " + name)
            filepath = matching[0]
            if (dest / filepath.name).exists():
                raise RuntimeError("Duplicate deck filename " + filepath.name)
            shutil.copyfile(filepath, dest / filepath.name)
            seen[name] = {k: row[k] for k in ("legend","original_sha256",
                "effective_sha256","selected","selected_swaps","agent")}
            row_count += 1
    if row_count != 58 or len(list(dest.glob("*.txt"))) != 58:
        raise RuntimeError(f"Incomplete full roster: {row_count}")
    manifest = sorted(seen.values(), key=lambda r: r["legend"])
    out = {"schema": 1,
           "status": "EXPERIMENTAL_COMPILED_POOL_HOLDOUT_GATED_NOT_FULL_RADIANCE",
           "agent": args.agent, "expected_legends": 58,
           "observed_legends": len(manifest),
           "changed_decks": sum(r["selected"] for r in manifest),
           "unchanged_decks": sum(not r["selected"] for r in manifest),
           "full_radiance_supported": False,
           "all_decks_globally_optimized": False,
           "independent_card_mechanics_verified": False,
           "limitations": "Compiler-defined card pool only; 142 Radiance names absent in previous audit; heuristic proposals and small-sample holdout comparisons, no proof of globally optimal 58 decks",
           "decks": manifest}
    (args.output / "optimization_manifest.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print("OPTIMIZATION_58_AGGREGATE", json.dumps(
        {k: v for k, v in out.items() if k != "decks"}), flush=True)
    return 0

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--source", type=pathlib.Path, required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.add_argument("--shards", type=int, default=16)
    p.add_argument("--agent", default="ismcts:sims=48")
    raise SystemExit(main(p.parse_args()))
