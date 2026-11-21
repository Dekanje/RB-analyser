#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class AgonysEmbrace final : public LegendCard {
public:
 const CardDef& def() const override { return def_; }
 TriggerType triggerType() const override {
  return TriggerType::WhenYouPlayFromFacedown;
 }
 // Once each turn; already handled by TriggerManager per card and global turn.
 bool firstTimeEachTurn(TriggerType trigger) const override {
  return trigger==TriggerType::WhenYouPlayFromFacedown;
 }
 void onTrigger(CardContext& ctx, const std::vector<GameObjectId>&) override {
  ctx.executor.drawCards(ctx.controller,1);
  if (ctx.state.turn.turn_player!=ctx.controller)
   ctx.executor.discardCards(ctx.controller,1);
 }
private:
 const CardDef def_ = [] {
  CardDef d; d.id=958; d.def_id="rad-153-167"; d.name="Agony's Embrace";
  d.set_code="RAD"; d.set_name="Radiance"; d.public_code="RAD-153/167";
  d.collector_number=153; d.card_type=CardType::Legend;
  d.domains={Domain::Body,Domain::Chaos}; d.tags={"Evelynn"};
  d.rarity=Rarity::Rare;
  d.ability_text="Once each turn, when you play a card from face down, draw 1. Then, if it's not your turn, discard 1.";
  return d;
 }();
};
}
void register_card_958(CardRegistry& r) { r.registerCard(958,std::make_unique<AgonysEmbrace>()); }
}