# GULA Platform — Application Atlas

**Classification:** CONFIDENTIAL
**Date:** 2026-07-18

---

## 1. Backend Applications

### Core Monolith (Production)

| Component | Location | Status | LOC |
|-----------|----------|--------|-----|
| FastAPI Application | `backend/app/main.py` | ✅ Production | 1,948 |
| Config & Secrets | `backend/app/config.py` | ✅ Production | — |
| Database Layer | `backend/app/database.py` | ✅ Production | — |
| Background Worker | `backend/app/worker.py` | ✅ Production | — |
| Route Modules | `backend/app/routes/` (53+ files) | ✅ Production | ~600K total |
| Service Layer | `backend/app/services/` (34+ files) | ✅ Production | — |
| ORM Models | `backend/app/models/` (31+ files) | ✅ Production | — |
| Core Infrastructure | `backend/app/core/` (15 modules) | ✅ Production | — |
| Security Modules | `backend/app/security/` (8+ modules) | ✅ Production | — |
| AI Modules | `backend/app/ai/` | ⚠️ Partial | — |
| Audit System | `backend/app/audit/` | ✅ Production | — |
| Financial Engine | `backend/app/financial/` | ⚠️ Schema only | — |
| Notifications | `backend/app/notifications/` | ✅ Production | — |
| Edge Platform | `backend/app/edge/` | ⚠️ Partial | — |
| Gateways | `backend/app/gateways/` | ✅ Production | — |

---

## 2. Microservices (Future Decomposition)

| Service | Location | Status | Tests | Notes |
|---------|----------|--------|-------|-------|
| **device_bridge** | `services/device_bridge/` | ✅ Production-ready | ✅ | ASTM/HL7 for Sysmex, Roche, Mindray |
| **ai** | `services/ai/main.py` | ✅ Functional | ❌ | Ollama-only, 3 tiers |
| **autonomous_manager** | `services/autonomous_manager/` | ✅ Functional | ❌ | Self-healing orchestration |
| **lab** | `services/lab/` | ❌ Stub | ❌ | Empty |
| **order** | `services/order/` | ❌ Stub | ❌ | Empty |
| **patient** | `services/patient/` | ❌ Stub | ❌ | Empty |
| **result** | `services/result/` | ❌ Stub | ❌ | Empty (with ClickHouse/Kafka/MinIO deps) |
| **sample** | `services/sample/` | ❌ Stub | ❌ | Empty |
| **notification** | `services/notification/` | ❌ Stub | ❌ | Empty |

---

## 3. Frontend Applications

| Application | Location | Framework | Status |
|-------------|----------|-----------|--------|
| Primary Portal | `frontend-v2/` | React 19 + Firebase | ✅ Production |
| Light Client | `client/` | tRPC + React 18 | ⚠️ Partial |
| Static PWA | `frontend/` | Static HTML/CSS/JS | ✅ Legacy |
| Desktop App | `hospital_desktop/` | — | ⚠️ Partial |

---

## 4. Supporting Platforms

| Platform | Location | Framework | Purpose |
|----------|----------|-----------|---------|
| National Health Oversight | `nhop-platform/` | FastAPI (separate, port 8100) | National citizen registry |
| Edge Agent | `edge_agent/` | Python (offline-first) | Remote lab site computing |
| AI Top-Level | `ai/` | Python | AI service, agent, outbreak, population health |
| CLI Tool | `cli/` | Python 2.1.0 | Developer tooling |
| Server Gateway | `server/` | Express.js | Additional routing |

---

## 5. Shared Library

| Component | Location | Status |
|-----------|----------|--------|
| Auth Module | `shared/auth/` | ✅ Production |
| RBAC Module | `shared/rbac/` | ✅ Production |
| Security Module | `shared/security/` | ✅ Production |
| Audit Module | `shared/audit/` | ✅ Production |
| Circuit Breaker | `shared/circuit_breaker/` | ✅ Production |
| Messaging | `shared/messaging/` | ✅ Production |

---

## 6. Infrastructure Configurations

| Configuration | Location | Services |
|---------------|----------|----------|
| Docker Compose (MVP) | `docker-compose.yml` | postgres, redis, backend, worker, frontend, api-gateway (+prometheus/grafana as profile) |
| Docker Compose (Full) | `docker-compose.full.yml` (821 lines) | 25+ services including Patroni, PgBouncer, ClickHouse, RabbitMQ, Kafka, MinIO, Ollama, Keycloak, Vault |
| Docker Compose (Scale) | `docker-compose.scale.yml` | HAProxy + N backend replicas |
| Kubernetes (Kustomize) | `k8s/` (base + 4 overlays) | dev, prod, region-eu, region-me |
| Helm Chart | `helm/` (v1.0.0, 38 templates) | 9 Bitnami dependencies |
| Terraform | `terraform/` (65 files, 12 modules) | AWS target (mismatched with DO deployment) |
| Monitoring | `config/prometheus/`, `config/grafana/` | 3 rule files, 4 dashboards |

---

## 7. Application Inventory Summary

| Category | Count |
|----------|-------|
| Production Applications | 8 |
| Stub/Incomplete Applications | 7 |
| Frontend Applications | 4 |
| Supporting Platforms | 5 |
| Infrastructure Configurations | 7 |
| CI/CD Workflows | 6 |
| **Total** | **37** |
