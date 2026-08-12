# GULA Platform — Production Guide v1.0

**Version:** 1.0
**Date:** 2026-07-15
**Status:** FINAL

---

## 1. Platform Overview

GULA is a national healthcare platform serving Iraqi medical laboratories. It is a monorepo consolidating three previously separate repositories into a single deployable unit.

- **Monorepo** with FastAPI monolith backend + React/Firebase frontend
- **PostgreSQL 16** + **Redis 7** backend
- **99.99%** availability target
- **Arabic-first**, FHIR-native
- **Self-healing**, offline-capable
- **Multi-tenant** with strict lab-level isolation
- **Field-level encryption** for PII

### Core Principles

1. **Stability first** — never break working code to add features
2. **Data integrity above all** — no change may risk patient data loss
3. **Fix before feature** — bugs and security issues take priority
4. **Test then commit** — all changes verified before deployment

---

## 2. Architecture Summary

### Request Lifecycle

```
Internet → Cloudflare (CDN/WAF/DDoS)
  → Host Nginx (TLS termination)
    → api-gateway (Docker nginx on 127.0.0.1:8080)
      → gula-backend (FastAPI, gunicorn + uvicorn workers, port 8000)
        → PostgreSQL 16 (primary + replicas)
        → Redis 7 (cache + rate limiting)
        → RabbitMQ (async messaging)
        → MinIO (object storage)
```

The backend never exposes a public port. All traffic enters through the Cloudflare edge, then through host Nginx, then through the internal api-gateway.

### Middleware Stack (order matters)

Requests flow through these layers in order:

1. `MaxBodySizeMiddleware` — 413 above `MAX_REQUEST_BODY_MB` (default 10)
2. `RequestIDMiddleware` — assigns `X-Request-ID` + binds to log ctx + DB correlation vars
3. `DocsAuthMiddleware` — guards `/docs`, `/redoc`, `/openapi.json` in production (admin JWT)
4. `CORSMiddleware`
5. `RequestTimingMiddleware` — per-request access log, `X-Response-Time` header
6. `SecurityHeadersMiddleware` — CSP, HSTS, X-Frame-Options, etc.
7. `GZipMiddleware`
8. `ReadinessMiddleware` — 503 on all non-whitelisted paths until `system_ready` is True
9. `DegradedModeMiddleware` — rejects writes when DB circuit is open
10. `ConcurrencyLimitMiddleware` — per-worker in-flight cap (`MAX_CONCURRENT_REQUESTS`, default 50)

### Self-Healing (3 Layers)

1. **Circuit Breaker** — isolates failing DB/Redis; flips to degraded mode
2. **Auto-Repair Engine** — GC, pool recycle, reconnects
3. **Adaptive Concurrency** — halves `_MAX_CONCURRENT` on 2 slow DB readings (>300ms); restores after 3 fast (<150ms)

### Service Components

| Component | Technology | Role |
|-----------|-----------|------|
| Backend API | FastAPI + gunicorn + uvicorn | Business logic, routing, auth |
| PostgreSQL 16 | Patroni HA | Primary data store |
| Redis 7 | Sentinel HA | Cache, session, rate limiting |
| RabbitMQ | 3-node cluster | Async messaging, outbox pattern |
| MinIO | 4-node distributed | Object storage (reports, artifacts) |
| Nginx | api-gateway | Internal reverse proxy |
| Cloudflare | Edge network | CDN, WAF, DDoS, DNS, TLS |
| Prometheus + Grafana | Monitoring | Metrics, dashboards, alerts |
| Loki | Log aggregation | Centralized logging |
| Tempo | Distributed tracing | Trace analysis |
| Linkerd | Service mesh | mTLS, traffic splitting |
| Cert-manager | Certificate management | Let's Encrypt auto-renewal |

---

## 3. Infrastructure Requirements

### Minimum (Development/Staging)

| Resource | Value |
|----------|-------|
| vCPU | 4 cores |
| RAM | 8 GB |
| SSD | 50 GB |
| Network | 100 Mbps |

