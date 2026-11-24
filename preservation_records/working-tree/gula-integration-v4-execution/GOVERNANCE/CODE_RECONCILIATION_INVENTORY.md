# Code Reconciliation Inventory

**Program:** GULA Stable v1.0.0 — Repository Unification
**Task:** Inventory the diverged working tree between local `HEAD` (`f478676b`, `remediate-security-001`) and `origin/main` (`2827c1ff`) before any code is ported.
**Integration branch:** `integration/gula-unification-v1` (base = `origin/main` @ `2827c1ff`).
**Status:** Phase 2 — RECONCILE (read-only inventory; no application code changed).
**Date:** 2026-11-14

> Evidence source: `$HOME/GULA_RECOVERY_BACKUP_20261114_190243/snapshot-comparison/` (rename-aware, `--no-renames` tree diff).
> Legend: **M** = present on both sides but modified · **A** = exists only on `origin/main` (adopt) · **D** = exists only on local `HEAD` (preserve/account).
> Verification vocabulary per `GOVERNANCE/AI_AGENT_RULES.md`: nothing here is "verified"; this is a static inventory.

## 1. Top-level disposition

| Area | M | A (remote-only) | D (local-only) | Total | Proposed disposition |
|---|---:|---:|---:|---:|---|
| `backend` | 1102 | 338 | 233 | 1673 | **MERGE** — adopt remote as base; forward-port selected local modules; reconcile tests |
| `docs` | 25 | 163 | 924 | 1112 | **MERGE** — keep remote program docs; preserve local program reports (decision on archive layout) |
| `archive` | 0 | 0 | 946 | 946 | **PRESERVE** — local archival of legacy trees (ADR-028); historical, no runtime effect |
| `platform` | 0 | 636 | 0 | 636 | **ADOPT** — remote-only platform layer |
| `.opencode` | 0 | 0 | 418 | 418 | **PRESERVE** — local agent/tooling configuration (not runtime) |
| `apps` | 0 | 327 | 0 | 327 | **ADOPT** — remote-only web/UI apps (`gula-web-suite`, `gula-platform-ui-refresh`) |
| `scripts` | 32 | 26 | 204 | 262 | **MERGE** — preserve local engine scripts; adopt remote scripts |
| `mobile` | 172 | 66 | 2 | 240 | **MERGE** — diverged mobile app |
| `frontend-v3` | 118 | 84 | 31 | 233 | **MERGE** — primary web client; see §6 |
| `(repo root)` | 26 | 140 | 13 | 179 | **MERGE** — remote adds ~140 program/report docs |
| `security` | 0 | 0 | 158 | 158 | **PRESERVE/ACCOUNT** — local standalone security package; see `SECURITY_COVERAGE_MATRIX.md` |
| `.ai` | 0 | 0 | 153 | 153 | **PRESERVE** — local governance brain/state |
| `mobile-expo` | 0 | 133 | 0 | 133 | **ADOPT** — remote-only |
| `shared` | 30 | 1 | 36 | 67 | **MERGE** — shared security/domain libraries |
| `.omm` | 0 | 0 | 61 | 61 | **PRESERVE** — local tooling |
| `nhop-platform` | 0 | 55 | 0 | 55 | **ADOPT** — remote-only |
| `packages` | 0 | 55 | 0 | 55 | **ADOPT** — remote-only monorepo packages |
| `.github` | 27 | 10 | 8 | 45 | **MERGE** — CI/workflows |
| `reports` | 0 | 29 | 1 | 30 | **ADOPT** (remote) + preserve local report |
| `.audit` | 0 | 25 | 0 | 25 | **ADOPT** |
| `hospital_desktop` | 23 | 1 | 0 | 24 | **MERGE** |
| `contracts` | 23 | 0 | 0 | 23 | **MERGE** |
| `config` | 15 | 2 | 3 | 20 | **MERGE** |
| `governance` | 17 | 0 | 0 | 17 | **MERGE** |
| `k8s` | 9 | 0 | 6 | 15 | **MERGE** |
| `services` | 14 | 0 | 0 | 14 | **MERGE** (future decomposition; not deleted) |
| `tools`, `presentations`, `security-audit` | 0 | 13/12/11 | 0 | 36 | **ADOPT** |
| `.agents` | 0 | 0 | 4 | 4 | **PRESERVE** |
| `STATUS`, `EVIDENCE`, `PROGRAM`, `GOVERNANCE`, `api` | 0 | 1–3 each | 0 | 9 | **ADOPT** — remote program scaffolding |
| misc root (`cli`, `client`, `ai`, `docker`, `server`, `helm`, `edge_agent`, `tests`, …) | ~13 | ~4 | 0 | varies | **MERGE** per file |

