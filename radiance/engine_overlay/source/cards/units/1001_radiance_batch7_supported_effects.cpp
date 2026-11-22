// Radiance Batch 7: seven individually implemented cards using existing
// engine semantics (finalized choice, equip, auras, and cost reductions).
// Printed data: pinned AlphaRune Riot-gallery JSON rad_048, 058, 071, 072,
// 122, 128, 037. No registry-only stubs.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <optional>
#include <vector>

namespace riftbound {
namespace {

class RadianceRiptideMage final : public UnitCard {
public:
    const CardDef& def() const override { return d_; }
    unsigned choicesAtFinalization() const override { return kFinalizeTrigger; }
    TriggerType triggerType() const override { return TriggerType::WhenYouPlayMe; }
    void onTrigger(CardContext& ctx, const std::vector<GameObjectId>&) override {
        auto legal=chooseableUnits(ctx.state,ctx.controller,[&](const GameObject& u){
            return u.controller!=ctx.controller && u.location.has_value();
        });
        std::sort(legal.begin(),legal.end());
        const auto t=pickTarget(ctx,"Riptide Mage: give an enemy unit -3 Might",legal);
        if (finalizingChoices(ctx)) return;
        if (t!=kInvalidId && ctx.state.objectExists(t))
            ctx.executor.giveTemporaryMight(t,-3);
    }
private:
    const CardDef d_=[] {
        CardDef d;
        d.id=1001; d.def_id="rad-058-167"; d.public_code="RAD-058/167";
        d.name="Riptide Mage"; d.set_code="RAD"; d.set_name="Radiance";
        d.collector_number=58; d.card_type=CardType::Unit;
        d.domains={Domain::Mind}; d.energy_cost=4; d.power_cost=1;
        d.might=3; d.rarity=Rarity::Uncommon;
        d.keywords.set(Keyword::Accelerate);
        d.ability_text="[Accelerate] (You may pay [1][B] as an additional cost to have me enter ready.)\nWhen you play me, give an enemy unit -3 [M] this turn.";
        return d;
    }();
};

class RadianceHighNote final : public SpellCard {
public:
    const CardDef& def() const override { return d_; }
    bool needsPlayTimeTarget() const override { return true; }
    TargetRequirements getTargetRequirements() const override {
        return TargetRequirements{.count=1,.must_be_unit=true};
    }
    void onResolve(CardContext& ctx, const std::vector<GameObjectId>&) override {
        auto legal=enumerateLegalTargets(ctx.state,ctx.controller);
        std::sort(legal.begin(),legal.end());
        const GameObjectId t=pickTarget(ctx,"High Note: unit loses Might",legal);
        if(t==kInvalidId || !ctx.state.objectExists(t))return;
        int n=0;
        for (const auto& [id,u]:ctx.state.objects.onBoard())
            if(u.isUnit() && u.location.has_value() &&
               u.controller==ctx.controller && u.is_exhausted) ++n;
        ctx.executor.giveTemporaryMight(t,-n);
    }
private:
    const CardDef d_=[] {
        CardDef d;
        d.id=1002; d.def_id="rad-048-167"; d.public_code="RAD-048/167";
        d.name="High Note"; d.set_code="RAD"; d.set_name="Radiance";
        d.collector_number=48; d.card_type=CardType::Spell;
        d.domains={Domain::Mind};d.energy_cost=3;d.rarity=Rarity::Common;
        d.keywords.set(Keyword::Reaction);
        d.ability_text="[Reaction] (Play any time, even before spells and abilities resolve.)\nGive a unit -[M] this turn equal to the number of exhausted units you control.";
        return d;
    }();
};

class RadianceNazumanNtofo final : public GearCard {
public:
    const CardDef& def() const override { return d_; }
    bool hasEquipAbility() const override {return true;}
    EquipCost equipCost(const GameState&,PlayerId,GameObjectId,GameObjectId) const override {
        // Printed Equip [1] is ONE Energy, not one Order Power.
        return {.valid=true,.energy=1};
    }
    KeywordSet equippedKeywords() const override {
        KeywordSet k;k.set(Keyword::Shield);return k;
    }
    int equippedShield() const override {return 2;}
private:
    const CardDef d_=[] {
        CardDef d;
        d.id=1003;d.def_id="rad-071-167";d.public_code="RAD-071/167";
        d.name="Nazuman Ntofo";d.set_code="RAD";d.set_name="Radiance";
        d.collector_number=71;d.card_type=CardType::Gear;
        d.domains={Domain::Order};d.energy_cost=1;d.rarity=Rarity::Common;
        d.keywords.set(Keyword::Equip);
        d.ability_text="Equip [1] ([1]: Attach this to a unit you control.)";
        d.effect_text="[Shield 2] (+2 [M] while I'm a defender.)";
        return d;
    }();
};

class RadianceOverloadedTraveler final : public UnitCard {
public:
    const CardDef& def() const override { return d_; }
    void applyPassiveAura(GameState& state,PlayerId controller) const override {
        forEachSelfOnce(*this,state,controller,[&](GameObjectId sid,GameObject& self){
            if(!self.isAtBattlefield())return;
            const auto bf=self.battlefieldId();
            for(const auto& [id,gear]:state.objects.onBoard()){
                if(!gear.isGear() || gear.controller!=controller ||
                   !gear.location.has_value() || gear.battlefieldId()!=bf) continue;
                if(gear.keywords.has(Keyword::Deploy)){
                    auraMight(self,sid,1);
                    break;
                }
            }
        });
    }
private:
    const CardDef d_=[]{
        CardDef d;
        d.id=1004;d.def_id="rad-072-167";d.public_code="RAD-072/167";
        d.name="Overloaded Traveler";d.set_code="RAD";d.set_name="Radiance";
        d.collector_number=72;d.card_type=CardType::Unit;
        d.domains={Domain::Body};d.energy_cost=2;d.might=2;d.rarity=Rarity::Common;
        d.ability_text="While there's a friendly gear with [Deploy] at my battlefield, I have +1 [M].";
        return d;
    }();
};

class RadiancePartyCrasher final : public UnitCard {
public:
    const CardDef& def() const override {return d_;}
    int selfCostReduction(const GameState& state,PlayerId player) const override {
        int count=0;
        for(const auto& [id,u]:state.objects.onBoard())
            if(u.isUnit() && u.controller==player && u.location.has_value() &&
               u.is_exhausted)++count;
        return count;
    }
private:
    const CardDef d_=[]{
        CardDef d;
        d.id=1005;d.def_id="rad-122-167";d.public_code="RAD-122/167";
        d.name="Party Crasher";d.set_code="RAD";d.set_name="Radiance";
        d.collector_number=122;d.card_type=CardType::Unit;
        d.domains={Domain::Order};d.energy_cost=9;d.power_cost=1;d.might=6;
        d.rarity=Rarity::Common;d.keywords.set(Keyword::Tank);
        d.ability_text="I cost [1] less for each exhausted unit you control.\n[Tank] (I must be assigned combat damage first.)";
        return d;
    }();
};

class RadianceSteadfastOutrider final : public UnitCard {
public:
    const CardDef& def() const override{return d_;}
    void applyPassiveAura(GameState& state,PlayerId controller) const override {
        forEachSelfOnce(*this,state,controller,[&](GameObjectId sid,GameObject& self){
            if(!self.isAtBattlefield())return;
            const auto bf=self.battlefieldId();
            int allies=0;
            for(const auto& [id,obj]:state.objects.onBoard()){
                if(id==sid || obj.controller!=controller || !obj.location.has_value() ||
                   obj.battlefieldId()!=bf)continue;
                if(obj.isUnit()||obj.isGear())++allies;
            }
            if(allies>=2)auraMight(self,sid,2);
        });
    }
private:
    const CardDef d_=[]{
        CardDef d;
        d.id=1006;d.def_id="rad-128-167";d.public_code="RAD-128/167";
        d.name="Steadfast Outrider";d.set_code="RAD";d.set_name="Radiance";
        d.collector_number=128;d.card_type=CardType::Unit;
        d.domains={Domain::Order};d.energy_cost=4;d.might=3;
        d.rarity=Rarity::Uncommon;d.keywords.set(Keyword::Tank);
        d.ability_text="[Tank] (I must be assigned combat damage first.)\nWhile there are 2 or more other friendly units and/or gear at my battlefield, I have +2 [M].";
        return d;
    }();
};

class RadianceWatchfulCurator final : public UnitCard {
public:
    const CardDef& def() const override{return d_;}
    void applyPassiveAura(GameState& state,PlayerId controller) const override {
        forEachSelfOnce(*this,state,controller,[&](GameObjectId sid,GameObject& self){
            if(!self.location.has_value())return;
            for(auto& [id,gear]:state.objects.onBoard()){
                if(gear.controller!=controller || !gear.isGear() ||
                   !gear.location.has_value())continue;
                auraKeyword(gear,sid,Keyword::Deflect,1);
            }
        });
    }
private:
    const CardDef d_=[]{
        CardDef d;
        d.id=1007;d.def_id="rad-037-167";d.public_code="RAD-037/167";
        d.name="Watchful Curator";d.set_code="RAD";d.set_name="Radiance";
        d.collector_number=37;d.card_type=CardType::Unit;
        d.domains={Domain::Calm};d.energy_cost=3;d.power_cost=1;d.might=4;
        d.rarity=Rarity::Uncommon;
        d.ability_text="Your gear have [Deflect]. (Opponents must pay [A] to choose each with a spell or ability.)";
        return d;
    }();
};

class RadianceSneakyZeebles final : public UnitCard {
public:
    const CardDef& def() const override {return d_;}
    TriggerType triggerType() const override {return TriggerType::WhenIConquer;}
    // [Add] abilities cannot be reacted to (CR 430.2).
    bool triggeredAbilityAdds(TriggerType t) const override {return t==TriggerType::WhenIConquer;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&) override {
        ctx.executor.addFloatingUniversalPower(ctx.controller,1);
    }
private:
    const CardDef d_=[]{
        CardDef d;
        d.id=1008;d.def_id="rad-076-167";d.public_code="RAD-076/167";
        d.name="Sneaky Zeebles";d.set_code="RAD";d.set_name="Radiance";
        d.collector_number=76;d.card_type=CardType::Unit;
        d.domains={Domain::Body};d.energy_cost=2;d.might=1;
        d.rarity=Rarity::Common;
        d.ability_text="When I conquer, [Add] [A]. (Abilities that add resources can't be reacted to.)";
        return d;
    }();
};

class RadianceForDemacia final : public SpellCard {
public:
    const CardDef& def() const override {return d_;}
    unsigned choicesAtFinalization() const override{return kFinalizeResolve;}
    FinalizeChoice mayChooseAtFinalization(const GameState&,PlayerId,GameObjectId) const override {
        return FinalizeChoice::No; // battlefield is the chosen object, not a unit
    }
    void onResolve(CardContext& ctx,const std::vector<GameObjectId>&) override {
        const int mode=pickBattlefield(*this,ctx,"For Demacia!: choose battlefield");
        if(mode==-1)return;             // waiting for decision
        if(finalizingChoices(ctx))return;
        if(mode<0 || static_cast<size_t>(mode)>=ctx.state.battlefields.size())return;
        const auto bf=ctx.state.battlefields[static_cast<size_t>(mode)].id;
        for(const auto& [id,u]:ctx.state.objects.onBoard()){
            if(!u.isUnit() || u.controller!=ctx.controller ||
               u.battlefieldId()!=std::optional<BattlefieldId>{bf})continue;
            ctx.executor.giveTemporaryKeyword(id,Keyword::Shield,2);
        }
    }
private:
    const CardDef d_=[]{
        CardDef d;
        d.id=1009;d.def_id="rad-117-167";d.public_code="RAD-117/167";
        d.name="For Demacia!";d.set_code="RAD";d.set_name="Radiance";
        d.collector_number=117;d.card_type=CardType::Spell;
        d.domains={Domain::Order};d.energy_cost=3;d.rarity=Rarity::Common;
        d.keywords.set(Keyword::Reaction);
        d.ability_text="[Reaction] (Play any time, even before spells and abilities resolve.)\\nChoose a battlefield. Give friendly units there [Shield 2] this turn.";
        return d;
    }();
};

class RadianceAnOfferYouCantRefuse final : public SpellCard {
public:
    const CardDef& def() const override{return d_;}
    unsigned choicesAtFinalization() const override{return kFinalizeResolve;}
    bool hasLegalTargets(const GameState& state,PlayerId controller) const override {
        for(const auto& [id,g]:state.objects.onBoard())
            if(g.isGear() && g.location.has_value() &&
               (g.controller==controller || !g.untargetable_by_enemy))return true;
        return false;
    }
    void onResolve(CardContext& ctx,const std::vector<GameObjectId>&) override {
        std::vector<GameObjectId> options;
        for(const auto& [id,g]:ctx.state.objects.onBoard())
            if(g.isGear() && g.location.has_value() &&
               (g.controller==ctx.controller || !g.untargetable_by_enemy))
                options.push_back(id);
        std::sort(options.begin(),options.end());
        const auto chosen=pickTarget(ctx,"An Offer You Can't Refuse: kill a gear",options);
        if(finalizingChoices(ctx))return;
        if(chosen==kInvalidId || !ctx.state.objectExists(chosen))return;
        const auto beneficiary=ctx.state.getObject(chosen).controller;
        ctx.executor.killObject(chosen);
        // An actual token tied to the pinned engine Gold card definition:
        // enters exhausted; its own reaction is registered on token card 326.
        ctx.executor.createToken(beneficiary,CardType::Gear,"Gold",0,{},
             KeywordSet{},LocationId{BaseLocation{beneficiary}},false,{},
             kGoldGearCardDefId,/*enters_exhausted=*/true);
    }
private:
    const CardDef d_=[]{
        CardDef d;
        d.id=1010;d.def_id="rad-101-167";d.public_code="RAD-101/167";
        d.name="An Offer You Can't Refuse";d.set_code="RAD";d.set_name="Radiance";
        d.collector_number=101;d.card_type=CardType::Spell;
        d.domains={Domain::Chaos};d.energy_cost=2;d.rarity=Rarity::Uncommon;
        d.keywords.set(Keyword::Action);
        d.ability_text="[Action] (Play on your turn or in showdowns.)\\nKill a gear. Its controller plays a Gold gear token exhausted.";
        return d;
    }();
};

} // namespace
void register_card_1001(CardRegistry& r){r.registerCard(1001,std::make_unique<RadianceRiptideMage>());}
void register_card_1002(CardRegistry& r){r.registerCard(1002,std::make_unique<RadianceHighNote>());}
void register_card_1003(CardRegistry& r){r.registerCard(1003,std::make_unique<RadianceNazumanNtofo>());}
void register_card_1004(CardRegistry& r){r.registerCard(1004,std::make_unique<RadianceOverloadedTraveler>());}
void register_card_1005(CardRegistry& r){r.registerCard(1005,std::make_unique<RadiancePartyCrasher>());}
void register_card_1006(CardRegistry& r){r.registerCard(1006,std::make_unique<RadianceSteadfastOutrider>());}
void register_card_1007(CardRegistry& r){r.registerCard(1007,std::make_unique<RadianceWatchfulCurator>());}
void register_card_1008(CardRegistry& r){r.registerCard(1008,std::make_unique<RadianceSneakyZeebles>());}
void register_card_1009(CardRegistry& r){r.registerCard(1009,std::make_unique<RadianceForDemacia>());}
void register_card_1010(CardRegistry& r){r.registerCard(1010,std::make_unique<RadianceAnOfferYouCantRefuse>());}
} // namespace riftbound