### Recommended (Production Single Node)

| Resource | Value |
|----------|-------|
| vCPU | 8 cores |
| RAM | 16 GB |
| SSD | 100 GB |
| Network | 1 Gbps |

### Production HA (3+ Node Cluster)

| Resource | Per Node |
|----------|----------|
| vCPU | 8 cores |
| RAM | 16 GB |
| SSD | 100 GB (NVMe) |
| Network | 1 Gbps internal, 100 Mbps public |

### Operating System

- **Ubuntu 22.04 LTS** (recommended)
- **Debian 12** (supported)
- All nodes must have identical OS and kernel versions

### Software Dependencies

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Orchestration |
| Kubernetes | 1.28+ | Container orchestration (K8s deployment) |
| Helm | 3.12+ | Package manager (K8s deployment) |
| Python | 3.11+ | Application runtime |
| Node.js | 20 LTS | Frontend build |
| PostgreSQL | 16 | Database |
| Redis | 7 | Cache |

---

## 4. Network Topology

### Network Diagram

```
Internet
    │
    ▼
Cloudflare Edge (CDN, WAF, DDoS)
    │
    ├── api.gula.health ─────► Host Nginx:443
    │                               │
    │                               ▼
    │                         api-gateway:8080
    │                               │
    │                               ▼
    │                         gula-backend:8000
    │                               │
    │                     ┌─────────┼─────────┐
    │                     ▼         ▼         ▼
    │               postgres:5432  redis:6379  rabbitmq:5672
    │                     │         │         │
    │                     ▼         ▼         ▼
    │               patroni/HA  sentinel/HA   mirrored queues
    │
    ├── app.gula.health ────► Frontend CDN (Cloudflare Pages)
    │
    └── *.gula.health ──────► Private DNS (internal only)
```

### Firewall Rules

| Source | Destination | Port | Protocol | Purpose |
|--------|-------------|------|----------|---------|
| Internet | Host | 80, 443 | TCP | HTTP/HTTPS (Cloudflare proxied) |
| api-gateway | backend | 8000 | TCP | Internal API traffic |
| backend | postgres | 5432 | TCP | Database connections |
| backend | redis | 6379 | TCP | Cache access |
| backend | rabbitmq | 5672, 15672 | TCP | Messaging |
| backend | minio | 9000, 9001 | TCP | Object storage |
| Admin VPN | Host | 22 | TCP | SSH access |
| Monitoring | Host | 9090, 3000, 3100 | TCP | Internal monitoring |
| Nodes (inter-node) | All | 0-65535 | TCP | Cluster communication |

### Security Groups

- **public-subnet**: 80, 443 from 0.0.0.0/0
- **private-subnet**: no public access, inter-node only
- **admin-subnet**: 22 from authorized admin IPs only
- **monitor-subnet**: 9090, 3000 from monitoring IPs only

---

## 5. DNS Configuration

### Public DNS

| Record | Type | Value | Notes |
|--------|------|-------|-------|
| `api.gula.health` | A | Cloudflare edge IPs | Proxied through Cloudflare |
| `app.gula.health` | A | Cloudflare edge IPs | Frontend SPA |
| `www.gula.health` | CNAME | `app.gula.health` | Redirect to app |
| `gula.health` | A | Cloudflare edge IPs | Marketing/landing |

### Internal DNS (Private)

| Record | Type | Value |
|--------|------|-------|
| `postgres-primary.gula.internal` | A | Primary node private IP |
| `postgres-replica-1.gula.internal` | A | Replica 1 private IP |
| `postgres-replica-2.gula.internal` | A | Replica 2 private IP |
| `redis-master.gula.internal` | A | Redis master private IP |
| `redis-replica-1.gula.internal` | A | Redis replica 1 private IP |
| `redis-replica-2.gula.internal` | A | Redis replica 2 private IP |
| `rabbitmq-1.gula.internal` | A | RabbitMQ node 1 |
| `rabbitmq-2.gula.internal` | A | RabbitMQ node 2 |
| `rabbitmq-3.gula.internal` | A | RabbitMQ node 3 |
| `minio-1.gula.internal` | A | MinIO node 1 |
| `minio-2.gula.internal` | A | MinIO node 2 |
| `minio-3.gula.internal` | A | MinIO node 3 |
| `minio-4.gula.internal` | A | MinIO node 4 |
| `api.gula.internal` | A | api-gateway private IP |
| `backend.gula.internal` | A | Backend service IP |

