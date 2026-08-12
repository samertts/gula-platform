# PI-004 — Infrastructure Guide

## National Platform Infrastructure Architecture

**Version:** 2.1.0
**Date:** July 2026

---

## 1. Network Topology

### 1.1 VPC Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     VPC (10.0.0.0/16)                    │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │  Public Subnet   │  │  Private Subnet │               │
│  │  10.0.1.0/24     │  │  10.0.2.0/24    │               │
│  │                  │  │                 │               │
│  │  NAT Gateway     │  │  ECS/EKS Nodes  │               │
│  │  Load Balancer   │  │  Backend Tasks  │               │
│  │  Bastion Host    │  │  Redis Cluster  │               │
│  └─────────────────┘  └─────────────────┘               │
│                                                          │
│  ┌─────────────────┐  ┌─────────────────┐               │
│  │  DB Subnet       │  │  Storage Subnet │               │
│  │  10.0.3.0/24     │  │  10.0.4.0/24    │               │
│  │                  │  │                 │               │
│  │  PostgreSQL HA   │  │  VPC Endpoint   │               │
│  │  Primary + Replic│  │  → S3 Gateway   │               │
│  │  Multi-AZ        │  │  → DynamoDB     │               │
│  └─────────────────┘  └─────────────────┘               │
│                                                          │
│  Availability Zones: me-central-1a, me-central-1b       │
└──────────────────────────────────────────────────────────┘
```

### 1.2 Security Groups

| Security Group | Rules | Source/Dest |
|---------------|-------|-------------|
| **alb-sg** | Inbound: 443, 80 | 0.0.0.0/0 |
| **backend-sg** | Inbound: 8000 | alb-sg only |
| **db-sg** | Inbound: 5432 | backend-sg, bastion-sg |
| **redis-sg** | Inbound: 6379 | backend-sg only |
| **bastion-sg** | Inbound: 22 | Office IPs only |
| **rabbitmq-sg** | Inbound: 5672, 15672 | backend-sg only |

### 1.3 Network Endpoints

| Endpoint | Type | Service |
|----------|------|---------|
| `com.amazonaws.me-central-1.s3` | Gateway | S3 access without NAT |
| `com.amazonaws.me-central-1.ecr.dkr` | Interface | ECR container registry |
| `com.amazonaws.me-central-1.ecr.api` | Interface | ECR API |
| `com.amazonaws.me-central-1.cloudwatch` | Interface | CloudWatch metrics |
| `com.amazonaws.me-central-1.logs` | Interface | CloudWatch Logs |
| `com.amazonaws.me-central-1.secretsmanager` | Interface | Secrets Manager |
| `com.amazonaws.me-central-1.kms` | Interface | KMS |

---

## 2. Compute

### 2.1 ECS Fargate (Primary)

| Service | Task Size | CPU | Memory | Min | Max | Auto-scaling |
|---------|-----------|-----|--------|-----|-----|--------------|
| gula-backend | 2 vCPU | 1024 | 2048MB | 2 | 10 | CPU > 70% |
| gula-worker | 1 vCPU | 512 | 1024MB | 1 | 5 | Queue depth |
| device-bridge | 1 vCPU | 512 | 1024MB | 1 | 3 | Device connections |

### 2.2 EKS Node Groups (Alternative)

| Node Group | Instance Type | Min | Max | Purpose |
|------------|--------------|-----|-----|---------|
| backend | t3.medium | 2 | 10 | Application pods |
| data | m6i.large | 2 | 5 | DB + Redis + message queue |
| monitoring | t3.small | 1 | 3 | Prometheus, Grafana, Loki |

### 2.3 Auto-Scaling Policies

```yaml
# Backend scaling policy
scaling_policy:
  metric: CPUUtilization
  target: 65
  scale_in: > 45% for 15 min
  scale_out: > 70% for 5 min
  cooldown: 120 seconds
