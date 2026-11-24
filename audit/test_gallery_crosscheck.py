import unittest
from gallery_crosscheck import compare
class Tests(unittest.TestCase):
    def test_added_missing_changed(self):
        old={"printings":[{"gallery_id":"a","name":"A"},{"gallery_id":"b"}]}
        r=compare(old,[(100,[{"gallery_id":"a","name":"B","public_code":"X"},{"gallery_id":"c","public_code":"Y"}],{})])["comparisons"][0]
        self.assertEqual((r["added"],r["missing"],r["changed"]),(["c"],["b"],["a"]))
    def test_duplicate(self):
        with self.assertRaises(ValueError): compare({"printings":[]},[(100,[{"gallery_id":"a"}]*2,{})])
