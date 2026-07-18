# PI-004: National Deployment, Operations & Resilience Platform

## Deployment Guide

**Version:** 1.0.0
**App Version:** 2.1.0
**Date:** 2026-07-16

---

### 1. Deployment Overview

The GULA Platform supports multiple deployment strategies suitable for environments ranging from single-server clinics to multi-region national healthcare deployments. This document covers all supported deployment topologies.

---

### 2. Docker Compose Deployment

#### 2.1 MVP Configuration (`docker-compose.yml`)

Minimum services for production launch at `docker-compose.yml`:

| Service | Container | Purpose |
|---------|-----------|---------|
| `postgres` | `gula-postgres` | PostgreSQL 16 (primary database) |
| `redis` | `gula-redis` | Redis 7 (cache, rate limiting, sessions) |
| `gula-backend` | `gula-backend` | FastAPI monolith (REST API) |
| `gula-worker` | `gula-worker` | Background task processor |
| `frontend` | `gula-frontend` | Nginx-served static frontend |
| `api-gateway` | `gula-api-gateway` | Nginx reverse proxy (TLS termination, routing) |
| `device-bridge` | `gula-device-bridge` | Lab instrument integration (ASTM/HL7) |

Deploy:

```bash
# Set environment variables
cp .env.example .env
# Edit .env with strong secrets
nano .env

# Deploy MVP stack
docker compose up -d --build --remove-orphans

# Verify readiness
make health-deep
```

Reference: `docker-compose.yml`, `docker-compose.yml:178` (backend healthcheck), `docker-compose.yml:261` (api-gateway).

#### 2.2 Full Infrastructure (`docker-compose.full.yml`)

Enterprise stack defined in `docker-compose.full.yml` adds:

- **PostgreSQL HA:** Primary + read replica + PgBouncer connection pooling
- **Redis Sentinel:** Primary + replica + sentinel for automatic failover
- **Messaging:** RabbitMQ, Kafka + ZooKeeper
- **Analytics:** ClickHouse for analytical queries
- **AI Services:** Ollama + AI service
- **Object Storage:** MinIO (S3-compatible)
- **Identity:** Keycloak for SSO/OIDC
- **Secrets Management:** HashiCorp Vault
- **Monitoring:** Prometheus, Grafana, Loki, Jaeger
- **Microservices:** lab, patient, order, result, sample, notification, autonomous-manager
- **Automated Backup:** Cron-based pg_dump container

Deploy:

```bash
docker compose -f docker-compose.full.yml up -d --build
```

#### 2.3 Horizontal Scaling (`docker-compose.scale.yml`)

Scale backend instances behind HAProxy (`config/haproxy/haproxy.cfg:60`):

```bash
# Scale to 5 backend instances
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d \
  --scale gula-backend=5

# Monitor via HAProxy stats
open http://localhost:8404/stats
```

Key configuration in `docker-compose.scale.yml`:
- Rolling updates: `parallelism: 1`, `delay: 10s`, `failure_action: rollback`
- HAProxy: `balance leastconn`, `slow-start 30s`, health checks every 5s (`haproxy.cfg:66-72`)
- Docker DNS resolution via `server-template` (auto-discover replicas)

#### 2.4 Architecture: Internet → Host Nginx → Docker Gateway

```
Internet → Host nginx (TLS, port 80/443)
         → Docker api-gateway (127.0.0.1:8080)
         → gula-backend (port 8000)
         → PostgreSQL 16 + Redis 7
```

Host nginx SSL configuration: `config/nginx/system/gula-platform-ssl.conf`:

