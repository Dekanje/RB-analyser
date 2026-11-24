"""OpenSpiel native search-summary plus deterministic legal-play regression."""
from pathlib import Path
from apply_elnuk_errata import once
def apply(root):
    p=root/"tests/cards/test_radiance_final64.cpp"
    s=p.read_text()
    s=once(s,"state.player(P1).neeko_legend_choices={CardDefId{258}};","state.player(P1).neeko_legend_choices={CardDefId{259}};")
    p.write_text(s)
    p=root/"src/openspiel/openspiel_tests.cpp"
    s=p.read_text()
    marker="class IsMctsHonestTest : public ::testing::Test {"
    tests=r"""
// Test-only controlled exposure: start from validated registered games.
// Actual observer searches occur on natural parked main-phase decisions.
// The later positive play is a synthetic snapshot with a funded hand; do
// not claim this snapshot is a naturally reached tournament position.
struct NeekoControlResult {
    std::vector<std::vector<int64_t>> histories;
    std::vector<::riftbound::SearchSummary> searches;
    std::vector<std::vector<Intent>> legal;
    ::riftbound::CardDefId granted=::riftbound::kInvalidId;
    int64_t worlds=0;
};
NeekoControlResult controlledNeeko(const std::string& owner_deck,const std::string& observer_deck,
                                    bool owner_p1,uint64_t seed) {
    using namespace ::riftbound;
    const auto owner=owner_p1?PlayerId::Player1:PlayerId::Player2;
    const auto observer=opponent(owner);
    const std::string d1=owner_p1?owner_deck:observer_deck;
    const std::string d2=owner_p1?observer_deck:owner_deck;
    auto game=::open_spiel::LoadGame("riftbound(deck1="+d1+",deck2="+d2+",seed="+std::to_string(seed)+")");
    const auto& rg=static_cast<const RiftboundGame&>(*game);
    if(!DeckValidator(rg.cardDb()).validate(rg.deck1()).is_legal ||
       !DeckValidator(rg.cardDb()).validate(rg.deck2()).is_legal)
        throw std::logic_error("controlled deck invalid");
    IsMctsAgent agent(d1,d2,"ignored",seed,seed*31+7,24,IsMctsAgent::WorldModel::Sampled);
    agent.setCheckWorlds(true);
    PasserAgent passer;
    EventBus bus;
    GameEngine engine(rg.cardDb(),bus,rg.cardRegistry());
    auto step=engine.beginGame(rg.deck1(),rg.deck2(),seed);
    NeekoControlResult out;
    std::optional<GameState> owner_main;
    // Passive scripted actual actions preserve comparability and leave
    // the searcher free to compute a real policy without applying it.
    for(int n=0;n<180 && step.kind==StepKind::NeedDecision;++n){
        const auto& st=engine.state();
        if(GameEngine::isResumableDecision(st,step.legal)){
            if(step.perspective==owner && !owner_main)owner_main=st;
            if(step.perspective==observer && step.legal.size()>1 && out.searches.size()<3){
                auto choice=agent.selectAction(st,step.legal);
                if(std::find(step.legal.begin(),step.legal.end(),choice)==step.legal.end())
                    throw std::logic_error("search chose illegal action");
                const auto& summary=agent.lastSearch();
                if(!summary.searched || summary.simulations!=24)
                    throw std::logic_error("expected actual sampled search");
                out.histories.push_back(st.action_history);
                out.legal.push_back(step.legal);
                out.searches.push_back(summary);
            }
        }
        if(owner_main && out.searches.size()==3)break;
        auto pass=passer.selectAction(st,step.legal);
        auto it=std::find(step.legal.begin(),step.legal.end(),pass);
        if(it==step.legal.end())throw std::logic_error("passer illegal");
        step=engine.applyChoice(static_cast<int>(it-step.legal.begin()));
    }
    out.worlds=agent.worldsChecked();
    if(!owner_main || out.searches.size()!=3)
        throw std::logic_error("missing controlled main-phase checkpoints");
    // Replay a legal Neeko PlayCard intent from a separate funded owner
    // main-phase snapshot. No fabricated grant and no direct trigger call.
    EventBus play_bus;
    GameEngine play(rg.cardDb(),play_bus,rg.cardRegistry());
    play.mutableState()=*owner_main;
    play.testHook_setAgents(&passer,&passer);
    auto& state=play.mutableState();
    auto& ps=state.player(owner);
    auto is_neeko=[&](GameObjectId id){return state.getObject(id).card_def_id==CardDefId{1131};};
    if(std::none_of(ps.hand.begin(),ps.hand.end(),is_neeko)){
        auto it=std::find_if(ps.main_deck.begin(),ps.main_deck.end(),is_neeko);
        if(it==ps.main_deck.end())throw std::logic_error("Neeko absent from diagnostic deck");
        std::iter_swap(it,std::prev(ps.main_deck.end()));
        play.testHook_drawCards(owner,1);
    }
    ps.rune_pool.energy=6;
    ps.rune_pool.universal_power=1;
    auto legal=play.generateLegalActions();
    auto it=std::find_if(legal.begin(),legal.end(),[&](const Intent& i){
        return i.type==IntentType::PlayCard && state.objectExists(i.card) && is_neeko(i.card);
    });
    if(it==legal.end())throw std::logic_error("funded Neeko was not legally playable");
    auto intent=*it;
    play.testHook_executeIntent(intent);
    play.testHook_runChain();
    play.testHook_cleanup();
    play.testHook_runChain();
    const auto& grants=state.player(owner).neeko_granted_legends;
    if(grants.size()!=1 || !state.objectExists(grants.front().legend))
        throw std::logic_error("native legal play did not resolve a legend grant");
    out.granted=state.getObject(grants.front().legend).card_def_id;
    return out;
}
TEST(NeekoControlledAgentTest, SameSampledSearchAndDistinctLegalPlayBothSeats){
    using namespace ::riftbound;
    const char* dir=std::getenv("RB_NEEKO_CONTROLLED_DECKS");
    ASSERT_NE(dir,nullptr);
    const std::string prefix=std::string(dir)+"/";
    int searched=0;
    int64_t worlds=0;
    for(bool owner_p1:{true,false}){
        const uint64_t seed=owner_p1?61041:61042;
        auto a=controlledNeeko(prefix+"neeko_a.txt",prefix+"observer.txt",owner_p1,seed);
        auto b=controlledNeeko(prefix+"neeko_b.txt",prefix+"observer.txt",owner_p1,seed);
        ASSERT_EQ(a.histories,b.histories);
        ASSERT_EQ(a.legal,b.legal);
        ASSERT_EQ(a.searches.size(),3u);
        ASSERT_EQ(b.searches.size(),3u);
        for(size_t i=0;i<a.searches.size();++i){
            const auto& x=a.searches[i];const auto& y=b.searches[i];
            EXPECT_TRUE(x.searched && y.searched);
            EXPECT_EQ(x.chosen,y.chosen);
            EXPECT_EQ(x.visits,y.visits);
            EXPECT_EQ(x.value,y.value);
            EXPECT_EQ(x.root_value,y.root_value);
            EXPECT_EQ(x.simulations,y.simulations);
            ++searched;
        }
        EXPECT_EQ(a.worlds,72);
        EXPECT_EQ(b.worlds,72);
        worlds+=a.worlds+b.worlds;
        EXPECT_EQ(a.granted,CardDefId{249});
        EXPECT_TRUE(b.granted==CardDefId{254} || b.granted==CardDefId{256} || b.granted==CardDefId{259});
        EXPECT_NE(a.granted,b.granted);
        RecordProperty(owner_p1?"p1_a_grant":"p2_a_grant",static_cast<int>(a.granted.raw()));
        RecordProperty(owner_p1?"p1_b_grant":"p2_b_grant",static_cast<int>(b.granted.raw()));
    }
    RecordProperty("paired_searches",searched);
    RecordProperty("worlds_checked",static_cast<int>(worlds));
}
"""
    p.write_text(once(s,marker,tests+"\n"+marker))
    print("NEEKO_CONTROLLED_AGENT_TESTS_APPLIED")
if __name__=="__main__":
    apply(Path("alpharune"))
