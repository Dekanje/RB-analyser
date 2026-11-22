#!/usr/bin/env python3
"""Apply Batch 10's 20 unique source identities after the accepted Batch 9 overlay.

This registers cards for incremental functional verification. Registry acceptance
must never be presented as certification of all printed mechanics.
"""
from pathlib import Path
import shutil

root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"
for src,dst in [
    ("cards/units/1048_radiance_batch10_tranche_a.cpp",
     "src/cards/units/1048_radiance_batch10_tranche_a.cpp"),
    ("cards/units/1058_radiance_batch10_tranche_b.cpp",
     "src/cards/units/1058_radiance_batch10_tranche_b.cpp"),
    ("tests/cards/test_radiance_batch10.cpp",
     "tests/cards/test_radiance_batch10.cpp"),
]:
    target=engine/dst
    if target.exists():raise SystemExit("Batch 10 source collision: "+str(target))
    shutil.copyfile(source/src,target)

# RAD-070 Hold 'Em needs the exact history of unit/gear plays TO A BATTLEFIELD,
# not a blanket "card played" flag. Install a turn-reset flag and the real
# CardPlayedEvent updater so base plays never grant the discount.
state_file=engine/"src/core/game_state.h"
game=state_file.read_text()
decl="    bool played_nontoken_gear_this_turn = false;"
reset="        played_nontoken_gear_this_turn = false;"
assert game.count(decl)==1 and game.count(reset)==1, "Batch 10 play-tracking anchors changed"
game=game.replace(decl,decl+"\n    bool played_unit_or_gear_to_battlefield_this_turn = false;",1)
game=game.replace(reset,reset+"\n        played_unit_or_gear_to_battlefield_this_turn = false;",1)
# A gear that was killed (but not bounced/recycled) satisfies RAD-005.
gear_decl="    bool unit_died_this_turn = false;"
gear_reset="        unit_died_this_turn = false;"
assert game.count(gear_decl)==1 and game.count(gear_reset)==1, "Gear-death flag anchor changed"
game=game.replace(gear_decl,gear_decl+"\n    bool gear_died_this_turn = false;",1)
game=game.replace(gear_reset,gear_reset+"\n        gear_died_this_turn = false;",1)
state_file.write_text(game)

trigger=engine/"src/engine/trigger_manager.cpp"
tr=trigger.read_text()
event_anchor="""        auto& pps = state_.player(e.player);
        if (e.card_type == CardType::Spell)"""
event_replace="""        auto& pps = state_.player(e.player);
        if ((e.card_type == CardType::Unit || e.card_type == CardType::Gear)
            && obj.isAtBattlefield())
            pps.played_unit_or_gear_to_battlefield_this_turn = true;
        if (e.card_type == CardType::Spell)"""
assert tr.count(event_anchor)==1, "Batch 10 CardPlayedEvent anchor changed"
tr=tr.replace(event_anchor,event_replace,1)
left_anchor="""void TriggerManager::onLeftBoard(const LeftBoardEvent& e) {
    const TriggerEventScope event_scope(state_.chain);"""
left_replace="""void TriggerManager::onLeftBoard(const LeftBoardEvent& e) {
    const TriggerEventScope event_scope(state_.chain);
    if (e.card_type == CardType::Gear && e.was_killed &&
        e.controller != PlayerId::None)
        state_.player(e.controller).gear_died_this_turn = true;"""
assert tr.count(left_anchor)==1, "Gear death event anchor changed"
trigger.write_text(tr.replace(left_anchor,left_replace,1))

# Ahri, Confident (RAD-038): a real, respondable Might-reduction trigger.
# Extend the enum with a new value at the END, leaving all existing values stable.
effects=engine/"src/effects/effect_types.h"
eff=effects.read_text()
enum_first=eff.index("enum class TriggerType")
last=eff.index("    WhenAnOpponentHidesACard,",enum_first)
end=eff.index("\n};",last)
assert "WhenEnemyMightReducedHere" not in eff
eff=eff[:end]+"\n    WhenEnemyMightReducedHere, // Radiance Ahri; emitted only for real enemy Might reduction"+eff[end:]
effects.write_text(eff)

