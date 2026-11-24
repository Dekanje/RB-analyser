#!/usr/bin/env python3
"""Explore three-deck six-domain lineups from fixed-deck 58-vs-elite evidence.

This is an exploratory screening model. It does NOT estimate probability of
winning Worlds. No sideboarding, opponent-adaptive elite metagame weighting,
playoff-specific agents or human skill is modeled. Sampling uncertainty is
quantified by resampling the ten opponent-archetype blocks.
"""
from __future__ import annotations
import argparse
import collections
import csv
import itertools
import json
import pathlib
import random
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from optimize_58 import effective_domains, registry
from round_robin_58 import load_decks, sha


def load_outcomes(field_dir, selected_dir, registry_file):
    meta=json.loads((field_dir/"summary.json").read_text())
    if (meta["status"]!="EXPLORATORY_58_VS_TOP10_128_ISMCTS_COMPLETE" or
        not meta["all_games_complete"] or meta["agent"]!="ismcts:sims=128" or
        meta["sideboarding"] is not False or meta["completed_bo3_series"]!=1140):
        raise RuntimeError("Unaccepted or incomplete 58-versus-elite evidence")
    game_rows=json.loads((field_dir/"scenarios.json").read_text())
    standings=json.loads((field_dir/"standings.json").read_text())
    if len(game_rows)!=1140 or len(standings)!=58:
        raise RuntimeError("Wrong full-field size")
    decks,_=load_decks(selected_dir)
    if set(decks)!={x["legend"] for x in standings}:
        raise RuntimeError("Different 58-Legend deck roster")
    byname=registry(registry_file)
    domains={}
    for n in decks:
        domains[n]=effective_domains(n,byname)
    anchors=sorted({x["anchor"] for x in game_rows})
    if len(anchors)!=10:
        raise RuntimeError("Expected exactly ten elite anchors")
    matches=collections.defaultdict(list)
    seen=set()
    for row in game_rows:
        if (not row["complete"] or row["status"]!="complete" or
            row["target_win"] not in (True,False) or
            row["target"] not in decks or row["anchor"] not in anchors or
            row["target"]==row["anchor"] or
            row["target_sha256"]!=sha(decks[row["target"]])):
            raise RuntimeError("Invalid completed elite-field sample")
        key=(row["target"],row["anchor"],row["seat"],row["repetition"])
        if key in seen:
            raise RuntimeError("Duplicate engine outcome")
        seen.add(key)
        matches[(row["target"],row["anchor"])].append(row["target_win"])
    observed={}
    for n in decks:
        for a in anchors:
            values=matches.get((n,a),[])
            if n==a:
                if values:
                    raise RuntimeError("Unexpected self-play anchor")
                observed[(n,a)]=0.5
            else:
                if len(values)!=2:
                    raise RuntimeError("Missing both-seat engine outcomes")
                observed[(n,a)]=sum(values)/2
    for r in standings:
        n=r["legend"]
        if sha(decks[n])!=r["deck_sha256"]:
            raise RuntimeError("Selected deck source SHA drift")
        if len(domains[n])!=2:
            raise RuntimeError("Unexpected single/multiple-domain Legend")
    return observed,domains,anchors,meta


def compatible_triples(domains:dict[str,set]) -> list[tuple[str,str,str]]:
    names=sorted(domains)
    valid=[]
    for a,b,c in itertools.combinations(names,3):
        if (domains[a]&domains[b] or domains[a]&domains[c] or
            domains[b]&domains[c]):
            continue
        if len(domains[a]|domains[b]|domains[c])==6:
            valid.append((a,b,c))
    return valid


