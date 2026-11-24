import unittest
from p0_06_optimizer_evidence import paired_p_bounds,check_score,HISTORICAL_MIN_GAIN
class Tests(unittest.TestCase):
    def test_historical_threshold(self):
        self.assertEqual(HISTORICAL_MIN_GAIN,1)
    def test_bounds(self):
        self.assertEqual(paired_p_bounds(0,5,24),[.0625,.0625])
        self.assertEqual(paired_p_bounds(7,12,24)[0],.0625)
        self.assertEqual(paired_p_bounds(0,0,24),[1.,1.])
    def test_invalid_marginals(self):
        for a in ((0,25,24),(-1,2,24),(True,2,24),(1,2,0)):
            with self.assertRaises(ValueError):paired_p_bounds(*a)
    def test_score(self):
        self.assertEqual(check_score(dict(baseline_wins=2,candidate_wins=5,total=18,valid=True,errors=[]),18),3)
    def test_fail_closed_score(self):
        for d in (dict(valid=False),dict(errors=[{}]),dict(candidate_wins=19),dict(total=17)):
            s=dict(baseline_wins=2,candidate_wins=5,total=18,valid=True,errors=[]);s.update(d)
            with self.assertRaises(ValueError):check_score(s,18)
