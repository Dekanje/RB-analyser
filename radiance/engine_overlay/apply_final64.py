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
trash_hook="""    // Radiance high-Energy recursion cards (Restorationist and Forbidden Technique)
    // trigger immediately from Trash when a qualifying play completes.
    // Printed Energy cost, NOT the actual amount spent, is the criterion.
    if (state_.objectExists(played_card)) {
        const auto& played=state_.getObject(played_card);
        const Card* played_class=played.card_def_id!=kInvalidId
            ?card_registry_.get(played.card_def_id):nullptr;
        if (played_class && played_class->def().energy_cost>=7) {
            std::vector<GameObjectId> from_trash;
            for(auto id:state_.player(playing_player).trash) {
                if(state_.objectExists(id) &&
                   (state_.getObject(id).card_def_id==CardDefId{1115} ||
                    state_.getObject(id).card_def_id==CardDefId{1069}) &&
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


# RAD-062 Gravity Field: location-specific 1E + 1 any Power per movement
# action. Ordinary multi-unit standard moves pay ONCE before choosing joins;
# effect-based moves pay according to the controller of the effect.
battlefield_state_path=engine/"src/core/game_state.h"
bfsource=battlefield_state_path.read_text()
bfanchor="    int multi_move_tax[2] = {0, 0};"
assert bfsource.count(bfanchor)==1,"Gravity BF field anchor changed"
bfsource=bfsource.replace(bfanchor,bfanchor+"""
    int gravity_move_tax_energy[2] = {0, 0};
    int gravity_move_tax_power[2] = {0, 0};""",1)
battlefield_state_path.write_text(bfsource)

gamepath=engine/"src/engine/game_engine.cpp"
g=gamepath.read_text()
bf_reset="        bf.multi_move_tax[0] = bf.multi_move_tax[1] = 0;   // Mageseeker Investigator"
assert g.count(bf_reset)==1,"Gravity reset anchor changed"
g=g.replace(bf_reset,bf_reset+"""
        bf.gravity_move_tax_energy[0] = bf.gravity_move_tax_energy[1] = 0;
        bf.gravity_move_tax_power[0] = bf.gravity_move_tax_power[1] = 0;""",1)

move_start="    std::vector<GameObjectId> moving = intent.units_to_move;"
assert g.count(move_start)==1,"Gravity standard movement anchor changed"
g=g.replace(move_start,move_start+"""
    if(auto* to_bf=std::get_if<BattlefieldLocation>(&dest)){
        const auto& bf=getBattlefield(to_bf->id);
        const int index=playerIndex(intent.player);
        const int energy=bf.gravity_move_tax_energy[index];
        const int power=bf.gravity_move_tax_power[index];
        if((energy>0||power>0) &&
           !resource::payIn(state_,events_,intent.player,energy,power,
                            resource::kAnyDomain))return;
    }""",1)
action_anchor="""        for (const auto& dest : standardMoveDestinations(state_.getObject(unit_id), player))
            actions.push_back(Intent::standardMove(player, {unit_id}, dest));"""
assert g.count(action_anchor)==1,"Gravity generated move anchor changed"
action_replacement="""        for (const auto& dest : standardMoveDestinations(state_.getObject(unit_id), player)) {
            if (auto* to_bf=std::get_if<BattlefieldLocation>(&dest)) {
                const auto& bf=getBattlefield(to_bf->id);
                const int idx=playerIndex(player);
                if(!resource::canPayIn(state_,player,bf.gravity_move_tax_energy[idx],
                                       bf.gravity_move_tax_power[idx],
                                       resource::kAnyDomain))continue;
            }
            actions.push_back(Intent::standardMove(player, {unit_id}, dest));
        }"""
g=g.replace(action_anchor,action_replacement,1)
gamepath.write_text(g)

expath=engine/"src/engine/effect_executor.cpp"
ex=expath.read_text()
ex_include='#include "engine/deck_ops.h"'
assert ex.count(ex_include)==1
ex=ex.replace(ex_include,ex_include+'\n#include "engine/resource_payment.h"',1)
move_begin="void EffectExecutor::moveToBattlefield(GameObjectId target, BattlefieldId bf) {"
move_end="void EffectExecutor::stunUnit(GameObjectId target) {"
assert ex.count(move_begin)==1 and ex.count(move_end)==1
beg=ex.index(move_begin);end=ex.index(move_end,beg);move=ex[beg:end]
old_loc="    auto old_loc = obj.location;"
assert move.count(old_loc)==1
move=move.replace(old_loc,"""    // The PLAYER performing the movement pays, even if their effect moves
    // somebody else's unit. Chain owner takes precedence over card owner.
    PlayerId mover=PlayerId::None;
    if(state_.chain.resuming.has_value())
        mover=state_.chain.resuming->controller;
    else if(acting_!=kInvalidId && state_.objectExists(acting_))
        mover=state_.getObject(acting_).controller;
    else mover=obj.controller;
    if(mover!=PlayerId::None){
        for(const auto& b:state_.battlefields)if(b.id==bf){
            const int idx=playerIndex(mover);
            const int energy=b.gravity_move_tax_energy[idx];
            const int power=b.gravity_move_tax_power[idx];
            if((energy>0||power>0) &&
               !resource::payIn(state_,events_,mover,energy,power,
                                resource::kAnyDomain))return;
            break;
        }
    }
