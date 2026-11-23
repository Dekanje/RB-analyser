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
    WhenAnotherFriendlyUnitBecomesExhausted, // Radiance Riven Deserter
    WhenFriendlyGearDiesAtBattlefield, // Radiance Battlefield Armorer""",1)
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


# Battlefield Armorer: a friendly gear dying at a battlefield must be a
# reactable trigger with the dead gear as its subject, not a test-only callback.
# TriggerManager already receives LeftBoardEvent after the gear was sent to
# Trash; use that event's last-known location and controller.
tr=trigger.read_text()
armorer_anchor="    if (!e.was_killed || e.card_type != CardType::Gear) return;"
assert tr.count(armorer_anchor)==1, "Armorer gear death trigger anchor changed"
tr=tr.replace(armorer_anchor,"""
    if(e.was_killed && e.card_type==CardType::Gear &&
       std::holds_alternative<BattlefieldLocation>(e.was_at) &&
       e.controller!=PlayerId::None) {
       const auto &dead=state_.getObject(e.object);
       // Tokens do not enter Trash (CR 183.1); no token can be recovered.
       if(!dead.isToken() && dead.zone==ZoneType::Trash) {
           std::vector<GameObjectId> watchers;
           for(const auto& [id,obj]:state_.objects.onBoard()) {
               if(id==e.object || !obj.isUnit() || !obj.location ||
                  obj.controller!=e.controller || obj.card_def_id==kInvalidId)
                   continue;
               if(cardFiresOn(card_registry_,obj.card_def_id,
                              TriggerType::WhenFriendlyGearDiesAtBattlefield))
                   watchers.push_back(id);
           }
           for(auto wid:watchers)
               fireTrigger(wid,e.controller,0,
                           TriggerType::WhenFriendlyGearDiesAtBattlefield,e.object);
       }
    }
""" + armorer_anchor,1)
trigger.write_text(tr)


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


# Real "As you play this" spell choices are made before spell target/cost.
# Pinned engine invokes the hook for permanents but omitted hand-played
# spells. Four Radiance Show Off spells require this before they resolve.
gg=gamefile.read_text()
spell_start=gg.index("void GameEngine::executePlaySpell(")
spell_end=gg.index("\nvoid GameEngine::finishPlaySpell(",spell_start)
spell_body=gg[spell_start:spell_end]
needle="    forgetPlayPayments(intent.player, intent.card);   // a new play: nothing is paid yet"
assert spell_body.count(needle)==1, "Spell as-you-play hook anchor changed"
spell_body=spell_body.replace(needle,needle+"""
    // CR 355.1: as-you-play choices of spells also precede payment.
    effect_executor_->makeAsYouPlayChoices(intent.player, intent.card);""",1)
gamefile.write_text(gg[:spell_start]+spell_body+gg[spell_end:])

# Pin the measured seed-1 deck fingerprint for the expanded 1,123-definition
# registry. This value came from the uncompromised full-regression test
# failure in run 45096185998; previous pool-size fingerprints remain active.
decktest=engine/"tests/test_deck_fuzz.cpp"
deck_source=decktest.read_text()
old_hash="""    constexpr uint64_t kRadiance1059DeckOfSeedOne = 11226295876980254031ull;
    const uint64_t expected = registry_->size()==1059 ? kRadiance1059DeckOfSeedOne"""
new_hash="""    constexpr uint64_t kRadiance1059DeckOfSeedOne = 11226295876980254031ull;
    constexpr uint64_t kRadiance1123DeckOfSeedOne = 2700713930748140182ull;
    const uint64_t expected = registry_->size()==1123 ? kRadiance1123DeckOfSeedOne
                             : registry_->size()==1059 ? kRadiance1059DeckOfSeedOne"""
assert deck_source.count(old_hash)==1, "Final64 seed pin anchor changed"
decktest.write_text(deck_source.replace(old_hash,new_hash,1))

# AlphaRune's strong-ID audit intentionally requires every integer-slot
# GameObjectId reader to be paired with a writer. Dockside Lock-Up stores
# __dockside_banished_card = int(unit.raw()) (plain GameObjectId encoding)
# and reads it through GameObjectId::fromRaw; a missing key means "none".
# Its hold trigger verifies objectExists and Banishment before using it.
audit=engine/"tests/test_strong_ids.cpp"
audited=audit.read_text()
audit_anchor='        {"src/cards/units/0643_keeper_of_masks.cpp", 1},'
audit_entry='        {"src/cards/units/1116_radiance_final64_d.cpp", 1},  // Dockside Lock-Up: __dockside_banished_card stores GameObjectId::raw; absence is none'
assert audited.count(audit_anchor)==1, "StrongIds audit entry anchor changed"
assert audit_entry not in audited, "StrongIds Dockside reader audited twice"
audit.write_text(audited.replace(audit_anchor,audit_anchor+"\n"+audit_entry,1))

# RAD-019 Firebrand Raider stops UNIT readiness (not rune/gear/legend
# readiness) during the turn player's Awaken Phase while it remains in play.
# All other units enter ready through its cross-player aura in the card class.
# Keep this as a pin-anchored upstream engine patch, not a global rule change.
engine_cpp=engine/"src/engine/game_engine.cpp"
engine_source=engine_cpp.read_text()
awaken_begin=engine_source.index("void GameEngine::awakenPhase()")
awaken_end=engine_source.index("void GameEngine::beginningStep()",awaken_begin)
awaken_source=engine_source[awaken_begin:awaken_end]
awaken_head="""    auto player = state_.turn.turn_player;
    {
        const SimultaneousTriggers together(state_.chain);"""
