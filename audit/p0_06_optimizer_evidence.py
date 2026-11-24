"""Read-only audit of the historical expanded optimizer's aggregate evidence."""
import argparse,csv,hashlib,io,json,math,zipfile
from collections import Counter
from pathlib import Path

ARCHIVE_SHA="1cdf59d8cc2c36dde035a142ad09556ee9323cfdbb836488e0c20bd75c09f872"
TRIALS_SHA="6c2164971048c4cee981ce861f11e7c8866e2a8cb07812b21c9682d811b7d4e7"
# Exact historical run 45181493632, job 137719193919 CLI log.
HISTORICAL_MIN_GAIN=1

def require(ok,msg):
    if not ok:raise ValueError(msg)

def sha(b):return hashlib.sha256(b).hexdigest()

def paired_p_bounds(b,c,n):
    """Bounds over all paired 2x2 tables compatible with the marginal wins.
    Not a p-value for the actual experiment, nor evidence of independent pairs.
    """
    require(all(type(x) is int for x in (b,c,n)) and n>0 and 0<=b<=n and 0<=c<=n,"invalid marginals")
    values=[]
    for both in range(max(0,b+c-n),min(b,c)+1):
        x,y=b-both,c-both
        d=x+y
        values.append(min(1.,2*sum(math.comb(d,i) for i in range(min(x,y)+1))/2**d))
    return [min(values),max(values)]

def check_score(s,expected):
    b,c,n=(s[k] for k in ("baseline_wins","candidate_wins","total"))
    require(type(n) is int and n==expected and all(type(x) is int and 0<=x<=n for x in (b,c)),"score bounds")
    require(type(s["valid"]) is bool and isinstance(s["errors"],list) and s["valid"]==(not s["errors"]),"invalid error flag")
    return c-b

def audit(trials,selected_hashes,rows,summary):
    require(len(trials)==len(rows)==len(selected_hashes)==58,"incomplete roster")
    require(len({x["legend"] for x in trials})==58 and set(rows)=={x["legend"] for x in trials},"duplicate/missing legend")
    require(len(set(selected_hashes))==58 and set(selected_hashes)=={x["effective_sha256"] for x in trials},"selected hash mismatch")
    stats=Counter();depths=Counter();promotions=[];errors=Counter()
    for x in trials:
        name=x["legend"];csvrow=rows[name]
        require(x["agent"]=="ismcts:sims=24" and x["samples"]==3 and x["holdout_samples"]==4,"unexpected budget")
        require(type(x["selected"]) is bool and x["selected"]==(x["original_sha256"]!=x["effective_sha256"]),"changed flag mismatch")
        require(csvrow["baseline_sha256"]==x["original_sha256"] and csvrow["selected_sha256"]==x["effective_sha256"] and csvrow["changed"]==str(x["selected"]) and int(csvrow["swap_count"])==len(x["selected_swaps"]),"CSV mismatch")
        stats["changed_legends"]+=x["selected"]
        flattened=[]
        for ix,r in enumerate(x["rounds"],1):
            require(r["round"]==ix and len(r["opponents"])==len(set(r["opponents"]))==6 and name not in r["opponents"],"invalid round/opponents")
            require(all(n in rows for n in r["opponents"]),"unknown opponent")
            stats["rounds"]+=1
            proposals={p["file"]:p for p in r["prefilter"]}
            require(len(proposals)==len(r["prefilter"]),"duplicate proposal")
            for p in r["prefilter"]:
                require(check_score(p["prefilter"],12)==p["delta_prefilter"],"prefilter delta")
                stats["prefilter_evaluations"]+=1
                stats["prefilter_invalid"]+=not p["prefilter"]["valid"]
                depth=len(p["swap_sequence"]);require(depth in (1,2),"unexpected swap depth");depths[depth]+=1
            require(len(r["trials"])==3 and len({p["file"] for p in r["trials"]})==3,"unexpected shortlist")
            for p in r["trials"]:
                require(p["file"] in proposals and all(p[k]==v for k,v in proposals[p["file"]].items()),"trial provenance")
                require(check_score(p["train"],18)==p["delta_train"],"training delta")
                stats["training_evaluations"]+=1;stats["training_invalid"]+=not p["train"]["valid"]
                for error in p["train"]["errors"]:errors[str(error.get("status","unknown"))]+=1
            h=r["holdout"]
            if h is not None:
                delta=check_score(h,24)
                stats["holdout_evaluations"]+=1;stats["holdout_invalid"]+=not h["valid"]
                for error in h["errors"]:errors[str(error.get("status","unknown"))]+=1
            best=r["trials"][0]
            selected=r["selected"]
            if selected:
                require(selected==best and best["train"]["valid"] and h is not None and h["valid"] and best["delta_train"]>=HISTORICAL_MIN_GAIN and delta>=HISTORICAL_MIN_GAIN,"invalid historical promotion")
                flattened.extend({"round":ix,**s} for s in selected["swap_sequence"])
                bounds=paired_p_bounds(h["baseline_wins"],h["candidate_wins"],h["total"])
                promotions.append({"legend":name,"round":ix,"training_delta":best["delta_train"],"holdout":h,
                    "conditional_mcnemar_p_bounds_from_marginals":bounds})
            else:
                require(ix==len(x["rounds"]),"continued after unselected round")
            if not best["train"]["valid"] and any(p["train"]["valid"] and p["delta_train"]>=2 for p in r["trials"][1:]):
                stats["invalid_top_blocks_valid_candidate_rounds"]+=1
        require(flattened==x["selected_swaps"] and bool(flattened)==x["selected"],"selected lineage mismatch")
    require(summary["legends"]==58 and summary["improved_provisionally"]==stats["changed_legends"] and summary["globally_optimal"] is False and summary["sideboarded_bo3"] is False,"summary mismatch")
    return {"status":"PASS_HISTORICAL_AGGREGATE_AUDIT_ONLY","counts":dict(stats),"proposal_depths":dict(depths),
            "promotions":promotions,"promotion_rounds":len(promotions),
            "historical_min_gain":HISTORICAL_MIN_GAIN,
            "promotions_below_two_training_wins":sum(p["training_delta"]<2 for p in promotions),
            "promotions_with_any_compatible_unadjusted_p_le_0_05":sum(p["conditional_mcnemar_p_bounds_from_marginals"][0]<=.05 for p in promotions),
            "reported_bo3_evaluations_not_independently_reconstructed":summary["bo3_evaluations"],
            "error_record_status_counts":dict(errors),"opponent_holdout_independence":False,
            "per_game_native_receipts_available_in_aggregate":False,
            "blind_discovery_certified":False,"production_adopted":0}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--archive",type=Path,required=True);p.add_argument("--output",type=Path,required=True);a=p.parse_args()
    require(sha(a.archive.read_bytes())==ARCHIVE_SHA,"archive drift")
    with zipfile.ZipFile(a.archive) as z:
        raw=z.read("all_58_trials.json");require(sha(raw)==TRIALS_SHA,"report drift")
        csvrows=list(csv.DictReader(io.StringIO(z.read("all_58.csv").decode())))
        require(len(csvrows)==58,"CSV size")
        report=audit(json.loads(raw),[sha(z.read(n)) for n in z.namelist() if n.startswith("selected_decks/") and n.endswith(".txt")],
                     {r["legend"]:r for r in csvrows},json.loads(z.read("summary.json")))
    a.output.parent.mkdir(parents=True,exist_ok=True)
    with a.output.open("x") as f:json.dump(report,f,indent=2,sort_keys=True)
    print(report["status"],report["counts"])
if __name__=="__main__":main()
