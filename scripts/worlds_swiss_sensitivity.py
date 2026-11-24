#!/usr/bin/env python3
"""Hypothetical nine-round Swiss record sensitivity for 919 legal lineups.

Conditional model assumptions:
- The three registered decks play three matches each.
- Opponent archetypes are sampled from ten frozen elite-anchor Legends.
- After one opponent mix and one posterior matchup-rate draw, match wins
  are independent Bernoulli trials at each deck's sampled matchup rate.
- A matchup against the same Legend/anchor is treated as 50%.
- Each other observed matchup has only two mirrored real 128-ISMCTS BO3
  results; use a Beta(0.5,0.5) posterior, not point-estimate certainty.

Compute P(Swiss wins >= 6), >= 7, >= 8. The threshold is NOT an official
Top-4 cut rule and these are NOT actual event-win probabilities.
The independence assumption ignores Swiss pairing feedback, opponents'
sideboarding, hidden information/skill gaps, draws and timer policy.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random
import sys
from collections import defaultdict

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from worlds_lineups import compatible_triples,load_outcomes
from worlds_robust_lineups import quantile
from round_robin_58 import sha


def binomial_three(p:float)->list[float]:
    if not 0<=p<=1:
        raise ValueError("Invalid Bernoulli match probability")
    q=1-p
    return [q*q*q,3*p*q*q,3*p*p*q,p*p*p]


def convolve(a,b):
    out=[0.]*(len(a)+len(b)-1)
    for i,pa in enumerate(a):
        for j,pb in enumerate(b):
            out[i+j]+=pa*pb
    return out


def swiss_record_tail(p_a:float,p_b:float,p_c:float,k:int)->float:
    """Exact nine-trial Poisson-binomial tail, 3 games per registered deck."""
    if not 0<=k<=9:
        raise ValueError("Win threshold must be between zero and nine")
    pmf=convolve(convolve(binomial_three(p_a),binomial_three(p_b)),
                 binomial_three(p_c))
    if len(pmf)!=10 or abs(sum(pmf)-1)>1e-10:
        raise RuntimeError("Probabilities do not normalize")
    return min(1.,max(0.,sum(pmf[k:])))


def evaluate(outcomes,domains,anchors,repetitions=500,concentration=1.,
             seed=202611251100):
    if not 50<=repetitions<=3000 or concentration<=0 or len(anchors)!=10:
        raise ValueError("Outside documented illustrative sensitivity model")
    triples=compatible_triples(domains)
    if not triples:
        raise RuntimeError("No legal domain-disjoint lineups")
    rng=random.Random(seed)
    names=sorted(domains)
    thresholds=(6,7,8)
    values={trio:{k:[] for k in thresholds} for trio in triples}
    for rep in range(repetitions):
        weights=[rng.gammavariate(concentration,1.) for _ in anchors]
        weight_sum=sum(weights);weights=[x/weight_sum for x in weights]
        rates={}
        for name in names:
            value=0.
            for opponent,w in zip(anchors,weights):
                if name==opponent:
                    chance=.5
                else:
                    observation=outcomes[(name,opponent)]
                    successes=round(2*observation)
                    if (abs(2*observation-successes)>1e-10 or
                        successes not in (0,1,2)):
                        raise RuntimeError("Incomplete actual mirrored BO3 evidence")
                    chance=rng.betavariate(successes+.5,2-successes+.5)
                value+=w*chance
            rates[name]=value
        for trio in triples:
            a,b,c=(rates[x] for x in trio)
            pmf=convolve(convolve(binomial_three(a),binomial_three(b)),
                         binomial_three(c))
            if len(pmf)!=10 or abs(sum(pmf)-1)>1e-9:
                raise RuntimeError("Swiss probability distribution corrupted")
            for k in thresholds:
                values[trio][k].append(sum(pmf[k:]))
    rows=[]
    for trio in triples:
        samples=values[trio]
        row={
            "lineup":list(trio),
            "domains":{n:sorted(domains[n]) for n in trio},
            "scenario_count":repetitions,
        }
        for k in thresholds:
            sample=samples[k]
            row[f"model_probability_at_least_{k}_wins_mean"]=round(
                sum(sample)/len(sample),6)
            row[f"model_probability_at_least_{k}_wins_p10"]=round(
                quantile(sample,.10),6)
            row[f"model_probability_at_least_{k}_wins_p90"]=round(
                quantile(sample,.90),6)
        rows.append(row)
    rows.sort(key=lambda r:(
        -r["model_probability_at_least_7_wins_mean"],
        -r["model_probability_at_least_6_wins_mean"],r["lineup"]))
    for i,row in enumerate(rows,1):
        row["illustrative_seven_win_rank"]=i
    return rows


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--field",type=pathlib.Path,required=True)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--registry",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--repetitions",type=int,default=600)
    p.add_argument("--concentration",type=float,default=1.)
    p.add_argument("--seed",type=int,default=202611251100)
    args=p.parse_args()
    outcomes,domains,anchors,source=load_outcomes(args.field,args.selected,
                                                   args.registry)
    rows=evaluate(outcomes,domains,anchors,args.repetitions,
                  args.concentration,args.seed)
    if len(rows)!=919:
        raise RuntimeError("Expected exact 919 legal lineups in frozen full field")
    benchmark=set(["Draven, Glorious Executioner","LeBlanc, Deceiver",
                   "Master Yi, Wuju Bladesman"])
    key=next((r for r in rows if set(r["lineup"])==benchmark),None)
    if key is None:
        raise RuntimeError("Previously leading lineup vanished from legal field")
    report={
        "status":"ILLUSTRATIVE_NINE_ROUND_SWISS_TAIL_PROBABILITIES_ONLY",
        "all_lineups":len(rows),"repetitions":args.repetitions,
        "source":source["status"],
        "source_sha256":sha(args.field/"scenarios.json"),
        "frozen_ten_elite_anchors":anchors,
        "assumed_swiss_total_rounds":9,
        "assumed_matches_per_deck":3,
        "thresholds":[6,7,8],
        "rule_for_top4_qualification_assumed":False,
        "swiss_pairing_feedback_simulated":False,
        "sideboard_policy_used":False,
        "actual_worlds_win_probability_estimated":False,
        "prior_lineup_rank_in_seven_win_sensitivity":key["illustrative_seven_win_rank"],
        "prior_lineup_probability_record":key,
        "top20":rows[:20],
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"swiss_threshold_sensitivity.json").write_text(
        json.dumps(report,indent=2))
    (args.output/"all919_swiss_thresholds.json").write_text(json.dumps(rows,indent=2))
    print("SWISS_THRESHOLD_SENSITIVITY_COMPLETE",json.dumps({
        k:v for k,v in report.items() if k not in ("top20","prior_lineup_probability_record")
    }),flush=True)


if __name__=="__main__":
    main()
