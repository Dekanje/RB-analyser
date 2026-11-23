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
CardDef mkFinal64_c(int id,int num,const char* name,CardType type,int energy,int power,int might,
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

class R64_1100 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenIConquer;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source))return;
   const auto& self=c.state.getObject(c.source);
   if(!self.isAtBattlefield())return;
   for(const auto& [id,o]:c.state.objects.onBoard())
     if(o.isGear()&&o.controller==c.controller&&o.isAtBattlefield()&&
        o.battlefieldId()==self.battlefieldId()&&o.hasKeyword(Keyword::Deploy)){
          c.executor.channelRunes(c.controller,1,true);
          return;
        }
 }
 void applyPassiveAura(GameState& s,PlayerId p)const override{
   forEachSelfOnce(*this,s,p,[&](GameObjectId source,GameObject& champion){
      if(!champion.location)return;
      for(auto& [id,o]:s.objects.onBoard())
        if(o.isGear()&&o.controller==p&&o.hasKeyword(Keyword::Deploy))
          auraKeyword(o,source,Keyword::Action);
   });
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1100,91,R"RB(Jarvan IV, Martial Paragon)RB",CardType::Unit,4,1,4,{Domain::Body},Rarity::Epic,R"RB(Your gear with [Deploy] have [Action]. (They can be played on your turn or in showdowns.)
When I conquer, if there is a friendly gear with [Deploy] here, channel 1 rune exhausted.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Demacia)RB",R"RB(Jarvan IV)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/8edacba51db193506e13e1afb6a8509256cdf55c-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1101 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // Channel replacement is enforced centrally by EffectExecutor::channelRunes.
 // Extra channels enter exhausted even when the original instruction channels ready.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1101,92,R"RB(Seraphic Wyvern)RB",CardType::Unit,7,0,7,{Domain::Body},Rarity::Epic,R"RB(If you would channel runes, channel that many runes plus 1 exhausted rune instead.)RB");
  d.tags={R"RB(Dragon)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/ad1793554440d8d5017eadc565ca6c787a969de1-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1102 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenIHold;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
   if(c.state.battlefields.empty())return;
   std::vector<LocationId> locations;
   for(const auto& b:c.state.battlefields)locations.push_back(BattlefieldLocation{b.id});
   const auto destination=c.executor.chooseLocationNow(c.controller,locations,
      "Explosimian: play three Bombs to one battlefield");
   KeywordSet kws;kws.set(Keyword::Deploy);
   for(int i=0;i<3;i++)
     c.executor.createToken(c.controller,CardType::Gear,"Bomb",0,{"Bomb"},
                            kws,destination,false,{},CardDefId{982});
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1102,94,R"RB(Explosimian)RB",CardType::Unit,6,0,6,{Domain::Chaos},Rarity::Common,R"RB(When I hold, play three Bomb gear tokens to a single battlefield. (They have [Deploy]. When each dies, deal 2 to an enemy there and kill your other Bombs there.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/f2590617229f3efc078aa2429f65b85101303200-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1103 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }

 static std::vector<GameObjectId> eligible(const GameState& s,PlayerId p){
   return boardObjects(s,[&](const GameObject& o){
     return o.isUnit()&&o.controller!=p&&o.moves_this_turn>0&&
            !moveDests(s,o).empty();
   });
 }
 bool canBePlayed(const GameState& s,PlayerId p)const override{
   return !eligible(s,p).empty();
 }
 FinalizeChoice mayChooseAtFinalization(const GameState& s,PlayerId p,GameObjectId id)const override{
   if(!s.objectExists(id))return FinalizeChoice::No;
   const auto& o=s.getObject(id);
   return o.isUnit()&&o.controller!=p&&o.location&&o.moves_this_turn>0
       ?FinalizeChoice::Yes:FinalizeChoice::No;
 }
 unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
 void onResolve(CardContext& c,const std::vector<GameObjectId>&)override{
   const auto target=pickTarget(c,"Siren's Song: enemy unit that moved this turn",
                                eligible(c.state,c.controller));
   if(target==kInvalidId){(void)finalizingChoices(c);return;}
   const int dest=pickMoveDest(*this,c,"Siren's Song: destination",
                              c.state.getObject(target));
   if(dest<0)return;
   if(finalizingChoices(c))return;
   moveTo(c,target,dest);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1103,98,R"RB(Siren's Song)RB",CardType::Spell,2,0,0,{Domain::Chaos},Rarity::Common,R"RB([Reaction] (Play any time, even before spells and abilities resolve.)
Move an enemy unit that moved this turn.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/742967b3e85f51b242fc04b8db4c4e3cd7b88672-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Reaction);
  return d;
 }();
};

