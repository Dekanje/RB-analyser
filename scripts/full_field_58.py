#!/usr/bin/env python3
"""Evaluate all 58 independently optimized Radiance decks against all 57 legal baselines.

This evaluates real AlphaRune BO3, mirrored seats, paired independent seeds.
The opponent field is fixed for comparability. It is NOT a tournament sideboard
simulation, a solved metagame, or a proof of globally optimal deck construction.
Every engine error is retained and causes fail-closed final assembly.
"""
import argparse
import collections
import concurrent.futures
import csv
import hashlib
import json
import math
import os
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from optimize_58 import stable_seed
from evaluate_radiance_ismcts import engine_bo3
from legal_candidate import make_legal_candidate
from run_actual_games import decode, header


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_source(output):
    raw = decode()
    return make_legal_candidate(raw, output / "legal_baselines")


def indexed(paths):
    result = {header(path): path for path in paths}
    if len(result) != len(paths):
        raise RuntimeError("Duplicate legend in roster")
    return result


def read_selected(root, originals):
    rows = json.loads((root / "all_58_trials.json").read_text(encoding="utf8"))
    selected = indexed(list((root / "selected_decks").glob("*.txt")))
    if len(rows) != 58 or len(selected) != 58:
        raise RuntimeError("Expected exactly 58 selected decks")
    expected = set(originals)
    if set(selected) != expected or {r["legend"] for r in rows} != expected:
        raise RuntimeError("Selected 58-legend roster differs from source")
    report = {}
    for row in rows:
        name = row["legend"]
        if digest(originals[name]) != row["original_sha256"]:
            raise RuntimeError("Source deck SHA drift: " + name)
        if digest(selected[name]) != row["effective_sha256"]:
            raise RuntimeError("Selected deck SHA drift: " + name)
        if (digest(originals[name]) != digest(selected[name])) != bool(row["selected"]):
            raise RuntimeError("Changed status inconsistent: " + name)
        report[name] = row
    return selected, report


def schedule(names, target, repeats, seed):
    """Exactly 57 opponents * two seat orders * repetitions per legend."""
    for opponent in sorted(names):
        if opponent == target:
            continue
        for seat in (0, 1):
            for repetition in range(repeats):
                yield (opponent, seat, repetition,
                       stable_seed(seed, target, opponent, seat, repetition,
                                   "ALL_57_INDEPENDENT_PAIRED"))


def mcnemar_exact(a_only, b_only):
    n = a_only + b_only
    if n == 0:
        return 1.0
    return min(1.0, 2.0 * sum(math.comb(n, k) for k in range(min(a_only, b_only) + 1)) / (2 ** n))


def holm(records):
    """Exact two-sided paired McNemar, family-wise Holm at 5% across changed decks."""
    changed = [r for r in records if r["changed"]]
    previous = 0.0
    for rank, row in enumerate(sorted(changed, key=lambda r: (r["mcnemar_p"], r["legend"]))):
        previous = max(previous, (len(changed)-rank) * row["mcnemar_p"])
        row["holm_adjusted_p"] = min(1.0, previous)
        row["independently_confirmed"] = (
            row["incomplete"] == 0 and
            row["candidate_wins"] > row["baseline_wins"] and
            row["holm_adjusted_p"] < 0.05)
    for row in records:
        if not row["changed"]:
            row["holm_adjusted_p"] = 1.0
            row["independently_confirmed"] = False
    return records


