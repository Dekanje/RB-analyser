#include "cards/card.h"
#include "cards/card_registry.h"
#include <memory>
namespace riftbound {
namespace {
class TheExile final : public LegendCard {
public:
 const CardDef& def() const override { return def_; }
private:
 const CardDef def_ = [] {
  CardDef d; d.id=956; d.def_id="rad-149-167"; d.name="The Exile";
  d.set_code="RAD"; d.set_name="Radiance"; d.public_code="RAD-149/167";
  d.collector_number=149; d.card_type=CardType::Legend;
  d.domains={Domain::Calm,Domain::Chaos}; d.tags={"Riven"};
  d.rarity=Rarity::Rare;
  d.ability_text="Units you play to battlefields you control enter ready.";
  return d;
 }();
};
}
void register_card_956(CardRegistry& r) { r.registerCard(956,std::make_unique<TheExile>()); }
}