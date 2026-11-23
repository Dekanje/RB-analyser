// Final Radiance batch: independent printing and metadata tests.
// These alone DO NOT certify the 64 gameplay mechanics.
#include "tests/cards/card_test_fixture.h"
#include "cards/card.h"
#include <gtest/gtest.h>
#include <set>
#include <string>
#include <vector>
namespace riftbound::test::final64 {
class RadianceFinal64Test: public CardTestFixture {};
struct Printed {int id,num,energy,power,might;const char* name;CardType type;};
static const std::vector<Printed> expected={
 {1068,6,4,1,0,R"R64(Scorched Earth)R64",CardType::Spell},
 {1069,10,2,0,0,R"R64(Forbidden Technique)R64",CardType::Spell},
 {1070,11,4,0,4,R"R64(Incorrigible Construct)R64",CardType::Unit},
 {1071,12,1,0,0,R"R64(Runeblade Anvil)R64",CardType::Gear},
 {1072,15,5,1,5,R"R64(Akali, Brash)R64",CardType::Unit},
 {1073,16,4,2,4,R"R64(Coalesced Energy)R64",CardType::Unit},
 {1074,18,9,2,9,R"R64(Drakehound Packmaster)R64",CardType::Unit},
 {1075,19,6,1,6,R"R64(Firebrand Raider)R64",CardType::Unit},
 {1076,22,4,1,0,R"R64(Whirling Twirligig)R64",CardType::Gear},
 {1077,31,4,0,2,R"R64(Stoic Ferryman)R64",CardType::Unit},
 {1078,33,1,1,0,R"R64(Command: Attack)R64",CardType::Spell},
 {1079,43,4,0,4,R"R64(Riven, Broken Blade)R64",CardType::Unit},
 {1080,44,4,2,0,R"R64(Hunting Blind)R64",CardType::Gear},
 {1081,45,4,1,4,R"R64(K'Sante, Dauntless)R64",CardType::Unit},
 {1082,46,8,1,0,R"R64(Resplendent Rostrum)R64",CardType::Gear},
 {1083,53,2,0,2,R"R64(Strigian Oracle)R64",CardType::Unit},
 {1084,54,3,0,3,R"R64(Trinket Peddler)R64",CardType::Unit},
 {1085,60,8,0,8,R"R64(The Empyrean)R64",CardType::Unit},
 {1086,62,5,1,0,R"R64(Gravity Field)R64",CardType::Gear},
 {1087,63,5,1,5,R"R64(Kai'Sa, Rebel)R64",CardType::Unit},
 {1088,64,2,0,0,R"R64(Scrutinizing Scope)R64",CardType::Gear},
 {1089,66,6,1,4,R"R64(Spirit of the Forge)R64",CardType::Unit},
 {1090,67,8,2,8,R"R64(Clocktower Guardian)R64",CardType::Unit},
 {1091,68,5,0,5,R"R64(Orianna, Mechanical Marvel)R64",CardType::Unit},
 {1092,69,9,2,0,R"R64(Zero Point Inflection)R64",CardType::Gear},
 {1093,74,3,0,3,R"R64(Raving Witness)R64",CardType::Unit},
 {1094,78,6,1,4,R"R64(Armored Tusker)R64",CardType::Unit},
 {1095,80,8,2,8,R"R64(Bloodscent Swarm)R64",CardType::Unit},
 {1096,82,4,2,0,R"R64(Primordial Roar)R64",CardType::Spell},
 {1097,84,4,1,0,R"R64(Cataclysm)R64",CardType::Spell},
 {1098,85,5,1,4,R"R64(Graves, Blasting Through)R64",CardType::Unit},
 {1099,90,5,1,5,R"R64(Evelynn, Consuming)R64",CardType::Unit},
 {1100,91,4,1,4,R"R64(Jarvan IV, Martial Paragon)R64",CardType::Unit},
 {1101,92,7,0,7,R"R64(Seraphic Wyvern)R64",CardType::Unit},
 {1102,94,6,0,6,R"R64(Explosimian)R64",CardType::Unit},
 {1103,98,2,0,0,R"R64(Siren's Song)R64",CardType::Spell},
 {1104,102,3,0,0,R"R64(Demon Shade)R64",CardType::Spell},
 {1105,103,3,0,3,R"R64(Gutter Guardian)R64",CardType::Unit},
 {1106,104,5,1,5,R"R64(Pitiless Stalker)R64",CardType::Unit},
 {1107,108,1,0,0,R"R64(Bushwhack Trap)R64",CardType::Gear},
 {1108,109,4,1,4,R"R64(Evelynn, In Control)R64",CardType::Unit},
 {1109,110,3,0,3,R"R64(Lulu, Whimsical)R64",CardType::Unit},
 {1110,111,4,1,0,R"R64(Mechanical Bandit)R64",CardType::Gear},
 {1111,112,4,0,4,R"R64(Ziggs, Explosive)R64",CardType::Unit},
 {1112,113,8,0,8,R"R64(Angler Wyrm)R64",CardType::Unit},
 {1113,114,5,1,5,R"R64(Riven, Deserter)R64",CardType::Unit},
 {1114,115,6,0,4,R"R64(Transpositionist)R64",CardType::Unit},
 {1115,120,2,0,2,R"R64(Meticulous Restorationist)R64",CardType::Unit},
 {1116,123,2,1,1,R"R64(Protector's Shield)R64",CardType::Gear},
 {1117,124,3,1,0,R"R64(Burn Away)R64",CardType::Spell},
 {1118,125,7,1,7,R"R64(Dune Devourer)R64",CardType::Unit},
 {1119,127,5,0,0,R"R64(Rousing Display)R64",CardType::Spell},
 {1120,129,2,0,1,R"R64(Trifarian Captain)R64",CardType::Unit},
 {1121,130,3,0,3,R"R64(Battlefield Armorer)R64",CardType::Unit},
 {1122,131,3,1,3,R"R64(Demacian Illuminators)R64",CardType::Unit},
 {1123,132,6,1,5,R"R64(Heimerdinger, Academy Instructor)R64",CardType::Unit},
 {1124,134,7,1,0,R"R64(Raucous Anthem)R64",CardType::Spell},
 {1125,135,8,2,0,R"R64(Remember the Fallen)R64",CardType::Spell},
 {1126,136,6,2,0,R"R64(Dockside Lock-Up)R64",CardType::Gear},
 {1127,137,9,2,8,R"R64(Mordekaiser, Dominating)R64",CardType::Unit},
 {1128,138,5,1,1,R"R64(Seraphine, Not Alone)R64",CardType::Unit},
 {1129,158,0,0,0,R"R64(Black Market)R64",CardType::Battlefield},
 {1130,163,0,0,0,R"R64(Hunters' Circle)R64",CardType::Battlefield},
 {1131,167,6,1,4,R"R64(Neeko, Blending In)R64",CardType::Unit},
};
TEST_F(RadianceFinal64Test, RaucousAnthemReadiesAndStrengthensAllFriendliesOnly){
 auto a=addUnit(P1,kInvalidId,2,0);
 auto b=addUnit(P1,kInvalidId,3,-1);
 auto enemy=addUnit(P2,kInvalidId,4,0);
 state.getObject(a).is_exhausted=true;
 state.getObject(b).is_exhausted=true;
 state.getObject(enemy).is_exhausted=true;
 auto spell=addToHand(P1,CardDefId{1124});
 playThroughEngine(spell);
 EXPECT_FALSE(state.getObject(a).is_exhausted);
 EXPECT_FALSE(state.getObject(b).is_exhausted);
 EXPECT_TRUE(state.getObject(enemy).is_exhausted);
 EXPECT_EQ(state.getObject(a).temp_might_bonus,3);
 EXPECT_EQ(state.getObject(b).temp_might_bonus,3);
 EXPECT_EQ(state.getObject(enemy).temp_might_bonus,0);
}
TEST_F(RadianceFinal64Test, BurnAwayBanishesSmallEnemyAndBurnsExactlyTwo){
 auto target=addUnit(P2,kInvalidId,3,0);
 addToDeck(P1,CardDefId{1084});
 addToDeck(P1,CardDefId{1084});
 auto spell=addToHand(P1,CardDefId{1117});
 EnginePathAgent choice(EnginePathAgent::choosing(target));
 playThroughEngine(spell,&choice);
 EXPECT_EQ(state.getObject(target).zone,ZoneType::Banishment);
 EXPECT_EQ(state.player(P1).main_deck.size(),0u);
 EXPECT_EQ(state.player(P1).trash.size(),3u);
}
TEST_F(RadianceFinal64Test, DemacianIlluminatorsBuffsAfterFriendlyUnitDies){
 addUnit(P1,CardDefId{1122},3,0);
 auto ally=addUnit(P1,kInvalidId,2,0);
 auto victim=addUnit(P1,kInvalidId,1,0);
 EnginePathAgent choice(EnginePathAgent::choosing(ally));
 resolveThroughEngine([&](EffectExecutor& exec,GameState&){exec.killObject(victim);},&choice);
 EXPECT_EQ(state.getObject(ally).buff_count,1);
}
TEST_F(RadianceFinal64Test, ExplosimianHoldCreatesThreeBombsAtOneBattlefield){
 auto unit=addUnit(P1,CardDefId{1102},6,0);
 fireTriggerThroughEngine(unit,TriggerType::WhenIHold);
 int bombs=0;std::set<BattlefieldId> battlefields;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.controller==P1&&o.isGear()&&o.name=="Bomb"&&o.isAtBattlefield()){
     ++bombs;battlefields.insert(*o.battlefieldId());
   }
 EXPECT_EQ(bombs,3);
 EXPECT_EQ(battlefields.size(),1u);
}
TEST_F(RadianceFinal64Test, EvelynnScoresOnHoldOnlyWithFriendlyFacedownHere){
 state.battlefields[0].controller=P1;
 auto eve=addUnit(P1,CardDefId{1108},4,0);
 const auto facedown=addToHand(P1,CardDefId{1096});
 auto& obj=state.getObject(facedown);
 state.player(P1).hand.erase(std::remove(state.player(P1).hand.begin(),
                             state.player(P1).hand.end(),facedown),
                             state.player(P1).hand.end());
 obj.zone=ZoneType::FacedownZone;obj.is_hidden=true;
 obj.hidden_at=state.battlefields[0].id;
 state.battlefields[0].facedown.push_back(facedown);
 auto before=state.player(P1).score;
 fireTriggerThroughEngine(eve,TriggerType::WhenIHold);
 EXPECT_EQ(state.player(P1).score,before+1);
}
TEST_F(RadianceFinal64Test, PitilessStalkerExhaustsToStunEnemy){
 auto stalker=addUnit(P1,CardDefId{1106},5,0);
 auto enemy=addUnit(P2,kInvalidId,5,0);
 auto* impl=card_registry.get(CardDefId{1106});
 ASSERT_NE(impl,nullptr);
 EXPECT_TRUE(impl->canActivateAbility(state,P1));
 Intent a;a.type=IntentType::ActivateAbility;a.player=P1;a.ability_source=stalker;
 EnginePathAgent choose(EnginePathAgent::choosing(enemy));
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(a);settleLikeTheEngine(e);
 },&choose,nullptr,P1);
 EXPECT_TRUE(state.getObject(stalker).is_exhausted);
 EXPECT_TRUE(state.getObject(enemy).is_stunned);
}
TEST_F(RadianceFinal64Test, FirebrandRaiderEntersReadyAndReadiesEnemiesOnPlay){
 auto enemy=addUnit(P2,kInvalidId,2,0);
 state.getObject(enemy).is_exhausted=true;
 auto raider=addToHand(P1,CardDefId{1075});
 playThroughEngine(raider);
 EXPECT_FALSE(state.getObject(raider).is_exhausted);
 EXPECT_FALSE(state.getObject(enemy).is_exhausted);
}
TEST_F(RadianceFinal64Test, FirebrandRaiderMakesOpponentsNewUnitEnterReady){
 auto raider=addUnit(P1,CardDefId{1075},6,-1);
 ASSERT_TRUE(state.getObject(raider).location.has_value());
 withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
 auto opponentUnit=addToHand(P2,CardDefId{1120});
 playThroughEngine(opponentUnit);
 EXPECT_FALSE(state.getObject(opponentUnit).is_exhausted)
   << "RAD-019 affects opposing units, not only the controller's";
}
TEST_F(RadianceFinal64Test, FirebrandRaiderPreventsUnitAwakenEvenForOpponent){
 auto raider=addUnit(P2,CardDefId{1075},6,-1);
 auto yours=addUnit(P1,kInvalidId,3,-1);
 state.getObject(yours).is_exhausted=true;
 ASSERT_TRUE(state.getObject(raider).location.has_value());
 withEngine([&](GameEngine& e){e.testHook_awakenPhase();},nullptr,nullptr,P1);
 EXPECT_TRUE(state.getObject(yours).is_exhausted)
   << "RAD-019 stops every unit's ready in the Awaken Phase";
}
TEST_F(RadianceFinal64Test, FerrymanMovesAnotherUnitFromItsBattlefieldToBase){
 auto ally=addUnit(P1,kInvalidId,2,0);
 auto ferryman=addToHand(P1,CardDefId{1077});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(ferryman,&accept,LocationId{BattlefieldLocation{state.battlefields[0].id}});
 EXPECT_TRUE(state.getObject(ally).isAtBase());
 EXPECT_TRUE(state.getObject(ferryman).isAtBattlefield());
}
TEST_F(RadianceFinal64Test, HuntingBlindGrantsShieldToFriendsAndMovesOpponentHere){
 auto ally=addUnit(P1,kInvalidId,3,0);
 auto enemy=addUnit(P2,kInvalidId,3,-1);
 auto gear=addToHand(P1,CardDefId{1080});
 EnginePathAgent agent(EnginePathAgent::accepting());
 playThroughEngine(gear,&agent,LocationId{BattlefieldLocation{state.battlefields[0].id}});
 withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
 EXPECT_TRUE(state.getObject(enemy).isAtBattlefield());
 EXPECT_TRUE(state.getObject(ally).hasKeyword(Keyword::Shield));
}
TEST_F(RadianceFinal64Test, ForbiddenTechniqueReadiesAnyUnit){
 auto enemy=addUnit(P2,kInvalidId,4,0);
 state.getObject(enemy).is_exhausted=true;
 const auto spell=addToHand(P1,CardDefId{1069});
 EnginePathAgent chooser(EnginePathAgent::choosing(enemy));
 playThroughEngine(spell,&chooser);
 EXPECT_FALSE(state.getObject(enemy).is_exhausted);
}
TEST_F(RadianceFinal64Test, CoalescedEnergyRecyclesRunesAndChannelsThemExhausted){
 for(int i=0;i<4;i++)addRune(P1,Domain::Fury);
 auto champion=addUnit(P1,CardDefId{1073},4,-1);
 fireTriggerThroughEngine(champion,TriggerType::AtEndOfTurn);
 int exhausted=0;
 int totalRunes=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.isRune()&&o.controller==P1){
     ++totalRunes;
     if(o.is_exhausted)++exhausted;
   }
 EXPECT_EQ(exhausted,4);
 EXPECT_EQ(totalRunes,4) << "The four previous runes must have been recycled, not duplicated";
}
TEST_F(RadianceFinal64Test, CataclysmBlocksOpponentSpellsAndMovesIntoOccupiedEnemyBattlefield){
 const auto own=addUnit(P1,kInvalidId,3,-1);
 state.battlefields[1].controller=P2;
 addUnit(P2,kInvalidId,2,1);
 auto spell=addToHand(P1,CardDefId{1097});
 playThroughEngine(spell);
 EXPECT_TRUE(state.player(P2).cant_play_spells_this_turn);
 EXPECT_EQ(state.getObject(own).battlefieldId(),state.battlefields[1].id);
}
TEST_F(RadianceFinal64Test, EvelynnConsumingReadiesAndStrengthensOnFacedownPlayTrigger){
 auto eve=addUnit(P1,CardDefId{1099},5,0);
 state.getObject(eve).is_exhausted=true;
 fireTriggerThroughEngine(eve,TriggerType::WhenYouPlayFromFacedown);
 EXPECT_FALSE(state.getObject(eve).is_exhausted);
 EXPECT_EQ(state.getObject(eve).temp_might_bonus,1);
}
TEST_F(RadianceFinal64Test, StrigianOraclePredictsWhenExhausted){
 auto oracle=addUnit(P1,CardDefId{1083},2,0);
 addToDeck(P1,CardDefId{1084});
 withEngine([&](GameEngine& e){e.testHook_executor().exhaustObject(oracle);
    settleLikeTheEngine(e);});
 EXPECT_TRUE(state.getObject(oracle).is_exhausted);
 EXPECT_FALSE(state.game_over);
}

