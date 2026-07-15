# ADR-015: Disaster Recovery Strategy

**Status:** Accepted
**Date:** 2026-07-15
**Deciders:** Engineering Lead, Platform Architect, CTO

---

## Context

The GULA platform serves Iraqi medical laboratories where data integrity and availability are critical for patient safety. A regional outage, natural disaster, or infrastructure failure could prevent laboratories from processing patient results.

**Requirements:**
- **RPO (Recovery Point Objective):** ≤ 5 seconds — virtually no data loss
- **RTO (Recovery Time Objective):** ≤ 5 minutes — rapid return to service
- **99.99% availability** across regions
- **Automated failover** where safe, manual where risk of split-brain
- **Data integrity verification** after any recovery
- **Compliance** with Iraqi health data regulations

**Constraints:**
- Primary data center must be in Middle East (Bahrain/Iraq) for data sovereignty
- DR region must be outside ME for geographic diversity (EU — Frankfurt)
- Synchronous replication across regions is impractical due to latency
- Budget limits 2-region active-active (too expensive for current scale)

## Decision

Implement an **active-passive multi-region DR strategy** with the following architecture:

### Architecture

```
┌──────────────────────┐        ┌──────────────────────┐
│   ME Region          │        │   EU Region          │
│   (Primary/Active)   │        │   (DR/Passive)       │
│                      │        │                      │
│  PostgreSQL Primary  │──WAL──►│  PostgreSQL DR       │
│                      │ stream │  (hot standby)       │
│  Redis Master        │──ASYNC─►│  Redis Replica       │
│                      │        │                      │
│  RabbitMQ Primary    │──SHOVEL►│  RabbitMQ Mirror     │
│                      │        │                      │
│  MinIO Primary       │──SYNC─►│  MinIO Replica       │
│                      │        │                      │
│  Backend (3 replicas)│        │  Backend (1 standby) │
│                      │        │                      │
│  Cloudflare Active   │        │  Cloudflare Passive  │
└──────────────────────┘        └──────────────────────┘
```

### Replication Strategy

| Component | Method | Sync Mode | RPO |
|-----------|--------|-----------|-----|
| PostgreSQL | Patroni streaming replication | Asynchronous (synchronous within region) | <5s |
| Redis | Standard async replication | Asynchronous | <1s |
| RabbitMQ | Shovel plugin | Asynchronous | <5s |
| MinIO | Bucket replication | Synchronous within region, async across | <10s |

### Failover Strategy

| Failure Scenario | Trigger | Action | Automation |
|-----------------|---------|--------|------------|
| Pod/container failure | Health check fails | K8s auto-restart | Fully automated |
| Node failure | Node heartbeat lost | Pod rescheduling | Fully automated |
| DB primary failure | Patroni detection | Replica promotion | Fully automated |
| Cache failure | Sentinel detection | Slave promotion | Fully automated |
| Queue failure | RabbitMQ detection | Mirror promotion | Fully automated |
| Storage failure | MinIO health check | Erasure coding rebuild | Fully automated |
| **Region failure** | Cloudflare health check | **Manual DNS change** | **Manual** |

**Why manual region failover?** Split-brain risk — if both regions think they are primary, data corruption is inevitable. The 15-minute RTO for full region failover is acceptable (only happens in extreme scenarios).

### Failover Process (Region Failure)

1. **Detect** — Cloudflare health checks fail on all ME endpoints (3 independent confirmations)
2. **Decide** — On-call confirms region is unreachable, Operations Lead authorizes failover
3. **Promote** — DR PostgreSQL promoted to primary (`pg_promote()`)
4. **Activate** — DR Redis made writable (`SLAVEOF NO ONE`), DR RabbitMQ reset
5. **Scale** — DR backend scaled from 1 standby to 3+ active replicas
6. **Switch** — Cloudflare DNS record updated to point to EU load balancer
7. **Verify** — Full health check, data integrity verification, write test
8. **Announce** — Stakeholder communication

**Target RTO:** 5 minutes (region failover from detection to traffic switch)

### Failback Process

