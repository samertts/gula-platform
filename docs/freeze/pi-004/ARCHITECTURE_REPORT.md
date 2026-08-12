# PI-004: National Deployment, Operations & Resilience Platform

## Architecture Report

**Version:** 1.0.0
**App Version:** 2.1.0
**Date:** 2026-07-16

---

### 1. Multi-Node, High-Availability Architecture

#### 1.1 Regional Topology

```
┌─────────────────────────────────────────────────────────────────────┐
│                        GULA Platform                                │
│                                                                     │
│   ┌────────── Primary Region (me-central1) ──────────┐              │
│   │    Baghdad, Iraq — DigitalOcean (fra1)           │              │
│   │                                                    │              │
│   │  Internet → Host nginx (TLS) → api-gateway       │              │
│   │               → gula-backend (FastAPI)            │              │
│   │               → PostgreSQL 16 (Patroni HA)        │              │
│   │               → Redis 7 (Sentinel HA)             │              │
│   │               → MinIO (Distributed, 4 nodes)      │              │
│   │               → RabbitMQ (3-node cluster)          │              │
│   └────────────────────────────────────────────────────┘              │
│                          │                                           │
│                          ▼ (async replication)                       │
│   ┌────────── DR Region (eu-west1) ──────────────────┐              │
│   │    Frankfurt, Germany — DigitalOcean (fra1-alt)  │              │
│   │    Standby PostgreSQL (streaming replication)    │              │
│   │    RabbitMQ Shovel (async message replication)   │              │
│   │    MinIO Bucket Replication (async)              │              │
│   └────────────────────────────────────────────────────┘              │
└─────────────────────────────────────────────────────────────────────┘
```

Reference: `config/dr/cross-region-replication.yml`

#### 1.2 Request Lifecycle

```
Internet → Host nginx (TLS 1.3, port 443)
         → Docker api-gateway (127.0.0.1:8080, nginx reverse proxy)
         → gula-backend (FastAPI, gunicorn + uvicorn workers)
         → PostgreSQL 16 + Redis 7
```

All backends expose no public ports. All traffic enters through the gateway (`docker-compose.yml:268`):

```yaml
ports:
  - "127.0.0.1:8080:80"  # api-gateway bound to localhost only
```

#### 1.3 Middleware Stack (Ordered)

Defined in `backend/app/main.py`:

1. `MaxBodySizeMiddleware` — 413 above MAX_REQUEST_BODY_MB (default 10)
2. `RequestIDMiddleware` — X-Request-ID + log ctx + DB correlation vars
3. `DocsAuthMiddleware` — guards /docs, /redoc, /openapi.json in production
4. `CORSMiddleware`
5. `RequestTimingMiddleware` — access log + X-Response-Time header
6. `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options, etc.
7. `GZipMiddleware`
8. `ReadinessMiddleware` — 503 until system_ready is True
9. `DegradedModeMiddleware` — rejects writes when DB circuit is open
10. `ConcurrencyLimitMiddleware` — per-worker in-flight cap (default 50)

Clinical writes (`/results`, `/orders`, `/samples`, `/critical-alerts`) are **exempt** from concurrency shedding — patient-safety operations must never be dropped.

#### 1.4 High Availability Guarantees

| Component | Mechanism | RTO |
|-----------|-----------|-----|
| PostgreSQL | Patroni HA (auto-failover, <30s detection) | <5m |
| Redis | Sentinel (auto-failover, 5s detection) | <30s |
| RabbitMQ | Mirrored queues, 3-node cluster | <10s |
| MinIO | Erasure coding, 4-node distributed | <1s |
| Backend API | Docker restart, health checks, LB | <15s |
| API Gateway | Nginx, multiple workers | <5s |

---

### 2. Zero-Trust Security Model

#### 2.1 Core Principles

Defined in `config/zero-trust/zero-trust-policy.yaml`:

1. **Never Trust, Always Verify** — No entity trusted by network location or prior verification
2. **Assume Breach** — Design assuming attacker is already present
3. **Least Privilege** — Minimum permissions, default deny
4. **Continuous Verification** — Every 60s revalidation

#### 2.2 Implementation

| Requirement | Implementation | Config File |
|-------------|---------------|-------------|
| mTLS all traffic | Linkerd service mesh | `linkerd-policy.yaml` |
| RBAC/ABAC | 9 RBAC roles + lab_id tenant isolation | `backend/app/security/rbac.py` |
| Network segmentation | AuthorizationPolicy per service | `linkerd-policy.yaml` |
| JWT authentication | FastAPI middleware | `backend/app/security/auth.py` |
| Audit logging | Immutable hash chain | `backend/app/audit/` |

#### 2.3 Service-to-Service Authorization Matrix

From `config/zero-trust/zero-trust-policy.yaml` appendix:

```
Source \ Target    | backend | worker | postgres | redis | rabbitmq
-------------------|---------|--------|----------|-------|---------
api-gateway        |  ALLOW  |  DENY  |   DENY   | DENY  |   DENY
gula-backend       |  ALLOW  |  ALLOW |   ALLOW  | ALLOW |   ALLOW
gula-worker        |  ALLOW  |  ALLOW |   ALLOW  | ALLOW |   ALLOW
device-bridge      |  ALLOW  |  DENY  |   DENY   | DENY  |   DENY
prometheus         |  ALLOW  |  ALLOW |   DENY   | DENY  |   DENY
grafana            |  DENY   |  DENY  |   DENY   | DENY  |   DENY
```

#### 2.4 mTLS Certificate Rotation

- Rotation interval: 24 hours (Linkerd default)
- SPIFFE-compliant identities for all workloads
- Certificate authority: Linkerd identity controller

---

### 3. Network Topology & Ingress

#### 3.1 Ingress Architecture

```
Internet
    │
    ▼
