# Repository guide

## Branch model
- `main`: public entry point and historical engine tree until Phase 0 integration review.
- `research/competitive-agent-benchmark-v1-2026-11-23`: sole current implementation/integration branch; existing CI branch filters require its exact name.
- New scoped work: `feature/<task>-<description>`, `fix/<task>-<description>`, or `research/<task>-<description>` from current verified integration head. No new long-lived parallel integration branches without a recorded decision.
- Existing experimental branches are retained historical references, not a list of active work. See [Branch register](BRANCH_REGISTER.md).

## Code navigation
| Area | Start with |
|---|---|
| C++ integration | [engine overlay](../radiance/engine_overlay/README.md) |
| Card coverage | [coverage ledger](../radiance/coverage_ledger.py), [coverage schema](CARD_COVERAGE.json) |
| Native matches | [run_actual_games](../scripts/run_actual_games.py), [round robin](../scripts/round_robin_58.py) |
| BO3 registration | [tournament BO3 policy](../scripts/tournament_bo3_policy.py), [sideboard](../scripts/sideboard_deck.py) |
| Agent benchmarking | [benchmark agent](../scripts/benchmark_agent_strength.py) |
| Deck search | [optimizer](../scripts/optimize_58.py), [evolutionary candidates](../scripts/evolutionary_candidates.py), [synergy](../scripts/synergy_multicard.py) |
| Tournament projections | [Swiss sensitivity](../scripts/worlds_swiss_sensitivity.py) — independent-match model only |
| Tests | [scripts/](../scripts/), [Radiance QA](../radiance/qa/) |
| CI | [workflow catalog](WORKFLOW_CATALOG.md) |

## Consolidation policy
Snapshot reviewed branch tips, compare ancestry and inspect exact file/overlay differences, workflow branch and path triggers, artifact producer/consumer references, and historical report links. Confirm native build and relevant acceptance gates before merging a candidate into main. Keep historical commits and manifests reachable. Retire or move workflow files only after dependency review and a tested replacement. Do not force-push history. Current cleanup intentionally does not move executable code or disable workflows.

## Generated data
Keep tracked launch markers and small reviewed manifests in place. Store large run data locally or in versioned artifact storage with hashes and reproducibility manifests. Do not add arbitrary generated output to Git. Use [reproducibility](REPRODUCIBILITY.md) conventions.
