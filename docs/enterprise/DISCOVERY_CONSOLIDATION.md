# GULA Platform — Discovery Consolidation (Canonical Inventory)

**Date:** 2026-07-18
**Classification:** Confidential — Technical Review Board
**Source:** 17 discovery reports synthesized into single canonical reference

---

## 1. Platform Identity

- **Product:** GULA Platform (منصة غولا الصحية) — Medical LIS/LIMS + National Health Platform
- **Deployment:** SaaS Multi-Tenant + On-Premise Edge
- **Market:** Iraq (Ministry of Health, private labs); MENA digital health ~$23.4B (2025)
- **Language:** Arabic-first, English bilingual
- **Version:** config.py = 2.1.0, CHANGELOG.md = 2.3.2, pyproject.toml = 2.2.0, Helm appVersion = 2.1.0 (divergence)
- **Git:** 467+ commits, 3,709+ files, 1,421+ directories
- **Code Distribution:** Python 60.5%, TypeScript/JavaScript 25%, Shell/YAML 10%, Other 4.5%
- **Total LOC (Python backend):** ~120,000+ across `app/`
- **Pricing:** SaaS tiers $100–$10,000+/mo
- **Target labs:** ~1,200 total in Iraq
- **Regulatory:** SNDHS-lite (Iraqi National Health Data System), MoI NID verification, National Health Insurance (Law No.22)

---

## 2. Repository Map

- **Type:** Monorepo (3 formerly independent repos consolidated)
- **Root directories:**
  - `.github/` — 6 CI/CD workflow files (ci.yml 644 lines, deploy, blue-green, canary, auto-rollback, quality-gate)
  - `backend/` — Core monolith (~120K LOC, 53+ routes, 60+ models, 34+ services, 48 migrations, 124 tests)
  - `services/` — 10 subdirectories (device_bridge=mature, ai=functional, autonomous_manager=functional, 6 stubs)
  - `frontend-v2/` — React + Firebase (citizen/doctor/lab/ministry portals)
  - `client/` — tRPC + React SPA
  - `frontend/` — Static HTML PWA
  - `hospital_desktop/` — Desktop application
  - `shared/` — Canonical library: auth, rbac, security, audit, circuit_breaker, messaging
  - `ai/` — Top-level AI modules
  - `scripts/` — 35+ operational scripts
  - `edge_agent/` — Edge computing agent
  - `nhop-platform/` — National Health Oversight (separate FastAPI)
  - `cli/` — Developer CLI v2.1.0
  - `server/` — Express.js gateway
  - `config/` — ~93 infrastructure config files (nginx, prometheus, grafana, haproxy, postgres, redis, rabbitmq, vault, tempo, loki, security, siem, quality-gates)
  - `k8s/` — Kubernetes manifests (base + overlays: dev, prod, region-eu, region-me)
  - `terraform/` — AWS IaC, ~65 files, 12 modules, 5 environments
  - `helm/` — Helm chart v1.0.0, 38 templates, 9 dependencies
  - `docs/` — ~200+ files (24 ADRs, 65 sovereign docs, 17 SNDHS, 7 runbooks, 9 production guides)
  - `digitalocean/`, `cloudflare/`, `supabase/` — PaaS configs
- **Root files:** docker-compose.yml (7 services), docker-compose.full.yml (25+, 821 lines), docker-compose.scale.yml, Dockerfile, Makefile (70+ targets, 522 lines), nginx.conf (151 lines), deploy.sh (351 lines), .env.example (364 lines)

---

## 3. Architecture Map

### Request Lifecycle
- Internet → Host Nginx (TLS 1.2/1.3, WAF ModSec, rate limit) → API Gateway Nginx (127.0.0.1:8080) → gula-backend FastAPI:8000 (gunicorn + uvicorn)

### Middleware Stack (11 layers, ordered)
1. MaxBodySizeMiddleware — 413 >10MB
2. RequestIDMiddleware — UUID X-Request-ID + log ctx
3. DocsAuthMiddleware — JWT-guard /docs in production
4. CORSMiddleware
5. RequestTimingMiddleware — X-Response-Time
6. SecurityHeadersMiddleware — CSP, HSTS, XFO
7. GZipMiddleware — >1KB
8. ReadinessMiddleware — 503 until system_ready
9. DegradedModeMiddleware — Circuit breaker (L2=read-only, L3=critical-only)
10. KernelMiddleware
11. ConcurrencyLimitMiddleware — max 200, clinical exempt

### Self-Healing (3 Layers)
- Circuit Breaker — DB 3 fails, Redis 5 fails; L1 cache, L2 read-only, L3 critical-only
- Auto-Repair Engine — memory GC, pool recycle, circuit probe, Redis reconnect
- Adaptive Concurrency — halves cap on 2 slow DB reads >300ms; restores on 3 fast <150ms
- Health Alert Loop — GREEN/YELLOW/RED scoring every 60s, webhook on transitions

### Health Endpoints (6, bypass all middlewares)
- `/health`, `/health/live` — liveness
- `/health/ready` — readiness (Docker healthcheck)
- `/health/status` — startup diagnostic
- `/health/deep` — grade + latencies + memory
- `/health/kernel` — kernel health

### Feature Flags (2 parallel systems)
- Per-tenant (`feature_flags.py`) — tier-based, DB-backed + Redis-cached
- Deployment-wide (`sndhs_flags.py`) — SNDHS_ENABLE_VISITS, SNDHS_ENABLE_NATIONAL_ID, ENABLE_FINANCIAL_ENGINE, ENABLE_ADS

### Startup Sequence
- validate_config() → wait_for_db() (15 retries, exponential backoff) → check_migrations() → seed_critical_data() → set_system_ready(True) → start background loops → boot kernel

