# GULA Definition of Done

## Purpose

The Definition of Done (DoD) establishes the minimum quality bar for every feature, change, or fix in GULA. No work item is complete until it satisfies ALL criteria in the DoD.

## Mandatory Criteria

### Code
- [ ] All code compiles without errors (`py_compile`)
- [ ] All linting checks pass (`pyflakes --select=E9,F821`)
- [ ] All pre-existing tests continue to pass
- [ ] New code follows existing style patterns
- [ ] No hardcoded secrets, URLs, or credentials
- [ ] No dead code or commented-out code
- [ ] No debug logging or print statements in production code
- [ ] Type hints present on all function signatures

### Testing
- [ ] Unit tests written for new service methods
- [ ] Integration tests written for new API endpoints
- [ ] Error cases tested (not just happy path)
- [ ] Tests are deterministic (no flaky tests)
- [ ] Test coverage >= 80% for new/modified modules

### Documentation
- [ ] API changes reflected in OpenAPI spec (auto-generated)
- [ ] Configuration changes documented in `.env.example`
- [ ] Database migrations documented in migration file
- [ ] Architecture decisions documented in ADR (if applicable)
- [ ] Release notes updated

### Security
- [ ] Security implications reviewed
- [ ] Authentication required for new endpoints
- [ ] Authorization enforced for all sensitive operations
- [ ] Input validation implemented
- [ ] Output encoding for XSS prevention (frontend)
- [ ] SQL injection prevention (parameterized queries)
- [ ] No secrets committed

### Database
- [ ] Migration is idempotent (guarded with _has_table/_has_column)
- [ ] Migration round-trip tested (upgrade → downgrade → upgrade)
- [ ] New columns are nullable or have server_default
- [ ] Indexes created for foreign keys and query patterns
- [ ] Existing migrations never modified

### Frontend (if applicable)
- [ ] Arabic/RTL support verified
- [ ] Responsive design verified (desktop, tablet, mobile)
- [ ] Keyboard navigation verified
- [ ] Screen reader compatibility verified
- [ ] Loading states implemented
- [ ] Error states implemented
- [ ] Empty states implemented
- [ ] Backend-driven permissions respected
- [ ] Dynamic menu integration verified

### Integration
- [ ] API backward compatibility maintained
- [ ] Event schemas backward compatible
- [ ] Integration tests with external systems pass

### Operations
- [ ] Monitoring metrics added (if applicable)
- [ ] Logging at appropriate levels
- [ ] Error messages are actionable
- [ ] Rollback plan documented (if applicable)

## Quality Gates (CI Enforcement)

| Gate | Tool | Threshold |
|------|------|-----------|
| Syntax check | `py_compile` | 0 errors |
| Lint | `pyflakes` | 0 errors (E9, F821) |
| Security scan | `bandit` | 0 high/medium severity |
| Secret detection | `gitleaks` | 0 findings |
| Dependency scan | `safety` | 0 critical/high CVEs |
| Migration idempotency | `alembic upgrade head` | Pass on clean DB |
| Migration round-trip | `alembic downgrade -1 && upgrade head` | Pass |
| Backend tests | `pytest` | All pass, >= 80% coverage |
| Import walk | Python import simulation | 0 errors |

## Definition of Done Exception

Exceptions to the DoD require:
1. Written justification
2. Architecture Board approval
3. A documented plan to meet the criteria in a follow-up work item
4. An expiration date for the exception

No exception may compromise clinical safety, data integrity, or security.