## 2. `backend/app` — the core merge

### 2.1 Local-only modules (D = 80 files) and proposed disposition

| Local-only module | Files | Proposed disposition | Rationale |
|---|---:|---|---|
| `backend/app/domain_platform/` | 19 | **PRESERVE** | PROGRAM-STABLE-004 Domain Platform (dormant strategic asset, no remote equivalent). |
| `backend/app/identity/workspaces/` | 4 | **SUPERSEDE** (decided) | Replaced by remote `identity/api/workspaces.py`, `identity/services/workspace_service.py`, `identity/models/workspace.py`, `niam_workspace_contexts`. |
| `backend/app/identity/citizen_registry/` | 4 | **SUPERSEDE** (decided) | Replaced by remote `verification_record_service` + `verification_records` (20260814_0001). |
| `backend/app/identity/professional_registry/` | 5 | **PRESERVE + ADAPT** | National professional licence registry has no remote equivalent; re-key to remote `niam_accounts`/`niam_identities`/`niam_persons`. |
| `backend/app/identity/organizations/` (`guard.py`, `hierarchy.py`) | 3 | **REVIEW** | Cross-org administration guard may be unique; compare with remote `organization_service`/`account_lifecycle_service`. |
| `backend/app/identity/security.py`, `identity/governance/boundaries.py` | 2 | **REVIEW** | Overlaps remote `identity/services/authorization_*`, `policy_engine`. |
| `backend/app/communication/experience/` + `models/communication_experience.py` | 9 | **MERGE** | Local comm inbox/preferences (`comm_*` tables). Remote has `identity/notifications` and `niam_notif_*`; reconcile or forward-port as distinct feature. |
| `backend/app/capabilities/search_service/` | 6 | **PRESERVE** | Canonical search promoted in local PROGRAM-01; remote has no canonical search package. |
| `backend/app/capabilities/document_management/pdf_generator.py` | 1 | **PRESERVE** | Adapter over `shared/pdf`; unique. |
| `backend/app/mpi/` + `models/mpi.py` | 8 | **REVIEW** | Master Patient Index vs remote national identity-merge services; likely overlapping. |
| `backend/app/notifications/` | 4 | **REVIEW** | Queue/telegram enterprise vs remote `identity/notifications` + `niam_notif_*`. |
| `backend/app/workflows/` | 3 | **PRESERVE / SUPERSEDE remote** | Local canonical replacement for remote `backend/app/national/workflow_runtime/` (remote-only, was broken — `application/service.py` 0 bytes). See §5 high-risk. |
| `backend/app/services/*.py` (9 service extracts) | 9 | **MERGE** | Local route→service extraction (`admin`, `dashboard`, `lab`, `metrics`, `mobile`, `quality_control`, `sample`, `stats`, `test_result`). Remote has a different `backend/app/services/` set. |
| `backend/app/telemetry.py` | 1 | **PRESERVE/REVIEW** | OTLP/HTTP tracing wiring; confirm remote equivalent (`core/observability`?). |
| `backend/app/audit/compat.py` | 1 | **REVIEW** | Compatibility shim; check remote audit layout. |
| `backend/app/core/bootstrap/platform_orgs.py` | 1 | **PRESERVE** | National ministry/directorate bootstrap. |

### 2.2 Remote-only modules (A = 188 files) — adopt

Grouped by subsystem (count): `identity` 41, `national` 33, `payments` 19, `services` 15, `core` 10, `clinical_gateway` 7, `integration` 7, `routes` 7, `chronic_care` 6, `devices` 6, `security` 6, `billing` 5, `platform` 5, `capabilities` 4, `clinical` 4, `models` 4, plus singletons (`audit`, `blood_bank`, `contracts`, `ehr`, `fhir`, `notifications`, `nursing`, `radiology`, `reference`).

These implement the newer origin/main lineage (account/membership/role model, clinical gateway, payments/billing, device gateways, chronic care, national interoperability). They are adopted wholesale; local code must be adapted to their contracts, not the reverse.

### 2.3 Diverged files (M = 905 in `backend/app`)

