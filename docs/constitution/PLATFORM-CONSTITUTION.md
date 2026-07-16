# GULA National Digital Health Platform — Constitution

**Version:** 1.0.0 (Frozen)
**Date:** 2026-07-16
**Classification:** SUPREME — Platform Constitution
**Supersedes:** All prior engineering guidelines

---

## Preamble

This Constitution is the supreme engineering authority of the GULA National Digital
Health Platform. Every module, application, API, database, plugin, AI model,
workflow, integration, mobile application, desktop application, and deployment
MUST comply with this document. Nothing may bypass these rules.

The Constitution derives its authority from the immutable principles of:

- **Patient Safety** — No change may risk patient data loss or harm
- **Data Integrity** — Patient data is sacred and immutable
- **Stability** — Working code must not be broken to add features
- **National Sovereignty** — Iraqi health data remains under Iraqi control
- **Zero Trust** — Trust nothing, verify everything

---

## Article I: Architecture Constitution

### Section 1.1 — Immutable Architecture Principles

| Principle | Mandate | Violation |
|-----------|---------|-----------|
| Clean Architecture | Layers: Routes → Services → Domain → Infrastructure. Inner layers never depend on outer layers. | BLOCKER |
| Domain-Driven Design | Every bounded context has explicit domain models, repositories, and services. Ubiquitous language enforced across code. | BLOCKER |
| CQRS | Reads and writes use separate models. Commands return void/ID. Queries never mutate state. | BLOCKER |
| Event-Driven | All cross-boundary communication via events. No synchronous cross-module calls. | BLOCKER |
| Hexagonal Architecture | Core domain has no framework dependencies. Adapters implement ports. | BLOCKER |
| Modular Monolith | Modules are physically separate Python packages. Cross-module imports must go through public interfaces only. | BLOCKER |
| Microservice Rules | Services communicate via events only. No shared databases. No synchronous HTTP between services. | BLOCKER |
| Plugin Rules | Plugin interface is versioned and stable. Plugins are sandboxed. No plugin may access the database directly. | BLOCKER |
| Offline First | Every feature must work offline. Sync is eventual and conflict-resolved via last-writer-wins with audit. | BLOCKER |

### Section 1.2 — FHIR Mandate

All health data exchange MUST use FHIR R4 resources. Every internal model MUST
have a FHIR mapping. Every API that exposes patient data MUST offer a FHIR
content-type option (`application/fhir+json`).

### Section 1.3 — API First

Every feature MUST be accessible via a well-defined API before any UI is built.
Internal APIs are versioned. Public APIs are versioned with deprecation notices
of at least 6 months.

### Section 1.4 — Security By Design

Security requirements are non-functional requirements. Every feature MUST pass
security review before deployment. Threats are modeled using STRIDE per feature.

### Section 1.5 — Privacy By Design

Data minimization is mandatory. Collect only what is needed. Retain only as long
as required. Encrypt everything sensitive. Every data access is logged and auditable.

### Section 1.6 — Accessibility By Design

All user interfaces MUST meet WCAG 2.1 AA minimum. Arabic-first interfaces with
full RTL support. Screen reader compatibility is required.

### Section 1.7 — Observability By Design

Every component MUST expose health, metrics, and traces. No silent failures.
Every error MUST be logged with correlation ID, user context, and stack trace.

### Section 1.8 — AI By Design

Every AI feature must have: human approval gate, explainability output,
hallucination detection, bias monitoring, and full audit trail.

---

## Article II: Engineering Constitution

### Section 2.1 — Coding Standards

| Rule | Standard | Enforcement |
|------|----------|-------------|
| Language | Python 3.11+ | pyproject.toml |
| Style | Ruff (all rules except E501, B008) | Pre-commit + CI |
| Formatting | Ruff formatter (double quotes, 100 chars) | CI gate |
| Type Hints | Required for all public APIs | MyPy strict |
| Docstrings | Google style for public APIs | Manual review |
| Imports | isort-compatible (Ruff I) | CI gate |
| No Wildcards | `from module import *` forbidden | Ruff F403 |

### Section 2.2 — Naming Standards

