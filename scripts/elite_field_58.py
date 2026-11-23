#!/usr/bin/env python3
"""Stronger-agent exploratory screening: 58 fixed legal Legends vs 10 elite anchors.

No Legend is weakened for another. Opponents are immutable and chosen from
prior exploratory head-to-head rankings (not current outcomes). Distinguish
9-anchor evaluations for anchors themselves from 10-anchor outsiders.
Tournament sideboarding and whole-deck reoptimization are not modeled.
"""
from __future__ import annotations
import argparse
import collections
import concurrent.futures
import csv
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from competitive_topk import select_topk
from round_robin_58 import load_decks, sha, wilson
from optimize_58 import stable_seed
from evaluate_radiance_ismcts import engine_bo3


def roster(selected, ranked, num_anchors):
    all_decks, _ = load_decks(selected)
    anchors, rows = select_topk(selected, ranked, num_anchors)
    if len(all_decks) != 58:
        raise RuntimeError("58 independent legal candidate decks required")
    return all_decks, anchors, rows


def schedule(targets, anchors, shard, shards, repetitions, seed):
    """Each target vs all other elite anchors, with mirrored seating."""
    for idx, name in enumerate(sorted(targets)):
        if idx % shards != shard:
            continue
        for opp in sorted(anchors):
            if name == opp:
                continue
            for seat in (0, 1):
                for rep in range(repetitions):
                    yield {
                        "target": name, "anchor": opp, "seat": seat,
                        "repetition": rep,
                        "seed": stable_seed(
                            seed, "WORLD_PRE_LEGACY_ELITE_ANCHOR_V1",
                            name, opp, seat, rep
                        ),
                    }


def evaluate_shard(args):
    args.output.mkdir(parents=True, exist_ok=True)
    targets, anchors, anchor_rows = roster(
        args.selected, args.ranked, args.anchors
    )
    exe = args.engine.resolve()
    if not exe.is_file():
        raise RuntimeError("Repaired engine binary missing")
    jobs = list(schedule(targets, anchors, args.shard, args.shards,
                         args.repetitions, args.seed))
    env = os.environ.copy()
    def play(row):
        game = engine_bo3(
            exe, targets[row["target"]], anchors[row["anchor"]],
            row["seat"], row["seed"], args.agent, args.timeout, env
        )
        done = game["status"] == "complete" and game["winner"] in (1,2)
        return {**row, "complete": done, "status": game["status"],
                "target_win": (game["winner"] == row["seat"] + 1 if done else None),
                "error": game.get("error", ""),
                "games": game.get("games", []),
                "target_sha256": sha(targets[row["target"]]),
                "anchor_sha256": sha(anchors[row["anchor"]])}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        completed = list(pool.map(play, jobs))
    completed.sort(key=lambda r: (r["target"],r["anchor"],
                                   r["seat"],r["repetition"]))
    body = {"shard": args.shard, "shards": args.shards,
            "repetitions": args.repetitions, "anchors": args.anchors,
            "anchor_names": [r["legend"] for r in anchor_rows],
            "source_sha256": sha(args.ranked),
            "engine_sha256": sha(exe), "agent": args.agent,
            "seed": args.seed, "expected": len(jobs),
            "finished": sum(r["complete"] for r in completed),
            "sideboarding": False, "scenarios": completed}
    (args.output / "shard.json").write_text(
        json.dumps(body, indent=2), encoding="utf-8"
    )
    print("ELITE_58_SHARD",args.shard,body["finished"],body["expected"],flush=True)
    if body["finished"] != body["expected"]:
        raise RuntimeError("Failed game detected: no ranking released")


