#include "tests/cards/card_test_fixture.h"
#include "engine/keyword_abilities.h"
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
TEST_F(RadianceBatch9Test, GuidebotDepartedBeforeFinalizationStillClosesChoices) {
    // Regress the native 407 Nasus v Rek'Sai Game 3 crash: Rocket Barrage
    // kills a Guidebot while its earlier WhenYouPlayACard trigger is pending.
    // An optional trigger that cannot act must record "nothing to decide"
    // and/or reach the end-of-choices marker, NEVER return early.
    auto bot=addUnit(P1,CardDefId{1025},3,0);
    withEngine([&](GameEngine& engine) {
        auto& s=engine.mutableState();
        ASSERT_TRUE(s.objectExists(bot));
        s.getObject(bot).location.reset(); // source left the board
        ChainItem pending;
        pending.id=s.chain.allocateId();
        pending.source=bot;
        pending.card_def_id=CardDefId{1025};
        pending.controller=P1;
        pending.is_ability=true;
        pending.is_activated_ability=false;
        pending.fired_trigger=TriggerType::WhenYouPlayACard;
        pending.finalizing=true;
        pending.triggering_subject=kInvalidId;
        s.chain.resuming=pending;
        auto* printed=card_registry.get(CardDefId{1025});
        ASSERT_NE(printed,nullptr);
        CardContext ctx{s,events,engine.testHook_executor(),P1,bot};
        ctx.registry=&card_registry;
        printed->onTrigger(ctx,{});
        ASSERT_TRUE(s.chain.resuming.has_value());
        EXPECT_EQ(s.chain.resuming->may_answer,0);
        EXPECT_NE(s.chain.resuming->finalize_checked & 64,0)
            << "A Guidebot with no location must still finish its choices";
        s.chain.resuming.reset();
    });
}
TEST_F(RadianceBatch9Test, GuidebotWithNoSourceObjectFinalizesWithoutPrompt) {
    withEngine([&](GameEngine& engine) {
        auto& s=engine.mutableState();
        ChainItem pending;
        pending.id=s.chain.allocateId();
        pending.source=kInvalidId;
        pending.card_def_id=CardDefId{1025};
        pending.controller=P1;
        pending.is_ability=true;
        pending.fired_trigger=TriggerType::WhenYouPlayACard;
        pending.finalizing=true;
        pending.triggering_subject=kInvalidId;
        s.chain.resuming=pending;
        const Card* printed=card_registry.get(CardDefId{1025});
        ASSERT_NE(printed,nullptr);
        CardContext ctx{s,events,engine.testHook_executor(),P1,kInvalidId};
        printed->onTrigger(ctx,{});
        ASSERT_TRUE(s.chain.resuming.has_value());
        EXPECT_EQ(s.chain.resuming->may_answer,0);
        EXPECT_NE(s.chain.resuming->finalize_checked & 64,0);
        s.chain.resuming.reset();
    });
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
        {996,"RAD-049/167","Industrious Mechsmith",4,0},
        {1029,"RAD-050/167","Mysterious Chronomancer",5,0},
        {1030,"RAD-055/167","Clanging Sentry",3,0},
        {1004,"RAD-072/167","Overloaded Traveler",2,0},
        {1008,"RAD-076/167","Sneaky Zeebles",2,0},
        {1000,"RAD-083/167","Stalwart Goatherd",4,0},
        {1034,"RAD-093/167","Disposal Expert",4,0},
        {1035,"RAD-097/167","Siren of the Shallows",2,0},
        {993,"RAD-099/167","Suave Negotiator",3,0},
        {1009,"RAD-117/167","For Demacia!",3,0},
        {999,"RAD-119/167","Hunting Dog",3,0},
        {1006,"RAD-128/167","Steadfast Outrider",4,0},
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
    EXPECT_TRUE(card_db.get(CardDefId{1000}).keywords.has(Keyword::Shield));
    EXPECT_TRUE(card_db.get(CardDefId{1009}).keywords.has(Keyword::Reaction));
    EXPECT_TRUE(card_db.get(CardDefId{999}).keywords.has(Keyword::Deathknell));
    EXPECT_TRUE(card_db.get(CardDefId{1006}).keywords.has(Keyword::Tank));
}
TEST_F(RadianceBatch9Test, IndustriousMechsmithPlaysThreeMightMechTokenAtSameBattlefield) {
    auto smith=addToHand(P1,CardDefId{996});
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
    auto traveler=addUnit(P1,CardDefId{1004},2,0);
    auto banner=addToHand(P1,CardDefId{1010});
    playThroughEngine(banner,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
    withEngine([&](GameEngine& engine){engine.testHook_recalculateAuras();});
    EXPECT_EQ(state.getObject(traveler).current_might,3);
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(banner);});
    withEngine([&](GameEngine& engine){engine.testHook_recalculateAuras();});
    EXPECT_EQ(state.getObject(traveler).current_might,2);
}
TEST_F(RadianceBatch9Test, SneakyZeeblesConquerAddsOneFloatingUniversalPower) {
    auto zeebles=addUnit(P1,CardDefId{1008},1,0);
    const auto before=state.player(P1).rune_pool.universal_power;
    fireTriggerThroughEngine(zeebles,TriggerType::WhenIConquer);
    EXPECT_EQ(state.player(P1).rune_pool.universal_power,before+1);
}


