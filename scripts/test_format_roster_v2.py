import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from types import SimpleNamespace
from format_match_v2 import VerifiedGateway, FormatRejected, HEADINGS, ENGINE_SHA
from format_roster_v2 import schedule, verify_coverage

class RosterTests(unittest.TestCase):
    def test_schedule_all_both_seats(self):
        names=[str(i) for i in range(58)]
        rows=[{**r,"receipt":{"status":"complete","winner":1,"native_ids_verified":True}} for r in schedule(names)]
        verify_coverage(rows,names)
        self.assertEqual(len(rows),58)
        self.assertEqual(rows[0]["seed"],rows[1]["seed"])
        with self.assertRaises(FormatRejected):
            verify_coverage(rows[:-1],names)
        with self.assertRaises(FormatRejected):
            verify_coverage(rows[:-1]+[rows[0]],names)
        rows[0]["receipt"]["native_ids_verified"]=False
        with self.assertRaises(FormatRejected):
            verify_coverage(rows,names)

    def test_real_roster_mapping_input(self):
        roster={str(i):b"registration" for i in range(58)}
        rows=[{**r,"receipt":{"status":"complete","winner":1,"native_ids_verified":True}} for r in schedule(roster)]
        verify_coverage(rows,roster)
        with self.assertRaises(FormatRejected):
            verify_coverage(rows,{k:v for k,v in roster.items() if k!="0"})
        rows[0]["two"]=rows[0]["one"]
        with self.assertRaises(FormatRejected):
            verify_coverage(rows,roster)

    def test_missing_legend(self):
        with self.assertRaises(FormatRejected):
            schedule([str(i) for i in range(57)])

    def test_actual_native_mismatch_rejected(self):
        g=VerifiedGateway.__new__(VerifiedGateway)
        with TemporaryDirectory() as root:
            g.engine=Path(root)/"binary"
            g.engine.write_bytes(b"test")
            g.definitions={"x":1,"y":2}
            expected=[{h:[] for h in HEADINGS} for _ in range(2)]
            expected[0]["MainDeck"]=[1,2]
            log="[DECK] P1 (a):\n main [y] Y\n main [x] X\n[DECK] P2 (b):\nGame over: winner=1 | reason=fixture | turns=1\n"
            with patch("format_match_v2.digest",return_value=ENGINE_SHA),patch(
                    "format_match_v2.subprocess.run",return_value=SimpleNamespace(returncode=0,stdout=log,stderr="")):
                with self.assertRaisesRegex(FormatRejected,"ordered vectors mismatch"):
                    g._native((b"a",b"b"),expected,1,"ismcts:sims=24",1)

    def test_match_snapshot_survives_source_mutation(self):
        g=VerifiedGateway.__new__(VerifiedGateway)
        v={"Legend":[1],"Champion":[2],"MainDeck":[3],"Battlefields":[4],"Runes":[5],"Sideboard":[]}
        g.gate=SimpleNamespace(validate=lambda raw:{k:list(x) for k,x in v.items()})
        g.provenance=lambda:{}
        with TemporaryDirectory() as root:
            a,b=Path(root)/"a",Path(root)/"b"
            a.write_bytes(b"original-a");b.write_bytes(b"original-b")
            observed=[]
            def game(one,two,*args,**kwargs):
                observed.append((one,two))
                a.write_bytes(b"changed")
                b.write_bytes(b"changed")
                return {"winner":1 if len(observed)==1 else 2}
            g.game=game
            result=g.declared_bo3(a,b,{},7)
            self.assertEqual(observed,[(b"original-a",b"original-b"),(b"original-b",b"original-a")])
            self.assertEqual(result["score"],[2,0])

if __name__=="__main__":
    unittest.main()
