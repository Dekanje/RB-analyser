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
    ("cards/legends/0958_agonys_embrace.cpp","src/cards/legends/0958_agonys_embrace.cpp"),
    ("cards/gear/0959_blade_of_the_exile.cpp","src/cards/gear/0959_blade_of_the_exile.cpp"),
    ("cards/legends/0960_pride_of_nazumah.cpp","src/cards/legends/0960_pride_of_nazumah.cpp"),
    ("cards/spells/0961_ntofo_strikes.cpp","src/cards/spells/0961_ntofo_strikes.cpp"),
    ("cards/spells/0962_last_caress.cpp","src/cards/spells/0962_last_caress.cpp")]:
    target=engine/dest
    if target.exists():raise SystemExit("Collision: "+str(target))
    shutil.copyfile(source/src,target)
def replace_once(path,before,after):
    s=path.read_text()
    if s.count(before)!=1:raise SystemExit(f"Unexpected anchor in {path}: {before}")
    path.write_text(s.replace(before,after,1))
init=engine/"src/cards/cards_init.cpp"
replace_once(init,"void register_card_955(CardRegistry&);",
"void register_card_955(CardRegistry&);\nvoid register_card_956(CardRegistry&);\nvoid register_card_957(CardRegistry&);\nvoid register_card_958(CardRegistry&);\nvoid register_card_959(CardRegistry&);\nvoid register_card_960(CardRegistry&);\nvoid register_card_961(CardRegistry&);\nvoid register_card_962(CardRegistry&);")
replace_once(init,"    register_card_955(registry);",
"    register_card_955(registry);\n    register_card_956(registry);\n    register_card_957(registry);\n    register_card_958(registry);\n    register_card_959(registry);\n    register_card_960(registry);\n    register_card_961(registry);\n    register_card_962(registry);")
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

# Generalized Equip alternative-payment hook, rather than a hard-coded card ID.
header=engine/"src/cards/card.h"
anchor="    virtual bool payEquipExtraCost(CardContext& /*ctx*/, GameObjectId /*unit*/) { return true; }"
insert="""    virtual bool canPayEquipAlternative(const GameState&, PlayerId,
                                         GameObjectId, GameObjectId) const { return false; }
    virtual bool payEquipAlternative(CardContext&, GameObjectId) { return false; }
"""+anchor
replace_once(header,anchor,insert)
card_impl=engine/"src/cards/card.cpp"
canpay="""    if (!resource::canPay(state, controller, cost.energy, cost.power,
                          cost.power_any_domain ? Domain::Count : cost.power_domain,
                          SpendFor::Gear))
        return false;
    return canPayEquipExtraCost(state, controller, gear, unit);"""
canpay_new="""    if (!resource::canPay(state, controller, cost.energy, cost.power,
                          cost.power_any_domain ? Domain::Count : cost.power_domain,
                          SpendFor::Gear) &&
        !canPayEquipAlternative(state, controller, gear, unit))
        return false;
    return canPayEquipExtraCost(state, controller, gear, unit);"""
replace_once(card_impl,canpay,canpay_new)
payment="""    if (!ctx.executor.payResources(ctx.controller, cost.energy, cost.power,
                                   resource::maskOf(cost.power_any_domain ? Domain::Count
                                                                          : cost.power_domain),
                                   SpendFor::Gear))
        return false;
    if (!payEquipExtraCost(ctx, unit)) return false;"""
payment_new="""    const bool payable_regular = resource::canPay(
        ctx.state, ctx.controller, cost.energy, cost.power,
        cost.power_any_domain ? Domain::Count : cost.power_domain, SpendFor::Gear);
    const bool payable_other = canPayEquipAlternative(
        ctx.state, ctx.controller, ctx.source, unit);
    if (!payable_regular && !payable_other) return false;
    const bool choose_other = payable_other &&
        (!payable_regular || ctx.executor.confirmNow(ctx.controller,
            "Pay Equip by exhausting a friendly unit instead of Power?"));
    if (choose_other) {
        if (!payEquipAlternative(ctx, unit)) return false;
    } else if (!ctx.executor.payResources(
        ctx.controller, cost.energy, cost.power,
        resource::maskOf(cost.power_any_domain ? Domain::Count : cost.power_domain),
        SpendFor::Gear)) return false;
    if (!payEquipExtraCost(ctx, unit)) return false;"""
# The pinned engine has two distinct Equip paths:
# - payEquipAndAttach(): immediate attachment (Weaponmaster)
# - payEquip(): pay the activated Equip cost, attach after resolving its chain item.
# They share the payment logic, but have different return statements.
payment_deferred = """    if (!ctx.executor.payResources(ctx.controller, cost.energy, cost.power,
                                   resource::maskOf(cost.power_any_domain ? Domain::Count
                                                                          : cost.power_domain),
                                   SpendFor::Gear))
        return false;
    return payEquipExtraCost(ctx, unit);"""
