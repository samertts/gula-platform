# GULA Platform — Deployment Guide v1.0

**Version:** 1.0
**Date:** 2026-07-15
**Status:** FINAL

---

## 1. Prerequisites

### Required Software

| Software | Minimum Version | Verify |
|----------|----------------|--------|
| Docker | 24.0+ | `docker --version` |
| Docker Compose | 2.20+ | `docker compose version` |
| Git | 2.30+ | `git --version` |
| Python | 3.11+ | `python3 --version` |
| Make | 4.0+ | `make --version` |
| curl | 7.68+ | `curl --version` |
| jq | 1.6+ | `jq --version` |

### Optional Software (for K8s deployment)

| Software | Minimum Version | Verify |
|----------|----------------|--------|
| kubectl | 1.28+ | `kubectl version --client` |
| Helm | 3.12+ | `helm version` |
| kustomize | 5.0+ | `kustomize version` |

### System Requirements

| Deployment Type | vCPU | RAM | SSD | Network |
|----------------|------|-----|-----|---------|
| Development | 2 | 4 GB | 20 GB | Any |
| Staging | 4 | 8 GB | 50 GB | 100 Mbps |
| Production | 8+ | 16 GB+ | 100 GB+ | 1 Gbps |

### Required Access

- Git repository access (GitHub)
- Container registry access (GHCR)
- Cloudflare DNS management (for production)
- Let's Encrypt email (for TLS certificates)
- Object storage credentials (for backups)

---

## 2. Environment Setup

### Clone Repository

```bash
git clone https://github.com/samertts/gula-platform.git
cd gula-platform
```

### Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Generate secure secrets
make secrets-gen
```

### `.env` Configuration Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SECRET_KEY` | YES | — | 64-byte random hex string |
| `ENCRYPTION_KEY` | YES | — | 32-byte random hex string |
| `NID_HMAC_KEY` | YES | — | 32-byte random hex string |
| `REFRESH_TOKEN_SECRET` | YES | — | 64-byte random hex string |
| `DEVICE_HMAC_KEY` | YES | — | 32-byte random hex string |
| `POSTGRES_USER` | YES | `gula` | Database user |
| `POSTGRES_PASSWORD` | YES | — | Strong random password |
| `POSTGRES_DB` | YES | `gula` | Database name |
| `POSTGRES_HOST` | YES | `postgres` | Database hostname |
| `POSTGRES_PORT` | NO | `5432` | Database port |
| `REDIS_PASSWORD` | YES | — | Redis password |
| `REDIS_HOST` | YES | `redis` | Redis hostname |
| `REDIS_PORT` | NO | `6379` | Redis port |
| `METRICS_BEARER_TOKEN` | YES | — | Prometheus metrics auth |
| `GULA_ADMIN_TOKEN` | YES | — | Admin operations token |
| `SENTRY_DSN` | NO | — | Sentry error tracking |
| `ALERT_WEBHOOK_URL` | NO | — | Slack/Discord/Telegram webhook |
| `ENABLE_FINANCIAL_ENGINE` | NO | `false` | Financial features |
| `ENABLE_ADS` | NO | `false` | Advertising features |
| `SNDHS_ENABLE_VISITS` | NO | `false` | SNDHS visit tracking |
| `SNDHS_ENABLE_NATIONAL_ID` | NO | `false` | National ID support |
| `RUNTIME_MODE` | NO | `api` | `api`, `worker`, `test`, `cli` |

### Environment File Security

```bash
# Ensure .env is not tracked by git
echo ".env" >> .gitignore

# Lock down permissions
chmod 600 .env

# Backup encrypted copy
gpg --symmetric --output .env.gpg .env
```

---

## 3. Docker Compose Deployment

### Standard Deployment

```bash
# 1. Start all services
docker compose up -d

# 2. Verify all containers are running
docker compose ps

# 3. Wait for services to be ready (up to 60s)
sleep 30

# 4. Check health endpoint
curl -s http://localhost:8080/health | jq .

# 5. Readiness check
curl -s http://localhost:8080/health/ready | jq .

# 6. View logs
docker compose logs --tail=50 gula-backend
```

### Deployment with Full Monitoring Stack

```bash
# Start with monitoring profile
docker compose --profile monitoring up -d

# Access Grafana at http://localhost:3000
# Default credentials: admin / admin (change on first login)
```

