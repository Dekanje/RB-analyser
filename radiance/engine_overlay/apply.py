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
    ("cards/spells/0962_last_caress.cpp","src/cards/spells/0962_last_caress.cpp"),
    ("cards/legends/0963_iron_revenant.cpp","src/cards/legends/0963_iron_revenant.cpp"),
    ("cards/units/0964_twice_slain.cpp","src/cards/units/0964_twice_slain.cpp"),
    ("cards/spells/0965_realm_of_death.cpp","src/cards/spells/0965_realm_of_death.cpp"),
    ("cards/legends/0969_jarvan_package.cpp","src/cards/legends/0969_jarvan_package.cpp"),
    ("cards/legends/0972_orianna_package.cpp","src/cards/legends/0972_orianna_package.cpp"),
    ("cards/legends/0978_ziggs_package.cpp","src/cards/legends/0978_ziggs_package.cpp"),
    ("cards/legends/0966_ekko_package.cpp","src/cards/legends/0966_ekko_package.cpp"),
    ("cards/legends/0975_seraphine_package.cpp","src/cards/legends/0975_seraphine_package.cpp"),
    ("cards/units/0983_additional_deck_cards.cpp","src/cards/units/0983_additional_deck_cards.cpp")]:
    target=engine/dest
    if target.exists():raise SystemExit("Collision: "+str(target))
    shutil.copyfile(source/src,target)
def replace_once(path,before,after):
    s=path.read_text()
    if s.count(before)!=1:raise SystemExit(f"Unexpected anchor in {path}: {before}")
    path.write_text(s.replace(before,after,1))
init=engine/"src/cards/cards_init.cpp"
replace_once(init,"void register_card_955(CardRegistry&);",
"void register_card_955(CardRegistry&);\nvoid register_card_956(CardRegistry&);\nvoid register_card_957(CardRegistry&);\nvoid register_card_958(CardRegistry&);\nvoid register_card_959(CardRegistry&);\nvoid register_card_960(CardRegistry&);\nvoid register_card_961(CardRegistry&);\nvoid register_card_962(CardRegistry&);\nvoid register_card_963(CardRegistry&);\nvoid register_card_964(CardRegistry&);\nvoid register_card_965(CardRegistry&);\nvoid register_card_969(CardRegistry&);\nvoid register_card_970(CardRegistry&);\nvoid register_card_971(CardRegistry&);\nvoid register_card_972(CardRegistry&);\nvoid register_card_973(CardRegistry&);\nvoid register_card_974(CardRegistry&);\nvoid register_card_978(CardRegistry&);\nvoid register_card_979(CardRegistry&);\nvoid register_card_980(CardRegistry&);\nvoid register_card_981(CardRegistry&);\nvoid register_card_982(CardRegistry&);\nvoid register_card_966(CardRegistry&);\nvoid register_card_967(CardRegistry&);\nvoid register_card_968(CardRegistry&);\nvoid register_card_975(CardRegistry&);\nvoid register_card_976(CardRegistry&);\nvoid register_card_977(CardRegistry&);\nvoid register_card_983(CardRegistry&);\nvoid register_card_984(CardRegistry&);\nvoid register_card_985(CardRegistry&);\nvoid register_card_986(CardRegistry&);")
replace_once(init,"    register_card_955(registry);",
"    register_card_955(registry);\n    register_card_956(registry);\n    register_card_957(registry);\n    register_card_958(registry);\n    register_card_959(registry);\n    register_card_960(registry);\n    register_card_961(registry);\n    register_card_962(registry);\n    register_card_963(registry);\n    register_card_964(registry);\n    register_card_965(registry);\n    register_card_969(registry);\n    register_card_970(registry);\n    register_card_971(registry);\n    register_card_972(registry);\n    register_card_973(registry);\n    register_card_974(registry);\n    register_card_978(registry);\n    register_card_979(registry);\n    register_card_980(registry);\n    register_card_981(registry);\n    register_card_982(registry);\n    register_card_966(registry);\n    register_card_967(registry);\n    register_card_968(registry);\n    register_card_975(registry);\n    register_card_976(registry);\n    register_card_977(registry);\n    register_card_983(registry);\n    register_card_984(registry);\n    register_card_985(registry);\n    register_card_986(registry);")
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