TEST_F(RadianceFinal64Test, StrigianOraclePredictRecyclesTopToBottomWithoutDuplication){
 const auto originalBottom=addToDeck(P1,CardDefId{1084});
 const auto originalTop=addToDeck(P1,CardDefId{1070});
 auto oracle=addUnit(P1,CardDefId{1083},2,0);
 EnginePathAgent recycle(EnginePathAgent::choosing(originalTop));
 withEngine([&](GameEngine& e){
   e.testHook_executor().exhaustObject(oracle);
   settleLikeTheEngine(e);
 },&recycle);
 EXPECT_TRUE(state.getObject(oracle).is_exhausted);
 const auto& deck=state.player(P1).main_deck;
 ASSERT_EQ(deck.size(),2u) << "Predict may recycle a card, not duplicate it";
 EXPECT_EQ(deck.front(),originalTop);
 EXPECT_EQ(deck.back(),originalBottom);
}
TEST_F(RadianceFinal64Test, SeraphinePlayCreatesRecruitAndExhaustedFriendsAddMight){
 auto other=addUnit(P1,kInvalidId,2,0);
 state.getObject(other).is_exhausted=true;
 auto sera=addToHand(P1,CardDefId{1128});
 playThroughEngine(sera);
 int recruits=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.controller==P1&&o.name=="Recruit"&&o.isUnit())++recruits;
 EXPECT_EQ(recruits,1);
 withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
 EXPECT_GE(state.getObject(sera).current_might,2);
}

