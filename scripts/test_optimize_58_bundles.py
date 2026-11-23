#!/usr/bin/env python3
"""Pure-Python invariants for expanded two-card Radiance deck proposals."""
import collections
import hashlib
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
import optimize_58 as opt


def card(name, might=1, ability_text=""):
    return {"name":name,"card_type":"unit","domains":[],"energy_cost":1,
            "power_cost":0,"might":might,"super_type":"","ability_text":ability_text,
            "tags":[]}


class BundleProposalTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name)
        self.source=self.root/"source.txt"
        self.old=[f"Core {n:02d}" for n in range(13)]
        self.new=[f"Upgrade {n:02d}" for n in range(15)]
        self.cards={x:card(x) for x in self.old}
        self.cards.update({x:card(x,10+n) for n,x in enumerate(self.new)})
        self.pop=collections.Counter()
        self.write_source()

    def write_source(self, side=""):
        text=("Legend:\n1 Test, Two Cards\n\nChampion:\n1 Test, Champion\n\n"
              "MainDeck:\n"+ "\n".join("3 "+x for x in self.old) +
              "\n\nBattlefields:\n1 Test Arena\n\nSideboard:\n"+
              side+"\n")
        self.source.write_text(text,encoding="utf-8")

    def proposals(self, n=12, bundles=4):
        with patch.object(opt,"effective_domains",return_value=set()):
            return opt.propose("Test, Two Cards",self.source,self.cards,
                               self.pop,n,12345,bundles=bundles)

    def test_bundles_are_different_from_singles_and_rules_legal(self):
        digest=hashlib.sha256(self.source.read_bytes()).hexdigest()
        results=self.proposals()
        self.assertEqual(len(results),12)
        self.assertEqual(sum(len(c["swap_sequence"])==2 for c in results),4)
        self.assertEqual(sum(len(c["swap_sequence"])==1 for c in results),8)
        for index,c in enumerate(results):
            candidate=self.root/f"candidate{index}.txt"
            candidate.write_text(c["text"],encoding="utf-8")
            _,counts,_=opt.parse_deck(candidate)
            self.assertEqual(sum(counts.values()),39)
            self.assertTrue(all(1<=q<=3 for q in counts.values()))
            self.assertEqual(len({s["remove"] for s in c["swap_sequence"]}),
                             len(c["swap_sequence"]))
            self.assertEqual(len({s["add"] for s in c["swap_sequence"]}),
                             len(c["swap_sequence"]))
            for s in c["swap_sequence"]:
                self.assertEqual(counts[s["remove"]],2)
                self.assertEqual(counts[s["add"]],1)
        self.assertEqual(digest,hashlib.sha256(self.source.read_bytes()).hexdigest())

    def test_legacy_single_card_mode_and_forbidden_cards(self):
        self.cards["Zhonya's Hourglass"]=card("Zhonya's Hourglass",99)
        results=self.proposals(n=6,bundles=0)
        self.assertEqual(len(results),6)
        self.assertTrue(all(len(x["swap_sequence"])==1 for x in results))
        self.assertFalse(any("Zhonya's Hourglass" in x["add"] for x in results))

    def test_candidate_selection_retains_full_swap_audit_trail(self):
        # Selection passes through the screening/training records. This was
        # omitted in the initial expanded run, causing a KeyError on acceptance.
        import inspect
        source=inspect.getsource(opt.main)
        self.assertIn("'swap_sequence':cand['swap_sequence']",source)
        self.assertIn("for step in r['selected']['swap_sequence']",source)
        generated=self.proposals()
        for candidate in generated:
            trial={'remove':candidate['remove'],'add':candidate['add'],
                   'swap_sequence':candidate['swap_sequence']}
            accepted=[{'round':1,'selected':trial}]
            swaps=[{'round':r['round'],**step}
                   for r in accepted if r['selected']
                   for step in r['selected']['swap_sequence']]
            self.assertEqual(swaps,[{'round':1,**step} for step in candidate['swap_sequence']])

    def test_unique_sideboard_card_cannot_be_added_again(self):
        self.cards[self.new[0]]["ability_text"]="[Unique]"
        self.write_source(side="1 "+self.new[0])
        results=self.proposals()
        self.assertTrue(results)
        self.assertFalse(any(self.new[0] in s["add"] for c in results
                             for s in c["swap_sequence"]))


if __name__=="__main__":
    unittest.main(verbosity=2)
