# Idempotency Schema Proposal

Phase 8/9 of the "P1 DATA-INTEGRITY + IDEMPOTENCY CLOSURE" workstream.
**No migration has been created for this.** Per this workstream's own
rule ("closing the four REQUIRES_IDEMPOTENCY operations needs a new
column pair — schema change → human approval required") and per
`CLAUDE.md`'s Autonomous Task Boundaries ("DB schema changes... any new
migration that adds/removes/alters columns" → Requires human approval),
and because this repository has no mechanical approval-gate mechanism to
invoke (no approval-tag system, no CI gate that records a human sign-off
on a pending migration) — this document **is** the approval request.
Nothing below has been applied to any real or disposable-but-persistent
schema; the proof harness in
`docs/engineering/AUTONOMOUS_ENGINEERING_FIELD_REPORT.md`-style scratch
scripts creates this table only in an ephemeral, throwaway database, via
raw SQL, never via an Alembic migration file.

## Why a shared table, not per-operation columns

`CitizenRelationshipWorkflow` embeds `idempotency_key_hash`/
`request_fingerprint` directly on `CitizenRelationship` because that
workflow only ever creates one kind of row. The four operations here
create **two different entity types** (`APIKey`, `DigitalCertificate`)
across **four operations**, all with the identical shape: "given a
client-supplied key, either replay a completed prior result or perform
the mutation exactly once." Copying the embedded-column approach would
mean touching two existing production tables in two different, subtly
different ways; a single small canonical table serves all four with one
schema, one set of semantics, and one constraint — satisfying this
workstream's own instruction not to build four separate tables, and not
to copy an entire workflow table where a small canonical one suffices.

## Exact schema

```sql
CREATE TABLE niam_idempotency_keys (
    id                 VARCHAR(26)  PRIMARY KEY,
    uuid               VARCHAR(36)  NOT NULL UNIQUE,
    operation          VARCHAR(50)  NOT NULL,   -- 'generate_api_key' | 'issue_certificate' | 'rotate_certificate' | 'rotate_api_key'
    actor_account_id   VARCHAR(26)  NOT NULL REFERENCES niam_accounts(id) ON DELETE CASCADE,
    key_hash           VARCHAR(64)  NOT NULL,   -- HMAC-SHA256(client Idempotency-Key), hex
    request_fingerprint VARCHAR(64) NOT NULL,   -- HMAC-SHA256(canonical request payload), hex
    status             VARCHAR(20)  NOT NULL DEFAULT 'pending',  -- pending | completed | failed
    result_type        VARCHAR(50),             -- 'api_key' | 'certificate', set on completed
    result_id          VARCHAR(26),             -- APIKey.id or DigitalCertificate.id, set on completed
    created_at         TIMESTAMPTZ NOT NULL,
    updated_at         TIMESTAMPTZ NOT NULL,
    expires_at         TIMESTAMPTZ NOT NULL,

    CONSTRAINT uq_niam_idempotency_scope UNIQUE (operation, actor_account_id, key_hash)
);
CREATE INDEX ix_niam_idempotency_result ON niam_idempotency_keys (result_type, result_id);
CREATE INDEX ix_niam_idempotency_expires ON niam_idempotency_keys (expires_at);
```

`IdentityBaseEntity`'s existing `id`/`created_at`/`updated_at`
convention is reused exactly (ULID `id`, `default=_ulid`).

### Ownership / security boundary

`actor_account_id` **is** the security boundary — Platform Authority is
explicitly platform-global (no organization/tenant dimension exists on
this axis; see `CERTIFICATE_AUTHORIZATION_RUNTIME_COMPLETION.md`'s own
Gate A finding). The unique constraint is therefore
`(operation, actor_account_id, key_hash)`, not `key_hash` alone: two
different actors who happen to supply the identical literal
`Idempotency-Key` string for the same operation get two independent
rows — one cannot replay or collide with the other's result. This is
the one deliberate difference from `CitizenRelationshipWorkflow`, whose
`idempotency_key_hash` is globally unique because that workflow's own
scoping already happens elsewhere.

### Key/fingerprint algorithm — reused, not invented

Both hashes reuse `CitizenRelationshipWorkflow`'s existing
`_digest()`/`_request_fingerprint()` pattern exactly: **HMAC-SHA256**
(not bare SHA-256) keyed by a dedicated env var with `AUDIT_ANCHOR_KEY`
as fallback (`_workflow_key()`, `>= 32` chars, fails closed). A new
`GULA_CERT_IDEMPOTENCY_KEY` (or reuse `AUDIT_ANCHOR_KEY` directly) would
follow the identical convention. `request_fingerprint` is
`json.dumps(payload, sort_keys=True, separators=(",", ":"))` over the
operation-specific canonical payload (below), matching
`_request_fingerprint`'s exact serialization.

### Client contract

`Idempotency-Key` header (or query param, matching this codebase's
existing param-based style for these routes), 16-128 characters —
identical bounds to `CitizenRelationshipWorkflow.create_pending`'s own
validation (`if not 16 <= len(idempotency_key) <= 128`).

## Per-operation contract

| | `generate_api_key` | `issue_certificate` | `rotate_certificate` | `rotate_api_key` |
|---|---|---|---|---|
| **Scope** | platform-global | platform-global | platform-global | platform-global |
| **Fingerprint payload** | `organization_id, name, scopes, permissions, allowed_ips, allowed_referrers, rate_limit, person_id, enterprise_account_id, expires_at` | `cert_type, subject, issuer, organization_id, person_id, machine_id, signature_algorithm, key_size, validity_days, rotation_period_days, issuer_ca_id` | `certificate_id` (the target being rotated) | `api_key_id` (the target being rotated) |
| **Owner** | `actor_account_id` | `actor_account_id` | `actor_account_id` | `actor_account_id` |
| **Result reference** | `result_type='api_key'`, `result_id=APIKey.id` | `result_type='certificate'`, `result_id=DigitalCertificate.id` | `result_type='certificate'`, `result_id=<new> DigitalCertificate.id` | `result_type='api_key'`, `result_id=<new> APIKey.id` |
| **Success replay** | same `(op, actor, key)` + same fingerprint → same `APIKey` metadata, **`raw_key` withheld** (a secret must never be re-disclosed on replay — a deliberate, documented deviation from `CitizenRelationshipWorkflow`, which has no secret to protect) | same → same certificate (private key already never returned, no special handling needed) | same → the **original** rotation's new-certificate result, not a second rotation | same → the **original** rotation's new-key result, `raw_key` withheld on replay |
| **Conflicting replay** | same `(op, actor, key)`, different fingerprint → `409` | same | same | same |
| **Cross-boundary** | different `actor_account_id` with the same key string → independent row, no collision (unique constraint scopes by actor) | same | same | same |
| **Concurrency** | `SELECT ... FOR UPDATE` on the `(operation, actor_account_id, key_hash)` row (matching `TrustFramework`'s own row-lock precedent from the prior operation) serializes two concurrent identical requests; the loser re-reads the winner's completed row after the lock releases | same | same | same |
| **Failure before commit** | no row exists (or row is `failed`) → retry proceeds as a fresh attempt, safe | same | same | same |
| **Failure after commit** | row is `completed` with a real `result_id` → retry replays, never re-runs the mutation | same | same | same |
| **Expiry** | `expires_at` — proposed 7 days for `generate_api_key`/`issue_certificate` (long enough to cover realistic client retry windows), 24 hours for the two `rotate_*` operations (a rotation's replay window should be short — an old idempotency key surviving for a week would let a client "re-rotate" back to a week-old already-rotated result, which is confusing even though not unsafe) | | | |

## Transaction model (reuses this codebase's established pattern, no new engine)

Same `get_niam_db` session and same route-commits-once convention as
every other NIAM route fixed this session and the prior one:

1. Compute `key_hash`, `request_fingerprint`.
2. `SELECT ... FOR UPDATE` the `(operation, actor_account_id, key_hash)`
   row if present.
3. Present + `status='completed'` + same fingerprint → return the
   referenced result (replay), no mutation, no second audit event.
4. Present + different fingerprint → `409`.
5. Present + `status='pending'` (a genuinely concurrent in-flight
   request) → the `FOR UPDATE` lock already serialized this; by the
   time this transaction acquires the lock, the first request has
   either committed (→ case 3) or rolled back (→ case 6).
6. Absent → insert a `pending` row, perform the real mutation + audit
   (`flush()`, matching the established pattern), update the row to
   `completed` with `result_type`/`result_id`, single `await db.commit()`
   at the route level — identical ownership boundary to every other
   NIAM write path fixed so far.

No new async engine, no second connection pool, no Redis as source of
truth (Redis is explicitly out per this workstream's own rule — it
would reintroduce the exact non-durable, non-restart-safe weakness
already identified in the ESB `IdempotencyService`, re-verified this
pass at `app/integration/esb/idempotency.py`: still an in-memory
`dict[str, float]` with a TTL, still lost on process restart, still not
tenant/actor-scoped — unsuitable, confirmed unchanged from the prior
operation's finding).

## Migration impact / compatibility

- Additive only: one new table, zero changes to any existing table.
- No existing column, index, or constraint is touched.
- No API response shape changes for any of the four operations when the
  `Idempotency-Key` is *absent* (fully backward compatible — a caller
  that never sends the header gets today's exact behavior, an operation
  performed unconditionally).
- Downgrade: `DROP TABLE niam_idempotency_keys` — no data loss for any
  other table, no FK from any other table points at this one.

## What this proposal is NOT

Not a request to add `idempotency_key_hash`/`request_fingerprint`
columns to `DigitalCertificate`/`APIKey` directly (rejected above, in
favor of the shared table). Not a request to use Redis. Not a request
to build a generic, codebase-wide idempotency framework — scoped to
exactly these four operations.

## Decision required

A human maintainer needs to approve, before any migration is written:

1. The shared-table design above (vs. embedded columns, vs. per-operation tables).
2. The `(operation, actor_account_id, key_hash)` uniqueness scope.
3. The proposed expiry windows (7 days / 24 hours).
4. Which env var carries the HMAC key (`AUDIT_ANCHOR_KEY` reused, or a
   new dedicated `GULA_CERT_IDEMPOTENCY_KEY`).

Until that approval exists, `docs/security/IDEMPOTENCY_CONTRACT_AND_GAP_REPORT.md`
correctly keeps these four operations classified `REQUIRES_IDEMPOTENCY`
/ `BLOCKED` — not `VERIFIED`.
