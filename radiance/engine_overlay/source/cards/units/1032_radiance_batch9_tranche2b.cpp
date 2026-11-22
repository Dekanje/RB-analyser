// Radiance Batch 9 tranche 2B: cards 1032..1035.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <string>
#include <vector>
namespace riftbound { namespace {
CardDef card9b(int id,int n,const char* name,CardType type,int energy,int power,int might,
    std::vector<Domain> domains,Rarity rarity,const char* text,
    std::initializer_list<Keyword> keywords={}) {
    CardDef d;d.id=CardDefId::fromRaw(id);const auto s=std::to_string(n);
    d.def_id="rad-"+std::string(3-s.size(),'0')+s+"-167";
    d.public_code="RAD-"+std::string(3-s.size(),'0')+s+"/167";
    d.name=name;d.set_code="RAD";d.set_name="Radiance";d.collector_number=n;
    d.card_type=type;d.energy_cost=energy;d.power_cost=power;d.might=might;
    d.domains=std::move(domains);d.rarity=rarity;d.ability_text=text;
    for(auto kw:keywords)d.keywords.set(kw);return d;
}
class SneakyZeebles9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenIConquer;}
    bool triggeredAbilityAdds(TriggerType t)const override {
        return t==TriggerType::WhenIConquer;
    }
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override {
        ctx.executor.addFloatingUniversalPower(ctx.controller,1);
    }
private:
    const CardDef d_=card9b(1032,76,"Sneaky Zeebles",CardType::Unit,2,0,1,
        {Domain::Body},Rarity::Common,"When I conquer, [Add] [A].");
};
class StalwartGoatherd9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
    unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override {
        auto eligible=[&](){
            return boardObjects(ctx.state,[&](const GameObject& g){
                if(!g.isGear()||!g.location)return false;
                if(g.card_def_id==kInvalidId)return true;
                return ctx.executor.cardDB().get(g.card_def_id).energy_cost<=4;
            });
        };
        const int confirm=confirmOptional(ctx,
            "Stalwart Goatherd: kill a gear with printed Energy cost 4 or less?",
            [&](){return !eligible().empty();});
        if(confirm<1)return;
        auto target=pickTarget(ctx,"Stalwart Goatherd: choose a gear to kill",eligible());
        if(finalizingChoices(ctx)||target==kInvalidId)return;
        if(ctx.state.objectExists(target)&&ctx.state.getObject(target).location)
            ctx.executor.killObject(target);
    }
private:
    const CardDef d_=[]{auto d=card9b(1033,83,"Stalwart Goatherd",CardType::Unit,4,0,2,
        {Domain::Body},Rarity::Uncommon,
        "[Shield 2] When you play me, you may kill a gear with Energy cost 4 or less.",
        {Keyword::Shield});d.shield_value=2;return d;}();
};
class DisposalExpert9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    bool entersReadyOnPlay(const GameState& state,PlayerId player,
                           const GameObject& self)const override {
        // The entering card can already be on the battlefield when this
        // condition is checked. Only OTHER friendly units prevent ready.
        for(const auto& [id,unit]:state.objects.onBoard())
            if(id!=self.id&&unit.location&&unit.isUnit()&&unit.controller==player)
                return false;
        return true;
    }
private:
    const CardDef d_=card9b(1034,93,"Disposal Expert",CardType::Unit,4,0,3,
        {Domain::Fury},Rarity::Common,
        "I enter ready if you control no other units. [Disarm 2] (When I attack, give an enemy unit here -2 [M] this turn.)",
        {Keyword::Disarm});
};
class SirenOfTheShallows9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
private:
    const CardDef d_=card9b(1035,97,"Siren of the Shallows",CardType::Unit,2,0,1,
        {Domain::Chaos},Rarity::Common,
        "[Disarm] (When I attack, give an enemy unit here -1 [M] this turn.) [Ganking] (I can move from battlefield to battlefield.)",
        {Keyword::Disarm,Keyword::Ganking});
};
}
void register_card_1032(CardRegistry& r){r.registerCard(1032,std::make_unique<SneakyZeebles9>());}
void register_card_1033(CardRegistry& r){r.registerCard(1033,std::make_unique<StalwartGoatherd9>());}
void register_card_1034(CardRegistry& r){r.registerCard(1034,std::make_unique<DisposalExpert9>());}
void register_card_1035(CardRegistry& r){r.registerCard(1035,std::make_unique<SirenOfTheShallows9>());}
} // namespace riftbound
