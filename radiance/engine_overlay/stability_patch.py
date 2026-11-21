#!/usr/bin/env python3
"""Reproducible, version-pinned engine *stability* patch for ISMCTS replay.

This touches only a disposable checkout at AlphaRune's pinned commit. It does
not skip matches, change decks, invent winners, or catch/discard rule failures.

The two observed failures motivating this patch were:
1. SIGSEGV in boost::context::jump_fcontext (Mordekaiser, 438 prior SIGSEGV
   series). Increase the protected fiber stack's reserved headroom and keep
   guard-page detection; validate the crashing seeds independently.
2. An otherwise affordable Convergent Mutation play chose an unaffordable
   second target when its finalize phase skipped the viability pass. Force
   the existing engine's *payable choice search* for this targeted spell.
   It must not convert an unpayable action into a game win.
"""
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
ENGINE = ROOT / "alpharune"
EXPECTED = "ec90f0fed002aed374d06249fa95e83e3cfbd386"
sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ENGINE, text=True).strip()
if sha != EXPECTED:
    raise SystemExit("Refusing stability patch on unverified engine commit " + sha)

def replace_once(path, old, new):
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"Expected unique pinned-source anchor in {path}: {count} occurrences")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")

step = ENGINE / "src/engine/step_driver.cpp"
replace_once(
    step,
    "constexpr size_t kFiberStackBytes = 256 * 1024;",
    "// ISMCTS can explore much deeper stacked finalize/trigger paths than the\n"
    "// older engine's 256 KiB fiber. The guard page is retained: a remaining\n"
    "// overflow is still a hard failure, never silently a simulated win.\n"
    "constexpr size_t kFiberStackBytes = 2 * 1024 * 1024;"
)
engine = ENGINE / "src/engine/game_engine.cpp"
replace_once(
    engine,
    "done = too_dear ? choosePrePlayViable(pre, payable)\n"
    "                                : collectFinalizeChoices(std::move(pre));",
    "// Convergent Mutation chooses a second target before paying, and\n"
    "// its Deflect/target-dependent costs must stay payable after *all*\n"
    "// choices. The regular fast finalize path can pick an unaffordable\n"
    "// second target even when the original play was affordable. Retain\n"
    "// the existing exact viable-sequence filtering for this spell.\n"
    "const bool requires_complete_viability =\n"
    "    state_.objectExists(what) &&\n"
    "    state_.getObject(what).name.get() == \"Convergent Mutation\";\n"
    "done = (too_dear || requires_complete_viability)\n"
    "           ? choosePrePlayViable(pre, payable)\n"
    "           : collectFinalizeChoices(std::move(pre));"
)
# Modes must be validated against *all* legal target types, not merely the
# first printed mode. Otherwise a valid choice can be offered and then fail
# with "no legal choice for a required target" when the first mode is empty.
mesmerize = ENGINE / "src/cards/spells/0839_mesmerize.cpp"
replace_once(
    mesmerize,
    "return friendlyUnitChoice(state, controller, object);",
    "const auto legal = chooseableUnits(state, controller,\n"
    "    [](const GameObject&) { return true; });\n"
    "return std::find(legal.begin(), legal.end(), object) != legal.end()\n"
    "    ? FinalizeChoice::Yes : FinalizeChoice::No;"
)
rocket = ENGINE / "src/cards/spells/0400_rocket_barrage.cpp"
replace_once(
    rocket,
    "return friendlyUnitChoice(state, controller, object,\n"
    "            [&](const GameObject& u) {\n"
    "                return u.isAtBase();\n"
    "            });",
    "const auto units = unitsInBases(state, controller);\n"
    "const auto gear = gearOnBoard(state, controller);\n"
    "return (std::find(units.begin(), units.end(), object) != units.end() ||\n"
    "        std::find(gear.begin(), gear.end(), object) != gear.end())\n"
    "    ? FinalizeChoice::Yes : FinalizeChoice::No;"
)


