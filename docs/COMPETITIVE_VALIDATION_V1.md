# Competitive Validation v1 — agent strength gate

This branch adds the first **isolated agent-strength measurement**. It does not alter existing 58-Legend decklists or production simulation workflows.

## Research question

Does a deeper ISMCTS policy (`ismcts:sims=128`) beat the existing shallow policy (`ismcts:sims=24`) when both pilots have **the exact same deck**?

A more expensive agent is not automatically stronger. If stronger search fails on this controlled test, adding millions of deck matchups would amplify a weak playing policy rather than resolve it.

## What it measures

- For each selected deck, evaluate a seed twice: challenger in seat 1, then seat 2.
- Use the same decklist and seed in each seat for a paired comparison.
- Record engine and deck hashes, full game statuses, and challenger wins.
- Do not count timeouts, crashes or draws as losses. Any incomplete game fails the overall gate.
- Export aggregate and per-deck challenger win rates with Wilson 95% intervals.

This benchmark **does not** demonstrate card-rule correctness, deck quality, full BO3, sideboarding or real-world tournament strength.

## Continuous integration

`.github/workflows/competitive-agent-strength.yml` runs *unit tests only* on pushes to this research branch. An optional `workflow_dispatch` job can run actual engine games using the pinned compiled engine and 58 candidate-deck artifacts. The gameplay job is never run automatically on a push.

The workflow dispatch interface may require the workflow to be present on the repository's default branch before it can be run through the GitHub Actions UI; do not merge the research work without reviewing the changes.

## Run locally on Linux or WSL2

Download the full-Radiance compiled Linux engine artifact from run **45205260187** and 58 selected candidate decklists from run **45181493632**, or use a locally compiled matching engine.

Ensure the `riftbound` binary runs on your machine and all shared-library dependencies resolve. For a Windows PC, use WSL2 Ubuntu to run the Linux binary, or compile a compatible native Windows build separately.

```bash
python3 -m unittest discover -s scripts -p 'test_benchmark_agent_strength.py' -v

python3 scripts/benchmark_agent_strength.py \
  --engine /path/to/riftbound \
  --decks-dir /path/to/selected_decks \
  --output /path/to/agent_strength.json \
  --baseline-agent ismcts:sims=24 \
  --challenger-agent ismcts:sims=128 \
  --repetitions 10 \
  --max-decks 3 \
  --timeout 300
```

Start small, then test 128, 512 and 1024 simulations per decision with broader archetype coverage. Prefer confidence intervals and independent holdout seeds over a single headline win rate. If all runs finish correctly but the challenger does not consistently outperform, improve the policy and evaluation function before scaling up.

## Subsequent validation gates

1. Rule-accurate, deterministic card and interaction tests against official rulings.
2. Stronger-agent comparisons with more archetypes and held-out seeds.
3. Tournament-realistic BO3, mulligan policies and between-game sideboard swaps.
4. Expand candidate deck search and verify changes against independently optimized adversaries.
5. Use metagame-weighted lineup evaluation with uncertainty intervals.

Legacy is excluded from the hypothetical Worlds target card pool.
