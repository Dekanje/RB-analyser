# Radiance — experimental original-deck integration

**Updated:** 2026-11-21. **Upstream:** `chorlick/alpharune@ec90f0fed002aed374d06249fa95e83e3cfbd386`.

## Card inventory

- **26/26** source-audited previously missing Radiance cards now have hand-authored C++ implementations on `radiance/engine-mechanics-development`.
- **1** additional Bomb token definition was implemented for Ziggs.
- Together with the 955 pinned upstream definitions, the experimental registry compiles **982 cards**. Evidence: [run #44882395508](https://github.com/Dekanje/RB-analyser/actions/runs/44882395508).
- The source was compiled and compared with card codes/names/types; **compilation is not proof of rules correctness**.
- Original source decklists are not edited, substituted, or modified. Previous 49-deck reports and `main` remain unchanged.

## Game compatibility

| Original Radiance deck | Audited missing cards | Source definitions | Original game vs Kennen |
|---|---:|---:|---|
| Riven | 2 | 2 | Completed |
| K'Sante | 3 | 3 | Completed |
| Evelynn | 2 | 2 | Completed |
| Mordekaiser | 3 | 3 | Completed |
| Jarvan IV | 3 | 3 | Completed |
| Orianna | 3 | 3 | Completed |
| Ziggs | 4 | 4 (+ Bomb) | Completed |
| Ekko | 3 | 3 | Completed |
| Seraphine | 3 | 3 | Completed |

**All nine** original Radiance decks completed engine-resolved games against Kennen with no substitutions in [successful run #44882736908](https://github.com/Dekanje/RB-analyser/actions/runs/44882736908). This proves game compatibility, not full effect/competitive accuracy. The subsequent broader **58-deck, both-seat validation** was triggered in [run #44883114325](https://github.com/Dekanje/RB-analyser/actions/runs/44883114325); its results are pending.

## Engine changes

- Added initial implementations for Riven's ready-entry, K'Sante's Shield-scaled Assault and signature spell, Evelynn's hidden-play trigger and Last Caress, Mordekaiser's restricted Power, death replacement and signature spell.
- Added initial Deploy battlefield placement, attack and hold interactions, Orianna's unit-gear transformation, Ziggs Bomb creation/death and gear damage, Ekko's next-unit cost reduction, replay and turn-end destruction, Seraphine's alternative spell cost with simultaneous exhaustion and Disarm.
- All are **experimental** until deterministic per-mechanic scenario tests, rules cross-checks, and a broader engine regression suite pass. The smoke games alone do not certify the 26 card texts.

## Simulation tooling

- `scripts/validate_58_originals.py`: strict deterministic original-deck validation (58 legends, both seats, deck SHA receipts, no substitution, no fabricated results).
- `scripts/run_bo3_pairings.py`: 1,711 unique pairings including mirrors, sharded and seeded, actual game results, no fictitious wins.
- `scripts/aggregate_bo3.py`: validates shard completeness and aggregates only completed real matches.
- `.github/workflows/radiance-58-compatibility.yml`: full 58 original-deck compatibility gate, activated by an explicit request file.
- `.github/workflows/radiance-full-bo3.yml`: on-demand 16-shard original-deck fixed-list series, gated by all 58 validation receipts.

**Important:** BO3 tooling uses independent real games on fixed original lists, but does **not** implement post-game sideboard swaps. It must not be labeled a fully tournament-accurate best-of-three simulator without sideboarding and comprehensive rules tests. A completed single-game compatibility test does not establish match win probability.

## Remaining acceptance conditions

1. **Passed:** All nine original Radiance smoke tests (run #44882736908).
2. **In progress:** Run all 58 original decks in both seats, preserving source SHA manifests (run #44883114325).
3. Build and execute deterministic card-by-card mechanics tests, including replacement events, targeting/Deflect, Deploy timing, Bomb chains, source-zone changes, simultaneous exhaustion, and end-of-turn effects.
4. Execute broad upstream regression tests and analyze any failed test before merging.
5. Run and label BO3 results with real outcomes and observed statistical uncertainty. Do not merge experimental win rates into verified results prematurely.

No auto notifications or periodic monitoring are enabled.
