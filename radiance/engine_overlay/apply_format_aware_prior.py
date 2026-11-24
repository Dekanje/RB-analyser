"""Bind sampled unknown identities to an explicit public registration universe.

Only opted-in candidate executions use this policy; default historical paths
retain upstream sampling. This is a public format restriction, not a decklist.
"""
from pathlib import Path
from apply_elnuk_errata import once
def apply(root):
    p=root/"src/rules/deck_model.h"
    s=once(p.read_text(),"#include <map>","#include <map>\n#include <set>")
    s=once(s,"    explicit DeckModel(const CardDB& db);","""    explicit DeckModel(const CardDB& db);
    static std::set<CardDefId> parseFormatIds(const CardDB& db,const std::string& text);
    bool formatRestricted() const { return !format_ids_.empty(); }
    bool permits(CardDefId id) const { return !formatRestricted() || format_ids_.count(id)!=0; }
    const std::set<CardDefId>& formatIds() const { return format_ids_; }""")
    s=once(s,"    RandomDeckBuilder builder_;","    RandomDeckBuilder builder_;\n    std::set<CardDefId> format_ids_;")
    p.write_text(s)
    p=root/"src/rules/deck_model.cpp"
    s=once(p.read_text(),"#include <algorithm>","#include <algorithm>\n#include <cstdlib>\n#include <stdexcept>\n#include <limits>")
    s=once(s,"DeckModel::DeckModel(const CardDB& db) : db_(db), builder_(db) {","""std::set<CardDefId> DeckModel::parseFormatIds(const CardDB& db,const std::string& text) {
    std::set<CardDefId> ids;
    size_t start=0;
    uint64_t previous=0;
    for(;;){
        auto end=text.find(',',start);
        auto part=text.substr(start,end==std::string::npos?end:end-start);
        if(part.empty() || part.size()>10 || part.front()=='0' ||
           part.find_first_not_of("0123456789")!=std::string::npos)
            throw std::invalid_argument("invalid public format identity list");
        auto n=std::stoull(part);
        if(n<=previous || n>std::numeric_limits<uint32_t>::max())
            throw std::invalid_argument("noncanonical public format identity list");
        CardDefId id{static_cast<uint32_t>(n)};
        auto it=db.all().find(id);
        if(it==db.all().end() || it->second.banned || it->second.isTokenCard())
            throw std::invalid_argument("unknown, native-banned or token format identity");
        ids.insert(id);previous=n;
        if(end==std::string::npos)break;
        start=end+1;
    }
    return ids;
}
DeckModel::DeckModel(const CardDB& db) : db_(db), builder_(db) {
    if(const char* raw=std::getenv("RIFTBOUND_FORMAT_PRIOR_IDS"))
        format_ids_=parseFormatIds(db,raw);
    auto filter=[&](std::vector<CardDefId>& ids){
        ids.erase(std::remove_if(ids.begin(),ids.end(),[&](CardDefId id){return !permits(id);}),ids.end());
    };""")
    s=once(s,"if (!d->banned && !d->isTokenCard() && isMainDeckType(*d))","if (permits(d->id) && !d->banned && !d->isTokenCard() && isMainDeckType(*d))")
    s=once(s,"if (!d->banned && !d->isTokenCard() && d->card_type == CardType::Rune)","if (permits(d->id) && !d->banned && !d->isTokenCard() && d->card_type == CardType::Rune)")
    s=once(s,"if (d->card_type != CardType::Legend) continue;","if (d->card_type != CardType::Legend || !permits(d->id)) continue;")
    s=once(s,"        pool.runes = cards->runes;\n        fillHidden(pool);","""        pool.runes = cards->runes;
        filter(pool.cards);
        for(auto& runes:pool.runes)filter(runes);
        pool.runes.erase(std::remove_if(pool.runes.begin(),pool.runes.end(),
            [](const auto& runes){return runes.empty();}),pool.runes.end());
        fillHidden(pool);""")
    s=once(s,"    return it == pools_.end() ? any_ : it->second;","""    if(formatRestricted() && it==pools_.end())
        throw std::logic_error("no opponent pool for public format legend");
    return it == pools_.end() ? any_ : it->second;""")
    p.write_text(s)
    p=root/"src/agents/determinizer.cpp"
    s=once(p.read_text(),"#include <tuple>","#include <tuple>\n#include <stdexcept>")
    s=once(s,"            const std::vector<CardDefId>& list = from.empty() ? model_.any().cards : from;","""            if(model_.formatRestricted() && from.empty())
                throw std::logic_error("no eligible public-format cards for hidden slot");
            const std::vector<CardDefId>& list = from.empty() ? model_.any().cards : from;""")
    s=once(s,"        const auto& rune_lists = pool.runes.empty() ? model_.any().runes : pool.runes;","""        if(model_.formatRestricted() && pool.runes.empty() && !opp_state.rune_deck.empty())
            throw std::logic_error("no eligible public-format rune pool");
        const auto& rune_lists = pool.runes.empty() ? model_.any().runes : pool.runes;""")
    s=once(s,"            if(d.card_type==CardType::Legend && !d.banned &&","            if(model_.permits(id) && d.card_type==CardType::Legend && !d.banned &&")
    s=once(s,"    for (const auto& line : knowledge::check(world)) say(\"knowledge: \" + line);","""    if(model_.formatRestricted()){
        const auto& own=world.player(observer);
        const auto& other=world.player(opp);
        if(own.neeko_legend_choices!=truth.player(observer).neeko_legend_choices)
            say("own private legend registration changed");
        if(other.neeko_revealed_legends!=truth.player(opp).neeko_revealed_legends)
            say("public Neeko history changed");
        if(other.neeko_legend_choices.size()>3)say("too many sampled extra legends");
        std::set<std::string> names;
        if(auto* d=def(DeckModel::legendOf(world,opp)))names.insert(d->name);
        for(auto id:other.neeko_legend_choices){
            const auto* d=def(id);
            if(!model_.permits(id)||!d||d->card_type!=CardType::Legend||!names.insert(d->name).second)
                say("invalid sampled public-format extra legend");
        }
        for(auto id:other.neeko_revealed_legends)
            if(std::find(other.neeko_legend_choices.begin(),other.neeko_legend_choices.end(),id)==other.neeko_legend_choices.end())
                say("public revealed legend missing from sampled pool");
    }
    for (const auto& line : knowledge::check(world)) say("knowledge: " + line);""")
    p.write_text(s)
    p=root/"src/main.cpp"
    s=once(p.read_text(),'#include "rules/deck_validator.h"','#include "rules/deck_validator.h"\n#include "rules/deck_model.h"\n#include <cstdlib>')
    anchor='    std::cout << "P1: " << card_db.get(deck1.legend).name'
    s=once(s,anchor,"""    if(std::getenv("RIFTBOUND_FORMAT_PRIOR_IDS")){
        try{
            DeckModel prior(card_db);
            for(const auto* deck:{&deck1,&deck2}){
                auto require=[&](CardDefId id){
                    if(!prior.permits(id))throw std::invalid_argument("registered identity outside public format prior");
                };
                require(deck->legend);require(deck->chosen_champion);
                for(const auto* list:{&deck->main_deck,&deck->rune_deck,&deck->battlefields,&deck->sideboard,&deck->neeko_legends})
                    for(auto id:*list)require(id);
            }
            if(debug_mode){
                std::cout<<"FORMAT_PRIOR_IDS=";
                bool first=true;
                for(auto id:prior.formatIds()){
                    if(!first)std::cout<<',';
                    std::cout<<id.raw();first=false;
                }
                std::cout<<"\\n";
            }
        }catch(const std::exception& e){
            std::cerr<<"Invalid public format prior: "<<e.what()<<"\\n";return 1;
        }
    }
"""+anchor)
    p.write_text(s)
    p=root/"src/openspiel/openspiel_tests.cpp"
    s=once(p.read_text(),'#include "agents/mcts_agent.h"','#include "agents/mcts_agent.h"\n#include "agents/determinizer.h"\n#include "core/knowledge_view.h"')
    marker="class IsMctsHonestTest : public ::testing::Test {"
    tests=r"""
TEST(NeekoFormatPriorTest, PublicPoolAndActualSampledWorlds){
    using namespace ::riftbound;
    const char* dir=std::getenv("RB_NEEKO_CONTROLLED_DECKS");
    ASSERT_NE(dir,nullptr);
    ASSERT_NE(std::getenv("RIFTBOUND_FORMAT_PRIOR_IDS"),nullptr);
    const std::string prefix=std::string(dir)+"/";
    auto game=::open_spiel::LoadGame("riftbound(deck1="+prefix+"neeko_b.txt,deck2="+prefix+"observer.txt,seed=61051)");
    const auto& rg=static_cast<const RiftboundGame&>(*game);
    const auto& db=rg.cardDb();
    WorldSampler sampler(db);
    const auto& model=sampler.model();
    ASSERT_TRUE(model.formatRestricted());
    for(auto id:{26,77,110,160,168,177,182,183,194,195,242,271,279,280,285,287,343,371,443,521,771,1079})
        EXPECT_FALSE(model.permits(CardDefId{static_cast<uint32_t>(id)}));
    for(const auto& [id,d]:db.all()){
        if(d.card_type!=CardType::Legend || !model.permits(id))continue;
        const auto& p=model.poolFor(id);
        EXPECT_TRUE(p.found);
        for(auto i:p.cards)EXPECT_TRUE(model.permits(i));
        for(auto i:p.hidden)EXPECT_TRUE(model.permits(i));
        for(const auto& runes:p.runes)for(auto i:runes)EXPECT_TRUE(model.permits(i));
    }
    if(!model.permits(CardDefId{315})){
        EXPECT_THROW(model.poolFor(CardDefId{315}),std::logic_error);
        for(uint32_t id=299;id<=322;++id)EXPECT_FALSE(model.permits(CardDefId{id}));
    }
    for(const auto& bad:{"","0","249,","249,249","254,249"," 249","249x","4294967296","999999999","326","110"})
        EXPECT_THROW(DeckModel::parseFormatIds(db,bad),std::invalid_argument)<<bad;
    EXPECT_EQ(DeckModel::parseFormatIds(db,"249,254").size(),2u);
    EventBus bus;GameEngine engine(db,bus,rg.cardRegistry());
    engine.beginGame(rg.deck1(),rg.deck2(),61051);
    const auto& truth=engine.state();
    int worlds=0,unknown=0;
    for(auto observer:{PlayerId::Player1,PlayerId::Player2}){
        knowledge::GameKnowledgeView view(truth,observer);
        for(unsigned seed=1;seed<=32;++seed){
            auto w=truth;std::mt19937_64 rng(seed);
            sampler.sample(w,observer,rng);
            EXPECT_TRUE(sampler.check(truth,w,observer).empty())<<seed;
            const auto& opp=w.player(opponent(observer));
            for(const auto* list:{&opp.hand,&opp.main_deck,&opp.rune_deck}){
                for(auto id:*list)if(!view.about(id).identity_known){
                    ++unknown;EXPECT_TRUE(model.permits(w.getObject(id).card_def_id));
                }
            }
            for(auto id:opp.neeko_legend_choices)EXPECT_TRUE(model.permits(id));
            ++worlds;
        }
    }
    EXPECT_EQ(worlds,64);EXPECT_GT(unknown,0);
    RecordProperty("worlds_checked",worlds);
    RecordProperty("unknown_slots_checked",unknown);
    RecordProperty("allowed_identities",static_cast<int>(model.formatIds().size()));
}
"""
    p.write_text(once(s,marker,tests+"\n"+marker))
    print("FORMAT_AWARE_PRIOR_PATCH_APPLIED")
if __name__=="__main__":
    apply(Path("alpharune"))
