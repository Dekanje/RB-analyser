// Mechanics Batch 6: full engine-path tests for three added Radiance units.
#include "tests/cards/card_test_fixture.h"
#include "cards/card.h"
#include <gtest/gtest.h>
#include <optional>
#include <vector>
namespace riftbound::test::radiance_batch6 {
class RadianceBatch6Test : public CardTestFixture {
protected:
    std::vector<GameObjectId> tokensNamed(const char* name) const {
        std::vector<GameObjectId> out;
        for (const auto& [id,obj]:state.objects.onBoard())
            if (obj.isUnit() && obj.name==name && obj.location.has_value())
                out.push_back(id);
        return out;
    }
};

TEST_F(RadianceBatch6Test, NewCardsHaveExactPrintedIdentities) {
    const auto& apparatus=card_db.get(998);
    EXPECT_EQ(apparatus.public_code,"RAD-009/167");
    EXPECT_EQ(apparatus.energy_cost,6);
    EXPECT_EQ(apparatus.power_cost,1);
    EXPECT_EQ(apparatus.might,3);
    EXPECT_TRUE(apparatus.domains.empty());
    const auto& dog=card_db.get(999);
    EXPECT_EQ(dog.public_code,"RAD-119/167");
    EXPECT_EQ(dog.energy_cost,3);
    EXPECT_EQ(dog.might,3);
    EXPECT_TRUE(dog.keywords.has(Keyword::Deathknell));
    const auto& goat=card_db.get(1000);
    EXPECT_EQ(goat.public_code,"RAD-083/167");
    EXPECT_EQ(goat.energy_cost,4);
    EXPECT_EQ(goat.might,2);
    EXPECT_EQ(goat.shield_value,2);
    EXPECT_TRUE(goat.keywords.has(Keyword::Shield));
}

TEST_F(RadianceBatch6Test, ApparatusAndItsMechEnterReadyInBase) {
    auto card=addToHand(P1,CardDefId{998});
    playThroughEngine(card);
    EXPECT_FALSE(state.getObject(card).is_exhausted);
    auto tokens=tokensNamed("Mech");
    ASSERT_EQ(tokens.size(),1u);
    EXPECT_EQ(state.getObject(tokens[0]).current_might,3);
    EXPECT_EQ(state.getObject(tokens[0]).controller,P1);
    EXPECT_TRUE(state.getObject(tokens[0]).isAtBase());
    EXPECT_FALSE(state.getObject(tokens[0]).is_exhausted);
}

TEST_F(RadianceBatch6Test, ApparatusPlaysMechAtSameBattlefield) {
    state.battlefields[0].controller=P1;
    const auto bf=state.battlefields[0].id;
    auto card=addToHand(P1,CardDefId{998});
    playThroughEngine(card,nullptr,LocationId{BattlefieldLocation{bf}});
    auto tokens=tokensNamed("Mech");
    ASSERT_EQ(tokens.size(),1u);
    EXPECT_EQ(state.getObject(tokens[0]).battlefieldId(),std::optional<BattlefieldId>{bf});
    EXPECT_EQ(state.getObject(card).battlefieldId(),std::optional<BattlefieldId>{bf});
    EXPECT_FALSE(state.getObject(tokens[0]).is_exhausted);
}

TEST_F(RadianceBatch6Test, HuntingDogDoesNotCreateBirdJustByBeingPlayed) {
    auto dog=addToHand(P1,CardDefId{999});
    playThroughEngine(dog);
    EXPECT_TRUE(tokensNamed("Bird").empty());
}

TEST_F(RadianceBatch6Test, HuntingDogDeathCreatesDeflectBirdInControllerBase) {
    auto dog=addToHand(P1,CardDefId{999});
    playThroughEngine(dog);
    resolveThroughEngine([&](EffectExecutor& ex,GameState&) {ex.killObject(dog);});
    EXPECT_EQ(state.getObject(dog).zone,ZoneType::Trash);
    auto birds=tokensNamed("Bird");
    ASSERT_EQ(birds.size(),1u);
    EXPECT_EQ(state.getObject(birds.front()).controller,P1);
    EXPECT_EQ(state.getObject(birds.front()).current_might,1);
    EXPECT_TRUE(state.getObject(birds.front()).isAtBase());
    EXPECT_TRUE(state.getObject(birds.front()).keywords.has(Keyword::Deflect));
}

TEST_F(RadianceBatch6Test, GoatherdMayDeclineKillingAnyGear) {
    auto gear=addToHand(P1,CardDefId{345}); // printed Energy cost 2
    playThroughEngine(gear);
    ASSERT_TRUE(state.getObject(gear).location.has_value());
    auto goat=addToHand(P1,CardDefId{1000});
    EnginePathAgent decline([](const std::vector<Intent>& legal) {
        for (const auto& intent:legal)
            if (intent.chosen_objects.empty()) return intent;
        return legal.front();
    });
    playThroughEngine(goat,&decline);
    EXPECT_TRUE(state.getObject(gear).location.has_value());
    EXPECT_TRUE(state.getObject(goat).location.has_value());
}

TEST_F(RadianceBatch6Test, GoatherdCanKillChosenAffordableGear) {
    auto gear=addToHand(P1,CardDefId{345});
    playThroughEngine(gear);
    auto goat=addToHand(P1,CardDefId{1000});
    EnginePathAgent choose(EnginePathAgent::choosing(gear));
    playThroughEngine(goat,&choose);
    EXPECT_FALSE(state.getObject(gear).location.has_value());
    EXPECT_TRUE(state.getObject(goat).location.has_value());
}

TEST_F(RadianceBatch6Test, GoatherdDoesNothingWithoutLegalGearTarget) {
    auto goat=addToHand(P1,CardDefId{1000});
    playThroughEngine(goat);
    EXPECT_TRUE(state.getObject(goat).location.has_value());
    EXPECT_TRUE(tokensNamed("Mech").empty());
}
}
