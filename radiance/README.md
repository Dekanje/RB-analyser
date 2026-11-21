# Radiance integration — source catalog and mechanics coverage

**This pipeline does not yet implement Radiance card effects.** It identifies all available English Riot gallery printings, checks standard numbered card coverage and compares them against AlphaRune's *compiled* C++ card registry.

- Data source: Riot's public card gallery, via the pinned normalized snapshot of [`Dystorted888/riftbound-card-data`](https://github.com/Dystorted888/riftbound-card-data), commit `8a10812968506363a373f36a8bb7cf4d94d02694` (October 26, 2026). Its source code is MIT, but **the Riot card content is excluded from the MIT license**.
- Runtime: `chorlick/alpharune` at `ec90f0fed002aed374d06249fa95e83e3cfbd386` (October 16, 2026). Engine registry contains 955 hand-authored classes. Upstream README licenses are TBD.
- Coverage: `radiance_reports/radiance_printings.json` contains minimal metadata and hashes of rules text rather than republishing card text. `unique_gameplay_cards.json` is a provisional fingerprint grouping; verify mechanics and printings before implementing. `radiance_coverage.csv` distinguishes a registered exact printing from name-only matches and missing classes. Even an exact registration is **not** evidence that the card effect is correctly implemented.
- Scope: base Radiance set numbering has 167 entries; different editions, overnumbered, signatures, promo, runes and legends may increase the number of printings. Do not silently equate printings to unique effects.
- Gameplay gate: until card-specific engine implementations, tests, setup/timing and relevant keyword mechanics pass, `mechanics_verified` is `false`, and results cannot be called accurate simulations.

## Mechanical implementation work

Cards still need exact actions, chain timing, triggered/replacement effects, tokens, interactions and Radiance-specific keywords **Show Off, Deploy and Disarm**, not just a static JSON record. The nine Radiance legends also require their champion and signature card semantics. Keep source decks unchanged, and keep new entries out of live matchups until certified. See [`docs/RADIANCE_ENGINE_INTEGRATION_BACKLOG.md`](../docs/RADIANCE_ENGINE_INTEGRATION_BACKLOG.md).

## Run

GitHub Actions → **Radiance gallery import and gameplay coverage audit** → Run workflow. It will download the pinned sources, reuse the cached AlphaRune binary and upload catalog/coverage artifacts. No PC, local build or paid service is required.