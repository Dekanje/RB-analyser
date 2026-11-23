#!/usr/bin/env python3
"""Deterministic tests for broad search, bans, signature and copy constraints."""
import collections
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from evolutionary_candidates import (
    generate_candidate, playable_pool, validate_main,
    registered_neeko_deck,
)

def card(name, kind="unit", cost=2, supertype=None, domains=None,
         text="", banned=False, tags=None):
    return {
        "name": name, "card_type": kind, "energy_cost": cost,
        "power_cost": 0, "super_type": supertype,
        "domains": domains or ["fury"], "ability_text": text,
        "banned": banned, "tags": tags or ["Team"],
        "might": 2, "features": {},
    }


class EvolutionaryCandidateTests(unittest.TestCase):
    def setUp(self):
        names = [f"Original {n:02d}" for n in range(13)]
        self.main = collections.Counter({n:3 for n in names})
        self.side = collections.Counter({"Side Unit":2})
        self.byname = {n:card(n) for n in names}
        self.byname["Original 00"]["super_type"] = "Signature"
        self.byname.update({f"New Card {i:02d}":card(f"New Card {i:02d}")
                            for i in range(30)})
        self.byname["Side Unit"] = card("Side Unit")
        self.byname["Unique New"] = card("Unique New",text="[Unique] Test")
        self.byname["Banned New"] = card("Banned New",banned=True)
        self.byname["Off Domain"] = card("Off Domain", domains=["calm"])
        self.byname["Signature New"] = card("Signature New",supertype="Signature")
        self.byname["Neeko, Blending In"] = card(
            "Neeko, Blending In",supertype="champion",domains=[])
        for name in ("Loose Cannon","Nine-Tailed Fox","Blind Monk",
                     "Relentless Storm"):
            self.byname[name]=card(name,kind="legend",domains=[])
        self.domains = {"fury"}
        self.pop = collections.Counter(self.main)
        self.pool = playable_pool(self.byname,self.domains)

    def test_legal_pool_filters_prohibited_entries(self):
        names = {c["name"] for c in self.pool}
        for disallowed in ("Banned New","Off Domain","Signature New"):
            self.assertNotIn(disallowed,names)
        self.assertIn("Neeko, Blending In",names)
        self.assertIn("Unique New", names)
        self.assertIn("New Card 01", names)

    def test_validate_unique_sideboard_and_signature(self):
        validate_main(self.main,self.main.copy(),self.side,self.byname,self.domains)
        other = self.main.copy()
        other["Original 01"] -= 2
        other["Side Unit"] += 2
        with self.assertRaises(ValueError):
            validate_main(self.main,other,self.side,self.byname,self.domains)
        other = self.main.copy()
        other["Original 01"] -= 1
        other["Signature New"] += 1
        with self.assertRaises(ValueError):
            validate_main(self.main,other,self.side,self.byname,self.domains)
        other = self.main.copy()
        other["Original 00"] -= 1
        other["New Card 01"] += 1
        with self.assertRaises(ValueError):
            validate_main(self.main,other,self.side,self.byname,self.domains)

    def test_multi_card_exploration_is_reproducible(self):
        result1 = generate_candidate(
            self.main, self.side, self.byname, self.domains,
            self.pool, 113, 3, 8, self.pop
        )
        result2 = generate_candidate(
            self.main, self.side, self.byname, self.domains,
            self.pool, 113, 3, 8, self.pop
        )
        self.assertIsNotNone(result1)
        self.assertEqual(result1,result2)
        main, steps = result1
        self.assertGreaterEqual(len(steps),3)
        self.assertGreaterEqual(len(steps),3)
        self.assertEqual(sum(main.values()),39)
        self.assertEqual(main["Original 00"],3)
        self.assertNotIn("Banned New",main)
        self.assertNotIn("Off Domain",main)
        validate_main(self.main,main,self.side,self.byname,self.domains)

    def test_neeko_registration_always_supplies_three_different_legends(self):
        original = ("Legend:\n1 Jinx, Loose Cannon\n\n"
                    "Champion:\n1 Jinx, Supercharged\n\n"
                    "MainDeck:\n39 Base\n\nBattlefields:\n1 A\n1 B\n1 C\n\n"
                    "Runes:\n12 Rune\n\nSideboard:\n")
        counts = collections.Counter({"Base":38,"Neeko, Blending In":1})
        output, chosen = registered_neeko_deck(
            original,counts,"Jinx, Loose Cannon",self.byname
        )
        self.assertEqual(chosen,["Nine-Tailed Fox","Blind Monk",
                                 "Relentless Storm"])
        self.assertIn("NeekoLegends:\n1 Nine-Tailed Fox\n1 Blind Monk\n"
                      "1 Relentless Storm\n",output)
        self.assertNotIn("1 Loose Cannon\n",output.split("NeekoLegends:")[1])
        output2, chosen2=registered_neeko_deck(
            original,collections.Counter({"Base":39}),
            "Jinx, Loose Cannon",self.byname
        )
        self.assertEqual(chosen2,[])
        self.assertNotIn("NeekoLegends",output2)

    def test_different_random_seeds_generate_diversity(self):
        seen = set()
        for seed in range(40):
            answer=generate_candidate(self.main,self.side,self.byname,self.domains,
                                     self.pool,seed,3,8,self.pop)
            if answer:
                counts,steps=answer
                seen.add(tuple(sorted(counts.items())))
        self.assertGreaterEqual(len(seen),15)


if __name__ == "__main__":
    unittest.main()
