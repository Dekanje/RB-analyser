// Radiance Batch 9 tranche 2C: cards 1036..1039.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <source_location>
#include <string>
#include <vector>
namespace riftbound {namespace {
CardDef card9c(int id,int n,const char* name,CardType type,int energy,int power,int might,
    std::vector<Domain> domains,Rarity rarity,const char* text,
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
class SuaveNegotiator9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenYouPlayMe;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        // The pinned AlphaRune simulation is two-player: the opponent is unique.
        const PlayerId other=opponent(ctx.controller);
        ctx.executor.drawCards(ctx.controller,1);
        ctx.executor.drawCards(other,1);
    }
private:
    const CardDef d_=card9c(1036,99,"Suave Negotiator",CardType::Unit,3,0,3,
        {Domain::Chaos},Rarity::Common,
        "When you play me, choose an opponent. You and that player each draw 1.");
};
class ForDemacia9 final:public SpellCard {
public:
    const CardDef& def()const override{return d_;}
    unsigned choicesAtFinalization()const override{return kFinalizeResolve;}
    FinalizeChoice mayChooseAtFinalization(const GameState&,PlayerId,GameObjectId)const override{
        return FinalizeChoice::No; // Choice is a battlefield, not an object.
    }
    void onResolve(CardContext& ctx,const std::vector<GameObjectId>&)override{
        const int count=static_cast<int>(std::min<size_t>(32,ctx.state.battlefields.size()));
        if(!count)return;
        std::vector<std::string> choices;
        for(int i=0;i<count;i++)choices.push_back("Battlefield "+std::to_string(i+1));
        const uint32_t mask=count==32?0xffffffffu:((1u<<count)-1u);
        const int which=pickMode(ctx,"For Demacia!: choose a battlefield",count,choices,
                                 mask,std::source_location::current(),PromptKind::Target);
        if(finalizingChoices(ctx)||which<0||which>=count)return;
        const auto bf=ctx.state.battlefields[which].id;
        std::vector<GameObjectId> friends;
        for(const auto& [id,u]:ctx.state.objects.onBoard())
            if(u.isUnit()&&u.isAtBattlefield()&&u.controller==ctx.controller&&
               u.battlefieldId()==bf)friends.push_back(id);
        std::sort(friends.begin(),friends.end());
        for(const auto uid:friends)
            ctx.executor.giveTemporaryKeyword(uid,Keyword::Shield,2);
    }
private:
    const CardDef d_=card9c(1037,117,"For Demacia!",CardType::Spell,3,0,0,
        {Domain::Order},Rarity::Common,
        "[Reaction] Choose a battlefield. Give friendly units there [Shield 2] this turn.",
        {Keyword::Reaction});
};
class HuntingDog9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    TriggerType triggerType()const override{return TriggerType::WhenIDie;}
    void onTrigger(CardContext& ctx,const std::vector<GameObjectId>&)override{
        KeywordSet keywords;keywords.set(Keyword::Deflect);
        ctx.executor.createToken(ctx.controller,CardType::Unit,"Bird",1,
            {"Bird"},keywords,LocationId{BaseLocation{ctx.controller}},false);
    }
private:
    const CardDef d_=card9c(1038,119,"Hunting Dog",CardType::Unit,3,0,3,
        {Domain::Order},Rarity::Common,
        "[Deathknell] Play a 1 [M] Bird unit token with [Deflect] to your base.",
        {Keyword::Deathknell});
};
class SteadfastOutrider9 final:public UnitCard {
public:
    const CardDef& def()const override{return d_;}
    void applyPassiveAura(GameState& state,PlayerId controller)const override{
        forEachSelfOnce(*this,state,controller,[&](GameObjectId source,GameObject& self){
            if(!self.isAtBattlefield()||!self.battlefieldId())return;
            const auto here=*self.battlefieldId();
            int count=0;
            for(const auto& [id,other]:state.objects.onBoard()) {
                if(id==source || !other.location || other.controller!=controller ||
                   !other.isAtBattlefield() || other.battlefieldId()!=here ||
                   (!other.isGear()&&!other.isUnit())) continue;
                if(++count>=2){auraMight(self,source,2);break;}
            }
        });
    }
private:
    const CardDef d_=card9c(1039,128,"Steadfast Outrider",CardType::Unit,4,0,3,
        {Domain::Order},Rarity::Uncommon,
        "[Tank] While there are 2 or more other friendly units and/or gear at my battlefield, I have +2 [M].",
        {Keyword::Tank});
};
}
void register_card_1036(CardRegistry& r){r.registerCard(1036,std::make_unique<SuaveNegotiator9>());}
void register_card_1037(CardRegistry& r){r.registerCard(1037,std::make_unique<ForDemacia9>());}
void register_card_1038(CardRegistry& r){r.registerCard(1038,std::make_unique<HuntingDog9>());}
void register_card_1039(CardRegistry& r){r.registerCard(1039,std::make_unique<SteadfastOutrider9>());}
} // namespace riftbound