### Deployment with HAProxy (Scaled)

```bash
# Start with scale profile
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d

# Access HAProxy stats at http://localhost:8404/stats

# Scale backend replicas
docker compose up -d --scale gula-backend=5
```

### Service Health Verification

```bash
# Full health check
make health

# Deep health diagnostic
make health-deep

# Combined status
make status
```

---

## 4. Kubernetes Deployment

### Prerequisites

```bash
# Create namespace
kubectl create namespace gula-platform

# Create secrets from .env
kubectl create secret generic gula-secrets --from-env-file=.env -n gula-platform

# Add required Helm repos
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo add grafana https://grafana.github.io/helm-charts
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add helm-stable https://charts.helm.sh/stable
helm repo update
```

### Helm Deployment

```bash
# Deploy PostgreSQL
helm upgrade --install postgres bitnami/postgresql \
  --namespace gula-platform \
  -f k8s/helm-values/postgres-values.yaml

# Deploy Redis
helm upgrade --install redis bitnami/redis \
  --namespace gula-platform \
  -f k8s/helm-values/redis-values.yaml

# Deploy GULA Platform
helm upgrade --install gula-platform helm/gula-platform \
  --namespace gula-platform \
  -f values-prod.yaml \
  --set image.tag=v1.0.0

# Wait for rollout
kubectl rollout status deployment/gula-backend -n gula-platform
```

### Kustomize Deployment

```bash
# Deploy the entire platform
kubectl apply -k k8s/overlays/production

# Verify resources
kubectl get all -n gula-platform

# Check pod status
kubectl get pods -n gula-platform -w
```

### K8s Ingress Configuration

```yaml
# k8s/base/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gula-api-ingress
  namespace: gula-platform
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - api.gula.health
    secretName: gula-api-tls
  rules:
  - host: api.gula.health
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: gula-backend
            port:
              number: 8000
```

---

## 5. Blue-Green Deployment

### Overview

Blue-green deployment maintains two identical environments (blue = current, green = new). Traffic is switched atomically.

### Procedure

```bash
# Step 1: Deploy the green environment
docker compose -f docker-compose.green.yml up -d

# Step 2: Run smoke tests against green
./scripts/smoke-test.sh --target green

# Step 3: Run integration tests
./scripts/integration_test.sh --target green

# Step 4: Switch traffic from blue to green
# Update api-gateway configuration
cp config/nginx/green.conf config/nginx/active.conf
docker compose exec api-gateway nginx -s reload

# Step 5: Monitor green for 15 minutes
watch -n 5 'curl -s https://api.gula.health/health/deep | jq .grade'

# Step 6: Decommission blue environment
docker compose -f docker-compose.blue.yml down
```

### K8s Blue-Green

```bash
# Deploy green
kubectl apply -f k8s/deployment-green.yaml

# Verify green
kubectl rollout status deployment/gula-backend-green -n gula-platform

# Switch label selector
kubectl patch service gula-backend -p '{"spec":{"selector":{"version":"green"}}}'

# After verification, remove blue
kubectl delete deployment gula-backend-blue -n gula-platform
```

### Automated Blue-Green via Helm

```bash
# Deploy green with canary annotations
helm upgrade --install gula-platform helm/gula-platform \
  --set canary.enabled=true \
  --set canary.weight=100
```

---

## 6. Canary Deployment

### Overview

Canary deployment routes a small percentage of traffic to the new version, gradually increasing as confidence grows.

### Procedure

```bash
# Step 1: Deploy canary (10% traffic)
kubectl apply -f k8s/deployment-canary.yaml

# Step 2: Verify metrics comparison
# Compare error rates, latency, and throughput between canary and stable

# Step 3: Gradually increase canary traffic
kubectl patch canary gula-backend --type merge \
  -p '{"spec":{"canary":{"weight":25}}}'
sleep 300  # Monitor for 5 minutes

kubectl patch canary gula-backend --type merge \
  -p '{"spec":{"canary":{"weight":50}}}'
sleep 300

kubectl patch canary gula-backend --type merge \
  -p '{"spec":{"canary":{"weight":75}}}'
sleep 300

# Step 4: Promote canary to stable
kubectl patch canary gula-backend --type merge \
  -p '{"spec":{"canary":{"weight":100}}}'

# Step 5: Remove old stable deployment
kubectl delete deployment gula-backend-stable -n gula-platform
```