TEST_F(RadianceBatch9Test, StalwartGoatherdHasShieldTwoAndMayKillLowCostGear) {
    auto target=addToHand(P1,CardDefId{1010}); // printed Energy 1
    playThroughEngine(target,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
    auto goatherd=addToHand(P1,CardDefId{1000});
    EnginePathAgent agent(EnginePathAgent::accepting());
    playThroughEngine(goatherd,&agent);
    EXPECT_TRUE(state.getObject(goatherd).hasKeyword(Keyword::Shield));
    EXPECT_EQ(state.getObject(goatherd).shield_value,2);
    EXPECT_EQ(state.getObject(target).zone,ZoneType::Trash);
}
TEST_F(RadianceBatch9Test, DisposalExpertEntersReadyOnlyWithoutOtherFriendlyUnits) {
    auto first=addToHand(P1,CardDefId{1034});
    playThroughEngine(first);
    EXPECT_FALSE(state.getObject(first).is_exhausted);
    EXPECT_TRUE(state.getObject(first).hasKeyword(Keyword::Disarm));
    auto second=addToHand(P1,CardDefId{1034});
    playThroughEngine(second);
    EXPECT_TRUE(state.getObject(second).is_exhausted);
}
TEST_F(RadianceBatch9Test, SirenHasGankingAndDisarmOnTheBattlefield) {
    auto siren=addUnit(P1,CardDefId{1035},1,0);
    EXPECT_TRUE(state.getObject(siren).hasKeyword(Keyword::Ganking));
    EXPECT_TRUE(state.getObject(siren).hasKeyword(Keyword::Disarm));
}
TEST_F(RadianceBatch9Test, SuaveNegotiatorDrawsForBothPlayersOnPlay) {
    addToDeck(P1,CardDefId{1012});
    addToDeck(P2,CardDefId{1012});
    auto before1=state.player(P1).hand.size();
    auto before2=state.player(P2).hand.size();
    auto negotiator=addToHand(P1,CardDefId{993});
    playThroughEngine(negotiator);
    EXPECT_EQ(state.player(P1).hand.size(),before1+1);
    EXPECT_EQ(state.player(P2).hand.size(),before2+1);
}
TEST_F(RadianceBatch9Test, ForDemaciaShieldsOnlyFriendlyUnitsAtChosenBattlefield) {
    auto ally=addUnit(P1,kInvalidId,3,0);
    auto other=addUnit(P1,kInvalidId,3,1);
    auto enemy=addUnit(P2,kInvalidId,3,0);
    auto spell=addToHand(P1,CardDefId{1009});
    playThroughEngine(spell);
    EXPECT_TRUE(state.getObject(ally).hasKeyword(Keyword::Shield));
    EXPECT_EQ(state.getObject(ally).shield_value,2);
    EXPECT_FALSE(state.getObject(other).hasKeyword(Keyword::Shield));
    EXPECT_FALSE(state.getObject(enemy).hasKeyword(Keyword::Shield));
}
TEST_F(RadianceBatch9Test, HuntingDogDeathknellCreatesDeflectBirdAtBase) {
    auto dog=addUnit(P1,CardDefId{999},3,0);
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(dog);});
    int birds=0;
    for(const auto& [id,u]:state.objects.onBoard())
        if(u.isUnit()&&u.name=="Bird"&&u.controller==P1&&u.isToken()){
            ++birds;
            EXPECT_TRUE(u.hasKeyword(Keyword::Deflect));
            EXPECT_EQ(u.base_might,1);
            EXPECT_FALSE(u.isAtBattlefield());
        }
    EXPECT_EQ(birds,1);
}
TEST_F(RadianceBatch9Test, SteadfastOutriderRequiresTwoOtherFriendsHereForTwoMight) {
    auto outrider=addUnit(P1,CardDefId{1006},3,0);
    auto friend1=addUnit(P1,kInvalidId,2,0);
    withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
    EXPECT_EQ(state.getObject(outrider).current_might,3);
    auto gear=addToHand(P1,CardDefId{1010});
    playThroughEngine(gear,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
    withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
    EXPECT_EQ(state.getObject(outrider).current_might,5);
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(gear);});
    withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
    EXPECT_EQ(state.getObject(outrider).current_might,3);
    EXPECT_TRUE(state.getObject(friend1).location.has_value());
}


