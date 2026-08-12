# GULA Platform — Infrastructure Analysis
**Date:** 2026-07-17

---

## 1. Deployment Targets (5 active)

| Target | Config | Services | Status |
|--------|--------|----------|--------|
| **Docker Compose (MVP)** | `docker-compose.yml` | 7 core services | **PRIMARY** |
| **Docker Compose (Full)** | `docker-compose.full.yml` | 25+ services | Ready |
| **Kubernetes (Kustomize)** | `k8s/` | Custom K8s manifests | Ready |
| **Kubernetes (Helm)** | `helm/gula-platform/` | 38 templates + 9 dependencies | Ready |
| **DigitalOcean** | `digitalocean/app.yaml` | App Platform spec | Ready |
| **Render** | `render.yaml` | PaaS config | Documented |
| **Supabase** | `supabase/` | Managed Postgres | Partial |

---

## 2. Docker Compose MVP (Production)

### Services

| Service | Image | Port | Memory Limit | CPU Limit |
|---------|-------|------|-------------|-----------|
| `postgres` | postgres:16-alpine | 5432 | 896m | 1.0 |
| `redis` | redis:7-alpine | 6379 | 320m | 0.5 |
| `gula-backend` | ghcr.io/gula/backend | 8000 (int) | 1536m | 1.5 |
| `gula-worker` | ghcr.io/gula/backend (same) | — | 512m | 0.5 |
| `frontend` | nginx:1.25-alpine | 80 (int) | — | — |
| `api-gateway` | nginx:1.25-alpine | 8080 (int) | — | — |
| `prometheus` | prom/prometheus:v2.50.1 | 9090 (profile) | — | — |
| `grafana` | grafana/grafana:10.3.3 | 3000 (profile) | — | — |
| `device-bridge` | build from services/device_bridge | 8200 (profile) | — | — |

### Network Architecture
```
Internet → Host Nginx (SSL, 80/443)
  → Docker API Gateway (127.0.0.1:8080)
    → backend:8000 (FastAPI)
    → frontend:80 (Static)
```

### Data Volumes
`pgdata`, `redis-data`, `certbot-webroot`, `audit-anchors`, `prometheus-data`, `grafana-data`

---

## 3. Docker Compose Full (25+ services)

### Additional Services
| Category | Services |
|----------|----------|
| **Database HA** | postgres-primary, postgres-replica, pgbouncer, backup-cron |
| **Redis HA** | redis, redis-replica, redis-sentinel (3 nodes) |
| **Analytics** | clickhouse |
| **Messaging** | rabbitmq (3-node), zookeeper, kafka |
| **AI** | ollama (0.1.29), ai-service |
| **Storage** | minio (distributed) |
| **Monitoring** | prometheus, grafana, loki, promtail, jaeger, node-exporter |
| **Security** | keycloak (23.0), vault (1.15) |
| **Microservices** | lab-service, patient-service, order-service, result-service, sample-service, notification-service, autonomous-manager |
| **Network** | 172.20.0.0/16 subnet, 18 Docker volumes |

---

## 4. Kubernetes (Kustomize)

### Base Components
| Component | Replicas | Init Containers | Health Checks |
|-----------|----------|----------------|---------------|
| backend | 2 (blue slot) | wait-for-postgres, wait-for-redis | Liveness: /health (30s/15s), Readiness: /health (15s/10s) |
| frontend | 1 | — | — |
| gateway | 1 | — | — |
| postgres | 1 statefulset | — | — |
| redis | 1 deployment | — | — |
| rabbitmq | 1 statefulset | — | — |
| microservices | 1 each | — | — |

### Overlays
| Overlay | Backend Replicas | Config |
|---------|------------------|--------|
| dev | 1 | Dev config |
| prod | 5 | Production config |
| region-eu | 2 | EU topology spread |
| region-me | 2 | ME topology spread |

### HPA
- CPU threshold: 70%
- Memory threshold: 80%
- Scale range: 2-10 replicas
- Scale-up: 2 pods/60s
- Scale-down: 1 pod/120s

### Blue-Green
- Slot-based (blue/green label)
- `gula-backend-active` service routes to live slot
- Init containers validate before serving

### Service Mesh
- Linkerd auto-inject at namespace level
- Service profiles with retry budgets

---

## 5. Helm Chart

### Chart Details
- **Chart version**: 1.0.0
- **App version**: 2.1.0
- **Values file**: 1326 lines
- **Dependencies**: 9 Bitnami charts

### Dependencies
| Dependency | Version | Purpose |
|------------|---------|---------|
| postgresql | ~12.0 | Database |
| redis | ~18.0 | Cache |
| rabbitmq | ~14.0 | Message broker |
| minio | ~14.0 | Object storage |
| prometheus | ~25.0 | Monitoring |
| grafana | ~8.0 | Dashboards |
| loki | ~6.0 | Log aggregation |
| tempo | ~1.0 | Distributed tracing |
| linkerd2 | ~1.0 | Service mesh |

### Key Values
- Registry: `ghcr.io/samertts/gula-platform`
- Pod security: runAsNonRoot, seccomp RuntimeDefault, ALL capabilities dropped
- Topology spread: maxSkew=1 across zones
- Postgres HA: Patroni + Spilo, 1 primary + 2 replicas, 50Gi, pgBackRest
- Redis HA: Sentinel, 3 nodes, quorum 2, 256MB maxmemory
- RabbitMQ: 3-node cluster, 6 queues
- MinIO: Distributed, 4 replicas, 100Gi, 3 buckets

---

## 6. Terraform (AWS Infrastructure)

