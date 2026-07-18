# GULA Platform — Dependency Genome

> **Version:** 2.1.0 | **Last Updated:** 2026-07-17 | **Classification:** CONFIDENTIAL
> Complete dependency map including internal graph, external packages, infrastructure, APIs, data flows, cross-cutting concerns, health metrics, and decision records.

---

## 1. Internal Dependency Graph

### 1.1 Service-to-Service Dependencies

```
                          ┌─────────────────────────────────────────────┐
                          │              gula-backend                    │
                          │  (FastAPI + gunicorn + uvicorn workers)      │
                          └──────┬──────────┬──────────┬───────────────┘
                                 │          │          │
                    ┌────────────┘          │          └────────────┐
                    ▼                       ▼                       ▼
           ┌────────────────┐   ┌────────────────────┐   ┌──────────────────┐
           │   PostgreSQL   │   │       Redis        │   │   External APIs   │
           │    (port 5432) │   │     (port 6379)    │   │   (HTTP/HTTPS)    │
           │   labdb        │   │   cache + sessions │   │                   │
           └────────────────┘   └────────────────────┘   └──────────────────┘
                    │                                        │
                    ▼                                        ▼
           ┌────────────────┐                       ┌──────────────────────┐
           │  nhop-platform │                       │  Cloudflare (DNS,    │
           │  (citizen reg) │                       │  WAF, R2, Workers)  │
           └────────────────┘                       └──────────────────────┘
                    │                                        │
                    ▼                                        ▼
           ┌────────────────┐                       ┌──────────────────────┐
           │  Device Bridge │                       │  Iraqi Gov APIs      │
           │  (ASTM/HL7)    │                       │  (MoI, NHI, Residency)│
           └────────────────┘                       └──────────────────────┘
```

### 1.2 Module-to-Module Dependencies (Backend Core)

```
config.py ←───── Every module (imports config constants)
     │
     ├──→ database.py ←── main.py, all routes, all services, tasks
     │         │
     │         ├──→ core/runtime_guard.py (edge access guard)
     │         ├──→ core/self_healing.py (circuit escalation)
     │         └──→ security/redis_client.py (window persistence)
     │
     ├──→ main.py ──→ core/startup_guard.py (readiness)
     │         │──→ core/logging_config.py (structured logging)
     │         │──→ core/self_healing.py (DegradedModeMiddleware)
     │         │──→ security/auth.py (DocsAuth, get_current_user)
     │         │──→ kernel/integration.py (kernel middleware)
     │         └──→ ALL route modules (app.include_router)
     │
     └──→ security/ ──→ security/auth.py → security/rbac.py
                │──→ security/encryption.py → config.py (ENCRYPTION_KEY)
                │──→ security/oauth2_provider.py → models/oauth2_*
                │──→ security/saml_service.py
                └──→ security/redis_client.py → config.py (REDIS_URL)
```

### 1.3 Route-to-Service Dependency Matrix

| Route Module | Depends On Services | Depends On Models |
|-------------|-------------------|-------------------|
| routes/login.py | security/auth.py, security/rate_limit.py | user, lab_user |
| routes/patients.py | patient_service, identity_matching, national_id | patient, lab |
| routes/results.py | order_service, audit_service, outbox_service, critical_alerts | lab_order, lab_result, test_result |
| routes/samples.py | order_service, audit_service | sample, lab_order |
| routes/quality_control.py | — | quality_control |
| routes/ai.py | ai/guardrails.py, ai/sandbox.py, clinical_engine | ai_interaction |
| routes/patient_card.py | patient_card, identity | patient, lab_order, lab_result |
| routes/mfa.py | security/mfa_service | mfa_device |
| routes/oauth2.py | security/oauth2_provider | oauth2_client, oauth2_token |
| routes/saml.py | security/saml_service | — |
| routes/claims.py | claims_service | claim |

---

## 2. External Dependencies

### 2.1 Python Packages (PyPI)

