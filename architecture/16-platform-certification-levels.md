# GULA Platform — Certification Levels (Bronze/Silver/Gold/Platinum/Diamond)

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Overview

Platform certification levels define progressive quality, security, and capability requirements. Moving up the levels increases confidence, reduces operational risk, and unlocks advanced features.

### Level Summary

| Level | Confidence | Security | Performance | Automation | AI Maturity |
|-------|-----------|----------|-------------|------------|-------------|
| 🟤 Bronze | Basic | Baseline | Functional | Manual | None |
| ⚪ Silver | Moderate | Standard | Reliable | Semi-automated | Basic |
| 🟡 Gold | High | Enhanced | Performant | Automated | Assisted |
| 🟣 Platinum | Very High | Advanced | Optimized | Auto-healing | Integrated |
| 💎 Diamond | Maximum | Zero-trust | Predictable | Autonomous | Native |

---

## 🟤 Bronze — Foundational

### Purpose

First deployable level. The platform works, is secured, and has documentation — but lacks operational maturity.

### Criteria by Dimension

| Dimension | Criteria | Evidence |
|-----------|----------|----------|
| **Architecture** | Layered structure exists | Module hierarchy document |
| **Architecture** | No circular dependencies | Dependency graph |
| **Architecture** | Kernel/business separation | Import analysis |
| **Security** | Authentication implemented | `backend/app/security/auth.py` — JWT |
| **Security** | Basic RBAC | `backend/app/security/rbac.py` — role check |
| **Security** | Secret detection passes | `gitleaks` — zero findings |
| **Security** | Basic rate limiting | `backend/app/security/rate_limit.py` — active |
| **Performance** | Application starts | `make up` — all containers healthy |
| **Performance** | Health endpoints respond | `/health/live` returns 200 |
| **Accessibility** | UI renders in Arabic | RTL layout active |
| **FHIR** | FHIR Patient resource exists | `backend/app/national/fhir/patient.py` |
| **Offline** | Basic offline capability | PWA service worker exists |
| **Reliability** | Graceful startup | `backend/app/core/startup_guard.py` — validates DB |
| **Maintainability** | Linting passes | `make lint` — zero errors |
| **Test Coverage** | Unit tests exist | `pytest` — some tests pass |
| **Documentation** | Architecture docs exist | `architecture/` directory populated |
| **Documentation** | README in root | `README.md` exists |
| **Code Quality** | Python syntax valid | `py_compile` — all files pass |
| **API Compat** | REST API works | Core CRUD endpoints functioning |
| **DB Integrity** | Base schema exists | Alembic migrations up to date |

### Evidence Checklist

- [ ] `make up` completes successfully
- [ ] `make health` returns all GREEN
- [ ] `make lint` has zero errors
- [ ] `make ci` syntax-gate passes
- [ ] JWT login/logout works
- [ ] Core CRUD endpoints respond (patients, orders, results)
- [ ] Architecture docs exist for all layers
- [ ] `.env.example` populated

### Automated Verification

```bash
make up && make health && make lint && make ci
```

---

## ⚪ Silver — Standard

### Purpose

Standard production deployment. All tests pass, monitoring in place, documented patterns.

### Criteria by Dimension

| Dimension | Criteria | Evidence |
|-----------|----------|----------|
| **Architecture** | DDD alignment checked | `shared/architecture/validator.py` — passes |
| **Architecture** | Layer violations = 0 | Architecture validation report |
| **Security** | OWASP ASVS L1 compliant | Security audit report |
| **Security** | CVE scan: zero critical/high | `safety`, `trivy` reports |
| **Security** | Audit logging in place | `backend/app/audit/audit_log.py` — active |
| **Performance** | P95 < 1s | Load test results |
| **Performance** | Throughput > 500 req/s | Load test results |
| **Accessibility** | WCAG 2.1 A compliant | Accessibility audit |
| **FHIR** | Patient, Observation, Organization | FHIR resource coverage ≥ 3 |
| **Offline** | Edge sync functional | Edge agent test |
| **Reliability** | Circuit breaker active | `backend/app/core/self_healing.py` — verified |
| **Reliability** | Retry pattern implemented | `backend/app/core/resilience.py` — in use |
| **Maintainability** | Complexity: function ≤ 10 | `radon cc` report |
| **Maintainability** | MI ≥ 50 (yellow+) | `radon mi` report |
| **Test Coverage** | Line ≥ 60% | `pytest --cov` report |
| **Test Coverage** | All existing tests pass | CI test job |
| **Documentation** | API docs generated | `/docs` accessible |
| **Documentation** | README per module | Module README check |
| **Code Quality** | Type hints on public functions | `mypy` (basic) |
| **API Compat** | Pagination implemented | `shared/schemas/pagination.py` — in use |
| **DB Integrity** | Migration round-trip tested | Alembic downgrade/upgrade verified |

