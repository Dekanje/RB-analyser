#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "core/events.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class KSanteCourageous final : public UnitCard {
public:
 const CardDef& def() const override { return def_; }
 TriggerType triggerType() const override { return TriggerType::WhenIHold; }
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&) override {
  ctx.executor.channelRunes(ctx.controller,1);
 }
private:
 const CardDef def_ = [] {
  CardDef d; d.id=957; d.def_id="rad-086-167"; d.name="K'Sante, Courageous";
  d.set_code="RAD"; d.set_name="Radiance"; d.public_code="RAD-086/167";
  d.collector_number=86; d.card_type=CardType::Unit;
  d.super_type=SuperType::Champion; d.domains={Domain::Body};
  d.tags={"Shurima","K'Sante"}; d.energy_cost=5; d.might=4;
  d.rarity=Rarity::Rare; d.keywords.set(Keyword::Accelerate);
  d.keywords.set(Keyword::Shield); d.shield_value=2;
  d.ability_text="[Accelerate]. [Shield 2]. When I hold, channel 1 rune.";
  return d;
 }();
};
}
void register_card_957(CardRegistry& r) { r.registerCard(957,std::make_unique<KSanteCourageous>()); }
}