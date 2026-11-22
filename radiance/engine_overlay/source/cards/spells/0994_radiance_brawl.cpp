// Radiance Wave 2: RAD-004 Brawl, exact printed Action spell.
// Snapshot: AlphaRune cards/json/rad_004_brawl.json (pinned upstream).
#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
namespace riftbound {
namespace {
class RadianceBrawl final : public SpellCard {
public:
 const CardDef& def() const override { return def_; }
 TargetRequirements getTargetRequirements() const override {
   return TargetRequirements{.count=1,.must_be_unit=true};
 }
 void onResolve(CardContext& ctx,const std::vector<GameObjectId>& targets) override {
   if(targets.empty() || !ctx.state.objectExists(targets.front())) return;
   const auto& unit=ctx.state.getObject(targets.front());
   if(!unit.isUnit() || !unit.location.has_value()) return;
   // Printed: give a unit Assault equal to its Might, evaluated at resolution.
   // The keyword grant expires this turn; engine handles attacker-only Might.
   ctx.executor.giveTemporaryKeyword(targets.front(),Keyword::Assault,unit.current_might);
 }
private:
 const CardDef def_=[] {
   CardDef d;
   d.id=994;d.def_id="rad-004-167";d.name="Brawl";d.set_code="RAD";
   d.set_name="Radiance";d.public_code="RAD-004/167";d.collector_number=4;
   d.card_type=CardType::Spell;d.domains={Domain::Chaos};
   d.energy_cost=3;d.power_cost=1;d.rarity=Rarity::Common;
   d.keywords.set(Keyword::Action);
   d.ability_text="[Action] Give a unit [Assault] this turn equal to its Might.";
   return d;
 }();
};
}
void register_card_994(CardRegistry& r){r.registerCard(994,std::make_unique<RadianceBrawl>());}
}