### Evidence Checklist

- [ ] All Bronze criteria satisfied
- [ ] All tests pass (`make test`)
- [ ] Monitoring dashboards deployed (Grafana)
- [ ] Self-healing active (circuit breaker verified)
- [ ] API documentation auto-generated
- [ ] Basic load test completed
- [ ] Security scan report available
- [ ] ADR process established

### Automated Verification

```bash
make test && make ci && radon cc backend/app/ && radon mi backend/app/
```

---

## 🟡 Gold — Advanced

### Purpose

Enterprise-grade deployment. Full CQRS, event-driven architecture, comprehensive tests, FHIR conformant.

### Criteria by Dimension

| Dimension | Criteria | Evidence |
|-----------|----------|----------|
| **Architecture** | Full CQRS implemented | `backend/app/ehr/commands/`, `queries/` |
| **Architecture** | Event-driven with outbox | `backend/app/services/outbox_service.py` — active |
| **Architecture** | Domain events published | Events defined per bounded context |
| **Security** | OWASP ASVS L2 compliant | Security audit report |
| **Security** | ABAC implemented | `backend/app/security/abac.py` — active |
| **Security** | Encryption at rest | `shared/security/encryption.py` — verified |
| **Security** | Idempotency middleware | `backend/app/core/idempotency.py` — in use |
| **Performance** | P50 < 200ms, P95 < 500ms | Load test results |
| **Performance** | Concurrency management | `ConcurrencyLimitMiddleware` verified |
| **Performance** | Cache-aside pattern used | `backend/app/core/cache_manager.py` — active |
| **Accessibility** | WCAG 2.1 AA compliant | Accessibility audit |
| **FHIR** | All mandatory FHIR resources | FHIR mapping coverage ≥ 8 |
| **FHIR** | FHIR search API works | `backend/app/national/fhir/search.py` — tested |
| **Offline** | Conflict resolution verified | Edge agent conflict tests |
| **Offline** | Delta sync protocol | Sync test results |
| **Reliability** | Bulkhead pattern | `ConcurrencyLimitMiddleware` — verified |
| **Reliability** | Graceful degradation | `DegradedModeMiddleware` — verified levels |
| **Maintainability** | MI ≥ 70 (green) | `radon mi` report |
| **Test Coverage** | Line ≥ 80% | `pytest --cov` report |
| **Test Coverage** | Integration tests cover CRUD | Test mapping |
| **Documentation** | ADRs for major decisions | `docs/adr/` — indexed |
| **Documentation** | Runbooks for ops procedures | `docs/runbooks/` |
| **Code Quality** | Mypy strict mode passes | `mypy --strict` |
| **Code Quality** | Mutation coverage ≥ 60% | Mutation test report |
| **API Compat** | HATEOAS links in responses | API audit |
| **API Compat** | Error format standardized | Error format audit |
| **DB Integrity** | All FK constraints verified | Referential integrity check |

### Evidence Checklist

- [ ] All Silver criteria satisfied
- [ ] Full test suite passes (line ≥ 80%, branch ≥ 70%)
- [ ] FHIR compliance verified
- [ ] ABAC policies enforced
- [ ] CQRS pattern verified across EHR module
- [ ] Outbox pattern delivering events reliably
- [ ] Load test: P50 < 200ms, P95 < 500ms
- [ ] Chaos tests passing
- [ ] ADR index complete
- [ ] Runbooks published

### Automated Verification

```bash
make test && pytest --cov=app --cov-branch --cov-report=term
python -m shared.architecture.validator backend/app/
python -c "check_fhir_compliance()"
```

---

## 🟣 Platinum — Optimized

### Purpose

Mission-critical deployment. Automated certification, chaos-tested, SLO attainment, full observability, auto-healing.

### Criteria by Dimension

