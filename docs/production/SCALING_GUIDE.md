# GULA Platform — Scaling Guide v1.0

**Version:** 1.0
**Date:** 2026-07-15
**Status:** FINAL

---

## 1. When to Scale

### Decision Matrix

| Metric | Warning Threshold | Critical Threshold | Action |
|--------|------------------|-------------------|--------|
| CPU utilization | >70% for 5 min | >85% for 5 min | Vertical or horizontal scale |
| Memory utilization | >80% for 5 min | >90% for 5 min | Vertical scale or memory limit increase |
| API latency p95 | >300 ms | >500 ms | Add replicas or optimize queries |
| API latency p99 | >500 ms | >1 s | Add replicas, check slow queries |
| Error rate (5xx) | >0.5% | >2% | Check health, scale if traffic related |
| DB connections | >60% of pool | >80% of pool | Increase pool size or add PgBouncer |
| DB query latency p95 | >200 ms | >500 ms | Add indexes, read replicas |
| DB replication lag | >5 s | >30 s | Check replica resources, network |
| Redis memory | >70% of max | >85% of max | Increase memory or cluster |
| Queue depth | >1000 messages | >10000 messages | Add queue consumers |
| Disk usage | >70% | >85% | Clean or expand |
| Request rate | >150 req/s (per instance) | >200 req/s | Add backend replicas |
| Concurrent users | >400 (per instance) | >500 | Add backend replicas |

### Growth Projections

| Metric | Current | 3 Months | 6 Months | 12 Months |
|--------|---------|----------|----------|-----------|
| Active labs | — | — | — | — |
| Daily orders | — | — | — | — |
| API req/s | — | — | — | — |
| DB size | — | — | — | — |
| Storage used | — | — | — | — |

*Fill in actual values from monitoring after deployment.*

### Scaling Cost-Benefit

| Action | Cost | Benefit | When |
|--------|------|---------|------|
| Add backend replica | $ | +200 req/s, HA | Immediate need |
| Increase backend CPU | $ | +50% throughput | CPU bottleneck |
| Add DB read replica | $$ | +1000 qps read capacity | Read-heavy workload |
| PgBouncer | $ | +500% connection capacity | Connection pool exhaustion |
| Redis Cluster | $$$ | Horizontally scalable cache | Cache > 10 GB |
| DB sharding | $$$$ | Vertically unlimited writes | Write throughput > 5000 tps |
| MinIO distributed | $$ | HA + scalable storage | Storage > 1 TB |
| K8s HPA | $ | Automatic scaling | Variable load patterns |

---

## 2. Vertical Scaling

### Backend Vertical Scaling

```yaml
# docker-compose.override.yml
services:
  gula-backend:
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: '16G'
        reservations:
          cpus: '4'
          memory: '8G'
```

### Database Vertical Scaling

```bash
# Increase PostgreSQL resources
docker compose up -d --no-deps postgres

# Update PostgreSQL config in docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    deploy:
      resources:
        limits:
          cpus: '8'
          memory: '16G'
    shm_size: '2gb'  # Increase shared memory
    # Also adjust:
    # postgresql.conf changes via environment
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      # Performance tuning
      PGDATA: /var/lib/postgresql/data/pgdata
    # Mount SSD-backed volume
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### PostgreSQL Tuning for Vertical Scale

```ini
# postgresql.conf — tuned for 16GB RAM, 8 vCPU
max_connections = 200
shared_buffers = 4GB          # 25% of RAM
effective_cache_size = 12GB   # 75% of RAM
work_mem = 64MB               # per-operation memory
maintenance_work_mem = 1GB    # for maintenance operations
wal_buffers = 64MB
random_page_cost = 1.1        # SSD
effective_io_concurrency = 200 # SSD
checkpoint_completion_target = 0.9
max_worker_processes = 8
max_parallel_workers_per_gather = 4
max_parallel_workers = 8
```

---

## 3. Horizontal Scaling

### Backend Replicas (Docker Compose)

```bash
# Standard scale
docker compose up -d --scale gula-backend=5

# With HAProxy load balancer
docker compose -f docker-compose.yml -f docker-compose.scale.yml up -d
docker compose up -d --scale gula-backend=5
```

HAProxy configuration for backend scaling:

```haproxy
# config/haproxy/haproxy.cfg
frontend gula-backend
    bind *:8000
    default_backend gula-backend-servers

backend gula-backend-servers
    balance roundrobin
    option httpchk GET /health/live
    http-check expect status 200
    default-server inter 10s fall 3 rise 2
    server backend-1 gula-backend-1:8000 check
    server backend-2 gula-backend-2:8000 check
    server backend-3 gula-backend-3:8000 check
    server backend-4 gula-backend-4:8000 check
    server backend-5 gula-backend-5:8000 check
