import unittest
from check_champion_multiswap import verify_control,MF,KEN
from format_match_v2 import transition,FormatRejected
def reg(champion,main,side):
    return {"Champion":[champion],"MainDeck":main,"Sideboard":side,"Legend":[1],"Battlefields":[2,3,4],"Runes":[5]*12,"NeekoLegends":[]}
class Tests(unittest.TestCase):
    def setUp(self):
        self.regs=[reg(193,[162,981,981,668,99],[444,444,180]),reg(900,[922,444,444,99],[483,922,481,481])]
        self.vs=[transition(self.regs[0],MF),transition(self.regs[1],KEN)]
    def test_control(self):
        verify_control(self.regs,self.vs)
    def test_fixed_zone_drift(self):
        self.vs[0]["Runes"][0]=6
        with self.assertRaises(FormatRejected):verify_control(self.regs,self.vs)
    def test_wrong_champion_provenance(self):
        self.vs[1]["Sideboard"].remove(900);self.vs[1]["MainDeck"].append(900)
        with self.assertRaises(FormatRejected):verify_control(self.regs,self.vs)
