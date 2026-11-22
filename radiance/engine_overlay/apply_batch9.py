#!/usr/bin/env python3
"""Apply Radiance Batch 9 tranche 1 after the accepted Batch 8 overlay.
Three distinct card mechanics, backed by engine-path tests and score hooks.
"""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"
for src,dst in [
    ("cards/units/1025_radiance_batch9_tranche1.cpp",
     "src/cards/units/1025_radiance_batch9_tranche1.cpp"),
    ("tests/cards/test_radiance_batch9.cpp",
     "tests/cards/test_radiance_batch9.cpp"),
]:
    target=engine/dst
    if target.exists():raise SystemExit("Batch9 source collision: "+str(target))
    shutil.copyfile(source/src,target)

init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
declaration="void register_card_1024(CardRegistry&);"
registration="    register_card_1024(registry);"
assert s.count(declaration)==1 and s.count(registration)==1, "Batch8 registration anchor changed"
s=s.replace(declaration,declaration+"\n"+ "\n".join(
    f"void register_card_{i}(CardRegistry&);" for i in range(1025,1028)),1)
s=s.replace(registration,registration+"\n"+ "\n".join(
    f"    register_card_{i}(registry);" for i in range(1025,1028)),1)
init.write_text(s)

# Deploy score behavior: "When you conquer here" watches the battlefield,
# whereas the pinned upstream onScore only dispatches this trigger to the
# battlefield's own card. Extend it to deployed gear at the scored battlefield.
# Also enforce Deploy's printed self-kill when an opponent holds at its BF.
triggers=engine/"src/engine/trigger_manager.cpp"
t=triggers.read_text()
anchor="    // Battlefield triggers\n    for (auto& bf : state_.battlefields) {"
patch="""    // Radiance Deploy gear observes conquers at its own battlefield.
    // On the opposing player's hold, the deployed gear dies (CR 323).
    std::vector<GameObjectId> score_deploy;
    std::vector<GameObjectId> destroy_deploy;
    for (const auto& [gid, gear] : state_.objects.onBoard()) {
        if (!gear.isGear() || !gear.isAtBattlefield() ||
            !gear.hasKeyword(Keyword::Deploy) || !gear.battlefieldId() ||
            *gear.battlefieldId() != e.battlefield) continue;
        if (e.method == ScoreMethod::Conquer && gear.controller == e.player &&
            cardFiresOn(card_registry_, gear.card_def_id,
                        TriggerType::WhenYouConquerHere))
            score_deploy.push_back(gid);
        if (e.method == ScoreMethod::Hold && gear.controller != e.player)
            destroy_deploy.push_back(gid);
    }
    for (const auto gid : score_deploy)
        fireTrigger(gid, e.player, 0, TriggerType::WhenYouConquerHere);
    if (effect_executor_)
        for (const auto gid : destroy_deploy)
            if (state_.objectExists(gid) && state_.getObject(gid).location)
                effect_executor_->killObject(gid);

"""
assert t.count(anchor)==1, "Batch9 Deploy score trigger anchor changed"
triggers.write_text(t.replace(anchor,patch+anchor,1))
print("RADIANCE_BATCH9_TRANCHE1_APPLIED: IDs 1025..1027; Deploy score integration")
