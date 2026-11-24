"""Correct private Neeko registration sampling and mode trace audiences.

The opponent pool is a heuristic prior, never the actual secret registration.
Keep publicly revealed choices for the rest of this game, even after departure.
"""
from pathlib import Path
from apply_elnuk_errata import once

def apply(root):
    p=root/"src/core/game_state.h"
    s=once(p.read_text(),"    std::vector<CardDefId> neeko_legend_choices;",
        "    std::vector<CardDefId> neeko_legend_choices;\n    std::vector<CardDefId> neeko_revealed_legends; // public history, not the secret registration")
    p.write_text(s)
    p=root/"src/cards/units/1116_radiance_final64_d.cpp"
    s=p.read_text()
    old="   c.state.player(c.controller).neeko_granted_legends.push_back({c.source,object});"
    new=old+"""
   auto& revealed=c.state.player(c.controller).neeko_revealed_legends;
   if(std::find(revealed.begin(),revealed.end(),def.id)==revealed.end())
     revealed.push_back(def.id);
"""
    p.write_text(once(s,old,new))
    p=root/"src/agents/determinizer.cpp"
    s=p.read_text()
    anchor="        world.player(opp).observed_cards.clear();"
    # No inspection of old secret vector or its length. Preserve known public
    # history and active grants. Select a prior over remaining choices.
    s=once(s,anchor,anchor+"""
        auto& other=world.player(opp);
        std::vector<CardDefId> known=other.neeko_revealed_legends;
        for(const auto& grant:other.neeko_granted_legends)
            if(world.objectExists(grant.legend))
                known.push_back(world.getObject(grant.legend).card_def_id);
        std::sort(known.begin(),known.end());
        known.erase(std::unique(known.begin(),known.end()),known.end());
        std::set<std::string> used;
        if(const auto* starting=def(legend))used.insert(starting->name);
        std::vector<CardDefId> choices;
        for(auto id:known){
            const auto* d=def(id);
            if(d && d->card_type==CardType::Legend && used.insert(d->name).second)
                choices.push_back(id);
        }
        // Sample independently of actual opponent Neeko presence and pool
        // cardinality: an unseen Neeko can be drawn by the existing model.
        // Registry-wide prior, not an optimized or calibrated opponent policy.
        std::vector<CardDefId> candidates;
        for(const auto& [id,d]:db_.all())
            if(d.card_type==CardType::Legend && !d.banned &&
               !used.count(d.name))candidates.push_back(id);
        std::sort(candidates.begin(),candidates.end());
        const size_t limit=choices.size()<3 ? choices.size()+pick(4-choices.size()) : choices.size();
        while(choices.size()<limit && !candidates.empty()){
            auto id=candidates[pick(candidates.size())];
            const auto* d=def(id);
            if(d && used.insert(d->name).second)choices.push_back(id);
            candidates.erase(std::remove_if(candidates.begin(),candidates.end(),
                [&](CardDefId i){return i==id || (d && def(i) && def(i)->name==d->name);}),candidates.end());
        }
        std::shuffle(choices.begin(),choices.end(),rng);
        other.neeko_legend_choices=std::move(choices);
""")
    p.write_text(s)
    p=root/"src/engine/observer_view.cpp"
    s=p.read_text()
    anchor="        put(out, card(ps.legend_zone));"
    s=once(s,anchor,anchor+"""
        // The owner knows their registered choices and ordering; other seat
        // sees only publicly revealed legend history, not count/order of pool.
        put(out,-1030);
        if(p==observer_){
            put(out,static_cast<int64_t>(ps.neeko_legend_choices.size()));
            for(auto id:ps.neeko_legend_choices)put(out,id.raw());
        }
        auto revealed=ps.neeko_revealed_legends;
        std::sort(revealed.begin(),revealed.end());
        put(out,static_cast<int64_t>(revealed.size()));
        for(auto id:revealed)put(out,id.raw());
""")
    p.write_text(s)
    p=root/"src/cards/card.cpp"
    s=p.read_text()
    old="""        RIFT_TRACE(ctx.events, "MODE_PROMPT: " + label + " [" + label_summary +
                             "] (agent decides among " +
                             std::to_string(legal.size()) + " modes)");"""
    new="""        if(label=="Neeko: choose a legend"){
            RIFT_TRACE_PRIVATE(ctx.events,ctx.controller,"MODE_PROMPT: " + label + " [" + label_summary +
                             "] (agent decides among " + std::to_string(legal.size()) + " modes)");
        }else{
"""+old+"""
        }"""
    s=once(s,old,new)
    old="""        RIFT_TRACE(ctx.events, "MODE_PICKED: " + label + " = mode#" +
                             std::to_string(m) +
                             (m < static_cast<int>(mode_labels.size())
                                ? " (" + mode_labels[m] + ")" : ""));"""
    new="""        if(label=="Neeko: choose a legend"){
            RIFT_TRACE_PRIVATE(ctx.events,ctx.controller,"MODE_PICKED: " + label + " = mode#" +
                             std::to_string(m) +
                             (m < static_cast<int>(mode_labels.size()) ? " (" + mode_labels[m] + ")" : ""));
        }else{
"""+old+"""
        }"""
    p.write_text(once(s,old,new))
    p=root/"tests/cards/test_radiance_final64.cpp"
    s=p.read_text()
    s=once(s,'#include "rules/deck_validator.h"','#include "rules/deck_validator.h"\n#include "agents/determinizer.h"\n#include "engine/observer_view.h"\n#include <random>')
    marker="} // namespace riftbound::test::final64"
    tests=r"""
TEST_F(RadianceFinal64Test, PrivacyNeekoSamplerIndependentOfOpponentSecretCountAndIds){
 WorldSampler sampler(card_db);
 state.player(P2).neeko_legend_choices={CardDefId{249}};
 auto variant=state;
 variant.player(P2).neeko_legend_choices={CardDefId{252},CardDefId{254},CardDefId{256}};
 state.player(P1).neeko_legend_choices={CardDefId{258}};
 variant.player(P1).neeko_legend_choices=state.player(P1).neeko_legend_choices;
 for(unsigned seed=1;seed<=64;++seed){
   auto a=state;auto b=variant;
   std::mt19937_64 ra(seed),rb(seed);
   sampler.sample(a,P1,ra);sampler.sample(b,P1,rb);
   EXPECT_EQ(a.player(P2).neeko_legend_choices,b.player(P2).neeko_legend_choices)<<seed;
   EXPECT_EQ(a.player(P1).neeko_legend_choices,state.player(P1).neeko_legend_choices);
   EXPECT_LE(a.player(P2).neeko_legend_choices.size(),3u);
   std::set<std::string> names;
   for(auto id:a.player(P2).neeko_legend_choices){
      const auto& d=card_db.get(id);
      EXPECT_EQ(d.card_type,CardType::Legend);
      EXPECT_FALSE(d.banned);
      EXPECT_TRUE(names.insert(d.name).second);
   }
 }
 EXPECT_EQ(state.player(P2).neeko_legend_choices.size(),1u);
 EXPECT_EQ(variant.player(P2).neeko_legend_choices.size(),3u);
}
TEST_F(RadianceFinal64Test, PrivacyNeekoSamplerRetainsPublicHistoryAfterDeparture){
 state.player(P2).neeko_legend_choices={CardDefId{249},CardDefId{252}};
 auto neeko=addUnit(P2,CardDefId{1131},4,0);
 fireTriggerThroughEngine(neeko,TriggerType::WhenYouPlayMe);
 ASSERT_EQ(state.player(P2).neeko_granted_legends.size(),1u);
 auto revealed=state.getObject(state.player(P2).neeko_granted_legends.front().legend).card_def_id;
 withEngine([&](GameEngine& e){
   e.testHook_executor().killObject(neeko);settleLikeTheEngine(e);
 });
 ASSERT_TRUE(state.player(P2).neeko_granted_legends.empty());
 ASSERT_EQ(state.player(P2).neeko_revealed_legends,std::vector<CardDefId>{revealed});
 WorldSampler sampler(card_db);
 for(unsigned seed=1;seed<=32;++seed){
   auto w=state;std::mt19937_64 rng(seed);sampler.sample(w,P1,rng);
   const auto& extra=w.player(P2).neeko_legend_choices;
   EXPECT_NE(std::find(extra.begin(),extra.end(),revealed),extra.end());
 }
}
TEST_F(RadianceFinal64Test, PrivacyNeekoObservationHidesOpponentPoolButIncludesOwn){
 state.player(P1).neeko_legend_choices={CardDefId{249}};
 auto variant=state;
 variant.player(P1).neeko_legend_choices={CardDefId{252},CardDefId{254},CardDefId{256}};
 EXPECT_EQ(ObserverView(state,P2,card_db).fingerprint(),ObserverView(variant,P2,card_db).fingerprint());
 EXPECT_NE(ObserverView(state,P1,card_db).fingerprint(),ObserverView(variant,P1,card_db).fingerprint());
}
TEST_F(RadianceFinal64Test, PrivacyNeekoModeTraceIsControllerOnlyBothSeats){
 for(auto controller:{P1,P2}){
   const auto other=opponent(controller);
   state.player(controller).neeko_legend_choices={CardDefId{249},CardDefId{252},CardDefId{254}};
   auto source=addUnit(controller,CardDefId{1131},4,0);
   std::vector<LogEvent> trace;
   auto connection=events.on_log.connect([&](const LogEvent& log){trace.push_back(log);});
   fireTriggerThroughEngine(source,TriggerType::WhenYouPlayMe);
   connection.disconnect();
   ASSERT_EQ(state.player(controller).neeko_granted_legends.size(),1u);
   int prompts=0,picks=0;
   for(const auto& log:trace){
      bool prompt=log.message.find("MODE_PROMPT: Neeko: choose a legend")!=std::string::npos;
      bool pick=log.message.find("MODE_PICKED: Neeko: choose a legend")!=std::string::npos;
      if(!prompt && !pick)continue;
      prompts+=prompt;picks+=pick;
      EXPECT_TRUE(log.visibleTo(controller));
      EXPECT_FALSE(log.visibleTo(other));
      EXPECT_FALSE(log.isPublic());
      if(prompt){
         for(auto id:state.player(controller).neeko_legend_choices)
             EXPECT_NE(log.message.find(card_db.get(id).name),std::string::npos);
      }
   }
   EXPECT_EQ(prompts,1);
   EXPECT_EQ(picks,1);
 }
}
"""
    p.write_text(once(s,marker,tests+"\n"+marker))
    print("RAD167_PRIVACY_CANDIDATE_PATCH_APPLIED")

if __name__=="__main__":
    apply(Path("alpharune"))
