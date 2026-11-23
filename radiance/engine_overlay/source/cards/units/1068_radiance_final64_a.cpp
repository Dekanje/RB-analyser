// RAD final64 generated canonical printing definitions. Mechanical status: WORK IN PROGRESS.
// These classes must not be declared mechanics-accepted without per-card scenarios.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/units/radiance_final64_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <string>
#include <tuple>
#include <vector>

namespace riftbound {
namespace {
CardDef mkFinal64_a(int id,int num,const char* name,CardType type,int energy,int power,int might,
              std::vector<Domain> domains,Rarity rarity,const char* rules) {
 CardDef d;
 d.id=CardDefId::fromRaw(id);
 const auto n=std::to_string(num);
 d.def_id="rad-"+std::string(3-n.size(),'0')+n+"-167";
 d.public_code="RAD-"+std::string(3-n.size(),'0')+n+"/167";
 d.name=name;d.set_code="RAD";d.set_name="Radiance";d.collector_number=num;
 d.card_type=type;d.energy_cost=energy;d.power_cost=power;d.might=might;
 d.domains=std::move(domains);d.rarity=rarity;d.ability_text=rules;
 return d;
}

class R64_1068 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }

 unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
 static uint32_t candidateMask(const GameState& s){
   uint32_t mask=0;
   for(size_t i=0;i<s.battlefields.size()&&i<32;i++){
     for(const auto& [id,o]:s.objects.onBoard())
       if(o.isUnit()&&o.battlefieldId()==s.battlefields[i].id){
         mask|=1u<<i;break;
       }
   }
   return mask;
 }
 bool canBePlayed(const GameState& s,PlayerId)const override{
   return candidateMask(s)!=0;
 }
 FinalizeChoice mayChooseAtFinalization(const GameState& s,PlayerId,GameObjectId id)const override{
   if(!s.objectExists(id))return FinalizeChoice::No;
   const auto& o=s.getObject(id);
   return o.isUnit()&&o.isAtBattlefield()?FinalizeChoice::Yes:FinalizeChoice::No;
 }
 void onResolve(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source))return;
   auto& counters=c.state.getObject(c.source).card_counters;
   int selected=counters["__f64_scorched_bf"]-1;
   if(selected<0){
     std::vector<std::string> labels;
     for(const auto& bf:c.state.battlefields)
       labels.push_back("Scorched Earth at "+std::to_string(bf.id.raw()));
     selected=pickMode(c,"Scorched Earth: choose one battlefield",
                       static_cast<int>(labels.size()),labels,candidateMask(c.state));
     if(selected<0)return;
     counters["__f64_scorched_bf"]=selected+1;
   }
   if(static_cast<size_t>(selected)>=c.state.battlefields.size()){
     (void)finalizingChoices(c);return;
   }
   const auto bf=c.state.battlefields[selected].id;
   auto units=boardObjects(c.state,[&](const GameObject& o){
      return o.isUnit()&&o.isAtBattlefield()&&o.battlefieldId()==bf;
   });
   std::vector<GameObjectId> damaged;
   (void)splitDamageAmong(c,"Scorched Earth",5,c.source,units,damaged);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1068,6,R"RB(Scorched Earth)RB",CardType::Spell,4,1,0,{Domain::Fury},Rarity::Common,R"RB([Action] (Play on your turn or in showdowns.)
Deal 5 damage split among units at a single battlefield.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/e646f9850571e20eca22e07af5d4dd68813fdd19-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Action);
  return d;
 }();
};

class R64_1069 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }

 bool canBePlayed(const GameState& s,PlayerId)const override{
   for(const auto& [id,o]:s.objects.onBoard())if(o.isUnit()&&o.location)return true;
   return false;
 }
 FinalizeChoice mayChooseAtFinalization(const GameState& s,PlayerId,GameObjectId id)const override{
   if(!s.objectExists(id))return FinalizeChoice::No;
   const auto& o=s.getObject(id);
   return o.isUnit()&&o.location?FinalizeChoice::Yes:FinalizeChoice::No;
 }
 unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
 void onResolve(CardContext& c,const std::vector<GameObjectId>&)override{
   const auto units=boardObjects(c.state,[](const GameObject& o){return o.isUnit();});
   const auto chosen=pickTarget(c,"Forbidden Technique: ready a unit",units);
   if(finalizingChoices(c))return;
   if(chosen!=kInvalidId)c.executor.readyObject(chosen);
 }
 // MECHANICS_INCOMPLETE: expensive-play replay from trash and banishment.