Host nginx (ports 80/443, TLS termination via Let's Encrypt)
    │
    ▼
Docker api-gateway (127.0.0.1:8080, nginx reverse proxy)
    ├── /api/* → gula-backend:8000
    ├── /      → frontend:80
    ├── /health → bypass rate limits
    └── /metrics → 404 (deny external)
```

#### 3.2 Kubernetes Ingress (`helm/gula-platform/values.yaml:594-651`)

```yaml
ingress:
  enabled: true
  className: nginx
  annotations:
    nginx.ingress.kubernetes.io/use-regex: "true"
    nginx.ingress.kubernetes.io/proxy-body-size: "10m"
    nginx.ingress.kubernetes.io/limit-rpm: "100"
    nginx.ingress.kubernetes.io/waf: "owasp-crs"
    nginx.ingress.kubernetes.io/modsecurity: "on"
    cert-manager.io/cluster-issuer: "letsencrypt-prod"
```

#### 3.3 DNS Architecture

| Domain | Purpose | Provider |
|--------|---------|----------|
| `gula-platform.org` | Main platform | Cloudflare |
| `*.gula.health` | Production API | Cloudflare (DNS01) |
| `api.gula-platform.org` | API endpoint | Cloudflare |
| `admin.gula.health` | Admin panel | Cloudflare |

#### 3.4 Network Security

- **Rate limiting zones** (`config/nginx/nginx.conf:131-136`):
  - `api_limit`: 120r/m
  - `auth_limit`: 10r/m
  - `upload_limit`: 20r/m
  - `health_limit`: 120r/m
  - `conn_limit`: per-IP connection limit
- **Fail2ban** (`config/ids/fail2ban-config.local`): 6 jails (auth, api, admin, rate-limit, WAF, recidivism)
- **Snort IDS** (`config/ids/snort-rules/local.rules`): 10 sections covering SQLi, XSS, path traversal, command injection, SSRF, API abuse, scanner detection, auth attacks, data exfiltration
- **SELinux/AppArmor** (`config/runtime-protection/apparmor-profile`)
- **Seccomp** (`config/runtime-protection/seccomp-profile.json`)

#### 3.5 Runtime Protection

- `security_opt: no-new-privileges:true` on all containers
- Read-only root filesystem (Helm default)
- Seccomp: `RuntimeDefault` profile
- Non-root user (UID 1000)

---

### 4. Self-Healing & Auto-Repair

#### 4.1 Three-Layer Self-Healing

**Layer 1: Circuit Breaker** (`backend/app/core/self_healing.py`)

Three degradation levels:

| Level | State | Behavior |
|-------|-------|----------|
| L1 | NORMAL | Full read/write, all endpoints operational |
| L2 | READ_ONLY | DB circuit open → writes return 503, reads pass |
| L3 | CRITICAL_ONLY | DB storm → only health, auth, kill-switch, metrics reachable |

Recovery: DB probed every 10s; circuit closes after 3 consecutive successful health checks.

**Layer 2: Auto-Repair Engine** (`backend/app/core/auto_repair.py`)

Automatic actions:
- Garbage collection when memory exceeds threshold
- Connection pool recycle when stale connections detected
- Automatic reconnect on transient network failures

**Layer 3: Adaptive Concurrency** (`backend/app/main.py::_adaptive_concurrency_loop`)

- Halves `_MAX_CONCURRENT` on 2 slow DB readings (>300ms)
- Restores after 3 consecutive fast readings (<150ms)
- Runs every 30s in background worker

#### 4.2 Self-Healing Scripts

| Script | Function | Location |
|--------|----------|----------|
| `auto_heal.sh` | Automated healing actions | `scripts/auto_heal.sh` |
| `self_heal.py` | Python self-healing daemon | `scripts/self_heal.py` |
| `gula_autofix.py` | Automated fix application | `scripts/gula_autofix.py` |
| `self-heal/auto-failover.sh` | Automated PostgreSQL failover | `scripts/self-heal/auto-failover.sh` |
| `emergency-fix.sh` | Emergency repair | `scripts/emergency-fix.sh` |
| `fix-server.sh` | Server-level repair | `scripts/fix-server.sh` |

#### 4.3 Health Alert Watchdog

The `_health_alert_loop` (defined in `backend/app/main.py`):
- Runs every `HEALTH_ALERT_INTERVAL_SECONDS` (default 60)
- Scores system GREEN/YELLOW/RED
- Fires `ALERT_WEBHOOK_URL` on transitions
- Sends RED reminders every 5 minutes

#### 4.4 Architecture Guardian (`scripts/architecture_guardian.py`)

Automated architecture compliance validation:

```bash
python3 scripts/architecture_guardian.py
```

#### 4.5 Quality Gates (`config/quality-gates/`)

Pre-deployment validation gates:

| Gate | File | What It Checks |
|------|------|----------------|
| Architecture | `architecture-gate.py` | Architecture compliance against defined patterns |
| Security | `security-gate.py` | Security posture and vulnerability thresholds |
| Performance | `performance-gate.py` | Performance baseline (latency, throughput) |
| Database | `database-gate.py` | Schema validity and migration idempotency |
| Scalability | `scalability-gate.py` | Scaling behavior under load |
| FHIR | `fhir-gate.py` | FHIR interoperability compliance |
| CI Quality | `architecture-gate-ci.yml` | CI pipeline gate |

---

### 5. Worker Process Architecture

#### 5.1 Process Separation

The monolith runs two separate processes:

| Process | Image | Container | RUNTIME_MODE |
|---------|-------|-----------|-------------|
| API Server | `backend/` | `gula-backend` | `api` |
| Background Worker | `backend/` | `gula-worker` | `worker` |

Worker responsibilities (`docker-compose.yml:204`):
- Outbox dispatch (guaranteed event delivery)
- Recovery probes
- Health watchdog
- Adaptive concurrency management
- Auto-repair engine

#### 5.2 Startup Guard (`backend/app/core/startup_guard.py`)

Blocks readiness until:
1. Config validated (no weak/missing secrets)
2. DB reachable
3. Migrations checked (Alembic)
4. Critical data seeded

Until passes, `system_ready = False` and `ReadinessMiddleware` returns 503 for all paths except health-check whitelist.

---

**References:** `config/dr/cross-region-replication.yml`, `config/zero-trust/`, `config/nginx/`, `config/ids/`, `config/runtime-protection/`, `config/quality-gates/`, `backend/app/core/self_healing.py`, `backend/app/core/auto_repair.py`, `backend/app/core/startup_guard.py`, `scripts/architecture_guardian.py`, `scripts/self_heal.py`, `scripts/auto_heal.sh`
