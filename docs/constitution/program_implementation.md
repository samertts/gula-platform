# GULA Platform — PROGRAM-IMPLEMENTATION-001
## Verified Gap Closure — Implementation Plan

Generated: 2026-07-22
Source: Enterprise Runtime Certification + Behavioral Verification Report

---

## 1. Verified Work Item Registry

### WI-001: Startup Guard Async Race Condition
| Field | Value |
|-------|-------|
| **Severity** | **CRITICAL** |
| **Evidence** | `/health/ready` returns 503. `system_ready` remains `False` indefinitely in TestClient. Runtime Certification Report #3, #9. |
| **Root Cause** | `run_startup_guard()` in `core/startup_guard.py:704` runs as a background `asyncio.create_task()`. The `ReadinessMiddleware` checks `system_ready` synchronously on every request. If the guard task is delayed (or fails silently after a previous failure), `system_ready` never transitions to `True`, blocking ALL non-health traffic. Production relies on Docker healthcheck `--start-period=60s` to mask the issue. |
| **Impact** | All API routes return 503 until startup guard completes. No production traffic possible without the 60-second delay mask. On guard failure, the system is permanently blind to non-health requests. |
| **Proposed Solution** | (a) Make `system_ready` awaitable — middleware polls with timeout, or (b) move guard to synchronous at end of lifespan start, or (c) add a fallback: if guard hasn't completed after 30s, set `system_ready` to partial-readiness. |
| **Files to Modify** | `app/core/startup_guard.py`, `app/factory.py` (lifespan handler), `app/main.py` (middleware registration: ReadinessMiddleware) |
| **Risk Assessment** | HIGH — changes to startup sequencing can cause deadlocks or prevent app from starting |
| **Rollback Strategy** | Revert `startup_guard.py` and `factory.py` changes; original Docker healthcheck `--start-period=60s` covers the issue |
| **Tests Required** | Startup sequence integration test: verify `system_ready=True` within 5s; readiness probe returns 200 after guard completes |

### WI-002: Duplicate OpenAPI Operation IDs
| Field | Value |
|-------|-------|
| **Severity** | **MAJOR** |
| **Evidence** | 9 warnings at app startup: duplicate operation IDs in `routes/password_reset.py` and `integration/connectors/routes.py` (8 routes). Runtime Certification Report #2. |
| **Root Cause** | (a) `password_reset.py` has two different functions with `operation_id="change_password"`. (b) `integration/connectors/routes.py` is imported/registered multiple times (once per connector) and the same router instance produces duplicate operation IDs. |
| **Impact** | OpenAPI schema has ambiguous operation IDs. Auto-generated clients may fail. API documentation has duplicate entries. |
| **Proposed Solution** | (a) Give each password_reset endpoint a unique `operation_id`. (b) In `integration/connectors/routes.py`, use unique `operation_id` per route or register the router once and pass connector name via path parameter. |
| **Files to Modify** | `app/routes/password_reset.py`, `app/integration/connectors/routes.py`, `app/factory.py` (connector registration) |
| **Risk Assessment** | LOW — operation_id is cosmetic for OpenAPI spec; changing it doesn't affect runtime behavior |
| **Rollback Strategy** | Revert the specific operation_id changes |
| **Tests Required** | OpenAPI schema generation test: verify no duplicate operation_id warning; count unique operation_id values matches path count |