### Modules (12)
| Module | Resources |
|--------|-----------|
| networking | VPC (10.3.0.0/16), 3 AZ subnets, NAT gateways, VPC endpoints |
| security | WAF, GuardDuty, Security Hub, Config, CloudTrail |
| storage | S3 buckets + lifecycle + replication |
| postgres | RDS r6g.xlarge, Multi-AZ, 500GB auto-scale, 35d backups |
| redis | ElastiCache r6g.xlarge, cluster mode (2+2), Multi-AZ |
| rabbitmq | Amazon MQ m5.xlarge, CLUSTER_MULTI_AZ |
| kubernetes | EKS 1.29, system (3) + app (5-20) + spot (5-20) node groups |
| alb | ALB + WAF + SSL + access logs |
| cdn | CloudFront all price class |
| dns | Route53 zones, DMARC/SPF/DKIM, health checks |
| monitoring | Prometheus + Grafana + Alertmanager + Thanos |
| backup | AWS Backup, cross-region, 35/120/365 day retention |

### Environments
| Environment | VPC | DB | Redis | EKS |
|-------------|-----|----|-------|-----|
| dev | 10.1.0.0/16 | Small | Small | Dev |
| staging | 10.2.0.0/16 | Medium | Medium | Staging |
| pilot | 10.3.0.0/16 | Production | Production | Production |
| prod | 10.3.0.0/16 | Production (multi-AZ) | Production | Production |
| dr | DR region | Read replica | Replica | DR |

---

## 7. CI/CD Pipeline (6 workflows)

### `ci.yml` — Main CI (644 lines)
| Job | Depends On | Description |
|-----|-----------|-------------|
| syntax-gate | — | py_compile + import-walk + flake8 E9/F821 |
| migration-check | — | Alembic upgrade on fresh PG16 |
| openapi-contract | — | OpenAPI spec validation |
| backend-test | — | pytest against PG16 + Redis 7.2 |
| smoke-test | — | Boot uvicorn, health checks |
| security-scan | — | Safety + Bandit + Hadolint + Gitleaks |
| build-and-push | all above | Matrix build of 8 images, Trivy scan |

### `quality-gate.yml`
- 9 gates: Architecture, Performance, Security, Database, API, FHIR, Scalability, Offline, Accessibility
- Release blocking on failure

### `deploy.yml` (SSH-based)
- SSH → git sync → preserve .env → generate secrets → pull images → zero-downtime restart → health check → auto-rollback

### Progressive Delivery
| Workflow | Strategy | Tool |
|----------|----------|------|
| `canary-deploy.yml` | 10% → 25% → 50% → 100% | Linkerd TrafficSplit |
| `blue-green-deploy.yml` | Blue ↔ Green slot swap | K8s service labels |
| `auto-rollback.yml` | Detect failure → revert | kubectl patch svc |

---

## 8. Monitoring Stack

| Component | Status | Config |
|-----------|--------|--------|
| **Prometheus** | Active | 2 scrape configs (MVP + Full), 3 rule files (396+289+151 lines) |
| **Grafana** | Active | 4 dashboards (platform, hospital, capacity, laboratory) |
| **Alertmanager** | Active | Slack + PagerDuty templates |
| **Loki** | Configured | Log aggregation from Docker |
| **Tempo** | Configured | OTLP + Jaeger + Zipkin receivers, S3 storage |
| **OpenTelemetry** | Configured | Collector with traces/metrics/logs pipelines |
| **Promtail** | Configured | Docker log collector |

### Prometheus Alert Rules
| Rule File | Alerts | Categories |
|-----------|--------|------------|
| `gula.yml` (396 lines) | Core | Backend down, DB down, Redis down, performance, capacity, infrastructure, errors, control layer |
| `gula-full.yml` (289 lines) | Business | Pipeline, security, capacity planning, observability |
| `slo.yml` (151 lines) | SLO | Burn rate alerts, latency SLO |

---

## 9. Supporting Infrastructure

| Component | Config | Purpose |
|-----------|--------|---------|
| **nginx.conf** | 151 lines | Standalone nginx: Brotli, rate limit, HSTS, proxy cache |
| **HAProxy** | haproxy.cfg | Load balancing for scale (leastconn) |
| **PostgreSQL** | postgresql.conf (87 lines) | Tuned for 4GB/2vCPU, 16 workers |
| **Redis** | redis.conf | AOF, allkeys-lru, maxmemory 512mb |
| **RabbitMQ** | Definitions JSON (178 lines) | 6 queues, 3 exchanges |
| **Vault** | vault-prod.hcl (50 lines) | Auto-unseal |
| **System tuning** | 99-gula-sysctl.conf (57 lines) | TCP buffers, keepalive, swappiness, fd limits |
| **Nginx WAF** | api-threat-protection.conf | SQL injection, XSS blocking |

---

## 10. Critical Infrastructure Findings

| Finding | Evidence | Risk |
|---------|----------|------|
| **MVP compose is primary but full.yml has HA** | MVP has single PG + Redis | **HIGH** — no HA in production |
| **Full.yml has 25+ services but not deployed** | Designed but not active | **MEDIUM** — over-engineered for current scale |
| **Terraform targets AWS but deployment is DO** | AWS vs DigitalOcean mismatch | **HIGH** — IaC needs re-targeting |
| **K8s not primary but well-documented** | 36 K8s manifest files | **LOW** — investment in wrong platform |
| **No Staging environment** | Only dev and prod in K8s overlays | **HIGH** — missing pre-production |
| **PostgreSQL config (full.yml) uses PG14** while MVP uses PG16 | Version inconsistency | **MEDIUM** |
| **Backup strategy documented but no automated restore test** | No evidence of restore testing | **HIGH** |
