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
 ("cards/units/1016_radiance_batch8_tranche2a.cpp","src/cards/units/1016_radiance_batch8_tranche2a.cpp"),
 ("cards/units/1019_radiance_batch8_tranche2b.cpp","src/cards/units/1019_radiance_batch8_tranche2b.cpp"),
 ("cards/units/1022_radiance_batch8_tranche2c.cpp","src/cards/units/1022_radiance_batch8_tranche2c.cpp"),
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
    f"void register_card_{i}(CardRegistry&);" for i in range(1010,1025)),1)
s=s.replace(registration,registration+"\n"+"\n".join(
    f"    register_card_{i}(registry);" for i in range(1010,1025)),1)
init.write_text(s)
# CR 323.6 has an "unless an effect would indicate otherwise" exception:
# [Deploy] is precisely the printed permission for an unattached Gear to
# remain at a battlefield. Ordinary unattached Gear still recalls to base.
game=engine/"src/engine/game_engine.cpp"
g=game.read_text()
before="if (obj.isGear() && !obj.attached_to.has_value() && obj.isAtBattlefield())"
after="if (obj.isGear() && !obj.attached_to.has_value() && obj.isAtBattlefield() &&\n            !obj.hasKeyword(Keyword::Deploy))"
assert g.count(before)==1, "Batch 8 Deploy cleanup anchor changed"
game.write_text(g.replace(before,after,1))

# Dreamroot observes a winning combat at its own Deploy battlefield.
tpath=engine/"src/engine/trigger_manager.cpp"
t=tpath.read_text()
before="    // Snapshot the surviving winner-side units at this BF. We snapshot first"
after="""    // Deployed gear watching its owner's combat win at this battlefield.
    std::vector<GameObjectId> winning_deploy_gear;
    for (auto& [id, gear] : state_.objects.onBoard()) {
        if (!gear.isGear() || !gear.isAtBattlefield() ||
            !gear.hasKeyword(Keyword::Deploy) || gear.controller != winner ||
            !gear.battlefieldId() || *gear.battlefieldId() != e.battlefield)
            continue;
        if (cardFiresOn(card_registry_, gear.card_def_id, TriggerType::WhenIWinCombat))
            winning_deploy_gear.push_back(id);
    }
    for (auto id : winning_deploy_gear)
        fireTrigger(id, winner, 0, TriggerType::WhenIWinCombat);

""" + before
assert t.count(before)==1, "CombatResult hook changed"
tpath.write_text(t.replace(before,after,1))

# The seed-1 deck fingerprint must be measured for this registry size.
# Full CI seed-1 probe run 45061034720 measured the hash for the
# 1,024-definition registry. Keep every earlier pool-size snapshot intact.
decktest=engine/"tests/test_deck_fuzz.cpp"
f=decktest.read_text()
before="""    constexpr uint64_t kRadiance1009DeckOfSeedOne = 16217678500199303007ull;
    const uint64_t expected = registry_->size()==1009 ? kRadiance1009DeckOfSeedOne"""
after="""    constexpr uint64_t kRadiance1009DeckOfSeedOne = 16217678500199303007ull;
    constexpr uint64_t kRadiance1024DeckOfSeedOne = 7489794038716556845ull;
    const uint64_t expected = registry_->size()==1024 ? kRadiance1024DeckOfSeedOne
                             : registry_->size()==1009 ? kRadiance1009DeckOfSeedOne"""
assert f.count(before)==1, "DeckFuzz seed-1 anchor changed after Batch 7"
decktest.write_text(f.replace(before,after,1))

print("RADIANCE_BATCH8_APPLIED: 15 cards, IDs 1010-1024")
