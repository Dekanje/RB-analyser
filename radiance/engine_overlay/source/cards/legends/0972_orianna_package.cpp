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
std::vector<GameObjectId> ownGears(const GameState& s,PlayerId p){
 std::vector<GameObjectId> r;
 for(const auto& [id,o]:s.objects.onBoard())
  if(o.isGear()&&o.controller==p&&o.location)r.push_back(id);
 std::sort(r.begin(),r.end());return r;
}
class LadyOfClockwork final:public LegendCard {
public:
 const CardDef& def()const override{return d_;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 TriggerType triggerType()const override{return TriggerType::AtStartOfMain;}
 bool triggerCondition(const GameState& s,GameObjectId source,PlayerId p,
                       TriggerType,GameObjectId)const override{
  return s.objectExists(source)&&!ownGears(s,p).empty()&&
    resource::canPay(s,p,1,0,Domain::Count);
 }
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
  auto gear=ownGears(ctx.state,ctx.controller);
  const int yes=confirmOptional(ctx,"Orianna: pay [1] to turn a gear into a unit gear?",
    [&](){return !gear.empty()&&resource::canPay(ctx.state,ctx.controller,1,0,Domain::Count);});
  if(yes<=0)return;
  const auto chosen=pickTarget(ctx,"Orianna: choose friendly gear",gear);
  if(chosen==kInvalidId)return;
  bool paid=true;
  if(costDueNow(ctx))paid=ctx.executor.payResources(ctx.controller,1,0,resource::kAnyDomain);
  if(finalizingChoices(ctx)||!paid||costUnpaid(ctx))return;
  if(!ctx.state.objectExists(chosen))return;
  auto& legend=ctx.state.getObject(ctx.source);
  if(legend.radiance_selected_gear.has_value()){
   auto old=*legend.radiance_selected_gear;
   if(old!=chosen&&ctx.state.objectExists(old)){
    auto& previous=ctx.state.getObject(old);
    previous.radiance_unit_gear=false;
    previous.base_might=0;
    previous.recomputeMight();
   }
  }
  auto& current=ctx.state.getObject(chosen);
  if(!current.isGear()||current.controller!=ctx.controller||!current.location)return;
  current.radiance_unit_gear=true;
  current.base_might=ctx.executor.cardDB().get(current.card_def_id).energy_cost;
  current.recomputeMight();
  legend.radiance_selected_gear=chosen;
  ctx.executor.recalculateContinuousEffects();
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=972;d.def_id="rad-145-167";d.name="Lady of Clockwork";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-145/167";
  d.collector_number=145;d.card_type=CardType::Legend;
  d.domains={Domain::Calm,Domain::Mind};d.tags={"Orianna"};d.rarity=Rarity::Rare;
  d.ability_text="At the start of your Main Phase, you may pay [1] to choose a friendly gear. It becomes a unit gear with Might equal to its Energy cost until you choose another gear with me.";
  return d;
 }();
};
class OriannaExquisite final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
 void applyPassiveAura(GameState& s,PlayerId p)const override{
  for(auto& [id,unit]:s.objects.onBoard()){
   if(unit.card_def_id!=CardDefId::fromRaw(973)||unit.controller!=p||!unit.isUnit())continue;
   auto bf=unit.battlefieldId();if(!bf)continue;
   bool gear_here=false;
   for(const auto& [gid,g]:s.objects.onBoard()){
    if(g.isGear()&&g.controller==p&&g.battlefieldId()&&*g.battlefieldId()==*bf){
       gear_here=true;break;
    }
   }
   if(!gear_here)unit.aura_no_combat_damage=true;
  }
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=973;d.def_id="rad-042-167";d.name="Orianna, Exquisite";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-042/167";
  d.collector_number=42;d.card_type=CardType::Unit;d.super_type=SuperType::Champion;
  d.energy_cost=3;d.might=4;d.domains={Domain::Calm};
  d.tags={"Orianna"};d.rarity=Rarity::Rare;
  d.keywords.set(Keyword::Shield);d.shield_value=1;
  d.ability_text="[Shield]. I don't deal combat damage unless there's a friendly gear here.";
  return d;
 }();
};
class TheBall final:public GearCard {
public:
 const CardDef& def()const override{return d_;}
 std::vector<TriggerType> triggerTypes()const override{
  return {TriggerType::WhenYouPlayMe,TriggerType::WhenIMove};
 }
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
  const int mode=pickMode(ctx,"The Ball: choose effect",2,
         {"Draw 1","Deal 2 damage to each enemy unit here"});
  if(mode<0||finalizingChoices(ctx))return;
  if(mode==0){ctx.executor.drawCards(ctx.controller,1);return;}
  if(!ctx.state.objectExists(ctx.source))return;
  auto bf=ctx.state.getObject(ctx.source).battlefieldId();
  if(!bf)return;
  std::vector<GameObjectId> targets;
  for(const auto& [id,o]:ctx.state.objects.onBoard()){
    if(o.isUnit()&&o.controller!=ctx.controller&&o.battlefieldId()&&*o.battlefieldId()==*bf)
      targets.push_back(id);
  }
  for(auto id:targets)ctx.executor.dealDamage(id,2,ctx.source);
  ctx.executor.killLethallyDamagedTogether(targets);
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=974;d.def_id="rad-146-167";d.name="The Ball";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-146/167";
  d.collector_number=146;d.card_type=CardType::Gear;d.super_type=SuperType::Signature;
  d.energy_cost=5;d.power_cost=1;d.domains={Domain::Calm,Domain::Mind};
  d.tags={"Device","Orianna"};d.rarity=Rarity::Epic;
  d.keywords.set(Keyword::Deploy);d.keywords.set(Keyword::Ganking);
  d.ability_text="[Deploy] [Ganking] While a unit, this can move between battlefields. When you play or move this, choose one: draw 1 or deal 2 to enemy units here.";
  return d;
 }();
};
}
void register_card_972(CardRegistry& r){r.registerCard(972,std::make_unique<LadyOfClockwork>());}
void register_card_973(CardRegistry& r){r.registerCard(973,std::make_unique<OriannaExquisite>());}
void register_card_974(CardRegistry& r){r.registerCard(974,std::make_unique<TheBall>());}
} // namespace riftbound