### Microservices Architecture (future state)
- RabbitMQ event bus (gula.events) connecting services on ports 8001–8006
- Only device_bridge and ai are production-ready; 7 others are stubs
- Full stack includes ClickHouse, Kafka, MinIO for result service

### Data Flow: Lab Result Ingestion
- Lab Analyzer (ASTM serial/TCP) → device_bridge → normalizer → test mapper → patient matcher → smart router → gula_client.py (HTTP POST) → device_results route → auth + validation → LabResult (optimistic lock) → audit → clinical engine → outbox → notification (WhatsApp/SMS)

---

## 4. Backend Analysis

### Technology Stack
| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.139.0 |
| ASGI | Uvicorn | 0.51.0 |
| WSGI | Gunicorn | 21.2+ |
| Python | CPython | 3.11+ |
| ORM | SQLAlchemy | 2.0.51 |
| Migrations | Alembic | 1.18.5 |
| Validation | Pydantic | 2.13.4 |
| DB Driver | psycopg2-binary | 2.9.9 |
| Auth | python-jose | 3.4+ (HS256) |
| Encryption | cryptography (Fernet) | 49.0.0 |
| Password | passlib[bcrypt] / bcrypt | 4.1.3 |
| HTTP Client | httpx | 0.27+ |
| Cache | redis-py | 8.0.1 |
| Error Tracking | sentry-sdk | 2.65.0 |

### Route Modules (53+ confirmed)
- **Core LIMS (16):** admin (37,893 LOC), login (7,330), register (21,530), labs (7,308), patients (8,732), results (11,594), test_results (24,384), samples (6,349), dashboard (6,327), stats (14,945), patient_card (11,396), quality_control (10,802), critical_alerts (1,118), device_results (3,993), batch (3,950), qr (2,736)
- **Clinical (8):** clinical (40,609), clinical_orders (9,855), clinical_documentation (11,846), clinical_quality (2,909), ehr (73,097 — largest), ehr_fhir (37,334), care_continuum (33,957), hospital (26,515)
- **AI (2):** ai (39,938), ai_telemetry (19,846)
- **Security (9):** identity (2,673), national_identity (755), mfa (4,486), password_reset (2,723), oauth2 (12,106), saml (2,147), service_accounts (3,462), consent (6,661), security (1,968)
- **National (6):** national_data (34,607), national_streaming (9,502), compliance (47,295), citizen_portal (17,175), claims (6,316), insurance (550)
- **Other (8+):** edge (32,912), metrics (12,801), mobile (13,349), notifications (4,632), tiers (21,577), integrations (4,425), setup (1,021), optimizer (3,069), canonical_patient (7,890)

### Service Layer (34+ files)
- Largest: interpretation.py (1,100+ LOC), clinical_service.py (1,336), ehr_service.py (1,324), care_continuum_service.py (1,084)
- Clinical intelligence, state, engine; hospital, data_platform, audit, outbox services

### Core Infrastructure (15 modules)
- startup_guard.py (713), self_healing.py (458), auto_repair.py (330), feature_flags.py (340), sndhs_flags.py (171), policy_engine.py (277), logging_config.py (24)

### Background Worker (6 resilient loops)
1. OutboxWorker — dispatch events (10s poll)
2. RecoveryWorker — probe failed services (30s poll)
3. _health_alert_loop — scoring (60s)
4. _adaptive_concurrency_loop — throttle adjustment
5. auto_repair.run — GC, pool recycle, reconnect
6. TaskWorker — discrete task queue

### Key Architectural Decisions
- Monolith-first (microservices are stubs)
- Lifespan pattern (not deprecated on_event)
- Context var correlation (request_id, endpoint, user_id, lab_id)
- Sliding window monitoring (5-min DB window, Redis persistence)
- Optimistic locking (version column on LabOrder + LabResult)
- Transactional outbox (OutboxEvent, FOR UPDATE SKIP LOCKED)
- Hash chain audit (SHA-256, HMAC checkpoints every 100 entries)
- Dual-read rule (national_id/sndhs_health_id may be None)
- Edge guard (blocks edge table access from API/test/cli runtimes)

---

## 5. Database Analysis

### Technology
- Primary: PostgreSQL 16 (MVP), 14.11 (full.yml)
- Analytics: ClickHouse 23.8
- Cache: Redis 7-alpine
- Object Storage: MinIO RELEASE.2024-01
- Message Queue: RabbitMQ 3.12-management
- Stream: Kafka 7.5.0

### Migration Inventory (48 files, 6 phases)
| Phase | Count | Date Range | Scope |
|-------|-------|------------|-------|
| 1 — Core LIMS Bootstrap | 8 | 2025-03-22 → 2026-03-24 | Base schema, roles, indexes, validation, citizen, patient, lab |
| 2 — Production Hardening | 5 | 2026-03-24 → 2026-03-29 | FK constraints, audit hash chain, production indexes, subscriptions, version+indexes |
| 3 — Domain Expansion | 5 | 2026-04-07 → 2026-05-03 | Claims, MPI/registry, consent, edge platform, stats indexes |
| 4 — SNDHS-lite Integration | 6 | 2026-05-05 | national_id, sndhs_health_id, visits, visit_id FK, audit v2, constraints |
| 5 — Financial + AI | 3 | 2026-05-06 → 2026-05-11 | Financial Phase A, AI interactions, AI safety columns |
| 6 — National Platform | 17 | 2026-07-14 → 2026-07-16 | LIMS 35 tables, pharmacy 23, radiology 19, nursing 15, EMS 12, blood bank 11, critical care 13, biomedical 11, public health 7, command center 4, pilot 5, lifecycle 5, trust 5, governance 3, auth/security 4, canonical patient, HWD, ecosystem partners |

### Core Tables (~20)
- labs, lab_users, users, patients, lab_orders, lab_results, samples, test_types, audit_logs, outbox_events

