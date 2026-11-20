# Radiance card-engine integration backlog

## Scope and evidence

Source build: `chorlick/alpharune` at `ec90f0fed002aed374d06249fa95e83e3cfbd386`, with 955 compiled card definitions.

Full card audit: [GitHub Actions audit](https://github.com/Dekanje/RB-analyser/actions/workflows/alpharune-card-audit.yml).
Compatibility candidate validation: [49/58 playable](https://github.com/Dekanje/RB-analyser/actions/runs/44839916541).
This backlog is **not** evidence of playable implementations.

Nine Radiance legends cannot currently be simulated accurately in this AlphaRune snapshot. Do not silently replace a Legend, Chosen Champion or signature card and call the outcome equivalent.

| Legend | Missing components encountered by original deck |
|---|---|
| Ekko, Boy Who Shattered Time | Ekko, Boy Who Shattered Time; Ekko, Revolutionary; Chronobreak |
| Evelynn, Agony's Embrace | Evelynn, Agony's Embrace; Last Caress |
| Jarvan IV, Exemplar of Demacia | Jarvan IV, Exemplar of Demacia; Jarvan IV, Royal Heir; Demacian Standard |
| K'Sante, Pride of Nazumah | K'Sante, Pride of Nazumah; K'Sante, Courageous; Ntofo Strikes |
| Mordekaiser, Iron Revenant | Mordekaiser, Iron Revenant; Mordekaiser, Twice Slain; Realm of Death |
| Orianna, Lady of Clockwork | Orianna, Lady of Clockwork; Orianna, Exquisite; The Ball |
| Riven, The Exile | Riven, The Exile; Blade of the Exile |
| Seraphine, Starry-Eyed Songstress | Seraphine, Starry-Eyed Songstress; Seraphine, Inspiring; Encore |
| Ziggs, Hexplosives Expert | Ziggs, Hexplosives Expert; Ziggs, Short-Fused; Hexplosive Minefield; Reckless Innovator |

These names refer to the exact source decklists; more in-game dependencies may emerge once the first missing definition is implemented.

## Required implementation work

1. Verify each printed card and its effective text against Riot's official gallery and errata. Store a provenance record, set/number, revision and relevant core-rules section. Do not infer effects from names.
2. Add the missing card definitions and actual mechanics to a branch of AlphaRune. The public gallery `card_index.json` is **not** the compiled simulation registry; use `riftbound --dump-registry` for the engine's effective card list.
3. Implement each Legend's triggered/static behaviors, Chosen Champion effects, signatures, tokens and any new Radiance keywords. Update cross-card mechanics as needed.
4. Write deterministic unit and integration tests for each card, including combat, reaction windows, alternate game states, card movement, and unusual interaction cases.
5. Pass the original unmodified deck through AlphaRune's deck validator and through at least one deterministic fully resolved game. Check main-deck, sideboard, rune, Battlefield, Unique, domain and effective-ban legality.
6. Add incremental smoke tests in GitHub Actions. Enable these Legends for the matrix **only** after exact engine semantics and tests have passed. Record unsupported/stub effects separately.
7. Re-run full opponent matrices using identical agents and enough repetitions for uncertainty estimates. Three engine games without between-game sideboarding are not a full tournament best-of-three match.

## Current deck compatibility strategy

All 58 original decklists are preserved in `data/optimized_58_decks.json.gz.b64`.

Exactly ten non-Radiance candidates have explicit substitutions in `compat/replacement_manifest.json`. The corrections address unknown individual cards and Ornn's illegal three-copy Unique gear. They are labeled *engine-compatible variants*; their outcomes are **not** exact outcomes for the original optimized lists.

The other nine Radiance decks remain **not simulated**. The `all_58_deck_status.csv` and `all_1711_pairings_with_status.csv` reports in the compatibility-matrix artifact explicitly distinguish simulated matchups from unsupported ones.

## Distribution and policy notes

AlphaRune's upstream README lists its license as TBD: do not presume derivative distribution permission. Riot's [Digital Tools Policy](https://developer.riotgames.com/docs/riftbound) restricts public apps that automate rules enforcement. Keep research tooling distinct from public game clients and review the relevant permissions before publishing or integrating it with a website.
