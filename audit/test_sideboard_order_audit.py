import unittest
from sideboard_order_audit import changed_order, parse_ordered


def deck(runes="1 Z Rune\n1 A Rune", battlefields="1 Z Field\n1 A Field", sideboard="1 X"):
    return (f"Legend:\n1 L\nChampion:\n1 C\nMainDeck:\n1 M\n"
            f"Battlefields:\n{battlefields}\nRunes:\n{runes}\nSideboard:\n{sideboard}\n").encode()


class OrderTests(unittest.TestCase):
    def test_sideboard_only(self):
        self.assertEqual(changed_order(deck(), deck(sideboard="1 Y")), ())

    def test_reordered_runes_and_battlefields(self):
        self.assertEqual(changed_order(deck(), deck(runes="1 A Rune\n1 Z Rune",
            battlefields="1 A Field\n1 Z Field", sideboard="1 Y")), ("Battlefields", "Runes"))

    def test_composition_change_rejected(self):
        with self.assertRaises(ValueError):
            changed_order(deck(), deck(runes="2 Z Rune", sideboard="1 Y"))

    def test_no_sideboard_change_rejected(self):
        with self.assertRaises(ValueError):
            changed_order(deck(), deck())

    def test_missing_section_rejected(self):
        with self.assertRaises(ValueError):
            parse_ordered(b"Legend:\n1 L\n")

    def test_duplicate_section_rejected(self):
        with self.assertRaises(ValueError):
            parse_ordered(deck() + b"Legend:\n1 L\n")


if __name__ == "__main__":
    unittest.main()
