# PI-004 — Release Notes

## deployment-platform-v1.0

**Release Date:** July 2026
**Version:** 2.1.0

---

## Overview

This initial release of the GULA Deployment Platform establishes the full production infrastructure for the Iraqi national health system. The platform supports 5 environment tiers (dev, staging, production, DR, sandbox) with Infrastructure as Code via Terraform, container orchestration via Docker Compose (primary) and Kubernetes (alternative), comprehensive monitoring via Prometheus + Grafana, and disaster recovery with 1-hour RPO and 4-hour RTO.

---

## What's Included

### Infrastructure
- **Terraform modules**: networking, compute (ECS + EKS), database, storage, CDN, security, monitoring
- **5 environment tiers**: dev, staging, production, DR, sandbox with isolated VPCs
- **Multi-AZ deployment**: PostgreSQL HA, Redis cluster, application auto-scaling
- **VPC architecture**: Public, private, database, and storage subnets with NAT gateway + VPC endpoints
- **Auto-scaling**: CPU-based (65% target), 2-10 backend replicas

### Compute & Orchestration
- **Docker Compose (primary)**: `docker-compose.yml` for MVP, `docker-compose.full.yml` for full stack, `docker-compose.scale.yml` for horizontal scaling
- **Kubernetes (alternative)**: Helm charts + Kustomize overlays for all 5 environments
- **CI/CD pipeline**: GitHub Actions with 6 sequential jobs (syntax → migration → smoke → test → security → build)
- **Blue/green deployment**: Zero-downtime traffic switching via nginx upstream swap
- **Canary deployment**: Weighted traffic routing (5% → 25% → 50% → 100%)

### Database
- **PostgreSQL 16 HA**: Primary + read replica with streaming replication
- **Redis 7 cluster**: 2 shards × 1 replica, AOF persistence, allkeys-lru eviction
- **RabbitMQ**: Async message broker with dead letter exchange, 20 queues
- **Connection management**: `WEB_CONCURRENCY × (DB_POOL_SIZE + DB_MAX_OVERFLOW) < max_connections`
- **Automated backups**: Daily full (30d retention), continuous WAL archiving (7d), monthly long-term (7yr)

### Monitoring & Observability
- **Prometheus**: 15s scrape interval, 15d retention, Thanos remote write
- **Grafana**: 8 pre-provisioned dashboards, OAuth authentication
- **Loki + Promtail**: Structured JSON logging with LogQL queries
- **Alertmanager**: 10 alert rules across critical/warning/info, routed to Telegram + Discord + PagerDuty
- **Health endpoints**: `/health`, `/health/live`, `/health/ready`, `/health/deep`, `/health/status`

### Disaster Recovery
- **RPO**: 1 hour | **RTO**: 4 hours (30 min read-only)
- **Cross-region failover**: Primary (Bahrain/AUH) → DR (Frankfurt)
- **PITR**: Point-in-time recovery within 7-day window (1-minute accuracy)
- **Backup verification**: Automated daily checks, monthly restore drills
- **Failback procedure**: Documented step-by-step with integrity verification

### Security
- **Defense in depth**: WAF, Shield Advanced, GuardDuty, Security Hub, Config
- **Encryption**: AES-256-GCM at rest, TLS 1.3 in transit, KMS key management
- **IAM**: Least-privilege roles for all services, automatic secret rotation (30-365 days)
- **Penetration testing**: 29 findings resolved (0 critical, 2 high)
- **Compliance**: Iraqi MoH, HIPAA-aligned, ISO 27001 controls

---

## Breaking Changes

- **Docker Compose network**: The production compose file now uses an explicit network (`gula-network`) with static IP allocation. Existing containers must be recreated.
- **Environment variables**: `DATABASE_URL` format changed to include SSL parameters (`?sslmode=require`). Update all `.env` files.
- **API Gateway port**: Internal API gateway port changed from 80 to 8080. Update any direct container references.
- **Secret names**: Legacy secrets removed from environment. All secrets now managed via AWS Secrets Manager.

---

## Known Issues

| ID | Description | Severity | Workaround | Target Fix |
|----|-------------|----------|------------|------------|
| INFRA-001 | EKS node group scaling takes 5-8 minutes | Low | Pre-warm with cluster-autoscaler overprovisioning | v2.2.0 |
| INFRA-002 | P99 latency spikes during backup window (02:00) | Low | Schedule backup at 02:00 (lowest traffic) | Acceptable |
| INFRA-003 | Terraform state locking conflict with parallel applies | Medium | Use `terraform lock` file + CI serialization | v2.2.0 |
| INFRA-004 | Prometheus retention causes PVC growth of 500MB/day | Low | Increase PVC size or enable compaction | v2.2.0 |
| INFRA-005 | Log shipping latency peaks at 30s during traffic spikes | Medium | Increase Promtail batch size | v2.1.1 |

---

## Future Roadmap

### v2.2.0
- Automated failover (Lambda + Route53 health checks)
- Service mesh (Istio) for canary deployments
- Kubernetes as primary deployment target
- Enhanced cost monitoring with Kubecost

### v2.3.0
- Multi-region active-active deployment
- Database sharding for national scale
- AI-powered predictive auto-scaling
- Compliance automation (auto-audit reports)

### v3.0.0
- Fully automated disaster recovery (no-touch failover)
- Edge computing nodes for remote labs
- Capacity planning with ML-based forecasting
- Zero-trust security model
