#!/usr/bin/env python3
"""Preregister and independently test selected registered-structure improvements.

Requires the completed 406-candidate 407-BO3 discovery artifact and the
580/580 native compatibility receipts. Selects EXACTLY 12 best positive,
distinct-Legend candidates before any new opponent/seed is played.
Each candidate faces six opponents outside its 2-opponent discovery panel,
both seats and two repetitions, at 128-search ISMCTS.
Never silently replace original decks. Strict whole-family Holm correction.
"""
from __future__ import annotations
import argparse
import concurrent.futures
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from full_field_58 import mcnemar_exact,holm
from optimize_58 import registry,stable_seed
from round_robin_58 import load_decks,sha
from sideboard_deck import parse_deck
from structural_deck_population import legal_registration
from tournament_bo3_policy import run_series

FAMILY=12
KINDS=("rune","battlefield","champion")


def sources(a):
    originals,_=load_decks(a.selected)
    manifest=json.loads((a.variants/"structural_manifest.json").read_text())
    screen=json.loads(a.screen.read_text())
    native=json.loads(a.certification.read_text())
    ranked=json.loads(a.ranked.read_text())
    records={x["legend"]:x for x in manifest["records"]}
    if any((
        manifest["status"]!="ALL58_REGISTERED_STRUCTURE_PROPOSALS_UNTESTED",
        manifest["legends"]!=58,
        manifest["variants_total"]!=580,
        manifest["native_registry_sha256"]!=sha(a.registry),
        screen["status"]!="ALL58_406_STRUCTURE_VARIANTS_SCREENED_NO_ACCEPTANCE",
        screen["legends"]!=58,
        screen["structural_candidates_scored"]!=406,
        screen["sideboard_only_deferred_for_real_sideboard_policy"]!=174,
        screen["confirmed_deck_upgrades"]!=0,
        screen["original_registered_decks_changed"] is not False,
        screen["source_manifest_sha256"]!=sha(a.variants/"structural_manifest.json"),
        native["status"]!="ALL_580_REGISTERED_STRUCTURAL_NATIVE_GAMES_PASS",
        native["all_native_games_completed"]!=580,
        native["native_game_failures"]!=0,
        native["source_manifest_sha256"]!=sha(a.variants/"structural_manifest.json"),
        native["native_engine_sha256"]!=screen["native_engine_sha256"],
        len(ranked)!=58,
        set(originals)!=set(records),
        {r["legend"] for r in ranked}!=set(originals),
    )):
        raise RuntimeError("Unverified 580/406 full-field source provenance")
    if any(records[name]["original_sha256"]!=sha(originals[name]) for name in originals):
        raise RuntimeError("Frozen original deck was modified")
    return originals,manifest,screen,native,ranked,records


def shortlist(screen,manifest):
    entries={r["legend"]:r for r in manifest["records"]}
    results=[];seen=set()
    for row in screen["best_unconfirmed_by_legend"]:
        name=row["legend"]
        if name in seen or name not in entries:
            raise RuntimeError("Duplicate or absent Legend")
        seen.add(name)
        matching=[v for v in entries[name]["variants"]
                  if v["sha256"]==row["candidate_sha256"]]
        if (len(matching)!=1 or row["kind"]!=matching[0]["kind"]
            or row["kind"] not in KINDS
            or row["screened_no_independent_confirmation"] is not True):
            raise RuntimeError("Screen winner is not source-certified")
        if row["sample_delta"]>0:
            results.append({
                "legend":name,"kind":row["kind"],
                "candidate_sha256":row["candidate_sha256"],
                "candidate_path":matching[0]["path"],
                "source_sha256":entries[name]["original_sha256"],
                "screen_delta":row["sample_delta"],
                "screen_candidate_wins":row["paired_wins_candidate"],
            })
    if seen!=set(entries):
        raise RuntimeError("Not all Legends represented")
    results.sort(key=lambda x:(-x["screen_delta"],-x["screen_candidate_wins"],x["legend"]))
    if len(results)<FAMILY:
        raise RuntimeError("Fewer than 12 positive discovery candidates")
    return [{**x,"index":i} for i,x in enumerate(results[:FAMILY])]


def opponent_panel(legend,ranked,seed,repetitions):
    others=[r["legend"] for r in ranked if r["legend"]!=legend]
    train=others[:2];held=others[2:8]
    if len(train)!=2 or len(held)!=6 or len(set(train+held))!=8:
        raise RuntimeError("Holdout reused discovery opponent")
    cases=[{
        "opponent":opp,"seat":seat,"repeat":rep,
        "seed":stable_seed(seed,"STRUCTURE_407_INDEPENDENT_128",legend,opp,seat,rep)
    } for opp in held for seat in (0,1) for rep in range(repetitions)]
    if len({x["seed"] for x in cases})!=len(cases):
        raise RuntimeError("Seed collision")
    return train,held,cases


