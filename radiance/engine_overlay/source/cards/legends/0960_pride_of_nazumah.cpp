#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class PrideOfNazumah final : public LegendCard {
public:
 const CardDef& def() const override { return def_; }
 TriggerType triggerType() const override { return TriggerType::Activated; }
 bool hasActivatedAbility() const override { return true; }
 ActivationCost getActivationCost() const override { return {.exhaust=true,.energy=1}; }
 TargetRequirements getTargetRequirements() const override {
  return TargetRequirements{.count=1,.must_be_unit=true,.must_be_friendly=true};
 }
 void onActivate(CardContext& ctx,const std::vector<GameObjectId>& targets) override {
  if(targets.empty()||!ctx.state.objectExists(targets[0]))return;
  auto& target=ctx.state.getObject(targets[0]);
  if(!target.isUnit()||target.controller!=ctx.controller||!target.location)return;
  ctx.executor.giveTemporaryKeyword(targets[0],Keyword::Assault,0);
  // Count separate grants: the printed "Assault equal to my Shield" stays dynamic.
  ++target.temp_assault_shield_multiples;
  target.recomputeMight();
 }
private:
 const CardDef def_=[] {
  CardDef d;d.id=960;d.def_id="rad-147-167";d.name="Pride of Nazumah";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-147/167";
  d.collector_number=147;d.card_type=CardType::Legend;
  d.domains={Domain::Calm,Domain::Body};d.tags={"K'Sante"};d.rarity=Rarity::Rare;
  d.ability_text="[1], [E]: Give a friendly unit 'I have [Assault] equal to my [Shield]' this turn.";
  return d;
 }();
};
}
void register_card_960(CardRegistry& registry) {
 registry.registerCard(960,std::make_unique<PrideOfNazumah>());
}
} // namespace riftbound
