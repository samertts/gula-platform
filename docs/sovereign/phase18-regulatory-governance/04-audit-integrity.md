# Phase 18-04 — Audit Integrity Assumptions & State Matrix

## Audit Integrity Contract

The platform's audit chain has **already** been hardened in production
phases 1–15. This phase formalises the **invariants** the chain provides
and the **state** of enforcement.

## Invariants (recap from `SOVEREIGN_INVARIANTS.md` §II)

- AI-1 — Append-only.
- AI-2 — Hash-chain continuity preserved across reconciliation, merges, and
  DR failover.
- AI-3 — Interop calls (in + out) emit a correlated `InteropAuditEvent`.
- AI-4 — A failed external integration MUST still produce an audit row.
- AI-5 — Crisis-mode degraded operation queues audit events for chained
  replay.

## Enforcement State Matrix

For each invariant: **C**ode-enforced / **P**rocess-enforced /
**D**ocumented-only.

| Invariant | C | P | D | Notes |
|-----------|:-:|:-:|:-:|-------|
| AI-1 (append-only) | ✓ | ✓ | — | No DELETE on `audit_logs`; reviewed in code review |
| AI-2 (chain continuity) | ✓ partial | ✓ | — | Verifier runs on demand; no continuous verifier yet |
| AI-3 (interop correlation) | — | — | ✓ | Wiring is Phase 16 future scope |
| AI-4 (fail-closed audit) | ✓ partial | — | — | Existing exception handling logs; interop layer not yet wired |
| AI-5 (crisis replay) | — | ✓ | ✓ | Edge buffer exists; replay protocol documented |

| Other invariants | C | P | D | Notes |
|------------------|:-:|:-:|:-:|-------|
| TI-1 (lab_id filter) | ✓ | ✓ | — | Enforced in routes; reviewed |
| TI-3 (no cross-tenant leak via reconciliation) | — | — | ✓ | Phase 19 future enforcement |
| CS-1 (clinical write exemption) | ✓ | — | — | `ConcurrencyLimitMiddleware` carve-out |
| CS-2 (optimistic lock) | ✓ | — | — | `version` column on results |
| CS-3 (logical merge) | — | — | ✓ | Phase 19 |
| AG-1 (no AI authority) | — | ✓ | ✓ | Documented; code path review per release |
| AG-3 (AI fail closed) | ✓ partial | ✓ | — | Existing fail-closed in clinical AI gates |
| GL-2 (legal hold) | — | — | ✓ | No retention purge today; future legal-hold table |

The matrix is reviewed quarterly; promotions from D → P → C are tracked.

## Hash-Chain Format (recap)

The audit chain (audit_logs v2 schema) carries:

- `id` — monotonic
- `prev_hash` — hash of previous row's canonical serialization
- `row_hash` — hash of this row's canonical serialization (incl. `prev_hash`)
- Subject and action fields
- Optional SNDHS correlation fields (Phase 1 SNDHS migration)

A break in the chain (`prev_hash` mismatch) is a SEV-1 incident.

## Verifier

A verifier traverses the chain and reports:

- last verified id
- mismatch positions (if any)
- re-hash time per 1k rows (performance)

The verifier is invoked:

- on demand (operations)
- nightly batch (production once enabled)
- pre-DR-cutover
- post-DR-cutover

The verifier is **read-only**. It never modifies the chain.

## Reconciliation & Merges

When Phase 19's MPI implementation merges two patient records, the audit
chain MUST receive:

- a "merge intent" event with both subject ids
- a "merge confirmed" event with the new canonical id
- references to both pre-merge audit subtrees

The merge does not delete or rewrite prior audit rows. The merge is
**logical**: both pre-merge ids remain in the chain forever; queries that
follow either id resolve to the canonical record.

## Sovereign-Grade Immutability

For sovereign deployment, additional immutability is recommended:

- Daily roll-up signed by sovereign KMS key.
- Roll-up exported to a cold archive (Tier-3) outside the operational
  network.
- Archive read by regulator on demand; archive write is one-way.

This is documentation-only today; the export pipeline is a future phase.

## Audit Surfaces NOT Yet Hardened

- Adapter audit (Phase 16 wiring)
- Reconciliation audit (Phase 19 wiring)
- AI invocation audit (Phase 21 wiring)
- Regulator access audit (Phase 18 future)
- Legal-hold lifecycle audit (Phase 18 future)

Each is documented; none affects the hardness of existing audit surfaces.