```

### Backend Replicas (Kubernetes HPA)

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gula-backend-hpa
  namespace: gula-platform
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gula-backend
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: 150
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
      - type: Pods
        value: 4
        periodSeconds: 60
      selectPolicy: Max
```

### Connection Pool Tuning for Multiple Replicas

When scaling backend replicas, adjust connection pool settings to stay within PostgreSQL `max_connections`:

```
max_connections >= WEB_CONCURRENCY × replicas × (DB_POOL_SIZE + DB_MAX_OVERFLOW)

Example: 3 workers × 5 replicas × (6 + 12) = 270 connections
→ Set max_connections = 300 (add headroom)
```

---

## 4. Database Scaling

### Read Replicas

```yaml
# docker-compose.db-scale.yml
services:
  postgres-replica-1:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
      PRIMARY_HOST: postgres
    command: >
      bash -c "until pg_isready -h $PRIMARY_HOST; do sleep 1; done
      && pg_basebackup -h $PRIMARY_HOST -D /var/lib/postgresql/data -S replication_slot -X stream -P
      && echo 'primary_conninfo = host=$PRIMARY_HOST port=5432 user=replicator password=$POSTGRES_PASSWORD' >> /var/lib/postgresql/data/postgresql.auto.conf
      && echo 'primary_slot_name = replication_slot' >> /var/lib/postgresql/data/postgresql.auto.conf
      && touch /var/lib/postgresql/data/standby.signal
      && docker-entrypoint.sh postgres"
    volumes:
      - postgres_replica_1:/var/lib/postgresql/data
    depends_on:
      - postgres
```

### Read/Write Splitting

Configure read/write splitting in `backend/app/config.py`:

```python
# Database read/write configuration
DATABASE_URL_READ = os.getenv(
    "DATABASE_URL_READ",
    f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST_REPLICA}:{DB_PORT}/{DB_NAME}"
)
```

### PgBouncer for Connection Pooling

```yaml
# docker-compose.pgbouncer.yml
services:
  pgbouncer:
    image: edoburu/pgbouncer:1.21
    environment:
      DB_USER: ${POSTGRES_USER}
      DB_PASSWORD: ${POSTGRES_PASSWORD}
      DB_HOST: postgres
      DB_PORT: "5432"
      DB_NAME: ${POSTGRES_DB}
      POOL_MODE: transaction
      MAX_CLIENT_CONN: 500
      DEFAULT_POOL_SIZE: 50
      RESERVE_POOL_SIZE: 10
      RESERVE_POOL_TIMEOUT: 3
    ports:
      - "5432:5432"
```

### Sharding Strategy

For >500 labs or >5000 tps write throughput:

| Shard | Lab ID Range | Server |
|-------|-------------|--------|
| Shard 0 | lab_id 0-199 | postgres-shard-0 |
| Shard 1 | lab_id 200-399 | postgres-shard-1 |
| Shard 2 | lab_id 400-599 | postgres-shard-2 |
| Shard 3 | lab_id 600+ | postgres-shard-3 |

Sharding is implemented at the application layer via a routing service in `backend/app/services/sharding/`.

---

## 5. Cache Scaling

### Redis Sentinel (up to 10 GB)

```yaml
# docker-compose.redis-scale.yml
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_master_data:/data

  redis-replica-1:
    image: redis:7-alpine
    command: redis-server --appendonly yes --replicaof redis-master 6379 --requirepass ${REDIS_PASSWORD} --masterauth ${REDIS_PASSWORD}
    depends_on:
      - redis-master

  redis-replica-2:
    image: redis:7-alpine
    command: redis-server --appendonly yes --replicaof redis-master 6379 --requirepass ${REDIS_PASSWORD} --masterauth ${REDIS_PASSWORD}
    depends_on:
      - redis-master

  redis-sentinel-1:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    volumes:
      - ./config/redis/sentinel-1.conf:/etc/redis/sentinel.conf

  redis-sentinel-2:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    volumes:
      - ./config/redis/sentinel-2.conf:/etc/redis/sentinel.conf

  redis-sentinel-3:
    image: redis:7-alpine
    command: redis-sentinel /etc/redis/sentinel.conf
    volumes:
      - ./config/redis/sentinel-3.conf:/etc/redis/sentinel.conf
```

### Redis Cluster (>10 GB)