TEST_F(RadianceFinal64Test, SeraphineExhaustionCreatesRecruitAndAuraCountsOnlyFriendlyOthers){
 auto ally=addUnit(P1,kInvalidId,2,0);
 auto enemy=addUnit(P2,kInvalidId,2,1);
 state.getObject(ally).is_exhausted=true;
 state.getObject(enemy).is_exhausted=true;
 auto sera=addToHand(P1,CardDefId{1128});
 playThroughEngine(sera);
 auto recruitCount=[&](){
   int n=0;
   for(const auto& [id,o]:state.objects.onBoard())
     if(o.controller==P1&&o.isUnit()&&o.name=="Recruit")++n;
   return n;
 };
 const int before=recruitCount();
 ASSERT_GE(before,1);
 state.getObject(sera).is_exhausted=false; // Ready as a fixture precondition.
 withEngine([&](GameEngine& e){
   e.testHook_executor().exhaustObject(sera);
   settleLikeTheEngine(e);
   e.testHook_recalculateAuras();
 });
 EXPECT_EQ(recruitCount(),before+1);
 int exhaustedOthers=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(id!=sera&&o.controller==P1&&o.isUnit()&&o.location&&o.is_exhausted)
     ++exhaustedOthers;
 EXPECT_EQ(state.getObject(sera).current_might,1+exhaustedOthers)
   << "Seraphine's Might bonus must ignore herself and enemy exhausted units";
}
TEST_F(RadianceFinal64Test, RivenDeserterGainsMightWhenAnotherFriendlyUnitExhausts){
 auto riven=addUnit(P1,CardDefId{1113},5,0);
 auto other=addUnit(P1,kInvalidId,2,0);
 withEngine([&](GameEngine& e){e.testHook_executor().exhaustObject(other);
   settleLikeTheEngine(e);});
 EXPECT_EQ(state.getObject(riven).temp_might_bonus,1);
}
TEST_F(RadianceFinal64Test, IncorrigibleConstructEntersReadyAfterShowingOffMech){
 addToHand(P1,CardDefId{1090}); // Clocktower Guardian is a Mech.
 auto construct=addToHand(P1,CardDefId{1070});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(construct,&accept);
 EXPECT_FALSE(state.getObject(construct).is_exhausted);
}

TEST_F(RadianceFinal64Test, IncorrigibleConstructEntersExhaustedWithoutFriendlyMech){
 // A non-Mech in hand and an opponent's Mech must not satisfy Show Off.
 addToHand(P1,CardDefId{1084}); // Trinket Peddler is not a Mech.
 addUnit(P2,CardDefId{1090},8,0); // Opponent's Mech is not friendly.
 auto construct=addToHand(P1,CardDefId{1070});
 playThroughEngine(construct);
 EXPECT_TRUE(state.getObject(construct).is_exhausted)
   << "Showing off is optional but requires a Mech in hand or a friendly Mech";
}
TEST_F(RadianceFinal64Test, IncorrigibleConstructAcceptsFriendlyBoardMech){
 // Showing off a friendly Mech already on the board is also legal.
 addUnit(P1,CardDefId{1090},8,0);
 auto construct=addToHand(P1,CardDefId{1070});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(construct,&accept);
 EXPECT_FALSE(state.getObject(construct).is_exhausted);
}
TEST_F(RadianceFinal64Test, TheEmpyreanShowsOffAndDrawsTwo){
 addToHand(P1,CardDefId{1090});
 for(int i=0;i<4;i++)addToDeck(P1,CardDefId{1070});
 const auto prior=state.player(P1).hand.size();
 auto dragon=addToHand(P1,CardDefId{1085});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(dragon,&accept);
 EXPECT_GE(state.player(P1).hand.size(),prior+2u);
}
TEST_F(RadianceFinal64Test, PrimordialRoarUsesShownUnitMightForDamage){
 addToHand(P1,CardDefId{1090}); // 8 Might
 auto enemy=addUnit(P2,kInvalidId,7,0);
 auto spell=addToHand(P1,CardDefId{1096});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(spell,&accept);
 EXPECT_FALSE(state.getObject(enemy).isAtBattlefield());
}
TEST_F(RadianceFinal64Test, RousingDisplayCreatesTwoRecruitsWithoutShowOff){
 auto spell=addToHand(P1,CardDefId{1119});
 playThroughEngine(spell);
 int recruits=0;
 for(const auto& [id,o]:state.objects.onBoard())
    if(o.controller==P1&&o.name=="Recruit"&&o.isUnit())++recruits;
 EXPECT_EQ(recruits,2);
}
TEST_F(RadianceFinal64Test, RousingDisplayShowsOffExpensiveCardToCreateFourRecruits){
 addToHand(P1,CardDefId{1090}); // 8-energy Mech
 auto spell=addToHand(P1,CardDefId{1119});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(spell,&accept);
 int recruits=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.controller==P1&&o.name=="Recruit"&&o.isUnit())++recruits;
 EXPECT_EQ(recruits,4);
}
TEST_F(RadianceFinal64Test, ScorchedEarthDealsExactlyFiveAllocatedDamageAtOneBattlefield){
 auto target=addUnit(P2,kInvalidId,12,0);
 auto unaffected=addUnit(P2,kInvalidId,12,1);
 auto spell=addToHand(P1,CardDefId{1068});
 // First select the battlefield (mode 0), then the only unit that may
 // receive this battlefield's damage. Other battlefields stay unaffected.
 EnginePathAgent select(EnginePathAgent::script({0,static_cast<int>(target.raw())}));
 playThroughEngine(spell,&select);
 EXPECT_EQ(state.getObject(target).damage_marked,5);
 EXPECT_EQ(state.getObject(unaffected).damage_marked,0);
}

