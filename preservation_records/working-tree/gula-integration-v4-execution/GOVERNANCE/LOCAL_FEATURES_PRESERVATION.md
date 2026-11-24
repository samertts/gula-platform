# Local Features Preservation Ledger

**Program:** GULA Stable v1.0.0 — Repository Unification
**Purpose:** Enumerate every capability that exists only on the local lineage (`remediate-security-001`, `f478676b`) and state exactly how it is preserved, so convergence on `origin/main` cannot silently lose work.
**Rule:** Archive-first; no feature is deleted without an approved, evidence-backed decision (`GOVERNANCE/AI_AGENT_RULES.md`).
**Date:** 2026-11-14

## 1. Preservation methods

| Method | Meaning |
|---|---|
| **PORT** | Re-apply the local code onto the remote base, adapting imports/contracts. Tests ported with it. |
| **FORWARD-MIGRATE** | Local schema re-expressed as a new forward Alembic revision. |
| **REFERENCE** | Kept as a standalone reference/scaffold, not wired into runtime (may be archived later). |
| **SUPERSEDE** | Remote implementation is canonical; local code retired to `archive/` with provenance; call-sites migrated. |
| **MERGE** | Three-way reconciliation at file level; local behaviour preserved inside the remote structure. |

## 2. Backend capabilities (local-only, `backend/app`)

| Capability | Local path | Method | Notes |
|---|---|---|---|
| Domain Platform (blueprints, isolation, lifecycle, versioning, contracts, binding, certification, 6 tables, 16 routes) | `backend/app/domain_platform/` (19 files) | **PORT** + **FORWARD-MIGRATE** (`20261114_0005`) | PROGRAM-STABLE-004 dormant strategic asset; no remote equivalent. |
| National professional registry (12 professions, verify = only privilege activation) | `backend/app/identity/professional_registry/` (5) | **PORT** + **FORWARD-MIGRATE** (`20261114_0004`) | Re-key FKs to remote `niam_persons`/`niam_identities`; preserve `authorization.py`. |
| Configurable identity providers / citizen registry | `backend/app/identity/citizen_registry/` (4) | **PARTIAL PORT** | Provider table preserved (`niam_identity_providers`); citizen verification **SUPERSEDED** by remote `verification_records`. |
| Cross-organisation access guard + hierarchy | `backend/app/identity/organizations/` (`guard.py`, `hierarchy.py`) | **MERGE** | Unique “zero cross-domain administration” guard; reconcile with remote `organization_service`. |
| Communication experience (inbox, events, preferences) | `backend/app/communication/experience/` + `models/communication_experience.py` (9) | **PORT** + **FORWARD-MIGRATE** (`20261114_0003`) | `comm_*` tables have no remote equivalent; reconcile with remote `identity/notifications`. |
| Canonical search service + indexer | `backend/app/capabilities/search_service/` (6) | **PORT** | Promoted in local PROGRAM-01; no remote canonical search. |
| Document PDF generator adapter | `backend/app/capabilities/document_management/pdf_generator.py` | **PORT** | Wraps `shared/pdf`. |
| Canonical workflow runtime | `backend/app/workflows/` (3) | **PORT (decision CR-1)** | Local replacement for remote `national/workflow_runtime` (known broken). Needs approval to retire the remote copy. |
| Master Patient Index | `backend/app/mpi/` + `models/mpi.py` (8) | **REVIEW** | Overlaps remote national identity merge; decide port vs supersede. |
| Notification queue (enterprise) | `backend/app/notifications/` (4) | **REVIEW** | Overlaps remote `identity/notifications` + `niam_notif_*`. |
| Route→service extractions (admin, dashboard, lab, metrics, mobile, quality control, sample, stats, test results) | `backend/app/services/*.py` (9) | **MERGE** | Tested behaviours preserved; remote restructured services differently. |
| OTLP telemetry wiring | `backend/app/telemetry.py` | **PORT/REVIEW** | Confirm against remote observability module. |
| Audit compatibility shim | `backend/app/audit/compat.py` | **REVIEW** | Align to remote audit. |
| National bootstrap seeding | `backend/app/core/bootstrap/platform_orgs.py` | **PORT** | Ministry/directorate seeding. |
| Local identity security helpers | `backend/app/identity/security.py`, `governance/boundaries.py` | **REVIEW** | Remote `identity/services/authorization_*` and `policy_engine` are canonical. |

