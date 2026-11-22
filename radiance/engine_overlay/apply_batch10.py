#!/usr/bin/env python3
"""Apply Batch 10's 20 unique source identities after the accepted Batch 9 overlay.

This registers cards for incremental functional verification. Registry acceptance
must never be presented as certification of all printed mechanics.
"""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"
for src,dst in [
    ("cards/units/1048_radiance_batch10_tranche_a.cpp",
     "src/cards/units/1048_radiance_batch10_tranche_a.cpp"),
    ("cards/units/1058_radiance_batch10_tranche_b.cpp",
     "src/cards/units/1058_radiance_batch10_tranche_b.cpp"),
    ("tests/cards/test_radiance_batch10.cpp",
     "tests/cards/test_radiance_batch10.cpp"),
]:
    target=engine/dst
    if target.exists():raise SystemExit("Batch 10 source collision: "+str(target))
    shutil.copyfile(source/src,target)

init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
decl="void register_card_1047(CardRegistry&);"
reg="    register_card_1047(registry);"
assert s.count(decl)==1 and s.count(reg)==1, "Accepted Batch 9 anchor changed"
s=s.replace(decl,decl+"\n"+"\n".join(
    f"void register_card_{i}(CardRegistry&);" for i in range(1048,1068)),1)
s=s.replace(reg,reg+"\n"+"\n".join(
    f"    register_card_{i}(registry);" for i in range(1048,1068)),1)
init.write_text(s)
print("RADIANCE_BATCH10_OVERLAY_APPLIED: 20 new identities, IDs 1048..1067")