| Element | Convention | Example |
|---------|-----------|---------|
| Packages | `snake_case` | `app/order_service/` |
| Modules | `snake_case` | `patient_service.py` |
| Classes | `PascalCase` | `LabOrderRepository` |
| Functions | `snake_case` | `create_patient()` |
| Variables | `snake_case` | `patient_name` |
| Constants | `UPPER_CASE` | `MAX_RETRY_COUNT` |
| Private | Leading underscore | `_internal_method()` |
| Protected | Leading underscore | `_protected_field` |
| DB Tables | `snake_case` plural | `lab_orders`, `patients` |
| DB Columns | `snake_case` | `national_id`, `created_at` |
| API Paths | `kebab-case` plural | `/api/v1/lab-orders` |
| API Fields | `snake_case` | `patient_name` |
| Environment Variables | `UPPER_CASE` | `DATABASE_URL` |

### Section 2.3 — API Standards

- RESTful resource-oriented design
- Versioned URL prefix: `/api/v1/`
- Standard HTTP methods: GET, POST, PUT, PATCH, DELETE
- Consistent error response format: `{"detail": "...", "code": "...", "request_id": "..."}`
- Pagination: `?limit=N&offset=N` with `X-Total-Count` header
- Rate limiting: `X-RateLimit-*` headers on all responses
- Content negotiation via `Accept` header
- OpenAPI 3.1 spec required for every endpoint

### Section 2.4 — Database Standards

- PostgreSQL 16 with UUID primary keys
- Every table has `created_at`, `updated_at` timestamps
- Soft delete via `deleted_at` column (not hard deletes)
- Audit logging for every mutation
- Index naming: `ix_{table}_{column}`
- FK naming: `fk_{child_table}_{parent_table}`
- Unique constraint naming: `uq_{table}_{columns}`
- No table without primary key
- No column without explicit type

### Section 2.5 — Migration Standards

| Rule | Mandate |
|------|---------|
| Immutability | Existing migrations never modified |
| New revisions | `alembic revision --autogenerate -m "..."` |
| Idempotency | Guards: `_has_column()`, `_table_exists()`, `_index_exists()` |
| Nullable columns | New columns MUST be nullable or have `server_default` |
| Round-trip test | `downgrade -1` then `upgrade head` must succeed |
| Clean DB test | Migrations must apply to empty database |

### Section 2.6 — Testing Standards

| Level | Scope | Tool | Required Coverage |
|-------|-------|------|-------------------|
| Unit | Single function/class | pytest | 95%+ |
| Integration | Service + DB | pytest + TestClient | 90%+ |
| API | Full HTTP round-trip | httpx TestClient | 95%+ |
| Security | Auth, RBAC, encryption | pytest | 100% |
| Performance | Latency, throughput | k6 | Key endpoints |
| Chaos | Resilience | Custom suite | Weekly |

### Section 2.7 — Logging Standards

- Structured JSON logging (all environments)
- Required fields: `timestamp`, `level`, `message`, `request_id`, `user_id`, `lab_id`, `service`, `module`
- Log levels: DEBUG (dev), INFO (prod ops), WARNING (abnormal), ERROR (failure), CRITICAL (data loss risk)
- No PII in logs (mask patient identifiers)
- Correlation ID propagates across all services

### Section 2.8 — Telemetry Standards

- OpenTelemetry for distributed tracing
- Prometheus metrics for: request count, latency (p50/p95/p99), error rate, active users, queue depth
- Sentry for error tracking (optional)
- Health check endpoints: `/health/live`, `/health/ready`, `/health/deep`
- Every service exposes port for scraping

### Section 2.9 — Documentation Standards

- ADRs for every architectural decision
- OpenAPI 3.1 for every API
- README.md for every package/module
- Inline documentation for complex logic (not trivial getters/setters)
- Runbooks for every operational procedure
- Architecture diagrams in `docs/architecture/`

### Section 2.10 — Versioning Standards

- Semantic Versioning: `MAJOR.MINOR.PATCH`
- MAJOR: breaking API/database changes
- MINOR: new features, backward compatible
- PATCH: bug fixes, no new features
- Release channels: stable, LTS, beta, RC, nightly
- Every release tagged in git

---

## Article III: Quality Constitution

### Section 3.1 — Mandatory Quality Gates

| Gate | Check | Threshold | Blocking |
|------|-------|-----------|----------|
| Q1 | Test coverage | >=95% overall | YES |
| Q2 | Critical bugs | 0 | YES |
| Q3 | High vulnerabilities | 0 | YES |
| Q4 | Architecture violations | 0 | YES |
| Q5 | Circular dependencies | 0 | YES |
| Q6 | Dead code | 0 detected | YES |
| Q7 | Unused dependencies | 0 | YES |
| Q8 | Hardcoded secrets | 0 | YES |
| Q9 | Broken documentation | 0 | YES |
| Q10 | MyPy strict errors | 0 | YES |
| Q11 | Ruff lint errors | 0 | YES |
| Q12 | Failed tests | 0 | YES |

