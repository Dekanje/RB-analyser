// Radiance Batch 9 tranche 3A, unique battlefield cards 157, 159, 160, 161.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "core/events.h"
#include "engine/effect_executor.h"
#include <memory>
#include <string>
#include <vector>
namespace riftbound { namespace {
CardDef bf9(int id,int number,const char* name,const char* rules) {
    CardDef d;
    d.id=CardDefId::fromRaw(id);
    auto n=std::to_string(number);
    d.def_id="rad-"+std::string(3-n.size(),'0')+n+"-167";
    d.public_code="RAD-"+std::string(3-n.size(),'0')+n+"/167";
    d.set_code="RAD";d.set_name="Radiance";d.name=name;d.collector_number=number;
    d.card_type=CardType::Battlefield;d.rarity=Rarity::Uncommon;
    d.ability_text=rules;
    return d;
}
class BandleScoutsAcademy9 final : public BattlefieldCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouHideACard;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        createGoldExhausted(ctx);
    }
private:
    const CardDef d_=bf9(1040,157,"Bandle Scouts' Academy",
        "When you hide a card here, play a Gold gear token exhausted.");
};
class BlackRoseSanctum9 final : public BattlefieldCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenAFriendlyUnitDies;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        ctx.executor.createToken(ctx.controller,CardType::Unit,"Recruit",1,
            {"Recruit"},KeywordSet{},LocationId{BaseLocation{ctx.controller}},false);
    }
private:
    const CardDef d_=bf9(1041,159,"Black Rose Sanctum",
        "For each player, the first time each turn a non-token unit they control dies here, they play a 1 [M] Recruit unit token to their base.");
};
class CosmicVista9 final : public BattlefieldCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouHoldHere;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        if(ctx.state.player(ctx.controller).rune_deck.empty())
            ctx.executor.scorePoints(ctx.controller,1);
    }
private:
    const CardDef d_=bf9(1042,160,"Cosmic Vista",
        "When you hold here, if your Rune Deck is empty, you score 1 point.");
};
class DurandMemorial9 final : public BattlefieldCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouDefendHere;}
    unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        const auto here=battlefieldOfCard(ctx.state,ctx.source);
        if(!here)return;
        auto candidates=chooseableUnits(ctx.state,ctx.controller,
            [&](const GameObject& unit){
                return unit.controller==ctx.controller&&unit.isAtBattlefield()&&
                       unit.battlefieldId()==here;
            });
        const GameObjectId choice=pickTarget(ctx,
            "Durand Memorial: choose a friendly defending unit here",candidates);
        if(finalizingChoices(ctx)||choice==kInvalidId)return;
        if(ctx.state.objectExists(choice))
            ctx.executor.giveKeywordThisCombat(choice,Keyword::Tank,1,*here);
    }
private:
    const CardDef d_=bf9(1043,161,"Durand Memorial",
        "When you defend here, choose a unit you control here. Give it [Tank] this combat.");
};
}
void register_card_1040(CardRegistry& r){r.registerCard(1040,std::make_unique<BandleScoutsAcademy9>());}
void register_card_1041(CardRegistry& r){r.registerCard(1041,std::make_unique<BlackRoseSanctum9>());}
void register_card_1042(CardRegistry& r){r.registerCard(1042,std::make_unique<CosmicVista9>());}
void register_card_1043(CardRegistry& r){r.registerCard(1043,std::make_unique<DurandMemorial9>());}
} // namespace riftbound
