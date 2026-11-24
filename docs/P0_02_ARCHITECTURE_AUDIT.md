# P0-02 — Architecture, build and deterministic-input audit
2026-11-24. Inspected active head 5e46b528ce31059523d3f5dbc11a6a96e68b07e6, upstream AlphaRune ec90f0fed002aed374d06249fa95e83e3cfbd386, corrected build workflow and the actual historical archive bytes. No runtime or historical deck mutation. This is a source/evidence audit, not fresh rules certification.

## Source-to-binary chain
- [Corrected build workflow](../.github/workflows/competitive-guidebot-native-qa.yml) at c35ceffa290056764df410ea38f97e01f2654031, [run 45282108093](https://github.com/Dekanje/RB-analyser/actions/runs/45282108093).
- Ubuntu 24.04, C++20, CMake >=3.20, Ninja Release, three build jobs, ccache; native Boost program_options/filesystem/system/context, nlohmann-json, Threads; GoogleTest v1.14.0 fetched by CMake. System package/compiler versions are not fully locked by the workflow. OpenSpiel v1.6.14 and its pinned dependencies and LibTorch 2.5.1 have conditional build paths; actual resolved flags and dependency SHAs must be captured from a fresh configure, not inferred from optional CMake code.
- Exact upstream [CMakeLists.txt](https://github.com/chorlick/alpharune/blob/ec90f0fed002aed374d06249fa95e83e3cfbd386/CMakeLists.txt). Clone AlphaRune to alpharune/ at the pinned commit; apply the workflow's 16 Python overlay scripts in their declared order (apply, wave1_regression_fix, apply_wave2, apply_wave3, apply_wave4, apply_batch6, apply_batch7, apply_batch8, apply_batch9, apply_batch9_battlefields, apply_batch9_disarm_chain, apply_batch10, apply_final64, stability_patch, fullfield_repair, tournament_starting_player). Overlay patch anchors and upstream checks guard against wrong base. Build riftbound and riftbound_tests; dump registry; run native GoogleTest XML and exact seed replay, then validate registry. See workflow for commands. This is the reproducible recipe, not a verified fresh local build.
- Architecture: DeckValidator parses ordered vectors and enforces registration; GameEngine and StepDriver execute native rules with Boost.Context fibers, effect/trigger/chain subsystems; agents use live observations, mirror/state cloning, determinization and search; Python benchmark invokes a separate native process per game, BO3 wrapper applies legal registered transitions and verifies first-player receipts; optimization and tournament projections are downstream. Agent observation security and policy quality are separate audit tasks.
- Upstream [README](https://github.com/chorlick/alpharune/blob/ec90f0fed002aed374d06249fa95e83e3cfbd386/README.md#license) explicitly states License TBD; no license file found in pinned tree. Do not assume an open-source redistribution grant. Clarify permission before distribution.
- Existing executable archive 14869638175: Linux x86-64 dynamic ELF; ldd in sandbox resolves libboost_program_options.so.1.83.0 but libboost_context.so.1.83.0 is missing. Native replay and fresh build were not executed here. Exact local blocker recorded; install compatible dependencies on authorized Linux/WSL2 or use scoped native CI. Do not substitute a mock for native evidence.
- Previously verified executable and registry hashes and 3916 enabled regression tests remain in [P0-01](P0_01_ARTIFACT_AUDIT.md).

## Root-cause evidence: ordering confound
- [sideboard_deck.py](../scripts/sideboard_deck.py) render_rows sorts each Counter alphabetically; [structural_deck_population.py](../scripts/structural_deck_population.py) uses render_deck for each candidate; Counter equality checks ignore order.
- [tournament_bo3_policy.py](../scripts/tournament_bo3_policy.py) deliberately preserves raw input file in Game 1; same stable_seed(seed,"sideboard_bo3",1) is passed to benchmark. This is correct for identical ordered inputs but not for alphabetically reordered proposals.
- Pinned [deck_validator.cpp](https://github.com/chorlick/alpharune/blob/ec90f0fed002aed374d06249fa95e83e3cfbd386/src/rules/deck_validator.cpp#L275) appends MainDeck/Battlefields/Runes in file order; [game_engine.cpp](https://github.com/chorlick/alpharune/blob/ec90f0fed002aed374d06249fa95e83e3cfbd386/src/engine/game_engine.cpp#L559) instantiates from vectors, shuffles ordered main/rune vectors and publishes battlefield choices as indexed actions. Same seed does not imply same cards/choices if input vectors change. Sideboard is not instantiated by setupPlayer. This is a concrete experimental-input defect; evidence is consistent with serialization rather than direct sideboard RNG coupling. Native controlled replay required before declaring causality fully resolved.

| Ordered playable differences | Training candidates | Training pairs | Training mismatches | Holdout candidates | Holdout pairs | Holdout mismatches |
|---|---:|---:|---:|---:|---:|---:|
| None | 39 | 156 | 0 | 1 | 24 | 0 |
| Battlefields | 69 | 276 | 75 | 7 | 168 | 28 |
| Runes | 12 | 48 | 24 | 1 | 24 | 5 |
| Both | 54 | 216 | 84 | 3 | 72 | 23 |
| Total | 174 | 696 | 183 | 12 | 288 | 56 |

All 174 candidate playable multisets equal their originals; 135 have changed playable order, none change MainDeck order. All 239 winner mismatches are in reordered candidates; 0/180 for preserved ordered sections versus 239/804 for reordered sections. Historical paired observations share candidates/opponents; these are descriptive counts, not independent significance tests.

## Reproduction
Read-only tool: audit/sideboard_order_audit.py; 6/6 local unit tests passed: python -m unittest discover -s audit -p 'test_sideboard_order_audit.py' -v. Full archive audit reproduced the table. It validates manifest candidate hashes, original hashes, playable multisets and receipt joins; it is not a native simulator. Run python audit/sideboard_order_audit.py ORIGINAL.zip STRUCTURAL.zip SCREEN.zip HOLDOUT0.zip ... HOLDOUT11.zip.
Original artifact 14823477036 from run 45181493632 (SHA-256 1cdf59d8cc2c36dde035a142ad09556ee9323cfdbb836488e0c20bd75c09f872); structural 14859277678 from 45259246337 (SHA-256 5e0f451f03a0a886c08bb9d12724224a681f3a7e15901b1ebc8c8d0ee49ad5b6). Both hashes independently matched GitHub metadata. Screen 14870734087 and 12 holdout IDs in P0-01. Preserve raw inputs; do not edit old evidence.

## Required corrective gate P0-02R
1. Add order-preserving serialization for sideboard-only proposals (preserve original playable sections, exact parsed vector sequence; update only sideboard). Use new experiment paths and manifest version, not historical files.
2. Add fail-closed ordered playable equality before screening. A multiset check alone is insufficient. Test repeated card rows, unsorted runes/battlefields, both seats, and preservation of original files. Consider canonical ordering across ALL future registrations as a separately versioned design, not a retrospective change.
3. Run a small native regression on corrected binary with an unchanged original, sideboard-only variant, reordered control and corrected variant; same engine, agents, seed, opponent and seat. Check actual first player, initial draws/action history where available and terminal winner, and repeat identical input to detect remaining nondeterminism. Test multiple seeds and both seats; fail closed on any error/mismatch for ordered-equivalent cases. Never strip sideboard to bypass legality validation.
4. Require native regression success before new sideboard fitness campaigns. Historical screening and holdout remain exploratory and cannot establish causal improvement; zero adopted upgrades. Preserve historical artifacts.
5. Continue P0-03/04 card coverage and rules audit; P0-09 clean local build and dependency lock remain pending.

P0-02 source/architecture inventory and historical order audit complete; native corrective gate P0-02R OPEN. Phase 0 not accepted. No fresh native matches or adopted decks.
