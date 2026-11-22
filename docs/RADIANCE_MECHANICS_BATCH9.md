# Radiance Batch 9 — staged mechanics implementation

## Baseline and scope

Batch 9 starts from the **accepted Batch 8** development-branch commit
`0588b5d51cd10457c47a422a60d4e55a4cafce33`: 1,024 compiled engine
definitions, 68 of 167 distinct numbered Radiance identities registered,
and a passing 3,697-test full AlphaRune regression.

The tentative Batch 9 size is **15 new numbered identities**. Individual
tranches are implementation candidates, not accepted batches, until their
engine tests and the strict compiled-card audit pass. Batch-wide acceptance
also requires all 15 to be implemented and a complete regression.

## Tranche 1 — new C++ implementations, pending CI

- **RAD-057 Piltovan Guidebot** (ID 1025): optional base-Might change to the
  **printed** Energy cost of a just-played card, including spells, this turn.
- **RAD-126 Mournful Spirit** (ID 1026): Deathknell optionally kills a unit
  or gear at the Spirit's recorded death location. A real triggered chain
  resolution must choose and pay any target protections.
- **RAD-073 Pillaged Armory** (ID 1027): Deploy Gear buffs a friendly unit
  on play or on a conquer at the Gear's battlefield. The engine's score
  dispatcher is extended to observe Deploy Gear; opposing holds kill the
  deployed Gear.

Expected after tranche 1: **1,027** card definitions, **71/167** Radiance
base identities registered, **96** still absent.

Gameplay tests include printed metadata, optional yes/no, Deathknell,
play- and conquer-time buff, and opponent-hold cleanup. These are **not
considered passing until CI reports success**.

## Engine gaps for subsequent tranches

Radiance introduced **Disarm**, whose keyword and combat trigger are
not yet present in pinned upstream AlphaRune. Implementing cards such as
Disposal Expert or Siren of the Shallows requires a new
stackable N-Might attack debuff and tests of attacker selection, Deflect,
combat timing, and end-of-turn expiry. They are not falsely counted as
implemented in tranche 1.

Other unimplemented Radiance cards remain open. No all-legend BO3
simulation claim is supported until full card coverage and simulation
accuracy are independently validated.

## Validation contract

The Batch 9 GitHub Actions workflow reuses the staged architecture:

- Ordinary commits: fast source and catalog preflight only.
- `[test-fix]`: compile and run all dedicated Batch 9 tests; a named
  `[test-fix:Suite.Test]` runs only the named regression.
- `[check-cards]`: all Radiance focused tests and strict compiled
  registry/catalog audit.
- `[batch-ready]`: all of the above plus mandatory full AlphaRune
  regression before any claim of full Batch 9 acceptance.

C++ compiler artifacts are cached using the PCH-safe launcher and a
Batch 9 cache key, restoring compatible Batch 8 entries on the first
cache-assisted build.
