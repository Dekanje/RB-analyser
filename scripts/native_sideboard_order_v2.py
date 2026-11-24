#!/usr/bin/env python3
"""Controlled Game 1 native replay; no deck fitness or adoption."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
from sideboard_order_v2 import digest, require_ordered, SCHEMA

ENGINE = "e49c0e4d97a86805b9d911175b686c53ff348736ee4406c50941fa0d7e88db6a"
REGISTRY = "d8102dd0930f466ce16c917035aff15eb21e347879800b08fa334b677f198b89"
SEEDS = (2026112401, 2026112402)
AGENT = "ismcts:sims=24"


def run_game(engine, one, two, seed):
    env = os.environ.copy()
    env.pop("RIFTBOUND_FORCE_STARTING_PLAYER", None)
    p = subprocess.run([str(engine.resolve()), "--deck1", str(one.resolve()),
        "--deck2", str(two.resolve()), "--agent1", AGENT, "--agent2", AGENT,
        "--game-mode", "match", "--seed", str(seed), "--web", "off",
        "--render-html", "off", "--trace"], env=env, capture_output=True,
        text=True, timeout=180)
    terminal = re.findall(r"^Game over: winner=([12]) \| reason=(.+) \| turns=(\d+)$",
                          p.stdout, re.M)
    trace = [line.strip() for line in p.stdout.splitlines()
             if line.strip().startswith("[TRC] ")]
    if (p.returncode or len(terminal) != 1 or not trace
            or not any("DRAW_HAND:" in line for line in trace)
            or not any("INTENT:" in line for line in trace)
            or "TOURNAMENT_FORCED_STARTING_PLAYER=" in p.stdout):
        raise RuntimeError("native trace/receipt failed, exit " + str(p.returncode)
                           + "; stderr: " + p.stderr[-500:])
    return {"winner": int(terminal[0][0]), "reason": terminal[0][1],
            "turns": int(terminal[0][2]), "trace_lines": len(trace),
            "trace_sha256": digest("\n".join(trace).encode())}


def execute(a):
    if digest(a.engine.read_bytes()) != ENGINE or digest(a.registry.read_bytes()) != REGISTRY:
        raise ValueError("unexpected native engine or registry")
    manifest = json.loads((a.corrected / "manifest_v2.json").read_text())
    if manifest["schema"] != SCHEMA or len(manifest["records"]) != 174:
        raise ValueError("wrong corrected population")
    records = sorted(manifest["records"], key=lambda r: r["historical_path"])
    # Fixed deterministic selection by input-order class; no fitness used.
    samples = [next(r for r in records if len(r["reordered_sections"]) == n)
               for n in (0, 2)]
    result = {"status": "IN_PROGRESS", "engine_sha256": ENGINE,
              "registry_sha256": REGISTRY, "agent": AGENT, "seeds": list(SEEDS),
              "manifest_sha256": digest((a.corrected / "manifest_v2.json").read_bytes()),
              "cases": [], "deck_adoption": 0}
    a.output.parent.mkdir(parents=True, exist_ok=True)
    if a.output.exists():
        raise ValueError("refusing to overwrite native receipt")
    def save():
        a.output.write_text(json.dumps(result, indent=2) + "\n")
    save()
    try:
        for row in samples:
            base = a.selected / row["original"]
            old = a.structural / row["historical_path"]
            fixed = a.corrected / row["corrected_path"]
            for p, key in ((base, "original_sha256"), (old, "historical_sha256"),
                           (fixed, "corrected_sha256")):
                if digest(p.read_bytes()) != row[key]:
                    raise ValueError("input hash changed")
            require_ordered(base.read_bytes(), fixed.read_bytes())
            opponent = next(p for p in sorted(a.selected.glob("*.txt")) if p != base)
            for seed in SEEDS:
                for seat in (1, 2):
                    receipts = {}
                    for label, path in (("baseline", base), ("repeat", base),
                                        ("corrected", fixed), ("historical", old)):
                        one, two = (path, opponent) if seat == 1 else (opponent, path)
                        receipts[label] = run_game(a.engine, one, two, seed)
                    case = {"candidate": row["corrected_sha256"],
                            "original": row["original_sha256"],
                            "historical": row["historical_sha256"],
                            "reordered_sections": row["reordered_sections"],
                            "opponent": digest(opponent.read_bytes()),
                            "seed": seed, "seat": seat, "receipts": receipts}
                    result["cases"].append(case)
                    save()
                    if not receipts["baseline"] == receipts["repeat"] == receipts["corrected"]:
                        raise RuntimeError("ordered-equivalent native trace mismatch")
                    if not row["reordered_sections"] and receipts["historical"] != receipts["baseline"]:
                        raise RuntimeError("unchanged-order control mismatch")
        result["status"] = "PASS_ORDERED_NATIVE_REPLAY"
        result["native_games"] = len(result["cases"]) * 4
        save()
    except Exception as exc:
        result["status"] = "FAILED"
        result["error"] = str(exc)
        save()
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("engine", "registry", "selected", "structural", "corrected", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    execute(p.parse_args())
