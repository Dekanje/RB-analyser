#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>

namespace riftbound {
namespace {
class RadianceHush final : public SpellCard {
public:
 const CardDef& def() const override { return def_; }
 unsigned choicesAtFinalization() const override { return kFinalizeResolve; }
 FinalizeChoice mayChooseAtFinalization(const GameState&, PlayerId,
                                        GameObjectId) const override {
   return FinalizeChoice::No;
 }
 static bool qualifies(const ChainItem& ci,const CardDB& db) {
   if(!ci.is_spell||ci.card_def_id==kInvalidId)return false;
   return db.get(ci.card_def_id).power_cost>=2;
 }
 bool hasLegalTargets(const GameState& state, PlayerId,
                      const CardDB& db) const override {
   return anyChainItem(state,[&](const ChainItem& ci){return qualifies(ci,db);});
 }
 bool hasLegalTargets(const GameState& state,PlayerId)const override{
   return anyChainItem(state,[](const ChainItem& ci){return ci.is_spell;});
 }
 void onResolve(CardContext& ctx,const std::vector<GameObjectId>&) override {
   const auto& db=ctx.executor.cardDB();
   const auto spell=pickChainItem(ctx,"Hush: counter spell with printed Power cost [A][A] or more",
       chainItemChoices(ctx,[&](const ChainItem& ci){return qualifies(ci,db);}));
   if(!spell.has_value())return;
   if(finalizingChoices(ctx))return;
   if(*spell!=kInvalidId)counterChosenItem(ctx,*spell);
 }
private:
 const CardDef def_=[]{
   CardDef d;d.id=987;d.def_id="rad-041-167";d.name="Hush";
   d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-041/167";
   d.collector_number=41;d.card_type=CardType::Spell;
   d.energy_cost=1;d.power_cost=2;d.rarity=Rarity::Rare;
   d.keywords.set(Keyword::Reaction);
   d.ability_text="[Reaction] Counter a spell with Power cost [A][A] or more.";
   return d;
 }();
};
}
void register_card_987(CardRegistry& r){r.registerCard(987,std::make_unique<RadianceHush>());}
} // namespace riftbound
