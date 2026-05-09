# Phase 19-05 — Longitudinal Record Continuity

## Goal

Given a patient's canonical id, present a complete, ordered, traceable
record of their clinical encounters across institutions and time, while:

- never violating tenant isolation
- never silently merging records that have not been governance-approved
- never losing audit lineage

## What "Longitudinal" Means Here

A patient's longitudinal record is the **union** of:

- lab orders + results in tenants where the canonical id is linked
- visits in SNDHS-enabled tenants
- patient-card events
- adapter-mediated data from peer institutions (where authorised)

The union is **computed on read**, not pre-materialised, except for
performance-critical aggregates that are explicitly approved.

## Tenant-Safe Longitudinal Read

A user requesting a longitudinal record sees:

- their own tenant's records in full
- redacted summaries of other tenants' records, **with explicit consent
  scope** carried in the request
- nothing at all if the cross-tenant scope is not present

A regulator with `REGULATOR_READ_FULL` may see across tenants, but only
within their scope and with audit logging on every cross-tenant fetch.

## Consent Scope

Cross-tenant longitudinal access requires a **consent scope**, materially:

- a digital consent token bound to the canonical patient id
- with a TTL
- with an explicit list of data classes
- recorded as an audit event when used

The platform does not guess at consent. If consent isn't present, the
longitudinal view is reduced to the caller's tenant scope only.

## Read Path

```
caller (with scope) ----> longitudinal API
                              |
                              v
                       canonical id resolution
                              |
                              v
            +---- tenant A (caller's) ----+
            |                              |
            +---- tenant B (consented?) ---+
            |                              |
            +---- tenant C (consented?) ---+
            |                              |
            +---- NHOP / MOH (consented?) -+
                              |
                              v
                       merged view (read-only,
                       with provenance per row)
```

Every row in the merged view carries provenance: `(tenant, source_id,
adapter, retrieved_at)`. Provenance never disappears.

## Merge Semantics on Conflicting Data

When tenant A and tenant B disagree on a fact (e.g., patient's reported
DOB), the longitudinal view does NOT silently choose one. It surfaces the
discrepancy:

- both values
- the source of each
- a "discrepancy_open" flag

The discrepancy may trigger a reconciliation event under Phase 19's
governance.

## Performance Strategy

Materialisation, when introduced, will be:

- per-canonical-id summary cache
- invalidated on any reconciliation event involving the id
- never stale beyond a documented bound
- never used as a source of truth — always a cache

## Cross-Tenant Privacy Boundaries

- Tenant B's clinician CANNOT see tenant A's free-text notes (PHI scope).
- Tenant B's clinician CAN see canonical lab values from tenant A within a
  consented data class (e.g., HbA1c history) once consent is asserted.
- Regulator can see across tenants with their own audit trail.

## Failure Modes

| Failure | Behavior |
|---------|----------|
| Canonical id resolution failure | Caller falls back to tenant-local view; banner shown |
| Consent token invalid | Cross-tenant view dropped silently to caller; explicit "no consent" surfaced |
| Adapter failure for peer data | Local view + "external data unavailable" annotation; never silent zeros |

## Out of Scope (this phase)

- The merged-view API endpoint
- The consent token system
- The materialisation cache
- Reviewer tooling for discrepancy resolution
