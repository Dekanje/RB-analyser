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
trigger.write_text(tr.replace(event_anchor,event_replace,1))

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
