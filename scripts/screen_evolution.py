#!/usr/bin/env python3
"""Paired real-engine screening of broad 3-8-card mutation candidates.

Only a selected panel of Legends is screened initially. The result is an
EXPLORATORY short list, not a claim of optimized cards or Worlds win rates.
Baseline and changed deck are tested against the same frozen strong opponents
in the same seating orders and with identical seeds.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from full_field_58 import assess_row
from round_robin_58 import load_decks, sha

PILOT = ("Draven, Glorious Executioner", "Rek'Sai, Void Burrower")


def load_search_sources(selected, proposals, ranked, opponent_count):
    originals, _ = load_decks(selected)
    manifest=json.loads((proposals/"manifest.json").read_text(encoding="utf-8"))
    records={x["legend"]:x for x in manifest["records"]}
    if (len(records)!=58 or manifest["candidate_count"]!=2320 or
        manifest["source_roster"]!=58 or
        set(records)!=set(originals) or
        manifest["status"]!="CANDIDATES_ONLY_NO_WIN_RATE_CLAIM"):
        raise RuntimeError("Full 58-legend proposal provenance missing")
    rows=json.loads(ranked.read_text(encoding="utf-8"))
    if (len(rows)!=58 or
        [r["rank_exploratory"] for r in rows]!=list(range(1,59)) or
        set(x["legend"] for x in rows)!=set(originals)):
        raise RuntimeError("Invalid independent frozen opponent rankings")
    for x in rows:
        if sha(originals[x["legend"]])!=x["deck_sha256"]:
            raise RuntimeError("Opponent SHA mismatch: "+x["legend"])
    for name, record in records.items():
        if (record["source_sha256"]!=sha(originals[name]) or
            record["generated"]!=40 or len(record["candidates"])!=40):
            raise RuntimeError("Source or candidate-population mismatch: "+name)
    if not 1<=opponent_count<=10:
        raise ValueError("Must screen against between 1 and 10 top anchors")
    return originals, records, rows


def opponent_panel(legend, rows, original, count):
    names=[r["legend"] for r in rows if r["legend"]!=legend][:count]
    if len(names)!=count:
        raise RuntimeError("Incomplete opponent panel")
    return {n:original[n] for n in names}


def validate_candidate_text(baseline:pathlib.Path, candidate:pathlib.Path, expected_sha:str):
    if sha(candidate)!=expected_sha:
        raise RuntimeError("Candidate SHA mismatch: "+str(candidate))
    before=baseline.read_text(encoding="utf-8")
    after=candidate.read_text(encoding="utf-8")
    if ("MainDeck:" not in before or "Battlefields:" not in before or
        "MainDeck:" not in after or "Battlefields:" not in after):
        raise RuntimeError("Malformed constructed deck")
    # MainDeck contents may change. The ONLY permitted non-main delta is
    # an appended NeekoLegends section with exactly three distinct Legends,
    # required by card RAD-167's registration rule. The base Legend, chosen
    # Champion, battlefield, rune and sideboard declarations are immutable.
    if before.split("MainDeck:",1)[0] != after.split("MainDeck:",1)[0]:
        raise RuntimeError("Candidate changed registered Legend/Champion")
    base_tail=before.split("Battlefields:",1)[1].rstrip()
    changed_tail=after.split("Battlefields:",1)[1].rstrip()
    if changed_tail!=base_tail:
        delimiter="\nNeekoLegends:\n"
        if changed_tail.count(delimiter)!=1:
            raise RuntimeError("Candidate changed registered non-main deck sections")
        original_tail, additional=changed_tail.split(delimiter,1)
        if original_tail.rstrip()!=base_tail:
            raise RuntimeError("Candidate altered original battlefield/rune/sideboard")
        lines=additional.splitlines()
        if len(lines)!=3 or any(not line.startswith("1 ") for line in lines):
            raise RuntimeError("Neeko special registration needs exactly three Legends")
        legends=[line[2:].strip() for line in lines]
        current_legend=before.split("Legend:",1)[1].split("Champion:",1)[0]
        source_legend=current_legend.strip().removeprefix("1 ").split(",",1)[-1].strip()
        if (len(set(legends))!=3 or any(not x for x in legends) or
            source_legend in legends):
            raise RuntimeError("Neeko registered Legends must be distinct, excluding self")
        main=after.split("MainDeck:",1)[1].split("Battlefields:",1)[0]
        if "Neeko, Blending In" not in main:
            raise RuntimeError("Neeko additional Legends supplied without Neeko")
    return True


def pilot_shard(args):
    originals, records, rows=load_search_sources(
        args.selected,args.proposals,args.ranked,args.opponents
    )
    legend=PILOT[args.legend_index]
    src=originals[legend]
    if not args.engine.is_file():
        raise RuntimeError("Engine binary missing")
    opponents=opponent_panel(legend,rows,originals,args.opponents)
    candidates=records[legend]["candidates"]
    selected=[(i,c) for i,c in enumerate(candidates) if i%args.shards==args.shard]
    args.output.mkdir(parents=True,exist_ok=True)
    results=[]
    for number, candidate in selected:
        if candidate["status"]!="UNTESTED_STRUCTURAL_CANDIDATE" or candidate["engine_simulated"]:
            raise RuntimeError("Input candidate already marked evaluated/invalid")
        candfile=args.proposals/candidate["path"]
        validate_candidate_text(src,candfile,candidate["sha256"])
        report=assess_row(
            legend,src,candfile,opponents,args.engine.resolve(),
            args.agent,args.timeout,args.repetitions,args.seed,args.workers
        )
        if (report["incomplete"] or report["completed"]!=
            len(opponents)*2*args.repetitions or
            report["baseline_sha256"]!=sha(src) or
            report["candidate_sha256"]!=candidate["sha256"]):
            raise RuntimeError("Incomplete or inconsistent candidate simulation")
        results.append({
            "candidate_index":number,
            "candidate_path":candidate["path"],
            "mutation_steps":candidate["mutation_steps"],
            "changed_main_slots":candidate["changed_main_slots"],
            "evaluation":report,
        })
        print("EVOLUTIONARY_SCREEN",legend,number,
              report["candidate_minus_baseline"],
              report["candidate_wins"],report["baseline_wins"],flush=True)
    payload={
        "legend":legend,"source_sha256":sha(src),
        "proposals_manifest_sha256":sha(args.proposals/"manifest.json"),
        "opponent_ranking_sha256":sha(args.ranked),
        "engine_sha256":sha(args.engine),
        "agent":args.agent,"seed":args.seed,
        "opponents":list(opponents),
        "repetitions":args.repetitions,
        "shard":args.shard,"shards":args.shards,
        "expected_candidates":len(selected),
        "complete_candidates":len(results),
        "status":"PAIRED_REAL_ENGINE_EXPLORATORY",
        "sideboarding":False,"records":results,
    }
    (args.output/"screen.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
    print("EVOLUTIONARY_SHARD_PASS",legend,len(results),flush=True)


def aggregate(args):
    originals, records, ranked=load_search_sources(
        args.selected,args.proposals,args.ranked,args.opponents
    )
    args.output.mkdir(parents=True,exist_ok=True)
    results_by_legend={}
    binary_hashes=set()
    for legend_index,legend in enumerate(PILOT):
        expected_panel=list(opponent_panel(legend,ranked,originals,args.opponents))
        merged=[]
        seen=set()
        for shard in range(args.shards):
            p=args.input/f"evolution-screen-{legend_index}-{shard}"/"screen.json"
            row=json.loads(p.read_text(encoding="utf-8"))
            if any((
                row["legend"]!=legend,row["source_sha256"]!=sha(originals[legend]),
                row["proposals_manifest_sha256"]!=sha(args.proposals/"manifest.json"),
                row["opponent_ranking_sha256"]!=sha(args.ranked),
                row["agent"]!=args.agent,row["seed"]!=args.seed,
                row["opponents"]!=expected_panel,
                row["repetitions"]!=args.repetitions,
                row["shard"]!=shard,row["shards"]!=args.shards,
                row["expected_candidates"]!=row["complete_candidates"],
                row["sideboarding"] is not False,
            )):
                raise RuntimeError("Untrusted candidate shard metadata")
            binary_hashes.add(row["engine_sha256"])
            for item in row["records"]:
                n=item["candidate_index"]
                if n in seen or n not in range(40) or n%args.shards!=shard:
                    raise RuntimeError("Repeated or unexpected candidate index")
                seen.add(n)
                expected=records[legend]["candidates"][n]
                if (item["candidate_path"]!=expected["path"] or
                    item["changed_main_slots"]!=expected["changed_main_slots"] or
                    item["mutation_steps"]!=expected["mutation_steps"]):
                    raise RuntimeError("Changed candidate manifest metadata")
                validate_candidate_text(
                    originals[legend],args.proposals/item["candidate_path"],
                    expected["sha256"]
                )
                ev=item["evaluation"]
                if (ev["incomplete"] or not ev["changed"] or
                    ev["completed"]!=args.opponents*2*args.repetitions or
                    ev["baseline_sha256"]!=sha(originals[legend]) or
                    ev["candidate_sha256"]!=expected["sha256"] or
                    len(ev["per_opponent"])!=args.opponents or
                    set(x["opponent"] for x in ev["per_opponent"])!=set(expected_panel)):
                    raise RuntimeError("Incomplete or wrong-source real-engine comparisons")
                merged.append(item)
        if seen!=set(range(40)):
            raise RuntimeError("Incomplete candidate population: "+legend)
        results_by_legend[legend]=sorted(
            merged,key=lambda x:(-x["evaluation"]["candidate_minus_baseline"],
                                  -x["evaluation"]["candidate_wins"],
                                  x["candidate_index"])
        )
    if len(binary_hashes)!=1:
        raise RuntimeError("Mixed engine binaries across screening shards")
    shortlists={}
    for legend in PILOT:
        ranked=results_by_legend[legend]
        shortlists[legend]=[{
            "candidate_index":x["candidate_index"],
            "candidate_path":x["candidate_path"],
            "sha256":x["evaluation"]["candidate_sha256"],
            "paired_win_delta":x["evaluation"]["candidate_minus_baseline"],
            "candidate_wins":x["evaluation"]["candidate_wins"],
            "baseline_wins":x["evaluation"]["baseline_wins"],
            "paired_samples":x["evaluation"]["completed"],
            "changed_main_slots":x["changed_main_slots"],
            "mcnemar_p_unadjusted":x["evaluation"]["mcnemar_p"],
            "status":"SCREENING_ONLY_NOT_HOLDOUT_CONFIRMED",
        } for x in ranked[:args.shortlist]]
    meta={
        "status":"EXPLORATORY_PILOT_SCREEN_COMPLETE",
        "legend_count":len(PILOT),"candidates_per_legend":40,
        "total_screened":sum(len(x) for x in results_by_legend.values()),
        "agent":args.agent,"engine_sha256":next(iter(binary_hashes)),
        "strong_opponents_per_legend":args.opponents,
        "mirrored_seats":True,"repetitions":args.repetitions,
        "baseline_source_sha256":
            {name:sha(originals[name]) for name in PILOT},
        "sideboarding":False,"holdout_validation":False,
        "candidate_confirmation":"NOT_ESTABLISHED",
        "shortlists":shortlists,
    }
    (args.output/"shortlists.json").write_text(json.dumps(meta,indent=2))
    (args.output/"full_screening.json").write_text(
        json.dumps(results_by_legend,indent=2)
    )
    print("EVOLUTIONARY_PILOT_FINAL",json.dumps({
        k:v for k,v in meta.items() if k!="shortlists"
    }),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--proposals",type=pathlib.Path,required=True)
    p.add_argument("--ranked",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,default=pathlib.Path("engine_build/riftbound"))
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--input",type=pathlib.Path)
    p.add_argument("--aggregate",action="store_true")
    p.add_argument("--legend-index",type=int,default=0)
    p.add_argument("--shards",type=int,default=4)
    p.add_argument("--shard",type=int,default=0)
    p.add_argument("--opponents",type=int,default=3)
    p.add_argument("--repetitions",type=int,default=1)
    p.add_argument("--shortlist",type=int,default=5)
    p.add_argument("--agent",default="ismcts:sims=24")
    p.add_argument("--timeout",type=float,default=120)
    p.add_argument("--workers",type=int,default=3)
    p.add_argument("--seed",type=int,default=202611241203)
    a=p.parse_args()
    if not 0<=a.legend_index<len(PILOT) or not 0<=a.shard<a.shards<=40:
        p.error("Invalid Legend or shard")
    if not 1<=a.opponents<=10 or not 1<=a.repetitions<=10 or not 1<=a.shortlist<=40:
        p.error("Invalid opponent/holdout configuration")
    if not 1<=a.workers<=16 or a.timeout<=0:
        p.error("Invalid game execution parameters")
    if a.aggregate:
        if a.input is None:
            p.error("Aggregation requires --input")
        aggregate(a)
    else:
        pilot_shard(a)


if __name__=="__main__":
    main()
