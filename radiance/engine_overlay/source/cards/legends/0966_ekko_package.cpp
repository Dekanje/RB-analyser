#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <vector>
#include <string>
namespace riftbound {
namespace {
class BoyWhoShatteredTime final : public LegendCard {
public:
 const CardDef& def()const override{return d_;}
 EmpowerSpec empowerSpec()const override{
  EmpowerSpec s;s.valid=true;s.cost={.exhaust=true,.energy=1};return s;
 }
 std::vector<ActivatedAbility> activatedAbilities()const override{
  return {{.cost={.exhaust=true,.disempower_self=true}},empowerAbility()};
 }
 void onActivate(CardContext& ctx,int index,const std::vector<GameObjectId>&)override{
  if(index==1){ctx.executor.empower(ctx.source);return;}
  auto& ps=ctx.state.player(ctx.controller);
  PlayerState::CostModifier modifier;
  modifier.source=ctx.source;
  modifier.energy_reduction=2;
  modifier.power_reduction=1;
  modifier.next_unit_only=true;
  modifier.units_only=true;
  modifier.this_turn_only=true;
  ps.cost_modifiers.push_back(modifier);
  auto& obj=ctx.state.getObject(ctx.source);
  obj.card_counters["__ekko_next_unit"]=ctx.state.turn.turn_number;
 }
 TriggerType triggerType()const override{return TriggerType::WhenYouPlayAUnit;}
 bool triggerCondition(const GameState& state,GameObjectId source,PlayerId controller,
                       TriggerType,GameObjectId subject)const override{
  if(!state.objectExists(source)||!state.objectExists(subject))return false;
  const auto& src=state.getObject(source);
  const auto it=src.card_counters.find("__ekko_next_unit");
  return it!=src.card_counters.end()&&it->second==state.turn.turn_number &&
         state.getObject(subject).controller==controller;
 }
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
  if(!ctx.state.chain.resuming)return;
  const auto unit=ctx.state.chain.resuming->triggering_subject;
  if(unit==kInvalidId||!ctx.state.objectExists(unit))return;
  auto& src=ctx.state.getObject(ctx.source);
  const auto it=src.card_counters.find("__ekko_next_unit");
  if(it==src.card_counters.end()||it->second!=ctx.state.turn.turn_number)return;
  src.card_counters.erase("__ekko_next_unit");
  DelayedAbility d;
  d.source=ctx.source;d.card_def_id=cardDefId();d.controller=ctx.controller;
  d.trigger=TriggerType::AtEndOfTurn;d.subject=unit;
  d.expires_on_turn=ctx.state.turn.turn_number;
  ctx.state.delayed_abilities.push_back(d);
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=966;d.def_id="rad-139-167";d.name="Boy Who Shattered Time";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-139/167";
  d.collector_number=139;d.card_type=CardType::Legend;d.rarity=Rarity::Rare;
  d.domains={Domain::Fury,Domain::Mind};d.tags={"Ekko"};d.champion_tag="Ekko";
  d.ability_text="[Empower] [1], [E]. Disempower me, [E]: Reduce the next unit you play this turn by [2][A] and give it 'Kill me at end of turn.'";
  return d;
 }();
};
class EkkoRevolutionary final:public UnitCard{
public:
 const CardDef& def()const override{return d_;}
 bool entersReadyOnPlay()const override{return true;}
 bool hasActivatedAbility()const override{return true;}
 bool isActionAbility()const override{return true;}
 ActivationCost getActivationCost()const override{
  ActivationCost c;c.discard=true;c.discard_count=1;c.energy=1;c.power=1;
  c.power_domain=Domain::Fury;c.banish_self=true;return c;
 }
 void onActivate(CardContext& ctx,const std::vector<GameObjectId>&)override{
  if(!ctx.state.objectExists(ctx.source))return;
  // This self-banish was paid as the ability's activation cost.
  auto& obj=ctx.state.getObject(ctx.source);
  if(obj.zone!=ZoneType::Banishment)return;
  ctx.executor.playIgnoringCost(obj.owner,ctx.source,LocationId{BaseLocation{obj.owner}});
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=967;d.def_id="rad-021-167";d.name="Ekko, Revolutionary";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-021/167";
  d.collector_number=21;d.card_type=CardType::Unit;d.super_type=SuperType::Champion;
  d.domains={Domain::Fury};d.tags={"Ekko","Zaun"};d.rarity=Rarity::Epic;
  d.energy_cost=5;d.power_cost=1;d.might=4;
  d.keywords.set(Keyword::Assault);d.assault_value=1;
  d.ability_text="I enter ready. [Assault]. [Action] Discard 1, [1][R]: Banish me then play me to your base ignoring cost.";
  return d;
 }();
};
class Chronobreak final:public SpellCard{
public:
 const CardDef& def()const override{return d_;}
 AdditionalPlayCost additionalPlayCost(const GameState&,const CardDB&,PlayerId,GameObjectId)const override{
  AdditionalPlayCost a;a.exists=true;a.mandatory=true;a.payable=true;return a;
 }
 PlayCostAdjust payAdditionalPlayCost(CardContext& ctx,
     const std::function<bool(const PlayCostAdjust&)>&)override{
  int available=0;
  for(const auto& [id,u]:ctx.state.objects.onBoard())
   if(u.isUnit()&&u.controller==ctx.controller&&u.location)++available;
  const int max=ctx.executor.maxPayableAnyPower(ctx.controller,std::min(available,16));
  std::vector<std::pair<int,std::string>> options;
  for(int i=0;i<=max;i++)options.emplace_back(i,"Pay "+std::to_string(i)+" Power");
  const int chosen=ctx.executor.chooseAmongNow(ctx.controller,options,"Chronobreak: additional Power cost");
  if(chosen>0&&!ctx.executor.payAnyPower(ctx.controller,chosen))return {};
  ctx.state.getObject(ctx.source).card_counters["__chronobreak_power"]=chosen;
  return {};
 }
 void onResolve(CardContext& ctx,const std::vector<GameObjectId>&)override{
  auto& self=ctx.state.getObject(ctx.source);
  const auto it=self.card_counters.find("__chronobreak_power");
  const int count=it==self.card_counters.end()?0:it->second;
  self.card_counters.erase("__chronobreak_power");
  struct Chosen {GameObjectId id;PlayerId owner;LocationId previous;};
  std::vector<Chosen> selected;
  for(int i=0;i<count;i++){
   std::vector<GameObjectId> eligible;
   for(const auto& [id,u]:ctx.state.objects.onBoard()) {
    if(!u.isUnit()||u.controller!=ctx.controller||!u.location)continue;
    if(std::any_of(selected.begin(),selected.end(),
                  [&](const Chosen& x){return x.id==id;}))continue;
    eligible.push_back(id);
   }
   if(eligible.empty())return;
   const auto id=ctx.executor.chooseObjectNow(ctx.controller,eligible,
      "Chronobreak: choose unit to banish and replay");
   if(id==kInvalidId||!ctx.state.objectExists(id))return;
   const auto& obj=ctx.state.getObject(id);
   selected.push_back({id,obj.owner,*obj.location});
  }
  // All selected units are banished before the first is played back.
  for(const auto& x:selected)if(ctx.state.objectExists(x.id))
    ctx.executor.banishObject(x.id);
  for(const auto& x:selected){
   if(!ctx.state.objectExists(x.id))continue;
   const LocationId base=BaseLocation{x.owner};
   LocationId place=base;
   if(x.previous!=base && ctx.executor.unitMayBePlayedTo(x.owner,x.previous)){
    const int which=ctx.executor.chooseValueNow(ctx.controller,
      {"Return to same location","Play to owner's base"},
      "Chronobreak: choose new location");
    if(which==0)place=x.previous;
   }
   ctx.executor.playIgnoringCost(x.owner,x.id,place);
  }
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=968;d.def_id="rad-140-167";d.name="Chronobreak";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-140/167";
  d.collector_number=140;d.card_type=CardType::Spell;d.super_type=SuperType::Signature;
  d.domains={Domain::Fury,Domain::Mind};d.tags={"Ekko"};d.rarity=Rarity::Epic;
  d.energy_cost=2;
  d.ability_text="As an additional cost, pay any amount of Power. Banish that many units you control, then each owner plays them back to the same location or base, ignoring cost.";
  return d;
 }();
};
}
void register_card_966(CardRegistry& r){r.registerCard(966,std::make_unique<BoyWhoShatteredTime>());}
void register_card_967(CardRegistry& r){r.registerCard(967,std::make_unique<EkkoRevolutionary>());}
void register_card_968(CardRegistry& r){r.registerCard(968,std::make_unique<Chronobreak>());}
} // namespace riftbound
