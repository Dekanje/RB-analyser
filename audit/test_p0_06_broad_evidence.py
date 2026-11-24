import unittest
from p0_06_broad_evidence import verify_pairs
class Tests(unittest.TestCase):
    def example(self):
        rows=[dict(opponent="A",seat=s,repetition=0,seed=5,both_complete=True,baseline_status="complete",
                   candidate_status="complete",baseline_win=0,candidate_win=1) for s in (0,1)]
        return dict(scenarios=rows,completed=2,expected=2,incomplete=0,baseline_wins=0,candidate_wins=2,
                    baseline_only_wins=0,candidate_only_wins=2,candidate_minus_baseline=2,mcnemar_p=.5)
    def test_pair(self):
        self.assertEqual(verify_pairs(self.example(),2)[2],.5)
    def test_missing(self):
        e=self.example();e["scenarios"].pop()
        with self.assertRaises(ValueError):verify_pairs(e,2)
    def test_duplicate(self):
        e=self.example();e["scenarios"][1]["seat"]=0
        with self.assertRaises(ValueError):verify_pairs(e,2)
    def test_invalid(self):
        e=self.example();e["scenarios"][0]["candidate_status"]="error"
        with self.assertRaises(ValueError):verify_pairs(e,2)
    def test_p_drift(self):
        e=self.example();e["mcnemar_p"]=.01
        with self.assertRaises(ValueError):verify_pairs(e,2)
