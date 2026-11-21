# RB-analyser — Radiance integration and complete-roster simulation

**Evidence checkpoint: 21 November 2026.** This document records observed GitHub Actions outcomes, not assumed completion.

## Engine and card coverage

- Pinned upstream: `chorlick/alpharune@ec90f0fed002aed374d06249fa95e83e3cfbd386`.
- Compiled source: **988** definitions = 955 pinned upstream + 33 new entries.
- The new entries cover all **26 cards** missing from the nine exact original Radiance decks, six additional Radiance cards required by other optimized decks (Battle Preparations, An Offer You Can't Refuse, Detonation Amplifier, Elnuk Herd, Hush, Shimmering Swimmer), and the Bomb token.
- [C++ compilation and original-deck smoke tests passed](https://github.com/Dekanje/RB-analyser/actions/runs/44887968248). All nine formerly excluded Radiance legends (Riven, K'Sante, Evelynn, Mordekaiser, Jarvan IV, Orianna, Ziggs, Ekko and Seraphine) completed real seeded games against Kennen. Original Azir and Renekton decks also completed tests after implementation of Hush and Shimmering Swimmer.
- **Do not infer card-rule certification from successful compile, registry import, or one game.** Deterministic mechanic-specific test coverage and end-to-end tournament sideboarding remain separate requirements.

## 58-deck compatibility

[Validation run #44888101645](https://github.com/Dekanje/RB-analyser/actions/runs/44888101645) **passed**: 58 decks × two seeded games in both seating orders = **116/116 completed**, zero failed.

The original optimized roster is stored separately, with SHA-256 fingerprints and no in-place edits.

The legally playable simulation roster contains **54 unchanged original decks plus four disclosed corrections**:

| Legend | Original issue | Disclosed candidate correction |
|---|---|---|
| Ornn, Fire Below the Mountain | 3 copies of Unique Forgefire Cape | 3→1 Forgefire Cape; Doran's Shield 2→3; Sterak's Gage 2→3 |
| Lucian, Purifier | Off-domain Chaos Detonation Amplifier | Remove 1 Detonation Amplifier; Crackshot Corsair 1→2 |
| Miss Fortune, Bounty Hunter | Off-domain Fury Elnuk Herd | Remove 1 Elnuk Herd; Scryer's Bloom 2→3 |
| Rengar, Pridestalker | Off-domain Chaos Detonation Amplifier | Remove 1 Detonation Amplifier; Petricite Monument 2→3 |

See `scripts/legal_candidate.py` and the `four_legal_candidates_manifest.json` in the validation artifact for exact original/effective SHA-256 values and each replacement. Each derived main deck preserves 39 cards plus its chosen champion, and the unchanged sideboard. These four decks **must not** be described as unmodified originals.

[Independent fast preflight](https://github.com/Dekanje/RB-analyser/actions/runs/44888585865) passed source SHA checks, correction count, and Python syntax checks.

## 58-deck matrix

[Full fixed-deck BO3 workflow #44888474847](https://github.com/Dekanje/RB-analyser/actions/runs/44888474847) launched after validation. The plan is 58 legends, **1,711 pairings including 58 mirrors**, **two series per pair**, or **3,422 best-of-three series**, sharded across 16 GitHub Actions jobs.

This format does **not** swap main-deck and sideboard cards between games. It is not a complete competitive tournament BO3 model; treat resulting rates as exploratory, particularly with only two series per pairing. Matchups that fail or time out must remain marked incomplete, never assigned synthetic wins.

## Regression gate

The initial extended engine passed 3,633/3,638 tests. The untouched upstream control passed all five suspect tests ([control run](https://github.com/Dekanje/RB-analyser/actions/runs/44887775766)), showing that the discrepancies came from the integration.

Follow-up changes repaired the Demacian Standard no-op trigger, the Back to Back pair-offer validation, source-scan counts, object-ID-dependent Overt Operation prompt ordering, and seeded-deck fixture calibration. Hush's new stricter counter target requires a qualifying `[A][A]` spell in the sweep test.

**Latest patch still requires a green complete regression run.** See [current suite](https://github.com/Dekanje/RB-analyser/actions/runs/44888797193); do not assume it passed before checking the workflow result.

## Change isolation

All changes are on `radiance/engine-mechanics-development`. They overlay a disposable pinned source checkout. The `main` branch, original 58 decklists, and existing 49-deck reports are preserved. Verify official Radiance rulings/errata and sideboard transitions separately before publishing competitive interpretations.
