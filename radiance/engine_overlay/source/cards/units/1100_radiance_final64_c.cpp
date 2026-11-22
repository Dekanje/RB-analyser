// RAD final64 generated canonical printing definitions. Mechanical status: WORK IN PROGRESS.
// These classes must not be declared mechanics-accepted without per-card scenarios.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "cards/card_registry.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <memory>
#include <string>
#include <tuple>
#include <vector>

namespace riftbound {
namespace {
CardDef mkFinal64(int id,int num,const char* name,CardType type,int energy,int power,int might,
              std::vector<Domain> domains,Rarity rarity,const char* rules) {
 CardDef d;
 d.id=CardDefId::fromRaw(id);
 const auto n=std::to_string(num);
 d.def_id="rad-"+std::string(3-n.size(),'0')+n+"-167";
 d.public_code="RAD-"+std::string(3-n.size(),'0')+n+"/167";
 d.name=name;d.set_code="RAD";d.set_name="Radiance";d.collector_number=num;
 d.card_type=type;d.energy_cost=energy;d.power_cost=power;d.might=might;
 d.domains=std::move(domains);d.rarity=rarity;d.ability_text=rules;
 return d;
}

class R64_1100 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1100,91,R"RB(Jarvan IV - Martial Paragon)RB",CardType::Unit,4,1,4,{Domain::Body},Rarity::Epic,R"RB(Your gear with [Deploy] have [Action]. (They can be played on your turn or in showdowns.)
When I conquer, if there is a friendly gear with [Deploy] here, channel 1 rune exhausted.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Demacia)RB",R"RB(Jarvan IV)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/8edacba51db193506e13e1afb6a8509256cdf55c-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1101 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1101,92,R"RB(Seraphic Wyvern)RB",CardType::Unit,7,0,7,{Domain::Body},Rarity::Epic,R"RB(If you would channel runes, channel that many runes plus 1 exhausted rune instead.)RB");
  d.tags={R"RB(Dragon)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/ad1793554440d8d5017eadc565ca6c787a969de1-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1102 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1102,94,R"RB(Explosimian)RB",CardType::Unit,6,0,6,{Domain::Chaos},Rarity::Common,R"RB(When I hold, play three Bomb gear tokens to a single battlefield. (They have [Deploy]. When each dies, deal 2 to an enemy there and kill your other Bombs there.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/f2590617229f3efc078aa2429f65b85101303200-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1103 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1103,98,R"RB(Siren's Song)RB",CardType::Spell,2,0,0,{Domain::Chaos},Rarity::Common,R"RB([Reaction] (Play any time, even before spells and abilities resolve.)
Move an enemy unit that moved this turn.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/742967b3e85f51b242fc04b8db4c4e3cd7b88672-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Reaction);
  return d;
 }();
};

class R64_1104 final : public SpellCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1104,102,R"RB(Demon Shade)RB",CardType::Spell,3,0,0,{Domain::Fury},Rarity::Uncommon,R"RB([Hidden] (Hide now for [A] to react with later for [0].)
Choose a friendly unit, then choose one —Move it to an open battlefield.
Give it [Ganking] this turn if there are no open battlefields. (It can move from battlefield to battlefield.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/e9dd313886624aafc7e0c7f9e1689225c042b484-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Hidden);
  return d;
 }();
};

class R64_1105 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1105,103,R"RB(Gutter Guardian)RB",CardType::Unit,3,0,3,{Domain::Chaos},Rarity::Uncommon,R"RB([Hidden] (Hide now for [A] to react with later for [0].)
[Show Off] a card with [Hidden]. (As you play me, you may reveal such a card from hand or pick another friendly one on the board.)
When you play me, if you showed off, [Add] [A].)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/756827744317003e4992163ff9bf1dc991682de8-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Hidden);
  return d;
 }();
};

class R64_1106 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1106,104,R"RB(Pitiless Stalker)RB",CardType::Unit,5,1,5,{},Rarity::Uncommon,R"RB([E]: [Stun] an enemy unit. (It doesn't deal combat damage this turn.))RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/fc61b244fb3ed01d61617c3c2633a71424604130-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1107 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1107,108,R"RB(Bushwhack Trap)RB",CardType::Unit,1,0,0,{Domain::Fury},Rarity::Rare,R"RB([Deploy] (Play this only to a battlefield. When an opponent holds here, kill this.)
While you or an ally control this battlefield, that player may hide an additional card here.)RB");
  d.tags={R"RB(Device)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/120762e23a599ee14d3f88856fcf707154338fb0-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Deploy);
  return d;
 }();
};

class R64_1108 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1108,109,R"RB(Evelynn - In Control)RB",CardType::Unit,4,1,4,{Domain::Chaos},Rarity::Rare,R"RB([Disarm] (When I attack, give an enemy unit here -1 [M] this turn.)
When I hold, if you control a facedown card here, score 1 point.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Evelynn)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/8c17158e6153eddb4b56abd8a09cbbd20600b049-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Disarm);
  return d;
 }();
};

