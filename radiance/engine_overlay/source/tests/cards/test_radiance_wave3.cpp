// Wave 3 deterministic engine-path tests for RAD-008 War Scout.
#include "tests/cards/card_test_fixture.h"
#include "cards/card.h"
#include <gtest/gtest.h>

namespace riftbound::test::radiance_wave3 {
class RadianceWave3Test : public CardTestFixture {};

TEST_F(RadianceWave3Test, WarScoutPrintedIdentityAndAccelerate) {
 const auto& d=card_db.get(995);
 EXPECT_EQ(d.public_code,"RAD-008/167");
 ASSERT_EQ(d.domains.size(),1u);
 EXPECT_EQ(d.domains.front(),Domain::Fury);
 EXPECT_EQ(d.card_type,CardType::Unit);
 EXPECT_EQ(d.energy_cost,3);
 EXPECT_EQ(d.might,2);
 EXPECT_TRUE(d.keywords.has(Keyword::Accelerate));
}

TEST_F(RadianceWave3Test, WarScoutBuffsChosenFriendlyUnitViaTriggeredChoice) {
 const auto target=addUnit(P1,kInvalidId,4,0);
 auto scout=addToHand(P1,995);
 EnginePathAgent agent(EnginePathAgent::choosing(target));
 playThroughEngine(scout,&agent);
 ASSERT_TRUE(state.objectExists(target));
 EXPECT_EQ(state.getObject(target).current_might,6);
}

TEST_F(RadianceWave3Test, WarScoutCanBuffEnemyUnitViaTriggeredChoice) {
 const auto target=addUnit(P2,kInvalidId,3,0);
 auto scout=addToHand(P1,995);
 EnginePathAgent agent(EnginePathAgent::choosing(target));
 playThroughEngine(scout,&agent);
 ASSERT_TRUE(state.objectExists(target));
 EXPECT_EQ(state.getObject(target).current_might,5);
}
}