### Domain Tables (~230 additional)
| Domain | Tables | Migration(s) |
|--------|--------|-------------|
| National LIMS | 35 | 20260714_0001 |
| Clinical Terminology/Knowledge/Quality/CDS | 43 | Clinical sub-packages |
| NHDW (Hospital) | 15 | 20260716_0001 |
| Pharmacy | 23 | 20260716_0003 |
| Radiology | 19 | 20260716_0004 |
| Nursing | 15 | 20260716_0002 |
| EMS | 12 | 20260716_0005 |
| Blood Bank | 11 | 20260716_0006 |
| Critical Care | 13 | 20260716_0007 |
| Biomedical | 11 | 20260716_0008 |
| Public Health | 7 | 20260716_0009 |
| Command Center | 4 | 20260716_0010 |
| Pilot/Lifecycle/Trust/Governance | 18 | 20260716_0011-0014 |
| Auth/Security | 4 | 20260716_0015 |
| Health Data (Warehouse/ODS/MDM) | 15+ | National |
| MPI/Citizen | 4 | 20260413_0001 |
| Edge Platform | 9 | 20260428_0001 |
| AI Interactions | 5 | 20260511_0001/0002 |
| Financial | 5 | 20260506_0001 |
| SNDHS | 3 | 20260505_0001-0006 |

### Migration Policy Compliance
- ✅ Never modify existing migrations (all 48 additive)
- ✅ All schema changes = new revision
- ✅ Base schema immutable (20250322_0000)
- ✅ Idempotent migrations (_has_column, _table_exists guards)
- ✅ New columns nullable

### Key Database Patterns
- Tenant isolation: every patient-data table has lab_id FK
- Optimistic locking: version column on lab_orders + lab_results (HTTP 409)
- Hash chain audit: SHA-256 chain, PG trigger prevents UPDATE/DELETE, HMAC checkpoints every 100 entries
- Encryption at rest: Fernet AES-256 + HMAC-SHA256 for national_id
- Dual-read rule: national_id/sndhs_health_id gracefully handle None

### Connection Pool
- SQLAlchemy QueuePool: pool_size=5, max_overflow=10, pool_timeout=10s, pool_recycle=1800s, pool_pre_ping=True
- 3 workers × 6 connections = 18 total (within PG max_connections=100)
- Statement timeout: 30s, work_mem: 128MB, idle_in_transaction: 30s

---

## 6. Security Analysis

### Defense-in-Depth Layers
- **Network:** TLS 1.2/1.3, ModSecurity WAF (SQLi/XSS), Nginx rate limit (10r/s general, 100r/min API), Cloudflare DDoS, Snort IDS + Fail2ban
- **Auth:** JWT HS256 (30min TTL), RBAC (9 roles × 16 permissions), ABAC, MFA (TOTP + WebAuthn/FIDO2/Passkeys), OAuth2/OIDC provider + PKCE, SAML 2.0 SSO
- **Data:** Fernet AES-256 at rest, HMAC-signed national IDs + patient card tokens, hash-chain audit, SHA-256 + PG trigger
- **Rate Limiting (4 tiers):** auth=10/min, public=30/min, user=60/min, admin=20/min; hard block after 5× limit for 1 hour
- **Infra:** API firewall (Redis + local dual-write, max 5,000 entries), circuit breakers (L1/L2/L3), startup guard, weak secret detection (15+ patterns), security headers (CSP, HSTS, XFO, XSS-Protection, Referrer, Permissions-Policy, COOP), CORS whitelist, tenant isolation (lab_id filter)

### JWT Configuration
| Parameter | Value |
|-----------|-------|
| Algorithm | HS256 (HMAC-SHA256) |
| Access TTL | 30 minutes |
| Refresh TTL | 30 days |
| Payload | user_id, lab_id, role, perm_version, jti, type, exp, iat |
| Blacklisting | Redis `blacklist:jti:{jti}` |
| Secrets | SECRET_KEY + REFRESH_TOKEN_SECRET (hard fail if missing/weak) |

### RBAC Roles (9, hierarchical)
| Role | Level | Scope |
|------|-------|-------|
| master_admin | 100 | All permissions |
| ministry_admin | 90 | Read + platform management |
| province_admin | 80 | Province-scoped |
| admin / lab_admin | 50 | Full lab management |
| doctor | 40 | Read-only clinical |
| staff / lab_staff | 20 | Read/write orders/results |
| technician | 20 | Order/result read/write |
| citizen | 10 | Own data only |

### Permissions (16 string permissions)
- patients:read/write/delete, orders:read/write, results:read/write, staff:manage, lab:read/manage, dashboard:read, audit:read, platform:manage_labs/users/view_stats, system:admin

### Encryption Keys (required, hard fail)
| Secret | Validation |
|--------|-----------|
| SECRET_KEY | Present + not weak |
| REFRESH_TOKEN_SECRET | Present + not weak |
| ENCRYPTION_KEY | Present + not weak + Fernet-valid |
| NID_HMAC_KEY | Present + not weak |
| NID_HMAC_KEY_PREV | Optional (key rotation) |

### Audit Hash Chain
- chain_hash = SHA-256(prev_hash + JSON(entry))
- Genesis: "0" × 64
- PG trigger prevents UPDATE/DELETE
- HMAC checkpoint files every 100 entries (audit_anchors_{YYYY-MM}.log)
- Coverage: all CREATE/UPDATE/DELETE, login/logout, permission changes, break-glass, AI decisions

### Security Testing
- Bandit SAST: 0 High, 2 Medium
- Gitleaks: 0 leaks (CI)
- Safety, Hadolint, Semgrep, OWASP ZAP configured