class R64_1109 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1109,110,R"RB(Lulu - Whimsical)RB",CardType::Unit,3,0,3,{Domain::Chaos},Rarity::Rare,R"RB(When I move, you may have another unit's base Might become 4 this turn.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Yordle)RB",R"RB(Bandle City)RB",R"RB(Lulu)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/defd09480671a1e394725f21b6c3448ebec77913-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1110 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1110,111,R"RB(Mechanical Bandit)RB",CardType::Gear,4,1,0,{Domain::Fury},Rarity::Rare,R"RB(At the start of your Beginning Phase, each player reveals the top card of their Main Deck. If you revealed a card with the lowest Energy cost, draw it. Recycle the rest.)RB");
  d.tags={R"RB(Device)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/cb2a419b61b6f1e6d138c3c3b07b393a4037237b-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1111 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1111,112,R"RB(Ziggs - Explosive)RB",CardType::Unit,4,0,4,{Domain::Chaos},Rarity::Rare,R"RB([1], [E]: Play a Bomb gear token to a battlefield. (It has [Deploy]. When it dies, deal 2 to an enemy there and kill your other Bombs there.)
When I defend, you may kill a friendly gear to give me +2 [M] this turn.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Bandle City)RB",R"RB(Ziggs)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/f0c1f1f3b69b31a69f9637ece841b5ee1029cdd3-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1112 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1112,113,R"RB(Angler Wyrm)RB",CardType::Unit,8,0,8,{Domain::Chaos},Rarity::Epic,R"RB([Deflect] (Opponents must pay [A] to choose me with a spell or ability.)
[E]: Choose an opponent. They must move a unit they control to my battlefield.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/e805eba9add03fd3e1b1601b15c12a46fd403282-744x1039.png?accountingTag=RB)RB";
  d.keywords.set(Keyword::Deflect);
  d.deflect_value=1;
  return d;
 }();
};

class R64_1113 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1113,114,R"RB(Riven - Deserter)RB",CardType::Unit,5,1,5,{Domain::Chaos},Rarity::Epic,R"RB(When another friendly unit becomes exhausted, give me +1 [M] this turn.
Exhaust a friendly unit: Ready a unit. Use this ability only once each turn.)RB");
  d.super_type=SuperType::Champion;
  d.tags={R"RB(Riven)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/59c080321a697164c9eeb6f0ad297ff0d0b85808-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1114 final : public UnitCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1114,115,R"RB(Transpositionist)RB",CardType::Unit,6,0,4,{Domain::Chaos},Rarity::Epic,R"RB([C], [E]: Return a friendly unit to its owner's hand. You may play a unit with less Might than that unit had, ignoring its cost.)RB");
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/60cf9dbb9345d44f0a9a78b60d5fb71411b50d69-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};

class R64_1115 final : public GearCard {
public:
 const CardDef& def() const override { return d_; }
 // MECHANICS_INCOMPLETE: printed non-keyword abilities require implementation and tests.
private:
 const CardDef d_=[] {
  auto d=mkFinal64(1115,120,R"RB(Meticulous Restorationist)RB",CardType::Gear,2,0,2,{Domain::Order},Rarity::Common,R"RB(When you play a card with Energy cost [7] or more, you may play me from your trash for [O].)RB");
  d.tags={R"RB(Device)RB"};
  d.image_url=R"RB(https://cmsassets.rgpub.io/sanity/images/dsfx7636/game_data_live/ee50fbf5e902e7109a3d54b417edc440b5a37198-744x1039.png?accountingTag=RB)RB";
  return d;
 }();
};
}
void register_card_1100(CardRegistry& r){r.registerCard(CardDefId{1100},std::make_unique<R64_1100>());}
void register_card_1101(CardRegistry& r){r.registerCard(CardDefId{1101},std::make_unique<R64_1101>());}
void register_card_1102(CardRegistry& r){r.registerCard(CardDefId{1102},std::make_unique<R64_1102>());}
void register_card_1103(CardRegistry& r){r.registerCard(CardDefId{1103},std::make_unique<R64_1103>());}
void register_card_1104(CardRegistry& r){r.registerCard(CardDefId{1104},std::make_unique<R64_1104>());}
void register_card_1105(CardRegistry& r){r.registerCard(CardDefId{1105},std::make_unique<R64_1105>());}
void register_card_1106(CardRegistry& r){r.registerCard(CardDefId{1106},std::make_unique<R64_1106>());}
void register_card_1107(CardRegistry& r){r.registerCard(CardDefId{1107},std::make_unique<R64_1107>());}
void register_card_1108(CardRegistry& r){r.registerCard(CardDefId{1108},std::make_unique<R64_1108>());}
void register_card_1109(CardRegistry& r){r.registerCard(CardDefId{1109},std::make_unique<R64_1109>());}
void register_card_1110(CardRegistry& r){r.registerCard(CardDefId{1110},std::make_unique<R64_1110>());}
void register_card_1111(CardRegistry& r){r.registerCard(CardDefId{1111},std::make_unique<R64_1111>());}
void register_card_1112(CardRegistry& r){r.registerCard(CardDefId{1112},std::make_unique<R64_1112>());}
void register_card_1113(CardRegistry& r){r.registerCard(CardDefId{1113},std::make_unique<R64_1113>());}
void register_card_1114(CardRegistry& r){r.registerCard(CardDefId{1114},std::make_unique<R64_1114>());}
void register_card_1115(CardRegistry& r){r.registerCard(CardDefId{1115},std::make_unique<R64_1115>());}
} // namespace riftbound
