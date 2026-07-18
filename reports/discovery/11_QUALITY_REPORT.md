# GULA Platform — Quality Report
**Date:** 2026-07-17

---

## 1. Test Inventory

### Backend Tests (`backend/tests/`)

| Category | Count | Files |
|----------|-------|-------|
| Unit/Integration (top-level) | ~30 | test_comprehensive.py, test_security.py, test_stress.py, etc. |
| Kernel | 35 | runtime, bootloader, lifecycle, services, event bus, outbox, etc. |
| Kernel Hardening | 7 | chaos, stress, memory, performance, security, recovery, observability |
| Integration | ~5 | booking/, identity/, integration/, notifications/, skills/ |
| **Total** | **~77+ test files** | |

### Root-Level Tests (`tests/`)
| Type | Files |
|------|-------|
| Load (k6) | k6-scenarios.js, gula-load-test.js |
| Load (Locust) | locustfile.py |
| Scenario | scenario_test.py |
| Integrity | integrity_test.py |
| Chaos | chaos-scenarios.yaml, chaos-mesh-experiment.yaml |
| Stress | stress-config.yml |

---

## 2. Test Coverage

| Module | Coverage | Target | Status |
|--------|----------|--------|--------|
| Auth | 96% | 90% | ✅ |
| Models | 95% | 90% | ✅ |
| Routes | 35% | 80% | ❌ |
| Services | 30% | 80% | ❌ |
| Edge/Interop | 0% | 70% | ❌ |
| **Overall** | **54%** | **70%** | ❌ |
| Statements covered | 9,328 / 17,273 | — | — |

### Test Quality

| Metric | Value |
|--------|-------|
| Total collected tests | 1505+ |
| Passing tests | 1234+ |
| Ruff lint errors | **0** (Milestone A PASS) |
| Ruff format | Clean |
| Static types | mypy configured |
| Pre-commit hooks | lint, py_compile, migration guards |

---

## 3. Linting & Static Analysis

### Current State (from QUALITY.md)
```
Ruff: 0 errors, 0 warnings, 0 formatting issues
flake8 (E9, F821): Clean
py_compile: All files pass
```

### Configuration (`pyproject.toml`)
```toml
[tool.ruff]
line-length = 120
target-version = "py311"
select = ["E", "F", "I", "N", "W", "UP", "B", "A", "SIM", "ARG", "PTH", "ERA", "PL", "TRY", "RUF", "RET"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short -x"

[tool.coverage.run]
source = ["app"]
fail_under = 50
```

---

## 4. Security Scan Results

| Tool | Findings | Status |
|------|----------|--------|
| Bandit | 0 High, 2 Medium | ✅ Acceptable |
| Gitleaks | 0 leaks | ✅ Clean |
| Safety | Pinned dependencies | ✅ Lock file |
| Hadolint | Dockerfile lint | ✅ Config |
| Trivy | Container scan in CI | ✅ Configured |

---

## 5. Known Quality Issues

| Issue | Evidence | Severity |
|-------|----------|----------|
| **Low route coverage (35%)** | 53+ route files, many untested | **HIGH** |
| **Low service coverage (30%)** | 34+ service files lightly tested | **HIGH** |
| **Zero edge/interop coverage** | No edge/interop tests exist | **CRITICAL** |
| **Large route files** | ehr.py (73KB), compliance.py (47KB), clinical.py (41KB) | **MEDIUM** |
| **No frontend tests** | No test framework found in frontend-v2 | **HIGH** |
| **No E2E tests** | Only k6 load tests exist | **HIGH** |
| **performance budget test exists** | `test_performance_budgets.py` (14,786 bytes) | **LOW** — good |
| **chaos tests exist** | `test_chaos_survival.py`, chaos-scenarios.yaml | **LOW** — good |
| **Duplicate clinical engines** | services/ai vs routes/ai.py | **MEDIUM** |

---

## 6. Architecture Quality

| Dimension | Assessment | Evidence |
|-----------|-----------|----------|
| Modularity | ✅ Good | Clear separation: routes/services/models/core |
| Single Responsibility | ⚠️ Partial | ehr.py (73KB), compliance.py (47KB) are monoliths |
| Dependency Direction | ✅ Good | Routes → Services → Models → DB |
| Duplicate Code | ⚠️ Some | 2 AI engines, 2 frontend stacks, 2 deployment systems |
| Dead Code | ⚠️ Likely | National platform tables without routes |
| Documentation Alignment | ❌ Poor | Docs reference 36 routes, code has 53+ |
| Test Coverage | ⚠️ Below target | 54% overall with critical gaps |

---

## 7. Technical Debt Indicators

| Indicator | Level | Evidence |
|-----------|-------|----------|
| Large binary files in migration | 76KB single migration | Risk |
| Same-day migrations (17 on 2026-07-16) | High churn | Risk |
| 6 microservice stubs with 0 tests | Dead weight | Medium |
| Firebase bypassing backend security | Architectural | Critical |
| Docs mention MySQL (wrong) | Documentation debt | Low |
| Version divergence (2.1.0 vs 2.3.2) | Tracking debt | Low |

---

## 8. Quality Gates (from `quality-gate.yml`)

| Gate | Implementation | Status |
|------|---------------|--------|
| Architecture | `architecture-gate.py` | Configured |
| Performance | `performance-gate.py` | Configured |
| Security | `security-gate.py` | Configured |
| Database | `database-gate.py` | Configured |
| API | `api-gate.py` | Configured |
| FHIR | `fhir-gate.py` | Configured |
| Scalability | `scalability-gate.py` | Configured |
| Offline | `offline-gate.py` | Configured |
| Accessibility | `accessibility-gate.js` | Configured |