### Critical Security Findings
| Finding | Risk |
|---------|------|
| Firebase bypasses backend security (direct Firestore access) | **CRITICAL** |
| Emergency break-glass audited but uncontrolled | **HIGH** |
| HS256 JWT — no RS256/ES256, key distribution risk | **HIGH** |
| No JWT kid header — no key rotation support | **MEDIUM** |
| No automated secrets rotation | **HIGH** |
| OAuth2 id_tokens use HMAC — OIDC compliance gap | **MEDIUM** |
| Redis password from env var (plaintext) | **MEDIUM** |
| Rate limit bypass in test mode | LOW |

---

## 7. Infrastructure Analysis

### Deployment Targets (7)
- **Docker Compose MVP** — PRIMARY (7 services: postgres, redis, gula-backend, gula-worker, frontend, api-gateway, prometheus/grafana/device-bridge as profile)
- **Docker Compose Full** — Ready (25+ services: +Patroni, PgBouncer, ClickHouse, RabbitMQ, Kafka, MinIO, Ollama, Keycloak, Vault, Loki, Tempo, Jaeger, all microservices)
- **Kubernetes Kustomize** — Ready (base + 4 overlays: dev, prod, region-eu, region-me)
- **Kubernetes Helm** — Ready (chart v1.0.0, 1326-line values.yaml, 9 Bitnami dependencies)
- **DigitalOcean** — Ready (app.yaml)
- **Render** — Documented
- **Supabase** — Partial

### Docker Compose MVP (Production)
| Service | Image | Memory | CPU |
|---------|-------|--------|-----|
| postgres | postgres:16-alpine | 896m | 1.0 |
| redis | redis:7-alpine | 320m | 0.5 |
| gula-backend | ghcr.io/gula/backend | 1,536m | 1.5 |
| gula-worker | same image | 512m | 0.5 |
| frontend | nginx:1.25-alpine | — | — |
| api-gateway | nginx:1.25-alpine | — | — |

### Docker Compose Full (Additional Services)
- Database HA: postgres-primary, postgres-replica, pgbouncer, backup-cron
- Redis HA: redis, redis-replica, redis-sentinel (3 nodes, quorum 2)
- Analytics: clickhouse
- Messaging: rabbitmq (3-node), zookeeper, kafka
- AI: ollama 0.1.29, ai-service
- Storage: minio (distributed, 4 replicas, 100Gi, 3 buckets)
- Monitoring: prometheus, grafana, loki, promtail, jaeger, node-exporter
- Security: keycloak 23.0, vault 1.15
- Microservices: lab, patient, order, result, sample, notification, autonomous-manager
- Network: 172.20.0.0/16, 18 Docker volumes

### Kubernetes (Kustomize)
- Base: backend (2 replicas, wait-for-postgres + wait-for-redis init containers), frontend, gateway, postgres statefulset, redis, rabbitmq, microservices
- HPA: CPU 70%, memory 80%, scale 2–10, scale-up 2 pods/60s, scale-down 1 pod/120s
- Blue-green: slot-based, gula-backend-active service routes to live slot
- Service mesh: Linkerd auto-inject, service profiles with retry budgets

### Helm Chart
- Version 1.0.0, App 2.1.0, 9 Bitnami deps (postgresql, redis, rabbitmq, minio, prometheus, grafana, loki, tempo, linkerd2)
- Pod security: runAsNonRoot, seccomp RuntimeDefault, ALL capabilities dropped
- Postgres HA: Patroni + Spilo, 1 primary + 2 replicas, 50Gi, pgBackRest

### Terraform (AWS, 12 modules)
- networking, security, storage, postgres, redis, rabbitmq, kubernetes (EKS 1.29), alb, cdn, dns, monitoring, backup
- 5 environments: dev, staging, pilot, prod, dr
- **MISMATCH:** Targets AWS; actual deployment is DigitalOcean

### CI/CD (6 workflows)
- `ci.yml` (644 lines, 7 jobs): syntax-gate → migration-check → openapi-contract → backend-test → smoke-test → security-scan → build-and-push (matrix 8 images + Trivy)
- `quality-gate.yml`: 9 gates (architecture, performance, security, database, API, FHIR, scalability, offline, accessibility)
- `deploy.yml`: SSH → git sync → secrets → pull → zero-downtime restart → health → auto-rollback
- Canary (Linkerd TrafficSplit: 10→25→50→100%), Blue-green (K8s slot swap), Auto-rollback

### Monitoring Stack
- Prometheus (2 scrape configs, 3 rule files: gula.yml 396 lines, gula-full.yml 289 lines, slo.yml 151 lines)
- Grafana (4 dashboards: platform, hospital, capacity, laboratory)
- Alertmanager (Slack + PagerDuty), Loki + Promtail, Tempo (OTLP + Jaeger + Zipkin), OpenTelemetry

### Critical Infrastructure Findings
| Finding | Risk |
|---------|------|
| MVP compose has no HA (single PG + Redis) | **HIGH** |
| Full.yml (25+ services) not deployed | **MEDIUM** |
| Terraform targets AWS but deployment is DigitalOcean | **HIGH** |
| No staging environment (only dev + prod) | **HIGH** |
| PG16 (MVP) vs PG14 (full.yml) version inconsistency | **MEDIUM** |
| No automated backup restore testing | **HIGH** |

---

## 8. Contradictions (14 documented)

### Version (C4)
- config.py = 2.1.0, CHANGELOG.md = 2.3.2, pyproject.toml = 2.2.0, Helm appVersion = 2.1.0

### Route Count
- CLAUDE.md claims 36; actual count is 53+

### Model Count
- CLAUDE.md claims 17; actual is 60+ files, ~250 tables

### Database Engine
- CLAUDE.md says PG16; full.yml uses PG14

### AI Providers (EO Violation — critical)
- Executive Orders 3 & 4 mandate Ollama-only; routes/ai.py uses Gemini + Groq; gateways/google_ai.py exists

### Microservices
- CLAUDE.md implies microservices ready; 6 of 9 are stubs with 0 tests

### Roles × Permissions
- CLAUDE.md: 9 × 13; actual code: 10 roles × 16 permissions

