// Batch 7: executable engine-path coverage for new cards 1001-1009 and existing RAD-101 engine card 984.
#include "tests/cards/card_test_fixture.h"
#include "cards/card.h"
#include "cards/card_helpers.h"
#include <gtest/gtest.h>
#include <optional>
namespace riftbound::test::radiance_batch7 {
class RadianceBatch7Test : public CardTestFixture {
protected:
    void recalc() {withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});}
};

TEST_F(RadianceBatch7Test, NineNewIdentitiesAndPreexistingOfferAreCorrect) {
    EXPECT_EQ(card_db.get(1001).public_code,"RAD-058/167");
    EXPECT_TRUE(card_db.get(1001).keywords.has(Keyword::Accelerate));
    EXPECT_EQ(card_db.get(1001).energy_cost,4);
    EXPECT_EQ(card_db.get(1001).power_cost,1);
    EXPECT_EQ(card_db.get(1002).public_code,"RAD-048/167");
    EXPECT_TRUE(card_db.get(1002).keywords.has(Keyword::Reaction));
    EXPECT_EQ(card_db.get(1003).public_code,"RAD-071/167");
    EXPECT_TRUE(card_db.get(1003).keywords.has(Keyword::Equip));
    EXPECT_EQ(card_db.get(1004).public_code,"RAD-072/167");
    EXPECT_EQ(card_db.get(1005).public_code,"RAD-122/167");
    EXPECT_TRUE(card_db.get(1005).keywords.has(Keyword::Tank));
    EXPECT_EQ(card_db.get(1006).public_code,"RAD-128/167");
    EXPECT_TRUE(card_db.get(1006).keywords.has(Keyword::Tank));
    EXPECT_EQ(card_db.get(1007).public_code,"RAD-037/167");
    EXPECT_EQ(card_db.get(1008).public_code,"RAD-076/167");
    EXPECT_EQ(card_db.get(1009).public_code,"RAD-117/167");
    EXPECT_TRUE(card_db.get(1009).keywords.has(Keyword::Reaction));
    EXPECT_EQ(card_db.get(984).public_code,"RAD-101/167");
    EXPECT_TRUE(card_db.get(984).keywords.has(Keyword::Action));
}

TEST_F(RadianceBatch7Test, RiptideMageDebuffsAnEnemyOnRealPlay) {
    const auto enemy=addUnit(P2,kInvalidId,6,0);
    const auto friendUnit=addUnit(P1,kInvalidId,6,0);
    const auto mage=addToHand(P1,CardDefId{1001});
    EnginePathAgent agent(EnginePathAgent::choosing(enemy));
    playThroughEngine(mage,&agent);
    EXPECT_EQ(state.getObject(enemy).current_might,3);
    EXPECT_EQ(state.getObject(friendUnit).current_might,6);
}

TEST_F(RadianceBatch7Test, HighNoteCountsOnlyFriendlyExhaustedUnits) {
    const auto a=addUnit(P1,kInvalidId,4,0);
    const auto b=addUnit(P1,kInvalidId,4,1);
    const auto opponentExhausted=addUnit(P2,kInvalidId,4,1);
    const auto target=addUnit(P2,kInvalidId,6,0);
    state.getObject(a).is_exhausted=true;
    state.getObject(b).is_exhausted=true;
    state.getObject(opponentExhausted).is_exhausted=true;
    const auto spell=addToHand(P1,CardDefId{1002});
    EnginePathAgent agent(EnginePathAgent::choosing(target));
    playThroughEngine(spell,&agent);
    EXPECT_EQ(state.getObject(target).current_might,4);
}

TEST_F(RadianceBatch7Test, NazumanNtofoHasEnergyOnlyEquipCostAndShieldTwo) {
    Card* gear=card_registry.get(CardDefId{1003});
    ASSERT_NE(gear,nullptr);
    EXPECT_TRUE(gear->hasEquipAbility());
    auto cost=gear->equipCost(state,P1,kInvalidId,kInvalidId);
    EXPECT_TRUE(cost.valid);
    EXPECT_EQ(cost.energy,1);
    EXPECT_EQ(cost.power,0); // NO Order rune required for Equip [1]
    EXPECT_EQ(gear->equippedShield(),2);
    EXPECT_TRUE(gear->equippedKeywords().has(Keyword::Shield));
}

TEST_F(RadianceBatch7Test, PartyCrasherDiscountCountsOnlyExhaustedFriendlyUnits) {
    const auto friendlyA=addUnit(P1,kInvalidId,3,0);
    const auto friendlyB=addUnit(P1,kInvalidId,3,0);
    const auto enemy=addUnit(P2,kInvalidId,3,0);
    state.getObject(friendlyA).is_exhausted=true;
    state.getObject(friendlyB).is_exhausted=true;
    state.getObject(enemy).is_exhausted=true;
    const auto* card=card_registry.get(CardDefId{1005});
    ASSERT_NE(card,nullptr);
    EXPECT_EQ(card->selfCostReduction(state,P1),2);
    state.getObject(friendlyB).is_exhausted=false;
    EXPECT_EQ(card->selfCostReduction(state,P1),1);
}