### WI-003: ABAC Not Wired Into Route Decorator Path
| Field | Value |
|-------|-------|
| **Severity** | **MAJOR** |
| **Evidence** | `security/abac.py` provides `ABACEngine.evaluate()` with attribute-based rules. `security/dependencies.py:require_permission()` delegates to RBAC only. ABAC is only accessible via POST `/authz/check`. Behavioral Verification Report §6.5. |
| **Root Cause** | The per-route `require_permission("resource:action")` decorator only checks RBAC permissions. ABAC evaluation requires an explicit POST to `/authz/check` endpoint, which routes never call automatically. If fine-grained ABAC is needed ("deny if patient is VIP", "deny if location is restricted"), each route must manually call the ABAC endpoint. |
| **Impact** | Attribute-based policies (location-based, patient-based, time-based) cannot be enforced at the route decorator level. ABAC engine exists but is effectively unused for per-route enforcement. |
| **Proposed Solution** | Add optional ABAC evaluation inside `require_permission()`: after RBAC passes, call `ABACEngine.evaluate()` with request context. Add `require_abac()` dependency that runs parallel to `require_permission()`. |
| **Files to Modify** | `app/security/dependencies.py`, `app/security/abac.py`, `app/security/rbac.py` |
| **Risk Assessment** | MEDIUM — adding ABAC evaluation to the decorator path adds latency to every request. Must be optional and cached. |
| **Rollback Strategy** | Revert changes to `dependencies.py`; ABAC remains accessible via POST `/authz/check` |
| **Tests Required** | ABAC integration test: create policy, call endpoint with `require_abac()`, verify enforcement; verify RBAC-only paths unchanged |

### WI-004: Migration Chain Integrity — Forward FK References
| Field | Value |
|-------|-------|
| **Severity** | **HIGH** |
| **Evidence** | `20260716_0003_pharmacy_platform.py`: `pharmacy_drug_batches` FK to `pharmacy_drug_suppliers` before the table exists. `20260716_0004_radiology_platform.py`: 4 forward FK references (appointments→modality_devices, exams→modality_devices, reports→templates, reports→critical_findings). Runtime Report #11. |
| **Root Cause** | Alembic autogenerate produced migrations with `create_table` in dependency order defined by the model file, not by FK dependency order. Manual review and reordering required. |
| **Impact** | Fresh database deployment fails. CI migration-gate fails. Reproducible builds impossible without manual fixes. |
| **Proposed Solution** | Fixes already applied as part of Runtime Certification. Formalize: add CI rule that runs `alembic upgrade head` on a fresh database and verifies zero errors. |
| **Files to Modify** | None (fixes already applied). Add CI validation: `.github/workflows/ci.yml` — add post-migration FK integrity check. |
| **Risk Assessment** | HIGH (of regression) — CI migration-gate already exists but doesn't catch FK ordering. Adding FK check is LOW risk. |
| **Rollback Strategy** | N/A (fixes already applied to migration files) |
| **Tests Required** | `alembic upgrade head` on clean database; `SELECT COUNT(*) FROM information_schema.table_constraints WHERE constraint_type='FOREIGN KEY'` on every migrated table |

### WI-005: Migration Chain Integrity — Python `true`/`false` literals
| Field | Value |
|-------|-------|
| **Severity** | **HIGH** |
| **Evidence** | 8 migration files (`20260716_0005` through `20260716_0012`) use `default=true` and `default=false` instead of `default=True` and `default=False`. Runtime Report #11. |
| **Root Cause** | Migration files generated with `sa.Boolean(), default=true` where `true`/`false` are not Python keywords. `true`/`false` would cause `NameError` at runtime. |
| **Impact** | `alembic upgrade head` fails with `NameError: name 'true' is not defined`. Blocking fresh deployments. |
| **Proposed Solution** | Fix already applied (batch sed replace). Add linter rule: `ruff --select=E0602` catches undefined names like `true`/`false`. |
| **Files to Modify** | None (fixes already applied). Add linter config: `backend/pyproject.toml` — ensure `E0602` (undefined name) is not ignored. |
| **Risk Assessment** | LOW — lint rule addition is non-invasive |
| **Rollback Strategy** | N/A (fixes already applied) |
| **Tests Required** | `ruff --select=E0602 migrations/`; verify zero NameError cases |

