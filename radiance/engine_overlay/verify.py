#!/usr/bin/env python3
"""Smoke-check real C++ registry; semantic scenario tests remain required."""
import json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[2]
exe=root/"alpharune/build/riftbound"
out=root/"radiance/engine_overlay/compiled_registry.json"
subprocess.run([str(exe),"--dump-registry",str(out)],check=True)
cards=json.loads(out.read_text())["cards"]
bycode={c["public_code"]:c for c in cards}
assert len(cards)==957,len(cards)
assert bycode["RAD-149/167"]["name"]=="The Exile"
assert bycode["RAD-149/167"]["card_type"]=="legend"
assert bycode["RAD-086/167"]["name"]=="K'Sante, Courageous"
assert bycode["RAD-086/167"]["card_type"]=="unit"
assert bycode["RAD-086/167"]["features"]["shield_value"]==2
assert bycode["RAD-086/167"]["features"]["keywords"][0]==1
print("REGISTRY_PASS: 957 compiled, includes 2 experimental Radiance classes")
print("FULL_NINE_DECKS_CERTIFIED: false")
