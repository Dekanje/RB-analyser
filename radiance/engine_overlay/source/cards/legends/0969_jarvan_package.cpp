#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include "engine/resource_payment.h"
#include <memory>
#include <vector>
#include <algorithm>
namespace riftbound {
namespace {
std::vector<GameObjectId> friendlyUnits(const GameState& s, PlayerId p) {
    std::vector<GameObjectId> ids;
    for (const auto& [id,o]:s.objects.onBoard())
        if(o.isUnit() && o.location && o.controller==p) ids.push_back(id);
    std::sort(ids.begin(),ids.end()); return ids;
}
class ExemplarOfDemacia final:public LegendCard {
 public:
  const CardDef& def()const override{return d_;}
  unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
  TriggerType triggerType()const override{return TriggerType::WhenYouPlayAGear;}
  bool triggerCondition(const GameState& s,GameObjectId source,PlayerId p,
                        TriggerType,GameObjectId subject)const override {
    if(!s.objectExists(source)||!s.objectExists(subject))return false;
    const auto& legend=s.getObject(source);const auto& gear=s.getObject(subject);
    return !legend.is_exhausted && gear.isGear() && gear.controller==p &&
      gear.hasKeyword(Keyword::Deploy) && gear.battlefieldId().has_value() &&
      !friendlyUnits(s,p).empty() &&
      resource::canPay(s,p,0,1,Domain::Count);
  }
  void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
    if(!ctx.state.chain.resuming)return;
    auto subject=ctx.state.chain.resuming->triggering_subject;
    if(!ctx.state.objectExists(subject))return;
    auto bf=ctx.state.getObject(subject).battlefieldId();
    if(!bf)return;
    auto legal=friendlyUnits(ctx.state,ctx.controller);
    int conf=confirmOptional(ctx,"Jarvan IV: pay [A] and exhaust to move a friendly unit?",
       [&](){return !legal.empty() && ctx.state.objectExists(ctx.source) &&
                    !ctx.state.getObject(ctx.source).is_exhausted &&
                    resource::canPay(ctx.state,ctx.controller,0,1,Domain::Count);});
    if(conf<=0)return;
    auto unit=pickTarget(ctx,"Jarvan IV: choose friendly unit to move",legal);
    if(unit==kInvalidId)return;
    bool paid=true;
    if(costDueNow(ctx)){
       paid=ctx.executor.payAnyPower(ctx.controller,1);
       if(paid)ctx.executor.exhaustObject(ctx.source);
    }
    if(finalizingChoices(ctx)||!paid||costUnpaid(ctx))return;
    if(ctx.state.objectExists(unit))ctx.executor.moveToBattlefield(unit,*bf);
  }
 private:
  const CardDef d_=[]{
    CardDef d;d.id=969;d.def_id="rad-155-167";d.name="Exemplar of Demacia";
    d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-155/167";
    d.collector_number=155;d.card_type=CardType::Legend;d.rarity=Rarity::Rare;
    d.domains={Domain::Body,Domain::Order};d.tags={"Jarvan IV"};
    d.ability_text="When you play a gear with Deploy, you may exhaust me and pay [A] to move a friendly unit to that battlefield.";
    return d;
  }();
};
class RoyalHeir final:public UnitCard {
 public:
  const CardDef& def()const override{return d_;}
  TriggerType triggerType()const override{return TriggerType::WhenIAttack;}
  unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
  void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
    if(!ctx.state.objectExists(ctx.source))return;
    const auto bf=ctx.state.getObject(ctx.source).battlefieldId();
    if(!bf)return;
    auto units=friendlyUnits(ctx.state,ctx.controller);
    units.erase(std::remove(units.begin(),units.end(),ctx.source),units.end());
    int conf=confirmOptional(ctx,"Jarvan IV, Royal Heir: move another friendly unit here?",
       [&](){return !units.empty();});
    if(conf<=0)return;
    const auto unit=pickTarget(ctx,"Jarvan IV, Royal Heir: move unit",units);
    if(finalizingChoices(ctx)||unit==kInvalidId)return;
    if(ctx.state.objectExists(unit))ctx.executor.moveToBattlefield(unit,*bf);
  }
 private:
  const CardDef d_=[]{
    CardDef d;d.id=970;d.def_id="rad-133-167";d.name="Jarvan IV, Royal Heir";
    d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-133/167";
    d.collector_number=133;d.card_type=CardType::Unit;d.super_type=SuperType::Champion;
    d.domains={Domain::Order};d.tags={"Demacia","Jarvan IV"};
    d.energy_cost=7;d.power_cost=1;d.might=7;d.rarity=Rarity::Rare;
    d.keywords.set(Keyword::Assault);d.assault_value=1;
    d.keywords.set(Keyword::Tank);
    d.ability_text="[Assault] [Tank] When I attack, you may move a unit you control to my battlefield.";
    return d;
  }();
};
class DemacianStandard final:public GearCard {
 public:
  const CardDef& def()const override{return d_;}
  std::vector<TriggerType> triggerTypes()const override{
    return {TriggerType::WhenIAttack,TriggerType::WhenIHold};
  }
  bool triggerCondition(const GameState& state,GameObjectId source,PlayerId controller,
                        TriggerType trigger,GameObjectId)const override{
    if(!state.objectExists(source))return false;
    const auto& gear=state.getObject(source);
    const auto bf=gear.battlefieldId();
    if(!bf||gear.controller!=controller)return false;
    if(trigger==TriggerType::WhenIHold)return true;
    if(trigger!=TriggerType::WhenIAttack)return false;
    for(const auto& [id,unit]:state.objects.onBoard())
      if(unit.isUnit()&&unit.controller==controller&&unit.battlefieldId() &&
         *unit.battlefieldId()==*bf &&
         unit.combat_designation==CombatDesignation::Attacker)return true;
    return false;
  }
  unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
  void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
    if(!ctx.state.objectExists(ctx.source)){finalizingChoices(ctx);return;}
    auto bf=ctx.state.getObject(ctx.source).battlefieldId();
    if(!bf){finalizingChoices(ctx);return;}
    if(ctx.firing_trigger==TriggerType::WhenIHold) {
       int ok=confirmOptional(ctx,"Demacian Standard: return to owner's hand?",
            [&](){return ctx.state.objectExists(ctx.source) &&
                       ctx.state.getObject(ctx.source).isAtBattlefield();});
       if(finalizingChoices(ctx)||ok<=0)return;
       ctx.executor.bounceToHand(ctx.source);
       return;
    }
    if(ctx.firing_trigger!=TriggerType::WhenIAttack){
      finalizingChoices(ctx);
      return;
    }
    std::vector<GameObjectId> attackers;
    for(const auto& [id,u]:ctx.state.objects.onBoard())
       if(u.isUnit()&&u.controller==ctx.controller&&u.battlefieldId() &&
          *u.battlefieldId()==*bf &&
          u.combat_designation==CombatDesignation::Attacker) attackers.push_back(id);
    const auto unit=pickTarget(ctx,"Demacian Standard: choose attacker for +2 Might",attackers);
    if(finalizingChoices(ctx)||unit==kInvalidId)return;
    ctx.executor.giveTemporaryMight(unit,2);
  }
 private:
  const CardDef d_=[]{
    CardDef d;d.id=971;d.def_id="rad-156-167";d.name="Demacian Standard";
    d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-156/167";
    d.collector_number=156;d.card_type=CardType::Gear;d.super_type=SuperType::Signature;
    d.domains={Domain::Body,Domain::Order};d.tags={"Device","Jarvan IV"};
    d.energy_cost=2;d.power_cost=1;d.rarity=Rarity::Epic;
    d.keywords.set(Keyword::Deploy);
    d.ability_text="[Deploy] When friendly units attack here, give one of them +2 Might this turn. When you hold here, you may return this to its owner's hand.";
    return d;
  }();
};
}
void register_card_969(CardRegistry& r){r.registerCard(969,std::make_unique<ExemplarOfDemacia>());}
void register_card_970(CardRegistry& r){r.registerCard(970,std::make_unique<RoyalHeir>());}
void register_card_971(CardRegistry& r){r.registerCard(971,std::make_unique<DemacianStandard>());}
} // namespace riftbound
