# Full Radiance implementation — first verified-development wave

This branch begins the **real C++ card-rules implementation** requested for full Radiance competitive simulation. It is not a finished set and MUST NOT be substituted into the completed 58-deck ranking until the full set and its interactions are tested.

## First five authored card mechanics

| Card | Printed code | Source C++ ID | Rules implemented | Test |
|---|---|---:|---|---|
| Wrath of the Freljord | RAD-077/167 | 989 | Enters ready, Shield 3 | Engine play + registry |
| Staunch Survivor | RAD-088/167 | 990 | Assault 2 and Shield 2 | Registered combat statistics |
| Supernova | RAD-059/167 | 991 | Targeted 10 damage, then draw 2 | Targeted engine-path spell |
| Avalanche | RAD-079/167 | 992 | 3 simultaneous damage to all units in bases | Engine-path base/battlefield isolation |
| Suave Negotiator | RAD-099/167 | 993 | On play, each player draws 1 | Engine-path triggers and card draw |

The matching source of record for identifiers, cost, domain, and printed effects is the pinned Riot gallery-derived data in **chorlick/alpharune**, pinned commit `ec90f0fed002aed374d06249fa95e83e3cfbd386`, files `cards/json/rad_077_wrath_of_the_freljord.json`, `rad_088_staunch_survivor.json`, `rad_059_supernova.json`, `rad_079_avalanche.json`, and `rad_099_suave_negotiator.json`. Check live errata separately before tournament claims.

## Integration and quality gates

1. The 955 upstream + 33 previous overlay sources remain SHA-pinned and unchanged. This branch adds **five** individual Card classes and registers them as IDs 989 through 993.
2. The workflow compiles the **real** pinned AlphaRune engine, not metadata stand-ins.
3. Six deterministic C++ tests cover registry identities, entering ready, printed combat modifiers, targeted damage + drawing, simultaneous damage in bases, and a when-played draw.
4. Run the entire upstream regression suite after the new tests.
5. Dump the effective registry and reconcile it with every base collector code `RAD-001/167` through `RAD-167/167`. Publish *missing IDs*, not invented completion claims.
6. Publish a gameplay verification report only after tests succeed. All previous match results remain untouched.

The build workflow is [radiance-wave1-implementations.yml](../.github/workflows/radiance-wave1-implementations.yml). Its registry audit outputs `results/radiance_wave1_coverage.json` with the exact unimplemented base card IDs.

## Important boundaries

- **Full set not yet supported.** Registered definitions and valid card names are not enough; every effect must be authored.
- Even a passing deterministic test of one interaction is not full card certification. Include negative tests, replacement effects, priority, unusual states, and all formats as needed.
- Suave Negotiator's opponent choice currently models a **1v1** game; there is only one opponent. Multi-player support requires explicit choice logic and test cases.
- The current engine requires dedicated work for Radiance **Deploy, Disarm, Show Off**, Bomb-token interactions and card-dependent mechanics; batch inclusion must fail closed if an unsupported keyword has functional rules.
- **Do not rerun the 58-legend ranking yet.** Complete the full numbered set, audit any gameplay-different alternate art/rulings, verify bans, optimize all decks using the expanded registry, and then run the BO3 matrix with strategic between-game sideboarding.

## Next implementation batches

Prioritize (a) single-card spell damage/draw, movement and cost rules that the engine already supports, (b) the shared Disarm/Deploy/Show Off engine events and replacement effects, (c) complex champions/legends/tokens/copying/priority, (d) cross-card integration and full regression. Maintain exact missing-ID evidence after each batch.