# Emit an event only if the target actually lost Might, and record the
# controller whose resolving card/ability caused the reduction.
executor=engine/"src/engine/effect_executor.cpp"
es=executor.read_text()
start=es.index("void EffectExecutor::giveTemporaryMight(")
end=es.index("\nvoid EffectExecutor::giveKeywordThisCombat(",start)
body=es[start:end]
old_line="    obj.temp_might_bonus += amount;"
assert body.count(old_line)==1
body=body.replace(old_line,
    "    const int rad10_previous_might = obj.current_might;\n"+old_line,1)
emit='    events_.emit(ObjectStateChangedEvent{target, "might_changed"});'
assert body.count(emit)==1
body=body.replace(emit,emit+"""
    if (amount < 0 && obj.isUnit() && obj.current_might < rad10_previous_might &&
        state_.chain.resuming.has_value()) {
        const PlayerId reducer = state_.chain.resuming->controller;
        if (reducer != PlayerId::None && reducer != obj.controller) {
            // StateChangeKey only accepts literal char arrays (not const char*).
            if (reducer == PlayerId::Player1)
                events_.emit(ObjectStateChangedEvent{target, "radiance_enemy_might_reduced_p1"});
            else
                events_.emit(ObjectStateChangedEvent{target, "radiance_enemy_might_reduced_p2"});
        }
    }""",1)
es=es[:start]+body+es[end:]
executor.write_text(es)

# Route only the new event to Ahri copies at the SAME battlefield, and put
# their abilities on the chain for a normal response window.
# A token unit or gear is played but is NOT a card: it has TokenCreatedEvent
# rather than CardPlayedEvent. Count battlefield token plays for RAD-070 too.
tr=trigger.read_text()
token_anchor="""void TriggerManager::onTokenCreated(const TokenCreatedEvent& e) {
    const TriggerEventScope event_scope(state_.chain);
    if (!state_.objectExists(e.object) || e.controller == PlayerId::None) return;
    if (!state_.getObject(e.object).location.has_value()) return;"""
token_replacement=token_anchor+"""
    if ((e.card_type == CardType::Unit || e.card_type == CardType::Gear) &&
        state_.getObject(e.object).isAtBattlefield())
        state_.player(e.controller).played_unit_or_gear_to_battlefield_this_turn = true;"""
assert tr.count(token_anchor)==1, "Batch 10 token-play event anchor changed"
trigger.write_text(tr.replace(token_anchor,token_replacement,1))

tr=trigger.read_text()  # preserve the already-inserted gear-death listener
change_anchor='    const PlayerId controller = state_.getObject(e.object).controller;'
onchange_start=tr.index("void TriggerManager::onObjectStateChanged(")
onchange_end=tr.index("\nvoid TriggerManager::",onchange_start+5)
section=tr[onchange_start:onchange_end]
assert section.count(change_anchor)==1
section=section.replace(change_anchor,change_anchor+"""
    if (e.what_changed == "radiance_enemy_might_reduced_p1" ||
        e.what_changed == "radiance_enemy_might_reduced_p2") {
        const PlayerId reducer=e.what_changed=="radiance_enemy_might_reduced_p1"
            ? PlayerId::Player1 : PlayerId::Player2;
        const auto& target=state_.getObject(e.object);
        if (!target.isUnit() || target.controller==reducer || !target.isAtBattlefield())
            return;
        std::vector<GameObjectId> ahri;
        for(const auto& [id,obj]:state_.objects.onBoard())
            if(obj.card_def_id==CardDefId{1050} && obj.controller==reducer &&
               obj.battlefieldId()==target.battlefieldId())
                ahri.push_back(id);
        for(auto id:ahri)
            fireTrigger(id,reducer,0,TriggerType::WhenEnemyMightReducedHere,e.object);
        return;
    }""",1)
tr=tr[:onchange_start]+section+tr[onchange_end:]
trigger.write_text(tr)

init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
decl="void register_card_1047(CardRegistry&);"
reg="    register_card_1047(registry);"
assert s.count(decl)==1 and s.count(reg)==1, "Accepted Batch 9 anchor changed"
s=s.replace(decl,decl+"\n"+"\n".join(
    f"void register_card_{i}(CardRegistry&);" for i in range(1048,1068)),1)
s=s.replace(reg,reg+"\n"+"\n".join(
    f"    register_card_{i}(registry);" for i in range(1048,1068)),1)
init.write_text(s)
print("RADIANCE_BATCH10_OVERLAY_APPLIED: 20 new identities, IDs 1048..1067")