### DNS Propagation

- Public DNS: Cloudflare-managed, propagation within seconds
- Internal DNS: CoreDNS (K8s) or dnsmasq (Docker), instant updates
- TTL: 300s for production records, 60s for failover records

---

## 6. TLS/SSL

### Certificate Management

| Component | Provider | Method | Renewal |
|-----------|----------|--------|---------|
| `api.gula.health` | Let's Encrypt | cert-manager (K8s) / certbot (Docker) | Auto, 30d before expiry |
| `app.gula.health` | Cloudflare | Edge certificate | Auto-managed |
| Internal mTLS | Linkerd | Auto-generated | Auto-rotated every 24h |

### HSTS Configuration

```
Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
```

### TLS Versions

- Minimum: TLS 1.2
- Preferred: TLS 1.3
- Disabled: TLS 1.0, TLS 1.1, SSLv2, SSLv3

### Cipher Suites (TLS 1.3)

```
TLS_AES_128_GCM_SHA256
TLS_AES_256_GCM_SHA384
TLS_CHACHA20_POLY1305_SHA256
```

### Certbot Auto-Renewal (Docker Deployment)

```bash
# Install certbot
apt-get install certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d api.gula.health --non-interactive --agree-tos -m admin@gula.health

# Auto-renewal (systemd timer)
systemctl enable certbot.timer
systemctl start certbot.timer

# Verify renewal
certbot renew --dry-run
```

