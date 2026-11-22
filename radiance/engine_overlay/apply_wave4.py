#!/usr/bin/env python3
"""Apply Wave 4 after Wave 1, 2 and 3, against pinned AlphaRune only."""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"

for src,dst in [
    ("cards/units/0996_radiance_industrious_mechsmith.cpp",
     "src/cards/units/0996_radiance_industrious_mechsmith.cpp"),
    ("cards/units/0997_radiance_bilgewater_tracker.cpp",
     "src/cards/units/0997_radiance_bilgewater_tracker.cpp"),
    ("tests/cards/test_radiance_wave4.cpp",
     "tests/cards/test_radiance_wave4.cpp"),
]:
    target=engine/dst
    if target.exists():
        raise SystemExit("Wave 4 path collision: "+str(target))
    shutil.copyfile(source/src,target)

init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
declaration="void register_card_995(CardRegistry&);"
registration="    register_card_995(registry);"
assert s.count(declaration)==1 and s.count(registration)==1, "Wave 3 registry anchors changed"
s=s.replace(declaration,declaration+"\nvoid register_card_996(CardRegistry&);\nvoid register_card_997(CardRegistry&);",1)
s=s.replace(registration,registration+"\n    register_card_996(registry);\n    register_card_997(registry);",1)
init.write_text(s)

# Keep the death-batch source scanner exact: Bilgewater Tracker adds one
# legitimately batched lethal-helper call. No test exclusion or weak bound.
perf=engine/"tests/test_review_fix_perf_engine.cpp"
old="    EXPECT_EQ(helper, 30);   // 28 verified 988-card sites + Supernova and Avalanche (Wave 1)"
new="    EXPECT_EQ(helper, 31);   // 30 Wave 1–3 sites + Bilgewater Tracker (Wave 4)"
p=perf.read_text()
assert p.count(old)==1, "Unexpected Wave 3 death-batch scan anchor"
perf.write_text(p.replace(old,new,1))

# Explicit 997-card seed-1 fingerprint measured from real GitHub Actions run
# 45003763684, DeckFuzz.DeckOfSeedOneIsPinned. Keep all earlier pool hashes.
decktest=engine/"tests/test_deck_fuzz.cpp"
p=decktest.read_text()
old="""    constexpr uint64_t kRadiance995DeckOfSeedOne = 6757871164987904898ull;
    const uint64_t expected = registry_->size()==995 ? kRadiance995DeckOfSeedOne"""
new="""    constexpr uint64_t kRadiance995DeckOfSeedOne = 6757871164987904898ull;
    constexpr uint64_t kRadiance997DeckOfSeedOne = 17916410112993108747ull;
    const uint64_t expected = registry_->size()==997 ? kRadiance997DeckOfSeedOne
                             : registry_->size()==995 ? kRadiance995DeckOfSeedOne"""
assert p.count(old)==1, "Unexpected Wave 3 seed fingerprint anchor"
decktest.write_text(p.replace(old,new,1))

# A new card pool changes random-deck generation, including seed 1.
# DO NOT suppress or change the existing pinned fingerprints. The latest
# 997-card hash must be measured in the compiled CI test and added explicitly
# in a follow-on patch; until then, the regression is EXPECTED TO FAIL CLOSED.
print("WAVE4_APPLIED: RAD-049 and RAD-003, engine IDs 996-997, engine-path tests")
