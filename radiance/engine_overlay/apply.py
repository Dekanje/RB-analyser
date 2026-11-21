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
    ("cards/units/0957_ksante_courageous.cpp","src/cards/units/0957_ksante_courageous.cpp")]:
    target=engine/dest
    if target.exists():raise SystemExit("Collision: "+str(target))
    shutil.copyfile(source/src,target)
def replace_once(path,before,after):
    s=path.read_text()
    if s.count(before)!=1:raise SystemExit(f"Unexpected anchor in {path}: {before}")
    path.write_text(s.replace(before,after,1))
init=engine/"src/cards/cards_init.cpp"
replace_once(init,"void register_card_955(CardRegistry&);",
"void register_card_955(CardRegistry&);\nvoid register_card_956(CardRegistry&);\nvoid register_card_957(CardRegistry&);")
replace_once(init,"    register_card_955(registry);",
"    register_card_955(registry);\n    register_card_956(registry);\n    register_card_957(registry);")
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
print("OVERLAY_SUCCESS two card classes and Riven ready-on-entry hook")
