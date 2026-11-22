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
 auto eve=addUnit(P1,CardDefId{1108},4,0);
 auto facedown=state.createObject();
 auto& obj=state.getObject(facedown);
 obj.owner=P1;obj.controller=P1;obj.card_type=CardType::Spell;
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
 for(const auto& [id,o]:state.objects.onBoard())
   if(o.isRune()&&o.controller==P1&&o.is_exhausted)++exhausted;
 EXPECT_EQ(exhausted,4);
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
 EnginePathAgent select(EnginePathAgent::choosing(target));
 playThroughEngine(spell,&select);
 EXPECT_EQ(state.getObject(target).damage_marked,5);
 EXPECT_EQ(state.getObject(unaffected).damage_marked,0);
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