### Test Count
- CLAUDE.md: 28 test modules; actual: 77+ files

### Architecture Layer Naming (C3)
- CLAUDE.md: 3-layer (routes → services → models)
- Constitution: 4-layer (routes → services → domain → infrastructure)

### UUID PK Mandate (C2)
- Constitution §2.4 mandates UUID PKs; most models use Integer/BigInteger

### Coverage Target Conflict (C1)
- Platform Constitution: ≥95%; Digital Constitution: 70%/90%+ critical; actual: 54% (routes 35%, services 30%, edge 0%)

### mTLS Mandate vs HTTP (C6)
- Constitution §4.3 mandates mTLS; device-bridge talks HTTP to backend

### SBOM Mandate vs CI (C7)
- Constitution §4.6 mandates SBOM every build; no SBOM step in CI

### FHIR Strategy (C5)
- Constitution mandates FHIR content-type on every endpoint; code implements FHIR as separate `/fhir/` route

---

## 9. Dependency Graph

### Internal Module Dependencies
```
main.py → config.py, database.py, routes/* (53+), core/* (15), models/*
routes/* → services/* (34+) → models/* (60+) → database.py
services/* → core/*, security/* (15)
security/* → shared/auth/*, shared/rbac/*, shared/security/*
core/* → database.py, shared/circuit_breaker/*
worker.py → core/self_healing.py, core/auto_repair.py, services/outbox_service.py, database.py
```

### External Service Dependencies
| Service | Dependencies |
|---------|-------------|
| gula-backend | PostgreSQL 16, Redis 7, Ollama (opt), Gemini API (opt, EO violation), Groq API (opt, EO violation), Sentry (opt) |
| gula-worker | PostgreSQL 16, Redis 7 |
| device_bridge | Lab analyzers (Sysmex, Roche, Mindray — serial/TCP) |
| services/ai | Ollama :11434, Redis (opt) |
| services/notification | RabbitMQ |
| services/{lab,order,patient,result,sample} | PostgreSQL, RabbitMQ |
| frontend-v2 | Firebase Auth, Cloud Firestore, FastAPI (minimal?) |
| client | FastAPI (tRPC) |

### Python Production Dependencies (17 core packages)
fastapi 0.139.0, uvicorn 0.51.0, gunicorn 21.2+, sqlalchemy 2.0.51, alembic 1.18.5, psycopg2-binary 2.9.9, pydantic 2.13.4, python-jose 3.4+, cryptography 49.0.0, passlib[bcrypt] 1.7.4, bcrypt 4.1.3, redis 8.0.1, httpx 0.27+, qrcode 7.4.2, Pillow 10.4.0, reportlab 4.1.0, sentry-sdk 2.65.0, python-multipart 0.0.20 (+ arabic-reshaper, python-bidi)

### Dev Dependencies
pytest 9.0.3, pytest-asyncio 0.23+, factory_boy 3.3.0, webauthn 2.0.0, email-validator 2.1.0

### Docker Image Dependencies (8-image matrix)
- ghcr.io/samertts/gula-platform/{backend, svc-lab, svc-order, svc-patient, svc-result, svc-sample, svc-notification, svc-ai}
- Python 3.11-slim base + 17 external images (postgres, redis, nginx, prometheus, grafana, ollama, minio, rabbitmq, kafka, clickhouse, vault, keycloak, pgbouncer, node-exporter)
- device_bridge → lablink-core:0.1.0 (Python 3.12)

### Key Dependency Findings
- Firebase Firestore is a separate data store not gated by backend — **CRITICAL** dual-write risk
- services/shared/ is a deprecated bridge — LOW
- services/result has ClickHouse + Kafka + MinIO deps but is stub — **MEDIUM** premature complexity
- Terraform targets AWS, deployment on DO — **HIGH** misalignment

---

## 10. Risk Register

### Risk Scoring: Likelihood (1-5) × Impact (1-5) = Score (1-25)

### Critical Risks (Score 15-25)
| ID | Risk | L | I | Score |
|----|------|---|---|-------|
| R01 | Firebase bypasses backend security | 5 | 5 | **25** |
| R03 | Patient data exposure via Firebase | 4 | 5 | **20** |
| R02 | No automated backup restore testing | 4 | 5 | **20** |
| R04 | EO violations (AI providers) | 5 | 4 | **20** |
| R05 | No staging environment | 4 | 4 | **16** |
| R06 | Single PostgreSQL in production | 3 | 5 | **15** |
| R07 | Version tracking inconsistency | 4 | 3 | **15** |

### High Risks (Score 10-14)
| ID | Risk | L | I | Score |
|----|------|---|---|-------|
| R08 | Low route test coverage (35%) | 4 | 3 | 12 |
| R09 | Low service test coverage (30%) | 4 | 3 | 12 |
| R10 | Zero edge/interop test coverage | 3 | 4 | 12 |
| R11 | 6 microservice stubs with 0 tests | 3 | 4 | 12 |
| R12 | JWT uses HS256 (symmetric key) | 3 | 4 | 12 |
| R13 | No automated secrets rotation | 4 | 3 | 12 |
| R14 | Massive schema churn (17 migrations in 1 day) | 4 | 3 | 12 |
| R15 | No frontend security testing | 3 | 4 | 12 |
| R16 | No E2E tests | 3 | 4 | 12 |
| R17 | Terraform targets AWS, runs on DO | 4 | 3 | 12 |
| R18 | Clinical CDS schema-only | 3 | 3 | 9 |
| R19 | National platform domains schema-only | 3 | 3 | 9 |

