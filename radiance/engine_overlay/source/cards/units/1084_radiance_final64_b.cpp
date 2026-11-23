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
CardDef mkFinal64_b(int id,int num,const char* name,CardType type,int energy,int power,int might,
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

class R64_1084 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // Printed Disarm is executed by the shared, fully reactable engine keyword dispatcher.

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1084,54,R"RB(Trinket Peddler)RB",CardType::Unit,3,0,3,{Domain::Mind},Rarity::Common,R"RB([Disarm] (When I attack, give an enemy unit here -1 [M] this turn.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/78106b7cea441b13d108e532adc5ce063f448165-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Disarm);
  return d;
 }();
};

class R64_1085 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 void asYouPlayChoices(CardContext& c)override{
   (void)f64ShowOff(c,[](const GameObject&,const CardDef&){return true;},
     "The Empyrean: Show Off a card");
 }
 TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!f64WasShownOff(c.state,c.source))return;
   const int power=f64ShownOffValue(c.state,c.source,"__final64_showoff_power");
   if(power>0)c.executor.predict(c.controller,power);
   c.executor.drawCards(c.controller,2);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1085,60,R"RB(The Empyrean)RB",CardType::Unit,8,0,8,{Domain::Mind},Rarity::Uncommon,R"RB([Show Off] a card. (As you play me, you may reveal a card from hand or pick another friendly one.)
When you play me, if you showed off a card, [Predict] equal to its Power cost, then draw 2. (Look at that many cards from your Main Deck. Recycle any of them and put the rest back in any order.))RB");
  d.tags={R"RB(Dragon)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/b7cd2e475834863bf4e66994118a835ba4377d16-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1086 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenIDie;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   c.executor.drawCards(c.controller,1);
 }
 // Opponents must pay [1][A] for ONE movement action to this battlefield,
 // irrespective of whether the moved unit belongs to the payer. Multiple
 // Gravity Fields increase both components of the surcharge.
 void applyPassiveAura(GameState& s,PlayerId controller) const override{
   if(controller==PlayerId::None)return;
   for(const auto& [id,obj]:s.objects.onBoard()){
     if(obj.card_def_id!=cardDefId()||obj.controller!=controller||
        !obj.isGear()||!obj.isAtBattlefield())continue;
     const auto where=obj.battlefieldId();
     if(!where)continue;
     for(auto& bf:s.battlefields)if(bf.id==*where){
       ++bf.gravity_move_tax_energy[playerIndex(opponent(controller))];
       ++bf.gravity_move_tax_power[playerIndex(opponent(controller))];
     }
   }
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1086,62,R"RB(Gravity Field)RB",CardType::Gear,5,1,0,{Domain::Mind},Rarity::Rare,R"RB([Deploy] (Play this only to a battlefield. When an opponent holds here, kill this.)
Opponents must pay [1][A] to move one or more units to this battlefield.
[Deathknell][>] Draw 1. (When I die, get the effect.))RB");
  d.tags={R"RB(Device)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/51f589e5ed0f7316b6cb64ebc93c4ef3e75b7f46-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Deploy);
  d.keywords.set(Keyword::Deathknell);
  return d;
 }();
};

class R64_1087 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1087,63,R"RB(Kai'Sa, Rebel)RB",CardType::Unit,5,1,5,{Domain::Mind},Rarity::Rare,R"RB([Disarm] (When I attack, give an enemy unit here -1 [M] this turn).
While I'm in a showdown, your spells have [Reaction]. (Play them any time, even before spells and abilities resolve.))RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Kai'Sa)RB",R"RB(The Void)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/53a7fdbb66f0d05111f4a7f54853db30f62fa5c4-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Disarm);
  return d;
 }();
};