These exist on both sides with different content. They must be reviewed three-way (local base → remote base → local intent). Highest-risk clusters:
- `backend/app/identity/` — remote account/membership/role architecture vs local workspace/professional/citizen modules.
- `backend/app/factory.py`, `backend/app/routes/` — route registration and composition root.
- `backend/app/models/` — ORM ownership of shared tables (`national_facilities` duplicate-owner blocker NR-006).
- `backend/app/security/` — local security package vs remote `backend/app/security` (6 remote-only files).

## 3. `backend/tests` (M 120 · A 95 · D 146)

- 146 local-only test files, 95 remote-only, 120 modified.
- Tests are **not** deleted to make checks pass (`AI_AGENT_RULES.md`). Reconciliation rule: for each preserved local feature, port its tests; for retired features, retain the tests in `archive/` with a provenance note; for remote features, adopt remote tests.
- Local test count baseline from the local lineage (5089 backend tests at PROGRAM-01 closure) is **not** comparable to remote's suite until the merge completes. Do not cite it as current.

## 4. Governance / tooling stacks (local-only, preserve)

| Area | Files | Note |
|---|---:|---|
| `.ai/` | 153 | Local architecture/governance state, baselines, engine state. |
| `.opencode/` | 418 | Agent skills/configuration. Not runtime. |
| `.omm/` | 61 | Local tooling state. |
| `.agents/` | 4 | Skill definitions. |
| `scripts/` local-only | 204 | Local engines: `architect`, `optimizer`, `learner`, `deployer`, `orchestrator`, `reviewer`, `builder`, `kernel`, `architecture`, `domains`, `project_brain`, `enterprise_validation_engine`, `self_heal`. |
| `security/` | 158 | See `SECURITY_COVERAGE_MATRIX.md`. |
| `archive/` | 946 | Legacy trees archived under local ADR-028. |

## 5. High-risk reconciliation conflicts (beyond migrations)

| ID | Conflict | Evidence | Decision needed |
|---|---|---|---|
| CR-1 | Local `backend/app/workflows/` vs remote `backend/app/national/workflow_runtime/` | Local removed `workflow_runtime` (0-byte service, HTTP 500) and built canonical `workflows`; remote still ships `workflow_runtime` | Keep local `workflows` and retire remote `workflow_runtime`, or adopt remote (re-introduces known defect). **Recommend local.** |
| CR-2 | `frontend-v3` vs remote `apps/` (`gula-web-suite`, `gula-platform-ui-refresh`) | Both sides ship web clients; remote adds a monorepo apps layer and `mobile-expo` | Decide the authoritative web client and deployment ownership (charter WEB-SURFACE blocker). |
| CR-3 | Local `security/` package vs remote in-app security | Remote has `backend/app/identity` authorization, `clinical_gateway`, `national/security`, `backend/app/security`; no `security/` dir | Preserve/account local package (charter) without double-enforcing controls. See `SECURITY_COVERAGE_MATRIX.md`. |
| CR-4 | Local service extraction (`backend/app/services/*`) vs remote `backend/app/services/` + `backend/services/` | Both sides restructured services differently | File-level merge; preserve local tested behaviors. |
| CR-5 | Duplicate ORM ownership of `national_facilities` | Open blocker NR-006 (pre-existing) | Single owner; not introduced by unification. |

## 6. `frontend-v3` (M 118 · A 84 · D 31)

Both sides modified the primary client. Remote additions include new app integration; local additions include demo/showcase and test infrastructure. Reconciliation requires a file-level three-way merge plus `tsc --noEmit`, ESLint and Vite build gates. Do not assume either side is a superset.

## 7. Next actions

1. Get decisions on CR-1 (workflows) and CR-2 (web client ownership). CR-3 disposition is documented in the security matrix.
2. Author forward-only migrations F1…F7 (see `MIGRATION_RECONCILIATION_MATRIX.md` §5/§8) including the professional-registry tables.
3. Port preserved local modules (`domain_platform`, `professional_registry`, `search_service`, `pdf_generator`, `workflows`, `platform_orgs`) onto the remote base with adapted imports/contracts; port their tests.
4. Retire superseded local modules (`identity/workspaces`, `identity/citizen_registry`) in favour of remote equivalents and update all call-sites.
5. Re-run static gates (`ruff`, `tsc`, ESLint, migration graph) before any commit; run the full backend/frontend test suites only after the module merge stabilizes.

---
_Static inventory generated from the rename-aware tree diff. No application code, tests, or database state were modified._
