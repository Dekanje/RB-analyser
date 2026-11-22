# Radiance Batch 10 — 20 new numbered card identities

Branch: `radiance/mechanics-batch10-2026-11-22`.
Baseline: Batch 9 full-regression acceptance (3,733/3,733 tests, 83 unique Radiance base identities).
Pinned upstream AlphaRune engine: `ec90f0fed002aed374d06249fa95e83e3cfbd386`.

## Authored in Batch 10

| Engine ID | Canonical code | Card | Functional status |
|---|---|---|---|
| 1048 | RAD-013 | Lost to the Sands | Initial spell effect; mode and targeting timing to verify |
| 1049 | RAD-035 | Invigorating Bloom | Play-time +3 Might; activated draw pending |
| 1050 | RAD-038 | Ahri, Confident | Disarm keyword; reaction to enemy Might reduction pending |
| 1051 | RAD-051 | Parallel Convergence | Bounce and damage; additional-cost timing pending |
| 1052 | RAD-070 | Hold 'Em | +3 Might effect; cost reduction pending |
| 1053 | RAD-087 | Portable Portal | Deploy/Ganking aura; optional play-time cost pending |
| 1054 | RAD-089 | Titanic Shrine | Play trigger draft; reaction timing/choice pending |
| 1055 | RAD-096 | Satchel Charge | Bomb token and move mechanics pending |
| 1056 | RAD-106 | The Good Stuff | Deploy and play/hold triggers; choices to verify |
| 1057 | RAD-107 | Bedeviling Stranger | Hidden and conditional bounce; battlefield-choice locking pending |
| 1058 | RAD-005 | Lingering Animus | Conditional enter-ready death history pending |
| 1059 | RAD-001 | Amateur Demolitionist | Play-time Bomb gear token using existing token effect; targeted gameplay test added |
| 1060 | RAD-028 | Ki Burst | Initial exhaust/stun; true additional-cost timing pending |
| 1061 | RAD-029 | Life from Stone | Initial exhaust/draw/channel; true additional-cost timing pending |
| 1062 | RAD-040 | Heartening Soul | Ready legend; legend activated-ability grant pending |
| 1063 | RAD-047 | Fanfare | Delayed next-three-unit trigger pending |
| 1064 | RAD-061 | Ekko, Ingenious | Ganking; return-unit-as-cost pending |
| 1065 | RAD-075 | Skystrike Squadron | Deflect; optional bounce and reduced cost pending |
| 1066 | RAD-116 | Concert Poster | Deploy; optional Recruit-token cost/creation pending |
| 1067 | RAD-121 | One-Two Punch | Initial Buff/Stun effect; lock/play-time targeting to verify |

The above is a **staged implementation, not twenty fully verified rules implementations**.
Every card has source-level printed identity and keyword metadata. Some have initial
mechanics implementations, while the explicit gaps above must be closed through
engine-path tests before Batch 10 can be fully accepted.

## Collision correction and validation scope

Batch 10 originally attempted to re-register RAD-021 (Ekko, Revolutionary) at
engine ID 1059, even though the earlier Ekko package already implements
RAD-021 at ID 967, including its activated ability. The duplicate definition
was replaced with RAD-001 (Amateur Demolitionist), keeping the 20-card
unique-identity goal. RAD-001 uses printed Fury, 2 Energy, 1 Power and 1 Might,
with its existing Bomb token defined at engine ID 982. Its Bomb play trigger
now has a dedicated gameplay test. The compiled registry, all twenty intended
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
