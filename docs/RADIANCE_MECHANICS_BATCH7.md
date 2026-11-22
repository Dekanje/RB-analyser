# Radiance mechanics Batch 7 — in-progress, 10 cards

Parent: radiance/mechanics-batch6-2026-11-22 (Batch 6's strict regression is separately gated).
Pinned AlphaRune: chorlick/alpharune@ec90f0fed002aed374d06249fa95e83e3cfbd386.
Draft PR #9; DO NOT merge to main or use in the published 58-legend BO3 ranking before full verification.

## Authored C++ effects
| Engine ID | Numbered code | Card | Actual gameplay mechanism |
| ---: | --- | --- | --- |
| 1001 | RAD-058/167 | Riptide Mage | Accelerate, when-play trigger chooses enemy to lose 3 Might |
| 1002 | RAD-048/167 | High Note | Reaction chooses a unit, decreases Might by number of own exhausted units |
| 1003 | RAD-071/167 | Nazuman Ntofo | Equip for one Energy (no Power), equipped bearer receives Shield 2 |
| 1004 | RAD-072/167 | Overloaded Traveler | +1 Might while friendly Deploy gear is at its battlefield |
| 1005 | RAD-122/167 | Party Crasher | Tank, self Energy cost reduced per own exhausted unit |
| 1006 | RAD-128/167 | Steadfast Outrider | Tank, +2 Might with >=2 other friendly units and/or gear at its battlefield |
| 1007 | RAD-037/167 | Watchful Curator | Friendly gear gain Deflect continuously |
| 1008 | RAD-076/167 | Sneaky Zeebles | Conquer trigger adds one unreactable universal Power |
| 1009 | RAD-117/167 | For Demacia! | Reaction selects battlefield, friendly units there get Shield 2 this turn |
| 1010 | RAD-101/167 | An Offer You Can't Refuse | Action kills chosen gear, its controller plays exhausted Gold token |

## Quality gates
- Phase 1: fast Python/audit preflight on each push; no C++ success claim.
- Phase 2: [check-cards] compiles actual C++ and runs all Radiance card test suites plus compiled registry/canonical catalog audit.
- Phase 3: [batch-ready] runs the full AlphaRune regression (including seed-1 deterministic deck snapshot) with no skipped tests.
- Expected after full integration: **1,010 compiled definitions**, **54/167 numbered Radiance cards**, **113 missing**. These are goals until compiled C++ and audit pass.
- The machine-readable coverage ledger records missing interaction tests for every newly authored card. Do not mark any of the cards completely verified merely due to one test.
- The remaining physically distinct but gameplay-equivalent and gameplay-distinct variants from the 219-entry reference catalog still require review.

## Follow-on test gaps
Combat-based Shield and Tank calculations; opponent-owned gear replaced on death; exhausted-unit dynamic discounts during actual payment; reactive timing/countering; keyword removal and movement timing; Deploy and Deflect interactions; conquest event production; details in radiance/coverage_ledger.py.

## Boundary
All previous 58-deck simulation results remain unchanged and should not be presented as full-Radiance results. The hourly implementation automation remains disabled at user request.
