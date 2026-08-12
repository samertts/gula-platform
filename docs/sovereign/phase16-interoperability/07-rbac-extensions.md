# Phase 16-07 — Institutional RBAC Extensions

Existing RBAC: 9 roles × 13 permissions in `backend/app/security/rbac.py`.
Phase 16 adds **four interop-only roles** that are never assumed by humans.
Phase 18 adds the regulator/inspector role family on top of this.

## New Roles (Interop-Only)

| Role | Purpose | Permissions |
|------|---------|-------------|
| `INTEROP_READER` | Read-only adapter, single tenant | `read:patient_summary`, `read:lab_result_public_subset` |
| `INTEROP_WRITER_LIMITED` | Adapter that can submit a result/order on behalf of a peer | `create:lab_order_referred`, `create:lab_result_referred` |
| `INTEROP_REGULATOR_READ` | Multi-tenant aggregate read for regulators | `read:audit_log_summary`, `read:tenant_metrics_aggregate` |
| `INTEROP_AGGREGATOR_DEID` | National statistics aggregator (de-identified) | `read:metrics_anonymized` |

## Boundary Rules

- These roles are **NOT** assignable to `lab_users`. Trying to assign
  programmatically MUST raise.
- These roles cannot be unioned with internal roles via group membership.
- Each role's permission list is a strict subset of an existing internal
  permission shape; no new privilege primitive is invented.
- An interop call's effective permissions are the **intersection** of:
  - the role's permission list
  - the manifest's `allowed_operations`
  - the data-class restriction in `data_classes_in/out`

## Permission Shape

The Phase-16 permissions follow the existing RBAC shape
(`<verb>:<resource>[:<modifier>]`). New verbs are **not** introduced. Where a
new resource is needed it is a "view" on existing data:

- `patient_summary` is a derived, redacted view of `Patient`.
- `lab_result_public_subset` is the result fields safe for inter-institutional
  exchange (no internal QC notes, no internal reviewer comments).
- `audit_log_summary` is a coarse-grained aggregate; never raw rows.
- `tenant_metrics_aggregate` is per-tenant counts only.
- `metrics_anonymized` enforces k-anonymity floor per Phase 20.

## Cross-Phase RBAC (Preview)

Phase 18 adds:

- `REGULATOR_READ_FULL` (regulator read on raw audit log; require explicit
  warrant flag in the access record)
- `INSPECTOR_READ_LIMITED` (lab-accreditation inspector; tenant-scoped)
- `EXTERNAL_AUDITOR_READ_TIME_BOXED` (third-party auditor with TTL)

These are **separate** from the interop family above. An external regulator
access is a human session, not an adapter session.

## Tests (Required Before Wiring)

Before any of these roles are activated in production, the test suite must
include:

- A test asserting `INTEROP_*` cannot be assigned to a user.
- A test asserting capability-intersection logic (role × manifest × data
  class).
- A test asserting that a tenant-scoped adapter cannot read another tenant.
- A test asserting that `INTEROP_AGGREGATOR_DEID` calls receive only
  k-anonymized data.

These tests live in `backend/tests/test_interop_rbac.py` (to be added when
Phase 16 wiring is approved).
