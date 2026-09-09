# GULA — Ministry of Health Delivery Baseline

**Branch commit:** `1a164ccd` (branch `claude/nr-003-canonical-drug-identity`)
**Base:** `main` @ `46158e90`
**Date:** 2026-09-09
**Status:** PRE-DELIVERY — NOT PRODUCTION READY

Every claim below is backed by executed evidence or is explicitly marked
NOT VERIFIED. Nothing here is inferred from code inspection alone.

---

## 1. Architecture scope

FastAPI monolith (`backend/app/`) on PostgreSQL 17/16 + Redis 7, behind an nginx
gateway. Arabic-first. A parallel `services/` tree exists but is not the
deployment target.

Canonical pharmacy identity model is fixed by **ADR-006** (`docs/pharmacy-platform/ADR.md`):

| Concern                             | Identity              | Rule                                         |
| ----------------------------------- | --------------------- | -------------------------------------------- |
| Internal database key               | `Integer` PK          | never exposed publicly                       |
| Public/canonical GULA drug identity | `drug_id`, UUID4      | server-generated, immutable, unique          |
| Business code                       | `drug_code`           | mutable; never a PK, FK or clinical-rule key |
| Package                             | GTIN (GS1)            | package level only (ADR-002)                 |
| Classification                      | ATC                   | classification only (ADR-005)                |
| FHIR / sync                         | `fhir_id` / `sync_id` | distinct identities                          |

The UUID4 identity is a **GULA platform identity, not a Ministry of Health
national registration number**. A future MoH identifier is to be added as an
additional external identifier.

## 2. Migration status

| Item                                        | State                     | Evidence                                                     |
| ------------------------------------------- | ------------------------- | ------------------------------------------------------------ |
| Revision ids unique                         | PASS                      | 102 revisions, no duplicates                                 |
| Exactly one head                            | PASS                      | `20260909_0001`                                              |
| `clinical_command_receipts` reachable       | PASS                      | 3 graph-integrity tests                                      |
| `20260815_0023` applies on a clean database | **PASS (was impossible)** | clean upgrade exit 0; both catalog FKs `integer`             |
| Clean database `upgrade head`               | **FAIL**                  | aborts at `20260820_0004`, see P0-1                          |
| Revisions applied before the abort          | 98                        | previously aborted at ~30 and rolled back to `20260505_0005` |
| Existing-database upgrade path              | NOT VERIFIED              | only clean-database creation was exercised                   |

## 3. Verified workflows (executed evidence)

| Workflow                                                                           | Evidence                                                                                                                                                                                                                                                                                                    |
| ---------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Blood Bank reservation/issue HTTP idempotency, failure injection, Wave 1 lifecycle | 32 tests passed against PostgreSQL 16.13 with the real FastAPI application                                                                                                                                                                                                                                  |
| Migration graph integrity                                                          | 3 tests passed                                                                                                                                                                                                                                                                                              |
| Pharmacy POS / substitution (ORM level)                                            | `test_pharmacy_pos.py` passed                                                                                                                                                                                                                                                                               |
| Canonical drug identity migration                                                  | 13/13 checks against real PostgreSQL: Integer PKs preserved, `drug_code` preserved, all rows identified, unique, v4 UUID, not a deterministic derivation, physical type `uuid`, NOT NULL, unique constraint + index present, catalog has no `lab_id`, re-run is a no-op, duplicate rejected by the database |
| Drug identity immutability (service layer)                                         | 6 focused tests passed: identity cannot be client-chosen at creation, `id`/`drug_id` updates rejected, business fields still updatable, clinical rule keyed on FK not `drug_code`                                                                                                                           |
| Pharmacy non-regression after the change                                           | 15 tests passed (POS, radiology workflow, migration graph, identity)                                                                                                                                                                                                                                        |
| Deterministic platform core                                                        | 25 tests passed                                                                                                                                                                                                                                                                                             |
| Security + tenant isolation regression                                             | passed in CI on `main` (evidence upload blocked by artifact quota)                                                                                                                                                                                                                                          |

## 4. Platform self-assessment (deterministic, no AI)

`python3 -m gula_intel.cli findings` on this commit:

| Rule                                      | State                | Status                   |
| ----------------------------------------- | -------------------- | ------------------------ |
| GULA-MIG-001 duplicate revision ids       | RAN, no findings     | VERIFIED                 |
| GULA-MIG-002 single head                  | RAN, no findings     | VERIFIED                 |
| GULA-STATE-001 duplicate state keys       | RAN, no findings     | VERIFIED                 |
| **GULA-SCHEMA-001 FK type compatibility** | **RAN, no findings** | **VERIFIED** (was 2× P0) |
| GULA-ARCH-001 table ownership             | RAN, found           | FAILED — 1× P1           |

Overall health **DEGRADED** (previously BLOCKED). `production_ready: false`.

## 5. Known blockers

### P0 — blocks a clean deployment

**P0-1. Hospital domain has no migration coverage.**
13 of 14 hospital ORM tables are created by no migration. `20260820_0004`
declares a foreign key to `hospital_operation_theaters`, which nothing creates,
so a clean-database `upgrade head` aborts there. Same defect class as NR-003.
Evidence: `psycopg2.errors.UndefinedTable: relation "hospital_operation_theaters" does not exist`.

