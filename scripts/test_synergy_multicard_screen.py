#!/usr/bin/env python3
"""Fail-closed screening evidence tests for coordinated main-deck packages."""
import hashlib
import json
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from test_synergy_multicard import SynergyPackageTests
from sideboard_deck import render_deck
from synergy_multicard_screen import validate_candidate, schedule, game


class ScreenTests(unittest.TestCase):
    def test_provenance_and_nonmain_immutability(self):
        original, byname = SynergyPackageTests().fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            src = root/"source.txt"
            src.write_text(render_deck(original))
            altered = original.clone()
            altered.main["Original 01"] -= 1
            altered.main["Original 02"] -= 1
            altered.main["Package 00"] += 1
            altered.main["Package 01"] += 1
            candidate = root/"candidate.txt"
            candidate.write_text(render_deck(altered))
            steps = [{"remove":"Original 01","add":"Package 00"},
                     {"remove":"Original 02","add":"Package 01"}]
            entry = {"path":"candidate.txt","sha256":hashlib.sha256(candidate.read_bytes()).hexdigest(),
                     "status":"SYNERGY_PACKAGES_UNTESTED_NO_STRENGTH_CLAIM",
                     "kind":"coordinated_main_deck_package",
                     "native_simulated":False,"depth":2,"steps":steps}
            self.assertEqual(validate_candidate(src,entry,byname,root),candidate)
            candidate.write_text(render_deck(original))
            with self.assertRaisesRegex(RuntimeError, "Modified or missing"):
                validate_candidate(src,entry,byname,root)
            candidate.write_text(render_deck(altered))
            wrong = dict(entry,steps=[steps[0],steps[0]])
            with self.assertRaisesRegex(RuntimeError, "repeated incoming"):
                validate_candidate(src,wrong,byname,root)
            outsider = dict(entry,path="../outside.txt")
            with self.assertRaisesRegex(RuntimeError, "escaped"):
                validate_candidate(src,outsider,byname,root)

    def test_four_independently_seeded_mirrored_cases(self):
        ranked=[{"legend":"A"},{"legend":"B"},{"legend":"C"}]
        x=schedule("A",ranked,42)
        self.assertEqual(len(x),4)
        self.assertEqual([(r["opponent"],r["seat"]) for r in x],
                         [("B",0),("B",1),("C",0),("C",1)])
        self.assertEqual(len({r["seed"] for r in x}),4)
        self.assertEqual(x,schedule("A",ranked,42))

    def test_no_missing_407_engine_receipt_is_counted_as_win(self):
        class Args:
            engine=pathlib.Path("/tmp/nonexistent_riftbound")
            agent="ismcts:sims=24"
            timeout=10
        case={"seat":0,"seed":12}
        fake={"status":"COMPLETE_RULE407_START_POLICY_BO3",
              "rule_407_4_start_choice_verified":False,
              "winner":1,"games":[{"engine_status":"complete"}]*2,
              "source_decks_return_to_registered_state_next_match":True,
              "sideboarding_applied":False}
        with patch("synergy_multicard_screen.run_series",return_value=fake):
            with self.assertRaisesRegex(RuntimeError, "BO3 incomplete"):
                game(Args(),pathlib.Path("a"),pathlib.Path("b"),case,{})


if __name__=="__main__":
    unittest.main()