```yaml
# docker-compose.redis-cluster.yml
services:
  redis-cluster-1:
    image: redis:7-alpine
    command: redis-cluster --cluster create redis-cluster-1:6379 redis-cluster-2:6379 redis-cluster-3:6379 redis-cluster-4:6379 redis-cluster-5:6379 redis-cluster-6:6379 --cluster-replicas 1
    network_mode: host
```

### Memory Optimization

```ini
# Redis configuration for cache
maxmemory 4gb
maxmemory-policy allkeys-lru
maxmemory-samples 10
lfu-log-factor 10
lfu-decay-time 1
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
```

---

## 6. Queue Scaling (RabbitMQ)

### Cluster Configuration

```yaml
# docker-compose.rabbitmq-cluster.yml
services:
  rabbitmq-1:
    image: rabbitmq:3.12-management-alpine
    hostname: rabbitmq-1
    environment:
      RABBITMQ_ERLANG_COOKIE: ${RABBITMQ_COOKIE}
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq_1_data:/var/lib/rabbitmq

  rabbitmq-2:
    image: rabbitmq:3.12-management-alpine
    hostname: rabbitmq-2
    environment:
      RABBITMQ_ERLANG_COOKIE: ${RABBITMQ_COOKIE}
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq_2_data:/var/lib/rabbitmq
    command: >
      bash -c "sleep 30
      && rabbitmq-server -detached
      && rabbitmqctl stop_app
      && rabbitmqctl join_cluster rabbit@rabbitmq-1
      && rabbitmqctl start_app"

  rabbitmq-3:
    image: rabbitmq:3.12-management-alpine
    hostname: rabbitmq-3
    environment:
      RABBITMQ_ERLANG_COOKIE: ${RABBITMQ_COOKIE}
      RABBITMQ_DEFAULT_USER: ${RABBITMQ_USER}
      RABBITMQ_DEFAULT_PASS: ${RABBITMQ_PASSWORD}
    volumes:
      - rabbitmq_3_data:/var/lib/rabbitmq
    command: >
      bash -c "sleep 35
      && rabbitmq-server -detached
      && rabbitmqctl stop_app
      && rabbitmqctl join_cluster rabbit@rabbitmq-1
      && rabbitmqctl start_app"
```

### Mirrored Queue Policy

```bash
# Set HA policy for mirrored queues
rabbitmqctl set_policy ha-all ".*" '{"ha-mode":"all","ha-sync-mode":"automatic"}'
```

---

## 7. Storage Scaling (MinIO)

### Distributed MinIO

```yaml
# docker-compose.minio-distributed.yml
services:
  minio-1:
    image: minio/minio:latest
    command: server --console-address ":9001" http://minio-{1...4}/data
    volumes:
      - minio_1_data:/data
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
    ports:
      - "9000:9000"

  minio-2:
    image: minio/minio:latest
    command: server --console-address ":9001" http://minio-{1...4}/data
    volumes:
      - minio_2_data:/data
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}

  minio-3:
    image: minio/minio:latest
    command: server --console-address ":9001" http://minio-{1...4}/data
    volumes:
      - minio_3_data:/data
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}

  minio-4:
    image: minio/minio:latest
    command: server --console-address ":9001" http://minio-{1...4}/data
    volumes:
      - minio_4_data:/data
    environment:
      MINIO_ROOT_USER: ${MINIO_USER}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD}
```

### Erasure Coding Configuration

| Nodes | Parity | Usable % | Failure Tolerance |
|-------|--------|----------|-------------------|
| 4 (2:2) | 2 | 50% | 2 nodes |
| 6 (4:2) | 2 | 66% | 2 nodes |
| 8 (6:2) | 2 | 75% | 2 nodes |
| 12 (8:4) | 4 | 66% | 4 nodes |
| 16 (10:6) | 6 | 62.5% | 6 nodes |

---

## 8. Cost Analysis

### Monthly Cost by Tier

#### SMB Tier (1-10 labs)

| Component | Configuration | Monthly Cost |
|-----------|--------------|-------------|
| VMs | 1 × 4 vCPU, 8 GB RAM | $100-200 |
| Storage | 100 GB SSD | $20-40 |
| Database | PostgreSQL single node | Included in VM |
| Cache | Redis single node | Included in VM |
| Backup | 200 GB object storage | $10-20 |
| Monitoring | Prometheus/Grafana (self-hosted) | $0 |
| CDN/WAF | Cloudflare Pro | $20 |
| TLS | Let's Encrypt (free) | $0 |
| **Total** | | **$150-280** |

#### Growth Tier (10-100 labs)