class R64_1104 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }

 bool canBePlayed(const GameState& s,PlayerId p)const override{
   return !f64Units(s,p).empty();
 }
 FinalizeChoice mayChooseAtFinalization(const GameState& s,PlayerId p,GameObjectId id)const override{
   if(!s.objectExists(id))return FinalizeChoice::No;
   const auto& o=s.getObject(id);
   return o.isUnit()&&o.controller==p&&o.location?FinalizeChoice::Yes:FinalizeChoice::No;
 }
 unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
 void onResolve(CardContext& c,const std::vector<GameObjectId>&)override{
   const auto unit=pickTarget(c,"Demon Shade: choose a friendly unit",f64Units(c.state,c.controller));
   if(unit==kInvalidId){(void)finalizingChoices(c);return;}
   uint32_t mask=0;
   std::vector<std::string> names;
   for(size_t i=0;i<c.state.battlefields.size()&&i<32;i++){
     const auto& bf=c.state.battlefields[i];
     names.push_back("Open battlefield #"+std::to_string(bf.id.raw()));
     if(!bf.controller.has_value()&&!bf.is_contested)mask|=1u<<i;
   }
   int picked=-2;
   if(mask){
     picked=pickMode(c,"Demon Shade: choose open battlefield",
         static_cast<int>(names.size()),names,mask);
     if(picked<0)return;
   }
   if(finalizingChoices(c))return;
   if(mask&&picked>=0&&static_cast<size_t>(picked)<c.state.battlefields.size())
     c.executor.moveToBattlefield(unit,c.state.battlefields[picked].id);
   else c.executor.giveTemporaryKeyword(unit,Keyword::Ganking,0);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1104,102,R"RB(Demon Shade)RB",CardType::Spell,3,0,0,{Domain::Chaos},Rarity::Uncommon,R"RB([Hidden] (Hide now for [A] to react with later for [0].)
Choose a friendly unit, then choose one —Move it to an open battlefield.
Give it [Ganking] this turn if there are no open battlefields. (It can move from battlefield to battlefield.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/e9dd313886624aafc7e0c7f9e1689225c042b484-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Hidden);
  return d;
 }();
};

class R64_1105 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 void asYouPlayChoices(CardContext& c)override{
   (void)f64ShowOff(c,[](const GameObject& o,const CardDef& d){
     return d.keywords.has(Keyword::Hidden)||o.hasKeyword(Keyword::Hidden);
   },"Gutter Guardian: Show Off a Hidden card");
 }
 TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
   if(f64WasShownOff(c.state,c.source))
     c.executor.addFloatingUniversalPower(c.controller,1);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1105,103,R"RB(Gutter Guardian)RB",CardType::Unit,3,0,3,{Domain::Chaos},Rarity::Uncommon,R"RB([Hidden] (Hide now for [A] to react with later for [0].)
[Show Off] a card with [Hidden]. (As you play me, you may reveal such a card from hand or pick another friendly one on the board.)
When you play me, if you showed off, [Add] [A].)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/756827744317003e4992163ff9bf1dc991682de8-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Hidden);
  return d;
 }();
};

