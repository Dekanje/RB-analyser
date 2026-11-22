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
