#!/usr/bin/env python3
"""Fail-closed 407 verified-policy result aggregation for Worlds lineup pilots.

This selects only candidates to confirm later, and never auto-accepts or
exports any changed registered deck. Three separate elite matchups each have
only four paired BO3 series/candidate, so headline rates are not robust.
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from full_field_58 import mcnemar_exact,holm

MATCHUPS={
    "draven-vs-miss-fortune":("Draven, Glorious Executioner","Miss Fortune, Bounty Hunter"),
    "leblanc-vs-reksai":("LeBlanc, Deceiver","Rek'Sai, Void Burrower"),
    "masteryi-vs-ambessa":("Master Yi, Wuju Bladesman","Ambessa, Matriarch of War"),
}


def aggregate(root:pathlib.Path):
    candidates=[]
    hashes=set()
    baselines={}
    for id,(legend,opponent) in MATCHUPS.items():
        file=root/f"competitive-worlds-sideboard-{id}"/"sideboard_policy_screen.json"
        payload=json.loads(file.read_text(encoding="utf-8"))
        if (payload.get("status")!="SINGLE_MATCHUP_STRATEGIC_BO3_POLICY_SCREEN_ONLY" or
            payload.get("legend")!=legend or payload.get("opponent")!=opponent or
            payload.get("any_deck_changes_adopted") is not False or
            payload.get("loser_chooses_first_verified") is not True or
            payload.get("baseline_completed_series")!=4 or
            payload.get("candidate_completed_series")!=4*payload["search_candidates"] or
            not payload.get("deck_sha256") or not payload.get("opponent_sha256")):
            raise RuntimeError("Malformed/failed immutable policy screen: "+id)
        hashes.add(payload["engine_sha256"])
        baseline=payload["baseline_games"]
        if (len(baseline)!=4 or
            any(x["target_win"] not in (0,1) for x in baseline)):
            raise RuntimeError("Baseline BO3 evidence incomplete")
        baselines[id]=sum(x["target_win"] for x in baseline)
        seen=set()
        for row in payload["candidate_results"]:
            number=row["candidate_index"]
            if (number in seen or
                row["paired_series"]!=4 or
                row["status"]!="EXPLORATORY_NO_HOLDOUT" or
                len(row["cases"])!=4 or
                row["baseline_wins"]!=baselines[id]):
                raise RuntimeError("Repeated or invalid candidate evidence")
            seen.add(number)
            wins=sum(x["target_win"] for x in row["cases"])
            pairs=list(zip(row["cases"],baseline))
            if any(
                (a["seat"],a["rep"],a["seed"])!=
                (b["seat"],b["rep"],b["seed"])
                or a["target_win"] not in (0,1)
                or len(a["forced_start_receipts"])==0
                or any(q["requested"]!=q["actual"]
                       for q in a["forced_start_receipts"])
                for a,b in pairs
            ):
                raise RuntimeError("Mismatched paired BO3 or unverified C++ turn order")
            candidate_only=sum(a["target_win"]==1 and b["target_win"]==0
                               for a,b in pairs)
            source_only=sum(a["target_win"]==0 and b["target_win"]==1
                            for a,b in pairs)
            p=mcnemar_exact(candidate_only,source_only)
            if (wins!=row["candidate_wins"] or
                wins-baselines[id]!=row["delta"] or
                abs(p-row["mcnemar_p_unadjusted"])>1e-12):
                raise RuntimeError("Discordant-pair score mismatch")
            candidates.append({
                "legend":legend,"opponent":opponent,"matchup":id,
                "policy_index":number,"policy":row["option"],
                "candidate_wins":wins,"baseline_wins":baselines[id],
                "candidate_minus_baseline":wins-baselines[id],
                "changed":True,"incomplete":0,"mcnemar_p":p,
            })
        if len(seen)!=payload["search_candidates"]:
            raise RuntimeError("Missing candidate policy from matched matchup")
    if len(hashes)!=1:
        raise RuntimeError("Mismatched native 407 engines")
    # Holm-adjust across all exploratory tested policies, BUT even a small
    # p-value does not graduate into acceptance without NEW holdout opponents.
    holm(candidates)
    for row in candidates:
        row["screening_only"] = True
        row["independently_confirmed"] = False
    by_matchup={}
    for key in MATCHUPS:
        rows=[x for x in candidates if x["matchup"]==key]
        rows.sort(key=lambda z:(-z["candidate_minus_baseline"],
                                -z["candidate_wins"],z["policy_index"]))
        by_matchup[key]=rows
    result={
        "status":"THREE_WORLDS_DECKS_407_POLICY_EXPLORATORY_ONLY",
        "matchups":len(MATCHUPS),
        "total_candidate_policies":len(candidates),
        "baseline_bo3_per_matchup":4,
        "candidate_bo3_per_policy":4,
        "native_engine_sha256":next(iter(hashes)),
        "loser_start_rule_verified":True,
        "multi_slot_sideboard_search":True,
        "familywise_adjustment":"Holm across all exploratory policies; holdout still required",
        "independent_holdout_performed":False,
        "confirmed_improvements":0,
        "registered_decks_modified":False,
        "best_3_by_matchup":{k:v[:3] for k,v in by_matchup.items()},
    }
    return result,by_matchup


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    a=p.parse_args()
    report,all_rows=aggregate(a.input)
    a.output.mkdir(parents=True,exist_ok=True)
    (a.output/"summary.json").write_text(json.dumps(report,indent=2))
    (a.output/"all_ranked_candidates.json").write_text(json.dumps(all_rows,indent=2))
    print("THREE_WORLDS_407_POLICY_SCREEN_COMPLETE",json.dumps({
        k:v for k,v in report.items() if k!="best_3_by_matchup"
    }),flush=True)


if __name__=="__main__":
    main()
