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
        const auto& d=card_db.get(CardDefId::fromRaw(w.id));
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

TEST_F(RadianceBatch8Test, TrancheTwoPrintedCardDataAndKeywords) {
    struct Identity{int id;const char* code;int energy;int power;};
    const Identity expected[]={
      {1016,"RAD-007/167",3,1},{1017,"RAD-024/167",2,0},
      {1018,"RAD-027/167",3,0},{1019,"RAD-030/167",5,0},
      {1020,"RAD-036/167",6,0},{1021,"RAD-039/167",4,2},
      {1022,"RAD-052/167",1,0},{1023,"RAD-056/167",3,1},
      {1024,"RAD-100/167",1,0}
    };
    for(const auto& want:expected){
        const auto& d=card_db.get(CardDefId::fromRaw(want.id));
        EXPECT_EQ(d.public_code,want.code);
        EXPECT_EQ(d.energy_cost,want.energy);
        EXPECT_EQ(d.power_cost,want.power);
    }
    EXPECT_TRUE(card_db.get(CardDefId{1017}).keywords.has(Keyword::Deploy));
    EXPECT_TRUE(card_db.get(CardDefId{1020}).keywords.has(Keyword::Deflect));
    EXPECT_TRUE(card_db.get(CardDefId{1022}).keywords.has(Keyword::Deploy));
    EXPECT_TRUE(card_db.get(CardDefId{1023}).keywords.has(Keyword::Action));
    EXPECT_TRUE(card_db.get(CardDefId{1024}).keywords.has(Keyword::Hidden));
}
TEST_F(RadianceBatch8Test, RallyForWarMakesThreeRecruitsAtOccupiedEnemyBattlefield) {
    addUnit(P2,kInvalidId,5,0);
    state.battlefields[0].controller=P2;
    addUnit(P1,kInvalidId,2,1);
    auto spell=addToHand(P1,CardDefId{1016});
    playThroughEngine(spell);
    int recruits=0;
    for(const auto& [id,u]:state.objects.onBoard())
        if(u.isUnit()&&u.isToken()&&u.name=="Recruit"&&u.controller==P1&&
           u.battlefieldId()==state.battlefields[0].id) ++recruits;
    EXPECT_EQ(recruits,3);
}
TEST_F(RadianceBatch8Test, DreamrootDrawsForVictoryHereButNotAtAnotherBattlefield) {
    addUnit(P1,kInvalidId,3,0);
    auto dreamroot=addToHand(P1,CardDefId{1017});
    playThroughEngine(dreamroot,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
    ASSERT_TRUE(state.getObject(dreamroot).isAtBattlefield());
    addToDeck(P1,CardDefId{1012});
    auto start=state.player(P1).hand.size();
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CombatResultEvent{state.battlefields[1].id,P1});
    });
    EXPECT_EQ(state.player(P1).hand.size(),start);
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CombatResultEvent{state.battlefields[0].id,P1});
    });
    EXPECT_EQ(state.player(P1).hand.size(),start+1);
}
TEST_F(RadianceBatch8Test, AvianBuffsUnbuffedUnitThenAddsTwoTemporaryMight) {
    auto avian=addUnit(P1,CardDefId{1018},3,0);
    auto unit=addUnit(P1,kInvalidId,2,0);
    auto* card=card_registry.get(CardDefId{1018});
    ASSERT_NE(card,nullptr);
    EXPECT_TRUE(card->hasActivatedAbility());
    EXPECT_TRUE(card->getActivationCost().exhaust);
    resolveThroughEngine([&](EffectExecutor& executor,GameState& state){
        CardContext ctx{state,events,executor,P1,avian};
        ctx.registry=&card_registry;
        card->onActivate(ctx,{unit});
    });
    EXPECT_EQ(state.getObject(unit).buff_count,1);
    resolveThroughEngine([&](EffectExecutor& executor,GameState& state){
        CardContext ctx{state,events,executor,P1,avian};
        ctx.registry=&card_registry;
        card->onActivate(ctx,{unit});
    });
    EXPECT_EQ(state.getObject(unit).buff_count,1);
    EXPECT_GE(state.getObject(unit).current_might,5);
}
TEST_F(RadianceBatch8Test, ConservatorReadiesAfterPlayingSevenEnergyCard) {
    auto conservator=addUnit(P1,CardDefId{1019},5,0);
    state.getObject(conservator).is_exhausted=true;
    auto expensive=addToHand(P1,CardDefId{416}); // Direwing: seven Energy.
    playThroughEngine(expensive);
    EXPECT_FALSE(state.getObject(conservator).is_exhausted);
}


