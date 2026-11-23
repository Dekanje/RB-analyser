# Radiance final 64 — implementation status

Target: all base cards RAD-001/167 through RAD-167/167 registered uniquely in AlphaRune.
This is one final batch, not a series of partially accepted batches.

- Accepted starting revision: `ce2916bcfede3d79f02060a97e4063676a1c3eef` (Batch 10).
- New definitions: engine 1068–1131, 64 cards, based on corrected printed metadata.
- Compiled registry target: 1,123 definitions; 167/167 base Radiance.
- Gameplay acceptance: NOT YET REACHED. Each card requires accurate effects and
  explicit engine-path scenario tests, plus full AlphaRune regression.
- The `mechanics_acceptance.json` check must fail closed until all 64 entries
  have independently passing effect scenarios. No metadata-only test qualifies.
- Do not disable or weaken existing tests to obtain a passing CI status.
- Source data contains errors (including printed card types, domains and Runeblade
  Anvil's kill cost); `manifest.json` records verified corrections.

## Next technical gate

Compile the complete one-batch registry, then implement all 64 distinct
mechanics. Validate resource payment, delayed effects, optional choices,
target finalization, hidden information, replacement effects, token play and
deck construction; finally run the complete suite and reach zero failures.

## Compiler fixes and early mechanics wave

Four distinct compiler helper names resolve the AlphaRune unity-build duplicate
symbol failure identified in run 45082063224. Implementations and initial
engine-path tests are in place for Raucous Anthem, Burn Away, Demacian
Illuminators, Explosimian, Evelynn In Control, and Pitiless Stalker.
This is a **work-in-progress test run**, not final gameplay acceptance.

## Second mechanics expansion

Adds shared Show Off choices and public reveal accounting; genuine deck-top
reveal handling; reactable exhaustion triggers; effects for Incorrigible
Construct, Forbidden Technique (normal cast), Coalesced Energy, Firebrand
Raider (entry/play), Stoic Ferryman, Hunting Blind, Rostrum, Oracle,
Empyrean, Scope, Raving Witness, Primordial Roar, Cataclysm, Evelynn,
Jarvan IV, Explosimian, Gutter Guardian, Stalker, Lulu pending, Mechanical
Bandit, Riven's exhaustion trigger, Rousing Display, Seraphine and more.
Some listed cards have pending additional clauses; **no 64-card acceptance yet**.

## Third mechanics wave

Implemented additional Scorched Earth split damage, Drakehound Packmaster
opponent-card play, Seraphic Wyvern channel replacement, Conquest tracking,
Mind/Body/Chaos spells, Show Off as-you-play spell core hook, Bushwhack Trap
facedown capacity, and multiple activated unit abilities with real engine-path
scenarios. Full compilation, correctness and regression remain unverified.

## Focused test failure correction — 23 November 2026

GitHub Actions run 45094719006 compiled all 64 added definitions, but the
focused test suite passed only 164/167 cases. The three failures are now
corrected in the test's engine-path setup: Scorched Earth must choose a
battlefield before its split-damage target; Armored Tusker must explicitly
choose the enemy after opting into its optional trigger; and Bushwhack Trap
must have a friendly unit actually maintaining control through engine cleanup.
These are scenario/fixture corrections and are **not** claims that the 64
mechanics have been accepted. Re-run the complete focused suite, strict
compiled-registry check, and independent mechanics acceptance after that.

## Full-regression baseline after focused registry success

After run 45095743580 passed all 167 focused tests and compiled 167/167
unique Radiance base identities, the team is running the full upstream
AlphaRune regression. The separately tracked 64 card-by-card mechanics
acceptance records are still pending; the final workflow must fail closed
until comprehensive printed-effect tests exist and pass. Keep full-regression
failure logs separate from mechanics acceptance. This is a diagnostic run,
not a declaration of final acceptance.

## Remaining-mechanics development branch

After the first full-regression run (45096185998) failed 4 of 3,805 tests,
RAD-125 Dune Devourer has a cast-time optional kill-and-discount effect and
RAD-123 Protector's Shield now declares its real Equipment, Quick-Draw,
Reaction and [1] Equip behavior. Four new dedicated tests were added.
Those edits remain provisional until compiled CI proves them. The known
regression failures remain open and the final64 mechanics ledger is pending.

## Full regression triage — run 45096185998

- Focused Radiance 167/167 PASS and 167/167 compiled base identities PASS.
- Full AlphaRune regression: 3,801/3,805 PASS; four failures, not accepted.
- HiddenOrderLeak.PositionsTheDeciderCannotTellApartShowItTheSame:
  identity-dependent action IDs/observations for hidden card variants in random
  decks 1029/5029, seed 20261043; root cause still under investigation.
- ActionIdsWalk.NoTwoLegalIntentsShareAnId_DecksFromTheWholePool:
  80 knowledge-tracker inconsistencies in pool-deck walk, first in deck 47
  (Matriarch of War) versus next at seed 7047, decision 157; unresolved.
- LedgerTest.Defs_APermanentHasReactionOnlyWhenTheCardItselfDoes:
  RAD-123 Protector's Shield missing Reaction keyword; corrected on the
  development branch alongside Equipment classification, Might bonus,
  functional [1] Equip cost and engine-path tests.
- DeckFuzz.DeckOfSeedOneIsPinned: measured 1,123-card hash
  2700713930748140182; this work branch pins that hash for exactly 1,123
  definitions, preserving previous size-specific pins.
- RAD-125 Dune Devourer optional kill-as-cost and RAD-045 K'Sante's triggered
  Shield doubling also have development implementations and tests.
- The 64-entry per-card mechanics ledger is still *pending*; none of these
  fixes silently changes acceptance flags or removes regression tests.

## Consolidated full regression — zone fixes and paid gear cost

All three revealed-top recycle paths now take the card out of Main Deck before placing it at bottom, preventing duplicate deck/hand IDs. Original hidden-order reproduction passed on diagnostic branch (run 45101910298). Whirling Twirligig's gear sacrifice now uses a true cost-object selection and its targeted engine test passed on run 45102040885. This branch must pass focused, all AlphaRune tests, and 64-card mechanics acceptance separately; the final64 ledger remains fail-closed.
