// Batch 8, cards 1016-1018: Rally, Dreamroot, Avian.
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
CardDef rad8A(int id,int n,const char* name,CardType type,int energy,int power,int might,
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
bool enemyOccupied8(const GameState& s,PlayerId p,BattlefieldId bf) {
    const auto& b=s.battlefields.at(static_cast<size_t>(bf.raw()));
    if(!b.controller || *b.controller!=opponent(p))return false;
    for(auto& [id,u]:s.objects.onBoard())
        if(u.isUnit()&&u.controller==opponent(p)&&u.battlefieldId()==bf)return true;
    return false;
}
class RallyForWar8 final:public SpellCard {
public:
    const CardDef& def()const override{return d_;}
    unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
    bool hasLegalTargets(const GameState& s,PlayerId p)const override{
        for(const auto& b:s.battlefields)if(enemyOccupied8(s,p,b.id))return true;
        return false;
    }
    void onResolve(CardContext& ctx,const std::vector<GameObjectId>&)override {
        int count=static_cast<int>(std::min<size_t>(32,ctx.state.battlefields.size()));
        uint32_t legal=0;std::vector<std::string> labels;
        for(int i=0;i<count;i++){
            labels.push_back("Battlefield "+std::to_string(i+1));
            if(enemyOccupied8(ctx.state,ctx.controller,ctx.state.battlefields[i].id))
                legal|=1u<<i;
        }
        if(!legal)return;
        int selected=pickMode(ctx,"Rally for War: occupied enemy battlefield",count,
            labels,legal,std::source_location::current(),PromptKind::Target);
        if(finalizingChoices(ctx)||selected<0||selected>=count||
            !(legal&(1u<<selected)))return;
        LocationId loc{BattlefieldLocation{ctx.state.battlefields[selected].id}};
        for(int i=0;i<3;i++)ctx.executor.createToken(ctx.controller,CardType::Unit,
            "Recruit",1,{"Recruit"},KeywordSet{},loc,false);
    }
private:
    const CardDef d_=rad8A(1016,7,"Rally for War",CardType::Spell,3,1,0,
        {Domain::Fury},Rarity::Common,
        "Choose an occupied enemy battlefield. Play three 1 [M] Recruit unit tokens there.");
};
class BlossomingDreamroot8 final:public GearCard {
public:
    const CardDef& def()const override{return d_;}
    // The CombatResult event dispatches this to Deploy gear at the won BF only.
    TriggerType triggerType()const override{return TriggerType::WhenIWinCombat;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override {
        ctx.executor.drawCards(ctx.controller,1);
    }
private:
    const CardDef d_=[]{auto d=rad8A(1017,24,"Blossoming Dreamroot",CardType::Gear,
        2,0,0,{Domain::Chaos},Rarity::Common,
        "[Deploy] When you win a combat here, draw 1.",{Keyword::Deploy});
        d.tags={"Device"};return d;}();
};
class IridescentAvian8 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    bool hasActivatedAbility()const override{return true;}
    ActivationCost getActivationCost()const override{return {.exhaust=true};}
    TargetRequirements getTargetRequirements()const override{
        return {.count=1,.must_be_unit=true};
    }
    void onActivate(CardContext& ctx,const std::vector<GameObjectId>& targets)override{
        if(targets.empty()||!ctx.state.objectExists(targets[0]))return;
        auto& u=ctx.state.getObject(targets[0]);
        if(!u.isUnit()||!u.location)return;
        if(u.buff_count>0)ctx.executor.giveTemporaryMight(targets[0],2);
        else ctx.executor.buffUnit(targets[0]);
    }
private:
    const CardDef d_=rad8A(1018,27,"Iridescent Avian",CardType::Unit,3,0,3,
        {Domain::Calm},Rarity::Common,
        "[E]: [Buff] a unit. If it's already buffed, give it +2 [M] this turn instead.");
};
} 
void register_card_1016(CardRegistry& r){r.registerCard(1016,std::make_unique<RallyForWar8>());}
void register_card_1017(CardRegistry& r){r.registerCard(1017,std::make_unique<BlossomingDreamroot8>());}
void register_card_1018(CardRegistry& r){r.registerCard(1018,std::make_unique<IridescentAvian8>());}
} // namespace riftbound
