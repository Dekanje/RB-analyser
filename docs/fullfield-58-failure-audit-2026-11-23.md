# Full-field BO3 failure audit and targeted repair (2026-11-23)

## Provenance
- Complete 58-legend exploratory optimizer: [run 45181493632](https://github.com/Dekanje/RB-analyser/actions/runs/45181493632), 58/58 selected source lists, 8 provisional changes, 16,704 cached BO3 evaluations. No claim of global optimality.
- Original full-field validation: [run 45181577579](https://github.com/Dekanje/RB-analyser/actions/runs/45181577579), **failed closed**.
- Original 58-optimized head-to-head: [run 45181587794](https://github.com/Dekanje/RB-analyser/actions/runs/45181587794), **failed closed**.
- Audited 22 of their 58 persisted shard artifacts, containing 3,876 BO3 scenarios and 110 incomplete match records. This is a *sample of artifacts*, not the total run-wide failure count.

## Observed failure categories within those 22 artifacts

| Engine error | Incomplete records |
|---|---:|
| Primordial Roar: offered no legal target | 46 |
| Silent process termination in Mordekaiser matchups | 42 |
| Convergent Mutation: unpayable choices | 18 |
| Mesmerize: offered no legal target | 2 |
| Burn Away: offered no legal target | 1 |
| One-Two Punch: offered no legal target | 1 |

The silent records all involved Mordekaiser. This pattern is consistent with the previously investigated Boost.Context fiber crash but an empty stderr alone does not prove every crash has the same root cause.

## Corrective source work

- `radiance/engine_overlay/stability_patch.py`: pinned upstream-only complete payable-choice preflight and exact viable choice search for Convergent Mutation, Mesmerize, One-Two Punch, Primordial Roar, and Burn Away. Preserve the previous stack-headroom and Boost.Context `forced_unwind` changes for Mordekaiser.
- `radiance/engine_overlay/fullfield_repair.py`: Primordial Roar's optional Show Off must not create a mandatory damage target if no unit is on the board. Clear the optional-effect marker for replayed cards. Abort when a version-pinned source anchor or expected earlier repair is missing.
- `scripts/optimize_58.py`: preserve nonzero C++ exit codes and Unix termination signals even if the binary prints no stderr.
- `scripts/replay_fullfield_failures.py`: replay recorded BO3 series/game seeds through the actual engine and ISMCTS policy, including all three component seeds for original Mesmerize/Burn Away series whose artifacts did not retain per-game statuses.

## Fail-closed acceptance process

1. Confirm exact pinned engine SHA and apply all 167 Radiance implementations.
2. Apply the existing stability patch and targeted Primordial Roar source repair; reject unexpected source changes.
3. Compile the actual C++ game binary, verify the full 1,123-entry engine registry and all 167 Radiance card identities.
4. Replay exact failed seeds; **do not count crashes, exceptions or timeouts as a loss for either side**.
5. Only if step 4 passes, run the full-field and optimized-vs-optimized BO3 workflows and publish their artifacts.
6. Retain 58 original/selected deck SHA receipts. These remain fixed-deck simulations with no between-game sideboarding and no globally optimal deck guarantee.

Do not mark a fix accepted merely because a patch applied or C++ compiled. Real-game exact-seed evidence and broader independent field validation are required.
