#!/usr/bin/env python3
"""Constructed 403.4/403.8 and real-engine BO3 orchestration invariants."""
import collections
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sideboard_deck import DeckState, render_deck
from tournament_bo3_policy import (
    cards_pool, check_final_legality, read_policy, run_series, transition,
)


def stub(name,domains,typ="unit",supertype="",tags=None,banned=False):
    return {"name":name,"domains":list(domains),"card_type":typ,
            "super_type":supertype,"tags":tags or [],"ability_text":"",
            "banned":banned}


class SideboardBo3Tests(unittest.TestCase):
    def setUp(self):
        self.db={}
        for tag,title,domain in [
            ("Draven","Glorious Executioner",("fury","chaos")),
            ("LeBlanc","Deceiver",("mind","order")),
        ]:
            self.db[title]=stub(title,domain,"legend",tags=[tag])
            self.db[tag+" Starting"]=stub(
                tag+" Starting",domain,"unit","champion",[tag]
            )
            self.db[tag+" Alternate"]=stub(
                tag+" Alternate",domain,"unit","champion",[tag]
            )
            for n in range(13):
                name=f"{tag} Main {n:02d}"
                self.db[name]=stub(name,domain)
            for n in range(3):
                name=f"{tag} Tech {n:02d}"
                self.db[name]=stub(name,domain)
        self.draven=DeckState(
            "Draven, Glorious Executioner","Draven Starting",
            collections.Counter({f"Draven Main {i:02d}":3 for i in range(13)}),
            collections.Counter({"Field A":1,"Field B":1,"Field C":1}),
            collections.Counter({"Fury Rune":6,"Chaos Rune":6}),
            collections.Counter({"Draven Alternate":1,"Draven Tech 00":3,
                                 "Draven Tech 01":3,"Draven Tech 02":3}),
        )
        self.leblanc=DeckState(
            "LeBlanc, Deceiver","LeBlanc Starting",
            collections.Counter({f"LeBlanc Main {i:02d}":3 for i in range(13)}),
            collections.Counter({"Field D":1,"Field E":1,"Field F":1}),
            collections.Counter({"Mind Rune":6,"Order Rune":6}),
            collections.Counter({"LeBlanc Alternate":1,"LeBlanc Tech 00":3,
                                 "LeBlanc Tech 01":3,"LeBlanc Tech 02":3}),
        )

    def test_game1_sideboarding_forbidden(self):
        with self.assertRaises(ValueError):
            transition(self.draven,{"swaps":[{
                "main_out":"Draven Main 00","side_in":"Draven Tech 00",
                "copies":1}]},self.db,game_no=1)
        with self.assertRaises(ValueError):
            transition(self.draven,{"chosen_champion":"Draven Alternate"},
                       self.db,game_no=1)

    def test_game2_swaps_and_sideboard_champion(self):
        plan={
            "swaps":[{"main_out":"Draven Main 00",
                      "side_in":"Draven Tech 00","copies":2}],
            "chosen_champion":"Draven Alternate"
        }
        state=transition(self.draven,plan,self.db,game_no=2)
        self.assertEqual(state.champion,"Draven Alternate")
        self.assertEqual(state.sideboard["Draven Starting"],1)
        self.assertEqual(state.main["Draven Main 00"],1)
        self.assertEqual(state.main["Draven Tech 00"],2)
        self.assertEqual(cards_pool(state),cards_pool(self.draven))
        self.assertEqual(sum(state.main.values()),39)
        self.assertEqual(sum(state.sideboard.values()),10)
        self.assertEqual(self.draven.champion,"Draven Starting")

    def test_champion_switch_from_main_deck(self):
        original=self.draven.clone()
        original.main["Draven Alternate"]=1
        original.main["Draven Main 00"]-=1
        original.sideboard["Draven Alternate"]-=1
        original.sideboard["Draven Main 00"]+=1
        changed=transition(original,{"chosen_champion":"Draven Alternate"},
                           self.db,game_no=2)
        self.assertEqual(changed.champion,"Draven Alternate")
        self.assertEqual(changed.main["Draven Starting"],1)
        self.assertEqual(cards_pool(changed),cards_pool(original))

    def test_reject_nonmatching_champion_and_duplicate_copies(self):
        with self.assertRaises(ValueError):
            transition(self.draven,{"chosen_champion":"LeBlanc Starting"},
                       self.db,game_no=2)
        illegal=self.draven.clone()
        illegal.sideboard["Draven Main 01"]+=1
        illegal.sideboard["Draven Tech 00"]-=1
        with self.assertRaises(ValueError):
            check_final_legality(illegal,illegal,self.db)
        with self.assertRaises(ValueError):
            transition(self.draven,{"swaps":[{
                "main_out":"Draven Main 00","side_in":"Draven Tech 00",
                "copies":4}]},self.db,game_no=2)

    def test_next_match_restores_original_and_no_pre_game_swap(self):
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)
            a,b=p/"draven.txt",p/"leblanc.txt"
            a.write_text(render_deck(self.draven),encoding="utf-8")
            b.write_text(render_deck(self.leblanc),encoding="utf-8")
            policy={"game2":{"p1":{"swaps":[{
                "main_out":"Draven Main 00","side_in":"Draven Tech 00",
                "copies":1}],"chosen_champion":"Draven Alternate"}},
                "game3":{"p2":{"chosen_champion":"LeBlanc Alternate"}}}
            recorded=[]
            def fake_engine(exe,deck1,deck2,seed,agent,timeout,env):
                recorded.append((deck1.read_text(),deck2.read_text()))
                return {"status":"complete","winner":1,"seconds":0}
            with patch("tournament_bo3_policy.benchmark",side_effect=fake_engine):
                r=run_series(p/"fakeengine",a,b,self.db,policy,
                             "ismcts:sims=24",21,2)
            self.assertEqual(r["status"],"COMPLETE_SIDEBORD_AWARE_APPROXIMATION")
            self.assertEqual(r["winner"],1)
            self.assertEqual(r["score"],[2,1])
            self.assertEqual(len(recorded),3)
            self.assertEqual(recorded[0][0],a.read_text())
            self.assertIn("Draven Tech 00",recorded[1][1])
            self.assertEqual(r["games"][1]["chosen_champions"][0],"Draven Alternate")
            self.assertEqual(r["games"][2]["chosen_champions"][0],"Draven Starting")
            self.assertEqual(r["games"][2]["chosen_champions"][1],"LeBlanc Alternate")
            self.assertEqual(a.read_text(),render_deck(self.draven))
            self.assertEqual(b.read_text(),render_deck(self.leblanc))

    def test_engine_error_is_never_counted_as_loss(self):
        with tempfile.TemporaryDirectory() as td:
            root=pathlib.Path(td)
            a=root/"d.txt";b=root/"l.txt"
            a.write_text(render_deck(self.draven))
            b.write_text(render_deck(self.leblanc))
            with patch("tournament_bo3_policy.benchmark",
                       return_value={"status":"error","winner":None,"error":"failure"}):
                result=run_series(root/"fake",a,b,self.db,{},"random",19)
            self.assertEqual(result["status"],"INCOMPLETE")
            self.assertIsNone(result["winner"])
            self.assertEqual(len(result["games"]),1)


if __name__=="__main__":
    unittest.main()
