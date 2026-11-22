// Radiance Batch 9, tranche 1: Guidebot, Mournful Spirit, Pillaged Armory.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <string>
#include <vector>

namespace riftbound {
namespace {
CardDef rad9(int id,int number,const char* name,CardType type,int energy,int power,
             int might,std::vector<Domain> domains,Rarity rarity,const char* rules,
             std::initializer_list<Keyword> kws={}) {
    CardDef d;d.id=CardDefId::fromRaw(id);
    const auto s=std::to_string(number);
    d.def_id="rad-"+std::string(3-s.size(),'0')+s+"-167";
    d.public_code="RAD-"+std::string(3-s.size(),'0')+s+"/167";
    d.name=name;d.set_code="RAD";d.set_name="Radiance";d.collector_number=number;
    d.card_type=type;d.energy_cost=energy;d.power_cost=power;d.might=might;
    d.domains=std::move(domains);d.rarity=rarity;d.ability_text=rules;
    for(const auto kw:kws)d.keywords.set(kw);
    return d;
}
class PiltovanGuidebot9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayACard;}
    unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override {
        if(!ctx.state.objectExists(ctx.source))return;
        auto& self=ctx.state.getObject(ctx.source);
        if(!self.location)return;
        const auto& chain=ctx.state.chain.resuming;
        if(!chain||chain->triggering_subject==kInvalidId||
           !ctx.state.objectExists(chain->triggering_subject))return;
        const auto& card=ctx.state.getObject(chain->triggering_subject);
        if(card.card_def_id==kInvalidId)return;
        const int energy=ctx.executor.cardDB().get(card.card_def_id).energy_cost;
        const int yes=confirmOptional(ctx,
            "Piltovan Guidebot: use the played card's printed Energy cost as base Might?",
            [](){return true;});
        if(finalizingChoices(ctx)||yes!=1)return;
        self.base_might_this_turn=energy;
        self.recomputeMight();
    }
private:
    const CardDef d_=rad9(1025,57,"Piltovan Guidebot",CardType::Unit,4,0,3,
        {Domain::Mind},Rarity::Uncommon,
        "When you play a card, you may have my base Might become equal to that card's Energy cost this turn.");
};
class MournfulSpirit9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenIDie;}
    unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override {
        if(!ctx.state.objectExists(ctx.source))return;
        const auto& dead=ctx.state.getObject(ctx.source);
        if(!dead.last_location)return;
        auto eligible=[&](){
            std::vector<GameObjectId> out;
            for(const auto& [id,object]:ctx.state.objects.onBoard()) {
                if(id==ctx.source||!object.location||*object.location!=*dead.last_location)
                    continue;
                if(!object.isUnit()&&!object.isGear())continue;
                if(object.controller!=ctx.controller&&object.untargetable_by_enemy)
                    continue;
                out.push_back(id);
            }
            std::sort(out.begin(),out.end());
            return out;
        };
        const int confirm=confirmOptional(ctx,
            "Mournful Spirit: kill a unit or gear at the location where it died?",
            [&](){return !eligible().empty();});
        if(confirm<1)return;
        const GameObjectId chosen=pickTarget(ctx,"Mournful Spirit: choose unit or gear here",
                                              eligible());
        if(finalizingChoices(ctx)||chosen==kInvalidId)return;
        if(ctx.state.objectExists(chosen)&&ctx.state.getObject(chosen).location)
            ctx.executor.killObject(chosen);
    }
private:
    const CardDef d_=rad9(1026,126,"Mournful Spirit",CardType::Unit,4,0,1,
        {Domain::Order},Rarity::Uncommon,
        "[Deathknell] You may kill a unit or gear here.",{Keyword::Deathknell});
};
class PillagedArmory9 final:public GearCard {
public:
    const CardDef& def()const override{return d_;}
    std::vector<TriggerType> triggerTypes()const override{
        return {TriggerType::WhenYouPlayThis,TriggerType::WhenYouConquerHere};
    }
    unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override {
        auto friendly=[&](){
            return chooseableUnits(ctx.state,ctx.controller,
                [&](const GameObject& o){return o.controller==ctx.controller;});
        };
        const auto chosen=pickTarget(ctx,"Pillaged Armory: buff a friendly unit",friendly());
        if(finalizingChoices(ctx)||chosen==kInvalidId)return;
        if(ctx.state.objectExists(chosen))ctx.executor.buffUnit(chosen);
    }
private:
    const CardDef d_=[]{auto d=rad9(1027,73,"Pillaged Armory",CardType::Gear,1,0,0,
        {Domain::Calm},Rarity::Common,
        "[Deploy] When you play this or when you conquer here, buff a friendly unit.",
        {Keyword::Deploy});d.tags={"Device"};return d;}();
};
} // namespace
void register_card_1025(CardRegistry& r){r.registerCard(1025,std::make_unique<PiltovanGuidebot9>());}
void register_card_1026(CardRegistry& r){r.registerCard(1026,std::make_unique<MournfulSpirit9>());}
void register_card_1027(CardRegistry& r){r.registerCard(1027,std::make_unique<PillagedArmory9>());}
} // namespace riftbound
