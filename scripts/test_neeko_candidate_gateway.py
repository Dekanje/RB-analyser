import unittest
from neeko_candidate_gateway import NeekoGate,receipt_v3,EXTRA
from format_gateway import FormatRejected
from format_match_v2 import transition

def card(i,name,kind,set_code="RAD"):
    return {"card_id":i,"card_def_id":"id"+str(i),"public_code":"code"+str(i),
            "name":name,"card_type":kind,"set":set_code,"banned":False,
            "tags":[],"super_type":""}
CARDS=[card(1,"Start","legend"),card(2,"Other","legend"),card(3,"OtherTwo","legend"),
       card(4,"OtherThree","legend"),card(5,"OtherFour","legend"),
       card(6,"Champion","unit"),card(7,"Main","unit"),card(8,"Field","battlefield"),
       card(9,"Rune","rune"),card(10,"Legacy","legend","OGS"),card(1131,"Neeko","unit")]
PROFILE={"schema_version":1,"format":"standard_constructed_1v1","ban_entries":[]}
RAW=b"Legend:\n1 Start\nChampion:\n1 Champion\nMainDeck:\n39 Main\nBattlefields:\n3 Field\nRunes:\n12 Rune\nSideboard:\n1 Neeko\n"
def extra(*rows):return RAW+("NeekoLegends:\n"+"\n".join(rows)+"\n").encode()
class Tests(unittest.TestCase):
    def setUp(self):self.g=NeekoGate(PROFILE,{"cards":CARDS},("RAD",))
    def test_optional_cardinality(self):
        rows=["1 Other","1 OtherTwo","1 OtherThree"]
        self.assertEqual(self.g.validate(RAW)[EXTRA],[])
        for n in range(4):self.assertEqual(self.g.validate(extra(*rows[:n]))[EXTRA],list(range(2,2+n)))
    def test_invalid_extras(self):
        for rows in [("1 Start",),("1 Other","1 Other"),("1 Other","1 OtherTwo","1 OtherThree","1 OtherFour"),
                     ("1 Main",),("1 Legacy",),("2 Other",),("1 Other #3",),("NeekoLegends:",)]:
            with self.subTest(rows=rows),self.assertRaises(FormatRejected):self.g.validate(extra(*rows))
    def test_no_neeko(self):
        with self.assertRaises(FormatRejected):self.g.validate(extra("1 Other").replace(b"1 Neeko\n",b""))
    def test_ban_alias(self):
        p={**PROFILE,"ban_entries":[{"code":"code2","engine_id":2,"name":"Other","type":"legend","aliases":[]}]}
        with self.assertRaises(FormatRejected):NeekoGate(p,{"cards":CARDS},("RAD",)).validate(extra("1 Other"))
    def test_transition_preserves_registration(self):
        v=self.g.validate(extra("1 OtherTwo","1 Other"))
        out=transition(v,{"swaps":[{"main_out":7,"side_in":1131,"copies":1}]})
        self.assertEqual(out[EXTRA],[3,2]);self.assertIn(1131,out["MainDeck"])
        self.assertEqual(transition(out,{"swaps":[{"main_out":1131,"side_in":7,"copies":1}]} )["NeekoLegends"],[3,2])
    def test_receipt(self):
        s="[DECK] P1 (a):\n    neeko_count 2\n    neeko [id3] OtherTwo\n    neeko [id2] Other\n[DECK] P2 (b):\n    neeko_count 0\n"
        d={"id2":2,"id3":3}
        self.assertEqual([v[EXTRA] for v in receipt_v3(s,d)],[[3,2],[]])
        for bad in [s.replace("neeko_count 2","neeko_count 1"),s.replace("    neeko_count 0\n",""),s.replace("[id2]","[bad]"),s.replace("neeko_count 2","neeko_count 2\n    neeko_count 2")]:
            with self.assertRaises(FormatRejected):receipt_v3(bad,d)
