#!/usr/bin/env python3
"""All four registered structural deck modes, copy cap and native-test guards."""
import collections
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from sideboard_deck import DeckState,parse_deck,render_deck
from structural_deck_population import (
    legal_registration,rune_variants,battlefield_variants,
    sideboard_variants,chosen_champion_variants,generate_one
)


def c(name,kind="unit",domains=("fury","chaos"),supertype="",tags=(),banned=False):
    return {"name":name,"card_type":kind,"domains":list(domains),
            "super_type":supertype,"tags":list(tags),"banned":banned,
            "ability_text":"","energy_cost":2,"power_cost":0}


class StructuralDeckTest(unittest.TestCase):
    def setUp(self):
        self.db={
            "Glorious Executioner":c(
                "Glorious Executioner",kind="legend",tags=("Draven",)),
            "Draven Starting":c(
                "Draven Starting",supertype="champion",tags=("Draven",)),
            "Draven Alternate":c(
                "Draven Alternate",supertype="champion",tags=("Draven",)),
            "Fury Rune":c("Fury Rune",kind="rune",domains=("fury",)),
            "Chaos Rune":c("Chaos Rune",kind="rune",domains=("chaos",)),
        }
        for i in range(13):
            name=f"Main {i:02d}"
            self.db[name]=c(name)
        for i in range(3):
            name=f"Tech {i:02d}"
            self.db[name]=c(name)
        for i in range(8):
            name=f"Spare {i:02d}"
            self.db[name]=c(name)
        for i in range(12):
            name=f"Field {i:02d}"
            self.db[name]=c(name,kind="battlefield",domains=())
        self.db["Illegal Field"]=c(
            "Illegal Field",kind="battlefield",domains=(),banned=True)
        self.db["Baron Pit"]=c(
            "Baron Pit",kind="battlefield",domains=(),supertype="token")
        self.db["Neeko, Blending In"]=c(
            "Neeko, Blending In",domains=(),supertype="champion")
        self.source=DeckState(
            "Draven, Glorious Executioner","Draven Starting",
            collections.Counter({f"Main {i:02d}":3 for i in range(13)}),
            collections.Counter({"Field 00":1,"Field 01":1,"Field 02":1}),
            collections.Counter({"Fury Rune":6,"Chaos Rune":6}),
            collections.Counter({"Draven Alternate":1,
                                 "Tech 00":3,"Tech 01":3,"Tech 02":3}),
        )

    def test_each_structural_family_preserves_native_constructed_conditions(self):
        variants=[
            ("rune",list(rune_variants(self.source,self.db))),
            ("battlefield",list(battlefield_variants(
                self.source,self.db,2026))),
            ("sideboard",list(sideboard_variants(
                self.source,self.db,2026))),
            ("champion",list(chosen_champion_variants(
                self.source,self.db))),
        ]
        self.assertEqual(len(variants[0][1]),4)
        self.assertEqual(len(variants[1][1]),3)
        self.assertEqual(len(variants[2][1]),3)
        self.assertEqual(len(variants[3][1]),1)
        for label,options in variants:
            for variant,state,detail in options:
                legal_registration(self.source,state,self.db)
                self.assertEqual(state.legend,self.source.legend)
                self.assertEqual(state.main if label!="champion" else
                                 sum(state.main.values()),self.source.main
                                 if label!="champion" else 39)
                self.assertEqual(sum(state.runes.values()),12)
                self.assertEqual(sum(state.battlefields.values()),3)
                self.assertEqual(sum(state.sideboard.values()),10)
                self.assertEqual(len(parse_deck(render_deck(state)).runes),
                                 len(state.runes))
        self.assertEqual(self.source.champion,"Draven Starting")
        self.assertEqual(self.source.sideboard["Draven Alternate"],1)

    def test_banned_and_duplicate_battlefield_rune_copy_fails_closed(self):
        mutated=self.source.clone()
        mutated.battlefields["Field 00"]=2
        mutated.battlefields.pop("Field 01")
        with self.assertRaises(ValueError):
            legal_registration(self.source,mutated,self.db)
        mutated=self.source.clone()
        mutated.battlefields.pop("Field 00")
        mutated.battlefields["Illegal Field"]=1
        with self.assertRaises(ValueError):
            legal_registration(self.source,mutated,self.db)
        mutated=self.source.clone()
        mutated.battlefields.pop("Field 00")
        mutated.battlefields["Baron Pit"]=1
        with self.assertRaises(ValueError):
            legal_registration(self.source,mutated,self.db)
        self.assertTrue(all("Baron Pit" not in row[2].values()
                            for row in battlefield_variants(self.source,self.db,2026)))
        mutated=self.source.clone()
        mutated.runes=collections.Counter({"Chaos Rune":12})
        legal_registration(self.source,mutated,self.db)
        mutated.runes=collections.Counter({"Not A Rune":12})
        with self.assertRaises(ValueError):
            legal_registration(self.source,mutated,self.db)

    def test_all_types_are_hashed_and_unadopted(self):
        with tempfile.TemporaryDirectory() as td:
            d=pathlib.Path(td)
            src=d/"draven_glorious_executioner.txt"
            src.write_text(render_deck(self.source))
            out=d/"out"
            row=generate_one("Draven, Glorious Executioner",
                             src,self.db,out,20261125)
            self.assertEqual(row["count"],11)
            self.assertEqual(set(row["types"]),
                             {"rune","battlefield","sideboard","champion"})
            self.assertTrue(all(not r["native_engine_simulated"]
                                and not r["fitness_evaluated"]
                                for r in row["variants"]))
            self.assertEqual(row["original_sha256"].__len__(),64)


if __name__=="__main__":
    unittest.main()
