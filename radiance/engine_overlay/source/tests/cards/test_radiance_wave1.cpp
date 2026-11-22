// Deterministic engine-path scenarios for the first five Radiance cards.
// These are distinct from registry-only metadata checks.
#include "tests/cards/card_test_fixture.h"
#include "cards/card.h"
#include <gtest/gtest.h>
#include <variant>

namespace riftbound::test::radiance_wave1 {
class RadianceWave1Test : public CardTestFixture {};

TEST_F(RadianceWave1Test, EveryCardHasItsExactCodeAndRegistryDefinition) {
    const std::pair<CardDefId,const char*> ids[] = {
        {989,"RAD-077/167"},{990,"RAD-088/167"},
        {991,"RAD-059/167"},{992,"RAD-079/167"},
        {993,"RAD-099/167"}
    };
    for (const auto& [id, code] : ids) {
        ASSERT_NE(card_registry.get(id),nullptr);
        const auto& d=card_db.get(id);
        EXPECT_EQ(d.public_code,code);
        EXPECT_EQ(d.set_code,"RAD");
        EXPECT_FALSE(d.name.empty());
    }
}

TEST_F(RadianceWave1Test, WrathAlwaysEntersReadyAndHasShieldThree) {
    const auto& d=card_db.get(989);
    EXPECT_EQ(d.shield_value,3);
    EXPECT_TRUE(card_registry.get(989)->entersReadyOnPlay(state,P1));
    auto card=addToHand(P1,989);
    playThroughEngine(card);
    ASSERT_TRUE(state.objectExists(card));
    EXPECT_TRUE(state.getObject(card).location.has_value());
    EXPECT_FALSE(state.getObject(card).is_exhausted);
}

TEST_F(RadianceWave1Test, StaunchSurvivorHasPrintedAssaultAndShieldTwo) {
    const auto& d=card_db.get(990);
    EXPECT_EQ(d.might,2);
    EXPECT_EQ(d.assault_value,2);
    EXPECT_EQ(d.shield_value,2);
    EXPECT_EQ(d.energy_cost,2);
    EXPECT_EQ(d.power_cost,1);
}

TEST_F(RadianceWave1Test, SupernovaDealsTenToChosenUnitAndDrawsTwo) {
    const auto victim=addUnit(P2,kInvalidId,3,0);
    addToDeck(P1,4);
    addToDeck(P1,4);
    auto spell=addToHand(P1,991);
    EnginePathAgent agent(EnginePathAgent::choosing(victim));
    playThroughEngine(spell,&agent);
    EXPECT_FALSE(state.getObject(victim).location.has_value());
    EXPECT_EQ(state.player(P1).hand.size(),2u);
}

TEST_F(RadianceWave1Test, AvalancheHitsBothBasesButNotBattlefields) {
    const auto friendly=addUnit(P1,kInvalidId,2);
    const auto enemy=addUnit(P2,kInvalidId,2);
    const auto battlefield=addUnit(P2,kInvalidId,5,0);
    const auto spell=addToHand(P1,992);
    playThroughEngine(spell);
    EXPECT_FALSE(state.getObject(friendly).location.has_value());
    EXPECT_FALSE(state.getObject(enemy).location.has_value());
    EXPECT_TRUE(state.getObject(battlefield).location.has_value());
}

TEST_F(RadianceWave1Test, SuaveNegotiatorDrawsOneForEachPlayer) {
    addToDeck(P1,4);
    addToDeck(P2,4);
    auto card=addToHand(P1,993);
    playThroughEngine(card);
    EXPECT_EQ(state.player(P1).hand.size(),1u);
    EXPECT_EQ(state.player(P2).hand.size(),1u);
}
} // namespace riftbound::test::radiance_wave1
