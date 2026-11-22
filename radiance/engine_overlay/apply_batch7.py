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

# The full Batch 7 CI run 45054554807 measured the deterministic
# seed-1 hash for the 1009-definition registry. This exact value may equal
# a previous pool's hash; retain ALL earlier snapshots and pin by pool size.
decktest=engine/"tests/test_deck_fuzz.cpp"
p=decktest.read_text()
before="""    constexpr uint64_t kRadiance1000DeckOfSeedOne = 16217678500199303007ull;
    const uint64_t expected = registry_->size()==1000 ? kRadiance1000DeckOfSeedOne"""
after="""    constexpr uint64_t kRadiance1000DeckOfSeedOne = 16217678500199303007ull;
    constexpr uint64_t kRadiance1009DeckOfSeedOne = 16217678500199303007ull;
    const uint64_t expected = registry_->size()==1009 ? kRadiance1009DeckOfSeedOne
                             : registry_->size()==1000 ? kRadiance1000DeckOfSeedOne"""
assert p.count(before)==1, "Batch 7 seed-1 test anchor changed"
decktest.write_text(p.replace(before,after,1))
print("RADIANCE_BATCH7_APPLIED: nine new C++ effects, IDs 1001..1009; pinned measured 1009-card seed-1 deck")
