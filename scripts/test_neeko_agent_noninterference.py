import unittest
from check_neeko_agent_noninterference import analyze
class Tests(unittest.TestCase):
    def test_cut_and_count(self):
        s="""[DECK] P1 (a):
  [TRC] [D:1] DECISION #1 (P2): 3 legal actions
  [TRC] [D:1] CHOSE: [P2] PlayCard X
  [TRC] [D:2] MODE_PROMPT: Neeko: choose a legend [X/Y]
  [TRC] [D:2] MODE_PICKED: Neeko: choose a legend = mode#1 (Y)
  [TRC] [D:3] CHOSE: [P2] EndTurn
"""
        prefix,n,m,yes,pick=analyze(s,"P2")
        self.assertEqual((len(prefix),n,m,yes),(2,1,1,True))
        self.assertIn("(Y)",pick)
    def test_no_prompt_is_not_sensitivity(self):
        p,n,m,yes,pick=analyze("  [TRC] CHOSE: [P1] EndTurn","P1")
        self.assertEqual((len(p),n,m,yes,pick),(1,1,0,False,None))
