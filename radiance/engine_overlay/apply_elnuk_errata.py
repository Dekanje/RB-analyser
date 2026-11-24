#!/usr/bin/env python3
"""Apply RAD-081 errata after the pinned baseline overlays.

Historical overlay source is unchanged; new candidate requires fresh native QA.
"""
from pathlib import Path

def once(text,old,new):
    if text.count(old)!=1:raise ValueError("unexpected patch anchor: "+old)
    return text.replace(old,new,1)

def apply(engine):
    path=engine/"src/cards/units/0983_additional_deck_cards.cpp"
    text=path.read_text()
    start=text.index("class ElnukHerd final")
    end=text.index("\n};",start)+3
    block=text[start:end]
    block=once(block,"otherFriends(const CardContext& ctx)","friendlyUnits(const CardContext& ctx)")
    block=once(block,"id!=ctx.source&&obj.isUnit()","obj.isUnit()")
    block=once(block,"otherFriends(ctx)","friendlyUnits(ctx)")
    block=once(block,"give another friendly unit +3 Might\",options","give a friendly unit +3 Might\",options")
    block=once(block,"give another friendly unit +3 Might this turn","give a friendly unit +3 Might this turn")
    test_path=engine/"tests/cards/test_radiance_final64.cpp"
    tests=test_path.read_text()
    marker="} // namespace riftbound::test::final64"
    new_tests=r"""
TEST_F(RadianceFinal64Test, ErrataElnukOnlyFriendlyCanTargetSelf){
 auto source=addUnit(P1,CardDefId{986},5,0);
 auto enemy=addUnit(P2,kInvalidId,4,1);
 EnginePathAgent self(EnginePathAgent::choosing(source));
 fireTriggerThroughEngine(source,TriggerType::WhenYouPlayMe,&self);
 ASSERT_TRUE(state.objectExists(source));
 EXPECT_EQ(state.getObject(source).current_might,8);
 EXPECT_EQ(state.getObject(enemy).current_might,4);
}
TEST_F(RadianceFinal64Test, ErrataElnukOffersSelfAndOtherFriendlyButNotEnemy){
 auto source=addUnit(P1,CardDefId{986},5,0);
 auto friend_unit=addUnit(P1,kInvalidId,4,-1);
 auto enemy=addUnit(P2,kInvalidId,6,1);
 EnginePathAgent chooser([&](const std::vector<Intent>& options){
   auto has=[&](GameObjectId id){
     return std::any_of(options.begin(),options.end(),[&](const Intent& i){
       return std::find(i.chosen_objects.begin(),i.chosen_objects.end(),id)!=i.chosen_objects.end();
     });
   };
   EXPECT_TRUE(has(source));
   EXPECT_TRUE(has(friend_unit));
   EXPECT_FALSE(has(enemy));
   auto it=std::find_if(options.begin(),options.end(),[&](const Intent& i){
     return std::find(i.chosen_objects.begin(),i.chosen_objects.end(),source)!=i.chosen_objects.end();
   });
   EXPECT_NE(it,options.end());
   return it==options.end()?options.front():*it;
 });
 fireTriggerThroughEngine(source,TriggerType::WhenYouPlayMe,&chooser);
 EXPECT_EQ(state.getObject(source).current_might,8);
 EXPECT_EQ(state.getObject(friend_unit).current_might,4);
 EXPECT_EQ(state.getObject(enemy).current_might,6);
}
TEST_F(RadianceFinal64Test, ErrataElnukMayStillChooseAnotherFriendly){
 auto source=addUnit(P1,CardDefId{986},5,0);
 auto friend_unit=addUnit(P1,kInvalidId,4,1);
 auto enemy=addUnit(P2,kInvalidId,6,-1);
 EnginePathAgent chooser(EnginePathAgent::choosing(friend_unit));
 fireTriggerThroughEngine(source,TriggerType::WhenYouPlayMe,&chooser);
 EXPECT_EQ(state.getObject(source).current_might,5);
 EXPECT_EQ(state.getObject(friend_unit).current_might,7);
 EXPECT_EQ(state.getObject(enemy).current_might,6);
}
"""
    tests=once(tests,marker,new_tests+"\n"+marker)
    path.write_text(text[:start]+block+text[end:])
    test_path.write_text(tests)
    print("RAD081_ERRATA_CANDIDATE_PATCH_APPLIED")

if __name__=="__main__":
    apply(Path("alpharune"))
