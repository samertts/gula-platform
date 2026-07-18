# PI-004 — National Deployment Guide

## Deployment Platform v1.0 — Infrastructure Deployment Guide

**Version:** 2.1.0
**Date:** July 2026

---

## 1. Deployment Overview

GULA is deployed across 5 environment tiers using Infrastructure as Code (Terraform) with containerized workloads via Docker Compose (primary MVP) and Kubernetes (future scale).

| Environment | Purpose | Infrastructure | Access |
|-------------|---------|---------------|--------|
| **dev** | Developer integration | Single-node Docker Compose | Engineering team |
| **staging** | Pre-production validation | HA Docker Compose + Redis cluster | QA, clinical reviewers |
| **production** | National live deployment | Multi-AZ K8s or Docker Compose scale | End users |
| **dr** | Disaster recovery | Passive replica in secondary region | Operations |
| **sandbox** | Partner integration testing | Isolated Docker Compose | Integration partners |

---

## 2. Docker Compose Deployment (Primary)

### 2.1 Base Deployment (`docker-compose.yml`)

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: gula
      POSTGRES_USER: gula
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U gula"]
      interval: 10s

  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data

  gula-backend:
    build: ./backend
    depends_on:
      postgres: { condition: service_healthy }
      redis: { condition: service_started }
    environment:
      DATABASE_URL: postgresql://gula:${DB_PASSWORD}@postgres:5432/gula
      REDIS_URL: redis://:${REDIS_PASSWORD}@redis:6379
      SECRET_KEY: ${SECRET_KEY}
      ENCRYPTION_KEY: ${ENCRYPTION_KEY}
    expose:
      - "8000"

  api-gateway:
    image: nginx:alpine
    volumes:
      - ./config/nginx/gateway.conf:/etc/nginx/conf.d/default.conf
    ports:
      - "8080:80"
    depends_on:
      - gula-backend
```

### 2.2 Full Stack with Monitoring (`docker-compose.full.yml`)

Extends base with:
- **Prometheus** — Metrics collection (15s scrape interval)
- **Grafana** — Pre-provisioned dashboards (auto-provisioned datasources)
- **Loki** — Log aggregation from all containers
- **Promtail** — Docker log shipping to Loki
- **RabbitMQ** — Async message broker for background tasks
- **HAProxy** — Load balancer for `make scale` (port 8404 for stats)

### 2.3 Scaled Deployment (`docker-compose.scale.yml`)

```bash
# Scale backend to N instances behind HAProxy
docker compose -f docker-compose.yml \
  -f docker-compose.scale.yml \
  up -d --scale gula-backend=5

# Monitor load distribution
curl http://localhost:8404/stats
```

---

## 3. Kubernetes Deployment (Helm + Kustomize)

### 3.1 Helm Chart Structure

```
helm/gula/
├── Chart.yaml
├── values.yaml
├── values-prod.yaml
├── values-staging.yaml
├── templates/
│   ├── deployment.yaml        # Backend deployment
│   ├── service.yaml           # Backend service
│   ├── configmap.yaml         # App config
│   ├── secret.yaml            # Sealed secrets
│   ├── ingress.yaml           # TLS + routing
│   ├── hpa.yaml               # Horizontal pod autoscaler
│   ├── pdb.yaml               # Pod disruption budget
│   ├── postgres/
│   │   ├── statefulset.yaml   # PostgreSQL HA
│   │   └── service.yaml
│   ├── redis/
│   │   ├── statefulset.yaml   # Redis cluster
│   │   └── service.yaml
│   └── monitoring/
│       ├── servicemonitor.yaml
│       └── podmonitor.yaml
```

### 3.2 Kustomize Overlays

```
k8s/
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   ├── service.yaml
│   ├── ingress.yaml
│   └── configmap.yaml
├── overlays/
│   ├── dev/
│   │   ├── kustomization.yaml
│   │   └── replica-count.yaml
│   ├── staging/
│   │   ├── kustomization.yaml
│   │   ├── hpa.yaml
│   │   └── resources.yaml
│   └── production/
│       ├── kustomization.yaml
│       ├── hpa.yaml
│       ├── pdb.yaml
│       ├── sealed-secrets.yaml
│       └── pod-antiaffinity.yaml
```

### 3.3 Kubernetes Deployment Commands

```bash
# Helm install
helm upgrade --install gula ./helm/gula \
  --values ./helm/gula/values-prod.yaml \
  --namespace gula \
  --create-namespace