class R64_1088 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }

 std::vector<ActivatedAbility> activatedAbilities()const override{
   ActivatedAbility a;a.cost.energy=1;a.cost.exhaust=true;return {a};
 }
 void onActivate(CardContext& c,int,const std::vector<GameObjectId>&)override{
   const auto guessed=c.executor.chooseValueNow(opponent(c.controller),
      {"Unit","Gear","Spell"},"Scrutinizing Scope: guess top-card type");
   const auto top=f64RevealTop(c,c.controller);
   if(top==kInvalidId)return;
   const auto type=c.state.getObject(top).card_type;
   const int actual=type==CardType::Unit?0:type==CardType::Gear?1:
                    type==CardType::Spell?2:-1;
   if(guessed==actual)f64RecycleRevealedTop(c,c.controller,top);
   else c.executor.drawCards(c.controller,1);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1088,64,R"RB(Scrutinizing Scope)RB",CardType::Gear,2,0,0,{Domain::Mind},Rarity::Rare,R"RB([1], [E]: Choose an opponent. They guess a card type. Reveal the top card of your Main Deck. If it has that type, recycle it. Otherwise, draw it. (Unit, gear, and spell are types.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/6a028fc372c14dda73864aba3d3e84063f6da98d-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1089 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 AdditionalPlayCost additionalPlayCost(const GameState& s,const CardDB&,PlayerId p,GameObjectId)const override{
   AdditionalPlayCost extra;extra.exists=true;
   extra.payable=!f64Gears(s,p).empty();
   return extra;
 }
 PlayCostAdjust payAdditionalPlayCost(CardContext& c,
        const std::function<bool(const PlayCostAdjust&)>&)override{
   auto gears=f64Gears(c.state,c.controller);
   if(gears.empty()||!c.executor.confirmNow(c.controller,
        "Spirit of the Forge: return a gear as optional play cost?"))return {};
   const auto choice=c.executor.chooseObjectNow(c.controller,gears,
          "Spirit of the Forge: friendly gear to return");
   if(choice==kInvalidId||!c.state.objectExists(choice))return {};
   const auto defId=c.state.getObject(choice).card_def_id;
   if(defId==kInvalidId)return {};
   const int energy=c.executor.cardDB().get(defId).energy_cost;
   c.executor.bounceToHand(choice);
   if(c.state.objectExists(c.source))
     c.state.getObject(c.source).card_counters["__f64_returned_gear_energy"]=energy+1;
   return {};
 }
 bool entersReadyOnPlay(const GameState& s,PlayerId,const GameObject& self)const override{
   const auto it=self.card_counters.find("__f64_returned_gear_energy");
   return it!=self.card_counters.end()&&it->second>0;
 }
 TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source))return;
   const auto& counters=c.state.getObject(c.source).card_counters;
   const auto it=counters.find("__f64_returned_gear_energy");
   if(it!=counters.end()&&it->second>0)
     c.executor.giveTemporaryMight(c.source,it->second-1);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1089,66,R"RB(Spirit of the Forge)RB",CardType::Unit,6,1,4,{Domain::Mind},Rarity::Rare,R"RB(You may return a friendly gear to its owner's hand as an additional cost to play me.
When you play me, if you paid the additional cost, ready me and give me +[M] this turn equal to the Energy cost of the gear you returned.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/7a1f527e5910fbc18f7cb3cddf2aa59b483393f4-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1090 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 std::vector<TriggerType> triggerTypes()const override{
   return {TriggerType::WhenYouPlayMe,TriggerType::WhenIHold,TriggerType::WhenIDie};
 }
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(c.firing_trigger!=TriggerType::WhenIDie){
     c.executor.predict(c.controller,3);
     return;
   }
   const auto top=f64RevealTop(c,c.controller);
   if(top==kInvalidId)return;
   c.executor.banishObject(top,c.controller);
   if(!c.state.objectExists(top) ||
      !c.executor.confirmNow(c.controller,
           "Clocktower Guardian Deathknell: play banished card without Energy cost?"))
     return;
   const auto& obj=c.state.getObject(top);
   std::optional<LocationId> where;
   if(obj.isUnit()||obj.isGear()){
      auto opts=playLocations(c.state,c.controller);
      if(!opts.locations.empty())where=c.executor.chooseLocationNow(c.controller,
          opts.locations,"Clocktower Guardian: free-Energy location");
   }
   (void)c.executor.playPayingCost(c.controller,top,where,
       EffectPlayCost{.ignore_energy=true});
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1090,67,R"RB(Clocktower Guardian)RB",CardType::Unit,8,2,8,{Domain::Mind},Rarity::Epic,R"RB(When you play me or when I hold, [Predict 3].
[Deathknell][>] Banish the top card of your Main Deck. You may play it, ignoring its Energy cost.)RB");
  d.tags={R"RB(Mech)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/b846d604eee450a4ab8f457f2738b0596e7b361e-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Deathknell);
  return d;
 }();
};

