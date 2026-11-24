#!/usr/bin/env python3
"""Prove that RAD-167 Neeko proposals are playable WITH legal pregame Legends.

This imports two previously blocked candidate Main Decks unchanged and adds
the C++ deck parser's supported NeekoLegends section. Never call any Neeko
mutation legal unless the 3 extra distinct Legends are declared and engine-
validated. This is a capability test, not competitive optimization.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess


EXTRA_LEGENDS = ("Loose Cannon", "Nine-Tailed Fox", "Blind Monk")
ARCHIVED_CANDIDATES = (
    ("Evelynn, Agony's Embrace",
     "evelynn_agony_s_embrace/candidate_0030.txt",
     "ddc58e2c9612b585235d0eecd277971c4a55633bee7732da78544765b3797f12"),
    ("Shen, Eye of Twilight",
     "shen_eye_of_twilight/candidate_0000.txt",
     "746ae7dc1753ab907bc20a4ccd1048e9f9f3784d24a38bd1ad0f5dd8fb555752"),
)


def write_registered_neeko_deck(source: pathlib.Path, destination: pathlib.Path):
    old = source.read_text(encoding="utf-8")
    if re.search(r"(?m)^NeekoLegends:\s*$", old):
        raise ValueError("Neeko registration section already exists")
    if len(re.findall(r"(?m)^\d+ Neeko, Blending In$",old)) != 1:
        raise ValueError("Expected one Neeko printing among this archived main deck")
    if "Sideboard:" not in old or not re.search(r"(?m)^Legend:\s*$",old):
        raise ValueError("Missing required Constructed source sections")
    if len(set(EXTRA_LEGENDS))!=3:
        raise ValueError("Three different additional Legends are required")
    registered = old.rstrip() + "\n\nNeekoLegends:\n"
    registered += "\n".join(f"1 {name}" for name in EXTRA_LEGENDS) + "\n"
    destination.parent.mkdir(parents=True,exist_ok=True)
    destination.write_text(registered,encoding="utf-8")


def play_game(engine:pathlib.Path, own:pathlib.Path, other:pathlib.Path, seed:int):
    argv=[str(engine.resolve()),"--deck1",str(own.resolve()),
          "--deck2",str(other.resolve()),"--agent1","ismcts:sims=24",
          "--agent2","ismcts:sims=24","--game-mode","match",
          "--seed",str(seed),"--web","off","--render-html","off"]
    try:
        result=subprocess.run(argv,capture_output=True,text=True,timeout=150)
    except subprocess.TimeoutExpired:
        return {"status":"timeout","winner":None,"error":"150s per-game timeout"}
    matches=re.findall(r"Game over:\s*winner\s*=\s*([012])",result.stdout)
    complete=result.returncode==0 and matches and matches[-1] in ("1","2")
    return {
        "status":"complete" if complete else "failure",
        "winner":int(matches[-1]) if complete else None,
        "returncode":result.returncode,
        "error":(result.stderr[-3000:]+result.stdout[-1000:]) if not complete else "",
    }


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--proposals",type=pathlib.Path,required=True)
    p.add_argument("--selected",type=pathlib.Path,required=True)
    p.add_argument("--engine",type=pathlib.Path,required=True)
    p.add_argument("--output",type=pathlib.Path,required=True)
    a=p.parse_args()
    a.output.mkdir(parents=True,exist_ok=True)
    anchors={"Evelynn, Agony's Embrace":"rek_sai_void_burrower.txt",
             "Shen, Eye of Twilight":"draven_glorious_executioner.txt"}
    records=[]
    for n,(legend,relative,expected_sha) in enumerate(ARCHIVED_CANDIDATES):
        source=a.proposals/relative
        digest=hashlib.sha256(source.read_bytes()).hexdigest()
        if digest!=expected_sha:
            raise RuntimeError("Frozen candidate SHA mismatch: "+legend)
        deck=a.output/"registered_decks"/source.name
        write_registered_neeko_deck(source,deck)
        opponent=a.selected/"selected_decks"/anchors[legend]
        if not opponent.is_file():
            raise RuntimeError("Missing frozen opponent deck")
        outcome=play_game(a.engine,deck,opponent,202611240800+n)
        records.append({
            "legend":legend,"original_source_sha256":digest,
            "registered_sha256":hashlib.sha256(deck.read_bytes()).hexdigest(),
            "chosen_extra_legends":list(EXTRA_LEGENDS),
            "outcome":outcome,
        })
        print("NEEKO_REGISTERED_GAME",legend,outcome["status"],
              outcome["winner"],flush=True)
    report={
        "status":"NEEKO_SPECIAL_REGISTERED_ACTUAL_ENGINE_SMOKE",
        "candidate_count":2,
        "completed_games":sum(x["outcome"]["status"]=="complete" for x in records),
        "expected_games":2,"sims":24,
        "note":"This restores special Neeko deckbuilding legality; does NOT validate deck superiority.",
        "records":records,
    }
    (a.output/"receipt.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    if report["completed_games"]!=2:
        raise RuntimeError("Neeko registered candidate game failed; see receipt")


if __name__=="__main__":
    main()
