#!/usr/bin/env python3
"""Sideboard-aware BO3 prototype using the real pinned AlphaRune executable.

Follows Constructed 403.4 for between-game 1-for-1 swaps, including permitted
Chosen Champion replacement from Main Deck/sideboard, and 403.8 restoration
for each NEW match. The engine still approximates the tournament's 407.4
loser-chooses-first rule by alternating input seats. This script DOES NOT
claim a fully tournament-equivalent match, expert sideboard policy or ranks.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import pathlib
import tempfile

from optimize_58 import BAN_KEYS, effective_domains, is_unique, key, registry, stable_seed, benchmark
from sideboard_deck import DeckState, apply_sideboard, parse_deck, render_deck


def cards_pool(state: DeckState) -> collections.Counter:
    return state.main + state.sideboard + collections.Counter({state.champion: 1})


def check_final_legality(registered: DeckState, changed: DeckState, byname: dict) -> None:
    """Fail closed on observable Standard and Constructed construction rules.

    This validator is not a replacement for native AlphaRune's deck checker,
    particularly for special deckbuilding variants such as Neeko.
    """
    if (changed.legend != registered.legend or
        changed.runes != registered.runes or
        changed.battlefields != registered.battlefields):
        raise ValueError("Legend, runes and battlefields must remain registered")
    if cards_pool(registered) != cards_pool(changed):
        raise ValueError("Sideboard changes altered registered card identities")
    if sum(changed.main.values()) != 39 or sum(changed.sideboard.values()) > 10:
        raise ValueError("Incorrect Constructed quantities")
    if set(changed.main) & set(changed.sideboard) and any(
        changed.main[x] + changed.sideboard[x] > 3
        for x in set(changed.main) & set(changed.sideboard)
    ):
        raise ValueError("Copy limit exceeded")
    domains = effective_domains(registered.legend, byname)
    champion = byname.get(changed.champion)
    legend_tag = key(registered.legend.split(",", 1)[0])
    if not champion or champion.get("card_type") != "unit" or (
        "champion" not in (champion.get("super_type") or "").lower()
    ):
        raise ValueError("Chosen champion must be an actual champion unit")
    if legend_tag not in {key(t) for t in champion.get("tags", [])}:
        raise ValueError("Chosen champion does not match registered Legend")
    for name, copies in cards_pool(changed).items():
        c = byname.get(name)
        if not c or copies < 1:
            raise ValueError("Unknown or invalid registered card: " + name)
        if c.get("banned") or key(name) in BAN_KEYS:
            raise ValueError("Banned card in registered pool: " + name)
        if not set(c.get("domains") or ()).issubset(domains):
            raise ValueError("Off-domain card: " + name)
        if copies > (1 if is_unique(c) else 3):
            raise ValueError("Copy limit breached: " + name)
        if name in changed.main and c.get("card_type") not in ("unit", "spell", "gear"):
            raise ValueError("Unexpected Main Deck card type: " + name)


def transition(
    registered: DeckState,
    plan: dict | None,
    byname: dict,
    *,
    game_no: int,
) -> DeckState:
    """Build an independent legal game configuration from registered cards."""
    if game_no < 1:
        raise ValueError("Invalid game number")
    if plan is None:
        plan = {}
    if not isinstance(plan, dict) or set(plan) - {"swaps", "chosen_champion"}:
        raise ValueError("Unexpected sideboard-plan keys")
    if game_no == 1 and (
        (plan.get("swaps") or []) or
        (plan.get("chosen_champion") not in (None, registered.champion))
    ):
        raise ValueError("Sideboarding is forbidden before game one")
    swaps = plan.get("swaps", [])
    if not isinstance(swaps, list):
        raise ValueError("Expected list of sideboard swaps")
    parsed = []
    for row in swaps:
        if not isinstance(row, dict) or set(row) != {"main_out", "side_in", "copies"}:
            raise ValueError("Malformed sideboard swap")
        parsed.append((row["main_out"], row["side_in"], row["copies"]))
    current = apply_sideboard(registered, parsed)
    chosen = plan.get("chosen_champion") or current.champion
    if not isinstance(chosen, str):
        raise ValueError("Invalid chosen champion")
    if chosen != current.champion:
        # The old Chosen Champion becomes Main Deck / sideboard material.
        # The new Chosen Champion must be present in that same registered pool.
        if current.main.get(chosen, 0) > 0:
            current.main[chosen] -= 1
            current.main[current.champion] += 1
        elif current.sideboard.get(chosen, 0) > 0:
            current.sideboard[chosen] -= 1
            current.sideboard[current.champion] += 1
        else:
            raise ValueError("Replacement champion not in registered card pool")
        current.main += collections.Counter()
        current.sideboard += collections.Counter()
        current.champion = chosen
    check_final_legality(registered, current, byname)
    return current


def read_policy(path: pathlib.Path | None) -> dict:
    if path is None:
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or set(raw) - {"game2", "game3"}:
        raise ValueError("Sideboard policy must contain only game2 and game3")
    for game, pair in raw.items():
        if not isinstance(pair, dict) or set(pair) - {"p1", "p2"}:
            raise ValueError("Each game plan must map p1/p2 to sideboard plans")
    return raw


def run_series(
    engine: pathlib.Path, deck1: pathlib.Path, deck2: pathlib.Path,
    byname: dict, policy: dict, agent: str, seed: int,
    timeout: float = 180, env: dict | None = None
) -> dict:
    registered1 = parse_deck(deck1.read_text(encoding="utf-8"))
    registered2 = parse_deck(deck2.read_text(encoding="utf-8"))
    check_final_legality(registered1, registered1, byname)
    check_final_legality(registered2, registered2, byname)
    wins = [0, 0]
    games = []
    env = env or os.environ.copy()
    with tempfile.TemporaryDirectory(prefix="rb_bo3_sb_") as location:
        root = pathlib.Path(location)
        for index in range(1, 4):
            game_policy = policy.get(f"game{index}", {})
            one = transition(registered1, game_policy.get("p1"), byname, game_no=index)
            two = transition(registered2, game_policy.get("p2"), byname, game_no=index)
            # Preserve the source deck verbatim in Game 1.
            f1 = deck1 if index == 1 else root / f"player1_game{index}.txt"
            f2 = deck2 if index == 1 else root / f"player2_game{index}.txt"
            if index != 1:
                f1.write_text(render_deck(one), encoding="utf-8")
                f2.write_text(render_deck(two), encoding="utf-8")
            flipped = index == 2
            a,b = (f2,f1) if flipped else (f1,f2)
            result = benchmark(
                engine, a, b, stable_seed(seed,"sideboard_bo3",index),
                agent, timeout, env
            )
            rec = {
                "game": index,
                "registered_deck_sha256": [
                    hashlib.sha256(deck1.read_bytes()).hexdigest(),
                    hashlib.sha256(deck2.read_bytes()).hexdigest()
                ],
                "active_deck_sha256": [
                    hashlib.sha256(f1.read_bytes()).hexdigest(),
                    hashlib.sha256(f2.read_bytes()).hexdigest()
                ],
                "chosen_champions": [one.champion,two.champion],
                "sideboard_swaps": [
                    game_policy.get("p1", {}).get("swaps", []),
                    game_policy.get("p2", {}).get("swaps", [])
                ],
                "engine_status": result["status"],
                "winner_seat": result["winner"],
                "error": result.get("error", ""),
            }
            games.append(rec)
            if result["status"] != "complete" or result["winner"] not in (1, 2):
                return {
                    "status": "INCOMPLETE", "winner": None,
                    "games": games, "sideboarding_applied": index > 1,
                    "no_tournament_start_player_equivalence": True
                }
            winner_p1 = (result["winner"] == 2 if flipped else result["winner"] == 1)
            wins[0 if winner_p1 else 1] += 1
            if max(wins) == 2:
                break
    return {
        "status": "COMPLETE_SIDEBORD_AWARE_APPROXIMATION",
        "winner": 1 if wins[0] == 2 else 2,
        "score": wins, "games": games, "sideboarding_applied": len(games) > 1,
        "exact_tournament_play_first_policy": False,
        "source_decks_return_to_registered_state_next_match": True,
        "agent": agent, "limitations": [
            "Alternated engine input seats do not implement 407.4 loser chooses to play first",
            "Sideboard decisions are externally declared and not learned expert policies",
            "No round timer or battlefield/start-game selection policy",
        ],
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--engine", type=pathlib.Path, required=True)
    p.add_argument("--deck1", type=pathlib.Path, required=True)
    p.add_argument("--deck2", type=pathlib.Path, required=True)
    p.add_argument("--registry", type=pathlib.Path, required=True)
    p.add_argument("--policy", type=pathlib.Path)
    p.add_argument("--agent", default="ismcts:sims=24")
    p.add_argument("--seed", type=int, default=202611240002)
    p.add_argument("--timeout", type=float, default=180)
    p.add_argument("--output", type=pathlib.Path, required=True)
    args = p.parse_args()
    if args.timeout <= 0:
        p.error("Invalid timeout")
    payload = run_series(
        args.engine.resolve(), args.deck1.resolve(), args.deck2.resolve(),
        registry(args.registry), read_policy(args.policy),
        args.agent, args.seed, args.timeout
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("TOURNAMENT_SIDEBORD_PROTOTYPE", json.dumps(payload), flush=True)
    if payload["status"] != "COMPLETE_SIDEBORD_AWARE_APPROXIMATION":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
