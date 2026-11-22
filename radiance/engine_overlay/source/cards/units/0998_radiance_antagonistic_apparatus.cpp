// RAD-009/167: entering ready and creating a ready 3-Might Mech at the
// played location. The base game engine handles normal unit token creation.
#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class RadianceAntagonisticApparatus final : public UnitCard {
public:
    const CardDef& def() const override { return def_; }
    bool entersReadyOnPlay() const override { return true; }
    TriggerType triggerType() const override { return TriggerType::WhenYouPlayMe; }
    void onTrigger(CardContext& ctx, const std::vector<GameObjectId>&) override {
        if (!ctx.state.objectExists(ctx.source)) return;
        const auto& unit=ctx.state.getObject(ctx.source);
        if (!unit.location.has_value()) return;
        ctx.executor.createToken(ctx.controller, CardType::Unit, "Mech", 3,
                                 {"Mech"}, KeywordSet{}, *unit.location,
                                 /*enter_ready=*/true);
    }
private:
    const CardDef def_=[] {
        CardDef d;
        d.id=998; d.def_id="rad-009-167";
        d.name="Antagonistic Apparatus"; d.set_code="RAD"; d.set_name="Radiance";
        d.public_code="RAD-009/167"; d.collector_number=9;
        d.artist="Caravan Studio";
        d.card_type=CardType::Unit;
        d.energy_cost=6; d.power_cost=1; d.might=3; d.rarity=Rarity::Uncommon;
        d.ability_text="I enter ready.\nWhen you play me, play a ready 3 [M] Mech unit token here.";
        d.image_url="https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/5be775464c8b897501317c6d32fd60c8b962b5c2-744x1039.png";
        return d;
    }();
};
}
void register_card_998(CardRegistry& r) {
    r.registerCard(998,std::make_unique<RadianceAntagonisticApparatus>());
}
}
