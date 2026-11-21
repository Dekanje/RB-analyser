#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/events.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <optional>
#include <vector>

namespace riftbound {
namespace {

class BattlePreparations final : public SpellCard {
public:
 const CardDef& def() const override { return def_; }
 TargetRequirements getTargetRequirements() const override {
  return TargetRequirements{.count=1,.must_be_unit=true};
 }
 bool needsPlayTimeTarget() const override { return true; }
 unsigned choicesAtFinalization() const override { return kFinalizeResolve; }
 FinalizeChoice mayChooseAtFinalization(const GameState& state,
     PlayerId controller, GameObjectId object) const override {
  if (!state.objectExists(object)) return FinalizeChoice::No;
  const auto& u=state.getObject(object);
  return u.isUnit() && u.location.has_value() ? FinalizeChoice::Yes : FinalizeChoice::No;
 }
 void asYouPlayChoices(CardContext& ctx) override {
  std::vector<GameObjectId> gears;
  for (auto cid:ctx.state.player(ctx.controller).hand)
   if (ctx.state.objectExists(cid) && ctx.state.getObject(cid).isGear()) gears.push_back(cid);
  for (const auto& [id,obj]:ctx.state.objects.onBoard())
   if (obj.isGear() && obj.controller==ctx.controller && obj.location) gears.push_back(id);
  if (gears.empty()) return;
  std::sort(gears.begin(),gears.end());
  if (!ctx.executor.confirmNow(ctx.controller,"Battle Preparations: Show Off a gear?")) return;
  const auto chosen=ctx.executor.chooseObjectNow(ctx.controller,gears,
       "Battle Preparations: reveal gear in hand or pick friendly gear");
  if (chosen==kInvalidId || !ctx.state.objectExists(chosen)) return;
  const auto& gear=ctx.state.getObject(chosen);
  if (gear.controller!=ctx.controller && gear.owner!=ctx.controller) return;
  if (gear.zone==ZoneType::Hand)
   ctx.events.emit(CardRevealedEvent{
      chosen,gear.card_def_id,gear.owner,true,PlayerId::None,ZoneType::Hand});
  ctx.state.getObject(ctx.source).card_counters["__battle_preparations_showoff"]=1;
 }
 void onResolve(CardContext& ctx,const std::vector<GameObjectId>& targets) override {
  auto units=enumerateLegalTargets(ctx.state,ctx.controller);
  auto locked=lockedPlayTarget(ctx,targets);
  const auto picked=locked ? *locked : pickTarget(ctx,"Battle Preparations: +2 Might",units);
  const auto& counters=ctx.state.getObject(ctx.source).card_counters;
  const auto it=counters.find("__battle_preparations_showoff");
  const bool showed=(it!=counters.end()&&it->second==1);
  std::vector<GameObjectId> exhausted;
  if (showed) {
   for (const auto& [id,obj]:ctx.state.objects.onBoard())
    if(obj.isRune() && obj.location && obj.is_exhausted)exhausted.push_back(id);
  }
  std::optional<std::vector<GameObjectId>> chosen;
  if (showed) {
   chosen=selectSeveral(ctx,"Battle Preparations: ready up to two runes",
                         exhausted,2);
   if (!chosen.has_value()) return;
  }
  if (finalizingChoices(ctx)) return;
  if (picked!=kInvalidId && ctx.state.objectExists(picked))
   ctx.executor.giveTemporaryMight(picked,2);
  if (showed && chosen)
   for(auto id:*chosen)
    if(ctx.state.objectExists(id) && ctx.state.getObject(id).isRune() &&
       ctx.state.getObject(id).is_exhausted)ctx.executor.readyObject(id);
 }
private:
 const CardDef def_=[] {
  CardDef d;d.id=983;d.def_id="rad-032-167";d.name="Battle Preparations";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-032/167";
  d.collector_number=32;d.card_type=CardType::Spell;d.domains={Domain::Calm};
  d.energy_cost=2;d.rarity=Rarity::Uncommon;
  d.keywords.set(Keyword::Reaction);
  d.ability_text="[Reaction] Show Off a gear. Give a unit +2 Might this turn. If you showed off, ready up to 2 runes.";
  return d;
 }();
};

class AnOfferYouCantRefuse final:public SpellCard {
public:
 const CardDef& def()const override{return def_;}
 TargetRequirements getTargetRequirements()const override{
  return TargetRequirements{.count=1,.must_be_gear=true};
 }
 bool needsPlayTimeTarget()const override{return true;}
 void onResolve(CardContext& ctx,const std::vector<GameObjectId>& targets)override{
  auto locked=lockedPlayTarget(ctx,targets);
  const auto target=locked ? *locked :
    pickTarget(ctx,"An Offer You Can't Refuse: kill a gear",
               enumerateLegalTargets(ctx.state,ctx.controller));
  if(target==kInvalidId || !ctx.state.objectExists(target))return;
  const auto& gear=ctx.state.getObject(target);
  if(!gear.isGear() || !gear.location)return;
  const PlayerId original_controller=gear.controller;
  if(original_controller==PlayerId::None)return;
  ctx.executor.killObject(target);
  // A replaced kill does not count as killing the gear.
  if(!ctx.state.objectExists(target) ||
     !ctx.state.getObject(target).last_known.valid ||
     !ctx.state.getObject(target).last_known.died)return;
  LocationId loc{BaseLocation{original_controller}};
  ctx.executor.createToken(original_controller,CardType::Gear,"Gold",0,
           {},{},loc,false,{},kGoldGearCardDefId,true);
 }
private:
 const CardDef def_=[]{
  CardDef d;d.id=984;d.def_id="rad-101-167";d.name="An Offer You Can't Refuse";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-101/167";
  d.collector_number=101;d.card_type=CardType::Spell;d.domains={Domain::Chaos};
  d.energy_cost=2;d.rarity=Rarity::Uncommon;
  d.keywords.set(Keyword::Action);
  d.ability_text="[Action] Kill a gear. Its controller plays a Gold gear token exhausted.";
  return d;
 }();
};

class DetonationAmplifier final:public GearCard {
public:
 const CardDef& def()const override{return def_;}
 TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 std::vector<GameObjectId> sacrificeOptions(const CardContext& ctx)const {
  std::vector<GameObjectId> options;
  for(const auto& [id,obj]:ctx.state.objects.onBoard())
   if(id!=ctx.source && (obj.isGear()||obj.isUnit()) &&
      obj.location && obj.controller==ctx.controller)options.push_back(id);
  std::sort(options.begin(),options.end());return options;
 }
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
  const int yes=confirmOptional(ctx,"Detonation Amplifier: kill another friendly permanent to draw?",
        [&](){return !sacrificeOptions(ctx).empty();});
  if(yes<=0)return;
  const auto target=pickTarget(ctx,"Detonation Amplifier: choose friendly unit or gear",
                               sacrificeOptions(ctx));
  if(finalizingChoices(ctx))return;
  if(target==kInvalidId||!ctx.state.objectExists(target))return;
  const auto& obj=ctx.state.getObject(target);
  if(obj.controller!=ctx.controller || !obj.location)return;
  ctx.executor.killObject(target);
  if(ctx.state.objectExists(target) && ctx.state.getObject(target).last_known.died)
    ctx.executor.drawCards(ctx.controller,1);
 }
private:
 const CardDef def_=[]{
  CardDef d;d.id=985;d.def_id="rad-017-167";d.name="Detonation Amplifier";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-017/167";
  d.collector_number=17;d.card_type=CardType::Gear;
  d.domains={Domain::Chaos};d.tags={"Device"};d.energy_cost=4;d.power_cost=1;
  d.rarity=Rarity::Rare;d.keywords.set(Keyword::Deploy);
  d.ability_text="[Deploy] When you play this, you may kill another friendly unit or gear to draw 1. Friendly Deathknell effects here trigger an additional time.";
  return d;
 }();
};

class ElnukHerd final:public UnitCard {
public:
 const CardDef& def()const override{return def_;}
 TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 std::vector<GameObjectId> otherFriends(const CardContext& ctx)const {
  std::vector<GameObjectId> opts;
  for(const auto& [id,obj]:ctx.state.objects.onBoard())
   if(id!=ctx.source&&obj.isUnit()&&obj.location&&obj.controller==ctx.controller)
     opts.push_back(id);
  std::sort(opts.begin(),opts.end());return opts;
 }
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
  auto options=otherFriends(ctx);
  auto choice=pickTarget(ctx,"Elnuk Herd: give another friendly unit +3 Might",options);
  if(finalizingChoices(ctx))return;
  if(choice!=kInvalidId && ctx.state.objectExists(choice) &&
     ctx.state.getObject(choice).isUnit() &&
     ctx.state.getObject(choice).controller==ctx.controller)
    ctx.executor.giveTemporaryMight(choice,3);
  if(playedFromFacedown(ctx.state,ctx.source) &&
     ctx.state.objectExists(ctx.source) &&
     ctx.state.getObject(ctx.source).location)
    ctx.executor.recycleCards(ctx.controller,{ctx.source});
 }
private:
 const CardDef def_=[]{
  CardDef d;d.id=986;d.def_id="rad-081-167";d.name="Elnuk Herd";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-081/167";
  d.collector_number=81;d.card_type=CardType::Unit;d.domains={Domain::Fury};
  d.energy_cost=6;d.might=5;d.rarity=Rarity::Uncommon;
  d.keywords.set(Keyword::Hidden);
  d.ability_text="[Hidden] When you play me, give another friendly unit +3 Might this turn, then recycle me if I was played from face down.";
  return d;
 }();
};
}
void register_card_983(CardRegistry& r){r.registerCard(983,std::make_unique<BattlePreparations>());}
void register_card_984(CardRegistry& r){r.registerCard(984,std::make_unique<AnOfferYouCantRefuse>());}
void register_card_985(CardRegistry& r){r.registerCard(985,std::make_unique<DetonationAmplifier>());}
void register_card_986(CardRegistry& r){r.registerCard(986,std::make_unique<ElnukHerd>());}
} // namespace riftbound
