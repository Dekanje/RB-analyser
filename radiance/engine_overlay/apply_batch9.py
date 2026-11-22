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
    ("cards/units/1028_radiance_batch9_tranche2a.cpp",
     "src/cards/units/1028_radiance_batch9_tranche2a.cpp"),
    ("cards/units/1032_radiance_batch9_tranche2b.cpp",
     "src/cards/units/1032_radiance_batch9_tranche2b.cpp"),
    ("cards/units/1036_radiance_batch9_tranche2c.cpp",
     "src/cards/units/1036_radiance_batch9_tranche2c.cpp"),
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
    f"void register_card_{i}(CardRegistry&);" for i in [1025,1026,1027,1029,1030,1034,1035]),1)
s=s.replace(registration,registration+"\n"+ "\n".join(
    f"    register_card_{i}(registry);" for i in [1025,1026,1027,1029,1030,1034,1035]),1)
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

# Radiance 2026-10-16 Core Rules: Disarm is a stackable attack-trigger keyword.
# Keep existing bit positions stable; extend keyword enum before Count sentinel.
types=engine/"src/core/types.h"
words=types.read_text()
old="    Deploy       = 25,  // Radiance: gear played to battlefield; dies on enemy hold\n    Count        = 26,"
new="    Deploy       = 25,  // Radiance: gear played to battlefield; dies on enemy hold\n    Disarm       = 26,  // Radiance: stackable -N Might when attacking\n    Count        = 27,"
assert words.count(old)==1, "Disarm enum anchor changed"
types.write_text(words.replace(old,new,1))

types_cpp=engine/"src/core/types.cpp"
names=types_cpp.read_text()
old="        case Keyword::Deploy:       return \"Deploy\";"
new=old+"\n        case Keyword::Disarm:       return \"Disarm\";"
assert names.count(old)==1, "Disarm string-table anchor changed"
types_cpp.write_text(names.replace(old,new,1))

# Common Disarm dispatcher: both printed keywords and continuous aura grants
# (e.g. Clanging Sentry) contribute to the SAME attack. Fired once per unit
# per combat by fireAttackDefendTriggers' existing per-combat guard. This
# implementation currently uses an immediate object-choice prompt, not a
# separate reactable ability on the chain. That timing gap is recorded in
# the Batch 9 report and evidence ledger.
trigger_source=engine/"src/engine/trigger_manager.cpp"
src=trigger_source.read_text()
before="    const bool is_defender = (obj.controller == defender);\n\n"
insert="""    const bool is_defender = (obj.controller == defender);

    // Radiance Disarm (2026-10-16): stack printed and aura-granted values.
    // The caller has already suppressed repeat attacks in this combat.
    if (is_attacker && obj.hasKeyword(Keyword::Disarm) && effect_executor_) {
        int disarm = 0;
        if (obj.keywords.has(Keyword::Disarm)) {
            disarm = 1;
            if (obj.card_def_id != kInvalidId)
                if (const Card* c = card_registry_.get(obj.card_def_id))
                    if (c->def().ability_text.find("[Disarm 2]") != std::string::npos)
                        disarm = 2;
        }
        for (const auto& aura : obj.aura_effects)
            if (aura.keyword == Keyword::Disarm)
                disarm += std::max(1, aura.keyword_value);
        if (disarm > 0) {
            std::vector<GameObjectId> opponents_here;
            for (const auto& [uid, target] : state_.objects.onBoard()) {
                if (!target.isUnit() || !target.isAtBattlefield() ||
                    target.controller == obj.controller ||
                    target.battlefieldId() != battlefield) continue;
                opponents_here.push_back(uid);
            }
            std::sort(opponents_here.begin(), opponents_here.end());
            if (!opponents_here.empty()) {
                GameObjectId chosen = effect_executor_->chooseObjectNow(
                    obj.controller, opponents_here,
                    "Disarm: choose an enemy unit here", PromptKind::ChooseObject);
                if (chosen != kInvalidId && state_.objectExists(chosen)) {
                    const auto& target = state_.getObject(chosen);
                    if (target.isUnit() && target.isAtBattlefield() &&
                        target.controller != obj.controller &&
                        target.battlefieldId() == battlefield)
                        effect_executor_->giveTemporaryMight(chosen, -disarm);
                }
            }
        }
    }

"""
assert src.count(before)==1, "Disarm attack hook anchor changed"
trigger_source.write_text(src.replace(before,insert,1))

print("RADIANCE_BATCH9_IMPLEMENTATIONS_APPLIED: 7 distinct new cards; existing Radiance identities not re-registered, Disarm keyword and attack dispatcher")
