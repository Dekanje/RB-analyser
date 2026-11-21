#include "cards/card.h"
#include "cards/card_registry.h"
#include "cards/card_helpers.h"
#include "core/game_state.h"
#include "core/events.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
#include <string>
#include <algorithm>
namespace riftbound {
namespace {
class StarryEyedSongstress final:public LegendCard {
public:
 const CardDef& def()const override{return d_;}
private:
 const CardDef d_=[]{
  CardDef d;d.id=975;d.def_id="rad-151-167";d.name="Starry-Eyed Songstress";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-151/167";
  d.collector_number=151;d.card_type=CardType::Legend;
  d.domains={Domain::Mind,Domain::Order};d.tags={"Seraphine"};d.champion_tag="Seraphine";
  d.rarity=Rarity::Rare;
  d.ability_text="As an additional cost to play a spell, you may exhaust me and three friendly units to reduce its cost by [2].";
  return d;
 }();
};
class SeraphineInspiring final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
 std::vector<TriggerType> triggerTypes()const override{
  return {TriggerType::WhenIAttack,TriggerType::WhenThreeFriendsExhausted};
 }
 bool firstTimeEachTurn(TriggerType t)const override {
  return t==TriggerType::WhenThreeFriendsExhausted;
 }
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override {
  const int answer=confirmOptional(ctx,
    "Seraphine, Inspiring: draw 1 for exhausting at least three friendly units?",
    [](){return true;});
  if(answer<1||finalizingChoices(ctx))return;
  ctx.executor.drawCards(ctx.controller,1);
 }
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
private:
 const CardDef d_=[]{
  CardDef d;d.id=976;d.def_id="rad-065-167";d.name="Seraphine, Inspiring";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-065/167";
  d.collector_number=65;d.card_type=CardType::Unit;d.super_type=SuperType::Champion;
  d.domains={Domain::Mind};d.tags={"Piltover","Seraphine"};
  d.energy_cost=4;d.power_cost=1;d.might=3;d.rarity=Rarity::Rare;
  d.ability_text="[Disarm 2]. Once each turn, when you exhaust three or more friendly units at the same time, you may draw 1.";
  return d;
 }();
};
class Encore final:public SpellCard{
public:
 const CardDef& def()const override{return d_;}
 unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
 FinalizeChoice mayChooseAtFinalization(const GameState&,PlayerId,GameObjectId)const override{
  return FinalizeChoice::No;
 }
 void onResolve(CardContext& ctx,const std::vector<GameObjectId>&)override {
  static const std::vector<std::string> labels={
   "Damage + Recruit","Damage + Might","Damage + Draw",
   "Recruit + Damage","Recruit + Might","Recruit + Draw",
   "Might + Damage","Might + Recruit","Might + Draw",
   "Draw + Damage","Draw + Recruit","Draw + Might"
  };
  const int choice=pickMode(ctx,"Encore: choose two different effects, in order",12,labels);
  if(choice<0||finalizingChoices(ctx))return;
  int a=choice/3,b=choice%3;
  if(b>=a)++b;
  for(int action:{a,b}){
   if(action==0){
    std::vector<GameObjectId> units;
    for(const auto& [id,u]:ctx.state.objects.onBoard())
     if(u.isUnit()&&u.location)units.push_back(id);
    if(units.empty())continue;
    const auto target=ctx.executor.chooseObjectNow(ctx.controller,units,
       "Encore: choose a unit to deal 2 to");
    if(target!=kInvalidId&&ctx.state.objectExists(target)){
      ctx.executor.dealDamage(target,2,ctx.source);
      ctx.executor.killLethallyDamagedTogether({target});
    }
   }else if(action==1){
    for(int n=0;n<2;n++){
     std::vector<LocationId> locs{BaseLocation{ctx.controller}};
     for(const auto& bf:ctx.state.battlefields)
      if(bf.controller.has_value()&&*bf.controller==ctx.controller)
       locs.push_back(BattlefieldLocation{bf.id});
     auto where=ctx.executor.chooseLocationNow(ctx.controller,locs,
       "Encore: play 1 Might Recruit");
     KeywordSet kw;
     ctx.executor.createToken(ctx.controller,CardType::Unit,"Recruit",1,
       {"Recruit"},kw,where,true);
    }
   }else if(action==2){
    std::vector<GameObjectId> candidates;
    for(const auto& [id,u]:ctx.state.objects.onBoard())
     if(u.isUnit()&&u.location)candidates.push_back(id);
    for(int k=0;k<2 && !candidates.empty();k++){
     auto unit=ctx.executor.chooseObjectNow(ctx.controller,candidates,
       "Encore: choose a unit for +1 Might");
     if(unit==kInvalidId)break;
     ctx.executor.giveTemporaryMight(unit,1);
     candidates.erase(std::remove(candidates.begin(),candidates.end(),unit),candidates.end());
    }
   }else if(action==3){
    auto& ps=ctx.state.player(ctx.controller);
    const int n=std::min<int>(2,ps.main_deck.size());
    if(n==0)continue;
    if(n==1){ctx.executor.drawCards(ctx.controller,1);continue;}
    std::vector<GameObjectId> top;
    for(int i=0;i<n;++i){
     auto id=ps.main_deck[ps.main_deck.size()-1-i];
     top.push_back(id);
     const auto& obj=ctx.state.getObject(id);
     ctx.events.emit(CardRevealedEvent{id,obj.card_def_id,obj.owner,false,
                                       ctx.controller,ZoneType::MainDeck});
    }
    auto draw=ctx.executor.chooseObjectNow(ctx.controller,top,
       "Encore: choose which of the top 2 cards to draw");
    if(draw==kInvalidId)draw=top.front();
    for(auto id:top)
     deck::take(ctx.state,id,deck::Place::Held,knowledge::only(ctx.controller),false);
    ctx.executor.drawHeldCard(ctx.controller,draw,false);
    for(auto id:top)if(id!=draw)ctx.executor.recycleCards(ctx.controller,{id});
   }
  }
 }
private:
 const CardDef d_=[]{
  CardDef d;d.id=977;d.def_id="rad-152-167";d.name="Encore";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-152/167";
  d.collector_number=152;d.card_type=CardType::Spell;d.super_type=SuperType::Signature;
  d.energy_cost=3;d.power_cost=1;
  d.domains={Domain::Mind,Domain::Order};d.tags={"Seraphine"};d.rarity=Rarity::Epic;
  d.ability_text="Choose two: Deal 2 to a unit; play two 1 Might Recruit tokens; give up to two units +1 Might this turn; look at top 2 Main Deck cards, draw one and recycle the other.";
  return d;
 }();
};
}
void register_card_975(CardRegistry& r){r.registerCard(975,std::make_unique<StarryEyedSongstress>());}
void register_card_976(CardRegistry& r){r.registerCard(976,std::make_unique<SeraphineInspiring>());}
void register_card_977(CardRegistry& r){r.registerCard(977,std::make_unique<Encore>());}
} // namespace riftbound