### Medium Risks (Score 5-9)
| ID | Risk | L | I | Score |
|----|------|---|---|-------|
| R20 | Monster route files (ehr.py 73KB, compliance.py 47KB) | 4 | 2 | 8 |
| R21 | Duplicate AI engines | 3 | 2 | 6 |
| R22 | No DICOM server | 2 | 3 | 6 |
| R23 | No LOINC/SNOMED/ICD data populated | 3 | 2 | 6 |
| R24 | Documentation behind code | 4 | 1 | 5 |
| R25 | No load test baseline | 3 | 2 | 6 |
| R26 | No synthetic monitoring | 2 | 3 | 6 |

### Low Risks (Score 1-4)
| ID | Risk | L | I | Score |
|----|------|---|---|-------|
| R27 | AWS Terraform for DO deployment | 2 | 2 | 4 |
| R28 | Old MySQL reference in docs | 2 | 1 | 2 |
| R29 | No internationalization | 1 | 2 | 2 |
| R30 | No customer evidence | 2 | 2 | 4 |

### Top 5 Immediate Action Risks
1. **R01** — Firebase security bypass (score 25)
2. **R02** — No backup restore testing (score 20)
3. **R04** — EO AI provider violations (score 20)
4. **R06** — Single PG instance (score 15)
5. **R03** — Patient data exposure via Firebase (score 20)

---

## 11. Technical Debt Register

### Summary (36 items, ~14 months estimated effort)
| Category | Count | Critical | High | Medium | Low | Est. Effort |
|----------|-------|----------|------|--------|-----|-------------|
| Architecture | 7 | 1 | 1 | 4 | 1 | 4 months |
| Code Quality | 6 | 0 | 4 | 0 | 1 | 4 months |
| Security | 6 | 1 | 2 | 3 | 0 | 2 months |
| Database | 5 | 1 | 1 | 2 | 1 | 1 month |
| Documentation | 6 | 0 | 0 | 4 | 2 | 1 month |
| Infrastructure | 6 | 2 | 1 | 3 | 0 | 2 months |
| **Total** | **36** | **5** | **9** | **16** | **5** | **~14 months** |

### Architecture Debt (7)
| ID | Debt | Location | Priority |
|----|------|----------|----------|
| AD01 | Monster route files (ehr.py 73KB, compliance.py 47KB, clinical.py 41KB) | routes/ | High |
| AD02 | Dual AI engine (services/ai vs routes/ai.py) | services/ai, routes/ai.py | Medium |
| AD03 | Dual frontend architecture (Firebase vs tRPC) | frontend-v2/, client/ | **Critical** |
| AD04 | 6 microservice stubs | services/{lab,order,patient,result,sample,notification} | Medium |
| AD05 | Deprecated services/shared bridge | services/shared/ | Low |
| AD06 | AWS Terraform for DO deployment | terraform/ | Medium |
| AD07 | National platform schema-only (200+ tables) | backend/app/national*/ | Medium |

### Code Quality Debt (6)
| ID | Debt | Location | Priority |
|----|------|----------|----------|
| CQ01 | Low route test coverage (35%) | routes/ | High |
| CQ02 | Low service test coverage (30%) | services/ | High |
| CQ03 | Zero edge/interop tests | edge/ | High |
| CQ04 | No frontend tests | frontend-v2/ | High |
| CQ05 | No E2E tests | entire platform | High |
| CQ06 | Duplicate clinical engine logic | services/interpretation.py, clinical_intelligence.py, clinical_engine.py | Low |

### Security Debt (6)
| ID | Debt | Location | Priority |
|----|------|----------|----------|
| SD01 | HS256 JWT (symmetric key) | security/auth.py | High |
| SD02 | No JWT kid header | security/auth.py | Medium |
| SD03 | No automated secrets rotation | CI/CD | High |
| SD04 | Firestore security bypass | frontend-v2/ | **Critical** |
| SD05 | Emergency break-glass audit-only | security/consent_dep.py | Medium |
| SD06 | OIDC uses HMAC for id_tokens | security/oauth2_provider.py | Medium |

### Database Debt (5)
| ID | Debt | Location | Priority |
|----|------|----------|----------|
| DB01 | Version divergence (2.1.0 vs 2.3.2) | config.py vs CHANGELOG.md | Low |
| DB02 | Massive same-day migrations (17 files) | migrations/versions/20260716_* | High |
| DB03 | No VACUUM/ANALYZE automation | PostgreSQL | Medium |
| DB04 | Single PG in production | docker-compose.yml | **Critical** |
| DB05 | No partition management for audit_logs | PostgreSQL at scale | Medium |

### Documentation Debt (6)
| ID | Debt | Location | Priority |
|----|------|----------|----------|
| DD01 | Route count mismatch (36 vs 53+) | CLAUDE.md | Medium |
| DD02 | Model count mismatch (17 vs 60+) | CLAUDE.md | Medium |
| DD03 | MySQL reference instead of PG | INFRASTRUCTURE_GUIDE.md | Low |
| DD04 | Missing consumer API changelog | docs/ | Medium |
| DD05 | Missing Arabic user manual | docs/ | Medium |
| DD06 | Missing on-premise deployment guide | docs/ | Medium |

### Infrastructure Debt (6)
| ID | Debt | Location | Priority |
|----|------|----------|----------|
| ID01 | No staging environment | k8s/overlays/ | **Critical** |
| ID02 | No backup restore testing | scripts/ | **Critical** |
| ID03 | No automated secrets rotation | CI/CD | High |
| ID04 | No synthetic monitoring | monitoring/ | Medium |
| ID05 | K8s overlays not primary deployment | k8s/ | Medium |
| ID06 | No APM integration | monitoring/ | Medium |

### Top 5 Urgent Debt Items
1. **SD04** — Firestore security bypass (Security, Critical)
2. **DB04** — Single PG instance (Database, Critical)
3. **ID02** — No backup restore testing (Infrastructure, Critical)
4. **ID01** — No staging environment (Infrastructure, Critical)
5. **CQ01** — Low route test coverage (Code Quality, High)

---

## 12. Constitution Validation

