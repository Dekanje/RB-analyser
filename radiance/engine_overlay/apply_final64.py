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


# Bloodscent Swarm reduces cost only for battlefield CONQUESTS, not holds.
# Keep that fact independent of the existing "scored (conquer or hold)" set.
state_path=engine/"src/core/game_state.h"
gs=state_path.read_text()
set_decl="    std::set<BattlefieldId> battlefields_scored_this_turn;"
assert gs.count(set_decl)==1
gs=gs.replace(set_decl,set_decl+"\n    std::set<BattlefieldId> battlefields_conquered_this_turn;",1)
reset="        battlefields_scored_this_turn.clear();"
assert gs.count(reset)==1
gs=gs.replace(reset,reset+"\n        battlefields_conquered_this_turn.clear();",1)
state_path.write_text(gs)
tr=trigger.read_text()
score_decl="""void TriggerManager::onScore(const ScoreEvent& e) {
    const TriggerEventScope event_scope(state_.chain);"""
assert tr.count(score_decl)==1
tr=tr.replace(score_decl,score_decl+"""
    if(e.method==ScoreMethod::Conquer)
        state_.player(e.player).battlefields_conquered_this_turn.insert(e.battlefield);""",1)
trigger.write_text(tr)


# Seraphic Wyvern channel-replacement: original runes keep their printed
# ready/exhausted instruction; each extra rune enters exhausted.
executor_path=engine/"src/engine/effect_executor.cpp"
exe=executor_path.read_text()
start=exe.index("void EffectExecutor::channelRunes(")
end=exe.index("\n}\n",start)+2
body=exe[start:end]
head="""void EffectExecutor::channelRunes(PlayerId player, int count, bool enter_exhausted) {
    RIFT_TRACE"""
replacement="""void EffectExecutor::channelRunes(PlayerId player, int count, bool enter_exhausted) {
    const int original_count=count;
    if(count>0) {
        for(const auto& [id,obj]:state_.objects.onBoard())
            if(obj.card_def_id==CardDefId{1101} && obj.isUnit() &&
               obj.controller==player && obj.location.has_value())
                ++count;
    }
    RIFT_TRACE"""
assert body.count(head)==1, "Wyvern channel entry anchor changed"
body=body.replace(head,replacement,1)
e="        rune.is_exhausted = enter_exhausted;"
assert body.count(e)==1
body=body.replace(e,"        const bool rune_enters_exhausted=enter_exhausted||i>=original_count;\n"+
                     "        rune.is_exhausted = rune_enters_exhausted;",1)
e='                         (enter_exhausted ? ", exhausted" : ", ready") + ")");'
assert body.count(e)==1
body=body.replace(e,'                         (rune_enters_exhausted ? ", exhausted" : ", ready") + ")");',1)
exe=exe[:start]+body+exe[end:]
executor_path.write_text(exe)


# Dynamic facedown capacity (Bushwhack Trap, Bandle Tree):
# rebuild on every aura pass so lost or bounced traps stop granting a slot.
gamefile=engine/"src/engine/game_engine.cpp"
gg=gamefile.read_text()
cap_anchor="        bf.multi_move_tax[0] = bf.multi_move_tax[1] = 0;"
assert gg.count(cap_anchor)==1, "Final64 dynamic facedown-capacity anchor changed"
gg=gg.replace(cap_anchor,
    "        bf.facedown_max_occupancy = 1; // Radiance Bushwhack Trap, rebuilt by auras\n"+
    cap_anchor,1)
gamefile.write_text(gg)

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
