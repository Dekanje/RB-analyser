// Radiance Batch 8 tranche 1 — six real card mechanics, pinned gallery text.
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
CardDef rad(int id,int num,const char* name,CardType type,int energy,int power,
            int might,std::vector<Domain> domains,Rarity rarity,const char* text,
            std::initializer_list<Keyword> keywords={}) {
    CardDef d;
    d.id=id;d.def_id="rad-"+std::to_string(num)+"-167";
    const std::string ns=std::to_string(num);
    d.public_code="RAD-"+std::string(3-ns.size(),'0')+ns+"/167";
    d.name=name;d.set_code="RAD";d.set_name="Radiance";
    d.collector_number=num;d.card_type=type;
    d.energy_cost=energy;d.power_cost=power;d.might=might;
    d.domains=std::move(domains);d.rarity=rarity;d.ability_text=text;
    for(auto k:keywords)d.keywords.set(k);
    return d;
}

class BannerOfConquest final:public GearCard {
public:
    const CardDef& def()const override{return d_;}
    void applyPassiveAura(GameState& state,PlayerId controller)const override{
        forEachSelfOnce(*this,state,controller,[&](GameObjectId source,GameObject& self){
            if(!self.isAtBattlefield())return;
            const auto bf=self.battlefieldId();
            for(auto& [id,unit]:state.objects.onBoard())
                if(unit.isUnit()&&unit.controller==controller&&unit.location&&
                   unit.battlefieldId()==bf)auraKeyword(unit,source,Keyword::Assault,1);
        });
    }
private:
    const CardDef d_=[]{auto d=rad(1010,2,"Banner of Conquest",CardType::Gear,1,1,0,
        {Domain::Fury},Rarity::Common,
        "[Deploy] Friendly units here have [Assault].",{Keyword::Deploy});
        d.tags={"Device"};return d;}();
};

class ConsultTheHeavens final:public SpellCard {
public:
    const CardDef& def()const override{return d_;}
    TargetRequirements getTargetRequirements()const override{
        return {.count=1,.must_be_unit=true};
    }
    bool needsPlayTimeTarget()const override{return true;}
    void onResolve(CardContext& ctx,const std::vector<GameObjectId>& targets)override{
        const auto locked=lockedPlayTarget(ctx,targets);
        const auto chosen=locked ? *locked :
            pickTarget(ctx,"Consult the Heavens: shield a unit",
                       enumerateLegalTargets(ctx.state,ctx.controller));
        if(chosen==kInvalidId||!ctx.state.objectExists(chosen))return;
        ctx.executor.giveTemporaryKeyword(chosen,Keyword::Shield,2);
        ctx.executor.predict(ctx.controller,1);
    }
private:
    const CardDef d_=rad(1011,25,"Consult the Heavens",CardType::Spell,1,0,0,
        {Domain::Calm},Rarity::Common,
        "[Reaction] Give a unit [Shield 2] this turn. [Predict].",
        {Keyword::Reaction});
};

class EntrenchedBoar final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    void asYouPlayChoices(CardContext& ctx)override{
        if(ctx.state.objectExists(ctx.source)&&
           ctx.executor.confirmNow(ctx.controller,"Entrenched Boar: enter ready and cannot move this turn?"))
            ctx.state.getObject(ctx.source).card_counters["__boar_enter_ready"]=1;
    }
    bool entersReadyOnPlay(const GameState&,PlayerId,const GameObject& self)const override{
        auto it=self.card_counters.find("__boar_enter_ready");
        return it!=self.card_counters.end()&&it->second==1;
    }
    void onPlay(CardContext& ctx)override{
        auto& self=ctx.state.getObject(ctx.source);
        if(auto it=self.card_counters.find("__boar_enter_ready");
           it!=self.card_counters.end()&&it->second==1)
            self.cant_move_this_turn=true;
    }
private:
    const CardDef d_=rad(1012,26,"Entrenched Boar",CardType::Unit,2,0,2,{},
        Rarity::Common,"You may have me enter ready. If you do, I can't move this turn.");
};

class HunkerDown final:public SpellCard {
public:
    const CardDef& def()const override{return d_;}
    TargetRequirements getTargetRequirements()const override{
        return {.count=1,.must_be_unit=true,.must_be_friendly=true};
    }
    bool needsPlayTimeTarget()const override{return true;}
    void onResolve(CardContext& ctx,const std::vector<GameObjectId>& targets)override{
        const auto locked=lockedPlayTarget(ctx,targets);
        const auto chosen=locked ? *locked :
            pickTarget(ctx,"Hunker Down: ready a friendly unit",
                       enumerateLegalTargets(ctx.state,ctx.controller));
        if(chosen==kInvalidId||!ctx.state.objectExists(chosen))return;
        auto& obj=ctx.state.getObject(chosen);
        if(!obj.isUnit()||obj.controller!=ctx.controller||!obj.location)return;
        obj.cant_move_this_turn=true;
        ctx.executor.readyObject(chosen);
        ctx.executor.drawCards(ctx.controller,1);
    }
private:
    const CardDef d_=rad(1013,34,"Hunker Down",CardType::Spell,1,0,0,
        {Domain::Calm},Rarity::Uncommon,
        "[Reaction] Ready a friendly unit. It can't move this turn. Draw 1.",
        {Keyword::Reaction});
};

class HeraldOfTheEmperor final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
    unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        auto legal=chooseableUnits(ctx.state,ctx.controller,[&](const GameObject& o){
            return o.controller==ctx.controller;
        });
        const auto chosen=pickTarget(ctx,"Herald of the Emperor: choose a friendly unit",legal);
        if(finalizingChoices(ctx))return;
        if(chosen==kInvalidId||!ctx.state.objectExists(chosen))return;
        auto& unit=ctx.state.getObject(chosen);
        if(!unit.isUnit()||!unit.location||unit.controller!=ctx.controller)return;
        unit.base_might_this_turn=5;
        unit.recomputeMight();
    }
private:
    const CardDef d_=rad(1014,118,"Herald of the Emperor",CardType::Unit,5,0,3,
        {Domain::Order},Rarity::Common,
        "When you play me, choose a friendly unit. Its base Might becomes 5 this turn.");
};

class MomentaryCompanion final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        if(ctx.state.turn.turn_player!=ctx.controller&&ctx.state.objectExists(ctx.source)&&
           ctx.state.getObject(ctx.source).location)
            ctx.state.getObject(ctx.source).keywords.set(Keyword::Temporary);
    }
private:
    const CardDef d_=rad(1015,95,"Momentary Companion",CardType::Unit,4,0,4,
        {Domain::Chaos},Rarity::Common,
        "[Hidden] When you play me, if it's not your turn, give me [Temporary].",
        {Keyword::Hidden});
};
} // anonymous namespace
void register_card_1010(CardRegistry& r){r.registerCard(1010,std::make_unique<BannerOfConquest>());}
void register_card_1011(CardRegistry& r){r.registerCard(1011,std::make_unique<ConsultTheHeavens>());}
void register_card_1012(CardRegistry& r){r.registerCard(1012,std::make_unique<EntrenchedBoar>());}
void register_card_1013(CardRegistry& r){r.registerCard(1013,std::make_unique<HunkerDown>());}
void register_card_1014(CardRegistry& r){r.registerCard(1014,std::make_unique<HeraldOfTheEmperor>());}
void register_card_1015(CardRegistry& r){r.registerCard(1015,std::make_unique<MomentaryCompanion>());}
} // namespace riftbound
