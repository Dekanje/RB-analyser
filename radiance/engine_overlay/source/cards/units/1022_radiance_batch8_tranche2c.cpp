// Batch 8, cards 1022-1024: Resource Extractor, Projectile, Waters' Wage.
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
CardDef rad8C(int id,int n,const char* name,CardType type,int energy,int power,int might,
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
class ResourceExtractor8 final:public GearCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::AtEndOfTurn;}
    bool triggerCondition(const GameState& s,GameObjectId source,PlayerId player,
                          TriggerType,GameObjectId)const override{
        if(!s.objectExists(source))return false;
        const auto& self=s.getObject(source);
        if(!self.isAtBattlefield()||!self.battlefieldId())return false;
        const auto& bf=s.battlefields.at(static_cast<size_t>(self.battlefieldId()->raw()));
        return bf.controller.has_value()&&*bf.controller==player;
    }
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        createGoldExhausted(ctx);
    }
private:
    const CardDef d_=[]{auto d=rad8C(1022,52,"Resource Extractor",CardType::Gear,1,0,0,
        {Domain::Mind},Rarity::Common,
        "[Deploy] At the end of your turn, if you control this battlefield, play a Gold gear token exhausted.",
        {Keyword::Deploy});d.tags={"Device"};return d;}();
};
class ImprovisedProjectile8 final:public SpellCard {
public:
    const CardDef& def()const override{return d_;}
    unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
    FinalizeChoice mayChooseAtFinalization(const GameState& s,PlayerId p,GameObjectId id)const override{
        if(id==kInvalidId||!s.objectExists(id)||!hasLegalTargets(s,p))return FinalizeChoice::No;
        const auto& o=s.getObject(id);
        if(!o.location)return FinalizeChoice::No;
        if(o.isGear()&&o.controller==p)return FinalizeChoice::Yes;
        if(o.isUnit()&&o.isAtBattlefield()&&(o.controller==p||!o.untargetable_by_enemy))return FinalizeChoice::Yes;
        return FinalizeChoice::No;
    }
    TargetRequirements getTargetRequirements()const override{return {.count=2};}
    bool needsPlayTimeTargetPair()const override{return true;}
    static std::vector<GameObjectId> friendlyGear(const GameState& s,PlayerId me){
        return boardObjects(s,[me](const GameObject& x){return x.isGear()&&x.controller==me;});
    }
    static std::vector<GameObjectId> unitOnBattlefield(const GameState& s,PlayerId me){
        return chooseableUnits(s,me,[](const GameObject& x){return x.isAtBattlefield();});
    }
    bool hasLegalTargets(const GameState& s,PlayerId me)const override{
        return !friendlyGear(s,me).empty()&&!unitOnBattlefield(s,me).empty();
    }
    void onResolve(CardContext& ctx,const std::vector<GameObjectId>&)override{
        auto [gear,unit]=pickTargetPair(ctx,"Improvised Projectile: gear then unit",
            friendlyGear(ctx.state,ctx.controller),
            [&](GameObjectId){return unitOnBattlefield(ctx.state,ctx.controller);});
        if(finalizingChoices(ctx)||gear==kInvalidId||unit==kInvalidId ||
           !ctx.state.objectExists(gear)||!ctx.state.objectExists(unit))return;
        const auto& g=ctx.state.getObject(gear);
        if(!g.isGear()||!g.location||g.controller!=ctx.controller)return;
        int energy=0;
        if(ctx.registry && g.card_def_id!=kInvalidId)
            if(const Card* c=ctx.registry->get(g.card_def_id))energy=c->def().energy_cost;
        if(energy>0)ctx.executor.dealDamage(unit,energy,ctx.source);
    }
private:
    const CardDef d_=rad8C(1023,56,"Improvised Projectile",CardType::Spell,3,1,0,
        {Domain::Mind},Rarity::Uncommon,
        "[Action] Choose a friendly gear. Deal damage equal to its Energy cost to a unit at a battlefield.",
        {Keyword::Action});
};
class TheWatersWage8 final:public SpellCard {
public:
    const CardDef& def()const override{return d_;}
    void onResolve(CardContext& ctx,const std::vector<GameObjectId>&)override{
        if(ctx.state.turn.turn_player==ctx.controller &&
           playedFromFacedown(ctx.state,ctx.source)){
            for(int i=0;i<3;i++)ctx.executor.createToken(ctx.controller,CardType::Gear,
                "Gold",0,{},KeywordSet{},LocationId{BaseLocation{ctx.controller}},
                true,{},kGoldGearCardDefId,false);
        }else createGoldExhausted(ctx);
    }
private:
    const CardDef d_=rad8C(1024,100,"The Waters' Wage",CardType::Spell,1,0,0,
        {Domain::Chaos},Rarity::Common,
        "[Hidden] Play a Gold gear token exhausted. If it's your turn and played from face down, play three ready Gold gear tokens instead.",
        {Keyword::Hidden});
};
}
void register_card_1022(CardRegistry& r){r.registerCard(1022,std::make_unique<ResourceExtractor8>());}
void register_card_1023(CardRegistry& r){r.registerCard(1023,std::make_unique<ImprovisedProjectile8>());}
void register_card_1024(CardRegistry& r){r.registerCard(1024,std::make_unique<TheWatersWage8>());}
} // namespace riftbound
