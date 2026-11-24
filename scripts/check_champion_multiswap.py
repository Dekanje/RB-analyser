"""Native champion changes and simultaneous multi-card swaps, diagnostic only."""
import argparse,json
from pathlib import Path
from collections import Counter
from guarded_bo3 import GuardedBO3,series,prepare,require,digest,vector_hash,AGENT,EXTRA
from format_roster_v2 import load_roster
from format_match_v2 import pool,FormatRejected

MF={"chosen_champion":162,"swaps":[{"main_out":981,"side_in":444,"copies":2},{"main_out":668,"side_in":180,"copies":1}]}
KEN={"chosen_champion":922,"swaps":[{"main_out":922,"side_in":483,"copies":1},{"main_out":444,"side_in":481,"copies":2}]}
def verify_control(regs,vs):
    a,b=regs;x,y=vs
    require(a["Champion"]==[193] and b["Champion"]==[900],"fixture original champion")
    require(x["Champion"]==[162] and y["Champion"]==[922],"changed champion mismatch")
    require(193 in x["MainDeck"] and 900 in y["Sideboard"] and 922 not in y["MainDeck"],"champion provenance mismatch")
    require(Counter(a["MainDeck"])-Counter(x["MainDeck"])==Counter({981:2,668:1,162:1}) and
            Counter(x["MainDeck"])-Counter(a["MainDeck"])==Counter({444:2,180:1,193:1}),"MF multi-swap mismatch")
    require(Counter(b["MainDeck"])-Counter(y["MainDeck"])==Counter({922:1,444:2}) and
            Counter(y["MainDeck"])-Counter(b["MainDeck"])==Counter({483:1,481:2}),"Kennen multi-swap mismatch")
    for o,v in zip(regs,vs):
        require(pool(o)==pool(v) and all(o[h]==v[h] for h in ("Legend","Battlefields","Runes",EXTRA)),"pool/fixed zone mismatch")
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("engine","registry","profile","selected","prior","output"):p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args();g=GuardedBO3(a.engine,a.registry,a.profile)
    roster=load_roster(g,a.selected,a.prior)
    raws=(roster["miss_fortune_bounty_hunter.txt"],roster["kennen_heart_of_the_tempest.txt"])
    policy={"game2":{"p1":MF,"p2":KEN,"loser_chooses_start":"opponent"}}
    p=prepare(g,raws,policy);verify_control(p[0][1],p[1][1])
    report={**g.provenance(),"status":"FAILED_OR_INCOMPLETE","policy":policy,
            "registered_sha256":[digest(x) for x in raws],"registered_vectors_sha256":[vector_hash(v) for v in p[0][1]],
            "changed_sha256":[digest(x) for x in p[1][0]],"changed_vectors_sha256":[vector_hash(v) for v in p[1][1]],
            "champions_before":[v["Champion"] for v in p[0][1]],"champions_after":[v["Champion"] for v in p[1][1]],
            "series":[],"negative_preflight":[],"adopted":0,"fitness_evaluated":False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as f:
        try:
            for label,plan in (("outside_pool",{"chosen_champion":999999}),("overdraw",{"swaps":[{"main_out":981,"side_in":444,"copies":3}]}),
                               ("overlap",{"swaps":[{"main_out":668,"side_in":444,"copies":1},{"main_out":444,"side_in":180,"copies":1}]})):
                try:prepare(g,raws,{"game2":{"p1":plan}})
                except FormatRejected:report["negative_preflight"].append(label)
                else:raise AssertionError(label+" accepted")
            for idx in (0,1):
                pair=raws[::-1] if idx else raws
                plan={"game2":{"p1":KEN if idx else MF,"p2":MF if idx else KEN,"loser_chooses_start":"self" if idx else "opponent"}}
                result=series(g,pair,plan,2026112440+idx)
                report["series"].append({"index":idx,"seed":2026112440+idx,"policy":plan,"result":result})
                print("P007_CHAMPION_SERIES",idx,result["status"],flush=True)
                require(result["status"]=="complete_declared_points_bo3" and result["sideboarding_applied"],"incomplete series")
                game=result["games"][1];expected=report["changed_sha256"][::-1] if idx else report["changed_sha256"]
                require(game["active_identity_sha256"]==expected,"G2 altered receipt mismatch")
            report["games_completed"]=sum(len(s["result"]["games"]) for s in report["series"])
            report["status"]="PASS_SCOPED_CHAMPION_MULTISWAP_BO3"
        finally:json.dump(report,f,indent=2)
if __name__=="__main__":main()
