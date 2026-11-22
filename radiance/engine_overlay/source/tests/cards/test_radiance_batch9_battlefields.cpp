// Radiance Batch 9: eight NEW battlefield identities and their engine event paths.
#include "tests/cards/card_test_fixture.h"
#include "cards/card_helpers.h"
#include "core/events.h"
#include "engine/effect_executor.h"
#include <gtest/gtest.h>
#include <algorithm>
namespace riftbound::test::radiance_battlefields9 {
class RadianceBatch9BattlefieldsTest:public CardTestFixture {
protected:
    GameObjectId install(int index,int raw) {
        auto cid=addUnit(P1,CardDefId::fromRaw(raw),0,-1);
        auto& obj=state.getObject(cid);
        obj.card_type=CardType::Battlefield;
        obj.location.reset();
        state.battlefields[index].card_object_id=cid;
        return cid;
    }
    int countTokens(PlayerId owner,const std::string& name) {
        int n=0;
        for(const auto& [id,obj]:state.objects.onBoard())
            if(obj.isToken() && obj.controller==owner && obj.name==name)++n;
        return n;
    }
};

TEST_F(RadianceBatch9BattlefieldsTest, AllEightIdentitiesAreUniqueBattlefieldCards) {
    for(const auto& [id,n,name]:std::vector<std::tuple<int,int,const char*>>{
        {1040,157,"Bandle Scouts' Academy"},{1041,159,"Black Rose Sanctum"},
        {1042,160,"Cosmic Vista"},{1043,161,"Durand Memorial"},
        {1044,162,"Firelights' Hideout"},{1045,164,"Packed Amphitheater"},
        {1046,165,"Rakelstake"},{1047,166,"Ruined Monastery"}}){
        const auto& d=card_db.get(CardDefId::fromRaw(id));
        EXPECT_EQ(d.card_type,CardType::Battlefield);
        EXPECT_EQ(d.public_code,"RAD-"+std::to_string(n)+"/167");
        EXPECT_EQ(d.name,name);
    }
}
TEST_F(RadianceBatch9BattlefieldsTest, BandleAcademyMakesExhaustedGoldOnlyWhenHidingHere) {
    install(0,1040);
    auto card=addToHand(P1,CardDefId{1012});
    state.getObject(card).hidden_at=state.battlefields[1].id;
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CardHiddenEvent{card,P1});
    });
    EXPECT_EQ(countTokens(P1,"Gold"),0);
    state.getObject(card).hidden_at=state.battlefields[0].id;
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CardHiddenEvent{card,P1});
    });
    EXPECT_EQ(countTokens(P1,"Gold"),1);
    for(const auto& [id,obj]:state.objects.onBoard()) {
        if(obj.isGear() && obj.name=="Gold" && obj.controller==P1)
            EXPECT_TRUE(obj.is_exhausted);
    }
}
TEST_F(RadianceBatch9BattlefieldsTest, BlackRosePaysOneRecruitForFirstNontokenDeathPerPlayer) {
    install(0,1041);
    auto first=addUnit(P1,kInvalidId,3,0);
    auto second=addUnit(P1,kInvalidId,3,0);
    resolveThroughEngine([&](EffectExecutor& ex,GameState&){
        ex.killObject(first);
    });
    EXPECT_EQ(countTokens(P1,"Recruit"),1);
    resolveThroughEngine([&](EffectExecutor& ex,GameState&){
        ex.killObject(second);
    });
    EXPECT_EQ(countTokens(P1,"Recruit"),1);
    auto other=addUnit(P2,kInvalidId,3,0);
    resolveThroughEngine([&](EffectExecutor& ex,GameState&){
        ex.killObject(other);
    });
    EXPECT_EQ(countTokens(P2,"Recruit"),1);
}
TEST_F(RadianceBatch9BattlefieldsTest, CosmicVistaScoresOnHoldOnlyIfRuneDeckEmpty) {
    install(0,1042);
    state.player(P1).rune_deck.clear();
    int before=state.player(P1).score;
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(ScoreEvent{P1,state.battlefields[0].id,ScoreMethod::Hold,before+1});
    });
    EXPECT_EQ(state.player(P1).score,before+1);
}
TEST_F(RadianceBatch9BattlefieldsTest, DurandMemorialGrantsTankOnlyToChosenDefenderHere) {
    install(0,1043);
    auto defender=addUnit(P2,kInvalidId,3,0);
    auto bystander=addUnit(P2,kInvalidId,3,1);
    // The event is emitted by the real combat state machine after this flag
    // becomes active. Mirror that state in the isolated event-path test.
    state.battlefields[0].combat_in_progress=true;
    state.battlefields[0].attacker=P1;
    state.battlefields[0].defender=P2;
    EnginePathAgent agent(EnginePathAgent::choosing(defender));
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CombatStartedEvent{state.battlefields[0].id,P1,P2});
    },nullptr,&agent);
    EXPECT_TRUE(state.getObject(defender).hasKeyword(Keyword::Tank));
    EXPECT_FALSE(state.getObject(bystander).hasKeyword(Keyword::Tank));
}
TEST_F(RadianceBatch9BattlefieldsTest, FirelightsGrantsAccelerateToNextUnitOnlyThisTurn) {
    install(0,1044);
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(ScoreEvent{P1,state.battlefields[0].id,ScoreMethod::Conquer,1});
    });
    EXPECT_EQ(state.player(P1).firelights_next_accelerate_turn,
              state.turn.turn_number+1);
    auto next=addToHand(P1,CardDefId{1012});
    playThroughEngine(next);
    EXPECT_EQ(state.player(P1).firelights_next_accelerate_turn,0);
}
TEST_F(RadianceBatch9BattlefieldsTest, PackedAmphitheaterOnlyBuffsChampionUnitsHere) {
    install(0,1045);
    auto champ=addUnit(P1,CardDefId{307},5,0);
    auto other=addUnit(P1,kInvalidId,3,0);
    auto elsewhere=addUnit(P2,CardDefId{307},5,1);
    withEngine([&](GameEngine& engine){engine.testHook_recalculateAuras();});
    EXPECT_EQ(state.getObject(champ).current_might,6);
    EXPECT_EQ(state.getObject(other).current_might,3);
    EXPECT_EQ(state.getObject(elsewhere).current_might,5);
}
TEST_F(RadianceBatch9BattlefieldsTest, RakelstakeTracksFirstPermanentPlayPerPlayerAtItsBattlefield) {
    auto bfcard=install(0,1046);
    addToDeck(P1,CardDefId{1012});
    auto first=addUnit(P1,kInvalidId,2,0);
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CardPlayedEvent{first,P1,CardType::Unit,1,0});
    });
    EXPECT_EQ(state.getObject(bfcard).card_counters["__rakelstake_p1_last_play_turn"],
              state.turn.turn_number+1);
    auto second=addUnit(P1,kInvalidId,2,0);
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(CardPlayedEvent{second,P1,CardType::Unit,2,0});
    });
    EXPECT_EQ(state.getObject(bfcard).card_counters["__rakelstake_p1_last_play_turn"],
              state.turn.turn_number+1);
}
TEST_F(RadianceBatch9BattlefieldsTest, RuinedMonasteryCanDeclineDiscardOnConquer) {
    install(0,1047);
    auto hand=addToHand(P1,CardDefId{1012});
    EnginePathAgent decline([](const std::vector<Intent>& legal){
        for(const auto& c:legal)if(c.declines)return c;
        return legal.front();
    });
    auto before=state.player(P1).hand.size();
    resolveThroughEngine([&](EffectExecutor&,GameState&){
        events.emit(ScoreEvent{P1,state.battlefields[0].id,ScoreMethod::Conquer,1});
    },&decline);
    EXPECT_EQ(state.player(P1).hand.size(),before);
    EXPECT_EQ(state.getObject(hand).zone,ZoneType::Hand);
}
} // namespace riftbound::test::radiance_battlefields9
