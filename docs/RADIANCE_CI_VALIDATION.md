# Radiance Batch 7 — staged fail-fast validation

Workflow: `.github/workflows/radiance-batch7-mechanics.yml`
Branch: `radiance/mechanics-batch7-2026-11-22`

## Commit markers

| Commit subject prefix | Work performed | Appropriate use |
| --- | --- | --- |
| Any other prefix, including `[ci-pipeline]` | Python syntax, source sanity, catalog preflight | Routine changes |
| `[test-fix]` | Preflight, compile C++ test target, run `RadianceBatch7Test.*` | Fix an ordinary Batch 7 mechanic |
| `[test-fix:DeckFuzz.DeckOfSeedOneIsPinned]` | Preflight, compile C++ test target, run exactly one named GoogleTest | Fix a specific failure |
| `[check-cards]` | Preflight, compile engine, run all Radiance tests, strict registry and catalog audit | When focused fixes pass |
| `[batch-ready]` | All batch checks, then the full AlphaRune regression | Final acceptance for a completed batch |

For example, `[test-fix:RadianceBatch7Test.OverloadedTravelerNeedsFriendlyDeployGearAtSameBattlefield] Correct Deploy aura fixture` runs only the relevant test after preflight and compilation.

A targeted test filter must be safe and match at least one test; a zero-test run cannot pass. `workflow_dispatch` also supports choosing targeted, batch, or full, with an optional GoogleTest filter.

## Speed improvements

- The expensive full regression happens **after** focused card tests and the registry audit have passed.
- In targeted mode, only the `riftbound_tests` C++ target is built; batch/full mode builds `riftbound` and `riftbound_tests`.
- `ccache` is restored from matching earlier commits and persisted even if a later test fails, avoiding needless re-compilation.
- Every normal push receives fast preflight. C++ validation is requested explicitly by commit marker or workflow dispatch.
- The staged workflow uses a new concurrency group, avoiding cancellation of the previous long-running Batch 7 validation during migration.

## Acceptance policy

No targeted or batch-only run certifies Batch 7. Final acceptance still requires all focused tests, strict catalog/registry verification, and the complete AlphaRune regression to pass. Full-Radiance 58-deck BO3 conclusions are **not** authorized while the set remains incomplete.

Current Batch 7 target: **1,009 compiled definitions**, **53 of 167 base Radiance cards registered**, **114 missing**. Nine new Batch 7 cards are authored; RAD-101/167 reuses the preexisting engine implementation at ID 984.
