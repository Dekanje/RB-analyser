# Radiance 58-deck optimization — evidence checkpoint (21 Nov 2026)

## Final recommendation

**Keep all 58 legality-corrected baseline decks for now.** This bounded ISMCTS
search did not identify any Radiance replacement that passed an independent
blind-seed confirmation at p < 0.05. Do not present this run as fully optimized
post-Radiance deckbuilding or as a complete 58×58 ranking.

## Primary source coverage

- Official Radiance contains 167 base-numbered cards (RAD).
- The SHA-pinned Riot-gallery mirror audit identified all 167; 25 card names
  matched compiled mechanics in the currently pinned AlphaRune engine.
- 142 printed cards have no corresponding compiled match and were **not**
  assigned fake game outcomes.
- 1,542 cost/domain-filtered candidate proposals were recorded, including 143
  compiled-name proposals across the 58-deck roster; proposals are **not**
  engine-proven improvements.
- The legal baseline is 54 unchanged original SHA-pinned decks and four
  separately disclosed legality corrections (Ornn, Lucian, Rengar, Miss Fortune).
- The November 23, 2026 global Standard ban wave is applied (except regional
  exceptions specified in Riot's announcement).

## Executable search

[58-deck ISMCTS upgrade search](https://github.com/Dekanje/RB-analyser/actions/runs/44930045768)
**PASS**: 16/16 shards and aggregation, all 58 decks, 103 experimental
Radiance one-card substitutions. The baseline was never overwritten. The
search used ISMCTS vs ISMCTS with 24 simulations/decision, matched randomized
seeds and sides, and fixed-deck BO3 (without between-game sideboarding).

The training-plus-holdout acceptance filter provisionally selected:

| Legend | Removal | Addition | Training paired BO3 wins (baseline → candidate) | Holdout wins |
|---|---|---|---|---|
| Orianna | Defy | Hush, RAD-041/167 | 0 → 4 /12 | 1 → 4 /12 |
| Vex | Disarming Rake | Reckless Innovator, RAD-105/167 | 0 → 3 /12 | 2 → 5 /12 |

Some other trials encountered card/engine errors, correctly marked incomplete
and not counted as candidate victories.

## Independent blind-seed validation

[Disjoint-seed blind validation workflow](https://github.com/Dekanje/RB-analyser/actions/runs/44930675550)
**PASS** as an executed validation study: 24/24 paired fixed-deck BO3 scenarios
per experimental swap, both seats, six leading opponents, zero incomplete
paired scenarios:

| Legend | Baseline wins | Candidate wins | Change | Paired exact two-sided p | Final decision |
|---|---:|---:|---:|---:|---|
| Orianna | 3 /24 | 3 /24 | 0 pp | 1.0 | Revert to baseline |
| Vex | 6 /24 | 9 /24 | +12.5 pp | 0.453125 | Revert; unsupported |

Tests are unadjusted; both already fail a conventional 5% criterion. This does
not show that the substitutions are bad, only that **we have not demonstrated
a repeatable advantage**.

## Methodology boundaries

- Reproduces actual gameplay in pinned **AlphaRune ec90f0fed...** plus the
  custom Radiance overlay, not an oracle of optimal play.
- The decklists are pre-existing candidates, not exhaustive optimal decks.
- The ISMCTS searcher is stronger than the uniform random agent but not a
  certified professional-player policy.
- No BO3 sideboarding decisions or finalized full Radiance ability coverage.
- Unimplemented cards need correct C++ rule behavior and mechanic-specific
  deterministic tests before they can enter real engine matchups.
- A future full-card-pool optimization must first implement the other 142
  cards, settle the known Mordekaiser/Seraphine search-engine crashes, and
  then retest legality and all matchups.

## Evidence and sources

- [Full numbered Radiance audit](https://github.com/Dekanje/RB-analyser/actions/runs/44929504017)
- [Actual upgrade search](https://github.com/Dekanje/RB-analyser/actions/runs/44930045768)
- [Independent validation](https://github.com/Dekanje/RB-analyser/actions/runs/44930675550)
- [Official Radiance set and dates](https://playriftbound.com/en-us/news/announcements/products-and-sets-into-2027/)
- [Official November 23 ban list](https://playriftbound.com/en-us/news/announcements/radiance-ban-list-updates-effective-november-23-2026/)