### Canary with Linkerd (Traffic Splitting)

```yaml
apiVersion: split.smi-spec.io/v1alpha2
kind: TrafficSplit
metadata:
  name: gula-backend-split
  namespace: gula-platform
spec:
  service: gula-backend
  backends:
  - service: gula-backend-stable
    weight: 900m  # 90%
  - service: gula-backend-canary
    weight: 100m  # 10%
```

### Automated Rollback

Canary automatically rolls back if any of these conditions are met:

- Error rate increase >2%
- p99 latency increase >50%
- HTTP 5xx rate >1%
- Health check failure rate >5%

---

## 7. Database Migration

### Standard Migration

```bash
# Run pending migrations
docker compose run --rm gula-backend alembic upgrade head

# Verify schema is up to date
docker compose run --rm gula-backend alembic check
```

### Migration During Deployment

```bash
# Step 1: Before deploying new code, run migrations
docker compose run --rm gula-backend alembic upgrade head

# Step 2: Verify migration
docker compose run --rm gula-backend alembic current

# Step 3: Deploy new code (old code is backward-compatible with new schema)
docker compose up -d --no-deps gula-backend

# Step 4: Post-deployment verification
curl -s https://api.gula.health/health/deep | jq .
```

### Creating a New Migration

```bash
# Auto-generate migration from model changes
docker compose run --rm gula-backend alembic revision --autogenerate \
  -m "describe_what_changed"

# Review the generated migration in migrations/versions/
# Verify idempotency guards are in place

# Test on clean database
docker compose down -v && docker compose up -d postgres
docker compose run --rm gula-backend alembic upgrade head
docker compose run --rm gula-backend alembic downgrade -1
docker compose run --rm gula-backend alembic upgrade head
```

### Migration Rollback

```bash
# Rollback one migration
docker compose run --rm gula-backend alembic downgrade -1

# Rollback to specific revision
docker compose run --rm gula-backend alembic downgrade <revision_id>

# Rollback all the way
docker compose run --rm gula-backend alembic downgrade base
```

---

## 8. Post-Deployment Verification Checklist

Run this complete checklist after every deployment:

### Health & Availability

- [ ] `curl -f http://localhost:8080/health` returns 200
- [ ] `curl -f http://localhost:8080/health/ready` returns 200
- [ ] `curl -f http://localhost:8080/health/deep` returns grade GREEN
- [ ] All containers show `Up` in `docker compose ps`
- [ ] No `CRITICAL` or `ERROR` logs in last 5 minutes

### Database

- [ ] `docker compose run --rm gula-backend alembic current` matches expected revision
- [ ] Database connectivity verified: `docker compose exec postgres pg_isready`
- [ ] Required tables exist: `labs`, `lab_users`, `patients`, `lab_orders`, `lab_results`
- [ ] No migration errors in logs

### Redis

- [ ] Redis connectivity verified: `docker compose exec redis redis-cli PING`
- [ ] Cache is warming (hit ratio increasing)

### API Functionality

- [ ] Authentication endpoints respond correctly
- [ ] Test user can log in and receive JWT
- [ ] Patient CRUD operations work
- [ ] Order creation and result entry work
- [ ] Search endpoints return results
- [ ] Statistics endpoints return data

### Performance

- [ ] API latency p95 < 200ms (from /health/deep)
- [ ] No slow queries in database logs
- [ ] Resource usage within expected ranges

### Security

- [ ] TLS certificate valid and not expiring
- [ ] HSTS headers present on responses
- [ ] Security headers present (CSP, X-Frame-Options, etc.)
- [ ] `/docs` and `/redoc` are blocked (if production)
- [ ] Rate limiting is active
- [ ] Admin token authentication works on protected endpoints

### Integrations

- [ ] Device bridge can connect (if applicable)
- [ ] Webhook notifications are delivered
- [ ] Email/SMS notifications work (if configured)
- [ ] Backup system operational

### Monitoring

- [ ] Metrics are flowing to Prometheus
- [ ] Grafana dashboards show data
- [ ] Logs are shipping to Loki
- [ ] Alerts are configured and firing correctly
- [ ] PagerDuty integration tested

### Business Logic

- [ ] Tenant isolation verified (lab A cannot access lab B data)
- [ ] Audit logs are being written for mutations
- [ ] Patient card generation works
- [ ] QR code scanning returns correct patient data