```bash
sudo cp config/nginx/system/gula-platform-ssl.conf /etc/nginx/sites-available/
sudo ln -sf /etc/nginx/sites-available/gula-platform /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

---

### 3. Kubernetes Deployment

#### 3.1 Base Kustomize (`k8s/base/`)

Base manifests at `k8s/base/kustomization.yaml` deploying into namespace `gula`:

- **namespace.yaml:** Namespace definition
- **configmap.yaml:** Environment configuration
- **secrets.yaml:** Secret templates
- **postgres/statefulset.yaml** + **service.yaml:** PostgreSQL StatefulSet
- **redis/deployment.yaml** + **service.yaml:** Redis Deployment
- **backend/deployment.yaml** + **service.yaml** + **hpa.yaml** + **pvc.yaml + service-blue-green.yaml:** Backend with blue/green service
- **frontend/deployment.yaml** + **service.yaml:** Frontend
- **gateway/deployment.yaml** + **service.yaml** + **ingress.yaml:** API gateway + ingress
- **rabbitmq/configmap.yaml** + **statefulset.yaml** + **service.yaml:** RabbitMQ
- **microservices/deployments.yaml** + **services.yaml** + **hpa.yaml:** Microservices
- **mesh/linkerd.yaml:** Linkerd service mesh configuration

#### 3.2 Environment Overlays

| Overlay | Path | Purpose |
|---------|------|---------|
| **dev** | `k8s/overlays/dev/` | Low resource limits, dev patches |
| **prod** | `k8s/overlays/prod/` | Production replicas, resource limits, prod config |
| **region-me** | `k8s/overlays/region-me/` | ME region topology spread, labels |
| **region-eu** | `k8s/overlays/region-eu/` | EU region topology spread, labels |

Deploy to production:

```bash
kustomize build k8s/overlays/prod | kubectl apply -f -
```

#### 3.3 Production Overlay (`k8s/overlays/prod/`)

```yaml
# kustomization.yaml
patchesStrategicMerge:
  - patch-replicas.yaml    # Increased replicas
  - patch-resources.yaml   # Production resource limits

images:
  - name: ghcr.io/samertts/gula-platform/backend
    newTag: latest

configMapGenerator:
  - name: gula-config
    behavior: merge
    literals:
      - ENV=production
      - ENABLE_API_DOCS=false
      - BASE_URL=https://gula-platform.org
```

---

### 4. Helm Chart Deployment

#### 4.1 Chart Structure (`helm/gula-platform/`)

The Helm chart at `helm/gula-platform/Chart.yaml` (v1.0.0, appVersion 2.1.0):

```yaml
# Chart.yaml dependencies:
- postgresql (Bitnami ~12.0)
- redis (Bitnami ~18.0)
- rabbitmq (Bitnami ~14.0)
- minio (Bitnami ~14.0)
- prometheus (Prometheus Community ~25.0)
- grafana (Grafana ~8.0)
- loki (Grafana ~6.0)
- tempo (Grafana ~1.0)
- linkerd2 (Linkerd ~1.0)
```

#### 4.2 Key Values (`values.yaml`)

- **Backend:** Blue/green + canary deployment, HPA (2-10 replicas, CPU 70%), PDB
- **PostgreSQL:** Patroni HA (Spilo 3.0-p1), 1 primary + 2 replicas, 50Gi storage
- **Redis:** Sentinel HA, 3 sentinel pods, quorum 2
- **RabbitMQ:** 3-node cluster, 6 queues defined
- **MinIO:** Distributed mode, 4 replicas, 100Gi storage
- **Monitoring:** Prometheus + Grafana + Loki + Tempo + Alertmanager
- **Service Mesh:** Linkerd with mTLS, ServiceProfile, TrafficSplit
- **Microservices:** lab, order, patient, result, sample, notification, AI

#### 4.3 Install

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add linkerd https://helm.linkerd.io/stable
helm dependency update helm/gula-platform/
helm install gula-platform ./helm/gula-platform/ \
  --namespace gula --create-namespace \
  -f custom-values.yaml
```

---

### 5. Blue/Green & Canary Deployment

#### 5.1 Blue/Green (`values.yaml:86-90`, `k8s/base/backend/service-blue-green.yaml`)

```yaml
blueGreen:
  enabled: true
  autoPromote: true
  analysisPeriodSeconds: 180
  prePromoteSmokeTest: true
```

Two services (`gula-backend-blue`, `gula-backend-green`) with traffic switched via Linkerd TrafficSplit (`values.yaml:800-806`):

