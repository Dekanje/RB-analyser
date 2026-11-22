// RAD-119/167: Deathknell creates a 1-Might Bird token with Deflect
// at its controller's base even when the Dog died at a battlefield.
#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class RadianceHuntingDog final : public UnitCard {
public:
    const CardDef& def() const override { return def_; }
    TriggerType triggerType() const override { return TriggerType::WhenIDie; }
    void onTrigger(CardContext& ctx, const std::vector<GameObjectId>&) override {
        KeywordSet keywords;
        keywords.set(Keyword::Deflect);
        ctx.executor.createToken(ctx.controller, CardType::Unit, "Bird",
                                 /*might=*/1, {"Bird"}, keywords,
                                 LocationId{BaseLocation{ctx.controller}},
                                 /*enter_ready=*/false);
    }
private:
    const CardDef def_=[] {
        CardDef d;
        d.id=999; d.def_id="rad-119-167";
        d.name="Hunting Dog"; d.set_code="RAD"; d.set_name="Radiance";
        d.public_code="RAD-119/167"; d.collector_number=119;
        d.artist="Kudos Productions";
        d.card_type=CardType::Unit; d.domains={Domain::Order};
        d.energy_cost=3; d.might=3; d.rarity=Rarity::Common;
        d.keywords.set(Keyword::Deathknell);
        d.ability_text="[Deathknell][>] Play a 1 [M] Bird unit token with [Deflect] to your base.";
        d.image_url="https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/cefd575150527670879748a7212f80a1f4c1c4fc-744x1039.png";
        return d;
    }();
};
}
void register_card_999(CardRegistry& r) {
    r.registerCard(999,std::make_unique<RadianceHuntingDog>());
}
}