| Package | Purpose | Version Constraint | Criticality |
|---------|---------|-------------------|-------------|
| fastapi | Web framework | ≥0.110 | CRITICAL |
| uvicorn[standard] | ASGI server | — | CRITICAL |
| gunicorn | WSGI process manager | — | CRITICAL |
| sqlalchemy | ORM | ≥2.0 | CRITICAL |
| psycopg2-binary | PostgreSQL adapter | — | CRITICAL |
| redis | Redis client | — | HIGH |
| python-jose[cryptography] | JWT encode/decode | — | CRITICAL |
| passlib[bcrypt] | Password hashing | — | CRITICAL |
| httpx | Async HTTP client | — | HIGH |
| sentry-sdk | Error tracking | — | OPTIONAL |
| google-generativeai | Gemini AI | ≥0.8.0 | OPTIONAL |
| groq | Groq AI client | — | OPTIONAL |
| python-multipart | Form/file upload | — | MEDIUM |
| pydantic | Data validation | ≥2.0 | HIGH |
| alembic | DB migrations | — | HIGH |
| cryptography | Encryption (Fernet) | — | CRITICAL |
| webauthn | WebAuthn/FIDO2 | — | MEDIUM |
| pyyaml | YAML parsing | — | LOW |
| jinja2 | Template rendering (reports) | — | MEDIUM |
| pikepdf | PDF manipulation | — | LOW |
| qrcode[pil] | QR code generation | — | LOW |
| pytest | Testing | — | HIGH (dev) |
| pytest-asyncio | Async test support | — | HIGH (dev) |
| flake8 | Linting | — | MEDIUM (dev) |
| pyflakes | Linting | — | MEDIUM (dev) |
| bandit | Security scanning | — | MEDIUM (dev) |
| safety | CVE scanning | — | MEDIUM (dev) |

### 2.2 Node.js Packages (npm)

| Package | Purpose | Location | Criticality |
|---------|---------|----------|-------------|
| react | UI framework | frontend-v2, client | HIGH |
| firebase | Auth + Firestore | frontend-v2 | HIGH |
| @trpc/client | Type-safe RPC | client | MEDIUM |
| @trpc/react-query | React bindings | client | MEDIUM |
| vite | Build tool | frontend-v2, client | HIGH |
| typescript | Type safety | frontend-v2, client | HIGH |
| react-router-dom | Routing | frontend-v2 | MEDIUM |
| recharts | Charts | frontend-v2 | LOW |

### 2.3 System Dependencies

| Dependency | Purpose | Criticality |
|-----------|---------|-------------|
| Python ≥3.11 | Runtime | CRITICAL |
| PostgreSQL 16 | Database | CRITICAL |
| Redis 7 | Cache/Sessions | HIGH |
| nginx | Reverse proxy | CRITICAL |
| Docker + Docker Compose | Containerization | CRITICAL |
| HAProxy | Load balancing | OPTIONAL |
| Prometheus | Monitoring | OPTIONAL |
| Grafana | Visualization | OPTIONAL |
| Loki | Log aggregation | OPTIONAL |
| RabbitMQ | Message queue | OPTIONAL |
| OpenTelemetry Collector | Distributed tracing | OPTIONAL |
| MinIO | Object storage | OPTIONAL |
| Vault | Secrets management | OPTIONAL |
| cert-manager | TLS certificates | OPTIONAL |

---

## 3. Infrastructure Dependencies

### 3.1 Runtime Services

| Service | Version | Required | Connection | Pool | Fallback |
|---------|---------|----------|------------|------|----------|
| PostgreSQL | 16 | ✅ YES | TCP:5432 | 5+10/worker | — |
| Redis | 7 | ❌ Optional | TCP:6379 | — | In-memory dict |
| nginx (api-gateway) | alpine | ✅ YES | HTTP:80/443 | — | — |
| Prometheus | latest | ❌ Optional | HTTP:9090 | — | — |
| Grafana | latest | ❌ Optional | HTTP:3000 | — | — |

### 3.2 Cloud Infrastructure

| Provider | Service | Purpose | Criticality |
|----------|---------|---------|-------------|
| DigitalOcean | Droplet/App Platform | Compute | CRITICAL |
| Cloudflare | DNS, WAF, CDN, R2 | Edge/CDN | HIGH |
| Cloudflare | Workers | Serverless | OPTIONAL |
| Supabase | Postgres (alternative) | Database | OPTIONAL |
| Render | PaaS | Alternative deployment | OPTIONAL |
| GitHub | Repo hosting, CI/CD | DevOps | CRITICAL |
| GHCR | Container registry | Image storage | CRITICAL |

---

## 4. API Dependencies

### 4.1 Internal API Endpoints

