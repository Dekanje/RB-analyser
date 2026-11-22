#!/usr/bin/env python3
"""One final Radiance batch: apply all 64 missing base identities after accepted Batch 10.

Registration alone is never equivalent to rules/mechanics acceptance.
"""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
overlay=root/"radiance/engine_overlay/source"
source_files=[
    "cards/units/1068_radiance_final64_a.cpp",
    "cards/units/1084_radiance_final64_b.cpp",
    "cards/units/1100_radiance_final64_c.cpp",
    "cards/units/1116_radiance_final64_d.cpp",
    "tests/cards/test_radiance_final64.cpp",
]
for source in source_files:
    target=engine/"src"/source if not source.startswith("tests/") else engine/source
    if target.exists():raise SystemExit(f"Final64 overlay collision: {target}")
    target.parent.mkdir(parents=True,exist_ok=True)
    shutil.copyfile(overlay/source,target)

init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
last_decl="void register_card_1067(CardRegistry&);"
last_call="    register_card_1067(registry);"
assert s.count(last_decl)==1 and s.count(last_call)==1, "Accepted Batch10 registration anchor changed"
s=s.replace(last_decl,last_decl+"\n"+"\n".join(
    f"void register_card_{i}(CardRegistry&);" for i in range(1068,1132)),1)
s=s.replace(last_call,last_call+"\n"+"\n".join(
    f"    register_card_{i}(registry);" for i in range(1068,1132)),1)
init.write_text(s)
print("RADIANCE_FINAL64_OVERLAY_APPLIED: engine IDs 1068..1131 (64 distinct identities)")
