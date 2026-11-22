# Radiance — mechanics-based batch implementation and CI contract

## Objective and measured baseline

- Deliver genuine, played-through-game C++ mechanics for all **167 numbered RAD base cards**, plus gameplay-distinct additional printings where verified as mechanically different. **219 gallery printings** do not equal 219 different game effects.
- As of the Wave 4 validated registry: 997 total compiled definitions, **41/167 numbered RAD identities**, **126 missing**. Nine newly authored C++ RAD cards across Waves 1–4; existing 32 registered RAD definitions still have separate testing gaps. Merely registered, compiled, or smoke-tested does not mean mechanics certified.
- Keep all prior 58-deck ISMCTS results and decklists unchanged until full Radiance rules/legality/variant coverage and integration regression are verified.

## Delivery units: not arbitrary two-card waves

Aim for **10–20 previously missing gameplay cards per batch**, based on a shared mechanics family and accurately implemented as working C++, not placeholder registrations. Divide only where a shared engine primitive is genuinely unimplemented or rules timing makes it unsafe to combine; record why the batch is smaller.

Suggested next implementation families (candidates; **not yet validated or approved**):

| Family | Representative unregistered numbered card candidates | Shared engine work |
|---|---|---|
| Targeting, temporary modifiers, ready/stun and spell choices | RAD-013 Lost to the Sands, RAD-025 Consult the Heavens, RAD-027 Iridescent Avian, RAD-028 Ki Burst, RAD-029 Life from Stone, RAD-034 Hunker Down, RAD-035 Invigorating Bloom, RAD-037 Watchful Curator, RAD-047 Fanfare, RAD-070 Hold 'Em | Paid targets, mode choice, temporary Might/Shield, Predict, exhausted costs, draw and trigger timing |
| Token creation, combat-board effects and unit enter-play triggers | RAD-001 Amateur Demolitionist, RAD-007 Rally for War, RAD-009 Antagonistic Apparatus, RAD-019 Firebrand Raider, RAD-026 Entrenched Boar, RAD-030 Sanctum Conservator, RAD-074 Raving Witness, RAD-083 Stalwart Goatherd, RAD-119 Hunting Dog, RAD-129 Trifarian Captain | Battlefield/base placement, Bomb/Recruit/Mech/Bird tokens, death triggers, movement, ready timing, gear targeting and search |
| Shared Radiance keywords and complex interactions | Deploy-based gear, Disarm-based units, Show Off cards and champion/legend packages | Implement keyword rules centrally, tests for choice timing, combat, replacements, held battlefields and cross-card triggers |

The list is intentionally illustrative: check each official printing and current errata, the pinned JSON, and the effective registry before taking any candidate. Filter out existing registered identities, newly banned cards, or special printings with the same gameplay rules. Do not force a 10-card group if it would require inventing behavior.

## Two-tier test loop

**During development / on each push** — quick review without cloning and rebuilding AlphaRune:
1. Python syntax and catalog/compiled-registry schema tests, duplicate-ID and unknown-code negative tests.
2. Source code, exact printed card texts and game-mechanics mapping review; compile issues are resolved during a separately requested targeted C++ build if needed.
3. Reuse cached engine compilation where possible; avoid redundant independent full-workflow jobs for each source-file commit.

**At batch finalization** — the only acceptance gate:
1. Commit with message **starting with** `[batch-ready]` to enable the full GitHub Actions build; or explicitly dispatch the full validation workflow.
2. Compile the **real pinned AlphaRune C++ engine**, its card registry and GTests. Run all new engine-path card-specific positive/negative tests and relevant cross-card interaction tests.
3. Run the **entire** upstream regression suite unfiltered (no disabled tests or raised tolerance merely to force green); update only intentional card-pool-dependent golden snapshots with actual measured reproducible values and keep prior snapshots.
4. Dump the compiled registry, assert exact expected card count and unique `card_id` / public codes, reconcile all 167 numbered identities and known non-gallery tokens, and publish the evidence ledger with missing cards / known gaps.
5. Mark the batch CI-pass only when all checks are green. Mechanics-certified status is stricter: test edge cases, legal move behavior, countered/invalid targets, replacement effects and interactions; do not conflate CI passing with universal behavior certification.

## Cost controls

- Each batch's workflow should have a fast preflight job on every development push and a full validation job gated behind `startsWith(github.event.head_commit.message, '[batch-ready]')` (or explicit workflow dispatch).
- Add per-branch `concurrency` with `cancel-in-progress: true`. This avoids work on superseded commits; note that jobs launched under older workflows might still finish.
- Reuse `ccache` with restore keys keyed by the pinned upstream SHA, compiler family/version and build mode; do not use a commit-SHA-only key with no shared restore prefix.
- Keep one cumulative branch and draft PR per mechanics group. Commit intermediate work without the full gate prefix. A skipped full job is NOT a successful batch validation.
- Cache misses, fresh runner provisioning, and compiled large-source C++ tests still incur material runtime. No claimed guaranteed speedup or delivery date.

## Handoff

At each scheduled implementation run, inspect branches, draft PRs and CI runs first; fix the current blocker and then implement multiple real cards or shared mechanics per run. Progress should be measured by **card effects implemented and verified**, not commits, documents, catalog-only validations, or merely executed CI builds.
