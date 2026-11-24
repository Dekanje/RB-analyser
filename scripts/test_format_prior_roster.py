import unittest
from copy import deepcopy
from check_format_prior_roster import schedule,verify,FormatRejected,AGENT
class Tests(unittest.TestCase):
    def setUp(self):
        self.m={str(i):{"deck_sha256":str(i),"vector_sha256":"v"+str(i),"extras":[]} for i in range(58)}
        self.p={"engine_sha256":"engine","public_prior_sha256":"policy"}
        self.rows=[]
        for r in schedule(self.m):
            a,b=self.m[r["one"]],self.m[r["two"]]
            self.rows.append({**r,"receipt":{**self.p,"status":"complete","native_ids_verified":True,
                "winner":1,"turns":1,"reason":"test","seed":r["seed"],"agent":AGENT,"forced_starting_player":None,
                "deck_sha256":[a["deck_sha256"],b["deck_sha256"]],
                "native_vectors_sha256":[a["vector_sha256"],b["vector_sha256"]],"native_extra_legend_ids":[[],[]]}})
    def test_complete(self):
        verify(self.rows,self.m,self.p)
    def test_missing(self):
        with self.assertRaises(FormatRejected):verify(self.rows[:-1],self.m,self.p)
    def test_drift(self):
        for key,value in (("public_prior_sha256","wrong"),("native_vectors_sha256",["wrong","wrong"]),
                          ("native_extra_legend_ids",[[249],[]]),("seed",0),("status","error")):
            rows=deepcopy(self.rows);rows[0]["receipt"][key]=value
            with self.assertRaises(FormatRejected):verify(rows,self.m,self.p)