def aggregate(args):
    args.output.mkdir(parents=True, exist_ok=True)
    targets, anchors, anchor_rows = roster(
        args.selected, args.ranked, args.anchors
    )
    wanted = {}
    for row in schedule(targets, anchors, 0, 1, args.repetitions, args.seed):
        key = (row["target"], row["anchor"], row["seat"], row["repetition"])
        wanted[key] = row["seed"]
    all_rows = []
    binary_hashes = set()
    for shard in range(args.shards):
        path = args.input / f"elite-58-shard-{shard}" / "shard.json"
        p = json.loads(path.read_text())
        if any((
            p["shard"] != shard, p["shards"] != args.shards,
            p["repetitions"] != args.repetitions,
            p["anchors"] != args.anchors,
            p["anchor_names"] != [r["legend"] for r in anchor_rows],
            p["source_sha256"] != sha(args.ranked),
            p["agent"] != args.agent, p["seed"] != args.seed,
            p["sideboarding"] is not False,
            p["finished"] != p["expected"],
        )):
            raise RuntimeError("Mismatched shard metadata: " + str(path))
        binary_hashes.add(p["engine_sha256"])
        all_rows.extend(p["scenarios"])
    keys = [(r["target"],r["anchor"],r["seat"],r["repetition"]) for r in all_rows]
    if len(binary_hashes) != 1 or len(keys) != len(wanted) or set(keys) != set(wanted):
        raise RuntimeError("Missing, duplicate or wrong-source elite evaluation")
    for row in all_rows:
        key = (row["target"],row["anchor"],row["seat"],row["repetition"])
        if (not row["complete"] or row["status"] != "complete" or
            row["target_win"] not in (True,False) or
            row["seed"] != wanted[key] or
            row["target_sha256"] != sha(targets[row["target"]]) or
            row["anchor_sha256"] != sha(anchors[row["anchor"]])):
            raise RuntimeError("Engine failure or SHA mismatch")
    results = collections.defaultdict(lambda: {"wins":0,"series":0})
    for row in all_rows:
        v = results[row["target"]]
        v["series"] += 1
        v["wins"] += int(row["target_win"])
    standings = []
    for name in sorted(targets):
        r = results[name]
        anchor_count = args.anchors - int(name in anchors)
        if r["series"] != anchor_count * 2 * args.repetitions:
            raise RuntimeError("Incorrect per-Legend anchor coverage")
        lo, hi = wilson(r["wins"], r["series"])
        standings.append({
            "legend": name, "anchor_opponents": anchor_count,
            "wins": r["wins"], "series": r["series"],
            "win_rate": round(r["wins"]/r["series"],6),
            "wilson95_low": lo, "wilson95_high": hi,
            "deck_sha256": sha(targets[name]),
        })
    standings.sort(key=lambda x: (-x["win_rate"], x["legend"]))
    for rank,row in enumerate(standings,1):
        row["exploratory_elite_rank"] = rank
    columns=["exploratory_elite_rank","legend","anchor_opponents","wins",
             "series","win_rate","wilson95_low","wilson95_high","deck_sha256"]
    with (args.output / "all_58_elite_screen.csv").open(
            "w",newline="",encoding="utf-8") as fp:
        w=csv.DictWriter(fp,fieldnames=columns)
        w.writeheader()
        w.writerows(standings)
    (args.output / "standings.json").write_text(json.dumps(standings,indent=2))
    all_rows.sort(key=lambda r:(r["target"],r["anchor"],r["seat"],r["repetition"]))
    (args.output / "scenarios.json").write_text(json.dumps(all_rows,indent=2))
    summary={
        "status":"EXPLORATORY_58_VS_TOP10_128_ISMCTS_COMPLETE",
        "legends":58,"anchor_count":args.anchors,
        "pair_records_per_seat": args.repetitions,
        "completed_bo3_series":len(all_rows),
        "expected_bo3_series":len(wanted),
        "per_legend_anchor_exception":"Anchors skip their own deck",
        "agent":args.agent,"engine_sha256":next(iter(binary_hashes)),
        "source_rankings_sha256":sha(args.ranked),
        "all_games_complete":True,"sideboarding":False,
        "proves_optimal_deck":False,"worlds_probability":False,
        "limitations":[
            "Only screening against an inherited fixed ten-deck opponent panel",
            "Anchor Legends face nine opponents; outsiders face ten",
            "Small sample, dependent mirrored games and no confidence in exact rank order",
            "No simulated sideboard swaps or human-calibrated expert play",
        ],
    }
    (args.output / "summary.json").write_text(json.dumps(summary,indent=2))
    print("ELITE_58_FINAL",json.dumps(summary),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--ranked",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,default=pathlib.Path("engine_build/riftbound"))
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--anchors",type=int,default=10)
    p.add_argument("--shards",type=int,default=29)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--repetitions",type=int,default=1)
    p.add_argument("--agent",default="ismcts:sims=128")
    p.add_argument("--workers",type=int,default=2)
    p.add_argument("--timeout",type=float,default=240)
    p.add_argument("--seed",type=int,default=202611240102)
    args=p.parse_args()
    if not 2<=args.anchors<=58 or not 1<=args.shards<=58 or not 0<=args.shard<args.shards:
        p.error("Invalid anchor count or shard")
    if not 1<=args.repetitions<=30 or not 1<=args.workers<=16 or args.timeout<=0:
        p.error("Invalid simulation budget")
    if args.aggregate:
        if args.input is None:
            p.error("Aggregate mode requires --input")
        aggregate(args)
    else:
        evaluate_shard(args)

if __name__=="__main__":
    main()