TEST_F(RadianceBatch8Test, RaptorDrawsWhenStunnedEnemyDiesAtSameBattlefield) {
    addUnit(P1,CardDefId{1020},6,0);
    auto enemy=addUnit(P2,kInvalidId,2,0);
    state.getObject(enemy).is_stunned=true;
    addToDeck(P1,CardDefId{1012});
    const auto before=state.player(P1).hand.size();
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(enemy);});
    EXPECT_EQ(state.player(P1).hand.size(),before+1);
}
TEST_F(RadianceBatch8Test, WardBuffsOwnUnitsThenDiesWhenUnitPlayed) {
    auto battlefieldAlly=addUnit(P1,kInvalidId,3,0);
    auto baseAlly=addUnit(P1,kInvalidId,3);
    auto enemy=addUnit(P2,kInvalidId,3,0);
    auto ward=addToHand(P1,CardDefId{1021});
    playThroughEngine(ward);
    recalc();
    EXPECT_EQ(state.getObject(battlefieldAlly).current_might,5);
    EXPECT_EQ(state.getObject(baseAlly).current_might,5);
    EXPECT_EQ(state.getObject(enemy).current_might,3);
    auto unit=addToHand(P1,CardDefId{1012});
    playThroughEngine(unit);
    EXPECT_EQ(state.getObject(ward).zone,ZoneType::Trash);
    recalc();
    EXPECT_EQ(state.getObject(battlefieldAlly).current_might,3);
}
TEST_F(RadianceBatch8Test, ExtractorCreatesGoldExhaustedWhenBattlefieldControlled) {
    addUnit(P1,kInvalidId,3,0);
    auto extractor=addToHand(P1,CardDefId{1022});
    playThroughEngine(extractor,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
    ASSERT_TRUE(state.getObject(extractor).isAtBattlefield());
    state.battlefields[0].controller=P1;
    fireTriggerThroughEngine(extractor,TriggerType::AtEndOfTurn);
    int gold=0;
    for(const auto& [id,g]:state.objects.onBoard()){
        if(!g.isGear()||g.name!="Gold"||g.controller!=P1)continue;
        ++gold;
        EXPECT_TRUE(g.is_exhausted);
        EXPECT_EQ(g.card_def_id,kGoldGearCardDefId);
    }
    EXPECT_EQ(gold,1);
}
TEST_F(RadianceBatch8Test, ProjectileDealsPrintedEnergyCostDamageOfFriendlyGear) {
    auto gear=addToHand(P1,CardDefId{1021}); // Ephemeral Ward has printed cost 4.
    playThroughEngine(gear);
    auto target=addUnit(P2,kInvalidId,8,0);
    auto spell=addToHand(P1,CardDefId{1023});
    playThroughEngine(spell);
    EXPECT_EQ(state.getObject(target).damage_marked,4);
}
TEST_F(RadianceBatch8Test, WatersWageNormalPlayMakesOneExhaustedGold) {
    auto spell=addToHand(P1,CardDefId{1024});
    playThroughEngine(spell);
    int gold=0;
    for(const auto& [id,g]:state.objects.onBoard()){
        if(!g.isGear()||g.name!="Gold"||g.controller!=P1)continue;
        ++gold; EXPECT_TRUE(g.is_exhausted);
    }
    EXPECT_EQ(gold,1);
}
TEST_F(RadianceBatch8Test, WatersWageFacedownOnOwnTurnMakesThreeReadyGold) {
    auto spell=addToHand(P1,CardDefId{1024});
    state.getObject(spell).card_counters["__played_from_facedown"]=1;
    state.getObject(spell).card_counters["__facedown_play_turn"]=state.turn.turn_number;
    resolveThroughEngine([&](EffectExecutor& ex,GameState& s){
        CardContext ctx{s,events,ex,P1,spell};
        ctx.registry=&card_registry;
        card_registry.get(CardDefId{1024})->onResolve(ctx,{});
    });
    int gold=0;
    for(const auto& [id,g]:state.objects.onBoard()){
        if(!g.isGear()||g.name!="Gold"||g.controller!=P1)continue;
        ++gold; EXPECT_FALSE(g.is_exhausted);
    }
    EXPECT_EQ(gold,3);
}


TEST_F(RadianceBatch8Test, EntrenchedBoarMayEnterReadyAtCostOfBeingUnableToMove) {
    auto boar=addToHand(P1,CardDefId{1012});
    EnginePathAgent accepts(EnginePathAgent::accepting());
    playThroughEngine(boar,&accepts);
    ASSERT_TRUE(state.getObject(boar).location.has_value());
    EXPECT_FALSE(state.getObject(boar).is_exhausted);
    EXPECT_TRUE(state.getObject(boar).cant_move_this_turn);
}
TEST_F(RadianceBatch8Test, MomentaryCompanionGetsTemporaryWhenPlayedOffTurn) {
    auto companion=addUnit(P1,CardDefId{1015},4,0);
    state.turn.phase=TurnPhase::MainPhase;
    state.turn.turn_player=P2;
    fireTriggerThroughEngine(companion,TriggerType::WhenYouPlayMe);
    EXPECT_TRUE(state.getObject(companion).hasKeyword(Keyword::Temporary));
}


TEST_F(RadianceBatch8Test, AvianExhaustAbilityResolvesViaEngineIntent) {
    auto avian=addUnit(P1,CardDefId{1018},3,0);
    auto target=addUnit(P1,kInvalidId,2,0);
    Intent activation;
    activation.type=IntentType::ActivateAbility;
    activation.player=P1;
    activation.ability_source=avian;
    activation.targets={target};
    withEngine([&](GameEngine& e){
        e.testHook_executeIntent(activation);
        settleLikeTheEngine(e);
    });
    EXPECT_TRUE(state.getObject(avian).is_exhausted);
    EXPECT_EQ(state.getObject(target).buff_count,1);
}
TEST_F(RadianceBatch8Test, RaptorDoesNotDrawFromUnstunnedEnemyDeath) {
    addUnit(P1,CardDefId{1020},6,0);
    auto enemy=addUnit(P2,kInvalidId,2,0);
    addToDeck(P1,CardDefId{1012});
    auto before=state.player(P1).hand.size();
    resolveThroughEngine([&](EffectExecutor& e,GameState&){e.killObject(enemy);});
    EXPECT_EQ(state.player(P1).hand.size(),before);
}

} // namespace riftbound::test::radiance_batch8