TEST_F(RadianceFinal64Test, ScorchedEarthMayDamageFriendlyUnitAtSecondBattlefield){
 // The printed split is not enemy-only and the battlefield is selected by the player.
 auto elsewhere=addUnit(P2,kInvalidId,12,0);
 auto friendly=addUnit(P1,kInvalidId,12,1);
 auto spell=addToHand(P1,CardDefId{1068});
 EnginePathAgent select(EnginePathAgent::script({1,static_cast<int>(friendly.raw())}));
 playThroughEngine(spell,&select);
 EXPECT_EQ(state.getObject(friendly).damage_marked,5);
 EXPECT_EQ(state.getObject(elsewhere).damage_marked,0);
}
TEST_F(RadianceFinal64Test, TrinketPeddlerSharedDisarmReducesEnemyMight){
 auto peddler=addUnit(P1,CardDefId{1084},3,0);
 auto enemy=addUnit(P2,kInvalidId,5,0);
 EnginePathAgent choice(EnginePathAgent::choosing(enemy));
 resolveThroughEngine([&](EffectExecutor&,GameState&){
   events.emit(CombatStartedEvent{state.battlefields[0].id,P1,P2});
 },&choice);
 EXPECT_TRUE(state.getObject(peddler).hasKeyword(Keyword::Disarm));
 EXPECT_EQ(state.getObject(enemy).temp_might_bonus,-1);
}
TEST_F(RadianceFinal64Test, GravityFieldDeathknellDrawsOneCard){
 addToDeck(P1,CardDefId{1084});
 auto gear=addToHand(P1,CardDefId{1086});
 playThroughEngine(gear,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
 const auto deck=state.player(P1).main_deck.size();
 withEngine([&](GameEngine& e){e.testHook_executor().killObject(gear);
   settleLikeTheEngine(e);});
 EXPECT_EQ(state.player(P1).main_deck.size()+1,deck);
}
TEST_F(RadianceFinal64Test, SpiritOfForgeReturnsGearAsCostAndGainsItsEnergyAsMight){
 auto gear=addToHand(P1,CardDefId{1088});
 playThroughEngine(gear);
 auto spirit=addToHand(P1,CardDefId{1089});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(spirit,&accept);
 EXPECT_TRUE(inHand(P1,gear));
 EXPECT_FALSE(state.getObject(spirit).is_exhausted);
 EXPECT_EQ(state.getObject(spirit).temp_might_bonus,2);
}
TEST_F(RadianceFinal64Test, ZeroPointInflectionDrawsTwoAfterPlayingAnotherCard){
 for(int i=0;i<3;i++)addToDeck(P1,CardDefId{1084});
 auto inflection=addToHand(P1,CardDefId{1092});
 playThroughEngine(inflection);
 auto unit=addToHand(P1,CardDefId{1084});
 playThroughEngine(unit);
 EXPECT_EQ(state.player(P1).main_deck.size(),1u);
}
TEST_F(RadianceFinal64Test, ArmoredTuskerOptionalMoveTriggerDealsShieldDamage){
 auto tusker=addUnit(P1,CardDefId{1094},4,-1);
 auto enemy=addUnit(P2,kInvalidId,12,1);
 // An unconditional accepting agent chooses the FIRST eligible unit
 // (the Tusker itself), not necessarily the intended opponent.
 // Explicitly say Yes to the optional trigger, then choose the enemy.
 EnginePathAgent accept(EnginePathAgent::script({1,static_cast<int>(enemy.raw())}));
 resolveThroughEngine([&](EffectExecutor& exec,GameState&){
   exec.moveToBattlefield(tusker,state.battlefields[1].id);
 },&accept);
 EXPECT_EQ(state.getObject(enemy).damage_marked,3);
}
TEST_F(RadianceFinal64Test, BloodscentSwarmDiscountCountsConquestsNotHolds){
 const auto* card=card_registry.get(CardDefId{1095});
 ASSERT_NE(card,nullptr);
 EXPECT_EQ(card->selfCostReduction(state,P1),0);
 state.player(P1).battlefields_scored_this_turn.insert(state.battlefields[0].id);
 EXPECT_EQ(card->selfCostReduction(state,P1),0);
 state.player(P1).battlefields_conquered_this_turn.insert(state.battlefields[0].id);
 EXPECT_EQ(card->selfCostReduction(state,P1),2);
}
TEST_F(RadianceFinal64Test, GravesDealDamageOnAttackTriggerButNoCombatDamage){
 auto graves=addUnit(P1,CardDefId{1098},5,0);
 auto enemy=addUnit(P2,kInvalidId,12,0);
 withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
 EXPECT_TRUE(state.getObject(graves).dealsNoCombatDamage());
 fireTriggerThroughEngine(graves,TriggerType::WhenIAttackOrDefend);
 EXPECT_EQ(state.getObject(enemy).damage_marked,5);
}
TEST_F(RadianceFinal64Test, SirensSongMovesOnlyEnemyUnitThatMovedThisTurn){
 auto enemy=addUnit(P2,kInvalidId,5,0);
 state.getObject(enemy).moves_this_turn=1;
 auto spell=addToHand(P1,CardDefId{1103});
 playThroughEngine(spell);
 EXPECT_TRUE(state.getObject(enemy).isAtBase());
}
TEST_F(RadianceFinal64Test, DemonShadeMovesFriendlyUnitToOpenBattlefield){
 auto friendUnit=addUnit(P1,kInvalidId,2,-1);
 auto shade=addToHand(P1,CardDefId{1104});
 playThroughEngine(shade);
 EXPECT_TRUE(state.getObject(friendUnit).isAtBattlefield());
}
TEST_F(RadianceFinal64Test, LuluCanChangeAnotherUnitsBaseMightAfterMove){
 auto lulu=addUnit(P1,CardDefId{1109},2,-1);
 auto other=addUnit(P1,kInvalidId,6,1);
 EnginePathAgent accept(EnginePathAgent::accepting());
 resolveThroughEngine([&](EffectExecutor& exec,GameState&){
   exec.moveToBattlefield(lulu,state.battlefields[0].id);
 },&accept);
 EXPECT_EQ(state.getObject(other).base_might_this_turn,4);
}
TEST_F(RadianceFinal64Test, ZiggsActivatedAbilityExhaustsAndPlaysBomb){
 auto ziggs=addUnit(P1,CardDefId{1111},4,0);
 state.player(P1).rune_pool.energy=1;
 Intent act;act.type=IntentType::ActivateAbility;act.player=P1;act.ability_source=ziggs;
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(act);settleLikeTheEngine(e);
 },nullptr,nullptr,P1);
 int bombs=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.name=="Bomb"&&o.isGear()&&o.controller==P1)++bombs;
 EXPECT_TRUE(state.getObject(ziggs).is_exhausted);
 EXPECT_EQ(bombs,1);
}
TEST_F(RadianceFinal64Test, ZiggsDefendCanKillFriendlyGearForTwoMight){
 auto gear=addToHand(P1,CardDefId{1088});
 playThroughEngine(gear);
 auto ziggs=addUnit(P1,CardDefId{1111},4,0);
 EnginePathAgent accept(EnginePathAgent::accepting());
 fireTriggerThroughEngine(ziggs,TriggerType::WhenIDefend,&accept);
 EXPECT_FALSE(state.getObject(gear).location.has_value());
 EXPECT_EQ(state.getObject(ziggs).temp_might_bonus,2);
}
TEST_F(RadianceFinal64Test, AnglerWyrmAbilityLetsOpponentSelectUnitToMove){
 auto angler=addUnit(P1,CardDefId{1112},8,0);
 auto enemy=addUnit(P2,kInvalidId,2,-1);
 EnginePathAgent chooser(EnginePathAgent::choosing(enemy));
 Intent act;act.type=IntentType::ActivateAbility;act.player=P1;act.ability_source=angler;
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(act);settleLikeTheEngine(e);
 },nullptr,&chooser,P1);
 EXPECT_TRUE(state.getObject(angler).is_exhausted);
 EXPECT_EQ(state.getObject(enemy).battlefieldId(),state.battlefields[0].id);
}
TEST_F(RadianceFinal64Test, RivenDeserterActivationCanOnlyBeUsedOncePerTurn){
 auto riven=addUnit(P1,CardDefId{1113},5,0);
 addUnit(P1,kInvalidId,2,0);
 auto* card=card_registry.get(CardDefId{1113});
 ASSERT_NE(card,nullptr);
 ASSERT_TRUE(card->canActivateAbilityAt(state,P1,riven,0));
 Intent act;act.type=IntentType::ActivateAbility;act.player=P1;act.ability_source=riven;
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(act);settleLikeTheEngine(e);
 },nullptr,nullptr,P1);
 EXPECT_FALSE(card->canActivateAbilityAt(state,P1,riven,0));
}
TEST_F(RadianceFinal64Test, TranspositionistReturnsUnitAndPlaysLowerMightUnitFree){
 auto target=addUnit(P1,kInvalidId,6,-1);
 auto replacement=addToHand(P1,CardDefId{1084});
 auto caster=addUnit(P1,CardDefId{1114},3,-1);
 addRune(P1,Domain::Chaos);
 Intent act;act.type=IntentType::ActivateAbility;act.player=P1;act.ability_source=caster;
 EnginePathAgent accept(EnginePathAgent::accepting());
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(act);settleLikeTheEngine(e);
 },&accept,nullptr,P1);
 EXPECT_TRUE(inHand(P1,target));
 EXPECT_TRUE(state.getObject(replacement).location.has_value());
}
TEST_F(RadianceFinal64Test, SeraphicWyvernAddsOneExhaustedRuneToReadyChannel){
 addUnit(P1,CardDefId{1101},8,0);
 for(int i=0;i<3;i++){
   auto rune=addRune(P1,Domain::Order);
   auto& obj=state.getObject(rune);
   obj.zone=ZoneType::RuneDeck;
   obj.location=std::nullopt;
   state.player(P1).rune_deck.push_back(rune);
 }
 withEngine([&](GameEngine& e){
   e.testHook_executor().channelRunes(P1,1,false);
 });
 int ready=0,exhausted=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.isRune()&&o.controller==P1)
     (o.is_exhausted?exhausted:ready)++;
 EXPECT_EQ(ready,1);
 EXPECT_EQ(exhausted,1);
 EXPECT_EQ(state.player(P1).rune_deck.size(),1u);
}
TEST_F(RadianceFinal64Test, DocksideLockUpBanishesNontokenUnitAndReplaysOnHold){
 auto target=addUnit(P2,CardDefId{1120},2,0);
 auto lock=addToHand(P1,CardDefId{1126});
 auto& hand=state.player(P1).hand;
 hand.erase(std::remove(hand.begin(),hand.end(),lock),hand.end());
 state.getObject(lock).zone=ZoneType::BattlefieldZone;
 state.getObject(lock).location=BattlefieldLocation{state.battlefields[0].id};
 EnginePathAgent choose(EnginePathAgent::choosing(target));
 fireTriggerThroughEngine(lock,TriggerType::WhenYouPlayThis,&choose);
 EXPECT_EQ(state.getObject(target).zone,ZoneType::Banishment);
 EXPECT_EQ(state.getObject(lock).card_counters.at("__dockside_banished_card"),
           static_cast<int>(target.raw()));
 fireTriggerThroughEngine(lock,TriggerType::WhenYouHoldHere);
 EXPECT_FALSE(state.getObject(lock).location.has_value());
 EXPECT_TRUE(state.getObject(target).location.has_value());
}
TEST_F(RadianceFinal64Test, MordekaiserDiscardsOneToKillTargetOnAttackTrigger){
 auto victim=addUnit(P2,kInvalidId,2,0);
 auto morde=addUnit(P1,CardDefId{1127},8,0);
 auto discarded=addToHand(P1,CardDefId{1117});
 const auto* card=card_registry.get(CardDefId{1127});
 ASSERT_NE(card,nullptr);
 EXPECT_TRUE(card->firesOn(TriggerType::WhenIAttack));
 EXPECT_TRUE(card->firesOn(TriggerType::WhenYouPlayMe));
 EnginePathAgent choices(EnginePathAgent::script({1,static_cast<int>(victim.raw()),
                                                static_cast<int>(discarded.raw())}));
 fireTriggerThroughEngine(morde,TriggerType::WhenIAttack,&choices);
 EXPECT_FALSE(state.getObject(victim).location.has_value());
 EXPECT_FALSE(inHand(P1,discarded));
}