# Mordekaiser: floating [A] restricted to playing units or gear.
pool=engine/"src/core/game_state.h"
replace_once(pool,
    '    int gear_power = 0;        // [A], "Use only to play gear or use gear abilities."',
    '    int gear_power = 0;        // [A], "Use only to play gear or use gear abilities."\n'
    '    int unit_or_gear_power = 0; // Mordekaiser: restricted [A]')
replace_once(pool, "        gear_power = 0;\n        for (int i = 0;",
    "        gear_power = 0;\n        unit_or_gear_power = 0;\n        for (int i = 0;")
replace_once(pool, "        int sum = universal_power + spell_power + gear_power;",
    "        int sum = universal_power + spell_power + gear_power + unit_or_gear_power;")
replace_once(pool,
    "        return (f == SpendFor::Spell ? spell_power : 0) +\n               (f == SpendFor::Gear ? gear_power : 0);",
    "        return (f == SpendFor::Spell ? spell_power : 0) +\n"
    "               (f == SpendFor::Gear ? gear_power : 0) +\n"
    "               ((f == SpendFor::Unit || f == SpendFor::Gear) ? unit_or_gear_power : 0);")
replace_once(pool,
    "        if (f == SpendFor::Gear) take(gear_power);",
    "        if (f == SpendFor::Gear) take(gear_power);\n"
    "        if (f == SpendFor::Unit || f == SpendFor::Gear) take(unit_or_gear_power);")
observer=engine/"src/engine/observer_view.cpp"
replace_once(observer,
    "        put(out, r.pool.spell_power); put(out, r.pool.gear_power);",
    "        put(out, r.pool.spell_power); put(out, r.pool.gear_power);\n"
    "        put(out, r.pool.unit_or_gear_power);")


# The printed Mordekaiser restriction says "PLAY units or gear", not pay
# for those cards' activated abilities. Preserve old restrictions allowing
# unit-energy for unit abilities and gear-power for gear abilities.
replace_once(pool,
    "    Gear,    // playing a gear, or an activated ability of a gear",
    "    Gear,    // playing a gear, or an activated ability of a gear\n"
    "    UnitAbility, // activated ability of a unit; excludes Mordekaiser play-only [A]\n"
    "    GearAbility, // activated ability of gear; excludes Mordekaiser play-only [A]")
replace_once(pool,
    "return (f == SpendFor::Unit ? unit_energy : 0) +",
    "return ((f == SpendFor::Unit || f == SpendFor::UnitAbility) ? unit_energy : 0) +")
replace_once(pool,
    "if (f == SpendFor::Unit) take(unit_energy);",
    "if (f == SpendFor::Unit || f == SpendFor::UnitAbility) take(unit_energy);")
replace_once(pool,
    "(f == SpendFor::Gear ? gear_power : 0) +",
    "((f == SpendFor::Gear || f == SpendFor::GearAbility) ? gear_power : 0) +")
replace_once(pool,
    "if (f == SpendFor::Gear) take(gear_power);",
    "if (f == SpendFor::Gear || f == SpendFor::GearAbility) take(gear_power);")
resource_header=engine/"src/engine/resource_payment.h"
replace_once(resource_header,
    "/// A showdown (or the combat that follows it) is under way somewhere.",
    """inline SpendFor spendForActivation(const GameObject& obj) {
    if (obj.isUnit()) return SpendFor::UnitAbility;
    if (obj.isGear()) return SpendFor::GearAbility;
    return spendForObject(obj);
}

/// A showdown (or the combat that follows it) is under way somewhere.""")
replace_once(game,
    "const SpendFor spend_for = spendForObject(state_.getObject(source_id));",
    "const SpendFor spend_for = spendForActivation(state_.getObject(source_id));")
replace_once(game,
    "        spendForObject(state_.getObject(source)));",
    "        spendForActivation(state_.getObject(source)));")


