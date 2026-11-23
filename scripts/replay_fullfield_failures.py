#!/usr/bin/env python3
"""Replay exact failing game seeds from 58-legend full-field and round-robin artifacts.

The input series seed is converted to the exact game seed used by the BO3
runner; do not substitute the series seed, which would be a different game.
Unknown engine results remain failures, never simulated wins.
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from optimize_58 import stable_seed
from run_actual_games import decode, header
from legal_candidate import make_legal_candidate

# (label, roster, deck A legend, deck B legend, initial seat, series seed,
#  zero-based specific failed game)
CASES = [
    ("primordial_roar_ev_lux", "selected",
     "Evelynn, Agony's Embrace", "Lux, Lady of Luminosity", 0, 1498714566, 0),
    ("primordial_roar_lee_nasus", "selected",
     "Lee Sin, Blind Monk", "Nasus, Curator of the Sands", 0, 1619278680, 1),
    ("one_two_punch_fiora_seraphine", "baseline",
     "Fiora, Grand Duelist", "Seraphine, Starry-Eyed Songstress", 1, 960472823, 0),
    ("primordial_roar_fiora_ornn", "baseline",
     "Fiora, Grand Duelist", "Ornn, Fire Below the Mountain", 0, 1418712806, 0),
    ("convergent_mutation_seraphine_vi", "selected",
     "Seraphine, Starry-Eyed Songstress", "Vi, Piltover Enforcer", 0, 462788786, 1),
    ("mordekaiser_jax_mord", "selected",
     "Jax, Grandmaster at Arms", "Mordekaiser, Iron Revenant", 0, 1421685259, 1),
    ("mordekaiser_mord_sett", "selected",
     "Mordekaiser, Iron Revenant", "Sett, The Boss", 0, 586095766, 2),
    ("mordekaiser_annie_mord", "baseline",
     "Annie, Dark Child", "Mordekaiser, Iron Revenant", 1, 1934929366, 0),
    # The full-field packet exposes only the series failure, not which
    # constituent game failed; replay all three deterministic game seeds.
    ("mesmerize_seraphine_fiora_g1", "baseline",
     "Seraphine, Starry-Eyed Songstress", "Fiora, Grand Duelist", 0, 1039926342, 0),
    ("mesmerize_seraphine_fiora_g2", "baseline",
     "Seraphine, Starry-Eyed Songstress", "Fiora, Grand Duelist", 0, 1039926342, 1),
    ("mesmerize_seraphine_fiora_g3", "baseline",
     "Seraphine, Starry-Eyed Songstress", "Fiora, Grand Duelist", 0, 1039926342, 2),
    ("burn_away_seraphine_mf_g1", "baseline",
     "Seraphine, Starry-Eyed Songstress", "Miss Fortune, Bounty Hunter", 1, 633416337, 0),
    ("burn_away_seraphine_mf_g2", "baseline",
     "Seraphine, Starry-Eyed Songstress", "Miss Fortune, Bounty Hunter", 1, 633416337, 1),
    ("burn_away_seraphine_mf_g3", "baseline",
     "Seraphine, Starry-Eyed Songstress", "Miss Fortune, Bounty Hunter", 1, 633416337, 2),
    ("lost_to_sands_kaisa_orianna_g1", "baseline",
     "Kai'Sa, Daughter of the Void", "Orianna, Lady of Clockwork", 1, 1738060168, 0),
    ("lost_to_sands_kaisa_orianna_g2", "baseline",
     "Kai'Sa, Daughter of the Void", "Orianna, Lady of Clockwork", 1, 1738060168, 1),
    ("lost_to_sands_kaisa_orianna_g3", "baseline",
     "Kai'Sa, Daughter of the Void", "Orianna, Lady of Clockwork", 1, 1738060168, 2),
]

def enumerate_roster(selected_folder, baseline_folder):
    selected = {header(p):p for p in selected_folder.glob("*.txt")}
    if len(selected)!=58:
        raise RuntimeError("Incomplete 58-legend selected roster")
    decks = decode()
    baselines = make_legal_candidate(decks, baseline_folder)
    if set(baselines)!=set(selected):
        raise RuntimeError("Selected and baseline roster have different legends")
    return selected,baselines

def execute(args):
    args.output.mkdir(parents=True,exist_ok=True)
    selected,baselines=enumerate_roster(args.selected,args.output/"baselines")
    report=[]
    for i,(label,roster,a,b,seat,series_seed,game_index) in enumerate(CASES,1):
        deck_a=(selected if roster=="selected" else baselines)[a]
        deck_b=(selected if roster=="selected" else baselines)[b]
        deck1,deck2=((deck_a,deck_b) if (seat+game_index)%2==0
                     else (deck_b,deck_a))
        seed=stable_seed(series_seed,"bo3",game_index)
        command=[str(args.engine.resolve()),"--deck1",str(deck1.resolve()),
                 "--deck2",str(deck2.resolve()),"--agent1",args.agent,
                 "--agent2",args.agent,"--game-mode","match","--seed",str(seed),
                 "--web","off","--render-html","off"]
        start=time.monotonic()
        try:
            proc=subprocess.run(command,capture_output=True,text=True,timeout=args.timeout)
            import re
            m=re.search(r"Game over:\s*winner\s*=\s*([12])",proc.stdout)
            good=proc.returncode==0 and m is not None
            status="complete" if good else "engine_error"
            error=proc.stderr[-2000:] if proc.stderr else (
                f"Process exit={proc.returncode}; no stderr; signal={-proc.returncode if proc.returncode<0 else 'none'}")
            rc=proc.returncode
        except subprocess.TimeoutExpired as ex:
            status="timeout";error=f"Timeout after {args.timeout}s";rc=None
        record={"label":label,"roster":roster,"deck1":header(deck1),
                "deck2":header(deck2),"bo3_series_seed":series_seed,
                "game_number":game_index+1,"exact_game_seed":seed,
                "status":status,"returncode":rc,"error":error,
                "elapsed_seconds":round(time.monotonic()-start,2)}
        report.append(record)
        (args.output/"exact_seed_replays.json").write_text(json.dumps(report,indent=2))
        print("EXACT_SEED_REPLAY",i,len(CASES),label,status,
              error[:200] if status!="complete" else "",flush=True)
    failed=[x["label"] for x in report if x["status"]!="complete"]
    if failed:
        raise RuntimeError("Exact-seed replays remain incomplete: "+", ".join(failed))
    print("EXACT_SEED_REPAIR_GATE_PASS",len(report),"real ISMCTS games",flush=True)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--engine",type=pathlib.Path,default=pathlib.Path("engine_build/riftbound"))
    ap.add_argument("--selected",type=pathlib.Path,default=pathlib.Path("results/selected/selected_decks"))
    ap.add_argument("--output",type=pathlib.Path,default=pathlib.Path("results/repaired_replays"))
    ap.add_argument("--agent",default="ismcts:sims=24")
    ap.add_argument("--timeout",type=int,default=85)
    execute(ap.parse_args())
