import unittest
from p0_08_tournament_evidence import game_score,exact_tail,swiss_record_tail
class Tests(unittest.TestCase):
    def row(self):
        return dict(seat=0,target_win=True,status="complete",complete=True,error="",games=[
            dict(game=1,status="complete",winner_seat=1,error=""),
            dict(game=2,status="complete",winner_seat=2,error="")])
    def test_mirrored_game_seats(self):
        r=self.row();self.assertEqual(game_score(r),(2,0))
        r["seat"]=1;r["target_win"]=False;self.assertEqual(game_score(r),(0,2))
    def test_false_winner(self):
        r=self.row();r["target_win"]=False
        with self.assertRaises(ValueError):game_score(r)
    def test_extra_game(self):
        r=self.row();r["games"].append(dict(game=3,status="complete",winner_seat=1,error=""))
        with self.assertRaises(ValueError):game_score(r)
    def test_bad_receipt(self):
        for bad in (0,True,3):
            r=self.row();r["games"][0]["winner_seat"]=bad
            with self.assertRaises(ValueError):game_score(r)
    def test_tail(self):
        self.assertAlmostEqual(exact_tail(.5,.5,.5,7),46/512)
        self.assertAlmostEqual(exact_tail(.2,.8,.4,6),swiss_record_tail(.2,.8,.4,6))
