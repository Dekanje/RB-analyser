# P0-01 — Priority historical artifact audit (2026-11-24)

Scope: historical evidence, not fresh native simulation. Active pre-audit head 1c1f014ec90b8bc194e19ca07e16c59c46131811. Downloaded ZIPs, checked SHA-256, parsed manifests and receipts, recalculated candidate scores and sideboard holdout statistics. No deck changes adopted.

## Archive provenance
| Run | Artifact | SHA-256 |
|---|---:|---|
| 45297203812 | 14877427266 | bad172ebf23d6483e6bd9a494ca9456732a0715a1731f2b84087376521d959d2 |
| 45297203812 | 14876264231 | a5d32b825dc5f3398780832c681895769eaabe0edd2fc67c05ae6bdf37698008 |
| 45283891778 | 14871286569 | f23f12baefa5df960dfd635c69a792d3835798f1073be0cb1ca88b074c5e780e |
| 45283891778 | 14870734087 | 9676904a30a8252ce3cb28077e7dda18327fd4d8915ce2229b0b3e4c851e0a32 |
| 45283891778 | 14869544409 | 16e45a206eee7ee998dfe3a99d440b31c4e45dd3c1516cb384a34f2d07a7e6e9 |
| 45283891778 | 14872476356 | 5a1ac6f7c9d072d8a33e6ca7b587dc4bb7b4fa57215b9347bb62687576c28dc0 |
| 45282108093 | 14869653235 | 7eefa909b2325d0845c1d232e66e7271636437cef0e7c6967f20c41763a3f5a4 |
| 45282108093 | 14869638175 | 38505daf7a8578d82aedb0322046a0153b37fbca98376d54af2904da7101f025 |
| 45276116223 | 14866902212 | 93b6bfe742a120eaada240c08574f9fc3637ad925c457e370b828ebd80d6ac80 |

Archive hashes match observed GitHub metadata. All 31 jobs in [synergy screen](https://github.com/Dekanje/RB-analyser/actions/runs/45297203812), 76 in [recertification and sideboard evaluation](https://github.com/Dekanje/RB-analyser/actions/runs/45283891778), and two in [corrected native QA](https://github.com/Dekanje/RB-analyser/actions/runs/45282108093) reported success. Artifacts expire Dec 23–24, 2026. Preserve authorized local copies and hashes; do not publish raw binaries or deck contents merely to archive evidence.

## Findings
- Corrected executable SHA-256 e49c0e4d97a86805b9d911175b686c53ff348736ee4406c50941fa0d7e88db6a; registry d8102dd0930f466ce16c917035aff15eb21e347879800b08fa334b677f198b89. Computed directly from archived files. Native certification and synergy/sideboard results reference this engine. QA XML: 3917 enumerated, one disabled, zero failures/errors (3916 enabled). Registry report not exhaustive mechanics certification.
- Native compatibility: verified 580 unique candidate hashes with completed native receipts and no errors, covering 58 legends; 229 rune, 174 battlefield, 174 sideboard, 3 champion variants. These are single games, not evidence of deck superiority.
- Synergy training: 348 packages (174 each of depth 2 and 3), 58 legends, six packages each. Verified actual candidate file hashes and proposal manifest hash; reconciled opponent/seat/seed and baseline wins and recalculated all 348 deltas. 1392 candidate BO3 plus 232 reused baseline BO3 = 1624. 151 positive, 111 equal, 86 negative. Agent ismcts:sims=24, seed 202611292015, two frozen opponents, mirrored seats, four cases per candidate, no sideboarding. No independent holdout, no upgrades accepted. Shared baseline and small samples preclude treating observations as independent evidence of strength.
- Sideboard training: aggregate reports 174 candidates, 696 candidate BO3, 232 baseline BO3, 183/696 paired comparisons differed in Game 1 winner despite same main/runes/battlefield/champion and numeric seed. Heuristic one-swap plans. This is a package comparison, not isolated causal tech-card evaluation.
- Sideboard holdout: all 12 individual shard records inspected (288 paired comparisons, 576 BO3). Recomputed exact two-sided McNemar p-values; matched candidate hashes to preregistration; verified disjoint training/holdout opponents and native Rule407 receipt flags. Agent ismcts:sims=128, seed 202611271300, six heldout opponents, two repetitions with mirrored seats; 56/288 Game 1 winner mismatches. Minimum raw p=0.2890625; minimum Holm-adjusted p=1; zero confirmed improvements. No decks modified. Shard archive IDs: 14871941637,14871602400,14872090958,14871343195,14872625348,14872975247,14872910179,14872820821,14872550468,14872310525,14873155580,14872395390.
- Older structural holdout: aggregate reports 288 paired comparisons (576 BO3), 12 hypotheses, zero confirmed; minimum Holm-adjusted p=1. Different native engine SHA-256 58dbebe75c3a55c354056867cfa885cc6a8a589aa511c0984ca524a754ad0807; no actual G2/G3 swaps. Underlying shards and older executable not independently audited. Do not pool with corrected engine.

## Disposition
Retain historical compatibility and regression evidence at its exact revision. Retain synergy/sideboard results for exploratory candidate selection only; zero accepted upgrades in these experiments does not prove no improvement exists. No championship prediction supported. Recheck RNG separation (sideboard registration must not change Game 1 public/hidden initial states, draw streams or equivalent agent behavior under controlled seed), then validate with deterministic native replays; keep aggregate historical comparisons labeled package-level. Prioritize accurate engine and agent strength before expensive campaigns. P0-01 priority artifact audit completed; full Phase 0 gate remains open. Older optimization artifacts and rule coverage are not comprehensively certified. Next P0-02 architecture/build/dependency inventory and RNG risk tracing; P0-03/04 card coverage and interactions follow.