| Endpoint Pattern | Service | Protocol | Consumer |
|-----------------|---------|----------|----------|
| /device-results | gula-backend | REST/HTTP | Device Bridge |
| /login | gula-backend | REST/HTTP | All frontends |
| /patients | gula-backend | REST/HTTP | All frontends |
| /results | gula-backend | REST/HTTP | All frontends |
| /health | gula-backend | REST/HTTP | Docker, Prometheus |
| /metrics/prom | gula-backend | REST/HTTP | Prometheus |

### 4.2 External API Dependencies

| External API | Endpoint | Protocol | Mode | Criticality |
|-------------|----------|----------|------|-------------|
| Iraqi MoI NID | MOI_NID_API_URL | REST/HTTPS | stub/live/shadow | HIGH |
| NHI Insurance | INSURANCE_API_URL | REST/HTTPS | stub/live/shadow | MEDIUM |
| MoI Residency | RESIDENCY_API_URL | REST/HTTPS | stub/live/shadow | MEDIUM |
| Cloudflare API | api.cloudflare.com | REST/HTTPS | stub/live/shadow | HIGH |
| Google AI (Gemini) | generativeai.googleapis.com | gRPC/REST | live | OPTIONAL |
| Groq API | api.groq.com | REST/HTTPS | live | OPTIONAL |
| Firebase APIs | firebase.googleapis.com | REST/HTTPS | live | HIGH (frontend) |

### 4.3 API Gateway Dependencies

```
Internet → Cloudflare (DNS/WAF) → host nginx (TLS) → 
  api-gateway (Docker nginx, 127.0.0.1:8080) → gula-backend (port 8000)
```

---

## 5. Data Flow Dependencies

### 5.1 Lab Result Lifecycle Data Flow
```
1. Lab Instrument → ASTM/HL7 → Device Bridge → gula_client.py → 
   POST /device-results → results.py → 
2.   ├── order_service (validate order exists, state = pending)
3.   ├── lab_result (CREATE with version=1)
4.   ├── audit_service (log create event)
5.   ├── outbox_service (queue notification event)
6.   ├── critical_alerts (check if results are critical values)
7.   └── notifications (push to doctor/patient via FCM)
```

### 5.2 Patient Identity Flow
```
1. ID Scan → /id-scan → identity service →
2.   ├── encryption (encrypt national_id with Fernet)
3.   ├── NID_HMAC (create HMAC for lookup)
4.   ├── identity_matching (MPI probabilistic matching)
5.   ├── mpi/matcher.py (score potential duplicates)
6.   ├── mpi/resolver.py (auto-merge or flag for review)
7.   └── canonical_patient (update golden record)
```

### 5.3 Audit Flow
```
Any mutation → audit_service →
  CREATE audit_log record →
    ├── previous_hash (SHA-256 chain)
    ├── table_name, record_id, action, changes
    └── old_values / new_values (JSON snapshot)
```

### 5.4 Outbox Event Flow
```
Service → outbox_event (CREATE with status=pending) →
  OutboxWorker (background loop) →
    ├── process_event (mark as processing)
    ├── dispatch (HTTP/webhook/notification)
    ├── mark as processed (processed_at = now)
    └── retry on failure (exponential backoff, max 5 attempts)
```

---

## 6. Cross-Cutting Concerns

### 6.1 Logging Dependency Chain
```
Request → RequestIDMiddleware (uuid.uuid4) →
  bind_log_context(request_id) →
    core/logging_config.py →
      Structlog/JSON formatter → stdout/stderr →
        Docker log driver → Loki → Grafana
```

### 6.2 Authentication Dependency Chain
```
Request → Authorization: Bearer <token> →
  security/dependencies.py → security/auth.py.decode_token() →
    JWT decode (HS256) → payload validation →
      get_current_user (DB lookup) →
        security/rbac.py (role check) →
          security/abac.py (attribute check, optional) →
            response
```

### 6.3 Audit Dependency Chain
```
Mutation → service/audit_service.log() →
  models/audit_log.py →
    SHA-256(previous_hash + record_id + action + timestamp) →
      INSERT into audit_logs →
        LabResult.version++ (optimistic lock)
```

### 6.4 Tenant Isolation Chain
```
get_current_user → lab_id from JWT payload →
  all queries filter by WHERE lab_id = current_user.lab_id →
    security/abac.py verifies lab_id match →
      response scoped to tenant
```

