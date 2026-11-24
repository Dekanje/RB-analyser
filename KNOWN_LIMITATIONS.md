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
