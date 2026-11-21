#!/usr/bin/env python3
"""Experimental post-sideboard BO3 with real AlphaRune ISMCTS games.

Game 1 always uses the registered 58-deck roster. Games 2/3 can use a
reproducible, conservative ONE-card main/sideboard exchange. This is a
mechanical proof of post-board play, NOT strategic sideboard optimization,
card-rule certification or a tournament-equivalent match simulation.
"""
import argparse
import collections
import hashlib
import itertools
import json
import pathlib
import re
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from run_actual_games import decode, gametest
from legal_candidate import make_legal_candidate
from run_bo3_pairings import atomic_write, validate_manifest

FORMAT = "experimental_one_swap_postboard_BO3_NOT_TOURNAMENT_CERTIFIED"

def parse_sections(source):
    lines = source.read_text(encoding="utf-8").splitlines()
    for name in ("MainDeck:", "Battlefields:", "Sideboard:"):
        if lines.count(name) != 1:
            raise ValueError("Missing or duplicate deck section " + name)
    a, b, c = (lines.index(x) for x in ("MainDeck:", "Battlefields:", "Sideboard:"))
    if not (a < b < c):
        raise ValueError("Deck sections are out of order")
    def count(start, end):
        cards = collections.Counter()
        for line in lines[start:end]:
            if not line.strip():
                continue
            match = re.fullmatch(r"\s*(\d+) (.+)", line)
            if not match:
                raise ValueError("Malformed card row: " + line)
            cards[match.group(2)] += int(match.group(1))
        return cards
    main = count(a + 1, b)
    side = count(c + 1, len(lines))
    if sum(main.values()) != 39:
        raise ValueError("Expected 39 main-deck cards besides chosen champion")
    if sum(side.values()) > 10:
        raise ValueError("Sideboard exceeds 10 cards")
    if any(n < 1 for n in list(main.values()) + list(side.values())):
        raise ValueError("Nonpositive card quantity")
    return lines, main, side

def render_sections(lines, main, side):
    a, b, c = (lines.index(x) for x in ("MainDeck:", "Battlefields:", "Sideboard:"))
    def rows(cards):
        return [f"{cards[name]} {name}" for name in sorted(cards) if cards[name] > 0]
    result = (lines[:a+1] + rows(main) + [""] + lines[b:c+1]
              + rows(side) + [""])
    return "\n".join(result).rstrip() + "\n"

def one_swap(source, opponent, match_seed, side_id, game_no, directory):
    """Registered deck remains immutable; generate a per-game sideboard state.

    Conservatively exclude comma-named characters to avoid swapping Chosen
    Champions or Signature characters without the required character rules.
    This deliberately makes NO claim to choose good counter-cards.
    """
    if game_no == 1:
        return source, []
    lines, main, side = parse_sections(source)
    original_union = main + side
    incoming = sorted(k for k, n in side.items() if n > 0 and "," not in k)
    outgoing = sorted(k for k, n in main.items() if n > 0 and "," not in k)
    possibilities = [(old, new) for old in outgoing for new in incoming if old != new]
    if not possibilities:
        return source, []
    identity = f"{source.name}|{opponent}|{match_seed}|{side_id}|{game_no}".encode()
    pick = int.from_bytes(hashlib.sha256(identity).digest()[:8], "big") % len(possibilities)
    old, new = possibilities[pick]
    main = main.copy(); side = side.copy()
    main[old] -= 1; main[new] += 1
    side[new] -= 1; side[old] += 1
    for cards in (main, side):
        for name in list(cards):
            if cards[name] == 0:
                del cards[name]
    if (sum(main.values()) != 39 or sum(side.values()) > 10
            or main + side != original_union):
        raise AssertionError("Illegal main/side size or modified registered card pool")
    directory.mkdir(parents=True, exist_ok=True)
    body = render_sections(lines, main, side)
    digest = hashlib.sha256(body.encode()).hexdigest()
    target = directory / (digest + ".txt")
    if not target.exists():
        target.write_text(body, encoding="utf-8")
    return target, [{"out": old, "in": new}]

