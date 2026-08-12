# Technical Debt Register — GULA Platform

**Version:** 1.0.0
**Date:** 2026-07-08
**Classification:** Internal — Engineering

---

## Debt Scoring

| Score | Level | Description |
|-------|-------|-------------|
| 1-3 | Low | Cosmetic, non-functional impact |
| 4-6 | Medium | Functional impact, needs planning |
| 7-9 | High | Significant risk or maintenance burden |
| 10 | Critical | Must resolve before proceeding |

Scoring: `Severity (1-5) × Frequency (1-5)` where 1 = Very Low, 5 = Very High.

## Debt Items

### D-001: Test Fixture Isolation Failures

| Field | Value |
|-------|-------|
| **Description** | 268 test errors from fixture isolation issues in conftest.py modules |
| **Location** | `backend/tests/test_tiers_privilege.py`, `test_tenant_isolation_matrix.py`, `test_chaos_survival.py` |
| **Severity** | 4 |
| **Frequency** | 5 |
| **Score** | 20 (Critical) |
| **Impact** | CI reliability degraded, developer trust in test suite |
| **Fix** | Refactor shared fixtures to use `request.getfixturevalue()` pattern |
| **Effort** | 2-3 days |
| **Priority** | Critical |

### D-002: mypy Type Errors

| Field | Value |
|-------|-------|
| **Description** | 1413 mypy strict errors across the codebase |
| **Location** | Entire `backend/app/` |
| **Severity** | 3 |
| **Frequency** | 5 |
| **Score** | 15 (Critical) |
| **Impact** | No static type checking enforcement, potential runtime type errors |
| **Fix** | Phased resolution: start with security/ and models/, then routes/services |
| **Effort** | 10-15 days (phased) |
| **Priority** | High |

### D-003: Route and Service Coverage Gap

| Field | Value |
|-------|-------|
| **Description** | Routes at ~35% coverage, services at ~30% |
| **Location** | `backend/app/routes/`, `backend/app/services/` |
| **Severity** | 4 |
| **Frequency** | 4 |
| **Score** | 16 (Critical) |
| **Impact** | Regression risk in critical paths (orders, results, samples) |
| **Fix** | Write integration tests for uncovered route handlers |
| **Effort** | 5-7 days |
| **Priority** | High |

### D-004: Two Frontend Codebases

| Field | Value |
|-------|-------|
| **Description** | Frontend-v2 (React/Firebase) and legacy frontend (static PWA) maintained in parallel |
| **Location** | `frontend-v2/`, `frontend/` |
| **Severity** | 3 |
| **Frequency** | 3 |
| **Score** | 9 (High) |
| **Impact** | Split developer attention, duplicated effort, potential inconsistency |
| **Fix** | Officially deprecate legacy frontend or consolidate |
| **Effort** | 3-5 days |
| **Priority** | Medium |

### D-005: Pydantic V2 Deprecation Warnings

| Field | Value |
|-------|-------|
| **Description** | `class Config` pattern deprecated in Pydantic V2, should use `ConfigDict` |
| **Location** | Various model files |
| **Severity** | 2 |
| **Frequency** | 4 |
| **Score** | 8 (High) |
| **Impact** | Non-functional warnings, future compatibility |
| **Fix** | Migrate `class Config` to `model_config = ConfigDict(...)` |
| **Effort** | 1-2 days |
| **Priority** | Medium |

### D-006: passlib/bcrypt Deprecation Warning

| Field | Value |
|-------|-------|
| **Description** | passlib 1.7.4 with bcrypt 4.1.3 produces deprecation warning |
| **Location** | `backend/app/security/auth.py` |
| **Severity** | 1 |
| **Frequency** | 5 |
| **Score** | 5 (Medium) |
| **Impact** | Warning noise, potential future incompatibility |
| **Fix** | Pin passlib version or migrate to direct bcrypt usage |
| **Effort** | 0.5 days |
| **Priority** | Low |

