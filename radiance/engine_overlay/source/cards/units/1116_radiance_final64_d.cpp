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
CardDef mkFinal64_d(int id,int num,const char* name,CardType type,int energy,int power,int might,
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

class R64_1116 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }
 bool hasEquipAbility()const override{return true;}
 EquipCost equipCost(const GameState&,PlayerId,GameObjectId,GameObjectId)const override{
   return {.valid=true,.energy=1};
 }
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1116,123,R"RB(Protector's Shield)RB",CardType::Gear,2,1,1,{Domain::Order},Rarity::Common,R"RB([Quick-Draw] (This has [Reaction]. When you play it, attach it to a unit you control.)
[Equip] [1] ([1]: Attach this to a unit you control.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/97618bc30e9b65a2e5223e6f94db58d7098d30a6-744x1039.png?accountingTag=RB)RB";
  d.tags={"Equipment"};
  d.might_bonus=1;
  d.keywords.set(Keyword::QuickDraw);
  d.keywords.set(Keyword::Equip);
  d.keywords.set(Keyword::Reaction);
  return d;
 }();
};

class R64_1117 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }

 static bool eligible(const GameState& s,GameObjectId id){
   if(!s.objectExists(id))return false;
   const auto& o=s.getObject(id);
   return o.location&&(o.isGear()||(o.isUnit()&&o.current_might<=3));
 }
 bool canBePlayed(const GameState& s,PlayerId)const override{
   for(const auto& [id,o]:s.objects.onBoard())if(eligible(s,id))return true;
   return false;
 }
 unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
 FinalizeChoice mayChooseAtFinalization(const GameState& s,PlayerId,GameObjectId id)const override{
   return eligible(s,id)?FinalizeChoice::Yes:FinalizeChoice::No;
 }
 void onResolve(CardContext& c,const std::vector<GameObjectId>&)override{
   std::vector<GameObjectId> options;
   for(const auto& [id,o]:c.state.objects.onBoard())if(eligible(c.state,id))options.push_back(id);
   std::sort(options.begin(),options.end());
   const auto target=pickTarget(c,"Burn Away: banish gear or small unit",options);
   if(finalizingChoices(c))return;
   if(target==kInvalidId)return;
   c.executor.banishObject(target,c.controller);
   c.executor.burn(c.controller,2);
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1117,124,R"RB(Burn Away)RB",CardType::Spell,3,1,0,{Domain::Order},Rarity::Uncommon,R"RB(Banish a unit with 3 [M] or less or a gear. [Burn 2]. (Put the top 2 cards of your Main Deck into your trash.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/751629a34ee6ba6476ce2f0a821b9f84b5562acd-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1118 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 static std::vector<GameObjectId> friendlyUnits(const GameState& s,PlayerId p){
   std::vector<GameObjectId> out;
   for(const auto& [id,o]:s.objects.onBoard())
     if(o.isUnit()&&o.controller==p&&o.location)out.push_back(id);
   std::sort(out.begin(),out.end());
   return out;
 }
 AdditionalPlayCost additionalPlayCost(const GameState& s,const CardDB&,PlayerId p,GameObjectId)const override{
   AdditionalPlayCost cost;
   cost.exists=true;
   cost.payable=!friendlyUnits(s,p).empty();
   cost.best.energy_reduction=2;
   return cost;
 }
 PlayCostAdjust payAdditionalPlayCost(CardContext& c,
   const std::function<bool(const PlayCostAdjust&)>& affordable)override{
   const auto candidates=friendlyUnits(c.state,c.controller);
   if(candidates.empty())return {};
   if(affordable(PlayCostAdjust{})&&
      !c.executor.confirmNow(c.controller,
       "Dune Devourer: kill a friendly unit to pay 2 less"))return {};
   const auto chosen=c.executor.chooseObjectNow(c.controller,candidates,
     "Dune Devourer: choose a friendly unit to kill as additional play cost");
   if(chosen==kInvalidId)return {};
   c.executor.killObject(chosen);
   return {.energy_reduction=2};
 }
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1118,125,R"RB(Dune Devourer)RB",CardType::Unit,7,1,7,{Domain::Order},Rarity::Uncommon,R"RB(You may kill a friendly unit as an additional cost to play me. If you do, I cost [2] less.
[Deflect] (Opponents must pay [A] to choose me with a spell or ability.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/4f49bf38f0d3abb71e148783ebec97f446db8166-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Deflect);
  d.deflect_value=1;
  return d;
 }();
};

