#!/usr/bin/env python3
"""Apply Wave 2 strictly after the validated Wave 1 overlay and regression fix."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"
for src,dst in [
 ("cards/spells/0994_radiance_brawl.cpp","src/cards/spells/0994_radiance_brawl.cpp"),
 ("tests/cards/test_radiance_wave2.cpp","tests/cards/test_radiance_wave2.cpp")
]:
 target=engine/dst
 if target.exists(): raise SystemExit("Wave 2 collision: "+str(target))
 shutil.copyfile(source/src,target)
init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
a="void register_card_993(CardRegistry&);"
b="    register_card_993(registry);"
assert s.count(a)==1 and s.count(b)==1,"Wave 1 registration anchors changed"
s=s.replace(a,a+"\nvoid register_card_994(CardRegistry&);",1)
s=s.replace(b,b+"\n    register_card_994(registry);",1)
init.write_text(s)
# Preserve 988/993 pinned deck fingerprints and explicitly pin the 994-card
# deterministic seed-1 deck fingerprint observed in the real compiled CI run.
# This is a catalog-dependent snapshot, not a rules change or relaxed test.
decktest=engine/"tests/test_deck_fuzz.cpp"
decksource=decktest.read_text()
old="""    constexpr uint64_t kRadiance993DeckOfSeedOne = 5259447031096685743ull;
    const uint64_t expected = registry_->size()==993 ? kRadiance993DeckOfSeedOne
                             : registry_->size()==988 ? kRadiance988DeckOfSeedOne
                             : kDeckOfSeedOne;"""
new="""    constexpr uint64_t kRadiance993DeckOfSeedOne = 5259447031096685743ull;
    constexpr uint64_t kRadiance994DeckOfSeedOne = 3093099139649196331ull;
    const uint64_t expected = registry_->size()==994 ? kRadiance994DeckOfSeedOne
                             : registry_->size()==993 ? kRadiance993DeckOfSeedOne
                             : registry_->size()==988 ? kRadiance988DeckOfSeedOne
                             : kDeckOfSeedOne;"""
assert decksource.count(old)==1,"Unexpected Wave 1 deck fingerprint anchor"
decktest.write_text(decksource.replace(old,new,1))
print("WAVE2_APPLIED: RAD-004 Brawl, engine ID 994, deterministic tests")