### D-007: Starlette Deprecation Warning

| Field | Value |
|-------|-------|
| **Description** | `HTTP_422_UNPROCESSABLE_ENTITY` deprecated, use `HTTP_422_UNPROCESSABLE_CONTENT` |
| **Location** | `backend/app/integration/presentation/routers/connectors.py` |
| **Severity** | 1 |
| **Frequency** | 3 |
| **Score** | 3 (Low) |
| **Impact** | Warning in test output |
| **Fix** | Update status code constant reference |
| **Effort** | 0.1 days |
| **Priority** | Low |

### D-008: Dev-mode 0.0.0.0 Binding

| Field | Value |
|-------|-------|
| **Description** | HL7 MLLP listener binds to `0.0.0.0` in dev configuration |
| **Location** | `backend/app/integration/infrastructure/config/settings.py:84` |
| **Severity** | 3 |
| **Frequency** | 1 |
| **Score** | 3 (Low) |
| **Impact** | Security scan finding (Medium bandit), dev-only |
| **Fix** | Bind to `127.0.0.1` in dev config or add security note |
| **Effort** | 0.1 days |
| **Priority** | Low |

### D-009: Microservices Tree Not Deployed

| Field | Value |
|-------|-------|
| **Description** | services/ directory contains 7 microservice skeletons that are not production targets |
| **Location** | `services/lab`, `order`, `patient`, `result`, `sample`, `notification`, `ai` |
| **Severity** | 2 |
| **Frequency** | 2 |
| **Score** | 4 (Low) |
| **Impact** | Codebase clutter, confusion about deployment targets |
| **Fix** | Document deprecation or remove skeleton code |
| **Effort** | 1 day |
| **Priority** | Low |

### D-010: SNDHS-lite Dual-Read Complexity

| Field | Value |
|-------|-------|
| **Description** | national_id and sndhs_health_id may be None for pre-backfill rows |
| **Location** | Patients model, SNDHS-related code |
| **Severity** | 2 |
| **Frequency** | 2 |
| **Score** | 4 (Low) |
| **Impact** | Additional None-check boilerplate |
| **Fix** | Enforce after backfill is complete across all tenants |
| **Effort** | N/A — intentional design |
| **Priority** | Low |

## Debt Summary

| Category | Count | Critical | High | Medium | Low |
|----------|-------|----------|------|--------|-----|
| Testing | 2 | 2 | 0 | 0 | 0 |
| Type Safety | 1 | 1 | 0 | 0 | 0 |
| Coverage | 1 | 1 | 0 | 0 | 0 |
| Frontend | 1 | 0 | 1 | 0 | 0 |
| Dependencies | 2 | 0 | 1 | 1 | 0 |
| Configuration | 1 | 0 | 0 | 0 | 1 |
| Architecture | 1 | 0 | 0 | 0 | 1 |
| Compliance | 1 | 0 | 0 | 0 | 1 |

## Paydown Plan

### Sprint 1: Critical Items
- D-001: Fix fixture isolation (2-3 days)
- D-003: Write route coverage tests (5-7 days)

### Sprint 2: High Items
- D-002: mypy — security/ and models/ modules (3-5 days)
- D-005: Pydantic V2 migration (1-2 days)

### Sprint 3: Medium Items
- D-004: Frontend deprecation decision (3-5 days)
- D-006: passlib/bcrypt cleanup (0.5 days)

### Backlog
- D-007: Starlette constant update (0.1 days)
- D-008: 0.0.0.0 binding fix (0.1 days)
- D-009: Microservices documentation (1 day)
- D-010: SNDHS backfill enforcement (N/A)

## References

- `docs/engineering/RISK-REGISTER.md` — Risk register
- `docs/engineering/QUALITY-GATES.md` — Quality gates
- `QUALITY.md` — Quality gate matrix (project root)
- `CLAUDE.md` — Engineering Constitution