"""+old_loc,1);
ex=ex[:beg]+move+ex[end:]
expath.write_text(ex)


# RAD-132 Heimerdinger Academy Instructor token replacement. This happens
# before the token is created/played (replacement effect), not after the
# original token emits TokenCreatedEvent / EnteredBoardEvent.
ex_path=engine/"src/engine/effect_executor.cpp"
ex=ex_path.read_text()
token_begin=ex.index("GameObjectId EffectExecutor::createToken(")
token_end=ex.index("BattlefieldId EffectExecutor::addBattlefieldToken(", token_begin)
token_fn=ex[token_begin:token_end]
start_anchor="    const bool asked_enter_ready = enter_ready;\n    auto id = state_.createObject();"
start_replacement="""    const bool asked_enter_ready = enter_ready;
    // Heimerdinger Academy Instructor (RAD-132): replacement is optional,
    // applies only to unit-token PLAY events controlled by this player,
    // and is active only while a friendly Heimerdinger is at a battlefield.
    // Preserve the location and ready/exhaust instructions.
    std::string played_name = name;
    int played_might = might;
    std::vector<std::string> played_tags = tags;
    KeywordSet played_keywords = keywords;
    CardDefId played_token_card = token_card;
    if (type == CardType::Unit) {
        bool heimer_present = false;
        for (const auto& [sid, source] : state_.objects.onBoard()) {
            if (source.card_def_id == CardDefId{1123} &&
                source.controller == controller && source.isUnit() &&
                source.isAtBattlefield()) {
                heimer_present = true;
                break;
            }
        }
        if (heimer_present && (!agent_query_ ||
                confirmNow(controller, "Heimerdinger: replace unit token with 3 Might Mech?"))) {
            played_name = "Mech";
            played_might = 3;
            played_tags = {"Mech"};
            played_keywords = KeywordSet{};
            played_token_card = kInvalidId;
        }
    }
    auto id = state_.createObject();"""
assert token_fn.count(start_anchor)==1,"Heimer token begin anchor changed"
token_fn=token_fn.replace(start_anchor,start_replacement,1)
replacements=[
 ("obj.card_def_id = token_card;","obj.card_def_id = played_token_card;"),
 ("obj.name = name;","obj.name = played_name;"),
 ("obj.base_might = might;","obj.base_might = played_might;"),
 ("obj.current_might = might;","obj.current_might = played_might;"),
 ("obj.tags = tags;","obj.tags = played_tags;"),
 ("obj.keywords = keywords;","obj.keywords = played_keywords;"),
 ('"TOKEN: created " + name + " ("','"TOKEN: created " + played_name + " ("'),
 ("std::to_string(might) +","std::to_string(played_might) +"),
 ("TokenCreatedEvent{id, controller, type, name, location}","TokenCreatedEvent{id, controller, type, played_name, location}"),
 ('"play an additional copy of " + name + "?"','"play an additional copy of " + played_name + "?"'),
 ('"play the additional " + name + " to"','"play the additional " + played_name + " to"'),
 ('"TOKEN: an additional copy of " + name + " is played"','"TOKEN: an additional copy of " + played_name + " is played"'),
 ("createToken(controller, type, name, might, tags, keywords, copy_at,","createToken(controller, type, played_name, played_might, played_tags, played_keywords, copy_at,"),
 ("asked_enter_ready, location_choices, token_card, enters_exhausted);","asked_enter_ready, location_choices, played_token_card, enters_exhausted);")
]
for old,new in replacements:
    assert token_fn.count(old)==1,"Heimer token anchor missing or duplicated: "+old
    token_fn=token_fn.replace(old,new,1)
ex_path.write_text(ex[:token_begin]+token_fn+ex[token_end:])


# RAD-012/015: true play permission from banishment, at normal costs and
# normal timing, expiring at the owner's next Ending Step.
gp=engine/"src/engine/game_engine.cpp"
g=gp.read_text()
banish_helper="""// RAD-012 / RAD-015: banished cards with a one-time play permission.
static bool radianceBanishedCardPlayable(const GameState& s,PlayerId who,GameObjectId id){
    if(!s.objectExists(id))return false;
    const auto& obj=s.getObject(id);
    if(obj.owner!=who||obj.zone!=ZoneType::Banishment)return false;
    const auto it=obj.card_counters.find("__rad_play_until_turn");
    if(it==obj.card_counters.end())return false;
    if(s.player(who).turns_taken>it->second)return false;
    if(s.turn.turn_player==who&&s.turn.phase==TurnPhase::EndingStep)return false;
    return true;
}
static void radianceAppendGrantedBanishment(const GameState& s,PlayerId who,
                                            std::vector<GameObjectId>& into){
    for(auto id:s.player(who).banishment)
        if(radianceBanishedCardPlayable(s,who,id))into.push_back(id);
}

