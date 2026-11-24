import unittest
from printing_evidence import inventory

class Tests(unittest.TestCase):
    def setUp(self):
        a={"gallery_id":"a","public_code":"OGN-001","set":"OGN","exact_engine_id":1,
           "identity_status":"exact_code_unverified","name":"A","rules_repr_sha256":"hash"}
        b={**a,"gallery_id":"b","public_code":"RAD-001a","set":"RAD","exact_engine_id":None,
           "identity_status":"candidate_only_unverified","candidate_engine_ids":[1]}
        self.rows={"printings":[a,b]}
        self.registry={"cards":[{"card_id":1,"public_code":"OGN-001","set":"OGN","banned":False}]}
        self.profile={"ban_entries":[{"engine_id":1}]}
    def run_inventory(self):
        return inventory(self.rows,self.registry,self.profile)
    def test_equal_is_not_approval(self):
        r=self.run_inventory()["rows"][0]
        self.assertEqual(r["classification"],"one_equal")
        self.assertTrue(r["any_banned_candidate"] and r["any_cross_set"])
        self.assertIsNone(r["approved_engine_id"])
        self.assertFalse(r["printing_equivalence_verified"])
    def test_different_rules_hash(self):
        self.rows["printings"][1]["rules_repr_sha256"]="other"
        self.assertEqual(self.run_inventory()["rows"][0]["classification"],"metadata_only")
    def test_missing_rules_hash_not_equal(self):
        for r in self.rows["printings"]: r["rules_repr_sha256"]=None
        self.assertEqual(self.run_inventory()["rows"][0]["classification"],"metadata_only")
    def test_unknown_candidate(self):
        self.rows["printings"][1]["candidate_engine_ids"]=[2]
        with self.assertRaises(KeyError): self.run_inventory()
    def test_duplicate_exact_mapping(self):
        self.rows["printings"].append({**self.rows["printings"][0],"gallery_id":"c"})
        with self.assertRaisesRegex(ValueError,"duplicate exact"): self.run_inventory()
    def test_exact_mismatch(self):
        self.registry["cards"][0]["public_code"]="wrong"
        with self.assertRaisesRegex(ValueError,"exact code mismatch"): self.run_inventory()
    def test_duplicate_candidates(self):
        self.rows["printings"][1]["candidate_engine_ids"]=[1,1]
        with self.assertRaises(ValueError): self.run_inventory()
