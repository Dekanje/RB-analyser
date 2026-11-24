import unittest
from p0_05_agent_evidence import audit, stable_seed

class AuditTests(unittest.TestCase):
    def rows(self):
        return [{"deck_file":"a","repetition":0,"challenger_first":s,"seed":stable_seed(1,"a",0),
                 "deck_sha256":"hash","status":"complete","winner_seat":1 if s else 2,
                 "challenger_win":True,"seconds":1} for s in (True,False)]
    def check(self, rows):
        return audit(rows,{"a":"hash"},1,["a"],1)
    def test_valid(self):
        self.assertEqual(self.check(self.rows())["pair_0_1_2_wins"],[0,0,1])
    def test_missing_and_duplicate(self):
        for rows in (self.rows()[:1],self.rows()+self.rows()[:1]):
            with self.assertRaises(ValueError):
                self.check(rows)
    def test_invalid_row(self):
        for k,v in (("seed",1),("deck_sha256","wrong"),("status","timeout"),("challenger_win",False),("winner_seat",0),("seconds",float("nan"))):
            rows=self.rows()
            rows[0][k]=v
            with self.assertRaises(ValueError):
                self.check(rows)
    def test_split_pair(self):
        rows=self.rows()
        rows[1].update(winner_seat=1,challenger_win=False)
        r=self.check(rows)
        self.assertEqual(r["pair_0_1_2_wins"],[0,1,0])
        self.assertEqual(r["conditional_pair_sign_p_two_sided"],1)