---

## 9. Rollback Procedure

### Automated Rollback

```bash
# Docker Compose: roll back to previous tag
docker compose up -d --no-deps gula-backend=previous-tag

# K8s Helm: roll back to previous revision
helm rollback gula-platform 1 --namespace gula-platform

# K8s kubectl: roll back deployment
kubectl rollout undo deployment/gula-backend -n gula-platform
```

### Manual Rollback (Docker Compose)

```bash
# Step 1: Identify the last good version
docker compose images gula-backend

# Step 2: Pull the previous image
docker compose pull gula-backend=<previous-tag>

# Step 3: Restart with previous image
docker compose up -d --no-deps --force-recreate gula-backend

# Step 4: Verify health
curl -f https://api.gula.health/health/ready

# Step 5: If DB migration was rolled back, run downgrade
docker compose run --rm gula-backend alembic downgrade -1
```

### Database Rollback

```bash
# Step 1: Check current migration
docker compose run --rm gula-backend alembic current

# Step 2: Rollback the migration
docker compose run --rm gula-backend alembic downgrade <previous_revision>

# Step 3: Verify
docker compose run --rm gula-backend alembic current
```

### Full System Rollback

```bash
# Step 1: Stop all services
docker compose down

# Step 2: Revert .env to previous version
cp .env.backup .env

# Step 3: Restore database from backup
./scripts/restore-test.sh latest

# Step 4: Start services with previous image tag
GULA_IMAGE_TAG=<previous-tag> docker compose up -d

# Step 5: Verify everything
make health && make health-deep
```

### Rollback Decision Matrix

| Issue Type | Rollback? | Alternative |
|-----------|-----------|-------------|
| Code error (API returns 500) | YES | Hotfix if quick |
| Migration error | YES | Fix forward if possible |
| Configuration error | YES | Fix config, restart |
| Performance regression | YES | Scale up, then fix |
| Security vulnerability | YES | Emergency hotfix |
| Data inconsistency | NO (see below) | Data repair procedure |
| Partial functionality | Maybe | Feature flag disable |

**Important**: Never roll back a database migration that removes columns or data. Always prefer a "fix forward" approach for data-affecting changes.

---

## 10. First-Time Deployment Checklist

### Pre-Deployment

- [ ] Source code cloned and on correct branch
- [ ] `.env` file created with strong secrets
- [ ] Required ports are available (80, 443, 5432, 6379, 5672, 9000)
- [ ] Docker and Docker Compose installed and running
- [ ] Network connectivity verified (can pull images)
- [ ] DNS configured (api.gula.health, app.gula.health)
- [ ] TLS certificates provisioned
- [ ] Backup destination configured
- [ ] Monitoring stack configured
- [ ] Alerting channels configured (Slack, PagerDuty)

### Deployment

- [ ] Run `make up` (or `docker compose up -d`)
- [ ] Wait for all containers to be healthy
- [ ] Run `make health-deep` — should show GREEN
- [ ] Create initial admin user
- [ ] Verify API endpoints respond
- [ ] Deploy frontend

### Post-Deployment

- [ ] Run smoke tests
- [ ] Verify TLS and DNS
- [ ] Configure monitoring dashboards
- [ ] Set up backup schedule
- [ ] Verify alert delivery
- [ ] Document all configuration changes
- [ ] Tag the release
- [ ] Notify stakeholders

---

## 11. Deployment Automation (CI/CD)

### CI Pipeline (`.github/workflows/ci.yml`)

The CI pipeline runs on every push and executes:

1. **syntax-gate** — Python compilation check + flake8
2. **migration-check** — Alembic migration test on fresh DB
3. **smoke-test** — API smoke tests
4. **backend-test** — Full pytest suite
5. **security-scan** — SAST, dependency scan, secret scan, container scan
6. **build-and-push** — Build and push Docker images to GHCR

### CD Pipeline (`.github/workflows/deploy.yml`)

```bash
# Trigger deployment manually
gh workflow run deploy.yml --ref main

# Trigger with specific tag
gh workflow run deploy.yml --ref v1.0.0

# Monitor deployment
gh run watch
```

### Local CI Simulation

```bash
# Full CI pipeline locally
make ci

# Partial checks
make lint
cd backend && python -m pytest tests/ -v
```