### Authority Hierarchy (7 documents)
| Rank | Document | Status |
|------|----------|--------|
| 1 | PLATFORM-CONSTITUTION.md v1.0.0 | FROZEN |
| 2 | ENGINEERING_CONSTITUTION.md v1.0.0 | ADOPTED |
| 3 | digital_dna.md v1.0 | RATIFIED |
| 4 | platform_identity.md v1.0 | RATIFIED |
| 5 | NATIONAL-TRUST-PLATFORM.md v1.0.0 | FROZEN |
| — | DIGITAL-CONSTITUTION.md v1.0.0 | SUPERSEDED |
| — | CLAUDE.md | OPERATIONAL |

### Contradictions Found (13, C1–C13)
| ID | Issue | Severity |
|----|-------|----------|
| C1 | Coverage target conflict (≥95% vs 70% vs 54%) | **CRITICAL** |
| C2 | UUID PK mandate vs Integer PK reality | **CRITICAL** |
| C3 | Architecture layer naming (3-layer vs 4-layer) | MAJOR |
| C4 | Version mismatch (2.1.0/2.2.0/2.3.2) | MINOR |
| C5 | FHIR mandate ambiguity (separate route vs content-type) | MAJOR |
| C6 | mTLS mandate vs HTTP comms | **CRITICAL** |
| C7 | SBOM mandate vs no SBOM in CI | MAJOR |
| C8 | Duplicate files (ENGINEERING_CONSTITUTION.md, quality_gates.md) | MINOR |
| C9 | DIGITAL-CONSTITUTION.md superseded but not deprecated | MAJOR |
| C10 | No README per module (Constitution Q5 violation) | MAJOR |
| C11 | No circular dependency check in CI (Constitution Q5 violation) | MAJOR |
| C12 | Failed tests contradiction (268 errors, 3 failures vs Q12=0) | MAJOR |
| C13 | Retention policy enforcement missing (clinical 25y, results 10y, audit 7y) | MAJOR |

### Gaps Found (6, G1–G6)
- G1: No ADR for layer restructuring
- G2: No ADR for UUID migration
- G3: Constitution enforcer gaps (no SBOM, migration policy, naming checks; not in CI)
- G4: No ADR for mTLS decision
- G5: No ADR for FHIR strategy
- G6: No ADR for SBOM decision

### Remediation Priority
- **IMMEDIATE (P0):** C1, C2, C6, C11
- **SHORT-TERM (P1):** C3, C5, C7, C10, C12
- **MEDIUM (P2):** C4, C8, C9, C13, G3
- **LONG-TERM (P3):** G1, G2, G4, G5, G6

---

## 13. Executive Summary (Key Findings)

### What's Working Well (9 strengths)
- Core LIMS production-ready (orders, results, samples, QC, patient cards, PDF, audit, multi-tenancy)
- Strong security foundation (JWT, RBAC, ABAC, MFA, OAuth2/OIDC, SAML, Fernet, hash-chain audit, rate limiting, circuit breakers)
- Advanced self-healing (3-layer: circuit breaker → auto-repair → adaptive concurrency)
- Comprehensive infrastructure (Docker Compose MVP+Full, K8s Kustomize+Helm, Terraform, 6 CI/CD workflows, canary/blue-green/auto-rollback)
- Arabic-first design (full UI, interpretations, PDF reports, RTL)
- Iraqi-specific integration (MoI National ID, SNDHS-lite, IQD claims)
- Healthcare standards (FHIR R4/R5 6 resources, LOINC, SNOMED CT, ICD-10/11, Westgard QC)
- Clinical intelligence (30+ interpretations, 15 multi-test syndrome patterns)
- Device integration (ASTM/HL7 bridge for Sysmex, Roche, Mindray)

### Critical Issues (4)
1. **Firebase security bypass** — frontend-v2 talks directly to Firestore, bypassing backend security (risk 25/25)
2. **No backup restore testing** — DR risk (risk 20/25)
3. **Single PostgreSQL instance** — no HA (risk 15/25)
4. **AI provider compliance** — Gemini/Groq violate EO 3 & 4 (risk 20/25)

### Major Gaps (9)
| Gap | Severity |
|-----|----------|
| Test coverage 54% (routes 35%, services 30%, edge 0%) | HIGH |
| No staging environment | HIGH |
| JWT uses HS256 (no key rotation) | HIGH |
| No secrets rotation | HIGH |
| 6 microservice stubs with 0 tests | MEDIUM |
| National platform domains schema-only (200+ tables, no code) | MEDIUM |
| Documentation behind code (36 vs 53+ routes) | MEDIUM |
| Version tracking divergence | LOW |

### Healthcare Standards Readiness
- Core LIMS: ✅ PRODUCTION
- FHIR R4/R5: ⚠️ PARTIAL (6/100+ resources)
- HL7 v2: ⚠️ ASTM only (no ADT/ORM/ORU)
- DICOM: ❌ NOT IMPLEMENTED
- LOINC/SNOMED/ICD: ⚠️ Model only (not populated)
- Clinical CDS: ❌ Schema only
- Pharmacy/Radiology/Nursing: ❌ Schema only

### Business Maturity
- ✅ Prototype, MVP, Production Ready (core LIMS)
- ⚠️ Enterprise Ready (partial — multi-branch, tiers need hardening)
- ⚠️ Government Ready (partial — SNDHS Phase 1 done, certification pending)
- ⚠️ Healthcare Ready (partial — core LIMS + basic EHR; multi-domain schema-only)
- ❌ International Ready (Arabic-only, Iraq-focused)

### Top 5 Strategic Recommendations
| Priority | Recommendation | Effort | Impact |
|----------|---------------|--------|--------|
| 1 | Fix Firebase security bypass | 2 weeks (lockdown) or 3 months (full migration) | Eliminates catastrophic data exposure |
| 2 | Add backup restore testing | 1 week | Ensures DR works |
| 3 | Deploy PostgreSQL HA | 2–3 weeks | Eliminates SPOF |
| 4 | Resolve AI provider compliance | 1 week | Regulatory compliance |
| 5 | Add integration tests (35% → 80%) | 4–6 weeks | Quality assurance foundation |

