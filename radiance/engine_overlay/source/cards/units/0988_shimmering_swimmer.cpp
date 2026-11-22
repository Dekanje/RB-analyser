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
class ShimmeringSwimmer final : public UnitCard {
public:
 const CardDef& def() const override {return def_;}
 static constexpr const char* kPaid=kAdditionalCostPaid;
 static std::vector<GameObjectId> friendlyFodder(const GameState& state,PlayerId p){
   std::vector<GameObjectId> options;
   for(const auto& [id,obj]:state.objects.onBoard())
     if((obj.isUnit()||obj.isGear())&&obj.controller==p&&obj.location)
       options.push_back(id);
   std::sort(options.begin(),options.end());return options;
 }
 AdditionalPlayCost additionalPlayCost(const GameState& state,const CardDB&,
                                       PlayerId player,GameObjectId)const override{
   AdditionalPlayCost c;c.exists=true;c.mandatory=false;
   c.payable=!friendlyFodder(state,player).empty();return c;
 }
 PlayCostAdjust payAdditionalPlayCost(
   CardContext& ctx,const std::function<bool(const PlayCostAdjust&)>&)override{
   auto& self=ctx.state.getObject(ctx.source);
   self.card_counters[kPaid]=0;
   const auto options=friendlyFodder(ctx.state,ctx.controller);
   if(options.empty()||!ctx.executor.confirmNow(ctx.controller,
       "Shimmering Swimmer: kill a friendly unit or gear as optional additional cost?"))return {};
   const auto victim=ctx.executor.chooseObjectNow(ctx.controller,options,
       "Shimmering Swimmer: choose unit or gear to kill as additional cost");
   if(victim==kInvalidId||!ctx.state.objectExists(victim))return {};
   ctx.executor.killObject(victim);
   self.card_counters[kPaid]=1;
   return {};
 }
 TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
 unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
 bool triggerCondition(const GameState& state,GameObjectId source,PlayerId,
                       TriggerType,GameObjectId)const override{
   if(!state.objectExists(source))return false;
   const auto& c=state.getObject(source).card_counters;
   auto it=c.find(kPaid);return it!=c.end()&&it->second==1;
 }
 void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
   std::vector<GameObjectId> units;
   for(const auto& [id,u]:ctx.state.objects.onBoard())
     if(u.isUnit()&&u.location)units.push_back(id);
   const auto target=pickTarget(ctx,"Shimmering Swimmer: deal 2 to a unit",units);
   if(finalizingChoices(ctx))return;
   if(ctx.state.objectExists(ctx.source))
     ctx.state.getObject(ctx.source).card_counters[kPaid]=0;
   if(target==kInvalidId||!ctx.state.objectExists(target))return;
   ctx.executor.dealDamage(target,2,ctx.source);
   ctx.executor.killLethallyDamagedTogether(std::vector<GameObjectId>{target});
 }
private:
 const CardDef def_=[]{
   CardDef d;d.id=988;d.def_id="rad-014-167";d.name="Shimmering Swimmer";
   d.set_code="RAD";d.set_name="Radiance";d.public_code="RAD-014/167";
   d.collector_number=14;d.card_type=CardType::Unit;d.domains={Domain::Fury};
   d.energy_cost=3;d.might=3;d.rarity=Rarity::Uncommon;
   d.ability_text="You may kill a friendly unit or gear as an additional cost to play me. When you play me, if you paid the additional cost, deal 2 to a unit.";
   return d;
 }();
};
}
void register_card_988(CardRegistry& r){r.registerCard(988,std::make_unique<ShimmeringSwimmer>());}
} // namespace riftbound