class R64_1119 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }

 void asYouPlayChoices(CardContext& c)override{
   (void)f64ShowOff(c,[](const GameObject&,const CardDef& d){
     return d.energy_cost>=7;
   },"Rousing Display: Show Off a card costing 7 or more");
 }
 void onResolve(CardContext& c,const std::vector<GameObjectId>&)override{
   const int n=f64WasShownOff(c.state,c.source)?4:2;
   for(int i=0;i<n;i++)f64Recruit(c,BaseLocation{c.controller});
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1119,127,R"RB(Rousing Display)RB",CardType::Spell,5,0,0,{Domain::Order},Rarity::Uncommon,R"RB([Show Off] a card with Energy cost [7] or more. (As you play this, you may reveal such a card from hand or pick a friendly one.)
Play two 1 [M] Recruit unit tokens to your base. If you showed off, play four to your base instead.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/18aa7cab082fd0e293260bcf480a1a76d12b64d9-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1120 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 TriggerType triggerType() const override{return TriggerType::WhenYouPlayMe;}
 static std::vector<GameObjectId> topFour(const CardContext& c){
   std::vector<GameObjectId> out;
   const auto& deck=c.state.player(c.controller).main_deck;
   for(auto it=deck.rbegin();it!=deck.rend()&&out.size()<4;++it)
     if(c.state.objectExists(*it))out.push_back(*it);
   return out;
 }
 static std::vector<GameObjectId> eligible(CardContext& c){
   std::vector<GameObjectId> out;
   for(auto id:topFour(c)){
     const auto& o=c.state.getObject(id);
     if(!o.isUnit()&&!o.isGear())continue;
     const auto& d=c.executor.cardDB().get(o.card_def_id);
     if(d.energy_cost<=3&&d.power_cost<=1)out.push_back(id);
   }
   return out;
 }
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   const auto& ri=c.state.chain.resuming;
   for(auto id:topFour(c))
     knowledge::shown(c.state,id,knowledge::only(c.controller));
   const int yes=confirmOptional(c,"Trifarian Captain: reveal a cheap unit or gear from top 4 and draw?",[&]{
      return !eligible(c).empty();
   });
   if(yes==-1)return;
   const auto top=topFour(c);
   GameObjectId chosen=kInvalidId;
   if(yes==1){
     chosen=pickUnseenCard(c,"Trifarian Captain: choose unit or gear to reveal",eligible(c));
     if(chosen==kInvalidId&&ri.has_value()&&ri->resume_point==7)return;
   }
   std::vector<GameObjectId> recycle;
   for(auto id:top){
     deck::take(c.state,id,deck::Place::Held,knowledge::only(c.controller),false);
     if(id!=chosen)recycle.push_back(id);
   }
   if(!recycle.empty())c.executor.recycleCards(c.controller,recycle);
   if(chosen!=kInvalidId&&c.state.objectExists(chosen)){
     const auto& card=c.state.getObject(chosen);
     c.events.emit(CardRevealedEvent{chosen,card.card_def_id,card.owner,
       true,c.controller,ZoneType::MainDeck});
     deck::putOnTop(c.state,c.controller,chosen,deck::Place::Held,knowledge::everyone());
     c.executor.drawCards(c.controller,1);
   }
 }
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1120,129,R"RB(Trifarian Captain)RB",CardType::Unit,2,0,1,{Domain::Order},Rarity::Uncommon,R"RB(When you play me, look at the top 4 cards of your Main Deck. You may reveal from among them a unit or gear with Energy cost no more than [3] and with Power cost no more than [A] and draw it. Recycle the rest.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/914ced10400826a878ed5cf7294207a4e7b542b1-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1121 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1121,130,R"RB(Battlefield Armorer)RB",CardType::Unit,3,0,3,{Domain::Order},Rarity::Rare,R"RB(When a friendly gear at a battlefield dies, you may pay [1] to return it to its owner's hand.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/eb04c39763de8fb8e56153d1f0e4f799e15dced9-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1122 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 TriggerType triggerType()const override{return TriggerType::WhenAFriendlyUnitDies;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override{
   std::vector<GameObjectId> allies;
   for(const auto& [id,o]:c.state.objects.onBoard())
      if(o.isUnit()&&o.controller==c.controller&&o.location)allies.push_back(id);
   std::sort(allies.begin(),allies.end());
   const auto target=pickTarget(c,"Demacian Illuminators: Buff friendly unit",allies);
   if(finalizingChoices(c))return;
   if(target!=kInvalidId)c.executor.buffUnit(target);
 }
 // MECHANICS_INCOMPLETE: remaining timing/interaction cases under review.