private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1069,10,R"RB(Forbidden Technique)RB",CardType::Spell,2,0,0,{Domain::Fury},Rarity::Uncommon,R"RB(Ready a unit.
When you play a card with Energy cost [7] or more, you may play this from your trash for [1][F][F]. Banish this.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/293518dcf6c2f9e3f59a2e259826fd813436b3a5-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1070 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 void asYouPlayChoices(CardContext& c)override{
   (void)f64ShowOff(c,[](const GameObject& o,const CardDef& d){
     return d.hasTag("Mech")||std::find(o.tags.begin(),o.tags.end(),"Mech")!=o.tags.end();
   },"Incorrigible Construct: Show Off a Mech");
 }
 bool entersReadyOnPlay(const GameState& s,PlayerId,const GameObject& self)const override{
   return f64WasShownOff(s,self.id);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1070,11,R"RB(Incorrigible Construct)RB",CardType::Unit,4,0,4,{Domain::Fury},Rarity::Uncommon,R"RB([Show Off] a Mech. (As you play me, you may reveal a Mech from hand or pick another friendly Mech.)
I enter ready if you showed off.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/e95470d5c2fbc9f7f8ab0b1c19f32fd704918c83-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1071 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1071,12,R"RB(Runeblade Anvil)RB",CardType::Gear,1,0,0,{Domain::Fury},Rarity::Uncommon,R"RB(When you play this or when this leaves the board, banish the top card of your Main Deck. Until your next Ending Phase, you may play that card. (You still pay its costs.)
[2][F], [E]: Kill this.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/11e2ddea70ec4dd8e562681a1ab1dfbc2b2dca0f-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1072 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1072,15,R"RB(Akali, Brash)RB",CardType::Unit,5,1,5,{Domain::Fury},Rarity::Rare,R"RB(The first time I move each turn, [Add] [1][A].
The second time I move each turn, banish the top card of your Main Deck. Until your next Ending Phase, you may play that card. (You still pay its costs.))RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Ionia)RB",R"RB(Akali)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/20997ddaef2cd714c36e5473c156faf331b80b7b-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1073 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::AtEndOfTurn;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   const auto runes=boardObjects(c.state,[&](const GameObject& o){
     return o.isRune()&&o.controller==c.controller;
   });
   if(!runes.empty())c.executor.recycleCards(c.controller,runes);
   c.executor.channelRunes(c.controller,4,true);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1073,16,R"RB(Coalesced Energy)RB",CardType::Unit,4,2,4,{Domain::Fury},Rarity::Rare,R"RB(At the end of your turn, recycle all your runes, then channel 4 runes exhausted.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/59e551045ca75d932ff76c4820d873d4a2cde9e8-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1074 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   const auto owner=opponent(c.controller);
   const auto stolen=f64RevealTop(c,owner);
   if(stolen==kInvalidId)return;
   c.executor.banishObject(stolen,c.controller);
   if(!c.state.objectExists(stolen))return;
   const auto& card=c.state.getObject(stolen);
   std::optional<LocationId> place=std::nullopt;
   if(card.isUnit()||card.isGear()){
     const auto choices=playLocations(c.state,c.controller);
     if(!choices.locations.empty())
       place=c.executor.chooseLocationNow(c.controller,choices.locations,
             "Drakehound Packmaster: play banished opponent card");
   }
   (void)c.executor.playIgnoringCost(c.controller,stolen,place);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1074,18,R"RB(Drakehound Packmaster)RB",CardType::Unit,9,2,9,{Domain::Fury},Rarity::Rare,R"RB(When you play me, reveal the top card of each opponent's Main Deck. Choose one and banish it, then play it, ignoring its cost. Recycle the rest.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/9ddc2759cf8b039bc1ee77e32326c5475cc001e8-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1075 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 bool entersReadyOnPlay()const override{return true;}
 TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   std::vector<GameObjectId> enemies;
   for(const auto& [id,o]:c.state.objects.onBoard())
     if(o.isUnit()&&o.controller!=c.controller&&o.location)enemies.push_back(id);
   for(auto id:enemies)c.executor.readyObject(id);
 }
 // MECHANICS_INCOMPLETE: remaining continuous effect needs engine hook.

