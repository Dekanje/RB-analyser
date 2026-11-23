#!/usr/bin/env python3
"""First matchup-specific legal BO3 sideboard policy search (research only).

Search 1-for-1 swaps, optional alternate Chosen Champion, and loser-first
choices on the actual corrected 407 AlphaRune engine. Initially pilot Draven
vs LeBlanc with frozen legal decks. Proposed policies are compared against
the original unchanged registered deck, with identical seeds and both seats.

No statistical acceptance: candidate selection and low simulation budget are
EXPLORATORY. Strict real-engine turn-state receipts on every Game 2/3.
"""
from __future__ import annotations
import argparse
import collections
import hashlib
import itertools
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from full_field_58 import mcnemar_exact
from optimize_58 import card_score,registry,stable_seed
from round_robin_58 import load_decks,sha
from sideboard_deck import parse_deck
from tournament_bo3_policy import transition,run_series,check_final_legality


def legal_plans(registered, byname, max_options=6, max_swap_depth=2):
    """Predeclare diverse 1-to-3-swap strategies with full structural legality."""
    if not 1 <= max_swap_depth <= 3:
        raise ValueError("Swap depth must be 1..3")
    check_final_legality(registered,registered,byname)
    main_names=sorted(registered.main)
    side_names=sorted(registered.sideboard)
    tag={registered.legend.split(", ",1)[0]}
    scored=[]
    for side in side_names:
        if side not in byname or side=="Neeko, Blending In":
            continue
        sc=byname[side]
        if "signature" in (sc.get("super_type") or "").lower():
            continue
        for own in main_names:
            if own not in byname or own==side:
                continue
            owncard=byname[own]
            if "signature" in (owncard.get("super_type") or "").lower():
                continue
            plan={"swaps":[{
                "main_out":own, "side_in":side,"copies":1
            }]}
            try:
                transition(registered,plan,byname,game_no=2)
            except ValueError:
                continue
            score=(card_score(sc,collections.Counter(),tag)-
                   card_score(owncard,collections.Counter(),tag))
            scored.append((score,own,side,plan))
    scored.sort(key=lambda x:(-x[0],x[1],x[2]))
    # Round-robin different sideboard cards FIRST. The previous heuristic
    # ranked three swaps all using the same Corrupt Enforcer; that does not
    # explore enough strategic diversity.
    selected=[];selected_pairs=set();represented_side=set();represented_main=set()
    for prefer_new_side in (True,False):
        for score,main_out,side_in,plan in scored:
            if (prefer_new_side and
                (side_in in represented_side or main_out in represented_main)):
                continue
            if (main_out,side_in) in selected_pairs:
                continue
            selected.append((score,main_out,side_in,plan))
            represented_side.add(side_in)
            represented_main.add(main_out)
            selected_pairs.add((main_out,side_in))
            if len(selected)>=max_options:
                break
        if len(selected)>=max_options:
            break
    choices=[]
    for score,main_out,side_in,plan in selected:
        choices.append({
            "plan":plan,"loser_chooses_start":"self",
            "heuristic_tech_swap_delta":round(score,4),
            "explanation":"Diversified one-card registered sideboard swap",
        })
    # Build wider multi-slot interactions from different Main and Side cards.
    # A double swap may perform differently from either swap in isolation.
    for depth in range(2,max_swap_depth+1):
        for group in itertools.combinations(selected,depth):
            old_cards=[x[1] for x in group]
            new_cards=[x[2] for x in group]
            if len(set(old_cards))!=depth or len(set(new_cards))!=depth:
                continue
            plan={"swaps":[x[3]["swaps"][0] for x in group]}
            try:
                transition(registered,plan,byname,game_no=2)
            except ValueError:
                continue
            choices.append({
                "plan":plan,"loser_chooses_start":"self",
                "heuristic_tech_swap_delta":round(sum(x[0] for x in group),4),
                "explanation":f"Predeclared legal {depth}-card sideboard combination",
            })
    # Opposite first-player choice tests the 407.4 strategic decision without
    # simultaneously changing card identities.
    choices.append({
        "plan":{},"loser_chooses_start":"opponent",
        "heuristic_tech_swap_delta":0,
        "explanation":"No sideboard changes; previous loser chooses opponent to play first",
    })
    for candidate in side_names+main_names:
        c=byname.get(candidate)
        if not c or candidate==registered.champion:
            continue
        if ("champion" not in (c.get("super_type") or "").lower()
            or candidate=="Neeko, Blending In"):
            continue
        plan={"chosen_champion":candidate}
        try:
            transition(registered,plan,byname,game_no=2)
        except ValueError:
            continue
        choices.append({
            "plan":plan,"loser_chooses_start":"self",
            "heuristic_tech_swap_delta":0,
            "explanation":"Use an alternative registered Chosen Champion",
        })
        break
    return choices


def schedule(legend,opponent,repetitions,seed):
    return [
        {"seat":seat,"rep":rep,
         "seed":stable_seed(seed,"TOURNAMENT_BO3_POLICY_V1",legend,opponent,seat,rep)}
        for seat in (0,1) for rep in range(repetitions)
    ]


def protocol_for(option,seat):
    # In seat 0 our deck is p1; in seat 1 our deck is p2.
    player="p1" if seat==0 else "p2"
    row={player:option["plan"],
         "loser_chooses_start":option["loser_chooses_start"]}
    return {"game2":row,"game3":row}