def assess_row(name, baseline, candidate, opponents, exe, agent, timeout,
               repeats, seed, workers):
    changed = digest(baseline) != digest(candidate)
    matches = list(schedule(opponents, name, repeats, seed))
    env = os.environ.copy()

    def evaluate(opponent, seat, repetition, match_seed):
        other = opponents[opponent]
        left = engine_bo3(exe, baseline, other, seat, match_seed, agent, timeout, env)
        right = (engine_bo3(exe, candidate, other, seat, match_seed, agent, timeout, env)
                 if changed else left)
        both_complete = left["status"] == right["status"] == "complete"
        baseline_win = (int(left["winner"] == seat+1) if both_complete else None)
        candidate_win = (int(right["winner"] == seat+1) if both_complete else None)
        return {"opponent": opponent, "seat": seat, "repetition": repetition,
                "seed": match_seed, "both_complete": both_complete,
                "baseline_status": left["status"], "candidate_status": right["status"],
                "baseline_win": baseline_win, "candidate_win": candidate_win,
                "baseline_error": left.get("error", ""),
                "candidate_error": right.get("error", "")}

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(lambda item: evaluate(*item), matches))
    results.sort(key=lambda r: (r["opponent"], r["seat"], r["repetition"]))
    complete = [r for r in results if r["both_complete"]]
    baseline_wins = sum(r["baseline_win"] for r in complete)
    candidate_wins = sum(r["candidate_win"] for r in complete)
    a_only = sum(r["candidate_win"] and not r["baseline_win"] for r in complete)
    b_only = sum(r["baseline_win"] and not r["candidate_win"] for r in complete)
    by_opponent = []
    for opp in sorted(opponents):
        if opp == name:
            continue
        rows = [r for r in complete if r["opponent"] == opp]
        count = len(rows)
        by_opponent.append({
            "opponent": opp, "completed": count, "expected": 2*repeats,
            "baseline_wins": sum(r["baseline_win"] for r in rows),
            "candidate_wins": sum(r["candidate_win"] for r in rows),
            "candidate_delta": sum(r["candidate_win"]-r["baseline_win"] for r in rows)})
    record = {"legend": name, "changed": changed, "total_opponents": len(opponents)-1,
              "expected": len(matches), "completed": len(complete),
              "incomplete": len(matches)-len(complete),
              "baseline_wins": baseline_wins, "candidate_wins": candidate_wins,
              "candidate_only_wins": a_only, "baseline_only_wins": b_only,
              "candidate_minus_baseline": candidate_wins-baseline_wins,
              "candidate_win_rate": (candidate_wins/len(complete) if complete else None),
              "baseline_win_rate": (baseline_wins/len(complete) if complete else None),
              "mcnemar_p": mcnemar_exact(a_only,b_only),
              "worse_opponents": [x["opponent"] for x in by_opponent if x["candidate_delta"] < 0],
              "improved_opponents": [x["opponent"] for x in by_opponent if x["candidate_delta"] > 0],
              "per_opponent": by_opponent,
              "scenarios": results,
              "baseline_sha256": digest(baseline),
              "candidate_sha256": digest(candidate)}
    return record


def run_shard(args):
    args.output.mkdir(parents=True, exist_ok=True)
    originals = frozen_source(args.output / "sources")
    selected, reports = read_selected(args.selected, originals)
    if len(originals) != 58:
        raise RuntimeError("Expected 58 legal baseline decks")
    chosen = sorted(originals)
    names = [name for i, name in enumerate(chosen) if i % args.shards == args.shard]
    completed = []
    for index, name in enumerate(names, 1):
        row = assess_row(name, originals[name], selected[name], originals,
                         args.engine.resolve(), args.agent, args.timeout,
                         args.repetitions, args.seed, args.workers)
        assert row["changed"] == bool(reports[name]["selected"])
        assert len(row["per_opponent"]) == 57
        assert row["expected"] == 57*2*args.repetitions
        completed.append(row)
        print("ALL_57_FULL_FIELD", args.shard, index, "/", len(names),
              name, "completed", row["completed"], "/", row["expected"],
              "delta", row["candidate_minus_baseline"], flush=True)
        (args.output / "full_field.json").write_text(json.dumps(
            {"shard": args.shard, "shards": args.shards,
             "repetitions": args.repetitions, "legends": completed}, indent=2))
    failures = [r["legend"] for r in completed if r["incomplete"]]
    if failures:
        raise RuntimeError("Full-field matchups incomplete; no false outcomes accepted: "+
                           ", ".join(failures))