TEST_F(RadianceFinal64Test, MordekaiserPlayTriggerCanDiscardOneToKillAnEnemyUnit){
 auto target=addUnit(P2,kInvalidId,3,0);
 auto discard=addToHand(P1,CardDefId{1117});
 auto mordekaiser=addToHand(P1,CardDefId{1127});
 EnginePathAgent pay(EnginePathAgent::script({1,static_cast<int>(target.raw()),
                                           static_cast<int>(discard.raw())}));
 playThroughEngine(mordekaiser,&pay);
 EXPECT_FALSE(state.getObject(target).location.has_value());
 EXPECT_FALSE(inHand(P1,discard));
}
TEST_F(RadianceFinal64Test, MordekaiserCannotKillWithoutPayingDiscard){
 auto target=addUnit(P2,kInvalidId,3,0);
 auto mordekaiser=addUnit(P1,CardDefId{1127},8,0);
 ASSERT_TRUE(state.player(P1).hand.empty());
 fireTriggerThroughEngine(mordekaiser,TriggerType::WhenIAttack);
 EXPECT_TRUE(state.getObject(target).location.has_value());
}
TEST_F(RadianceFinal64Test, RememberTheFallenPlaysEligibleTrashCardsButNotExpensiveUnits){
 auto gear=addToHand(P1,CardDefId{1116});
 auto unit=addToHand(P1,CardDefId{1120});
 auto expensive=addToHand(P1,CardDefId{1118});
 for(auto id:{gear,unit,expensive}){
   auto& hand=state.player(P1).hand;
   hand.erase(std::remove(hand.begin(),hand.end(),id),hand.end());
   state.getObject(id).zone=ZoneType::Trash;
   state.getObject(id).location=std::nullopt;
   state.player(P1).trash.push_back(id);
 }
 auto spell=addToHand(P1,CardDefId{1125});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(spell,&accept);
 EXPECT_TRUE(state.getObject(gear).location.has_value());
 EXPECT_TRUE(state.getObject(unit).location.has_value());
 EXPECT_EQ(state.getObject(expensive).zone,ZoneType::Trash);
 EXPECT_FALSE(state.getObject(expensive).location.has_value());
}