def play(engine,target,opponent,byname,option,case,agent,timeout):
    if case["seat"]==0:
        a,b=target,opponent
    else:
        a,b=opponent,target
    payload=run_series(
        engine,a,b,byname,
        protocol_for(option,case["seat"]),
        agent,case["seed"],timeout
    )
    accepted=(payload["status"]=="COMPLETE_RULE407_START_POLICY_BO3" and
              payload["rule_407_4_start_choice_verified"] is True and
              payload["winner"] in (1,2) and
              all(g["engine_status"]=="complete" for g in payload["games"]))
    if not accepted:
        raise RuntimeError("Actual sideboard BO3 failed; no win assigned: "
                           +json.dumps(payload)[-1000:])
    my_seat=case["seat"]+1
    return {
        "seat":case["seat"],"rep":case["rep"],"seed":case["seed"],
        "target_win":int(payload["winner"]==my_seat),
        "game_count":len(payload["games"]),
        "forced_start_receipts":[{
            "game":g["game"],"loser":g["previous_game_loser_identity"],
            "chosen":g["loser_chose"],
            "requested":g["expected_engine_starting_seat"],
            "actual":g["verified_engine_starting_seat"],
        } for g in payload["games"][1:]],
    }


def evaluate(args):
    decks,_=load_decks(args.selected)
    if args.legend not in decks or args.opponent not in decks or args.legend==args.opponent:
        raise RuntimeError("Legend or opponent missing from unchanged 58-deck roster")
    if not args.engine.is_file():
        raise RuntimeError("Compilied rule-407 engine binary required")
    byname=registry(args.registry)
    registered=parse_deck(decks[args.legend].read_text(encoding="utf-8"))
    check_final_legality(registered,registered,byname)
    options=legal_plans(registered,byname,args.max_tech_options,
                        args.max_swap_depth)
    if len(options)<2:
        raise RuntimeError("No independent sideboard/start choices generated")
    cases=schedule(args.legend,args.opponent,args.repetitions,args.seed)
    frozen={"plan":{},"loser_chooses_start":"self"}
    baseline=[
        play(args.engine,decks[args.legend],decks[args.opponent],
             byname,frozen,c,args.agent,args.timeout)
        for c in cases
    ]
    records=[]
    for i,option in enumerate(options):
        trials=[
            play(args.engine,decks[args.legend],decks[args.opponent],
                 byname,option,c,args.agent,args.timeout)
            for c in cases
        ]
        own=sum(x["target_win"] for x in trials)
        source=sum(x["target_win"] for x in baseline)
        wins_only=sum(x["target_win"] and not b["target_win"]
                      for x,b in zip(trials,baseline))
        baseline_only=sum(b["target_win"] and not x["target_win"]
                          for x,b in zip(trials,baseline))
        record={
            "candidate_index":i,"option":option,
            "candidate_wins":own,"baseline_wins":source,
            "delta":own-source,
            "mcnemar_p_unadjusted":mcnemar_exact(wins_only,baseline_only),
            "paired_series":len(trials),"cases":trials,
            "status":"EXPLORATORY_NO_HOLDOUT",
        }
        records.append(record)
        print("SIDEBOARD_POLICY_SCREEN",args.legend,i,
              "delta",record["delta"],"of",len(trials),flush=True)
    records.sort(key=lambda r:(-r["delta"],-r["candidate_wins"],r["candidate_index"]))
    payload={
        "status":"SINGLE_MATCHUP_STRATEGIC_BO3_POLICY_SCREEN_ONLY",
        "legend":args.legend,"opponent":args.opponent,
        "deck_sha256":sha(decks[args.legend]),
        "opponent_sha256":sha(decks[args.opponent]),
        "engine_sha256":sha(args.engine),
        "registry_sha256":sha(args.registry),
        "agent":args.agent,"seed":args.seed,"repetitions":args.repetitions,
        "search_candidates":len(options),
        "baseline_completed_series":len(baseline),
        "candidate_completed_series":len(cases)*len(options),
        "loser_chooses_first_verified":True,
        "sideboard_is_optimized":False,
        "holdout_confirmation":False,
        "any_deck_changes_adopted":False,
        "baseline_games":baseline,
        "candidate_results":records,
    }
    args.output.mkdir(parents=True,exist_ok=True)
    (args.output/"sideboard_policy_screen.json").write_text(
        json.dumps(payload,indent=2),encoding="utf-8"
    )
    print("SIDEBOARD_POLICY_SCREEN_FINAL",
          json.dumps({k:v for k,v in payload.items()
                      if k not in ("baseline_games","candidate_results")}),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--selected",type=pathlib.Path,required=True)
    parser.add_argument("--engine",type=pathlib.Path,required=True)
    parser.add_argument("--registry",type=pathlib.Path,required=True)
    parser.add_argument("--output",type=pathlib.Path,required=True)
    parser.add_argument("--legend",default="Draven, Glorious Executioner")
    parser.add_argument("--opponent",default="LeBlanc, Deceiver")
    parser.add_argument("--max-tech-options",type=int,default=3)
    parser.add_argument("--max-swap-depth",type=int,default=2)
    parser.add_argument("--agent",default="ismcts:sims=24")
    parser.add_argument("--seed",type=int,default=202611240818)
    parser.add_argument("--repetitions",type=int,default=2)
    parser.add_argument("--timeout",type=float,default=200)
    a=parser.parse_args()
    if (not 1<=a.max_tech_options<=20 or
        not 1<=a.max_swap_depth<=3 or
        not 1<=a.repetitions<=10 or a.timeout<=0):
        parser.error("Invalid policy exploration budget")
    evaluate(a)


if __name__=="__main__":
    main()
