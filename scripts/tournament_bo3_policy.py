#!/usr/bin/env python3
"""BO3 with legal between-game swaps, Champion changes and loser-chooses-first.

Implements Constructed 403.4/403.8, plus 407.4 first-player selection for
Games 2/3 using the explicitly modified actual C++ AlphaRune turn order.
A mismatched engine receipt is an ERROR, never counted as a win.
Chosen sideboard strategies are still externally supplied, not learned.
Not yet a complete tournament model (clock and matchup-sideboard policy).
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
        if not isinstance(pair, dict) or set(pair) - {
            "p1", "p2", "loser_chooses_start"
        }:
            raise ValueError("Each game plan must map p1/p2 and optional loser_chooses_start")
        if pair.get("loser_chooses_start", "self") not in ("self", "opponent"):
            raise ValueError("Loser must choose self or opponent to start")
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
    previous_winner_identity = None
    env = dict(os.environ.copy() if env is None else env)
    # Game 1 must not inherit a user shell's experimental turn override.
    env.pop("RIFTBOUND_FORCE_STARTING_PLAYER", None)
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
            per_game_env = env.copy()
            start_choice = None
            prev_loser = None
            first_player_identity = None
            expected_engine_seat = None
            if index > 1:
                if previous_winner_identity not in (1,2):
                    raise RuntimeError("Missing the previous game's verified winner")
                prev_loser = 3 - previous_winner_identity
                # Tournament 407.4: the loser chooses to play first themselves
                # or nominates their opponent. Default strategic policy = self.
                start_choice = game_policy.get("loser_chooses_start", "self")
                if start_choice not in ("self","opponent"):
                    raise ValueError("Invalid loser-chooses-start policy")
                first_player_identity = (
                    prev_loser if start_choice == "self" else previous_winner_identity
                )
                expected_engine_seat = (3 - first_player_identity
                                        if flipped else first_player_identity)
                per_game_env["RIFTBOUND_FORCE_STARTING_PLAYER"] = str(expected_engine_seat)
            result = benchmark(
                engine, a, b, stable_seed(seed,"sideboard_bo3",index),
                agent, timeout, per_game_env
            )
            # Receipt parsed from the engine's actual GameState turn.starting_player.
            # Its absence means an old engine was used: fail closed.
            if index > 1 and result["status"] == "complete" and (
                result.get("forced_start_verified") is not True or
                result.get("forced_starting_player") != expected_engine_seat
            ):
                # A missing turn receipt is itself an error. However, do
                # NOT overwrite a genuine native engine failure/timeout with
                # this secondary symptom: retain the original stderr and
                # process-exit reason so the exact failed seed can be fixed.
                result = {**result, "status":"error",
                          "error":"C++ forced first-player receipt absent or incorrect"}
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
                "previous_game_loser_identity": prev_loser,
                "loser_chose": start_choice,
                "first_player_identity": first_player_identity,
                "expected_engine_starting_seat": expected_engine_seat,
                "verified_engine_starting_seat": result.get("forced_starting_player"),
                "forced_start_verified": result.get("forced_start_verified", False),
                "error": result.get("error", ""),
            }
            games.append(rec)
            if result["status"] != "complete" or result["winner"] not in (1, 2):
                return {
                    "status": "INCOMPLETE", "winner": None,
                    "games": games, "sideboarding_applied": index > 1,
                    "rule_407_4_start_choice_verified": False
                }
            winner_p1 = (result["winner"] == 2 if flipped else result["winner"] == 1)
            previous_winner_identity = 1 if winner_p1 else 2
            wins[0 if winner_p1 else 1] += 1
            if max(wins) == 2:
                break
    return {
        "status": "COMPLETE_RULE407_START_POLICY_BO3",
        "winner": 1 if wins[0] == 2 else 2,
        "score": wins, "games": games,
        "sideboarding_applied": any(any(g["sideboard_swaps"]) or g["chosen_champions"] != [registered1.champion, registered2.champion] for g in games[1:]),
        "rule_407_4_start_choice_verified": all(
            g["forced_start_verified"] and
            g["verified_engine_starting_seat"]==g["expected_engine_starting_seat"]
            for g in games[1:]
        ),
        "source_decks_return_to_registered_state_next_match": True,
        "agent": agent, "limitations": [
            "A declared loser-start decision is applied; intelligent first-player choice is not learned",
            "Sideboard decisions are externally declared and not learned expert policies",
            "No round timer or matchup-optimized battlefield policy",
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
    print("TOURNAMENT_SIDEBOARD_PROTOTYPE", json.dumps(payload), flush=True)
    if payload["status"] != "COMPLETE_RULE407_START_POLICY_BO3":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
