// RAD-083/167: Shield 2; when played, MAY target and kill a gear whose
// printed Energy cost is <=4. Selection uses the optional Deflect-aware
// target helper and is finalized when the trigger is placed on the chain.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class RadianceStalwartGoatherd final : public UnitCard {
public:
    const CardDef& def() const override { return def_; }
    TriggerType triggerType() const override { return TriggerType::WhenYouPlayMe; }
    unsigned choicesAtFinalization() const override { return kFinalizeTrigger; }
    void onTrigger(CardContext& ctx, const std::vector<GameObjectId>&) override {
        std::vector<GameObjectId> eligible;
        for (const auto& [id, obj]:ctx.state.objects.onBoard()) {
            if (!obj.isGear() || !obj.location.has_value()) continue;
            // Printed cost, NOT current play cost or a runtime GameObject
            // property. The registry is populated on the real engine path.
            if (obj.card_def_id==kInvalidId || !ctx.registry) continue;
            const Card* gear_card=ctx.registry->get(obj.card_def_id);
            if (gear_card && gear_card->def().energy_cost <= 4)
                eligible.push_back(id);
        }
        auto chosen=selectSeveralTargets(*this, ctx,
            "Stalwart Goatherd: optionally kill gear costing 4 or less",
            eligible, 1);
        if (!chosen.has_value()) return;
        if (finalizingChoices(ctx)) return;
        if (chosen->empty()) return;
        const auto id=chosen->front();
        if (ctx.state.objectExists(id) &&
            ctx.state.getObject(id).location.has_value())
            ctx.executor.killObject(id);
    }
private:
    const CardDef def_=[] {
        CardDef d;
        d.id=1000; d.def_id="rad-083-167";
        d.name="Stalwart Goatherd"; d.set_code="RAD"; d.set_name="Radiance";
        d.public_code="RAD-083/167"; d.collector_number=83;
        d.artist="Six More Vodka";
        d.card_type=CardType::Unit; d.domains={Domain::Body};
        d.energy_cost=4; d.might=2; d.rarity=Rarity::Uncommon;
        d.keywords.set(Keyword::Shield); d.shield_value=2;
        d.ability_text="[Shield 2] (+2 [M] while I'm a defender.)\nWhen you play me, you may kill a gear with Energy cost [4] or less.";
        d.image_url="https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/bff85727b58017cbd3921fd73e9b363f5a0205e4-744x1039.png";
        return d;
    }();
};
}
void register_card_1000(CardRegistry& r) {
    r.registerCard(1000,std::make_unique<RadianceStalwartGoatherd>());
}
}