### Cert-Manager (K8s Deployment)

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@gula.health
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
```

---

## 7. Storage

### Storage Requirements

| Service | Base Size | Growth Rate | Retention |
|---------|-----------|-------------|-----------|
| PostgreSQL | 10 GB | 1 GB/day | Full duration |
| PostgreSQL WAL | 500 MB | 5 GB/day | Until archived |
| MinIO (reports) | 5 GB | 500 MB/day | 90 days |
| MinIO (artifacts) | 1 GB | 100 MB/day | 30 days |
| Redis | 256 MB | — | Ephemeral |
| Logs (Loki) | 2 GB | 200 MB/day | 30 days |
| Backups | 30 GB | 3 GB/day | 90 days |
| Prometheus | 5 GB | 500 MB/day | 30 days |

### Storage Architecture

- **PostgreSQL**: SSD/NVMe for data directory, separate SSD for WAL
- **MinIO**: RAID-10 SSD for performance, erasure coding for durability
- **Redis**: RAM only, RDB snapshots to SSD
- **Backups**: HDD/object storage for cost efficiency
- **Logs**: SSD for hot tier, object storage for cold tier

### Backup Storage Calculation

```
Daily data growth: 1 GB (DB) + 5 GB (WAL) + 500 MB (MinIO) = ~6.5 GB
Monthly data growth: ~195 GB
90-day retention: ~585 GB total
Backup overhead (compression, indexes): ~20%
Total backup storage needed: ~700 GB
```

### Filesystem Layout

| Mount Point | Size | Filesystem | Purpose |
|-------------|------|------------|---------|
| `/var/lib/postgresql/data` | 100 GB | ext4/XFS | PostgreSQL data |
| `/var/lib/postgresql/wal` | 50 GB | ext4/XFS | WAL files |
| `/var/lib/minio` | 200 GB | ext4/XFS | Object storage |
| `/var/lib/redis` | 10 GB | ext4/XFS | Redis persistence |
| `/var/log/gula` | 20 GB | ext4/XFS | Application logs |
| `/backups` | 1 TB | ext4/XFS | Backup storage |

---

## 8. Performance Baseline

### Throughput

| Metric | Normal Load | Peak Load | Breaking Point |
|--------|-------------|-----------|----------------|
| Requests/second | 200 | 500 | 1,200 |
| Concurrent users | 500 | 1,000 | 2,500 |

### Latency (Single Backend Instance)

| Percentile | Normal Load | Peak Load |
|------------|-------------|-----------|
| p50 | <50 ms | <80 ms |
| p95 | <200 ms | <320 ms |
| p99 | <500 ms | <650 ms |

### Error Rate

| Condition | Target | Threshold |
|-----------|--------|-----------|
| Normal | <0.1% | >0.5% alert |
| Peak | <1% | >2% alert |
| Breaking | >5% | Auto-scaling trigger |

### Database Performance

| Metric | Value |
|--------|-------|
| Max connections | 100 (default) |
| Connection pool (per worker) | 6 |
| Pool overflow (per worker) | 12 |
| Query latency p95 | <100 ms |
| Write throughput | 5,000 tps |
| Cache hit ratio | >95% |

### Resource Utilization

| Resource | Normal | Peak | Alert Threshold |
|----------|--------|------|-----------------|
| CPU | 30-40% | 60-70% | >80% for 5min |
| Memory | 50-60% | 70-80% | >90% for 5min |
| Disk I/O | 20-30% | 40-50% | >80% for 10min |
| Network | 10-20% | 30-40% | >70% for 5min |

---

## 9. High Availability

### Architecture Overview

```
                         ┌──────────────┐
                         │  Cloudflare   │
                         │ (Global LB)   │
                         └──────┬───────┘
                                │
                        ┌───────┴───────┐
                        │  Host Nginx   │
                        │ (TLS term.)   │
                        └───────┬───────┘
                                │
                        ┌───────┴───────┐
                        │  api-gateway  │
                        │ (nginx:8080)  │
                        └───────┬───────┘
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
           ┌──────────┐  ┌──────────┐  ┌──────────┐
           │ backend 1│  │ backend 2│  │ backend 3│
           │ (uvicorn)│  │ (uvicorn)│  │ (uvicorn)│
           └────┬─────┘  └────┬─────┘  └────┬─────┘
                │             │             │
                └─────────────┼─────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
            ┌───────▼───────┐   ┌───────▼───────┐
            │  PostgreSQL   │   │  Redis Sentinel│
            │ Patroni HA    │   │  3-node cluster│
            │ primary+2 repl│   │  1M + 2R       │
            └───────────────┘   └───────────────┘
```

### Component HA Configuration

| Component | Strategy | Nodes | Failover Time |
|-----------|----------|-------|---------------|
| Backend | Blue-green deployment | 2+ replicas | <10s |
| PostgreSQL | Patroni + streaming replication | 1 primary + 2 replicas | <30s |
| Redis | Sentinel | 1 master + 2 replicas | <10s |
| RabbitMQ | Mirrored queues | 3-node cluster | <5s |
| MinIO | Erasure coding | 4 nodes (16:8) | <5s |
| api-gateway | Health check + failover | 2 instances | <5s |

### Blue-Green Deployment

```
Blue (current) ───► Green (new)
    │                      │
    │  1. Deploy Green     │
    │  2. Smoke tests      │
    │  3. Switch traffic   │
    └──────────────────────┘
    │                      │
    │  4. Verify Green     │
    │  5. Keep Blue standby│
    └──────────────────────┘
