#!/usr/bin/env python3
"""Tests for structural one-for-one Constructed sideboarding."""
import collections
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sideboard_deck import DeckState, apply_sideboard, parse_deck, render_deck


class SideboardTests(unittest.TestCase):
    def sample(self):
        return DeckState(
            "Ambessa, Matriarch of War",
            "Ambessa, The Wolf",
            collections.Counter({f"Main {i:02d}": 3 for i in range(13)}),
            collections.Counter({"Battlefield A": 1, "Battlefield B": 1,
                                 "Battlefield C": 1}),
            collections.Counter({"Body Rune": 6, "Order Rune": 6}),
            collections.Counter({"Side A": 3, "Side B": 3,
                                 "Side C": 2, "Side D": 2}),
        )

    def test_round_trip_preserves_registered_counts(self):
        state = self.sample()
        decoded = parse_deck(render_deck(state))
        self.assertEqual(decoded.legend, state.legend)
        self.assertEqual(decoded.champion, state.champion)
        self.assertEqual(decoded.main, state.main)
        self.assertEqual(decoded.sideboard, state.sideboard)
        self.assertEqual(decoded.battlefields, state.battlefields)
        self.assertEqual(decoded.runes, state.runes)

    def test_successful_swaps_do_not_touch_registered_deck(self):
        registered = self.sample()
        pool = registered.main + registered.sideboard
        result = apply_sideboard(registered, [
            ("Main 01", "Side A", 2), ("Main 02", "Side C", 1)
        ])
        self.assertEqual(sum(result.main.values()), 39)
        self.assertEqual(sum(result.sideboard.values()), 10)
        self.assertEqual(result.main["Main 01"], 1)
        self.assertEqual(result.main["Side A"], 2)
        self.assertEqual(result.sideboard["Main 02"], 1)
        self.assertEqual(result.main + result.sideboard, pool)
        self.assertEqual(result.runes, registered.runes)
        self.assertEqual(result.battlefields, registered.battlefields)
        self.assertEqual(registered.main["Main 01"], 3)
        self.assertEqual(registered.sideboard["Side A"], 3)
        self.assertEqual(parse_deck(render_deck(result)).main, result.main)

    def test_reject_illegal_swaps_before_side_effects(self):
        registered = self.sample()
        bad = [
            [("Main 01", "Side A", 4)],
            [("Main 01", "Missing", 1)],
            [("Missing", "Side A", 1)],
            [("Main 01", "Side A", 0)],
            [("Main 01", "Side A", -1)],
            [("Main 01", "Side A", True)],
            [("Main 01", "Main 01", 1)],
            [("Main 01", "Side A", 2), ("Main 01", "Side B", 2)],
        ]
        original = render_deck(registered)
        for swaps in bad:
            with self.subTest(swaps=swaps), self.assertRaises(ValueError):
                apply_sideboard(registered, swaps)
            self.assertEqual(render_deck(registered), original)

    def test_reject_oversized_sideboard(self):
        state = self.sample()
        state.sideboard["Extra"] = 1
        with self.assertRaises(ValueError):
            render_deck(state)

    def test_missing_and_disordered_sections_are_rejected(self):
        lines = render_deck(self.sample()).splitlines()
        with self.assertRaises(ValueError):
            parse_deck("\n".join(line for line in lines if line != "Sideboard:"))
        with self.assertRaises(ValueError):
            parse_deck("Champion:\n1 Example\nLegend:\n1 Example\n")

    def test_round_trip_swap_reverse(self):
        state = self.sample()
        mutated = apply_sideboard(state, [("Main 02", "Side B", 2)])
        original = apply_sideboard(mutated, [("Side B", "Main 02", 2)])
        self.assertEqual(original.main, state.main)
        self.assertEqual(original.sideboard, state.sideboard)


if __name__ == "__main__":
    unittest.main()
