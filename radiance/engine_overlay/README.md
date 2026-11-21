# Radiance engine development — experimental

This development branch is deliberately isolated from the verified 49-deck simulations.

Current C++ additions: Riven's Legend (RAD-149/167) with a conditional ready-on-entry engine hook; K'Sante, Courageous (RAD-086/167) with Accelerate, Shield 2 and a Hold trigger that channels a rune.

The workflow compiles the genuine pinned AlphaRune engine and checks its compiled card registry. No card is marked competitively certified by this compilation test. All nine original Radiance decks remain blocked pending implementation and deterministic scenario tests for the remaining effects. Never use metadata-only cards or behavior stubs to generate win rates.

The overlay checks the exact upstream commit before modifying its temporary checkout. No original deck file or prior result is changed.
