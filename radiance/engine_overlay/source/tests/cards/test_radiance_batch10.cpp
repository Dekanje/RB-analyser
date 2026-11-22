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
  {1059,21,5,1,4,"Ekko, Revolutionary",CardType::Unit},
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
 EXPECT_TRUE(card_db.get(CardDefId{1059}).keywords.has(Keyword::Assault));
 EXPECT_TRUE(card_db.get(CardDefId{1064}).keywords.has(Keyword::Ganking));
 EXPECT_TRUE(card_db.get(CardDefId{1065}).keywords.has(Keyword::Deflect));
 EXPECT_TRUE(card_db.get(CardDefId{1066}).keywords.has(Keyword::Deploy));
}
TEST_F(RadianceBatch10Test, EkkoRevolutionaryEntersReady) {
 const auto card=addToHand(P1,CardDefId{1059});
 playThroughEngine(card);
 EXPECT_FALSE(state.getObject(card).is_exhausted);
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
 EXPECT_TRUE(state.getObject(ally).has_buff);
 EXPECT_TRUE(state.getObject(foe).is_stunned);
}
} // namespace