# Radiance Deploy — Gear is played to a battlefield, never the base.
# A Deploy permanent is killed when the other player holds its battlefield.
types=engine/"src/core/types.h"
replace_once(types,
    "    Flow         = 24,  // Vendetta: spell may be played from trash for its Flow cost, then banished\n    Count        = 25,",
    "    Flow         = 24,  // Vendetta: spell may be played from trash for its Flow cost, then banished\n"
    "    Deploy       = 25,  // Radiance: gear played to battlefield; dies on enemy hold\n"
    "    Count        = 26,")
replace_once(game,
    """        play_intent.play_location = BaseLocation{player};
        actions.push_back(play_intent);
    }

    // Play spells from hand — Neutral Open allows any spell""",
    """        if (card.hasKeyword(Keyword::Deploy)) {
            for (const auto& bf : state_.battlefields) {
                Intent battlefield_play = play_intent;
                battlefield_play.play_location = BattlefieldLocation{bf.id};
                actions.push_back(battlefield_play);
            }
        } else {
            play_intent.play_location = BaseLocation{player};
            actions.push_back(play_intent);
        }
    }

    // Play spells from hand — Neutral Open allows any spell""")
replace_once(game,
    """            make(IntentType::PlayCard, {}, LocationId{BaseLocation{player}});
            if (!card.isUnit() || ps.units_play_base_only) continue;""",
    """            if (card.isGear() && card.hasKeyword(Keyword::Deploy)) {
                for (const auto& bf : state_.battlefields)
                    make(IntentType::PlayCard, {},
                         LocationId{BattlefieldLocation{bf.id}});
                continue;
            }
            make(IntentType::PlayCard, {}, LocationId{BaseLocation{player}});
            if (!card.isUnit() || ps.units_play_base_only) continue;""")
trigger=engine/"src/engine/trigger_manager.cpp"
replace_once(trigger,
    """        for (auto wid : watchers)
            fireTrigger(wid, e.player, 0, TriggerType::WhenYouPlayAGear, /*subject=*/e.object);
    }

    // "When you play a unit" and its relatives.""",
    """        for (auto wid : watchers)
            fireTrigger(wid, e.player, 0, TriggerType::WhenYouPlayAGear, /*subject=*/e.object);
        fireLegendTrigger(TriggerType::WhenYouPlayAGear,e.player,0,e.object);
    }

    // "When you play a unit" and its relatives.""")
replace_once(trigger,
    """    // Battlefield triggers
    for (auto& bf : state_.battlefields) {""",
    """    // Deploy gear stays in a battlefield. Its score triggers work from there
    // just as unit triggers do. An opponent's hold kills Deploy after scoring.
    std::vector<GameObjectId> deploy_to_kill;
    for (auto& [gid, gear] : state_.objects.onBoard()) {
        if (!gear.isGear() || !gear.isAtBattlefield() ||
            !gear.hasKeyword(Keyword::Deploy) ||
            !gear.battlefieldId() || *gear.battlefieldId() != e.battlefield)
            continue;
        if (gear.controller == e.player && e.method == ScoreMethod::Hold &&
            cardFiresOn(card_registry_, gear.card_def_id, TriggerType::WhenIHold))
            fireTrigger(gid, e.player, 0, TriggerType::WhenIHold, scored_bf_card);
        if (gear.controller != e.player && e.method == ScoreMethod::Hold)
            deploy_to_kill.push_back(gid);
    }
    if (effect_executor_) {
        for (auto gid : deploy_to_kill)
            if (state_.objectExists(gid) && state_.getObject(gid).isAtBattlefield())
                effect_executor_->killObject(gid);
    }

    // Battlefield triggers
    for (auto& bf : state_.battlefields) {""")
replace_once(trigger,
    """    // Battlefield cards: "When combat starts here," (Threshold of the Gray).
    fireBattlefieldTriggers(TriggerType::WhenCombatStartsHere, e.attacker, e.battlefield);""",
    """    // Gear with Deploy can have "When one or more friendly units attack here".
    // One trigger per combat event, not per attacker.
    for (const auto& [gid, gear] : state_.objects.onBoard()) {
        if (!gear.isGear() || !gear.hasKeyword(Keyword::Deploy) ||
            !gear.battlefieldId() || *gear.battlefieldId() != e.battlefield ||
            gear.controller != e.attacker)
            continue;
        if (cardFiresOn(card_registry_,gear.card_def_id,TriggerType::WhenIAttack))
            fireTrigger(gid,e.attacker,0,TriggerType::WhenIAttack);
    }
    // Battlefield cards: "When combat starts here," (Threshold of the Gray).
    fireBattlefieldTriggers(TriggerType::WhenCombatStartsHere, e.attacker, e.battlefield);""")