### 6.5 Self-Healing Chain
```
DB Connection Error → database.py check_db_connection_detail() →
  db_window.record(status) → sliding window count →
    If refused ≥ 20/5min → _trigger_circuit_open() →
      core/self_healing.py → CircuitState.OPEN →
        DegradedModeMiddleware → blocks writes →
          RecoveryWorker (background) → probe DB →
            If OK → half_open → circuit CLOSED
```

---

## 7. Dependency Health Metrics

### 7.1 Version Currency

| Category | Total | Current | Behind 1 Major | Behind ≥2 Major | Unknown |
|----------|-------|---------|----------------|-----------------|---------|
| Python packages | ~30 | 80% | 12% | 3% | 5% |
| npm packages | ~15 | 75% | 15% | 5% | 5% |
| System services | ~8 | 100% | 0% | 0% | 0% |
| Container images | ~5 | 100% | 0% | 0% | 0% |

### 7.2 Vulnerability Status

| Scan Type | Tool | Total Findings | Critical | High | Medium | Low |
|-----------|------|---------------|----------|------|--------|-----|
| CVE Scan | safety | 0 | 0 | 0 | 0 | 0 |
| SAST | bandit (-ll -ii) | 0 | 0 | 0 | 0 | 0 |
| Container | hadolint | 0 | 0 | 0 | 0 | 0 |
| Secrets | gitleaks | 0 | 0 | 0 | 0 | 0 |
| IaC | checkov | 0 | 0 | 0 | 0 | 0 |
| DAST | ZAP | 0 | 0 | 0 | 0 | 0 |

### 7.3 SBOM Generation
- **Tool:** scripts/generate-sbom.sh
- **Output Format:** SPDX 2.3
- **Frequency:** Per release + CI pipeline
- **Validation:** scripts/validate-sbom.sh

---

## 8. Dependency Decision Records

### DDR-001: Why FastAPI over Django?
- **Decision:** FastAPI with async support
- **Rationale:** High-throughput lab API with many concurrent device connections; async I/O for DB/Redis/HTTP; native OpenAPI docs for government interoperability; lightweight compared to Django
- **ADR Reference:** ADR-002 (Monolith-First)

### DDR-002: Why PostgreSQL 16 over MySQL/MariaDB?
- **Decision:** PostgreSQL 16
- **Rationale:** Advanced indexing (GIN, GiST for JSON/array queries), CTEs for recursive patient hierarchies, native partitioning for time-series lab results, better concurrency, pg_stat_statements for query tuning
- **ADR Reference:** ADR-005 (PostgreSQL + Redis Stack)

### DDR-003: Why Redis over Memcached?
- **Decision:** Redis with Sentinel/Cluster HA
- **Rationale:** Data structure flexibility (sets for rate limiting, sorted sets for queues, hashes for sessions), persistence (RDB/AOF for sliding window survival), pub/sub for event bus, Sentinel for HA
- **ADR Reference:** ADR-005

### DDR-004: Why Outbox Pattern over 2PC?
- **Decision:** Outbox pattern with event table
- **Rationale:** Avoids distributed transaction complexity; guarantees eventual delivery without 2PC coordinator; allows retry with backoff; audit trail via outbox_events table; works with PostgreSQL-only deployments

### DDR-005: Why Single Writer + Read Replicas over Distributed SQL?
- **Decision:** Primary + optional read replicas
- **Rationale:** Lab workloads are write-heavy but not globally distributed; read replicas provide sufficient read scaling; avoids distributed SQL complexity; patroni provides HA failover

### DDR-006: Why Fernet over AES-GCM for PII Encryption?
- **Decision:** Fernet (AES-128-CBC + HMAC)
- **Rationale:** Built into Python cryptography library; provides authenticated encryption; key rotation support; simpler API than raw AES-GCM; sufficient for national_id encryption at rest

### DDR-007: Why Gemini over OpenAI/Groq as Primary AI?
- **Decision:** Gemini 2.0 Flash as primary
- **Rationale:** Arabic language support (critical for Iraqi healthcare), free tier availability (1,500 req/day), Google AI Studio for prototyping, HIPAA-compliant enterprise tier available; Groq as secondary for low-latency inference

