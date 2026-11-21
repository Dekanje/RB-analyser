#include "cards/card.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <vector>
namespace riftbound {
namespace {
class TwiceSlain final : public UnitCard {
public:
 const CardDef& def() const override{return def_;}
 bool hasReplacementEffect() const override{return true;}
 Applies replacementAppliesTo(const GameState& state,GameObjectId self,PlayerId controller,
                              GameObjectId dying) const override{
  if(self!=dying||!state.objectExists(self))return Applies::No;
  const auto& obj=state.getObject(self);
  if(!obj.isUnit()||!obj.location||obj.controller!=controller)return Applies::No;
  const auto it=obj.card_counters.find("__twice_slain_save_turn");
  if(it!=obj.card_counters.end()&&it->second==state.turn.turn_number)return Applies::No;
  // Nested sacrifice can kill another Twice Slain and recursively target this
  // unit again. A death replacement already resolving cannot re-enter itself.
  const auto processing=obj.card_counters.find("__twice_slain_processing");
  if(processing!=obj.card_counters.end()&&processing->second>0)return Applies::No;
  for(const auto& [id,c]:state.objects.onBoard())
   if(id!=self&&c.isUnit()&&c.location&&c.controller==controller)return Applies::Yes;
  return Applies::No;
 }
 bool applyReplacement(CardContext& ctx,GameObjectId dying) override{
  if(dying!=ctx.source||!ctx.state.objectExists(dying))return false;
  std::vector<GameObjectId> sacrifices;
  for(const auto& [id,c]:ctx.state.objects.onBoard())
   if(id!=dying&&c.isUnit()&&c.location&&c.controller==ctx.controller)sacrifices.push_back(id);
  if(sacrifices.empty())return false;
  if(!ctx.executor.confirmNow(ctx.controller,
     "Mordekaiser, Twice Slain: kill a friendly unit to recall and save me?"))return false;
  GameObjectId sacrifice=ctx.executor.chooseObjectNow(ctx.controller,sacrifices,
     "Mordekaiser, Twice Slain: choose friendly unit to kill as cost");
  if(sacrifice==kInvalidId||!ctx.state.objectExists(sacrifice))return false;
  // Mark the original replacement as active *before* recursively killing its
  // sacrifice. Otherwise two Twice Slain can choose each other indefinitely,
  // overflowing Boost fiber/context stacks during ISMCTS simulation.
  auto& counters=ctx.state.getObject(dying).card_counters;
  counters["__twice_slain_processing"] += 1;
  ctx.executor.killObject(sacrifice);
  if(ctx.state.objectExists(dying)) {
    auto& after=ctx.state.getObject(dying).card_counters;
    auto it=after.find("__twice_slain_processing");
    if(it!=after.end()) {
      if(--it->second<=0)after.erase(it);
    }
  }
  if(!ctx.state.objectExists(sacrifice)||!ctx.state.getObject(sacrifice).last_known.died)return false;
  if(!ctx.state.objectExists(dying))return false;
  ctx.state.getObject(dying).card_counters["__twice_slain_save_turn"]=ctx.state.turn.turn_number;
  ctx.executor.healExhaustRecall(dying);
  return true;
 }
private:
 const CardDef def_=[] {
  CardDef d;d.id=964;d.def_id="rad-020-167";d.name="Mordekaiser, Twice Slain";
  d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-020/167";
  d.collector_number=20;d.card_type=CardType::Unit;d.super_type=SuperType::Champion;
  d.domains={Domain::Fury};d.energy_cost=7;d.power_cost=1;d.might=5;
  d.rarity=Rarity::Rare;d.tags={"Mordekaiser"};d.keywords.set(Keyword::Accelerate);
  d.keywords.set(Keyword::Assault);d.assault_value=3;
  d.ability_text="[Accelerate] [Assault 3] Once each turn, if I would die, you may kill a friendly unit to heal me, exhaust me and recall me instead.";
  return d;
 }();
};
}
void register_card_964(CardRegistry& r){r.registerCard(964,std::make_unique<TwiceSlain>());}
} // namespace riftbound