private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1122,131,R"RB(Demacian Illuminators)RB",CardType::Unit,3,1,3,{Domain::Order},Rarity::Rare,R"RB(When one or more friendly units die, [Buff] a friendly unit. (Give it a +1 [M] buff if it doesn't have one.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/127c2700ee4e2557dfd463ed84c45f4600ad9723-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1123 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1123,132,R"RB(Heimerdinger, Academy Instructor)RB",CardType::Unit,6,1,5,{Domain::Order},Rarity::Rare,R"RB(If you would play a unit token to a location while I'm at a battlefield, you may play a 3 [M] Mech unit token to that same location instead.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Yordle)RB",R"RB(Heimerdinger)RB",R"RB(Piltover)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/1795e905171c74b84b4b7f84a57fecbb4bbd6f75-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1124 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }

 void onResolve(CardContext& c,const std::vector<GameObjectId>&)override{
   std::vector<GameObjectId> allies;
   for(const auto& [id,o]:c.state.objects.onBoard())
     if(o.isUnit()&&o.controller==c.controller&&o.location)allies.push_back(id);
   std::sort(allies.begin(),allies.end());
   for(const auto id:allies){
     if(!c.state.objectExists(id)||!c.state.getObject(id).location)continue;
     c.executor.readyObject(id);
     c.executor.giveTemporaryMight(id,3);
   }
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1124,134,R"RB(Raucous Anthem)RB",CardType::Spell,7,1,0,{Domain::Order},Rarity::Rare,R"RB(Ready your units and give them +3 [M] this turn.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/0c307d5f4785efc4f0a4c8e486b53735f8cf04aa-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1125 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1125,135,R"RB(Remember the Fallen)RB",CardType::Spell,8,2,0,{Domain::Order},Rarity::Rare,R"RB(Play up to 3 units and/or gear from your trash, each with Energy cost no more than [3] and Power cost no more than [A], ignoring their costs.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/0bfd45446d5ffb816438ae2668ad4e5b7f188ad3-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1126 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1126,136,R"RB(Dockside Lock-Up)RB",CardType::Gear,6,2,0,{Domain::Order},Rarity::Epic,R"RB([Deploy] (Play this only to a battlefield. When an opponent holds here, kill this.)
When you play this, banish a unit here.
When you hold here, kill this to play the banished card, ignoring its cost. (Tokens aren't cards.))RB");
  d.tags={R"RB(Device)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/4f477ccc474cb16e4e9d681b388f0673f77fae5b-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Deploy);
  return d;
 }();
};

class R64_1127 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1127,137,R"RB(Mordekaiser, Dominating)RB",CardType::Unit,9,2,8,{Domain::Order},Rarity::Epic,R"RB(When you play me or when I attack, you may discard 1 to kill a unit or gear.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Noxus)RB",R"RB(Mordekaiser)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/43068166258356908b364566abcfc57123e96caa-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1128 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }

 std::vector<TriggerType> triggerTypes()const override{
   return {TriggerType::WhenYouPlayMe,TriggerType::WhenIBecomeExhausted};
 }
 void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
   c.executor.createToken(c.controller,CardType::Unit,"Recruit",1,{"Recruit"},
                          KeywordSet{},BaseLocation{c.controller},false);
 }
 void applyPassiveAura(GameState& s,PlayerId p)const override{
   forEachSelfOnce(*this,s,p,[&](GameObjectId source,GameObject& self){
     if(!self.location)return;
     int exhausted=0;
     for(const auto& [id,o]:s.objects.onBoard())
       if(id!=source&&o.isUnit()&&o.controller==p&&o.location&&o.is_exhausted)
         ++exhausted;
     if(exhausted)auraMight(self,source,exhausted);
   });
 }

private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1128,138,R"RB(Seraphine, Not Alone)RB",CardType::Unit,5,1,1,{Domain::Order},Rarity::Epic,R"RB(When you play me or when I become exhausted, play a 1 [M] Recruit unit token to your base.
I have +1 [M] for each other exhausted unit you control.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Piltover)RB",R"RB(Seraphine)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/756f0d5d9e83ba0ebcfaf1b69055fdc29458b084-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1129 final : public BattlefieldCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1129,158,R"RB(Black Market)RB",CardType::Battlefield,0,0,0,{},Rarity::Uncommon,R"RB([A][A]: Draw 1. Each player may use this ability once on their turn (even if they don't control this battlefield).)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/9a02ae108f32a8b88be47a94b5f0d39b5a06a6a1-1039x744.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1130 final : public BattlefieldCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1130,163,R"RB(Hunters' Circle)RB",CardType::Battlefield,0,0,0,{},Rarity::Uncommon,R"RB(For each player, the first unit or gear they play here on their turn costs [1] less.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/e7e25d90506d805f1996e7f751cb5b6baa8ec305-1039x744.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1131 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64_d(1131,167,R"RB(Neeko, Blending In)RB",CardType::Unit,6,1,4,{},Rarity::Epic,R"RB((Neutral cards can go in decks of any Domain.)
If Neeko is in your deck, choose 3 different legends in addition to your starting legend. (Different means none match names.)
When you play me, choose one of those legends and add it to your Legend Zone while I'm on the board.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Ixtal)RB",R"RB(Neeko)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/607da6f534ce1b960ad02586ed4cd47c996e2c42-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};
}
void register_card_1116(CardRegistry& r){r.registerCard(CardDefId{1116},std::make_unique<R64_1116>());}
void register_card_1117(CardRegistry& r){r.registerCard(CardDefId{1117},std::make_unique<R64_1117>());}
void register_card_1118(CardRegistry& r){r.registerCard(CardDefId{1118},std::make_unique<R64_1118>());}
void register_card_1119(CardRegistry& r){r.registerCard(CardDefId{1119},std::make_unique<R64_1119>());}
void register_card_1120(CardRegistry& r){r.registerCard(CardDefId{1120},std::make_unique<R64_1120>());}
void register_card_1121(CardRegistry& r){r.registerCard(CardDefId{1121},std::make_unique<R64_1121>());}
void register_card_1122(CardRegistry& r){r.registerCard(CardDefId{1122},std::make_unique<R64_1122>());}
void register_card_1123(CardRegistry& r){r.registerCard(CardDefId{1123},std::make_unique<R64_1123>());}
void register_card_1124(CardRegistry& r){r.registerCard(CardDefId{1124},std::make_unique<R64_1124>());}
void register_card_1125(CardRegistry& r){r.registerCard(CardDefId{1125},std::make_unique<R64_1125>());}
void register_card_1126(CardRegistry& r){r.registerCard(CardDefId{1126},std::make_unique<R64_1126>());}
void register_card_1127(CardRegistry& r){r.registerCard(CardDefId{1127},std::make_unique<R64_1127>());}
void register_card_1128(CardRegistry& r){r.registerCard(CardDefId{1128},std::make_unique<R64_1128>());}
void register_card_1129(CardRegistry& r){r.registerCard(CardDefId{1129},std::make_unique<R64_1129>());}
void register_card_1130(CardRegistry& r){r.registerCard(CardDefId{1130},std::make_unique<R64_1130>());}
void register_card_1131(CardRegistry& r){r.registerCard(CardDefId{1131},std::make_unique<R64_1131>());}
} // namespace riftbound
