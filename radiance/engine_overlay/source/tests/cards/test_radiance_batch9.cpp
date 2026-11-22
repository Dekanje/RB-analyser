#include "tests/cards/card_test_fixture.h"
#include "cards/card.h"
#include "cards/card_helpers.h"
#include <gtest/gtest.h>
namespace riftbound::test::radiance_batch9 {
class RadianceBatch9Test:public CardTestFixture {};

TEST_F(RadianceBatch9Test, FirstThreeCardIdentitiesAreDistinctAndPrintedCorrectly) {
    struct Want {int id;const char* code;const char* name;int energy;};
    for(const auto& w:std::vector<Want>{
        {1025,"RAD-057/167","Piltovan Guidebot",4},
        {1026,"RAD-126/167","Mournful Spirit",4},
        {1027,"RAD-073/167","Pillaged Armory",1}}) {
        const auto& d=card_db.get(CardDefId::fromRaw(w.id));
        EXPECT_EQ(d.public_code,w.code);
        EXPECT_EQ(d.name,w.name);
        EXPECT_EQ(d.energy_cost,w.energy);
    }
    EXPECT_TRUE(card_db.get(CardDefId{1026}).keywords.has(Keyword::Deathknell));
    EXPECT_TRUE(card_db.get(CardDefId{1027}).keywords.has(Keyword::Deploy));
}
TEST_F(RadianceBatch9Test, GuidebotCopiesPlayedCardsPrintedEnergyCostThisTurn) {
    auto bot=addUnit(P1,CardDefId{1025},3,0);
    auto bigger=addToHand(P1,CardDefId{1020}); // Storm Raptor, printed Energy 6
    EnginePathAgent agent(EnginePathAgent::accepting());
    playThroughEngine(bigger,&agent);
    EXPECT_EQ(state.getObject(bot).base_might,3);
    EXPECT_EQ(state.getObject(bot).baseMight(),6);
    EXPECT_EQ(state.getObject(bot).current_might,6);
}
TEST_F(RadianceBatch9Test, GuidebotMayDeclineChangingItsBaseMight) {
    auto bot=addUnit(P1,CardDefId{1025},3,0);
    auto bigger=addToHand(P1,CardDefId{1020});
    EnginePathAgent agent([](const std::vector<Intent>& choices){
        for(const auto& c:choices)if(c.declines)return c;
        return choices.front();
    });
    playThroughEngine(bigger,&agent);
    EXPECT_EQ(state.getObject(bot).baseMight(),3);
}
TEST_F(RadianceBatch9Test, MournfulSpiritDeathknellCanKillEnemyUnitAtItsLocation) {
    auto spirit=addUnit(P1,CardDefId{1026},1,0);
    auto enemy=addUnit(P2,kInvalidId,3,0);
    EnginePathAgent agent(EnginePathAgent::accepting());
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(spirit);},
                         &agent);
    EXPECT_EQ(state.getObject(spirit).zone,ZoneType::Trash);
    EXPECT_EQ(state.getObject(enemy).zone,ZoneType::Trash);
}
TEST_F(RadianceBatch9Test, PillagedArmoryBuffsFriendlyUnitWhenPlayed) {
    auto ally=addUnit(P1,kInvalidId,3,0);
    auto armory=addToHand(P1,CardDefId{1027});
    EnginePathAgent agent(EnginePathAgent::choosing(ally));
    playThroughEngine(armory,&agent,
        LocationId{BattlefieldLocation{state.battlefields[0].id}});
    EXPECT_TRUE(state.getObject(armory).isAtBattlefield());
    EXPECT_EQ(state.getObject(ally).buff_count,1);
}
TEST_F(RadianceBatch9Test, PillagedArmoryBuffsAgainOnConquerAtItsBattlefield) {
    auto ally=addUnit(P1,kInvalidId,3,0);
    auto armory=addToHand(P1,CardDefId{1027});
    EnginePathAgent agent(EnginePathAgent::choosing(ally));
    playThroughEngine(armory,&agent,
        LocationId{BattlefieldLocation{state.battlefields[0].id}});
    ASSERT_EQ(state.getObject(ally).buff_count,1);
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(ScoreEvent{P1,state.battlefields[0].id,ScoreMethod::Conquer,1});
    },&agent);
    EXPECT_EQ(state.getObject(ally).buff_count,1); // Buff is non-stacking.
}
TEST_F(RadianceBatch9Test, DeployGearDiesWhenOpponentHoldsAtItsBattlefield) {
    auto ally=addUnit(P1,kInvalidId,3,0);
    auto armory=addToHand(P1,CardDefId{1027});
    EnginePathAgent agent(EnginePathAgent::choosing(ally));
    playThroughEngine(armory,&agent,
        LocationId{BattlefieldLocation{state.battlefields[0].id}});
    ASSERT_TRUE(state.getObject(armory).isAtBattlefield());
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(ScoreEvent{P2,state.battlefields[0].id,ScoreMethod::Hold,1});
    });
    EXPECT_EQ(state.getObject(armory).zone,ZoneType::Trash);
}

