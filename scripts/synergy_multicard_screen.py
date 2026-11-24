#!/usr/bin/env python3
"""Real corrected-engine Rule407 BO3 fitness for 58x6 coordinated MainDeck packages.

Source decks, engine binary and each generated package are SHA-pinned. Compare
every changed deck to the SAME unchanged baseline in four mirrored, paired
BO3 scenarios; baseline reused once per Legend. 24-ISMCTS is training-only.
No candidate is adopted and screening p-values are NOT holdout confirmation.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/"scripts"))
from optimize_58 import registry, stable_seed
from round_robin_58 import load_decks, sha
from sideboard_deck import parse_deck
from structural_deck_population import legal_registration
from structural_fitness_screen import opponents_for, score
from tournament_bo3_policy import run_series
from synergy_multicard import STATUS

SCREEN_STATUS = "MULTICARD_SYNERGY_407_TRAINING_ONLY_NO_DECK_ADOPTION"


def inputs(a):
    sources, _ = load_decks(a.selected)
    manifest = json.loads((a.proposals/"manifest.json").read_text())
    native = json.loads(a.certification.read_text())
    ranked = json.loads(a.ranked.read_text())
    rows = {x["legend"]: x for x in manifest["records"]}
    expected_roster = hashlib.sha256(json.dumps(
        {n: sha(path) for n, path in sorted(sources.items())},
        sort_keys=True).encode()).hexdigest()
    expected_engine = sha(a.engine) if a.engine else native["native_engine_sha256"]
    if (len(sources) != 58 or manifest.get("status") != STATUS
            or manifest.get("legends") != 58
            or manifest.get("candidates_total") != 348
            or manifest.get("candidates_per_legend") != 6
            or manifest.get("depths_per_legend") != {"2": 3, "3": 3}
            or manifest.get("seed") != a.generation_seed
            or manifest.get("registry_sha256") != sha(a.registry)
            or manifest.get("source_roster_sha256") != expected_roster
            or manifest.get("original_decks_modified") is not False
            or manifest.get("engine_strength_established") is not False
            or set(rows) != set(sources)
            or native.get("status") != "ALL_580_REGISTERED_STRUCTURAL_NATIVE_GAMES_PASS"
            or native.get("all_native_games_completed") != 580
            or native.get("native_game_failures") != 0
            or native.get("native_engine_sha256") != expected_engine
            or native.get("original_decks_modified") is not False
            or len(ranked) != 58 or {x["legend"] for x in ranked} != set(sources)):
        raise RuntimeError("Inconsistent full-field source / repaired binary provenance")
    for name, rec in rows.items():
        if (rec["original_sha256"] != sha(sources[name]) or rec["count"] != 6
                or len(rec["candidates"]) != 6
                or [x["depth"] for x in rec["candidates"]] != [2,2,2,3,3,3]):
            raise RuntimeError("Changed or incomplete original/variant manifest: "+name)
    return sources, manifest, native, ranked, rows


def validate_candidate(original, entry, byname, proposals):
    path = (proposals/entry["path"]).resolve()
    if not path.is_relative_to(proposals.resolve()):
        raise RuntimeError("Candidate escaped frozen proposal directory")
    if not path.is_file() or sha(path) != entry["sha256"] or entry["status"] != STATUS:
        raise RuntimeError("Modified or missing source-hashed candidate")
    if entry["kind"] != "coordinated_main_deck_package" or entry["native_simulated"]:
        raise RuntimeError("Candidate was altered or marked accepted")
    before = parse_deck(original.read_text(encoding="utf-8"))
    after = parse_deck(path.read_text(encoding="utf-8"))
    legal_registration(before, after, byname)
    if (before.champion != after.champion or before.legend != after.legend
            or before.runes != after.runes or before.battlefields != after.battlefields
            or before.sideboard != after.sideboard):
        raise RuntimeError("Candidate changed frozen registered non-main components")
    steps = entry["steps"]
    if len(steps) != entry["depth"] or entry["depth"] not in (2,3):
        raise RuntimeError("Not a two-/three-slot package")
    if len({x["add"] for x in steps}) != entry["depth"]:
        raise RuntimeError("Package has repeated incoming cards")
    reconstructed = before.main.copy()
    for step in steps:
        if set(step) != {"remove", "add"} or reconstructed[step["remove"]] < 1:
            raise RuntimeError("Tampered atomic substitution")
        reconstructed[step["remove"]] -= 1
        reconstructed[step["add"]] += 1
    reconstructed += collections.Counter()
    if reconstructed != after.main or reconstructed == before.main:
        raise RuntimeError("Package moves do not match actual candidate card counts")
    return path


def schedule(name, ranked, seed):
    return [{"opponent": other, "seat": seat,
             "seed": stable_seed(seed, "SYNERGY_407_TRAINING", name, other, seat)}
            for other in opponents_for(name, ranked, 2) for seat in (0,1)]


def game(a, target, other, case, byname):
    first, second = (target,other) if case["seat"] == 0 else (other,target)
    result = run_series(a.engine.resolve(), first, second, byname, {},
                        a.agent, case["seed"], a.timeout)
    if (result.get("status") != "COMPLETE_RULE407_START_POLICY_BO3"
            or result.get("rule_407_4_start_choice_verified") is not True
            or result.get("winner") not in (1,2)
            or len(result.get("games", [])) not in (2,3)
            or any(g.get("engine_status") != "complete" for g in result["games"])
            or not result.get("source_decks_return_to_registered_state_next_match")
            or result.get("sideboarding_applied")):
        raise RuntimeError("Native repaired-engine BO3 incomplete: "
                           +json.dumps(result)[-1000:])
    return int(result["winner"] == case["seat"]+1)


def run(a):
    if not a.engine or not a.engine.is_file():
        raise RuntimeError("Expected real repaired C++ executable")
    sources, manifest, native, ranked, rows = inputs(a)
    byname = registry(a.registry)
    names = [n for i,n in enumerate(sorted(sources)) if i%a.shards==a.shard]
    results = []
    a.output.parent.mkdir(parents=True, exist_ok=True)
    for name in names:
        cases = schedule(name, ranked, a.seed)
        base_wins = [game(a, sources[name], sources[c["opponent"]], c, byname)
                     for c in cases]
        candidates = []
        for entry in rows[name]["candidates"]:
            candidate = validate_candidate(sources[name], entry, byname, a.proposals)
            wins = [game(a, candidate, sources[c["opponent"]], c, byname)
                    for c in cases]
            paired = [{**c, "baseline_win": b, "candidate_win": w}
                      for c,b,w in zip(cases,base_wins,wins)]
            candidates.append({
                "candidate_sha256": entry["sha256"], "path": entry["path"],
                "depth": entry["depth"], "steps": entry["steps"],
                "heuristic_delta": entry["heuristic_delta"],
                "printed_synergy_signals": entry["printed_synergy_signals"],
                "paired_receipts": paired, "score": score(paired),
                "status": "FOUR_REAL_407_TRAINING_BO3_PAIRS",
            })
            print("SYNERGY_407_TRAINING", name, entry["depth"],
                  entry["sha256"][:12], candidates[-1]["score"]["delta"], flush=True)
        results.append({
            "legend": name, "original_sha256": sha(sources[name]),
            "frozen_opponents": opponents_for(name, ranked, 2),
            "baseline_cases": [{**c, "baseline_win":w} for c,w in zip(cases,base_wins)],
            "candidates": candidates,
        })
        a.output.write_text(json.dumps({
            "status": SCREEN_STATUS, "shard":a.shard,"shards":a.shards,
            "generation_manifest_sha256":sha(a.proposals/"manifest.json"),
            "repaired_engine_certification_sha256":sha(a.certification),
            "ranked_sha256":sha(a.ranked),"engine_sha256":sha(a.engine),
            "agent":a.agent,"seed":a.seed,"sideboarding":False,
            "source_decks_modified":False,"results":results
        },indent=2))
    print("SYNERGY_407_SHARD_COMPLETE",a.shard,len(results),flush=True)


def aggregate(a):
    sources, manifest, native, ranked, rows = inputs(a)
    byname = registry(a.registry)
    engine_sha = native["native_engine_sha256"]
    verified, seen = [], set()
    for shard in range(a.shards):
        file = a.input/("synergy-shard-%d"%shard)/"screen.json"
        data = json.loads(file.read_text())
        if (data["status"] != SCREEN_STATUS or data["shard"] != shard
                or data["shards"] != a.shards
                or data["generation_manifest_sha256"] != sha(a.proposals/"manifest.json")
                or data["repaired_engine_certification_sha256"] != sha(a.certification)
                or data["ranked_sha256"] != sha(a.ranked)
                or data["engine_sha256"] != engine_sha
                or data["agent"] != a.agent or data["seed"] != a.seed
                or data["sideboarding"] is not False
                or data["source_decks_modified"] is not False):
            raise RuntimeError("Shard provenance does not match verified repaired binary")
        expected = [n for i,n in enumerate(sorted(sources)) if i%a.shards==shard]
        if [r["legend"] for r in data["results"]] != expected:
            raise RuntimeError("Incomplete/misallocated Legend shard")
        for row in data["results"]:
            name=row["legend"]
            if name in seen:
                raise RuntimeError("Duplicate Legend in 29 shards")
            seen.add(name)
            cases=schedule(name,ranked,a.seed)
            baseline=[{**c, "baseline_win":b["baseline_win"]}
                      for c,b in zip(cases,row["baseline_cases"])]
            if row["original_sha256"] != sha(sources[name]) or baseline!=row["baseline_cases"]:
                raise RuntimeError("Baseline receipts do not match frozen schedule")
            if row["frozen_opponents"] != opponents_for(name,ranked,2):
                raise RuntimeError("Wrong opponent panel")
            if len(row["candidates"])!=6:
                raise RuntimeError("Missing coordinated packages")
            for rec, item in zip(rows[name]["candidates"],row["candidates"]):
                validate_candidate(sources[name],rec,byname,a.proposals)
                if (item["candidate_sha256"]!=rec["sha256"] or item["path"]!=rec["path"]
                        or item["depth"]!=rec["depth"] or item["steps"]!=rec["steps"]
                        or item["heuristic_delta"]!=rec["heuristic_delta"]
                        or item["printed_synergy_signals"]!=rec["printed_synergy_signals"]
                        or item["status"]!="FOUR_REAL_407_TRAINING_BO3_PAIRS"
                        or len(item["paired_receipts"])!=4):
                    raise RuntimeError("Candidate was not completely evaluated")
                expected_paired=[{**c,"baseline_win":b["baseline_win"],
                                  "candidate_win":w["candidate_win"]}
                                 for c,b,w in zip(cases,baseline,item["paired_receipts"])]
                if (expected_paired!=item["paired_receipts"]
                    or any(x["candidate_win"] not in (0,1) for x in expected_paired)
                    or score(expected_paired)!=item["score"]):
                    raise RuntimeError("Paired 407 BO3 receipts inconsistent")
            verified.append(row)
    if len(seen)!=58 or sum(len(r["candidates"]) for r in verified)!=348:
        raise RuntimeError("Not all 58x6 candidates have real completed BO3")
    shortlist={}
    for row in verified:
        name=row["legend"]
        selected=sorted(row["candidates"],key=lambda x:(
            -x["score"]["delta"],-x["score"]["candidate_wins"],
            x["candidate_sha256"]))[:2]
        shortlist[name]=[{"path":c["path"],"sha256":c["candidate_sha256"],
            "training_candidate_wins":c["score"]["candidate_wins"],
            "training_baseline_wins":c["score"]["baseline_wins"],
            "mcnemar_p_unadjusted_training":c["score"]["mcnemar_p_unadjusted"]}
            for c in selected]
    a.output.mkdir(parents=True,exist_ok=True)
    summary={
        "status":"ALL58_348_MULTICARD_TRAINING_407_COMPLETED_NO_UPGRADES_ACCEPTED",
        "legends":58,"candidate_packages":348,
        "two_card_packages":174,"three_card_packages":174,
        "paired_bo3_cases_per_package":4,"candidate_bo3_completed":348*4,
        "baseline_bo3_completed":58*4,
        "engine_sha256":engine_sha,"source_manifest_sha256":sha(a.proposals/"manifest.json"),
        "agent":a.agent,"seed":a.seed,"sideboarding":False,
        "independent_holdout":False,"confirmed_upgrades":0,
        "source_decks_modified":False,"accepted_deck_changes":False,
        "shortlist_top_two_per_legend":shortlist,
    }
    (a.output/"summary.json").write_text(json.dumps(summary,indent=2))
    (a.output/"complete_training_receipts.json").write_text(json.dumps(verified,indent=2))
    print("ALL58_SYNERGY_348_NATIVE_407_TRAINING_PASS",json.dumps({
        k:v for k,v in summary.items() if k!="shortlist_top_two_per_legend"}),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ("selected","proposals","registry","ranked","certification"):
        p.add_argument("--"+name,type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--shards",type=int,default=29)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--generation-seed",type=int,default=202611282200)
    p.add_argument("--seed",type=int,default=202611292015)
    p.add_argument("--agent",default="ismcts:sims=24")
    p.add_argument("--timeout",type=float,default=175)
    a=p.parse_args()
    if not 0<=a.shard<a.shards<=58 or a.timeout<=0 or a.agent!="ismcts:sims=24":
        p.error("Unsupported training/shard arguments")
    if a.aggregate:
        if not a.input: p.error("Aggregation needs --input")
        aggregate(a)
    else:
        run(a)


if __name__ == "__main__":
    main()
