#!/usr/bin/env python3
"""Validate all 58 unchanged original decks against the actual compiled engine.

This checks deck legality and completion of deterministic real engine games,
not correctness of every card's ability and not tournament sideboarding.
"""
import argparse
import hashlib
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_actual_games import decode, gametest, header

def run(engine, repeats, timeout, output):
    original = decode()
    decks = {header(p): p for p in original}
    if len(decks) != 58:
        raise RuntimeError(f"Expected 58 unique legends, found {len(decks)}")
    anchor = "Kennen, Heart of the Tempest"
    if anchor not in decks:
        raise RuntimeError("Missing unchanged Kennen anchor")
    records = []
    for idx, (name, path) in enumerate(sorted(decks.items())):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        for iteration in range(repeats):
            # Pair both seat orders so an engine failure cannot be hidden by seat.
            a, b = (path, decks[anchor]) if iteration % 2 == 0 else (decks[anchor], path)
            seed = 20261122000 + idx * 100 + iteration
            start = time.monotonic()
            result = gametest(engine, a, b, seed, timeout, "random")
            record = {
                "legend": name, "original_filename": path.name,
                "original_sha256": digest, "seat": 1 if iteration % 2 == 0 else 2,
                "seed": seed, "status": result["status"], "winner": result["winner"],
                "elapsed_sec": round(time.monotonic() - start, 3),
                "stderr_tail": result["stderr_tail"][-700:],
            }
            print(f"VALIDATE {idx + 1}/58 ({iteration + 1}/{repeats}) "
                  f"{name}: {result['status']}", flush=True)
            records.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    summary = {
        "schema": 1, "mode": "original_deck_compatibility_NOT_rules_certification",
        "deck_count": 58, "repetitions": repeats,
        "games": len(records),
        "complete": sum(r["status"] == "complete" for r in records),
        "failed": sum(r["status"] != "complete" for r in records),
        "records": records,
    }
    output.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print("ORIGINAL_58_VALIDATION", {k:v for k,v in summary.items() if k != "records"})
    print("No substitutions, no synthetic wins, no sideboard swaps.", flush=True)
    return 0 if summary["failed"] == 0 else 1

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--engine", default="alpharune/build/riftbound")
    p.add_argument("--repetitions", type=int, default=2)
    p.add_argument("--seconds", type=int, default=60)
    p.add_argument("--output", default="results/all_58_engine_validation.json")
    args = p.parse_args()
    if not 1 <= args.repetitions <= 20 or args.seconds < 1:
        p.error("repetitions 1-20 and seconds >=1 required")
    sys.exit(run(ROOT / args.engine, args.repetitions, args.seconds, ROOT / args.output))