```

---

## 3. Database

### 3.1 PostgreSQL 16 HA

| Configuration | Primary | Read Replica | Standby |
|---------------|---------|--------------|---------|
| Instance type | db.r6g.large | db.r6g.large | db.r6g.large |
| vCPU | 2 | 2 | 2 |
| Memory | 16GB | 16GB | 16GB |
| Storage | 200GB gp3 | 200GB gp3 | 200GB gp3 |
| IOPS | 3000 | 3000 | 3000 |
| Max connections | 100 | 50 | 100 |
| Replication | — | Streaming async | Streaming sync |
| AZ | me-central-1a | me-central-1b | me-central-1a |
| Backup | Automated daily | — | — |
| Retention | 30 days | — | — |

### 3.2 Connection Pool (Application Level)

```python
DB_POOL_SIZE = 6       # Per worker
DB_MAX_OVERFLOW = 12   # Per worker
WEB_CONCURRENCY = 3    # Gunicorn workers
# Total: 3 × (6 + 12) = 54 < 100 (max_connections)
```

### 3.3 Redis 7 Cluster

| Configuration | Primary | Replica |
|---------------|---------|---------|
| Instance type | cache.r6g.large | cache.r6g.large |
| vCPU | 2 | 2 |
| Memory | 13.07GB | 13.07GB |
| Clustering | Enabled (shards: 2) | — |
| Node type | 2 shards × 1 replica | — |
| Max memory policy | allkeys-lru | — |
| Persistence | AOF (every 1s) | — |

### 3.4 RabbitMQ

| Configuration | Value |
|---------------|-------|
| Instance | mq.m5.large |
| vCPU | 2 |
| Memory | 8GB |
| Storage | 100GB gp3 |
| Max queues | 20 |
| Max connections | 500 |
| Dead letter exchange | Enabled |
| Message persistence | Queue durable + persistent delivery |

---

## 4. Storage

### 4.1 S3 Buckets

| Bucket | Purpose | Lifecycle | Encryption |
|--------|---------|-----------|------------|
| `gula-apps-prod` | Static app hosting | N/A | SSE-S3 |
| `gula-backups` | DB backups | 30d → Glacier, 365d → Deep Archive | SSE-S3 + KMS |
| `gula-logs` | Application logs | 90d → Glacier, 365d → Delete | SSE-S3 |
| `gula-uploads` | User file uploads | 30d temporary | SSE-S3 (KMS) |
| `gula-artifacts` | Build artifacts | 90d | SSE-S3 |
| `gula-ml-models` | ML model storage | Indefinite | SSE-KMS |

### 4.2 Cross-Region Replication

```
Source: gula-*-prod (me-central-1)
Destination: gula-*-dr (eu-central-1)
Replication time: < 15 minutes
Replication scope: All objects
IAM role: gula-s3-replication-role
```

---

## 5. CDN (CloudFront)

### 5.1 Distribution Configuration

| Property | Value |
|----------|-------|
| Origins | S3 buckets (app origins) |
| Price class | All Edge Locations (Global) |
| SSL | Custom certificate (ACM) |
| Minimum TLS | TLSv1.2_2021 |
| Default TTL | 86400 seconds |
| Max TTL | 31536000 seconds |
| Error pages | 403 → /index.html (SPA), 404 → /index.html |
| Geo restriction | None (national access only) |
| WAF ACL | gula-waf (SQLi, XSS, rate limiting) |
| Logging | S3 bucket `gula-cdn-logs` |

### 5.2 Behaviors

| Path Pattern | Origin | Policy | Allowed Methods |
|-------------|--------|--------|----------------|
| `/citizen/*` | citizen S3 | Managed-CachingOptimized | GET, HEAD |
| `/doctor/*` | doctor S3 | Managed-CachingOptimized | GET, HEAD |
| `/lab/*` | lab S3 | Managed-CachingOptimized | GET, HEAD |
| `/radiology/*` | radiology S3 | Managed-CachingOptimized | GET, HEAD |
| `/ministry/*` | ministry S3 | Managed-CachingOptimized | GET, HEAD |
| `/api/*` | ALB | Managed-NoCache | ALL |
| `/ws/*` | ALB | WebSocket | GET |

---

## 6. Security Services

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **AWS WAF** | Web application firewall | SQLi, XSS, rate-based rules, IP reputation lists |
| **AWS KMS** | Encryption key management | Customer-managed keys, automatic rotation (1 year) |
| **AWS IAM** | Identity and access management | Least-privilege roles for all services |
| **AWS Secrets Manager** | Secret storage | Automatic rotation for DB credentials (180 days) |
| **AWS Shield** | DDoS protection | AWS Shield Advanced |
| **AWS GuardDuty** | Threat detection | Enabled on all accounts |
| **AWS Security Hub** | Security posture | CIS benchmarks, Foundational Security Best Practices |
| **AWS Config** | Compliance monitoring | All resources tracked, rules for encryption/access |
| **AWS CloudTrail** | API audit trail | Multi-region, log file validation enabled |

---

## 7. Monitoring Infrastructure

### 7.1 Prometheus Configuration

| Setting | Value |
|---------|-------|
| Retention | 15 days |
| Scrape interval | 15s (default), 5s (critical) |
| Storage | 50GB EBS gp3 |
| Remote write | Thanos (long-term, S3) |
| Rules | 25 alerting rules, 10 recording rules |

### 7.2 Grafana Configuration

| Setting | Value |
|---------|-------|
| Dashboards | 8 pre-provisioned |
| Datasources | Prometheus, Loki, CloudWatch, PostgreSQL |
| Users | OAuth via Google Workspace |
| Auth proxy | Behind API Gateway with JWT |

### 7.3 Agent Deployment

```yaml
# DaemonSet for node monitoring
node_exporter:
  enabled: true
  version: 1.8.x

cadvisor:
  enabled: true
  version: 0.49.x

promtail:
  enabled: true
  version: 3.x
  clients:
    - url: http://loki:3100/loki/api/v1/push
```

---

## 8. Terraform Modules Documentation

### 8.1 Module: `networking`

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `vpc_cidr` | string | `10.0.0.0/16` | VPC CIDR block |
| `azs` | list | `["a", "b"]` | Availability Zones |
| `public_subnets` | list | `["10.0.1.0/24", "10.0.5.0/24"]` | Public subnet CIDRs |
| `private_subnets` | list | `["10.0.2.0/24", "10.0.6.0/24"]` | Private subnet CIDRs |
| `database_subnets` | list | `["10.0.3.0/24", "10.0.7.0/24"]` | DB subnet CIDRs |

**Outputs:** `vpc_id`, `public_subnet_ids`, `private_subnet_ids`, `db_subnet_ids`, `vpc_endpoint_sg_id`

### 8.2 Module: `database`

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `instance_class` | string | `db.r6g.large` | RDS instance type |
| `allocated_storage` | number | 200 | Storage in GB |
| `multi_az` | bool | true | Multi-AZ deployment |
| `backup_retention` | number | 30 | Days of backup retention |
| `deletion_protection` | bool | true | Prevent accidental deletion |

**Outputs:** `primary_endpoint`, `reader_endpoint`, `replica_endpoint`, `port`

### 8.3 Module: `compute`

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `task_cpu` | number | 1024 | CPU units for Fargate task |
| `task_memory` | number | 2048 | Memory MB for Fargate task |
| `min_capacity` | number | 2 | Minimum task count |
| `max_capacity` | number | 10 | Maximum task count |
| `container_port` | number | 8000 | Application container port |

**Outputs:** `cluster_name`, `service_name`, `task_definition_arn`, `target_group_arn`

### 8.4 Module: `monitoring`

| Input | Type | Default | Description |
|-------|------|---------|-------------|
| `prometheus_retention` | string | `15d` | Prometheus data retention |
| `grafana_admin_password` | string | (required) | Grafana admin password |
| `alertmanager_slack_url` | string | (required) | Slack webhook URL |
| `alertmanager_pagerduty_key` | string | (optional) | PagerDuty integration key |

**Outputs:** `prometheus_endpoint`, `grafana_endpoint`, `alertmanager_endpoint`
