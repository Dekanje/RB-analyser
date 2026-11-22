// Radiance Wave 3: RAD-008 War Scout. Official gallery: Accelerate; on-play +2 Might to a unit.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <vector>

namespace riftbound {
namespace {
class RadianceWarScout final : public UnitCard {
public:
 const CardDef& def() const override { return def_; }
 unsigned choicesAtFinalization() const override { return kFinalizeTrigger; }
 TriggerType triggerType() const override { return TriggerType::WhenYouPlayMe; }
 void onTrigger(CardContext& ctx, const std::vector<GameObjectId>&) override {
   auto units = chooseableUnits(ctx.state, ctx.controller,
       [](const GameObject& unit) { return unit.isUnit() && unit.location.has_value(); });
   std::sort(units.begin(), units.end());
   const GameObjectId chosen = pickTarget(ctx, "War Scout: give a unit +2 Might", units);
   if (finalizingChoices(ctx)) return; // CR 383.3: trigger targets selected on chain entry
   if (chosen == kInvalidId || !ctx.state.objectExists(chosen)) return;
   ctx.executor.giveTemporaryMight(chosen, 2);
 }
private:
 const CardDef def_ = [] {
   CardDef d;
   d.id=995; d.def_id="rad-008-167"; d.name="War Scout";
   d.set_code="RAD"; d.set_name="Radiance"; d.public_code="RAD-008/167";
   d.collector_number=8; d.artist="Six More Vodka";
   d.card_type=CardType::Unit; d.domains={Domain::Fury};
   d.tags={"Yordle","Demacia"};
   d.energy_cost=3; d.might=2; d.rarity=Rarity::Common;
   d.keywords.set(Keyword::Accelerate);
   d.ability_text="[Accelerate] (You may pay [1][R] as an additional cost to have me enter ready.)\nWhen you play me, give a unit +2 [M] this turn.";
   return d;
 }();
};
}
void register_card_995(CardRegistry& r) { r.registerCard(995,std::make_unique<RadianceWarScout>()); }
}
