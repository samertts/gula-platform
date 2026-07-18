# PI-004: National Deployment, Operations & Resilience Platform

## Infrastructure Guide

**Version:** 1.0.0
**App Version:** 2.1.0
**Date:** 2026-07-16

---

### 1. PostgreSQL HA (Patroni)

#### 1.1 Architecture

Production PostgreSQL uses Patroni with Spilo 3.0-p1 (`helm/gula-platform/values.yaml:292-296`):

- **Primary:** 1 instance (read/write)
- **Replicas:** 2 instances (read-only, failover candidates)
- **DCS:** etcd (recommended) or Consul for leader election
- **Replication:** Synchronous streaming replication
- **Watchdog:** Automatic, prevents split-brain (`patroni.yml:212-215`)

#### 1.2 Patroni Configuration (`config/postgres-ha/patroni.yml`)

Key parameters:

```yaml
# PostgreSQL
max_connections: 200
shared_buffers: 512MB
effective_cache_size: 1536MB
work_mem: 16MB
maintenance_work_mem: 128MB
wal_level: replica
synchronous_commit: on
synchronous_standby_names: '*'

# Archiving (pgBackRest)
archive_mode: on
archive_command: "pgbackrest --stanza=gula archive-push %p"
archive_timeout: 60

# Patroni
ttl: 30
loop_wait: 10
retry_timeout: 10
maximum_lag_on_failover: 1048576
```

#### 1.3 Failover Script (`config/postgres-ha/failover.sh`)

Automated failover discovers Patroni members, evaluates candidates by lag, triggers failover via Patroni REST API, verifies new leader, updates service registry (Consul), and sends webhook alert.

```bash
./config/postgres-ha/failover.sh          # Execute failover
DRY_RUN=true ./config/postgres-ha/failover.sh  # Dry run
```

#### 1.4 Read Replicas (`config/postgres-ha/read-replicas.sh`)

```bash
./config/postgres-ha/read-replicas.sh     # Manage read replicas
```

#### 1.5 Connection Pooling

**PgBouncer** (`docker-compose.full.yml:83-106`):

```yaml
pgbouncer:
  image: edoburu/pgbouncer:1.22.1
  environment:
    POOL_MODE: transaction
    MAX_CLIENT_CONN: 1000
    DEFAULT_POOL_SIZE: 50
    MIN_POOL_SIZE: 10
    RESERVE_POOL_SIZE: 5
```

#### 1.6 Helm Chart Configuration

From `helm/gula-platform/values.yaml:283-379`:

```yaml
postgres:
  patroni:
    enabled: true
    image: registry.opensource.zalan.do/acid/spilo:3.0-p1
    pgParameters:
      max_connections: "200"
      shared_buffers: "256MB"
      wal_level: replica
  primary:
    replicaCount: 1
    resources:
      limits:
        memory: "2Gi"
        cpu: "2000m"
  replica:
    enabled: true
    replicaCount: 2
  storage:
    size: 50Gi
  backup:
    enabled: true
    schedule: "0 2 * * *"
    retentionDays: 30
    pgbackrest:
      enabled: true
```

---

### 2. Redis Cluster / Sentinel

#### 2.1 Sentinel HA (`config/redis-sentinel/`)

From `docker-compose.yml:51-78` and `docker-compose.full.yml:108-184`:

```yaml
# Redis Primary
redis:
  command: >
    redis-server --appendonly yes --maxmemory 256mb
    --maxmemory-policy volatile-lru
    --requirepass ${REDIS_PASSWORD}

# Redis Replica
redis-replica:
  command: >
    redis-server --appendonly yes --replicaof redis 6379
    --replica-read-only yes

# Redis Sentinel
redis-sentinel:
  command: >
    sh -c "echo 'sentinel monitor gula-redis redis 6379 1
    sentinel down-after-milliseconds gula-redis 5000
    sentinel failover-timeout gula-redis 10000
    sentinel parallel-syncs gula-redis 1' > /tmp/sentinel.conf
    && redis-sentinel /tmp/sentinel.conf"
```

Sentinel configuration file: `config/redis-sentinel/sentinel.conf`
Docker Compose HA: `config/redis-sentinel/docker-compose.redis-ha.yml`

#### 2.2 Redis Cluster Mode (`config/redis-cluster/redis-cluster.conf`)

Available for sharded deployments with 6+ nodes. Disabled by default in Helm (`values.yaml:401`):

```yaml
redis:
  cluster:
    enabled: false
    replicaCount: 6
```

