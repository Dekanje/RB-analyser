// Wave 4: check actual engine effects, not card names or metadata alone.
#include "tests/cards/card_test_fixture.h"
#include "cards/card.h"
#include <gtest/gtest.h>
#include <algorithm>
#include <variant>
namespace riftbound::test::radiance_wave4 {
class RadianceWave4Test : public CardTestFixture {
protected:
    std::vector<GameObjectId> mechTokens() const {
        std::vector<GameObjectId> ids;
        for (const auto& [id,obj] : state.objects.onBoard()) {
            if (obj.name == "Mech" && obj.isUnit() && obj.location.has_value())
                ids.push_back(id);
        }
        return ids;
    }
};

TEST_F(RadianceWave4Test, PrintedCostDomainAndIdentity) {
    const auto& smith=card_db.get(996);
    const auto& tracker=card_db.get(997);
    EXPECT_EQ(smith.public_code,"RAD-049/167");
    EXPECT_TRUE(smith.domains.empty());           // neutral
    EXPECT_EQ(smith.energy_cost,4);
    EXPECT_EQ(smith.might,1);
    EXPECT_EQ(tracker.public_code,"RAD-003/167");
    ASSERT_EQ(tracker.domains.size(),1u);
    EXPECT_EQ(tracker.domains.front(),Domain::Body);
    EXPECT_EQ(tracker.energy_cost,3);
    EXPECT_EQ(tracker.might,3);
}

TEST_F(RadianceWave4Test, IndustriousMechsmithCreatesThreeMightMechInBase) {
    auto smith=addToHand(P1,996);
    playThroughEngine(smith);
    auto tokens=mechTokens();
    ASSERT_EQ(tokens.size(),1u);
    const auto& mech=state.getObject(tokens.front());
    EXPECT_EQ(mech.current_might,3);
    EXPECT_EQ(mech.controller,P1);
    EXPECT_TRUE(mech.isAtBase());
    EXPECT_TRUE(mech.is_exhausted);
    EXPECT_TRUE(state.getObject(smith).is_exhausted); // played to base normally
}

TEST_F(RadianceWave4Test, IndustriousMechsmithCreatesTokenAtSameBattlefield) {
    state.battlefields[0].controller=P1;
    auto smith=addToHand(P1,996);
    const auto bf=state.battlefields[0].id;
    playThroughEngine(smith,nullptr,LocationId{BattlefieldLocation{bf}});
    auto tokens=mechTokens();
    ASSERT_EQ(tokens.size(),1u);
    EXPECT_EQ(state.getObject(smith).battlefieldId(),std::optional<BattlefieldId>{bf});
    EXPECT_EQ(state.getObject(tokens.front()).battlefieldId(),
              std::optional<BattlefieldId>{bf});
    EXPECT_EQ(state.getObject(tokens.front()).current_might,3);
}

TEST_F(RadianceWave4Test, BilgewaterTrackerCanDeclineEveryOptionalTarget) {
    const auto target=addUnit(P2,kInvalidId,3,0);
    auto tracker=addToHand(P1,997);
    EnginePathAgent agent([](const std::vector<Intent>& legal) {
        for (const auto& i : legal)
            if (i.type==IntentType::MakeChoice && i.chosen_objects.empty())
                return i; // decline: choose no units
        return legal.front();
    });
    playThroughEngine(tracker,&agent);
    EXPECT_EQ(state.getObject(target).damage_marked,0);
    EXPECT_TRUE(state.getObject(tracker).location.has_value());
}

TEST_F(RadianceWave4Test, BilgewaterTrackerChoosesTwoUnitsAndNotThird) {
    const auto first=addUnit(P2,kInvalidId,4,0);
    const auto second=addUnit(P1,kInvalidId,4,1);
    const auto third=addUnit(P2,kInvalidId,4,1);
    auto tracker=addToHand(P1,997);
    EnginePathAgent agent([first,second,choice=0](const std::vector<Intent>& legal) mutable {
        const GameObjectId wanted=choice++ == 0 ? first : second;
        for (const auto& i : legal)
            if (!i.chosen_objects.empty() && i.chosen_objects.front()==wanted)
                return i;
        return legal.front();
    });
    playThroughEngine(tracker,&agent);
    EXPECT_EQ(state.getObject(first).damage_marked,1);
    EXPECT_EQ(state.getObject(second).damage_marked,1);
    EXPECT_EQ(state.getObject(third).damage_marked,0);
    EXPECT_EQ(state.getObject(tracker).damage_marked,0);
}

TEST_F(RadianceWave4Test, BilgewaterTrackerDamageIsLethalForOneMightUnits) {
    const auto victim=addUnit(P2,kInvalidId,1,0);
    const auto survivor=addUnit(P2,kInvalidId,4,1);
    auto tracker=addToHand(P1,997);
    EnginePathAgent agent(EnginePathAgent::choosing(victim));
    playThroughEngine(tracker,&agent);
    EXPECT_FALSE(state.getObject(victim).location.has_value());
    EXPECT_TRUE(state.getObject(survivor).location.has_value());
    EXPECT_EQ(state.getObject(survivor).damage_marked,0);
}
} // namespace riftbound::test::radiance_wave4
