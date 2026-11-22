// Radiance Batch 9 tranche 3B, unique battlefield cards 162, 164, 165, 166.
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
CardDef bf9b(int id,int number,const char* name,const char* rules) {
    CardDef d;
    d.id=CardDefId::fromRaw(id);
    auto n=std::to_string(number);
    d.def_id="rad-"+std::string(3-n.size(),'0')+n+"-167";
    d.public_code="RAD-"+std::string(3-n.size(),'0')+n+"/167";
    d.set_code="RAD";d.set_name="Radiance";d.name=name;d.collector_number=number;
    d.card_type=CardType::Battlefield;d.rarity=Rarity::Uncommon;d.ability_text=rules;
    return d;
}
class FirelightsHideout9 final : public BattlefieldCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouConquerHere;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        // Turn-stamped rather than a persistent blanket grant. The play
        // engine consumes it when the next unit is actually played.
        ctx.state.player(ctx.controller).firelights_next_accelerate_turn =
            ctx.state.turn.turn_number + 1;
    }
private:
    const CardDef d_=bf9b(1044,162,"Firelights' Hideout",
        "When you conquer here, the next unit you play this turn has [Accelerate].");
};
class PackedAmphitheater9 final : public BattlefieldCard {
public:
    const CardDef& def()const override{return d_;}
    void applyPassiveAura(GameState& state,PlayerId)const override{
        for(const auto& bf:state.battlefields){
            if(!state.objectExists(bf.card_object_id))continue;
            if(state.getObject(bf.card_object_id).card_def_id!=cardDefId())continue;
            for(auto& [id,unit]:state.objects.onBoard()){
                if(!unit.isUnit()||unit.super_type!=SuperType::Champion||
                   !unit.battlefieldId()||*unit.battlefieldId()!=bf.id)continue;
                auraMight(unit,bf.card_object_id,1);
            }
        }
    }
private:
    const CardDef d_=bf9b(1045,164,"Packed Amphitheater",
        "Champion units here have +1 [M].");
};
class Rakelstake9 final : public BattlefieldCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayACard;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        ctx.executor.predict(ctx.controller,1);
    }
private:
    const CardDef d_=bf9b(1046,165,"Rakelstake",
        "For each player, the first time they play a unit or gear here each turn, they [Predict].");
};
class RuinedMonastery9 final : public BattlefieldCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouConquerHere;}
    unsigned choicesAtFinalization()const override{return kFinalizeTrigger;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        const int yes=confirmOptional(ctx,
            "Ruined Monastery: discard 1 to channel 1 rune exhausted?",
            [&](){return !ctx.state.player(ctx.controller).hand.empty();});
        if(yes!=1||finalizingChoices(ctx))return;
        discardThenAct(ctx,1,"Ruined Monastery: choose a card to discard",
            [](CardContext& c){c.executor.channelRunes(c.controller,1,true);});
    }
private:
    const CardDef d_=bf9b(1047,166,"Ruined Monastery",
        "When you conquer here, you may discard 1 and channel 1 rune exhausted.");
};
}
void register_card_1044(CardRegistry& r){r.registerCard(1044,std::make_unique<FirelightsHideout9>());}
void register_card_1045(CardRegistry& r){r.registerCard(1045,std::make_unique<PackedAmphitheater9>());}
void register_card_1046(CardRegistry& r){r.registerCard(1046,std::make_unique<Rakelstake9>());}
void register_card_1047(CardRegistry& r){r.registerCard(1047,std::make_unique<RuinedMonastery9>());}
} // namespace riftbound
