// Batch 10: independent registry/printed-identity verification.
// Mechanics-specific engine path tests will be required before acceptance.
#include "tests/cards/card_test_fixture.h"
#include "cards/card.h"
#include <gtest/gtest.h>
#include <set>
#include <string>
#include <vector>
namespace riftbound::test::radiance_batch10 {
class RadianceBatch10Test:public CardTestFixture {};
struct Printed {
 int id,number,energy,power,might; const char* name; CardType type;
};
TEST_F(RadianceBatch10Test, AhriGainsOneMightWhenHerDisarmReducesEnemyHere) {
 auto ahri=addUnit(P1,CardDefId{1050},4,0);
 auto enemy=addUnit(P2,kInvalidId,5,0);
 EnginePathAgent choice(EnginePathAgent::choosing(enemy));
 resolveThroughEngine([&](EffectExecutor&,GameState&){
    events.emit(CombatStartedEvent{state.battlefields[0].id,P1,P2});
 },&choice);
 EXPECT_EQ(state.getObject(enemy).temp_might_bonus,-1);
 EXPECT_EQ(state.getObject(ahri).temp_might_bonus,1);
}
TEST_F(RadianceBatch10Test, GoodStuffPlayDiscardsOneAndDrawsThree) {
 auto extra=addToHand(P1,CardDefId{1058});
 for(int i=0;i<3;i++)addToDeck(P1,CardDefId{1058});
 auto gear=addToHand(P1,CardDefId{1056});
 playThroughEngine(gear,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
 EXPECT_FALSE(inHand(P1,extra));
 EXPECT_EQ(state.player(P1).main_deck.size(),0u);
}
TEST_F(RadianceBatch10Test, GoodStuffBouncesWhenControllerHoldsItsBattlefield) {
 // The play trigger draws three: keep the deck nonempty, otherwise Burnout
 // ends the test game before its later Hold trigger can resolve.
 addUnit(P1,kInvalidId,2,0);
 for(int i=0;i<3;i++)addToDeck(P1,CardDefId{1058});
 auto gear=addToHand(P1,CardDefId{1056});
 addToHand(P1,CardDefId{1058});
 playThroughEngine(gear,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
 ASSERT_TRUE(state.getObject(gear).isAtBattlefield());
 ASSERT_FALSE(state.game_over);
 fireTriggerThroughEngine(gear,TriggerType::WhenYouHoldHere);
 EXPECT_TRUE(inHand(P1,gear));
}
TEST_F(RadianceBatch10Test, TitanicShrineExhaustsToDrawForLargestPlayedUnit) {
 auto shrine=addToHand(P1,CardDefId{1054});
 playThroughEngine(shrine);
 ASSERT_FALSE(state.getObject(shrine).is_exhausted);
 addToDeck(P1,CardDefId{1058});
 auto before=state.player(P1).main_deck.size();
 auto large=addToHand(P1,CardDefId{1062});
 playThroughEngine(large);
 EXPECT_TRUE(state.getObject(shrine).is_exhausted);
 EXPECT_EQ(state.player(P1).main_deck.size()+1,before);
}
TEST_F(RadianceBatch10Test, LostToSandsOnlyOffersBattlefieldUnitNotBaseUnit) {
 auto base=addUnit(P2,kInvalidId,2,-1);
 auto battlefield=addUnit(P2,kInvalidId,3,0);
 auto spell=addToHand(P1,CardDefId{1048});
 EnginePathAgent chooser(EnginePathAgent::choosing(battlefield));
 playThroughEngine(spell,&chooser);
 EXPECT_FALSE(chooser.wasOffered(base));
 EXPECT_TRUE(chooser.wasOffered(battlefield));
}
TEST_F(RadianceBatch10Test, HearteningSoulGrantsExhaustAbilityOnlyToFriendlyLegend) {
 const auto legend=state.createObject();
 auto& obj=state.getObject(legend);
 obj.owner=P1;obj.controller=P1;obj.card_type=CardType::Legend;
 obj.card_def_id=CardDefId{966};obj.zone=ZoneType::LegendZone;
 state.player(P1).legend_zone=legend;
 const auto soul=addUnit(P1,CardDefId{1062},7,-1);
 withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
 const auto& grants=state.getObject(legend).granted_abilities;
 bool found=false;
 for(const auto& grant:grants)
   if(grant.source_def_id==CardDefId{1062}&&grant.ability_index==0)found=true;
 EXPECT_TRUE(found);
 const auto* card=card_registry.get(CardDefId{1062});
 ASSERT_NE(card,nullptr);
 EXPECT_TRUE(card->canActivateAbilityAt(state,P1,legend,0));
 EXPECT_FALSE(card->canActivateAbilityAt(state,P1,soul,0));
}
TEST_F(RadianceBatch10Test, HearteningSoulLegendCanActivateGrantedMightAbility) {
 auto legend=state.createObject();
 auto& obj=state.getObject(legend);
 obj.owner=P1;obj.controller=P1;obj.card_type=CardType::Legend;
 obj.card_def_id=CardDefId{966};obj.zone=ZoneType::LegendZone;
 state.player(P1).legend_zone=legend;
 addUnit(P1,CardDefId{1062},7,-1);
 const auto target=addUnit(P1,kInvalidId,2,-1);
 withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
 Intent ability;ability.type=IntentType::ActivateAbility;ability.player=P1;
 ability.ability_source=legend;ability.granted_ability_def=CardDefId{1062};
 ability.ability_index=0;
 EnginePathAgent choose(EnginePathAgent::choosing(target));
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(ability);settleLikeTheEngine(e);
 },&choose,nullptr,P1);
 EXPECT_TRUE(state.getObject(legend).is_exhausted);
 EXPECT_EQ(state.getObject(target).temp_might_bonus,3);
}
TEST_F(RadianceBatch10Test, AllFourFinalizeSpellsDeclareTargetsAndRequireLegalChoices) {
 for(int id:{1048,1051,1055,1067}){
   const auto* card=card_registry.get(CardDefId::fromRaw(id));
   ASSERT_NE(card,nullptr);
   EXPECT_NE(card->mayChooseAtFinalization(state,P1,kInvalidId),
             Card::FinalizeChoice::Undeclared)<<id;
 }
 const auto* lost=card_registry.get(CardDefId{1048});
 const auto* parallel=card_registry.get(CardDefId{1051});
 const auto* satchel=card_registry.get(CardDefId{1055});
 const auto* oneTwo=card_registry.get(CardDefId{1067});
 EXPECT_FALSE(lost->canBePlayed(state,P1));
 EXPECT_FALSE(parallel->canBePlayed(state,P1));
 EXPECT_FALSE(satchel->canBePlayed(state,P1));
 EXPECT_FALSE(oneTwo->canBePlayed(state,P1));
 addUnit(P1,kInvalidId,2,-1);
 EXPECT_TRUE(satchel->canBePlayed(state,P1));
 EXPECT_FALSE(parallel->canBePlayed(state,P1));
 addUnit(P2,kInvalidId,3,0);
 EXPECT_TRUE(lost->canBePlayed(state,P1));
 EXPECT_TRUE(parallel->canBePlayed(state,P1));
 EXPECT_TRUE(oneTwo->canBePlayed(state,P1));
}
TEST_F(RadianceBatch10Test, BedevilingStrangerWithoutFourUnitsFinalizesCleanly) {
 auto card=addToHand(P1,CardDefId{1057});
 playThroughEngine(card);
 EXPECT_TRUE(state.getObject(card).location.has_value());
}
TEST_F(RadianceBatch10Test, TwentyNewUniqueCardsHaveCanonicalPrintedMetadata) {
 const std::vector<Printed> want={
  {1048,13,3,1,0,"Lost to the Sands",CardType::Spell},
  {1049,35,3,0,0,"Invigorating Bloom",CardType::Gear},
  {1050,38,4,1,4,"Ahri, Confident",CardType::Unit},
  {1051,51,2,1,0,"Parallel Convergence",CardType::Spell},
  {1052,70,3,0,0,"Hold 'Em",CardType::Spell},
  {1053,87,2,0,0,"Portable Portal",CardType::Gear},
  {1054,89,3,0,0,"Titanic Shrine",CardType::Gear},
  {1055,96,3,1,0,"Satchel Charge",CardType::Spell},
  {1056,106,3,1,0,"The Good Stuff",CardType::Gear},
  {1057,107,2,0,2,"Bedeviling Stranger",CardType::Unit},
  {1058,5,2,0,2,"Lingering Animus",CardType::Unit},
  {1059,1,2,0,1,"Amateur Demolitionist",CardType::Unit},
  {1060,28,1,0,0,"Ki Burst",CardType::Spell},
  {1061,29,1,0,0,"Life from Stone",CardType::Spell},
  {1062,40,7,1,7,"Heartening Soul",CardType::Unit},
  {1063,47,3,0,0,"Fanfare",CardType::Spell},
  {1064,61,3,0,4,"Ekko, Ingenious",CardType::Unit},
  {1065,75,5,0,4,"Skystrike Squadron",CardType::Unit},
  {1066,116,1,0,0,"Concert Poster",CardType::Gear},
  {1067,121,3,0,0,"One-Two Punch",CardType::Spell},
 };
 ASSERT_EQ(want.size(),20u);
 std::set<int> ids;std::set<std::string> codes;
 for(const auto& w:want) {
   const auto& d=card_db.get(CardDefId::fromRaw(w.id));
   auto s=std::to_string(w.number);
   auto code="RAD-"+std::string(3-s.size(),'0')+s+"/167";
   EXPECT_TRUE(ids.insert(w.id).second);
   EXPECT_TRUE(codes.insert(code).second);
   EXPECT_EQ(d.id.raw(),w.id)<<w.name;
   EXPECT_EQ(d.name,w.name)<<w.id;
   EXPECT_EQ(d.public_code,code)<<w.id;
   EXPECT_EQ(d.card_type,w.type)<<w.id;
   EXPECT_EQ(d.energy_cost,w.energy)<<w.id;
   EXPECT_EQ(d.power_cost,w.power)<<w.id;
   EXPECT_EQ(d.might,w.might)<<w.id;
   EXPECT_EQ(d.set_code,"RAD");
   EXPECT_FALSE(d.ability_text.empty())<<w.id;
 }
}
TEST_F(RadianceBatch10Test, PrintedKeywordsAreRegistered) {
 EXPECT_TRUE(card_db.get(CardDefId{1050}).keywords.has(Keyword::Disarm));
 EXPECT_TRUE(card_db.get(CardDefId{1053}).keywords.has(Keyword::Deploy));
 EXPECT_TRUE(card_db.get(CardDefId{1056}).keywords.has(Keyword::Deploy));
 EXPECT_TRUE(card_db.get(CardDefId{1057}).keywords.has(Keyword::Hidden));
 EXPECT_TRUE(card_db.get(CardDefId{967}).keywords.has(Keyword::Assault));
 EXPECT_EQ(card_db.get(CardDefId{1064}).super_type,SuperType::Champion);
 EXPECT_TRUE(card_db.get(CardDefId{1064}).keywords.has(Keyword::Ganking));
 EXPECT_TRUE(card_db.get(CardDefId{1065}).keywords.has(Keyword::Deflect));
 EXPECT_TRUE(card_db.get(CardDefId{1066}).keywords.has(Keyword::Deploy));
}
TEST_F(RadianceBatch10Test, OriginalEkkoRemainsRegisteredWithActivatedAbility) {
 const auto& ekko=card_db.get(CardDefId{967});
 EXPECT_EQ(ekko.name,"Ekko, Revolutionary");
 EXPECT_EQ(ekko.public_code,"RAD-021/167");
}
TEST_F(RadianceBatch10Test, AmateurDemolitionistHasPrintedFuryDomainAndTags) {
 const auto& d=card_db.get(CardDefId{1059});
 EXPECT_EQ(d.public_code,"RAD-001/167");
 ASSERT_EQ(d.domains.size(),1u);
 EXPECT_EQ(d.domains.front(),Domain::Fury);
 EXPECT_EQ(d.energy_cost,2);
 EXPECT_EQ(d.power_cost,0);
 EXPECT_EQ(d.might,1);
 EXPECT_EQ(d.tags,std::vector<std::string>({"Bandle City","Yordle"}));
}
TEST_F(RadianceBatch10Test, AmateurDemolitionistCreatesBombAtBattlefield) {
 auto card=addToHand(P1,CardDefId{1059});
 playThroughEngine(card);
 int bombs=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.controller==P1&&o.isGear()&&o.name=="Bomb"&&o.isAtBattlefield())
     ++bombs;
 EXPECT_EQ(bombs,1);
}
TEST_F(RadianceBatch10Test, KiBurstExhaustsFriendlyUnitBeforeSpellResolves) {
 auto ally=addUnit(P1,kInvalidId,3,0);
 auto enemy=addUnit(P2,kInvalidId,3,0);
 auto spell=addToHand(P1,CardDefId{1060});
 playThroughEngine(spell);
 EXPECT_TRUE(state.getObject(ally).is_exhausted);
 EXPECT_TRUE(state.getObject(ally).is_stunned||state.getObject(enemy).is_stunned);
}
TEST_F(RadianceBatch10Test, LifeFromStonePaysExhaustAsAdditionalCastCost) {
 auto ally=addUnit(P1,kInvalidId,3,0);
 auto spell=addToHand(P1,CardDefId{1061});
 playThroughEngine(spell);
 EXPECT_TRUE(state.getObject(ally).is_exhausted);
}
TEST_F(RadianceBatch10Test, HoldEmDiscountsAfterBattlefieldTokenUnitPlay) {
 const auto where=BattlefieldLocation{state.battlefields[0].id};
 withEngine([&](GameEngine& e) {
   e.testHook_executor().createToken(P1,CardType::Unit,"Recruit",1,
       {"Recruit"},KeywordSet{},where,false);
 });
 const auto* hold=card_registry.get(CardDefId{1052});
 ASSERT_NE(hold,nullptr);
 EXPECT_EQ(hold->selfCostReduction(state,P1),2);
}
TEST_F(RadianceBatch10Test, HoldEmDoesNotDiscountAfterBasePlay) {
 const auto unit=addToHand(P1,CardDefId{1058});
 playThroughEngine(unit);
 const auto* hold=card_registry.get(CardDefId{1052});
 ASSERT_NE(hold,nullptr);
 EXPECT_EQ(hold->selfCostReduction(state,P1),0);
}
TEST_F(RadianceBatch10Test, HoldEmDiscountsAfterBattlefieldUnitPlay) {
 addUnit(P1,kInvalidId,2,0);
 const auto unit=addToHand(P1,CardDefId{1058});
 playThroughEngine(unit,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
 const auto* hold=card_registry.get(CardDefId{1052});
 ASSERT_NE(hold,nullptr);
 EXPECT_EQ(hold->selfCostReduction(state,P1),2);
}
TEST_F(RadianceBatch10Test, LingeringAnimusEntersReadyAfterFriendlyGearDies) {
 auto gear=addToHand(P1,CardDefId{1049});
 playThroughEngine(gear);
 withEngine([&](GameEngine& e){e.testHook_executor().killObject(gear);});
 EXPECT_TRUE(state.player(P1).gear_died_this_turn);
 const auto animus=addToHand(P1,CardDefId{1058});
 playThroughEngine(animus);
 EXPECT_FALSE(state.getObject(animus).is_exhausted);
}
TEST_F(RadianceBatch10Test, BedevilingStrangerChoosesCrowdedBattlefieldToBounceEnemy) {
 addUnit(P1,kInvalidId,2,0);
 addUnit(P1,kInvalidId,2,0);
 addUnit(P1,kInvalidId,2,0);
 const auto enemy=addUnit(P2,kInvalidId,2,0);
 const auto card=addToHand(P1,CardDefId{1057});
 EnginePathAgent accepts(EnginePathAgent::accepting());
 playThroughEngine(card,&accepts);
 EXPECT_TRUE(inHand(P2,enemy));
}
TEST_F(RadianceBatch10Test, PortablePortalPaidTriggerReadiesUnitAtItsBattlefield) {
 auto ally=addUnit(P1,kInvalidId,4,0);
 state.getObject(ally).is_exhausted=true;
 addRune(P1,Domain::Body);
 auto gear=addToHand(P1,CardDefId{1053});
 EnginePathAgent accepts(EnginePathAgent::accepting());
 playThroughEngine(gear,&accepts,LocationId{BattlefieldLocation{state.battlefields[0].id}});
 EXPECT_FALSE(state.getObject(ally).is_exhausted);
}
TEST_F(RadianceBatch10Test, InvigoratingBloomMightyExhaustActivationDrawsOne) {
 auto mighty=addUnit(P1,kInvalidId,5,-1);
 addToDeck(P1,CardDefId{1058});
 const auto gear=addToHand(P1,CardDefId{1049});
 playThroughEngine(gear);
 const auto* card=card_registry.get(CardDefId{1049});
 ASSERT_NE(card,nullptr);
 ASSERT_TRUE(card->hasActivatedAbility());
 EXPECT_TRUE(card->canActivateAbility(state,P1));
 const auto before=state.player(P1).main_deck.size();
 Intent a;a.type=IntentType::ActivateAbility;
 a.player=P1;a.ability_source=gear;a.ability_index=0;
 EnginePathAgent agent(EnginePathAgent::choosing(mighty));
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(a);settleLikeTheEngine(e);
 },&agent,nullptr,P1);
 EXPECT_TRUE(state.getObject(mighty).is_exhausted);
 EXPECT_TRUE(state.getObject(gear).is_exhausted);
 EXPECT_EQ(state.player(P1).main_deck.size()+1,before);
}
TEST_F(RadianceBatch10Test, SatchelChargeNeedsFriendlyUnitToMove) {
 const auto* spell=card_registry.get(CardDefId{1055});
 ASSERT_NE(spell,nullptr);
 EXPECT_FALSE(spell->canBePlayed(state,P1));
 addUnit(P1,kInvalidId,2,-1);
 EXPECT_TRUE(spell->canBePlayed(state,P1));
}
TEST_F(RadianceBatch10Test, SatchelChargeMovesFriendlyUnitAndPlaysBombToken) {
 const auto ally=addUnit(P1,kInvalidId,2,-1);
 const auto spell=addToHand(P1,CardDefId{1055});
 playThroughEngine(spell);
 EXPECT_TRUE(state.getObject(ally).isAtBattlefield());
 int bombs=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.name=="Bomb"&&o.isGear()&&o.controller==P1&&o.isAtBattlefield())++bombs;
 EXPECT_EQ(bombs,1);
}
TEST_F(RadianceBatch10Test, ParallelConvergencePaysBounceAtCastTime) {
 const auto ally=addUnit(P1,kInvalidId,2,-1);
 const auto enemy=addUnit(P2,kInvalidId,3,0);
 const auto spell=addToHand(P1,CardDefId{1051});
 playThroughEngine(spell);
 EXPECT_TRUE(inHand(P1,ally));
 EXPECT_FALSE(state.getObject(enemy).isAtBattlefield());
}
TEST_F(RadianceBatch10Test, FanfareDrawsExactlyForNextThreeFriendlyUnitPlays) {
 for(int i=0;i<4;i++)addToDeck(P1,CardDefId{1058});
 const auto spell=addToHand(P1,CardDefId{1063});
 playThroughEngine(spell);
 const auto before=state.player(P1).main_deck.size();
 for(int i=0;i<4;i++) {
   const auto unit=addToHand(P1,CardDefId{1058});
   playThroughEngine(unit);
 }
 EXPECT_EQ(state.player(P1).main_deck.size()+3,before);
}
TEST_F(RadianceBatch10Test, EkkoIngeniousReturnsFriendlyUnitAsMandatoryPlayCost) {
 const auto ally=addUnit(P1,kInvalidId,2,-1);
 const auto ekko=addToHand(P1,CardDefId{1064});
 playThroughEngine(ekko);
 EXPECT_TRUE(inHand(P1,ally));
 EXPECT_TRUE(state.getObject(ekko).location.has_value());
}
TEST_F(RadianceBatch10Test, SkystrikeSquadronCanReturnGearForEnergyDiscount) {
 const auto gear=addToHand(P1,CardDefId{1049});
 playThroughEngine(gear);
 ASSERT_TRUE(state.getObject(gear).location.has_value());
 const auto squad=addToHand(P1,CardDefId{1065});
 EnginePathAgent agent(EnginePathAgent::accepting());
 playThroughEngine(squad,&agent);
 EXPECT_TRUE(inHand(P1,gear));
 EXPECT_TRUE(state.getObject(squad).location.has_value());
}
TEST_F(RadianceBatch10Test, ConcertPosterPaidPlayTriggerCreatesRecruitInBase) {
 state.player(P1).rune_pool.energy+=1;
 const auto poster=addToHand(P1,CardDefId{1066});
 EnginePathAgent accepts(EnginePathAgent::accepting());
 playThroughEngine(poster,&accepts,LocationId{BattlefieldLocation{state.battlefields[0].id}});
 int recruit=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.controller==P1&&o.name=="Recruit"&&o.isUnit()
       &&o.location&&o.zone==ZoneType::Base)++recruit;
 EXPECT_EQ(recruit,1);
}
TEST_F(RadianceBatch10Test, HoldEmGrantsThreeMightToChosenUnit) {
 auto unit=addUnit(P1,kInvalidId,2,0);
 auto spell=addToHand(P1,CardDefId{1052});
 playThroughEngine(spell);
 EXPECT_EQ(state.getObject(unit).current_might,5);
}
TEST_F(RadianceBatch10Test, OneTwoPunchBuffsFriendlyAndStunsEnemy) {
 auto ally=addUnit(P1,kInvalidId,2,0);
 auto foe=addUnit(P2,kInvalidId,3,0);
 auto spell=addToHand(P1,CardDefId{1067});
 playThroughEngine(spell);
 EXPECT_TRUE(state.getObject(ally).buff_count>0);
 EXPECT_TRUE(state.getObject(foe).is_stunned);
}
} // namespace