### DDR-008: Why In-Memory Redis Fallback over Crash?
- **Decision:** Graceful degradation with dict fallback
- **Rationale:** Lab operations must not stop when Redis is down; rate limiting and sessions degrade gracefully; sliding window loses some precision but circuit breaker still works via in-memory counts

### DDR-009: Why 3-Level Degradation over Binary Up/Down?
- **Decision:** L1_CACHE_HEAVY → L2_READ_ONLY → L3_CRITICAL_ONLY
- **Rationale:** Continuous patient care during partial outages; lab technicians can still read results (L2) even if writes are blocked; health endpoints remain accessible in L3 for monitoring; precise escalation prevents unnecessary full outages

### DDR-010: Why JWT over Session Cookies for Mobile?
- **Decision:** JWT with refresh tokens
- **Rationale:** Mobile apps need stateless auth; no server-side session storage for thousands of concurrent mobile clients; refresh tokens allow long-lived sessions (30 days) without storing credentials; Works with React Native/Flutter apps

---

## 9. Dependency Graph Visual Summary

### Layer 0 — Hardware/OS
```
DigitalOcean Droplet / DO App Platform
  ├── Ubuntu/Debian
  ├── Docker Engine 24+
  └── System Tuning (config/system/)
```

### Layer 1 — Infrastructure Services
```
PostgreSQL 16 ──────── Redis 7 ───────────── nginx
  ├── config/postgres/    ├── config/redis/      ├── config/nginx/
  ├── HA: patroni         ├── HA: sentinel        └── SSL: cert-manager
  └── DR: PITR            └── Cluster: redis-cluster
```

### Layer 2 — Application Runtime
```
Python 3.11+ ─────────── Node.js 20+ (frontend)
  ├── FastAPI                ├── React
  ├── SQLAlchemy 2.0         ├── Firebase SDK
  ├── uvicorn + gunicorn     └── Vite
  └── alembic
```

### Layer 3 — Backend Application
```
gula-backend ─────────── gula-worker
  ├── main.py                 ├── OutboxWorker
  ├── 51 route modules        ├── RecoveryWorker
  ├── 34 service modules      ├── HealthWatchdog
  ├── 25+ ORM models          ├── AdaptiveConcurrency
  ├── 17 core modules         ├── AutoRepair
  └── 15 security modules     └── TaskWorker
```

### Layer 4 — Integration Layer
```
Device Bridge ────────── nhop-platform ───────── External APIs
  ├── ASTM/HL7 parsers       ├── Citizen Registry    ├── MoI NID
  ├── vendor adapters        └── SNDHS compliance    ├── NHI Insurance
  └── gula_client.py                                └── Cloudflare
```

### Layer 5 — Frontend Layer
```
frontend-v2 (React/Firebase) ── client (tRPC/React) ── frontend (PWA)
  ├── Citizen Portal                ├── SPA               ├── Offline
  ├── Ministry Dashboard            └── tRPC API          ├── Result Viewing
  ├── Doctor Workspace                                   └── Login/Register
  └── Lab Dashboard
```

### Layer 6 — Observability
```
Prometheus ←── gula-backend (/metrics) ──→ Grafana Dashboards
    │                                              │
    └── Alertmanager (slack/pagerduty)              └── Loki (logs)
         │                                                    │
         └── ALERT_WEBHOOK_URL (Telegram/Discord/Slack)       └── OpenTelemetry
```

---

## 10. Dependency Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| PyPI package vulnerability | LOW | HIGH | safety scan in CI, automated PRs |
| PostgreSQL 16 EOL (2028) | LOW | CRITICAL | Migration plan ready for v17+ |
| Redis license change | LOW | MEDIUM | In-memory fallback, Valkey migration path |
| Google AI Gemini deprecation | LOW | MEDIUM | Generic AI provider abstraction |
| Firebase pricing change | MEDIUM | MEDIUM | Migration to self-hosted alternative |
| Docker Compose deprecation | LOW | MEDIUM | Kubernetes overlay already prepared |
| Single cloud provider lock-in | MEDIUM | HIGH | Terraform modules support multiple providers |
| npm package vulnerability | LOW | MEDIUM | Dependabot + lockfile verification |

---

*End of Dependency Genome — Complete dependency map with 10 sections covering internal, external, infrastructure, API, data flow, cross-cutting concerns, health metrics, and decision records.*