"""
hand_anchor="std::vector<GameObjectId> GameEngine::handAndChampion(PlayerId player) const {"
assert g.count(hand_anchor)==1,"banish helper insertion anchor"
g=g.replace(hand_anchor,banish_helper+hand_anchor,1)
# handAndChampion is used by ambush play generators only.
body_anchor="        out.push_back(ps.champion_zone);\n    return out;\n}"
assert g.count(body_anchor)==1,"handAndChampion body anchor"
g=g.replace(body_anchor,"        out.push_back(ps.champion_zone);\n    radianceAppendGrantedBanishment(state_,player,out);\n    return out;\n}",1)
# Main phase: units, gear and spells may be played at their printed costs.
unita="    std::vector<GameObjectId> unit_sources = ps.hand;"
assert g.count(unita)==1,"unit source anchor"
g=g.replace(unita,unita+"\n    radianceAppendGrantedBanishment(state_,player,unit_sources);",1)
playa="            play_intent.card = card_id;\n            play_intent.use_alt_play_cost = alt == 1;"
assert g.count(playa)==1,"unit intent source"
g=g.replace(playa,"            play_intent.card = card_id;\n            if(card.zone==ZoneType::Banishment)play_intent.play_source=Intent::PlaySource::Banishment;\n            play_intent.use_alt_play_cost = alt == 1;",1)
geara="    // Play gear from hand (to base only, CR 149.2)\n    for (auto card_id : ps.hand) {"
assert g.count(geara)==1,"gear source anchor"
g=g.replace(geara,"    // Play gear from hand or permission-granted banishment (CR 149.2)\n    std::vector<GameObjectId> rad_gear_sources=ps.hand;\n    radianceAppendGrantedBanishment(state_,player,rad_gear_sources);\n    for (auto card_id : rad_gear_sources) {",1)
# Previous overlays can alter the play-intent body: restrict this edit to
# the gear generation block, rather than matching a whole source-wide pair.
gear_start=g.index("    // Play gear from hand or permission-granted banishment")
gear_end=g.index("    // Play spells from hand",gear_start)
gear_section=g[gear_start:gear_end]
gearintent="        play_intent.card = card_id;"
assert gear_section.count(gearintent)==1,"gear card assignment"
gear_section=gear_section.replace(gearintent,gearintent+"\n        if(card.zone==ZoneType::Banishment)play_intent.play_source=Intent::PlaySource::Banishment;",1)
g=g[:gear_start]+gear_section+g[gear_end:]
spellstart="    if (ps.cant_play_cards_this_turn || ps.cant_play_spells_this_turn) return;\n    for (auto card_id : ps.hand) {"
assert g.count(spellstart)==1,"spell source"
g=g.replace(spellstart,"    if (ps.cant_play_cards_this_turn || ps.cant_play_spells_this_turn) return;\n    std::vector<GameObjectId> rad_spell_sources=ps.hand;\n    radianceAppendGrantedBanishment(state_,player,rad_spell_sources);\n    for (auto card_id : rad_spell_sources) {",1)
emit_a="        auto emit = [&](Intent play) { actions.push_back(std::move(play)); };"
assert g.count(emit_a)==1,"spell emit"
g=g.replace(emit_a,"        auto emit = [&](Intent play) {\n            if(card.zone==ZoneType::Banishment)play.play_source=Intent::PlaySource::Banishment;\n            actions.push_back(std::move(play));\n        };",1)
reaction="    std::vector<GameObjectId> sources = ps.hand;\n    if (ps.champion_zone != kInvalidId"
assert g.count(reaction)==1,"reaction permanent source"
g=g.replace(reaction,"    std::vector<GameObjectId> sources = ps.hand;\n    radianceAppendGrantedBanishment(state_,player,sources);\n    if (ps.champion_zone != kInvalidId",1)
reactionintent="        play.card = card_id;\n        if (card.isGear()) {"
assert g.count(reactionintent)==1,"reaction intent source"
g=g.replace(reactionintent,"        play.card = card_id;\n        if(card.zone==ZoneType::Banishment)play.play_source=Intent::PlaySource::Banishment;\n        if (card.isGear()) {",1)
# Also permit banished [Ambush] units at their proper showdown and closed timings.
for t in ["IntentType::PlayActionCard","IntentType::PlayReaction"]:
    aa="            ambush.type = "+t+";\n            ambush.player = player;"
    assert g.count(aa)==1,"ambush type anchor "+t
    g=g.replace(aa,"            ambush.type = "+t+";\n            ambush.play_source=card.zone==ZoneType::Banishment ? Intent::PlaySource::Banishment : Intent::PlaySource::Hand;\n            ambush.player = player;",1)
# Card play removes the specific card from banishment, and clears its grant
# so the same object cannot be replayed if it is banished again.
cardseg="void GameEngine::executePlayCard(const Intent& intent) {"
idx=g.index(cardseg);end=g.index("void GameEngine::executePlaySpell(",idx)
part=g[idx:end]
a="    } else if (intent.play_source == Intent::PlaySource::Trash &&\n               card.zone == ZoneType::Trash) {"
assert part.count(a)==1,"permanent remove source"
part=part.replace(a,"    } else if (intent.play_source == Intent::PlaySource::Banishment &&\n               card.zone == ZoneType::Banishment) {\n        auto& zone=state_.player(card.owner).banishment;\n        zone.erase(std::remove(zone.begin(),zone.end(),intent.card),zone.end());\n        card.card_counters.erase(\"__rad_play_until_turn\");\n"+a,1)
g=g[:idx]+part+g[end:]
spella="    } else if (intent.play_source == Intent::PlaySource::Trash &&\n               card.zone == ZoneType::Trash) {\n        // Trash-replay (Death from Below):"
assert g.count(spella)==1,"spell remove source"
g=g.replace(spella,"    } else if (intent.play_source == Intent::PlaySource::Banishment &&\n               card.zone == ZoneType::Banishment) {\n        auto& zone=state_.player(card.owner).banishment;\n        zone.erase(std::remove(zone.begin(),zone.end(),intent.card),zone.end());\n        card.card_counters.erase(\"__rad_play_until_turn\");\n"+spella,1)
gp.write_text(g)


# RAD-163 Hunters Circle: location-aware discount for the first unit or gear
# each player plays to this battlefield on their own turn.
hunter_path=engine/"src/engine/game_engine.cpp"
g=hunter_path.read_text()
# executePlayCard is located BEFORE generateMainPhaseActions in pinned
# AlphaRune. Forward-declare these helpers so calls compile independently
# of their later definitions.
hunter_forward_decl="""static bool radianceHuntersFirstPlayHere(
    const GameState&, PlayerId, GameObjectId, const std::optional<LocationId>&);