def series(exe, decks, legend_a, legend_b, pair_index, iteration, seconds, agent, cache):
    wins = {"A": 0, "B": 0}
    games = []
    seed_root = 202612480000 + pair_index * 1000 + iteration * 10
    for number in (1, 2, 3):
        # Alternate seats. Mirrors remain two distinct competitors.
        first_side = "A" if (number - 1 + iteration) % 2 == 0 else "B"
        second_side = "B" if first_side == "A" else "A"
        game_seed = seed_root + number - 1
        a_file, a_swaps = one_swap(decks[legend_a], legend_b, seed_root,
                                   "A", number, cache)
        b_file, b_swaps = one_swap(decks[legend_b], legend_a, seed_root,
                                   "B", number, cache)
        p1 = a_file if first_side == "A" else b_file
        p2 = b_file if first_side == "A" else a_file
        result = gametest(exe, p1, p2, game_seed, seconds, agent)
        board = {
            "A": {"swaps": a_swaps, "deck_sha256": hashlib.sha256(a_file.read_bytes()).hexdigest()},
            "B": {"swaps": b_swaps, "deck_sha256": hashlib.sha256(b_file.read_bytes()).hexdigest()}
        }
        entry = {"number": number, "seed": game_seed,
                 "seat1": legend_a if first_side == "A" else legend_b,
                 "seat2": legend_b if first_side == "A" else legend_a,
                 "status": result["status"], "winner_seat": result["winner"],
                 "returncode": result["returncode"],
                 "stderr_tail": result["stderr_tail"][-900:],
                 "postboard": number > 1, "sideboard": board}
        if result["status"] != "complete" or result["winner"] not in (1, 2):
            games.append(entry)
            return {"legend_a": legend_a, "legend_b": legend_b,
                    "instance": iteration, "status": "incomplete",
                    "reason": "Engine game failed or timed out; no synthetic winner",
                    "games": games}
        winner_side = first_side if result["winner"] == 1 else second_side
        entry["winner_side"] = winner_side
        entry["winner"] = legend_a if winner_side == "A" else legend_b
        games.append(entry)
        wins[winner_side] += 1
        if wins[winner_side] == 2:
            return {"legend_a": legend_a, "legend_b": legend_b,
                    "instance": iteration, "status": "complete",
                    "winner": entry["winner"], "winner_side": winner_side,
                    "score": wins, "mirror": legend_a == legend_b, "games": games}
    return {"legend_a": legend_a, "legend_b": legend_b, "instance": iteration,
            "status": "incomplete", "reason": "Neither competitor reached 2 wins",
            "games": games}

def main(args):
    original = decode()
    decks = make_legal_candidate(original, ROOT / "decks_postboard_source")
    validate_manifest(decks, ROOT / args.validation, True)
    if not 0 <= args.shard < args.shards:
        raise ValueError("Invalid shard")
    pairs = list(itertools.combinations_with_replacement(sorted(decks), 2))
    if len(pairs) != 1711:
        raise RuntimeError("Roster not 58")
    selection = [(i, a, b) for i, (a, b) in enumerate(pairs)
                 if i % args.shards == args.shard]
    output = ROOT / args.output
    cache = output.parent / ("sideboard_decks_" + str(args.shard))
    report = {"schema": 1, "format": FORMAT, "agent": args.agent,
              "sideboarding": "seeded-one-swap, games 2/3 only",
              "source": "54 unchanged original SHA-pinned decks plus four disclosed rules-legal candidates",
              "shard": args.shard, "shards": args.shards,
              "total_pairings": 1711, "shard_pairings": len(selection),
              "series_per_pair": args.series_per_pair,
              "limitations": "Unoptimized deterministic sideboard policy; provisional Radiance coverage; not tournament odds",
              "results": [], "complete": False}
    exe = (ROOT / args.engine).resolve()
    if not exe.exists():
        raise RuntimeError("Compiled engine not found")
    begun = time.monotonic()
    for i, a, b in selection:
        for iteration in range(args.series_per_pair):
            if args.max_seconds and time.monotonic() - begun >= args.max_seconds:
                print("POSTBOARD_BUDGET_REACHED", flush=True)
                report["complete"] = False
                atomic_write(output, report)
                return 1
            row = series(exe, decks, a, b, i, iteration, args.seconds,
                         args.agent, cache)
            report["results"].append(row)
            print(f"POSTBOARD_BO3_PAIR {i+1}/1711 {a} vs {b} "
                  f"instance={iteration+1} {row['status']}", flush=True)
            if len(report["results"]) % 10 == 0:
                atomic_write(output, report)
    report["series_complete"] = sum(r["status"] == "complete" for r in report["results"])
    report["series_incomplete"] = len(report["results"]) - report["series_complete"]
    report["sideboard_swaps"] = sum(
        len(p["swaps"]) for r in report["results"] for g in r["games"]
        for p in g["sideboard"].values())
    report["complete"] = len(report["results"]) == len(selection) * args.series_per_pair
    atomic_write(output, report)
    print("POSTBOARD_BO3_SUMMARY", json.dumps({k: v for k, v in report.items()
                                               if k != "results"}), flush=True)
    return 0 if report["complete"] and report["series_incomplete"] == 0 else 1

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--engine", default="alpharune/build/riftbound")
    p.add_argument("--validation", default="results/all_58_legal_candidate_validation.json")
    p.add_argument("--output", default="results/postboard_shard.json")
    p.add_argument("--shards", type=int, default=128)
    p.add_argument("--shard", type=int, default=0)
    p.add_argument("--series-per-pair", type=int, default=20)
    p.add_argument("--agent", default="ismcts:sims=48")
    p.add_argument("--seconds", type=int, default=100)
    p.add_argument("--max-seconds", type=int, default=3050)
    a = p.parse_args()
    if not (1 <= a.shards <= 256 and 1 <= a.series_per_pair <= 20
            and 1 <= a.seconds <= 600 and a.max_seconds >= 0):
        p.error("Invalid simulation budget")
    sys.exit(main(a))
