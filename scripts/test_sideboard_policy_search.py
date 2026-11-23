#!/usr/bin/env python3
"""Deterministic legal sideboard candidate and 407 game evidence tests."""
import collections
import pathlib
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sideboard_deck import DeckState
from sideboard_policy_search import legal_plans,play,protocol_for,schedule
from tournament_bo3_policy import transition


def stub(name,domain=("fury","chaos"),typ="unit",supertype="",tags=None):
    return {"name":name,"card_type":typ,"super_type":supertype,
            "domains":list(domain),"tags":tags or [],"ability_text":"",
            "might":2,"energy_cost":2,"power_cost":0}


class SideboardPolicyResearchTest(unittest.TestCase):
    def setUp(self):
        self.db={
            "Glorious Executioner":stub("Glorious Executioner",typ="legend",tags=["Draven"]),
            "Draven Starting":stub("Draven Starting",supertype="champion",tags=["Draven"]),
            "Draven Alternate":stub("Draven Alternate",supertype="champion",tags=["Draven"]),
        }
        for n in range(13):
            self.db[f"Main {n:02d}"]=stub(f"Main {n:02d}")
        for n in range(3):
            self.db[f"Tech {n:02d}"]=stub(f"Tech {n:02d}",supertype="")
        self.original=DeckState(
            "Draven, Glorious Executioner","Draven Starting",
            collections.Counter({f"Main {i:02d}":3 for i in range(13)}),
            collections.Counter({"Field A":1,"Field B":1,"Field C":1}),
            collections.Counter({"Fury Rune":6,"Chaos Rune":6}),
            collections.Counter({"Draven Alternate":1, "Tech 00":3,
                                 "Tech 01":3,"Tech 02":3}),
        )

    def test_plans_are_registered_legal_and_strict(self):
        candidates=legal_plans(self.original,self.db,3,max_swap_depth=3)
        self.assertGreaterEqual(len(candidates),6)
        singles=[x for x in candidates if len(x["plan"].get("swaps",[]))==1]
        self.assertEqual(len({x["plan"]["swaps"][0]["side_in"] for x in singles}),3)
        self.assertEqual(len({x["plan"]["swaps"][0]["main_out"] for x in singles}),3)
        self.assertTrue(any(len(x["plan"].get("swaps",[]))==2 for x in candidates))
        self.assertTrue(any(len(x["plan"].get("swaps",[]))==3 for x in candidates))
        self.assertTrue(any(x["loser_chooses_start"]=="opponent"
                            for x in candidates))
        self.assertTrue(any(x["plan"].get("chosen_champion")=="Draven Alternate"
                            for x in candidates))
        for choice in candidates:
            transition(self.original,choice["plan"],self.db,game_no=2)
        self.assertEqual(sum(self.original.main.values()),39)

    def test_policy_uses_correct_target_seat_and_identity(self):
        x={"plan":{"swaps":[{"main_out":"Main 00",
                            "side_in":"Tech 00","copies":1}]},
           "loser_chooses_start":"opponent"}
        first=protocol_for(x,0)
        second=protocol_for(x,1)
        self.assertIn("p1",first["game2"])
        self.assertNotIn("p2",first["game2"])
        self.assertIn("p2",second["game3"])
        self.assertEqual(first["game2"]["loser_chooses_start"],"opponent")
        cases=schedule("Draven","LeBlanc",2,2026)
        self.assertEqual(len(cases),4)
        self.assertEqual([r["seat"] for r in cases],[0,0,1,1])
        self.assertEqual(len({r["seed"] for r in cases}),4)

    def test_actual_engine_receipt_gate(self):
        option={"plan":{},"loser_chooses_start":"self"}
        case={"seat":1,"rep":0,"seed":33}
        fake={
            "status":"COMPLETE_RULE407_START_POLICY_BO3",
            "rule_407_4_start_choice_verified":True,
            "winner":2,
            "games":[
                {"game":1,"engine_status":"complete",
                 "previous_game_loser_identity":None,"loser_chose":None,
                 "expected_engine_starting_seat":None,
                 "verified_engine_starting_seat":None},
                {"game":2,"engine_status":"complete",
                 "previous_game_loser_identity":1,"loser_chose":"self",
                 "expected_engine_starting_seat":1,
                 "verified_engine_starting_seat":1},
            ]
        }
        with patch("sideboard_policy_search.run_series",return_value=fake) as mocked:
            row=play(pathlib.Path("engine"),pathlib.Path("target"),
                     pathlib.Path("opponent"),self.db,option,case,"random",12)
        self.assertEqual(row["target_win"],1)
        self.assertEqual(row["forced_start_receipts"][0]["actual"],1)
        self.assertEqual(mocked.call_args.args[1],pathlib.Path("opponent"))
        fake["rule_407_4_start_choice_verified"]=False
        with patch("sideboard_policy_search.run_series",return_value=fake):
            with self.assertRaises(RuntimeError):
                play(pathlib.Path("engine"),pathlib.Path("target"),
                     pathlib.Path("opponent"),self.db,option,case,"random",12)


if __name__=="__main__":
    unittest.main()
