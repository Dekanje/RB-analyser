#!/usr/bin/env python3
"""No-engine regression for non-adopting all-58 next-wave selection."""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from select_wave2_holdouts import choose
from round_robin_58 import sha


class Wave2SelectionTests(unittest.TestCase):
    def test_positive_each_legend_independent_and_untouched_holdout_field(self):
        legends=[
            "Draven, Glorious Executioner","LeBlanc, Deceiver",
            "Master Yi, Wuju Bladesman","Miss Fortune, Bounty Hunter",
            "Rek'Sai, Void Burrower",
        ]+[f"Other Legend {n}" for n in range(6)]
        with tempfile.TemporaryDirectory() as td:
            p=pathlib.Path(td)
            originals={};manifest={};detail={};summary=[]
            ranked=[{"legend":n} for n in legends]
            for i,n in enumerate(legends):
                file=p/f"source_{i}.txt"
                file.write_text(n)
                originals[n]=file
                manifest[n]={"candidates":[
                    {"sha256":str(index),"path":f"candidate_{i}_{index}.txt"}
                    for index in range(40)]}
                detail[n]={"candidate_results":[{
                    "candidate_index":index,
                    "status":"COMPLETED_SCREENING_ONLY"
                } for index in range(0,40,5)]}
                summary.append({
                    "legend":n,"baseline_sha256":sha(file),
                    "candidate_delta":2 if i<5 else 1,
                    "candidate_wins":4 if i<5 else 3,
                    "baseline_wins":2,
                    "independently_confirmed":False,
                    "exploratory_candidate_index":0,
                    "exploratory_candidate_sha256":"0",
                })
            selected=choose(originals,manifest,ranked,
                            {"best_per_legend":summary},detail,top_k=2)
            self.assertEqual(len(selected),5)
            self.assertEqual(set(x["legend"] for x in selected),set(legends[:5]))
            self.assertTrue(all(x["screening_delta"]>0 for x in selected))
            self.assertTrue(all(len(x["training_opponents"])==3 and
                                len(x["holdout_opponents"])==6 for x in selected))
            self.assertTrue(all(not set(x["training_opponents"]) &
                                    set(x["holdout_opponents"]) for x in selected))
            summary[1]["candidate_delta"]=-1
            filtered=choose(originals,manifest,ranked,
                            {"best_per_legend":summary},detail,top_k=2)
            self.assertNotIn("LeBlanc, Deceiver",[x["legend"] for x in filtered])
            with self.assertRaises(ValueError):
                choose(originals,manifest,ranked,
                       {"best_per_legend":summary},detail,top_k=0)


if __name__=="__main__":
    unittest.main()
