// Radiance Batch 10, tranche A: ten unique numbered identities.
// Ability coverage is intentionally incremental; do not treat registration as full mechanics certification.
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
CardDef rad10a(int id,int n,const char* name,CardType type,int energy,int power,int might,
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
std::vector<GameObjectId> r10units(const GameState& s,PlayerId controller,
                                    bool friendly=true) {
  std::vector<GameObjectId> v;
  for(const auto& [id,o]:s.objects.onBoard())
    if(o.location&&o.isUnit()&&(friendly?(o.controller==controller):(o.controller!=controller)))
      v.push_back(id);
  std::sort(v.begin(),v.end());return v;
}
std::vector<GameObjectId> r10gear(const GameState& s) {
  std::vector<GameObjectId> v;
  for(const auto& [id,o]:s.objects.onBoard())if(o.location&&o.isGear())v.push_back(id);
  std::sort(v.begin(),v.end());return v;
}
class Radiance10_1048 final:public SpellCard {
public:
 const CardDef& def()const override{return d_;}
    void onResolve(CardContext& c,const std::vector<GameObjectId>&)override {
      auto v=r10gear(c.state);auto units=r10units(c.state,c.controller);
      auto enemies=r10units(c.state,c.controller,false);
      v.insert(v.end(),units.begin(),units.end());v.insert(v.end(),enemies.begin(),enemies.end());
      std::sort(v.begin(),v.end());v.erase(std::unique(v.begin(),v.end()),v.end());
      auto id=pickTarget(c,"Lost to the Sands: unit to deal 4 or gear to kill",v);
      if(finalizingChoices(c)||id==kInvalidId||!c.state.objectExists(id))return;
      if(c.state.getObject(id).isGear())c.executor.killObject(id);
      else if(c.state.getObject(id).isAtBattlefield())c.executor.dealDamage(id,4,c.source);
    }
private:
 const CardDef d_=rad10a(1048,13,"Lost to the Sands",CardType::Spell,3,1,0,{Domain::Fury},Rarity::Uncommon,"[Action] (Play on your turn or in showdowns.)\nChoose one —\nDeal 4 to a unit at a battlefield.Kill a gear.",{Keyword::Action});
};
class Radiance10_1049 final:public GearCard {
public:
 const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayThis;}
    void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
      const auto v=r10units(c.state,c.controller);
      auto id=pickTarget(c,"Invigorating Bloom: +3 Might this turn",v);
      if(!finalizingChoices(c)&&id!=kInvalidId)c.executor.giveTemporaryMight(id,3);
    }
private:
 const CardDef d_=rad10a(1049,35,"Invigorating Bloom",CardType::Gear,3,0,0,{Domain::Calm},Rarity::Uncommon,"When you play this, give a friendly unit +3 [M] this turn.\nExhaust a friendly [Mighty] unit, [E]: Draw 1. (A unit is Mighty while it has 5+ [M].)",{});
};
class Radiance10_1050 final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
    // [Disarm] is executed by the shared Batch 9 attack trigger dispatcher.
    // Bonus for an enemy's reduced Might still needs a dedicated event hook.