1. **Fix** — Root cause of original failure resolved in ME region
2. **Sync** — ME region catches up as standby from EU
3. **Verify** — Data parity confirmed between regions
4. **Schedule** — Maintenance window announced
5. **Switch** — During maintenance, promote ME, redirect DNS
6. **Verify** — Full health check, data integrity verification

**Target RTO:** 15 minutes (failback, includes maintenance window planning)

## Alternatives Considered

### 1. Active-Active (Multi-Primary)

**Pros:** No failover needed, load balanced across regions, lower latency for distributed users.
**Cons:**
- **Conflict resolution complexity** — Concurrent writes to same patient record in different regions create conflicts
- **2x infrastructure cost** — Both regions must run at full capacity
- **Write latency** — Cross-region conflict resolution adds latency
- **Rejected because:** Complexity of conflict resolution for health data (where data integrity is paramount) is not worth the benefit.

### 2. Active-Passive with Automatic Failover

**Pros:** Faster RTO (fully automated), less human error risk.
**Cons:**
- **Split-brain risk** — If network partitions, both regions may think the other is down and both become primary
- **Auto-promotion safety** — Hard to guarantee no data corruption
- **Rejected because:** Risk of split-brain for health data outweighs the RTO improvement. Manual failover with verification is safer.

### 3. Backup-Restore Only (No DR Region)

**Pros:** Cheapest option, simplest.
**Cons:**
- **RPO** — At best 1 hour (hourly backups), at worst 24 hours
- **RTO** — Hours to restore from backup
- **Does not meet requirements** — 5 second RPO, 5 minute RTO
- **Rejected because:** Completely fails to meet business requirements.

### 4. Cloud Provider DR (AWS/Azure Cross-Region)

**Pros:** Managed infrastructure, simpler replication.
**Cons:**
- **Vendor lock-in** — Tied to specific cloud provider
- **Data sovereignty** — Health data must remain under our control
- **Cost at scale** — Egress fees for cross-region replication
- **Rejected because:** Self-managed gives us full data sovereignty and cloud-agnostic deployment.

## Consequences

### Positive
- **RPO ≤ 5s** — Near-zero data loss via WAL streaming
- **RTO ≤ 5min** — Fast recovery for region failure scenario
- **Data sovereignty** — Full control over where health data resides
- **Cloud-agnostic** — Can run in any region, any provider, or on-premise
- **Proven technology** — Patroni, Sentinel, RabbitMQ clusters are battle-tested

### Negative
- **+30% infrastructure cost** — DR region requires at least 50% of primary resources
- **Operational complexity** — Managing Patroni, cross-region replication, DNS failover
- **Manual region failover** — Requires trained on-call personnel to execute within 5 minutes
- **Cross-region latency** — WAL streaming from ME to EU may have 50-100ms latency

### Risks
- **Split-brain** — Manual region failover mitigates but doesn't eliminate risk. Network partition during failover could cause both regions to accept writes. Mitigated by: 3 independent health checks, explicit decision step, Patroni safeguards.
- **Replication lag** — Under heavy write load, async replication to EU may exceed 5s RPO. Mitigated by: monitoring replication lag, alerting at >5s, throttling writes if lag exceeds threshold.
- **Data corruption propagation** — A bad migration or data corruption on primary would replicate to DR. Mitigated by: delayed replica (1 hour behind) for point-in-time recovery, regular integrity checks.

## Testing Requirements

- **Quarterly full failover test** — Complete region failover and failback
- **Monthly Patroni failover test** — Database failover in staging
- **Weekly backup restore test** — Restore from backup to verify integrity
- **Chaos engineering** — Random component failures to test resilience

## References

- `docs/production/DISASTER_RECOVERY_GUIDE.md` — Complete DR procedures
- ADR-013: Production Platform Architecture
- ADR-005: PostgreSQL Redis Stack
- Patroni documentation: https://patroni.readthedocs.io
- PostgreSQL streaming replication: https://www.postgresql.org/docs/16/warm-standby.html
- Redis Sentinel: https://redis.io/docs/management/sentinel
- `scripts/dr_recovery.sh` — DR recovery automation
- `scripts/pg_failover.sh` — PostgreSQL failover script