| Dimension | Criteria | Evidence |
|-----------|----------|----------|
| **Architecture** | Automated arch validation in CI | Architecture validator in CI pipeline |
| **Security** | OWASP ASVS L3 compliant | Penetration test report |
| **Security** | Zero-trust architecture | mTLS, continuous verification |
| **Security** | Break glass procedure tested | `backend/app/national/security/break_glass.py` — drilled |
| **Performance** | P99 < 2s at peak load | Load test at 2× expected peak |
| **Performance** | Resource efficiency optimized | Resource utilization < 70% at peak |
| **Accessibility** | WCAG 2.1 AAA targets met | Accessibility audit for critical paths |
| **FHIR** | FHIR R5 compatibility verified | FHIR R5 schema validation |
| **Offline** | Auto-sync with conflict auto-resolve | Automated sync tests |
| **Reliability** | SLO attainment ≥ 99.9% | Uptime monitoring (90 days) |
| **Reliability** | MTBF > 720h, MTTR < 30min | Incident tracking data |
| **Reliability** | Chaos-tested all resilience patterns | Chaos suite — all passed |
| **Maintainability** | All functions complexity ≤ 10 | `radon cc` — zero violations |
| **Test Coverage** | Mutation ≥ 60% | Mutation test report |
| **Test Coverage** | Contract tests for all APIs | Contract test results |
| **Documentation** | Automated doc generation | CI doc generation pipeline |
| **Code Quality** | Zero code smells (SonarQube) | SonarQube report |
| **API Compat** | Backward compat verified per release | API diff in CI |
| **DB Integrity** | Migration safety verified per change | Automated migration check |

### Evidence Checklist

- [ ] All Gold criteria satisfied
- [ ] Certification automated in CI
- [ ] SLO attainment ≥ 99.9% for 90 days
- [ ] Chaos suite passes all scenarios
- [ ] Penetration test: ASVS L3
- [ ] Zero critical/high CVEs
- [ ] Contract tests for all public APIs
- [ ] SBOM generated per release

### Automated Verification

```bash
make test && make chaos && python -m shared.architecture.validator --strict
```

---

## 💎 Diamond — Autonomous

### Purpose

Decades-ready, fully autonomous platform. AI-assisted operations, self-healing, zero-downtime deployments, predictive maintenance.

### Criteria by Dimension

| Dimension | Criteria | Evidence |
|-----------|----------|----------|
| **Architecture** | Self-optimizing architecture | Adaptive concurrency, auto-scaling |
| **Architecture** | Module auto-discovery | `backend/app/kernel/module/discovery.py` — active |
| **Security** | AI-driven threat detection | Intrusion detection with ML |
| **Security** | Automated incident response | Self-healing with auto-remediation |
| **Performance** | Predictive scaling | Auto-scaling based on ML predictions |
| **Performance** | Latency SLA: 99.9% within budget | Predictive SLO management |
| **Accessibility** | User-specific accessibility adaptation | Adaptive UI per user needs |
| **FHIR** | Real-time FHIR subscription | FHIR subscriptions active |
| **Offline** | Fully autonomous edge | Edge self-management |
| **Reliability** | Self-healing for all failure modes | Full auto-repair coverage |
| **Reliability** | Predictive failure detection | ML-based anomaly detection on metrics |
| **Reliability** | Zero-downtime deployments | Blue-green deployment verified |
| **Maintainability** | Automated refactoring | AI-assisted code quality |
| **Test Coverage** | AI-generated test coverage | Automated test generation |
| **Documentation** | AI-generated documentation | Auto-documentation pipeline |
| **Code Quality** | AI-assisted code review | Automated code review |
| **API Compat** | Automated compat verification | API compatibility AI check |

### Evidence Checklist

- [ ] All Platinum criteria satisfied
- [ ] Zero-downtime deployment verified
- [ ] Self-healing covers all failure modes
- [ ] Predictive maintenance active
- [ ] AI-driven ops decision making in place
- [ ] Fully autonomous edge operations
- [ ] Decades readiness plan established

---

## Certification Process

### Assessment Flow

```
Project requests certification → Self-assessment → Evidence collection
    → Automated verification → Peer review → Board approval → Certification granted
```

### Recertification

| Level | Recertification Period |
|-------|------------------------|
| Bronze | Every 12 months |
| Silver | Every 6 months |
| Gold | Every 6 months |
| Platinum | Every 3 months |
| Diamond | Every 3 months |

### Upgrade Path

```
Bronze ─→ Silver ─→ Gold ─→ Platinum ─→ Diamond
   ↑         ↑         ↑          ↑
   | After satisfying all criteria of current level + next level
   | Automated verification must pass for target level
```

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial certification levels |

**Review Cycle**: This document must be reviewed and updated semi-annually.
