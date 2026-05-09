# Phase 17-04 — Deployment Topology Guidance

## Topology Levels

GULA supports four topologies. Choose by deployment scale.

### A. Solo (development / pilot lab)

- 1 host
- Docker Compose (`docker-compose.yml`)
- Single backend, postgres, redis, api-gateway
- Pilot tenant, no DR

### B. Single-region production (small ministry / single province)

- 2+ hosts (or one orchestrator + workers)
- Backend replicas behind HAProxy (`docker-compose.scale.yml`)
- PostgreSQL with continuous WAL backup
- Redis with periodic snapshot
- Monitoring (`make monitoring`)
- Alerting webhook configured

### C. Two-region production (national pilot)

- Region A (primary), Region B (DR)
- Synchronous PostgreSQL replication for clinical-critical tables; async for
  analytics tables
- Redis with replicated config (data treated as cache; not authoritative)
- Audit-chain replica with verifier
- Edge agents per province

### D. National full topology

- 2+ datacenters (Tier-1 + Tier-2)
- 1+ cold archive site (Tier-3)
- N edge / provincial sites
- nhop-platform per regulatory requirement (citizen registry companion)
- Per-province firewall + adapter VPN endpoints

## Component Layout

```
                +-------------------+
                |  Public ingress   |
                |  (host nginx TLS) |
                +---------+---------+
                          |
                +---------v---------+
                |  api-gateway      |  (Docker nginx, 127.0.0.1:8080)
                +---------+---------+
                          |
              +-----------+-----------+
              |           |           |
       +------v---+ +-----v---+ +-----v---+
       | backend  | | backend | | backend |  (gunicorn + uvicorn)
       +----+-----+ +-----+---+ +----+----+
            |             |          |
            +------+------+----------+
                   |
       +-----------v-----------+
       |  postgres primary     |
       +-----------+-----------+
                   |
                   |  WAL stream
                   v
       +-----------+-----------+
       |  postgres replica     |  (Tier-2)
       +-----------------------+
```

Side cars (independent of clinical path):

```
edge_agent  -->  device_bridge  -->  api-gateway
nhop-platform  --(separate FastAPI on 8100)
prometheus + grafana  (internal only; SSH tunnel to reach)
```

## Network Boundaries

| Boundary | Required control |
|----------|------------------|
| Public → host nginx | TLS termination only |
| Host nginx → api-gateway | local socket / 127.0.0.1 |
| api-gateway → backend | internal Docker network |
| Backend → DB | internal Docker network only; no public exposure |
| Backend → Redis | internal only |
| Backend → adapter peers | dedicated egress IP per environment |
| Edge → core | mTLS over VPN |

## Configuration Discipline

- All deployments use the same image tag for backend/microservices in a
  rollout cycle.
- Per-environment secrets are sovereign-KMS-backed in production (consult
  `digitalocean/` or `k8s/` overlays for the relevant deployment).
- `.env.production` documents variable shape; never holds secret values.

## Edge / Provincial Sites

Each provincial site runs:

- `gula-backend` (1 replica, smaller image)
- local PostgreSQL (acts as authoritative for the province during partial
  outages — see Phase 23)
- local Redis (cache)
- `services/device_bridge/` — instrument adapter
- VPN client to central gateway

The province is its own bounded trust domain (Phase 16). It is **not** a
sub-tenant of central; it is a peer.

## Sovereign Hosting Considerations

When deploying on sovereign cloud or government datacenter:

- Confirm data residency for backups and Tier-3 cold storage.
- Confirm KMS region affinity (no cross-border KMS calls).
- Confirm log destination residency (no cross-border log shipping).
- Confirm monitoring stack residency.

The platform code itself is residency-agnostic; the deployment overlay sets
residency.
