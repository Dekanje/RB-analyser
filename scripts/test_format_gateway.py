import unittest
from format_gateway import FormatGate, FormatRejected

def card(i,name,kind,set_="RAD",banned=False,tags=(),super_type=None):
    return dict(card_id=i,public_code=f"X{i}",name=name,card_type=kind,set=set_,
                banned=banned,tags=list(tags),super_type=super_type)

CARDS=[card(1,"Title","legend",tags=["Hero"]),card(2,"Hero, Chosen","unit"),
       card(3,"Main","unit"),card(4,"Field","battlefield"),card(5,"Rune","rune","OGN"),
       card(6,"Banned Field","battlefield"),card(7,"Banned Unit","unit"),
       card(8,"Main","unit","OGN"),card(9,"Token","unit",super_type="token")]
PROFILE=dict(schema_version=1,format="standard_constructed_1v1",
             ban_entries=[dict(code=f"X{i}",engine_id=i,name=CARDS[i-1]["name"],
                               type=CARDS[i-1]["card_type"],aliases=[])
                          for i in (6,7)])

def gate(sets=("RAD","OGN"),exempt=()):
    return FormatGate(PROFILE,{"cards":CARDS},sets,exempt)

def deck(main="39 Main #3",bf="3 Field",champ="1 Hero, Chosen",side=""):
    return f"Legend:\n1 Hero, Title\nChampion:\n{champ}\nMainDeck:\n{main}\nBattlefields:\n{bf}\nRunes:\n12 Rune\nSideboard:\n{side}\n".encode()

class FormatTests(unittest.TestCase):
    def test_explicit_and_legend_alias(self):
        self.assertEqual(gate().validate(deck())["Legend"],[1])
    def test_banned_battlefield(self):
        with self.assertRaisesRegex(FormatRejected,"banned"):
            gate().validate(deck(bf="3 Banned Field"))
    def test_banned_champion(self):
        with self.assertRaisesRegex(FormatRejected,"banned"):
            gate().validate(deck(champ="1 Banned Unit"))
    def test_banned_main_and_side(self):
        for raw in (deck(main="39 Banned Unit"),deck(side="1 Banned Unit #7")):
            with self.assertRaisesRegex(FormatRejected,"banned"):
                gate().validate(raw)
    def test_ambiguous_name_and_wrong_id(self):
        for main in ("39 Main","39 Main #4"):
            with self.assertRaises(FormatRejected):
                gate().validate(deck(main=main))
    def test_set_exclusion_and_rune_exemption(self):
        with self.assertRaisesRegex(FormatRejected,"set excluded"):
            gate(("RAD",)).validate(deck())
        self.assertEqual(gate(("RAD",),(5,)).validate(deck())["Runes"],[5]*12)
        with self.assertRaisesRegex(FormatRejected,"set excluded"):
            gate(("RAD",),(5,)).validate(deck(main="39 Main #8"))
    def test_nonrune_exemption_rejected(self):
        with self.assertRaises(FormatRejected):
            gate(("RAD",),(8,))
    def test_token_rejected(self):
        with self.assertRaisesRegex(FormatRejected,"token"):
            gate().validate(deck(main="39 Token"))
    def test_unknown_and_wrong_section(self):
        for raw in (deck(side="1 Unknown"),deck(side="1 Field")):
            with self.assertRaises(FormatRejected):
                gate().validate(raw)
    def test_counts_and_sections(self):
        for raw in (deck(main="38 Main #3"),deck().replace(b"Runes:",b"Extra:")):
            with self.assertRaises(FormatRejected):
                gate().validate(raw)
    def test_native_unban_incompatible(self):
        cards=[{**c,"banned":True} if c["card_id"]==3 else c for c in CARDS]
        with self.assertRaisesRegex(FormatRejected,"unban"):
            FormatGate(PROFILE,{"cards":cards},("RAD",))

if __name__=="__main__":
    unittest.main()
