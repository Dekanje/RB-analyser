#!/usr/bin/env python3
"""Add engine-path regression fixtures after apply_elnuk_errata.py."""
from pathlib import Path
from apply_elnuk_errata import once

def apply(engine):
    p=engine/"tests/cards/test_radiance_final64.cpp"
    text=p.read_text()
    marker="} // namespace riftbound::test::final64"
    tests=r"""
// Set up a previously hidden card at a held battlefield, then exercise
// executeIntent's actual hidden-card play, chain and departure pipeline.
// This deliberately does not test the earlier Hide cost/payment decision.
TEST_F(RadianceFinal64Test, ErrataElnukHiddenSelfRecyclesToOwnersDeck){
 auto ally=addUnit(P1,kInvalidId,3,0);
 state.battlefields[0].controller=P1;
 auto source=addToHand(P1,CardDefId{986});
 auto& hand=state.player(P1).hand;
 hand.erase(std::remove(hand.begin(),hand.end(),source),hand.end());
 auto& obj=state.getObject(source);
 obj.zone=ZoneType::FacedownZone;
 obj.is_hidden=true;
 obj.hidden_at=state.battlefields[0].id;
 state.battlefields[0].facedown.push_back(source);
 auto bottom=addToHand(P1,CardDefId{1084});
 auto& h=state.player(P1).hand;
 h.erase(std::remove(h.begin(),h.end(),bottom),h.end());
 state.getObject(bottom).zone=ZoneType::MainDeck;
 state.player(P1).main_deck.push_back(bottom);
 EnginePathAgent chooser(EnginePathAgent::choosing(source));
 withEngine([&](GameEngine& e){
   Intent play;
   play.type=IntentType::PlayReaction;
   play.player=P1;
   play.card=source;
   play.play_location=LocationId{BattlefieldLocation{state.battlefields[0].id}};
   e.testHook_executeIntent(play);
   settleLikeTheEngine(e);
 },&chooser);
 ASSERT_TRUE(state.objectExists(source));
 EXPECT_EQ(state.getObject(source).zone,ZoneType::MainDeck);
 EXPECT_FALSE(state.getObject(source).location.has_value());
 ASSERT_EQ(state.player(P1).main_deck.size(),2u);
 EXPECT_EQ(state.player(P1).main_deck.front(),source);
 EXPECT_EQ(state.player(P1).main_deck.back(),bottom);
 EXPECT_TRUE(state.battlefields[0].facedown.empty());
 EXPECT_EQ(state.getObject(ally).current_might,3);
}
TEST_F(RadianceFinal64Test, ErrataElnukHiddenBuffsOtherFriendlyThenRecycles){
 auto ally=addUnit(P1,kInvalidId,3,0);
 auto enemy=addUnit(P2,kInvalidId,4,1);
 state.battlefields[0].controller=P1;
 auto source=addToHand(P1,CardDefId{986});
 auto& hand=state.player(P1).hand;
 hand.erase(std::remove(hand.begin(),hand.end(),source),hand.end());
 auto& obj=state.getObject(source);
 obj.zone=ZoneType::FacedownZone;
 obj.is_hidden=true;
 obj.hidden_at=state.battlefields[0].id;
 state.battlefields[0].facedown.push_back(source);
 EnginePathAgent chooser(EnginePathAgent::choosing(ally));
 withEngine([&](GameEngine& e){
   Intent play;
   play.type=IntentType::PlayReaction;
   play.player=P1;
   play.card=source;
   play.play_location=LocationId{BattlefieldLocation{state.battlefields[0].id}};
   e.testHook_executeIntent(play);
   settleLikeTheEngine(e);
 },&chooser);
 ASSERT_TRUE(state.objectExists(source));
 EXPECT_EQ(state.getObject(source).zone,ZoneType::MainDeck);
 ASSERT_EQ(state.player(P1).main_deck.size(),1u);
 EXPECT_EQ(state.player(P1).main_deck.front(),source);
 EXPECT_EQ(state.getObject(ally).current_might,6);
 EXPECT_EQ(state.getObject(enemy).current_might,4);
 EXPECT_TRUE(state.battlefields[0].facedown.empty());
}
TEST_F(RadianceFinal64Test, ErrataElnukQueuedTriggerAfterSourceDeathBuffsRemainingFriendly){
 auto source=addUnit(P1,CardDefId{986},5,0);
 auto ally=addUnit(P1,kInvalidId,3,1);
 auto enemy=addUnit(P2,kInvalidId,4,-1);
 EnginePathAgent chooser(EnginePathAgent::choosing(ally));
 withEngine([&](GameEngine& e){
   e.testHook_executor().queueTriggeredAbility(source,P1,TriggerType::WhenYouPlayMe,kInvalidId);
   e.testHook_executor().killObject(source);
   settleLikeTheEngine(e);
 },&chooser);
 ASSERT_TRUE(state.objectExists(source));
 EXPECT_EQ(state.getObject(source).zone,ZoneType::Trash);
 EXPECT_EQ(state.getObject(ally).current_might,6);
 EXPECT_EQ(state.getObject(enemy).current_might,4);
 EXPECT_TRUE(state.player(P1).main_deck.empty());
}
"""
    p.write_text(once(text,marker,tests+"\n"+marker))
    print("RAD081_INTERACTION_TESTS_APPLIED")

if __name__=="__main__":
    apply(Path("alpharune"))