private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1075,19,R"RB(Firebrand Raider)RB",CardType::Unit,6,1,6,{Domain::Fury},Rarity::Rare,R"RB(I enter ready.
When you play me, ready all enemy units.
Other units enter ready.
Units don't ready during the Awaken Phase.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/922ef5a266378fa8ebd7e75bf83435bacd1a75d8-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1076 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }
 std::vector<ActivatedAbility> activatedAbilities()const override{
   ActivatedAbility gold;gold.cost.exhaust=true;
   ActivatedAbility recruit;recruit.cost.exhaust=true;
   ActivatedAbility mech;mech.cost.exhaust=true;mech.cost.kill_friendly_unit=true;
   return {gold,recruit,mech};
 }
 unsigned choicesAtFinalization()const override{return kFinalizeActivate;}
 static std::vector<GameObjectId> sacrificialGears(const GameState& s,PlayerId p,GameObjectId self){
   auto gears=f64Gears(s,p);
   gears.erase(std::remove(gears.begin(),gears.end(),self),gears.end());
   return gears;
 }
 bool canActivateAbilityAt(const GameState& s,PlayerId p,GameObjectId source,int index)const override{
   if(!GearCard::canActivateAbilityAt(s,p,source,index))return false;
   if(index==1)return !sacrificialGears(s,p,source).empty();
   if(index==2)return !f64Units(s,p).empty();
   return index==0;
 }
 void onActivate(CardContext& c,int index,const std::vector<GameObjectId>&)override{
   const LocationId atBase=BaseLocation{c.controller};
   if(index==0){
     if(finalizingChoices(c))return;
     c.executor.createToken(c.controller,CardType::Gear,"Gold",0,{"Gold"},
         KeywordSet{},atBase,false,{},CardDefId{326},true);
     return;
   }
   if(index==1){
     if(costAlreadyPaid(c)){
       if(finalizingChoices(c))return;
       f64Recruit(c,atBase,1);
       return;
     }
     auto gears=sacrificialGears(c.state,c.controller,c.source);
     std::sort(gears.begin(),gears.end());
     const auto sacrifice=pickTarget(c,"Whirling Twirligig: kill friendly gear as cost",gears);
     if(sacrifice!=kInvalidId&&costDueNow(c))c.executor.killObject(sacrifice);
     if(finalizingChoices(c))return;
     return;
   }
   if(index==2){
     if(finalizingChoices(c))return;
     f64Mech(c,atBase,3);
   }
 }
private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1076,22,R"RB(Whirling Twirligig)RB",CardType::Gear,4,1,0,{Domain::Fury},Rarity::Epic,R"RB([E]: Play a Gold gear token exhausted. (It has "[Reaction][>] Kill this, [E]: [Add] [A].")
Kill a friendly gear, [E]: Play a 1 [M] Recruit unit token.
Kill a friendly unit, [E]: Play a 3 [M] Mech unit token.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/a05ff95e5bb933664e09656973c72f4d39d8e701-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1077 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source)){(void)finalizingChoices(c);return;}
   const auto& self=c.state.getObject(c.source);
   if(!self.isAtBattlefield()){(void)finalizingChoices(c);return;}
   std::vector<GameObjectId> alternatives;
   for(const auto& [id,o]:c.state.objects.onBoard())
     if(id!=c.source&&o.isUnit()&&o.controller==c.controller&&o.isAtBattlefield()&&
        o.battlefieldId()==self.battlefieldId())alternatives.push_back(id);
   std::sort(alternatives.begin(),alternatives.end());
   const int yes=confirmOptional(c,"Stoic Ferryman: move another friendly unit here to base?",
      [&](){return !alternatives.empty();});
   if(yes<0)return;
   if(yes==0){(void)finalizingChoices(c);return;}
   const auto target=pickTarget(c,"Stoic Ferryman: friendly unit to base",alternatives);
   if(finalizingChoices(c))return;
   if(target!=kInvalidId)c.executor.moveToBase(target);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1077,31,R"RB(Stoic Ferryman)RB",CardType::Unit,4,0,2,{Domain::Calm},Rarity::Common,R"RB([Shield 3] (+3 [M] while I'm a defender.)
When you play me to a battlefield, you may move another unit you control here to your base.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/8513fbe02a37f957b2a98bcee5badfdc56f41e82-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Shield);
  d.shield_value=3;
  return d;
 }();
};

