#!/usr/bin/env python3
"""Unit regression for coordinated synergy packages, before any native BO3."""
import collections
import hashlib
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from sideboard_deck import DeckState, parse_deck, render_deck
from structural_deck_population import legal_registration
from synergy_multicard import package_search, printed_pair_synergy


class SynergyPackageTests(unittest.TestCase):
    def fixture(self):
        legend = "Test Hero, Test Legend"
        champion = "Test Hero, Champion"
        byname = {
            "Test Legend": {"name": "Test Legend", "card_type": "legend",
                            "domains": ["Fury", "Chaos"], "tags": ["Test Hero"]},
            champion: {"name": champion, "card_type": "unit", "super_type": "Champion",
                       "domains": ["Fury"], "tags": ["Test Hero"], "energy_cost": 3},
        }
        main = collections.Counter()
        for i in range(13):
            name = "Original %02d" % i
            main[name] = 3
            byname[name] = {"name": name, "card_type": "unit", "super_type": "",
                            "domains": ["Fury"], "tags": ["Soldier"], "energy_cost": 2,
                            "might": 2, "ability_text": " "}
        byname["Original 00"]["super_type"] = "Signature"
        for i in range(15):
            name = "Package %02d" % i
            byname[name] = {"name": name, "card_type": "spell" if i % 3 == 0 else "unit",
                            "super_type": "", "domains": ["Fury", "Chaos"] if i%2 else ["Fury"],
                            "tags": ["Soldier", "Test Hero"] if i%2 else ["Soldier"],
                            "energy_cost": i%5+1, "might": 3,
                            "ability_text": "When you play a spell, draw a card" if i%3 else "Draw one"}
        byname["Package 14"]["banned"] = True
        for i in range(3):
            name = "Battlefield %d" % i
            byname[name] = {"name": name, "card_type": "battlefield",
                            "domains": [], "super_type": ""}
        for domain in ("Fury", "Chaos"):
            name = domain + " Rune"
            byname[name] = {"name": name, "card_type": "rune", "domains": [domain]}
        deck = DeckState(
            legend, champion, main,
            collections.Counter({"Battlefield %d"%i: 1 for i in range(3)}),
            collections.Counter({"Fury Rune": 6, "Chaos Rune": 6}),
            collections.Counter()
        )
        return deck, byname

    def test_printed_synergy_is_bounded_and_explainable(self):
        a = {"card_type": "unit", "tags": ["Soldier"],
             "ability_text": "When you play a spell, draw a card"}
        b = {"card_type": "spell", "tags": ["Soldier"], "ability_text": "Draw a card"}
        value, signals = printed_pair_synergy(a, b)
        self.assertGreater(value, 0)
        self.assertIn("printed_spell_play_trigger", signals)
        self.assertIn("shared_printed_tag", signals)

    def test_six_deterministic_two_three_card_packages_keep_registration(self):
        original, byname = self.fixture()
        legal_registration(original, original, byname)
        a = package_search(original, byname, original.legend, 1234)
        b = package_search(original, byname, original.legend, 1234)
        self.assertEqual(a, b)
        self.assertEqual(len(a), 6)
        self.assertEqual([x["depth"] for x in a], [2,2,2,3,3,3])
        hashes = set()
        for row in a:
            self.assertEqual(len(row["steps"]), row["depth"])
            self.assertEqual(len({s["add"] for s in row["steps"]}), row["depth"])
            self.assertNotIn("Package 14", row["deck"])
            h = hashlib.sha256(row["deck"].encode()).hexdigest()
            self.assertNotIn(h, hashes)
            hashes.add(h)
            changed = parse_deck(row["deck"])
            legal_registration(original, changed, byname)
            self.assertEqual(changed.main["Original 00"], 3)
            self.assertEqual(changed.sideboard, original.sideboard)
            self.assertEqual(changed.champion, original.champion)
            self.assertEqual(changed.runes, original.runes)
            self.assertEqual(changed.battlefields, original.battlefields)
            self.assertEqual(sum(changed.main.values()), 39)

    def test_missing_alternatives_fails_closed(self):
        original, byname = self.fixture()
        for i in range(15):
            byname.pop("Package %02d" % i)
        with self.assertRaisesRegex(RuntimeError, "Insufficient compiled legal alternatives"):
            package_search(original, byname, original.legend, 1234)


if __name__ == "__main__":
    unittest.main()
