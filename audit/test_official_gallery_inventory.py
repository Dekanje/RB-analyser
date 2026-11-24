import json
import unittest
from official_gallery_inventory import collect, gallery_record, stable_hash

def page(total, ids):
    return json.dumps({"metadata":{"totalItems":total},"data":[{"id":i} for i in ids]}).encode()

class GalleryTests(unittest.TestCase):
    def test_full_pagination(self):
        data=iter([page(201,[str(i) for i in range(200)]),page(201,["200"])])
        rows,meta=collect("riftbound_gallery_cards",lambda _:next(data))
        self.assertEqual(len(rows),201)
        self.assertTrue(meta["advertised_count_matched"])
        self.assertEqual(len(meta["pages"]),2)
    def test_sparse_reported_as_incomplete(self):
        rows,meta=collect("riftbound_gallery_cards",lambda _:page(10,["a"]))
        self.assertEqual(len(rows),1)
        self.assertFalse(meta["advertised_count_matched"])
    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError,"repeated"):
            collect("riftbound_gallery_cards",lambda _:page(2,["a","a"]))
    def test_changed_total_rejected(self):
        data=iter([page(201,["a"]),page(202,["b"])])
        with self.assertRaisesRegex(ValueError,"changed"):
            collect("riftbound_gallery_cards",lambda _:next(data))
    def test_rules_not_exported(self):
        raw={"id":"x","name":"X","set":{"value":{"id":"RAD"}},
             "text":{"richText":{"body":"test rules"}}}
        r=gallery_record(raw)
        self.assertEqual(r["rules_repr_sha256"],stable_hash("test rules"))
        self.assertNotIn("test rules",json.dumps(r))
        self.assertIsNone(r["public_code"])
    def test_invalid_source_kind(self):
        with self.assertRaises(ValueError):
            collect("unknown",lambda _:b"")

if __name__=="__main__":
    unittest.main()