class R64_1078 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }
 unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
 static std::vector<GameObjectId> deployGears(const GameState& s,PlayerId p){
   auto gears=f64Gears(s,p);
   std::vector<GameObjectId> out;
   for(auto id:gears)if(s.objectExists(id)&&s.getObject(id).hasKeyword(Keyword::Deploy))out.push_back(id);
   return out;
 }
 static std::vector<GameObjectId> topFive(const CardContext& c){
   std::vector<GameObjectId> out;
   const auto& deck=c.state.player(c.controller).main_deck;
   for(auto it=deck.rbegin();it!=deck.rend()&&out.size()<5;++it)
     if(c.state.objectExists(*it))out.push_back(*it);
   return out;
 }
 static std::vector<GameObjectId> topGears(const CardContext& c){
   std::vector<GameObjectId> out;
   for(auto id:topFive(c))if(c.state.getObject(id).isGear())out.push_back(id);
   return out;
 }
 void onResolve(CardContext& c,const std::vector<GameObjectId>&)override{
   const auto gears=deployGears(c.state,c.controller);
   const uint32_t legal=gears.empty()?2u:3u;
   const int mode=pickMode(c,"Command: Attack",2,
     {"Move friendly Deploy gear to battlefield","Look at top five; reveal and draw gear"},legal);
   GameObjectId selected=kInvalidId;
   if(mode==0)selected=pickTarget(c,"Command: Attack: move Deploy gear",gears);
   if(finalizingChoices(c))return;
   if(mode==0){
     if(selected==kInvalidId||!c.state.objectExists(selected))return;
     std::vector<LocationId> destinations;
     for(const auto& bf:c.state.battlefields)
       if(c.state.getObject(selected).battlefieldId()!=bf.id)
         destinations.push_back(BattlefieldLocation{bf.id});
     if(destinations.empty())return;
     const auto where=c.executor.chooseLocationNow(c.controller,destinations,
       "Command: Attack: choose battlefield for gear");
     if(const auto* bf=std::get_if<BattlefieldLocation>(&where))
       c.executor.moveToBattlefield(selected,bf->id);
     return;
   }
   if(mode!=1)return;
   const auto& ri=c.state.chain.resuming;
   for(auto id:topFive(c))knowledge::shown(c.state,id,knowledge::only(c.controller));
   const int yes=confirmOptional(c,"Command: Attack: reveal and draw top-five gear?",[&]{
     return !topGears(c).empty();
   });
   if(yes==-1)return;
   const auto top=topFive(c);
   GameObjectId picked=kInvalidId;
   if(yes==1){
     picked=pickUnseenCard(c,"Command: Attack: choose gear to reveal",topGears(c));
     if(picked==kInvalidId&&ri.has_value()&&ri->resume_point==7)return;
   }
   std::vector<GameObjectId> rest;
   for(auto id:top){
     deck::take(c.state,id,deck::Place::Held,knowledge::only(c.controller),false);
     if(id!=picked)rest.push_back(id);
   }
   if(!rest.empty())c.executor.recycleCards(c.controller,rest);
   if(picked!=kInvalidId&&c.state.objectExists(picked)){
     const auto& o=c.state.getObject(picked);
     c.events.emit(CardRevealedEvent{picked,o.card_def_id,o.owner,
       true,c.controller,ZoneType::MainDeck});
     deck::putOnTop(c.state,c.controller,picked,deck::Place::Held,knowledge::everyone());
     c.executor.drawCards(c.controller,1);
   }
 }
