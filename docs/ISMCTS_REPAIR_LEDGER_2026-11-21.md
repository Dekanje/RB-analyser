# ISMCTS engine repair — evidence ledger (21 November 2026)

## Goal

Run all 58 legally corrected Riftbound legend decks in 1,711 fixed-deck
pairings including mirrors, 20 ISMCTS-vs-ISMCTS BO3 series per pairing:
**34,220 actual series**, no imputed wins or excluded legends.

The current engine uses pinned `chorlick/alpharune@ec90f0fed002aed374d06249fa95e83e3cfbd386`
plus the isolated Radiance C++ overlay. Results are not tournament BO3 because
sideboard swaps between games are not implemented, and the full Radiance set
is not mechanically implemented.

## Prior run postmortem

[Prior failed full run #44900171748](https://github.com/Dekanje/RB-analyser/actions/runs/44900171748)

- 34,220 scheduled; 33,664 complete; **556 incomplete**.
- 438 process crashes `SIGSEGV (-11)`.
- 88 Convergent Mutation invalid payable target decisions.
- 27 Mesmerize incomplete required target decisions.
- 3 Rocket Barrage incomplete required target decisions.

[Signature audit #44932628360](https://github.com/Dekanje/RB-analyser/actions/runs/44932628360)
retains failed series and exact seeds.

## Proven behavior

- [First repair run #44932743894](https://github.com/Dekanje/RB-analyser/actions/runs/44932743894)
  showed 116/116 legal-deck game smoke tests but failed the strict crash-seed gate.
- [Second repair run #44933842004](https://github.com/Dekanje/RB-analyser/actions/runs/44933842004)
  completed all six known Seraphine/other spell error seeds; five Mordekaiser seeds still
  crashed. Its experimental Convergent Mutation target-pair refactor altered behavior
  and failed 2/3,638 C++ regression tests. The refactor was reverted.
- [Restored-targeting regression #44934944711](https://github.com/Dekanje/RB-analyser/actions/runs/44934944711)
  **PASS 3,638/3,638** enabled tests with source-compatible pre-play target probes.
- [Third strict replay #44934944704](https://github.com/Dekanje/RB-analyser/actions/runs/44934944704)
  again showed all six known spell error seeds complete, but five Mordekaiser seeds
  still crashed. No all-field simulation results were produced.
- [Search-budget isolation #44934124678](https://github.com/Dekanje/RB-analyser/actions/runs/44934124678)
  showed one Mordekaiser–Azir seed passes at ISMCTS budgets 1, 2, 4, 8 and 12
  but crashes at 24. This does not justify lowering the benchmark's budget.
- [World-model isolation #44934465355](https://github.com/Dekanje/RB-analyser/actions/runs/44934465355)
  confirmed Mordekaiser–Azir crashes at 24 ISMCTS sims with both sampled and
  perfect information; different MCTS implementation completed that seed.
- [Seat isolation #44934603657](https://github.com/Dekanje/RB-analyser/actions/runs/44934603657)
  localized the Mordekaiser–Azir crash to Mordekaiser controlling the ISMCTS
  searching seat in this test.
- [GDB #44933693367](https://github.com/Dekanje/RB-analyser/actions/runs/44933693367)
  reaches `boost::context::jump_fcontext` with a null-looking continuation.
- [AddressSanitizer #44934287276](https://github.com/Dekanje/RB-analyser/actions/runs/44934287276)
  independently reproduces stack-overflow diagnostics at `jump_fcontext` for Mordekaiser;
  the sanitizer does not establish whether invalid continuation, recursion, or
  an abandoned-fiber unwinding violation originated the problem.
- **Concrete source defect identified:** `StepDriver::~StepDriver` requires
  `boost::context::detail::forced_unwind` to propagate when destroying an
  abandoned search clone. Two catch-all handlers in `GameEngine::probeAdds`
  suppressed that very exception, potentially resuming a dead fiber. Patch
  `e191491e` rethrows `forced_unwind` in both handlers, keeping regular error
  handling unchanged. Exact-seed replay and regression validation on that
  version are pending; do not claim the crash cured before they pass.
- [Trace #44935091188](https://github.com/Dekanje/RB-analyser/actions/runs/44935091188)
  records gameplay before the failure, not a definitive causal frame.

## Current source changes

Changes are version-gated and applied to an ephemeral pinned checkout:
`radiance/engine_overlay/stability_patch.py` and the narrowly scoped
`Twice Slain` card overlay. Includes guarded Boost context resumes,
target-affordability probes and multi-mode spell legal target checks,
a larger protected fiber stack, an ISMCTS search depth cutoff, and nested
death-replacement reentrancy protection. The last three measures are
*not demonstrated to cure* the Mordekaiser fault; don't claim otherwise.

## Acceptance criteria — strict, non-negotiable

1. Original 58 roster passes legality plus 116/116 seat smoke tests.
2. Previously failing exact-seed games, including Mordekaiser and Seraphine,
   all finish without exceptions, SIGSEGV or timeouts at **ISMCTS sims=24**.
3. Full C++ regression suite passes, without removing tests or changing
   tested printed card semantics.
4. Launch 64-shard full matrix on same exact version and selected legal roster.
5. Aggregator requires every one of 1,711 matchup keys and 34,220 completed
   BO3 series. Do not turn failures into draws or wins. Do not publish the
   previous random-agent rates as ISMCTS win rates.

## Reproduction workflows

- [Active repair and full field gate](https://github.com/Dekanje/RB-analyser/actions/workflows/ismcts-stability-58-full.yml)
- [Mechanics regression](https://github.com/Dekanje/RB-analyser/actions/workflows/ismcts-stability-regression.yml)
- [AddressSanitizer](https://github.com/Dekanje/RB-analyser/actions/workflows/ismcts-sanitizer-replay.yml)
