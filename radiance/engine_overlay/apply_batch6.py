#!/usr/bin/env python3
"""Overlay for the mechanics-based Radiance Batch 6.

Apply after the pinned Waves 1–4 overlays. Intentionally no full-regression
fingerprint adjustment here: any new card pool must first be measured in a
real compiled engine, preserving all previously pinned seed snapshots.
"""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"
files=[
    ("cards/units/0998_radiance_antagonistic_apparatus.cpp",
     "src/cards/units/0998_radiance_antagonistic_apparatus.cpp"),
    ("cards/units/0999_radiance_hunting_dog.cpp",
     "src/cards/units/0999_radiance_hunting_dog.cpp"),
    ("cards/units/1000_radiance_stalwart_goatherd.cpp",
     "src/cards/units/1000_radiance_stalwart_goatherd.cpp"),
    ("tests/cards/test_radiance_batch6.cpp",
     "tests/cards/test_radiance_batch6.cpp"),
]
for src,dest in files:
    target=engine/dest
    if target.exists():
        raise SystemExit("Batch6 overlay collision: "+str(target))
    shutil.copyfile(source/src,target)
init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
declaration="void register_card_997(CardRegistry&);"
call="    register_card_997(registry);"
assert s.count(declaration)==1 and s.count(call)==1, "Wave 4 anchors changed"
newdeclaration="\n".join(f"void register_card_{i}(CardRegistry&);" for i in range(998,1001))
newcalls="\n".join(f"    register_card_{i}(registry);" for i in range(998,1001))
s=s.replace(declaration,declaration+"\n"+newdeclaration,1)
s=s.replace(call,call+"\n"+newcalls,1)
init.write_text(s)
# The full Batch 6 CI run 45040092801 measured the 1000-card
# deterministic seed-1 deck hash. Preserve earlier pool-dependent snapshots.
decktest=engine/"tests/test_deck_fuzz.cpp"
p=decktest.read_text()
before="""    constexpr uint64_t kRadiance997DeckOfSeedOne = 17916410112993108747ull;
    const uint64_t expected = registry_->size()==997 ? kRadiance997DeckOfSeedOne"""
after="""    constexpr uint64_t kRadiance997DeckOfSeedOne = 17916410112993108747ull;
    constexpr uint64_t kRadiance1000DeckOfSeedOne = 16217678500199303007ull;
    const uint64_t expected = registry_->size()==1000 ? kRadiance1000DeckOfSeedOne
                             : registry_->size()==997 ? kRadiance997DeckOfSeedOne"""
assert p.count(before)==1, "Batch 6 deterministic deck test anchor changed"
decktest.write_text(p.replace(before,after,1))
print("RADIANCE_BATCH6_APPLIED: 998 RAD-009; 999 RAD-119; 1000 RAD-083")