def protocol(a):
    original,manifest,screen,native,ranked,records=sources(a)
    expected=shortlist(screen,manifest)
    if a.select:
        selection={
            "schema":1,"status":"STRUCTURE_HOLDOUT_FROZEN_12",
            "hypotheses":FAMILY,
            "selection_rule":"Largest positive delta, one tested registration per Legend, deterministic tie breaks",
            "source_406_sha256":sha(a.screen),
            "source_580_manifest_sha256":sha(a.variants/"structural_manifest.json"),
            "source_580_native_sha256":sha(a.certification),
            "ranked_58_sha256":sha(a.ranked),
            "agent":a.agent,"seed":a.seed,"repetitions":a.repetitions,
            "training_opponents":2,"unseen_opponents":6,
            "no_candidate_accepted":True,"selected":expected,
        }
        a.output.parent.mkdir(parents=True,exist_ok=True)
        a.output.write_text(json.dumps(selection,indent=2))
        print("FROZEN_STRUCTURE_128_HOLDOUT",[(x["legend"],x["screen_delta"])
                                              for x in expected],flush=True)
        return None
    selection=json.loads(a.selection.read_text())
    if any((
        selection["schema"]!=1,
        selection["status"]!="STRUCTURE_HOLDOUT_FROZEN_12",
        selection["hypotheses"]!=FAMILY,
        selection["source_406_sha256"]!=sha(a.screen),
        selection["source_580_manifest_sha256"]!=sha(a.variants/"structural_manifest.json"),
        selection["source_580_native_sha256"]!=sha(a.certification),
        selection["ranked_58_sha256"]!=sha(a.ranked),
        selection["selected"]!=expected,
        selection["agent"]!=a.agent,
        selection["seed"]!=a.seed,
        selection["repetitions"]!=a.repetitions,
        selection["no_candidate_accepted"] is not True,
    )):
        raise RuntimeError("Holdout selection was altered after preregistration")
    return original,manifest,screen,native,ranked,records,selection


def play(a,name,target,other,case,byname):
    d1,d2=(target,other) if case["seat"]==0 else (other,target)
    r=run_series(a.engine.resolve(),d1,d2,byname,{},a.agent,
                 case["seed"],a.timeout)
    if (r["status"]!="COMPLETE_RULE407_START_POLICY_BO3"
        or r["rule_407_4_start_choice_verified"] is not True
        or r["winner"] not in (1,2)
        or any(g["engine_status"]!="complete" for g in r["games"])):
        raise RuntimeError("Native 407 BO3 incomplete; no imputed win: "
                           +json.dumps(r)[-800:])
    return int(r["winner"]==case["seat"]+1)


def evaluate(a):
    original,manifest,screen,native,ranked,records,selection=protocol(a)
    chosen=selection["selected"][a.index]
    name=chosen["legend"]
    candidate=a.variants/chosen["candidate_path"]
    if (not a.engine.is_file()
        or sha(a.engine)!=native["native_engine_sha256"]
        or sha(candidate)!=chosen["candidate_sha256"]):
        raise RuntimeError("Changed compiled engine or candidate card identities")
    byname=registry(a.registry)
    legal_registration(parse_deck(original[name].read_text()),
                       parse_deck(candidate.read_text()),byname)
    train,held,cases=opponent_panel(name,ranked,a.seed,a.repetitions)
    def paired(case):
        baseline=play(a,name,original[name],original[case["opponent"]],case,byname)
        modified=play(a,name,candidate,original[case["opponent"]],case,byname)
        return {**case,"baseline_win":baseline,"candidate_win":modified,
                "actual_cpp_407_verified":True}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:
        receipts=list(pool.map(paired,cases))
    c=sum(x["candidate_win"] for x in receipts)
    b=sum(x["baseline_win"] for x in receipts)
    can_only=sum(x["candidate_win"] and not x["baseline_win"] for x in receipts)
    base_only=sum(x["baseline_win"] and not x["candidate_win"] for x in receipts)
    result={
        "status":"STRUCTURE_128_INDEPENDENT_407_BO3_COMPLETED",
        "index":a.index,"legend":name,"kind":chosen["kind"],
        "candidate_sha256":chosen["candidate_sha256"],
        "source_sha256":chosen["source_sha256"],
        "native_engine_sha256":sha(a.engine),
        "selection_sha256":sha(a.selection),
        "agent":a.agent,"seed":a.seed,"repetitions":a.repetitions,
        "trained_opponents":train,"heldout_opponents":held,
        "baseline_wins":b,"candidate_wins":c,
        "candidate_only":can_only,"baseline_only":base_only,
        "mcnemar_p":mcnemar_exact(can_only,base_only),
        "completed_paired_bo3":len(receipts),
        "no_auto_acceptance":True,
        "paired":receipts,
    }
    if len(receipts)!=6*2*a.repetitions:
        raise RuntimeError("Incomplete native BO3 holdout")
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2))
    print("STRUCTURE_128_HOLDOUT",name,"candidate",c,"original",b,
          "p",result["mcnemar_p"],flush=True)


