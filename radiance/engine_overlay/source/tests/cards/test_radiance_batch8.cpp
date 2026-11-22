#include "tests/cards/card_test_fixture.h"
#include "cards/card.h"
#include "cards/card_helpers.h"
#include <gtest/gtest.h>
namespace riftbound::test::radiance_batch8 {
class RadianceBatch8Test:public CardTestFixture {
protected:
    void recalc(){withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});}
};
TEST_F(RadianceBatch8Test, IdentitiesUniqueAndPrintedCosts) {
    struct Want {int id;const char* code;int energy;int power;};
    const Want expected[]={
        {1010,"RAD-002/167",1,1},{1011,"RAD-025/167",1,0},
        {1012,"RAD-026/167",2,0},{1013,"RAD-034/167",1,0},
        {1014,"RAD-118/167",5,0},{1015,"RAD-095/167",4,0},
    };
    for(const auto& w:expected){
        const auto& d=card_db.get(CardDefId{w.id});
        EXPECT_EQ(d.public_code,w.code);
        EXPECT_EQ(d.energy_cost,w.energy);
        EXPECT_EQ(d.power_cost,w.power);
    }
}
TEST_F(RadianceBatch8Test, BannerGrantsAssaultOnlyToFriendlyUnitsAtItsBattlefield) {
    auto at=addUnit(P1,kInvalidId,3,0);
    auto elsewhere=addUnit(P1,kInvalidId,3,1);
    auto enemy=addUnit(P2,kInvalidId,3,0);
    auto banner=addToHand(P1,CardDefId{1010});
    playThroughEngine(banner,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
    recalc();
    EXPECT_TRUE(state.getObject(at).hasKeyword(Keyword::Assault));
    EXPECT_FALSE(state.getObject(elsewhere).hasKeyword(Keyword::Assault));
    EXPECT_FALSE(state.getObject(enemy).hasKeyword(Keyword::Assault));
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(banner);});
    recalc();
    EXPECT_FALSE(state.getObject(at).hasKeyword(Keyword::Assault));
}
TEST_F(RadianceBatch8Test, ConsultShieldsUnitAndPredictsTopOfDeck) {
    auto target=addUnit(P1,kInvalidId,3,0);
    addToDeck(P1,CardDefId{1012});
    const auto spell=addToHand(P1,CardDefId{1011});
    EnginePathAgent agent(EnginePathAgent::choosing(target));
    playThroughEngine(spell,&agent);
    EXPECT_TRUE(state.getObject(target).hasKeyword(Keyword::Shield));
}
TEST_F(RadianceBatch8Test, HunkerReadiesOnlyFriendlyTargetAndDraws) {
    auto ally=addUnit(P1,kInvalidId,3,0);
    auto enemy=addUnit(P2,kInvalidId,3,0);
    state.getObject(ally).is_exhausted=true;
    state.getObject(enemy).is_exhausted=true;
    addToDeck(P1,CardDefId{1012});
    const auto spell=addToHand(P1,CardDefId{1013});
    EnginePathAgent agent(EnginePathAgent::choosing(ally));
    auto before=state.player(P1).hand.size();
    playThroughEngine(spell,&agent);
    EXPECT_FALSE(state.getObject(ally).is_exhausted);
    EXPECT_TRUE(state.getObject(ally).cant_move_this_turn);
    EXPECT_TRUE(state.getObject(enemy).is_exhausted);
    EXPECT_EQ(state.player(P1).hand.size(),before);
}
TEST_F(RadianceBatch8Test, HeraldChangesBaseMightWithoutOverwritingPrintedMight) {
    auto ally=addUnit(P1,kInvalidId,2,0);
    const auto herald=addToHand(P1,CardDefId{1014});
    EnginePathAgent agent(EnginePathAgent::choosing(ally));
    playThroughEngine(herald,&agent);
    EXPECT_EQ(state.getObject(ally).base_might,2);
    EXPECT_EQ(state.getObject(ally).baseMight(),5);
    EXPECT_EQ(state.getObject(ally).current_might,5);
}
TEST_F(RadianceBatch8Test, MomentaryCompanionHasHiddenAndNotTemporaryByDefault) {
    auto c=addToHand(P1,CardDefId{1015});
    playThroughEngine(c);
    EXPECT_TRUE(state.getObject(c).hasKeyword(Keyword::Hidden));
    EXPECT_FALSE(state.getObject(c).hasKeyword(Keyword::Temporary));
}
TEST_F(RadianceBatch8Test, EntrenchedBoarDefaultsToExhaustedWhenReadyNotChosen) {
    const auto c=addToHand(P1,CardDefId{1012});
    playThroughEngine(c);
    EXPECT_TRUE(state.getObject(c).location.has_value());
    EXPECT_TRUE(state.getObject(c).is_exhausted);
}
} // namespace riftbound::test::radiance_batch8
