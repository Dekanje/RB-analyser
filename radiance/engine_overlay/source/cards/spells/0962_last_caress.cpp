#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class LastCaress final : public SpellCard {
public:
 const CardDef& def() const override {return def_;}
 void onResolve(CardContext& ctx,const std::vector<GameObjectId>&)override{
  auto& ps=ctx.state.player(ctx.controller);
  if(ps.next_unit_any_bf_buff_turn!=ctx.state.turn.turn_number){
   ps.next_unit_any_bf_buff_turn=ctx.state.turn.turn_number;
   ps.next_unit_any_bf_buff_count=0;
  }
  ++ps.next_unit_any_bf_buff_count;
  DelayedAbility da;
  da.source=ctx.source;da.card_def_id=cardDefId();da.controller=ctx.controller;
  da.trigger=TriggerType::WhenYouPlayAUnit;
  da.expires_on_turn=ctx.state.turn.turn_number;
  ctx.state.delayed_abilities.push_back(da);
 }
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
  if(!ctx.state.chain.resuming)return;
  const GameObjectId unit=ctx.state.chain.resuming->triggering_subject;
  if(unit==kInvalidId||!ctx.state.objectExists(unit))return;
  const auto& u=ctx.state.getObject(unit);
  if(!u.isUnit()||!u.location||u.controller!=ctx.controller)return;
  ctx.executor.buffUnit(unit);
 }
private:
 const CardDef def_=[] {
  CardDef d;d.id=962;d.def_id="rad-154-167";d.name="Last Caress";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-154/167";
  d.collector_number=154;d.card_type=CardType::Spell;
  d.super_type=SuperType::Signature;d.domains={Domain::Body,Domain::Chaos};
  d.tags={"Evelynn"};
  d.energy_cost=2;d.rarity=Rarity::Epic;d.keywords.set(Keyword::Reaction);
  d.ability_text="[Reaction] The next unit you play this turn (even from face down) can be played to any battlefield. When you play it, [Buff] it.";
  return d;
 }();
};
}
void register_card_962(CardRegistry& r){r.registerCard(962,std::make_unique<LastCaress>());}
} // namespace riftbound