static void radianceMarkHunterPlay(
    GameState&, PlayerId, const std::optional<LocationId>&);

"""
play_def="void GameEngine::executePlayCard(const Intent& intent) {"
assert g.count(play_def)==1, "Hunter forward-declaration anchor changed"
g=g.replace(play_def,hunter_forward_decl+play_def,1)
hunter_helper="""static const char* radianceHunterKey(PlayerId p) {
    return p==PlayerId::Player1?"__rad_hc_p1_turn":"__rad_hc_p2_turn";
}
static bool radianceHuntersFirstPlayHere(const GameState& s,PlayerId p,
                                GameObjectId card,
                                const std::optional<LocationId>& dest) {
    if(s.turn.turn_player!=p||!s.objectExists(card)||!dest.has_value()||
       !std::holds_alternative<BattlefieldLocation>(*dest))return false;
    const auto& played=s.getObject(card);
    if(!played.isUnit()&&!played.isGear())return false;
    const auto where=std::get<BattlefieldLocation>(*dest).id;
    for(const auto& b:s.battlefields) {
       if(b.id!=where||!s.objectExists(b.card_object_id))continue;
       const auto& source=s.getObject(b.card_object_id);
       if(source.card_def_id!=CardDefId{1130})return false;
       const auto it=source.card_counters.find(radianceHunterKey(p));
       return it==source.card_counters.end()||it->second!=s.turn.turn_number;
    }
    return false;
}
static void radianceMarkHunterPlay(GameState& s,PlayerId p,
                                   const std::optional<LocationId>& dest) {
    const auto where=std::get<BattlefieldLocation>(*dest).id;
    for(const auto& b:s.battlefields)if(b.id==where&&s.objectExists(b.card_object_id)){
        s.getObject(b.card_object_id).card_counters[radianceHunterKey(p)]
            =s.turn.turn_number;
        return;
    }
}
"""
anchor="std::vector<Intent> GameEngine::generateMainPhaseActions(PlayerId player) const {"
assert g.count(anchor)==1,"Hunter helpers anchor"
g=g.replace(anchor,hunter_helper+anchor,1)
start=g.index(anchor);end=g.index("std::vector<Intent> GameEngine::generateMulliganActions(",start)
block=g[start:end]
discount_expr="""        bool hunter_ok=false;
        Card::PlayCostAdjust hunter_adj;
        hunter_adj.energy_reduction=1;
        if(passesPlayGates(player,card_id))for(const auto& bf:state_.battlefields){
            const std::optional<LocationId> to=BattlefieldLocation{bf.id};
            if(radianceHuntersFirstPlayHere(state_,player,card_id,to)&&
               canAffordWith(player,card_id,0,hunter_adj)){hunter_ok=true;break;}
        }
