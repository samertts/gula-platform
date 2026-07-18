# GULA PLATFORM — DEPLOYMENT MASTER PLAN

**Status:** VERIFIED (from audit) + PROPOSED (recommendations)
**Date:** 2026-07-17

---

## CURRENT DEPLOYMENT OPTIONS (Verified)

| Platform | Status | Details |
|----------|--------|---------|
| Docker Compose (MVP) | ✅ Primary | postgres:16 + redis:7 + backend + worker + frontend + gateway |
| Docker Compose (Full) | ✅ Available | + replica DB, pgbouncer, redis HA, rabbitmq, kafka, clickhouse, minio, ollama, keycloak, vault, observability |
| Docker Compose (Scale) | ✅ Available | HAProxy + N backend replicas |
| Kubernetes (K8s) | ⚠️ Available | Base manifests + dev/prod/region overlays, Linkerd mesh |
| DigitalOcean App Platform | ✅ Available | Docker build + static frontend + Redis |
| Render | ✅ Available | Docker + static site + Redis KV |
| Supabase | ⚠️ Partial | PostgreSQL managed only (no Auth/Storage/Realtime) |
| Cloudflare | ✅ Configured | WAF, DNS, Worker, R2, rate limiting |
| Helm Charts | ⚠️ Available | Located at `helm/` directory |

---

## ENVIRONMENT STRATEGY

```yaml
environments:
  - name: development
    purpose: "Developer local testing"
    deployment: "docker compose up"
    seeds: "Test data, mock external services"
    features: "All enabled"
    
  - name: staging
    purpose: "Pre-production validation"
    deployment: "docker compose (full stack) or K8s"
    monitoring: "Prometheus + Grafana"
    features: "All enabled, rate limits reduced"
    
  - name: production
    purpose: "Live customer-facing"
    deployment: "docker compose (scaled) or K8s (prod overlay)"
    monitoring: "Full observability stack"
    features: "Feature-flagged rollout"
    sla: "99.9% uptime"
    
  - name: government
    purpose: "National deployment (air-gapped or isolated)"
    deployment: "K8s on government data center"
    monitoring: "Internal only"
    features: "SNDHS-enabled, restricted AI to local models"
    compliance: "National data sovereignty requirements"
```

---

## DEPLOYMENT ARCHITECTURE (Recommended)

### Small Lab Deployment
```
1 server (4GB RAM, 2 CPU, 50GB SSD)
  ├── Docker Compose (MVP)
  │   ├── postgres:16-alpine (896m limit)
  │   ├── redis:7-alpine (320m limit)
  │   ├── gula-backend (2 workers, 1GB limit)
  │   ├── gula-worker (512m limit)
  │   ├── frontend (nginx)
  │   └── api-gateway (nginx)
  └── Cloudflare (WAF, DNS, CDN)
```

### Hospital Deployment
```
3 servers (16GB RAM, 8 CPU, 200GB SSD each)
  ├── Server 1: PostgreSQL 16 (primary) + Redis 7
  ├── Server 2: gula-backend (3-5 workers) + gula-worker
  └── Server 3: PostgreSQL (replica) + monitoring stack
  External: Cloudflare + Backups to S3-compatible storage
```

### National Deployment (Air-Gapped)
```
Government Data Center
  ├── K8s cluster (5+ nodes)
  │   ├── PostgreSQL HA (Patroni + etcd)
  │   ├── Redis Sentinel (3 nodes)
  │   ├── RabbitMQ (3-node cluster)
  │   ├── gula-backend (5+ replicas)
  │   ├── gula-worker (2 replicas)
  │   ├── Ollama (GPU node for local AI)
  │   ├── MinIO (4-node distributed)
  │   └── Monitoring (internal Prometheus/Grafana)
  └── Backup: Encrypted tapes + secondary data center
```

---

## INFRASTRUCTURE AS CODE

| Tool | Status | Location |
|------|--------|----------|
| Docker Compose | ✅ Primary | `docker-compose.yml`, `docker-compose.full.yml` |
| K8s Manifests | ✅ Available | `k8s/base/`, `k8s/overlays/` |
| Helm Charts | ⚠️ Available | `helm/` |
| Terraform | ⚠️ Available | `terraform/` |
| DigitalOcean App Spec | ✅ Available | `digitalocean/app.yaml` |
| Render Blueprint | ✅ Available | `render.yaml` |
| Ansible | ❌ Not present | Consider adding for server setup |