#### 2.3 Helm Configuration (`values.yaml:381-431`)

```yaml
redis:
  sentinel:
    enabled: true
    replicaCount: 3
    quorum: 2
  config:
    maxmemory: "256mb"
    maxmemoryPolicy: volatile-lru
    appendonly: "yes"
  storage:
    size: 10Gi
```

#### 2.4 Standalone Redis Config (`config/redis/redis.conf`)

Standalone configuration for non-clustered deployments.

---

### 3. RabbitMQ Cluster

#### 3.1 Architecture

From `helm/gula-platform/values.yaml:433-499`:

```yaml
rabbitmq:
  cluster:
    enabled: true
    replicaCount: 3
  config:
    vmMemoryHighWatermark: 0.4
    diskFreeLimit: 1.0
    managementPort: 15672
    amqpPort: 5672
  storage:
    size: 10Gi
  resources:
    limits:
      memory: "2Gi"
      cpu: "2000m"
```

#### 3.2 Queues

Six queues defined in `values.yaml:450-468`:

| Queue | TTL | Purpose |
|-------|-----|---------|
| `orders.events` | 24h | Order status changes |
| `samples.events` | 24h | Sample lifecycle events |
| `results.events` | 24h | Result publication |
| `alerts.events` | 24h | Alert notifications |
| `audit.events` | 7d | Audit log events |
| `retry.queue` | 1h | Failed message retry |

#### 3.3 HA Configuration (`config/rabbitmq-cluster/`)

- RabbitMQ config: `rabbitmq.conf`
- Definitions: `definitions.json`
- Docker Compose HA: `docker-compose.rabbitmq-ha.yml`

#### 3.4 Standalone Config (`config/rabbitmq/`)

For non-clustered deployments.

---

### 4. MinIO HA Object Storage

#### 4.1 Architecture

From `helm/gula-platform/values.yaml:501-538`:

```yaml
minio:
  mode: distributed
  replicaCount: 4
  drivesPerNode: 1
  storage:
    size: 100Gi
  resources:
    limits:
      memory: "1Gi"
      cpu: "1000m"
```

#### 4.2 Buckets

```yaml
buckets:
  - name: lab-results
    policy: private
  - name: audit-logs
    policy: private
  - name: patient-documents
    policy: private
```

#### 4.3 HA Configuration (`config/minio-ha/`)

- **MinIO config:** `minio-config.json`
- **Nginx proxy:** `nginx-minio.conf` (load balancing for MinIO nodes)
- **Replication rules:** `replication-rules.json`
- **Docker Compose HA:** `docker-compose.minio-ha.yml`

#### 4.4 Single-Node Dev (`docker-compose.full.yml:344-366`)

```yaml
minio:
  image: minio/minio:RELEASE.2024-01-18T22-51-28Z
  command: server /data --console-address ":9002"
```

---

### 5. Service Mesh (Linkerd)

#### 5.1 Architecture

Linkerd service mesh provides:
- mTLS for all service-to-service communication
- Zero-trust AuthorizationPolicy
- Traffic splitting (blue/green, canary)
- Service profiles with retry budgets
- Metrics visualization via Linkerd Viz

#### 5.2 Mesh Configuration (`k8s/base/mesh/linkerd.yaml`, `helm/gula-platform/values.yaml:758-811`)

```yaml
serviceMesh:
  linkerd:
    enabled: true
    autoInject: enabled
    serviceProfile:
      enabled: true
      routes:
        - name: "GET /health"
          isRetryable: true
          timeout: 3s
        - name: "POST /api/results"
          isRetryable: false
          timeout: 60s
```

#### 5.3 mTLS Authorization

Linkerd authorization policies at `config/zero-trust/linkerd-policy.yaml`:

- Default deny-all at namespace level
- Per-service AuthorizationPolicy with authenticated identity requirements
- Database layer: only backend + worker can connect to PostgreSQL, Redis, RabbitMQ
- Mesh-wide mTLS enforcement with 24h certificate rotation

```yaml
apiVersion: policy.linkerd.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: default-deny-all
spec:
  requiredAuthentication:
    identities:
      - "*.serviceaccount.identity.linkerd.cluster.local"
```

#### 5.4 Topology Spread Constraints

All stateful workloads use topology spread constraints (`values.yaml:61-67`):

```yaml
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: DoNotSchedule
```

---

### 6. Secrets Management (Vault)

#### 6.1 Vault Configuration (`config/vault/`)

