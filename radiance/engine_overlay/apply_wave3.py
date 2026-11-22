#!/usr/bin/env python3
"""Apply Wave 3 after validated Wave 1 and Wave 2; no main-branch mutation."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"
for src,dst in [
 ("cards/units/0995_radiance_war_scout.cpp","src/cards/units/0995_radiance_war_scout.cpp"),
 ("tests/cards/test_radiance_wave3.cpp","tests/cards/test_radiance_wave3.cpp")
]:
 target=engine/dst
 if target.exists(): raise SystemExit("Wave 3 collision: "+str(target))
 shutil.copyfile(source/src,target)
init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
a="void register_card_994(CardRegistry&);"
b="    register_card_994(registry);"
assert s.count(a)==1 and s.count(b)==1,"Wave 2 registration anchors changed"
s=s.replace(a,a+"\nvoid register_card_995(CardRegistry&);",1)
s=s.replace(b,b+"\n    register_card_995(registry);",1)
init.write_text(s)
# Explicit compiled-pool seed-1 snapshot for the 995-card registry. Keep all
# previous 988/993/994 assertions unchanged; do not relax reproducibility.
decktest=engine/"tests/test_deck_fuzz.cpp"
decksource=decktest.read_text()
old="""    constexpr uint64_t kRadiance994DeckOfSeedOne = 3093099139649196331ull;
    const uint64_t expected = registry_->size()==994 ? kRadiance994DeckOfSeedOne"""
new="""    constexpr uint64_t kRadiance994DeckOfSeedOne = 3093099139649196331ull;
    constexpr uint64_t kRadiance995DeckOfSeedOne = 6757871164987904898ull;
    const uint64_t expected = registry_->size()==995 ? kRadiance995DeckOfSeedOne
                             : registry_->size()==994 ? kRadiance994DeckOfSeedOne"""
assert decksource.count(old)==1,"Unexpected Wave 2 seed fingerprint anchor"
decktest.write_text(decksource.replace(old,new,1))
print("WAVE3_APPLIED: RAD-008 War Scout, engine ID 995, deterministic tests")
