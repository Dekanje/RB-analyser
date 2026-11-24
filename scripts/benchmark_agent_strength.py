#!/usr/bin/env python3
"""Paired, mirrored single-game agent-strength benchmark for AlphaRune.

Purpose: test whether a higher ISMCTS budget actually beats a lower one
when BOTH agents pilot exactly the same deck. This isolates playing policy
quality from deck quality. It is NOT a BO3, sideboard, tournament or
Rules-correctness certification. This script fails closed on engine errors.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import pathlib
import re
import subprocess
import sys
import time
from collections import defaultdict


WINNER_RE = re.compile(r"Game over:\s*winner\s*=\s*([012])")


def stable_seed(master: int, deck_name: str, repetition: int) -> int:
    digest = hashlib.sha256(
        f"AGENT_BENCH_V1|{master}|{deck_name}|{repetition}".encode("utf-8")
    ).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF


def game_schedule(decks: list[pathlib.Path], repetitions: int, seed: int):
    """Each chosen deck/seed is played in both agent seating orders."""
    for deck in sorted(decks, key=lambda path: path.name):
        for rep in range(repetitions):
            paired_seed = stable_seed(seed, deck.name, rep)
            for challenger_first in (True, False):
                yield deck, rep, paired_seed, challenger_first


def sha256(path: pathlib.Path) -> str:
    result = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            result.update(chunk)
    return result.hexdigest()


def parse_result(returncode: int, stdout: str, stderr: str) -> dict:
    matches = WINNER_RE.findall(stdout)
    if returncode == 0 and matches and matches[-1] in ("1", "2"):
        return {"status": "complete", "winner_seat": int(matches[-1])}
    detail = stderr[-800:] or stdout[-800:] or f"Exit code {returncode}"
    return {"status": "error", "winner_seat": None, "error": detail}


def play_once(
    engine: pathlib.Path,
    deck: pathlib.Path,
    baseline: str,
    challenger: str,
    challenger_first: bool,
    seed: int,
    timeout: float,
) -> dict:
    agent1 = challenger if challenger_first else baseline
    agent2 = baseline if challenger_first else challenger
    command = [
        str(engine.resolve()), "--deck1", str(deck.resolve()),
        "--deck2", str(deck.resolve()), "--agent1", agent1,
        "--agent2", agent2, "--game-mode", "match", "--seed", str(seed),
        "--web", "off", "--render-html", "off",
    ]
    start = time.monotonic()
    try:
        completed = subprocess.run(
            command, text=True, capture_output=True, timeout=timeout, check=False
        )
        result = parse_result(completed.returncode, completed.stdout, completed.stderr)
    except subprocess.TimeoutExpired:
        result = {"status": "timeout", "winner_seat": None, "error": "Engine timeout"}
    result["seconds"] = round(time.monotonic() - start, 3)
    result["challenger_first"] = challenger_first
    result["seed"] = seed
    result["challenger_win"] = (
        (result["winner_seat"] == (1 if challenger_first else 2))
        if result["status"] == "complete" else None
    )
    return result


def wilson_interval(wins: int, games: int) -> tuple[float | None, float | None]:
    if games == 0:
        return None, None
    z = 1.9599639845
    p = wins / games
    factor = 1 + z * z / games
    center = (p + z * z / (2 * games)) / factor
    half = z * math.sqrt((p * (1 - p) + z * z / (4 * games)) / games) / factor
    return round(max(0, center - half), 4), round(min(1, center + half), 4)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--decks-dir", type=pathlib.Path, required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.add_argument("--baseline-agent", default="ismcts:sims=24")
    p.add_argument("--challenger-agent", default="ismcts:sims=128")
    p.add_argument("--repetitions", type=int, default=1)
    p.add_argument("--max-decks", type=int, default=3)
    p.add_argument("--deck-name", action="append", default=[],
                   help="Exact .txt filename; repeat to choose a representative deck panel")
    p.add_argument("--timeout", type=float, default=240)
    p.add_argument("--seed", type=int, default=20261123)
    args = p.parse_args()
    if args.repetitions < 1 or args.max_decks < 0 or args.timeout <= 0:
        p.error("Expected repetitions>=1, max-decks>=0 and timeout>0")
    if args.baseline_agent == args.challenger_agent:
        p.error("Choose different baseline and challenger agents")
    if not args.engine.is_file():
        p.error(f"Engine not found: {args.engine}")
    if not args.decks_dir.is_dir():
        p.error(f"Deck directory not found: {args.decks_dir}")
    available = {deck.name: deck for deck in args.decks_dir.glob("*.txt")}
    if args.deck_name:
        missing = sorted(set(args.deck_name) - set(available))
        if missing:
            p.error(f"Deck filenames not found: {missing}")
        selected = [available[name] for name in sorted(set(args.deck_name))]
    else:
        selected = sorted(available.values(), key=lambda path: path.name)
    if args.max_decks:
        selected = selected[:args.max_decks]
    if not selected:
        p.error("No input .txt deck files selected")

    by_deck = defaultdict(lambda: {"wins": 0, "completed": 0, "failures": 0})
    games = []
    for deck, rep, seed, challenger_first in game_schedule(
        selected, args.repetitions, args.seed
    ):
        result = play_once(
            args.engine, deck, args.baseline_agent, args.challenger_agent,
            challenger_first, seed, args.timeout
        )
        result.update({"deck_file": deck.name, "deck_sha256": sha256(deck),
                       "repetition": rep})
        games.append(result)
        row = by_deck[deck.name]
        if result["status"] == "complete":
            row["completed"] += 1
            row["wins"] += int(result["challenger_win"])
        else:
            row["failures"] += 1
        print("BENCHMARK_GAME", deck.name, rep,
              "challenger_first" if challenger_first else "challenger_second",
              result["status"], result["challenger_win"], flush=True)

    summaries = []
    for name in sorted(by_deck):
        row = by_deck[name]
        low, high = wilson_interval(row["wins"], row["completed"])
        summaries.append({
            "deck_file": name, **row,
            "win_rate": (row["wins"] / row["completed"] if row["completed"] else None),
            "wilson95_low": low, "wilson95_high": high
        })
    wins = sum(row["wins"] for row in by_deck.values())
    completed = sum(row["completed"] for row in by_deck.values())
    failures = sum(row["failures"] for row in by_deck.values())
    low, high = wilson_interval(wins, completed)
    summary = {
        "purpose": "Agent strength sanity benchmark; NOT deck ranking or BO3",
        "engine_sha256": sha256(args.engine),
        "baseline_agent": args.baseline_agent,
        "challenger_agent": args.challenger_agent,
        "decks_tested": len(selected),
        "repetitions_per_deck": args.repetitions,
        "mirrored_agent_seating": True,
        "identical_deck_on_both_sides": True,
        "completed_games": completed, "failed_games": failures,
        "challenger_wins": wins,
        "challenger_win_rate": wins / completed if completed else None,
        "wilson95_low": low, "wilson95_high": high,
        "conclusion": "INCOMPLETE" if failures else "SAMPLED_ONLY",
        "limitations": [
            "No sideboarding, mulligan expertise certification or tournament BO3",
            "No proof that the engine or card effects match official rules",
            "No claim that increasing search budget guarantees better play",
        ],
    }
    payload = {"summary": summary, "by_deck": summaries, "games": games}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("BENCHMARK_FINAL", json.dumps(summary), flush=True)
    return 2 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
