#!/usr/bin/env python3
"""Smoke-check real C++ registry; semantic scenario tests remain required."""
import json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[2]
exe=root/"alpharune/build/riftbound"
out=root/"radiance/engine_overlay/compiled_registry.json"
subprocess.run([str(exe),"--dump-registry",str(out)],check=True)
cards=json.loads(out.read_text())["cards"]
bycode={c["public_code"]:c for c in cards}
assert len(cards)==959,len(cards)
assert bycode["RAD-149/167"]["name"]=="The Exile"
assert bycode["RAD-149/167"]["card_type"]=="legend"
assert bycode["RAD-086/167"]["name"]=="K'Sante, Courageous"
assert bycode["RAD-086/167"]["card_type"]=="unit"
assert bycode["RAD-086/167"]["features"]["shield_value"]==2
assert bycode["RAD-086/167"]["features"]["keywords"][0]==1
assert bycode["RAD-153/167"]["name"]=="Agony's Embrace"
assert bycode["RAD-153/167"]["card_type"]=="legend"
assert bycode["RAD-150/167"]["name"]=="Blade of the Exile"
assert bycode["RAD-150/167"]["card_type"]=="gear"
assert bycode["RAD-150/167"]["super_type"]=="signature"
print("REGISTRY_PASS: 959 compiled, includes 4 experimental Radiance classes")
# Real original Riven deck smoke; status is NOT a full semantic certification.
import sys
sys.path.insert(0,str(root/"scripts"))
from run_actual_games import decode, header, gametest
decks={header(f):f for f in decode()}
res=gametest(exe,decks["Riven, The Exile"],decks["Kennen, Heart of the Tempest"],
             20261121311,90,"random")
print("ORIGINAL_RIVEN_VS_KENNEN "+str(res["status"])+" "+res["stderr_tail"][-250:])
assert res["status"]=="complete",res["stderr_tail"][-1000:]
print("FULL_NINE_DECKS_CERTIFIED: false")
