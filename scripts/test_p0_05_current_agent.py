import unittest
from unittest.mock import patch
from p0_05_current_agent import schedule,summarize,native_result,PANEL,FormatRejected
class Tests(unittest.TestCase):
    def rows(self):
        m={d:{"deck_sha256":"d","vector_sha256":"v"} for d in PANEL}
        rows=[{**c,"receipt":{"status":"complete","native_ids_verified":True,"world_check_enabled":True,
            "winner":c["challenger_seat"],"challenger_win":True,"deck_sha256":["d","d"],
            "native_vectors_sha256":["v","v"],"turns":10,"reason":f'P{c["challenger_seat"]} reached 8 points',
            "trace_lines":2,"trace_sha256":"a"*64,"seconds":1}} for c in schedule()]
        return rows,m
    def test_schedule(self):
        r=schedule()
        self.assertEqual(len(r),24)
        self.assertEqual(len({x["seed"] for x in r}),12)
        self.assertEqual(r[0]["agents"],list(reversed(r[1]["agents"])))
    def test_summary(self):
        r,m=self.rows()
        self.assertEqual(summarize(r,m)["pair_0_1_2_wins"],[0,0,12])
    def test_schedule_drift(self):
        r,m=self.rows()
        for bad in (r[:-1],r[1:]+r[:1]):
            with self.assertRaises(FormatRejected):summarize(bad,m)
    def test_invalid_receipts(self):
        for k,v in (("status","timeout"),("winner",0),("challenger_win",False),("deck_sha256",["x","x"]),
                    ("world_check_enabled",False),("reason","turn cap"),("seconds",float("nan"))):
            r,m=self.rows();r[0]["receipt"][k]=v
            with self.assertRaises(FormatRejected):summarize(r,m)
    def test_terminal(self):
        class Gate:
            prior_text="p"
            definitions={}
        vec={}
        s="Game over: winner=1 | reason=P1 reached 8 points | turns=10\n[TRC] DRAW_HAND: x\n[TRC] INTENT: x"
        with patch("p0_05_current_agent.verify_prior"),patch("p0_05_current_agent.receipt_v3",return_value=[vec,vec]):
            self.assertTrue(native_result(s,0,Gate(),vec,schedule()[0])["challenger_win"])
            for bad in (s+"\nGame over: winner=0",s.replace("P1 reached","P2 reached"),s+"\nTOURNAMENT_FORCED_STARTING_PLAYER=1",s.replace("DRAW_HAND:","X:")):
                with self.assertRaises(FormatRejected):native_result(bad,0,Gate(),vec,schedule()[0])
