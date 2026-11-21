#!/usr/bin/env python3
"""Deterministic tests for *experimental*, not strategically optimized sideboarding."""
import collections
import hashlib
import pathlib
import tempfile
import unittest
from unittest.mock import patch
from sideboard_bo3 import parse_sections, one_swap, series

def fixture(root, side=True):
    cards = "\n".join(f"3 Main Card {i:02d}" for i in range(13))
    board = "1 Alternate Card\n2 Another Card\n" if side else ""
    text = ("Legend:\n1 Example, Legend\n\nChosenChampion:\n1 Example, Champion\n"
            "\nMainDeck:\n" + cards + "\n\nBattlefields:\n"
            "1 Field A\n1 Field B\n1 Field C\n\nRunes:\n"
            "6 Body Rune\n6 Chaos Rune\n\nSideboard:\n" + board)
    path = root / "fixture.txt"
    path.write_text(text, encoding="utf-8")
    return path

class SideboardTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = pathlib.Path(self.tmp.name)
        self.original = fixture(self.root)
        self.source_hash = hashlib.sha256(self.original.read_bytes()).hexdigest()

    def test_game_one_uses_registered_deck(self):
        path, swaps = one_swap(self.original, "Opponent", 101, "A", 1,
                               self.root / "generated")
        self.assertEqual(path, self.original)
        self.assertEqual(swaps, [])

    def test_postboard_conserves_registered_pool_and_champion(self):
        _, main, side = parse_sections(self.original)
        path, swaps = one_swap(self.original, "Opponent", 101, "A", 2,
                               self.root / "generated")
        self.assertEqual(len(swaps), 1)
        lines, changed_main, changed_side = parse_sections(path)
        self.assertEqual(changed_main + changed_side, main + side)
        self.assertEqual(sum(changed_main.values()), 39)
        self.assertEqual(sum(changed_side.values()), 3)
        self.assertIn("1 Example, Champion", lines)
        self.assertIn("1 Field A", lines)
        self.assertEqual(hashlib.sha256(self.original.read_bytes()).hexdigest(),
                         self.source_hash)
        self.assertNotEqual(path, self.original)

    def test_postboard_repeatability(self):
        a, swaps_a = one_swap(self.original, "Opponent", 101, "A", 2,
                              self.root / "generated")
        b, swaps_b = one_swap(self.original, "Opponent", 101, "A", 2,
                              self.root / "generated")
        self.assertEqual((a, swaps_a), (b, swaps_b))

    def test_empty_sideboard_no_swap(self):
        source = fixture(self.root, side=False)
        path, swaps = one_swap(source, "Opponent", 101, "A", 2,
                               self.root / "generated")
        self.assertEqual(path, source)
        self.assertEqual(swaps, [])

    def test_real_series_record_shape_and_postboard(self):
        deck = self.original
        records = []
        def mock_game(exe, left, right, seed, seconds, agent):
            records.append((left, right))
            return {"status": "complete", "winner": 1,
                    "returncode": 0, "stderr_tail": ""}
        with patch("sideboard_bo3.gametest", side_effect=mock_game):
            result = series(self.root / "engine",
                            {"Alpha": deck, "Beta": deck},
                            "Alpha", "Beta", 0, 0, 100,
                            "ismcts:sims=48", self.root / "generated")
        self.assertEqual(result["status"], "complete")
        self.assertEqual(len(records), 3)
        self.assertEqual(records[0], (deck, deck))
        self.assertEqual(result["games"][0]["sideboard"]["A"]["swaps"], [])
        self.assertTrue(result["games"][1]["sideboard"]["A"]["swaps"])
        self.assertEqual(result["winner_side"], "A")
        self.assertEqual(result["score"], {"A": 2, "B": 1})

if __name__ == "__main__":
    unittest.main()