---

## DATABASE DEPLOYMENT

### Primary Strategy
| Aspect | Choice | Rationale |
|--------|--------|-----------|
| Engine | PostgreSQL 16 | Latest stable, JSONB, partitioning, logical replication |
| Connection pooling | PgBouncer | Transaction pooling for serverless/PAAS |
| HA | Streaming replication + Patroni | Auto-failover, no data loss |
| Backup | pg_dump (daily) + WAL archiving (continuous) | PITR capability |
| Migration | Alembic | Idempotent revisions, CI-enforced |
| Read replicas | Optional (READ_REPLICA_ENABLED) | Analytics workload isolation |

### HA Configuration
```yaml
postgres:
  primary: "postgres-primary"
  replica: "postgres-replica"
  pooler: "pgbouncer"
  automation: "patroni"
  failover: "automatic (30s detection + 10s promotion)"
  replication: "synchronous (1 replica) / asynchronous (2+)"
  backup:
    full: "Daily pg_dump"
    wal: "Continuous WAL archiving to S3"
    retention: "30 days (WAL) + 12 monthly (snapshots)"
```

---

## MONITORING & OBSERVABILITY

| Layer | Tool | Status |
|-------|------|--------|
| Metrics | Prometheus | ✅ Configured |
| Dashboards | Grafana | ✅ 11 dashboards |
| Logs | Loki + Promtail | ✅ Configured |
| Tracing | Tempo + Jaeger | ⚠️ Configured |
| Alerting | Alertmanager | ✅ Configured |
| Uptime | Cloudflare + Prometheus | ✅ |
| Dependency | OpenTelemetry Collector | ⚠️ Configured |
| Synthetic | k6 | ✅ Available (k6/ directory) |

---

## SECURITY DEPLOYMENT

| Layer | Control | Implementation |
|-------|---------|---------------|
| Edge | WAF | Cloudflare (9 rules + managed) |
| Edge | DDoS | Cloudflare |
| Edge | Bot detection | Cloudflare Worker |
| Network | SSL/TLS | Let's Encrypt, auto-renewal, TLS 1.2+ |
| Network | Rate limiting | nginx (5 zones) + Cloudflare |
| Application | Auth | JWT + OAuth2 + SAML + MFA |
| Application | Authorization | RBAC + ABAC |
| Application | Circuit breaker | DB + Redis, 4 degradation levels |
| Data | Encryption at rest | Fernet (national IDs) |
| Data | Encryption in transit | TLS everywhere |
| Secrets | Vault | HashiCorp Vault (optional, configured) |
| Identity | Keycloak | SSO (optional, configured) |

---

## DISASTER RECOVERY

| Scenario | RPO | RTO | Strategy |
|----------|-----|-----|----------|
| Process crash | 0 (stateless) | <30s | Systemd auto-restart, Docker restart policy |
| Node failure | <5min | <5min | Active-passive replica |
| DB failure | <1min (sync rep) | <2min | Patroni auto-failover |
| Region failure | <15min | <30min | Warm standby in second region |
| Data corruption | <24h | <4h | PITR from WAL archive |
| Full site loss | <24h | <24h | Cold standby, restore from backups |
| Ransomware | <24h | <48h | Immutable backups, offline copies |

### DR Testing Cadence
| Test Type | Frequency | Verification |
|-----------|-----------|-------------|
| Process restart | Weekly | Automated health check |
| Node failover | Monthly | Active-passive switch |
| DB failover | Monthly | Patroni failover test |
| Backup restore | Monthly | Full restore to test environment |
| Region failover | Quarterly | Traffic switch to secondary |
| Full DR drill | Bi-annual | Complete site failover exercise |

---

## DEPLOYMENT ROADMAP

| Phase | Target | Timeline |
|-------|--------|----------|
| 1 | Single lab (Docker Compose) | Current |
| 2 | Hospital (Docker Compose + HA) | Month 1-3 |
| 3 | Lab chain (K8s + blue-green) | Month 4-6 |
| 4 | National (K8s + Patroni + multi-region) | Month 7-12 |
| 5 | Cross-border (K8s federation) | Month 13-24 |
| 6 | Global (Multi-cloud, mesh) | Month 24-48 |
