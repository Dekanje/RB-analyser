// Radiance Batch 10, tranche B: ten additional unique identities.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <string>
#include <vector>
namespace riftbound {
namespace {
CardDef rad10b(int id,int n,const char* name,CardType type,int energy,int power,int might,
               std::vector<Domain> domains,Rarity rarity,const char* rules,
               std::initializer_list<Keyword> keywords={}) {
  CardDef d;d.id=CardDefId::fromRaw(id);auto s=std::to_string(n);
  d.def_id="rad-"+std::string(3-s.size(),'0')+s+"-167";
  d.public_code="RAD-"+std::string(3-s.size(),'0')+s+"/167";
  d.name=name;d.set_code="RAD";d.set_name="Radiance";d.collector_number=n;
  d.card_type=type;d.energy_cost=energy;d.power_cost=power;d.might=might;
  d.domains=std::move(domains);d.rarity=rarity;d.ability_text=rules;
  for(auto kw:keywords)d.keywords.set(kw);
  if(d.keywords.has(Keyword::Assault))d.assault_value=1;
  if(d.keywords.has(Keyword::Deflect))d.deflect_value=1;
  return d;
}
std::vector<GameObjectId> units10b(const GameState& s,PlayerId p,bool friendly) {
  std::vector<GameObjectId> v;for(const auto& [id,o]:s.objects.onBoard())
    if(o.location&&o.isUnit()&&((o.controller==p)==friendly))v.push_back(id);
  std::sort(v.begin(),v.end());return v;
}
class Radiance10_1058 final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
    bool entersReadyOnPlay(const GameState& state,PlayerId player)const override {
       return state.player(player).unit_died_this_turn;
    }
    // Friendly gear-death tracking is not yet available in this version.
private:
 const CardDef d_=rad10b(1058,5,"Lingering Animus",CardType::Unit,2,0,2,{Domain::Fury},Rarity::Common,"I enter ready if a friendly unit or gear died this turn.",{});
};
class Radiance10_1059 final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
    bool entersReadyOnPlay()const override{return true;}
    // [Assault] is engine-provided; optional banish/replay activation pending.
private:
 const CardDef d_=rad10b(1059,21,"Ekko, Revolutionary",CardType::Unit,5,1,4,{Domain::Fury},Rarity::Epic,"I enter ready.\n[Assault] (+1 [M] while I'm an attacker.)\n[Action][>] Discard 1, [1][R]: Banish me, then play me to your base, ignoring my cost.",{Keyword::Assault,Keyword::Action});
};
class Radiance10_1060 final:public SpellCard {
public:
 const CardDef& def()const override{return d_;}
    void onResolve(CardContext& c,const std::vector<GameObjectId>&)override {
       auto friendly=units10b(c.state,c.controller,true);
       auto cost=pickTarget(c,"Ki Burst: exhaust a friendly unit as cost",friendly);
       if(finalizingChoices(c)||cost==kInvalidId)return;
       c.executor.exhaustObject(cost);
       auto enemy=units10b(c.state,c.controller,false);
       auto target=pickTarget(c,"Ki Burst: stun a unit",enemy);
       if(target!=kInvalidId)c.executor.stunUnitBy(target,c.source);
    }
    // Cost timing and targeting during cast remain unverified.
private:
 const CardDef d_=rad10b(1060,28,"Ki Burst",CardType::Spell,1,0,0,{Domain::Calm},Rarity::Common,"[Action] (Play on your turn or in showdowns.)\nAs an additional cost to play this, exhaust a friendly unit.\n[Stun] a unit. (It doesn't deal combat damage this turn.)",{Keyword::Action});
};
class Radiance10_1061 final:public SpellCard {
public:
 const CardDef& def()const override{return d_;}
    void onResolve(CardContext& c,const std::vector<GameObjectId>&)override {
       auto friendly=units10b(c.state,c.controller,true);
       auto cost=pickTarget(c,"Life from Stone: exhaust a friendly unit as cost",friendly);
       if(finalizingChoices(c)||cost==kInvalidId)return;
       c.executor.exhaustObject(cost);
       c.executor.drawCards(c.controller,1);
       c.executor.channelRunes(c.controller,1,true);
    }
    // Cost must ultimately be paid as the spell is played, not on resolution.
private:
 const CardDef d_=rad10b(1061,29,"Life from Stone",CardType::Spell,1,0,0,{Domain::Calm},Rarity::Common,"[Reaction] (Play any time, even before spells and abilities resolve.)\nAs an additional cost to play this, exhaust a friendly unit.\nDraw 1 and channel 1 rune exhausted.",{Keyword::Reaction});
};
class Radiance10_1062 final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
    void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
       // Ready a friendly legend; activated-ability grant still pending.
       for(const auto& [id,o]:c.state.objects.onBoard())
         if(o.controller==c.controller&&o.card_type==CardType::Legend) {
           c.executor.readyObject(id);break;
         }
    }
