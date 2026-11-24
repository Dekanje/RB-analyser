# GitHub Actions workflow catalog

Snapshot: 105 workflow files on the active branch at `f174f87932f2feab72b732249986d38bd48d2512`. Categories are navigation groupings based on filenames, not declarations that each workflow is current, green or safe to rerun.

## Preferred evidence entry points
| Workflow | Intended interpretation |
|---|---|
| [Agent-strength validation](../.github/workflows/competitive-agent-strength.yml) | Isolated agent benchmarking; not tournament validity |
| [RAD-057 native QA](../.github/workflows/competitive-guidebot-native-qa.yml) | Native correction evidence |
| [580 native re-certification](../.github/workflows/competitive-guidebot-fresh580-native.yml) | Registered structures, not exhaustive card correctness |
| [Multi-card screening](../.github/workflows/competitive-multicard-synergy-407.yml) | Training only; no adoption |
| [Swiss threshold sensitivity](../.github/workflows/competitive-swiss-thresholds.yml) | Hypothetical independent-match projection only |

The reviewed competitive workflow definitions explicitly reference the current research branch and specific paths/launch markers. Some use pinned artifact run IDs. Do not rename the branch, delete producer workflows, edit trigger paths or reuse markers without reviewing all dependencies. A new stable CI pipeline should be introduced and tested before retiring historical jobs. No existing workflow was edited in this cleanup.

## Full inventory
### Engine / compatibility / audits (7)
- [alpharune-49-compat-matrix.yml](../.github/workflows/alpharune-49-compat-matrix.yml)
- [alpharune-baseline-control.yml](../.github/workflows/alpharune-baseline-control.yml)
- [alpharune-card-audit.yml](../.github/workflows/alpharune-card-audit.yml)
- [alpharune-compatibility.yml](../.github/workflows/alpharune-compatibility.yml)
- [alpharune-parallel.yml](../.github/workflows/alpharune-parallel.yml)
- [alpharune-smoke.yml](../.github/workflows/alpharune-smoke.yml)
- [audit-domain-illegal-decks.yml](../.github/workflows/audit-domain-illegal-decks.yml)

### Radiance implementation and validation (26)
- [blind-validate-all58-full-radiance.yml](../.github/workflows/blind-validate-all58-full-radiance.yml)
- [radiance-2026-11-23-bans.yml](../.github/workflows/radiance-2026-11-23-bans.yml)
- [radiance-58-blind-validation.yml](../.github/workflows/radiance-58-blind-validation.yml)
- [radiance-58-compatibility.yml](../.github/workflows/radiance-58-compatibility.yml)
- [radiance-58-full-field-validation.yml](../.github/workflows/radiance-58-full-field-validation.yml)
- [radiance-58-ismcts-search.yml](../.github/workflows/radiance-58-ismcts-search.yml)
- [radiance-58-legal-candidate.yml](../.github/workflows/radiance-58-legal-candidate.yml)
- [radiance-batch10-mechanics.yml](../.github/workflows/radiance-batch10-mechanics.yml)
- [radiance-batch6-mechanics.yml](../.github/workflows/radiance-batch6-mechanics.yml)
- [radiance-batch7-mechanics.yml](../.github/workflows/radiance-batch7-mechanics.yml)
- [radiance-batch8-mechanics.yml](../.github/workflows/radiance-batch8-mechanics.yml)
- [radiance-batch9-mechanics.yml](../.github/workflows/radiance-batch9-mechanics.yml)
- [radiance-catalog.yml](../.github/workflows/radiance-catalog.yml)
- [radiance-engine-prototype.yml](../.github/workflows/radiance-engine-prototype.yml)
- [radiance-fast-preflight.yml](../.github/workflows/radiance-fast-preflight.yml)
- [radiance-final64-mechanics.yml](../.github/workflows/radiance-final64-mechanics.yml)
- [radiance-full-bo3.yml](../.github/workflows/radiance-full-bo3.yml)
- [radiance-full-pool-audit.yml](../.github/workflows/radiance-full-pool-audit.yml)
- [radiance-live-refresh.yml](../.github/workflows/radiance-live-refresh.yml)
- [radiance-nine-source-audit.yml](../.github/workflows/radiance-nine-source-audit.yml)
- [radiance-regression.yml](../.github/workflows/radiance-regression.yml)
- [radiance-wave1-implementations.yml](../.github/workflows/radiance-wave1-implementations.yml)
- [radiance-wave2-implementations.yml](../.github/workflows/radiance-wave2-implementations.yml)
- [radiance-wave3-implementations.yml](../.github/workflows/radiance-wave3-implementations.yml)
- [radiance-wave4-implementations.yml](../.github/workflows/radiance-wave4-implementations.yml)
- [radiance-wave5-audit.yml](../.github/workflows/radiance-wave5-audit.yml)

