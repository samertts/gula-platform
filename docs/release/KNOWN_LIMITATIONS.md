# GULA Platform — Known Limitations

**Version:** 1.0 | **Applies to:** v2.5.0
**Last Updated:** 2026-07-23

## Table of Contents

- [1. Architectural Limitations](#1-architectural-limitations)
- [2. Feature Limitations](#2-feature-limitations)
- [3. Operational Limitations](#3-operational-limitations)
- [4. Technical Debt](#4-technical-debt)
- [5. Test Limitations](#5-test-limitations)
- [6. Documentation Limitations](#6-documentation-limitations)
- [7. Related Documents](#7-related-documents)

---

## 1. Architectural Limitations

| Limitation | Impact | Mitigation | Target Resolution |
|---|---|---|---|
| Single-process FastAPI monolith | Vertical scaling bound at per-worker throughput; horizontal scaling requires HAProxy | `make scale REPLICAS=N` via HAProxy + docker-compose scale | Q4 2026 |
| No database read replicas in production | All queries (including analytics) hit primary, competing with OLTP | `READ_REPLICA_URL` config exists in `config.py`; PgBouncer required before use | Q3 2026 |
| In-process event bus | No cross-service event delivery; events lost on process restart | Kernel event bus is in-memory only; NATS/event broker planned | Q1 2027 |
| Polling-based outbox (10s interval) | Event delivery latency up to 10s; no streaming semantics | Outbox worker polls every 10s; stream-based outbox planned | Q4 2026 |
| Database-per-deployment (shared schema across tenants) | Noisy-neighbor risk; large-lab workloads can impact smaller tenants | Schema-per-tenant for large labs planned | Q2 2027 |
| No Kafka/RabbitMQ in production stack | Event volume ceiling estimated at ~1M/day; no replay/retention beyond outbox | Full infra compose (`docker-compose.full.yml`) includes RabbitMQ; Kafka planned | Q1 2027 |
| No PgBouncer or connection pooler | Connection pool limited to `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW)` = 54 default; spike above causes errors | Pool sizing formula documented in `database.py`; PgBouncer deployment recommended before scaling | Q4 2026 |
| Microservices tree (`services/`) is not the deployment target | 7 service stubs create confusion about architecture direction (TD-001) | Stubs documented but not removed; no business logic should be committed there | Q3 2026 |
| Backend dual structure (`backend/services/` and `backend/core/` experimental stubs) | Developers must know which `core/` or `services/` directory is active (TD-002) | CLAUDE.md warns to avoid; cleanup planned | Q4 2026 |
| 47 Alembic migration revisions | Slow `alembic upgrade head`; complex dependency chain; CI migration-gate slowdown (TD-003) | Squash migrations periodically; next squash target at 50 revisions | Q4 2026 |

## 2. Feature Limitations

| Feature | Limitation | Workaround | Priority |
|---|---|---|---|
| **FHIR R4** | Read-only for most resources; native data model exists but write path is via native API only | Use GULA native API for all mutations | P2 |
| **National ID (SNDHS)** | Phase 1 only — `patients.national_id` and `sndhs_health_id` may be `None` for pre-backfill rows; no full SNDHS integration | Dual-read rule: all code must handle `None` gracefully; adapter mode defaults to `stub` | P1 |
| **Financial Engine** | Phase A schema only — routes and services deferred to Phase B+; `ENABLE_FINANCIAL_ENGINE` and `ENABLE_ADS` default off | No workaround; no business logic should be added without explicit approval | P3 |
| **AI Integration** | Gemini-only for cloud AI provider; no GPU-backed serving; Ollama for local/edge only | Rules-based fallback when no AI key is configured; Groq API key optional | P2 |
| **Mobile Apps** | Android/iOS native apps in development; only PWA available for mobile | PWA is fully offline-capable as interim solution | P1 |
| **OAuth2 / OIDC** | Basic OAuth2 provider with no OIDC support; no social login | Direct JWT authentication with httpOnly cookies | P2 |
| **External Government Adapters** | All adapters (NID, Insurance, Residency, Cloudflare) default to `stub` mode; live endpoints require uncommitted credentials | Set `GULA_ADAPTER_MODE` env vars and configure API URLs for live mode | P2 |
| **Redis** | Optional — in-memory fallback is not shared across workers, limiting cross-process session invalidation | Set `REDIS_URL` for multi-worker rate limiting and session management | P2 |
| **Arabic i18n** | Platform is Arabic-first but translations have gaps: clinical terms may not match Iraqi usage, RTL edge cases, machine-translated content needs human review (TD-010) | P1 item; translation audit and clinical review in progress | Q3 2026 |
| **API Documentation** | `/docs`, `/redoc`, `/openapi.json` guarded in production behind `ENABLE_API_DOCS` (default false) | Set `ENABLE_API_DOCS=true` for government testers | P3 |
| **Firebase** | Fully removed except `FCM_SERVER_KEY` for optional push notifications; no Firebase data dependency remains | Push notifications optional; PWA works without FCM | P3 |
| **Device Bridge Protocols** | Only ASTM and HL7 supported; no DICOM, LIS2-A, or POCT1-A support (TD-008) | Driver development per new protocol | Q1 2027 |
| **Multi-Platform Frontend** | Three separate frontend apps (`frontend/`, `frontend-v2/`, `client/`) with different stacks — 3x maintenance burden (TD-007) | Consolidation planned; frontend-v2 is the primary target | Q2 2027 |

## 3. Operational Limitations

| Limitation | Impact | Mitigation |
|---|---|---|
| Single-region deployment | No disaster recovery if region fails; RPO/RTO not measured | Backup/restore only (`make backup`); multi-region active-active planned |
| No PgBouncer in production | Connection pool is limited to ~54 concurrent DB connections; spikes cause `too many clients` errors | Pool sizing formula documented (`WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW)`); PgBouncer deployment recommended |
| No read replicas configured | Analytics and reporting queries compete with transactional OLTP workload | Scheduled analytics window; `READ_REPLICA_URL` env var available but not wired |
| No Kubernetes in production | Manual scaling via `docker-compose scale`; no auto-scaling, no service mesh | K8s manifests exist in `k8s/` but not primary deployment target |
| Docker Compose as primary deployment | No built-in rolling updates, health-gated deployments, or secret rotation | Blue-green and canary workflows exist in CI but require manual setup |
| Adaptive concurrency is reactive | Halves `_MAX_CONCURRENT` only after detecting 2 slow DB readings; oscillates degrade→recover (TD-004) | Predictive concurrency with moving-average response times planned |
| Circuit breaker gaps | DB partial availability, cascading recovery thundering herd, in-memory state (lost on restart), no manual override API (TD-005) | Graduated circuit states + persistence + admin API planned |
| 647 open technical debt items | 1644 estimated remediation hours; 4 P0 blockers, 13 P1 critical items | See full registry at `docs/technical-debt/REGISTRY.md` |
| Adapter mode defaults to stub | All government integrations (NID, insurance, residency) return mock data until explicitly configured | Set adapter mode env vars and configure live endpoints |

## 4. Technical Debt

| Debt | Module | Impact | Effort to Fix |
|---|---|---|---|
| F821 undefined-name errors resolved; **898+ ruff style/naming warnings remaining** | All backend modules | Code quality, naming consistency — no runtime impact | Medium |
| **220 B904 exception-chaining warnings** require human review for each | All backend modules | Error clarity improvement — no runtime impact | Low |
| **1413 mypy strict type errors** across codebase | Entire `backend/app/` | No static type checking enforcement; potential runtime type errors | High (10-15 days phased) |
| Module-level circular import: `database.py` ↔ `self_healing.py` | `core/` (TD-3282, P1) | Mitigated by lazy imports; causes import ordering constraints | Low (8 hrs) |
| Test coverage at ~55% — below 60% threshold (TD-3902, P2) | Routes (~35%), Services (~30%) | Regression risk in critical paths (orders, results, samples) | Medium (5-7 days) |
| Fixture isolation failures causing 268 test errors (D-001) | `conftest.py` across test suite | CI reliability degradation; developer trust in test suite | Critical (2-3 days) |
| Pydantic V2 deprecation — `class Config` pattern deprecated | Various model files | Non-functional warnings; future compatibility risk | Low (1-2 days) |
| SNDHS dual-read complexity: `national_id` and `sndhs_health_id` may be None | Patients model, SNDHS code | Additional `None`-check boilerplate; intentional design until full backfill | N/A (intentional) |
| 172/173 kernel tests passing (1 pre-existing flaky isolation test) | `test_kernel/` | One flaky test reduces CI signal reliability | Low |
| Cross-domain leakage: 365 items across bounded contexts | 25+ platform modules | Architecture boundary violations; domain coupling | High (1095 hours estimated) |
| Large files/functions: 67 items identified | Various | Maintainability and readability concerns | Medium (134 hours) |
| Documentation gaps: 60 items | `docs/` | Missing ADRs, module READMEs, deployment runbooks | Low (60 hours) |

## 5. Test Limitations

| Gap | Impact | Coverage |
|---|---|---|
| No E2E tests for all clinical workflows | Regression risk for multi-step flows (order → sample → result → report) | Unit/integration only |
| No automated performance regression tests | Scaling characteristics unknown before production incidents | Basic stress tests exist (`test_stress.py`) |
| No property-based testing for domain logic | Order state machine, clinical calculations not fuzz-tested | Manual edge case tests only |
| Limited UI tests (Playwright) | Frontend regression risk for citizen and doctor portals | 28 E2E tests across 7 suites for frontend-v2 |
| Migration tests only cover upgrade/downgrade | Data correctness across migrations not verified | `alembic upgrade/downgrade -1` round-trip in CI |
| 1 pre-existing flaky test in kernel test suite | Reduces CI signal reliability; occasional false failures | 172/173 kernel tests passing |
| Security regression testing limited | `test_security.py` covers invariants but may miss new attack vectors | Bandit and safety scans in CI pipeline |

## 6. Documentation Limitations

| Gap | Status |
|---|---|
| No user manual for lab technicians | Missing |
| No integration cookbook for government partners | Missing |
| No admin guide for hospital IT staff | Missing |
| No Arabic documentation (despite Arabic-first platform) | Missing |
| No deployment runbooks per environment | Missing |
| No disaster recovery procedure (RPO/RTO, backup restoration) | Missing |
| No developer onboarding guide | Missing |
| No clinical workflow documentation | Missing |
| No performance baseline (p50/p95/p99 per endpoint) | Missing |
| No security architecture / threat model document | Missing |
| No formal testing strategy document | Missing |
| API reference exists (OpenAPI) but lacks usage examples, error codes | Incomplete |
| No per-module README files (C10 constitution contradiction) | Missing |
| 60 documentation gap items in technical debt registry | Open |

## 7. Related Documents

- [Technical Debt Registry](../technical-debt/REGISTRY.md) — 647 items, 1644 hours estimated
- [Technical Debt Register](../engineering/TECHNICAL_DEBT_REGISTER.md) — 10 prioritized items
- [Technical Debt Analysis](../engineering/TECHNICAL-DEBT.md) — 10 scored debt items
- [CHANGELOG.md](../../CHANGELOG.md) — Release history and known issues
- [Risk Register](../engineering/RISK-REGISTER.md) — Operational and security risks
- [Quality Gates](../engineering/QUALITY-GATES.md) — Quality gate definitions and thresholds
- [CLAUDE.md](../../CLAUDE.md) — Engineering constitution and autonomous task boundaries
