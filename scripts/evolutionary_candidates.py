#!/usr/bin/env python3
"""Broad, reproducible, LEGALITY-GATED evolutionary deck candidate generation.

Generate independent 3-8+ slot changes for any or all of the 58 Legends.
Generate only proposed lists, never assert they are stronger. The unchanged
Champion/Runes/Battlefields/Sideboard are held constant for this initial pass.
Actual AlphaRune simulation and printed-rule legality gate must follow.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import random
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from optimize_58 import (
    BAN_KEYS, card_score, effective_domains, is_unique, key, parse_deck,
    registry, render_deck, stable_seed,
)
from round_robin_58 import load_decks, sha


def playable_pool(byname: dict, domains: set) -> list[dict]:
    """Compiled non-banned non-signature non-token cards in allowed domains."""
    usable = []
    for c in byname.values():
        kind = (c.get("card_type") or "").lower()
        supertype = (c.get("super_type") or "").lower()
        if kind not in ("unit", "spell", "gear"):
            continue
        if c.get("banned") or key(c["name"]) in BAN_KEYS:
            continue
        if "signature" in supertype or "token" in supertype:
            continue
        if set(c.get("domains") or ()) - domains:
            continue
        usable.append(c)
    return usable


def validate_main(
    original_main: collections.Counter,
    candidate_main: collections.Counter,
    side: collections.Counter,
    byname: dict,
    domains: set,
) -> None:
    if sum(original_main.values()) != 39 or sum(candidate_main.values()) != 39:
        raise ValueError("Invalid main-deck size")
    for name, count in candidate_main.items():
        if count <= 0 or name not in byname:
            raise ValueError("Uncompiled card or negative count: " + name)
        c = byname[name]
        if c.get("banned") or key(name) in BAN_KEYS:
            raise ValueError("Candidate includes banned card: " + name)
        if set(c.get("domains") or ()) - domains:
            raise ValueError("Candidate includes off-domain card: " + name)
        if c["card_type"] not in ("unit", "gear", "spell"):
            raise ValueError("Wrong main-deck card type: " + name)
        if "token" in (c.get("super_type") or "").lower():
            raise ValueError("Token in main deck: " + name)
        max_copies = 1 if is_unique(c) else 3
        if count + side.get(name, 0) > max_copies:
            raise ValueError("Copy limit exceeded: " + name)
        if (c.get("super_type") or "").lower() == "signature":
            if count != original_main.get(name, 0):
                raise ValueError("Locked signature quantity changed: " + name)
    for name, count in original_main.items():
        c = byname.get(name)
        if c and (c.get("super_type") or "").lower() == "signature":
            if candidate_main.get(name, 0) != count:
                raise ValueError("Removed required signature card")


def change_one(
    counts: collections.Counter,
    originals: collections.Counter,
    side: collections.Counter,
    byname: dict,
    pool: list[dict],
    rng: random.Random,
    weighted_popularity: collections.Counter,
    domains: set,
    previously_added: set[str],
    previously_removed: set[str],
) -> tuple[str, str] | None:
    removable = [
        name for name, n in counts.items()
        if n > 0 and name in byname and name not in previously_added and
        "signature" not in (byname[name].get("super_type") or "").lower()
    ]
    if not removable:
        return None
    old = rng.choice(removable)
    old_card = byname[old]
    old_tags = set(old_card.get("tags") or ())
    old_energy = old_card.get("energy_cost") or 0
    old_power = old_card.get("power_cost") or 0
    mode = rng.randrange(5)
    candidates = []
    for c in pool:
        new = c["name"]
        if new == old or new in previously_removed:
            continue
        cap = 1 if is_unique(c) else 3
        if counts.get(new, 0) + side.get(new, 0) >= cap:
            continue
        new_energy = c.get("energy_cost") or 0
        new_power = c.get("power_cost") or 0
        if mode <= 1:
            # Curve-preserving swaps; allow both unit/spell/gear diversity.
            if abs(new_energy - old_energy) > 2 or abs(new_power - old_power) > 1:
                continue
            if mode == 0 and c["card_type"] != old_card["card_type"]:
                continue
        if mode == 2:
            # Archetype rebuilding by shared tags / tribe.
            if not old_tags.intersection(c.get("tags") or ()):
                continue
        if mode == 3:
            # Explore substantial curve changes but maintain overall deck budget.
            if abs(new_energy - old_energy) > 4:
                continue
        candidates.append(c)
    if not candidates:
        return None
    if mode == 4:
        # Unbiased legal exploration; no heuristic win-rate claims.
        new = rng.choice(candidates)["name"]
    else:
        # Heuristic is only a proposal ordering, not a simulation result.
        ranked = sorted(
            candidates, key=lambda c: -card_score(c, weighted_popularity, old_tags)
        )
        head = ranked[:min(len(ranked), 24)]
        new = rng.choice(head)["name"]
    counts[old] -= 1
    counts[new] += 1
    if counts[old] == 0:
        del counts[old]
    validate_main(originals, counts, side, byname, domains)
    return old, new


def generate_candidate(
    original: collections.Counter,
    side: collections.Counter,
    byname: dict,
    domains: set,
    pool: list[dict],
    seed: int,
    min_swaps: int,
    max_swaps: int,
    popularity: collections.Counter,
) -> tuple[collections.Counter, list[dict]] | None:
    rng = random.Random(seed)
    count = rng.randint(min_swaps, max_swaps)
    current = original.copy()
    changes = []
    previously_added = set()
    previously_removed = set()
    for _ in range(count):
        # Limit retry inflation, but preserve actual legal mutations.
        result = None
        for __ in range(20):
            result = change_one(
                current, original, side, byname, pool, rng,
                popularity, domains, previously_added, previously_removed,
            )
            if result is not None:
                break
        if result is None:
            return None
        changes.append({"remove": result[0], "add": result[1]})
        previously_removed.add(result[0])
        previously_added.add(result[1])
    validate_main(original, current, side, byname, domains)
    if current == original:
        return None
    card_distance = sum(
        max(0, original.get(n,0) - current.get(n,0))
        for n in original
    )
    if card_distance < min_swaps:
        # Reversions do not qualify as broad search.
        return None
    return current, changes


def generate_for_legend(
    name: str,
    deck: pathlib.Path,
    byname: dict,
    popularity: collections.Counter,
    output: pathlib.Path,
    desired: int,
    min_swaps: int,
    max_swaps: int,
    seed: int,
    max_attempts: int,
) -> dict:
    source_text, main, side = parse_deck(deck)
    domains = effective_domains(name, byname)
    pool = playable_pool(byname, domains)
    if not pool:
        raise RuntimeError("Empty legal card pool for: " + name)
    validate_main(main, main.copy(), side, byname, domains)
    slug = deck.stem
    dirpath = output / slug
    dirpath.mkdir(parents=True, exist_ok=True)
    seen = {sha(deck)}
    output_rows = []
    for attempt in range(max_attempts):
        if len(output_rows) >= desired:
            break
        proposal = generate_candidate(
            main, side, byname, domains, pool,
            stable_seed(seed, name, attempt, "EVOLUTIONARY_DIVERSITY_V1"),
            min_swaps, max_swaps, popularity,
        )
        if proposal is None:
            continue
        changed, sequence = proposal
        rendered = render_deck(source_text, changed)
        blob = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
        if blob in seen:
            continue
        seen.add(blob)
        distance = sum(max(0, main.get(n,0) - changed.get(n,0))
                       for n in main)
        path = dirpath / f"candidate_{len(output_rows):04d}.txt"
        path.write_text(rendered, encoding="utf-8")
        output_rows.append({
            "path": str(path.relative_to(output)),
            "sha256": blob, "changed_main_slots": distance,
            "mutation_steps": sequence, "engine_simulated": False,
            "status": "UNTESTED_STRUCTURAL_CANDIDATE",
        })
    return {
        "legend": name, "source_sha256": sha(deck),
        "domains": sorted(domains), "pool_size": len(pool),
        "requested": desired, "generated": len(output_rows),
        "attempts_budget": max_attempts,
        "min_swaps": min_swaps, "max_swaps": max_swaps,
        "candidates": output_rows,
        "sideboarding_optimized": False,
        "worlds_legal_certified": False,
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected", type=pathlib.Path, required=True)
    p.add_argument("--registry", type=pathlib.Path, required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    p.add_argument("--legend", action="append", default=[],
                   help="Exact Legend name; may be repeated. Default: all 58.")
    p.add_argument("--desired", type=int, default=40)
    p.add_argument("--min-swaps", type=int, default=3)
    p.add_argument("--max-swaps", type=int, default=8)
    p.add_argument("--max-attempts", type=int, default=1000)
    p.add_argument("--seed", type=int, default=202611240300)
    args = p.parse_args()
    if (not 1 <= args.desired <= 1000 or
        not 1 <= args.min_swaps <= args.max_swaps <= 20 or
        not args.desired <= args.max_attempts <= 100000):
        p.error("Invalid population budget")
    decks, trials = load_decks(args.selected)
    byname = registry(args.registry)
    if args.legend:
        unknown = set(args.legend) - set(decks)
        if unknown:
            p.error("Legend name not found: " + str(sorted(unknown)))
        names = sorted(set(args.legend))
    else:
        names = sorted(decks)
    pop = collections.Counter()
    for deck in decks.values():
        _, main, _ = parse_deck(deck)
        pop.update(main)
    args.output.mkdir(parents=True, exist_ok=True)
    report = []
    for name in names:
        record = generate_for_legend(
            name, decks[name], byname, pop, args.output,
            args.desired, args.min_swaps, args.max_swaps,
            args.seed, args.max_attempts,
        )
        if record["generated"] < args.desired:
            raise RuntimeError("Could not build requested unique candidates: " + name)
        report.append(record)
        print("CANDIDATE_POPULATION",
              name, record["generated"], "/", record["requested"], flush=True)
    manifest = {
        "schema": 1, "source_roster": len(decks),
        "legend_count": len(names), "candidate_count":
            sum(r["generated"] for r in report),
        "registry_sha256": sha(args.registry),
        "seed": args.seed, "status": "CANDIDATES_ONLY_NO_WIN_RATE_CLAIM",
        "mutation_range": [args.min_swaps,args.max_swaps],
        "locked_sections": ["Legend","Champion","Battlefields","Runes","Sideboard"],
        "requires_engine_card_legality_check": True,
        "requires_actual_ismcts_bo3": True,
        "records": report,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print("EVOLUTIONARY_CANDIDATES_COMPLETE",json.dumps({
        k:v for k,v in manifest.items() if k != "records"
    }),flush=True)


if __name__ == "__main__":
    main()
