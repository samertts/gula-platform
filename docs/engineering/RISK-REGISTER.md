# Risk Register — GULA Platform

**Version:** 1.0.0
**Date:** 2026-07-08
**Classification:** Internal — Engineering

---

## Risk Scoring

| Score | Level | Description |
|-------|-------|-------------|
| 1-3 | Low | Acceptable, monitor periodically |
| 4-6 | Medium | Requires mitigation plan |
| 7-9 | High | Requires immediate action |
| 10 | Critical | Blocking — must resolve before proceeding |

Scoring: `Likelihood (1-5) × Impact (1-5)` where 1 = Very Low, 5 = Very High.

## Risk Register

### R-001: Patient Data Exposure

| Field | Value |
|-------|-------|
| **Risk** | Unauthorised access to patient data across tenant boundaries |
| **Likelihood** | 2 (Low) |
| **Impact** | 5 (Critical) |
| **Score** | 10 (Critical) |
| **Current Mitigation** | lab_id filtering on all queries, RBAC, audit logging, encryption |
| **Residual Risk** | 3 (Low) |
| **Status** | Managed |

### R-002: Data Loss on Migration

| Field | Value |
|-------|-------|
| **Risk** | Schema migration causes data loss or corruption |
| **Likelihood** | 1 (Very Low) |
| **Impact** | 5 (Critical) |
| **Score** | 5 (Medium) |
| **Current Mitigation** | Immutable migrations, idempotency guards, downgrade testing, CI migration check |
| **Residual Risk** | 2 (Low) |
| **Status** | Managed |

### R-003: Test Coverage Gap

| Field | Value |
|-------|-------|
| **Risk** | Insufficient test coverage in routes/services misses regressions |
| **Likelihood** | 4 (High) |
| **Impact** | 3 (Medium) |
| **Score** | 12 (Critical) |
| **Current Mitigation** | 54% coverage, quality gates catch syntax/compilation issues |
| **Residual Risk** | 6 (Medium) |
| **Status** | Mitigating — increasing coverage |

### R-004: Fixture Instability

| Field | Value |
|-------|-------|
| **Risk** | 268 test fixture errors undermine CI reliability and developer trust |
| **Likelihood** | 5 (Very High) |
| **Impact** | 3 (Medium) |
| **Score** | 15 (Critical) |
| **Current Mitigation** | Core tests (1234+) pass, errors are fixture isolation issues |
| **Residual Risk** | 8 (High) |
| **Status** | Under investigation |

### R-005: Dependency Vulnerability

| Field | Value |
|-------|-------|
| **Risk** | Third-party dependency introduces security vulnerability |
| **Likelihood** | 3 (Medium) |
| **Impact** | 4 (High) |
| **Score** | 12 (Critical) |
| **Current Mitigation** | Bandit scan, safety scan in CI, hadolint for Docker |
| **Residual Risk** | 6 (Medium) |
| **Status** | Managed — monitoring |

### R-006: Single Point of Failure

| Field | Value |
|-------|-------|
| **Risk** | PostgreSQL single instance failure causes complete outage |
| **Likelihood** | 2 (Low) |
| **Impact** | 5 (Critical) |
| **Score** | 10 (Critical) |
| **Current Mitigation** | pg_dump backups, recovery scripts, failover scripting |
| **Residual Risk** | 5 (Medium) |
| **Status** | Managed — DR plan exists |

### R-007: National ID Compliance

| Field | Value |
|-------|-------|
| **Risk** | Non-compliant handling of Iraqi national ID data |
| **Likelihood** | 2 (Low) |
| **Impact** | 4 (High) |
| **Score** | 8 (High) |
| **Current Mitigation** | AES-256 encryption at rest, dual-read None handling, feature flags |
| **Residual Risk** | 3 (Low) |
| **Status** | Managed |

### R-008: Secret Key Compromise

| Field | Value |
|-------|-------|
| **Risk** | SECRET_KEY, ENCRYPTION_KEY, or JWT secret leaked |
| **Likelihood** | 1 (Very Low) |
| **Impact** | 5 (Critical) |
| **Score** | 5 (Medium) |
| **Current Mitigation** | No hardcoded secrets, env-only, gitignored, Gitleaks scan |
| **Residual Risk** | 2 (Low) |
| **Status** | Managed |

### R-009: Concurrent Access Conflict

| Field | Value |
|-------|-------|
| **Risk** | Race condition in LabResult optimistic lock causes data loss |
| **Likelihood** | 2 (Low) |
| **Impact** | 4 (High) |
| **Score** | 8 (High) |
| **Current Mitigation** | version column optimistic lock, retry logic |
| **Residual Risk** | 3 (Low) |
| **Status** | Managed |

### R-010: Regulatory Change

| Field | Value |
|-------|-------|
| **Risk** | Iraqi healthcare regulation changes require platform modification |
| **Likelihood** | 3 (Medium) |
| **Impact** | 3 (Medium) |
| **Score** | 9 (High) |
| **Current Mitigation** | Feature flags, SNDHS-lite architecture, configurable compliance |
| **Residual Risk** | 5 (Medium) |
| **Status** | Monitoring |

## Risk Matrix

```
Impact →
 5 | R-001  R-006  R-008
 4 | R-005  R-007  R-009
 3 |        R-003  R-010
 2 |               R-004
 1 |
   +------------------------
     1    2    3    4    5
              Likelihood →
```

## Mitigation Plan

### Immediate (Critical — score 10+)

| Risk | Action | Owner | By |
|------|--------|-------|-----|
| R-003 (12) | Write tests for uncovered routes | Engineering | 30 days |
| R-004 (15) | Fix fixture isolation in conftest.py | Engineering | 14 days |
| R-005 (12) | Enable Dependabot/Renovate | DevOps | 7 days |

### Short-term (High — score 7-9)

| Risk | Action | Owner | By |
|------|--------|-------|-----|
| R-007 (8) | Complete national ID compliance audit | Security | 30 days |
| R-009 (8) | Add integration test coverage for optimistic lock | Engineering | 30 days |
| R-010 (9) | Monitor Iraqi healthcare regulatory landscape | Product | Ongoing |

### Managed (Medium — score 4-6)

| Risk | Action | Owner | By |
|------|--------|-------|-----|
| R-002 (5) | Add migration integrity fuzz testing | Engineering | 60 days |
| R-006 (5) | Test DR recovery procedure | DevOps | 30 days |
| R-008 (5) | Verify Gitleaks scan in CI | Security | 7 days |
| R-001 (3) | Continue current practices | Engineering | Ongoing |

## References

- `docs/engineering/TECHNICAL-DEBT.md` — Technical debt register
- `CLAUDE.md` — Engineering Constitution security invariants
- `SECURITY.md` — Security policy and scan results
- `docs/adr/` — Architecture Decision Records
