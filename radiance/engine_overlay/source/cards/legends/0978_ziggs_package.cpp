#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include "engine/resource_payment.h"
#include <algorithm>
#include <memory>
#include <vector>
namespace riftbound {
namespace {
std::vector<LocationId> allBattlefields(const GameState& s){
 std::vector<LocationId> b;for(const auto& x:s.battlefields)b.push_back(BattlefieldLocation{x.id});
 return b;
}
GameObjectId makeBomb(CardContext& ctx,LocationId where) {
 KeywordSet kw;kw.set(Keyword::Deploy);
 return ctx.executor.createToken(ctx.controller,CardType::Gear,"Bomb",0,{"Bomb"},kw,where,
                                  false,{},CardDefId{982});
}
class BombToken final:public GearCard {
public:
 const CardDef& def()const override{return d_;}
 TriggerType triggerType()const override{return TriggerType::WhenIDie;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
  if(!ctx.state.objectExists(ctx.source)){
   finalizingChoices(ctx);
   return;
  }
  const auto& bomb=ctx.state.getObject(ctx.source);
  // Last-known location is recorded at the kill (CR 383.2.c.3); tokens
  // may have no historical last_location after leaving the battlefield.
  const auto& old=bomb.last_known.valid && bomb.last_known.location
     ? bomb.last_known.location : bomb.last_location;
  if(!old||!std::holds_alternative<BattlefieldLocation>(*old)){
   finalizingChoices(ctx);
   return;
  }
  const auto bf=std::get<BattlefieldLocation>(*old).id;
  std::vector<GameObjectId> enemy,bombs;
  for(const auto& [id,c]:ctx.state.objects.onBoard()){
   if(!c.battlefieldId()||*c.battlefieldId()!=bf)continue;
   if(c.isUnit()&&c.controller!=ctx.controller)enemy.push_back(id);
   if(c.isGear()&&c.controller==ctx.controller&&c.name=="Bomb"&&id!=ctx.source)
     bombs.push_back(id);
  }
  GameObjectId target=kInvalidId;
  if(!enemy.empty())target=pickTarget(ctx,"Bomb: deal 2 to an enemy here",enemy);
  if(finalizingChoices(ctx))return;
  if(target!=kInvalidId&&ctx.state.objectExists(target)) {
    ctx.executor.dealDamage(target,2,ctx.source);
    ctx.executor.killLethallyDamagedTogether({target});
  }
  // Every other Bomb killed here gets its own death trigger. The chain handles
  // their triggered effects; no damage is suppressed or synthesized.
  for(auto id:bombs)
    if(ctx.state.objectExists(id)&&ctx.state.getObject(id).isAtBattlefield())
      ctx.executor.killObject(id);
 }
private:
 const CardDef d_=[] {
  CardDef d;d.id=982;d.def_id="rad-bomb-token";d.name="Bomb";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-TBomb";
  d.card_type=CardType::Gear;d.super_type=SuperType::Token;
  d.tags={"Bomb"};d.rarity=Rarity::Common;
  d.keywords.set(Keyword::Deploy);
  d.ability_text="[Deploy]. When this dies, deal 2 to an enemy unit here and kill your other Bombs here.";
  return d;
 }();
};
class HexplosivesExpert final:public LegendCard {
public:
 const CardDef& def()const override{return d_;}
 bool hasActivatedAbility()const override{return true;}
 ActivationCost getActivationCost()const override{
  return {.exhaust=true,.energy=1,.power=1,.power_any_domain=true};
 }
 void onActivate(CardContext& ctx,const std::vector<GameObjectId>&)override{
  const auto locs=allBattlefields(ctx.state);
  if(locs.empty())return;
  const auto bf=ctx.executor.chooseLocationNow(ctx.controller,locs,"Ziggs: play Bomb to battlefield");
  makeBomb(ctx,bf);
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=978;d.def_id="rad-141-167";d.name="Hexplosives Expert";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-141/167";
  d.collector_number=141;d.card_type=CardType::Legend;d.rarity=Rarity::Rare;
  d.domains={Domain::Fury,Domain::Chaos};d.tags={"Yordle","Ziggs"};
  d.champion_tag="Ziggs";
  d.ability_text="[1][A], [E]: Play a Bomb gear token to a battlefield.";
  return d;
 }();
};
class ZiggsShortFused final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
 TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
  auto locs=allBattlefields(ctx.state);if(locs.empty())return;
  makeBomb(ctx,ctx.executor.chooseLocationNow(ctx.controller,locs,
      "Ziggs, Short-Fused: play Bomb token"));
 }
 void applyPassiveAura(GameState& state,PlayerId p)const override{
  int count=0;
  for(const auto& [id,o]:state.objects.onBoard())
    if(o.card_def_id==CardDefId{979}&&o.controller==p&&o.isUnit()&&o.location)++count;
  state.player(p).radiance_gear_bonus_damage+=count;
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=979;d.def_id="rad-023-167";d.name="Ziggs, Short-Fused";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-023/167";
  d.collector_number=23;d.card_type=CardType::Unit;d.super_type=SuperType::Champion;
  d.energy_cost=5;d.power_cost=1;d.might=5;
  d.domains={Domain::Fury};d.tags={"Bandle City","Ziggs"};d.rarity=Rarity::Epic;
  d.ability_text="When you play me, play a Bomb gear token to a battlefield. Abilities of friendly gear deal 1 Bonus Damage.";
  return d;
 }();
};
class HexplosiveMinefield final:public SpellCard {
public:
 const CardDef& def()const override{return d_;}
 void onResolve(CardContext& ctx,const std::vector<GameObjectId>&)override{
  std::vector<GameObjectId> bombs;
  for(const auto& [id,obj]:ctx.state.objects.onBoard())
    if(obj.isGear()&&obj.controller==ctx.controller&&obj.name=="Bomb"&&obj.location)
       bombs.push_back(id);
  if(bombs.empty())return;
  std::vector<std::pair<int,std::string>> counts;
  for(int n=0;n<=static_cast<int>(bombs.size());++n)
     counts.emplace_back(n,"Kill "+std::to_string(n)+" Bomb tokens");
  const int count=ctx.executor.chooseAmongNow(ctx.controller,counts,
                                               "Hexplosive Minefield: how many Bombs?");
  std::vector<GameObjectId> chosen;
  for(int i=0;i<count&&!bombs.empty();++i){
   const auto id=ctx.executor.chooseObjectNow(ctx.controller,bombs,
                                               "Hexplosive Minefield: choose a Bomb");
   if(id==kInvalidId)break;
   auto it=std::find(bombs.begin(),bombs.end(),id);
   if(it==bombs.end())break;
   bombs.erase(it);chosen.push_back(id);
  }
  if(chosen.empty())return;
  const int amount=static_cast<int>(chosen.size());
  ctx.state.getObject(ctx.source).card_counters["__bombs_eot"]=amount;
  for(auto id:chosen)if(ctx.state.objectExists(id))ctx.executor.killObject(id);
  DelayedAbility da;da.source=ctx.source;da.card_def_id=cardDefId();
  da.controller=ctx.controller;da.trigger=TriggerType::AtEndOfTurn;
  da.expires_on_turn=ctx.state.turn.turn_number;
  ctx.state.delayed_abilities.push_back(da);
 }
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
  if(!ctx.state.objectExists(ctx.source))return;
  auto& source=ctx.state.getObject(ctx.source);
  const int count=source.card_counters["__bombs_eot"];
  source.card_counters.erase("__bombs_eot");
  if(count<=0)return;
  const auto locs=allBattlefields(ctx.state);if(locs.empty())return;
  const auto loc=ctx.executor.chooseLocationNow(ctx.controller,locs,
                                                "Hexplosive Minefield: all Bombs to battlefield");
  for(int i=0;i<count;++i)makeBomb(ctx,loc);
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=980;d.def_id="rad-142-167";d.name="Hexplosive Minefield";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-142/167";
  d.collector_number=142;d.card_type=CardType::Spell;d.super_type=SuperType::Signature;
  d.energy_cost=2;d.power_cost=1;d.rarity=Rarity::Epic;
  d.domains={Domain::Fury,Domain::Chaos};d.tags={"Ziggs"};
  d.keywords.set(Keyword::Action);
  d.ability_text="[Action] Kill any number of friendly Bomb tokens. At end of turn, play that many Bomb tokens to a single battlefield.";
  return d;
 }();
};
class RecklessInnovator final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
 TriggerType triggerType()const override{return TriggerType::WhenIAmExhausted;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override {
  const bool can_pay=resource::canPay(ctx.state,ctx.controller,0,1,Domain::Chaos);
  const int choice=pickMode(ctx,"Reckless Innovator: choose an exhaust effect",2,
      {"Play an exhausted Gold token","Pay [P] to draw 1"},can_pay?3u:1u);
  if(choice<0||finalizingChoices(ctx))return;
  if(choice==1) {
    if(ctx.executor.payResources(ctx.controller,0,1,resource::maskOf(Domain::Chaos)))
      ctx.executor.drawCards(ctx.controller,1);
  } else {
    KeywordSet kw;
    ctx.executor.createToken(ctx.controller,CardType::Gear,"Gold",0,{"Gold"},kw,
                             BaseLocation{ctx.controller},false,{},
                             CardDefId{326},true);
  }
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=981;d.def_id="rad-105-167";d.name="Reckless Innovator";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-105/167";
  d.collector_number=105;d.card_type=CardType::Unit;d.domains={Domain::Chaos};
  d.energy_cost=3;d.might=3;d.rarity=Rarity::Uncommon;
  d.keywords.set(Keyword::Accelerate);
  d.ability_text="[Accelerate] When I become exhausted, choose one: play an exhausted Gold gear token; pay [P] to draw 1.";
  return d;
 }();
};
}
void register_card_978(CardRegistry& r){r.registerCard(978,std::make_unique<HexplosivesExpert>());}
void register_card_979(CardRegistry& r){r.registerCard(979,std::make_unique<ZiggsShortFused>());}
void register_card_980(CardRegistry& r){r.registerCard(980,std::make_unique<HexplosiveMinefield>());}
void register_card_981(CardRegistry& r){r.registerCard(981,std::make_unique<RecklessInnovator>());}
void register_card_982(CardRegistry& r){r.registerCard(982,std::make_unique<BombToken>());}
} // namespace riftbound