# Orianna: a chosen gear has both unit and gear properties while chosen;
# reset this on leaving the board. Printed CardType stays Gear.
object_header=engine/"src/core/game_object.h"
replace_once(object_header,
    "    // ── Convenience ──",
    "    bool radiance_unit_gear = false; // Orianna's chosen gear is also a unit\n"
    "    // ── Convenience ──")
replace_once(object_header,
    "    bool isUnit() const { return card_type == CardType::Unit; }",
    "    bool isUnit() const { return card_type == CardType::Unit || radiance_unit_gear; }")
board_state=engine/"src/core/board_state.h"
replace_once(board_state,
    "    obj.moves_this_turn = 0;\n    // Keywords: the printed ones again.",
    "    obj.moves_this_turn = 0;\n    obj.radiance_unit_gear = false;\n"
    "    if (def) obj.base_might = def->might;\n    // Keywords: the printed ones again.")

# Ziggs: gear ability Bonus Damage applies to each separate damage instance.
player_state=engine/"src/core/game_state.h"
replace_once(player_state,
    "    int bonus_damage_dealt = 0;      // Annie, Fiery",
    "    int radiance_gear_bonus_damage = 0; // Ziggs, Short-Fused\n"
    "    int bonus_damage_dealt = 0;      // Annie, Fiery")
replace_once(game,
    "        ps.bonus_damage_dealt = 0;   // Annie, Fiery",
    "        ps.bonus_damage_dealt = 0;   // Annie, Fiery\n"
    "        ps.radiance_gear_bonus_damage = 0;")
executor_impl=engine/"src/engine/effect_executor.cpp"
replace_once(executor_impl,
    "int bonus = state_.player(src_obj.controller).bonus_damage_dealt +",
    "int bonus = state_.player(src_obj.controller).bonus_damage_dealt +\n"
    "                            (src_obj.isGear() ? state_.player(src_obj.controller).radiance_gear_bonus_damage : 0) +")

# Reckless Innovator: when a unit becomes exhausted. The engine already
# emits ObjectStateChangedEvent("exhausted") on standard move, activation,
# and direct effects. Route it into a typed trigger.
effects=engine/"src/effects/effect_types.h"
replace_once(effects,
    "    WhenAnOpponentHidesACard,    // delayed abilities only:",
    "    WhenIAmExhausted,           // Radiance: When I become exhausted\n"
    "    WhenAnOpponentHidesACard,    // delayed abilities only:")
replace_once(trigger,
    '    if (e.what_changed == "joined_combat") {',
    """    if (e.what_changed == "exhausted") {
        const auto& obj=state_.getObject(e.object);
        if (obj.isUnit() && obj.card_def_id!=kInvalidId &&
            cardFiresOn(card_registry_,obj.card_def_id,TriggerType::WhenIAmExhausted))
            fireTrigger(e.object,controller,0,TriggerType::WhenIAmExhausted);
        return;
    }
    if (e.what_changed == "joined_combat") {""")
replace_once(executor_impl,
    '    if (!inPlay(obj)) return;\n    obj.is_exhausted = true;\n    events_.emit(ObjectStateChangedEvent{target, "exhausted"});',
    '    if (!inPlay(obj) || obj.is_exhausted) return;\n    obj.is_exhausted = true;\n    events_.emit(ObjectStateChangedEvent{target, "exhausted"});')