### WI-006: Migration Chain Integrity — `metadata` Column Reserved Name
| Field | Value |
|-------|-------|
| **Severity** | **HIGH** |
| **Evidence** | 59+ models across `models/`, `insurance/domain/`, `radiology/`, `national/` use `metadata = Column(...)` which is a reserved attribute name in SQLAlchemy Declarative API. Runtime Certification found and fixed 13 model files. |
| **Root Cause** | SQLAlchemy 2.0+ reserves `metadata` as a class-level attribute on declarative models. All models using `metadata = Column(...)` fail on import. |
| **Impact** | App fails to import on SQLAlchemy 2.0+. All routes return 503. Fresh deployments impossible. |
| **Proposed Solution** | Fix already applied to 13 model files. Remaining `metadata = Column(...)` in newer migration files (not in model files) should be handled at migration time only. |
| **Files to Modify** | None (model fixes already applied). Migration files with `sa.Column("metadata", ...)` are safe because they use raw column names, not Python attributes. |
| **Risk Assessment** | LOW — fixes already applied and verified |
| **Rollback Strategy** | N/A (fixes already applied) |
| **Tests Required** | `python -c "from app.models import *"` verifies all models load without SQLAlchemy reserved-name errors |

### WI-007: 8-Service DORMANT Clinical Engine Cluster
| Field | Value |
|-------|-------|
| **Severity** | **MAJOR** |
| **Evidence** | `services/clinical_engine.py`, `clinical_intelligence.py`, `ali_reza_engine.py`, `samir_engine.py`, `epidemiology.py`, `clinical_state.py`, and related test mock/diagnostics — NONE imported by any registered route. Behavioral Verification §3.1. |
| **Root Cause** | These services were written for a clinical decision-support feature that was either never completed or was replaced by the AI Fabric (42 endpoints, active). The engine cluster exists as dead weight — approximately 2,900+ lines of unmaintained code. |
| **Impact** | Codebase bloat (2,900+ lines). Maintenance burden. Potential confusion for developers. No runtime impact (not reachable). |
| **Proposed Solution** | Option A: Remove entirely (cleanest). Option B: Deprecate with `DeprecationWarning` and remove after 2 releases. Option C: Mark as DORMANT in CODEOWNERS and skip in CI. |
| **Files to Modify** | `backend/app/services/clinical_engine.py`, `clinical_intelligence.py`, `ali_reza_engine.py`, `samir_engine.py`, `epidemiology.py`, `clinical_state.py` + test files |
| **Risk Assessment** | LOW (removal risk) / MEDIUM (if any external code transitively depends on these) |
| **Rollback Strategy** | Git revert of file deletions |
| **Tests Required** | Verify zero importers remain after removal; verify no test imports break |

### WI-008: 1 DEAD CODE Service — `risk_based_auth_service.py`
| Field | Value |
|-------|-------|
| **Severity** | **MINOR** |
| **Evidence** | Zero importers anywhere in the codebase. Behavioral Verification §3.4. |
| **Root Cause** | Unused service that was never integrated into the auth pipeline. |
| **Impact** | Dead code, test bloat. No runtime impact. |
| **Proposed Solution** | Remove file. |
| **Files to Modify** | `backend/app/services/risk_based_auth_service.py` |
| **Risk Assessment** | LOW |
| **Rollback Strategy** | Git revert |
| **Tests Required** | Verify zero imports to this module |

### WI-009: 8 Active Services with Zero Test Coverage
| Field | Value |
|-------|-------|
| **Severity** | **HIGH** |
| **Evidence** | 8 services (order_service, patient_service, ehr_service, clinical_service, hospital_service, care_continuum_service, data_platform_service, authorization_service) are actively used by registered routes but have ZERO direct test coverage. Behavioral Verification §6.3. |
| **Root Cause** | Test gap introduced during rapid feature development. These services were added without corresponding unit/integration tests. |
| **Impact** | Regression risk for 8 production services. `authorization_service` alone has 11 classes and 28 endpoints with zero test coverage. |
| **Proposed Solution** | Add pytest test files for each service. Priority: `authorization_service.py` (11 classes, 28 endpoints, security-critical). |
| **Files to Modify** | Create: `backend/tests/services/test_authorization_service.py`, `test_order_service.py`, `test_patient_service.py`, `test_ehr_service.py`, `test_clinical_service.py`, `test_hospital_service.py`, `test_care_continuum_service.py`, `test_data_platform_service.py` |
| **Risk Assessment** | MEDIUM — large test surface; tests may reveal latent bugs |
| **Rollback Strategy** | Tests only; no production code changed. Revert test file additions. |
| **Tests Required** | Each new test file must achieve >70% line coverage of its target service |