### Section 3.2 — Quality Enforcement

- Quality gates run on every PR
- PR cannot merge if any blocking gate fails
- Gates are defined in `config/quality-gates/`
- Exemptions require 3-person engineering review
- Coverage reports published to every PR

### Section 3.3 — Continuous Quality Monitoring

- Weekly dependency audit
- Monthly architecture review
- Quarterly technical debt assessment
- Annual full platform audit

---

## Article IV: Security Constitution

### Section 4.1 — Zero Trust Architecture

- Every request is authenticated, authorized, and encrypted
- No trust based on network location
- Microsegmentation enforced
- Continuous verification of all entities
- mTLS between all services

### Section 4.2 — Access Control

| Layer | Mechanism | Scope |
|-------|-----------|-------|
| Authentication | JWT (access + refresh tokens) | All API access |
| Authorization | RBAC (9 roles x 13 permissions) | All operations |
| Fine-grained | ABAC (resource attributes) | Sensitive data |
| API-level | API keys with scoped permissions | Integration access |
| Audit | Every access logged | All operations |

### Section 4.3 — mTLS

All inter-service communication MUST use mutual TLS. Certificate lifecycle
is automated. Certificate rotation is monthly. Expired certificates trigger
automatic alerting.

### Section 4.4 — Encryption Standards

| Data State | Standard | Implementation |
|-----------|----------|----------------|
| At rest (DB) | AES-256-GCM | Fernet (Python cryptography) |
| At rest (disk) | LUKS/AES-256 | OS-level encryption |
| In transit (internal) | TLS 1.3 | mTLS |
| In transit (external) | TLS 1.3 | nginx termination |
| End-to-end | Per-field encryption | National ID, health ID |

### Section 4.5 — Secrets Management

- No secrets in code, config files, or Docker images
- Secrets loaded from environment variables at runtime
- Vault integration for production secrets
- Automated rotation every 90 days
- Weak secret detection on startup (hard fail)

### Section 4.6 — SBOM (Software Bill of Materials)

- SBOM generated on every build
- SBOM stored as CI artifact
- SBOM validated against vulnerability databases
- Dependency scanning in CI (safety, pip-audit, Trivy)

### Section 4.7 — Supply Chain Security

- All dependencies pinned with hash verification
- Dependabot configured for automated PRs
- Weekly vulnerability scan
- Third-party code review required for new dependencies
- Docker images scanned with Trivy

### Section 4.8 — Dependency Guardian

- Automated dependency upgrade PRs (Dependabot)
- Pinning all transitive dependencies
- Lockfile maintained and verified
- Deprecation detection and migration planning

### Section 4.9 — AI Security Guardian

- AI model provenance tracking
- Model integrity verification
- Prompt injection detection
- Output sanitization
- Rate limiting on AI endpoints

### Section 4.10 — Runtime Guardian

- Runtime application self-protection (RASP)
- File integrity monitoring
- Process monitoring
- Network anomaly detection
- Container runtime security

### Section 4.11 — Architecture Guardian

- Automated architecture compliance checking
- Dependency graph validation
- Layer boundary enforcement
- Cross-module import detection
- Circular dependency detection

---

## Article V: AI Constitution

### Section 5.1 — Human Approval

Every AI decision that affects patient care MUST have human approval.
AI provides recommendations, never final decisions in clinical pathways.

### Section 5.2 — Explainability

Every AI output MUST include an explanation of how the result was reached.
Black-box models are not permitted for clinical decisions.

### Section 5.3 — Prompt Registry

All AI prompts are registered, versioned, and immutable once deployed.
Prompt changes require review and approval.

### Section 5.4 — Model Registry

All AI models are registered with:
- Model ID, version, source
- Training data provenance
- Validation results
- Performance metrics
- Known limitations

### Section 5.5 — Model Validation

Every model MUST pass validation before deployment:
- Accuracy >= threshold
- Bias testing
- Adversarial testing
- Edge case coverage

### Section 5.6 — Model Monitoring

- Continuous performance monitoring
- Data drift detection
- Concept drift detection
- Automatic alerting on degradation

### Section 5.7 — Hallucination Detection

- Factual consistency verification
- Source grounding verification
- Confidence scoring
- Automatic flagging of uncertain outputs

