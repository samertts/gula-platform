# GULA Platform — Architecture Decision Log

**Version:** 1.0 | **Last Updated:** 2026-07-23

A chronological record of all significant architectural decisions made during the GULA Platform's evolution. This document consolidates all Architecture Decision Records (ADRs) from `docs/adr/`, decisions from `docs/decisions/ARCHITECTURE_DECISIONS.md`, and key implicit decisions that shaped the platform. Entries are numbered ADL-001 through ADL-038.

---

## Table of Contents

- [Decision Log](#decision-log)
- [Detailed Records](#detailed-records)
  - [ADL-001 through ADL-013: Foundational Decisions (2026-01-01)](#adl-001-through-adl-013-foundational-decisions-2026-01-01)
  - [ADL-014 through ADL-015: Governance & Skills (2026-07-06)](#adl-014-through-adl-015-governance--skills-2026-07-06)
  - [ADL-016 through ADL-023: Core Infrastructure (2026-07-08)](#adl-016-through-adl-023-core-infrastructure-2026-07-08)
  - [ADL-024 through ADL-025: Platform Capabilities (2026-07-13)](#adl-024-through-adl-025-platform-capabilities-2026-07-13)
  - [ADL-026 through ADL-036: National Platform (2026-07-15)](#adl-026-through-adl-036-national-platform-2026-07-15)
  - [ADL-037: Platform Constitution (2026-07-16)](#adl-037-platform-constitution-2026-07-16)
  - [ADL-038: Data Preservation Constitution (2026-07-22)](#adl-038-data-preservation-constitution-2026-07-22)

---

## Decision Log

| ID | Date | Title | Status | ADR Ref |
|----|------|-------|--------|---------|
| ADL-001 | 2026-01-01 | Monolith-First Architecture | Accepted | ADR-002 |
| ADL-002 | 2026-01-01 | Multi-Tenant Isolation via lab_id | Accepted | ADR-003 |
| ADL-003 | 2026-01-01 | FastAPI Framework Selection | Accepted | Implicit |
| ADL-004 | 2026-01-01 | PostgreSQL 16 + Redis 7 Stack | Accepted | ADR-005† |
| ADL-005 | 2026-01-01 | Monorepo Consolidation | Accepted | Implicit |
| ADL-006 | 2026-01-01 | API Gateway Pattern (Two-Layer nginx) | Accepted | Implicit |
| ADL-007 | 2026-01-01 | Middleware Stack Ordering | Accepted | Implicit |
| ADL-008 | 2026-01-01 | Health Endpoint Strategy | Accepted | Implicit |
| ADL-009 | 2026-01-01 | Event-Driven Outbox Pattern | Accepted | Implicit |
| ADL-010 | 2026-01-01 | Background Worker Architecture | Accepted | Implicit |
| ADL-011 | 2026-01-01 | Database Migration Immutability Policy | Accepted | Implicit |
| ADL-012 | 2026-01-01 | Feature Flag Architecture | Accepted | Implicit |
| ADL-013 | 2026-01-01 | Microservice Decomposition Strategy | Accepted | Implicit |
| ADL-014 | 2026-07-06 | Engineering Constitution as Root Authority | Accepted | ADR-001 |
| ADL-015 | 2026-07-06 | Skill Platform Architecture | Accepted | ADR-004 |
| ADL-016 | 2026-07-08 | PostgreSQL 16 with Redis 7 (Formalized) | Accepted | ADR-005 |
| ADL-017 | 2026-07-08 | Clinical AI Integration | Accepted | ADR-006 |
| ADL-018 | 2026-07-08 | Device Bridge ASTM/HL7 | Accepted | ADR-007 |
| ADL-019 | 2026-07-08 | Patient Card QR/HMAC System | Accepted | ADR-008 |
| ADL-020 | 2026-07-08 | Self-Healing Infrastructure | Accepted | ADR-009 |
| ADL-021 | 2026-07-08 | SNDHS-lite Government Integration | Accepted | ADR-010 |
| ADL-022 | 2026-07-08 | Edge Agent Architecture | Accepted | Implicit |
| ADL-023 | 2026-07-08 | National Platform Separation (nhop-platform) | Accepted | Implicit |
| ADL-024 | 2026-07-13 | Notification Platform Architecture | Accepted | ADR-011 |
| ADL-025 | 2026-07-13 | Engineering Automation Platform | Accepted | ADR-012 |
| ADL-026 | 2026-07-15 | Production Platform Architecture | Accepted | ADR-013 |
| ADL-027 | 2026-07-15 | Observability Stack Selection | Accepted | ADR-014 |
| ADL-028 | 2026-07-15 | Disaster Recovery Strategy | Accepted | ADR-015 |
| ADL-029 | 2026-07-15 | National Electronic Health Record Platform | Accepted | ADR-016 |
| ADL-030 | 2026-07-15 | National Health Data Platform | Accepted | ADR-017 |
| ADL-031 | 2026-07-15 | National Platform Operations Center | Accepted | ADR-018 |
| ADL-032 | 2026-07-15 | National Digital Health Ecosystem | Accepted | ADR-019 |
| ADL-033 | 2026-07-15 | National Citizen Super App | Accepted | ADR-020 |
| ADL-034 | 2026-07-15 | National Health Intelligence Platform | Accepted | ADR-021 |
| ADL-035 | 2026-07-15 | National Doctor Clinical Workspace | Accepted | ADR-022 |
| ADL-036 | 2026-07-15 | National Laboratory Desktop Professional | Accepted | ADR-023 |
| ADL-037 | 2026-07-16 | Platform Constitution & National Trust Framework | Accepted (Frozen) | ADR-024 |
| ADL-038 | 2026-07-22 | Data Preservation Constitution | Accepted | ADR-025 |

† *Formalized later as ADR-005 but implemented on this date.*

---

## Detailed Records

### ADL-001 through ADL-013: Foundational Decisions (2026-01-01)

---

### ADL-001: Monolith-First Architecture
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Adopt modular monolith as the primary deployment target (`backend/app/`) with well-defined internal modules |
| **Reason** | 3-5 person team, microservices complexity too high, need rapid delivery. Previous microservices approach required 8+ containers |
| **Impact** | Single Docker image, unified CI, 36 route modules and all business logic in one process. `services/` directory holds skeletons for future extraction |
| **ADR Ref** | ADR-002, AD-ARC-001 |
| **Status** | Accepted |

---

### ADL-002: Multi-Tenant Isolation via lab_id
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Shared-database, shared-schema with `lab_id` FK on every tenant-scoped table. Every query must filter by `lab_id = current_user.lab_id` |
| **Reason** | Database-per-tenant creates migration overhead on N databases. Schema-per-tenant complicates connection pooling. Single DB is simpler and sufficient for 50+ labs |
| **Impact** | 17 tenant-scoped models carry `lab_id`. Platform roles bypass filter for cross-lab analytics. Zero data leakage incidents since v1.0 |
| **ADR Ref** | ADR-003, AD-ARC-002 |
| **Status** | Accepted |

---

### ADL-003: FastAPI Framework Selection
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Use FastAPI (ASGI, gunicorn + uvicorn) as the Python web framework for the monolith |
| **Reason** | Async-native for AI inference, Pydantic v2 validation for clinical data integrity, auto-generated OpenAPI docs for mobile/government integration, dependency injection for auth/DB session management, lifespan context manager pattern |
| **Impact** | All 36 route modules use FastAPI `APIRouter`. All models use Pydantic v2 schemas. `Depends(get_current_user)` enforces auth. 2,500 req/s on 4-core droplet |
| **ADR Ref** | AD-ARC-003 |
| **Status** | Accepted |

---

### ADL-004: PostgreSQL 16 + Redis 7 Stack
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | PostgreSQL 16 as primary DB (ACID, Arabic full-text search via ICU, JSONB for flexible schemas). Redis 7 for cache, JWT blacklist, rate limiting counters, session storage, Pub/Sub |
| **Reason** | PostgreSQL provides ACID compliance for patient data, ICU tokenization for Arabic names, Alembic migrations. Redis provides fast in-memory operations for non-durable state. Both are mature, well-supported open source |
| **Impact** | Connection pool formula: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < max_connections`. Defaults: 3 × (6 + 12) = 54. Redis configured via `REDIS_URL` env var. Pub/sub for real-time notifications |
| **ADR Ref** | ADR-005 (formalized 2026-07-08), AD-ARC-003 |
| **Status** | Accepted |

---

### ADL-005: Monorepo Consolidation
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Merge three repositories (`samertts/gula-platform`, `samertts/LabLink-Core`, `samertts/Front-end-`) into a single monorepo |
| **Reason** | Cross-repo changes required 2-3 PRs. CI/CD was inconsistent (GitHub Actions + CircleCI + custom scripts). Documentation fragmented. Atomic cross-cutting changes impossible |
| **Impact** | Single `git clone`, atomic PRs, unified CI (`.github/workflows/ci.yml`), directory-level CODEOWNERS. Repository is ~31,000 commits, ~500MB. Cross-cutting feature time-to-merge dropped from 2 days to 4 hours |
| **ADR Ref** | AD-ARC-004 |
| **Status** | Accepted |

---

### ADL-006: API Gateway Pattern (Two-Layer nginx)
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Two-layer nginx architecture: host nginx (TLS termination via Let's Encrypt) + Docker api-gateway nginx (routes to `gula-backend:8000`). Backend never exposes a public port |
| **Reason** | nginx is battle-tested, well-understood, zero additional databases required. Two layers provide defence-in-depth. Host nginx blocks malicious traffic before it reaches Docker |
| **Impact** | All traffic: Internet → host nginx (TLS) → api-gateway (127.0.0.1:8080) → gula-backend (port 8000). HAProxy alongside nginx for `make scale REPLICAS=N` |
| **ADR Ref** | AD-ARC-005 |
| **Status** | Accepted |

---

### ADL-007: Middleware Stack Ordering
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | 11-layer middleware stack in strict order: MaxBodySize → RequestID → DocsAuth → CORS → RequestTiming → SecurityHeaders → GZip → Readiness → DegradedMode → Kernel → ConcurrencyLimit |
| **Reason** | Ordering is critical: reject oversized payloads early, assign request ID before any logging, guard docs before CORS, capture timing around all business logic, apply security headers, compress responses, block if not ready, shed load if degraded, limit concurrency. Clinical writes are exempt from shedding |
| **Impact** | ~3-5ms overhead per request. All middlewares in `backend/app/main.py`. `_ALWAYS_ALLOWED_PATHS` bypasses readiness/degraded/concurrency middlewares for health endpoints |
| **ADR Ref** | AD-ARC-008 |
| **Status** | Accepted |

---

### ADL-008: Health Endpoint Strategy
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Five health endpoints with specific purposes: `/health` (liveness, <10ms), `/health/live` (Docker healthcheck, <10ms), `/health/ready` (readiness, <500ms), `/health/status` (diagnostic, explains WHY unready), `/health/deep` (full diagnostic with grade/latency/memory, <2000ms) |
| **Reason** | Different consumers need different information. Docker needs simple liveness. api-gateway needs DB connectivity check. Operators need diagnostic info. All five bypass readiness middleware so they work during outages |
| **Impact** | Endpoints in `backend/app/routes/health.py`. Docker healthcheck curls `/health/live` every 30s. `make health-deep` returns GREEN/YELLOW/RED grade with component latencies |
| **ADR Ref** | AD-ARC-009 |
| **Status** | Accepted |

---

### ADL-009: Event-Driven Outbox Pattern
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Transactional outbox pattern: write events to `outbox_events` DB table in same transaction as business operation, background worker polls and dispatches to EventBus at-least-once |
| **Reason** | Events must be committed atomically with business data (no dual-write problem). Celery adds Redis/RabbitMQ hard dependency and operational overhead. CDC (Debezium) is disproportionate for ~1,000 events/day per lab |
| **Impact** | All event-emitting operations use `emit_to_outbox()`. Worker polls every 10s in batches of 50. Handlers must be idempotent. ~50,000 events/day across 50+ labs with 99.99% delivery |
| **ADR Ref** | AD-ARC-007 |
| **Status** | Accepted |

---

### ADL-010: Background Worker Architecture
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Separate worker process (`backend/app/worker.py`, `RUNTIME_MODE=worker`) running same codebase as API. Double-gate (`background_tasks_enabled()`) prevents accidental task launching. API process never runs background tasks |
| **Reason** | Background tasks must not compete with API requests for CPU/memory. Celery rejected (complexity, Redis dependency). In-process asyncio rejected (task interference with request latency) |
| **Impact** | Worker runs: OutboxWorker, RecoveryWorker, adaptive concurrency loop, health alert loop (60s), auto-repair engine (30s). Shared Docker image, different command |
| **ADR Ref** | AD-ARC-014 |
| **Status** | Accepted |

---

### ADL-011: Database Migration Immutability Policy
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Never modify existing migrations. All schema changes = new Alembic revision. `20250322_0000_create_base_schema.py` is immutable. Every migration must be idempotent (use guard functions). New columns nullable or with `server_default` |
| **Reason** | Modifying existing migrations causes `NoSuchTableError` on fresh deploys and silent schema drift. CI migration-gate validates round-trip (`downgrade -1 && upgrade head`) |
| **Impact** | 47+ migration files. CI runs `alembic upgrade head` on fresh postgres:16-alpine. Policy enforced via code review and CI |
| **ADR Ref** | AD-ARC-015 |
| **Status** | Accepted |

---

### ADL-012: Feature Flag Architecture
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Dual feature flag system: per-tenant flags (`feature_flags.py`) in DB with subscription tier matrix (3 tiers × 16 features), and deployment-wide flags (`sndhs_flags.py`) via environment variables |
| **Reason** | Single env var per feature doesn't scale (15+ vars per deployment). LaunchDarkly adds external dependency and network latency. Different labs need different feature sets on the same deployment |
| **Impact** | `SNDHS_ENABLE_VISITS`, `SNDHS_ENABLE_NATIONAL_ID`, `ENABLE_FINANCIAL_ENGINE`, `ENABLE_ADS` all default to false. `RUNTIME_MODE` controls execution context (api/worker/test/cli) |
| **ADR Ref** | AD-ARC-013 |
| **Status** | Accepted |

---

### ADL-013: Microservice Decomposition Strategy
| Field | Value |
|-------|-------|
| **Date** | 2026-01-01 |
| **Decision** | Domain-event-driven extraction using Strangler Fig pattern. A domain graduates from monolith when it meets ≥2 criteria: independent scaling, deploy cadence, team ownership, technology divergence |
| **Reason** | Premature extraction adds complexity without benefit. Delayed extraction can cause resource pressure. Objective criteria prevent both extremes. The outbox pattern and EventBus already support eventual decomposition |
| **Impact** | `services/` directory contains 8 skeletons built via CI matrix. No domains extracted yet. Quarterly architecture review evaluates extraction criteria |
| **ADR Ref** | AD-ARC-006 |
| **Status** | Accepted |

---

### ADL-014 through ADL-015: Governance & Skills (2026-07-06)

---

### ADL-014: Engineering Constitution as Root Authority
| Field | Value |
|-------|-------|
| **Date** | 2026-07-06 |
| **Decision** | Adopt the Engineering Constitution as the single root authority for all engineering decisions — core values, decision-making framework, architecture governance, quality standards |
| **Reason** | No single authoritative document existed. Multiple undocumented conventions led to inconsistent implementations across repositories |
| **Impact** | All ADRs, code reviews, and architectural decisions must be consistent with the Constitution. Section 7 establishes ADR process |
| **ADR Ref** | ADR-001 |
| **Status** | Accepted |

---

### ADL-015: Skill Platform Architecture
| Field | Value |
|-------|-------|
| **Date** | 2026-07-06 |
| **Decision** | Skill-based plugin architecture: independent, self-contained modules loaded at runtime by the Kernel with declarative permissions, resource limits, and event bus communication |
| **Reason** | AI capabilities and automation must be extensible without modifying core platform code. Hardcoded AI features are not extensible. Per-skill microservices have too much overhead |
| **Impact** | Skills in `skills/` directory. Kernel manages lifecycle. Event bus for inter-skill communication |
| **ADR Ref** | ADR-004 |
| **Status** | Accepted |

---

### ADL-016 through ADL-023: Core Infrastructure (2026-07-08)

---

### ADL-016: PostgreSQL 16 with Redis 7 (Formalized)
| Field | Value |
|-------|-------|
| **Date** | 2026-07-08 |
| **Decision** | Formal ratification of the PostgreSQL 16 + Redis 7 stack decision first implemented on 2026-01-01 |
| **Reason** | Formal documentation of the stack with explicit alternatives analysis and trade-off documentation |
| **Impact** | Reaffirms existing architecture. Documented in ADR-005 with detailed alternatives (MySQL 8, MariaDB, MongoDB, CockroachDB, Memcached, Valkey, Dragonfly) |
| **ADR Ref** | ADR-005 |
| **Status** | Accepted |

---

### ADL-017: Clinical AI Integration
| Field | Value |
|-------|-------|
| **Date** | 2026-07-08 |
| **Decision** | AI through dedicated monolith module (`backend/app/ai/`) communicating with external services (Ollama, OpenAI-compatible) via abstraction layer. Feature flag gated. All AI operations async and non-blocking |
| **Reason** | AI features (result interpretation, anomaly detection, trend analysis, predictive analytics) must integrate without compromising stability. Async prevents AI latency (2-30s) from blocking responses |
| **Impact** | `backend/app/ai/` for monolith-side integration. `ai/` at root for independent AI services. Abstraction layer supports multiple providers |
| **ADR Ref** | ADR-006 |
| **Status** | Accepted |

---

### ADL-018: Device Bridge ASTM/HL7
| Field | Value |
|-------|-------|
| **Date** | 2026-07-08 |
| **Decision** | Dedicated device bridge service (`services/device_bridge/`) as separate Docker container. Supports ASTM E1381/1382 and HL7 v2.x. Normalises instrument formats to standard schema. Authenticated HTTP to backend via `gula_client.py` |
| **Reason** | Lab instruments use vendor-specific protocols that must be handled by a dedicated process. Direct integration in monolith would couple instrument parsing to API logic |
| **Impact** | `docker compose --profile device-bridge up device-bridge`. Supports Sysmex, Roche, Mindray, generic devices. Configurable device profiles |
| **ADR Ref** | ADR-007 |
| **Status** | Accepted |

---

### ADL-019: Patient Card QR/HMAC System
| Field | Value |
|-------|-------|
| **Date** | 2026-07-08 |
| **Decision** | HMAC-SHA256 signed QR tokens (`{patient_id}:{lab_id}:{expiry}:{signature}`) with Arabic-first printable HTML. Key (`NID_HMAC_KEY`) from env, no hardcoded fallback. Verification before data reveal |
| **Reason** | Patients need portable, verifiable offline records. HMAC simpler than JWT for this use case. QR codes work on any smartphone. Offline verification possible for token, online for full data |
| **Impact** | Three routes: generate, verify, scan. HMAC verification is non-negotiable security invariant. Rate-limited scan endpoint |
| **ADR Ref** | ADR-008, AD-ARC-010 |
| **Status** | Accepted |

---

### ADL-020: Self-Healing Infrastructure
| Field | Value |
|-------|-------|
| **Date** | 2026-07-08 |
| **Decision** | Three-layer self-healing: (1) Circuit breaker (`self_healing.py`) — isolates failing DB/Redis, DegradedModeMiddleware rejects writes during open circuit. (2) Auto-repair engine (`auto_repair.py`) — GC, pool recycle, reconnects. (3) Adaptive concurrency — halves `_MAX_CONCURRENT` on slow DB, restores after fast readings |
| **Reason** | Uptime and data integrity are critical for medical labs. Failures should not cause complete unavailability. Circuit breaker prevents cascading failures |
| **Impact** | Degraded mode allows reads during DB issues. `DegradedModeMiddleware` in middleware stack (layer 9). Health alert watchdog scores GREEN/YELLOW/RED every 60s |
| **ADR Ref** | ADR-009 |
| **Status** | Accepted |

---

### ADL-021: SNDHS-lite Government Integration
| Field | Value |
|-------|-------|
| **Date** | 2026-07-08 |
| **Decision** | Phased SNDHS integration with feature flags. Phase 1: encrypted `patients.national_id` (AES-256), `patients.sndhs_health_id`, `visits` table, `lab_orders.visit_id`, enhanced audit log v2. Dual-read pattern: all code handles `None` for pre-backfill rows |
| **Reason** | Iraqi Ministry of Health requires national health data system integration. Phased approach with feature flags enables safe rollout. Encrypted storage for national IDs |
| **Impact** | Migration files `20260505_0001` through `20260505_0006`. Backfill script `scripts/sndhs_phase1_backfill.py`. Rollback scripts available. Flags default to `false` |
| **ADR Ref** | ADR-010 |
| **Status** | Accepted |

---

### ADL-022: Edge Agent Architecture
| Field | Value |
|-------|-------|
| **Date** | 2026-07-08 |
| **Decision** | Full offline edge agent (`edge_agent/`) as standalone Docker container with local SQLite, ASTM/HL7 device bridge integration, bidirectional sync engine, last-writer-wins conflict resolution, deferred MPI matching |
| **Reason** | Iraqi labs have unreliable internet. Remote desktop/VPN impossible offline. Read-only offline blocks critical work. PWA with IndexedDB insufficient for complex lab workflows |
| **Impact** | Edge agent modules: config, governance, identity, maintenance, policy, registry, scheduler, telemetry, trust. Not yet deployed to production |
| **ADR Ref** | AD-ARC-011 |
| **Status** | Accepted |

---

### ADL-023: National Platform Separation (nhop-platform)
| Field | Value |
|-------|-------|
| **Date** | 2026-07-08 |
| **Decision** | Separate NHOP platform (`nhop-platform/`) as independent FastAPI app on port 8100 with own DB, JWT realm, and deployment lifecycle. API bridge for cross-platform communication |
| **Reason** | National oversight has fundamentally different compliance requirements (export controls, data retention). Commingling creates security and compliance conflicts. GULA owns per-lab LIMS; NHOP owns national citizen registry |
| **Impact** | Two independent platforms behind same api-gateway. SNDHS integration defines the interface. Different deployment cadences (NHOP changes are government-gated) |
| **ADR Ref** | AD-ARC-012 |
| **Status** | Accepted |

---

### ADL-024 through ADL-025: Platform Capabilities (2026-07-13)

---

### ADL-024: Notification Platform Architecture
| Field | Value |
|-------|-------|
| **Date** | 2026-07-13 |
| **Decision** | Multi-channel notification platform: template engine (`shared/notifications/template.py`), sender layer (`shared/notifications/sender.py`) with graceful degradation, service layer (`backend/app/notifications/service.py`) with circuit breaker and audit, Telegram gateway via gateway pattern |
| **Reason** | Multiple channels (email, SMS, push, WhatsApp, Telegram) with different API requirements. External notification service rejected due to cost and Iraqi data sovereignty requirements |
| **Impact** | Channel-agnostic API for business logic. Graceful degradation when channels unavailable. Circuit breaker protection against failing notification APIs |
| **ADR Ref** | ADR-011 |
| **Status** | Accepted |

---

### ADL-025: Engineering Automation Platform
| Field | Value |
|-------|-------|
| **Date** | 2026-07-13 |
| **Decision** | Engineering Automation Platform under `backend/app/engineering/` with generators (modules, CRUD, DTOs, repositories, REST APIs, CQRS), validators (architecture compliance), intelligence (knowledge graph, dependency graph), quality gates, CI/CD generation, and SBOM security |
| **Reason** | Repetitive engineering tasks (new modules, CRUD endpoints, tests, docs) are error-prone and inconsistent when done manually |
| **Impact** | Consistent code structure. Faster development of new modules. Architecture compliance checks automated |
| **ADR Ref** | ADR-012 |
| **Status** | Accepted |

---

### ADL-026 through ADL-036: National Platform (2026-07-15)

---

### ADL-026: Production Platform Architecture
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Evolve from Docker Compose prototype to production-grade architecture: 99.99% availability, multi-region DR (RPO 5s, RTO 5min), zero-downtime deployments (blue-green + canary), full observability, enterprise security |
| **Reason** | Current Docker Compose deployment insufficient for national-scale healthcare platform serving medical labs |
| **Impact** | Multi-region active-passive topology. Kubernetes (k8s/) overlays for orchestration. DigitalOcean droplet as primary, with expansion path |
| **ADR Ref** | ADR-013 |
| **Status** | Accepted |

---

### ADL-027: Observability Stack Selection
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Open-source observability stack: Prometheus + Loki + Tempo for metrics/logs/traces, Grafana for dashboards, Alertmanager for alerting. Promtail for log shipping, OpenTelemetry SDK for instrumentation |
| **Reason** | Open source avoids vendor lock-in. CNCF ecosystem provides integration. Prometheus is standard for metrics. Loki is cost-effective for logs. Tempo for distributed tracing as microservices emerge |
| **Impact** | `config/prometheus/`, `config/grafana/` with provisioned dashboards. Alerting routes to Slack/Telegram. Metrics token for access control |
| **ADR Ref** | ADR-014 |
| **Status** | Accepted |

---

### ADL-028: Disaster Recovery Strategy
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Multi-region active-passive DR: primary in Iraqi data center, standby in secondary region. PostgreSQL streaming replication (synchronous within region, asynchronous across regions). RPO ≤ 5s, RTO ≤ 5min. Automated failover with manual split-brain prevention |
| **Reason** | Regional outage or disaster must not prevent labs from processing results. 99.99% availability requires multi-region. 5-second RPO critical for patient data integrity |
| **Impact** | Backup strategy: hourly pg_dump, daily encrypted to S3-compatible storage. Restore drills monthly. Full runbook in `docs/sndhs/phase1/RUNBOOK.md` |
| **ADR Ref** | ADR-015 |
| **Status** | Accepted |

---

### ADL-029: National Electronic Health Record Platform
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Evolve GULA into a national EHR platform: single longitudinal record per citizen spanning all healthcare encounters. FHIR R4 compliance. Zero duplication of existing GULA clinical data. Role-based access with patient consent |
| **Reason** | Patient health data is fragmented across LIS, hospital systems, physician records, and paper files. No unified EHR exists for Iraqi citizens |
| **Impact** | Scalable to ~45M citizens. Integrates lab results, visits, hospitalizations, prescriptions, immunizations. FHIR R4 for interoperability |
| **ADR Ref** | ADR-016 |
| **Status** | Accepted |

---

### ADL-030: National Health Data Platform
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Unified data backbone: data lake + enterprise warehouse + MDM + event store + feature store. Data governance with lineage, cataloging, and quality monitoring |
| **Reason** | Growing health data volume requires unified platform for analytics, AI, reporting, and interoperability across all subsystems |
| **Impact** | AI-ready data pipelines. Compliance with Iraqi data sovereignty and privacy regulations |
| **ADR Ref** | ADR-017 |
| **Status** | Accepted |

---

### ADL-031: National Platform Operations Center
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Centralized operations center: unified health/performance/alerts dashboard, release management with approval gates, incident management with severity/escalation, environment management, change management with blast radius control, 24/7 alerting, compliance reporting |
| **Reason** | Expanding from single-lab SaaS to national healthcare platform makes operational complexity unmanageable without centralized tooling |
| **Impact** | Multi-environment management (sandbox/staging/production). On-call scheduling with escalation. Audit trail for all operational changes |
| **ADR Ref** | ADR-018 |
| **Status** | Accepted |

---

### ADL-032: National Digital Health Ecosystem
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Protocol-agnostic integration platform supporting REST, FHIR, HL7 v2, ASTM, SOAP. Partner management with onboarding/credentialing. API gateway with auth/routing/throttling. Schema registry. Event-driven publish/subscribe |
| **Reason** | Point-to-point integrations with government registries, HIS, pharmacy, insurance, and international networks are fragile and unscalable |
| **Impact** | Integration monitoring with error tracking. Synchronous and asynchronous integration patterns. Ecosystem extends beyond lab management |
| **ADR Ref** | ADR-019 |
| **Status** | Accepted |

---

### ADL-033: National Citizen Super App
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Single mobile/web application for citizens: longitudinal health record, lab results, appointments, prescriptions, immunizations, secure messaging with providers, push notifications, offline support |
| **Reason** | Citizens interact with healthcare through fragmented channels (paper records, different hospital systems, unconnected mobile apps). No single app provides complete health information access |
| **Impact** | Multi-platform (Android, iOS, PWA). Offline-first for low-connectivity regions. Arabic-first UI. All data flows through GULA backend API |
| **ADR Ref** | ADR-020 |
| **Status** | Accepted |

---

### ADL-034: National Health Intelligence Platform
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Centralized AI/ML platform: clinical AI (diagnostic support, result interpretation), lab AI (QC, workflow optimization), hospital AI (resource optimization, readmission risk), public health AI (disease surveillance, outbreak detection), LLM gateway with safety filters, model lifecycle management |
| **Reason** | AI/ML capabilities are fragmented across the platform. Unified intelligence platform ensures consistent AI capabilities across all healthcare applications |
| **Impact** | LLM gateway with prompt guards and usage governance. Model training/evaluation/deployment/monitoring lifecycle. Governance framework for clinical AI safety |
| **ADR Ref** | ADR-021 |
| **Status** | Accepted |

---

### ADL-035: National Doctor Clinical Workspace
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Unified clinical workspace for physicians: patient dashboard, longitudinal record, clinical orders (lab, imaging, medications, referrals), clinical documentation, result review with AI interpretation, integration with all national platform services |
| **Reason** | Physicians piece together patient info from multiple sources — fragmented workflow reduces efficiency and increases error risk |
| **Impact** | End-to-end patient care management. Trend visualization for lab results. AI-powered interpretation via ADR-021 |
| **ADR Ref** | ADR-022 |
| **Status** | Accepted |

---

### ADL-036: National Laboratory Desktop Professional
| Field | Value |
|-------|-------|
| **Date** | 2026-07-15 |
| **Decision** | Single approved laboratory desktop application: ASTM/HL7 native instrument integration, barcode/RFID sample tracking, rapid data entry for high-throughput workflows, offline-first with automatic sync, FHIR-compatible, Windows native |
| **Reason** | Iraqi labs use inconsistent LIS interfaces. Web UI alone doesn't meet high-throughput lab needs: real-time instrument integration, offline resilience, desktop-native performance |
| **Impact** | Offline-first ensures operation during internet outages. Automatic sync when connectivity restored. Windows native (standard OS in Iraqi labs) |
| **ADR Ref** | ADR-023 |
| **Status** | Accepted |

---

### ADL-037: Platform Constitution (2026-07-16)

---

### ADL-037: Platform Constitution & National Trust Framework
| Field | Value |
|-------|-------|
| **Date** | 2026-07-16 |
| **Decision** | Freeze the Platform Constitution as a formal governance document defining architectural boundaries, compliance requirements, and trust framework. Establishes Platform Constitution as authoritative governing document at the architecture level |
| **Reason** | Platform has grown to 47+ route modules, 31+ services, 19 ORM models, 43 migrations, 8 microservices. Governance must be formalized to maintain architectural integrity |
| **Impact** | Sets immutable rules for platform evolution. Defines national trust framework for cross-platform security. Frozen status means no further modifications without full architecture committee review |
| **ADR Ref** | ADR-024 |
| **Status** | Accepted (Frozen) |

---

### ADL-038: Data Preservation Constitution (2026-07-22)

---

### ADL-038: Data Preservation Constitution
| Field | Value |
|-------|-------|
| **Date** | 2026-07-22 |
| **Decision** | Adopt a permanent, non-negotiable Data Preservation Constitution with automated quality gates (data-preservation-gate in CI) enforcing: never modify existing migrations, all migrations must be idempotent with guard functions, downgrade paths required, no destructive schema changes without explicit approval |
| **Reason** | Patient data integrity is critical. Migration drift, lack of rollback enforcement, and inconsistent policies across CLAUDE.md and ad-hoc scripts create data loss risk. AI-assisted development may introduce violations |
| **Impact** | CI pipeline includes `data-preservation-gate` job (exit code 0=pass, 1=warning, 2=block merge). Complements ADR-015 (Disaster Recovery) and ADL-011 (Migration Policy) |
| **ADR Ref** | ADR-025 |
| **Status** | Accepted |

---

## Cross-Reference Matrix

| Topic | ADL Entry | ADR Ref | Decision Doc |
|-------|-----------|---------|--------------|
| Monolith-First | ADL-001 | ADR-002 | AD-ARC-001 |
| Multi-Tenant Isolation | ADL-002 | ADR-003 | AD-ARC-002 |
| FastAPI Framework | ADL-003 | — | AD-ARC-003 |
| PostgreSQL + Redis | ADL-004, ADL-016 | ADR-005 | — |
| Monorepo | ADL-005 | — | AD-ARC-004 |
| API Gateway | ADL-006 | — | AD-ARC-005 |
| Middleware Stack | ADL-007 | — | AD-ARC-008 |
| Health Endpoints | ADL-008 | — | AD-ARC-009 |
| Outbox Pattern | ADL-009 | — | AD-ARC-007 |
| Worker Architecture | ADL-010 | — | AD-ARC-014 |
| Migration Policy | ADL-011 | — | AD-ARC-015 |
| Feature Flags | ADL-012 | — | AD-ARC-013 |
| Microservice Strategy | ADL-013 | — | AD-ARC-006 |
| Engineering Constitution | ADL-014 | ADR-001 | — |
| Skill Platform | ADL-015 | ADR-004 | — |
| AI Integration | ADL-017 | ADR-006 | — |
| Device Bridge | ADL-018 | ADR-007 | — |
| Patient Card | ADL-019 | ADR-008 | AD-ARC-010 |
| Self-Healing | ADL-020 | ADR-009 | — |
| SNDHS Integration | ADL-021 | ADR-010 | — |
| Edge Agent | ADL-022 | — | AD-ARC-011 |
| NHOP Separation | ADL-023 | — | AD-ARC-012 |
| Notifications | ADL-024 | ADR-011 | — |
| Engineering Automation | ADL-025 | ADR-012 | — |
| Production Platform | ADL-026 | ADR-013 | — |
| Observability | ADL-027 | ADR-014 | — |
| Disaster Recovery | ADL-028 | ADR-015 | — |
| National EHR | ADL-029 | ADR-016 | — |
| Health Data Platform | ADL-030 | ADR-017 | — |
| Operations Center | ADL-031 | ADR-018 | — |
| Health Ecosystem | ADL-032 | ADR-019 | — |
| Citizen Super App | ADL-033 | ADR-020 | — |
| Health Intelligence | ADL-034 | ADR-021 | — |
| Doctor Workspace | ADL-035 | ADR-022 | — |
| Lab Desktop | ADL-036 | ADR-023 | — |
| Platform Constitution | ADL-037 | ADR-024 | — |
| Data Preservation | ADL-038 | ADR-025 | — |

---

## Related Documents

- `docs/adr/README.md` — ADR index and process
- `docs/adr/ADR-001-engineering-constitution.md` through `ADR-025-*` — Individual ADRs
- `docs/decisions/ARCHITECTURE_DECISIONS.md` — Detailed architecture decisions (AD-ARC-001 through AD-ARC-015)
- `ARCHITECTURE.md` — System architecture overview
- `CLAUDE.md` — Engineering guide with architectural rules
- `docs/architecture/CANONICAL_ARCHITECTURE.md` — Canonical architecture reference