TEST_F(RadianceBatch9Test, DisarmTwoFromDisposalExpertLowersEnemyMightOnceWhenAttacking) {
    auto attacker=addUnit(P1,CardDefId{1034},3,0);
    auto defender=addUnit(P2,kInvalidId,5,0);
    EnginePathAgent choice(EnginePathAgent::choosing(defender));
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CombatStartedEvent{state.battlefields[0].id,P1,P2});
    },&choice);
    EXPECT_TRUE(state.getObject(attacker).hasKeyword(Keyword::Disarm));
    EXPECT_EQ(state.getObject(defender).temp_might_bonus,-2);
    EXPECT_EQ(state.getObject(defender).current_might,3);
}
TEST_F(RadianceBatch9Test, SirenDisarmsForOneAndCanGank) {
    addUnit(P1,CardDefId{1035},1,0);
    auto defender=addUnit(P2,kInvalidId,5,0);
    EnginePathAgent choice(EnginePathAgent::choosing(defender));
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CombatStartedEvent{state.battlefields[0].id,P1,P2});
    },&choice);
    EXPECT_EQ(state.getObject(defender).temp_might_bonus,-1);
}
TEST_F(RadianceBatch9Test, TwoClangingSentriesStackDisarmTwoOnFriendlyMech) {
    auto mech=addUnit(P1,kInvalidId,3,0);
    state.getObject(mech).tags={"Mech"};
    addUnit(P1,CardDefId{1030},2,0);
    addUnit(P1,CardDefId{1030},2,0);
    auto defender=addUnit(P2,kInvalidId,6,0);
    withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
    ASSERT_TRUE(state.getObject(mech).hasKeyword(Keyword::Disarm));
    EnginePathAgent choice(EnginePathAgent::choosing(defender));
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CombatStartedEvent{state.battlefields[0].id,P1,P2});
    },&choice);
    EXPECT_EQ(state.getObject(defender).temp_might_bonus,-2);
}
TEST_F(RadianceBatch9Test, DisarmDoesNotTargetFriendlyUnitsOrUnitsAtOtherBattlefields) {
    addUnit(P1,CardDefId{1029},4,0);
    auto ally=addUnit(P1,kInvalidId,5,0);
    auto elsewhere=addUnit(P2,kInvalidId,5,1);
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CombatStartedEvent{state.battlefields[0].id,P1,P2});
    });
    EXPECT_EQ(state.getObject(ally).temp_might_bonus,0);
    EXPECT_EQ(state.getObject(elsewhere).temp_might_bonus,0);
}


TEST_F(RadianceBatch9Test, DisarmIsAReactableFinalizableKeywordTrigger) {
    const Card* ability=keywordAbilityCard(Keyword::Disarm);
    ASSERT_NE(ability,nullptr);
    EXPECT_NE(ability->choicesAtFinalization(),0u);
    EXPECT_EQ(ability->triggerType(),TriggerType::WhenIAttack);
    auto attacker=addUnit(P1,CardDefId{1034},3,0);
    EXPECT_EQ(keywordAbilityInstances(state.getObject(attacker),
                                      Keyword::Disarm,false),1);
}
TEST_F(RadianceBatch9Test, DisarmStacksPrintedTwoAndAuraOneAsOneTrigger) {
    auto attacker=addUnit(P1,CardDefId{1034},3,0);
    state.getObject(attacker).tags={"Mech"};
    addUnit(P1,CardDefId{1030},2,0);
    auto enemy=addUnit(P2,kInvalidId,7,0);
    withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
    ASSERT_TRUE(state.getObject(attacker).hasKeyword(Keyword::Disarm));
    EXPECT_EQ(keywordAbilityInstances(state.getObject(attacker),Keyword::Disarm,false),1);
    EnginePathAgent chooser(EnginePathAgent::choosing(enemy));
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CombatStartedEvent{state.battlefields[0].id,P1,P2});
    },&chooser);
    EXPECT_EQ(state.getObject(enemy).temp_might_bonus,-3);
}
TEST_F(RadianceBatch9Test, DefendingDisarmUnitDoesNotDebuffAttacker) {
    auto attacker=addUnit(P1,kInvalidId,5,0);
    addUnit(P2,CardDefId{1035},1,0);
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CombatStartedEvent{state.battlefields[0].id,P1,P2});
    });
    EXPECT_EQ(state.getObject(attacker).temp_might_bonus,0);
}

} // namespace riftbound::test::radiance_batch9