class R64_1106 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 std::vector<ActivatedAbility> activatedAbilities()const override {
   ActivatedAbility a;a.cost.exhaust=true;
   return {a};
 }
 unsigned choicesAtFinalization()const override{return kFinalizeActivate;}
 bool canActivateAbility(const GameState& s,PlayerId p)const override{
   for(const auto& [id,o]:s.objects.onBoard())
     if(o.isUnit()&&o.controller!=p&&o.location)return true;
   return false;
 }
 void onActivate(CardContext& c,int,const std::vector<GameObjectId>&)override {
   std::vector<GameObjectId> enemies;
   for(const auto& [id,o]:c.state.objects.onBoard())
     if(o.isUnit()&&o.controller!=c.controller&&o.location)enemies.push_back(id);
   std::sort(enemies.begin(),enemies.end());
   const auto target=pickTarget(c,"Pitiless Stalker: stun enemy unit",enemies);
   if(finalizingChoices(c))return;
   if(target!=kInvalidId)c.executor.stunUnitBy(target,c.source);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1106,104,R"RB(Pitiless Stalker)RB",CardType::Unit,5,1,5,{Domain::Chaos},Rarity::Uncommon,R"RB([E]: [Stun] an enemy unit. (It doesn't deal combat damage this turn.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/fc61b244fb3ed01d61617c3c2633a71424604130-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1107 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }

 void applyPassiveAura(GameState& s,PlayerId p)const override {
   forEachSelfOnce(*this,s,p,[&](GameObjectId,GameObject& trap){
     if(!trap.isAtBattlefield())return;
     for(auto& bf:s.battlefields)
       if(bf.id==trap.battlefieldId()&&bf.controller==p)
         ++bf.facedown_max_occupancy;
   });
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1107,108,R"RB(Bushwhack Trap)RB",CardType::Gear,1,0,0,{Domain::Chaos},Rarity::Rare,R"RB([Deploy] (Play this only to a battlefield. When an opponent holds here, kill this.)
While you or an ally control this battlefield, that player may hide an additional card here.)RB");
  d.tags={R"RB(Device)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/120762e23a599ee14d3f88856fcf707154338fb0-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Deploy);
  return d;
 }();
};

class R64_1108 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenIHold;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
   if(!c.state.objectExists(c.source))return;
   const auto& eve=c.state.getObject(c.source);
   if(!eve.isAtBattlefield())return;
   const auto bf=eve.battlefieldId();
   for(const auto& slot:c.state.battlefields){
     if(slot.id!=*bf)continue;
     for(const auto id:slot.facedown){
       if(!c.state.objectExists(id))continue;
       const auto& card=c.state.getObject(id);
       if(card.controller==c.controller&&card.is_hidden&&card.hidden_at==*bf){
         c.executor.scorePoints(c.controller,1);
         return;
       }
     }
   }
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1108,109,R"RB(Evelynn, In Control)RB",CardType::Unit,4,1,4,{Domain::Chaos},Rarity::Rare,R"RB([Disarm] (When I attack, give an enemy unit here -1 [M] this turn.)
When I hold, if you control a facedown card here, score 1 point.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Evelynn)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/8c17158e6153eddb4b56abd8a09cbbd20600b049-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Disarm);
  return d;
 }();
};