TEST_F(RadianceFinal64Test, RememberTheFallenPlaysNoMoreThanThreeCheapTrashCards){
 std::vector<GameObjectId> cheap;
 for(int i=0;i<4;++i){
   auto id=addToHand(P1,CardDefId{i%2==0?1084:1083});
   auto& hand=state.player(P1).hand;
   hand.erase(std::remove(hand.begin(),hand.end(),id),hand.end());
   state.getObject(id).zone=ZoneType::Trash;
   state.getObject(id).location=std::nullopt;
   state.player(P1).trash.push_back(id);
   cheap.push_back(id);
 }
 auto spell=addToHand(P1,CardDefId{1125});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(spell,&accept);
 int returned=0,remaining=0;
 for(auto id:cheap){
   if(state.getObject(id).location.has_value())++returned;
   if(state.getObject(id).zone==ZoneType::Trash)++remaining;
 }
 EXPECT_EQ(returned,3);
 EXPECT_EQ(remaining,1);
}
TEST_F(RadianceFinal64Test, CommandAttackLooksAtTopFiveAndDrawsOnlyRevealedGear){
 auto eligible=addToDeck(P1,CardDefId{1116});
 addToDeck(P1,CardDefId{1117});
 addToDeck(P1,CardDefId{1118});
 addToDeck(P1,CardDefId{1125});
 auto spell=addToHand(P1,CardDefId{1078});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(spell,&accept);
 EXPECT_TRUE(inHand(P1,eligible));
 EXPECT_EQ(state.player(P1).main_deck.size(),3u);
}

TEST_F(RadianceFinal64Test, CommandAttackMovesFriendlyDeployGearToAnotherBattlefield){
 auto gear=addToHand(P1,CardDefId{1080}); // Hunting Blind is friendly Deploy gear.
 playThroughEngine(gear,nullptr,LocationId{BattlefieldLocation{state.battlefields[0].id}});
 ASSERT_EQ(state.getObject(gear).battlefieldId(),state.battlefields[0].id);
 auto spell=addToHand(P1,CardDefId{1078});
 EnginePathAgent select(EnginePathAgent::script({0,static_cast<int>(gear.raw()),0}));
 playThroughEngine(spell,&select);
 EXPECT_EQ(state.getObject(gear).battlefieldId(),state.battlefields[1].id)
   << "Command: Attack's first mode must move the chosen friendly Deploy gear";
}
TEST_F(RadianceFinal64Test, WhirlingTwirligigExhaustsToPlayAnExhaustedGold){
 auto source=addToHand(P1,CardDefId{1076});
 playThroughEngine(source);
 Intent act;act.type=IntentType::ActivateAbility;act.player=P1;
 act.ability_source=source;act.ability_index=0;
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(act);settleLikeTheEngine(e);
 },nullptr,nullptr,P1);
 EXPECT_TRUE(state.getObject(source).is_exhausted);
 int gold=0;
 for(const auto& [id,o]:state.objects.onBoard()){
   if(o.controller==P1&&o.card_def_id==CardDefId{326}&&o.isGear()){
     ++gold;EXPECT_TRUE(o.is_exhausted);
   }
 }
 EXPECT_EQ(gold,1);
}
TEST_F(RadianceFinal64Test, RavingWitnessRecyclingTopCardDoesNotDuplicateDeckObject){
 auto revealed=addToDeck(P1,CardDefId{1116}); // Gear, not a Mighty unit
 auto witness=addUnit(P1,CardDefId{1093},3,0);
 fireTriggerThroughEngine(witness,TriggerType::WhenIMove);
 const auto& deck=state.player(P1).main_deck;
 EXPECT_EQ(std::count(deck.begin(),deck.end(),revealed),1);
 EXPECT_TRUE(std::find(state.player(P1).hand.begin(),
                       state.player(P1).hand.end(),revealed)==state.player(P1).hand.end());
 EXPECT_EQ(state.getObject(revealed).zone,ZoneType::MainDeck);
}
TEST_F(RadianceFinal64Test, MechanicalBanditRecycleAndDrawLeaveUniqueDeckMembership){
 auto high=addToDeck(P1,CardDefId{1118}); // Dune Devourer, Energy 7
 auto low=addToDeck(P2,CardDefId{1116}); // Protector's Shield, Energy 1
 auto bandit=addToHand(P1,CardDefId{1110});
 playThroughEngine(bandit);
 fireTriggerThroughEngine(bandit,TriggerType::AtStartOfBeginning);
 const auto& deck1=state.player(P1).main_deck;
 const auto& deck2=state.player(P2).main_deck;
 EXPECT_EQ(std::count(deck1.begin(),deck1.end(),high),1);
 EXPECT_EQ(std::count(deck2.begin(),deck2.end(),low),0);
 EXPECT_TRUE(inHand(P2,low));
 EXPECT_EQ(state.getObject(high).zone,ZoneType::MainDeck);
 EXPECT_EQ(state.getObject(low).zone,ZoneType::Hand);
}
TEST_F(RadianceFinal64Test, WhirlingTwirligigPaysFriendlyGearDeathToCreateRecruit){
 auto gear=addToHand(P1,CardDefId{1088});
 playThroughEngine(gear);
 auto source=addToHand(P1,CardDefId{1076});
 playThroughEngine(source);
 Intent act;act.type=IntentType::ActivateAbility;act.player=P1;
 act.ability_source=source;act.ability_index=1;
 EnginePathAgent choose(EnginePathAgent::choosing(gear));
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(act);settleLikeTheEngine(e);
 },&choose,nullptr,P1);
 EXPECT_FALSE(state.getObject(gear).location.has_value());
 EXPECT_TRUE(state.getObject(source).is_exhausted);
 int recruits=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.controller==P1&&o.isUnit()&&o.name=="Recruit")++recruits;
 EXPECT_EQ(recruits,1);
}
TEST_F(RadianceFinal64Test, WhirlingTwirligigSacrificeOnlyTargetsFriendlyUnit){
 auto friendly=addUnit(P1,kInvalidId,2,-1);
 auto enemy=addUnit(P2,kInvalidId,2,-1);
 auto source=addToHand(P1,CardDefId{1076});
 playThroughEngine(source);
 const auto* card=card_registry.get(CardDefId{1076});
 ASSERT_NE(card,nullptr);
 const auto& abilities=card->abilities();
 ASSERT_EQ(abilities.size(),3u);
 EXPECT_FALSE(abilities[2].cost.kill_friendly_unit)
   << "A unit killed as cost is chosen at finalization, not targeted";
 EXPECT_EQ(abilities[2].targets.count,0);
 Intent act;act.type=IntentType::ActivateAbility;act.player=P1;
 act.ability_source=source;act.ability_index=2;
 EnginePathAgent choose(EnginePathAgent::choosing(friendly));
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(act);settleLikeTheEngine(e);
 },&choose,nullptr,P1);
 EXPECT_FALSE(choose.wasOffered(enemy));
 EXPECT_FALSE(state.getObject(friendly).location.has_value());
 EXPECT_TRUE(state.getObject(enemy).location.has_value());
}
TEST_F(RadianceFinal64Test, WhirlingTwirligigSacrificesUnitAsCostToCreateMech){
 auto sacrifice=addUnit(P1,kInvalidId,2,-1);
 auto source=addToHand(P1,CardDefId{1076});
 playThroughEngine(source);
 Intent act;act.type=IntentType::ActivateAbility;act.player=P1;
 act.ability_source=source;act.ability_index=2;
 // Sole friendly unit is chosen as a cost at activation finalization.
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(act);settleLikeTheEngine(e);
 },nullptr,nullptr,P1);
 EXPECT_TRUE(state.getObject(source).is_exhausted);
 EXPECT_FALSE(state.getObject(sacrifice).location.has_value());
 int mechs=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.controller==P1&&o.name=="Mech"&&o.isUnit()&&o.current_might==3)++mechs;
 EXPECT_EQ(mechs,1);
}
TEST_F(RadianceFinal64Test, WhirlingTwirligigUnitSacrificePreventedBySorakaCreatesNoMech){
 auto soraka=addUnit(P1,CardDefId{550},4,0);
 auto saved=addUnit(P1,kInvalidId,2,0);
 auto source=addToHand(P1,CardDefId{1076});
 playThroughEngine(source);
 Intent act;act.type=IntentType::ActivateAbility;act.player=P1;
 act.ability_source=source;act.ability_index=2;
 EnginePathAgent choose(EnginePathAgent::choosing(saved));
 withEngineDefaultTurn([&](GameEngine& e){
   e.testHook_executeIntent(act);settleLikeTheEngine(e);
 },&choose,nullptr,P1);
 EXPECT_TRUE(state.getObject(source).is_exhausted);
 EXPECT_TRUE(state.getObject(saved).isAtBase());
 EXPECT_TRUE(state.getObject(saved).is_exhausted);
 EXPECT_TRUE(state.getObject(soraka).location.has_value());
 int mechs=0;
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.controller==P1&&o.isUnit()&&o.name=="Mech")++mechs;
 EXPECT_EQ(mechs,0) << "Prevented kill-as-cost cannot create a free Mech";
}
TEST_F(RadianceFinal64Test, RivenBrokenBladeBuffAndStunAreDistinctModesThisTurn){
 auto riven=addUnit(P1,CardDefId{1079},4,0);
 auto enemy=addUnit(P2,kInvalidId,4,0);
 EnginePathAgent buffMode(EnginePathAgent::script({0}));
 fireTriggerThroughEngine(riven,TriggerType::WhenIBecomeExhausted,&buffMode);
 EXPECT_EQ(state.getObject(riven).buff_count,1);
 EXPECT_EQ(state.getObject(riven).card_counters.at("__riven43_mask"),1);
 EnginePathAgent stunMode(EnginePathAgent::script({1,static_cast<int>(enemy.raw())}));
 fireTriggerThroughEngine(riven,TriggerType::WhenIBecomeExhausted,&stunMode);
 EXPECT_TRUE(state.getObject(enemy).is_stunned);
 EXPECT_EQ(state.getObject(riven).buff_count,0);
 EXPECT_EQ(state.getObject(riven).card_counters.at("__riven43_mask"),3);
}
TEST_F(RadianceFinal64Test, RivenBrokenBladeSpendsBuffToReadyWhenExhausted){
 auto riven=addUnit(P1,CardDefId{1079},4,0);
 state.getObject(riven).buff_count=1;
 state.getObject(riven).is_exhausted=true;
 EnginePathAgent readyMode(EnginePathAgent::script({2}));
 fireTriggerThroughEngine(riven,TriggerType::WhenIBecomeExhausted,&readyMode);
 EXPECT_FALSE(state.getObject(riven).is_exhausted);
 EXPECT_EQ(state.getObject(riven).buff_count,0);
 EXPECT_EQ(state.getObject(riven).card_counters.at("__riven43_mask"),4);
}

