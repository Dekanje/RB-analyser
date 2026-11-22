// Batch 8, cards 1019-1021: Conservator, Raptor, Ward.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <string>
#include <vector>
namespace riftbound { namespace {
CardDef rad8B(int id,int n,const char* name,CardType type,int energy,int power,int might,
              std::vector<Domain> domains,Rarity rarity,const char* rules,
              std::initializer_list<Keyword> keywords={}) {
    CardDef d;d.id=CardDefId::fromRaw(id);auto num=std::to_string(n);
    d.def_id="rad-"+std::string(3-num.size(),'0')+num+"-167";
    d.public_code="RAD-"+std::string(3-num.size(),'0')+num+"/167";
    d.set_code="RAD";d.set_name="Radiance";d.name=name;d.collector_number=n;
    d.card_type=type;d.energy_cost=energy;d.power_cost=power;d.might=might;
    d.domains=std::move(domains);d.rarity=rarity;d.ability_text=rules;
    for(auto kw:keywords)d.keywords.set(kw);return d;
}
class SanctumConservator8 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayACard;}
    bool triggerConditionOn(const GameState&,const TriggerEvent& e)const override{
        return e.subject_card&&e.subject_card->energy_cost>=7;
    }
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        if(ctx.state.objectExists(ctx.source)&&ctx.state.getObject(ctx.source).location)
            ctx.executor.readyObject(ctx.source);
    }
private:
    const CardDef d_=rad8B(1019,30,"Sanctum Conservator",CardType::Unit,5,0,5,
        {Domain::Calm},Rarity::Common,
        "When you play a card with Energy cost [7] or more, ready me.");
};
class StormRaptor8 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenAnEnemyUnitDiesHere;}
    bool triggerCondition(const GameState& state,GameObjectId,PlayerId,
                          TriggerType,GameObjectId dead_id)const override{
        if(dead_id==kInvalidId||!state.objectExists(dead_id))return false;
        const auto& last=state.getObject(dead_id).last_known;
        return last.valid&&last.died&&last.stunned;
    }
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        ctx.executor.drawCards(ctx.controller,1);
    }
private:
    const CardDef d_=rad8B(1020,36,"Storm Raptor",CardType::Unit,6,0,6,
        {Domain::Calm},Rarity::Uncommon,
        "[Deflect] When a stunned enemy unit dies here, draw 1.",{Keyword::Deflect});
};
class EphemeralWard8 final:public GearCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayAUnit;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        if(ctx.state.objectExists(ctx.source)&&ctx.state.getObject(ctx.source).location)
            ctx.executor.killObject(ctx.source);
    }
    void applyPassiveAura(GameState& state,PlayerId controller)const override{
        forEachSelfOnce(*this,state,controller,[&](GameObjectId id,GameObject&){
            for(auto& [uid,u]:state.objects.onBoard())
                if(u.isUnit()&&u.location&&u.controller==controller)auraMight(u,id,2);
        });
    }
private:
    const CardDef d_=rad8B(1021,39,"Ephemeral Ward",CardType::Gear,4,2,0,
        {Domain::Calm},Rarity::Rare,
        "Your units have +2 [M]. When you play a unit, kill this.");
};
}
void register_card_1019(CardRegistry& r){r.registerCard(1019,std::make_unique<SanctumConservator8>());}
void register_card_1020(CardRegistry& r){r.registerCard(1020,std::make_unique<StormRaptor8>());}
void register_card_1021(CardRegistry& r){r.registerCard(1021,std::make_unique<EphemeralWard8>());}
} // namespace riftbound
