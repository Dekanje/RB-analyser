# Radiance Batch 8 — 15-card validation candidate

**Baseline:** Batch 7 passed its full regression at 1,009 compiled engine card definitions,
with 53/167 numbered Radiance cards registered.

**Candidate target:** 1,024 compiled definitions, 68/167 distinct numbered Radiance cards
registered, 99 not yet implemented.

All 15 Batch 8 C++ card implementations are present on the development branch,
but **do not call this batch accepted until the final full-regression workflow passes**.

**Measured targeted test gate (run 45060798628):** 18/18 dedicated Batch 8
scenario tests passed. Compiler cache: 116/121 hits (95.87%), with a 54-second
C++ build. This is evidence for the targeted scope only; the deterministic
seed-deck fingerprint and final full regression are still separate checks.

## Included mechanics

| Set code | Card | Engine ID | Tested behavior |
| --- | --- | ---: | --- |
| RAD-002 | Banner of Conquest | 1010 | Deploy; Assault aura limited to same battlefield |
| RAD-025 | Consult the Heavens | 1011 | Reaction Shield 2 and Predict |
| RAD-026 | Entrenched Boar | 1012 | Optional ready entry, movement restricted |
| RAD-034 | Hunker Down | 1013 | Ready, cannot move, draw |
| RAD-118 | Herald of the Emperor | 1014 | Change friendly unit base Might this turn |
| RAD-095 | Momentary Companion | 1015 | Hidden, off-turn Temporary |
| RAD-007 | Rally for War | 1016 | Occupied enemy battlefield, three Recruit tokens |
| RAD-024 | Blossoming Dreamroot | 1017 | Deploy, draw when controller wins combat here |
| RAD-027 | Iridescent Avian | 1018 | Exhaust to Buff; +2 temporary Might if already buffed |
| RAD-030 | Sanctum Conservator | 1019 | Ready after a card with printed Energy cost 7+ |
| RAD-036 | Storm Raptor | 1020 | Deflect; stunned enemy death here triggers draw |
| RAD-039 | Ephemeral Ward | 1021 | Global friendly +2 Might, dies on friendly unit play |
| RAD-052 | Resource Extractor | 1022 | Deploy, Gold at end of turn while controlling battlefield |
| RAD-056 | Improvised Projectile | 1023 | Choose friendly gear then battlefield unit; damage based on printed cost |
| RAD-100 | The Waters' Wage | 1024 | Exhausted Gold; conditional three ready Gold when played face down |

The custom gameplay code is in three C++ source files for IDs 1016–1024
plus the previously implemented IDs 1010–1015. The overlay registers
each distinct ID and contains special engine dispatch for Deploy and
combat-result triggers. The registry verification rejects missing
identities, unexpected duplicate public codes and mismatched metadata.

## Validation contract

Push prefixes select validation scopes:

- `[test-fix:Suite.Test]`: preflight, compile tests, **one named test**.
- `[test-fix]`: preflight, compile tests, **all Batch 8 tests**.
- `[check-cards]`: all Radiance tests and strict compiled registry/catalog audit.
- `[batch-ready]`: all above plus full engine regression, mandatory for acceptance.

The safe precompiled-header cache launcher and explicit cache saving
are configured for subsequent iterations. A cold build can still take minutes.

**Limits:** Registration is not proof that every real game interaction is
correct. Full-set Radiance gameplay and 58-legend BO3 analyses remain
blocked while other cards are missing; this document describes Batch 8 only.
