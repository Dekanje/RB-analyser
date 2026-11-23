#!/usr/bin/env python3
"""Pinned AlphaRune override for loser-chooses-first best-of-three policy.

Single-game subprocesses may set RIFTBOUND_FORCE_STARTING_PLAYER=1 or 2.
The default, with variable unset, is EXACTLY the historical random coin flip.
The overridden engine consumes the original coin flip before forcing the
starting player, so live and ISMCTS mirrored OpenSpiel engines advance the
RNG stream identically. This is essential to prevent search-state divergence.

GameEngine is used both by the live match and by its OpenSpiel replay/search
states; reading the process-level env there applies the override consistently
to every clone and determinization within the single-game subprocess.

This is NOT a workaround that swaps seats (that previously left actual first
turn order random). A receipt from main.cpp explicitly reports the actual
GameState.turn.starting_player for strict Python-side verification.
"""
from __future__ import annotations

import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENGINE = ROOT / "alpharune"
PIN = "ec90f0fed002aed374d06249fa95e83e3cfbd386"


def replace_once(path: pathlib.Path, before: str, after: str) -> None:
    source = path.read_text(encoding="utf-8")
    occurrences = source.count(before)
    if occurrences != 1:
        raise RuntimeError(
            f"Expected exactly one pinned AlphaRune anchor in {path}: "
            f"{occurrences}; anchor starts {before[:90]!r}"
        )
    path.write_text(source.replace(before, after, 1), encoding="utf-8")


def patch(start: pathlib.Path) -> None:
    game = start / "src/engine/game_engine.cpp"
    main = start / "src/main.cpp"
    replace_once(game,
        "#include <algorithm>\n#include <cassert>",
        "#include <algorithm>\n#include <cassert>\n#include <cstdlib>")
    replace_once(game,
        """void GameEngine::determineTurnOrder() {
    // Random coin flip for first player (CR 116)
    std::uniform_int_distribution<int> coin(0, 1);
    state_.turn.turn_player = coin(rng_) == 0 ? PlayerId::Player1 : PlayerId::Player2;
    state_.turn.starting_player = state_.turn.turn_player;""",
        """void GameEngine::determineTurnOrder() {
    // Random coin flip for first player (CR 116). Consume the same RNG draw
    // even under tournament override: live and ISMCTS replay must match.
    std::uniform_int_distribution<int> coin(0, 1);
    const int toss = coin(rng_);
    state_.turn.turn_player = toss == 0 ? PlayerId::Player1 : PlayerId::Player2;
    // In BO3 games 2/3 the previous game's loser chooses who plays first.
    // This explicit override is shared by the engine's live and OpenSpiel
    // game objects, which execute inside the same single-game subprocess.
    const char* forced_start = std::getenv("RIFTBOUND_FORCE_STARTING_PLAYER");
    if (forced_start != nullptr && forced_start[0] != '\\0') {
        if (std::string(forced_start) == "1") {
            state_.turn.turn_player = PlayerId::Player1;
        } else if (std::string(forced_start) == "2") {
            state_.turn.turn_player = PlayerId::Player2;
        } else {
            throw std::invalid_argument(
                "RIFTBOUND_FORCE_STARTING_PLAYER must be 1 or 2");
        }
    }
    state_.turn.starting_player = state_.turn.turn_player;""")
    replace_once(main,
        "#include <algorithm>\n#include <atomic>",
        "#include <algorithm>\n#include <atomic>\n#include <cstdlib>")
    replace_once(main,
        '''            auto result = engine.runGame(deck1, deck2, *seat1, *seat2, game_seed);
            std::cout << "\\nGame over: winner="''',
        '''            auto result = engine.runGame(deck1, deck2, *seat1, *seat2, game_seed);
            // Deliberately report the engine's actual start state, not an
            // echoed environment variable. Python rejects mismatches.
            const char* forced = std::getenv("RIFTBOUND_FORCE_STARTING_PLAYER");
            if (forced != nullptr && forced[0] != '\\0') {
                std::cout << "\\nTOURNAMENT_FORCED_STARTING_PLAYER="
                          << static_cast<int>(engine.state().turn.starting_player)
                          << "\\n";
            }
            std::cout << "\\nGame over: winner="'''
        )
    print("PINNED_TOURNAMENT_STARTING_PLAYER_OVERRIDE_APPLIED", PIN, flush=True)


def main() -> None:
    sha = subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ENGINE, text=True).strip()
    if sha != PIN:
        raise SystemExit("Refusing to patch unknown AlphaRune commit: " + sha)
    patch(ENGINE)


if __name__ == "__main__":
    main()