| Component | Configuration | Monthly Cost |
|-----------|--------------|-------------|
| VMs | 3 × 8 vCPU, 16 GB RAM | $600-1,200 |
| Storage | 3 × 200 GB SSD | $90-180 |
| Database | PostgreSQL with Patroni (3 nodes) | Included in VMs |
| Cache | Redis Sentinel (3 nodes) | Included in VMs |
| Queue | RabbitMQ (3 nodes) | Included in VMs |
| Object Storage | MinIO (4 nodes) | Included in VMs |
| Backup | 500 GB object storage | $25-50 |
| Monitoring | Grafana Cloud (free tier) | $0 |
| CDN/WAF | Cloudflare Business | $200 |
| TLS | Let's Encrypt (free) | $0 |
| DNS | Cloudflare (included) | $0 |
| **Total** | | **$915-1,630** |

#### Enterprise Tier (100-500 labs)

| Component | Configuration | Monthly Cost |
|-----------|--------------|-------------|
| VMs | 6 × 16 vCPU, 32 GB RAM | $2,400-4,800 |
| Storage | 6 × 500 GB NVMe | $600-1,200 |
| Database | Patroni + PgBouncer (3+ nodes) | Included in VMs |
| Cache | Redis Cluster (6 nodes) | Included in VMs |
| Queue | RabbitMQ Cluster (3 nodes) | Included in VMs |
| Object Storage | MinIO Distributed (8 nodes) | Included in VMs |
| Backup | 2 TB object storage | $100-200 |
| Monitoring | Grafana Cloud Pro | $100 |
| CDN/WAF | Cloudflare Enterprise | $1,500 |
| SIEM | Self-hosted Wazuh | $0 |
| **Total** | | **$4,700-7,800** |

#### National Tier (500+ labs)

| Component | Configuration | Monthly Cost |
|-----------|--------------|-------------|
| VMs | 12+ × 32 vCPU, 64 GB RAM | $9,600-19,200 |
| Storage | 12+ × 1 TB NVMe | $3,600-7,200 |
| Database | Sharded PostgreSQL (4+ shards) | Included in VMs |
| Cache | Redis Cluster (12+ nodes) | Included in VMs |
| Queue | RabbitMQ Cluster (5+ nodes) | Included in VMs |
| Object Storage | MinIO Distributed (16 nodes) | Included in VMs |
| Backup | 5 TB object storage + DR | $500-1,000 |
| DR Region | 50% of primary resources | $4,800-9,600 |
| Monitoring | Grafana Cloud Advanced | $500 |
| CDN/WAF | Cloudflare Enterprise | $3,000 |
| SIEM | Self-hosted Wazuh + SOC | $2,000-5,000 |
| **Total** | | **$24,000-45,500** |

### Scaling Cost per 100 req/s

| Method | Cost Increase | Time to Implement | Complexity |
|--------|--------------|-------------------|------------|
| Add backend replica | +$100-200/month | 5 minutes | Low |
| Increase CPU/memory | +$50-150/month | 5 minutes | Low |
| Add DB read replica | +$200-400/month | 30 minutes | Medium |
| Add cache node | +$100-200/month | 15 minutes | Medium |
| Add queue node | +$100-200/month | 15 minutes | Medium |
| Full DB sharding | +$500-2,000/month | 1-2 weeks | High |

---

## 9. Scaling Playbooks

### Playbook: Traffic Spike

```bash
# 1. Add backend replicas
docker compose up -d --scale gula-backend=10 --no-deps gula-backend

# 2. Increase connection pool
# Set in .env:
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
docker compose up -d --no-deps gula-backend

# 3. Scale read replicas if DB is bottleneck
docker compose up -d --scale postgres-replica=3

# 4. Enable rate limiting (if needed)
curl -X POST https://api.gula.health/admin/rate-limit \
  -H "Authorization: Bearer $GULA_ADMIN_TOKEN" \
  -d '{"mode": "strict", "limit": 100}'
```

### Playbook: Storage Growth

```bash
# 1. Add MinIO nodes
docker compose up -d --scale minio=8

# 2. Increase retention period settings
# Set in .env:
REPORT_RETENTION_DAYS=60
BACKUP_RETENTION_DAYS=120

# 3. Archive old data
./scripts/archive-old-data.sh --before "2026-01-01"
```

### Playbook: Queue Backlog

```bash
# 1. Inspect queue depth
rabbitmqctl list_queues name messages consumers

# 2. Add consumers via worker scaling
docker compose up -d --scale gula-worker=5

# 3. Increase prefetch if workers are fast
rabbitmqctl set_parameter -p gula default-prefetch 50

# 4. If persistent backlog, purge old messages
rabbitmqctl purge_queue gula.events
```
