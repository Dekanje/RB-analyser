# P0-03 — Historical card evidence inventory
2026-11-24. [CI run 45305366242](https://github.com/Dekanje/RB-analyser/actions/runs/45305366242) completed successfully at ed286c34b520e4d010d4077c08119346252a6a0b. Six unit tests and full historical inventory generation passed. Artifact 14879939071 archive SHA-256 475df235e78e19fd29544b0856c14cc1470c8940485bd1a767df9a4cfd7120d3; ledger SHA-256 3a02ed25f358642f7287b90f1fd7a17874d0d757173a51d600f4687b00a1b7ea. Independent local inspection recomputed archive, registry, and XML hashes; checked every engine identity, code, set/type, token and ban marker against the archived registry; verified all mapped test IDs were enabled, completed and without failure/error/skipped flags. No fresh native games or C++ changes. 
## Results
- 1123 engine identities, 1122 nonempty public codes, 20 duplicate-name groups. One token (Shadow Clone, VEN engine ID 955) has no public code. Ten compiled token definitions overall. Twelve compiled ban flags are historical evidence, not a current official ban list.
- 298 OGN, 24 OGS, 234 SFD, 231 UNL, 168 VEN, 168 RAD. 58 legend definitions. All 167 numbered Radiance codes registered.
- 219 catalog printings: 167 numbered base cards, 18 letter variants, 17 overnumbered and 17 special/rune entries. All 52 nonbase entries remain unresolved; not evidence of 52 missing mechanics. Fifteen letter variants have different raw rules-text hashes, three equal. Raw hash equality/difference is not normalized rules equivalence.
- 64 explicit scenario-mapped cards with 144 links to passing tests. 1059 other compiled entries lack this exact explicit mapping, not necessarily unimplemented or untested. Historical WAVE1 short-name links recorded separately. All 37 historical questions remain open.
- 3917 regression cases enumerated, 3916 enabled passing, one suppressed CardTestFixture.DISABLED_BaronNashor_AuraGivesFriendlyUnitsPlus2M. Actual XML confirms both RadianceFinal64Test.QABaronNashorAuraAffectsOtherFriendlyUnits and QABaronNashorAuraStacksWithHeimerMechReplacement passed; disabled upstream test remains distinct.
## Reproduce
Use registry.json from artifact 14869638175 and all_tests.xml from artifact 14869653235, pinned QA commit c35ceffa290056764df410ea38f97e01f2654031.
```bash
python3 -m unittest discover -s audit -p 'test_card_evidence_inventory.py' -v
python3 audit/card_evidence_inventory.py --registry /path/registry.json --xml /path/all_tests.xml --catalog radiance/data/radiance_catalog.json --acceptance radiance/final64/mechanics_acceptance.json --historical-ledger radiance/coverage_ledger.py --output results/p003/card_evidence.json
```
The generated artifact contains the detailed ledger; [CARD_COVERAGE.json](CARD_COVERAGE.json) retains the summary and hashes. Preserve authorized artifact copies before expiration.
## Scope and next steps
Historical inventory gate passed. Full P0-03 remains open: compare against authoritative dated all-set catalog, resolve format legality, printing/token equivalence, expand evidence mapping. P0-04: reconcile 37 historical questions against actual enabled tests and test bodies, add focused tests where absent, investigate disabled Baron test. Do not infer official legality or complete rules correctness.
