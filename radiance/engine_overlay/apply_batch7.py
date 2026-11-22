#!/usr/bin/env python3
"""Batch 7 overlay after validated AlphaRune Waves 1–5 and Batch 6.

This is a real source overlay, not a registry-only placeholder. Full regression
needs an explicit measured seed-1 snapshot for the new card pool at final gate.
"""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"

for src,dst in [
    ("cards/units/1001_radiance_batch7_supported_effects.cpp",
     "src/cards/units/1001_radiance_batch7_supported_effects.cpp"),
    ("tests/cards/test_radiance_batch7.cpp",
     "tests/cards/test_radiance_batch7.cpp"),
]:
    target=engine/dst
    if target.exists():
        raise SystemExit("Batch 7 source collision: "+str(target))
    shutil.copyfile(source/src,target)

init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
declaration="void register_card_1000(CardRegistry&);"
registration="    register_card_1000(registry);"
assert s.count(declaration)==1 and s.count(registration)==1, "Batch 6 cards_init anchors changed"
s=s.replace(declaration,declaration+"\n"+"\n".join(
    f"void register_card_{i}(CardRegistry&);" for i in range(1001,1010)),1)
s=s.replace(registration,registration+"\n"+"\n".join(
    f"    register_card_{i}(registry);" for i in range(1001,1010)),1)
init.write_text(s)

# Batch 6 CI must supply the exact 1000-card seed-1 fingerprint before final
# regression; similarly Batch 7's 1010-card value is measured, never guessed.
print("RADIANCE_BATCH7_APPLIED: nine new C++ effects, IDs 1001..1009")
