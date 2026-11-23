#!/usr/bin/env python3
"""Fail-closed actual-407 sideboard-only candidate fitness tests."""
import collections
import pathlib
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))

from sideboard_deck import DeckState
from structural_sideboard_174 import (
    KIND,COUNT,deterministic_sideboard_plan,case_schedule,
    play,paired_score,
)
from tournament_bo3_policy import transition


def stub(name,domains=("fury","chaos"),kind="unit",supertype="",tags=None):
    return {"name":name,"card_type":kind,"super_type":supertype,
            "domains":list(domains),"tags":tags or [],"banned":False,
            "energy_cost":1,"power_cost":0,"might":2,"ability_text":""}


class Sideboard174ActualNativeTests(unittest.TestCase):
    def setUp(self):
        self.db={
            "Glorious Executioner":stub("Glorious Executioner",
                                          kind="legend",tags=["Draven"]),
            "Draven Starting":stub("Draven Starting",
                                    supertype="champion",tags=["Draven"]),
        }
        for n in range(13):
            self.db[f"Main {n:02d}"]=stub(f"Main {n:02d}")
        for n in range(5):
            self.db[f"Tech {n:02d}"]=stub(f"Tech {n:02d}")
        self.base=DeckState(
            "Draven, Glorious Executioner","Draven Starting",
            collections.Counter({f"Main {i:02d}":3 for i in range(13)}),
            collections.Counter({"Battlefield A":1,"Battlefield B":1,
                                 "Battlefield C":1}),
            collections.Counter({"Fury Rune":6,"Chaos Rune":6}),
            collections.Counter({"Tech 00":3,"Tech 01":3,"Tech 02":3,
                                 "Tech 04":1}),
        )
        # Each candidate is a legal sideboard-only swap at fixed 10-card size.
        self.changed=self.base.clone()
        self.changed.sideboard["Tech 04"]-=1
        self.changed.sideboard["Tech 03"]+=1
        self.changed.sideboard=+self.changed.sideboard
        self.db["Tech 03"]["might"]=4

    def test_force_specific_new_card_into_game2_and_game3(self):
        with patch("structural_sideboard_174.card_score",
                   side_effect=lambda c,*args: c.get("might",0)):
            base_plan=deterministic_sideboard_plan(self.base,self.db)
            changed_plan=deterministic_sideboard_plan(
                self.changed,self.db,require_in="Tech 03")
        self.assertEqual(changed_plan["side_in"],"Tech 03")
        self.assertEqual(changed_plan["plan"]["swaps"][0]["copies"],1)
        transition(self.changed,changed_plan["plan"],self.db,game_no=2)
        transition(self.base,base_plan["plan"],self.db,game_no=2)
        self.assertEqual(sum(self.base.main.values()),39)
        with self.assertRaises(RuntimeError):
            deterministic_sideboard_plan(self.base,self.db,
                                         require_in="Does Not Exist")

    def test_native_swap_receipt_is_mandatory_and_player_seat_is_correct(self):
        chosen={"plan":{"swaps":[{"main_out":"Main 00","side_in":"Tech 03",
                                  "copies":1}]},
                "side_in":"Tech 03","main_out":"Main 00"}
        case={"opponent":"LeBlanc","seat":1,"seed":357}
        outcome={
            "status":"COMPLETE_RULE407_START_POLICY_BO3",
            "rule_407_4_start_choice_verified":True,
            "winner":2,"sideboarding_applied":True,
            "source_decks_return_to_registered_state_next_match":True,
            "games":[
                {"game":1,"engine_status":"complete","winner_seat":1},
                {"game":2,"engine_status":"complete",
                 "sideboard_swaps":[[],chosen["plan"]["swaps"]],
                 "forced_start_verified":True,
                 "verified_engine_starting_seat":1,
                 "expected_engine_starting_seat":1}
            ]
        }
        a=SimpleNamespace(engine=pathlib.Path("engine"),agent="random",timeout=3)
        with patch("structural_sideboard_174.run_series",return_value=outcome) as f:
            result=play(a,pathlib.Path("target"),pathlib.Path("enemy"),
                        case,self.db,chosen)
        self.assertEqual(result["target_win"],1)
        self.assertEqual(result["actual_swaps"],1)
        self.assertEqual(f.call_args.args[1],pathlib.Path("enemy"))
        self.assertEqual(f.call_args.args[2],pathlib.Path("target"))
        outcome["games"][1]["sideboard_swaps"]=[[],[]]
        with patch("structural_sideboard_174.run_series",return_value=outcome):
            with self.assertRaises(RuntimeError):
                play(a,pathlib.Path("target"),pathlib.Path("enemy"),
                     case,self.db,chosen)

    def test_paired_evidence_and_arithmetic(self):
        rows=[{"baseline_win":a,"candidate_win":b}
              for a,b in [(0,1),(1,0),(0,0),(1,1)]]
        z=paired_score(rows)
        self.assertEqual(z["delta"],0)
        self.assertEqual(z["candidate_only"],1)
        self.assertEqual(z["baseline_only"],1)
        with self.assertRaises(RuntimeError):
            paired_score(rows[:-1])
        self.assertEqual(COUNT,174)
        self.assertEqual(KIND,"sideboard")
        schedule=case_schedule("Draven",[
            {"legend":"LeBlanc"},{"legend":"Rek'Sai"},{"legend":"Draven"}
        ],2026)
        self.assertEqual(len(schedule),4)
        self.assertEqual(len({p["seed"] for p in schedule}),4)


if __name__=="__main__":
    unittest.main()