TEST_F(RadianceBatch7Test, OverloadedTravelerNeedsFriendlyDeployGearAtSameBattlefield) {
    const auto traveler=addUnit(P1,CardDefId{1004},2,0);
    recalc();
    EXPECT_EQ(state.getObject(traveler).current_might,2); // no qualifying Deploy gear
    KeywordSet deploy; deploy.set(Keyword::Deploy);
    GameObjectId deployed=kInvalidId;
    resolveThroughEngine([&](EffectExecutor& e,GameState&){
        // Unattached gear at a battlefield is recalled during cleanup (CR 323.6).
        // Create it in base first; it must not grant the battlefield aura there.
        deployed=e.createToken(P1,CardType::Gear,"Test Deploy Gear",0,{},deploy,
            LocationId{BaseLocation{P1}},false);
    });
    recalc();
    EXPECT_EQ(state.getObject(traveler).current_might,2);
    resolveThroughEngine([&](EffectExecutor& e,GameState&){
        // Attachment follows the legal engine path and moves gear with its bearer.
        EXPECT_TRUE(e.attachGear(deployed,traveler));
    });
    recalc();
    EXPECT_EQ(state.getObject(deployed).battlefieldId(),
              state.getObject(traveler).battlefieldId());
    EXPECT_EQ(state.getObject(traveler).current_might,3);
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(deployed);});
    recalc();
    EXPECT_EQ(state.getObject(traveler).current_might,2);
}

TEST_F(RadianceBatch7Test, SteadfastOutriderRequiresTwoOtherAlliesAtSameBattlefield) {
    const auto outrider=addUnit(P1,CardDefId{1006},3,0);
    const auto other1=addUnit(P1,kInvalidId,2,0);
    recalc();
    EXPECT_EQ(state.getObject(outrider).current_might,3);
    const auto other2=addUnit(P1,kInvalidId,2,0);
    recalc();
    EXPECT_EQ(state.getObject(outrider).current_might,5);
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(other2);});
    recalc();
    EXPECT_EQ(state.getObject(outrider).current_might,3);
    EXPECT_TRUE(state.getObject(other1).location.has_value());
}

TEST_F(RadianceBatch7Test, WatchfulCuratorGrantsDeflectOnlyToFriendlyGear) {
    auto curator=addUnit(P1,CardDefId{1007},4,0);
    GameObjectId friendly=kInvalidId,enemy=kInvalidId;
    resolveThroughEngine([&](EffectExecutor& e,GameState&){
        friendly=e.createToken(P1,CardType::Gear,"Friendly Device",0,{},KeywordSet{},
                              LocationId{BaseLocation{P1}},false);
        enemy=e.createToken(P2,CardType::Gear,"Enemy Device",0,{},KeywordSet{},
                           LocationId{BaseLocation{P2}},false);
    });
    recalc();
    EXPECT_TRUE(state.getObject(friendly).hasKeyword(Keyword::Deflect));
    EXPECT_FALSE(state.getObject(enemy).hasKeyword(Keyword::Deflect));
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(curator);});
    recalc();
    EXPECT_FALSE(state.getObject(friendly).hasKeyword(Keyword::Deflect));
}

TEST_F(RadianceBatch7Test, SneakyZeeblesConquerAbilityAddsUnreactableUniversalPower) {
    const auto zeebles=addUnit(P1,CardDefId{1008},1,0);
    const Card* card=card_registry.get(CardDefId{1008});
    ASSERT_NE(card,nullptr);
    EXPECT_EQ(card->triggerType(),TriggerType::WhenIConquer);
    EXPECT_TRUE(card->triggeredAbilityAdds(TriggerType::WhenIConquer));
    const int before=state.player(P1).rune_pool.universal_power;
    withEngine([&](GameEngine& e){
        CardContext ctx{e.mutableState(),events,e.testHook_executor(),P1,zeebles};
        ctx.registry=&card_registry;
        card_registry.get(CardDefId{1008})->onTrigger(ctx,{});
    });
    EXPECT_EQ(state.player(P1).rune_pool.universal_power,before+1);
}

TEST_F(RadianceBatch7Test, ForDemaciaGrantsShieldAtChosenBattlefieldOnly) {
    const auto ally=addUnit(P1,kInvalidId,3,0);
    const auto elsewhere=addUnit(P1,kInvalidId,3,1);
    const auto enemy=addUnit(P2,kInvalidId,3,0);
    const auto card=addToHand(P1,CardDefId{1009});
    EnginePathAgent agent([](const std::vector<Intent>& legal){
        for(const auto& x:legal) if(x.chosen_value.has_value() && *x.chosen_value==0)return x;
        return legal.front();
    });
    playThroughEngine(card,&agent);
    EXPECT_TRUE(state.getObject(ally).keywords.has(Keyword::Shield));
    EXPECT_FALSE(state.getObject(elsewhere).keywords.has(Keyword::Shield));
    EXPECT_FALSE(state.getObject(enemy).keywords.has(Keyword::Shield));
}

TEST_F(RadianceBatch7Test, AnOfferKillsChosenGearAndCreatesExhaustedGold) {
    auto gear=addToHand(P1,CardDefId{345});
    playThroughEngine(gear);
    ASSERT_TRUE(state.getObject(gear).location.has_value());
    const auto spell=addToHand(P1,CardDefId{984});
    EnginePathAgent agent(EnginePathAgent::choosing(gear));
    playThroughEngine(spell,&agent);
    EXPECT_EQ(state.getObject(gear).zone,ZoneType::Trash);
    int gold=0;
    for(const auto& [id,g]:state.objects.onBoard()) {
        if(!g.isGear() || g.name!="Gold" || !g.location.has_value())continue;
        ++gold;
        EXPECT_EQ(g.controller,P1);
        EXPECT_TRUE(g.is_exhausted);
        EXPECT_EQ(g.card_def_id,kGoldGearCardDefId);
    }
    EXPECT_EQ(gold,1);
}

} // namespace riftbound::test::radiance_batch7