"""
needle="        const bool printed_ok = canAfford(player, card_id);\n        if (!printed_ok && !alt_ok) continue;"
assert block.count(needle)==1,"hunter unit entry"
block=block.replace(needle,"        const bool printed_ok = canAfford(player, card_id);\n"+discount_expr+"        if (!printed_ok && !alt_ok && !hunter_ok) continue;",1)
needle="            if (alt == 0 && !printed_ok) continue;"
assert block.count(needle)==1,"hunter unit alt gate"
block=block.replace(needle,"            if (alt == 0 && !printed_ok && !hunter_ok) continue;",1)
# Do not depend on other overlays' exact unit-base formatting.
# Remove unaffordable ordinary base plays after the complete action list
# is built; Hunter discounts only exist at the selected battlefield.

needle="                if (can_play_here) {\n                    Intent bf_play = play_intent;"
assert block.count(needle)==1,"hunter BF slot"
block=block.replace(needle,"""                const std::optional<LocationId> to=BattlefieldLocation{bf.id};
                const bool hunter_afford=alt==0&&passesPlayGates(player,card_id)&&
                    radianceHuntersFirstPlayHere(state_,player,card_id,to)&&
                    canAffordWith(player,card_id,0,hunter_adj);
                if (can_play_here && (alt==1||printed_ok||hunter_afford)) {
                    Intent bf_play = play_intent;""",1)
# Deploy gear can only be played at BFs, and its cost may be discounted here.
needle="        if (!canAfford(player, card_id)) continue;\n\n        Intent play_intent;"
assert block.count(needle)==1,"hunter gear affordability"
block=block.replace(needle,"""        const bool printed_ok=canAfford(player,card_id);
        Card::PlayCostAdjust hunter_adj;hunter_adj.energy_reduction=1;
        bool hunter_ok=false;
        if(card.keywords.has(Keyword::Deploy)&&passesPlayGates(player,card_id))
            for(const auto& bf:state_.battlefields){
                const std::optional<LocationId> to=BattlefieldLocation{bf.id};
                if(radianceHuntersFirstPlayHere(state_,player,card_id,to)&&
                   canAffordWith(player,card_id,0,hunter_adj))hunter_ok=true;
            }
        if(!printed_ok&&!hunter_ok)continue;

        Intent play_intent;""",1)
# Initial Radiance overlay rewrites the gear destination as a Deploy/else
# branch; locate that block rather than the original pre-Deploy sequence.
gear_begin=block.index("    // Play gear from hand or permission-granted banishment")
gear_end=block.index("    // Play spells from hand",gear_begin)
gear_block=block[gear_begin:gear_end]
needle="""        if (card.hasKeyword(Keyword::Deploy)) {
            for (const auto& bf : state_.battlefields) {
                Intent battlefield_play = play_intent;
                battlefield_play.play_location = BattlefieldLocation{bf.id};
                actions.push_back(battlefield_play);
            }
        } else {
            play_intent.play_location = BaseLocation{player};
            actions.push_back(play_intent);
        }"""
assert gear_block.count(needle)==1,"hunter post-Deploy gear destination"
gear_block=gear_block.replace(needle,"""        if (card.hasKeyword(Keyword::Deploy)) {
            for (const auto& bf : state_.battlefields) {
                const std::optional<LocationId> to=BattlefieldLocation{bf.id};
                const bool with_discount=radianceHuntersFirstPlayHere(state_,player,card_id,to)&&
                    canAffordWith(player,card_id,0,hunter_adj);
                if(!printed_ok&&!with_discount)continue;
                Intent battlefield_play=play_intent;
                battlefield_play.play_location=to;
                actions.push_back(battlefield_play);
            }
        } else if(printed_ok) {
            play_intent.play_location=BaseLocation{player};
            actions.push_back(play_intent);
        }""",1)
block=block[:gear_begin]+gear_block+block[gear_end:]
end_anchor="    return actions;\n}"
assert block.count(end_anchor)==1,"Hunter main-phase return"
block=block.replace(end_anchor,"""    actions.erase(std::remove_if(actions.begin(),actions.end(),[&](const Intent& a){
        if(a.type!=IntentType::PlayCard || a.use_alt_play_cost ||
           !a.play_location.has_value() ||
           !std::holds_alternative<BaseLocation>(*a.play_location) ||
           !state_.objectExists(a.card))return false;
        const auto& obj=state_.getObject(a.card);
        return obj.isUnit()&&!canAfford(player,a.card);
    }),actions.end());
    return actions;
}""",1)
g=g[:start]+block+g[end:]
start=g.index("void GameEngine::executePlayCard(const Intent& intent) {")
end=g.index("void GameEngine::executePlaySpell(",start)
block=g[start:end]
needle="    bool paid_via_grant = false;\n    if (intent.play_source == Intent::PlaySource::Trash)"
assert block.count(needle)==1,"hunter cost setup"
block=block.replace(needle,"    const bool hunter_discount=radianceHuntersFirstPlayHere(state_,intent.player,intent.card,intent.play_location);\n"+needle,1)
needle="    if (!intent.use_alt_play_cost && !paid_via_grant)\n        prepay = payAdditionalPlayCosts(intent.player, intent.card, location_power);"
assert block.count(needle)==1,"hunter prepay"
block=block.replace(needle,needle+"\n    if(hunter_discount)prepay.energy_reduction+=1;",1)
needle="        payAdditionalCost(intent.player, alt.energy, alt.power, d, spendForObject(card));"
assert block.count(needle)==1,"hunter alt cost"
block=block.replace(needle,"        payAdditionalCost(intent.player, std::max(0,alt.energy-(hunter_discount?1:0)), alt.power, d, spendForObject(card));",1)
needle="    // Track play count\n    ps.cards_played_this_turn++;"
assert block.count(needle)==1,"hunter use count"
block=block.replace(needle,"    if(hunter_discount)radianceMarkHunterPlay(state_,intent.player,intent.play_location);\n"+needle,1)
g=g[:start]+block+g[end:]
hunter_path.write_text(g)


# RAD-167 Neeko's three pregame legend choices are part of a legal deck
# submission, not arbitrary random legends chosen after the game starts.
dh=engine/"src/rules/deck_validator.h"
d=dh.read_text()
anchor="    std::vector<CardDefId> sideboard;     // 0-10 cards"
assert d.count(anchor)==1,"Neeko deck submission anchor"
d=d.replace(anchor,anchor+"\n    std::vector<CardDefId> neeko_legends;  // exactly three named legends, if Neeko is in deck",1)
dh.write_text(d)
dc=engine/"src/rules/deck_validator.cpp"
d=dc.read_text()
marker="    checkBanList(deck, result);\n\n    return result;"
assert d.count(marker)==1,"Neeko validator anchor"
validate="""    checkBanList(deck, result);
    // RAD-167: Neeko selects exactly three EXTRA legends at deck submission.
    // Names, not printing IDs, must all differ from each other and from the
    // starting legend (including alternate printings with the same name).
    const bool neeko_in_deck = deck.chosen_champion==CardDefId{1131} ||
        std::find(deck.main_deck.begin(),deck.main_deck.end(),CardDefId{1131})
            !=deck.main_deck.end();
    if(neeko_in_deck) {
        if(deck.neeko_legends.size()!=3)
            result.addError("Neeko requires exactly 3 extra legends");
        std::set<std::string> names{legend.name};
        for(auto id:deck.neeko_legends) {
            if(id==kInvalidId) {
                result.addError("Neeko legends must be valid Legend cards");
                continue;
            }
            const auto& choice=db_.get(id);
            if(choice.card_type!=CardType::Legend)
                result.addError("Neeko legends must be Legend cards: "+choice.name);
            if(!names.insert(choice.name).second)
                result.addError("Neeko legends must all have different names from each other and the starting legend");
        }
    }else if(!deck.neeko_legends.empty()) {
        result.addError("Neeko legends supplied without Neeko in the deck");
    }

    return result;"""
d=d.replace(marker,validate,1)
marker='        } else if (section == "sideboard") {\n            for (int i = 0; i < count; ++i) deck.sideboard.push_back(id);'
assert d.count(marker)==1,"Neeko deck text parser anchor"
d=d.replace(marker,marker+'\n        } else if (section == "neekolegends") {\n            for (int i = 0; i < count; ++i) deck.neeko_legends.push_back(id);',1)
dc.write_text(d)

# The seeded random-deck builder must obey the new Neeko validation rule.
# Make all OTHER seeded choices first, then deterministically select exactly
# three unique legend NAMES. This preserves the historical seed-1 deck hash
# (which hashes only legend/champion/main/runes/battlefields).
random_deck_path=engine/"src/rules/random_deck.cpp"
rd=random_deck_path.read_text()
build_end="""    return deck;
}