awaken_replacement="""    auto player = state_.turn.turn_player;
    bool firebrand_prevents_unit_ready = false;
    for (const auto& [firebrand_id, firebrand] : state_.objects.onBoard()) {
        if (firebrand.card_def_id == CardDefId{1075} &&
            firebrand.isUnit() && firebrand.location.has_value()) {
            firebrand_prevents_unit_ready = true;
            break;
        }
    }
    {
        const SimultaneousTriggers together(state_.chain);"""
assert awaken_source.count(awaken_head)==1, "AwakenPhase turn-player anchor changed"
awaken_source=awaken_source.replace(awaken_head,awaken_replacement,1)
ready_anchor="""            if (obj.controller == player && obj.is_exhausted && obj.location.has_value()) {
                const Card* card = obj.card_def_id != kInvalidId"""
ready_replacement="""            if (obj.controller == player && obj.is_exhausted && obj.location.has_value()) {
                if (firebrand_prevents_unit_ready && obj.isUnit()) continue;
                const Card* card = obj.card_def_id != kInvalidId"""
assert awaken_source.count(ready_anchor)==1, "AwakenPhase unit-ready gate anchor changed"
awaken_source=awaken_source.replace(ready_anchor,ready_replacement,1)
engine_cpp.write_text(engine_source[:awaken_begin]+awaken_source+engine_source[awaken_end:])

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

# RAD-063 Kai'Sa, Rebel: a spell of the player's gains [Reaction] only
# while the player's Kai'Sa is actually at an ACTIVE showdown battlefield.
# Do not permanently mutate the spell's printed keyword set (hand, trash,
# chain) or use an aura snapshot from before the showdown opened.
game_engine_path=engine/"src/engine/game_engine.cpp"
source=game_engine_path.read_text()
helper_anchor="void GameEngine::generateSpellActions("
helper= """static bool radianceRebelGrantsSpellReaction(const GameState& state, PlayerId player) {
    for (const auto& bf : state.battlefields) {
        if (!bf.showdown_in_progress) continue;
        for (const auto& [id, obj] : state.objects.onBoard()) {
            if (obj.card_def_id != CardDefId{1087} || obj.controller != player ||
                !obj.isUnit() || !obj.isAtBattlefield()) continue;
            if (obj.battlefieldId() == bf.id) return true;
        }
    }
    return false;
}

"""
assert source.count(helper_anchor)==1,"RAD-063 grant anchor changed"
source=source.replace(helper_anchor,helper+helper_anchor,1)
reaction_anchor="        bool has_reaction = card.keywords.has(Keyword::Reaction);"
assert source.count(reaction_anchor)==2,"RAD-063 hand/trash timing anchors changed"
source=source.replace(reaction_anchor,
    "        bool has_reaction = card.keywords.has(Keyword::Reaction) ||\n"
    "            radianceRebelGrantsSpellReaction(state_, player);")
game_engine_path.write_text(source)


# RAD-120: a 7+-Energy card just FINISHED being played (a spell only on
# resolution, as AlphaRune's native WhenYouPlayACard event semantics require).
# Unlike [Flow], this queues a specific optional trigger for the Restorationist
# in its owner's Trash; it does not grant permission for the rest of the turn.
tm_path=engine/"src/engine/trigger_manager.cpp"
tm=tm_path.read_text()
trash_hook="""    // Radiance Restorationist: the card itself can trigger from Trash.
    // Printed Energy cost, NOT the actual amount spent, is the criterion.
    if (state_.objectExists(played_card)) {
        const auto& played=state_.getObject(played_card);
        const Card* played_class=played.card_def_id!=kInvalidId
            ?card_registry_.get(played.card_def_id):nullptr;
        if (played_class && played_class->def().energy_cost>=7) {
            std::vector<GameObjectId> from_trash;
            for(auto id:state_.player(playing_player).trash) {
                if(state_.objectExists(id) &&
                   state_.getObject(id).card_def_id==CardDefId{1115} &&
                   state_.getObject(id).zone==ZoneType::Trash &&
                   state_.getObject(id).owner==playing_player)
                    from_trash.push_back(id);
            }
            for(auto id:from_trash)
                fireTrigger(id,playing_player,0,TriggerType::WhenYouPlayACard,
                            played_card);
        }
    }
"""
first_anchor="    // [Vision] (CR 817):"
assert tm.count(first_anchor)==1,"Restorationist permanent event anchor moved"
tm=tm.replace(first_anchor,
    "    { const auto played_card=e.object; const auto playing_player=e.player;\n"
    +trash_hook+"    }\n\n"+first_anchor,1)
spell_anchor="    // The same play, completed: if it was not from a hand (finding G12)."
assert tm.count(spell_anchor)==1,"Restorationist spell resolved event anchor moved"
tm=tm.replace(spell_anchor,
    "    { const auto played_card=e.spell; const auto playing_player=e.controller;\n"
    +trash_hook+"    }\n\n"+spell_anchor,1)
tm_path.write_text(tm)

print("RADIANCE_FINAL64_OVERLAY_APPLIED: engine IDs 1068..1131 (64 distinct identities)")
