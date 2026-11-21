#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
// RAD-150/167: [Equip] costs [A] OR exhaust a friendly ready unit.
// The generic engine overlay adds an explicit optional Equip payment branch.
class BladeOfTheExile final : public GearCard {
public:
 const CardDef& def() const override { return def_; }
 bool hasEquipAbility() const override { return true; }
 EquipCost equipCost(const GameState&,PlayerId,GameObjectId,GameObjectId) const override {
  return {.valid=true,.energy=0,.power=1,.power_any_domain=true};
 }
 bool canPayEquipAlternative(const GameState& state,PlayerId controller,
                              GameObjectId,GameObjectId) const override {
  for (const auto& [id,obj] : state.objects.onBoard()) {
   if (obj.controller==controller && obj.isUnit() && !obj.is_exhausted)
    return true;
  }
  return false;
 }
 bool payEquipAlternative(CardContext& ctx,GameObjectId) override {
  std::vector<GameObjectId> candidates;
  for (const auto& [id,obj] : ctx.state.objects.onBoard()) {
   if (obj.controller==ctx.controller && obj.isUnit() && !obj.is_exhausted)
    candidates.push_back(id);
  }
  if(candidates.empty())return false;
  GameObjectId chosen=ctx.executor.chooseObjectNow(ctx.controller,candidates,
                                                   "Exhaust a friendly unit to Equip Blade of the Exile");
  if(chosen==kInvalidId || !ctx.state.objectExists(chosen) ||
     ctx.state.getObject(chosen).is_exhausted)return false;
  ctx.executor.exhaustObject(chosen);
  return ctx.state.getObject(chosen).is_exhausted;
 }
private:
 const CardDef def_ = [] {
  CardDef d; d.id=959; d.def_id="rad-150-167"; d.name="Blade of the Exile";
  d.set_code="RAD"; d.set_name="Radiance"; d.public_code="RAD-150/167";
  d.collector_number=150; d.card_type=CardType::Gear;
  d.super_type=SuperType::Signature; d.domains={Domain::Calm,Domain::Chaos};
  d.tags={"Equipment","Riven"}; d.energy_cost=3; d.power_cost=1;
  d.might_bonus=3; d.rarity=Rarity::Epic;
  d.keywords.set(Keyword::Equip);
  d.ability_text="[Equip] — [A] or exhaust a friendly unit.";
  return d;
 }();
};
}
void register_card_959(CardRegistry& r) {r.registerCard(959,std::make_unique<BladeOfTheExile>());}
} // namespace riftbound
