# Phase 19-01 — Health Data Fabric Architecture

## Position

The "fabric" is not a new system. It is a coherent view of three already-
existing concerns plus governance:

1. **Patient identity** — `patients` (existing); national_id and SNDHS
   health_id (existing, encrypted).
2. **Master Patient Index** — `services/mpi/` (existing scaffold).
3. **Longitudinal record** — `lab_orders` + `lab_results` + `samples`
   (existing); cross-institution stitching is new.
4. **Reconciliation governance** — new (this phase).

## Architectural Goals

- A patient is **one** logical subject, regardless of how many tenants
  contain a record.
- A merge is **logical**: constituent records remain in storage with their
  audit lineage; queries follow a canonical id.
- Cross-tenant identity reconciliation is **explicit**, **audited**, and
  **never silent**.
- Terminology drift is detected and contained; it never silently corrupts
  results.

## Logical Model

```
+-------------------------+
| canonical_patient       |  <-- one row per logical national subject
+-------------------------+
          ^
          | reconciled via
          |
+---------+---------------+
| reconciliation_event    |  <-- append-only; one row per merge/link
+---------+---------------+
          |
          v
+-------------------------+
| patient (per tenant)    |  <-- existing rows (untouched on merge)
+-------------------------+
```

`canonical_patient` is a **logical** structure. In implementation it can be
a derived view, a materialised table updated on reconciliation events, or a
service. The choice is deferred to the implementation phase.

What matters is the contract:

- A canonical id is stable.
- A reconciliation event names both the canonical id and the constituent
  patient ids (each `lab_id` + tenant patient id).
- Constituent rows are never modified by a merge.

## Data Sources

- `patients` (per tenant) — local identity.
- `patient.national_id` — Iraqi national id (encrypted).
- `patient.sndhs_health_id` — SNDHS health id.
- `visits` — clinical episode tracking.
- `lab_orders` / `lab_results` / `samples` — clinical records.
- `audit_logs v2` — chain.
- Future: `reconciliation_events` table.

## Identity Matching Modes

| Mode | Inputs | Outcome |
|------|--------|---------|
| Deterministic | `national_id` exact match (within hash space) | Auto-link **only** if confidence is unambiguous + cross-checked secondary attributes pass |
| Probabilistic | name + DOB + phone + locality | Always escalates to human reviewer |
| Manual | Operator-driven | Always escalates to human reviewer |

No mode unconditionally auto-merges. Even deterministic match requires a
secondary-attribute check.

## Privacy-Preserving Identity Matching

Identity matching MUST NOT log raw national_id values. Matching uses:

- HMAC-derived national_id (existing `NID_HMAC_KEY`)
- Tokenised secondary attributes (e.g., locality bucket) for probabilistic
  matching
- A confidence score logged in the reconciliation event

Logs and matching engines never see plaintext national_id.

## Integration with Phase 16

Reconciliation can be **triggered** by an inbound adapter call (e.g., MOH
sends a patient update). The adapter:

- carries an `INTEROP_*` principal
- proposes a reconciliation event in `proposed` state
- waits for governance disposition (auto-link if deterministic + safe;
  human review otherwise)

The adapter never directly performs a merge.

## Integration with Phase 18

Reconciliation events are part of the audit chain (AI-2 invariant). A
canonical id transition is a chain event, not a metadata blip.

## Integration with NHOP

`nhop-platform/` (national citizen registry companion) holds national-level
citizen identity. GULA's fabric:

- consumes citizen identity via an adapter (NHOP adapter)
- never **owns** national identity
- writes lab-clinical events back to NHOP only via adapter
- is a citizen-record subscriber, not authoritative

## Out of Scope (this phase)

- The actual `canonical_patient` table or service implementation
- The reconciliation worker
- The merge UI
- The reviewer tooling
