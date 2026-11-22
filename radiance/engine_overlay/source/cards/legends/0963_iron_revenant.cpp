#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class IronRevenant final : public LegendCard {
public:
 const CardDef& def() const override{return def_;}
 bool hasActivatedAbility() const override{return true;}
 bool isReactionAbility() const override{return true;}
 bool abilityAddsResources() const override{return true;}
 ActivationCost getActivationCost() const override{return {.exhaust=true};}
 bool canActivateAbility(const GameState& state,PlayerId p) const override{
  for(auto id:state.player(p).trash){
   if(!state.objectExists(id))continue;
   const auto& c=state.getObject(id);
   if(c.isUnit()||c.isGear())return true;
  }
  return false;
 }
 void onActivate(CardContext& ctx,const std::vector<GameObjectId>&)override{
  std::vector<GameObjectId> cost_cards;
  for(auto id:ctx.state.player(ctx.controller).trash){
   if(!ctx.state.objectExists(id))continue;
   const auto& c=ctx.state.getObject(id);
   if(c.isUnit()||c.isGear())cost_cards.push_back(id);
  }
  if(cost_cards.empty())return;
  const auto chosen=ctx.executor.chooseObjectNow(ctx.controller,cost_cards,
                 "Mordekaiser: banish unit or gear from trash as a cost");
  if(chosen==kInvalidId||!ctx.state.objectExists(chosen))return;
  ctx.executor.banishObject(chosen);
  if(!ctx.state.objectExists(chosen)||ctx.state.getObject(chosen).zone!=ZoneType::Banishment)return;
  ++ctx.state.player(ctx.controller).rune_pool.unit_or_gear_power;
 }
private:
 const CardDef def_=[] {
  CardDef d;d.id=963;d.def_id="rad-143-167";d.name="Iron Revenant";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-143/167";
  d.collector_number=143;d.card_type=CardType::Legend;d.rarity=Rarity::Rare;
  d.domains={Domain::Fury,Domain::Order};d.tags={"Mordekaiser"};
  d.ability_text="[Reaction] Banish a unit or gear from your trash, exhaust me: [Add] [A]. Spend only to play units or gear.";
  return d;
 }();
};
}
void register_card_963(CardRegistry& r){r.registerCard(963,std::make_unique<IronRevenant>());}
} // namespace riftbound
