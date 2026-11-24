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

- P0-03R slice 3 isolated roster gate/guarded CLI implemented; scoped all-58 native receipt acceptance passed. CLI currently only supports one pinned ban snapshot and explicit set selection, not alternate official format approval or comprehensive legality. End-to-end CLI passed; optimizer/tournament adoption remains pending.

- P0-03R slice 3 original CI failed on coverage verifier dictionary-count handling despite all 58 native games completing; independent receipt reconciliation passed. Corrected verifier and direct CLI tests implemented, corrective CI and independent receipt inspection passed. No original evidence relabeled or overwritten.

- Scoped roster acceptance covers 58 historical registrations and 29 mirrored pairs, not all matchups or full mechanics. Existing native CLI and legacy scripts remain historical-only; new jobs use the verified gateway. Additional approved configurations and official legal pool still open.

- P0-03R slice 4 implements named approved research configurations in isolation. Scoped validation accepted. Both configurations use the same dated ban snapshot; future Worlds/no-Legacy and other dated ban profiles require explicit legal pool/printing evidence and reviewed native support. Production optimizer/tournament integration remains open.

- P0-03 duplicate-name audit: 13/20 groups differ in inspected compiled fields, seven do not; no equivalence certified. Direct official gallery acquisition implemented; CI receipt pending. Gallery row coverage, legal-pool enumeration, errata and 52 historical RAD nonbase printing equivalences still open. See docs/P0_03_OFFICIAL_GALLERY.md.

- Direct official gallery acquisition succeeded, but source count mismatch (1408/1416) remains unresolved. 1121/1123 compiled IDs exact-code matched; two gameplay tokens absent. 285 candidate-only printings, two unmatched UNL gallery records (Buff/XP Tracker), and 52 RAD nonbase printings within candidate-only remain unresolved. All numbered main-set ranges present, OGS 24 exact codes. Gallery metadata is not complete official legality or mechanical equivalence.

2026-11-24 — Alternate pagination cross-check implemented at 1f40e3775883edb42f26fafc7a2ee6bf948c848e (feature/p0-03-gallery-crosscheck), CI 45382955404 observed in_progress/pending. Compares page sizes 100 and 150 against pinned prior report, reports identity additions/removals, metadata changes and unmatched UNL controls. Two targeted tests added. Acceptance requires actual CI and artifact inspection; no equivalence or legality promotion.

- Alternate pagination reproduces 1408/1416 at all three sizes; source completeness open. Buff and XP Tracker gallery Token supertype confirmed; behavioral evidence remains open.

2026-11-24 — Printing evidence ledger implemented on feature/p0-03-printing-evidence at dd8cb847e00f3f0c413fe823ceeeafa848082c68. Pins gallery, registry and ban profile, classifies 285 candidate rows, including 52 RAD, by comparator metadata and raw rules representation hashes; flags cross-set and banned candidate IDs and preserves ambiguity. Seven targeted tests written; no automatic aliases. Independent exploratory local comparison of pinned gallery rows (before CI): 149 with one equal raw hash/metadata candidate, 11 multiple equal, 125 metadata-only; RAD 17 one equal, 35 metadata-only. All remain unapproved. CI 45396801069 observed completed/success. Acceptance requires actual CI and artifact inspection. Official Rules Hub dated November 23 links separate Origins/Spiritforged/Unleashed/Vendetta/Radiance errata; gallery equality is not errata reconciliation. No native gameplay, no deck changes.

- Printing ledger accepted in scope: 285 candidate printings, 297 references; 131 single equal non-null raw fingerprint/metadata, 11 multiple equal, 143 metadata-only. 51 cross-set, two banned candidate rows. Equality is not functional equivalence; 18 missing rules hashes not treated as equality; zero approved aliases. Eight-row source discrepancy remains.

- P0-03 errata inventory accepted in scope, 67 headings mapped to 68 compiled identity references; 54 have test-name leads only. Confirmed source defects: Neeko requires exactly three instead of up to three and guarded format parser lacks NeekoLegends; Elnuk Herd excludes itself as target despite errata. No fix yet; Forbidden Technique and Last Caress wording review still open. See docs/P0_03_ERRATA.md.

