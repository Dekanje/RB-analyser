#!/usr/bin/env python3
"""Version-locked experimental C++ overlay; not full nine-deck support."""
import pathlib,subprocess,shutil
root=pathlib.Path(__file__).resolve().parents[2]
engine=root/"alpharune"
sha=subprocess.check_output(["git","rev-parse","HEAD"],cwd=engine,text=True).strip()
if sha!="ec90f0fed002aed374d06249fa95e83e3cfbd386":
    raise SystemExit("Unsupported AlphaRune source commit: "+sha)
source=root/"radiance/engine_overlay/source"
for src,dest in [
    ("cards/legends/0956_the_exile.cpp","src/cards/legends/0956_the_exile.cpp"),
    ("cards/units/0957_ksante_courageous.cpp","src/cards/units/0957_ksante_courageous.cpp"),
    ("cards/legends/0958_agonys_embrace.cpp","src/cards/legends/0958_agonys_embrace.cpp")]:
    target=engine/dest
    if target.exists():raise SystemExit("Collision: "+str(target))
    shutil.copyfile(source/src,target)
def replace_once(path,before,after):
    s=path.read_text()
    if s.count(before)!=1:raise SystemExit(f"Unexpected anchor in {path}: {before}")
    path.write_text(s.replace(before,after,1))
init=engine/"src/cards/cards_init.cpp"
replace_once(init,"void register_card_955(CardRegistry&);",
"void register_card_955(CardRegistry&);\nvoid register_card_956(CardRegistry&);\nvoid register_card_957(CardRegistry&);\nvoid register_card_958(CardRegistry&);")
replace_once(init,"    register_card_955(registry);",
"    register_card_955(registry);\n    register_card_956(registry);\n    register_card_957(registry);\n    register_card_958(registry);")
game=engine/"src/engine/game_engine.cpp"
original="        if (state_.player(card.controller).otherUnitsEnterReady(card.id)) enters_ready = true;"
replacement=original+"""
        // Radiance Riven: only units played to an ALREADY-controlled battlefield.
        if (std::holds_alternative<BattlefieldLocation>(loc)) {
            const auto& ps = state_.player(item.controller);
            if (ps.legend_zone != kInvalidId &&
                state_.objectExists(ps.legend_zone) &&
                state_.getObject(ps.legend_zone).name == "The Exile") {
                const auto& bf = getBattlefield(std::get<BattlefieldLocation>(loc).id);
                if (bf.controller.has_value() && *bf.controller == item.controller)
                    enters_ready = true;
            }
        }"""
replace_once(game,original,replacement)
trigger=engine/"src/engine/trigger_manager.cpp"
original_trigger="""void TriggerManager::onPlayedFromFacedown(const PlayedFromFacedownEvent& e) {
    const TriggerEventScope event_scope(state_.chain);"""
# Add the Legend trigger in the card-play handler, not all trigger handlers.
handler=trigger.read_text()
start=handler.find(original_trigger)
if start<0:raise SystemExit("Missing face-down trigger handler")
end=handler.find("\nvoid TriggerManager::",start+1)
if end<0:raise SystemExit("Missing next trigger handler")
part=handler[start:end]
needle="""    }
}"""
if part.count(needle)!=1:raise SystemExit("Ambiguous face-down trigger terminator")
newpart=part.replace(needle,'''    }
    // Radiance Evelynn: Legends also watch cards played from face down.
    fireLegendTrigger(TriggerType::WhenYouPlayFromFacedown, e.player, 0, e.card);
}''',1)
trigger.write_text(handler[:start]+newpart+handler[end:])
print("OVERLAY_SUCCESS three card classes, Riven entry and Evelynn face-down trigger")
