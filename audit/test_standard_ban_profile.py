import unittest
from standard_ban_profile import audit, indexes, scan_registration

PROFILE = {"schema_version":1,"profile_id":"test",
           "ban_entries":[{"code":"A","engine_id":1,"name":"The Tree",
                           "type":"battlefield","aliases":["Tree"]},
                          {"code":"B","engine_id":2,"name":"Zhonya's Gear",
                           "type":"gear","aliases":[]}]}
REGISTRY = {"cards":[{"public_code":"A","card_id":1,"name":"The Tree",
                      "card_type":"battlefield","banned":False},
                     {"public_code":"B","card_id":2,"name":"Zhonya's Gear",
                      "card_type":"gear","banned":True}]}


class BanAuditTests(unittest.TestCase):
    def test_native_discrepancy_explicit(self):
        r = audit(PROFILE, REGISTRY, {})
        self.assertFalse(r["native_enforcement_matches"])
        self.assertEqual([x["code"] for x in r["missing_native_bans"]], ["A"])
        self.assertFalse(r["complete_legality_verified"])

    def test_alias_apostrophe_print_id_and_sections(self):
        names,_ = indexes(PROFILE,REGISTRY)
        text = "Legend:\n1 L\nChampion:\n1 C\nMainDeck:\n1 Zhonya’s Gear #42\nBattlefields:\n1 Tree\nRunes:\n1 R\nSideboard:\n2 Zhonya's Gear\n"
        self.assertEqual([(x["section"],x["code"]) for x in scan_registration(text,names)],
                         [("MainDeck","B"),("Battlefields","A"),("Sideboard","B")])

    def test_wrong_registry_identity_rejected(self):
        with self.assertRaises(ValueError):
            indexes(PROFILE,{"cards":[{**REGISTRY["cards"][0],"card_id":9},REGISTRY["cards"][1]]})

    def test_missing_section_rejected(self):
        with self.assertRaises(ValueError):
            scan_registration("Legend:\n1 L",{})

    def test_duplicate_code_rejected(self):
        with self.assertRaises(ValueError):
            indexes(PROFILE,{"cards":REGISTRY["cards"]+[REGISTRY["cards"][0]]})

    def test_alias_not_substring(self):
        names,_ = indexes(PROFILE,REGISTRY)
        text = "Legend:\n1 L\nChampion:\n1 C\nMainDeck:\n1 Tree Walker\nBattlefields:\n1 Other\nRunes:\n1 R\nSideboard:\n"
        self.assertEqual(scan_registration(text,names),[])


if __name__ == "__main__":
    unittest.main()