def aggregate(a):
    original,manifest,screen,native,ranked,records,selection=protocol(a)
    outcomes=[]
    for selected in selection["selected"]:
        idx=selected["index"]
        p=json.loads((a.input/f"structure-holdout-{idx}"/"holdout.json").read_text())
        train,held,cases=opponent_panel(selected["legend"],ranked,a.seed,a.repetitions)
        if any((
            p["status"]!="STRUCTURE_128_INDEPENDENT_407_BO3_COMPLETED",
            p["index"]!=idx,
            p["legend"]!=selected["legend"],
            p["kind"]!=selected["kind"],
            p["candidate_sha256"]!=selected["candidate_sha256"],
            p["source_sha256"]!=selected["source_sha256"],
            p["native_engine_sha256"]!=native["native_engine_sha256"],
            p["selection_sha256"]!=sha(a.selection),
            p["agent"]!=a.agent,p["seed"]!=a.seed,
            p["repetitions"]!=a.repetitions,
            p["trained_opponents"]!=train,p["heldout_opponents"]!=held,
            p["completed_paired_bo3"]!=len(cases),
            len(p["paired"])!=len(cases),
            p["no_auto_acceptance"] is not True,
        )):
            raise RuntimeError("Modified or incomplete preregistered holdout "+str(idx))
        for found,wanted in zip(p["paired"],cases):
            if (any(found[k]!=wanted[k] for k in ("opponent","seat","repeat","seed"))
                or found["actual_cpp_407_verified"] is not True
                or found["candidate_win"] not in (0,1)
                or found["baseline_win"] not in (0,1)):
                raise RuntimeError("Untrusted game receipt or holdout seed")
        cw=sum(x["candidate_win"] for x in p["paired"])
        bw=sum(x["baseline_win"] for x in p["paired"])
        co=sum(x["candidate_win"] and not x["baseline_win"] for x in p["paired"])
        bo=sum(x["baseline_win"] and not x["candidate_win"] for x in p["paired"])
        if (cw!=p["candidate_wins"] or bw!=p["baseline_wins"] or
            co!=p["candidate_only"] or bo!=p["baseline_only"] or
            abs(p["mcnemar_p"]-mcnemar_exact(co,bo))>1e-12):
            raise RuntimeError("Invalid McNemar calculation")
        outcomes.append({
            "legend":selected["legend"],"kind":selected["kind"],
            "candidate_sha256":selected["candidate_sha256"],
            "candidate_wins":cw,"baseline_wins":bw,"delta":cw-bw,
            "changed":True,"incomplete":0,
            "mcnemar_p":p["mcnemar_p"],
        })
    if len(outcomes)!=FAMILY:
        raise RuntimeError("Full 12-candidate family required for Holm")
    holm(outcomes)
    summary={
        "status":"TWELVE_STRUCTURE_128_ISMCTS_407_HOLDOUT_COMPLETE",
        "hypotheses":FAMILY,
        "completed_paired_BO3":FAMILY*6*2*a.repetitions,
        "compiled_engine_sha256":native["native_engine_sha256"],
        "holm_fwer":0.05,
        "confirmed":sum(x["independently_confirmed"] for x in outcomes),
        "original_58_decks_modified":False,
        "no_unconfirmed_deck_adopted":True,
        "no_game_2_3_sideboard_swaps":True,
        "limitations":"Independent elite panel; policy default loser starts, no strategic sideboard",
        "results":sorted(outcomes,key=lambda x:(-x["delta"],x["legend"])),
    }
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(summary,indent=2))
    print("STRUCTURE_INDEPENDENT_407_FINAL",json.dumps(
        {k:v for k,v in summary.items() if k!="results"}),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for flag in ("selected","variants","registry","screen","certification","ranked","output"):
        p.add_argument("--"+flag,type=pathlib.Path,required=True)
    p.add_argument("--selection",type=pathlib.Path)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--engine",type=pathlib.Path)
    p.add_argument("--select",action="store_true")
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--index",type=int,default=0)
    p.add_argument("--repetitions",type=int,default=2)
    p.add_argument("--agent",default="ismcts:sims=128")
    p.add_argument("--seed",type=int,default=202611261230)
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--timeout",type=float,default=240)
    a=p.parse_args()
    if (not 0<=a.index<FAMILY or not 1<=a.repetitions<=10
        or not 1<=a.workers<=12 or a.timeout<=0):
        p.error("Invalid holdout search budget")
    if a.select:
        protocol(a)
    elif a.aggregate:
        if a.selection is None or a.input is None:
            p.error("Aggregate requires source selection and all 12 source receipts")
        aggregate(a)
    else:
        if a.selection is None or a.engine is None:
            p.error("Native engine and preregistered candidate family required")
        evaluate(a)


if __name__=="__main__":
    main()