### WI-010: API Standards Non-Compliance
| Field | Value |
|-------|-------|
| **Severity** | **MAJOR** |
| **Evidence** | No `/api/v1/` prefix on any route. No standard response envelope (e.g., `{data, error, meta}`). No deprecation headers. Behavioral Verification §6.6 grades API Standards as D. |
| **Root Cause** | Routes were registered directly under `/` without version prefix. No API versioning strategy was enforced during development. |
| **Impact** | Breaking changes cannot be communicated via versioned URLs. Clients must update on every endpoint change. No deprecation notice mechanism. |
| **Proposed Solution** | Phase 1: Add `APIRouter` with `/api/v1` prefix to all new routes. Phase 2: Add `X-API-Deprecated` and `Sunset` headers to legacy routes. Phase 3: Add standard response envelope middleware. |
| **Files to Modify** | `app/factory.py`, all route files (add `/api/v1` prefix), `app/middleware.py` (response envelope middleware) |
| **Risk Assessment** | HIGH — changing route prefixes breaks all existing clients. Must be done alongside backward-compatible aliases. |
| **Rollback Strategy** | Keep old routes as `_legacy` aliases; remove in next major version |
| **Tests Required** | Test both `/api/v1/...` and legacy `/...` routes return identical responses |

### WI-011: Patient Data Encryption at Rest — Not Applied
| Field | Value |
|-------|-------|
| **Severity** | **HIGH** |
| **Evidence** | Behavioral Verification §6.6: "encryption.py not used for patient data at rest." `patients.national_id` should be encrypted per security invariants. |
| **Root Cause** | `security/encryption.py` exists and provides encrypt/decrypt functions, but no model field uses them. The `national_id` field is a plaintext `String` column. |
| **Impact** | Patient national ID stored in plaintext in database. Violation of security invariant #8 in CLAUDE.md. |
| **Proposed Solution** | Add `@validates('national_id')` on Patient model that encrypts on write and decrypts on read. Add migration to encrypt existing plaintext national_ids. |
| **Files to Modify** | `app/models/patient.py`, `app/services/patient_service.py`, `app/security/encryption.py` (verify API compatibility) |
| **Risk Assessment** | HIGH — encrypting existing data requires a migration that reads every patient row, encrypts national_id, and writes back. Must be done during maintenance window. |
| **Rollback Strategy** | Migration script must include a rollback step that decrypts all values back to plaintext |
| **Tests Required** | Encryption round-trip test: create patient with national_id, read from DB (verify ciphertext), read via model (verify plaintext), decrypt migration rollback |

### WI-012: `system_ready` Probes Not Synchronized
| Field | Value |
|-------|-------|
| **Severity** | **MINOR** |
| **Evidence** | `/health/ready` and `/health/status` both check `system_ready` but `/health/ready` returns 503 while `/health/status` returns 200 with `ready: false`. Inconsistent behavior. |
| **Root Cause** | Different design philosophies: `/health/ready` is a Docker healthcheck probe (strict), `/health/status` is a diagnostic endpoint (informational). |
| **Impact** | Operator confusion: health endpoint says "ready: false" but returns 200. |
| **Proposed Solution** | Make `/health/status` return 503 when `system_ready` is false, matching `/health/ready`. Or clearly document the distinction. |
| **Files to Modify** | `app/main.py` — `/health/status` response status code |
| **Risk Assessment** | LOW — non-functional change; monitoring dashboards may need update |
| **Rollback Strategy** | Revert status code change |
| **Tests Required** | Test that `/health/status` returns 503 when `system_ready=False` |