std::string RandomDeckBuilder::toDeckList(const DeckSubmission& deck) const {"""
assert rd.count(build_end)==1,"Neeko random-deck build return anchor"
rd=rd.replace(build_end,"""    // RAD-167: Neeko in the chosen champion slot OR Main Deck.
    // Distinct means distinct names, including from starting legend.
    if(deck.chosen_champion==CardDefId{1131} ||
       std::find(deck.main_deck.begin(),deck.main_deck.end(),CardDefId{1131})
           !=deck.main_deck.end()) {
        std::set<std::string> seen{db_.get(deck.legend).name};
        std::vector<CardDefId> pool;
        for(const auto& candidate:legends_)
            if(seen.insert(db_.get(candidate.legend).name).second)
                pool.push_back(candidate.legend);
        if(pool.size()<3)
            throw std::logic_error("RandomDeckBuilder: insufficient distinct Neeko legends");
        for(int i=0;i<3;++i) {
            const auto j=rng.below(pool.size());
            deck.neeko_legends.push_back(pool[j]);
            pool.erase(pool.begin()+static_cast<std::ptrdiff_t>(j));
        }
    }
    return deck;
}

std::string RandomDeckBuilder::toDeckList(const DeckSubmission& deck) const {""",1)
print_anchor='    section("Runes", deck.rune_deck);\n    return out.str();'
assert rd.count(print_anchor)==1,"Neeko random-deck print anchor"
rd=rd.replace(print_anchor,'    section("Runes", deck.rune_deck);\n    if(!deck.neeko_legends.empty())section("NeekoLegends",deck.neeko_legends);\n    return out.str();',1)
random_deck_path.write_text(rd)

# Persist choice and active grant pairing in the copied GameState (also
# preserved by ISMCTS observations and simulation snapshots).
gs=engine/"src/core/game_state.h"
g=gs.read_text()
marker="    GameObjectId legend_zone = kInvalidId;"
assert g.count(marker)==1,"Neeko player legend field"
g=g.replace(marker,marker+"""
    std::vector<CardDefId> neeko_legend_choices;
    struct NeekoLegendGrant {
        GameObjectId source = kInvalidId;
        GameObjectId legend = kInvalidId;
    };
    std::vector<NeekoLegendGrant> neeko_granted_legends;""",1)
gs.write_text(g)
# Setup binds these three to the player, not to a later random choice.
ge=engine/"src/engine/game_engine.cpp"
g=ge.read_text()
marker="    ps.legend_zone = legend_id;"
assert g.count(marker)==1,"Neeko game setup"
g=g.replace(marker,marker+"\n    ps.neeko_legend_choices = deck.neeko_legends;",1)
marker="    ask(ps.legend_zone);"
assert g.count(marker)==1,"Neeko legend effects"
g=g.replace(marker,marker+"\n    for(const auto& grant:ps.neeko_granted_legends)ask(grant.legend);",1)
ge.write_text(g)

# Neeko secondary legends must receive the normal legend-zone triggers,
# including phase and player-scoped legend abilities; treating them as
# passive-only objects would make most selected legends inert in matches.
neeko_tm_path=engine/"src/engine/trigger_manager.cpp"
nt=neeko_tm_path.read_text()
legend_start="""        auto legend_id = state_.player(pid).legend_zone;
        if (legend_id == kInvalidId || !state_.objectExists(legend_id)) continue;
        auto& legend = state_.getObject(legend_id);
        if (cardFiresOn(card_registry_, legend.card_def_id, t)) {
            fireTrigger(legend_id, pid, triggering_spell_energy_spent, t, subject);
        }"""
legend_replace="""        const auto& ps=state_.player(pid);
        std::vector<GameObjectId> legends{ps.legend_zone};
        for(const auto& grant:ps.neeko_granted_legends)legends.push_back(grant.legend);
        for(auto legend_id:legends) {
            if(legend_id==kInvalidId||!state_.objectExists(legend_id))continue;
            const auto& legend=state_.getObject(legend_id);
            if(legend.zone!=ZoneType::LegendZone)continue;
            if(cardFiresOn(card_registry_,legend.card_def_id,t))
                fireTrigger(legend_id,pid,triggering_spell_energy_spent,t,subject);
        }"""
assert nt.count(legend_start)==1,"Neeko legend event helper anchor"
nt=nt.replace(legend_start,legend_replace,1)
for trigger in ["AtEndOfTurn","AtStartOfBeginning","AtStartOfMain"]:
    old=f"""                fireTrigger(ps.legend_zone, e.turn_player, 0, TriggerType::{trigger});
            }}
        }}"""
    extra=f"""                fireTrigger(ps.legend_zone, e.turn_player, 0, TriggerType::{trigger});
            }}
        }}
        for(const auto& grant:ps.neeko_granted_legends) {{
            if(!state_.objectExists(grant.legend))continue;
            const auto& legend=state_.getObject(grant.legend);
            if(legend.zone!=ZoneType::LegendZone)continue;
            if(cardFiresOn(card_registry_,legend.card_def_id,TriggerType::{trigger}))
                fireTrigger(grant.legend,e.turn_player,0,TriggerType::{trigger});
        }}"""
    assert nt.count(old)==1,"Neeko phase legend anchor "+trigger
    nt=nt.replace(old,extra,1)
mighty="""        auto legend_id = state_.player(controller).legend_zone;
        if (legend_id != kInvalidId && state_.objectExists(legend_id) &&
            cardFiresOn(card_registry_, state_.getObject(legend_id).card_def_id,
                        TriggerType::WhenAUnitBecomesMighty))
            fireTrigger(legend_id, controller, 0,
                        TriggerType::WhenAUnitBecomesMighty, /*subject=*/e.object);"""
mighty_extra=mighty+"""
        for(const auto& grant:state_.player(controller).neeko_granted_legends){
            if(!state_.objectExists(grant.legend))continue;
            const auto& legend=state_.getObject(grant.legend);
            if(legend.zone!=ZoneType::LegendZone)continue;
            if(cardFiresOn(card_registry_,legend.card_def_id,TriggerType::WhenAUnitBecomesMighty))
                fireTrigger(grant.legend,controller,0,
                            TriggerType::WhenAUnitBecomesMighty,e.object);
        }"""
assert nt.count(mighty)==1,"Neeko mighty event anchor"
nt=nt.replace(mighty,mighty_extra,1)
neeko_tm_path.write_text(nt)

# Activated granted legends exhaust like other legends, and must be readied
# when their controller's next Awakening Step begins.
ng=engine/"src/engine/game_engine.cpp"
gg=ng.read_text()
ready_anchor="""        // Also ready the legend
        auto legend_id = state_.player(player).legend_zone;
        if (legend_id != kInvalidId && state_.objectExists(legend_id)) {
            auto& legend = state_.getObject(legend_id);
            if (legend.is_exhausted) {
                legend.is_exhausted = false;
                events_.emit(ObjectStateChangedEvent{legend_id, "readied"});
            }
        }"""
ready_patch=ready_anchor+"""
        for(const auto& grant:state_.player(player).neeko_granted_legends){
            if(!state_.objectExists(grant.legend))continue;
            auto& legend=state_.getObject(grant.legend);
            if(legend.zone==ZoneType::LegendZone&&legend.is_exhausted){
                legend.is_exhausted=false;
                events_.emit(ObjectStateChangedEvent{grant.legend,"readied"});
            }
        }"""
assert gg.count(ready_anchor)==1,"Neeko awakening ready anchor"
gg=gg.replace(ready_anchor,ready_patch,1)
ng.write_text(gg)

# A Legend-Zone grant is a WHILE effect; immediately remove it when that
# specific Neeko leaves the board, not when a triggered chain item resolves.
ex=engine/"src/engine/effect_executor.cpp"
e=ex.read_text()
start=e.index("void EffectExecutor::leftBoard(GameObjectId object) {")
end=e.index("void EffectExecutor::putIntoDeckFromBoard(",start)
part=e[start:end]
marker="    if (!state_.objectExists(object)) return;"
assert part.count(marker)==1,"Neeko leaves board source"
part=part.replace(marker,marker+"""
    // RAD-167 Neeko: Legend Zone addition stops existing immediately
    // when its granting Neeko leaves, even if another Neeko remains.
    for(auto player:{PlayerId::Player1,PlayerId::Player2}){
        auto& grants=state_.player(player).neeko_granted_legends;
        for(auto it=grants.begin();it!=grants.end();){
            if(it->source!=object){++it;continue;}
            if(state_.objectExists(it->legend))state_.objects.erase(it->legend);
            it=grants.erase(it);
        }
    }""",1)
e=e[:start]+part+e[end:]
ex.write_text(e)


# RAD-068 Orianna, Mechanical Marvel: an optional gear discount (1 Energy
# AND 1 any Power) per active Orianna source per turn, not just the first
# gear played. An unspent discount may be saved for a later gear.
orianna_state=engine/"src/core/game_state.h"
os=orianna_state.read_text()
oa="        bool first_gear_per_turn = false;"
assert os.count(oa)==1,"Orianna modifier-field anchor"
os=os.replace(oa,oa+"""
        bool radiance_orianna_once = false;       // one discount per source/turn
        bool radiance_orianna_declined = false;   // temporarily excluded for this payment""",1)
