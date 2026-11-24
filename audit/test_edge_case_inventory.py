import unittest
from edge_case_inventory import inventory,BARON
class Tests(unittest.TestCase):
    def test_names_not_proof(self):
        ledger={"entries":[{"engine_id":1,"print_ids":["RAD-001/167"],"name":"Brawl",
                  "known_gaps":["cost"],"historical_test_name_links":[{"enabled_test_matches":["RadianceTest.BrawlCost"]}],
                  "scenario_test_ids":[],"interaction_test_ids":[]}]}
        xml=b'<testsuites><testsuite><testcase classname="RadianceTest" name="BrawlCost" status="run" result="completed"/><testcase classname="RadianceTest" name="BrawlOther" status="run" result="completed"><failure/></testcase><testcase classname="Other" name="YetiBrawler" status="run" result="completed"/></testsuite></testsuites>'
        r=inventory(ledger,xml);q=r["questions"][0]
        self.assertFalse(q["behavior_verified"]);self.assertEqual(r["closed_questions"],0)
        self.assertEqual([l["result"] for l in q["leads"]],["enabled_pass","not_passing"])
        self.assertEqual(r["xml_counts"]["not_passing"],1)
    def test_disabled_not_pass(self):
        xml=b'<testsuites><testsuite><testcase classname="CardTestFixture" name="DISABLED_BaronNashor_AuraGivesFriendlyUnitsPlus2M" status="notrun" result="suppressed"/></testsuite></testsuites>'
        self.assertEqual(inventory({"entries":[]},xml)["baron"]["status"],"disabled")
    def test_duplicate_rejected(self):
        x='<testcase classname="A" name="B" status="run" result="completed"/>'
        with self.assertRaises(ValueError):inventory({"entries":[]},("<testsuites>"+x+x+"</testsuites>").encode())
