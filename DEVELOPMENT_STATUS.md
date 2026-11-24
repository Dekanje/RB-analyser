# Development status — 2026-11-24
## Branch and evidence
Active implementation baseline: `research/competitive-agent-benchmark-v1-2026-11-23`, commit `0b9739bb6c20e8ed5a805a78239d5faa09b226ad`. Default main before documentation setup: `0b6d0c2eda7e6dc829d635f8a14e05ab0e669724` (older Radiance mapping work). Do not resume engine development on main merely because it is default.
| Evidence | Observed status | Interpretation |
|---|---|---|
| [45297203812](https://github.com/Dekanje/RB-analyser/actions/runs/45297203812) at 0b9739bb6c20e8ed5a805a78239d5faa09b226ad | completed/success; aggregate artifact 14877427266 | 58×6 coordinated package screening; training only, no adoption; results not independently inspected |
| [45283891778](https://github.com/Dekanje/RB-analyser/actions/runs/45283891778) at 32fbedf14fd7b362478a4fb321ebed14e31aaa56 | completed/success | 580 registered-structure native re-certification; not universal rules proof |
| [45282108093](https://github.com/Dekanje/RB-analyser/actions/runs/45282108093) | completed/success | RAD-057 correction and regression workflow |
| [45277847529](https://github.com/Dekanje/RB-analyser/actions/runs/45277847529) | completed/failure | historical failed RAD-057 workflow; do not conflate with corrected successor |
| radiance/qa/2026-11-23-full-qa.md | historical repository report | 1,123 registered identities, 167/167 numbered Radiance identities, 274/274 focused tests, 3,912/3,912 upstream+overlay tests, one disabled upstream test; 64/64 Final64 mapped scenarios; 37 historical edge-case questions not reconciled; not independently rerun this session |
## Phase state
0 IN PROGRESS: branch inventory, workflow metadata, relevant code/doc review and documentation setup. Full audit, artifact inspection, local reproducibility, license and benchmark still open.
1–2 PARTIAL: catalog/registry and card tests exist; exact legal functional coverage, variant equivalence and comprehensive rules evidence pending.
3–4 PARTIAL: existing native engine and ISMCTS benchmarks; actual local throughput and agent strength not certified here.
5–7 PARTIAL/UNKNOWN: synergy scripts exist; autonomous training and independent full archetype discovery not verified.
8 PARTIAL: multi-card screening completed; independent holdout promotion missing/unverified.
9 PARTIAL: scripts/tournament_bo3_policy.py implements registered pool checks, supplied sideboard plans, champion swaps and first-player receipts; clock and adaptive matchup policy outstanding per source.
10–14 PARTIAL/UNKNOWN: historical optimization evidence exists; no production gate accepted.
15–17 NOT VERIFIED: full Swiss/cut tournament, UI and maintenance require audit/implementation.
No phase gate is accepted in this session. No engine code altered, no fresh simulations or tests executed.
Next: Phase 0. Read docs/HANDOVER.md; reconcile artifact evidence and test coverage before further candidate adoption.

## Repository hygiene follow-up
2026-11-24: inspected 44 branch refs and 105 workflow paths; verified active/main divergence (839 ahead, 1 behind at pre-cleanup comparison). Added navigation, contribution policy, branch/workflow/evidence indexes and local ignore rules. No executable code or workflow modified, no branch deleted. Reviewed Swiss sensitivity script: it is a hypothetical independent Bernoulli threshold model, not a full Swiss simulator. Phase 0 remains open; next P0-01 as before, with ancestry/dependency audit prior to main consolidation.

## P0-01 priority artifact audit
2026-11-24: [audit report](docs/P0_01_ARTIFACT_AUDIT.md). Verified archive provenance, 580 compatibility receipts, 348 package hashes/deltas, native QA XML and 12 sideboard holdout shards. 1624 synergy BO3, 928 sideboard training BO3, 576 sideboard holdout BO3; older structural holdout aggregate 576 BO3. Zero confirmed upgrades in these experiments. Corrected engine Game 1 paired winner mismatch 183/696 training and 56/288 holdout. No fresh native execution. P0-01 priority scope complete; historical coverage remains bounded; Phase 0 not accepted. Next P0-02 architecture and reproducible build/dependency audit, including RNG path risk.

## P0-02 architecture and order audit
2026-11-24: [architecture audit](docs/P0_02_ARCHITECTURE_AUDIT.md). Pinned upstream/build/overlay chain inventoried, license TBD confirmed, archived binary requires missing Boost.Context 1.83 in current sandbox. Read-only audit implemented and tested (6/6 local unit tests; actual 174-candidate and 12-holdout archive cross-tab reproduced). All 239 historical Game 1 winner mismatches occur in reordered runes/battlefields; 0/180 paired observations with unchanged playable order. Source trace shows alphabetical serialization plus native order-sensitive setup. No fresh native simulation; no fix to production paths yet. Next P0-02R order-preserving serialization and controlled native regression, then P0-03/04. Phase 0 still open.
