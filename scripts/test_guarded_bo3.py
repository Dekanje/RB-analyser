import unittest
import json
from guarded_bo3 import series,prepare,strict_terminal,vector_hash,FormatRejected,AGENT,digest
class Fake:
    def __init__(self,winners):
        self.gate=self;self.winners=iter(winners);self.calls=[];self.bad=None
    def validate(self,raw):return json.loads(raw)
    def render(self,v):return json.dumps(v,sort_keys=True).encode()
    def provenance(self):return {"production_authorized":False}
    def game(self,a,b,seed,agent,timeout,forced_start=None):
        self.calls.append((a,b,forced_start))
        w=next(self.winners);vs=[self.validate(a),self.validate(b)]
        r={**self.provenance(),"status":"complete","winner":w,"reason":f"P{w} reached 8 points","turns":8,
           "native_ids_verified":True,"world_check_enabled":True,"seed":seed,"agent":agent,"forced_starting_player":forced_start,
           "deck_sha256":[digest(a),digest(b)],"native_vectors_sha256":[vector_hash(v) for v in vs],
           "native_extra_legend_ids":[v["NeekoLegends"] for v in vs],"trace_lines":2,"trace_sha256":"a"*64}
        if self.bad:r.update(self.bad)
        return r
class Tests(unittest.TestCase):
    def setUp(self):
        self.v={"Legend":[1],"Champion":[2],"MainDeck":[3,4,3],"Battlefields":[5,6,7],"Runes":[8]*12,"Sideboard":[9,10],"NeekoLegends":[11,12]}
        self.a=json.dumps(self.v).encode();self.b=json.dumps({**self.v,"Legend":[13]}).encode()
        self.swap={"swaps":[{"main_out":3,"side_in":9,"copies":1}]}
    def test_two_games(self):
        g=Fake([1,2]);r=series(g,(self.a,self.b),{},1)
        self.assertEqual(r["score"],[2,0]);self.assertEqual(len(g.calls),2)
        self.assertEqual(g.calls[1],(self.b,self.a,1))
    def test_three_games_and_restore(self):
        g=Fake([1,1,2]);r=series(g,(self.a,self.b),{"game2":{"p1":self.swap,"loser_chooses_start":"opponent"}},1)
        self.assertEqual(r["score"],[1,2]);self.assertEqual(g.calls[1][2],2)
        self.assertEqual(g.calls[2],(self.a,self.b,1))
        self.assertEqual(g.validate(g.calls[1][1])["NeekoLegends"],[11,12])
        self.assertTrue(r["sideboarding_applied"])
    def test_champion_switch(self):
        g=Fake([]);p=prepare(g,(self.a,self.b),{"game2":{"p1":{"chosen_champion":9}}})
        self.assertEqual(p[1][1][0]["Champion"],[9]);self.assertEqual(p[1][1][0]["Sideboard"],[2,10])
    def test_bad_future_plan_prevents_execution(self):
        g=Fake([1,2])
        with self.assertRaises(FormatRejected):series(g,(self.a,self.b),{"game3":{"p1":{"chosen_champion":99}}},1)
        self.assertEqual(g.calls,[])
    def test_bad_receipts(self):
        for bad in ({"status":"timeout"},{"winner":0},{"winner":True},{"reason":"turn cap"},{"forced_starting_player":1},{"world_check_enabled":False},{"deck_sha256":[]},{"native_extra_legend_ids":[]},{"trace_sha256":"x"}):
            g=Fake([1]);g.bad=bad;r=series(g,(self.a,self.b),{},1)
            self.assertEqual(r["status"],"incomplete");self.assertIsNone(r["winner"]);self.assertEqual(r["score"],[0,0])
    def test_terminal(self):
        t="Game over: winner=1 | reason=P1 reached 8 points | turns=9"
        self.assertEqual(strict_terminal(t,None),(1,"P1 reached 8 points",9))
        self.assertEqual(strict_terminal("TOURNAMENT_FORCED_STARTING_PLAYER=2\n"+t,2)[0],1)
        for x in (t+"\nGame over: winner=0",t.replace("P1 reached","P2 reached"),t.replace("8 points","turn cap"),t+"\nTOURNAMENT_FORCED_STARTING_PLAYER=1"):
            with self.assertRaises(FormatRejected):strict_terminal(x,None)
