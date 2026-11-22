// RAD-003/167 Bilgewater Tracker: choose UP TO two units (friendly or enemy)
// on the triggered ability's finalization pass; damage is simultaneous.
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
class RadianceBilgewaterTracker final : public UnitCard {
public:
    const CardDef& def() const override { return def_; }
    TriggerType triggerType() const override { return TriggerType::WhenYouPlayMe; }
    unsigned choicesAtFinalization() const override { return kFinalizeTrigger; }
    void onTrigger(CardContext& ctx, const std::vector<GameObjectId>&) override {
        auto candidates = chooseableUnits(ctx.state, ctx.controller,
            [](const GameObject& o) { return o.isUnit() && o.location.has_value(); });
        // Pick zero, one, or two distinct targets; the target chooser
        // applies Deflect and checks legality. Never auto-select a target.
        auto picked = selectSeveralTargets(*this, ctx,
            "Bilgewater Tracker: choose up to two units", candidates, /*max_picks=*/2);
        if (!picked.has_value()) return;          // waiting for actual player choice
        if (finalizingChoices(ctx)) return;       // CR 383.3: no effect during selection
        std::vector<GameObjectId> victims;
        for (GameObjectId id : *picked) {
            if (!ctx.state.objectExists(id) ||
                !ctx.state.getObject(id).location.has_value()) continue;
            victims.push_back(id);
        }
        for (GameObjectId id : victims) ctx.executor.dealDamage(id, 1, ctx.source);
        ctx.executor.killLethallyDamagedTogether(victims);
    }
private:
    const CardDef def_ = [] {
        CardDef d;
        d.id=997; d.def_id="rad-003-167";
        d.name="Bilgewater Tracker"; d.set_code="RAD"; d.set_name="Radiance";
        d.public_code="RAD-003/167"; d.collector_number=3;
        d.artist="Six More Vodka"; d.card_type=CardType::Unit;
        d.domains={Domain::Body};
        d.energy_cost=3; d.might=3; d.rarity=Rarity::Common;
        d.ability_text="When you play me, deal 1 to each of up to 2 units.";
        d.image_url="https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/b660759a6bcb9c7ca41ea969cf11463259e284c9-744x1039.png";
        return d;
    }();
};
}
void register_card_997(CardRegistry& r) {
    r.registerCard(997, std::make_unique<RadianceBilgewaterTracker>());
}
}
