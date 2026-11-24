# Contributing to RB-Analyser 2.0

Read [AGENTS](AGENTS.md), [master plan](MASTER_PLAN.md), [status](DEVELOPMENT_STATUS.md), [limitations](KNOWN_LIMITATIONS.md) and [handover](docs/HANDOVER.md) first. Use the [active research branch](https://github.com/Dekanje/RB-analyser/tree/research/competitive-agent-benchmark-v1-2026-11-23) as the current baseline, not historical main. Branch from its verified head for code changes.

## Workflow
1. Assign a master-plan task ID and describe the expected behavior and acceptance criteria.
2. Create a scoped feature/fix branch; preserve existing code unless a justified change is necessary.
3. Add positive/negative and regression tests; run targeted local checks, then appropriate CI gates. Never turn timeouts or illegal games into wins/losses.
4. Review diff, native/agent/rules provenance and test results. Expensive campaigns run locally where practical; do not launch them by changing marker files casually.
5. Merge only reviewed changes; update status, handover, known limitations, decisions and evidence links. Record exact commits, tests, seeds, counts and uncertainty.

Use descriptive commit subjects (e.g. `fix(rules): validate trigger resolution [P2-06]`). Keep changes focused. Do not commit secrets, unapproved full card-text dumps, generated binaries or private research results. Use the [workflow catalog](docs/WORKFLOW_CATALOG.md) before altering CI. Branch retirement requires an explicit dependency and ancestry audit, and preserved immutable evidence. See [QA requirements](docs/QA_REQUIREMENTS.md).
