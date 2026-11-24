# RB-Analyser 2.0

**Competitive Riftbound research engine · Development / experimental**

A research project for rules-accurate native simulations, intelligent play, independent legal deck discovery, matchup/meta/universal optimization and realistic tournament analysis. The primary objective is championship-winning probability, not raw simulation volume. No mandatory paid AI/API or cloud compute is planned.

> **Status:** Phase 0 (baseline audit) in progress. The existing engine and optimization experiments are valuable but are not a certified production release. No claim of exhaustive rules correctness, global deck optimality or guaranteed tournament success.

## Start here

| Resource | Purpose |
|---|---|
| [Master plan](MASTER_PLAN.md) | 18 phases and mandatory acceptance gates |
| [Development status](DEVELOPMENT_STATUS.md) | Verified observations and outstanding work |
| [Handover](docs/HANDOVER.md) | Exact next task |
| [Documentation index](docs/README.md) | Technical specifications and historical evidence |
| [Repository guide](docs/REPOSITORY_GUIDE.md) | Source layout and working practices |
| [Known limitations](KNOWN_LIMITATIONS.md) | Risks and unverified claims |
| [Contributing](CONTRIBUTING.md) | Development and QA workflow |

## Repository layout

| Path | Responsibility |
|---|---|
| `radiance/engine_overlay/` | C++ AlphaRune integration and fixes |
| `radiance/data/`, `radiance/validation/`, `radiance/qa/` | Catalog, validation inputs and historical QA |
| `scripts/` | Native game/BO3 orchestration, agents, deck search, tests, projections |
| `data/` | Versioned candidate inputs, manifests and workflow launch markers |
| `optimization/` | Historical optimization reports |
| `audit/`, `compat/`, `bo3/` | Earlier audit, compatibility and BO3 utilities |
| `.github/workflows/` | CI and historical/research experiment workflows |
| `docs/` | Specifications, QA evidence, operations and handover |

## Development entry point

This is the active integration/research branch, not a release. Clone or switch to it explicitly:

```bash
git clone --branch research/competitive-agent-benchmark-v1-2026-11-23 https://github.com/Dekanje/RB-analyser.git
cd RB-analyser
python3 -m unittest discover -s scripts -p 'test_synergy_multicard*.py' -v
````
The command above is a targeted Python regression example, not a full validation or a playable build. For native engine prerequisites, artifact provenance and agent benchmark commands, see [Competitive validation](docs/COMPETITIVE_VALIDATION_V1.md) and [Reproducibility](docs/REPRODUCIBILITY.md). The clean local build remains a Phase 0 deliverable.

## Evidence and results

Native completed games, statistical projections, heuristic screens and hypothetical examples are separate evidence categories. Latest successful research runs are indexed in [Evidence index](docs/EVIDENCE_INDEX.md). A green workflow does not imply all rules are correct or a candidate was adopted. Swiss threshold sensitivity is a projection, not a full Swiss/tournament simulator.

## Dependencies and rights

Native engine upstream: [AlphaRune](https://github.com/chorlick/alpharune), C++ with Python orchestration. Upstream licensing was marked TBD in the historical README; verify rights before redistribution. No new license is asserted. This is an unofficial research project and does not imply Riot endorsement. Repository visibility and historical artifacts are unchanged.