TEST_F(RadianceFinal64Test, RivenBrokenBladeUnusedModesResetAtStartOfNextTurn){
 auto riven=addUnit(P1,CardDefId{1079},4,0);
 auto enemy=addUnit(P2,kInvalidId,4,0);
 EnginePathAgent buff(EnginePathAgent::script({0}));
 fireTriggerThroughEngine(riven,TriggerType::WhenIBecomeExhausted,&buff);
 EnginePathAgent stun(EnginePathAgent::script({1,static_cast<int>(enemy.raw())}));
 fireTriggerThroughEngine(riven,TriggerType::WhenIBecomeExhausted,&stun);
 ASSERT_EQ(state.getObject(riven).card_counters.at("__riven43_mask"),3);
 ASSERT_EQ(state.getObject(riven).buff_count,0);
 ++state.turn.turn_number;
 EnginePathAgent again(EnginePathAgent::script({0}));
 fireTriggerThroughEngine(riven,TriggerType::WhenIBecomeExhausted,&again);
 EXPECT_EQ(state.getObject(riven).card_counters.at("__riven43_mask"),1);
 EXPECT_EQ(state.getObject(riven).buff_count,1);
}
TEST_F(RadianceFinal64Test, TrifarianCaptainRevealsAndDrawsOnlyEligibleFromTopFour){
 const auto cheapGear=addToDeck(P1,CardDefId{1116});
 const auto expensiveUnit=addToDeck(P1,CardDefId{1118});
 const auto spell=addToDeck(P1,CardDefId{1117});
 const auto expensiveSpell=addToDeck(P1,CardDefId{1125});
 auto captain=addToHand(P1,CardDefId{1120});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(captain,&accept);
 EXPECT_TRUE(inHand(P1,cheapGear));
 EXPECT_FALSE(inHand(P1,expensiveUnit));
 EXPECT_FALSE(inHand(P1,spell));
 EXPECT_FALSE(inHand(P1,expensiveSpell));
 EXPECT_EQ(state.player(P1).main_deck.size(),3u);
}

