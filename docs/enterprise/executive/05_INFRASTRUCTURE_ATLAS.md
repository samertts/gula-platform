# GULA Platform — Infrastructure Atlas

**Classification:** CONFIDENTIAL
**Date:** 2026-07-18

---

## 1. Deployment Architecture

```
Internet
  → Cloudflare (WAF, DDoS, CDN, DNS, rate limiting)
    → Host Nginx (TLS 1.2/1.3, ModSecurity WAF, rate limit)
      → API Gateway Nginx (127.0.0.1:8080)
        → gula-backend (gunicorn + uvicorn, port 8000)
          → PostgreSQL 16 + Redis 7
```

**Key principle:** Backend never exposes a public port. All traffic enters through the gateway.

---

## 2. Deployment Targets (7)

| Target | Status | Details |
|--------|--------|---------|
| **Docker Compose MVP** | ✅ PRIMARY | 7 services: postgres:16-alpine, redis:7-alpine, gula-backend (2 workers), gula-worker, frontend, api-gateway, prometheus/grafana (profile) |
| **Docker Compose Full** | ✅ Available | 25+ services: Patroni HA, PgBouncer, ClickHouse, RabbitMQ, Kafka, MinIO, Ollama, Keycloak, Vault, Loki, Tempo, Jaeger, 8 microservices |
| **Docker Compose Scale** | ✅ Available | HAProxy + N backend replicas; stats at :8404 |
| **Kubernetes (Kustomize)** | ✅ Available | Base + 4 overlays (dev, prod, region-eu, region-me) |
| **Helm** | ✅ Available | Chart v1.0.0, 38 templates, 9 Bitnami deps |
| **DigitalOcean** | ✅ Configured | app.yaml |
| **Render / Supabase** | ⚠️ Partial | Documented |

---

## 3. Production Resource Allocation (MVP)

| Service | Image | Memory | CPU |
|---------|-------|--------|-----|
| postgres | postgres:16-alpine | 896m | 1.0 |
| redis | redis:7-alpine | 320m | 0.5 |
| gula-backend | ghcr.io/gula/backend | 1,536m | 1.5 |
| gula-worker | (same image) | 512m | 0.5 |
| frontend | nginx:1.25-alpine | — | — |
| api-gateway | nginx:1.25-alpine | — | — |

---

## 4. Database Deployment

| Aspect | Current | Recommended |
|--------|---------|-------------|
| Engine | PostgreSQL 16 (single instance) | Patroni HA + PgBouncer |
| Connection Pool | QueuePool: pool_size=5, max_overflow=10 | Same + PgBouncer pooling |
| Backup | Daily pg_dump to .sql.gz | Daily + continuous WAL archiving |
| Restore Testing | ❌ None | Weekly automated restore test |
| HA | ❌ None | Streaming replication + Patroni auto-failover |
| Migration | Alembic (48 revisions) | Same (idempotent, CI-enforced) |

**Connection budget:** 3 workers × (6 connections) = 18 total (within PG max_connections=100)

---

## 5. Network Architecture

| Layer | Technology | Purpose |
|-------|------------|---------|
| Edge | Cloudflare | WAF (9 rules + managed), DDoS, CDN, DNS, bot detection, rate limiting |
| Edge | Cloudflare Workers | Serverless functions |
| Network | Let's Encrypt TLS | Auto-renewal, TLS 1.2+ |
| Network | Docker Compose (172.20.0.0/16) | Internal service network |
| Network | ModSecurity WAF | SQLi/XSS prevention |
| Network | Snort IDS + Fail2ban | Intrusion detection |
| API Gateway | Nginx (127.0.0.1:8080) | Rate limiting, 5 zones |
| Service Mesh | Linkerd (K8s only) | mTLS, retry budgets, traffic split |

**Memory:** 18 Docker volumes, 18 networks (full stack)

---

## 6. Monitoring Stack

| Layer | Tool | Status |
|-------|------|--------|
| Metrics Collection | Prometheus | ✅ 2 scrape configs |
| Alert Rules | 3 rule files (836 lines) | ✅ gula.yml, gula-full.yml, slo.yml |
| Dashboards | Grafana (11) | ✅ Platform, Hospital, Capacity, Laboratory |
| Log Aggregation | Loki + Promtail | ✅ Configured |
| Distributed Tracing | Tempo + OpenTelemetry | ⚠️ Configured (not primary) |
| Alerting | Alertmanager | ✅ Slack + PagerDuty |
| Uptime | Cloudflare + Prometheus | ✅ |
| Synthetic | k6 | ✅ Scripts exist (no baseline) |
| APM | None | ❌ Missing |

---

## 7. CI/CD Pipeline

| Stage | Tools | Blocking |
|-------|-------|----------|
| Syntax Gate | py_compile | ✅ Blocks if fails |
| Migration Check | Alembic upgrade on clean PG | ✅ Blocks if fails |
| OpenAPI Contract | OpenAPI diff | ✅ Blocks if fails |
| Backend Test | pytest (1,755 tests) | ✅ Blocks if fails |
| Smoke Test | curl health endpoints | ✅ Blocks if fails |
| Security Scan | Safety, Bandit, Hadolint, Gitleaks, Trivy | ✅ Non-blocking |
| Build & Push | Docker buildx (8-image matrix) | ✅ Blocks if fails |

---

## 8. Disaster Recovery

| Scenario | RPO | RTO | Strategy | Status |
|----------|-----|-----|----------|--------|
| Process crash | 0 | <30s | Docker auto-restart | ✅ Implemented |
| Node failure | <5min | <5min | Active-passive replica | ❌ Not deployed |
| DB failure | <1min | <2min | Patroni auto-failover | ❌ Not deployed |
| Region failure | <15min | <30min | Warm standby | ❌ Not deployed |
| Data corruption | <24h | <4h | PITR from WAL | ⚠️ Configured |
| Full site loss | <24h | <24h | Cold standby | ❌ Not tested |

### Critical Gaps
- **No staging environment** — Changes deployed directly to production
- **No automated restore testing** — Backups exist but never verified
- **Single PostgreSQL instance** — No HA in production
- **Terraform targets AWS** — Actual deployment is DigitalOcean

---

## 9. Security Infrastructure

| Layer | Control | Implementation |
|-------|---------|---------------|
| Edge | WAF | Cloudflare (9 rules + managed ruleset) |
| Edge | DDoS | Cloudflare |
| Edge | Bot detection | Cloudflare Workers |
| Network | TLS | Let's Encrypt, auto-renewal, 1.2+ |
| Network | Rate limiting | Nginx (5 zones) + Cloudflare |
| Application | Auth | JWT + OAuth2 + SAML + MFA (TOTP/WebAuthn/FIDO2) |
| Application | Authorization | RBAC + ABAC (9 roles × 16 permissions) |
| Application | Circuit breaker | DB + Redis, 4 degradation levels |
| Data | Encryption at rest | Fernet (AES-256) for national IDs |
| Data | Encryption in transit | TLS everywhere |
| Secrets | Vault | HashiCorp Vault (optional, configured in full stack) |
| Identity | Keycloak | SSO (optional, configured in full stack) |