private:
 const CardDef d_=rad10a(1050,38,"Ahri, Confident",CardType::Unit,4,1,4,{Domain::Calm},Rarity::Rare,"[Disarm] (When I attack, give an enemy unit here -1 [M] this turn.)\nWhen you reduce the Might of an enemy unit here by 1 or more, give me +1 [M] this turn.",{Keyword::Disarm});
};
class Radiance10_1051 final:public SpellCard {
public:
 const CardDef& def()const override{return d_;}
    void onResolve(CardContext& c,const std::vector<GameObjectId>&)override {
      auto friendly=r10units(c.state,c.controller);
      auto [a,b]=pickTargetPair(c,
        "Parallel Convergence: return a friendly unit, then damage a unit",
        friendly,[&](GameObjectId) {
          auto any=r10units(c.state,c.controller);
          auto enemy=r10units(c.state,c.controller,false);
          any.insert(any.end(),enemy.begin(),enemy.end());
          any.erase(std::remove_if(any.begin(),any.end(),[&](GameObjectId id) {
            return !c.state.objectExists(id)||!c.state.getObject(id).isAtBattlefield();
          }),any.end());
          std::sort(any.begin(),any.end());
          return any;
        });
      if(finalizingChoices(c))return;
      if(a!=kInvalidId)c.executor.bounceToHand(a);
      if(b!=kInvalidId)c.executor.dealDamage(b,5,c.source);
    }
private:
 const CardDef d_=rad10a(1051,51,"Parallel Convergence",CardType::Spell,2,1,0,{Domain::Mind},Rarity::Common,"As an additional cost to play this, return a friendly unit to its owner's hand.\nDeal 5 to a unit at a battlefield.",{});
};
class Radiance10_1052 final:public SpellCard {
public:
 const CardDef& def()const override{return d_;}
    void onResolve(CardContext& c,const std::vector<GameObjectId>&)override {
      auto u=r10units(c.state,c.controller),e=r10units(c.state,c.controller,false);
      u.insert(u.end(),e.begin(),e.end());std::sort(u.begin(),u.end());
      auto t=pickTarget(c,"Hold 'Em: give a unit +3 Might",u);
      if(!finalizingChoices(c)&&t!=kInvalidId)c.executor.giveTemporaryMight(t,3);
    }
private:
 const CardDef d_=rad10a(1052,70,"Hold 'Em",CardType::Spell,3,0,0,{Domain::Body},Rarity::Common,"[Action] (Play on your turn or in showdowns.)\nThis costs [2] less if you've played a unit or gear to a battlefield this turn.\nGive a unit +3 [M] this turn.",{Keyword::Action});
};
class Radiance10_1053 final:public GearCard {
public:
 const CardDef& def()const override{return d_;}
    void applyPassiveAura(GameState& s,PlayerId player)const override {
      forEachSelfOnce(*this,s,player,[&](GameObjectId source,GameObject& gear) {
        if(!gear.isAtBattlefield())return;
        for(auto& [id,unit]:s.objects.onBoard())
          if(unit.location&&unit.isUnit()&&unit.controller==player&&
             unit.battlefieldId()==gear.battlefieldId())
            auraKeyword(unit,source,Keyword::Ganking);
      });
    }
private:
 const CardDef d_=rad10a(1053,87,"Portable Portal",CardType::Gear,2,0,0,{Domain::Body},Rarity::Rare,"[Deploy] (Play this only to a battlefield. When an opponent holds here, kill this.)\nWhen you play this, you may pay [O] to ready a unit here.\nFriendly units here have [Ganking]. (They can move from battlefield to battlefield.)",{Keyword::Deploy,Keyword::Ganking});
};
class Radiance10_1054 final:public GearCard {
public:
 const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayACard;}
    void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
      if(!c.state.objectExists(c.source))return;
      auto& self=c.state.getObject(c.source);
      if(!self.location||self.is_exhausted)return;
      const auto& chain=c.state.chain.resuming;
      if(!chain||!c.state.objectExists(chain->triggering_subject))return;
      const auto& unit=c.state.getObject(chain->triggering_subject);
      if(!unit.isUnit()||unit.controller!=c.controller)return;
      int maxM=-1;
      for(const auto& [id,o]:c.state.objects.onBoard())
        if(o.isUnit()&&id!=unit.id)maxM=std::max(maxM,o.current_might);
      if(unit.current_might<=maxM)return;
      c.executor.exhaustObject(c.source);
      c.executor.drawCards(c.controller,1);
    }