class R64_1091 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // Initial aura integration: the engine's unified cost calculation uses both
 // Energy and Power reductions. Further acceptance requires player choice
 // and per-source once-per-turn tracking (not just first gear per turn).
 void applyPassiveAura(GameState& s,PlayerId controller)const override{
   if(controller==PlayerId::None)return;
   for(const auto& [id,obj]:s.objects.onBoard()){
     if(obj.card_def_id!=cardDefId()||obj.controller!=controller||
        !obj.isUnit()||!obj.isAtBattlefield())continue;
     auto& mods=s.player(controller).cost_modifiers;
     if(std::any_of(mods.begin(),mods.end(),[&](const auto& m){
         return m.source==id&&m.gear_only&&m.from_aura;}))continue;
     PlayerState::CostModifier m;
     m.source=id;
     m.energy_reduction=1;
     m.power_reduction=1;
     m.gear_only=true;
     m.first_gear_per_turn=true;
     m.affects_friendly_only=true;
     m.this_turn_only=false;
     mods.push_back(m);
   }
 }
private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1091,68,R"RB(Orianna, Mechanical Marvel)RB",CardType::Unit,5,0,5,{Domain::Mind},Rarity::Epic,R"RB(Once each turn, while I'm at a battlefield, you may pay [1][A] less to play a gear.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Piltover)RB",R"RB(Orianna)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/00f5a081a085e9c3851daf79d9e39bd378f71fe3-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1092 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }

 std::vector<TriggerType> triggerTypes()const override{
   return {TriggerType::WhenYouPlayACard,TriggerType::WhenYouDrawACard};
 }
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source))return;
   if(c.firing_trigger==TriggerType::WhenYouPlayACard){
     c.executor.drawCards(c.controller,2);
     return;
   }
   if(c.firing_trigger!=TriggerType::WhenYouDrawACard ||
      c.state.player(c.controller).hand.size()<10)return;
   const int cards=static_cast<int>(c.state.player(c.controller).hand.size());
   if(cards>0)c.executor.discardCards(c.controller,cards);
   c.executor.killObject(c.source);
   c.executor.scorePoints(opponent(c.controller),1);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1092,69,R"RB(Zero Point Inflection)RB",CardType::Gear,9,2,0,{Domain::Mind},Rarity::Epic,R"RB(When you play a card, draw 2.
When you draw 1 or more cards with 9 or more other cards in your hand, discard your hand, kill this, and choose an opponent. They score 1 point.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/5e0646270d27f9fa78f4c3a637695e5cdeb8ee67-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1093 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenIMove;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   const auto top=f64RevealTop(c,c.controller);
   if(top==kInvalidId)return;
   const auto& obj=c.state.getObject(top);
   const bool mighty=obj.isUnit()&&obj.card_def_id!=kInvalidId&&
        c.executor.cardDB().get(obj.card_def_id).might>=5;
   if(mighty)c.executor.drawCards(c.controller,1);
   else f64RecycleRevealedTop(c,c.controller,top);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1093,74,R"RB(Raving Witness)RB",CardType::Unit,3,0,3,{Domain::Body},Rarity::Common,R"RB(When I move, reveal the top card of your Main Deck. If it's [Mighty], draw it. Otherwise, recycle it. (A unit is Mighty while it has 5+ [M].))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/778e70b353d7f28eae9b54b1a37af3853238ba04-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1094 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenIMove;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source)){(void)finalizingChoices(c);return;}
   const auto& self=c.state.getObject(c.source);
   auto options=boardObjects(c.state,[](const GameObject& o){
      return o.isUnit()&&o.isAtBattlefield();
   });
   const int confirm=confirmOptional(c,
      "Armored Tusker: deal Shield value as damage to battlefield unit?",
      [&](){return !options.empty()&&self.shield_value>0;});
   if(confirm<0)return;
   if(confirm==0){(void)finalizingChoices(c);return;}
   const auto target=pickTarget(c,"Armored Tusker: deal Shield damage",options);
   if(finalizingChoices(c))return;
   if(target!=kInvalidId)c.executor.dealDamage(target,self.shield_value,c.source);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1094,78,R"RB(Armored Tusker)RB",CardType::Unit,6,1,4,{Domain::Body},Rarity::Uncommon,R"RB([Shield 3] (+3 [M] while I'm a defender.)
