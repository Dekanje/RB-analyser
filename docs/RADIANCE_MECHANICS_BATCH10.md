# Radiance Batch 10 — 20 new numbered card identities

Branch: `radiance/mechanics-batch10-2026-11-22`.
Baseline: Batch 9 full-regression acceptance (3,733/3,733 tests, 83 unique Radiance base identities).
Pinned upstream AlphaRune engine: `ec90f0fed002aed374d06249fa95e83e3cfbd386`.

## Authored in Batch 10

| Engine ID | Canonical code | Card | Functional status |
|---|---|---|---|
| 1048 | RAD-013 | Lost to the Sands | Choose eligible gear or battlefield unit at finalization; effect test added, CI pending |
| 1049 | RAD-035 | Invigorating Bloom | Play-time +3 Might plus Mighty-unit exhaust activation and draw; test pending |
| 1050 | RAD-038 | Ahri, Confident | Disarm and new reactive enemy-Might-reduction event at same battlefield; gameplay test pending |
| 1051 | RAD-051 | Parallel Convergence | Mandatory friendly-unit return is a play-time cost; battlefield damage chosen at finalization; test pending |
| 1052 | RAD-070 | Hold 'Em | +3 Might and -2 Energy conditional on tracked battlefield permanent play; tests pending |
| 1053 | RAD-087 | Portable Portal | Deploy/Ganking aura and optional Body Power ready effect at trigger finalization; test pending |
| 1054 | RAD-089 | Titanic Shrine | Pay exhaust at trigger finalization, then draw on resolution; test pending |
| 1055 | RAD-096 | Satchel Charge | Play-time selected friendly move and Bomb gear token placement; test pending |
| 1056 | RAD-106 | The Good Stuff | Deploy, discard/draw play trigger and self-return hold trigger; tests pending |
| 1057 | RAD-107 | Bedeviling Stranger | Battlefield choice finalized before reactions; conditional optional enemy bounce; test pending |
| 1058 | RAD-005 | Lingering Animus | Enter-ready checks friend unit or killed gear this turn, with gear death event hook; test pending |
| 1059 | RAD-001 | Amateur Demolitionist | Play-time Bomb gear token using existing token effect; targeted gameplay test added |
| 1060 | RAD-028 | Ki Burst | Exhaust-friendly-unit as cast-time additional cost; target/stun integration tests added, validation pending |
| 1061 | RAD-029 | Life from Stone | Exhaust-friendly-unit as cast-time additional cost; draw/channel integration test added, validation pending |
| 1062 | RAD-040 | Heartening Soul | Readies friendly legend and grants exhausted +3-Might activated ability; engine-path tests pending |
| 1063 | RAD-047 | Fanfare | Delayed repeat trigger draws for up to three unit plays this turn; gameplay test pending |
| 1064 | RAD-061 | Ekko, Ingenious | Mandatory return-unit-as-play-cost and Champion metadata implemented; test pending |
| 1065 | RAD-075 | Skystrike Squadron | Optional friendly-gear bounce for -2 Energy implemented; test pending |
| 1066 | RAD-116 | Concert Poster | Optional 1 Energy cost at trigger finalization and Recruit token in base implemented; test pending |
| 1067 | RAD-121 | One-Two Punch | Friendly Buff / enemy Stun targets locked at spell finalization; test pending |

The above is a **staged implementation, not twenty fully verified rules implementations**.
Every card has source-level printed identity and keyword metadata. Some have initial
mechanics implementations, while the explicit gaps above must be closed through
engine-path tests before Batch 10 can be fully accepted.

## Collision correction and validation scope

Batch 10 originally attempted to re-register RAD-021 (Ekko, Revolutionary) at
engine ID 1059, even though the earlier Ekko package already implements
RAD-021 at ID 967, including its activated ability. The duplicate definition
was replaced with RAD-001 (Amateur Demolitionist), keeping the 20-card
unique-identity goal. RAD-001 uses printed Fury, 2 Energy, 0 Power and 1 Might,
with its existing Bomb token defined at engine ID 982. Its Bomb play trigger
now has a dedicated gameplay test. Ki Burst and Life from Stone also use
play-time unit-exhaust additional costs instead of incorrectly paying during
resolution, with dedicated tests. These tests must still pass in compiled CI. The compiled registry, all twenty intended
base identities, and the full regression still require GitHub Actions proof.

## Planned gates

1. All twenty newly registered with exact unique public codes and engine IDs (1048–1067);
   no duplicate prints or shadow card registrations.
2. Compiled registry size 1,059; 103 of 167 Radiance base identities present; 64 missing.
3. Focused Batch 10 gameplay tests, including optional costs, trigger timing and stack
   interactions for every one of the twenty cards, with failures fixed instead of skipped.
4. Complete AlphaRune regression with all earlier tests and reproducible seeded-deck
   fingerprint for the new card pool.
5. Catalog/variant evidence ledger remains noncertifying until mechanics are proven.

**No 58-deck BO3 simulation results are claimed while the remaining 64 Radiance cards
and the listed rules-interaction gaps are unresolved.**

## Additional mechanics-development validation

RAD-047/051/061/075/116 have added effects and engine-path tests in the
batch 10 development branch. These are **not accepted** until the focused
CI run and full AlphaRune regression pass, and their edge cases are audited.

Further engine-path tests have been added for Bloom's Mighty activation,
Satchel Charge movement, Hold 'Em conditional discount, Portable Portal,
Bedeviling Stranger, and Lingering Animus. These are unaccepted until CI proof.

## Final mechanics-wave changes still under test

Added actual event-based Ahri Might-reduction trigger (new trigger enum appended to
preserve earlier IDs), legend-granted activated ability for Heartening Soul,
finalization timing and focused cases for Lost to the Sands, Titanic Shrine,
One-Two Punch, and existing The Good Stuff play/hold clauses. These additions
require compiled gameplay tests and the full regression; they are not certified
by the strict identity registry alone. The coverage ledger intentionally does
not claim all 167 cards or all variants are implemented.

## Batch 10 full-regression candidate

Hold 'Em now counts both ordinary card plays and token unit/gear plays to a
battlefield. The complete 20-card focused gameplay suite, registry audit, and
full upstream AlphaRune regression are mandatory acceptance gates. This is a
**candidate only** until the GitHub Actions full job succeeds and its output
has been inspected. A successful run does not certify unrelated, still-missing
Radiance cards or every possible card interaction.

## Focused failure corrections before full gate

The previous compiled 123-test run passed 120 tests and exposed exactly three
failures. Invigorating Bloom rechecked the cost-exhausted unit at resolution;
now its paid-cost continuation draws without reevaluating the ready-only list.
Portable Portal paid Body Power before collecting its unit target; it now
collects the target before paying, with payment immediately before the finalize
marker. The Good Stuff hold test had an empty deck and could encounter Burnout
from its mandatory three-card draw; the corrected test supplies three cards and
keeps battlefield control. These fixes are **unverified until full CI**.
