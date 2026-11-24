# RB-analyser — Riftbound gameplay experiments

This repository contains 58 previously optimized candidate decklists and a GitHub Actions workflow to attempt actual AlphaRune C++ simulations.

Game outcomes are recorded **only** after the AlphaRune engine completes actual matches; previous heuristic probabilities are not game results. Initial runs are build and compatibility smoke tests, not evidence that all 58 decks work. BO3 without validated sideboard substitutions is labeled **unsideboarded**, not tournament BO3.

AlphaRune upstream: https://github.com/chorlick/alpharune (upstream license currently marked TBD). This is a research setup; no website or other repositories are modified.

## RB-Analyser 2.0 development
The active implementation and authoritative development documentation are on [research/competitive-agent-benchmark-v1-2026-11-23](https://github.com/Dekanje/RB-analyser/tree/research/competitive-agent-benchmark-v1-2026-11-23). Start with [AGENTS.md](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/AGENTS.md), [MASTER_PLAN.md](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/MASTER_PLAN.md), [DEVELOPMENT_STATUS.md](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/DEVELOPMENT_STATUS.md), [KNOWN_LIMITATIONS.md](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/KNOWN_LIMITATIONS.md) and [handover](https://github.com/Dekanje/RB-analyser/blob/research/competitive-agent-benchmark-v1-2026-11-23/docs/HANDOVER.md). Main remains the historical engine baseline pending an explicit consolidation review.