private:
 const CardDef d_=rad10b(1062,40,"Heartening Soul",CardType::Unit,7,1,7,{Domain::Calm},Rarity::Rare,"When you play me, ready a friendly legend.\nFriendly legends have \"[E]: Give a unit +3 [M] this turn.\"",{});
};
class Radiance10_1063 final:public SpellCard {
public:
 const CardDef& def()const override{return d_;}
    // Next three friendly unit plays need a duration-limited delayed effect.
private:
 const CardDef d_=rad10b(1063,47,"Fanfare",CardType::Spell,3,0,0,{},Rarity::Common,"The next three times you play a unit this turn, draw 1.",{});
};
class Radiance10_1064 final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
    // [Ganking] is engine-provided. Return-friendly-unit play cost pending.
private:
 const CardDef d_=rad10b(1064,61,"Ekko, Ingenious",CardType::Unit,3,0,4,{Domain::Mind},Rarity::Rare,"As an additional cost to play me, return a friendly unit to its owner's hand.\n[Ganking] (I can move from battlefield to battlefield.)",{Keyword::Ganking});
};
class Radiance10_1065 final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
    // [Deflect] is engine-provided. Optional bounce-discount cost pending.
private:
 const CardDef d_=rad10b(1065,75,"Skystrike Squadron",CardType::Unit,5,0,4,{Domain::Body},Rarity::Common,"You may return a friendly gear to its owner's hand as an additional cost to play me. If you do, I cost [2] less.\n[Deflect] (Opponents must pay [A] to choose me with a spell or ability.)",{Keyword::Deflect});
};
class Radiance10_1066 final:public GearCard {
public:
 const CardDef& def()const override{return d_;}
    std::vector<TriggerType> triggerTypes()const override {
       return {TriggerType::WhenYouPlayThis,TriggerType::WhenYouConquerHere};
    }
    void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
       // Optional [1] payment to create a Recruit is not yet connected.
       (void)c;
    }
private:
 const CardDef d_=rad10b(1066,116,"Concert Poster",CardType::Gear,1,0,0,{Domain::Order},Rarity::Common,"[Deploy] (Play this only to a battlefield. When an opponent holds here, kill this.)\nWhen you play this or when you conquer here, you may pay [1] to play a 1 [M] Recruit unit token to your base.",{Keyword::Deploy});
};
class Radiance10_1067 final:public SpellCard {
public:
 const CardDef& def()const override{return d_;}
    void onResolve(CardContext& c,const std::vector<GameObjectId>&)override {
      auto ally=units10b(c.state,c.controller,true);
      auto enemy=units10b(c.state,c.controller,false);
      auto [a,e]=pickTargetPair(c,"One-Two Punch: buff friend then stun enemy",
        ally,[&](GameObjectId){return units10b(c.state,c.controller,false);});
      if(finalizingChoices(c))return;
      if(a!=kInvalidId)c.executor.buffUnit(a);
      if(e!=kInvalidId)c.executor.stunUnitBy(e,c.source);
    }
private:
 const CardDef d_=rad10b(1067,121,"One-Two Punch",CardType::Spell,3,0,0,{},Rarity::Common,"[Action] (Play on your turn or in showdowns.)\n[Buff] a friendly unit and [Stun] an enemy unit. (Give the friendly unit a +1 [M] buff if it doesn't have one. The enemy unit doesn't deal combat damage this turn.)",{Keyword::Action});
};
} // anonymous
void register_card_1058(CardRegistry& r){r.registerCard(1058,std::make_unique<Radiance10_1058>());}
void register_card_1059(CardRegistry& r){r.registerCard(1059,std::make_unique<Radiance10_1059>());}
void register_card_1060(CardRegistry& r){r.registerCard(1060,std::make_unique<Radiance10_1060>());}
void register_card_1061(CardRegistry& r){r.registerCard(1061,std::make_unique<Radiance10_1061>());}
void register_card_1062(CardRegistry& r){r.registerCard(1062,std::make_unique<Radiance10_1062>());}
void register_card_1063(CardRegistry& r){r.registerCard(1063,std::make_unique<Radiance10_1063>());}
void register_card_1064(CardRegistry& r){r.registerCard(1064,std::make_unique<Radiance10_1064>());}
void register_card_1065(CardRegistry& r){r.registerCard(1065,std::make_unique<Radiance10_1065>());}
void register_card_1066(CardRegistry& r){r.registerCard(1066,std::make_unique<Radiance10_1066>());}
void register_card_1067(CardRegistry& r){r.registerCard(1067,std::make_unique<Radiance10_1067>());}
} // namespace riftbound
