import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from approved_format import APPROVED, CONFIG_ROOT, load_configuration, ApprovedGateway
from format_match_v2 import FormatRejected, VerifiedGateway

class ConfigTests(unittest.TestCase):
    def test_exact_approved_files(self):
        for key,h in APPROVED.items():
            d,actual=load_configuration(key)
            self.assertEqual(actual,h)
            self.assertEqual(d["configuration_id"],key)
            self.assertFalse(d["official_full_legality_certified"])

    def test_unknown_id(self):
        for key in ("worlds-no-legacy","../outside",""):
            with self.assertRaises(FormatRejected):
                load_configuration(key)

    def test_modified_config_refused(self):
        key=next(iter(APPROVED))
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/(key+".json")
            p.write_bytes((CONFIG_ROOT/p.name).read_bytes()+b" ")
            with self.assertRaisesRegex(FormatRejected,"configuration bytes"):
                load_configuration(key,tmp)

    def test_named_policy_difference(self):
        a,_=load_configuration("standard-2026-11-23-research-v1")
        b,_=load_configuration("hypothetical-exclude-ogs-v1")
        self.assertEqual(set(a["allowed_sets"])-set(b["allowed_sets"]),{"OGS"})
        self.assertEqual(b["classification"],"hypothetical_set_filter")

    def test_gateway_inherits_pins_and_receipts(self):
        with patch.object(VerifiedGateway,"__init__",return_value=None) as init, \
             patch.object(VerifiedGateway,"provenance",return_value={"full_official_legality_certified":False}):
            g=ApprovedGateway("engine","registry","profile","hypothetical-exclude-ogs-v1")
            init.assert_called_once_with("engine","registry","profile",
                                         ("OGN","SFD","UNL","VEN","RAD"),())
            p=g.provenance()
            self.assertEqual(p["configuration_sha256"],APPROVED["hypothetical-exclude-ogs-v1"])
            self.assertFalse(p["full_official_legality_certified"])

if __name__=="__main__":
    unittest.main()
