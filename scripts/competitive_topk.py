#!/usr/bin/env python3
"""Independent stronger-agent BO3 league for a selected top-K subset.

Source is the immutable 58-Legend candidate roster plus prior exploratory
rankings, not generated/picked from this validation's own outcomes.
All pairings use both seating orders and reproducible independent seeds.
Tournament sideboarding is NOT modeled and none of these ranks prove a
Worlds-winning deck.
"""
from __future__ import annotations

import argparse
import collections
import concurrent.futures
import csv
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from round_robin_58 import load_decks, pair_schedule, sha, wilson
from evaluate_radiance_ismcts import engine_bo3


def select_topk(selected: pathlib.Path, ranked: pathlib.Path, top: int):
    decks, _ = load_decks(selected)
    rows = json.loads(ranked.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or len(rows) != 58:
        raise RuntimeError("Expected complete source rankings of 58 Legends")
    if len(set(r["legend"] for r in rows)) != 58:
        raise RuntimeError("Duplicate source ranked legend")
    if set(r["legend"] for r in rows) != set(decks):
        raise RuntimeError("Ranked Legend roster differs from pinned candidate source")
    if [r.get("rank_exploratory") for r in rows] != list(range(1, 59)):
        raise RuntimeError("Rank ordering does not match exploratory source")
    for r in rows:
        if sha(decks[r["legend"]]) != r["deck_sha256"]:
            raise RuntimeError("Rankings and selected decks do not share SHA provenance")
    if top < 2 or top > 58:
        raise ValueError("top must be between 2 and 58")
    included = rows[:top]
    return {r["legend"]: decks[r["legend"]] for r in included}, included


def expected_schedule(decks: dict, reps: int, seed: int):
    return {(x["a"], x["b"], x["seat"], x["repetition"]):
            x["seed"] for x in pair_schedule(decks, 0, 1, reps, seed)}


def play_shard(args):
    args.output.mkdir(parents=True, exist_ok=True)
    decks, top_rows = select_topk(args.selected, args.ranked, args.top)
    jobs = list(pair_schedule(decks, args.shard, args.shards,
                              args.repetitions, args.seed))
    exe = args.engine.resolve()
    if not exe.is_file():
        raise RuntimeError("Missing compiled engine binary")
    env = os.environ.copy()

    def one(item):
        a = decks[item["a"]]
        b = decks[item["b"]]
        played = engine_bo3(exe, a, b, item["seat"], item["seed"],
                            args.agent, args.timeout, env)
        completed = played["status"] == "complete" and played["winner"] in (1, 2)
        return {
            **item, "complete": completed, "status": played["status"],
            "winner": (("a" if played["winner"] == item["seat"] + 1 else "b")
                       if completed else None),
            "error": played.get("error", ""),
            "games": played.get("games", []),
            "a_sha256": sha(a), "b_sha256": sha(b),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        output = list(pool.map(one, jobs))
    output.sort(key=lambda r: (r["a"], r["b"], r["seat"], r["repetition"]))
    meta = {
        "top": args.top, "selected_legends": [r["legend"] for r in top_rows],
        "selected_source_sha256": sha(args.ranked), "engine_sha256": sha(exe),
        "shard": args.shard, "shards": args.shards,
        "repetitions": args.repetitions, "seed": args.seed,
        "agent": args.agent, "expected": len(jobs),
        "complete": sum(bool(r["complete"]) for r in output),
        "sideboard_swaps": False, "results": output,
    }
    (args.output / "shard.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    print("TOPK_SHARD_FINAL", args.shard, meta["complete"], "/", meta["expected"],
          flush=True)
    if meta["complete"] != meta["expected"]:
        raise RuntimeError("Incomplete game outcomes; fail closed")


def aggregate(args):
    args.output.mkdir(parents=True, exist_ok=True)
    decks, top_rows = select_topk(args.selected, args.ranked, args.top)
    expected = expected_schedule(decks, args.repetitions, args.seed)
    all_results = []
    engine_hashes = set()
    for shard in range(args.shards):
        path = args.input / f"competitive-topk-shard-{shard}" / "shard.json"
        packet = json.loads(path.read_text())
        if any((
            packet["top"] != args.top, packet["shard"] != shard,
            packet["shards"] != args.shards,
            packet["repetitions"] != args.repetitions,
            packet["seed"] != args.seed,
            packet["agent"] != args.agent,
            packet["expected"] != packet["complete"],
            packet["selected_source_sha256"] != sha(args.ranked),
            packet["selected_legends"] != [r["legend"] for r in top_rows],
            packet["sideboard_swaps"] is not False,
        )):
            raise RuntimeError("Shard metadata or results cannot be trusted: " + str(path))
        engine_hashes.add(packet["engine_sha256"])
        all_results.extend(packet["results"])
    if len(engine_hashes) != 1:
        raise RuntimeError("Inconsistent engine binary hashes across shards")
    keylist = [(r["a"], r["b"], r["seat"], r["repetition"]) for r in all_results]
    if len(keylist) != len(expected) or set(keylist) != set(expected):
        raise RuntimeError("Missing or repeated matchups; no ranking allowed")
    for row in all_results:
        key = (row["a"], row["b"], row["seat"], row["repetition"])
        if (not row["complete"] or row["status"] != "complete" or
            row["winner"] not in ("a", "b") or row["seed"] != expected[key] or
            row["a_sha256"] != sha(decks[row["a"]]) or
            row["b_sha256"] != sha(decks[row["b"]])):
            raise RuntimeError("Incomplete / corrupted engine evidence")
    per = collections.defaultdict(lambda: {"wins": 0, "played": 0})
    for row in all_results:
        for own, won in ((row["a"], row["winner"] == "a"),
                         (row["b"], row["winner"] == "b")):
            per[own]["played"] += 1
            per[own]["wins"] += int(won)
    standings = []
    expected_per_legend = (args.top - 1) * 2 * args.repetitions
    for name in decks:
        w, n = per[name]["wins"], per[name]["played"]
        if n != expected_per_legend:
            raise RuntimeError("Incorrect sample size for " + name)
        low, high = wilson(w, n)
        standings.append({"legend": name, "wins": w, "series": n,
                          "win_rate": round(w / n, 6),
                          "wilson95_low": low, "wilson95_high": high,
                          "deck_sha256": sha(decks[name])})
    standings.sort(key=lambda row: (-row["win_rate"], row["legend"]))
    for i, row in enumerate(standings, start=1):
        row["topk_rank"] = i
    with (args.output / "ranked.csv").open("w", newline="", encoding="utf-8") as fp:
        columns = ["topk_rank", "legend", "wins", "series", "win_rate",
                   "wilson95_low", "wilson95_high", "deck_sha256"]
        writer = csv.DictWriter(fp, fieldnames=columns)
        writer.writeheader()
        writer.writerows(standings)
    all_results.sort(key=lambda row:
                     (row["a"], row["b"], row["seat"], row["repetition"]))
    (args.output / "matches.json").write_text(
        json.dumps(all_results, indent=2), encoding="utf-8"
    )
    (args.output / "standings.json").write_text(
        json.dumps(standings, indent=2), encoding="utf-8"
    )
    metadata = {
        "status": "EXPLORATORY_FIXED_DECK_TOPK_COMPLETE",
        "top": args.top, "source_rankings_sha256": sha(args.ranked),
        "source_selected_roster_count": 58,
        "unordered_pairs": args.top * (args.top - 1) // 2,
        "total_completed_bo3_series": len(all_results),
        "expected_completed_bo3_series": len(expected),
        "repetitions_per_seat": args.repetitions,
        "mirrored_seats": True, "engine_sha256": next(iter(engine_hashes)),
        "agent": args.agent, "sideboarding": False,
        "global_optimality": False, "worlds_prediction": False,
        "limitations": [
            "Seating and stochastic simulations are sampled, not exhaustive",
            "Top-K selection inherits weak-agent baseline rankings",
            "No between-game sideboard policy, metagame weighting or rules certification",
            "Wilson intervals assume independent series and may understate uncertainty",
        ],
    }
    (args.output / "summary.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    print("TOPK_FINAL", json.dumps(metadata), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--selected", type=pathlib.Path, required=True)
    p.add_argument("--ranked", type=pathlib.Path, required=True)
    p.add_argument("--engine", type=pathlib.Path, default=pathlib.Path("engine_build/riftbound"))
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.add_argument("--input", type=pathlib.Path)
    p.add_argument("--aggregate", action="store_true")
    p.add_argument("--top", type=int, default=10)
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--shards", type=int, default=10)
    p.add_argument("--repetitions", type=int, default=2)
    p.add_argument("--workers", type=int, default=2)
    p.add_argument("--timeout", type=float, default=180)
    p.add_argument("--agent", default="ismcts:sims=128")
    p.add_argument("--seed", type=int, default=202611240001)
    args = p.parse_args()
    if not 2 <= args.top <= 58 or not 1 <= args.shards <= 58 or not 0 <= args.shard < args.shards:
        p.error("Invalid top or shard settings")
    if not 1 <= args.repetitions <= 30 or not 1 <= args.workers <= 16 or args.timeout <= 0:
        p.error("Invalid simulation budget")
    if args.aggregate:
        if args.input is None:
            p.error("--aggregate requires --input")
        aggregate(args)
    else:
        play_shard(args)


if __name__ == "__main__":
    main()
