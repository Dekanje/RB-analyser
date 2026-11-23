#!/usr/bin/env python3
"""Immutable one-for-one Constructed main-deck sideboard transformations.

This is a STRUCTURAL precursor for tournament BO3. It does not optimize
sideboard choices or change the Chosen Champion. Printed card legality
and exact domain/ban enforcement remain the engine deck validator's job.
"""
from __future__ import annotations

import argparse
import collections
import dataclasses
import json
import pathlib
import re


HEADINGS = ("Legend", "Champion", "MainDeck", "Battlefields", "Runes", "Sideboard")
CARD_ROW = re.compile(r"^\s*(\d+)\s+(.+?)\s*$")


@dataclasses.dataclass
class DeckState:
    legend: str
    champion: str
    main: collections.Counter
    battlefields: collections.Counter
    runes: collections.Counter
    sideboard: collections.Counter

    def clone(self) -> "DeckState":
        return DeckState(
            self.legend, self.champion, self.main.copy(),
            self.battlefields.copy(), self.runes.copy(), self.sideboard.copy()
        )


def parse_rows(lines: list[str], section: str) -> collections.Counter:
    count = collections.Counter()
    for line in lines:
        if not line.strip():
            continue
        match = CARD_ROW.fullmatch(line)
        if not match:
            raise ValueError(f"Malformed {section} entry: {line}")
        copies, card = int(match.group(1)), match.group(2)
        if copies <= 0:
            raise ValueError("Card copies must be strictly positive")
        count[card] += copies
    return count


def parse_deck(text: str) -> DeckState:
    sections = {k: [] for k in HEADINGS}
    current = None
    seen = set()
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.endswith(":") and stripped[:-1] in HEADINGS:
            key = stripped[:-1]
            if key in seen or HEADINGS[len(seen)] != key:
                raise ValueError(f"Duplicate or out-of-order section: {key}")
            seen.add(key)
            current = key
        elif not stripped and current is None:
            continue
        elif current is None:
            raise ValueError("Deck content before its first section")
        else:
            sections[current].append(line)
    if set(sections) != seen:
        raise ValueError("Missing one or more deck sections")
    fields = {k: parse_rows(v, k) for k, v in sections.items()}
    for single in ("Legend", "Champion"):
        if sum(fields[single].values()) != 1:
            raise ValueError(f"{single} must contain exactly one card")
    state = DeckState(
        next(iter(fields["Legend"])), next(iter(fields["Champion"])),
        fields["MainDeck"], fields["Battlefields"], fields["Runes"],
        fields["Sideboard"]
    )
    validate_structure(state)
    return state


def validate_structure(state: DeckState) -> None:
    if sum(state.main.values()) != 39:
        raise ValueError("Constructed main deck must contain 39 cards plus chosen champion")
    if sum(state.battlefields.values()) != 3:
        raise ValueError("Three registered battlefields required")
    if sum(state.runes.values()) != 12:
        raise ValueError("Exactly twelve registered runes required")
    if sum(state.sideboard.values()) > 10:
        raise ValueError("Constructed sideboard exceeds ten cards")
    for section in (state.main, state.battlefields, state.runes, state.sideboard):
        if any(n <= 0 for n in section.values()):
            raise ValueError("Cards with nonpositive copies found")


def render_rows(counter: collections.Counter) -> list[str]:
    return [f"{count} {card}" for card, count in sorted(counter.items()) if count > 0]


def render_deck(state: DeckState) -> str:
    validate_structure(state)
    sections = (
        ("Legend", collections.Counter({state.legend: 1})),
        ("Champion", collections.Counter({state.champion: 1})),
        ("MainDeck", state.main),
        ("Battlefields", state.battlefields),
        ("Runes", state.runes),
        ("Sideboard", state.sideboard),
    )
    return "\n\n".join(
        section + ":\n" + "\n".join(render_rows(cards)) for section, cards in sections
    ).rstrip() + "\n"


def apply_sideboard(
    registered: DeckState,
    swaps: list[tuple[str, str, int]],
) -> DeckState:
    """Swap equal quantities of cards from registered main and sideboard.

    Swaps have (main_card_to_remove, sideboard_card_to_add, quantity).
    Preserve full registered card multiset and all immutable deck fields.
    Reuse the ORIGINAL registered state for each new match.
    """
    validate_structure(registered)
    result = registered.clone()
    original_pool = registered.main + registered.sideboard
    for main_out, side_in, quantity in swaps:
        if (not isinstance(quantity, int) or isinstance(quantity, bool) or quantity <= 0):
            raise ValueError("Each sideboard swap quantity must be a positive integer")
        if main_out == side_in:
            raise ValueError("Meaningless same-card substitution")
        if result.main[main_out] < quantity:
            raise ValueError(f"Insufficient main-deck card copies: {main_out}")
        if result.sideboard[side_in] < quantity:
            raise ValueError(f"Insufficient sideboard card copies: {side_in}")
        result.main[main_out] -= quantity
        result.sideboard[main_out] += quantity
        result.sideboard[side_in] -= quantity
        result.main[side_in] += quantity
        result.main += collections.Counter()
        result.sideboard += collections.Counter()
    if result.main + result.sideboard != original_pool:
        raise RuntimeError("Sideboard operation changed the registered card pool")
    if result.legend != registered.legend or result.champion != registered.champion:
        raise RuntimeError("Champion/Legend changes are not implemented by this helper")
    if result.runes != registered.runes or result.battlefields != registered.battlefields:
        raise RuntimeError("Registered runes/battlefields must remain unchanged")
    validate_structure(result)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--registered", type=pathlib.Path, required=True)
    p.add_argument("--swaps-json", type=pathlib.Path, required=True)
    p.add_argument("--output", type=pathlib.Path, required=True)
    args = p.parse_args()
    source = parse_deck(args.registered.read_text(encoding="utf-8"))
    payload = json.loads(args.swaps_json.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        p.error("Expected JSON array of {main_out,side_in,copies}")
    swaps = []
    for row in payload:
        if not isinstance(row, dict) or set(row) != {"main_out", "side_in", "copies"}:
            p.error("Every swap must define main_out, side_in and copies")
        swaps.append((row["main_out"], row["side_in"], row["copies"]))
    updated = apply_sideboard(source, swaps)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_deck(updated), encoding="utf-8")
    print("STRUCTURAL_SIDEBOARD_OK", len(swaps),
          "card swaps; tournament deck rules and strategy NOT independently certified")


if __name__ == "__main__":
    main()
