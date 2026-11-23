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

## Full regression audit repairs following 45102270144

The previous full run passed 3,823 of 3,825 tests and all 187 focused tests,
with zero missing Radiance base cards. Its ONLY full-suite failures were:

- StrongIds: RAD-136 Dockside Lock-Up's raw GameObjectId stored under
  __dockside_banished_card lacked an explicit matching writer/reader audit
  entry. The pinned engine overlay now extends that audit (plain raw ID,
  missing key means none; reader checks existence and Banishment zone).
- SweepCosts: RAD-033 Command: Attack now explicitly declares it may choose
  friendly on-board Deploy gear in its first mode, and no other board object,
  for finalize-pass card-selection / discount purposes.

These two fixes are now submitted for the exact full AlphaRune regression
without disabling or skipping tests. The separate 64-card printed-effect
mechanics gate remains fail-closed, with 54 pending and 10 in review. A clean
engine-wide result is NOT equivalent to mechanics acceptance.

## RAD-019 Firebrand Raider engine-wide rules

Added both missing continuous effects: all *other* units (regardless of
controller) enter ready while Raider remains in play, and units (but not
runes, gear, or legends) do not ready during any Awaken Phase. Implemented
using AlphaRune's existing cross-player units_enter_ready_by aura index and
a pinned AwakenPhase guard. Two new engine-path tests cover an opponent's
unit entering and the opponent's unit remaining exhausted in Awaken. The
focused execution and full regressions must pass before accepting RAD-019.

Raider overlay preflight repair: the upstream `game_engine.cpp` contains multiple similar turn-player batches. The patch now anchors strictly within `GameEngine::awakenPhase()` before replacing the global-ready loop. No gameplay acceptance was inferred from the earlier failed installation.

## Mechanics acceptance review progress

Six source-reviewed Final64 cards are now marked accepted with dedicated
engine-path scenarios: RAD-019, RAD-031, RAD-044, RAD-124, RAD-127, RAD-134.
The ledger remains **fail closed** at 6 accepted / 10 in review / 48
pending, and MUST NOT report complete until all 64 pass in the full
regression XML. Firebrand Raider's three focused tests passed in run
45103320523. Full regression is required after its global aura and Awaken
hook changes, before considering engine-wide integration stable.

## RAD-125 and RAD-016 adversarial mechanics tests

Dune Devourer's optional kill-as-cost now checks an actual LeftBoardEvent
death via Card::killAsCost. A friendly unit saved by Soraka's death
replacement does not earn the 2-Energy discount. A new real-engine path
tests paid-but-prevented sacrifice and full printed cost. Coalesced Energy's
end-turn test also checks that exactly four runes remain on-board, to catch
accidental duplication during recycle/channel. Pending cached targeted CI.

## Whirling Twirligig replacement-safe Mech cost

Both of the card's sacrifice modes now use actual finalization-time
kill-as-cost with a friendly chosen object, without a target/Deflect charge.
The unit-sacrifice-to-Mech mode must **not** create a Mech if Soraka saves
the sacrificed unit. The focused test covers that replacement and both
normal sacrifices. RAD-022 stays in review until the test is compiled and
passes. The accepted count is 10 (54 still unaccepted).

## Expanded mechanics acceptance after replacement-safe unit cost

Ledger review now has 23 accepted, 6 in review and 35 pending Final64
cards. The most recent standalone Whirling Twirligig pass confirmed 5 of
5 focused tests, including the Soraka prevented-death case (45104538770).
The Dune Devourer and Coalesced Energy adversarial checks also passed
(45104062547). All new card entries are linked to specific full-engine
GoogleTest cases, not identity-only assertions.

Re-run the entire upstream AlphaRune suite and strict registry audit at
this revision, then retain final CI failure only for still-unaccepted
printed mechanics (41 cards).

## 23 November — accepted 52/64, pending 12/64; full regression checkpoint

The accepted per-card ledger now records 52 independently reviewed cards with
passing named AlphaRune engine-path scenarios, up from 23 at the beginning of
this implementation session. Source-level and targeted-CI defects were
corrected, including RAD-111 Mechanical Bandit: only its controller draws
their own revealed card when it has the lowest Energy cost; the opponent's
revealed card is recycled. Positive, negative, tied-cost and ownership tests
all passed.

Focused CI checkpoints (all passed):
- 45127025773 — Incorrigible Construct's valid/invalid Show Off.
- 45127376772 — Scorched Earth and Strigian Oracle.
- 45127670182 — Command: Attack's two modes and Seraphine.
- 45128246359 — Riven, Trifarian Captain, Remember the Fallen and Mordekaiser.
- 45128572504 — Mechanical Bandit, Raving Witness, Primordial Roar, Cataclysm.
- 45128898773 — Ziggs, Riven Deserter and Transpositionist.
- 45129313864 — Gutter Guardian, Empyrean, Spirit, Rostrum and Jarvan.
- 45129782350 — complete 100-test focused Final64 suite; six additional cards accepted.
- 45130151465 — strict Bomb death cascade and token-prohibited Dockside Lock-Up.

Remaining **not accepted** (requires implementing gameplay mechanics and
independent printed-effect tests, not just identity registration):
- RAD-010/167 Forbidden Technique
- RAD-012/167 Runeblade Anvil
- RAD-015/167 Akali, Brash
- RAD-062/167 Gravity Field
- RAD-063/167 Kai'Sa, Rebel
- RAD-068/167 Orianna, Mechanical Marvel
- RAD-120/167 Meticulous Restorationist
- RAD-130/167 Battlefield Armorer
- RAD-132/167 Heimerdinger, Academy Instructor
- RAD-158/167 Black Market
- RAD-163/167 Hunters' Circle
- RAD-167/167 Neeko, Blending In

**The 64-card mechanics acceptance gate must remain FAILED** until all
remaining 12 effects have correct full gameplay implementations and
passing adversarial engine-path scenarios. A passing compiler or upstream
regression alone does not imply complete Radiance simulation support.
Run the full 1,123-definition registry, focused tests, full upstream
AlphaRune regression and separate strict acceptance at this checkpoint;
record each result independently.