- RAD-081 Elnuk native correction implemented in isolated post-baseline overlay; three native tests and full QA pending acceptance. Face-down and source-removal cases still require separate regressions. Current approved engine unchanged; no corrected gameplay claims yet.

- RAD-081 target-selection correction accepted in candidate build (3/3 focused, 3919 enabled full suite). Candidate is not yet authorized by approved gateway. Face-down recycling and source-removal interactions still open. Historical binary remains immutable.

- RAD-081 follow-up interaction tests written, native results pending. Hidden play uses prehidden fixture (not initial Hide payment or full legal-action gate); removal fixture queues trigger and kills source directly, not a full response sequence. Approved binary still unchanged.

- RAD-081 follow-up accepted within six native scenarios; hidden payment and full response sequence remain outside scope. No candidate binary authorization; build hashes differ despite identical registry and unchanged gameplay source in follow-up.

- RAD-167 candidate native correction written; additional legend cardinality, sideboard registration, shared active pool and resolve-time choice addressed in source. Full legal registrations, guarded BO3, ban/set gate, private observation and prompt leakage remain open; native CI acceptance pending.

- RAD-167 scoped native correction accepted (6/6 focused, 3928 enabled full suite); full legal registration, BO3 and ordered receipt including extra legends, set/ban checks and privacy remain open. Old approved engine unchanged.

- Candidate-only Neeko registration/receipt adapter implemented; CI acceptance pending. Native debug receipts contain private registration identities and must not be agent observations. Actual privacy and determinization audits, native direct negatives, updated engine approval and full roster revalidation remain open. Existing approved gateway remains unchanged.

- Guarded candidate registration accepted for seven native games and four preflight negatives. Agent privacy/determinization and direct native negatives remain open; no production authorization.

- Confirmed Neeko private-information leakage in sampled-world clone (opponent secret pool/count retained) and public mode-choice traces; corrective candidate implemented, native CI pending. Observer fingerprint correction pending; prior uncalibrated and registry-wide, new RNG sequence, public history same-game only; LogEvent audience and actual ISMCTS noninterference tests, broader view/continuation audit remain open. No candidate authorized.

- Direct native negatives accepted (5/5). Initial privacy workflow failed at exact-source anchor before build; corrected anchor and added both-seat LogEvent regression. New CI pending; no engine authorization.

- Scoped Neeko privacy correction accepted: four native privacy tests, full 3932 enabled regression tests, seven guarded games. Actual ISMCTS action-level invariance, broader observation/continuation privacy, format-aware sampling prior and cross-game knowledge remain open; no candidate authorization.

- Cached native agent noninterference screen implemented, results pending; partial trace-level comparison only, not internal search-state proof. Format-aware sampling, other observation consumers and production approval remain open.

- Native agent behavioral screen initially failed on invalid fixture identity before any gameplay; corrected ID verified against compiled registry, cached rerun pending. Prior native sampler own-pool preservation fixture used nonlegend sentinel ID258; it does not establish legality of that own registration. Replace with valid legend during next rebuild. No change to old approvals.

- Actual ISMCTS behavioral screen: 18 games, 8/8 identical trace pairs and 2 repeat controls, but zero detected Neeko selection prompts. Overall gate failed; no general noninterference certification. Three-copy diagnostic fixture with fresh seeds and trace diagnostics pending. No new authorization.

- V2 behavioral screen: all eight pairs matched but no actual Neeko selection observed, so overall gate failed. Controlled OpenSpiel search-summary and funded legal-play test implemented, pending CI. Separate synthetic positive play is not a naturally reached competitive position or end-to-end privacy proof. Historical approved engine unchanged.

- Controlled ISMCTS noninterference accepted in scoped six paired searches and four distinct legal-play controls (288 sampled worlds). Positive play separate synthetic snapshot; broader continuation/feature privacy, format-aware prior and all-58 fresh certification remain open. No production approval.