Production configuration at `config/vault/vault-prod.hcl`:

```hcl
listener "tcp" {
  address     = "0.0.0.0:8200"
  tls_disable = 0
  tls_cert_file = "/vault/certs/vault.crt"
  tls_key_file  = "/vault/certs/vault.key"
}

storage "file" {
  path = "/vault/data"
}

# Auto-unseal via Transit (KMS preferred for production)
# seal "awskms" { region = "me-south-1" kms_key_id = "alias/gula-vault-unseal" }
```

#### 6.2 Dev Mode (`docker-compose.full.yml:412-438`)

```yaml
vault:
  image: hashicorp/vault:1.15
  command: vault server -dev -dev-root-token-id=${VAULT_TOKEN}
  cap_add:
    - IPC_LOCK
```

#### 6.3 Helm External Secrets (`values.yaml:1296-1324`)

```yaml
secrets:
  name: gula-secrets
  annotations:
    secret-management: external-vault
  keys:
    - POSTGRES_PASSWORD
    - REDIS_PASSWORD
    - SECRET_KEY
    - ENCRYPTION_KEY
    - NID_HMAC_KEY
    - DEVICE_HMAC_KEY
    - REFRESH_TOKEN_SECRET
    - RABBITMQ_USER
    - RABBITMQ_PASS
    - MINIO_ACCESS_KEY
    - MINIO_SECRET_KEY
    - FCM_SERVER_KEY
    - SENTRY_DSN
  externalSecret:
    enabled: false
    provider: vault
    vault:
      path: secret/gula-platform
      role: gula-platform
```

#### 6.4 Secret Rotation (`scripts/rotate-secrets.sh`, `scripts/rotate-keys.sh`)

```bash
./scripts/rotate-secrets.sh     # Rotate all platform secrets
./scripts/rotate-keys.sh        # Rotate encryption keys
./scripts/setup-secrets.sh      # Initial secret setup
```

---

### 7. Certificate Management

#### 7.1 Cert-Manager (`config/cert-manager/`)

**ClusterIssuer** (`cluster-issuer.yaml`):

- Production: Let's Encrypt ACME `https://acme-v02.api.letsencrypt.org/directory`
- Staging: `https://acme-staging-v02.api.letsencrypt.org/directory`
- DNS01 challenge via Cloudflare API (`.`gula.health`)
- HTTP01 challenge via nginx ingress

**Certificate Template** (`certificate-template.yaml`):

```yaml
certificate:
  commonName: "*.gula.health"
  dnsNames:
    - "*.gula.health"
    - "gula.health"
    - "*.api.gula.health"
    - "*.admin.gula.health"
    - "*.app.gula.health"
  duration: 2160h   # 90 days
  renewBefore: 720h # 30 days before expiry
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
```

#### 7.2 Certificate Renewal

```bash
./scripts/cert-renew.sh          # Automated renewal
kubectl apply -f config/cert-manager/certificate-template.yaml
```

#### 7.3 SSL Configuration

Host nginx SSL at `config/nginx/system/gula-platform-ssl.conf`.

---

### 8. System Tuning

#### 8.1 sysctl (`config/system/99-gula-sysctl.conf`)

```conf
# Network tuning
net.core.somaxconn = 65535
net.ipv4.tcp_max_syn_backlog = 65535
net.ipv4.ip_local_port_range = 1024 65535

# Connection tracking
net.netfilter.nf_conntrack_max = 262144
net.netfilter.nf_conntrack_tcp_timeout_time_wait = 30
```

#### 8.2 Limits (`config/system/gula-limits.conf`)

```conf
gula    soft    nofile    65535
gula    hard    nofile    65535
gula    soft    nproc     32768
gula    hard    nproc     32768
```

#### 8.3 PostgreSQL Tuning (`config/postgres/postgresql.conf`)

Production settings for PostgreSQL 16 on 4GB RAM budget:
- `shared_buffers`: 512MB
- `effective_cache_size`: 1536MB
- `work_mem`: 16MB
- `maintenance_work_mem`: 128MB
- `max_connections`: 200
- `wal_level`: replica

---

**References:** `config/postgres-ha/`, `config/redis-sentinel/`, `config/redis-cluster/`, `config/rabbitmq-cluster/`, `config/minio-ha/`, `config/vault/`, `config/cert-manager/`, `config/system/`, `config/postgres/`, `config/zero-trust/`, `k8s/base/mesh/linkerd.yaml`
