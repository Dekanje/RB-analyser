# P0-08 — Tournament functionality baseline
2026-11-24 — P0-08 scoped baseline ACCEPTED. Repository recursive tree reviewed at 46ddcd17beca272b889c9d171fcf5aea306931eb: historical tournament-related Python code is lineup screening, fixed-deck matchup evaluation, declared BO3 policies and independent-record projections; no full Swiss entrant pairing/standings/cut/bracket simulator located. New read-only audit [988d48b](https://github.com/Dekanje/RB-analyser/commit/988d48b28ee50c91fff1a6bb36f670c8eb85b965), CI [45481940927](https://github.com/Dekanje/RB-analyser/actions/runs/45481940927) completed/success, five targeted tests plus full archive reconstruction. Artifact 14961579369 ZIP SHA-256 833e8b94a06857535a1831f0ca11941428335ba12f9c0a2e134cf9e1be715915, report.json SHA-256 413f23a758a0e0434f0e613eac4ce22f328d360a20bf4f50a92f0c1081736051. Independently downloaded and checked original archives and output: 58 decks, ten anchors, 570 directed nonmirror matchup cells, 1140 unique scheduled series and seeds, both deck hashes on every record, 2713 recorded game winners, 707 two-game and 433 three-game series, complete winner identity progression and 58 historical aggregate win tallies; no per-game native trace or ordered ID receipts. Historical engine SHA-256 17dfb633c6936d74596305c35dcbd0b8793a3da0463e7ce932ab5105c66fe5af, registry d8102dd0930f466ce16c917035aff15eb21e347879800b08fa334b677f198b89. Source scenarios SHA-256 2244555cf69a8fd9996fcb5005d24c45a59181ca3312f6a36ad39d5b64204b3c; source run 45222607317; archived fixed-deck ISMCTS128, no sideboarding. Reconstructed all 919 six-domain disjoint triples independently; reproduced historical top20 bootstrap rows (500 resamples, seed 202611240404), all 919 robust rows (600 modeled scenarios, seed 202611240900), all 919 nine-trial tail rows (600 modeled scenarios, seed 202611251100), both concentration 1.0. Independent exhaustive enumeration of 512 binary vectors for each of 125 probability triples and ten thresholds: 1250/1250 comparisons within absolute tolerance 1e-12. These are statistical calculation checks, not real tournament events. No new native games, no complete event, no actual Swiss pairing, no championship probability.
Format defect: worlds_lineups.py historical report claims five sets OGN/SFD/UNL/VEN/RAD only, but it checks disjoint domains rather than validating format. Historical registry name resolution finds four OGS-only legends (Annie, Garen, Lux, Master Yi), seven non-Legend rows / 15 copies resolving exclusively to OGS, two cross-set ambiguous Champion names (Ahri and Yasuo, OGN/SFD). 189/919 historical triples contain at least one of the four affected legends; independently counted from the original 919-row table. The 730 other triples are NOT certified either. OGS is not asserted officially illegal or identical to Legacy; this is a discrepancy with the historical report's own declared five-set policy. Do not silently remove any legends, claim future Worlds rules, or adopt a five-set rule without explicit versioned format verification and printing equivalence. Historical outputs remain immutable and exploratory; no production authorization. Full event functionality remains Phase 9/15.

## Requirement matrix (event scope)
| Requirement | Capability | Classification | Evidence / residual |
|---|---|---|---|
| TR-01 | Swiss score-group pairing | MISSING | No entrant pairing; independent match draws only. |
| TR-02 | Floats and pairing constraints | MISSING | No score groups or float policy. |
| TR-03 | Rematch avoidance | MISSING | No entrant opponent history. |
| TR-04 | Match points and standings | MISSING | Elite matchup win-rate ranking is not event standings. |
| TR-05 | Opponent match win percentage | MISSING | No event opponent records, floors or exclusions. |
| TR-06 | Game win percentage | MISSING | Historical game wins reconstructable, no event tiebreak calculation. |
| TR-07 | Opponent game win percentage | MISSING | No event tiebreak calculation. |
| TR-08 | Byes | MISSING | No odd-entrant round or bye history. |
| TR-09 | Withdrawals | MISSING | No active entrant lifecycle. |
| TR-10 | Intentional draws | MISSING | No draws in projection or points-only guarded BO3. |
| TR-11 | Round time | MISSING | Process timeout is not event clock. |
| TR-12 | End-of-match procedure | MISSING | Two-wins progression only; no event extra turns or draw adjudication. |
| TR-13 | Multiple days | MISSING | Nine-trial projection has no day boundary. |
| TR-14 | Intermediate qualification cuts | MISSING | Threshold tails are not actual qualification. |
| TR-15 | Standings carryover/reset | MISSING | No stage records. |
| TR-16 | Top-cut qualification | MISSING | Explicitly not simulated in all historical reports. |
| TR-17 | Elimination bracket | MISSING | Predesignated playoff deck is not a bracket. |
| TR-18 | Seeding and play/draw | MISSING | P0-07 loser-start at match level only; no bracket seeding. |
| TR-19 | Legal sideboarding | PARTIAL | P0-07 six declared points-only series, 14 native games; no event integration or adaptive policy. |
| TR-20 | Immutable registered lists | PARTIAL | P0-07 freezes two registrations per series; no event roster lock. |
| TR-21 | Skill distributions | MISSING | Beta matchup posterior is not player skill. |
| TR-22 | Event overrides | DEFECTIVE | Historical five-set label not enforced; current dated match-level gateway only, no sourced event profile. |
| TR-23 | Replay and audit | PARTIAL | Historical match receipt reconstruction and deterministic projection replay; no event ledger. |
| TR-24 | Tournament objective optimization | PARTIAL | Lineup mean and record-tail proxies; no actual qualification or title objective. |
| TR-25 | Independent validation | PARTIAL | 1250 probability checks, bounded match QA; no full native versus statistical event cross-validation. |

Counts: 19 missing, 5 partial, 1 defective, 0 fully verified tournament capabilities. Classification is at event scope; passing limited match components and arithmetic remains useful evidence. Every TR requirement stays open for production event certification.

## Archive sources
| Run | Artifact | ZIP SHA-256 |
|---|---:|---|
|45222607317|14841669639|986d5dbca90c1dc621c6ee309278790e1cf00dddd4ac592969fb8c8442762fc1|
|45181493632|14823477036|1cdf59d8cc2c36dde035a142ad09556ee9323cfdbb836488e0c20bd75c09f872|
|45205260187|14833662301|d600355e3a13c8dcbad08bcc67aa995f14b95f51247b09a501d5cc7c89097b99|
|45244227502|14854411637|18009f683aeafc88c7209c4581dbc9556b34f23d44c44c2db77bc11702aa4770|
|45225542088|14843520123|5785ea6d1c419e52c7adfcb76b21dc3644d608f218eaeb0b2b36dce1f4ea7877|
|45245706918|14853402315|37b0c166ccf790a1009e2ee5389c5f9ece750c28477e8f39f68107399dfbc780|
|45254851008|14858215856|c6f3ae5e9c4f8c3c8f63cfbe40d0111cb167b7c57ed17db7118ac2fc271d2e4d|

The two historical engine archives have identical registry bytes; projection workflow uses newer registry archive while source series used older binary. No binary executed by audit. Historical source load_outcomes validates target hashes but not anchor hashes or exact two-seat set; new audit checks both hashes, both seats, seed schedule, strict receipt counts and identity outcomes. These checks are not integrated into the legacy projection entry points; preserve old results rather than silently recomputing a different experiment. Historical 50% mirrors are imputed and two observations per nonmirror are weak evidence. Bootstrap frequency, expected wins, record threshold tails, and model scenario percentiles are not event title probability or calibrated confidence intervals.

## Phase 9/15 backlog
Phase 9: explicit versioned event schema, entrant immutable registration locks, complete native match interface incl draws/time, score-group pairing and deterministic constraints, byes/drops, standings, tiebreaker policy and day/cut bookkeeping, seeded bracket fixtures. Phase 15: official event sourcing with effective dates, configurable tournament-specific overrides, full native versus validated joint statistical match-score/duration/skill model, independent reference standings/pairing checks, calibration/uncertainty and championship objective. All profile rules must be sourced and tested before official label. No new mass optimization.

Next unfinished task: P0-09 local reproducibility closure work: preserve exact accepted lock and package plan durably on repository feature branch without raw binaries, verify package/tool executable availability and physical-host preflight requirements; actual user's PC remains unverified until authorized local execution. Then Phase 0 remaining ancestry, licensing and performance profiling, integration evidence matrix and final gate review. No Phase 1 advance until Phase 0 blockers explicitly reconciled; no mass optimization.
