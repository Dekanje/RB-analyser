#!/usr/bin/env python3
"""Independent elite-panel 407 BO3 confirmation for real sideboard-card proposals.

Preregister 12 distinct-Legend source-hashed proposals from 174 completed
24-ISMCTS actual-swap screens. Confirm a registered sideboard + fixed legal
heuristic policy PACKAGE, not an isolated card effect. A changed registered
Sideboard can perturb native Game 1 RNG stream with the same numeric seed:
record winner mismatches but do not invent identical game-1 trajectories.

All new opponents are disjoint from the two initial screen opponents.
128 ISMCTS; six opponent decks × 2 seats × 2 reps = 24 BO3 per contender,
each paired against the untouched original with its own frozen sideboard
policy. Holm FWER 5% across the twelve preregistered hypotheses. Do not auto
modify any registered deck even when a statistical signal is observed.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))

from full_field_58 import holm,mcnemar_exact
from optimize_58 import registry,stable_seed
from round_robin_58 import load_decks,sha
from sideboard_deck import parse_deck
from structural_deck_population import legal_registration
from structural_sideboard_174 import COUNT,KIND,deterministic_sideboard_plan
from structural_fitness_screen import opponents_for
from tournament_bo3_policy import run_series,transition

FAMILY=12
OPPONENTS_HELD_OUT=6


def sources(a):
    originals,_=load_decks(a.selected)
    manifest=json.loads((a.variants/"structural_manifest.json").read_text())
    native=json.loads(a.certification.read_text())
    screen=json.loads(a.screen.read_text())
    all_evidence=json.loads(a.evidence.read_text())
    ranked=json.loads(a.ranked.read_text())
    rows={x["legend"]:x for x in manifest["records"]}
    if (manifest["status"]!="ALL58_REGISTERED_STRUCTURE_PROPOSALS_UNTESTED"
        or manifest["legends"]!=58 or manifest["variants_total"]!=580
        or manifest["families"].get(KIND)!=COUNT
        or manifest["native_registry_sha256"]!=sha(a.registry)
        or native["status"]!="ALL_580_REGISTERED_STRUCTURAL_NATIVE_GAMES_PASS"
        or native["source_manifest_sha256"]!=sha(a.variants/"structural_manifest.json")
        or native["all_native_games_completed"]!=580
        or native["native_game_failures"]!=0
        or screen["status"]!="ALL174_SIDEB0ARD_VARIANTS_NATIVE_407_G2_G3_SCREEN_COMPLETE"
        or screen["sideboard_variants_actually_played"]!=COUNT
        or screen["candidate_bo3_completed"]!=COUNT*4
        or screen["baseline_bo3_completed"]!=58*4
        or screen["confirmed_upgrades"]!=0
        or screen["accepted_deck_changes"] is not False
        or screen["source_manifest_sha256"]!=sha(a.variants/"structural_manifest.json")
        or screen["native_engine_sha256"]!=native["native_engine_sha256"]
        or len(ranked)!=58
        or set(rows)!=set(originals) or set(all_evidence)!=set(originals)
        or len(screen["best_unconfirmed_by_legend"])!=58
        or {r["legend"] for r in ranked}!=set(originals)):
        raise RuntimeError("Unverified all-174 native sideboard source evidence")
    if any(rows[n]["original_sha256"]!=sha(originals[n]) for n in originals):
        raise RuntimeError("Original 58 deck content changed")
    if a.engine is not None and sha(a.engine)!=native["native_engine_sha256"]:
        raise RuntimeError("Native C++ engine digest mismatch")
    return originals,manifest,native,screen,all_evidence,ranked,rows


def shortlist(screen,evidence,manifest):
    records={r["legend"]:r for r in manifest["records"]}
    suggested=[]
    for x in screen["best_unconfirmed_by_legend"]:
        name=x["legend"]
        candidates=evidence[name]["sideboard_proposals"]
        matched=[y for y in candidates
                 if y["candidate_sha256"]==x["candidate_sha256"]]
        candidate_source=[y for y in records[name]["variants"]
                          if y["sha256"]==x["candidate_sha256"]]
        if (len(matched)!=1 or len(candidate_source)!=1
            or candidate_source[0]["kind"]!=KIND
            or matched[0]["score"]!=x["score"]
            or matched[0]["sideboard_added_card"]!=candidate_source[0]["changes"]["in"]):
            raise RuntimeError("Tampered selected sideboard-only candidate")
        evidence_row=matched[0]
        if evidence_row["score"]["delta"]>0:
            suggested.append({
                "legend":name,
                "candidate_sha256":evidence_row["candidate_sha256"],
                "candidate_path":evidence_row["path"],
                "original_sha256":evidence_row["registered_original_sha256"],
                "sideboard_added_card":evidence_row["sideboard_added_card"],
                "source_screen_delta":evidence_row["score"]["delta"],
                "source_screen_candidate_wins":evidence_row["score"]["candidate_wins"],
                "original_policy":evidence_row["baseline_policy"],
                "candidate_policy":evidence_row["candidate_policy"],
            })
    suggested.sort(key=lambda x:(
        -x["source_screen_delta"],-x["source_screen_candidate_wins"],
        x["legend"],x["candidate_sha256"]
    ))
    if len(suggested)<FAMILY:
        raise RuntimeError("Too few positive-screen sideboard hypotheses: "
                           +str(len(suggested)))
    selected=suggested[:FAMILY]
    for i,x in enumerate(selected):
        x["index"]=i
    if len({x["legend"] for x in selected})!=FAMILY:
        raise RuntimeError("Sideboard holdout reuses a Legend")
    return selected


def cases(name,ranked,seed,repeats):
    training=opponents_for(name,ranked,2)
    opponents=[x["legend"] for x in ranked
               if x["legend"]!=name and x["legend"] not in training]
    held=opponents[:OPPONENTS_HELD_OUT]
    if (len(held)!=OPPONENTS_HELD_OUT or len(set(held))!=len(held)
        or set(held)&set(training)):
        raise RuntimeError("Sideboard holdout must avoid trained opponents")
    tests=[
        {"opponent":o,"seat":seat,"repeat":rep,
         "seed":stable_seed(seed,"SIDEBOARD_174_INDEPENDENT_407_128",
                            name,o,seat,rep)}
        for o in held for seat in (0,1) for rep in range(repeats)
    ]
    if len({x["seed"] for x in tests})!=len(tests):
        raise RuntimeError("Duplicate heldout random seeds")
    return training,held,tests


def preregister(a):
    original,manifest,native,screen,evidence,ranked,records=sources(a)
    selected=shortlist(screen,evidence,manifest)
    frozen={
        "schema":1,
        "status":"SIDEBOARD_ACTUAL_SWAP_12_HOLDOUT_PREREGISTERED",
        "hypotheses":FAMILY,"source_174_sha256":sha(a.screen),
        "source_174_evidence_sha256":sha(a.evidence),
        "source_580_manifest_sha256":sha(a.variants/"structural_manifest.json"),
        "source_native_certification_sha256":sha(a.certification),
        "ranked_58_sha256":sha(a.ranked),
        "agent":a.agent,"seed":a.seed,"repetitions":a.repetitions,
        "training_opponents":2,"heldout_opponents":OPPONENTS_HELD_OUT,
        "no_candidate_accepted":True,"selected":selected
    }
    for row in selected:
        cases(row["legend"],ranked,a.seed,a.repetitions)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(frozen,indent=2))
    print("SIDEBOARD_174_HOLDOUT_FROZEN_12",[
        (x["legend"],x["sideboard_added_card"]) for x in selected
    ],flush=True)


def validate_selection(a):
    original,manifest,native,screen,evidence,ranked,records=sources(a)
    doc=json.loads(a.selection.read_text())
    wanted=shortlist(screen,evidence,manifest)
    if (doc.get("status")!="SIDEBOARD_ACTUAL_SWAP_12_HOLDOUT_PREREGISTERED"
        or doc.get("schema")!=1 or doc.get("hypotheses")!=FAMILY
        or doc.get("source_174_sha256")!=sha(a.screen)
        or doc.get("source_174_evidence_sha256")!=sha(a.evidence)
        or doc.get("source_580_manifest_sha256")!=sha(a.variants/"structural_manifest.json")
        or doc.get("source_native_certification_sha256")!=sha(a.certification)
        or doc.get("ranked_58_sha256")!=sha(a.ranked)
        or doc.get("selected")!=wanted
        or doc.get("agent")!=a.agent or doc.get("seed")!=a.seed
        or doc.get("repetitions")!=a.repetitions
        or doc.get("training_opponents")!=2
        or doc.get("heldout_opponents")!=OPPONENTS_HELD_OUT
        or doc.get("no_candidate_accepted") is not True):
        raise RuntimeError("Changed 12-source research hypotheses after preregistration")
    return original,manifest,native,screen,evidence,ranked,records,doc


def native_match(a,target,opponent,policy,scenario,byname):
    seat=scenario["seat"]
    deck1,deck2=(target,opponent) if seat==0 else (opponent,target)
    seat_label="p1" if seat==0 else "p2"
    staged={
        "game2":{seat_label:policy["plan"],"loser_chooses_start":"self"},
        "game3":{seat_label:policy["plan"],"loser_chooses_start":"self"}
    }
    r=run_series(a.engine,deck1,deck2,byname,staged,
                 a.agent,scenario["seed"],a.timeout)
    if (r.get("status")!="COMPLETE_RULE407_START_POLICY_BO3"
        or r.get("rule_407_4_start_choice_verified") is not True
        or r.get("winner") not in (1,2)
        or not r.get("sideboarding_applied")
        or not r.get("source_decks_return_to_registered_state_next_match")
        or not 2<=len(r.get("games",[]))<=3
        or r["games"][0].get("sideboard_swaps")!=[[],[]]):
        raise RuntimeError("Actual native-407 BO3 or game1 registration failed")
    for game in r["games"][1:]:
        swaps=game["sideboard_swaps"][seat]
        if (game["engine_status"]!="complete"
            or game.get("forced_start_verified") is not True
            or game["expected_engine_starting_seat"]!=game["verified_engine_starting_seat"]
            or swaps!=policy["plan"]["swaps"]):
            raise RuntimeError("Candidate native G2/G3 sideboard action unverified")
    return {"win":int(r["winner"]==seat+1),
            "game1_winner_seat":r["games"][0]["winner_seat"],
            "native_verified":True,"swapped_games":len(r["games"])-1}


def trial(a,baseline,candidate,other,baseline_policy,candidate_policy,scenario,byname):
    b=native_match(a,baseline,other,baseline_policy,scenario,byname)
    c=native_match(a,candidate,other,candidate_policy,scenario,byname)
    return {
        **scenario,
        "baseline_win":b["win"],"candidate_win":c["win"],
        "game1_same_winner":b["game1_winner_seat"]==c["game1_winner_seat"],
        "baseline_swapped_games":b["swapped_games"],
        "candidate_swapped_games":c["swapped_games"],
        "actual_native_407_verified":b["native_verified"] and c["native_verified"]
    }


def evaluate(a):
    original,manifest,native,screen,evidence,ranked,records,doc=validate_selection(a)
    selected=doc["selected"][a.index]
    name=selected["legend"]
    candidate=a.variants/selected["candidate_path"]
    baseline=original[name]
    if (not a.engine.is_file()
        or sha(candidate)!=selected["candidate_sha256"]
        or sha(baseline)!=selected["original_sha256"]):
        raise RuntimeError("Native binary or selected deck changed")
    byname=registry(a.registry)
    base_state=parse_deck(baseline.read_text())
    changed_state=parse_deck(candidate.read_text())
    legal_registration(base_state,changed_state,byname)
    if (base_state.main!=changed_state.main
        or base_state.runes!=changed_state.runes
        or base_state.battlefields!=changed_state.battlefields
        or base_state.champion!=changed_state.champion):
        raise RuntimeError("Sideboard-only claim changes main/Champion/runes/fields")
    for state,policy in (
        (base_state,selected["original_policy"]),
        (changed_state,selected["candidate_policy"])
    ):
        if deterministic_sideboard_plan(
            state,byname,
            require_in=selected["sideboard_added_card"]
            if state is changed_state else None
        )!=policy:
            raise RuntimeError("Heuristic sideboard policy changed after preregistration")
        transition(state,policy["plan"],byname,game_no=2)
    training,held,tests=cases(name,ranked,a.seed,a.repetitions)
    def compare(one):
        return trial(a,baseline,candidate,original[one["opponent"]],
                     selected["original_policy"],selected["candidate_policy"],
                     one,byname)
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        rows=list(pool.map(compare,tests))
    b=sum(x["baseline_win"] for x in rows)
    c=sum(x["candidate_win"] for x in rows)
    plus=sum(x["candidate_win"] and not x["baseline_win"] for x in rows)
    minus=sum(x["baseline_win"] and not x["candidate_win"] for x in rows)
    payload={
        "status":"SIDEB0ARD_ACTUAL_NATIVE_407_INDEPENDENT_128_BO3",
        "index":a.index,"legend":name,"candidate_sha256":sha(candidate),
        "original_sha256":sha(baseline),"selection_sha256":sha(a.selection),
        "native_engine_sha256":sha(a.engine),
        "agent":a.agent,"seed":a.seed,"repetitions":a.repetitions,
        "training_opponents":training,"heldout_opponents":held,
        "baseline_wins":b,"candidate_wins":c,
        "candidate_only":plus,"baseline_only":minus,
        "mcnemar_p":mcnemar_exact(plus,minus),
        "game1_same_winner_count":sum(x["game1_same_winner"] for x in rows),
        "actual_native_407_policy_verified":True,
        "paired_completed":len(rows),"no_candidate_auto_adopted":True,
        "paired":rows,
    }
    if len(rows)!=OPPONENTS_HELD_OUT*2*a.repetitions:
        raise RuntimeError("Missing independent native BO3 experiment")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(payload,indent=2))
    print("REAL_SIDEBOARD_128_HOLDOUT",name,
          "candidate",c,"original",b,"p",payload["mcnemar_p"],flush=True)


def aggregate(a):
    original,manifest,native,screen,evidence,ranked,records,doc=validate_selection(a)
    results=[]
    for selected in doc["selected"]:
        idx=selected["index"];name=selected["legend"]
        row=json.loads((a.input/f"sideboard-holdout-{idx}"/"holdout.json").read_text())
        trained,held,expected=cases(name,ranked,a.seed,a.repetitions)
        if (row["status"]!="SIDEB0ARD_ACTUAL_NATIVE_407_INDEPENDENT_128_BO3"
            or row["index"]!=idx or row["legend"]!=name
            or row["candidate_sha256"]!=selected["candidate_sha256"]
            or row["original_sha256"]!=selected["original_sha256"]
            or row["selection_sha256"]!=sha(a.selection)
            or row["native_engine_sha256"]!=native["native_engine_sha256"]
            or row["agent"]!=a.agent or row["seed"]!=a.seed
            or row["repetitions"]!=a.repetitions
            or row["training_opponents"]!=trained
            or row["heldout_opponents"]!=held
            or row["paired_completed"]!=len(expected)
            or row["actual_native_407_policy_verified"] is not True
            or row["no_candidate_auto_adopted"] is not True
            or len(row["paired"])!=len(expected)):
            raise RuntimeError("Independent 12 policy shards are not source-identical")
        for found,wanted in zip(row["paired"],expected):
            if (any(found[k]!=wanted[k] for k in
                    ("opponent","seat","repeat","seed"))
                or found["baseline_win"] not in (0,1)
                or found["candidate_win"] not in (0,1)
                or not isinstance(found["game1_same_winner"],bool)
                or found["actual_native_407_verified"] is not True
                or found["baseline_swapped_games"]<1
                or found["candidate_swapped_games"]<1):
                raise RuntimeError("Unverified heldout 407 actual swap receipt")
        b=sum(x["baseline_win"] for x in row["paired"])
        c=sum(x["candidate_win"] for x in row["paired"])
        plus=sum(x["candidate_win"] and not x["baseline_win"]
                 for x in row["paired"])
        minus=sum(x["baseline_win"] and not x["candidate_win"]
                  for x in row["paired"])
        if (b!=row["baseline_wins"] or c!=row["candidate_wins"]
            or plus!=row["candidate_only"] or minus!=row["baseline_only"]
            or row["game1_same_winner_count"]!=sum(
                x["game1_same_winner"] for x in row["paired"])
            or abs(row["mcnemar_p"]-mcnemar_exact(plus,minus))>1e-12):
            raise RuntimeError("Nonreproducible independent McNemar score")
        results.append({
            "legend":name,"sideboard_added_card":selected["sideboard_added_card"],
            "candidate_sha256":selected["candidate_sha256"],
            "candidate_wins":c,"baseline_wins":b,"delta":c-b,
            "changed":True,"incomplete":0,"mcnemar_p":mcnemar_exact(plus,minus),
            "game1_different_winner_count":len(row["paired"])-
                                                row["game1_same_winner_count"]
        })
    if len(results)!=FAMILY:
        raise RuntimeError("Missing whole preregistered policy hypothesis family")
    holm(results)
    report={
        "status":"TWELVE_SIDEB0ARD_128_ISMCTS_ACTUAL_407_HOLDOUT_COMPLETE",
        "hypotheses":FAMILY,
        "completed_paired_bo3":FAMILY*OPPONENTS_HELD_OUT*2*a.repetitions,
        "native_engine_sha256":native["native_engine_sha256"],
        "holm_fwer":0.05,
        "candidate_policy_signals":sum(x["independently_confirmed"] for x in results),
        "registered_decks_auto_modified":False,
        "confirmed_causal_tech_card_effects":0,
        "game1_seed_path_mismatch_warning":(
            "The same numeric seed can yield differing Game 1 outcomes "
            "for legal registrations that differ only in Sideboard, "
            "so this tests the entire registered deck + heuristic policy package, "
            "NOT the isolated effect of the new tech card."
        ),
        "results":sorted(results,key=lambda x:(-x["delta"],x["legend"]))
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(report,indent=2))
    print("12_REAL_SIDEBOARD_407_HOLDOUT_COMPLETE",json.dumps({
        k:v for k,v in report.items() if k!="results"
    }),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("selected","variants","registry","screen","evidence",
                 "certification","ranked","output"):
        p.add_argument("--"+name,type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path)
    p.add_argument("--selection",type=pathlib.Path)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--select",action="store_true")
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--index",type=int,default=0)
    p.add_argument("--repetitions",type=int,default=2)
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--seed",type=int,default=202611271300)
    p.add_argument("--agent",default="ismcts:sims=128")
    p.add_argument("--timeout",type=float,default=260)
    a=p.parse_args()
    if (not 1<=a.workers<=8 or not 1<=a.repetitions<=4
        or not 0<=a.index<FAMILY or a.timeout<=0):
        p.error("Invalid preregistered strong-agent sideboard budget")
    if a.select:
        preregister(a)
    else:
        if a.selection is None:
            p.error("Active independent holdout requires --selection")
        if a.aggregate:
            if a.input is None:
                p.error("Aggregate requires --input")
            aggregate(a)
        else:
            if a.engine is None:
                p.error("Actual C++ 407 engine required")
            evaluate(a)


if __name__=="__main__":
    main()
