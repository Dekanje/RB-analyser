# Handover — 2026-11-24
Current task P0-01: consolidate evidence on active branch `research/competitive-agent-benchmark-v1-2026-11-23`. Engine baseline 0b9739bb6c20e8ed5a805a78239d5faa09b226ad. Documentation-only setup; no code/simulation change and no phase gate accepted.
1. Read root instructions/master plan/status/limitations and this file. Resolve actual active ref and inspect latest commit and Actions runs.
2. Retrieve aggregate artifact 14877427266 from run 45297203812 and certification artifacts from run 45283891778; record hashes, manifests, exact sample counts, errors, agent parameters and selection boundaries. Do not promote training candidates.
3. Build baseline inventory of workflows, pinned AlphaRune revision/overlay, rules/catalog provenance, test counts, card coverage, BO3 and search scripts. Reconcile 37 historical edge-case questions and disabled test with new evidence.
4. Record component-by-component verified/partial/missing/defective/unknown matrix, reproduce build locally or document blocker, verify license, establish throughput benchmark and agent-strength evidence.
5. Update status and limitations with exact evidence; choose smallest highest-risk missing test/implementation, on a new branch. Do not begin further large screening until baseline is audited.
Existing useful docs: COMPETITIVE_VALIDATION_V1.md, ../radiance/qa/2026-11-23-full-qa.md, ../scripts/tournament_bo3_policy.py and ../scripts/synergy_multicard_screen.py. Keep prior evidence intact.

## Repository organization follow-up
Read [repository guide](REPOSITORY_GUIDE.md), [branch register](BRANCH_REGISTER.md), [workflow catalog](WORKFLOW_CATALOG.md) and [evidence index](EVIDENCE_INDEX.md). The active branch remains unchanged in name; main is an entry point until integration review. Before consolidation, compare historical branches against active, audit workflow/path and artifact dependency chains, and verify a reproducible build. Do not restart completed screenings or rename workflows just to tidy the repository.