```

### Health Check Configuration

| Check | Interval | Timeout | Unhealthy Threshold |
|-------|----------|---------|---------------------|
| `/health/live` | 10s | 5s | 3 failures |
| `/health/ready` | 15s | 5s | 3 failures |
| `/health/deep` | 60s | 10s | 2 failures |

---

## 10. Disaster Recovery

### Recovery Objectives

| Metric | Target |
|--------|--------|
| RPO (Recovery Point Objective) | 5 seconds |
| RTO (Recovery Time Objective) | 5 minutes |
| Availability SLA | 99.99% |
| Max data loss | 5 seconds of transactions |

### DR Topology

```
┌──────────────────────┐        ┌──────────────────────┐
│   ME Region          │        │   EU Region          │
│   (Primary)          │────────│   (DR)               │
│                      │ WAL    │                      │
│  PostgreSQL Primary  │ stream │  PostgreSQL Replica  │
│  Redis Master        │───────►│  Redis Replica       │
│  RabbitMQ Primary    │ async  │  RabbitMQ Replica    │
│  MinIO Primary       │        │  MinIO Replica       │
│                      │        │                      │
│  Cloudflare          │        │  Cloudflare          │
│  (Active)            │        │  (Passive)           │
└──────────────────────┘        └──────────────────────┘
```

### Backup Schedule

| Type | Frequency | Retention | Location |
|------|-----------|-----------|----------|
| WAL archive | Continuous (5s) | 7 days | S3-compatible storage |
| Full backup | Daily | 90 days | S3-compatible storage |
| Weekly backup | Weekly | 52 weeks | S3-compatible storage |
| Monthly backup | Monthly | 36 months | Cold storage |
| Logical dump | Weekly | 4 weeks | Separate region |

### Failure Scenarios & Recovery

| Scenario | Detection | Action | RTO |
|----------|-----------|--------|-----|
| Pod/container failure | Health check fails | K8s auto-restart | <30s |
| Node failure | Node heartbeat lost | Pod rescheduled to healthy node | <2min |
| DB primary failure | Patroni detection | Automatic replica promotion | <30s |
| DB replica failure | Patroni detection | New replica synced from primary | <5min |
| Cache failure | Sentinel detection | Slave promotion | <10s |
| Queue failure | RabbitMQ detection | Mirrored queue failover | <5s |
| Storage failure | MinIO detection | Erasure coding rebuild | <5min |
| Region failure | Cloudflare health check | DNS failover to DR region | <5min |
| Data corruption | Monitoring alert | PITR from last good backup | <1h |

See complete DR procedures in [Disaster Recovery Guide](DISASTER_RECOVERY_GUIDE.md).

---

## 11. Security

### Security Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Cloudflare Edge                    │
│          WAF + DDoS Protection + CDN + TLS           │
└──────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│                   Host Nginx                         │
│            TLS Termination + Rate Limiting           │
└──────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│                   Linkerd Service Mesh               │
│             mTLS + Traffic Splitting + Metrics       │
└──────────────────────────────────────────────────────┘
                          │
┌─────────────────────────────────────────────────────┐
│                gula-backend (FastAPI)                │
│   JWT Auth + RBAC + ABAC + Audit + Encryption       │
│   Rate Limiting + Input Validation + CSP/HPKP/HSTS  │
└──────────────────────────────────────────────────────┘
```

### Authentication & Authorization

- **JWT**: Short-lived access tokens (15min), long-lived refresh tokens (7 days)
- **RBAC**: 9 roles × 13 permissions across lab, doctor, patient, admin tiers
- **ABAC**: Attribute-based access for sensitive operations (national ID, financial data)
- **Consent**: Patient consent management for data sharing

### Data Protection

| Data Type | At Rest | In Transit |
|-----------|---------|------------|
| Patient PII | AES-256 field-level encryption | TLS 1.3 |
| National ID | AES-256 + HMAC signature | TLS 1.3 |
| Clinical results | Database-level encryption | TLS 1.3 |
| Credentials | bcrypt hashing | Cannot transit |
| API keys | Hashicorp Vault | TLS 1.3 |
| Audit logs | SHA-256 hash chain | TLS 1.3 |

### Network Security

- **WAF**: Cloudflare Managed Ruleset + custom OWASP rules
- **DDoS**: Cloudflare DDoS protection (L3/L4/L7)
- **IDS/IPS**: Cloudflare + host-level fail2ban
- **Rate Limiting**: Per-IP, per-endpoint, per-tenant (Redis-backed)
- **mTLS**: Linkerd service mesh for inter-service communication

