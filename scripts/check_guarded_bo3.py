"""Four frozen native series; not deck optimization."""
import argparse,json
from pathlib import Path
from guarded_bo3 import GuardedBO3,series,require,digest,EXTRA
from format_roster_v2 import load_roster
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ("engine","registry","profile","selected","prior","output"):p.add_argument("--"+n,type=Path,required=True)
    a=p.parse_args();g=GuardedBO3(a.engine,a.registry,a.profile)
    roster=load_roster(g,a.selected,a.prior)
    v=g.gate.validate(roster["ahri_nine_tailed_fox.txt"])
    require(v["Legend"]==[252] and 56 in v["Sideboard"] and 811 in v["MainDeck"],"fixture mismatch")
    v["Sideboard"][v["Sideboard"].index(56)]=1131;v[EXTRA]=[256,249,254]
    one=g.render(v);two=roster["akali_rogue_assassin.txt"]
    swap={"swaps":[{"main_out":811,"side_in":1131,"copies":1}]}
    cases=[]
    for idx,(flip,choice) in enumerate(((False,"self"),(False,"opponent"),(True,"self"),(True,"opponent"))):
        who="p2" if flip else "p1"
        policy={"game2":{who:swap,"loser_chooses_start":choice},"game3":{"loser_chooses_start":choice}}
        raws=(two,one) if flip else (one,two)
        cases.append((idx,flip,choice,policy,raws))
    report={**g.provenance(),"status":"FAILED_OR_INCOMPLETE","series":[],"adopted":0,"fitness_evaluated":False}
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as f:
        try:
            for idx,flip,choice,policy,raws in cases:
                result=series(g,raws,policy,202611241930+idx)
                report["series"].append({"case":idx,"registration_flipped":flip,"choice":choice,"policy":policy,"series_seed":202611241930+idx,"result":result})
                print("P007_SERIES",idx,result["status"],flush=True)
            require(all(x["result"]["status"]=="complete_declared_points_bo3" and x["result"]["sideboarding_applied"] for x in report["series"]),"incomplete series")
            report["games_completed"]=sum(len(x["result"]["games"]) for x in report["series"])
            report["status"]="PASS_SCOPED_DECLARED_POINTS_BO3"
        finally:json.dump(report,f,indent=2)
if __name__=="__main__":main()