### WI-013: TrackedEntity Relationship Back-Reference Mismatch
| Field | Value |
|-------|-------|
| **Severity** | **MAJOR** |
| **Evidence** | Behavioral Verification §6.2: `lims/models.py` defines `TrackedEntity` with a `parent` relationship using `back_populates="children"`, but `children` is defined via `backref` instead of `back_populates`. SQLAlchemy ORM mismatch. |
| **Root Cause** | One side of the bidirectional relationship uses `back_populates` while the other uses `backref`. SQLAlchemy ORM issues a warning and the relationship may not sync correctly in memory. |
| **Impact** | ORM relationship desynchronization: `parent.children` may not reflect in-memory changes until flush. Subtle bugs in sample/entity tracking workflows. |
| **Proposed Solution** | Change `backref` to `back_populates` on the `children` side, matching the `parent` side. |
| **Files to Modify** | `app/lims/models.py` |
| **Risk Assessment** | LOW — ORM-level fix; DB schema unchanged |
| **Rollback Strategy** | Revert the relationship definition change |
| **Tests Required** | Unit test: create TrackedEntity with parent, verify `parent.children` includes child before flush |

### WI-014: Migration Chain — No Round-Trip in CI
| Field | Value |
|-------|-------|
| **Severity** | **MAJOR** |
| **Evidence** | Behavioral Verification §6.6: migration grade D — "no migration round-trip in CI." CI runs `alembic upgrade head` only, never `alembic downgrade -1` then `upgrade head`. |
| **Root Cause** | CI migration-gate (`ci.yml`) only verifies forward migration. Round-trip (downgrade+upgrade) is not automated. |
| **Impact** | Non-idempotent migrations can be merged. If a migration can't be downgraded, rollback is impossible. |
| **Proposed Solution** | Add `alembic downgrade -1 && alembic upgrade head` step to CI migration-gate job. |
| **Files to Modify** | `.github/workflows/ci.yml` — migration-check job |
| **Risk Assessment** | LOW — CI-only change; no production impact |
| **Rollback Strategy** | Revert CI config change |
| **Tests Required** | CI pipeline passes with round-trip step |

### WI-015: pgvector Extension Not Available on All Deployments
| Field | Value |
|-------|-------|
| **Severity** | **MAJOR** |
| **Evidence** | Runtime Certification Report #11: `20260719_0001_ai_platform_tables.py` fails with `InFailedSqlTransaction` when `vector` extension is unavailable. Fixed via autocommit workaround. |
| **Root Cause** | The migration's `_enable_pgvector()` function runs `CREATE EXTENSION IF NOT EXISTS vector` inside the transactional Alembic migration. If the extension binary (`vector.control`) is not installed on the PostgreSQL server, the transaction aborts and ALL subsequent migration statements fail. |
| **Impact** | Deployments without pgvector cannot run `alembic upgrade head`. Currently mitigated by try/except in autocommit mode, but the workaround is fragile. |
| **Proposed Solution** | (a) Add pgvector to Docker deployment docs and postgres Dockerfile. (b) Make the migration non-transactional for the CREATE EXTENSION step. (c) Document pgvector as a required extension for AI features. |
| **Files to Modify** | `docs/sndhs/phase1/RUNBOOK.md` or equivalent deployment guide, `docker-compose.yml` (postgres init script) |
| **Risk Assessment** | MEDIUM — documentation + init script changes only |
| **Rollback Strategy** | N/A (no production code change) |
| **Tests Required** | Migration test on database WITHOUT pgvector: verify graceful skip; migration test WITH pgvector: verify vector extension exists |

---

## 2. Batch Execution Plan

### Batch 1: Critical Runtime Failures
| Items | WI-001 (Startup Guard) |
|-------|----------------------|
| **Effort** | 2 days |
| **Risk** | HIGH |
| **Affected Modules** | `core/startup_guard.py`, `factory.py`, `main.py` |
| **Regression Probability** | MEDIUM (20%) |