### Secrets Management

- **Production secrets**: Hashicorp Vault (K8s) or encrypted `.env` (Docker)
- **Key rotation**: Automatic every 90 days, manual on compromise
- **No hardcoded secrets**: All secrets fail hard in `config.py`
- **Weak secret detection**: `_is_weak_secret()` validates minimum entropy

### Audit Logging

- All mutations are logged to `audit_logs` table
- SHA-256 hash chain ensures immutability
- Correlated by `X-Request-ID` across all services
- 7-year retention for compliance
- Real-time anomaly detection on audit stream

---

## 12. Monitoring

### Stack Components

| Component | Purpose | Retention | Access |
|-----------|---------|-----------|--------|
| Prometheus | Metrics collection | 30 days | Internal + Grafana |
| Grafana | Dashboards & alerts | — | VPN + SSO auth |
| Loki | Log aggregation | 30 days | Grafana Explore |
| Tempo | Distributed tracing | 7 days | Grafana Explore |
| Alertmanager | Alert routing | — | Slack, PagerDuty, Email |
| OpenTelemetry | Instrumentation | — | All services |

### Critical Dashboards

| Dashboard | Purpose | Refresh |
|-----------|---------|---------|
| GULA Platform Overview | System-wide health, request rate, error rate, latency | 15s |
| Database Performance | Query latency, connections, cache hit ratio, replication lag | 15s |
| Redis Performance | Memory, hit rate, command latency, connected clients | 15s |
| RabbitMQ Overview | Queue depth, message rate, consumer lag | 15s |
| Kubernetes Overview | Pod health, resource usage, node status | 30s |
| Business Metrics | Active labs, orders/day, results/day, alerts | 1min |
| Security Overview | Failed auth, rate limit hits, WAF blocks, audit anomalies | 1min |
| Cost & Capacity | Resource costs, growth trends, capacity forecasts | 1h |

### Alert Rules

| Alert | Condition | Severity | Channel |
|-------|-----------|----------|---------|
| Backend down | `/health` returns non-200 | CRITICAL | PagerDuty + Slack |
| Error rate spike | >1% 5xx errors (5min window) | CRITICAL | PagerDuty + Slack |
| High latency p95 | >500ms (5min window) | WARNING | Slack |
| DB connection pool exhaustion | >80% connections used | CRITICAL | PagerDuty + Slack |
| Replication lag | >10s (Patroni) | CRITICAL | PagerDuty + Slack |
| Disk space | <20% free on any volume | WARNING | Slack |
| Certificate expiry | <30 days | WARNING | Slack + Email |
| Certificate expiry | <7 days | CRITICAL | PagerDuty + Slack |
| Rate limit threshold | >80% of limit (5min window) | WARNING | Slack |
| WAF blocks spike | >100 blocks in 5min | WARNING | Slack |

### SLIs/SLOs

| SLI | Target | SLO |
|-----|--------|-----|
| API availability (HTTP 200) | 99.99% | 99.95% |
| API latency p95 | <200ms | <500ms |
| API latency p99 | <500ms | <1s |
| Database availability | 99.99% | 99.95% |
| Database query latency p95 | <100ms | <500ms |
| Cache hit ratio | >95% | >90% |
| Backup success rate | 100% | 99.9% |
| Deployment success rate | 99% | 95% |

---

## 13. Scaling

### Scaling Strategy

| Tier | Backend Replicas | DB Connections | Redis | Notes |
|------|-----------------|---------------|-------|-------|
| SMB | 2 | 50 | Single | <10 labs |
| Growth | 4 | 100 | Sentinel | 10-100 labs |
| Enterprise | 8 | 200 | Cluster | 100-500 labs |
| National | 16+ | 400 | Cluster | 500+ labs |

### Vertical Scaling

```yaml
# docker-compose.override.yml
services:
  gula-backend:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
        reservations:
          cpus: '2'
          memory: 4G
```