```yaml
trafficSplit:
  enabled: true
  backends:
    - service: gula-backend-blue
      weight: 100
    - service: gula-backend-green
      weight: 0
```

#### 5.2 Canary (`values.yaml:91-96`, `config/haproxy/haproxy.cfg`)

```yaml
canary:
  enabled: true
  weight: 0
  maxWeight: 100
  stepWeight: 10
  stepIntervalSeconds: 300
```

Canary routing via ingress annotations (`values.yaml:648-651`):

```yaml
canary:
  enabled: true
  weight: "0"
  header: "X-Canary"
  headerValue: "true"
```

---

### 6. Horizontal & Vertical Scaling

#### 6.1 Horizontal Pod Autoscaler

Backend HPA (`k8s/base/backend/hpa.yaml`, `values.yaml:135-153`):

```yaml
autoscaling:
  enabled: true
  minReplicas: 2
  maxReplicas: 10
  targetCPUUtilizationPercentage: 70
  targetMemoryUtilizationPercentage: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
```

#### 6.2 Connection Pool Budget

Formula from `docker-compose.yml:138`: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < max_connections`

Default: `3 × (6 + 12) = 54 < 100` (PostgreSQL default max_connections)

Patroni production settings (`config/postgres-ha/patroni.yml:64`): `max_connections: 200`

---

### 7. Infrastructure-as-Code Patterns

#### 7.1 Quality Gates (`config/quality-gates/`)

Automated validation gates for deployment:

| Gate | File | Purpose |
|------|------|---------|
| Architecture | `architecture-gate.py` | Architecture compliance validation |
| Security | `security-gate.py` | Security posture checks |
| Performance | `performance-gate.py` | Performance baseline validation |
| Database | `database-gate.py` | Schema and migration checks |
| Scalability | `scalability-gate.py` | Scaling validation |
| API | `api-gate.py` | API contract conformance |
| FHIR | `fhir-gate.py` | FHIR interoperability |
| Accessibility | `accessibility-gate.js` | Accessibility compliance |
| Offline | `offline-gate.py` | Offline capability verification |

#### 7.2 Preflight Checks (`scripts/preflight.sh`)

Run before any deployment to validate prerequisites:

```bash
./scripts/preflight.sh
```

#### 7.3 Deployment Script (`scripts/deploy.sh`)

```bash
./scripts/deploy.sh
```

#### 7.4 Constitution Enforcement (`scripts/constitution_enforcer.py`)

20-rule governance enforcer that runs during CI/CD pipeline.

---

### 8. Makefile Deployment Targets

| Target | Command |
|--------|---------|
| `make up` | `docker compose up -d` + wait for readiness |
| `make restart` | Rebuild images + restart + deep health check |
| `make scale` | `BACKEND_REPLICAS=N` scaling via docker compose |
| `make ci` | Syntax gate + lint + docker build (full CI) |
| `make helm-deploy` | Helm install/upgrade |
| `make helm-lint` | Helm chart linting |
| `make blue-green-deploy` | Blue/green traffic switch |
| `make canary-deploy` | Canary release with weight increment |

---

### 9. Deployment Checklist

- [ ] Secrets generated (`make secrets-gen`)
- [ ] `.env` populated with strong secrets
- [ ] SSL certificates configured (`config/ssl/`)
- [ ] Host nginx configured for the domain
- [ ] Metrics bearer token generated (`make metrics-token`)
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Health endpoints returning 200 (`make health-deep`)
- [ ] Monitoring stack active (`make monitoring`)
- [ ] Backups configured (`make continuous-backup`)
- [ ] Feature flags verified for deployment target

---

**References:** `docker-compose.yml`, `docker-compose.full.yml`, `docker-compose.scale.yml`, `config/haproxy/haproxy.cfg`, `k8s/base/`, `k8s/overlays/prod/`, `helm/gula-platform/`, `config/nginx/`, `scripts/deploy.sh`, `scripts/preflight.sh`, `config/quality-gates/`