class R64_1109 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenIMove;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   auto units=boardObjects(c.state,[&](const GameObject& o){
     return o.isUnit()&&o.id!=c.source;
   });
   const int yes=confirmOptional(c,
     "Lulu: make another unit's base Might 4 this turn?",[&](){return !units.empty();});
   if(yes<0)return;
   if(yes==0){(void)finalizingChoices(c);return;}
   const auto target=pickTarget(c,"Lulu: unit to set base Might to 4",units);
   if(finalizingChoices(c))return;
   if(target!=kInvalidId&&c.state.objectExists(target)){
     auto& o=c.state.getObject(target);
     o.base_might_this_turn=4;
     o.recomputeMight();
     c.events.emit(ObjectStateChangedEvent{target,"might_changed"});
   }
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1109,110,R"RB(Lulu, Whimsical)RB",CardType::Unit,3,0,3,{Domain::Chaos},Rarity::Rare,R"RB(When I move, you may have another unit's base Might become 4 this turn.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Yordle)RB",R"RB(Bandle City)RB",R"RB(Lulu)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/defd09480671a1e394725f21b6c3448ebec77913-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1110 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::AtStartOfBeginning;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   const auto yours=f64RevealTop(c,c.controller);
   const auto theirs=f64RevealTop(c,opponent(c.controller));
   if(yours==kInvalidId&&theirs==kInvalidId)return;
   auto energy=[&](GameObjectId id)->int{
     if(id==kInvalidId||!c.state.objectExists(id))return 999;
     const auto def=c.state.getObject(id).card_def_id;
     return def==kInvalidId?999:c.executor.cardDB().get(def).energy_cost;
   };
   const int lowest=std::min(energy(yours),energy(theirs));
   for(const auto [owner,card] :
       std::vector<std::pair<PlayerId,GameObjectId>>{
           {c.controller,yours},{opponent(c.controller),theirs}}){
     if(card==kInvalidId||!c.state.objectExists(card))continue;
     if(energy(card)==lowest)c.executor.drawCards(owner,1);
     else f64RecycleRevealedTop(c,owner,card);
   }
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1110,111,R"RB(Mechanical Bandit)RB",CardType::Gear,4,1,0,{Domain::Chaos},Rarity::Rare,R"RB(At the start of your Beginning Phase, each player reveals the top card of their Main Deck. If you revealed a card with the lowest Energy cost, draw it. Recycle the rest.)RB");
  d.tags={R"RB(Device)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/cb2a419b61b6f1e6d138c3c3b07b393a4037237b-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1111 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 std::vector<ActivatedAbility> activatedAbilities()const override {
   ActivatedAbility a;a.cost.energy=1;a.cost.exhaust=true;return {a};
 }
 TriggerType triggerType()const override{return TriggerType::WhenIDefend;}
 unsigned choicesAtFinalization()const override{return kFinalizeActivate|kFinalizeTrigger;}
 void onActivate(CardContext& c,int,const std::vector<GameObjectId>&)override{
   const int chosen=pickBattlefield(*this,c,"Ziggs: play a Bomb");
   if(chosen<0)return;
   if(finalizingChoices(c))return;
   if(static_cast<size_t>(chosen)<c.state.battlefields.size())
     f64Bomb(c,BattlefieldLocation{c.state.battlefields[chosen].id});
 }
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(costAlreadyPaid(c)){
     if(finalizingChoices(c))return;
     c.executor.giveTemporaryMight(c.source,2);
     return;
   }
   auto gears=f64Gears(c.state,c.controller);
   const int yes=confirmOptional(c,"Ziggs: kill friendly gear to gain +2 Might?",
                                 [&](){return !gears.empty();});
   if(yes<0)return;
   if(yes==0){(void)finalizingChoices(c);return;}
   const auto gear=pickCostObject(c,"Ziggs: choose gear to kill",gears);
   if(gear==kInvalidId)return;
   if(costDueNow(c))killAsCost(c,gear);
   if(finalizingChoices(c))return;
   if(!costUnpaid(c))c.executor.giveTemporaryMight(c.source,2);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1111,112,R"RB(Ziggs, Explosive)RB",CardType::Unit,4,0,4,{Domain::Chaos},Rarity::Rare,R"RB([1], [E]: Play a Bomb gear token to a battlefield. (It has [Deploy]. When it dies, deal 2 to an enemy there and kill your other Bombs there.)