# Kustomize apply
kubectl apply -k k8s/overlays/production/

# Scale
kubectl scale deployment gula-backend --replicas=5 -n gula

# Rollout status
kubectl rollout status deployment/gula-backend -n gula
```

---

## 4. Terraform IaC (5 Environments)

### 4.1 Module Structure

```
terraform/
├── modules/
│   ├── networking/           # VPC, subnets, NAT, endpoints
│   ├── compute/              # ECS Fargate / EKS node groups
│   ├── database/             # PostgreSQL RDS, Redis ElastiCache
│   ├── storage/              # S3 buckets with lifecycle
│   ├── cdn/                  # CloudFront distributions
│   ├── security/             # WAF, KMS, Secrets Manager, IAM
│   └── monitoring/           # CloudWatch, Prometheus
├── environments/
│   ├── dev/
│   │   ├── main.tf
│   │   ├── terraform.tfvars
│   │   └── backend.conf
│   ├── staging/
│   ├── production/
│   ├── dr/
│   └── sandbox/
```

### 4.2 Terraform Workflow

```bash
# Initialize
cd terraform/environments/production
terraform init

# Plan
terraform plan -out=tfplan

# Apply
terraform apply tfplan

# Destroy (DR environment teardown)
terraform destroy -target=module.compute
```

---

## 5. Blue/Green Deployment

### 5.1 Strategy

Two identical environments (blue = live, green = staging) behind a load balancer:

```
User → Load Balancer (80/20 split)
         ├── Blue (current production) → 100% traffic
         └── Green (new version) → 0% traffic initially

Step 1: Deploy to green
Step 2: Run smoke tests against green
Step 3: Shift 10% traffic to green
Step 4: Monitor for 15 minutes
Step 5: Shift 50% → 100% traffic to green
Step 6: Blue becomes new staging
```

### 5.2 Docker Compose Blue/Green

```bash
# Deploy green
docker compose -p gula-green -f docker-compose.green.yml up -d

# Switch traffic
docker compose exec gateway nginx -s reload  # swaps upstream

# Verify
curl https://api.gula.health/health/deep

# Tear down blue
docker compose -p gula-blue down
docker compose -p gula-green rename gula-blue
```

---

## 6. Canary Deployment

```bash
# Deploy canary (1 instance with new version)
docker compose up -d --scale gula-backend=1 --scale gula-backend-canary=1

# Route 5% of traffic to canary (via nginx weight)
# nginx.conf:
upstream backend {
    server gula-backend:8000 weight=95;
    server gula-backend-canary:8000 weight=5;
}

# Monitor for 30 minutes
# If no errors: increase canary to 25% → 50% → 100%
# If errors: remove canary instance
```

---

## 7. Rollback Procedure

### 7.1 Automated Rollback

```bash
# Docker Compose
docker compose pull gula-backend              # pulls tagged version
docker compose up -d --no-deps gula-backend   # restart with old tag

# Kubernetes
kubectl rollout undo deployment/gula-backend -n gula
kubectl rollout status deployment/gula-backend -n gula

# Terraform
terraform plan -target=module.compute -var="ami_id=${PREVIOUS_AMI}"
terraform apply -target=module.compute
```

### 7.2 Rollback Criteria

| Signal | Threshold | Action |
|--------|-----------|--------|
| Error rate (5xx) | > 1% | Immediate rollback |
| Request latency (P99) | > 2s | Immediate rollback |
| DB connection errors | > 5/min | Immediate rollback |
| Health check failures | 2 consecutive | Automatic rollback |
| Disk I/O wait time | > 30% | Manual rollback |

---

## 8. Environment Variable Management

Secrets are managed via:
- **Development:** `.env` file (gitignored)
- **Staging:** AWS Secrets Manager
- **Production:** Sealed Secrets (K8s) + AWS Secrets Manager
- **CI/CD:** GitHub Actions secrets

### Key Environment Variables

| Variable | Source | Rotation |
|----------|--------|----------|
| `SECRET_KEY` | Secrets Manager | 90 days |
| `ENCRYPTION_KEY` | Secrets Manager | 90 days |
| `DB_PASSWORD` | Secrets Manager | 180 days |
| `REDIS_PASSWORD` | Secrets Manager | 180 days |
| `METRICS_BEARER_TOKEN` | Secret rotation | 30 days |
| `JWT_PUBLIC_KEY` | Configmap | Key rotation |
| `SENTRY_DSN` | Secrets Manager | Token-based |
