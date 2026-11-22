// Wave 2 deterministic engine-path tests for RAD-004 Brawl.
#include "tests/cards/card_test_fixture.h"
#include "cards/card.h"
#include <gtest/gtest.h>
namespace riftbound::test::radiance_wave2 {
class RadianceWave2Test: public CardTestFixture {};
TEST_F(RadianceWave2Test, BrawlIsRegisteredAsChaosActionWithPrintedCost) {
 const auto& d=card_db.get(994);
 EXPECT_EQ(d.public_code,"RAD-004/167");
 ASSERT_EQ(d.domains.size(),1u);
 EXPECT_EQ(d.domains.front(),Domain::Chaos);
 EXPECT_EQ(d.energy_cost,3);
 EXPECT_EQ(d.power_cost,1);
 EXPECT_TRUE(d.keywords.has(Keyword::Action));
}
TEST_F(RadianceWave2Test, BrawlGrantsAssaultEqualToChosenUnitMight) {
 const auto target=addUnit(P1,kInvalidId,4,0);
 auto spell=addToHand(P1,994);
 EnginePathAgent agent(EnginePathAgent::choosing(target));
 playThroughEngine(spell,&agent);
 ASSERT_TRUE(state.objectExists(target));
 const auto& u=state.getObject(target);
 EXPECT_TRUE(u.keywords.has(Keyword::Assault));
 EXPECT_EQ(u.temp_assault_value,4);
}
TEST_F(RadianceWave2Test, BrawlCanTargetEnemyUnit) {
 const auto target=addUnit(P2,kInvalidId,3,0);
 auto spell=addToHand(P1,994);
 EnginePathAgent agent(EnginePathAgent::choosing(target));
 playThroughEngine(spell,&agent);
 ASSERT_TRUE(state.objectExists(target));
 EXPECT_EQ(state.getObject(target).temp_assault_value,3);
}
} // namespace
