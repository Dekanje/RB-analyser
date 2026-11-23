#!/usr/bin/env python3
"""407-enabled sideboard policy holdout across exact and unseen elite opponents.

Three pilot strategies are preregistered before this evaluation. Each targets
two frozen elite Legends: one was screened previously (new seeds only), one
was not seen during that policy's four-series screen.

Experimental method: 128-sim ISMCTS, same 407 native engine + seat/seed for
baseline versus changed policy, two repetitions per seating order. Each
paired unit is a completed best-of-three match, not a single game. Strict
fail-closed receipts, pooled Holm control, and no automatic acceptance.

We do not model real human-player sideboarding, tournament round clock or
post-selection metagame. No adjustment is made to the registered decks.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from full_field_58 import holm,mcnemar_exact
from optimize_58 import registry,stable_seed
from round_robin_58 import load_decks,sha
from sideboard_deck import parse_deck
from sideboard_policy_search import play
from tournament_bo3_policy import transition


def load_inputs(args):
    selected=json.loads(args.selection.read_text(encoding="utf-8"))
    if (selected.get("schema")!=1 or
        selected.get("status")!="PREREGISTERED_407_POLICY_HOLDOUT_NO_ADOPTION" or
        selected.get("pilot_aggregate_run")!=45251930166 or
        selected.get("verified_407_engine_run")!=45244227502 or
        selected.get("repetitions")!=args.repetitions or
        selected.get("agent")!=args.agent or
        selected.get("new_seed")!=args.seed or
        selected.get("hypotheses")!=3 or
        len(selected.get("choices",[]))!=3):
        raise RuntimeError("Holdout experiment changed after registration")
    if (selected["aggregated_file_sha256"]!=sha(args.pilot):
        raise RuntimeError("Actual frozen pilot artifact bytes do not match")
    pilot=json.loads(args.pilot.read_text(encoding="utf-8"))
    if set(pilot)!={"draven-vs-miss-fortune","leblanc-vs-reksai","masteryi-vs-ambessa"}:
        raise RuntimeError("Wrong initial pilot source artifact")
    originals,_=load_decks(args.selected)
    byname=registry(args.registry)
    if set(x["legend"] for x in selected["choices"])!={
        "Draven, Glorious Executioner","LeBlanc, Deceiver","Master Yi, Wuju Bladesman"
    }:
        raise RuntimeError("Wrong preregistered Worlds lineup")
    for p in selected["choices"]:
        name=p["legend"];index=p["policy_index"];match=p["source_matchup"]
        row=next((x for x in pilot[match] if x["policy_index"]==index),None)
        if (not row or row["legend"]!=name or
            row["candidate_minus_baseline"]<0 or
            row["policy"]["plan"]!=p["plan"] or
            row["policy"]["loser_chooses_start"]!=p["loser_chooses_start"]):
            raise RuntimeError("Selected strategy does not match actual prior screening")
        if len(p["opponents"])!=2 or p["opponents"][0]!=row["opponent"]:
            raise RuntimeError("Missing original opponent for independent new seeds")
        if any(x not in originals or x==name for x in p["opponents"]) or (
            p["opponents"][0]==p["opponents"][1]):
            raise RuntimeError("Holdout opponent has unavailable source deck")
        registered=parse_deck(originals[name].read_text(encoding="utf-8"))
        transition(registered,p["plan"],byname,game_no=2)
        transition(registered,p["plan"],byname,game_no=3)
    return selected,pilot,originals,byname


def cases_for(legend, opponent, repetitions, seed):
    return [
        {"seat":seat,"rep":rep,
         "seed":stable_seed(seed,"BO3_407_SIDEBOARD_HOLDOUT_V1",
                            legend,opponent,seat,rep)}
        for seat in (0,1) for rep in range(repetitions)
    ]


def test_one(args):
    selection,pilot,decks,byname=load_inputs(args)
    choice=selection["choices"][args.index]
    if not args.engine.is_file():
        raise RuntimeError("Native 407 engine binary missing")
    baseline={"plan":{},"loser_chooses_start":"self"}
    experimental={"plan":choice["plan"],
                  "loser_chooses_start":choice["loser_chooses_start"]}
    all_cases=[]
    for opponent in choice["opponents"]:
        for case in cases_for(choice["legend"],opponent,args.repetitions,args.seed):
            original=play(args.engine,decks[choice["legend"]],
                          decks[opponent],byname,baseline,case,args.agent,args.timeout)
            modified=play(args.engine,decks[choice["legend"]],
                          decks[opponent],byname,experimental,case,args.agent,args.timeout)
            if any((
                (original["seat"],original["rep"],original["seed"])!=
                (modified["seat"],modified["rep"],modified["seed"]),
                original["game1_winner_seat"]!=modified["game1_winner_seat"],
                not original["forced_start_receipts"],
                not modified["forced_start_receipts"]
            )):
                raise RuntimeError("Game 1 divergence or missing actual 407 receipts")
            all_cases.append({
                "opponent":opponent,**case,
                "baseline_win":original["target_win"],
                "candidate_win":modified["target_win"],
                "game1_winner_seat":original["game1_winner_seat"],
                "baseline_407_receipts":original["forced_start_receipts"],
                "candidate_407_receipts":modified["forced_start_receipts"],
            })
            print("INDEPENDENT_407_POLICY_MATCH",choice["legend"],
                  opponent,case["seat"],case["rep"],
                  original["target_win"],modified["target_win"],flush=True)
    expected=4*args.repetitions
    if len(all_cases)!=expected:
        raise RuntimeError("Incomplete preregistered sideboard BO3 holdout")
    a=sum(r["candidate_win"]==1 and r["baseline_win"]==0 for r in all_cases)
    b=sum(r["candidate_win"]==0 and r["baseline_win"]==1 for r in all_cases)
    record={
        "status":"ACTUAL_407_POLICY_HOLDOUT_COMPLETED_NOT_ADOPTED",
        "index":args.index,"legend":choice["legend"],
        "original_source_matchup":choice["source_matchup"],
        "chosen_policy_index":choice["policy_index"],
        "selected_option":experimental,
        "original_deck_sha256":sha(decks[choice["legend"]]),
        "frozen_opponent_decks_sha256":{name:sha(decks[name])
                                     for name in choice["opponents"]},
        "selection_sha256":sha(args.selection),
        "pilot_sha256":sha(args.pilot),
        "engine_sha256":sha(args.engine),
        "registry_sha256":sha(args.registry),
        "agent":args.agent,"seed":args.seed,
        "repetitions":args.repetitions,
        "holdout_opponents":choice["opponents"],
        "new_second_opponent":True,
        "candidate_completed_series":len(all_cases),
        "baseline_completed_series":len(all_cases),
        "candidate_wins":sum(r["candidate_win"] for r in all_cases),
        "baseline_wins":sum(r["baseline_win"] for r in all_cases),
        "candidate_only_wins":a,"baseline_only_wins":b,
        "mcnemar_p":mcnemar_exact(a,b),
        "cases":all_cases,
        "automatic_deck_or_policy_adoption":False,
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"holdout.json").write_text(json.dumps(record,indent=2),encoding="utf-8")
    print("INDEPENDENT_407_POLICY_COMPLETED",record["legend"],
          record["candidate_wins"],record["baseline_wins"],record["mcnemar_p"])


def aggregate(args):
    selection,pilot,decks,byname=load_inputs(args)
    tested=[];binary_hashes=set()
    for i,choice in enumerate(selection["choices"]):
        p=args.input/f"competitive-407-policy-holdout-{i}"/"holdout.json"
        result=json.loads(p.read_text(encoding="utf-8"))
        expected=4*args.repetitions
        if any((
            result["status"]!="ACTUAL_407_POLICY_HOLDOUT_COMPLETED_NOT_ADOPTED",
            result["index"]!=i,
            result["legend"]!=choice["legend"],
            result["original_source_matchup"]!=choice["source_matchup"],
            result["chosen_policy_index"]!=choice["policy_index"],
            result["selected_option"]!={"plan":choice["plan"],
                "loser_chooses_start":choice["loser_chooses_start"]},
            result["original_deck_sha256"]!=sha(decks[choice["legend"]]),
            result["frozen_opponent_decks_sha256"]!={n:sha(decks[n])
                                                    for n in choice["opponents"]},
            result["selection_sha256"]!=sha(args.selection),
            result["pilot_sha256"]!=sha(args.pilot),
            result["agent"]!=args.agent or result["seed"]!=args.seed or
            result["repetitions"]!=args.repetitions,
            result["holdout_opponents"]!=choice["opponents"],
            result["new_second_opponent"] is not True,
            result["candidate_completed_series"]!=expected,
            result["baseline_completed_series"]!=expected,
            result["automatic_deck_or_policy_adoption"] is not False
        )):
            raise RuntimeError("Wrong-source or incomplete actual 407 evidence")
        binary_hashes.add(result["engine_sha256"])
        rows=result["cases"]
        schedule=[
            {"opponent":n,**c}
            for n in choice["opponents"]
            for c in cases_for(choice["legend"],n,args.repetitions,args.seed)
        ]
        if len(rows)!=len(schedule):
            raise RuntimeError("Missing 407 paired game receipts")
        for case,expected_case in zip(rows,schedule):
            if (any(case[k]!=expected_case[k]
                    for k in ("opponent","seat","rep","seed")) or
                case["candidate_win"] not in (0,1) or
                case["baseline_win"] not in (0,1) or
                case["game1_winner_seat"] not in (1,2) or
                not case["baseline_407_receipts"] or
                not case["candidate_407_receipts"]):
                raise RuntimeError("Missing/invalid actual engine BO3 outcome")
            for row in case["baseline_407_receipts"]+case["candidate_407_receipts"]:
                if row["requested"]!=row["actual"] or row["actual"] not in (1,2):
                    raise RuntimeError("Unverified actual first player")
        a=sum(x["candidate_win"] and not x["baseline_win"] for x in rows)
        b=sum(x["baseline_win"] and not x["candidate_win"] for x in rows)
        if (a!=result["candidate_only_wins"] or b!=result["baseline_only_wins"]
            or sum(x["candidate_win"] for x in rows)!=result["candidate_wins"]
            or sum(x["baseline_win"] for x in rows)!=result["baseline_wins"]
            or abs(mcnemar_exact(a,b)-result["mcnemar_p"])>1e-12):
            raise RuntimeError("Invalid paired McNemar evidence")
        tested.append({
            "legend":choice["legend"],"opponents":choice["opponents"],
            "candidate_policy_index":choice["policy_index"],
            "original_deck_sha256":result["original_deck_sha256"],
            "changed":True,"incomplete":0,
            "candidate_wins":result["candidate_wins"],
            "baseline_wins":result["baseline_wins"],
            "mcnemar_p":result["mcnemar_p"],
            "paired_series":len(rows),
        })
    if len(binary_hashes)!=1:
        raise RuntimeError("Differing 407 native engines in hypothesis family")
    holm(tested)
    # Statistical improvement is conditional on fixed opponents and artificial
    # strategic agents, never directly changes registered lists or Worlds meta.
    for row in tested:
        row["statistically_positive_signal"]=row["independently_confirmed"]
        row["policy_accepted_for_worlds"]=False
        row["reason"]="Not tested in Swiss, against expert policies or across full World metagame"
    summary={
        "status":"THREE_407_SIDEBOARD_POLICIES_HOLDOUT_COMPLETE",
        "hypotheses_tested":3,
        "completed_paired_bo3":sum(x["paired_series"] for x in tested),
        "agent":args.agent,"repetitions":args.repetitions,
        "native_407_engine_sha256":next(iter(binary_hashes)),
        "different_from_training_seeds":True,
        "original_and_new_opponent_per_policy":True,
        "familywise_adjustment":"Holm FWER 0.05 for 3 preregistered policies",
        "statistically_positive":sum(x["statistically_positive_signal"] for x in tested),
        "registered_decklists_unchanged":True,
        "sideboard_policies_automatically_adopted":False,
        "real_worlds_achievement_probability":False,
        "results":tested,
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"decision.json").write_text(json.dumps(summary,indent=2))
    print("407_POLICY_HOLDOUT_FINAL",json.dumps(summary),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selection",type=pathlib.Path,required=True)
    p.add_argument("--pilot",type=pathlib.Path,required=True)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--registry",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,default=pathlib.Path("engine_build/riftbound"))
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--index",type=int,default=0)
    p.add_argument("--agent",default="ismcts:sims=128")
    p.add_argument("--seed",type=int,default=202611250531)
    p.add_argument("--repetitions",type=int,default=2)
    p.add_argument("--timeout",type=float,default=240)
    args=p.parse_args()
    if not 0<=args.index<3 or not 1<=args.repetitions<=10 or args.timeout<=0:
        p.error("Invalid controlled holdout parameters")
    if args.aggregate:
        if not args.input:
            p.error("--aggregate requires --input")
        aggregate(args)
    else:
        test_one(args)


if __name__=="__main__":
    main()
