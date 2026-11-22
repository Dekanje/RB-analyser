#!/usr/bin/env python3
"""Wave 1 regression repair against pinned AlphaRune, applied to disposable checkout.

Never changes upstream or production history. Maintains the two old baseline
test invariants when the compiled pool is exactly 988; adds the 993-card
snapshot explicitly and addresses a repeat-spell playability bug exposed by
the expanded fuzz deck pool.
"""
import pathlib

root = pathlib.Path(__file__).resolve().parents[2]
engine = root / "alpharune"

def replace_once(relative, old, new):
    p = engine / relative
    text = p.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise SystemExit(f"Unexpected pinned-source anchor count ({text.count(old)}): {relative} :: {old[:100]}")
    p.write_text(text.replace(old, new, 1), encoding="utf-8")

# The prior 988-card regression counted 28 lethal-helper sites across C++
# cards. Wave 1 adds exactly two more in a new card source (Supernova,
# Avalanche). Do not turn off the scan or silently drop any assertions.
replace_once(
    "tests/test_review_fix_perf_engine.cpp",
    "    EXPECT_EQ(helper, 28);   // 22 baseline + 6 explicit Radiance helper call sites",
    "    EXPECT_EQ(helper, 30);   // 28 verified 988-card sites + Supernova and Avalanche (Wave 1)"
)

# A pinned seed is a snapshot of the FULL registered pool. A new set changes
# deterministic decks, even when RandomDeckBuilder remains deterministic.
# Preserve the old snapshot for the old-sized registry and explicitly add the
# measured 993-card snapshot. Future waves must explicitly refresh this test.
replace_once(
    "tests/test_deck_fuzz.cpp",
    '''    constexpr uint64_t kRadiance988DeckOfSeedOne = 10066350758104723585ull;
    const uint64_t expected = registry_->size()==988
        ? kRadiance988DeckOfSeedOne : kDeckOfSeedOne;
    EXPECT_EQ(h, expected) << "the deck of seed 1 changed: h = " << h;''',
    '''    constexpr uint64_t kRadiance988DeckOfSeedOne = 10066350758104723585ull;
    constexpr uint64_t kRadiance993DeckOfSeedOne = 5259447031096685743ull;
    const uint64_t expected = registry_->size()==993 ? kRadiance993DeckOfSeedOne
                             : registry_->size()==988 ? kRadiance988DeckOfSeedOne
                             : kDeckOfSeedOne;
    EXPECT_EQ(h, expected) << "the deck of seed 1 changed for registry "
                           << registry_->size() << ": h = " << h;'''
)

# Comparing the number of decisions in ONE randomly generated game is a
# stochastic coincidence, not evidence that the two different agents use the
# same policy. Compare several deterministic seeds and both outcome and count.
# Keep the reproducibility checks of the selected player agent.
replace_once(
    "tests/test_random_player_agent.cpp",
    "    EXPECT_NE(player.decisions, random.decisions);",
    """    bool agents_differ = player.decisions != random.decisions ||
                         player.winner != random.winner;
    for (uint64_t seed : {uint64_t{32}, uint64_t{33}, uint64_t{34}, uint64_t{35}}) {
        if (agents_differ) break;
        const auto baseline = fuzz::playGame(db, registry, a, b, seed);
        const auto randomized = fuzz::playGame(db, registry, a, b, seed, opt);
        ASSERT_FALSE(randomized.failed) << randomized.termination
                                         << " " << randomized.exception;
        agents_differ |= randomized.decisions != baseline.decisions ||
                         randomized.winner != baseline.winner;
    }
    EXPECT_TRUE(agents_differ) << "two distinct policies matched five deterministic game outcomes";"""
)

# Rocket Barrage (an existing, not Radiance, card) has a required choice
# determined at spell finalization. When random expanded-pool games reach a
# position with no complete affordable mode+target, a nominal hand-play offer
# must not be emitted. The same dry-run guard already used for spells that
# might have Deflect is applied here even if there is no Deflect.
# Unlike swallowing the executePlaySpell exception, this fixes the action gate.
replace_once(
    "src/engine/game_engine.cpp",
    """            if (afford_plain && spell_card &&
                (spell_card->choicesAtFinalization() & Card::kFinalizeResolve) &&
                !spell_card->needsPlayTimeTarget() && anyDeflectFor(player) &&
                !payableThroughAFinalizeChoice(player, card_id, nullptr, true))
                continue;""",
    """            if (afford_plain && spell_card &&
                (spell_card->choicesAtFinalization() & Card::kFinalizeResolve) &&
                !spell_card->needsPlayTimeTarget() &&
                (anyDeflectFor(player) ||
                 card.card_def_id == CardDefId{400} /* Rocket Barrage: required mode+target */) &&
                !payableThroughAFinalizeChoice(player, card_id, nullptr, true))
                continue;"""
)
print("WAVE1_REGRESSION_PATCH_APPLIED: 2 pinned fixture adjustments, 1 robust agent test, Rocket Barrage playability gate")
