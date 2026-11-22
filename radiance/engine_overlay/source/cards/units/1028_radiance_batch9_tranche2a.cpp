// Radiance Batch 9 tranche 2A: four independent mechanics (IDs 1028..1031).
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <memory>
#include <string>
#include <vector>
namespace riftbound {
namespace {
CardDef card9a(int id,int n,const char* name,CardType type,int energy,int power,
    int might,std::vector<Domain> domains,Rarity rarity,const char* text,
    std::initializer_list<Keyword> keywords={}) {
    CardDef d;d.id=CardDefId::fromRaw(id);auto s=std::to_string(n);
    d.def_id="rad-"+std::string(3-s.size(),'0')+s+"-167";
    d.public_code="RAD-"+std::string(3-s.size(),'0')+s+"/167";
    d.name=name;d.set_code="RAD";d.set_name="Radiance";d.collector_number=n;
    d.card_type=type;d.energy_cost=energy;d.power_cost=power;d.might=might;
    d.domains=std::move(domains);d.rarity=rarity;d.ability_text=text;
    for(auto kw:keywords)d.keywords.set(kw);
    return d;
}
class IndustriousMechsmith9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override {
        if(!ctx.state.objectExists(ctx.source))return;
        const auto& self=ctx.state.getObject(ctx.source);
        if(!self.location)return;
        ctx.executor.createToken(ctx.controller,CardType::Unit,"Mech",3,
            {"Mech"},KeywordSet{},*self.location,false);
    }
private:
    const CardDef d_=card9a(1028,49,"Industrious Mechsmith",CardType::Unit,4,0,1,
        {Domain::Mind},Rarity::Common,"When you play me, play a 3 [M] Mech unit token here.");
};
class MysteriousChronomancer9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override {
        ctx.executor.predict(ctx.controller,2);
    }
private:
    const CardDef d_=card9a(1029,50,"Mysterious Chronomancer",CardType::Unit,5,0,4,
        {Domain::Mind},Rarity::Common,
        "When you play me, [Predict 2]. [Disarm 2] (When I attack, give an enemy unit here -2 [M] this turn.)",
        {Keyword::Disarm});
};
class ClangingSentry9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    void applyPassiveAura(GameState& state,PlayerId controller)const override {
        forEachSelfOnce(*this,state,controller,[&](GameObjectId source,GameObject&){
            for(auto& [id,unit]:state.objects.onBoard())
                if(unit.location&&unit.isUnit()&&unit.controller==controller&&hasTag(unit,"Mech"))
                    auraKeyword(unit,source,Keyword::Disarm,1);
        });
    }
private:
    const CardDef d_=card9a(1030,55,"Clanging Sentry",CardType::Unit,3,0,2,
        {Domain::Mind},Rarity::Uncommon,
        "Your Mechs have [Disarm]. (When each of us attacks, give an enemy unit there -1 [M] this turn.)");
};
class OverloadedTraveler9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    void applyPassiveAura(GameState& state,PlayerId controller)const override {
        forEachSelfOnce(*this,state,controller,[&](GameObjectId source,GameObject& self){
            if(!self.isAtBattlefield()||!self.battlefieldId())return;
            const auto here=*self.battlefieldId();
            for(const auto& [id,gear]:state.objects.onBoard()) {
                if(gear.controller==controller&&gear.isGear()&&gear.isAtBattlefield()&&
                   gear.battlefieldId()==here&&gear.hasKeyword(Keyword::Deploy)) {
                    auraMight(self,source,1);
                    return;
                }
            }
        });
    }
private:
    const CardDef d_=card9a(1031,72,"Overloaded Traveler",CardType::Unit,2,0,2,
        {Domain::Body},Rarity::Common,
        "While there's a friendly gear with [Deploy] at my battlefield, I have +1 [M].");
};
}
void register_card_1028(CardRegistry& r){r.registerCard(1028,std::make_unique<IndustriousMechsmith9>());}
void register_card_1029(CardRegistry& r){r.registerCard(1029,std::make_unique<MysteriousChronomancer9>());}
void register_card_1030(CardRegistry& r){r.registerCard(1030,std::make_unique<ClangingSentry9>());}
void register_card_1031(CardRegistry& r){r.registerCard(1031,std::make_unique<OverloadedTraveler9>());}
} // namespace riftbound
