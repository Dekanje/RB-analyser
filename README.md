# RB-Analyser 2.0

**Competitive Riftbound research engine · In development**

RB-Analyser aims to discover and optimize legal decks for every legend, evaluate them with intelligent native BO3 agents and maximize championship-winning probability through configurable tournament simulation.

> **Project status:** Phase 0 — baseline and architectural audit. No production release or exhaustive rules certification is claimed.

## Start here

[Open the active development branch](https://github.com/Dekanje/RB-analyser/tree/research/competitive-agent-benchmark-v1-2026-11-23) · [View Actions](https://github.com/Dekanje/RB-analyser/actions)

| Resource | Purpose |
|---|---|
| [Master plan](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/MASTER_PLAN.md) | 18 phases, requirements and acceptance gates |
| [Current status](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/DEVELOPMENT_STATUS.md) | Verified evidence and outstanding tasks |
| [Latest handover](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/docs/HANDOVER.md) | Resume development here |
| [Documentation hub](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/docs/README.md) | Technical specifications and repository navigation |
| [Tournament specification](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/docs/TOURNAMENT_SPEC.md) | Swiss, intermediate cuts, top cut and elimination |
| [Evidence index](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/docs/EVIDENCE_INDEX.md) | Research runs and historical QA |
| [Known limitations](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/KNOWN_LIMITATIONS.md) | Explicit coverage and reliability gaps |
| [Contributing](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/CONTRIBUTING.md) | Scoped development and acceptance process |

## Research scope

- Legal card and rules implementation, intelligent ISMCTS and self-play.
- Independent deck and archetype discovery, synergy and multi-card optimization.
- Matchup-specific, meta-specific and robust all-around decks for every legal legend.
- Full BO3 with legal sideboarding, configurable Swiss, qualification cuts and seeded playoffs.
- Independent statistical validation, reproducibility and local execution without mandatory paid APIs.

## Repository organization

The default branch is the historical engine baseline and navigation entry point. The latest implementation and authoritative documentation are on the [active research branch](https://github.com/Dekanje/RB-analyser/tree/research/competitive-agent-benchmark-v1-2026-11-23). Existing Actions workflows depend on that exact branch name. Main will be consolidated only after the Phase 0 ancestry, dependency and validation audit; no experimental code has been silently merged.

| Source area | Link |
|---|---|
| Native engine integration | [radiance/engine_overlay](https://github.com/Dekanje/RB-analyser/tree/research/competitive-agent-benchmark-v1-2026-11-23/radiance/engine_overlay) |
| Simulation, search and tests | [scripts](https://github.com/Dekanje/RB-analyser/tree/research/competitive-agent-benchmark-v1-2026-11-23/scripts) |
| Versioned inputs | [data](https://github.com/Dekanje/RB-analyser/tree/research/competitive-agent-benchmark-v1-2026-11-23/data) |
| Historical optimization | [optimization](https://github.com/Dekanje/RB-analyser/tree/research/competitive-agent-benchmark-v1-2026-11-23/optimization) |
| Branches | [Branch register](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/docs/BRANCH_REGISTER.md) |
| CI workflows | [Workflow catalog](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/docs/WORKFLOW_CATALOG.md) |

To check out the current development baseline:

```bash
git clone --branch research/competitive-agent-benchmark-v1-2026-11-23 https://github.com/Dekanje/RB-analyser.git
```

See [local benchmark and native-engine prerequisites](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/docs/COMPETITIVE_VALIDATION_V1.md). The reproducible full local setup remains an audit deliverable.

## Research integrity and dependencies

Only completed native games count as actual game results. Heuristics, statistical projections and training-only candidate screens are labeled separately. Successful CI does not establish exhaustive correctness or deck optimality. No real-world tournament victory is guaranteed.

C++ engine foundation: [AlphaRune](https://github.com/chorlick/alpharune). The historical README noted upstream licensing TBD; verify rights before distribution. This is an unofficial research project, not a Riot-endorsed product.

Historical README: [pre-cleanup snapshot](https://github.com/Dekanje/RB-analyser/blob/0b6d0c2eda7e6dc829d635f8a14e05ab0e669724/README.md).
