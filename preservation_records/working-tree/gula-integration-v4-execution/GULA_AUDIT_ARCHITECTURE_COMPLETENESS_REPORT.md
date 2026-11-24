# GULA Audit Architecture Completeness Report

**Directive:** GULA-PBR-2026-11-19, §4 (Priority P1 — Audit System End-to-End Integrity)  
**Repository:** `gula-integration` · **Branch:** `integration/gula-unification-v1`  
**HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549` · **Date:** 2026-11-19  
**Method:** read-only source scan (`grep`, `read`), cross-checked against the two prior independently verified audit reports and the Team C remediation register. No file except this report was created for this workstream; no code was changed here.

---

## 1. Scope and result

This review extends the two previously corrected findings (`AUDIT-POSITIONAL-001` / `SEC-001`, `AUDIT-BYPASS-001` / `SEC-014`) to the whole active audit surface. **No new actionable bypass of the canonical hash chain was found.** One pre-existing schema-mismatch finding is deliberately retained per directive §4. Domain-specific audit subsystems are classified and left untouched (no opportunistic repair of dormant/incompatible systems).

| Classification | Count | Status | Note |
|---|---:|---|---|
| Canonical chained writer (`log_action`) | 1 | `INDEPENDENTLY VERIFIED` (prior award, engineering scope) | `backend/app/services/audit_service.py` |
| Modules calling canonical writer | 59 | `INDEPENDENTLY VERIFIED` (prior award for the 50 corrected call sites) | 206 textual `log_action(` occurrences incl. definition/re-export |
| Direct `AuditLog(...)` ORM writes outside canonical writer | 0 | `INTEGRATED` | only `audit_service.py:214` constructs the ORM model |
| Raw SQL audit writers | 2 | see §4 | canonical SQLite write reservation + retained `shared/audit` mismatch |
| Domain-specific audit subsystems | 13 tables | `IMPLEMENTED` (classified, not chained) | separate ownership; no chain claim |
| Background/worker processes writing canonical audit directly | 0 | `IMPLEMENTED` | verified by source scan |

---

## 2. Canonical writer and chain

- **Writer:** `backend/app/services/audit_service.py::log_action` — single entry point; `chain_hash = SHA256(prev_hash + canonical record JSON)`.
- **Chain verification:** `verify_audit_chain()` — recomputes in `id ASC` order, skips legacy NULL-hash rows, reports `intact` / `tampered` with `broken_entries`.
- **Immutability:** PostgreSQL `BEFORE UPDATE/DELETE` triggers from `20250322_0002_perf_indexes_audit_protection.py` reject mutation at the DB layer. SQLite has no trigger (dev/test dialect only); tamper detection is verification-based there.
- **SEC-015 (this session):** predecessor now read before INSERT on both dialects; concurrent writers serialized by a PG advisory xact lock / SQLite write reservation. See `GULA_SEC015_AUDIT_CHAIN_REMEDIATION_REPORT.md`.
- **Decorator:** `backend/app/audit/__init__.py::audit_log` delegates to canonical `log_action` then commits; used on three FHIR routes (`ehr_fhir.py:1367,1391,1414`). No independent chain implementation.

## 3. Every active writer classified

| Pathway | Writer | Canonical chain? | Evidence | Status |
|---|---|---|---|---|
| Service/route audit events | `log_action` | Yes | 59 modules; prior 50-call-site fix in `GULA_AUDIT_POSITIONAL_FIX_REPORT.md:44` | `INDEPENDENTLY VERIFIED` (prior) |
| AI critical-result alerts | `log_action` (was direct `AuditLog`) | Yes (since `AUDIT-BYPASS-001`) | `routes/ai.py::_emit_critical_alert`; `GULA_AUDIT_BYPASS_FIX_REPORT.md:29,40` | `INDEPENDENTLY VERIFIED` (prior) |
| FHIR create/update/delete | `@audit_log` → `log_action` | Yes | `audit/__init__.py:14-60`; `ehr_fhir.py:1367,1391,1414` | `TESTED` |
| Compliance UI read (`/compliance/audit-integrity`) | `verify_audit_chain` (read-only) | n/a | `routes/compliance.py:679`; 21 tests in `test_compliance_integrity.py` | `TESTED` |
| Governance audit events | `gov_national_audit_events` (own model) | No — separate subsystem | `governance/models/security.py:29`; route auth tested 11/11 | `IMPLEMENTED` |
| Control-plane audit | `shared/audit/service.py` raw SQL | **No — retained finding** | §4 below | `BLOCKED` (owner/integration decision) |
| Domain-specific audit tables | own models/services | No — separate subsystems | §5 | `IMPLEMENTED` (classified) |

## 4. Retained finding — `shared/audit/service.py` (do not repair here)

`shared/audit/service.py:43-56` issues a raw `INSERT INTO audit_logs (action, entity_type, entity_id, …, previous_hash, chain_hash, timestamp)` with its own chain computation (`previous_hash`, `GENESIS` sentinel). This does **not** match the canonical schema (`resource_type`, `resource_id`, `created_at`, 64-zero genesis) and therefore cannot be verified by `verify_audit_chain()`. It is reached only through `backend/app/control_plane/audit.py::EnterpriseAudit`, which is wired as an optional auditor in `control_plane/sdk.py:50,60,132`; no route or task calls it directly in this tree.

Per directive §4 this mismatch **remains documented** until its ownership and integration strategy are resolved. It is classified `BLOCKED` (ownership/architecture decision), not `PRODUCTION READY`, and no code change was made.

Note: the SEC-015 SQLite guard `UPDATE audit_logs SET id = id WHERE 1 = 0` is the only other raw statement touching `audit_logs`; it is dialect-gated to non-PostgreSQL, changes no values, and is covered by the structural test in `test_audit_chain_integrity.py`.

## 5. Domain-specific audit subsystems (classified, untouched)

| Subsystem | Table | Model | Ownership |
|---|---|---|---|
| Identity (NIAM) | `niam_audit_entries` | `identity/models/audit.py:267` | Identity platform |
| Identity admin portal | `niam_admin_audit_logs` | `identity/admin/models.py:60` | Identity platform |
| National identity | `national_identity_audit_logs` | `national/domain/audit_identity.py:7` | National domain |
| National task engine | `national_task_audit_logs` | `national/task_engine/infrastructure/models.py:126` | National domain |
| Partner ecosystem | `ecosystem_partner_audit_logs` | `national/ecosystem/partners/models.py:73` | National domain |
| Merge audit (national) | `national_merge_audit` | `national/domain/merge_record.py:42` | National domain |
| Merge audit (MPI) | `mpi_merge_audit` | `services/mpi/models.py:192` | MPI service |
| Governance | `gov_national_audit_events`, `gov_ai_audit_events`, `gov_health_number_audit` | `governance/models/*.py` | Governance domain |
| Clinical quality | `clinical_audit_records` | `clinical/quality/models.py:73` | Clinical domain |
| Authorization | `authorization_audit` | `models/authorization.py:210` | Identity/security |
| Billing / payments | `billing_audit_events`, `pay_audit_events`, `pay_subscription_audit_events` | `billing/models.py:126`, `payments/models*.py` | Financial domains |

These are independent records, not extensions of the canonical `audit_logs` chain. No claim is made that they are tamper-evident or chained. Their coexistence is documented ownership, not a bypass of the canonical chain.

## 6. Background jobs / workers / administrative paths

- Source scan found **no** `log_action` call in any module whose path indicates task/worker/job/background/outbox/event processing. Audit writes occur synchronously in request/service paths.
- Outbox events emitted by LIMS critical-result workflows are durable records in their own tables, not audit-chain entries; `AUD-CLIN-001` added a commit in `process_critical_alert` so the `notification_pending` outbox row survives the request. This is clinical-alert durability, not an audit bypass, and is already independently verified by Team C.
- Administrative identity/permission changes, clinical record changes, patient access and FHIR reads/writes route through the canonical writer or the decorator (§3).

## 7. Regression tests

No new defect was confirmed in this workstream, so no new test was added here. Existing evidence:
- `backend/tests/unit/test_audit_chain_integrity.py` — 13/13 (SEC-015, including tamper, NULL hash, missing predecessor, concurrency, rollback).
- `backend/tests/unit/test_audit_bypass_regression.py` — 3/3 (`AUDIT-BYPASS-001`).
- `backend/tests/unit/test_audit_positional_regression.py` — 11/11 (`AUDIT-POSITIONAL-001`).
- `backend/tests/test_compliance_integrity.py` — 21/21 after removal of hash re-stitching.
- Related audit suites total: **73 passed / 0 failed** (`/tmp/opencode/sec015_related_audit.log`).

## 8. Strict status and non-claims

- Canonical audit chain: `TESTED` (this session) + prior `INDEPENDENTLY VERIFIED` for the two corrected bypass findings; SEC-015 independent review recorded in its dedicated report.
- `shared/audit/service.py` schema mismatch: `BLOCKED` (retained, owner/architecture decision).
- Domain-specific subsystems: `IMPLEMENTED` (classified only; no integration/verification claim).

No `PRODUCTION READY`. No clinical, legal, regulatory, ministerial or release approval. No new audit engine created. No production DB/Redis access, real PHI, or secrets. No commit, push, merge, PR or deployment. Standing decision remains **HOLD**; Stable v1.0.0 is **NOT declared**.
