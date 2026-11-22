#!/usr/bin/env python3
"""Apply unique Radiance battlefield tranche after Batch 9's Disarm overlay."""
from pathlib import Path
import shutil
root=Path(__file__).resolve().parents[2]
engine=root/"alpharune"
source=root/"radiance/engine_overlay/source"
for src,dst in [
 ("cards/battlefields/1040_radiance_batch9_battlefields_a.cpp",
  "src/cards/battlefields/1040_radiance_batch9_battlefields_a.cpp"),
 ("cards/battlefields/1044_radiance_batch9_battlefields_b.cpp",
  "src/cards/battlefields/1044_radiance_batch9_battlefields_b.cpp"),
]:
    target=engine/dst
    assert not target.exists(),f"Collision {target}"
    shutil.copyfile(source/src,target)

init=engine/"src/cards/cards_init.cpp"
s=init.read_text()
declaration="void register_card_1035(CardRegistry&);"
registration="    register_card_1035(registry);"
assert s.count(declaration)==1 and s.count(registration)==1
s=s.replace(declaration,declaration+"\n"+"\n".join(
    f"void register_card_{i}(CardRegistry&);" for i in range(1040,1048)),1)
s=s.replace(registration,registration+"\n"+"\n".join(
    f"    register_card_{i}(registry);" for i in range(1040,1048)),1)
init.write_text(s)

# Firelights' Hideout: a turn-stamped bonus used for the next unit (not the
# next card or every subsequent unit). No default value persists across turns.
gs=engine/"src/core/game_state.h"
s=gs.read_text()
anchor="    int cards_played_this_turn = 0;"
assert s.count(anchor)==1
s=s.replace(anchor,anchor+"\n    int firelights_next_accelerate_turn = 0;",1)
gs.write_text(s)

ge=engine/"src/engine/game_engine.cpp"
s=ge.read_text()
anchor="    if (!card.isUnit()) return false;\n    if (card.keywords.has(Keyword::Accelerate)) return true;"
replacement="""    if (!card.isUnit()) return false;
    if (state_.player(player).firelights_next_accelerate_turn ==
        state_.turn.turn_number + 1) return true;
    if (card.keywords.has(Keyword::Accelerate)) return true;"""
assert s.count(anchor)==1, "Accelerate gate changed"
ge.write_text(s.replace(anchor,replacement,1))

tm=engine/"src/engine/trigger_manager.cpp"
s=tm.read_text()
# A real played unit consumes Firelights' delayed grant, after its optional
# additional [Accelerate] cost was offered and after the play was accepted.
anchor="    // Per-turn \"what have you played\" tracking (Swain, Visionary)."
replacement="""    // Firelights' Hideout: spend the grant on the next actually played unit.
    if (e.card_type == CardType::Unit)
        state_.player(e.player).firelights_next_accelerate_turn = 0;

""" + anchor
assert s.count(anchor)==1
s=s.replace(anchor,replacement,1)

# Rakelstake: battlefield itself observes FIRST unit/gear play here each turn
# by each player. Only permanent plays count; a play elsewhere does not.
anchor="    // [Vision] (CR 817): \"When this is played, [Predict].\""
replacement="""    // Radiance Rakelstake: each player predicts on their first unit/gear play
    // at this battlefield per turn; other cards/battlefields are unaffected.
    if (e.card_type == CardType::Unit || e.card_type == CardType::Gear) {
        const auto played_here = obj.battlefieldId();
        if (played_here) {
            for (const auto& bf : state_.battlefields) {
                if (bf.id != *played_here || !state_.objectExists(bf.card_object_id))
                    continue;
                auto& board = state_.getObject(bf.card_object_id);
                if (board.card_def_id != CardDefId::fromRaw(1046)) continue;
                const auto mark = e.player == PlayerId::Player1
                    ? "__rakelstake_p1_last_play_turn" : "__rakelstake_p2_last_play_turn";
                if (board.card_counters[mark] == state_.turn.turn_number + 1) break;
                board.card_counters[mark] = state_.turn.turn_number + 1;
                fireTrigger(bf.card_object_id,e.player,0,
                            TriggerType::WhenYouPlayACard,e.object);
                break;
            }
        }
    }

""" + anchor
assert s.count(anchor)==1
s=s.replace(anchor,replacement,1)

# Black Rose Sanctum: per player, first non-token unit dying at the
# battlefield each turn produces a Recruit at the dead unit owner's base.
anchor="    // Deathknell an Equipment gave the unit"
replacement="""    // Radiance Black Rose Sanctum: per-player once/turn non-token unit death.
    if (state_.objectExists(e.object) &&
        state_.getObject(e.object).isUnit() &&
        !state_.getObject(e.object).isToken() &&
        e.controller != PlayerId::None) {
        for (const auto& bf : state_.battlefields) {
            if (e.was_at != LocationId{BattlefieldLocation{bf.id}} ||
                !state_.objectExists(bf.card_object_id)) continue;
            auto& card = state_.getObject(bf.card_object_id);
            if (card.card_def_id != CardDefId::fromRaw(1041)) continue;
            const auto key = e.controller == PlayerId::Player1
                ? "__black_rose_p1_dead_turn" : "__black_rose_p2_dead_turn";
            if (card.card_counters[key] == state_.turn.turn_number + 1) break;
            card.card_counters[key] = state_.turn.turn_number + 1;
            fireTrigger(bf.card_object_id,e.controller,0,
                        TriggerType::WhenAFriendlyUnitDies,e.object);
            break;
        }
    }
""" + anchor
assert s.count(anchor)==1
s=s.replace(anchor,replacement,1)

# Bandle Scouts' Academy: this checks the actual hidden-at battlefield
# rather than all hidden cards across the board.
anchor="    checkDelayedAbilities(TriggerType::WhenAnOpponentHidesACard, opponent(e.player), e.card);"
replacement="""    // Radiance Bandle Scouts' Academy observes hidden cards at THIS BF.
    if (state_.objectExists(e.card)) {
        const auto hidden_here = state_.getObject(e.card).hidden_at;
        for (const auto& bf : state_.battlefields) {
            if (bf.id != hidden_here || !state_.objectExists(bf.card_object_id))
                continue;
            if (state_.getObject(bf.card_object_id).card_def_id ==
                CardDefId::fromRaw(1040))
                fireTrigger(bf.card_object_id,e.player,0,
                            TriggerType::WhenYouHideACard,e.card);
            break;
        }
    }
""" + anchor
assert s.count(anchor)==1
s=s.replace(anchor,replacement,1)
tm.write_text(s)
print("RADIANCE_BATCH9_BATTLEFIELDS_APPLIED: 1040..1047, eight unique effects and event hooks")