### Batch 2: Migration Integrity
| Items | WI-004, WI-005, WI-006, WI-014, WI-015 |
|-------|----------------------------------------|
| **Effort** | 1 day |
| **Risk** | LOW |
| **Affected Modules** | `.github/workflows/ci.yml`, `migrations/versions/` (CI validation only) |
| **Regression Probability** | LOW (5%) |

### Batch 3: Security Issues
| Items | WI-003 (ABAC), WI-011 (Encryption) |
|-------|-------------------------------------|
| **Effort** | 3 days |
| **Risk** | HIGH |
| **Affected Modules** | `security/dependencies.py`, `security/abac.py`, `models/patient.py`, `security/encryption.py` |
| **Regression Probability** | MEDIUM (25%) |

### Batch 4: Authorization
| Items | WI-003 (ABAC, overlaps with Batch 3) |
|-------|--------------------------------------|
| **Effort** | 1 day |
| **Risk** | MEDIUM |
| **Affected Modules** | `security/dependencies.py`, `security/abac.py` |
| **Regression Probability** | MEDIUM (15%) |

### Batch 5: Performance & API Standards
| Items | WI-002 (Duplicate OpIDs), WI-010 (API Standards), WI-012 (Probes) |
|-------|-------------------------------------------------------------------|
| **Effort** | 3 days |
| **Risk** | LOW |
| **Affected Modules** | `routes/password_reset.py`, `integration/connectors/routes.py`, `factory.py`, `middleware.py`, `main.py` |
| **Regression Probability** | LOW (10%) |

### Batch 6: Observability
| Items | WI-012 (Probes, overlaps with Batch 5) |
|-------|----------------------------------------|
| **Effort** | 0.5 days |
| **Risk** | LOW |
| **Affected Modules** | `main.py` |
| **Regression Probability** | LOW (5%) |

### Batch 7: Architecture Cleanup
| Items | WI-007 (DORMANT cluster), WI-008 (DEAD CODE), WI-009 (Zero test coverage), WI-013 (back_populates) |
|-------|-----------------------------------------------------------------------------------------------------|
| **Effort** | 5 days |
| **Risk** | MEDIUM |
| **Affected Modules** | 6 service files (DORMANT), 1 service file (DEAD), 8 new test files, `lims/models.py` |
| **Regression Probability** | LOW (10%) for removals; MEDIUM (30%) for new tests may reveal latent bugs |

### Execution Order

```
Batch 1 (Critical)       → Day 1-2     → MUST pass full certification
Batch 2 (Migration)      → Day 3       → MUST pass full certification
Batch 3 (Security)       → Day 4-6     → MUST pass full certification
Batch 4 (Authorization)  → Day 7       → MUST pass full certification
Batch 5 (Performance)    → Day 8-10    → MUST pass full certification
Batch 6 (Observability)  → Day 11      → MUST pass full certification
Batch 7 (Cleanup)        → Day 12-16   → MUST pass full certification
```

---

## 3. Enterprise Change Log

| Change ID | Work Item | Type | Date | Author | Risk | Rollback |
|-----------|-----------|------|------|--------|------|----------|
| C001 | WI-001 | Bug fix | 2026-07-22 | Runtime Cert Batch 1 | LOW | Revert startup_guard.py + config.py + conftest.py + test fixtures |
| C002 | WI-002 | Bug fix | TBD | TBD | LOW | Revert operation_id changes |
| C003 | WI-003 | Feature | TBD | TBD | MEDIUM | Revert dependencies.py |
| C004 | WI-004 | CI | TBD | TBD | LOW | Revert CI config |
| C005 | WI-005 | CI | TBD | TBD | LOW | Revert linter config |
| C006 | WI-006 | Bug fix | Already applied | Runtime Cert | LOW | N/A (already in tree) |
| C007 | WI-007 | Cleanup | TBD | TBD | LOW | Git revert file deletions |
| C008 | WI-008 | Cleanup | TBD | TBD | LOW | Git revert file deletion |
| C009 | WI-009 | Testing | TBD | TBD | MEDIUM | Revert test file additions |
| C010 | WI-010 | Enhancement | TBD | TBD | HIGH | Keep legacy route aliases |
| C011 | WI-011 | Security fix | TBD | TBD | HIGH | Migration rollback script |
| C012 | WI-012 | Bug fix | TBD | TBD | LOW | Revert status code change |
| C013 | WI-013 | Bug fix | TBD | TBD | LOW | Revert relationship change |
| C014 | WI-014 | CI | TBD | TBD | LOW | Revert CI config |
| C015 | WI-015 | Documentation | TBD | TBD | MEDIUM | Revert deployment guide |