### Competitive agents / BO3 / search (45)
- [competitive-406-structural-fitness.yml](../.github/workflows/competitive-406-structural-fitness.yml)
- [competitive-407-policy-holdout.yml](../.github/workflows/competitive-407-policy-holdout.yml)
- [competitive-58-neeko-preflight.yml](../.github/workflows/competitive-58-neeko-preflight.yml)
- [competitive-58-nextwave.yml](../.github/workflows/competitive-58-nextwave.yml)
- [competitive-agent-512.yml](../.github/workflows/competitive-agent-512.yml)
- [competitive-agent-panel.yml](../.github/workflows/competitive-agent-panel.yml)
- [competitive-agent-pilot.yml](../.github/workflows/competitive-agent-pilot.yml)
- [competitive-agent-strength.yml](../.github/workflows/competitive-agent-strength.yml)
- [competitive-all58-candidates.yml](../.github/workflows/competitive-all58-candidates.yml)
- [competitive-all58-independent-holdout.yml](../.github/workflows/competitive-all58-independent-holdout.yml)
- [competitive-champion-switch-smoke.yml](../.github/workflows/competitive-champion-switch-smoke.yml)
- [competitive-elite58-screen.yml](../.github/workflows/competitive-elite58-screen.yml)
- [competitive-evolution-screen.yml](../.github/workflows/competitive-evolution-screen.yml)
- [competitive-evolutionary-proposals.yml](../.github/workflows/competitive-evolutionary-proposals.yml)
- [competitive-exhaustive-580-native.yml](../.github/workflows/competitive-exhaustive-580-native.yml)
- [competitive-guidebot-fresh580-native.yml](../.github/workflows/competitive-guidebot-fresh580-native.yml)
- [competitive-guidebot-fresh580-preflight.yml](../.github/workflows/competitive-guidebot-fresh580-preflight.yml)
- [competitive-guidebot-native-qa.yml](../.github/workflows/competitive-guidebot-native-qa.yml)
- [competitive-independent-holdout.yml](../.github/workflows/competitive-independent-holdout.yml)
- [competitive-multicard-synergy-407.yml](../.github/workflows/competitive-multicard-synergy-407.yml)
- [competitive-nasus-game3-exact-debug.yml](../.github/workflows/competitive-nasus-game3-exact-debug.yml)
- [competitive-neeko-registration.yml](../.github/workflows/competitive-neeko-registration.yml)
- [competitive-phase5-128-holdout.yml](../.github/workflows/competitive-phase5-128-holdout.yml)
- [competitive-registered-structure.yml](../.github/workflows/competitive-registered-structure.yml)
- [competitive-repaired-engine-qa.yml](../.github/workflows/competitive-repaired-engine-qa.yml)
- [competitive-robust-worlds.yml](../.github/workflows/competitive-robust-worlds.yml)
- [competitive-rule407-engine.yml](../.github/workflows/competitive-rule407-engine.yml)
- [competitive-sideboard-128-preflight.yml](../.github/workflows/competitive-sideboard-128-preflight.yml)
- [competitive-sideboard-174-aggregate-recovery.yml](../.github/workflows/competitive-sideboard-174-aggregate-recovery.yml)
- [competitive-sideboard-174-fitness.yml](../.github/workflows/competitive-sideboard-174-fitness.yml)
- [competitive-sideboard-174-shard6-replay.yml](../.github/workflows/competitive-sideboard-174-shard6-replay.yml)
- [competitive-sideboard-bo3-smoke.yml](../.github/workflows/competitive-sideboard-bo3-smoke.yml)
- [competitive-sideboard-policy-pilot.yml](../.github/workflows/competitive-sideboard-policy-pilot.yml)
- [competitive-sideboard-policy-preflight.yml](../.github/workflows/competitive-sideboard-policy-preflight.yml)
- [competitive-sideboard-structure.yml](../.github/workflows/competitive-sideboard-structure.yml)
- [competitive-structural-128-aggregate-recovery.yml](../.github/workflows/competitive-structural-128-aggregate-recovery.yml)
- [competitive-structural-128-holdout.yml](../.github/workflows/competitive-structural-128-holdout.yml)
- [competitive-structural-all58-native.yml](../.github/workflows/competitive-structural-all58-native.yml)
- [competitive-structural-native-smoke.yml](../.github/workflows/competitive-structural-native-smoke.yml)
- [competitive-swiss-thresholds.yml](../.github/workflows/competitive-swiss-thresholds.yml)
- [competitive-top10-strong-screen.yml](../.github/workflows/competitive-top10-strong-screen.yml)
- [competitive-wave2-holdout-preflight.yml](../.github/workflows/competitive-wave2-holdout-preflight.yml)
- [competitive-worlds-lineups.yml](../.github/workflows/competitive-worlds-lineups.yml)
- [competitive-worlds-policy-aggregate.yml](../.github/workflows/competitive-worlds-policy-aggregate.yml)
- [competitive-worlds-sideboard-depth3.yml](../.github/workflows/competitive-worlds-sideboard-depth3.yml)