### 90-Day Priority Focus
1. Secure frontend-backend architecture (Firestore lockdown)
2. Stabilize production infrastructure (PG HA, backup testing)
3. Close test coverage gap on critical routes and services
4. Align AI provider usage with regulatory policy
5. Freeze schema expansion until existing code catches up

---

## 14. Healthcare Standards Support Inventory

| Standard | Implementation | Status |
|----------|---------------|--------|
| FHIR R4/R5 | routes/ehr_fhir.py — Patient, Encounter, Observation, Condition, MedicationRequest, Immunization | ⚠️ 6/100+ resources |
| HL7 v2 | gateways/lab_device_gateway.py — ASTM/HL7 | ⚠️ ASTM only |
| LOINC | clinical/terminology/models.py — searchable | ⚠️ Model only |
| SNOMED CT | clinical/terminology/models.py — searchable via TerminologyService | ⚠️ Model only |
| ICD-10/ICD-11 | Both modeled with hierarchy, billable flags | ⚠️ Model only |
| UCUM, ATC, RxNorm, CPT | All modeled | ⚠️ Model only |
| Westgard Rules | 1-2s, 1-3s, 2-2s, R-4s, 4-1s, 10-x | ✅ Implemented |
| DICOM | Not implemented | ❌ Missing |

---

## 15. CI/CD Pipeline Inventory

| Workflow | Lines | Jobs | Purpose |
|----------|-------|------|---------|
| ci.yml | 644 | 7 | syntax-gate, migration-check, openapi-contract, backend-test, smoke-test, security-scan, build-and-push (8-image matrix + Trivy) |
| quality-gate.yml | — | 9 gates | Architecture, Performance, Security, Database, API, FHIR, Scalability, Offline, Accessibility |
| deploy.yml | — | 1 | SSH → git sync → secrets → pull → zero-downtime restart → health check → auto-rollback |
| canary-deploy.yml | — | 1 | Linkerd TrafficSplit: 10% → 25% → 50% → 100% |
| blue-green-deploy.yml | — | 1 | K8s slot swap |
| auto-rollback.yml | — | 1 | Detect failure → kubectl patch svc |

### CI Security Scanning
- Safety (CVE), Bandit -ll -ii (SAST), Hadolint (Dockerfile), Gitleaks (secrets), Trivy (container), Semgrep (custom rules), OWASP ZAP (DAST — configured)

---

## 16. Testing Inventory

| Category | Files | Coverage | Status |
|----------|-------|----------|--------|
| Unit/Integration | 124 files in backend/tests/ | 54% overall | ✅ Functional |
| Routes | 53+ modules | 35% | ❌ Below threshold |
| Services | 34+ files | 30% | ❌ Below threshold |
| Edge/Interop | 0 | 0% | ❌ Critical gap |
| Frontend | frontend-v2/ | 0% | ❌ Missing |
| E2E | Entire platform | 0% | ❌ Missing |
| Load/Stress | k6 + Locust scripts exist | No baseline | ⚠️ Unmeasured |
| Security | Bandit, Gitleaks, Safety, Hadolint | CI-gated | ✅ Functional |
| Chaos | chaos-mesh experiments | Defined | ⚠️ Not regular |
| Total collected | 1,505+ tests | — | — |

### Test Modules (key)
- test_comprehensive.py, test_stress.py, test_system_improvements.py, test_security.py, test_patient_card.py, test_mpi_matcher.py, test_outbox_service.py, test_feature_flags.py, test_edge_platform.py, test_stability_assertions.py

---

## 17. Operational Maturity Matrix

| Capability | Status | Details |
|-----------|--------|---------|
| Container Orchestration | ✅ MVP | Docker Compose (7 services) |
| HA Database | ❌ Not deployed | Patroni config exists in full.yml |
| HA Redis | ❌ Not deployed | Sentinel config exists |
| Message Broker | ⚠️ Configured | RabbitMQ in full.yml; 1 service uses it |
| Stream Processing | ⚠️ Configured | Kafka in full.yml; not consumed |
| Monitoring | ✅ Prometheus + Grafana | 4 dashboards, 3 rule files (836 total alert lines) |
| Alerting | ✅ Alertmanager | Slack + PagerDuty |
| Log Aggregation | ⚠️ Configured | Loki + Promtail in full.yml |
| Distributed Tracing | ⚠️ Configured | Tempo + OpenTelemetry in full.yml |
| CI/CD | ✅ 6 workflows | Build, test, security scan, deploy (canary/blue-green/rollback) |
| IaC | ⚠️ Mismatched | Terraform targets AWS; actual DO deployment |
| DR | ⚠️ Untested | Cross-region config exists; no restore testing |
| Service Mesh | ⚠️ Configured | Linkerd in K8s manifests |
| Chaos Engineering | ⚠️ Defined | chaos-mesh experiments exist |
| Load Testing | ⚠️ Scripted | k6 + Locust scripts; no baseline |
| WAF | ✅ ModSecurity | Configured in nginx |
| IDS | ⚠️ Configured | Snort rules + Fail2ban |
| Secrets Management | ⚠️ Vault configured | Vault in full.yml; not in MVP |
| Backup | ✅ pg_dump scripted | Automated but untested for restore |

---

*Compiled from 17 discovery reports (Master Discovery, Repository Map, Architecture Map, Backend Analysis, Database Analysis, Security Analysis, Infrastructure Analysis, Contradictions, Dependency Graph, Risk Register, Technical Debt, Constitution Validation, Executive Summary). All findings supported by code/config/documentation references in source reports.*
