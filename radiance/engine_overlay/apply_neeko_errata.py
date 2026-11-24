#!/usr/bin/env python3
"""Candidate native RAD-167 correction, after the historical overlays.

The dated card erratum (up to three) takes precedence over the patch-note
example using three. Register once for main/champion/sideboard, never per copy.
"""
from pathlib import Path
from apply_elnuk_errata import once

def apply(engine):
    h=engine/"src/rules/deck_validator.h"
    ht=once(h.read_text(),"// exactly three named legends, if Neeko is in deck","// up to three named legends, if Neeko is in registered pool")
    p=engine/"src/rules/deck_validator.cpp"
    s=p.read_text()
    s=once(s,"// RAD-167: Neeko selects exactly three EXTRA legends at deck submission.","// RAD-167: register up to three extra legends for the full registered pool.")
    s=once(s,"std::find(deck.main_deck.begin(),deck.main_deck.end(),CardDefId{1131})\n            !=deck.main_deck.end();","std::find(deck.main_deck.begin(),deck.main_deck.end(),CardDefId{1131})\n            !=deck.main_deck.end() ||\n        std::find(deck.sideboard.begin(),deck.sideboard.end(),CardDefId{1131})\n            !=deck.sideboard.end();")
    s=once(s,'if(deck.neeko_legends.size()!=3)\n            result.addError("Neeko requires exactly 3 extra legends");','if(deck.neeko_legends.size()>3)\n            result.addError("Neeko allows at most 3 extra legends");')
    s=once(s,'if(id==kInvalidId) {\n                result.addError("Neeko legends must be valid Legend cards");','if(id==kInvalidId || db_.all().find(id)==db_.all().end()) {\n                result.addError("Neeko legends must be valid Legend cards");')
    c=engine/"src/cards/units/1116_radiance_final64_d.cpp"
    ct=c.read_text()
    start=ct.index("class R64_1131 final")
    end=ct.index("\n};",start)+3
    b=ct[start:end]
    # Selection is a non-target decision on resolution per Riot's patch notes.
    # Do not commit an index into a changing list during finalization.
    b=once(b," unsigned choicesAtFinalization() const override { return kFinalizeTrigger; }\n","")
    a=b.index("   // A queued play trigger")
    z=b.index("   const auto& def=legend->def();",a)
    b=b[:a]+"""   if(!c.state.objectExists(c.source) ||
      !c.state.getObject(c.source).location.has_value())return;
   const auto& ps=c.state.player(c.controller);
   const auto& selected=ps.neeko_legend_choices;
   if(selected.empty() || selected.size()>3 || !c.registry)return;
   std::vector<std::string> labels;
   uint32_t available=0;
   for(size_t i=0;i<selected.size();++i){
     const auto* legend=c.registry->get(selected[i]);
     if(!legend || legend->def().card_type!=CardType::Legend)return;
     const auto& name=legend->def().name;
     labels.push_back(name);
     bool active=false;
     if(c.state.objectExists(ps.legend_zone))
       active=c.state.getObject(ps.legend_zone).name==name;
     for(const auto& grant:ps.neeko_granted_legends)
       if(c.state.objectExists(grant.legend) &&
          c.state.getObject(grant.legend).name==name)active=true;
     if(!active)available|=(1u<<i);
   }
   if(!available)return;
   const int choice=pickMode(c,"Neeko: choose a legend",
      static_cast<int>(selected.size()),labels,available);
   if(choice<0 || choice>=static_cast<int>(selected.size()) ||
      !(available & (1u<<choice)))return;
   const auto* legend=c.registry->get(selected[choice]);
   if(!legend)return;
"""+b[z:]
    b=once(b,"choose 3 different legends","choose up to 3 different legends")
    b=once(b,"   obj.zone=ZoneType::LegendZone;","   obj.zone=ZoneType::LegendZone;\n   obj.is_exhausted=false;")
    # Keep historical random builder choosing three; legal policy, not minimum.
    q=engine/"tests/cards/test_radiance_final64.cpp"
    qt=q.read_text()
    marker="} // namespace riftbound::test::final64"
    tests=r"""
TEST_F(RadianceFinal64Test, ErrataNeekoAcceptsZeroThroughThreeAdditionalLegends){
 DeckSubmission d;
 d.legend=CardDefId{249};
 d.chosen_champion=CardDefId{1131};
 const std::vector<CardDefId> ids={CardDefId{252},CardDefId{254},CardDefId{256}};
 for(size_t n=0;n<=ids.size();++n){
   d.neeko_legends.assign(ids.begin(),ids.begin()+n);
   auto v=DeckValidator(card_db).validate(d);
   EXPECT_FALSE(std::any_of(v.errors.begin(),v.errors.end(),[](const std::string& e){
      return e.find("Neeko ")!=std::string::npos;
   }))<<n;
 }
}
TEST_F(RadianceFinal64Test, ErrataNeekoRejectsFourAndDuplicateAndInvalidLegends){
 DeckSubmission d;
 d.legend=CardDefId{249};
 d.chosen_champion=CardDefId{1131};
 auto rejects=[&](const char* message){
   auto v=DeckValidator(card_db).validate(d);
   return std::any_of(v.errors.begin(),v.errors.end(),[&](const std::string& e){
      return e.find(message)!=std::string::npos;
   });
 };
 d.neeko_legends={CardDefId{252},CardDefId{254},CardDefId{256},CardDefId{258}};
 EXPECT_TRUE(rejects("Neeko allows at most 3"));
 d.neeko_legends={CardDefId{252},CardDefId{252}};
 EXPECT_TRUE(rejects("Neeko legends must all have different names"));
 d.neeko_legends={CardDefId{249}};
 EXPECT_TRUE(rejects("Neeko legends must all have different names"));
 d.neeko_legends={CardDefId{1084}};
 EXPECT_TRUE(rejects("Neeko legends must be Legend cards"));
 d.neeko_legends={CardDefId{99999}};
 EXPECT_TRUE(rejects("Neeko legends must be valid Legend cards"));
}
TEST_F(RadianceFinal64Test, ErrataNeekoSideboardOnlyRegistrationAccepted){
 DeckSubmission d;
 d.legend=CardDefId{249};
 d.chosen_champion=CardDefId{1084};
 d.sideboard={CardDefId{1131}};
 d.neeko_legends={CardDefId{252},CardDefId{254}};
 auto v=DeckValidator(card_db).validate(d);
 EXPECT_FALSE(std::any_of(v.errors.begin(),v.errors.end(),[](const std::string& e){
    return e.find("Neeko ")!=std::string::npos;
 }));
 d.sideboard.clear();
 v=DeckValidator(card_db).validate(d);
 EXPECT_TRUE(std::any_of(v.errors.begin(),v.errors.end(),[](const std::string& e){
    return e.find("Neeko legends supplied without Neeko")!=std::string::npos;
 }));
}
TEST_F(RadianceFinal64Test, ErrataNeekoOneRegisteredLegendEntersReady){
 state.player(P1).neeko_legend_choices={CardDefId{252}};
 auto neeko=addUnit(P1,CardDefId{1131},4,0);
 fireTriggerThroughEngine(neeko,TriggerType::WhenYouPlayMe);
 const auto& grants=state.player(P1).neeko_granted_legends;
 ASSERT_EQ(grants.size(),1u);
 ASSERT_TRUE(state.objectExists(grants[0].legend));
 const auto& o=state.getObject(grants[0].legend);
 EXPECT_EQ(o.card_def_id,CardDefId{252});
 EXPECT_FALSE(o.is_exhausted);
 EXPECT_EQ(o.zone,ZoneType::LegendZone);
}
TEST_F(RadianceFinal64Test, ErrataNeekoTwoRegisteredLegendsAllowsSecondChoice){
 state.player(P1).neeko_legend_choices={CardDefId{252},CardDefId{254}};
 auto neeko=addUnit(P1,CardDefId{1131},4,0);
 EnginePathAgent choose_second([](const std::vector<Intent>& options){
    EXPECT_EQ(options.size(),2u);
    auto it=std::find_if(options.begin(),options.end(),[](const Intent& i){
       return i.chosen_value==1;
    });
    EXPECT_NE(it,options.end());
    return it==options.end()?options.front():*it;
 });
 fireTriggerThroughEngine(neeko,TriggerType::WhenYouPlayMe,&choose_second);
 const auto& grants=state.player(P1).neeko_granted_legends;
 ASSERT_EQ(grants.size(),1u);
 EXPECT_EQ(state.getObject(grants[0].legend).card_def_id,CardDefId{254});
}
TEST_F(RadianceFinal64Test, ErrataNeekoSharedPoolExcludesActiveAndReusesAfterDeparture){
 state.player(P1).neeko_legend_choices={CardDefId{252},CardDefId{254}};
 auto a=addUnit(P1,CardDefId{1131},4,0);
 auto b=addUnit(P1,CardDefId{1131},4,0);
 auto c=addUnit(P1,CardDefId{1131},4,0);
 fireTriggerThroughEngine(a,TriggerType::WhenYouPlayMe);
 ASSERT_EQ(state.player(P1).neeko_granted_legends.size(),1u);
 EXPECT_EQ(state.getObject(state.player(P1).neeko_granted_legends[0].legend).card_def_id,CardDefId{252});
 EnginePathAgent only_remaining([](const std::vector<Intent>& options){
    EXPECT_EQ(options.size(),1u);
    EXPECT_EQ(options.front().chosen_value,1);
    return options.front();
 });
 fireTriggerThroughEngine(b,TriggerType::WhenYouPlayMe,&only_remaining);
 ASSERT_EQ(state.player(P1).neeko_granted_legends.size(),2u);
 EXPECT_EQ(state.getObject(state.player(P1).neeko_granted_legends[1].legend).card_def_id,CardDefId{254});
 fireTriggerThroughEngine(c,TriggerType::WhenYouPlayMe);
 ASSERT_EQ(state.player(P1).neeko_granted_legends.size(),2u);
 withEngine([&](GameEngine& e){
    e.testHook_executor().killObject(a);
    settleLikeTheEngine(e);
 });
 ASSERT_EQ(state.player(P1).neeko_granted_legends.size(),1u);
 auto d=addUnit(P1,CardDefId{1131},4,0);
 fireTriggerThroughEngine(d,TriggerType::WhenYouPlayMe);
 ASSERT_EQ(state.player(P1).neeko_granted_legends.size(),2u);
 EXPECT_EQ(state.getObject(state.player(P1).neeko_granted_legends.back().legend).card_def_id,CardDefId{252});
}
"""
    qt=once(qt,marker,tests+"\n"+marker)
    h.write_text(ht);p.write_text(s);c.write_text(ct[:start]+b+ct[end:]);q.write_text(qt)
    print("RAD167_ERRATA_CANDIDATE_PATCH_APPLIED")

if __name__=="__main__":
    apply(Path("alpharune"))
