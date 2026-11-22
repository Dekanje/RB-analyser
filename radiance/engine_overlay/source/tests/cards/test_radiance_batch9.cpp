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
} // namespace riftbound::test::radiance_batch9
