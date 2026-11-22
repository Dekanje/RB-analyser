#include "cards/card.h"
#include "cards/card_registry.h"
#include "cards/card_helpers.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class RealmOfDeath final : public SpellCard {
public:
 const CardDef& def() const override{return def_;}
 unsigned choicesAtFinalization() const override{return kFinalizeResolve;}
 FinalizeChoice mayChooseAtFinalization(const GameState& state,PlayerId player,GameObjectId id)const override{
  return friendlyUnitChoice(state,player,id);
 }
 TargetRequirements getTargetRequirements() const override{return {.count=2,.must_be_unit=true};}
 bool needsPlayTimeTargetPair()const override{return true;}
 bool hasLegalTargets(const GameState& state,PlayerId p)const override{
  bool mine=false,enemy=false;
  for(const auto& [id,u]:state.objects.onBoard()){
   if(!u.isUnit()||!u.location)continue;
   if(u.controller==p)mine=true;
   else if(!u.untargetable_by_enemy)enemy=true;
  }
  return mine&&enemy;
 }
 void onResolve(CardContext& ctx,const std::vector<GameObjectId>&)override{
  std::vector<GameObjectId> mine;
  for(const auto& [id,u]:ctx.state.objects.onBoard())
   if(u.isUnit()&&u.location&&u.controller==ctx.controller)mine.push_back(id);
  auto foes=[&](GameObjectId){
   std::vector<GameObjectId> r;
   for(const auto& [id,u]:ctx.state.objects.onBoard())
    if(u.isUnit()&&u.location&&u.controller!=ctx.controller&&!u.untargetable_by_enemy)r.push_back(id);
   return r;
  };
  auto [friendly,enemy]=pickTargetPair(ctx,"Realm of Death",mine,foes);
  if(finalizingChoices(ctx))return;
  if(friendly==kInvalidId||enemy==kInvalidId||
     !ctx.state.objectExists(friendly)||!ctx.state.objectExists(enemy))return;
  ctx.executor.giveTemporaryMight(friendly,2);
  ctx.executor.giveTemporaryMight(enemy,-2);
  const int f=ctx.state.getObject(friendly).current_might;
  const int e=ctx.state.getObject(enemy).current_might;
  ctx.executor.dealDamage(enemy,f,ctx.source);
  ctx.executor.dealDamage(friendly,e,ctx.source);
  ctx.executor.killLethallyDamagedTogether(std::vector<GameObjectId>{friendly,enemy});
 }
private:
 const CardDef def_=[] {
  CardDef d;d.id=965;d.def_id="rad-144-167";d.name="Realm of Death";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-144/167";
  d.collector_number=144;d.card_type=CardType::Spell;d.super_type=SuperType::Signature;
  d.domains={Domain::Fury,Domain::Order};d.tags={"Mordekaiser"};d.energy_cost=2;d.power_cost=1;
  d.rarity=Rarity::Epic;
  d.ability_text="Give an enemy unit -2 Might this turn and a friendly unit +2 Might this turn. They deal damage equal to their Mights to each other.";
  return d;
 }();
};
}
void register_card_965(CardRegistry& r){r.registerCard(965,std::make_unique<RealmOfDeath>());}
} // namespace riftbound