**P0-2. Pharmacy ORM ↔ physical schema divergence.**
All 23 pharmacy tables shared between the ORM and the migrations diverge:
roughly 190 ORM-only columns, ~200 database-only columns, ~150 type mismatches,
including `id: VARCHAR != INTEGER`. The ORM cannot execute against the migrated
schema, so all 63 pharmacy endpoints would fail at runtime. NR-003's identity
model is now correct in the database; the ORM/API layer is not yet reconciled.
Classification of every artifact (KEEP / RECONCILE / REPLACE) is recorded in the
NR-003 analysis.

### P1 — required for delivery

- **P1-1.** Pharmacy public API still exposes the internal Integer PK as the
  canonical identifier; it must move to `drug_id`. Blocked behind P0-2.
- **P1-2.** Clinical safety rules — **ORM-only defect, not a database risk.**
  Verified on the migrated schema: `pharmacy_contraindication_rules`,
  `pharmacy_allergy_rules`, `pharmacy_dose_guidelines` and
  `pharmacy_drug_monitoring` each already carry `drug_id integer` as a foreign
  key to the catalog, and **none has a physical `drug_code` column**. The
  contract §7 invariant — a business-code edit can never detach a clinical rule
  — therefore already holds in the database. The denormalized `drug_code` exists
  only in the Generation B ORM, so no data migration is required and no mapping
  is ambiguous; the fix is subsumed by P0-2. This corrects an earlier
  characterisation of it as a live clinical-safety risk.
- **P1-3.** No migration-built schema test harness. Pharmacy tests build schema
  from ORM metadata on SQLite, which is how P0-2 survived undetected.
- **P1-4.** `scripts/constitution_enforcer.py` crashes on `ast.Str` (removed in
  Python 3.12) while its workflow pins 3.14; the governance gate is red on
  `main` itself. One-line fix, not applied here.
- **P1-5.** Golden-path end-to-end journeys are **NOT VERIFIED**.

### P2 — important

- **P2-1.** GULA-ARCH-001: `national_facilities` mapped by two app packages.
- **P2-2.** `pharmacy_drug_substitution_requests` carries two `String(26)`
  catalog references with no FK, inconsistent with the corrected rules table.
- **P2-3.** GitHub Actions artifact storage quota exhausted account-wide, so CI
  evidence cannot be archived.
- **P2-4.** Repository security controls not enabled: code scanning and
  dependency graph are off; the Secret Scan workflow token lacks
  `pull-requests:read` and never actually runs.
- **P2-5.** Pre-existing repo-wide formatting debt (Ruff Format, Prettier) and a
  failing `frontend-v3` test (`MobileBottomNav.test.tsx`).

### P3 — post-delivery

- Generation C normalisation (formulation / package / pricing / ATC hierarchy /
  ingredients) — **DEFERRED, FOLLOW-UP PHARMACY CORE BUILD**.
- GULA-SCHEMA-002 ORM ↔ migration-built schema drift detector — **DEFERRED**.
  Design note: type comparison must normalise dialect-rendered equivalents
  (SQLAlchemy `DateTime(timezone=True)` _is_ PostgreSQL `TIMESTAMP`), or it will
  emit false positives.

## 6. Security posture

Enforced and unchanged by this baseline: JWT authentication, RBAC/ABAC,
per-tenant isolation on patient data, hash-chained audit logging, durable
idempotency for safety-critical clinical commands, secrets with no hardcoded
fallbacks. Nothing was stubbed, weakened or bypassed.

The new `drug_id` is an **identifier, not an authorization mechanism**.
Authorization remains based on the authenticated principal, organization,
facility, relationship, role and policy. Because the catalog is global national
reference data (ADR-001), it carries no tenant column; tenant scope lives on
inventory and location records.

**Not verified in this baseline:** IDOR testing against pharmacy endpoints
(blocked behind P0-2).

## 7. Data integrity posture

- Internal Integer primary keys are never rewritten.
- `drug_id` backfill runs exactly once and is guarded against regeneration.
- The identity migration is **fail-closed**: it re-checks NULLs and duplicates
  and aborts with a structured diagnostic before applying `NOT NULL`/`UNIQUE`,
  rather than transforming or discarding data.
- No destructive operation, no PK rewrite, no data deletion.
- **Production data: `PRODUCTION_DATA_NOT_PRESENT_IN_VERIFICATION_ENVIRONMENT`.**
  All verification used disposable local PostgreSQL with synthetic rows only.
  Production row counts remain UNKNOWN and were never invented.

## 8. What is NOT implemented

- Pharmacy ORM/API reconciliation (P0-2) and the public `drug_id` API contract (P1-1).
- Hospital domain migrations (P0-1).
- Clinical-rule FK conversion (P1-2).
- Generation C normalisation, GULA-SCHEMA-002 (P3).
- Any frontend change. No frontend route was modified or verified in this baseline.
- End-to-end golden-path verification.

## 9. Production readiness

**`production_ready: false`.**

A clean-database deployment is not yet possible (P0-1). The pharmacy domain is
not runtime-executable against the migrated schema (P0-2). No end-to-end
clinical journey has been verified. This baseline establishes the canonical
pharmacy identity in the database and removes the migration blocker that made
the chain unbuildable; it does not constitute a demonstrable delivery.