[Tank] (I must be assigned combat damage first.)
When I move, you may deal damage equal to my [Shield] to a unit at a battlefield.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/c479f2fda00506e71a57ac4e8cc297f7f3110a54-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Shield);
  d.keywords.set(Keyword::Tank);
  d.shield_value=3;
  return d;
 }();
};

class R64_1095 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 int selfCostReduction(const GameState& s,PlayerId p)const override {
   return static_cast<int>(2*s.player(p).battlefields_conquered_this_turn.size());
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1095,80,R"RB(Bloodscent Swarm)RB",CardType::Unit,8,2,8,{Domain::Body},Rarity::Uncommon,R"RB(I cost [2] less for each battlefield you've conquered this turn.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/775ccea752fb404be2433c4b870c7877e2445a8c-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1096 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }

 void asYouPlayChoices(CardContext& c)override{
   (void)f64ShowOff(c,[](const GameObject& o,const CardDef& d){
     return d.card_type==CardType::Unit||o.isUnit();
   },"Primordial Roar: Show Off a unit");
 }
 unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
 FinalizeChoice mayChooseAtFinalization(const GameState& s,PlayerId,GameObjectId id)const override{
   if(!s.objectExists(id))return FinalizeChoice::No;
   const auto& o=s.getObject(id);
   return o.isUnit()&&o.location?FinalizeChoice::Yes:FinalizeChoice::No;
 }
 void onResolve(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!f64WasShownOff(c.state,c.source)){(void)finalizingChoices(c);return;}
   const auto units=boardObjects(c.state,[](const GameObject& o){return o.isUnit();});
   const auto target=pickTarget(c,"Primordial Roar: damage a unit",units);
   if(finalizingChoices(c))return;
   if(target!=kInvalidId)
     c.executor.dealDamage(target,
       f64ShownOffValue(c.state,c.source,"__final64_showoff_might"),c.source);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1096,82,R"RB(Primordial Roar)RB",CardType::Spell,4,2,0,{Domain::Body},Rarity::Uncommon,R"RB([Show Off] a unit. (As you play this, you may reveal a unit from hand or pick a friendly unit.)
If you showed off a unit, deal damage equal to that unit's Might to a unit.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/945633b0c2ed7f303245c917ffbcdb80dcfb524e-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1097 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }

