# Testing Strategy

## Test Suite Overview

| Category | Files | Tests | Purpose |
|----------|-------|-------|---------|
| Unit | 25 | 400+ | Service, model, domain logic |
| Integration | 10 | 200+ | Route, DB, cross-module |
| Security | 3 | 54+ | Auth, JWT, encryption, RBAC |
| Regression | 5 | 100+ | Stability, concurrency, chaos |
| Skills | 15 | 100+ | Skill platform lifecycle |
| Performance | 2 | 50+ | Stress, performance budgets |

## Running Tests

```bash
# Full suite
cd backend && .venv/bin/python -m pytest tests/ -v

# With coverage
cd backend && .venv/bin/python -m pytest tests/ --cov=app --cov-report=term-missing

# Security tests only
cd backend && .venv/bin/python -m pytest tests/test_security.py tests/test_security_regression.py -v

# Integration tests
cd backend && .venv/bin/python -m pytest tests/integration/ -v

# Single test
cd backend && .venv/bin/python -m pytest tests/test_security.py::test_jwt_reject_expired -v
```

## Quality Gates

### Gate A: Backend Foundation
- **Ruff lint**: 0 errors
- **Ruff format**: All files formatted
- **PyCompile**: All files compile
- **Tests**: 1234+ passing

### Gate B: Security
- **Bandit**: 0 High, 2 Medium (dev config only), 53 Low
- **Security tests**: 54+ passing
- **No permission bypasses**: Verified

### Gate C: Testing
- **Coverage**: 54% (17273 statements, 7992 missed)
- **High-coverage modules**: auth (96%), models (95%), integration domain (90%+)
- **Known gaps**: routes (avg 35%), services (avg 30%), edge/interoperability (0%)

### Gate D: Production Readiness
- All quality gates green
- No critical security findings
- No architecture regressions
- Documentation complete

## Test Markers

```python
@pytest.mark.unit          # Fast, isolated unit tests
@pytest.mark.integration   # Tests requiring DB or multiple modules
@pytest.mark.security      # Security-focused tests
@pytest.mark.stress        # Performance/load tests
```

## Coverage Targets

| Module | Current | Target | Priority |
|--------|---------|--------|----------|
| security/ | 65% | 80% | High |
| models/ | 90% | 95% | High |
| routes/ | 35% | 60% | Medium |
| services/ | 30% | 50% | Medium |
| integration/ | 70% | 85% | High |
| edge/ | 25% | 50% | Low |

## Known Issues

1. **268 test errors**: Fixture/collection issues in slower test modules (test_tiers_privilege, test_tenant_isolation_matrix). These are test isolation issues, not production code bugs.
2. **3 test failures**: Minor assertion mismatches in test ordering scenarios.
3. **bcrypt deprecation warning**: passlib 1.7.4 with bcrypt 4.1.3 shows `__about__` deprecation — non-functional.
