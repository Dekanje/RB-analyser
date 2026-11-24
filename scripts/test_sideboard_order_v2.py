import unittest
from sideboard_order_v2 import ordered, repair, require_ordered, sideboard_offset


def deck(main="1 Z\n37 A\n1 Z", bf="1 Z Field\n1 A Field\n1 B Field",
         runes="6 Z Rune\n6 A Rune", side="1 Old"):
    return (f"Legend:\n1 L\nChampion:\n1 C\nMainDeck:\n{main}\n"
            f"Battlefields:\n{bf}\nRunes:\n{runes}\nSideboard:\n{side}\n").encode()


class OrderV2Tests(unittest.TestCase):
    def test_preserves_noncontiguous_rows_and_unsorted_sections(self):
        a = deck()
        b = deck(main="37 A\n2 Z", bf="1 A Field\n1 B Field\n1 Z Field",
                 runes="6 A Rune\n6 Z Rune", side="1 New")
        fixed = repair(a, b)
        self.assertEqual(fixed[:sideboard_offset(fixed)], a[:sideboard_offset(a)])
        self.assertEqual(ordered(fixed)["Sideboard"], ["New"])
        require_ordered(a, fixed)

    def test_strict_gate_rejects_reordered_candidate(self):
        with self.assertRaisesRegex(ValueError, "ordered playable"):
            require_ordered(deck(), deck(runes="6 A Rune\n6 Z Rune", side="1 New"))

    def test_rejects_composition_change(self):
        with self.assertRaisesRegex(ValueError, "playable composition"):
            repair(deck(), deck(runes="12 A Rune", side="1 New"))

    def test_rejects_unchanged_sideboard(self):
        with self.assertRaisesRegex(ValueError, "no sideboard"):
            repair(deck(), deck())

    def test_preserves_crlf_prefix(self):
        a = deck().replace(b"\n", b"\r\n")
        b = deck(side="1 New")
        fixed = repair(a, b)
        self.assertTrue(fixed.startswith(a[:sideboard_offset(a)]))
        require_ordered(a, fixed)

    def test_rejects_bad_card_count(self):
        with self.assertRaises(ValueError):
            repair(deck(), deck(side="11 New"))

    def test_rejects_missing_section(self):
        with self.assertRaises(ValueError):
            repair(deck(), b"Legend:\n1 L\n")

    def test_preserves_candidate_sideboard_order(self):
        b = deck(side="1 Y\n1 X\n1 Y")
        self.assertEqual(ordered(repair(deck(), b))["Sideboard"], ["Y", "X", "Y"])


if __name__ == "__main__":
    unittest.main()