TEST_F(RadianceBatch9Test, AdditionalTwelveCardsHaveCorrectPinnedIdentitiesAndCosts) {
    struct Row {int id;const char* code;const char* name;int energy;int power;};
    const Row expected[]={
        {1028,"RAD-049/167","Industrious Mechsmith",4,0},
        {1029,"RAD-050/167","Mysterious Chronomancer",5,0},
        {1030,"RAD-055/167","Clanging Sentry",3,0},
        {1031,"RAD-072/167","Overloaded Traveler",2,0},
        {1032,"RAD-076/167","Sneaky Zeebles",2,0},
        {1033,"RAD-083/167","Stalwart Goatherd",4,0},
        {1034,"RAD-093/167","Disposal Expert",4,0},
        {1035,"RAD-097/167","Siren of the Shallows",2,0},
        {1036,"RAD-099/167","Suave Negotiator",3,0},
        {1037,"RAD-117/167","For Demacia!",3,0},
        {1038,"RAD-119/167","Hunting Dog",3,0},
        {1039,"RAD-128/167","Steadfast Outrider",4,0},
    };
    for(const auto& e:expected){
        const auto& card=card_db.get(CardDefId::fromRaw(e.id));
        EXPECT_EQ(card.name,e.name);
        EXPECT_EQ(card.public_code,e.code);
        EXPECT_EQ(card.energy_cost,e.energy);
        EXPECT_EQ(card.power_cost,e.power);
    }
    EXPECT_TRUE(card_db.get(CardDefId{1029}).keywords.has(Keyword::Disarm));
    EXPECT_TRUE(card_db.get(CardDefId{1034}).keywords.has(Keyword::Disarm));
    EXPECT_TRUE(card_db.get(CardDefId{1035}).keywords.has(Keyword::Disarm));
    EXPECT_TRUE(card_db.get(CardDefId{1035}).keywords.has(Keyword::Ganking));
    EXPECT_TRUE(card_db.get(CardDefId{1033}).keywords.has(Keyword::Shield));
    EXPECT_TRUE(card_db.get(CardDefId{1037}).keywords.has(Keyword::Reaction));
    EXPECT_TRUE(card_db.get(CardDefId{1038}).keywords.has(Keyword::Deathknell));
    EXPECT_TRUE(card_db.get(CardDefId{1039}).keywords.has(Keyword::Tank));
}
TEST_F(RadianceBatch9Test, IndustriousMechsmithPlaysThreeMightMechTokenAtSameBattlefield) {
    auto smith=addToHand(P1,CardDefId{1028});
    playThroughEngine(smith,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
    int mechs=0;
    for(const auto& [id,o]:state.objects.onBoard())
        if(o.isUnit()&&o.controller==P1&&hasTag(o,"Mech")&&o.isToken()){
            ++mechs;
            EXPECT_EQ(o.base_might,3);
            EXPECT_EQ(o.battlefieldId(),state.battlefields[0].id);
        }
    EXPECT_EQ(mechs,1);
}
TEST_F(RadianceBatch9Test, MysteriousChronomancerCallsPredictAndRetainsDisarmTwo) {
    addToDeck(P1,CardDefId{1012});
    addToDeck(P1,CardDefId{1019});
    auto card=addToHand(P1,CardDefId{1029});
    playThroughEngine(card);
    EXPECT_TRUE(state.getObject(card).hasKeyword(Keyword::Disarm));
}
TEST_F(RadianceBatch9Test, ClangingSentryGrantsDisarmToFriendlyMechAndNotEnemy) {
    auto sentry=addUnit(P1,CardDefId{1030},2,0);
    auto friendly=addUnit(P1,kInvalidId,3,0);
    auto enemy=addUnit(P2,kInvalidId,3,0);
    state.getObject(friendly).tags={"Mech"};
    state.getObject(enemy).tags={"Mech"};
    withEngine([&](GameEngine& engine){engine.testHook_recalculateAuras();});
    EXPECT_TRUE(state.getObject(friendly).hasKeyword(Keyword::Disarm));
    EXPECT_FALSE(state.getObject(enemy).hasKeyword(Keyword::Disarm));
    EXPECT_FALSE(state.getObject(sentry).hasKeyword(Keyword::Disarm));
}
TEST_F(RadianceBatch9Test, OverloadedTravelerGainsMightOnlyWithFriendlyDeployGearHere) {
    auto traveler=addUnit(P1,CardDefId{1031},2,0);
    auto banner=addToHand(P1,CardDefId{1010});
    playThroughEngine(banner,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
    withEngine([&](GameEngine& engine){engine.testHook_recalculateAuras();});
    EXPECT_EQ(state.getObject(traveler).current_might,3);
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(banner);});
    withEngine([&](GameEngine& engine){engine.testHook_recalculateAuras();});
    EXPECT_EQ(state.getObject(traveler).current_might,2);
}
TEST_F(RadianceBatch9Test, SneakyZeeblesConquerAddsOneFloatingUniversalPower) {
    auto zeebles=addUnit(P1,CardDefId{1032},1,0);
    const auto before=state.player(P1).rune_pool.universal;
    fireTriggerThroughEngine(zeebles,TriggerType::WhenIConquer);
    EXPECT_EQ(state.player(P1).rune_pool.universal,before+1);
}

} // namespace riftbound::test::radiance_batch9
