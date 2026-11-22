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

## Tranche 2 — 12 authored cards, awaiting acceptance CI

| Code | Card | Engine ID | Intended mechanic |
|---|---|---:|---|
| RAD-049 | Industrious Mechsmith | 1028 | Play 3-Might Mech token here |
| RAD-050 | Mysterious Chronomancer | 1029 | Predict 2; Disarm 2 |
| RAD-055 | Clanging Sentry | 1030 | Give friendly Mechs Disarm, stackable |
| RAD-072 | Overloaded Traveler | 1031 | +1 Might while friendly Deploy gear here |
| RAD-076 | Sneaky Zeebles | 1032 | Add universal power on conquer |
| RAD-083 | Stalwart Goatherd | 1033 | Shield 2; optional kill Gear costing up to 4 |
| RAD-093 | Disposal Expert | 1034 | Enter ready when alone; Disarm 2 |
| RAD-097 | Siren of the Shallows | 1035 | Disarm 1; Ganking |
| RAD-099 | Suave Negotiator | 1036 | Each player draws 1 on play |
| RAD-117 | For Demacia! | 1037 | Give Shield 2 to friendly units at chosen BF |
| RAD-119 | Hunting Dog | 1038 | Deathknell Bird token with Deflect |
| RAD-128 | Steadfast Outrider | 1039 | Tank; +2 Might if two other friendlies here |

**Candidate-only registry projection:** 1,039 engine definitions, 80/167 Radiance numbered identities registered, 87 remaining. Neither new card behavior nor registry counts count as accepted until strict CI succeeds.

### Disarm implementation and limitations

The Batch 9 overlay adds `Keyword::Disarm` (bit 25), a name mapping, and an attack-event handler for printed/aura keyword strength. A unit's printed Disarm 2 and multiple Disarm 1 auras combine into a single attack's Might penalty against a chosen enemy unit at the same battlefield, once per combat, and the engine's standard temporary-Might field expires at the turn's end. Gameplay tests cover printed Disarm 1/2, aura stacking and field/owner isolation.

**Known gap:** The current Disarm attack dispatcher asks for an immediate target rather than putting a separate reactable triggered ability onto the combat chain. That means reaction windows and resource costs for selecting protected units (such as Deflect) are not independently certified. These require a proper follow-up before declaring Disarm's interactions completely supported. Do not treat a passing regression as proof that every Disarm rule is implemented correctly.