private:
 const CardDef d_=rad10a(1054,89,"Titanic Shrine",CardType::Gear,3,0,0,{Domain::Body},Rarity::Rare,"When you play a unit with Might greater than each other unit on the board, exhaust me to draw 1.",{});
};
class Radiance10_1055 final:public SpellCard {
public:
 const CardDef& def()const override{return d_;}
    // TODO: Bomb gear token linked death behavior and move choice, pending mechanic tests.
private:
 const CardDef d_=rad10a(1055,96,"Satchel Charge",CardType::Spell,3,1,0,{Domain::Chaos},Rarity::Common,"[Action] (Play on your turn or in showdowns.)\nMove a friendly unit, then play a Bomb gear token to a battlefield. (It has [Deploy]. When it dies, deal 2 to an enemy there and kill your other Bombs there.)",{Keyword::Action,Keyword::Deploy});
};
class Radiance10_1056 final:public GearCard {
public:
 const CardDef& def()const override{return d_;}
    std::vector<TriggerType> triggerTypes()const override {
      return {TriggerType::WhenYouPlayThis,TriggerType::WhenYouHoldHere};
    }
    void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
      if(c.firing_trigger==TriggerType::WhenYouPlayThis) {
        c.executor.discardCards(c.controller,1);
        c.executor.drawCards(c.controller,3);
      }else if(c.firing_trigger==TriggerType::WhenYouHoldHere && c.state.objectExists(c.source))
        c.executor.bounceToHand(c.source);
    }
private:
 const CardDef d_=rad10a(1056,106,"The Good Stuff",CardType::Gear,3,1,0,{Domain::Body},Rarity::Uncommon,"[Deploy] (Play this only to a battlefield. When an opponent holds here, kill this.)\nWhen you play this, discard 1, then draw 3.\nWhen you hold here, return this to its owner's hand.",{Keyword::Deploy});
};
class Radiance10_1057 final:public UnitCard {
public:
 const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
    void onTrigger(CardContext& c,const std::vector<GameObjectId>&)override {
      // Four or more units at the chosen battlefield are required; location
      // choice should be locked at trigger finalization (follow-up test).
      std::vector<GameObjectId> v;
      for(const auto& bf:c.state.battlefields) {
        int total=0;
        for(const auto& [id,o]:c.state.objects.onBoard())
          if(o.isUnit()&&o.isAtBattlefield()&&o.battlefieldId()==bf.id)++total;
        if(total<4)continue;
        for(const auto& [id,o]:c.state.objects.onBoard())
          if(o.isUnit()&&o.controller!=c.controller&&o.battlefieldId()==bf.id)v.push_back(id);
      }
      std::sort(v.begin(),v.end());
      if(v.empty())return;
      int yes=confirmOptional(c,"Bedeviling Stranger: return an enemy unit?",[&](){return true;});
      if(yes<1)return;
      auto id=pickTarget(c,"Bedeviling Stranger: enemy unit to bounce",v);
      if(!finalizingChoices(c)&&id!=kInvalidId)c.executor.bounceToHand(id);
    }
private:
 const CardDef d_=rad10a(1057,107,"Bedeviling Stranger",CardType::Unit,2,0,2,{Domain::Chaos},Rarity::Rare,"[Hidden] (Hide now for [A] to react with later for [0].)\nWhen you play me, choose a battlefield. If there are 4 or more units there, you may return an enemy unit there to its owner's hand.",{Keyword::Hidden});
};
} // anonymous
void register_card_1048(CardRegistry& r){r.registerCard(1048,std::make_unique<Radiance10_1048>());}
void register_card_1049(CardRegistry& r){r.registerCard(1049,std::make_unique<Radiance10_1049>());}
void register_card_1050(CardRegistry& r){r.registerCard(1050,std::make_unique<Radiance10_1050>());}
void register_card_1051(CardRegistry& r){r.registerCard(1051,std::make_unique<Radiance10_1051>());}
void register_card_1052(CardRegistry& r){r.registerCard(1052,std::make_unique<Radiance10_1052>());}
void register_card_1053(CardRegistry& r){r.registerCard(1053,std::make_unique<Radiance10_1053>());}
void register_card_1054(CardRegistry& r){r.registerCard(1054,std::make_unique<Radiance10_1054>());}
void register_card_1055(CardRegistry& r){r.registerCard(1055,std::make_unique<Radiance10_1055>());}
void register_card_1056(CardRegistry& r){r.registerCard(1056,std::make_unique<Radiance10_1056>());}
void register_card_1057(CardRegistry& r){r.registerCard(1057,std::make_unique<Radiance10_1057>());}
} // namespace riftbound
