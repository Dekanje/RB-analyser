# Known limitations
- Branch fragmentation: main is behind the active research branch; do not merge experimental code without audit.
- AlphaRune upstream licensing marked TBD in README; verify actual license and distribution rights before redistribution.
- Registered identity != mechanics correctness. Historical QA reports 37 unresolved edge-case coverage questions, one disabled upstream test, unverified variant equivalence; reconcile with subsequent fixes, do not label all cards certified.
- Priority native certification and screening artifacts independently inspected for integrity; not fresh gameplay reproduction. Older holdout shards and full historical corpus remain unaudited.
- ISMCTS strength and real-human calibration not established by workflow success. Audit hidden observations and search budgets.
- BO3 policy is partial: supplied rather than learned sideboards; clocks and full tournament modeling incomplete per source.
- Latest coordinated multi-card screen is training-only; no adoption without independent validation.
- Full Swiss, tiebreaks, intermediate qualification, playoff seeding, format versions and championship optimization not yet certified.
- Local PC hardware/throughput, checkpoint recovery and resource budgets unknown. No guaranteed global optimum; simulation confidence intervals exclude systematic engine/pilot bias.
- Public repository: do not publish secrets, private deck results or full protected text without authorization; visibility unchanged.

- Existing Swiss threshold sensitivity script is a hypothetical independent-match projection, not actual Swiss pairings, cut or playoff logic. Existing workflow branch/path filters and pinned artifacts make mass deletion or renaming unsafe until dependency audit.

- Sideboard-only changes can alter Game 1 winner at the same numeric seed (183/696 training, 56/288 holdout). Cause not established; isolate RNG and initialization before causal tech evaluation. See docs/P0_01_ARTIFACT_AUDIT.md.

- P0-02: historical order confound established (135/174 sideboard candidates reordered playable sections; all 239 mismatches occur in reordered group). Direct sideboard RNG coupling not demonstrated. Corrected serialization and native replay gate pending; preserve historical evidence. Archived binary cannot run in current sandbox without libboost_context.so.1.83.0; clean build/version lock and upstream redistribution rights unresolved. See docs/P0_02_ARCHITECTURE_AUDIT.md.

- P0-02R scoped correction accepted: 8/8 native comparison cases, 32 games; no corrected trace mismatch. This verifies the ordering defect and repair within sampled conditions, not universal determinism. Historical screening scripts remain unchanged; no rerun for adoption. Future v2 screening needs manifest and strict ordered-input gate plus fresh native certification.

- P0-03 historical inventory independently verified; no official all-set legal pool or print equivalence certification. 1059 definitions lack explicit Final64-style mapping, not proof of absent implementation; 37 historical edge-case questions and 52 nonbase RAD printing equivalences remain open. 20 duplicate-name groups need identity review, and 12 historical compiled ban flags require dated official format comparison. See docs/P0_03_CARD_EVIDENCE.md and docs/CARD_COVERAGE.json.

- Current Standard native legality mismatch: archived compiled registry has 12 of 22 official bans effective 2026-11-23. Python optimizer knows all 22 but BO3 pool validator does not include battlefield bans and other entry points need audit. Versioned profile/auditor accepted; no production enforcement correction yet. See docs/P0_03_STANDARD_BANS.md.

- P0-03R first slice implemented on isolated branch: explicit format gateway for new native single games/fixed BO3. Scoped receipt accepted (56/58 preflight, 22 ban controls and four native games); tournament sideboarding and legacy entry-point migration not implemented. Direct historical binary still has only 12 native bans. Ambiguous names must be resolved explicitly; no roster exclusions permitted for production optimization. See docs/P0_03R_FORMAT_GATEWAY.md.

- Ahri, Inquisitive (119/539) and Yasuo, Windrider (205/546) have ambiguous compiled names and different tags. Historical parser receipts now confirm OGN IDs 119/205 and explicit registrations match sampled behavior; alternate-print equivalence remains unresolved.

- P0-03R slice 2 implemented on isolated branch: scoped native resolved vectors and declared BO3 validation accepted; 58/58 preflight and seven native games. Only one approved ban profile pinned; additional format approvals, direct native enforcement, full official catalog, wider optimizer/tournament integration and broad native roster certification remain outstanding.