When I defend, you may kill a friendly gear to give me +2 [M] this turn.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Bandle City)RB",R"RB(Ziggs)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/f0c1f1f3b69b31a69f9637ece841b5ee1029cdd3-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1112 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 std::vector<ActivatedAbility> activatedAbilities()const override{
   ActivatedAbility a;a.cost.exhaust=true;return {a};
 }
 unsigned choicesAtFinalization()const override{return kFinalizeActivate;}
 bool canActivateAbilityAt(const GameState& s,PlayerId p,GameObjectId source,int)const override{
   if(!s.objectExists(source)||!s.getObject(source).isAtBattlefield())return false;
   const auto here=s.getObject(source).battlefieldId();
   for(const auto& [id,o]:s.objects.onBoard())
     if(o.isUnit()&&o.controller==opponent(p)&&o.location&&
         o.battlefieldId()!=here)return true;
   return false;
 }
 void onActivate(CardContext& c,int,const std::vector<GameObjectId>&)override{
   if(!c.state.objectExists(c.source)){(void)finalizingChoices(c);return;}
   const auto& self=c.state.getObject(c.source);
   if(!self.isAtBattlefield()){(void)finalizingChoices(c);return;}
   auto enemies=boardObjects(c.state,[&](const GameObject& o){
     return o.isUnit()&&o.controller==opponent(c.controller)&&
            o.battlefieldId()!=self.battlefieldId();
   });
   const auto picked=selectObjectAs(c,opponent(c.controller),
        "Angler Wyrm: move one of your units to its battlefield",enemies);
   if(!picked.has_value())return;
   if(finalizingChoices(c))return;
   if(*picked!=kInvalidId)
     c.executor.moveToBattlefield(*picked,*self.battlefieldId());
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1112,113,R"RB(Angler Wyrm)RB",CardType::Unit,8,0,8,{Domain::Chaos},Rarity::Epic,R"RB([Deflect] (Opponents must pay [A] to choose me with a spell or ability.)
[E]: Choose an opponent. They must move a unit they control to my battlefield.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/e805eba9add03fd3e1b1601b15c12a46fd403282-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Deflect);
  d.deflect_value=1;
  return d;
 }();
};

class R64_1113 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{
   return TriggerType::WhenAnotherFriendlyUnitBecomesExhausted;
 }
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   if(c.state.objectExists(c.source)&&c.state.getObject(c.source).location)
     c.executor.giveTemporaryMight(c.source,1);
 }
 std::vector<ActivatedAbility> activatedAbilities()const override{
   return {ActivatedAbility{}};
 }
 unsigned choicesAtFinalization()const override{return kFinalizeActivate;}
 bool canActivateAbilityAt(const GameState& s,PlayerId p,GameObjectId source,int)const override{
   if(!s.objectExists(source))return false;
   const auto& obj=s.getObject(source);
   const auto it=obj.card_counters.find("__f64_riven_used_turn");
   if(it!=obj.card_counters.end()&&it->second==s.turn.turn_number+1)return false;
   for(const auto& [id,o]:s.objects.onBoard())
     if(o.isUnit()&&o.controller==p&&o.location&&!o.is_exhausted)return true;
   return false;
 }
 void onActivate(CardContext& c,int,const std::vector<GameObjectId>&)override{
   auto ready=boardObjects(c.state,[&](const GameObject& o){
     return o.isUnit()&&o.controller==c.controller&&!o.is_exhausted;
   });
   auto cost=selectObjectAs(c,c.controller,"Riven: exhaust friendly unit as cost",ready,7);
   if(!cost.has_value())return;
   auto units=boardObjects(c.state,[](const GameObject& o){return o.isUnit();});
   auto target=selectTargetOrNone(*this,c,"Riven: unit to ready",units,9,false);
   if(!target.has_value())return;
   if(costDueNow(c)&&*cost!=kInvalidId){
     c.executor.exhaustObject(*cost);
     if(c.state.objectExists(c.source))
       c.state.getObject(c.source).card_counters["__f64_riven_used_turn"]=
              c.state.turn.turn_number+1;
   }
   if(finalizingChoices(c))return;
   if(*target!=kInvalidId)c.executor.readyObject(*target);
 }
