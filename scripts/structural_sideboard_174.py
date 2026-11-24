#!/usr/bin/env python3
"""Use actual between-game 407 BO3 sideboarding to screen the remaining 174 variants.

All 580 structural registrations have passed native card validation. The 406
rune/battlefield/Champion variants have already been tested separately. The
174 sideboard-only variants are not playable improvements unless a Game 2/3
swap really happens. This module compares each new sideboard card against a
frozen original with a *separately chosen legal baseline swap policy*.

First-game Main, Runes, Battlefields and Chosen Champion are invariant between
candidate and control. Same-seed Game 1 winner MUST match (otherwise abort).
Actual Game 2/3 native C++ turn-state receipt and distinct swap-card effects
must be witnessed. Strict all-174 coverage; 24-search discovery only, no deck
adoption or unsupported claim about optimal sideboard policies.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))

from full_field_58 import mcnemar_exact
from optimize_58 import card_score, registry, stable_seed
from round_robin_58 import load_decks, sha
from sideboard_deck import parse_deck
from structural_deck_population import legal_registration
from tournament_bo3_policy import check_final_legality, run_series, transition
from structural_fitness_screen import opponents_for

KIND="sideboard"
COUNT=174


def sources(a):
    original,_=load_decks(a.selected)
    roster=json.loads((a.variants/"structural_manifest.json").read_text())
    native=json.loads(a.certification.read_text())
    ranked=json.loads(a.ranked.read_text())
    rows={x["legend"]:x for x in roster["records"]}
    if (roster.get("status")!="ALL58_REGISTERED_STRUCTURE_PROPOSALS_UNTESTED"
        or roster.get("legends")!=58
        or roster.get("variants_total")!=580
        or roster.get("families",{}).get(KIND)!=COUNT
        or roster.get("native_registry_sha256")!=sha(a.registry)
        or native.get("status")!="ALL_580_REGISTERED_STRUCTURAL_NATIVE_GAMES_PASS"
        or native.get("all_native_games_completed")!=580
        or native.get("native_game_failures")!=0
        or native.get("source_manifest_sha256")!=sha(a.variants/"structural_manifest.json")
        or native.get("original_decks_modified") is not False
        or len(ranked)!=58 or set(original)!=set(rows)
        or {r["legend"] for r in ranked}!=set(original)):
        raise RuntimeError("Sideboard-only 174 source is not full-field-native-certified")
    if any(rows[name]["original_sha256"]!=sha(original[name])
           for name in original):
        raise RuntimeError("Original registered deck hashes changed")
    if a.engine is not None and sha(a.engine)!=native["native_engine_sha256"]:
        raise RuntimeError("Wrong 407 C++ binary for exact native registration")
    return original,roster,native,ranked,rows


def deterministic_sideboard_plan(state,byname,*,require_in=None):
    """Choose the highest-scored legal one-for-one Main -> Side exchange.

    A changed variant MUST swap the exact newly registered tech card into
    the Main Deck. The original registered deck can instead choose its
    highest-scored legal tech card from its own Sideboard. Both have the
    identical Main and a legally valid 10-card registered Sideboard.
    Score is heuristic, NOT an empirically optimized opponent adaptation.
    """
    check_final_legality(state,state,byname)
    tag={state.legend.split(",",1)[0]}
    if require_in is not None:
        if state.sideboard.get(require_in,0)<1:
            raise RuntimeError("Novel tech card missing from candidate sideboard")
        side=[require_in]
    else:
        side=sorted(state.sideboard)
    proposals=[]
    for incoming in side:
        c=byname.get(incoming)
        if not c or "signature" in (c.get("super_type") or "").lower():
            continue
        if incoming=="Neeko, Blending In":
            continue
        for outgoing in sorted(state.main):
            x=byname.get(outgoing)
            if (not x or outgoing==incoming or
                "signature" in (x.get("super_type") or "").lower()):
                continue
            swap={"main_out":outgoing,"side_in":incoming,"copies":1}
            plan={"swaps":[swap]}
            try:
                transition(state,plan,byname,game_no=2)
            except ValueError:
                continue
            heuristic=(card_score(c,collections.Counter(),tag)-
                       card_score(x,collections.Counter(),tag))
            proposals.append((heuristic,outgoing,incoming,plan))
    if not proposals:
        raise RuntimeError("No actual legal 1-for-1 swap for registered sideboard")
    proposals.sort(key=lambda x:(-x[0],x[1],x[2]))
    best=proposals[0]
    return {"plan":best[3],"side_in":best[2],"main_out":best[1],
            "score_heuristic":round(best[0],5),
            "strategy":"one_predeclared_legal_swap_g2_g3"}


def case_schedule(name,ranked,seed):
    return [
        {"opponent":opponent,"seat":seat,
         "seed":stable_seed(seed,"SIDEBOARD_174_ACTUAL_407",name,opponent,seat)}
        for opponent in opponents_for(name,ranked,2)
        for seat in (0,1)
    ]


def play(a,target,other,case,byname,chosen):
    side=case["seat"]
    first,second=(target,other) if side==0 else (other,target)
    identity="p1" if side==0 else "p2"
    per_game={
        "game2":{identity:chosen["plan"],"loser_chooses_start":"self"},
        "game3":{identity:chosen["plan"],"loser_chooses_start":"self"}
    }
    r=run_series(a.engine,first,second,byname,per_game,
                 a.agent,case["seed"],a.timeout)
    if (r.get("status")!="COMPLETE_RULE407_START_POLICY_BO3"
        or r.get("rule_407_4_start_choice_verified") is not True
        or r.get("winner") not in (1,2)
        or not r.get("source_decks_return_to_registered_state_next_match")
        or len(r["games"]) not in (2,3)
        or not r.get("sideboarding_applied")
        or any(g.get("engine_status")!="complete" for g in r["games"])):
        raise RuntimeError("Native 407 BO3 incomplete or swap not used: "
                           +json.dumps(r)[-900:])
    card=chosen["side_in"]
    if r["games"][0].get("sideboard_swaps") not in ([[],[]],((),())):
        raise RuntimeError("Game 1 performed forbidden sideboard action")
    for g in r["games"][1:]:
        swaps=g["sideboard_swaps"][side]
        if (len(swaps)!=1 or swaps[0]["side_in"]!=card
            or swaps[0]["main_out"]!=chosen["main_out"]
            or swaps[0]["copies"]!=1
            or g["forced_start_verified"] is not True
            or g["verified_engine_starting_seat"]!=g["expected_engine_starting_seat"]):
            raise RuntimeError("Actual card swap or turn-start engine receipt absent")
    return {
        "target_win":int(r["winner"]==side+1),
        "game1_winner_seat":r["games"][0]["winner_seat"],
        "games_played":len(r["games"]),
        "actual_swaps":len(r["games"])-1,
        "rule_407_start_receipts_verified":True
    }


def paired_score(paired):
    if len(paired)!=4 or any(
        p["baseline_win"] not in (0,1) or p["candidate_win"] not in (0,1)
        for p in paired
    ):
        raise RuntimeError("Incomplete paired BO3 outcomes")
    a=sum(x["candidate_win"] and not x["baseline_win"] for x in paired)
    b=sum(x["baseline_win"] and not x["candidate_win"] for x in paired)
    return {"candidate_wins":sum(x["candidate_win"] for x in paired),
            "baseline_wins":sum(x["baseline_win"] for x in paired),
            "delta":sum(x["candidate_win"]-x["baseline_win"] for x in paired),
            "mcnemar_p_unadjusted":mcnemar_exact(a,b),
            "candidate_only":a,"baseline_only":b}


def screen(a):
    original,roster,native,ranked,rows=sources(a)
    if not a.engine.is_file():
        raise RuntimeError("Native C++ binary unavailable")
    byname=registry(a.registry)
    target_names=[n for i,n in enumerate(sorted(original))
                  if i%a.shards==a.shard]
    output=[]
    for name in target_names:
        base=original[name]
        base_state=parse_deck(base.read_text())
        sideboard=[v for v in rows[name]["variants"] if v["kind"]==KIND]
        case_list=case_schedule(name,ranked,a.seed)
        original_policy=deterministic_sideboard_plan(base_state,byname)
        original_games=[play(a,base,original[x["opponent"]],x,byname,original_policy)
                        for x in case_list]
        evaluated=[]
        for variant in sideboard:
            target=a.variants/variant["path"]
            if sha(target)!=variant["sha256"]:
                raise RuntimeError("Changed registered sideboard proposal")
            proposed=parse_deck(target.read_text())
            legal_registration(base_state,proposed,byname)
            if (proposed.main!=base_state.main or
                proposed.runes!=base_state.runes or
                proposed.battlefields!=base_state.battlefields or
                proposed.champion!=base_state.champion):
                raise RuntimeError("Sideboard-only variant unexpectedly alters Game 1")
            fresh=variant["changes"]["in"]
            policy=deterministic_sideboard_plan(proposed,byname,require_in=fresh)
            if policy["side_in"]!=fresh:
                raise RuntimeError("Proposed new sideboard card never gets played")
            games=[play(a,target,original[x["opponent"]],x,byname,policy)
                   for x in case_list]
            paired=[]
            for case,b,c in zip(case_list,original_games,games):
                # Both submitted lists have identical Game 1 *playable* cards
                # and neither game-1 deck may be sideboarded. Different
                # registered sideboards can perturb the engine's RNG/object
                # setup despite the same numeric seed. Record the divergence
                # as a real experimental limitation, not as an automatic
                # invalid win or a simulated sideboard benefit.
                paired.append({
                    **case,"baseline_win":b["target_win"],
                    "candidate_win":c["target_win"],
                    "game1_same_winner":(
                        b["game1_winner_seat"]==c["game1_winner_seat"]
                    ),
                    "game1_playable_cards_identical":True,
                    "baseline_swaps":b["actual_swaps"],
                    "candidate_swaps":c["actual_swaps"],
                    "actual_native_407_verified":True
                })
            evaluated.append({
                "kind":KIND,"path":variant["path"],
                "candidate_sha256":variant["sha256"],
                "registered_original_sha256":sha(base),
                "sideboard_added_card":fresh,
                "baseline_policy":original_policy,
                "candidate_policy":policy,
                "paired_completed":len(paired),
                "paired_receipts":paired,
                "score":paired_score(paired),
                "status":"ACTUAL_407_SIDEB0ARD_TECH_CARD_SCREEN_ONLY"
            })
            print("NEW_SIDEBOARD_CARD_407_FITNESS",name,
                  fresh,variant["sha256"][:10],
                  evaluated[-1]["score"]["delta"],flush=True)
        output.append({
            "legend":name,"registered_original_sha256":sha(base),
            "frozen_opponents":opponents_for(name,ranked,2),
            "baseline_policy":original_policy,"sideboard_proposals":evaluated
        })
    result={
        "status":"ALL58_NATIVE_SIDEB0ARD_174_DISCOVERY_PART",
        "shard":a.shard,"shards":a.shards,
        "registered_manifest_sha256":sha(a.variants/"structural_manifest.json"),
        "source_580_native_certification_sha256":sha(a.certification),
        "frozen_ranked_58_sha256":sha(a.ranked),
        "engine_sha256":sha(a.engine),
        "agent":a.agent,"seed":a.seed,
        "legends_expected":len(target_names),
        "legends_completed":len(output),
        "original_decks_modified":False,
        "sideboard_strategy":"Heuristic legal 1-swap in Games 2/3, not expert play",
        "results":output
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2))
    print("SIDEBOARD_174_NATIVE_407_SHARD_PASS",a.shard,len(output),flush=True)


def aggregate(a):
    original,roster,native,ranked,rows=sources(a)
    accepted={}
    for shard in range(a.shards):
        path=a.input/f"sideboard174-{shard}"/"sideboard_fitness.json"
        payload=json.loads(path.read_text())
        names=[n for i,n in enumerate(sorted(original))
               if i%a.shards==shard]
        if (payload.get("status")!="ALL58_NATIVE_SIDEB0ARD_174_DISCOVERY_PART"
            or payload.get("shard")!=shard
            or payload.get("shards")!=a.shards
            or payload.get("registered_manifest_sha256")!=sha(a.variants/"structural_manifest.json")
            or payload.get("source_580_native_certification_sha256")!=sha(a.certification)
            or payload.get("frozen_ranked_58_sha256")!=sha(a.ranked)
            or payload.get("engine_sha256")!=native["native_engine_sha256"]
            or payload.get("agent")!=a.agent or payload.get("seed")!=a.seed
            or payload.get("original_decks_modified") is not False
            or payload.get("legends_expected")!=len(names)
            or payload.get("legends_completed")!=len(names)
            or [x["legend"] for x in payload["results"]]!=names):
            raise RuntimeError("Unverified 174-sideboard shard: "+str(shard))
        for row in payload["results"]:
            name=row["legend"]
            expected=[x for x in rows[name]["variants"] if x["kind"]==KIND]
            if (name in accepted or row["registered_original_sha256"]!=sha(original[name])
                or row["frozen_opponents"]!=opponents_for(name,ranked,2)
                or len(expected)!=len(row["sideboard_proposals"])):
                raise RuntimeError("Altered registered family sideboard candidates")
            control_wins=None
            for rec,entry in zip(row["sideboard_proposals"],expected):
                if (rec["candidate_sha256"]!=entry["sha256"]
                    or rec["path"]!=entry["path"]
                    or rec["kind"]!=KIND
                    or rec["sideboard_added_card"]!=entry["changes"]["in"]
                    or rec["registered_original_sha256"]!=sha(original[name])
                    or rec["status"]!="ACTUAL_407_SIDEB0ARD_TECH_CARD_SCREEN_ONLY"
                    or rec["paired_completed"]!=4):
                    raise RuntimeError("Native sideboard registered proposal mismatched")
                data=rec["paired_receipts"]
                wanted=case_schedule(name,ranked,a.seed)
                if len(data)!=4:
                    raise RuntimeError("Missing BO3 sideboard receipt")
                if any(
                    any(p[k]!=w[k] for k in ("opponent","seat","seed"))
                    or p["baseline_win"] not in (0,1)
                    or p["candidate_win"] not in (0,1)
                    or p["game1_playable_cards_identical"] is not True
                    or not isinstance(p["game1_same_winner"],bool)
                    or p["actual_native_407_verified"] is not True
                    or p["baseline_swaps"]<1 or p["candidate_swaps"]<1
                    for p,w in zip(data,wanted)
                ):
                    raise RuntimeError("Native sideboard actual card swap missing")
                if rec["score"]!=paired_score(data):
                    raise RuntimeError("Changed paired scoreboard")
                base=[p["baseline_win"] for p in data]
                if control_wins is None:
                    control_wins=base
                elif control_wins!=base:
                    raise RuntimeError("Uncached original baseline for related variants")
            accepted[name]=row
    flat=[{"legend":name,**entry}
          for name in sorted(accepted)
          for entry in accepted[name]["sideboard_proposals"]]
    if len(accepted)!=58 or len(flat)!=COUNT:
        raise RuntimeError("Not all 174 registered sideboard cards played in native BO3")
    shortlist=sorted(flat,key=lambda x:(
        -x["score"]["delta"],-x["score"]["candidate_wins"],
        x["legend"],x["candidate_sha256"]
    ))
    game1_diff=sum(
        not q["game1_same_winner"] for x in flat
        for q in x["paired_receipts"]
    )
    summary={
        "status":"ALL174_SIDEB0ARD_VARIANTS_NATIVE_407_G2_G3_SCREEN_COMPLETE",
        "legends":58,"sideboard_variants_actually_played":COUNT,
        "paired_real_bo3_per_candidate":4,
        "game1_winner_mismatch_count":game1_diff,
        "game1_seed_coupling_warning":(
            "Identical registered main/runes/battlefields/champion and identical "
            "numeric seeds do NOT guarantee identical Game 1 trajectories "
            "when sideboard contents differ. Mismatches are recorded; "
            "candidate effect cannot be attributed solely to Game 2/3 tech."
        ),
        "candidate_bo3_completed":COUNT*4,
        "baseline_bo3_completed":58*4,
        "actual_new_sideboard_card_active_for_games_2_3":True,
        "native_engine_sha256":native["native_engine_sha256"],
        "source_manifest_sha256":sha(a.variants/"structural_manifest.json"),
        "strategy_quality":"Simple heuristic one-swap choices, not optimized or tournament prediction",
        "sideboard_card_preregistered_as_new":True,
        "strong_agent_independent_holdout_count":0,
        "confirmed_upgrades":0,"accepted_deck_changes":False,
        "best_unconfirmed_by_legend":[{
            "legend":name,
            "candidate_sha256":sorted(accepted[name]["sideboard_proposals"],
                key=lambda r:(-r["score"]["delta"],
                              -r["score"]["candidate_wins"],r["candidate_sha256"]))[0]["candidate_sha256"],
            "score":sorted(accepted[name]["sideboard_proposals"],
                key=lambda r:(-r["score"]["delta"],
                              -r["score"]["candidate_wins"],r["candidate_sha256"]))[0]["score"]
        } for name in sorted(accepted)]
    }
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/"summary.json").write_text(json.dumps(summary,indent=2))
    (a.output/"all_sideboard_policy_evidence.json").write_text(
        json.dumps(accepted,indent=2))
    (a.output/"ranked_unconfirmed_sideboard_proposals.json").write_text(
        json.dumps([{"legend":x["legend"],"candidate_sha256":x["candidate_sha256"],
                     "sideboard_added_card":x["sideboard_added_card"],
                     "sideboard_swap":x["candidate_policy"],"score":x["score"]}
                    for x in shortlist],indent=2))
    print("ALL174_ACTUAL_407_SIDEBOARD_POLICY_SCREEN_PASS",
          {k:v for k,v in summary.items()
           if k!="best_unconfirmed_by_legend"},flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ("selected","variants","registry","certification","ranked","output"):
        p.add_argument("--"+flag,type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--shards",type=int,default=29)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--seed",type=int,default=202611270101)
    p.add_argument("--agent",default="ismcts:sims=24")
    p.add_argument("--timeout",type=float,default=175)
    a=p.parse_args()
    if not 1<=a.shards<=58 or not 0<=a.shard<a.shards or a.timeout<=0:
        p.error("Invalid screen controls")
    if a.aggregate:
        if not a.input:
            p.error("Aggregation needs --input")
        aggregate(a)
    else:
        if a.engine is None:
            p.error("Real patched 407 engine is required")
        screen(a)


if __name__=="__main__":
    main()