orianna_state.write_text(os)

orianna_engine=engine/"src/engine/game_engine.cpp"
og=orianna_engine.read_text()
applies_anchor="    if (mod.gear_only && !card.isGear()) return false;"
assert og.count(applies_anchor)==1,"Orianna applies anchor"
og=og.replace(applies_anchor,applies_anchor+"""
    if (mod.radiance_orianna_once) {
        if (mod.radiance_orianna_declined || !state.objectExists(mod.source)) return false;
        const auto& source=state.getObject(mod.source);
        if (source.card_def_id!=CardDefId{1091} ||
            source.controller!=payer || !source.isAtBattlefield())return false;
        const auto it=source.card_counters.find("__rad_orianna_used_turn");
        if (it!=source.card_counters.end() && it->second==state.turn.turn_number)
            return false;
    }""",1)
payment_start=og.index("GameEngine::CostPaymentAdvance GameEngine::beginCostPayment(")
payment_end=og.index("GameEngine::CostPaymentAdvance GameEngine::beginPaymentOf(",payment_start)
payment_block=og[payment_start:payment_end]
payment_anchor="""    auto& ps = state_.player(player);
    const auto cost = effectiveCardCost(state_, def, card_registry_.get(card.card_def_id),
                                        player, card, adj);"""
assert payment_block.count(payment_anchor)==1,"Orianna payment anchor"
payment_patch="""    auto& ps = state_.player(player);
    // Affordability checks assume all optional Orianna discounts can be used.
    // At actual payment, offer each source independently and preserve
    // unspent discounts for another gear later in this turn.
    std::vector<GameObjectId> orianna_used;
    if (card.isGear()) {
        for (auto& m : ps.cost_modifiers) {
            if (!m.radiance_orianna_once ||
                !costModifierApplies(state_,m,true,player,card,
                                     anyCombatInProgress(state_),def.energy_cost))
                continue;
            m.radiance_orianna_declined = true;
            // A legal play cannot decline its last necessary discount.
            const bool can_skip=canAffordWith(player,card_obj,0,adj);
            if (!can_skip ||
                effect_executor_->confirmNow(player,
                    "Orianna: spend this source's [1][A] gear discount?")) {
                m.radiance_orianna_declined = false;
                orianna_used.push_back(m.source);
            }
        }
    }
    const auto cost = effectiveCardCost(state_, def, card_registry_.get(card.card_def_id),
                                        player, card, adj);
    for (auto& m : ps.cost_modifiers)
        if (m.radiance_orianna_once) m.radiance_orianna_declined=false;
    // A source used for this paid play cannot be used again this turn;
    // its standing aura is restored on the next aura pass but the counter
    // survives until the turn number changes.
    for (auto id : orianna_used)
        if (state_.objectExists(id))
            state_.getObject(id).card_counters["__rad_orianna_used_turn"]
                = state_.turn.turn_number;"""
