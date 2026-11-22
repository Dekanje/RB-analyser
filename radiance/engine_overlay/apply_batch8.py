#!/usr/bin/env python3
"""Apply Radiance Batch 8 after the fully validated Batch 7 overlay."""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"
files=[
 ("cards/units/1010_radiance_batch8.cpp","src/cards/units/1010_radiance_batch8.cpp"),
 ("tests/cards/test_radiance_batch8.cpp","tests/cards/test_radiance_batch8.cpp"),
]
for src,dest in files:
    target=engine/dest
    if target.exists():raise SystemExit("Batch8 source collision: "+str(target))
    shutil.copyfile(source/src,target)
init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
declaration="void register_card_1009(CardRegistry&);"
registration="    register_card_1009(registry);"
assert s.count(declaration)==1 and s.count(registration)==1, "Batch7 anchors changed"
s=s.replace(declaration,declaration+"\n"+"\n".join(
    f"void register_card_{i}(CardRegistry&);" for i in range(1010,1016)),1)
s=s.replace(registration,registration+"\n"+"\n".join(
    f"    register_card_{i}(registry);" for i in range(1010,1016)),1)
init.write_text(s)
print("RADIANCE_BATCH8_TRANCHE1_APPLIED: engine IDs 1010..1015")
