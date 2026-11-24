import unittest
from format_match_v2 import receipt_vectors, transition, pool, FormatRejected

class MatchTests(unittest.TestCase):
    def setUp(self):
        self.v={"Legend":[1],"Champion":[2],"MainDeck":[3,4,3,5],
                "Battlefields":[6,7,8],"Runes":[9]*12,"Sideboard":[10,11]}
    def test_swap_and_pool(self):
        out=transition(self.v,{"swaps":[{"main_out":3,"side_in":10,"copies":1}]})
        self.assertEqual(out["MainDeck"],[4,3,5,10])
        self.assertEqual(out["Sideboard"],[11,3])
        self.assertEqual(pool(out),pool(self.v))
        self.assertEqual(self.v["MainDeck"],[3,4,3,5])
    def test_champion_swap(self):
        self.assertEqual(transition(self.v,{"chosen_champion":10})["Sideboard"],[2,11])
    def test_overdraw(self):
        with self.assertRaises(FormatRejected):
            transition(self.v,{"swaps":[{"main_out":3,"side_in":10,"copies":2}]})
    def test_bad_policy(self):
        for p in ({"x":1},{"chosen_champion":999},{"swaps":[{"main_out":3,"side_in":10,"copies":True}]}):
            with self.assertRaises(FormatRejected):
                transition(self.v,p)
    def test_receipts_order(self):
        log="[DECK] P1 (a):\n    main      [x] X\n    main      [y] Y\n[DECK] P2 (b):\n    side      [y] Y\n"
        v=receipt_vectors(log,{"x":1,"y":2})
        self.assertEqual(v[0]["MainDeck"],[1,2])
        self.assertEqual(v[1]["Sideboard"],[2])
    def test_missing_receipt(self):
        with self.assertRaises(FormatRejected):
            receipt_vectors("[DECK] P1 (a):",{})
    def test_unknown_definition(self):
        with self.assertRaises(FormatRejected):
            receipt_vectors("[DECK] P1 (a):\n    main [x] X",{})
    def test_duplicate_header(self):
        with self.assertRaises(FormatRejected):
            receipt_vectors("[DECK] P1 (a):\n[DECK] P1 (a):",{})

if __name__=="__main__":
    unittest.main()
