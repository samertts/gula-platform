# MPI Execution Authorization Request & Decision Register Entry

**Date:** 2026-11-18
**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1` (HEAD unchanged at `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`)
**Scope:** MPI Integrity & Reliability implementation (MPI-01 … MPI-10), engineering evidence only
**Status of this record:** `EXECUTION_AUTHORIZED_FOR_MPI_ONLY_SCOPE` — **not** a release, security, clinical or schema decision

---

## 1. Purpose and honesty boundary

This record documents the **execution authorization under which the MPI-only implementation was carried out**. It does **not** rewrite history and does **not** claim that any approval existed before the owner's current instruction.

The three pre-existing governance baselines remain exactly as recorded:

| Artifact | Status before this work | Status now |
|---|---|---|
| `GOVERNANCE/FINAL_DECISION.md` | **HOLD** (md5 `effdfeaf10234678d83b2668c4489552`) | **HOLD — unchanged**, md5 re-verified |
| `GOVERNANCE/GECS/DECISION_REGISTRY.md` D-020 | `PENDING_APPROVAL` | `PENDING_APPROVAL — unchanged` |
| `GOVERNANCE/GECS/DECISION_REGISTRY.md` D-021 | `PENDING_APPROVAL — no approval record exists` | `PENDING_APPROVAL — no approval record exists — unchanged` |

`MPI_SERIALIZATION_ARCHITECTURE_DECISION.md` §10 recorded D-MPI-1 as `NEEDS_OWNER_DECISION` on 2026-11-17. **That historical entry is deliberately not edited.** This document is the *new*, dated authorization record for the MPI-only engineering execution requested on 2026-11-18.

---

## 2. Decision register entry — D-MPI-1 (execution authorization)

| Field | Value |
|---|---|
| **Decision ID** | D-MPI-1 (execution authorization addendum; historical `NEEDS_OWNER_DECISION` entry retained in `MPI_SERIALIZATION_ARCHITECTURE_DECISION.md` §10) |
| **Date of authorization** | 2026-11-18 |
| **Authorized scope** | Implementation of the recommended architecture **B + D + existing ascending-row-lock order + idempotency + detection-only verification** in the MPI service code only (`backend/app/services/mpi/`), plus synthetic-only tests and governance evidence |
| **Selected serialization** | Transaction-scoped `pg_advisory_xact_lock` on one stable versioned key, acquired before tail read and before any SAVEPOINT; session-scoped locks never used |
| **Version control** | Atomic `UPDATE … SET version = version + 1 … RETURNING version` with optional optimistic guard |
| **Retry** | Bounded (max 3), explicit SQLSTATE classification, fresh session per attempt, reconcile-before-replay, no replay of permanent errors |
| **Explicitly NOT authorized** | Schema/DDL change, sentinel-row fallback (D-MPI-2a), new Redis/distributed lock/external service, API contract change, application migration, commit/push/merge/deploy, HOLD lift, D-020/D-021 approval |
| **Status** | `EXECUTION_AUTHORIZED_FOR_MPI_ONLY_SCOPE` — engineering evidence only |
| **Evidence** | `MPI-01` … `MPI-10` reports in this directory; `MPI-09_POSTGRESQL_VALIDATION_REPORT.md` §4–§6 |

**Statement of non-retroactivity:** this entry authorizes work from 2026-11-18 forward. It does not assert that D-MPI-1 was approved on any earlier date, and it does not convert the earlier architecture study into an approval record.

---

## 3. Decisions that remain unresolved (owner action still required)

| ID | Decision | Status after this work | Why it still blocks production/rollout |
|---|---|---|---|
| **D-MPI-2a** | Sentinel-row schema authorization (fallback A) | `NEEDS_OWNER_DECISION` — **not granted** | No schema change was made; advisory-lock path is PostgreSQL-specific and the sentinel fallback was deliberately not implemented |
| **D-MPI-3** | Cross-domain reference ownership / unmerge policy | `NEEDS_OWNER_DECISION` + `LEGAL_REVIEW_REQUIRED` | ~90 soft references across domains remain unmanaged; unmerge is not implemented; no fork-response policy exists |
| **D-MPI-4** | Audit event taxonomy for review decisions | `NEEDS_OWNER_DECISION` + `SECURITY_REVIEW_REQUIRED` | Review confirm/reject still writes no new `MergeAudit.event_type`; verification remains detection-only |
| **D-MPI-5** | Concurrent first-resolve policy | `NEEDS_OWNER_DECISION` | Existing `uq_identity_claims_lab_patient` constraint + reconcile path are implemented, but the policy for which caller "wins" is not formally accepted |
| **D-MPI-6** | Canonical-service hardening scope | `NEEDS_OWNER_DECISION` | MPI-02/03 hardening was applied inside the authorized MPI-only scope; broader cross-domain canonical ownership is unsettled |
| **D-020 / D-021 / Release** | Security / clinical / release decisions | `PENDING_APPROVAL` / `HOLD` | Unchanged; this work is not security certification, clinical certification, or production readiness |

---

## 4. Owner action request

1. **Accept or reject** the D-MPI-1 execution-authorization addendum above (§2). Acceptance does not lift HOLD.
2. **Resolve D-MPI-2a** if a portable sentinel fallback is required for non-PostgreSQL deployments.
3. **Resolve D-MPI-3 / D-MPI-4** (legal + security review) before any cross-domain repointing, unmerge, or new audit event taxonomy is introduced.
4. **Resolve D-MPI-5 / D-MPI-6** to accept the concurrent-first-resolve outcome semantics and canonical hardening scope.
5. **Keep HOLD** until D-020, D-021 and all release criteria are independently met.

**No action in this tranche changed any of these statuses.** This document records what was authorized, what was done, and what still needs a human owner decision.
