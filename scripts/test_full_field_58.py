#!/usr/bin/env python3
"""Regression tests: exhaustive 58x57 opponent schedules and paired outcomes."""
import hashlib
import pathlib
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import full_field_58 as ff


class FullFieldTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=pathlib.Path(self.temp.name)
        self.names=[f"Legend {index:02d}" for index in range(58)]
        self.decks={}
        for name in self.names:
            fp=self.root/(name.replace(" ","_")+".txt")
            fp.write_text(name,encoding="utf8")
            self.decks[name]=fp

    def test_schedule_reaches_every_other_deck_both_seats(self):
        schedule=list(ff.schedule(self.decks,self.names[0],2,123))
        self.assertEqual(len(schedule),57*2*2)
        self.assertEqual(len({(op,seat,repeat) for op,seat,repeat,_ in schedule}),len(schedule))
        self.assertEqual({op for op,_,_,_ in schedule},set(self.names[1:]))
        self.assertEqual({seat for _,seat,_,_ in schedule},{0,1})
        self.assertEqual(schedule,list(ff.schedule(self.decks,self.names[0],2,123)))

    def test_changed_and_unchanged_both_cover_all_opponents(self):
        target=self.names[0]; original=self.decks[target]
        candidate=self.root/"candidate.txt"
        candidate.write_text("an actual changed cardlist",encoding="utf8")
        calls=[]
        def fake_engine(exe,deck,opponent,seat,seed,agent,timeout,env):
            calls.append((deck.name,opponent.name,seat,seed))
            return {"status":"complete",
                    "winner": seat+1 if deck==candidate else 2-seat,
                    "games":[]}
        with patch.object(ff,"engine_bo3",side_effect=fake_engine):
            row=ff.assess_row(target,original,candidate,self.decks,
                              pathlib.Path("unused"),"ismcts:sims=24",60,1,987,4)
        self.assertEqual(row["completed"],114)
        self.assertEqual(row["total_opponents"],57)
        self.assertEqual(row["baseline_wins"],0)
        self.assertEqual(row["candidate_wins"],114)
        self.assertEqual(len(calls),228)
        self.assertEqual(len(row["per_opponent"]),57)
        calls.clear()
        with patch.object(ff,"engine_bo3",side_effect=fake_engine):
            row=ff.assess_row(target,original,original,self.decks,
                              pathlib.Path("unused"),"ismcts:sims=24",60,1,987,4)
        self.assertFalse(row["changed"])
        self.assertEqual(row["completed"],114)
        self.assertEqual(len(calls),114)
        self.assertEqual(row["candidate_minus_baseline"],0)

    def test_timeout_is_not_counted_as_loss(self):
        target=self.names[0]; original=self.decks[target]
        candidate=self.root/"candidate.txt"
        candidate.write_text("changed",encoding="utf8")
        def fake_engine(exe,deck,opponent,seat,seed,agent,timeout,env):
            if deck==candidate:
                return {"status":"incomplete","winner":None,"games":[]}
            return {"status":"complete","winner":seat+1,"games":[]}
        with patch.object(ff,"engine_bo3",side_effect=fake_engine):
            row=ff.assess_row(target,original,candidate,self.decks,
                              pathlib.Path("unused"),"ismcts:sims=24",60,1,987,4)
        self.assertEqual(row["completed"],0)
        self.assertEqual(row["incomplete"],114)
        self.assertEqual(row["candidate_wins"],0)
        self.assertEqual(row["baseline_wins"],0)

    def test_holm_multiple_testing_and_no_changes(self):
        rows=[
            {"legend":"A","changed":True,"mcnemar_p":0.001,"incomplete":0,
             "candidate_wins":100,"baseline_wins":70},
            {"legend":"B","changed":True,"mcnemar_p":0.03,"incomplete":0,
             "candidate_wins":80,"baseline_wins":70},
            {"legend":"C","changed":False,"mcnemar_p":1.0,"incomplete":0,
             "candidate_wins":50,"baseline_wins":50}
        ]
        ff.holm(rows)
        self.assertAlmostEqual(rows[0]["holm_adjusted_p"],0.002)
        self.assertTrue(rows[0]["independently_confirmed"])
        self.assertAlmostEqual(rows[1]["holm_adjusted_p"],0.03)
        self.assertTrue(rows[1]["independently_confirmed"])
        self.assertFalse(rows[2]["independently_confirmed"])
        self.assertEqual(ff.mcnemar_exact(6,0),0.03125)
        self.assertEqual(ff.mcnemar_exact(0,0),1.0)


if __name__=="__main__":
    unittest.main(verbosity=2)
