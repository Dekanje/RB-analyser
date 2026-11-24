# Handover — 2026-11-24
Active branch: `research/competitive-agent-benchmark-v1-2026-11-23`; native engine baseline 0b9739bb6c20e8ed5a805a78239d5faa09b226ad. Read AGENTS, master plan, status, limitations and latest refs/CI.
P0-01, P0-02 and scoped P0-02R accepted within their stated scope. P0-02R run 45304720496 passed; artifact 14880102318 independently checked (174 corrected hashes, 32 native games, all eight corrected trace comparisons matched). Exact tested scripts integrated from 1f761804dec829c5ac116a5324e332d56cd66295. No deck adoption.
## Next task P0-03 — card coverage
1. Use pinned registry archive 14869638175, QA XML 14869653235 and catalog/ledger at current ref. Inventory engine IDs/public codes, set/type counts, bans, duplicates, variants, tokens, legends and unknown legal status. Distinguish compiled registration from actual card behavior and official legality; pin sources.
2. Populate docs/CARD_COVERAGE.json with traceable evidence or a generated ledger schema/report; never promote based on metadata alone. Reconcile Final64 mapped scenarios with actual enabled tests. 
3. P0-04: review 37 historical edge-case questions and disabled Baron test against newer evidence; add missing focused regression scenarios in isolated work. P0-09 clean local build/toolchain lock pending.
4. Future sideboard screening must use versioned corrected manifest and strict ordered input gate before native certification and fitness; legacy campaigns remain exploratory; no mass campaigns until baseline gate.
Update status, limitations, changelog and handover after each milestone.
