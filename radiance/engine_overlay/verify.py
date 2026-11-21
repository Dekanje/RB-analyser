#!/usr/bin/env python3
"""Smoke-check real C++ registry; semantic scenario tests remain required."""
import json,pathlib,subprocess
root=pathlib.Path(__file__).resolve().parents[2]
exe=root/"alpharune/build/riftbound"
out=root/"radiance/engine_overlay/compiled_registry.json"
subprocess.run([str(exe),"--dump-registry",str(out)],check=True)
cards=json.loads(out.read_text())["cards"]
bycode={c["public_code"]:c for c in cards}
assert len(cards)==976,len(cards)
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
assert bycode["RAD-147/167"]["card_type"]=="legend"
assert bycode["RAD-147/167"]["name"]=="Pride of Nazumah"
assert bycode["RAD-148/167"]["name"]=="Ntofo Strikes"
assert bycode["RAD-148/167"]["card_type"]=="spell"
assert bycode["RAD-148/167"]["super_type"]=="signature"
assert bycode["RAD-154/167"]["name"]=="Last Caress"
assert bycode["RAD-154/167"]["card_type"]=="spell"
assert bycode["RAD-143/167"]["card_type"]=="legend"
assert bycode["RAD-020/167"]["name"]=="Mordekaiser, Twice Slain"
assert bycode["RAD-144/167"]["name"]=="Realm of Death"
assert bycode["RAD-144/167"]["super_type"]=="signature"
assert bycode["RAD-155/167"]["card_type"]=="legend"
assert bycode["RAD-133/167"]["name"]=="Jarvan IV, Royal Heir"
assert bycode["RAD-156/167"]["card_type"]=="gear"
assert bycode["RAD-145/167"]["card_type"]=="legend"
assert bycode["RAD-042/167"]["name"]=="Orianna, Exquisite"
assert bycode["RAD-146/167"]["card_type"]=="gear"
assert bycode["RAD-141/167"]["card_type"]=="legend"
assert bycode["RAD-023/167"]["name"]=="Ziggs, Short-Fused"
assert bycode["RAD-142/167"]["card_type"]=="spell"
assert bycode["RAD-105/167"]["name"]=="Reckless Innovator"
print("REGISTRY_PASS: 976 compiled, includes 21 experimental Radiance additions including Bomb token")
# Real original Riven deck smoke; status is NOT a full semantic certification.
import sys
sys.path.insert(0,str(root/"scripts"))
from run_actual_games import decode, header, gametest
decks={header(f):f for f in decode()}
res=gametest(exe,decks["Riven, The Exile"],decks["Kennen, Heart of the Tempest"],
             20261121311,90,"random")
print("ORIGINAL_RIVEN_VS_KENNEN "+str(res["status"])+" "+res["stderr_tail"][-250:])
assert res["status"]=="complete",res["stderr_tail"][-1000:]
k=gametest(exe,decks["K'Sante, Pride of Nazumah"],
           decks["Kennen, Heart of the Tempest"],20261121401,90,"random")
print("ORIGINAL_KSANTE_VS_KENNEN "+str(k["status"])+" "+k["stderr_tail"][-250:])
assert k["status"]=="complete",k["stderr_tail"][-1000:]
e=gametest(exe,decks["Evelynn, Agony's Embrace"],
           decks["Kennen, Heart of the Tempest"],20261121411,90,"random")
print("ORIGINAL_EVELYNN_VS_KENNEN "+str(e["status"])+" "+e["stderr_tail"][-250:])
assert e["status"]=="complete",e["stderr_tail"][-1000:]
m=gametest(exe,decks["Mordekaiser, Iron Revenant"],
           decks["Kennen, Heart of the Tempest"],20261121421,90,"random")
print("ORIGINAL_MORDEKAISER_VS_KENNEN "+str(m["status"])+" "+m["stderr_tail"][-250:])
assert m["status"]=="complete",m["stderr_tail"][-1000:]
j=gametest(exe,decks["Jarvan IV, Exemplar of Demacia"],
           decks["Kennen, Heart of the Tempest"],20261121651,90,"random")
print("ORIGINAL_JARVAN_VS_KENNEN "+str(j["status"])+" "+j["stderr_tail"][-250:])
assert j["status"]=="complete",j["stderr_tail"][-1000:]
o=gametest(exe,decks["Orianna, Lady of Clockwork"],
           decks["Kennen, Heart of the Tempest"],20261121731,90,"random")
print("ORIGINAL_ORIANNA_VS_KENNEN "+str(o["status"])+" "+o["stderr_tail"][-250:])
assert o["status"]=="complete",o["stderr_tail"][-1000:]
z=gametest(exe,decks["Ziggs, Hexplosives Expert"],
           decks["Kennen, Heart of the Tempest"],20261121811,90,"random")
print("ORIGINAL_ZIGGS_VS_KENNEN "+str(z["status"])+" "+z["stderr_tail"][-250:])
assert z["status"]=="complete",z["stderr_tail"][-1000:]
print("FULL_NINE_DECKS_CERTIFIED: false")
