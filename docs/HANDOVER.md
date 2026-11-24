# Handover — 2026-11-24
Active branch: `research/competitive-agent-benchmark-v1-2026-11-23`. Engine baseline 0b9739bb6c20e8ed5a805a78239d5faa09b226ad. Read root instructions, master plan, status, limitations and latest ref/CI.
P0-01 priority artifact audit completed. P0-02 source/build/architecture and historical order audit completed within source scope: [report](P0_02_ARCHITECTURE_AUDIT.md). Read-only audit + six unit tests passed locally; no new native games. No deck adoption or Phase 0 acceptance.
## Next task P0-02R — corrective gate
1. Implement isolated order-preserving sideboard proposal serializer and strict ordered-playable-input gate, with tests. Keep historical workflow inputs and manifests unchanged; create versioned experiment namespace.
2. Verify a controlled native replay across baseline/sideboard-only/reordered/corrected inputs, same engine/agent/seed/seat; include repeated identical-input controls, both seats, multiple seeds and native receipts. Sandbox lacks Boost.Context 1.83; use compatible local environment or scoped CI. Do not declare fixed without native evidence.
3. Keep historical sideboard results exploratory. No large campaigns until gate passes.
4. Then P0-03/04: reconcile legal card coverage, 37 historical edge-case questions and disabled upstream test. P0-09 clean local installation and toolchain lock pending. Preserve artifact copies before expiry; keep branches/workflows pending ancestry/dependency audit.
Update status, limitations, changelog and handover after each milestone.