private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1078,33,R"RB(Command: Attack)RB",CardType::Spell,1,1,0,{Domain::Calm},Rarity::Uncommon,R"RB(Choose one —Move a friendly gear with [Deploy] to a battlefield.
Look at the top 5 cards of your Main Deck. You may reveal a gear from among them and draw it. Recycle the rest.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/b025756992e22af480902e13b01e25acbc747221-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1079 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 TriggerType triggerType()const override{return TriggerType::WhenIBecomeExhausted;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source)){(void)finalizingChoices(c);return;}
   const auto& src=c.state.getObject(c.source);
   const auto& counts=src.card_counters;
   const int turn=static_cast<int>(c.state.turn.turn_number)+1;
   const auto it=counts.find("__riven43_turn");
   const int used=(it!=counts.end()&&it->second==turn)
      ?(counts.count("__riven43_mask")?counts.at("__riven43_mask"):0):0;
   uint32_t legal=0;
   if(!(used&1))legal|=1u;
   if(src.buff_count>0&&!(used&2))legal|=2u;
   if(src.buff_count>0&&!(used&4))legal|=4u;
   const auto enemies=boardObjects(c.state,[&](const GameObject& o){
      return o.isUnit()&&o.controller!=c.controller&&o.location;
   });
   if(enemies.empty())legal&=~2u;
   const int mode=pickMode(c,"Riven, Broken Blade: choose an unused mode",3,
       {"Buff me","Spend my buff to stun an enemy unit","Spend my buff to ready me"},legal);
   GameObjectId target=kInvalidId;
   if(mode==1)target=pickTarget(c,"Riven: stun enemy unit",enemies);
   if(finalizingChoices(c))return;
   if(mode<0||mode>=3)return;
   auto& obj=c.state.getObject(c.source);
   obj.card_counters["__riven43_turn"]=turn;
   obj.card_counters["__riven43_mask"]=used|(1<<mode);
   if(mode==0)c.executor.buffUnit(c.source);
   else if(obj.buff_count>0&&mode==1&&target!=kInvalidId&&
           c.executor.spendBuff(c.source,c.controller))
      c.executor.stunUnitBy(target,c.source);
   else if(obj.buff_count>0&&mode==2&&c.executor.spendBuff(c.source,c.controller))
      c.executor.readyObject(c.source);
 }
private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1079,43,R"RB(Riven, Broken Blade)RB",CardType::Unit,4,0,4,{Domain::Calm},Rarity::Rare,R"RB(When I become exhausted, choose one that hasn't been chosen this turn —[Buff] me. (Give me a +1 [M] buff if I don't have one.)Spend my buff to [Stun] an enemy unit. (It doesn't deal combat damage this turn.)Spend my buff to ready me.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Riven)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/0c9ac0da1c144f46a1e0c5423f51f9b8f6ba295b-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1080 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenYouPlayThis;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source)){(void)finalizingChoices(c);return;}
   const auto& self=c.state.getObject(c.source);
   if(!self.isAtBattlefield()){(void)finalizingChoices(c);return;}
   std::vector<GameObjectId> enemies;
   for(const auto& [id,o]:c.state.objects.onBoard())
     if(o.isUnit()&&o.controller!=c.controller&&o.location &&
        (!o.battlefieldId()||o.battlefieldId()!=self.battlefieldId()))
       enemies.push_back(id);
   std::sort(enemies.begin(),enemies.end());
   const int yes=confirmOptional(c,"Hunting Blind: move enemy here?",
      [&](){return !enemies.empty();});
   if(yes<0)return;
   if(yes==0){(void)finalizingChoices(c);return;}
   const auto target=pickTarget(c,"Hunting Blind: enemy unit to move",enemies);
   if(finalizingChoices(c))return;
   if(target!=kInvalidId)c.executor.moveToBattlefield(target,*self.battlefieldId());
 }
 void applyPassiveAura(GameState& s,PlayerId p)const override {
   forEachSelfOnce(*this,s,p,[&](GameObjectId source,GameObject& gear){
     if(!gear.isAtBattlefield())return;
     for(auto& [id,unit]:s.objects.onBoard())
       if(unit.isUnit()&&unit.controller==p&&unit.isAtBattlefield()&&
          unit.battlefieldId()==gear.battlefieldId())
         auraKeyword(unit,source,Keyword::Shield,2);
   });
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1080,44,R"RB(Hunting Blind)RB",CardType::Gear,4,2,0,{Domain::Calm},Rarity::Epic,R"RB([Deploy] (Play this only to a battlefield. When an opponent holds here, kill this.)
When you play this, you may move an enemy unit to this battlefield.
Friendly units here have [Shield 2]. (+2 [M] while they're defenders.))RB");
  d.tags={R"RB(Device)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/0a625c22d828c83302132b0465dceb3ab11a08bc-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Deploy);
  return d;
 }();
};

class R64_1081 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 TriggerType triggerType()const override{return TriggerType::WhenIAttackOrDefend;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source)||!c.state.getObject(c.source).isAtBattlefield()){
     (void)finalizingChoices(c);return;
   }
   const auto here=c.state.getObject(c.source).battlefieldId();
   auto friends=boardObjects(c.state,[&](const GameObject& o){
     return o.isUnit()&&o.controller==c.controller&&o.isAtBattlefield()&&o.battlefieldId()==here;
   });
   const auto selected=pickTarget(c,"K'Sante: double Shield of a friendly unit here",friends);
   if(finalizingChoices(c))return;
   if(selected==kInvalidId||!c.state.objectExists(selected))return;
   const int shield=c.state.getObject(selected).shield_value;
   if(shield>0)c.executor.giveTemporaryKeyword(selected,Keyword::Shield,shield);
 }
