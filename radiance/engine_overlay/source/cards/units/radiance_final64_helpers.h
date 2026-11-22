#pragma once
// Shared, card-specific helpers for the final 64 Radiance implementations.
// All functions are inline: AlphaRune builds card sources using C++ unity TUs.
#include "cards/card.h"
#include "cards/card_helpers.h"
#include "core/game_state.h"
#include "engine/effect_executor.h"
#include <algorithm>
#include <vector>

namespace riftbound {
inline std::vector<GameObjectId> f64Units(const GameState& s,PlayerId controller,
                                         bool friendly=true,bool battlefieldOnly=false){
 return boardObjects(s,[&](const GameObject& o){
   return o.isUnit()&&((o.controller==controller)==friendly)&&
          (!battlefieldOnly||o.isAtBattlefield());
 });
}
inline std::vector<GameObjectId> f64Gears(const GameState& s,PlayerId controller,
                                         bool friendly=true){
 return boardObjects(s,[&](const GameObject& o){
   return o.isGear()&&((o.controller==controller)==friendly);
 });
}
inline GameObjectId f64Recruit(CardContext& c,LocationId where,int might=1){
 return c.executor.createToken(c.controller,CardType::Unit,"Recruit",might,
    {"Recruit"},KeywordSet{},where,false);
}
inline GameObjectId f64Mech(CardContext& c,LocationId where,int might=3){
 return c.executor.createToken(c.controller,CardType::Unit,"Mech",might,
    {"Mech"},KeywordSet{},where,false);
}
inline GameObjectId f64Bomb(CardContext& c,LocationId where){
 KeywordSet kw;kw.set(Keyword::Deploy);
 return c.executor.createToken(c.controller,CardType::Gear,"Bomb",0,
    {"Bomb"},kw,where,false,{},CardDefId{982});
}
inline int f64TotalFriendlyExhausted(const GameState& s,PlayerId p,GameObjectId exclude=kInvalidId){
 int n=0;
 for(const auto& [id,o]:s.objects.onBoard())
   if(id!=exclude&&o.isUnit()&&o.controller==p&&o.location&&o.is_exhausted)++n;
 return n;
}
}
