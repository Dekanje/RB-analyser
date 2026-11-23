#!/usr/bin/env python3
"""Robustness study of 919 Worlds-compatible lineups, NOT Worlds predictions.

Use only completed, pinned 58-vs-ten-elite ISMCTS BO3 outcomes. Mix opponents
with a fixed-seed Dirichlet distribution to model unknown Worlds composition;
sample Beta(.5,.5) posterior per *observed matchup* (2 seat-mirrored BO3).
For a Legend versus identical anchor, symmetry fixes chance 50%.

Output posterior predictive expected Swiss series wins under fixed-deck
agents, not real event performance. No deck/sideboard changes or league wins
are inferred. The tournament's Swiss cut and playoff path are not simulated.
"""
from __future__ import annotations
import argparse
import json
import math
import pathlib
import random
import statistics
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from worlds_lineups import load_outcomes,compatible_triples
from round_robin_58 import sha


def quantile(xs, fractional):
    if not xs:
        raise ValueError("Cannot take quantile of empty list")
    sorted_x=sorted(xs)
    index=(len(sorted_x)-1)*fractional
    lower=math.floor(index); upper=math.ceil(index)
    return sorted_x[lower]*(upper-index)+sorted_x[upper]*(index-lower) if lower!=upper else sorted_x[lower]


def evaluate_robustness(outcomes,domains,anchors,repetitions=500,concentration=1.0,
                        seed=202611240900):
    if repetitions<20 or concentration<=0 or len(anchors)!=10:
        raise ValueError("Invalid robust lineup experiment size")
    triples=compatible_triples(domains)
    if not triples:
        raise ValueError("No three disjoint-domain decks")
    names=sorted(domains)
    metrics={trio:[] for trio in triples}
    playoffs={trio:[] for trio in triples}
    rng=random.Random(seed)
    for rep in range(repetitions):
        # A common opponent mix and a common matchup sample for all lineups
        # avoids giving one lineup a more favorable world than another.
        weights=[rng.gammavariate(concentration,1.) for _ in anchors]
        total=sum(weights); weights=[w/total for w in weights]
        rates={}
        for name in names:
            value=0.
            for anchor,w in zip(anchors,weights):
                if name==anchor:
                    matchup=0.5  # fixed-deck mirror must be symmetric
                else:
                    pair=outcomes[(name,anchor)]
                    # Each observed nonmirror is two real BO3 (one each seat).
                    wins=round(2*pair)
                    if abs(wins-2*pair)>1e-8 or wins not in (0,1,2):
                        raise RuntimeError("Unsupported/nonbinary observed BO3 exposure")
                    matchup=rng.betavariate(wins+0.5,2-wins+0.5)
                value+=w*matchup
            rates[name]=value
        for trio in triples:
            # Exactly three Swiss rounds assigned to each registered deck.
            metrics[trio].append(3*sum(rates[n] for n in trio))
            # Playoff candidate is chosen before tournament; max sampled
            # here measures *potential*, not a finalized designation.
            playoffs[trio].append(max(rates[n] for n in trio))
    ranked=[]
    for trio in triples:
        swiss=metrics[trio]
        playoff=playoffs[trio]
        ranked.append({
            "lineup":list(trio),
            "domains":{n:sorted(domains[n]) for n in trio},
            "swiss_expected_wins_mean":round(statistics.mean(swiss),5),
            "swiss_expected_wins_p10":round(quantile(swiss,.1),5),
            "swiss_expected_wins_p50":round(quantile(swiss,.5),5),
            "swiss_expected_wins_p90":round(quantile(swiss,.9),5),
            "playoff_best_member_rate_mean":round(statistics.mean(playoff),5),
            "sampled_worlds":repetitions,
        })
    ranked.sort(key=lambda r:(-r["swiss_expected_wins_p10"],
                              -r["swiss_expected_wins_mean"],r["lineup"]))
    for rank,item in enumerate(ranked,1):
        item["robust_swiss_rank"]=rank
    return ranked


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--field",type=pathlib.Path,required=True)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--registry",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--worlds",type=int,default=600)
    p.add_argument("--concentration",type=float,default=1.)
    p.add_argument("--seed",type=int,default=202611240900)
    args=p.parse_args()
    outcomes,domains,anchors,meta=load_outcomes(args.field,args.selected,args.registry)
    ranked=evaluate_robustness(outcomes,domains,anchors,args.worlds,
                               args.concentration,args.seed)
    args.output.mkdir(parents=True,exist_ok=True)
    packet={
        "status":"EXPLORATORY_FIXED_DECK_ROBUSTNESS_NOT_WORLDS_WIN_CHANCE",
        "source":meta["status"],
        "source_sha256":sha(args.field/"scenarios.json"),
        "source_engine_sha256":meta["engine_sha256"],
        "legends":58,
        "compatible_lineups":len(ranked),
        "worlds":args.worlds,
        "dirichlet_concentration":args.concentration,
        "posterior":"Beta(0.5,0.5) prior + two mirrored BO3 series per nonmirror matchup",
        "sampled_opponent_field":"Ten frozen elite decks with randomized weights; no archetypes asserted",
        "statistical_note":"p10/p90 concern modeled expected Swiss wins, NOT realized tournament wins",
        "no_sideboarding":True,
        "no_actual_playoff_qualification_simulated":True,
        "no_top_four_qualification_simulated":True,
        "result_is_worlds_win_probability":False,
        "baseline_decks_modified":False,
        "top20_robust":ranked[:20],
    }
    (args.output/"robust_lineups.json").write_text(json.dumps(packet,indent=2))
    (args.output/"all_919_robust.json").write_text(json.dumps(ranked,indent=2))
    print("ROBUST_WORLDS_LINEUPS",json.dumps({
        k:v for k,v in packet.items() if k not in ("top20_robust",)
    }),flush=True)


if __name__=="__main__":
    main()
