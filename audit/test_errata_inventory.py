import unittest
from xml.etree import ElementTree as ET
from errata_inventory import inventory, norm, EXPECTED
class Tests(unittest.TestCase):
    def fixture(self):
        return {"articles":[{"date":str(i),"url":"fixture","names":[f"card {i}-{j}" for j in range(n)]} for i,n in enumerate(EXPECTED)],"explicit_title_aliases":{}}
    def test_ambiguity_not_certified(self):
        index=self.fixture()
        cards=[{"card_id":i,"public_code":str(i),"name":"card 0-0","ability_text":"","effect_text":""} for i in (1,2)]
        result=inventory(index,{"cards":cards},ET.fromstring("<testsuites/>"))
        self.assertEqual(result["summary"]["multiple_compiled_ids"],1)
        self.assertFalse(result["rows"][0]["behavior_verified"])
        self.assertFalse(result["all_errata_behavior_verified"])
    def test_missing_row_count(self):
        index=self.fixture();index["articles"][0]["names"].pop()
        with self.assertRaises(ValueError):inventory(index,{"cards":[]},ET.fromstring("<testsuites/>"))
    def test_normalization(self):self.assertEqual(norm("Rek’Sai"),norm("Rek'Sai"))
    def test_name_lead_not_behavior(self):
        index=self.fixture()
        xml=ET.fromstring('<testsuites><testcase classname="X" name="Card00" status="run" result="completed"/></testsuites>')
        result=inventory(index,{"cards":[]},xml)
        self.assertTrue(result["rows"][0]["test_name_leads"])
        self.assertFalse(result["rows"][0]["behavior_verified"])