### Horizontal Scaling

```bash
# Docker Compose
docker compose up -d --scale gula-backend=5

# With HAProxy
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d --scale gula-backend=5

# Kubernetes HPA
kubectl autoscale deployment gula-backend --cpu-percent=70 --min=2 --max=10
```

### Database Scaling

1. **Read replicas** (up to 3): Offload reporting, analytics, read-heavy queries
2. **Connection pooling**: PgBouncer for high-connection environments
3. **Vertical**: Increase CPU/RAM on primary
4. **Sharding**: Horizontal sharding by `lab_id` beyond 500 labs
5. **Citus**: Distributed PostgreSQL for analytics workloads

### Cache Scaling

- **Redis Cluster**: Partition data across nodes (up to 1000 nodes)
- **Read replicas**: Offload read traffic
- **Memory management**: Eviction policy `allkeys-lru`
- **Persistence**: RDB snapshots + AOF for durability

### Cost Analysis per Tier

| Tier | Monthly Infrastructure Cost | Monthly Ops Cost | Total |
|------|---------------------------|-----------------|-------|
| SMB | $500-1,000 | $1,000-2,000 | $1,500-3,000 |
| Growth | $2,000-4,000 | $3,000-5,000 | $5,000-9,000 |
| Enterprise | $5,000-10,000 | $5,000-10,000 | $10,000-20,000 |
| National | $15,000-30,000 | $10,000-20,000 | $25,000-50,000 |

---

## 14. Upgrades

### Versioning

```
v<major>.<minor>.<patch>
- Major: Breaking changes, DB migrations requiring downtime
- Minor: New features, backward-compatible
- Patch: Bug fixes, security patches
```

### Upgrade Types

| Type | Downtime | Duration | Process |
|------|----------|----------|---------|
| Patch | None | <1min | Rolling update |
| Minor | <5s | 5-10min | Blue-green |
| Major | <15min | 30-60min | Blue-green + DB migration |
| Emergency | <30s | Immediate | Hotfix branch + rolling |

### Rolling Update Procedure

```bash
# 1. Pull new images
docker compose pull gula-backend

# 2. Rolling restart (one container at a time)
docker compose up -d --no-deps --scale gula-backend=0 gula-backend
sleep 10  # Wait for health
docker compose up -d --no-deps --scale gula-backend=1 gula-backend
sleep 10
# Repeat for remaining...

# 3. Verify
curl -f https://api.gula.health/health/ready
```

### Blue-Green Deployment Procedure

```bash
# 1. Deploy green stack
docker compose -f docker-compose.green.yml up -d

# 2. Run smoke tests
./scripts/smoke-test.sh green

# 3. Switch traffic
# Update api-gateway config to point to green
docker compose exec api-gateway nginx -s reload

# 4. Monitor
watch -n 5 'curl -s https://api.gula.health/health/deep | jq .grade'

# 5. After 15min, retire blue
docker compose -f docker-compose.blue.yml down
```

### Database Migration During Upgrade

```bash
# 1. Run migrations (safe, backward-compatible)
docker compose run --rm gula-backend alembic upgrade head

# 2. Verify schema
docker compose run --rm gula-backend alembic check

# 3. Deploy new code (after old code works with new schema)
# Rolling update or blue-green as above
```

---

## 15. Troubleshooting

### Common Issues

#### Backend Returns 503

| Possible Cause | Check | Fix |
|---------------|-------|-----|
| DB unreachable | `docker compose logs postgres` | Restart postgres, check connectivity |
| Circuit breaker open | `/health/deep` grade | Wait for auto-repair or restart backend |
| OOM killed | `docker inspect gula-backend` | Increase memory limit |
| Config error | `docker compose logs gula-backend` | Fix `.env` values |
| Disk full | `df -h` | Clean disk, prune old data |

#### High Latency

