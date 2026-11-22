// RAD-049/167 Industrious Mechsmith: a domainless 1-Might unit that creates
// a 3-Might Mech token at the same location when played.
#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class RadianceIndustriousMechsmith final : public UnitCard {
public:
    const CardDef& def() const override { return def_; }
    TriggerType triggerType() const override { return TriggerType::WhenYouPlayMe; }
    void onTrigger(CardContext& ctx, const std::vector<GameObjectId>&) override {
        if (!ctx.state.objectExists(ctx.source)) return;
        const auto& self = ctx.state.getObject(ctx.source);
        if (!self.location.has_value()) return;
        // The token is played "here", not into the controller's base by default.
        // A Mech created in base is exhausted; normal enter-ready replacement
        // effects are handled by EffectExecutor::createToken.
        ctx.executor.createToken(ctx.controller, CardType::Unit, "Mech",
                                 /*might=*/3, /*tags=*/{"Mech"},
                                 KeywordSet{}, *self.location, /*enter_ready=*/false);
    }
private:
    const CardDef def_ = [] {
        CardDef d;
        d.id=996; d.def_id="rad-049-167";
        d.name="Industrious Mechsmith"; d.set_code="RAD"; d.set_name="Radiance";
        d.public_code="RAD-049/167"; d.collector_number=49;
        d.artist="Six More Vodka";
        d.card_type=CardType::Unit; // Neutral domainless unit
        d.energy_cost=4; d.might=1; d.rarity=Rarity::Common;
        d.ability_text="When you play me, play a 3 [M] Mech unit token here.";
        d.image_url="https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/c8f6b4191874f23b522566f8ebeeb6e5ee18eb7f-744x1039.png";
        return d;
    }();
};
}
void register_card_996(CardRegistry& r) {
    r.registerCard(996, std::make_unique<RadianceIndustriousMechsmith>());
}
}