private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1113,114,R"RB(Riven, Deserter)RB",CardType::Unit,5,1,5,{Domain::Chaos},Rarity::Epic,R"RB(When another friendly unit becomes exhausted, give me +1 [M] this turn.
Exhaust a friendly unit: Ready a unit. Use this ability only once each turn.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Riven)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/59c080321a697164c9eeb6f0ad297ff0d0b85808-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1114 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 std::vector<ActivatedAbility> activatedAbilities()const override{
   ActivatedAbility a;a.cost.power=1;a.cost.power_domain=Domain::Chaos;
   a.cost.exhaust=true;return {a};
 }
 unsigned choicesAtFinalization()const override{return kFinalizeActivate;}
 bool canActivateAbilityAt(const GameState& s,PlayerId p,GameObjectId,int)const override{
   return !f64Units(s,p).empty();
 }
 void onActivate(CardContext& c,int,const std::vector<GameObjectId>&)override{
   const auto friendly=f64Units(c.state,c.controller);
   const auto returned=pickTarget(c,"Transpositionist: friendly unit to return",friendly);
   if(finalizingChoices(c))return;
   if(returned==kInvalidId||!c.state.objectExists(returned))return;
   const int might=c.state.getObject(returned).current_might;
   c.executor.bounceToHand(returned);
   std::vector<GameObjectId> candidates;
   for(auto id:c.state.player(c.controller).hand) {
     if(!c.state.objectExists(id))continue;
     const auto& o=c.state.getObject(id);
     if(!o.isUnit()||o.card_def_id==kInvalidId)continue;
     if(c.executor.cardDB().get(o.card_def_id).might<might)candidates.push_back(id);
   }
   if(candidates.empty()||!c.executor.confirmNow(c.controller,
     "Transpositionist: play lower-Might unit ignoring its cost?"))return;
   const auto choice=c.executor.chooseObjectNow(c.controller,candidates,
                                      "Transpositionist: unit to play for free");
   if(choice==kInvalidId)return;
   const auto locations=playLocations(c.state,c.controller);
   const auto where=c.executor.chooseLocationNow(c.controller,locations.locations,
                                     "Transpositionist: choose play location");
   (void)c.executor.playIgnoringCost(c.controller,choice,where);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1114,115,R"RB(Transpositionist)RB",CardType::Unit,6,0,4,{Domain::Chaos},Rarity::Epic,R"RB([C], [E]: Return a friendly unit to its owner's hand. You may play a unit with less Might than that unit had, ignoring its cost.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/60cf9dbb9345d44f0a9a78b60d5fb71411b50d69-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1115 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_c(1115,120,R"RB(Meticulous Restorationist)RB",CardType::Unit,2,0,2,{Domain::Order},Rarity::Common,R"RB(When you play a card with Energy cost [7] or more, you may play me from your trash for [O].)RB");
  d.tags={R"RB(Device)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/ee50fbf5e902e7109a3d54b417edc440b5a37198-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};
}
void register_card_1100(CardRegistry& r){r.registerCard(CardDefId{1100},std::make_unique<R64_1100>());}
void register_card_1101(CardRegistry& r){r.registerCard(CardDefId{1101},std::make_unique<R64_1101>());}
void register_card_1102(CardRegistry& r){r.registerCard(CardDefId{1102},std::make_unique<R64_1102>());}
void register_card_1103(CardRegistry& r){r.registerCard(CardDefId{1103},std::make_unique<R64_1103>());}
void register_card_1104(CardRegistry& r){r.registerCard(CardDefId{1104},std::make_unique<R64_1104>());}
void register_card_1105(CardRegistry& r){r.registerCard(CardDefId{1105},std::make_unique<R64_1105>());}
void register_card_1106(CardRegistry& r){r.registerCard(CardDefId{1106},std::make_unique<R64_1106>());}
void register_card_1107(CardRegistry& r){r.registerCard(CardDefId{1107},std::make_unique<R64_1107>());}
void register_card_1108(CardRegistry& r){r.registerCard(CardDefId{1108},std::make_unique<R64_1108>());}
void register_card_1109(CardRegistry& r){r.registerCard(CardDefId{1109},std::make_unique<R64_1109>());}
void register_card_1110(CardRegistry& r){r.registerCard(CardDefId{1110},std::make_unique<R64_1110>());}
void register_card_1111(CardRegistry& r){r.registerCard(CardDefId{1111},std::make_unique<R64_1111>());}
void register_card_1112(CardRegistry& r){r.registerCard(CardDefId{1112},std::make_unique<R64_1112>());}
void register_card_1113(CardRegistry& r){r.registerCard(CardDefId{1113},std::make_unique<R64_1113>());}
void register_card_1114(CardRegistry& r){r.registerCard(CardDefId{1114},std::make_unique<R64_1114>());}
void register_card_1115(CardRegistry& r){r.registerCard(CardDefId{1115},std::make_unique<R64_1115>());}
} // namespace riftbound
