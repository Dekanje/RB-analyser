#!/usr/bin/env python3
"""Fail-closed pooled 512-vs-128 ISMCTS agent-strength paired mirrors.

This proves the compiled engine is stable at 512 sims and measures playing
policy improvement with the SAME deck on each seat. Even if 512 outperforms
128, expert-human tactical competence and deck ranking remain unvalidated.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"scripts"))
from benchmark_agent_strength import stable_seed,wilson_interval,sha256

PANEL=[
    "draven_glorious_executioner.txt",
    "leblanc_deceiver.txt",
    "master_yi_wuju_bladesman.txt",
    "miss_fortune_bounty_hunter.txt",
    "rek_sai_void_burrower.txt",
    "ambessa_matriarch_of_war.txt",
]


def pool(input_dir,decks_dir,engine,seed,repetitions):
    if len(PANEL)!=len(set(PANEL)):
        raise RuntimeError("Duplicate benchmark deck")
    all_games=[];by_deck=[]
    for index,file in enumerate(PANEL):
        p=input_dir/f"agent-strength-512-{index}"/"strength.json"
        packet=json.loads(p.read_text(encoding="utf-8"))
        summary=packet["summary"]
        if (summary["engine_sha256"]!=sha256(engine) or
            summary["baseline_agent"]!="ismcts:sims=128" or
            summary["challenger_agent"]!="ismcts:sims=512" or
            summary["decks_tested"]!=1 or
            summary["repetitions_per_deck"]!=repetitions or
            summary["mirrored_agent_seating"] is not True or
            summary["identical_deck_on_both_sides"] is not True or
            summary["failed_games"]!=0 or
            summary["completed_games"]!=2*repetitions or
            summary["conclusion"]!="SAMPLED_ONLY" or
            len(packet["by_deck"])!=1 or
            len(packet["games"])!=2*repetitions):
            raise RuntimeError("Incomplete/superficially altered 512 strength panel")
        if packet["by_deck"][0]["deck_file"]!=file:
            raise RuntimeError("Wrong file in agent strength benchmark")
        d=decks_dir/file
        expected_deck_hash=sha256(d)
        for rep in range(repetitions):
            pair=packet["games"][2*rep:2*rep+2]
            expected_seed=stable_seed(seed,file,rep)
            for seat,record in zip((True,False),pair):
                if (record["status"]!="complete" or
                    record["deck_file"]!=file or
                    record["deck_sha256"]!=expected_deck_hash or
                    record["repetition"]!=rep or
                    record["seed"]!=expected_seed or
                    record["challenger_first"] is not seat or
                    record["challenger_win"] not in (True,False) or
                    record["winner_seat"] not in (1,2) or
                    record["challenger_win"]!=(
                        record["winner_seat"]==(1 if seat else 2)
                    )):
                    raise RuntimeError("Invalid real-engine paired game proof")
        wins=sum(x["challenger_win"] for x in packet["games"])
        if wins!=summary["challenger_wins"]:
            raise RuntimeError("Inconsistent per-deck challenger wins")
        by_deck.append({"deck":file,"challenger_wins":wins,
                        "completed_games":2*repetitions,
                        "deck_sha256":expected_deck_hash})
        all_games+=packet["games"]
    total=len(all_games);wins=sum(x["challenger_win"] for x in all_games)
    lo,hi=wilson_interval(wins,total)
    return {
        "status":"512_VS_128_REAL_ENGINE_MIRROR_BENCHMARK_COMPLETE",
        "full_cpp_407_engine_sha256":sha256(engine),
        "baseline":"ismcts:sims=128","challenger":"ismcts:sims=512",
        "same_deck_both_seats":True,"paired_game_seeds":True,
        "decks_tested":len(PANEL),
        "completed_real_engine_games":total,
        "failed_games":0,
        "512_wins":wins,"512_sampled_win_rate":wins/total,
        "wilson95":(lo,hi),
        "512_strength_signal_significant":lo>0.5,
        "512_strength_not_expert_competence":True,
        "no_decks_optimized_or_promoted":True,
        "results_by_deck":by_deck,
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input",type=pathlib.Path,required=True)
    p.add_argument("--decks",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    p.add_argument("--seed",type=int,default=202611250900)
    p.add_argument("--repetitions",type=int,default=2)
    a=p.parse_args()
    if a.repetitions<1:
        p.error("Invalid per-deck repetitions")
    result=pool(a.input,a.decks,a.engine,a.seed,a.repetitions)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2))
    print("128_VS_512_FINAL",json.dumps(result),flush=True)


if __name__=="__main__":
    main()
