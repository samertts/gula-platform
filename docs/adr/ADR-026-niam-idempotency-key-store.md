# ADR-026: NIAM Shared Idempotency Key Store

**Status:** Proposed
**Date:** 2026-09-21
**Deciders:** Pending human maintainer approval (see "Decision required" below)

## Context

Four NIAM Platform Authority operations create a new credential-bearing
row and are unsafe to retry blindly: `generate_api_key`,
`issue_certificate`, `rotate_certificate`, `rotate_api_key`. A client
retry after a timeout (before ever seeing a response) can currently
mint a second, orphaned API key, or double-rotate a certificate/API key
and silently invalidate the credential the client already received.
`revoke_certificate`/`revoke_api_key` are already safe (their
`is_active` precondition makes a retry a natural no-op/404), and
`TrustFramework`'s `activate_framework` is already safe (this session's
own state-machine fix made re-activation an explicit idempotent no-op)
— neither needed a new mechanism.

This codebase already has one real, durable idempotency pattern:
`CitizenRelationshipWorkflow` (`app/identity/services/citizen_relationship_service.py`)
embeds `idempotency_key_hash`/`request_fingerprint` directly on the
`CitizenRelationship` row it creates, using HMAC-SHA256 keyed by
`AUDIT_ANCHOR_KEY` (or a dedicated override), validated `Idempotency-Key`
bounds (16-128 chars), and `SELECT ... FOR UPDATE` to serialize
concurrent identical requests. It also has one clearly unsuitable
pattern for this purpose: `app/integration/esb/idempotency.py`'s
`IdempotencyService` — an in-memory `dict`, non-durable, not
actor/tenant-scoped, lost on process restart or under
`WEB_CONCURRENCY > 1`.

## Decision

Add one new, shared PostgreSQL table, `niam_idempotency_keys`, covering
all four operations — not four separate tables, and not embedded
columns on `APIKey`/`DigitalCertificate` (see Alternatives). Schema,
full per-operation contract, and the transaction model are specified in
`docs/security/IDEMPOTENCY_SCHEMA_PROPOSAL.md`. Summary:

- `(operation, actor_account_id, key_hash)` is the uniqueness scope —
  Platform Authority has no tenant dimension, so the acting identity is
  the correct security boundary (reusing `CitizenRelationshipWorkflow`'s
  key/fingerprint algorithm exactly, but scoped differently since that
  workflow's own scoping already happens elsewhere).
- `result_type`/`result_id` polymorphically reference the created
  `APIKey` or `DigitalCertificate` row.
- One transaction, one commit, matching every other NIAM write path
  already fixed this session (`certificates`, `TrustFramework`) — the
  idempotency-row insert, the business mutation, and marking the row
  `completed` all happen before a single `await db.commit()`.
- No Redis, no new async engine, no second connection pool — reuses
  `get_niam_db` exactly as-is.

**Not yet accepted.** No migration has been written. This ADR and
`IDEMPOTENCY_SCHEMA_PROPOSAL.md` together constitute the approval
request; the design's semantics (replay, conflict, cross-actor
isolation, concurrency, failure-before/after-commit, restart-durability)
were proven against a real, ephemeral PostgreSQL table — never the
production schema — before writing this ADR, so the request is backed
by evidence, not merely a proposal on paper.

## Alternatives Considered

### 1. Embed `idempotency_key_hash`/`request_fingerprint` on `APIKey` and `DigitalCertificate` directly (the `CitizenRelationshipWorkflow` pattern, applied twice)

**Pros:**
- Exact precedent already exists and is proven in production-adjacent code.
- No new table, no polymorphic `result_type`/`result_id` reference.

**Cons:**
- Two separate schema changes (one per entity) instead of one.
- `rotate_certificate`/`rotate_api_key` create a *new* row while
  deactivating an *old* one — the idempotency key would need to live on
  the new row, but the thing being retried is identified by the *old*
  row's id (`certificate_id`/`api_key_id`), which the new row doesn't
  share a natural join key with without extra bookkeeping.
- Scatters the same concept across two tables instead of one place to
  reason about expiry/cleanup.

**Status:** Rejected because: two operations don't map cleanly onto "the
key lives on the row it creates," and this workstream's own instruction
was explicit not to copy an entire workflow table's approach where a
smaller canonical design suffices.

### 2. One idempotency table per operation (four tables)

**Pros:**
- Slightly simpler per-table schema (no `operation` discriminator column).

**Cons:**
- Four migrations instead of one for materially identical semantics.
- No evidence any operation needs materially different columns.

**Status:** Rejected because: this workstream's own instruction was
explicit — do not create separate tables "unless evidence proves they
require materially different semantics," and no such evidence exists;
all four operations share an identical contract shape.

### 3. Redis-backed idempotency (TTL keys)

**Pros:**
- Very fast, simple `SETNX`-style implementation.

**Cons:**
- Not durable across a Redis restart/eviction — silently reintroduces
  exactly the weakness already identified in the ESB's in-memory
  `IdempotencyService`.
- This workstream's own rule: "Do NOT introduce Redis as the source of
  truth... PostgreSQL must be authoritative."

**Status:** Rejected because: explicitly disallowed by this workstream's
own constraints, and it would not actually solve the durability problem
these four operations need solved.

## Consequences

### Positive
- One canonical, reusable idempotency mechanism for any future NIAM
  operation with the same "creates one credential-bearing row" shape.
- Durable across process restarts and horizontal scaling (real
  PostgreSQL row, not per-process memory) — proven via a fresh-connection
  replay test, not assumed.
- No secret re-disclosure on replay (`generate_api_key`/`rotate_api_key`
  withhold `raw_key` on a replayed response) — a deliberate security
  property this design states explicitly rather than leaving implicit.

### Negative
- One new table and one new migration to review and approve.
- A cleanup job (or lazy expiry check) is eventually needed to prune
  `expires_at`-passed rows — not designed in this pass, since it's an
  operational concern independent of the core correctness contract.

### Neutral
- Adds `operation`/`actor_account_id`/`key_hash` as the composite
  uniqueness scope, which is specific to Platform Authority's
  platform-global model; a future tenant-scoped consumer of this same
  table would need to decide whether `actor_account_id` alone remains
  the right boundary or whether a tenant/org column should be added at
  that time — not a concern for the four operations this ADR covers.

## References

- `docs/security/IDEMPOTENCY_SCHEMA_PROPOSAL.md` — full schema, exact
  constraints, per-operation contract.
- `docs/security/IDEMPOTENCY_CONTRACT_AND_GAP_REPORT.md` — classification
  of all NIAM Platform Authority operations by idempotency requirement.
- `app/identity/services/citizen_relationship_service.py` — the reused
  HMAC-SHA256 key/fingerprint algorithm.
- `app/integration/esb/idempotency.py` — the rejected in-memory pattern.
- `docs/security/CERTIFICATE_AUTHORIZATION_RUNTIME_COMPLETION.md` /
  `docs/security/TRUSTFRAMEWORK_STATE_MACHINE_STATUS.md` — the
  established route-commits-once transaction convention this design
  reuses.

## Decision required

A human maintainer must approve, before any migration is written:

1. The shared-table design (vs. the two rejected alternatives above).
2. The `(operation, actor_account_id, key_hash)` uniqueness scope.
3. The proposed expiry windows (7 days for `generate_api_key`/
   `issue_certificate`, 24 hours for the two `rotate_*` operations).
4. Which env var carries the HMAC key (reuse `AUDIT_ANCHOR_KEY`, or a
   new dedicated `GULA_CERT_IDEMPOTENCY_KEY`).