TEST_F(RadianceFinal64Test, TrifarianCaptainDrawsNothingWhenTopFourContainNoEligibleCard){
 auto expensiveUnit=addToDeck(P1,CardDefId{1118});
 auto expensiveSpell=addToDeck(P1,CardDefId{1125});
 auto captain=addToHand(P1,CardDefId{1120});
 EnginePathAgent accept(EnginePathAgent::accepting());
 playThroughEngine(captain,&accept);
 EXPECT_FALSE(inHand(P1,expensiveUnit));
 EXPECT_FALSE(inHand(P1,expensiveSpell));
 ASSERT_EQ(state.player(P1).main_deck.size(),2u);
 const auto& deck=state.player(P1).main_deck;
 EXPECT_NE(std::find(deck.begin(),deck.end(),expensiveUnit),deck.end());
 EXPECT_NE(std::find(deck.begin(),deck.end(),expensiveSpell),deck.end());
}
TEST_F(RadianceFinal64Test, DuneDevourerCanPayPrintedCostWithoutSacrificing){
 auto devourer=addToHand(P1,CardDefId{1118});
 state.player(P1).rune_pool.energy=7;
 state.player(P1).rune_pool.universal_power=1;
 playThroughEngine(devourer,nullptr,std::nullopt,nullptr,false);
 EXPECT_TRUE(state.getObject(devourer).location.has_value());
 EXPECT_EQ(state.getObject(devourer).zone,ZoneType::Base);
 EXPECT_EQ(state.player(P1).rune_pool.energy,0);
}
TEST_F(RadianceFinal64Test, ProtectorsShieldEquipInactiveWhileAttachedButWorksWhenDetached){
 auto first=addUnit(P1,kInvalidId,2,-1);
 auto second=addUnit(P1,kInvalidId,3,-1);
 auto gear=addToHand(P1,CardDefId{1116});
 playThroughEngine(gear);
 ASSERT_EQ(state.getObject(gear).attached_to,std::optional<GameObjectId>{first});
 state.player(P1).rune_pool.energy+=1;
 // CR 718.2 / 721.2: attached Equipment's own Equip is inactive.
 EXPECT_FALSE(equipThroughEngine(gear,second));
 EXPECT_EQ(state.getObject(gear).attached_to,std::optional<GameObjectId>{first});
 // A detached copy may activate its Equip again, paying the printed [1].
 withEngine([&](GameEngine& engine){engine.testHook_executor().unattachGear(gear);});
 ASSERT_FALSE(state.getObject(gear).attached_to.has_value());
 EXPECT_TRUE(equipThroughEngine(gear,second));
 EXPECT_EQ(state.getObject(gear).attached_to,std::optional<GameObjectId>{second});
}
TEST_F(RadianceFinal64Test, KSanteDauntlessDoublesFriendlyShieldAtItsBattlefield){
 auto ksante=addUnit(P1,CardDefId{1081},4,0);
 ASSERT_EQ(state.getObject(ksante).shield_value,1);
 fireTriggerThroughEngine(ksante,TriggerType::WhenIAttackOrDefend);
 EXPECT_EQ(state.getObject(ksante).shield_value,2);
 EXPECT_EQ(state.getObject(ksante).temp_shield_value,1);
}
TEST_F(RadianceFinal64Test, ProtectorsShieldQuickDrawAttachesAndGivesMight){
 auto unit=addUnit(P1,kInvalidId,3,-1);
 auto shield=addToHand(P1,CardDefId{1116});
 playThroughEngine(shield);
 ASSERT_TRUE(state.getObject(shield).attached_to.has_value());
 EXPECT_EQ(*state.getObject(shield).attached_to,unit);
 EXPECT_EQ(state.getObject(shield).might_bonus,1);
}
TEST_F(RadianceFinal64Test, ProtectorsShieldEquipCostsOneEnergyNoPower){
 const auto* card=card_registry.get(CardDefId{1116});
 ASSERT_NE(card,nullptr);
 EXPECT_TRUE(card->hasEquipAbility());
 const auto cost=card->equipCost(state,P1,kInvalidId,kInvalidId);
 EXPECT_TRUE(cost.valid);
 EXPECT_EQ(cost.energy,1);
 EXPECT_EQ(cost.power,0);
 const auto& def=card_db.get(CardDefId{1116});
 EXPECT_TRUE(def.keywords.has(Keyword::QuickDraw));
 EXPECT_TRUE(def.keywords.has(Keyword::Reaction));
 EXPECT_TRUE(def.keywords.has(Keyword::Equip));
 EXPECT_TRUE(std::find(def.tags.begin(),def.tags.end(),"Equipment")!=def.tags.end());
 EXPECT_EQ(def.might_bonus,1);
}
TEST_F(RadianceFinal64Test, DuneDevourerKillsFriendlyUnitAsAdditionalPlayCostForEnergyDiscount){
 auto sacrifice=addUnit(P1,kInvalidId,3,-1);
 addUnit(P1,kInvalidId,2,-1);
 auto devourer=addToHand(P1,CardDefId{1118});
 state.player(P1).rune_pool.energy=5; // Printed 7; sacrifice discounts by 2
 state.player(P1).rune_pool.universal_power=1;
 EnginePathAgent yes(EnginePathAgent::accepting());
 playThroughEngine(devourer,&yes,std::nullopt,nullptr,false);
 EXPECT_TRUE(state.getObject(devourer).location.has_value());
 EXPECT_EQ(state.getObject(devourer).zone,ZoneType::Base);
 EXPECT_FALSE(state.getObject(sacrifice).location.has_value());
 EXPECT_EQ(state.player(P1).rune_pool.energy,0);
}
TEST_F(RadianceFinal64Test, DuneDevourerDoesNotDiscountPreventedSacrifice){
 auto soraka=addUnit(P1,CardDefId{550},4,0);
 auto protectedUnit=addUnit(P1,kInvalidId,2,0);
 auto devourer=addToHand(P1,CardDefId{1118});
 state.player(P1).rune_pool.energy=7;
 state.player(P1).rune_pool.universal_power=1;
 // Soraka replaces the friendly unit's death with heal, exhaust and
 // recall. "Kill as additional cost" did not happen: cost remains 7.
 EnginePathAgent yes(EnginePathAgent::script({1,static_cast<int>(protectedUnit.raw())}));
 playThroughEngine(devourer,&yes,std::nullopt,nullptr,false);
 EXPECT_TRUE(state.getObject(devourer).location.has_value());
 EXPECT_TRUE(state.getObject(protectedUnit).isAtBase());
 EXPECT_TRUE(state.getObject(protectedUnit).is_exhausted);
 EXPECT_EQ(state.player(P1).rune_pool.energy,0);
 EXPECT_TRUE(state.getObject(soraka).location.has_value());
}
TEST_F(RadianceFinal64Test, DuneDevourerHasCorrectOptionalAdditionalCostAndDeflect){
 const auto* card=card_registry.get(CardDefId{1118});
 ASSERT_NE(card,nullptr);
 auto noFriendly=card->additionalPlayCost(state,card_db,P1,kInvalidId);
 EXPECT_TRUE(noFriendly.exists);
 EXPECT_FALSE(noFriendly.payable);
 addUnit(P1,kInvalidId,2,-1);
 auto yesFriendly=card->additionalPlayCost(state,card_db,P1,kInvalidId);
 EXPECT_TRUE(yesFriendly.payable);
 EXPECT_EQ(yesFriendly.best.energy_reduction,2);
 const auto& def=card_db.get(CardDefId{1118});
 EXPECT_TRUE(def.keywords.has(Keyword::Deflect));
 EXPECT_EQ(def.deflect_value,1);
}
TEST_F(RadianceFinal64Test, BushwhackTrapGrantsExtraFacedownSlotOnlyWhileHeld){
 // A handwritten controller field does not persist through engine cleanup:
 // hold the battlefield with a friendly unit instead.
 addUnit(P1,kInvalidId,2,0);
 state.battlefields[0].controller=P1;
 auto trap=addToHand(P1,CardDefId{1107});
 playThroughEngine(trap,nullptr,
    LocationId{BattlefieldLocation{state.battlefields[0].id}});
 withEngine([&](GameEngine& e){e.testHook_recalculateAuras();});
 EXPECT_EQ(state.battlefields[0].facedown_max_occupancy,2);
 withEngine([&](GameEngine& e){
   e.testHook_executor().killObject(trap);
   e.testHook_recalculateAuras();
 });
 EXPECT_EQ(state.battlefields[0].facedown_max_occupancy,1);
}
TEST_F(RadianceFinal64Test, SixtyFourUniqueCardDefinitionsHaveCanonicalMetadata){
 ASSERT_EQ(expected.size(),64u);
 std::set<int> ids,numbers;std::set<std::string> public_codes;
 for(const auto& e:expected){
   const auto& d=card_db.get(CardDefId::fromRaw(e.id));
   ASSERT_EQ(d.id,CardDefId::fromRaw(e.id));
   EXPECT_EQ(d.name,e.name)<<e.id;
   EXPECT_EQ(d.card_type,e.type)<<e.id;
   EXPECT_EQ(d.collector_number,e.num)<<e.id;
   EXPECT_EQ(d.energy_cost,e.energy)<<e.id;
   EXPECT_EQ(d.power_cost,e.power)<<e.id;
   EXPECT_EQ(d.might,e.might)<<e.id;
   EXPECT_EQ(d.set_code,"RAD");
   EXPECT_EQ(d.set_name,"Radiance");
   EXPECT_FALSE(d.ability_text.empty())<<e.id;
   ids.insert(e.id);numbers.insert(e.num);public_codes.insert(d.public_code);
 }
 EXPECT_EQ(ids.size(),64u);
 EXPECT_EQ(numbers.size(),64u);
 EXPECT_EQ(public_codes.size(),64u);
 EXPECT_EQ(card_registry.size(),1123u);
}
} // namespace riftbound::test::final64
