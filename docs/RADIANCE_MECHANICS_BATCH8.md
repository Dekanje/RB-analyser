# Radiance Batch 8 — staged implementation

Baseline: accepted Batch 7 engine, 1,009 definitions, 53/167 numbered Radiance identities.
Target: 15 additional **distinct** Radiance base cards (68/167), all with actual gameplay implementations and scenario tests. This is not achieved until strict audit and full regression pass.

## Tranche 1 — implemented, awaiting CI
- RAD-002 Banner of Conquest — Deploy battlefield Assault aura (engine ID 1010)
- RAD-025 Consult the Heavens — Shield 2 and Predict (1011)
- RAD-026 Entrenched Boar — optional enter-ready / no move (1012)
- RAD-034 Hunker Down — friendly ready, movement restriction and draw (1013)
- RAD-118 Herald of the Emperor — temporary change to base Might (1014)
- RAD-095 Momentary Companion — off-turn Temporary / Hidden (1015)

## Tranche 2 — planned, **not implemented yet**
- RAD-007 Rally for War
- RAD-024 Blossoming Dreamroot
- RAD-027 Iridescent Avian
- RAD-030 Sanctum Conservator
- RAD-036 Storm Raptor
- RAD-039 Ephemeral Ward
- RAD-052 Resource Extractor
- RAD-056 Improvised Projectile
- RAD-100 The Waters' Wage

All 15 are missing from the *compiled* 1,009-card registry and their printed rules were retrieved from pinned AlphaRune gallery JSON. No runtime or registry-only stubs are counted as complete.

Batch 8 uses an adapted staged workflow: ordinary push only preflight, test-fix for named tests, check-cards for card tests + full duplicate audit, batch-ready for mandatory 3,675+ full regression. The full acceptance gate is not run for incomplete tranches.
