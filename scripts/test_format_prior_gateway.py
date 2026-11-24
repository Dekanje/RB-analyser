import unittest
from types import SimpleNamespace
from format_prior_gateway import prior_ids,prior_text,verify_prior,FormatRejected
class Tests(unittest.TestCase):
    def test_public_filter(self):
        def card(name,set_,banned=False,super_type=None):
            return {"name":name,"set":set_,"banned":banned,"super_type":super_type}
        gate=SimpleNamespace(ids={1:card("A","OGN"),2:card("B","OGS"),3:card("C","OGN"),
            4:card("C","OGN"),5:card("D","OGN",True),6:card("E","OGN",False,"token"),7:card("Rune","OGS")},
            sets={"OGN"},exempt={7},banned={3},banned_names={"c"})
        self.assertEqual(prior_ids(gate),[1,7])
        self.assertEqual(prior_text(gate),"1,7")
    def test_receipt_fail_closed(self):
        verify_prior("FORMAT_PRIOR_IDS=1,7\n","1,7")
        for s in ("","FORMAT_PRIOR_IDS=7,1\n","FORMAT_PRIOR_IDS=1,7\nFORMAT_PRIOR_IDS=1,7\n"):
            with self.assertRaises(FormatRejected):verify_prior(s,"1,7")
