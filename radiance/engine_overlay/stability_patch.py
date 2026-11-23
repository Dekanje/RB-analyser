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


# Keep Convergent Mutation's existing two-stage play-target contract: one
# target in the intent, another in its pre-play finalize choice. The tested
# contract is necessary for chain-response semantics and the pinned C++
# regression tests. Filter each *first* target by whether a COMPLETE,
# affordable second-target choice exists before offering that play.
header = ENGINE / "src/engine/game_engine.h"
replace_once(header,
    """    bool prePlayProbe(PlayerId player, GameObjectId card_id,
                      const PlayerState::TrashReplayGrant* grant);""",
    """    bool prePlayProbe(PlayerId player, GameObjectId card_id,
                      const PlayerState::TrashReplayGrant* grant,
                      const std::vector<GameObjectId>& initial_targets = {});""")
replace_once(engine,
    """bool GameEngine::prePlayProbe(PlayerId player, GameObjectId card_id,
                              const PlayerState::TrashReplayGrant* grant) {""",
    """bool GameEngine::prePlayProbe(PlayerId player, GameObjectId card_id,
                              const PlayerState::TrashReplayGrant* grant,
                              const std::vector<GameObjectId>& initial_targets) {""")
replace_once(engine,
    """    pre.pre_play_choices = true;
    // The grant, if any, is looked up again in each run:""",
    """    pre.pre_play_choices = true;
    pre.targets = initial_targets;
    // The grant, if any, is looked up again in each run:""")
replace_once(engine,
    """    effect_executor_->setChoiceFilter([this, player, card_id, via_grant](GameObjectId t) {
        std::vector<GameObjectId> all;
        if (state_.chain.resuming.has_value()) all = state_.chain.resuming->chosen_objects;
        all.push_back(t);
        std::vector<GameObjectId> unpaid = {t};""",
    """    effect_executor_->setChoiceFilter([this, player, card_id, via_grant, initial_targets](GameObjectId t) {
        std::vector<GameObjectId> all;
        if (state_.chain.resuming.has_value()) all = state_.chain.resuming->chosen_objects;
        all.push_back(t);
        for (auto pt : initial_targets)
            if (std::find(all.begin(), all.end(), pt) == all.end()) all.push_back(pt);
        std::vector<GameObjectId> unpaid = initial_targets;
        unpaid.push_back(t);""")
replace_once(engine,
    """    const PrePlayPayable payable = [this, player, card_id, via_grant](
                                       const std::vector<GameObjectId>& chosen) {
        const auto* g = via_grant ? trashGrantFor(player, card_id) : nullptr;
        if (via_grant) return g && canPayTrashGrant(player, card_id, *g, chosen, {});
        return chosen.empty() ? canAfford(player, card_id)
                              : canAffordChoosing(player, card_id, chosen, {});
    };""",
    """    const PrePlayPayable payable = [this, player, card_id, via_grant, initial_targets](
                                       const std::vector<GameObjectId>& chosen_in) {
        std::vector<GameObjectId> chosen = chosen_in;
        for (auto pt : initial_targets)
            if (std::find(chosen.begin(), chosen.end(), pt) == chosen.end()) chosen.push_back(pt);
        const auto* g = via_grant ? trashGrantFor(player, card_id) : nullptr;
        if (via_grant) return g && canPayTrashGrant(player, card_id, *g, chosen, initial_targets);
        return chosen.empty() ? canAfford(player, card_id)
                              : canAffordChoosing(player, card_id, chosen, initial_targets);
    };""")
replace_once(engine,
    """            for (auto& tset : spellTargetSets(spell_card, state_, player, req, legal_targets)) {
                if (!affordableChoosing(tset)) continue;
                Intent play;""",
    """            for (auto& tset : spellTargetSets(spell_card, state_, player, req, legal_targets)) {
                if (!affordableChoosing(tset)) continue;
                // Convergent Mutation chooses a second distinct unit in a
                // finalize pass. Its first target alone being affordable does
                // not prove the full spell is playable (CR 355.8).
                if (card.name == "Convergent Mutation" &&
                    !state_.chain.resuming.has_value() &&
                    !const_cast<GameEngine*>(this)->prePlayProbe(player, card_id, nullptr, tset))
                    continue;
                Intent play;""")

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
            if ((n == "Mesmerize" || n == "Rocket Barrage" || n == "One-Two Punch") &&
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

# Fail closed with a descriptive engine error if a Boost fiber continuation is
# invalid, instead of jumping through a null stack/context pointer (SIGSEGV).
# These checks do not produce or alter results from successful game actions.
replace_once(step,
    """    yield_target_ = std::move(yield_target_).resume();

    at_decision_ = false;""",
    """    if (!yield_target_)
        throw std::logic_error("StepDriver::selectActionFor: no caller fiber continuation");
    yield_target_ = std::move(yield_target_).resume();

    at_decision_ = false;""")
replace_once(step,
    """    engine_fiber_ = std::move(engine_fiber_).resume();
}

void StepDriver::markDone()""",
    """    if (!engine_fiber_)
        throw std::logic_error("StepDriver::provideChoice: engine fiber continuation missing");
    engine_fiber_ = std::move(engine_fiber_).resume();
}

void StepDriver::markDone()""")

# CRITICAL: Boost.Context's forced_unwind exception must never be suppressed.
# StepDriver::~StepDriver destroys parked speculative ISMCTS clone fibers by
# unwinding. Mordekaiser's immediate [Add] ability enters probeAdds(), whose
# two catch-all handlers previously swallowed forced_unwind and corrupted the
# suspended fiber continuation (observed jump_fcontext with RSP=0).
# Preserve the documented handling of regular probe failures, but rethrow
# forced_unwind in both handlers. All genuine game outcomes remain unchanged.
replace_once(
    engine,
    '#include "game_engine.h"',
    '#include "game_engine.h"\n#include <boost/context/fiber.hpp>'
)
replace_once(
    engine,
    """                    reached = search(depth + 1);
                } catch (...) {
                    reached = false;
                }
                state_ = std::move(saved);""",
    """                    reached = search(depth + 1);
                } catch (const boost::context::detail::forced_unwind&) {
                    throw;  // destroying parked ISMCTS fibers must unwind
                } catch (...) {
                    reached = false;
                }
                state_ = std::move(saved);"""
)
replace_once(
    engine,
    """            ok = search(0);
        } catch (...) {
            ok = false;
        }
        if (effect_executor_->hasPendingChoice())""",
    """            ok = search(0);
        } catch (const boost::context::detail::forced_unwind&) {
            throw;  // cannot continue from a destroyed caller context
        } catch (...) {
            ok = false;
        }
        if (effect_executor_->hasPendingChoice())"""
)

print("PINNED_ISMCTS_STABILITY_PATCH_APPLIED", EXPECTED)
