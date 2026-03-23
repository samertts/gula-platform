# GULA Platform - Enterprise Medical Laboratory Architecture

## System Architecture

```
Internet
    │
    ▼
┌─────────────────────────────────────────────────────┐
│  WAF / Rate Limiting / IP Filtering                 │
│  (Nginx with ModSecurity rules)                     │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│  API Gateway (Nginx)                                │
│  - Rate limiting: 100 req/min per IP                │
│  - Auth endpoint: 10 req/min                        │
│  - Security headers (XSS, CSRF, CSP)                │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
  ┌─────────────┐ ┌──────────┐ ┌──────────┐
  │ Lab Service │ │ Patient  │ │ Order    │
  │ :8001       │ │ Service  │ │ Service  │
  │             │ │ :8002    │ │ :8003    │
  └─────────────┘ └──────────┘ └──────────┘
         │             │             │
  ┌─────────────┐ ┌──────────┐
  │ Result Svc  │ │ Sample   │
  │ :8004       │ │ Service  │
  │             │ │ :8005    │
  └─────────────┘ └──────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  RabbitMQ Event Bus                                 │
│  Queues: orders.events | samples.events             │
│         results.events | alerts.events              │
│         audit.events   | retry.queue                │
│  All queues: durable + persistent + ACK delivery    │
└──────────────────────┬──────────────────────────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
  ┌─────────────┐ ┌──────────┐ ┌──────────────────┐
  │ AI Service  │ │ Notif.   │ │ Kafka Pipeline   │
  │ (Ollama)    │ │ Service  │ │ Analytics Stream │
  │ llama3      │ │          │ │                  │
  └─────────────┘ └──────────┘ └──────────────────┘
         │
    3 AI Tiers:
    - Operational AI
    - Clinical AI
    - Population AI
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
  ┌─────────────┐ ┌──────────┐ ┌──────────────────┐
  │ PostgreSQL  │ │  Redis   │ │  ClickHouse      │
  │ Primary/    │ │  Cache   │ │  Analytics       │
  │ Replica     │ │          │ │                  │
  │ (PgBouncer) │ └──────────┘ └──────────────────┘
  └─────────────┘
         │
  ┌─────────────────────────────────────────────────┐
  │  MinIO Object Storage                           │
  │  Buckets: medical-reports | lab-images          │
  │          device-results                         │
  └─────────────────────────────────────────────────┘
         │
  ┌─────────────────────────────────────────────────┐
  │  Monitoring Stack                               │
  │  Prometheus (metrics) | Grafana (dashboards)    │
  │  Loki (logs) | Jaeger (tracing)                 │
  └─────────────────────────────────────────────────┘
```

## Executive Orders Status

| Order | Description | Status | Implementation |
|-------|-------------|--------|----------------|
| 1 | System restart and verification | ✅ | `make restart` |
| 2 | RabbitMQ queues verification | ✅ | `make check-queues` |
| 3 | Local AI (Ollama) verification | ✅ | `make pull-ai` |
| 4 | Disable external AI providers | ✅ | `.env: AI_PROVIDER=ollama, AI_FALLBACK=false` |
| 5 | Medical audit logging | ✅ | `audit_log` table + triggers + RabbitMQ |
| 6 | Durable persistent RabbitMQ | ✅ | `config/rabbitmq/definitions.json` |
| 7 | Circuit Breaker pattern | ✅ | `services/shared/circuit_breaker.py` |
| 8 | Retry Queue | ✅ | `retry.queue` in RabbitMQ |
| 9 | PgBouncer connection pooling | ✅ | `gula-pgbouncer` service |
| 10 | Read/Write splitting | ✅ | Primary + Replica PostgreSQL |
| 11 | Table partitioning | ✅ | `test_results` partitioned by month |
| 12 | ClickHouse analytics | ✅ | `gula-clickhouse` + schema |
| 13 | MinIO object storage | ✅ | `gula-minio` + result upload API |
| 14 | Monitoring (Prometheus/Loki/Jaeger) | ✅ | Full observability stack |
| 15 | API security (rate limiting/WAF) | ✅ | Nginx with rate limiting zones |
| 16 | Keycloak identity management | ✅ | `gula-keycloak` service |
| 17 | HashiCorp Vault secrets | ✅ | `gula-vault` + `make vault-init` |
| 18 | Apache Kafka data pipeline | ✅ | `gula-kafka` + `gula-zookeeper` |
| 19 | Multi-tier AI system | ✅ | Operational/Clinical/Population AI |
| 20 | Backup system | ✅ | `scripts/backup.sh` |
| 21 | Kubernetes readiness | ✅ | `k8s/base/` + `k8s/overlays/dev` & `prod` (kustomize) — `make k8s-dev` / `make k8s-prod` |
| 22 | Blue-Green deployment | ✅ | `.github/workflows/blue-green-deploy.yml` — auto-switch blue↔green on every main push |
| 23 | Autonomous self-healing | ✅ | `gula-autonomous-manager` |

## Service Ports

| Service | Port | Description |
|---------|------|-------------|
| API Gateway | 80 | Main entry point |
| Frontend | 8080 | Web UI |
| Lab Service | 8001 | Lab management |
| Patient Service | 8002 | Patient records |
| Order Service | 8003 | Test orders |
| Result Service | 8004 | Test results |
| Sample Service | 8005 | Sample tracking |
| Notification | 8006 | Notifications |
| Autonomous Manager | 8010 | Self-healing |
| AI Service | 9000 | Local AI (Ollama) |
| Ollama | 11434 | llama3 model |
| PostgreSQL Primary | 5432 | Write operations |
| PostgreSQL Replica | 5433 | Read operations |
| PgBouncer | 6432 | Connection pool |
| Redis | 6379 | Cache |
| RabbitMQ | 5672/15672 | Event bus |
| Kafka | 9092 | Analytics pipeline |
| ClickHouse | 8123 | Analytics queries |
| MinIO | 9003/9002 | Object storage |
| Keycloak | 8081 | Identity/SSO |
| Vault | 8200 | Secrets management |
| Prometheus | 9090 | Metrics |
| Grafana | 3000 | Dashboards |
| Loki | 3100 | Log aggregation |
| Jaeger | 16686 | Distributed tracing |

## Quick Start

```bash
# 1. Start all services
make up

# 2. Pull AI model (required once)
make pull-ai

# 3. Verify health
make health

# 4. Check RabbitMQ queues
make check-queues

# 5. Initialize Vault secrets
make vault-init
```
