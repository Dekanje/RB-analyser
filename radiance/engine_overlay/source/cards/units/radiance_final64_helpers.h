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

template <typename Predicate>
inline bool f64ShowOff(CardContext& c,Predicate&& eligible,
                       const std::string& label) {
 if(!c.state.objectExists(c.source))return false;
 auto& played=c.state.getObject(c.source);
 played.card_counters["__final64_showoff"]=0;
 std::vector<GameObjectId> candidates;
 for(const auto id:c.state.player(c.controller).hand) {
   if(id==c.source || !c.state.objectExists(id))continue;
   const auto& o=c.state.getObject(id);
   if(o.card_def_id==kInvalidId)continue;
   const auto& d=c.executor.cardDB().get(o.card_def_id);
   if(eligible(o,d))candidates.push_back(id);
 }
 for(const auto& [id,o]:c.state.objects.onBoard()){
   if(id==c.source||o.controller!=c.controller||!o.location||
      o.card_def_id==kInvalidId)continue;
   const auto& d=c.executor.cardDB().get(o.card_def_id);
   if(eligible(o,d))candidates.push_back(id);
 }
 std::sort(candidates.begin(),candidates.end());
 if(candidates.empty()||!c.executor.confirmNow(c.controller,label))return false;
 const auto chosen=c.executor.chooseObjectNow(c.controller,candidates,label);
 if(chosen==kInvalidId)return false;
 const auto& card=c.state.getObject(chosen);
 const auto& def=c.executor.cardDB().get(card.card_def_id);
 const bool fromHand=(card.zone==ZoneType::Hand);
 if(fromHand)c.events.emit(CardRevealedEvent{chosen,card.card_def_id,card.owner,true,
                                            PlayerId::None,ZoneType::Hand});
 played.card_counters["__final64_showoff"]=1;
 played.card_counters["__final64_showoff_energy"]=def.energy_cost;
 played.card_counters["__final64_showoff_power"]=def.power_cost;
 played.card_counters["__final64_showoff_might"]=fromHand?def.might:card.current_might;
 return true;
}
inline bool f64WasShownOff(const GameState& s,GameObjectId id){
 if(!s.objectExists(id))return false;
 const auto& counters=s.getObject(id).card_counters;
 const auto it=counters.find("__final64_showoff");
 return it!=counters.end()&&it->second==1;
}
inline int f64ShownOffValue(const GameState& s,GameObjectId id,const char* key){
 if(!s.objectExists(id))return 0;
 const auto& c=s.getObject(id).card_counters;
 const auto it=c.find(key);
 return it==c.end()?0:it->second;
}


inline GameObjectId f64RevealTop(CardContext& c,PlayerId owner){
 c.executor.lookBeforeReveal(owner);
 auto& deck=c.state.player(owner).main_deck;
 if(deck.empty())return kInvalidId;
 const auto top=deck.back();
 if(!c.state.objectExists(top))return kInvalidId;
 (void)c.executor.seenOnTopOfDeck(owner,top);
 if(!c.state.objectExists(top)||c.state.getObject(top).zone!=ZoneType::MainDeck)
   return kInvalidId; // replacement moved or banished the card
 const auto& obj=c.state.getObject(top);
 c.events.emit(CardRevealedEvent{top,obj.card_def_id,obj.owner,true,
                                 PlayerId::None,ZoneType::MainDeck});
 return top;
}

// Revealed top cards remain in Main Deck until explicitly taken. A
// recycleCards call on one still in the deck inserts a duplicate object.
inline void f64RecycleRevealedTop(CardContext& c,PlayerId owner,GameObjectId top){
 if(top==kInvalidId||!c.state.objectExists(top))return;
 if(c.state.getObject(top).zone!=ZoneType::MainDeck)return;
 auto& deck=c.state.player(owner).main_deck;
 if(std::find(deck.begin(),deck.end(),top)==deck.end())return;
 if(!deck::take(c.state,top,deck::Place::Held,knowledge::everyone()))return;
 c.executor.recycleCards(owner,{top},knowledge::everyone());
}
inline int f64TotalFriendlyExhausted(const GameState& s,PlayerId p,GameObjectId exclude=kInvalidId){
 int n=0;
 for(const auto& [id,o]:s.objects.onBoard())
   if(id!=exclude&&o.isUnit()&&o.controller==p&&o.location&&o.is_exhausted)++n;
 return n;
}
}