### Section 5.8 — Bias Detection

- Demographic parity testing
- Equal opportunity testing
- Disparate impact analysis
- Continuous bias monitoring

### Section 5.9 — AI Audit Trail

Every AI interaction is logged:
- Input, output, confidence
- Model version, prompt version
- Human approval (if required)
- Timestamp, user, context

### Section 5.10 — AI Safety

- Guardrails on all AI outputs
- Content filtering
- Prompt injection prevention
- Rate limiting and resource isolation
- Kill switch for AI features

---

## Article VI: Operations Constitution

### Section 6.1 — Monitoring

Monitoring is mandatory for every service and includes:
- CPU, memory, disk, network
- Request rate, latency, error rate
- Database connection pool depth
- Queue depths
- Cache hit rates

### Section 6.2 — Distributed Tracing

- OpenTelemetry spans for every request
- Trace context propagated across all services
- Sampling rate: 100% for errors, 10% for normal traffic
- Traces stored in Tempo/ClickHouse

### Section 6.3 — Metrics

| Metric Type | Examples | Collection |
|-------------|----------|------------|
| RED metrics | Rate, Errors, Duration | Prometheus |
| USE metrics | Utilization, Saturation, Errors | Prometheus |
| Business metrics | Orders/hour, Active labs | Custom |
| SRE metrics | SLO attainment, Error budget | Prometheus |

### Section 6.4 — Health Checks

| Level | Endpoint | Purpose | Frequency |
|-------|----------|---------|-----------|
| Liveness | `/health/live` | Process alive | 10s |
| Readiness | `/health/ready` | Can serve traffic | 10s |
| Deep | `/health/deep` | Full diagnostic | 60s |
| Component | Per-service | Specific dependency | 30s |

### Section 6.5 — Backups

| Type | Schedule | Retention | Destination |
|------|----------|-----------|-------------|
| Full DB | Daily | 30 days | S3-compatible |
| WAL | Continuous | 7 days | S3-compatible |
| Config files | Daily | 90 days | Git + S3 |
| Secrets | On rotation | 3 versions | Vault |

### Section 6.6 — Recovery

- Recovery Time Objective (RTO): 4 hours
- Recovery Point Objective (RPO): 1 hour
- Automated failover for database
- Automated recovery testing monthly

### Section 6.7 — Chaos Engineering

- Weekly chaos experiments in staging
- Monthly in production (controlled blast radius)
- Game days every quarter
- Failure modes: network partition, node failure, DNS failure, certificate expiry, resource exhaustion

### Section 6.8 — Capacity Planning

- Monthly capacity review
- Auto-scaling based on metrics
- Annual capacity forecasting
- Load testing before major releases

### Section 6.9 — Business Continuity

- Disaster recovery plan documented and tested
- Multi-region failover capability
- Communication plan for incidents
- Regular tabletop exercises

### Section 6.10 — Disaster Recovery

| Scenario | Response | RTO | RPO |
|----------|----------|-----|-----|
| Single instance failure | Auto-restart | 1 min | 0 |
| DB primary failure | Auto-failover | 5 min | <1 min |
| Region failure | Manual failover | 1 hour | 1 hour |
| Data corruption | PITR recovery | 2 hours | 1 hour |

---

## Article VII: Developer Constitution

### Section 7.1 — Automatic Code Generation

CRUD operations, DTOs, repositories, commands, queries, events, services,
REST APIs, SDKs, CLI, documentation, unit tests, and integration tests
MUST be auto-generated from canonical schemas.

### Section 7.2 — Automatic Tests

Every code change MUST automatically generate:
- Unit tests for new functions
- Integration tests for new endpoints
- Security tests for new data access
- Performance benchmarks for critical paths

### Section 7.3 — Automatic Documentation

Documentation MUST be auto-generated from code:
- OpenAPI from route definitions
- ADRs from architecture decisions
- Runbooks from operational patterns
- READMEs from module metadata

### Section 7.4 — Automatic API Catalog

Every API MUST be discoverable in the API catalog. The catalog is
auto-generated from OpenAPI specs and includes: endpoint, method,
parameters, auth method, rate limit, SLA tier.

### Section 7.5 — Automatic SDK

Client SDKs MUST be auto-generated from OpenAPI specs for:
Python, TypeScript, Java, Dart/Flutter.

### Section 7.6 — Automatic Architecture Validation