# Seraphine: optional alternate spell cost paid BEFORE normal resources.
# The extra cost is exhaust the ready legend and three distinct ready units.
game=engine/"src/engine/game_engine.cpp"
replace_once(game,
    "void GameEngine::forgetPlayPayments(PlayerId player, GameObjectId card_id) {",
    """static std::vector<GameObjectId> seraphineReadyUnits(const GameState& state, PlayerId player) {
    std::vector<GameObjectId> ready;
    for (const auto& [id,obj] : state.objects.onBoard())
        if (obj.isUnit() && obj.controller == player && obj.location && !obj.is_exhausted)
            ready.push_back(id);
    return ready;
}
static bool seraphineMayReduceSpell(const GameState& state, PlayerId player) {
    const auto legend = state.player(player).legend_zone;
    if (!state.objectExists(legend)) return false;
    const auto& l = state.getObject(legend);
    return l.card_def_id == CardDefId::fromRaw(975) && !l.is_exhausted &&
           seraphineReadyUnits(state,player).size() >= 3;
}
void GameEngine::forgetPlayPayments(PlayerId player, GameObjectId card_id) {""")
replace_once(game,
    """    if (!addl.exists || !addl.payable) return {};
    CardContext ctx{state_, events_, *effect_executor_, player, card_id};
    const EffectExecutor::ActingFor acting(*effect_executor_, card_id);
    ctx.registry = &card_registry_;
    const auto adj = cc->payAdditionalPlayCost(ctx, [&](const Card::PlayCostAdjust& a) {
        return canAffordWith(player, card_id, extra_any_power, a);
    });
    if (adj.ignore_cost || adj.energy_reduction > 0 || adj.power_reduction > 0)
        RIFT_TRACE(events_, "ADDITIONAL_COST: " + state_.getObject(card_id).name +
                         (adj.ignore_cost ? " ignores its cost"
                              : " costs [" + std::to_string(adj.energy_reduction) + "] and " +
                                std::to_string(adj.power_reduction) + " Power less"));
    return adj;""",
    """    Card::PlayCostAdjust adj{};
    CardContext ctx{state_, events_, *effect_executor_, player, card_id};
    const EffectExecutor::ActingFor acting(*effect_executor_, card_id);
    ctx.registry = &card_registry_;
    if (addl.exists && addl.payable)
        adj = cc->payAdditionalPlayCost(ctx, [&](const Card::PlayCostAdjust& a) {
            return canAffordWith(player, card_id, extra_any_power, a);
        });
    if (state_.getObject(card_id).isSpell() && seraphineMayReduceSpell(state_,player)) {
        Card::PlayCostAdjust discounted=adj;
        discounted.energy_reduction+=2;
        if (canAffordWith(player,card_id,extra_any_power,discounted)) {
            const bool must_pay=!canAffordWith(player,card_id,extra_any_power,adj);
            if (must_pay || effect_executor_->confirmNow(player,
                "Seraphine: exhaust legend and three ready friendly units to reduce spell cost by 2?")) {
                auto available=seraphineReadyUnits(state_,player);
                std::vector<GameObjectId> selected;
                for(int i=0;i<3;i++) {
                    if(available.empty())break;
                    const auto chosen=effect_executor_->chooseObjectNow(player,available,
                        "Seraphine: choose a distinct ready unit to exhaust");
                    if(chosen==kInvalidId || !state_.objectExists(chosen))break;
                    selected.push_back(chosen);
                    available.erase(std::remove(available.begin(),available.end(),chosen),available.end());
                }
                if(selected.size()==3) {
                    const auto legend=state_.player(player).legend_zone;
                    effect_executor_->exhaustObject(legend);
                    // Pay the simultaneous exhaustion cost before announcing it.
                    for(auto id:selected)state_.getObject(id).is_exhausted=true;
                    for(auto id:selected)
                        events_.emit(ObjectStateChangedEvent{id,"exhausted"});
                    events_.emit(ObjectStateChangedEvent{selected.front(),"seraphine_three_exhausted"});
                    adj.energy_reduction+=2;
                }
            }
        }
    }
    if (adj.ignore_cost || adj.energy_reduction > 0 || adj.power_reduction > 0)
        RIFT_TRACE(events_, "ADDITIONAL_COST: " + state_.getObject(card_id).name +
                         (adj.ignore_cost ? " ignores its cost"
                              : " costs [" + std::to_string(adj.energy_reduction) + "] and " +
                                std::to_string(adj.power_reduction) + " Power less"));
    return adj;""")