payment_block=payment_block.replace(payment_anchor,payment_patch);
og=og[:payment_start]+payment_block+og[payment_end:]
orianna_engine.write_text(og)

# Deterministic rune payment (the 60-pair hidden-information regression).
# The pinned resource::payIn default used lowest GameObjectId as the tie
# breaker even between DIFFERENT rune cards. Salting object IDs can then
# exhaust/recycle a different rune for Gravity Field's [1][A] movement tax.
# Sort by observable rune identity first, by ID only for equal copies.
resource_path=engine/"src/engine/resource_payment.h"
resources=resource_path.read_text()
rune_begin=resources.index("inline std::vector<GameObjectId> runesInBase(")
rune_end=resources.index("/// Energy `player` could pay",rune_begin)
rune_block=resources[rune_begin:rune_end]
old_sort="    std::sort(out.begin(), out.end());"
assert rune_block.count(old_sort)==1,"Canonical rune payment sort anchor changed"
new_sort="""    // Different rune types must not be selected based on object IDs:
    // under hidden-order ID relabelling they are the same public game.
    // The final ID tie-break matters only for indistinguishable copies.
    std::sort(out.begin(), out.end(), [&](GameObjectId a, GameObjectId b) {
        const auto& ra=state.getObject(a);
        const auto& rb=state.getObject(b);
        if(ra.card_def_id!=rb.card_def_id)return ra.card_def_id<rb.card_def_id;
        if(ra.domains.get()!=rb.domains.get())
            return ra.domains.get()<rb.domains.get();
        if(ra.is_exhausted!=rb.is_exhausted)
            return !ra.is_exhausted;
        return a<b;
    });"""
rune_block=rune_block.replace(old_sort,new_sort,1)
resources=resources[:rune_begin]+rune_block+resources[rune_end:]
resource_path.write_text(resources)

print("RADIANCE_FINAL64_OVERLAY_APPLIED: engine IDs 1068..1131 (64 distinct identities)")