## 3. Migrations

All still-needed local schema is preserved as forward revisions (see `DATABASE_COMPATIBILITY_REPORT.md`):

| Local revision | Preserved as |
|---|---|
| `20260802_0001_widen_patient_health_id` | `20261114_0001` |
| `20260802_0002_stable_fk_indexes` | `20261114_0002` |
| `20260804_0001_communication_experience` | `20261114_0003` |
| `20260805_0001_claims_lab_idempotency` | `20261114_0001` |
| `20260805_0002_stable_identity_platform` | registry/providers → `20261114_0004`; workspace tables **SUPERSEDED** |
| `20260806_0001_domain_platform` | `20261114_0005` |
| `20260810_0001_professional_authorizations` | `20261114_0004` |
| `20260722_0001` (15 indexes) | `20261114_0006` |

## 4. Security package (`security/`, 158 files)

- Not imported by backend (0 import hits); standalone toolkit/scaffold.
- **REFERENCE** disposition: preserve intact for now; per-module coverage and carry-forward controls in `SECURITY_COVERAGE_MATRIX.md`.
- Modules that must not be dropped before human review: `crypto/`, `compliance/`, `container/`, `kubernetes/`, `fhir/`, `terraform/`, `threat_detection/`, `headers/`.

## 5. Governance, tooling and engines

| Asset | Local-only count | Method |
|---|---:|---|
| `.ai/` governance brain/state/baselines | 153 | **PRESERVE** |
| `.opencode/` agent skills/config | 418 | **PRESERVE** |
| `.omm/` tooling state | 61 | **PRESERVE** |
| `.agents/` skill definitions | 4 | **PRESERVE** |
| `scripts/` engines (architect, optimizer, learner, deployer, orchestrator, reviewer, builder, kernel, architecture, domains, project_brain, enterprise_validation_engine, self_heal) | 204 files | **PRESERVE** (not runtime-critical; port after backend merge) |
| `archive/` legacy trees (ADR-028) | 946 | **PRESERVE** (historical) |
| Local program reports (`docs/`, root) | 924 docs | **PRESERVE**; later dedupe against remote docs |

## 6. Tests (146 local-only, 120 modified)

- PORT each preserved feature's tests with the feature (domain platform 71, professional registry/authorization, communication, search, workflows, services).
- **SUPERSEDED** features: move their tests to `archive/` with a provenance header; do not delete.
- Do not adjust a test to make a gate pass; fix code or record an explicit exception.

## 7. Frontend

| Local asset | Count | Method |
|---|---:|---|
| `frontend-v3` modified files | 118 | **MERGE** (three-way) |
| `frontend-v3` local-only files | 31 | **REVIEW** — includes demo/showcase and test infra |
| `mobile` modified / local-only | 172 / 2 | **MERGE** |
| `hospital_desktop` modified | 23 | **MERGE** |
| `shared/` local-only | 36 | **MERGE** (`shared/security/` is byte-identical on both sides) |

Decision CR-2 (authoritative web client: `frontend-v3` vs `apps/*`) is still open and gates the frontend merge.

## 8. Superseded local capabilities (retired, not deleted)

| Capability | Local tables/code | Remote canonical replacement |
|---|---|---|
| Workspace platform | `niam_workspaces` + 7 `niam_workspace_*`, `identity/workspaces/` | `niam_workspace_contexts`, `niam_memberships*`, `niam_roles/permissions`, `identity/api/workspaces.py` |
| Citizen identity verification | `niam_citizen_identity_verifications`, `identity/citizen_registry/` verification path | `verification_records` (`20260814_0001`), `verification_record_service` |
| Standalone security toolkit | `security/` | `backend/app/security/*` + `backend/app/identity/*` (runtime); toolkit retained as reference |

## 9. Preservation status

| Area | Status |
|---|---|
| Migrations | **PRESERVED** (forward-authored, isolated-runtime PASS) |
| Backend unique modules | **PENDING PORT** (inventory complete) |
| Security toolkit | **REFERENCE — preserved** |
| Governance/tooling | **PRESERVED** |
| Tests | **PENDING PORT** |
| Frontend | **BLOCKED** on CR-2 |
| Superseded features | **DECIDED — retire to archive during code merge** |

---
_No local feature has been deleted. This ledger is the checklist the code-merge phase must satisfy._
