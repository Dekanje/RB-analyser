# Experimental 58-legend deck optimization — 21 November 2026

This branch is independent of `main` and `radiance/engine-mechanics-development`. The original 58 optimized decklists are **never edited**.

## Sources and rules

- Pinned C++ engine: `chorlick/alpharune@ec90f0fed002aed374d06249fa95e83e3cfbd386`, with the existing Radiance engine overlay.
- Source: `data/optimized_58_decks.json.gz.b64`, decoded by `scripts/run_actual_games.py`.
- Baseline: **54 untouched original lists and four disclosed, SHA-checked legal candidates**, created by `scripts/legal_candidate.py`.
- Restrictions: currently compiled standard pool, legend's domain identity, main-card type, per-card copies across main and sideboard, no new signature, no printed Unique overflow, and bans including the November 23 Standard wave (applied preemptively). The engine independently validates any candidate played.
- The main-deck card count is fixed (39 plus a separate Chosen Champion). The sideboard, runes, battlefields, legend and champion are held fixed.
- Engine decision policy: `ismcts:sims=24`, with sampled hidden-information worlds (not perfect-information MCTS). This is stronger than uniform random in an initial 12-game calibration, but it is not a trained competitive human-level policy.

## Algorithm and admission criteria

1. Generate up to 10 legal one-copy main-deck swaps, preserving card type and a similar energy/Power-cost band.
2. Quickly rank candidates using random-agent games as a **screen only**. Random scores cannot certify a deck.
3. Test the two shortlisted candidates with both seats, repeated seeds and three fixed strong opponents using **ISMCTS on both sides**.
4. Promote a candidate only when it beats its incumbent by at least two games in training and **also** on an independently seeded holdout batch; reject any engine errors/timeouts.
5. Repeat the search on a promoted candidate for a second round. Stop per legend when no further tested swap passes both gates.
6. Export **all 58 selected lists**, which include unchanged incumbents for legends with no validated improvement. Every candidate file keeps its source SHA receipt and swap log.

This is a **bounded experimental hill-climb**, not an exhaustive global optimization. Small validation samples are not statistically decisive. To measure competitive decks, a true tournament BO3 with sideboard choices, stronger policy testing, larger blind seeds, and card-specific rule certification are still needed.

## Run and reproducibility

Use [the optimization GitHub Action](https://github.com/Dekanje/RB-analyser/actions/workflows/optimization-ismcts.yml). It compiles the pinned C++ engine, runs the algorithm, and uploads all 58 selected decks and the experiment log.

The source is [`scripts/optimize_58.py`](../scripts/optimize_58.py); output files and reports appear in the Action artifact under `optimization/results/`.

The agent and seeds are fixed to keep reruns comparable, but the resulting evaluation may depend on engine/compiler revisions, so cite the Actions run SHA along with any win rate. No result here should be labeled a tournament win-rate prediction.