---

## 4. Risk Matrix

| Risk | Probability | Impact | Work Items | Mitigation |
|------|-------------|--------|------------|------------|
| Startup deadlock after guard changes | 20% | CRITICAL | WI-001 | Test on staging; health endpoints always accessible; container auto-restart |
| Encryption migration data loss | 10% | CRITICAL | WI-011 | Test on DB copy; rollback script ready; backup before migration |
| API versioning breaks clients | 40% | MAJOR | WI-010 | Legacy URL aliases; 6-month deprecation window; client notification |
| ABAC evaluation latency | 30% | MINOR | WI-003 | Cache ABAC results per-request; benchmark before/after |
| DORMANT code removal breaks external tooling | 5% | MINOR | WI-007, WI-008 | Verify zero CI/script references |
| Migration round-trip fails on CI | 50% | MINOR | WI-014 | Fix immediately; block merge until pass |
| Linter false positives on migration files | 10% | MINOR | WI-005 | Use `# noqa: E0602` on legitimate uses |

---

## 5. Regression Matrix

| Component | WI-001 | WI-003 | WI-010 | WI-011 | WI-013 |
|-----------|--------|--------|--------|--------|--------|
| Health endpoints | HIGH | NONE | NONE | NONE | NONE |
| Auth/JWT | NONE | MEDIUM | NONE | NONE | NONE |
| Patient CRUD | NONE | NONE | MEDIUM | HIGH | NONE |
| LIMS orders/samples | NONE | NONE | MEDIUM | NONE | MEDIUM |
| API clients | NONE | NONE | HIGH | NONE | NONE |
| Audit log | NONE | NONE | MEDIUM | NONE | NONE |
| National platform | NONE | NONE | MEDIUM | NONE | NONE |

Cells: NONE = zero regression risk, LOW = <5%, MEDIUM = 5-25%, HIGH = >25%

---

## 6. Expected Runtime Improvements

| Metric | Current | After Batch 1 | After Batch 3 | After Batch 5 | After Batch 7 |
|--------|---------|---------------|---------------|---------------|---------------|
| `system_ready` timeout | Indefinite | **120s** | 120s | 120s | 120s |
| Manual `system_ready=True` workaround | 5 locations | **0 locations** | 0 | 0 | 0 |
| Production startup timeout | None | **120s configurable** | 120s | 120s | 120s |
| `X-Response-Time` (health) | 36ms | 36ms | 36ms | 36ms | 36ms |
| `X-Response-Time` (auth check) | N/A | N/A | **+2ms** (ABAC eval) | +2ms | +2ms |
| OpenAPI schema warnings | 9 | 9 | 9 | **0** | 0 |
| Test coverage (services/) | 0% | 0% | 0% | 0% | **>70%** |
| Dead code (lines) | ~3,000 | ~3,000 | ~3,000 | ~3,000 | **0** |
| DORMANT services | 6 | 6 | 6 | 6 | **0** |
| API Standards grade | D | D | D | **B** | B |
| Security grade | A | A | **A+** | A+ | A+ |
| Migration round-trips | Never | Never | Never | Never | **CI-enforced** |
| Encryption at rest | None | None | **National ID** | National ID | National ID |

---

## Approval

**Status**: AWAITING APPROVAL

This implementation plan is ready for review. Upon approval, implementation will proceed in batch order. Each batch must pass the full Runtime Certification suite before the next batch begins.