### ISMCTS diagnostics (12)
- [ismcts-crash-diagnostics-v2.yml](../.github/workflows/ismcts-crash-diagnostics-v2.yml)
- [ismcts-debug-crashes.yml](../.github/workflows/ismcts-debug-crashes.yml)
- [ismcts-failure-signatures.yml](../.github/workflows/ismcts-failure-signatures.yml)
- [ismcts-full-bo3.yml](../.github/workflows/ismcts-full-bo3.yml)
- [ismcts-morde-trace.yml](../.github/workflows/ismcts-morde-trace.yml)
- [ismcts-postmortem.yml](../.github/workflows/ismcts-postmortem.yml)
- [ismcts-sampler-isolation.yml](../.github/workflows/ismcts-sampler-isolation.yml)
- [ismcts-sanitizer-replay.yml](../.github/workflows/ismcts-sanitizer-replay.yml)
- [ismcts-search-depth-diagnostics.yml](../.github/workflows/ismcts-search-depth-diagnostics.yml)
- [ismcts-seat-isolation.yml](../.github/workflows/ismcts-seat-isolation.yml)
- [ismcts-stability-58-full.yml](../.github/workflows/ismcts-stability-58-full.yml)
- [ismcts-stability-regression.yml](../.github/workflows/ismcts-stability-regression.yml)

### Optimization and repair (10)
- [full-field-58-validation.yml](../.github/workflows/full-field-58-validation.yml)
- [optimization-ismcts.yml](../.github/workflows/optimization-ismcts.yml)
- [optimization-source-export.yml](../.github/workflows/optimization-source-export.yml)
- [optimize-all58-expanded-bundles.yml](../.github/workflows/optimize-all58-expanded-bundles.yml)
- [optimize-all58-final-radiance.yml](../.github/workflows/optimize-all58-final-radiance.yml)
- [optimized-58-round-robin.yml](../.github/workflows/optimized-58-round-robin.yml)
- [repair-fullfield-engine-replay.yml](../.github/workflows/repair-fullfield-engine-replay.yml)
- [repaired-58-full-field-validation.yml](../.github/workflows/repaired-58-full-field-validation.yml)
- [repaired-58-round-robin.yml](../.github/workflows/repaired-58-round-robin.yml)
- [test-optimize-58-bundles.yml](../.github/workflows/test-optimize-58-bundles.yml)

### Exports and historical utilities (5)
- [export-58-deckbook.yml](../.github/workflows/export-58-deckbook.yml)
- [export-988-card-registry.yml](../.github/workflows/export-988-card-registry.yml)
- [export-alpharune-snapshot.yml](../.github/workflows/export-alpharune-snapshot.yml)
- [export-current-radiance-overlay.yml](../.github/workflows/export-current-radiance-overlay.yml)
- [inspect-original-ornn.yml](../.github/workflows/inspect-original-ornn.yml)

### P0-04 provenance (isolated candidate branch)
- [p0-04-overlay-provenance.yml](https://github.com/Dekanje/RB-analyser/blob/39cc94bf866d61b3638b216fe6c4e45f0b77204d/.github/workflows/p0-04-overlay-provenance.yml) — pinned read-only overlay reconstruction and historical XML reconciliation, run 45463414756. No C++ build. Retain candidate ancestry.

### P0-09 local reproducibility (isolated candidate branches)
- [Clean native build](https://github.com/Dekanje/RB-analyser/blob/6432f9832b147903ec82eaa3e61e278e77c3e5df/.github/workflows/p0-09-local-reproducibility.yml) — run 45464883262.
- [Independent package preflight](https://github.com/Dekanje/RB-analyser/blob/6dee53a2249b06216bc3da07c0628e61b092c8df/.github/workflows/p0-09-package-preflight.yml) — run 45465382677, no compilation.

- [P0-05 guarded current agent calibration](https://github.com/Dekanje/RB-analyser/blob/a1a753648227b134c0a06a8583c53546acb7c70b/.github/workflows/p0-05-current-agent-calibration.yml) — 24 planned native games, research only.