Architecture compliance MUST be automatically validated on every build.
Gates: layer violations, circular dependencies, dead code, module boundaries.

### Section 7.7 — Automatic Security Review

Security review MUST be automated:
- SAST (Bandit, Semgrep)
- Dependency scanning (Safety, Trivy)
- Secret scanning (Gitleaks)
- Container scanning (Trivy)

### Section 7.8 — Automatic Release Notes

Release notes MUST be auto-generated from git history, structured as:
- Features
- Bug fixes
- Security updates
- Breaking changes
- Deprecations

---

## Article VIII: Release Constitution

### Section 8.1 — Release Channels

| Channel | Quality Gate | Frequency | Support |
|---------|-------------|-----------|---------|
| Nightly | Syntax only | Daily | None |
| Beta | All gates pass | Weekly | Best effort |
| RC | Full certification | Before release | High |
| Stable | Production certified | Monthly | LTS |
| LTS | Full audit | Quarterly | 2 years |
| Hotfix | Expedited | As needed | Immediate |

### Section 8.2 — Rollback Policy

Every deployment MUST support rollback to the previous version.
Rollback must be: automated, tested, complete within 5 minutes.

### Section 8.3 — Migration Validation

Database migrations are validated before any release:
- Fresh DB test: `alembic upgrade head`
- Downgrade test: `alembic downgrade -1 && alembic upgrade head`
- Empty DB test: migrations on empty schema
- Existing data test: migrations preserve existing data

### Section 8.4 — Compatibility Validation

| Layer | Backward Compatible | Breaking Change Notice |
|-------|-------------------|----------------------|
| API | 2 versions back | 6 months notice |
| Database | N/A (migrations) | Migration plan |
| SDK | 1 version back | 3 months notice |
| Events | Schema registry | 3 months notice |

### Section 8.5 — Feature Flags

- Every new feature behind a feature flag
- Flags are per-tenant in feature matrix
- Flags are deployment-wide in SNDHS/Financial configs
- Flags are removed after stable release + 2 weeks

---

## Article IX: Continuous Evolution

### Section 9.1 — Self Assessment

Monthly self-assessment against:
- Architecture principles
- Quality targets
- Security standards
- Performance budgets
- Documentation completeness

### Section 9.2 — Technical Debt Detection

- Automated detection via static analysis
- Tracked in technical debt register
- 20% of each sprint allocated to debt reduction
- Critical debt escalated to engineering leadership

### Section 9.3 — Architecture Drift Detection

- Automated architecture compliance scanning (Gate Q4)
- Drift reports generated weekly
- Drift remediation plans required within 1 week

### Section 9.4 — Automatic Refactoring Suggestions

- Detected by automated analysis
- Prioritized by risk/reward
- Auto-generate refactoring PRs
- Human review required before merge

### Section 9.5 — Performance Optimization Suggestions

- Automated from production metrics
- Profiling data collected weekly
- Suggestions ranked by impact
- Performance budget enforcement

### Section 9.6 — Security Improvement Suggestions

- Automated from security scan results
- Prioritized by CVSS score
- Remediation SLA: Critical 24h, High 7d, Medium 30d

### Section 9.7 — Dependency Improvement Suggestions

- Automated from Dependabot and safety checks
- Major upgrades require compatibility testing
- Security patches auto-merged with CI validation

---

## Article X: Amendment Process

### Section 10.1 — Constitutional Amendments

1. Propose change as ADR with rationale
2. Engineering review (minimum 3 reviewers)
3. Security review if security-related
4. 7-day comment period
5. Engineering Lead approval
6. Update constitution version
7. Announce to all developers

### Section 10.2 — Emergency Amendments

For security or regulatory emergencies:
1. Engineering Lead approves immediately
2. Document as ADR within 24 hours
3. Ratify within 7 days

### Section 10.3 — Versioning

- This Constitution uses SemVer
- MAJOR: structural/principle changes
- MINOR: new articles/sections
- PATCH: clarifications, non-substantive changes

---

## Signatories

This Constitution is adopted and frozen as the supreme engineering authority
of the GULA National Digital Health Platform.

**Date:** 2026-07-16
**Version:** 1.0.0 — FROZEN

---

## References

- `CLAUDE.md` — Engineering constitution (operational guidance)
- `docs/adr/` — Architecture Decision Records
- `docs/engineering/` — Engineering assessments
- `config/quality-gates/` — Quality gate scripts
- `Makefile` — Build and operations
- `.github/workflows/` — CI/CD pipelines
