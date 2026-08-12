# GULA Platform — Certification Framework

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Architecture Certification](#1-architecture-certification)
2. [Security Certification](#2-security-certification)
3. [Performance Certification](#3-performance-certification)
4. [Accessibility Certification](#4-accessibility-certification)
5. [FHIR Compliance Certification](#5-fhir-compliance-certification)
6. [Offline Capability Certification](#6-offline-capability-certification)
7. [Reliability Certification](#7-reliability-certification)
8. [Maintainability Certification](#8-maintainability-certification)
9. [Test Coverage Certification](#9-test-coverage-certification)
10. [Documentation Certification](#10-documentation-certification)
11. [Code Quality Certification](#11-code-quality-certification)
12. [API Compatibility Certification](#12-api-compatibility-certification)
13. [Database Integrity Certification](#13-database-integrity-certification)

---

## 1. Architecture Certification

### 1.1 Purpose

Verify that all modules in the platform comply with the defined architecture — clean architecture, DDD alignment, proper dependency direction, and absence of circular dependencies.

### 1.2 Criteria

| Criterion | Threshold | Method |
|-----------|-----------|--------|
| Layer violation | Zero violations | `shared/architecture/validator.py` |
| Circular dependencies | Zero cycles | Module dependency graph analysis |
| Dependency direction | Kernel → Business only | Import analysis |
| Module isolation | No cross-module ORM imports | Code audit |
| Clean Architecture layers | Domain has zero framework imports | Import scanner |
| DDD alignment | Entities encapsulate behavior | Code review |

### 1.3 Automated Checks

- `shared/architecture/validator.py` — Architecture validation
- `shared/architecture/knowledge_graph.py` — Codebase knowledge graph
- `make ci` — Includes syntax-gate + import-walk validation

### 1.4 Remediation

| Violation | Remediation |
|-----------|-------------|
| Layer violation | Move the violating import to the correct layer |
| Circular dependency | Extract shared interface into kernel/shared |
| Framework import in domain | Extract framework dependency to infrastructure layer |
| Cross-module ORM import | Add repository interface in domain, implementation in infrastructure |

### 1.5 Evidence Requirements

- Architecture validation report from `shared/architecture/validator.py`
- Dependency graph visualization (no cycles)
- Layer violation count = 0
- Architecture review board sign-off

---

## 2. Security Certification

### 2.1 Purpose

Verify that the platform meets OWASP ASVS Level 2 (or higher), follows NIST CSF guidelines, and passes CIS benchmarks for the technology stack.

### 2.2 Criteria

| Criterion | Threshold | Method |
|-----------|-----------|--------|
| OWASP ASVS Level | Level 2 minimum | Automated scan + manual review |
| OWASP API Security | Top 10 mitigated | `backend/app/firewall/` audit |
| Secret detection | Zero secrets in code | `gitleaks`, `trufflehog` |
| Dependency CVEs | Zero critical/high | `safety`, `trivy` scan |
| Authentication | JWT with blacklist, rotation | `backend/app/security/auth.py` review |
| Authorization | RBAC + ABAC enforced | Permissions audit |
| Encryption at rest | AES-256-GCM for PII | `shared/security/encryption.py` check |
| Encryption in transit | TLS 1.3 enforced | nginx config check |
| Rate limiting | Enabled on all endpoints | `backend/app/security/rate_limit.py` |
| Audit logging | All mutations logged | Coverage analysis |

### 2.3 Automated Checks

- `backend/app/core/kill_switch.py` — Kill switch audit
- `backend/app/firewall/api_firewall.py` — Firewall rules
- `beandit -ll -ii` — Python security linter
- `gitleaks` — Secret scanning
- `safety` — CVE scan
- `trivy` — Container vulnerability scan
- `hadolint` — Dockerfile linting

### 2.4 Evidence Requirements

- OWASP ASVS assessment report
- SAST/DAST scan results (no critical/high findings)
- SBOM with dependency vulnerability assessment
- Penetration test report (annual minimum)
- Security review sign-off

### 2.5 Code References

- `backend/app/security/` — All security modules
- `backend/app/firewall/` — API firewall
- `backend/app/core/self_healing.py` — Security degradation
- `.github/workflows/ci.yml` — Security scan job
- `shared/security/` — Shared security utilities

---

## 3. Performance Certification

### 3.1 Purpose

Verify that the platform meets response time SLAs, handles expected throughput, and uses resources efficiently under load.

### 3.2 Criteria

| Metric | Target | Method |
|--------|--------|--------|
| P50 latency | < 200ms | Load testing |
| P95 latency | < 500ms | Load testing |
| P99 latency | < 2000ms | Load testing |
| Throughput | > 1000 req/s (baseline) | Load testing |
| Error rate under load | < 1% | Load testing |
| Memory per worker | < 512MB | Resource monitoring |
| DB connection utilization | < 80% of pool | `get_pool_status()` |
| Concurrency limit | No shedding under target load | Load testing |
| Database query P95 | < 100ms | Query profiling |

### 3.3 Automated Checks

- `make test` — Load and stress tests
- `make scenario-test` — End-to-end load test with configurable USERS and ROUNDS
- `make integrity-test` — Concurrent order validation
- `backend/app/database.py` — `check_db_connection_detail()`

### 3.4 Evidence Requirements

- Load test results (P50/P95/P99 latency at target concurrency)
- Stress test results (breakpoint, saturation point)
- Database query profiling output
- Resource utilization under load (CPU, memory, connections)
- Performance sign-off

### 3.5 Code References

- `backend/app/main.py:ConcurrencyLimitMiddleware` — Concurrency management
- `backend/app/database.py` — Connection pool configuration
- `backend/tests/test_stress.py` — Stress tests
- `Makefile` — `scenario-test`, `integrity-test` targets

---

## 4. Accessibility Certification

### 4.1 Purpose

Verify that all user interfaces meet WCAG 2.1 AA standards, support RTL (Arabic-first) layout, and work with screen readers.

### 4.2 Criteria

| Criterion | Threshold | Method |
|-----------|-----------|--------|
| WCAG 2.1 AA compliance | Pass all criteria | Automated + manual audit |
| RTL support | Full bidirectional layout | `shared/design_system/rtl.py` |
| Screen reader support | Semantic HTML + ARIA labels | axe-core audit |
| Color contrast | ≥ 4.5:1 (normal), ≥ 3:1 (large) | Contrast analysis |
| Keyboard navigation | All features accessible | Manual testing |
| Touch targets | ≥ 44×44px | Design review |
| Text scaling | No loss of function at 200% | Browser testing |

### 4.3 Evidence Requirements

- WCAG 2.1 AA conformance report
- Accessibility audit results (axe-core, WAVE)
- RTL layout verification for all screens
- Screen reader compatibility test results
- Keyboard navigation flow documentation

### 4.4 Code References

- `shared/design_system/tokens.py` — Design tokens
- `shared/design_system/components.py` — Shared components
- `shared/design_system/rtl.py` — RTL support
- `frontend-v2/src/` — Frontend source

---

## 5. FHIR Compliance Certification

### 5.1 Purpose

Verify that FHIR resource mappings conform to R4/R5 specifications, including US Core, IPA, and national profiles.

### 5.2 Criteria

| Criterion | Threshold | Method |
|-----------|-----------|--------|
| Resource structure | Conforms to FHIR R4/R5 schema | Schema validation |
| Search parameters | FHIR search API compliant | `backend/app/national/fhir/search.py` audit |
| Bundle format | FHIR Bundle compliant | `backend/app/national/fhir/bundle.py` audit |
| Operations | create, read, update, search implemented | API audit |
| Profiles | US Core / IPA profiles supported | Mapping audit |
| Terminology | SNOMED, LOINC codes used | `backend/app/national/fhir/terminology.py` audit |
| Validation | FHIR validation on output | `backend/app/national/fhir/validation.py` |

### 5.3 Evidence Requirements

- FHIR resource validation report (all resources pass FHIR schema)
- FHIR Search API compliance
- Profile conformance documentation
- Terminology server integration verified

### 5.4 Code References

- `backend/app/national/fhir/` — FHIR resource mapping (10 modules)
- `backend/app/lims/fhir_mappers.py` — LIMS-to-FHIR mapping
- `backend/app/interoperability/` — HL7/FHIR interop
- `backend/app/national/fhir/validation.py` — FHIR validation

---

## 6. Offline Capability Certification

### 6.1 Purpose

Verify that edge agents, mobile apps, and PWAs function correctly offline and synchronize reliably when connectivity is restored.

### 6.2 Criteria

| Criterion | Threshold | Method |
|-----------|-----------|--------|
| Offline operation | All critical features work offline | Scenario testing |
| Sync reliability | Zero data loss in sync | Sync integration test |
| Conflict resolution | All conflicts detected and logged | `edge_agent/` audit |
| Delta sync | Only changed data transmitted | Protocol analysis |
| Reconnection | Auto-sync within 30s of reconnect | Integration test |
| Batch upload | ≤ 5s for 1000 records | Performance test |

### 6.3 Evidence Requirements

- Offline capability test results
- Sync reliability metrics (synced/conflicted/lost ratio)
- Conflict resolution trace log
- Bandwidth utilization analysis
- Edge agent certification report

### 6.4 Code References

- `edge_agent/` — Edge agent (offline operation)
- `frontend/` — Offline-capable PWA
- `backend/app/edge/` — Edge platform management
- `services/device_bridge/` — Device bridge

---

## 7. Reliability Certification

### 7.1 Purpose

Verify the platform's ability to recover from failures, maintain data integrity, and meet uptime SLAs.

### 7.2 Criteria

| Metric | Target | Method |
|--------|--------|--------|
| MTBF (Mean Time Between Failures) | > 720 hours | Production monitoring |
| MTTR (Mean Time To Recover) | < 30 minutes | Incident tracking |
| Fault tolerance | No SPOF in critical path | Architecture review |
| Circuit breaker recovery | < 30s for auto-recovery | `self_healing.py` verification |
| Data integrity after failure | Zero corruption | Chaos testing |
| Backup RPO | < 1 hour | Backup verification |
| Backup RTO | < 30 minutes | Restore drill |

### 7.3 Evidence Requirements

- Uptime monitoring data (last 90 days minimum)
- Incident post-mortem records
- Chaos test results
- Backup/restore test results
- MTBF/MTTR tracking

### 7.4 Code References

- `backend/app/core/self_healing.py` — Self-healing
- `backend/app/core/auto_repair.py` — Auto-repair
- `backend/tests/chaos/` — Chaos testing suite
- `Makefile` — `chaos`, `integrity-test` targets

---

## 8. Maintainability Certification

### 8.1 Purpose

Verify that code is maintainable — low complexity, high cohesion, low coupling, and well-structured.

### 8.2 Criteria

| Metric | Threshold | Method |
|--------|-----------|--------|
| Cyclomatic complexity (per function) | ≤ 10 | `radon cc` |
| Cyclomatic complexity (per class) | ≤ 20 | `radon cc` |
| Maintainability Index | ≥ 70 (green) | `radon mi` |
| Lines of code per function | ≤ 40 | Code analysis |
| Lines of code per file | ≤ 500 | Code analysis |
| Module coupling | Low (few imports) | Import analysis |
| Cohesion | High (focused modules) | Code review |

### 8.3 Automated Checks

- `radon cc` — Cyclomatic complexity analysis
- `radon mi` — Maintainability Index
- `pyflakes` — Static analysis
- `flake8` — Lint (select E9, F821)

### 8.4 Remediation

| Issue | Remediation |
|-------|-------------|
| High complexity | Refactor into smaller functions |
| Low maintainability | Add documentation, reduce complexity |
| High coupling | Extract interface, use dependency injection |
| Low cohesion | Split module by concern |

### 8.5 Evidence Requirements

- Cyclomatic complexity report
- Maintainability Index report per module
- Code structure analysis
- Code review sign-off

---

## 9. Test Coverage Certification

### 9.1 Purpose

Verify that the codebase has adequate test coverage at all levels of the test pyramid.

### 9.2 Criteria

| Level | Target | Method |
|-------|--------|--------|
| Line coverage | ≥ 80% | `pytest --cov` |
| Branch coverage | ≥ 70% | `pytest --cov-branch` |
| Mutation coverage | ≥ 60% | `mutmut` or `cosmic-ray` |
| Integration tests | All critical paths covered | Test mapping |
| API contract tests | All endpoints covered | Contract tests |
| Chaos tests | Resilience patterns verified | Chaos suite |

### 9.3 Automated Checks

- `pytest —cov` — Code coverage
- `Makefile` — `test`, `ci` targets
- `.github/workflows/ci.yml` — CI test jobs

### 9.4 Evidence Requirements

- Coverage report (line + branch)
- Mutation testing report
- Test execution report (all passing)
- Test-to-code ratio

### 9.5 Code References

- `backend/tests/` — 28 test modules
- `Makefile` — Test targets
- `.github/workflows/ci.yml` — CI pipeline

---

## 10. Documentation Certification

### 10.1 Purpose

Verify that the platform has adequate documentation — architecture docs, API docs, ADRs, READMEs, and operational runbooks.

### 10.2 Criteria

| Document Type | Required | Check |
|---------------|----------|-------|
| ADR coverage | All architecture decisions documented | ADR index check |
| API documentation | 100% of endpoints documented | OpenAPI spec check |
| README per module | Each module has README | File existence check |
| Architecture docs | Architecture doc for each major domain | Document index |
| Operational runbooks | All operational procedures documented | Runbook index |
| Changelog | Updated for each release | File content check |
| Migration guides | Breaking changes documented | Change audit |

### 10.3 Evidence Requirements

- ADR completeness report (all decisions have ADRs)
- API documentation coverage (100% of endpoints)
- README presence check (all modules)
- Architecture document index completeness
- Runbook completeness review

### 10.4 Code References

- `docs/adr/` — Architecture Decision Records
- `docs/runbooks/` — Operational runbooks
- `architecture/` — Architecture documentation
- `backend/app/main.py` — OpenAPI auto-generated docs

---

## 11. Code Quality Certification

### 11.1 Purpose

Verify that code meets quality standards for linting, typing, and code smells.

### 11.2 Criteria

| Check | Threshold | Tool |
|-------|-----------|------|
| Python linting | Zero errors | `pyflakes`, `flake8` (E9, F821) |
| Type hints | All functions typed | `mypy` (strict) |
| Import formatting | Consistent | `isort` |
| Code formatting | Consistent | `black` (where configured) |
| Code smells | Zero critical | `pylint`, `sonarqube` |
| Duplicate code | < 5% duplication | `pylint` duplicate analysis |
| Dead code | Zero dead imports | `vulture` or manual audit |

### 11.3 Automated Checks

- `make lint` — pyflakes + flake8
- `make ci` — syntax-gate (py_compile every file)
- `.github/workflows/ci.yml` — Lint job

### 11.4 Evidence Requirements

- Lint report (zero errors)
- Type checking report (all functions typed)
- Code smell report (zero critical)
- Duplicate code analysis

### 11.5 Code References

- `Makefile` — lint, ci targets
- `.github/workflows/ci.yml` — CI pipeline
- `backend/app/_compat.py` — Compatibility module

---

## 12. API Compatibility Certification

### 12.1 Purpose

Verify that API changes are backward-compatible and breaking changes are properly managed.

### 12.2 Criteria

| Check | Method |
|-------|--------|
| Backward compatibility | Compare API specs before/after change |
| Breaking change detection | Automated diff of OpenAPI specs |
| Deprecation policy | Deprecated endpoints return Sunset header |
| API versioning | Version in URL path |
| Response shape stability | Contract testing |
| Error format consistency | Error shape remains unchanged |

### 12.3 Evidence Requirements

- API diff report (showing no breaking changes)
- Contract test results
- Deprecation policy compliance
- Migration guide (if breaking changes exist)

### 12.4 Code References

- `backend/app/routes/` — All API routes
- `backend/app/main.py` — OpenAPI configuration

---

## 13. Database Integrity Certification

### 13.1 Purpose

Verify that database schema changes maintain referential integrity, follow migration policy, and are safe for production.

### 13.2 Criteria

| Check | Method |
|-------|--------|
| Referential integrity | FK constraints on all relationships |
| Migration idempotency | All migrations pass `upgrade → downgrade -1 → upgrade` |
| No destructive changes | No DROP COLUMN/DROP TABLE without review |
| Nullable new columns | New columns nullable or have server_default |
| Index coverage | Foreign keys indexed |
| Migration immutability | Existing migrations never modified |

### 13.3 Automated Checks

- `make ci` — Migration gate (CI)
- Alembic upgrade/downgrade round-trip
- FK constraint validation

### 13.4 Evidence Requirements

- Migration round-trip test results
- Referential integrity audit
- Index coverage analysis
- Migration policy compliance report

### 13.5 Code References

- `backend/migrations/versions/` — Migration files
- `backend/app/models/` — ORM models
- `CLAUDE.md` — Migration Policy section

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial certification framework |

**Review Cycle**: This document must be reviewed and updated quarterly or when significant architectural changes occur.