replace_once(game,
    "    return canAffordWith(player, card_obj, extra_any_power, Card::PlayCostAdjust{});\n}\n\n// Whether",
    """    if (card.isSpell() && seraphineMayReduceSpell(state_,player)) {
        Card::PlayCostAdjust discount{};
        discount.energy_reduction=2;
        if (const Card* cls=card_registry_.get(card.card_def_id)) {
            const auto a=cls->additionalPlayCost(state_,card_db_,player,card_obj);
            if(a.exists && a.payable) {
                discount.energy_reduction+=a.best.energy_reduction;
                discount.power_reduction+=a.best.power_reduction;
                discount.ignore_cost=a.best.ignore_cost;
            }
        }
        if(canAffordWith(player,card_obj,extra_any_power,discount))return true;
    }
    return canAffordWith(player, card_obj, extra_any_power, Card::PlayCostAdjust{});
}

// Whether""")
replace_once(game,
    '    for (auto unit_id : moving) events_.emit(ObjectStateChangedEvent{unit_id, "exhausted"});',
    '    for (auto unit_id : moving) events_.emit(ObjectStateChangedEvent{unit_id, "exhausted"});\n'
    '    if(moving.size()>=3)\n'
    '        events_.emit(ObjectStateChangedEvent{moving.front(),"seraphine_three_exhausted"});')
replace_once(effects,
    "    WhenIAmExhausted,           // Radiance: When I become exhausted",
    "    WhenIAmExhausted,           // Radiance: When I become exhausted\n"
    "    WhenThreeFriendsExhausted, // Radiance: a batch exhausted >=3 friendly units")
replace_once(trigger,
    "    if (e.what_changed == \"joined_combat\") {",
    """    if (e.what_changed == "seraphine_three_exhausted") {
        std::vector<GameObjectId> watchers;
        for(const auto& [id,o]:state_.objects.onBoard())
            if(o.isUnit()&&o.controller==controller&&o.location&&o.card_def_id!=kInvalidId &&
                cardFiresOn(card_registry_,o.card_def_id,TriggerType::WhenThreeFriendsExhausted))
                watchers.push_back(id);
        for(auto id:watchers)
            fireTrigger(id,controller,0,TriggerType::WhenThreeFriendsExhausted);
        return;
    }
    if (e.what_changed == "joined_combat") {""")


# Radiance Detonation Amplifier: each friendly Deathknell at its battlefield
# produces one additional real chain item, additive with Karthus, Eternal.
replace_once(trigger,
    """    const int extra = obj.hasKeyword(Keyword::Deathknell)
        ? std::max(0, state_.player(controller).deathknell_double_count) : 0;""",
    """    int radiance_extra = 0;
    const auto where = obj.last_known.valid && obj.last_known.location
                       ? obj.last_known.location : obj.last_location;
    if (obj.hasKeyword(Keyword::Deathknell) && where) {
        for (const auto& [id, gear] : state_.objects.onBoard()) {
            if (!gear.isGear() || gear.card_def_id != CardDefId::fromRaw(985) ||
                gear.controller != controller || !gear.location.has_value()) continue;
            if (*gear.location == *where) ++radiance_extra;
        }
    }
    const int extra = obj.hasKeyword(Keyword::Deathknell)
        ? std::max(0, state_.player(controller).deathknell_double_count) +
          radiance_extra : 0;""")


# Correct regression invariants: native typed object identity, official
# spelling of new Deploy keyword in logs/card ledger.
object_header=engine/"src/core/game_object.h"
replace_once(object_header,
    "    bool radiance_unit_gear = false; // Orianna's chosen gear is also a unit",
    "    bool radiance_unit_gear = false; // Orianna's chosen gear is also a unit\n"
    "    std::optional<GameObjectId> radiance_selected_gear; // typed legend reference")
types_impl=engine/"src/core/types.cpp"
replace_once(types_impl,
    '        case Keyword::Flow:         return "Flow";',
    '        case Keyword::Flow:         return "Flow";\n'
    '        case Keyword::Deploy:       return "Deploy";')

print("OVERLAY_SUCCESS 986 definitions and corrected card/regression contracts")
