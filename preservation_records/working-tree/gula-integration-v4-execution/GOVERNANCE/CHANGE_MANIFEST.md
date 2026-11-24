# Change Manifest — Unification Working Tree

**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1`
**HEAD:** `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` — *"Add GitHub Actions workflow for GitHub Pages deployment"* (2026-11-07)
**Synchronisation with upstream:** `git rev-list --left-right --count HEAD...origin/main` → **`0  0`** (identical to `origin/main`)
**Commits created by this program:** **0**
**Pushes / merges / PRs / deploys:** **none**
**Manifest date:** 2026-11-17

---

## 1. Totals

| Bucket | Count | Insertions | Deletions |
|---|---:|---:|---:|
| Unstaged modifications (` M`) | **80** | **1 451** | **1 860** |
| Staged renames (`R `) — byte-identical `R100` | **20** | **0** | **0** |
| Untracked (`??`) | **88** | not counted (new files) | — |
| **Total working-tree entries** | **188** | | |

`git diff --cached --numstat` sum: **insertions 0 / deletions 0** across the 20 renames — they are
pure moves, no content edit. These 20 renames are **pre-existing** (the CR-1 archive of the broken
workflow runtime) and are present in the pre-remediation state; this program did not stage or
unstage anything.

`git status --porcelain` bucket distribution:

```
88 ??
80  M
20 R
```

> **Topology note:** this directory is a **linked worktree** of the `gula-platform` repository
> (`git rev-parse --git-dir` → `…/gula-platform/.git/worktrees/gula-integration`). A commit here
> writes objects and a branch ref into the shared `.git`; the parent working tree is untouched. See
> `GOVERNANCE/GIT_READINESS_REPORT.md` §1. Branch `integration/gula-unification-v1` does **not**
> exist on `origin`.

---

## 2. Staged renames (20, all `R100`, 0 content change)

All 20 move broken/duplicate workflow runtime code into `archive/legacy/workflow_runtime/`
(CR-1). Verified byte-identical: `git diff --cached --numstat` = `0 0` for every entry.

| From | To |
|---|---|
| `backend/app/identity/workflows/engine.py` | `archive/legacy/workflow_runtime/identity_workflows/engine.py` |
| `backend/app/identity/workflows/models.py` | `archive/legacy/workflow_runtime/identity_workflows/models.py` |
| `backend/app/national/workflow_runtime/__init__.py` | `archive/legacy/workflow_runtime/national_workflow_runtime/__init__.py` |
| `backend/app/national/workflow_runtime/api/__init__.py` | `…/national_workflow_runtime/api/__init__.py` |
| `backend/app/national/workflow_runtime/api/routes.py` | `…/national_workflow_runtime/api/routes.py` |
| `backend/app/national/workflow_runtime/application/__init__.py` | `…/national_workflow_runtime/application/__init__.py` |
| `backend/app/national/workflow_runtime/application/interfaces.py` | `…/national_workflow_runtime/application/interfaces.py` |
| `backend/app/national/workflow_runtime/application/service.py` | `…/national_workflow_runtime/application/service.py` |
| `backend/app/national/workflow_runtime/domain/__init__.py` | `…/national_workflow_runtime/domain/__init__.py` |
| `backend/app/national/workflow_runtime/domain/entities.py` | `…/national_workflow_runtime/domain/entities.py` |
| `backend/app/national/workflow_runtime/domain/enums.py` | `…/national_workflow_runtime/domain/enums.py` |
| `backend/app/national/workflow_runtime/domain/events.py` | `…/national_workflow_runtime/domain/events.py` |
| `backend/app/national/workflow_runtime/domain/repository.py` | `…/national_workflow_runtime/domain/repository.py` |
| `backend/app/national/workflow_runtime/domain/saga_engine.py` | `…/national_workflow_runtime/domain/saga_engine.py` |
| `backend/app/national/workflow_runtime/domain/workflow_state_machine.py` | `…/national_workflow_runtime/domain/workflow_state_machine.py` |
| `backend/app/national/workflow_runtime/exceptions.py` | `…/national_workflow_runtime/exceptions.py` |
| `backend/app/national/workflow_runtime/infrastructure/__init__.py` | `…/national_workflow_runtime/infrastructure/__init__.py` |
| `backend/app/national/workflow_runtime/infrastructure/models.py` | `…/national_workflow_runtime/infrastructure/models.py` |
| `backend/app/national/workflow_runtime/infrastructure/repository.py` | `…/national_workflow_runtime/infrastructure/repository.py` |
| `backend/app/platform/workflow.py` | `archive/legacy/workflow_runtime/platform_workflow.py` |

**Disposition:** do **not** ship this staging decision silently — the archive move is part of CR-1
and must be reviewed with the workflow-runtime replacement (canonical `backend/app/workflows/`).

---

## 3. Modified tracked files (80)

Grouped by concern. Line counts are `git diff --numstat`.

### 3.1 Security remediation (S-01…S-13) — authorization, degraded mode, kill-switch

| File | +/− | Change |
|---|---:|---|
| `backend/app/control_plane/routes.py` | +125 / −31 | S-01/S-02: role-gated reads (`master_admin`/`ministry_admin`), `master_admin` writes, two-person deploy (distinct token-derived approver) |
| `backend/app/governance/routes/governance_routes.py` | +58 / −30 | S-04/S-05: shared operational read policy, `master_admin` writes; audit actor server-derived |
| `backend/app/pilot_platform/api/routes.py` | +51 / −17 | S-04: pilot-platform read/write policy |
| `backend/app/lifecycle_platform/api/routes.py` | +39 / −19 | S-04: lifecycle read/write policy |
| `backend/app/contracts/routes.py` | +20 / −10 | S-04: contracts export gated |
| `backend/app/certification/routes.py` | +9 / −5 | S-04: certification surfaces gated |
| `backend/app/identity/api/persons.py` | | S-03: registry reader/writer gates |
| `backend/app/identity/api/sessions.py` | | S-03: session reads/termination gated |
| `backend/app/identity/trust/routes.py` | | S-03: device register/trust/revoke gated |
| `backend/app/identity/api/router.py` | | S-03: router wiring |
| `backend/app/identity/adaptive_auth/routes.py` | | S-08: AI/adaptive-auth internals gated |
| `backend/app/identity/governance/routes.py` | | S-08: governance reads gated |
| `backend/app/identity/workflows/routes.py` | | S-08 + canonical router mount |
| `backend/app/national/document_platform/api/routes.py` | | S-08: national document surfaces gated |
| `backend/app/lims/routes.py` | | S-12: LIMS indicators authenticated |
| `backend/app/routes/ai.py`, `backend/app/routes/ai_telemetry.py` | | S-08/S-09: AI internals gated |
| `backend/app/routes/citizen_portal.py`, `backend/app/routes/demo.py` | | S-04/S-07: portal + demo surfaces |
| `backend/app/routes/verification.py` | +31 / −10 | **S-13**: `SELF_VERIFIABLE_ROLES = ("citizen",)`; no self-activation of professional roles |
| `backend/app/security/platform_access.py` (new, untracked) | | shared policy primitives used by S-04…S-12 |
| `backend/app/identity/api/access.py` (new, untracked) | | NIAM registry reader/writer gates (S-03) |
| `backend/app/security/auth.py`, `dependencies.py`, `rate_limit.py` | | degraded-mode veto plumbing (S-06) |
| `backend/app/security/redis_client.py` | +83 / −17 | S-06: `security_store()` fail-closed boundary |
| `backend/app/core/kill_switch.py` | +62 / −16 | unreadable shared state ⇒ **ACTIVE** in production/staging (fail-closed); `shared_state_readable` in `status()` |
| `backend/app/config.py` | +19 / −1 | HTTPS-derived `Secure` cookie flag, `ALLOW_DEGRADED_REDIS` |
| `backend/app/middleware.py` | | cookie helper + `Secure` derivation (S-07) |
| `backend/app/routes/login.py` | | cookie helper adoption |
| `backend/app/database.py` | +80 / −0 | session/engine boundary used by the security store and rehearsal runs |
| `frontend-v3/src/api/endpoints.ts` | | client alignment with gated endpoints |

### 3.2 S-13 / NIAM / audit

| File | +/− | Change |
|---|---:|---|
| `backend/app/identity/models/audit.py` | +37 / −0 | new audit actions for the gated surfaces |
| `backend/app/identity/base.py`, `backend/app/models/__init__.py` | | registry/export wiring |

### 3.3 Service extraction wiring (NR-006-dupe / §5.1 gap)

| File | +/− | Change |
|---|---:|---|
| `backend/app/routes/quality_control.py` | +53 / −263 | delegates to `quality_control_service` |
| `backend/app/routes/mobile.py` | +43 / −42 | delegates to `mobile_service` |
| `backend/app/routes/dashboard.py` | | delegates to `dashboard_service` |
| `backend/app/routes/stats.py` | | shadowing bug fix + service delegation |
| `backend/app/routes/metrics.py` | | delegates to `metrics_service` |
| `backend/app/services/order_service.py` | | shared order-path fix |
| `backend/app/domain/exceptions.py` | | `DomainError` mapping used by the extractions |

> Note: `admin`, `test_results`, `labs`, `samples` routes remain **unwired** (2 216 LOC of dead
> service twins) — that is criterion 9 and remains **NOT MET**.

### 3.4 Database migration repairs (NR-003 / NR-009 / NR-010)

| File | +/− | Change |
|---|---:|---|
| `backend/migrations/versions/20260815_0023_drug_substitution.py` | +66 / −1 | NR-003: catalog identity alignment (`Integer` → `String(26)` FK consistency) |
| `backend/migrations/versions/20260716_0003_pharmacy_platform.py` | +18 / −18 | NR-003: catalog PK declared `String(26)` |
| `backend/migrations/versions/20260716_0004_radiology_platform.py` | +21 / −3 | NR-010: circular FK + drop order fixed for `downgrade base` |
| `backend/migrations/versions/20260820_0004_surgical_safety_checklists.py` | +20 / −5 | NR-009: conditional FK to `hospital_operation_theaters` |
| `backend/migrations/versions/20260814_0002_organization_structure.py` | | downgrade-path repair |
| `backend/migrations/versions/20260324_0006_patient_family_guardian.py` | | documented no-op downgrade |
| `backend/migrations/versions/20260324_0009_audit_chain_hash_result_engine_version.py` | | idempotent index drop |
| `backend/migrations/versions/20260324_0010_production_indexes.py` | | idempotent index drop |

### 3.5 Dependency remediation (Phase 1 — criterion 11)

| File | +/− | Change |
|---|---:|---|
| `backend/requirements.txt` | | six packages raised to minimum fix version + security **floors** |
| `backend/requirements-lock.txt` | | lock regenerated (72 pins; `pillow==13.0.0`, `joserfc==1.7.6`, `certifi==2026.10.18`, `dnspython==2.9.2`, `pyasn1==0.6.5`, `urllib3==2.8.0`, `idna==3.20`) |
| `backend/tests/test_dependency_upgrade_compat.py` (new, untracked) | | 33 behaviour-only compat tests (no version assertions) |
| `SECURITY_REMEDIATION_REPORT.md` | +59 / −0 | addendum A1–A3 (remediation evidence, BLOCKED network disclosure) |

### 3.6 Ported-module integration (unification)

| File | +/− | Change |
|---|---:|---|
| `backend/app/platform/notifications.py` | +96 / −10 | Telegram enterprise notification port |
| `shared/notifications/__init__.py` | +31 / −2 | shared notification surface |
| `shared/circuit_breaker.py` | +52 / −13 | reliability primitives used by providers |
| `shared/qr/generator.py`, `shared/pyproject.toml` | | shared-core alignment |
| `backend/app/capabilities/search_service/*` | | canonical search provider port |
| `backend/app/capabilities/document_management/__init__.py` | | PDF adapter registration |
| `backend/app/document_intelligence/application/{service,wiring}.py`, `infrastructure/services.py` | | re-pointed to canonical search |
| `backend/app/national/document_platform/application/service.py` | | PDF export delegator |
| `backend/app/blood_bank/domain/state_machine.py` | | `verified -> in_progress` transition |
| `backend/app/factory.py` | | router registration for the ported modules |
| `backend/pyproject.toml` | | tooling targets |

### 3.7 Frontend / CI / tests

| File | +/− | Change |
|---|---:|---|
| `.github/workflows/frontend-pwa.yml` | | **F-01**: `VITE_API_BASE_URL` → `https://api.gula-platform.org/api` (gateway `/api/` route) |
| `frontend-v3/package.json`, `package-lock.json` | | test tooling |
| `frontend-v3/vite.config.ts` | | vitest configuration |
| `frontend-v3/src/components/navigation/MobileBottomNav.test.tsx` | | component test |
| `services/lab/Dockerfile` | | build alignment |
| `backend/tests/test_niam_v2.py` | | 3 stale `identity.workflows.models` imports |
| `backend/tests/test_comprehensive.py`, `test_stress.py`, `test_document_intelligence.py` | | stale mocks/imports |
| `docs/adr/README.md` | | ADR index |

---

## 4. Untracked files (84)

### 4.1 Governance deliverables (26 documents + evidence dir, of which 24 are untracked)

`GOVERNANCE/` — all new in this program except the two pre-existing files noted below:

`CODE_RECONCILIATION_INVENTORY.md`, `DATABASE_COMPATIBILITY_REPORT.md`,
`DEPENDENCY_VULNERABILITY_REPORT.md`, `EXECUTION_LEDGER.md`, `FINAL_DECISION.md`,
`FRONTEND_INTEGRATION_REPORT.md`, `LOCAL_FEATURES_PRESERVATION.md`,
`MIGRATION_RECONCILIATION_MATRIX.md`, `NATIONAL_INTEGRATION_ROADMAP.md`,
`NATIONAL_SERVICE_CONTRACTS.md`, `NATIONAL_SERVICE_INVENTORY.md`,
**`PHASE_C_DATABASE_REHEARSAL_REPORT.md`** (new), `PUBLIC_ENDPOINT_REGISTER.md`,
`REFERENCE_STATE_REPORT.md`, `REMEDIATION_STAGE_REPORT.md`, `REPOSITORY_UNIFICATION_REPORT.md`,
`RESUMPTION_STATUS.md`, `SECURITY_COVERAGE_MATRIX.md`, `SECURITY_REVIEW_REPORT.md`,
`UNIFICATION_BLOCKERS.md`, plus this manifest, `GIT_READINESS_REPORT.md`,
`FINAL_REMEDIATION_AND_RELEASE_REPORT.md`, `ADR_DECISION_REQUEST.md`, and `GOVERNANCE/evidence/`
(`index_target_missing.txt` 0 B, `migration_reconciliation_matrix.json` 27 858 B,
`migration_reconciliation_matrix.tsv` 23 077 B).

`GLOSI/` — registry + tools + 20 tests (structurally validated, **no project approved**).

### 4.2 New backend modules (ported, untested/unreviewed by a human)

`backend/app/communication/`, `backend/app/domain_platform/`,
`backend/app/identity/professional_registry/`, `backend/app/workflows/`,
`backend/app/models/communication_experience.py`,
`backend/app/notifications/telegram_enterprise.py`,
`backend/app/capabilities/search_service/{composition,exceptions,indexer,interfaces,search,semantic}.py`,
`backend/app/capabilities/document_management/pdf_generator.py`,
`backend/app/security/platform_access.py`, `backend/app/identity/api/access.py`,
`backend/app/services/{admin,dashboard,lab,metrics,mobile,quality_control,sample,stats,test_result}_service.py`,
`shared/communication/`, `shared/communication_providers/`,
`shared/notifications/telegram.py`, `scripts/domains/`, `scripts/domains.py`.

### 4.3 New migrations (6 — head chain)

`20261114_0001_unify_foundation.py`, `20261114_0002_unify_fk_indexes.py`,
`20261114_0003_unify_communication.py`, `20261114_0004_unify_professional_identity.py`,
`20261114_0005_unify_domain_platform.py`, `20261114_0006_unify_authorization_indexes.py`.

### 4.4 New tests (23 files/dirs)

Security regression (10): `test_control_plane_authorization`, `test_niam_registry_authorization`,
`test_national_governance_authorization`, `test_governance_audit_authorization`,
`test_governance_anonymous_access`, `test_security_store_policy`, `test_ai_platform_authorization`,
`test_lims_quality_authorization`, `test_professional_verification_authorization`,
`test_kill_switch_fail_closed`.
Unification/functional (13): `test_identity_workflows_canonical`, `test_domain_platform`,
`test_document_platform_pdf`, `test_communication_experience`, `test_dependency_upgrade_compat`,
`test_niam_professional_registry`, `test_stats_service`, `test_test_result_service`,
`tests/communication/`, `tests/communication_providers/`, `tests/notifications/test_telegram.py`,
`tests/notifications/test_telegram_enterprise.py`, `tests/unit/`.

### 4.5 Other

`docs/goc/`, `docs/adr/ADR-026-global-operations-center.md`.

### 4.6 Artifact that must NOT be committed

| Path | Why |
|---|---|
| `.gula-lite-permission-test.txt` | Test artefact written at repo root (0 business value). Recommended for `.gitignore` or deletion, not inclusion. |

---

## 5. What is deliberately **not** in the working tree

| Item | Status |
|---|---|
| Reduction of the 426-table ORM↔migration gap | **Not attempted** — blocked by NR-011 + ADR-A |
| `national_encounters` creation | **Not attempted** — ADR-A prerequisite (NR-011) |
| Normalisation of the `pharmacy_drug_catalog_id_seq` default | **Not attempted** — NR-012, needs reviewed migration |
| Wiring `admin`/`test_results`/`labs`/`samples` to their service twins | **Not attempted** — criterion 9, gated on contract mapping |
| Removal/registration of the unserved `backend/app/insurance/api/*` (84 endpoints) | **Not attempted** — ADR-I |
| MyPy 71 scoped errors | **Not attempted** — tracked debt |
| Any changes to `gula-platform` or `Platform-Core` | **Out of scope, untouched** |
| Any migration/`stamp`/`DROP` on `gula` or another operational DB | **Not performed** — Phase C used disposable clones only |

---

## 6. Integrity statements

1. **Zero commits, zero pushes, zero merges, zero PRs, zero deploys.** HEAD is unchanged at
   `2827c1ff`, identical to `origin/main` (`0 0`), and `integration/gula-unification-v1` does not
   exist on `origin` (0 matching remote heads).
2. **No history rewrite.** No rebase, no amend, no reset, no force operation was executed.
3. **The 20 staged renames** were present before this program and were left staged; the manifest
   records them rather than altering them.
4. **Pre-existing uncommitted changes were preserved**, not reverted, not discarded.
5. **Every Phase C database write occurred on a disposable clone** created with
   `CREATE DATABASE … TEMPLATE`; `gula` was never migrated, stamped or written.
6. **No secrets, credentials or PII appear in this manifest** or in the `GOVERNANCE/` reports. The
   local development PostgreSQL password that appeared in reproduction commands was **redacted to
   `<DEV_DB_PASSWORD>` across 8 occurrences in 7 documents** before finalisation. Phase C reported
   only row counts and MD5 hashes of synthetic NIAM seed data — no record content, no PII.
