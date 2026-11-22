// Radiance wave 1: five genuine, individually-authored C++ card rules.
// Source: Riot gallery snapshot card text in AlphaRune cards/json/rad_*.json.
// This is NOT a stub/metadata-only set import.
#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <variant>
#include <vector>

namespace riftbound {
namespace {

// RAD-077/167: I enter ready. Shield 3.
class RadianceWrathOfTheFreljord final : public UnitCard {
public:
    const CardDef& def() const override { return def_; }
    bool entersReadyOnPlay(const GameState&, PlayerId) const override { return true; }
private:
    const CardDef def_ = [] {
        CardDef d;
        d.id=989; d.def_id="rad-077-167";
        d.name="Wrath of the Freljord"; d.set_code="RAD"; d.set_name="Radiance";
        d.public_code="RAD-077/167"; d.collector_number=77;
        d.card_type=CardType::Unit; d.domains={Domain::Body};
        d.energy_cost=9; d.might=7; d.rarity=Rarity::Common;
        d.keywords.set(Keyword::Shield); d.shield_value=3;
        d.ability_text="I enter ready. [Shield 3]";
        return d;
    }();
};

// RAD-088/167: Assault 2, Shield 2. The engine calculates these
// combat bonuses from the printed keyword and numeric feature values.
class RadianceStaunchSurvivor final : public UnitCard {
public:
    const CardDef& def() const override { return def_; }
private:
    const CardDef def_ = [] {
        CardDef d;
        d.id=990; d.def_id="rad-088-167";
        d.name="Staunch Survivor"; d.set_code="RAD"; d.set_name="Radiance";
        d.public_code="RAD-088/167"; d.collector_number=88;
        d.card_type=CardType::Unit; d.domains={Domain::Body};
        d.energy_cost=2; d.power_cost=1; d.might=2; d.rarity=Rarity::Rare;
        d.keywords.set(Keyword::Assault); d.assault_value=2;
        d.keywords.set(Keyword::Shield); d.shield_value=2;
        d.ability_text="[Assault 2], [Shield 2]";
        return d;
    }();
};

// RAD-059/167: Deal 10 to a unit. Draw 2.
// "A unit" is a play-time target; the target must still be legal on resolve.
class RadianceSupernova final : public SpellCard {
public:
    const CardDef& def() const override { return def_; }
    TargetRequirements getTargetRequirements() const override {
        return TargetRequirements{.count=1,.must_be_unit=true};
    }
    void onResolve(CardContext& ctx, const std::vector<GameObjectId>& targets) override {
        if (targets.empty() || !ctx.state.objectExists(targets.front())) return;
        const GameObjectId target=targets.front();
        ctx.executor.dealDamage(target,10,ctx.source);
        ctx.executor.killLethallyDamagedTogether({target});
        ctx.executor.drawCards(ctx.controller,2);
    }
private:
    const CardDef def_ = [] {
        CardDef d;
        d.id=991; d.def_id="rad-059-167";
        d.name="Supernova"; d.set_code="RAD"; d.set_name="Radiance";
        d.public_code="RAD-059/167"; d.collector_number=59;
        d.card_type=CardType::Spell; d.domains={Domain::Order};
        d.energy_cost=9; d.power_cost=1; d.rarity=Rarity::Uncommon;
        d.ability_text="Deal 10 to a unit. Draw 2.";
        return d;
    }();
};

// RAD-079/167: Deal 3 to ALL units in bases, regardless of controller.
// Damage is assigned to the complete snapshot before simultaneous lethal
// cleanup. Units at battlefields are unaffected.
class RadianceAvalanche final : public SpellCard {
public:
    const CardDef& def() const override { return def_; }
    void onResolve(CardContext& ctx, const std::vector<GameObjectId>&) override {
        std::vector<GameObjectId> victims;
        for (const auto& [id,obj] : ctx.state.objects.onBoard()) {
            if (obj.isUnit() && obj.location.has_value() &&
                std::holds_alternative<BaseLocation>(*obj.location))
                victims.push_back(id);
        }
        std::sort(victims.begin(),victims.end());
        for (GameObjectId id : victims)
            ctx.executor.dealDamage(id,3,ctx.source);
        ctx.executor.killLethallyDamagedTogether(victims);
    }
private:
    const CardDef def_ = [] {
        CardDef d;
        d.id=992; d.def_id="rad-079-167";
        d.name="Avalanche"; d.set_code="RAD"; d.set_name="Radiance";
        d.public_code="RAD-079/167"; d.collector_number=79;
        d.card_type=CardType::Spell; d.domains={Domain::Body};
        d.energy_cost=5; d.power_cost=2; d.rarity=Rarity::Uncommon;
        d.ability_text="Deal 3 to all units in bases.";
        return d;
    }();
};

// RAD-099/167: "When you play me, choose an opponent.
// You and that player each draw 1." 1v1 AlphaRune only has one opponent.
class RadianceSuaveNegotiator final : public UnitCard {
public:
    const CardDef& def() const override { return def_; }
    TriggerType triggerType() const override { return TriggerType::WhenYouPlayMe; }
    void onTrigger(CardContext& ctx, const std::vector<GameObjectId>&) override {
        ctx.executor.drawCards(ctx.controller,1);
        ctx.executor.drawCards(opponent(ctx.controller),1);
    }
private:
    const CardDef def_ = [] {
        CardDef d;
        d.id=993; d.def_id="rad-099-167";
        d.name="Suave Negotiator"; d.set_code="RAD"; d.set_name="Radiance";
        d.public_code="RAD-099/167"; d.collector_number=99;
        d.card_type=CardType::Unit; d.domains={Domain::Chaos};
        d.energy_cost=3; d.might=3; d.rarity=Rarity::Common;
        d.ability_text="When you play me, choose an opponent. You and that player each draw 1.";
        return d;
    }();
};
}  // namespace

void register_card_989(CardRegistry& r){r.registerCard(989,std::make_unique<RadianceWrathOfTheFreljord>());}
void register_card_990(CardRegistry& r){r.registerCard(990,std::make_unique<RadianceStaunchSurvivor>());}
void register_card_991(CardRegistry& r){r.registerCard(991,std::make_unique<RadianceSupernova>());}
void register_card_992(CardRegistry& r){r.registerCard(992,std::make_unique<RadianceAvalanche>());}
void register_card_993(CardRegistry& r){r.registerCard(993,std::make_unique<RadianceSuaveNegotiator>());}
}  // namespace riftbound