private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1081,45,R"RB(K'Sante, Dauntless)RB",CardType::Unit,4,1,4,{Domain::Calm},Rarity::Epic,R"RB([Shield] (+1 [M] while I'm a defender.)
When I attack or defend, double the [Shield] of a unit you control here this turn.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Shurima)RB",R"RB(K'Sante)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/f56e9f9db199f915e32ea264b7dab70202f97957-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Shield);
  d.shield_value=1;
  return d;
 }();
};

class R64_1082 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }

 std::vector<ActivatedAbility> activatedAbilities()const override{
   ActivatedAbility a;a.cost.exhaust=true;return {a};
 }
 TriggerType triggerType()const override{return TriggerType::WhenIBecomeExhausted;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onActivate(CardContext& c,int,const std::vector<GameObjectId>&)override{
   c.executor.drawCards(c.controller,1);
   c.executor.channelRunes(c.controller,1,true);
 }
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   std::vector<GameObjectId> allies;
   for(const auto& [id,o]:c.state.objects.onBoard())
     if(o.isUnit()&&o.controller==c.controller&&o.location)allies.push_back(id);
   std::sort(allies.begin(),allies.end());
   const auto target=pickTarget(c,"Resplendent Rostrum: give +3 Might",allies);
   if(finalizingChoices(c))return;
   if(target!=kInvalidId)c.executor.giveTemporaryMight(target,3);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1082,46,R"RB(Resplendent Rostrum)RB",CardType::Gear,8,1,0,{Domain::Calm},Rarity::Epic,R"RB([E]: Draw 1 and channel 1 rune exhausted.
When I become exhausted, give a friendly unit +3 [M] this turn.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/df1c12e65cc3c63c96fb6c96b2071795f37f30a6-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1083 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenIBecomeExhausted;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   c.executor.predict(c.controller,1);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_a(1083,53,R"RB(Strigian Oracle)RB",CardType::Unit,2,0,2,{Domain::Mind},Rarity::Common,R"RB(When I become exhausted, [Predict]. (Look at the top card of your Main Deck. You may recycle it.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/5973b5036060f29e24f8778949bf6f01f360c0a4-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};
}
void register_card_1068(CardRegistry& r){r.registerCard(CardDefId{1068},std::make_unique<R64_1068>());}
void register_card_1069(CardRegistry& r){r.registerCard(CardDefId{1069},std::make_unique<R64_1069>());}
void register_card_1070(CardRegistry& r){r.registerCard(CardDefId{1070},std::make_unique<R64_1070>());}
void register_card_1071(CardRegistry& r){r.registerCard(CardDefId{1071},std::make_unique<R64_1071>());}
void register_card_1072(CardRegistry& r){r.registerCard(CardDefId{1072},std::make_unique<R64_1072>());}
void register_card_1073(CardRegistry& r){r.registerCard(CardDefId{1073},std::make_unique<R64_1073>());}
void register_card_1074(CardRegistry& r){r.registerCard(CardDefId{1074},std::make_unique<R64_1074>());}
void register_card_1075(CardRegistry& r){r.registerCard(CardDefId{1075},std::make_unique<R64_1075>());}
void register_card_1076(CardRegistry& r){r.registerCard(CardDefId{1076},std::make_unique<R64_1076>());}
void register_card_1077(CardRegistry& r){r.registerCard(CardDefId{1077},std::make_unique<R64_1077>());}
void register_card_1078(CardRegistry& r){r.registerCard(CardDefId{1078},std::make_unique<R64_1078>());}
void register_card_1079(CardRegistry& r){r.registerCard(CardDefId{1079},std::make_unique<R64_1079>());}
void register_card_1080(CardRegistry& r){r.registerCard(CardDefId{1080},std::make_unique<R64_1080>());}
void register_card_1081(CardRegistry& r){r.registerCard(CardDefId{1081},std::make_unique<R64_1081>());}
void register_card_1082(CardRegistry& r){r.registerCard(CardDefId{1082},std::make_unique<R64_1082>());}
void register_card_1083(CardRegistry& r){r.registerCard(CardDefId{1083},std::make_unique<R64_1083>());}
} // namespace riftbound