payment_deferred_new = """    const bool payable_regular = resource::canPay(
        ctx.state, ctx.controller, cost.energy, cost.power,
        cost.power_any_domain ? Domain::Count : cost.power_domain, SpendFor::Gear);
    const bool payable_other = canPayEquipAlternative(
        ctx.state, ctx.controller, ctx.source, unit);
    if (!payable_regular && !payable_other) return false;
    const bool choose_other = payable_other &&
        (!payable_regular || ctx.executor.confirmNow(ctx.controller,
            "Pay Equip by exhausting a friendly unit instead of Power?"));
    if (choose_other) {
        if (!payEquipAlternative(ctx, unit)) return false;
    } else if (!ctx.executor.payResources(
        ctx.controller, cost.energy, cost.power,
        resource::maskOf(cost.power_any_domain ? Domain::Count : cost.power_domain),
        SpendFor::Gear)) return false;
    return payEquipExtraCost(ctx, unit);"""
s=card_impl.read_text()
if s.count(payment)!=1 or s.count(payment_deferred)!=1:
    raise SystemExit("Unrecognized AlphaRune Equip payment implementation")
card_impl.write_text(s.replace(payment,payment_new,1)
                      .replace(payment_deferred,payment_deferred_new,1))


# K'Sante's "Assault equal to my Shield" is a temporary dynamic property.
# Each grant stacks, and it follows Shield changes until expiration.
object_header=engine/"src/core/game_object.h"
replace_once(object_header,
    '    int temp_shield_value = 0;   // temporary shield applied "this turn"',
    '    int temp_shield_value = 0;   // temporary shield applied "this turn"\n'
    '    int temp_assault_shield_multiples = 0; // K\'Sante: dynamic Assault=Shield grants this turn')
replace_once(object_header,
    "            current_might += assault_value;",
    "            current_might += assault_value + temp_assault_shield_multiples * shield_value;")
board_state=engine/"src/core/board_state.h"
replace_once(board_state,
    "    obj.temp_shield_value = 0;\n    obj.temp_deflect_value = 0;",
    "    obj.temp_shield_value = 0;\n    obj.temp_deflect_value = 0;\n"
    "    obj.temp_assault_shield_multiples = 0;")
replace_once(board_state,
    "obj.temp_assault_value != 0 || obj.temp_shield_value != 0 ||",
    "obj.temp_assault_value != 0 || obj.temp_shield_value != 0 ||\n"
    "           obj.temp_assault_shield_multiples != 0 ||")
replace_once(game,
    '    obj.temp_deflect_value = 0;   // [Deflect N] given "this turn"',
    '    obj.temp_deflect_value = 0;   // [Deflect N] given "this turn"\n'
    '    obj.temp_assault_shield_multiples = 0;')
executor_impl=engine/"src/engine/effect_executor.cpp"
replace_once(executor_impl,
    '    mix(static_cast<uint64_t>(static_cast<int64_t>(obj.temp_assault_value)));',
    '    mix(static_cast<uint64_t>(static_cast<int64_t>(obj.temp_assault_value)));\n'
    '    mix(static_cast<uint64_t>(static_cast<int64_t>(obj.temp_assault_shield_multiples)));')


# Last Caress: a turn-scoped delayed one-shot for the next unit play.
player_state=engine/"src/core/game_state.h"
replace_once(player_state,
    '    bool units_enter_ready_this_turn = false;   // "Units you play this turn enter ready" (Confront, Bushwhack)',
    '    int next_unit_any_bf_buff_turn = -1;\n'
    '    int next_unit_any_bf_buff_count = 0;\n'
    '    bool units_enter_ready_this_turn = false;   // "Units you play this turn enter ready" (Confront, Bushwhack)')
replace_once(player_state,
    "        units_enter_ready_this_turn = false;",
    "        next_unit_any_bf_buff_count = 0;\n        next_unit_any_bf_buff_turn = -1;\n"
    "        units_enter_ready_this_turn = false;")
playperm=engine/"src/engine/play_permissions.cpp"
replace_once(playperm,
    "    if (controlled) return true;  // default: controlled BFs",
    "    if (controlled) return true;  // default: controlled BFs\n"
    "    if (ps.next_unit_any_bf_buff_turn == state.turn.turn_number &&\n"
    "        ps.next_unit_any_bf_buff_count > 0) return true; // Last Caress")
replace_once(trigger,
    "void TriggerManager::announceUnitPlayed(GameObjectId unit, PlayerId player) {\n    std::vector<GameObjectId> watchers;",
    """void TriggerManager::announceUnitPlayed(GameObjectId unit, PlayerId player) {
    // Last Caress: consume location permission on the first unit played.
    // The actual Buff is a delayed triggered ability on the chain, not
    // an immediate/unreactable bonus.
    auto& ps = state_.player(player);
    if (ps.next_unit_any_bf_buff_count > 0 &&
        ps.next_unit_any_bf_buff_turn == state_.turn.turn_number &&
        state_.objectExists(unit))
        ps.next_unit_any_bf_buff_count = 0;
    std::vector<GameObjectId> watchers;""")

print("OVERLAY_SUCCESS seven C++ cards; includes Last Caress delayed play and K\'Sante Assault")
