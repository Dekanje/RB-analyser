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
    "cards/units/radiance_final64_helpers.h",
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


# Final64 "When I become exhausted" and "When another friendly unit becomes
# exhausted" events, with real reactable chain entries.
effects=engine/"src/effects/effect_types.h"
t=effects.read_text()
anchor_enum="    WhenEnemyMightReducedHere, // Radiance Ahri; emitted only for real enemy Might reduction"
assert t.count(anchor_enum)==1, "Final64 exhaust enum anchor changed"
t=t.replace(anchor_enum,anchor_enum+"""
    WhenIBecomeExhausted, // Radiance Riven, Rostrum, Oracle, Seraphine
    WhenAnotherFriendlyUnitBecomesExhausted, // Radiance Riven Deserter""",1)
effects.write_text(t)

trigger=engine/"src/engine/trigger_manager.cpp"
t=trigger.read_text()
anchor_trigger="""void TriggerManager::onObjectStateChanged(const ObjectStateChangedEvent& e) {
    const TriggerEventScope event_scope(state_.chain);
    if (!state_.objectExists(e.object)) return;
    const PlayerId controller = state_.getObject(e.object).controller;"""
assert t.count(anchor_trigger)==1, "Final64 exhausted event anchor changed"
replace_trigger=anchor_trigger+"""
    if (e.what_changed == "exhausted") {
        const auto& exhausted=state_.getObject(e.object);
        if (exhausted.card_def_id!=kInvalidId &&
            cardFiresOn(card_registry_,exhausted.card_def_id,TriggerType::WhenIBecomeExhausted))
            fireTrigger(e.object,controller,0,TriggerType::WhenIBecomeExhausted,
                        e.object);
        std::vector<GameObjectId> other_watchers;
        for (const auto& [id,obj]:state_.objects.onBoard()) {
            if (id==e.object || obj.controller!=controller || !obj.location ||
                obj.card_def_id==kInvalidId)continue;
            if(cardFiresOn(card_registry_,obj.card_def_id,
                           TriggerType::WhenAnotherFriendlyUnitBecomesExhausted))
                other_watchers.push_back(id);
        }
        for(auto id:other_watchers)
            fireTrigger(id,controller,0,TriggerType::WhenAnotherFriendlyUnitBecomesExhausted,
                        e.object);
    }
"""
trigger.write_text(t.replace(anchor_trigger,replace_trigger,1))

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