| Possible Cause | Check | Fix |
|---------------|-------|-----|
| N+1 queries | Slow query log | Add eager loading |
| Missing index | `EXPLAIN ANALYZE` | Create index |
| Connection pool exhausted | `SELECT count(*) FROM pg_stat_activity` | Increase pool size |
| Resource contention | `top`, `htop` | Scale up |

#### Database Connection Issues

| Possible Cause | Check | Fix |
|---------------|-------|-----|
| Pool exhaustion | `SELECT count(*) FROM pg_stat_activity` | Increase `DB_POOL_SIZE` |
| Replication lag | `pg_stat_replication` | Check replica health |
| Deadlocks | PostgreSQL logs | Investigate transaction order |
| Max connections reached | `SHOW max_connections` | Increase or add PgBouncer |

#### Certificate Issues

| Possible Cause | Check | Fix |
|---------------|-------|-----|
| Renewal failed | `certbot certificates` | Manual renew |
| DNS propagation | `dig api.gula.health` | Wait or fix DNS |
| Rate limited | Let's Encrypt logs | Use staging for testing |

### Debugging Commands

```bash
# Check container health
docker compose ps
docker compose logs --tail=100 gula-backend

# Check database connectivity
docker compose exec postgres pg_isready
docker compose exec postgres psql -U gula -c "SELECT 1"

# Check Redis connectivity
docker compose exec redis redis-cli PING

# Check API health
curl -s https://api.gula.health/health | jq .
curl -s https://api.gula.health/health/deep | jq .

# Check resources
docker stats --no-stream
df -h
free -h
uptime

# Check application logs
docker compose logs --tail=500 gula-backend | grep ERROR
docker compose logs --tail=500 gula-backend | grep CRITICAL
```

### Diagnostic Endpoints

| Endpoint | Purpose | Access |
|----------|---------|--------|
| `/health` | Liveness check | Public |
| `/health/live` | Liveness (K8s) | Public |
| `/health/ready` | Readiness (Docker/K8s) | Public |
| `/health/status` | Startup diagnostics | Public |
| `/health/deep` | Full diagnostic + grade | Internal |
| `/metrics/prom` | Prometheus metrics | Internal (bearer token) |

---

## 16. Support

### On-Call Rotation

| Role | Responsibility | Hours |
|------|---------------|-------|
| Primary on-call | First response, triage, mitigation | 24/7 |
| Secondary on-call | Escalation, complex issues | 24/7 |
| DBA on-call | Database-specific issues | 24/7 (on-demand) |
| Security on-call | Security incidents | 24/7 (on-demand) |

### Escalation Matrix

| Severity | Response Time | Escalation Path |
|----------|--------------|-----------------|
| SEV1 (Platform down) | <15 min | On-call → Engineering Lead → CTO |
| SEV2 (Degraded) | <30 min | On-call → Engineering Lead |
| SEV3 (Minor bug) | <2 h | Team channel → Jira ticket |
| SEV4 (Cosmetic) | <1 week | Jira ticket |

### Communication Channels

| Channel | Purpose | Access |
|---------|---------|--------|
| PagerDuty | Incident alerting | On-call team |
| Slack (#gula-ops) | Operations discussion | All engineers |
| Slack (#gula-alerts) | Automated alerts | All team |
| Email (ops@gula.health) | Non-urgent issues | Operations team |
| Phone tree | Emergency contact | Management |

### Runbooks

All runbooks are in the `docs/runbooks/` directory:

| Runbook | File |
|---------|------|
| Backend Down | `docs/runbooks/backend-down.md` |
| Database Down | `docs/runbooks/database-down.md` |
| High Latency | `docs/runbooks/high-latency.md` |
| Disk Full | `docs/runbooks/disk-full.md` |
| Certificate Expiry | `docs/runbooks/certificate-expiry.md` |
| Security Incident | `docs/runbooks/security-incident.md` |
| Failed Deployment | `docs/runbooks/failed-deployment.md` |

See also: [Incident Response Guide](INCIDENT_RESPONSE_GUIDE.md) for full incident lifecycle.
