#include "cards/card.h"
#include "cards/card_registry.h"
#include "cards/card_helpers.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class NtofoStrikes final : public SpellCard {
public:
 const CardDef& def() const override { return def_; }
 unsigned choicesAtFinalization() const override {return kFinalizeResolve;}
 FinalizeChoice mayChooseAtFinalization(const GameState& state,PlayerId controller,GameObjectId object)const override{
  return friendlyUnitChoice(state,controller,object);
 }
 TargetRequirements getTargetRequirements() const override{
  return TargetRequirements{.count=2,.must_be_unit=true};
 }
 bool needsPlayTimeTargetPair() const override{return true;}
 bool hasLegalTargets(const GameState& state,PlayerId controller)const override{
  bool friendly=false,enemy=false;
  for(const auto& [id,obj]:state.objects.onBoard()){
   if(!obj.isUnit()||!obj.location)continue;
   if(obj.controller==controller)friendly=true;
   else if(!obj.untargetable_by_enemy)enemy=true;
  }
  return friendly&&enemy;
 }
 void onResolve(CardContext& ctx,const std::vector<GameObjectId>&)override{
  std::vector<GameObjectId> friendlies;
  for(const auto& [id,obj]:ctx.state.objects.onBoard())
   if(obj.isUnit()&&obj.location&&obj.controller==ctx.controller)friendlies.push_back(id);
  auto enemies=[&](GameObjectId){
   std::vector<GameObjectId> v;
   for(const auto& [id,obj]:ctx.state.objects.onBoard())
    if(obj.isUnit()&&obj.location&&obj.controller!=ctx.controller&&!obj.untargetable_by_enemy)
     v.push_back(id);
   return v;
  };
  auto [friendly,enemy]=pickTargetPair(ctx,"Ntofo Strikes",friendlies,enemies);
  if(finalizingChoices(ctx))return;
  if(friendly==kInvalidId||enemy==kInvalidId)return;
  if(!ctx.state.objectExists(friendly)||!ctx.state.objectExists(enemy))return;
  const auto& f=ctx.state.getObject(friendly);
  const auto& e=ctx.state.getObject(enemy);
  if(!f.isUnit()||f.controller!=ctx.controller||!f.location||!e.isUnit()||e.controller==ctx.controller||!e.location)return;
  ctx.executor.giveTemporaryKeyword(friendly,Keyword::Shield,2);
  const int damage=ctx.state.getObject(friendly).shield_value;
  ctx.executor.dealDamage(enemy,damage,ctx.source);
  ctx.executor.killLethallyDamagedTogether(std::vector<GameObjectId>{enemy});
 }
private:
 const CardDef def_=[]{
  CardDef d;d.id=961;d.def_id="rad-148-167";d.name="Ntofo Strikes";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-148/167";
  d.collector_number=148;d.card_type=CardType::Spell;
  d.super_type=SuperType::Signature;d.domains={Domain::Calm,Domain::Body};
  d.tags={"K\'Sante"};
  d.energy_cost=2;d.power_cost=1;d.rarity=Rarity::Epic;
  d.keywords.set(Keyword::Action);
  d.ability_text="[Action] Give a friendly unit [Shield 2] this turn, then deal damage equal to its [Shield] to an enemy unit.";
  return d;
 }();
};
}
void register_card_961(CardRegistry& r){r.registerCard(961,std::make_unique<NtofoStrikes>());}
} // namespace riftbound
