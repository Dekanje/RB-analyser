# Radiance nine-deck integration — experimental status

**Evidence date:** 2026-11-21. **Pinned upstream:** `chorlick/alpharune@ec90f0fed002aed374d06249fa95e83e3cfbd386`.

The experimental overlay modifies a disposable upstream checkout; it does **not** change the 58 original optimized decklists or the existing 49-deck compatibility results. It is **not** merged to `main`.

## Evidence

- Baseline: 955 compiled upstream C++ card definitions.
- Experimental branch: **965** compiled definitions, **10 Radiance additions**, verified by [GitHub Actions #44849845334](https://github.com/Dekanje/RB-analyser/actions/runs/44849845334).
- Original deck smoke tests completed vs the unchanged Kennen deck with deterministic seeds: **Riven**, **K’Sante**, **Evelynn**, **Mordekaiser**. A smoke-test pass is not proof that all card interactions work correctly.
- **No competitive gameplay semantics certified**, no complete 58-deck BO3 matrix or post-game sideboard validation.

| Original Radiance legend | Missing cards audited | Experimental C++ definitions present | Original-game smoke |
|---|---:|---:|---|
| Riven, The Exile | 2 | 2 | Complete |
| K’Sante, Pride of Nazumah | 3 | 3 | Complete |
| Evelynn, Agony’s Embrace | 2 | 2 | Complete |
| Mordekaiser, Iron Revenant | 3 | 3 | Complete |
| Ekko, Boy Who Shattered Time | 3 | 0 | Blocked |
| Jarvan IV, Exemplar of Demacia | 3 | 0 | Blocked |
| Orianna, Lady of Clockwork | 3 | 0 | Blocked |
| Seraphine, Starry-Eyed Songstress | 3 | 0 | Blocked |
| Ziggs, Hexplosives Expert | 4 | 0 | Blocked |
| **Total** | **26** | **10** | **4 / 9** |

## Remaining blockers, in required order

1. Implement the **16 remaining unique card definitions** and their engine behavior, with exact published text and provenance (three each for Ekko, Jarvan IV, Orianna, Seraphine; four for Ziggs). This includes substantial new rules features—notably Deploy/Disarm, changing gear into unit gear, Bomb token death chains, triggered and simultaneous payments, and replay/cost-reset interactions.
2. Write deterministic scenario tests for **all 26** newly required mechanics, including the ten experimental classes. Fix discovered rules errors before certifying any of the nine original decks. Check interactions, targeting, timing, hidden information, death replacements, resource restrictions, and boundary turns.
3. Check unmodified deck legality (main deck, runes, battlefields, signatures, Chosen Champion, domain, Unique, effective bans), then run more than one complete game per deck.
4. Run seeded, paired-seat simulations with statistical uncertainty. Distinguish unsideboarded game series from actual competitive best-of-three matches with legal sideboarding between games.
5. Only then enable verified decks in the full 58-deck pairing matrix. Do not silently substitute unavailable cards, silently assume a keyword works, or interpret a successful registry import as implemented gameplay.

## Source locations

- `radiance/engine_overlay/apply.py`: pinned-source engine overlay.
- `radiance/engine_overlay/source/cards/`: hand-authored prototype cards.
- `radiance/engine_overlay/verify.py`: compiled-registry and original-deck smoke checks.
- `docs/RADIANCE_ENGINE_INTEGRATION_BACKLOG.md`: full rules and admission requirements.
- `data/optimized_58_decks.json.gz.b64`: unchanged original decklists.