def aggregate(args):
    args.output.mkdir(parents=True, exist_ok=True)
    originals = frozen_source(args.output / "sources")
    selected, selected_reports = read_selected(args.selected, originals)
    records=[]
    for shard in range(args.shards):
        path = args.input / f"shard-{shard}" / "full_field.json"
        package = json.loads(path.read_text())
        if package["shard"] != shard or package["shards"] != args.shards:
            raise RuntimeError("Wrong shard provenance: "+str(path))
        if package["repetitions"] != args.repetitions:
            raise RuntimeError("Repetition mismatch")
        records.extend(package["legends"])
    names = [r["legend"] for r in records]
    if len(names) != 58 or set(names) != set(originals):
        raise RuntimeError("Full 58-legend validation missing or duplicated")
    for row in records:
        name = row["legend"]
        if (row["expected"] != 57*2*args.repetitions or
                row["completed"] != row["expected"] or row["incomplete"] or
                len(row["per_opponent"]) != 57 or
                set(x["opponent"] for x in row["per_opponent"]) != set(originals)-{name} or
                row["baseline_sha256"] != digest(originals[name]) or
                row["candidate_sha256"] != digest(selected[name])):
            raise RuntimeError("Full field incomplete / source changed: " + name)
        if row["changed"] != bool(selected_reports[name]["selected"]):
            raise RuntimeError("Candidate mismatch: " + name)
    holm(records)
    records.sort(key=lambda r:r["legend"])
    conservative = args.output / "conservative_confirmed_decks"
    exploratory = args.output / "exploratory_selected_decks"
    conservative.mkdir(exist_ok=True);exploratory.mkdir(exist_ok=True)
    table=[]
    for row in records:
        name=row["legend"]
        source = selected[name] if row["independently_confirmed"] else originals[name]
        shutil.copy2(source, conservative / originals[name].name)
        shutil.copy2(selected[name], exploratory / originals[name].name)
        table.append({key:row[key] for key in (
            "legend","changed","completed","expected","baseline_wins",
            "candidate_wins","candidate_minus_baseline","mcnemar_p",
            "holm_adjusted_p","independently_confirmed","baseline_sha256",
            "candidate_sha256")})
    with (args.output / "all_58_decisions.csv").open("w", newline="") as fp:
        writer=csv.DictWriter(fp, fieldnames=list(table[0]))
        writer.writeheader();writer.writerows(table)
    (args.output / "all_58_full_field.json").write_text(json.dumps(records,indent=2))
    meta={"legends_evaluated":58, "opponents_per_legend":57, "both_seats":True,
          "paired_repetitions_per_seat":args.repetitions,
          "total_paired_scenarios":sum(r["expected"] for r in records),
          "complete_paired_scenarios":sum(r["completed"] for r in records),
          "candidate_decks_changed":sum(r["changed"] for r in records),
          "improvements_holm_confirmed":sum(r["independently_confirmed"] for r in records),
          "all_58_decks_exported":len(list(conservative.glob("*.txt")))==58,
          "opponents":"frozen legal 58-deck baseline field, not simultaneously reoptimized",
          "agent":args.agent, "fixed_deck_bo3":True, "sideboard_swaps":False,
          "global_optimality_proven":False, "status":"FULL_FIELD_VALIDATION_COMPLETE"}
    (args.output/"summary.json").write_text(json.dumps(meta,indent=2))
    print("ALL_58_FULL_FIELD_FINAL",json.dumps(meta),flush=True)


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--selected",type=pathlib.Path,required=True)
    parser.add_argument("--engine",type=pathlib.Path,default=pathlib.Path("engine_build/riftbound"))
    parser.add_argument("--output",type=pathlib.Path,required=True)
    parser.add_argument("--input",type=pathlib.Path)
    parser.add_argument("--aggregate",action="store_true")
    parser.add_argument("--shard",type=int,default=0)
    parser.add_argument("--shards",type=int,default=29)
    parser.add_argument("--repetitions",type=int,default=1)
    parser.add_argument("--workers",type=int,default=4)
    parser.add_argument("--timeout",type=int,default=65)
    parser.add_argument("--agent",default="ismcts:sims=24")
    parser.add_argument("--seed",type=int,default=2026112399192)
    args=parser.parse_args()
    if not 0 <= args.shard < args.shards <= 58:
        parser.error("Invalid shard assignment")
    if not 1 <= args.repetitions <= 10 or not 1 <= args.workers <= 16:
        parser.error("Invalid evaluation budget")
    if args.aggregate:
        if args.input is None:
            parser.error("--aggregate requires --input")
        aggregate(args)
    else:
        run_shard(args)