def rank_lineups(
    outcomes:dict,
    domains:dict,
    anchors:list,
    resamples:int=200,
    seed:int=202611240404,
):
    triples=compatible_triples(domains)
    if not triples:
        raise RuntimeError("No Worlds-compatible three-deck lineup")
    rates={n:sum(outcomes[(n,a)] for a in anchors)/len(anchors)
           for n in domains}
    main=[]
    for trio in triples:
        members=sorted(trio,key=lambda x:(-rates[x],x))
        value=sum(rates[x] for x in trio)/3
        main.append({
            "legends":list(trio),
            "domains":{n:sorted(domains[n]) for n in trio},
            "exploratory_swiss_expected_wins":round(9*value,4),
            "exploratory_mean_match_rate":round(value,6),
            "lowest_member_match_rate":round(min(rates[x] for x in trio),6),
            "playoff_candidate":members[0],
            "playoff_candidate_elite_rate":round(rates[members[0]],6),
        })
    main.sort(key=lambda r:(-r["exploratory_mean_match_rate"],
                            -r["lowest_member_match_rate"],r["legends"]))
    # Global anchor-block bootstrap: an archetype is resampled as a block,
    # preserving correlation of results across candidate Legends.
    rng=random.Random(seed)
    wins=collections.Counter()
    for rep in range(resamples):
        sampled=[rng.choice(anchors) for _ in anchors]
        sampled_rates={n:sum(outcomes[(n,a)] for a in sampled)/len(sampled)
                       for n in domains}
        maximum=max(
            sum(sampled_rates[n] for n in triple)
            for triple in triples
        )
        leaders=[trio for trio in triples
                 if abs(sum(sampled_rates[n] for n in trio)-maximum)<1e-10]
        # Deterministic fractional tie assignment avoids alphabetical bias.
        for trio in leaders:
            wins[trio]+=1/len(leaders)
    for row in main:
        row["bootstrap_best_lineup_frequency"]=round(
            wins[tuple(row["legends"])]/resamples,4
        )
    return main


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--field",type=pathlib.Path,required=True)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--registry",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--bootstrap",type=int,default=200)
    p.add_argument("--seed",type=int,default=202611240404)
    args=p.parse_args()
    if not 10<=args.bootstrap<=5000:
        p.error("Bootstrap resamples must be 10-5000")
    data,dom,anchors,source=load_outcomes(
        args.field,args.selected,args.registry
    )
    ranked=rank_lineups(data,dom,anchors,args.bootstrap,args.seed)
    args.output.mkdir(parents=True,exist_ok=True)
    report={
        "status":"HYPOTHETICAL_WORLDS_LINEUP_EXPLORATORY_NOT_PREDICTION",
        "rules":"Three decks, pairwise disjoint domains, OGN/SFD/UNL/VEN/RAD only; Legacy illegal",
        "all_lineups_evaluated":len(ranked),
        "field_source":source["status"],
        "worlds_win_probability_estimated":False,
        "bootstrap_resamples":args.bootstrap,
        "bootstrap_best_lineup_frequency_is_not_tournament_win_chance":True,
        "anchor_self_play_handling":"Imputed exactly 50% for a Legend against its own elite-anchor entry",
        "assumptions":[
            "Ten elite anchors receive equal opponent weights",
            "Every selected deck plays 3 Swiss rounds for an equal nine-round schedule",
            "Top-four qualification and playoff formats are not simulated",
            "Individual games have no sideboard changes",
            "Agents use ISMCTS 128 with low game counts and are not expert-calibrated",
        ],
        "top_20":ranked[:20],
    }
    (args.output/"lineups.json").write_text(
        json.dumps(report,indent=2),encoding="utf-8"
    )
    with (args.output/"top20.csv").open("w",newline="",encoding="utf-8") as f:
        w=csv.writer(f)
        w.writerow(["rank","deck_a","deck_b","deck_c","expected_swiss_wins_sampled",
                    "mean_elite_match_rate","lowest_deck_rate",
                    "playoff_candidate","bootstrap_best_lineup_frequency"])
        for i,row in enumerate(ranked[:20],1):
            w.writerow([i,*row["legends"],row["exploratory_swiss_expected_wins"],
                        row["exploratory_mean_match_rate"],
                        row["lowest_member_match_rate"],
                        row["playoff_candidate"],
                        row["bootstrap_best_lineup_frequency"]])
    print("WORLDS_LINEUP_EXPLORATORY",json.dumps({
        "lineup_count":len(ranked),"best":ranked[0],
        "bootstrap":args.bootstrap,"not_worlds_win_prob":True
    }),flush=True)


if __name__=="__main__":
    main()