# Convergent Mutation has TWO chosen friendly units. The old engine used
# one play-intent target and another finalize target, leaving target payment
# validation split across paths. Use the same complete *pair* selection
# machinery used for other two-target spells (all choices before cost).
mutation = ENGINE / "src/cards/spells/0108_convergent_mutation.cpp"
replace_once(
    mutation,
    """    void onResolve(CardContext& ctx, const std::vector<GameObjectId>& targets) override {
        const GameObjectId chosen = targets.empty() ? kInvalidId : targets[0];
        const auto other = selectTargetOrNone(*this, ctx, "Convergent Mutation (copy Might from)",
                                              friendlyUnits(ctx.state, ctx.controller, chosen),
                                              7, /*allow_none=*/false);
        if (!other.has_value()) return;          // waiting for the agent
        if (finalizingChoices(ctx)) return;      // choices end here (CR 355)
        // Either target no longer legal: that instruction is ignored (CR
        // 359.3.e.5), and it has nothing else to do.
        if (chosen == kInvalidId || *other == kInvalidId) return;
        if (!ctx.state.objectExists(chosen) || !ctx.state.objectExists(*other)) return;
        const int target_might = ctx.state.getObject(*other).current_might;""",
    """    bool needsPlayTimeTargetPair() const override { return true; }
    void onResolve(CardContext& ctx, const std::vector<GameObjectId>&) override {
        const auto own = friendlyUnits(ctx.state, ctx.controller, kInvalidId);
        const auto options = [&](GameObjectId chosen) {
            return friendlyUnits(ctx.state, ctx.controller, chosen);
        };
        auto [chosen, other] = pickTargetPair(ctx, "Convergent Mutation", own, options);
        if (finalizingChoices(ctx)) return;
        if (chosen == kInvalidId || other == kInvalidId) return;
        if (!ctx.state.objectExists(chosen) || !ctx.state.objectExists(other)) return;
        const int target_might = ctx.state.getObject(other).current_might;"""
)
replace_once(mutation,
    "return TargetRequirements{.count = 1, .must_be_unit = true, .must_be_friendly = true};",
    "return TargetRequirements{.count = 2, .must_be_unit = true, .must_be_friendly = true};")

# For two-mode spells, an affordable printed cost alone does not guarantee
# any complete payable target sequence. Use the engine's exact pre-play probe
# before offering such cards rather than allowing impossible moves that crash.
replace_once(
    engine,
    """        if (req.count == 0) {
            // No play-time target. A spell that chooses in its finalize pass""",
    """        if (req.count == 0) {
            // Multi-mode spells must have at least one complete payable mode
            // and target before the action is offered. Use the pre-existing
            // exact choice probe (not a guessed victory, and never a bypass).
            // A chain-resuming context cannot be probed by this engine; its
            // normal finalization legality path remains in place there.
            const auto& n = card.name.get();
            if ((n == "Mesmerize" || n == "Rocket Barrage") &&
                !state_.chain.resuming.has_value() &&
                !payableThroughAFinalizeChoice(player, card_id, nullptr, true))
                continue;
            // No play-time target. A spell that chooses in its finalize pass""")

# Prevent deep or cyclic information-set search paths from recursing into
# a host stack fault. A horizon cutoff estimates the value of the genuine
# reached engine position using the existing ISMCTS evaluator; it does not
# assign a fabricated match winner or classify failed games as completed.
search = ENGINE / "src/agents/mcts_agent.cpp"
replace_once(search, "const std::vector<double> returns = simulate(world);",
             "const std::vector<double> returns = simulate(world, 0);")
replace_once(search,
    """    std::vector<double> simulate(::open_spiel::State& state) {
        if (state.IsTerminal()) return state.Returns();

        const std::vector<::open_spiel::Action> legal = state.LegalActions();""",
    """    std::vector<double> simulate(::open_spiel::State& state, int depth) {
        if (state.IsTerminal()) return state.Returns();
        // Search cutoff only: real games continue and determine all wins.
        if (depth >= 128) return evaluator_->Evaluate(state);

        const std::vector<::open_spiel::Action> legal = state.LegalActions();""")
replace_once(search,
    """        state.ApplyAction(chosen);
        std::vector<double> returns = simulate(state);
        node.children[chosen].return_sum += returns[player];""",
    """        state.ApplyAction(chosen);
        std::vector<double> returns = simulate(state, depth + 1);
        node.children[chosen].return_sum += returns[player];""")

print("PINNED_ISMCTS_STABILITY_PATCH_APPLIED", EXPECTED)