 static uint32_t targets(const GameState& s,PlayerId p){
   uint32_t mask=0;
   for(size_t i=0;i<s.battlefields.size()&&i<32;i++){
     const auto& bf=s.battlefields[i];
     if(!bf.controller.has_value()||*bf.controller==p)continue;
     bool occupied=false;
     for(const auto& [id,o]:s.objects.onBoard())
       if(o.isUnit()&&o.controller!=p&&o.battlefieldId()==bf.id){occupied=true;break;}
     if(occupied)mask|=1u<<i;
   }
   return mask;
 }
 bool canBePlayed(const GameState& s,PlayerId p)const override{
   if(!targets(s,p))return false;
   for(const auto& [id,o]:s.objects.onBoard())
     if(o.isUnit()&&o.controller==p&&o.location)return true;
   return false;
 }
 FinalizeChoice mayChooseAtFinalization(const GameState& s,PlayerId p,GameObjectId id)const override{
   if(!s.objectExists(id))return FinalizeChoice::No;
   const auto& o=s.getObject(id);
   return o.isUnit()&&o.controller==p&&o.location?FinalizeChoice::Yes:FinalizeChoice::No;
 }
 unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
 void onResolve(CardContext& c,const std::vector<GameObjectId>&)override{
   const auto units=boardObjects(c.state,[&](const GameObject& o){
     return o.isUnit()&&o.controller==c.controller;
   });
   const auto chosen=pickTarget(c,"Cataclysm: friendly unit",units);
   std::vector<std::string> labels;
   for(const auto& bf:c.state.battlefields)
     labels.push_back("Enemy battlefield "+std::to_string(bf.id.raw()));
   const int destination=pickMode(c,"Cataclysm: occupied enemy battlefield",
     static_cast<int>(labels.size()),labels,targets(c.state,c.controller));
   if(destination<0)return;
   if(finalizingChoices(c))return;
   c.state.player(opponent(c.controller)).cant_play_spells_this_turn=true;
   if(chosen!=kInvalidId&&static_cast<size_t>(destination)<c.state.battlefields.size())
     c.executor.moveToBattlefield(chosen,c.state.battlefields[destination].id);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1097,84,R"RB(Cataclysm)RB",CardType::Spell,4,1,0,{Domain::Body},Rarity::Rare,R"RB(Opponents can't play spells this turn.
Move a friendly unit to an occupied enemy battlefield.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/dc551ece6cf007c76a3a16feba5f26fb7dd4ed65-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1098 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenIAttackOrDefend;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source))return;
   const auto& graves=c.state.getObject(c.source);
   if(!graves.isAtBattlefield())return;
   const auto enemies=boardObjects(c.state,[&](const GameObject& o){
      return o.isUnit()&&o.controller!=c.controller&&o.battlefieldId()==graves.battlefieldId();
   });
   const int damage=graves.current_might;
   for(auto id:enemies)
     if(c.state.objectExists(id))c.executor.dealDamage(id,damage,c.source);
 }
 void applyPassiveAura(GameState& s,PlayerId p)const override{
   forEachSelfOnce(*this,s,p,[&](GameObjectId source,GameObject& graves){
     if(!graves.location)return;
     GameObject::AuraEffect noDamage;
     noDamage.source=source;noDamage.suppress_combat_damage=true;
     graves.aura_effects.push_back(noDamage);
   });
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1098,85,R"RB(Graves, Blasting Through)RB",CardType::Unit,5,1,4,{Domain::Body},Rarity::Rare,R"RB(When I attack or defend, deal damage equal to my Might to all enemy units here.
I don't deal combat damage.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Bilgewater)RB",R"RB(Graves)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/5bc0671f9f78630e2932052bb9f7f42ef2742c86-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1099 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenYouPlayFromFacedown;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
   if(!c.state.objectExists(c.source))return;
   if(!c.state.getObject(c.source).location)return;
   c.executor.readyObject(c.source);
   c.executor.giveTemporaryMight(c.source,1);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_b(1099,90,R"RB(Evelynn, Consuming)RB",CardType::Unit,5,1,5,{Domain::Body},Rarity::Epic,R"RB([Ambush] (You may play me as a [Reaction] to a battlefield where you have units.)
When you play a card from face down, ready me and give me +1 [M] this turn.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Evelynn)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/26b83de26622fb5163d2fe321ff29e2bf16ac027-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Ambush);
  return d;
 }();
};
}
void register_card_1084(CardRegistry& r){r.registerCard(CardDefId{1084},std::make_unique<R64_1084>());}
void register_card_1085(CardRegistry& r){r.registerCard(CardDefId{1085},std::make_unique<R64_1085>());}
void register_card_1086(CardRegistry& r){r.registerCard(CardDefId{1086},std::make_unique<R64_1086>());}
void register_card_1087(CardRegistry& r){r.registerCard(CardDefId{1087},std::make_unique<R64_1087>());}
void register_card_1088(CardRegistry& r){r.registerCard(CardDefId{1088},std::make_unique<R64_1088>());}
void register_card_1089(CardRegistry& r){r.registerCard(CardDefId{1089},std::make_unique<R64_1089>());}
void register_card_1090(CardRegistry& r){r.registerCard(CardDefId{1090},std::make_unique<R64_1090>());}
void register_card_1091(CardRegistry& r){r.registerCard(CardDefId{1091},std::make_unique<R64_1091>());}
void register_card_1092(CardRegistry& r){r.registerCard(CardDefId{1092},std::make_unique<R64_1092>());}
void register_card_1093(CardRegistry& r){r.registerCard(CardDefId{1093},std::make_unique<R64_1093>());}
void register_card_1094(CardRegistry& r){r.registerCard(CardDefId{1094},std::make_unique<R64_1094>());}
void register_card_1095(CardRegistry& r){r.registerCard(CardDefId{1095},std::make_unique<R64_1095>());}
void register_card_1096(CardRegistry& r){r.registerCard(CardDefId{1096},std::make_unique<R64_1096>());}
void register_card_1097(CardRegistry& r){r.registerCard(CardDefId{1097},std::make_unique<R64_1097>());}
void register_card_1098(CardRegistry& r){r.registerCard(CardDefId{1098},std::make_unique<R64_1098>());}
void register_card_1099(CardRegistry& r){r.registerCard(CardDefId{1099},std::make_unique<R64_1099>());}
} // namespace riftbound
