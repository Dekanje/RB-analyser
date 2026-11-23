#!/usr/bin/env python3
"""No-engine tests: source integrity for evolutionary screen."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from screen_evolution import PILOT, opponent_panel, validate_candidate_text
from round_robin_58 import sha


class EvolutionScreenTests(unittest.TestCase):
    def test_frozen_proposal_components(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            before=root/"source.txt"; after=root/"candidate.txt"
            tail=("\nBattlefields:\n1 Field A\n1 Field B\n1 Field C\n\n"
                  "Runes:\n6 Fury Rune\n6 Chaos Rune\n\nSideboard:\n1 Strong Tech\n")
            start="Legend:\n1 Draven, Glorious Executioner\n\nChampion:\n1 Draven, Showboat\n\nMainDeck:\n"
            before.write_text(start+"3 Card A\n3 Card B\n"+tail)
            after.write_text(start+"2 Card A\n4 Card B\n"+tail)
            self.assertTrue(validate_candidate_text(before,after,sha(after)))
            with self.assertRaises(RuntimeError):
                validate_candidate_text(before,after,"wronghash")
            after.write_text(after.read_text().replace("1 Field A","1 Different Field"))
            with self.assertRaises(RuntimeError):
                validate_candidate_text(before,after,sha(after))

    def test_registered_neeko_suffix_is_sole_exception(self):
        with tempfile.TemporaryDirectory() as temp:
            root=pathlib.Path(temp)
            before=root/"before.txt";after=root/"after.txt"
            start=("Legend:\\n1 Draven, Glorious Executioner\\n\\n"
                   "Champion:\\n1 Draven, Showboat\\n\\nMainDeck:\\n")
            suffix=("\\nBattlefields:\\n1 Field A\\n1 Field B\\n1 Field C\\n\\n"
                    "Runes:\\n6 Fury Rune\\n6 Chaos Rune\\n\\nSideboard:\\n1 Tech\\n")
            before.write_text(start+"39 Card A\\n"+suffix)
            core=start+"38 Card A\\n1 Neeko, Blending In\\n"+suffix
            extra="\\nNeekoLegends:\\n1 Loose Cannon\\n1 Blind Monk\\n1 Nine-Tailed Fox\\n"
            after.write_text(core.rstrip()+extra)
            self.assertTrue(validate_candidate_text(before,after,sha(after)))
            after.write_text(core.rstrip()+"\\nNeekoLegends:\\n1 Loose Cannon\\n1 Loose Cannon\\n1 Blind Monk\\n")
            with self.assertRaises(RuntimeError):
                validate_candidate_text(before,after,sha(after))
            after.write_text(core.replace("1 Tech","1 Unapproved Tech").rstrip()+extra)
            with self.assertRaises(RuntimeError):
                validate_candidate_text(before,after,sha(after))
            after.write_text(start+"39 Card A\\n"+suffix.rstrip()+extra)
            with self.assertRaises(RuntimeError):
                validate_candidate_text(before,after,sha(after))
            after.write_text(core.rstrip()+"\\nNeekoLegends:\\n1 Glorious Executioner\\n1 Blind Monk\\n1 Nine-Tailed Fox\\n")
            with self.assertRaises(RuntimeError):
                validate_candidate_text(before,after,sha(after))

    def test_panel_never_includes_self(self):
        ranked=[{"legend":n} for n in (
            "Draven, Glorious Executioner","Rek'Sai, Void Burrower",
            "Ambessa, Matriarch of War","Volibear, Relentless Storm")]
        d={x["legend"]:x["legend"] for x in ranked}
        selected=opponent_panel(PILOT[0],ranked,d,3)
        self.assertEqual(list(selected),list(d)[1:4])
        self.assertNotIn(PILOT[0],selected)
        with self.assertRaises(RuntimeError):
            opponent_panel(PILOT[0],ranked,d,4)


if __name__=="__main__":
    unittest.main()
