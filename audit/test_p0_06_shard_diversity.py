import unittest
from p0_06_shard_diversity import parse,changed,key,distance,legal_bytes
class Tests(unittest.TestCase):
    def raw(self):
        return b"Legend:\n1 L\nChampion:\n1 C\nMainDeck:\n38 A\n1 B\nBattlefields:\n1 F\nRunes:\n12 R\nSideboard:\n"
    def test_mutation(self):
        v=parse(self.raw());w=changed(v,[{"remove":"B","add":"D"}])
        self.assertEqual(distance(v["MainDeck"],w["MainDeck"]),1)
        self.assertNotEqual(key(v),key(w))
        self.assertEqual(v["MainDeck"]["B"],1)
    def test_impossible(self):
        with self.assertRaises(ValueError):changed(parse(self.raw()),[{"remove":"Z","add":"D"}])
    def test_bad_deck(self):
        with self.assertRaises(ValueError):parse(self.raw().replace(b"1 B",b"0 B"))
    def test_correction(self):
        self.assertEqual(legal_bytes(self.raw(),[{"before":"1 B","after":"1 D"}]),self.raw().replace(b"1 B",b"1 D"))
        with self.assertRaises(ValueError):legal_bytes(self.raw(),[{"before":"1 Z","after":"1 D"}])
    def test_order(self):
        self.assertEqual(key(parse(self.raw())),key(parse(self.raw().replace(b"38 A\n1 B",b"1 B\n38 A"))))
