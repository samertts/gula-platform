# Phase 17-01 — DR / Failover Readiness

## Targets (proposed; ratify with operations chief)

| Class | Target |
|-------|-------|
| RPO (clinical critical results) | **0 minutes** — synchronous replication required |
| RPO (orders, samples, audit) | **≤ 5 minutes** |
| RPO (configuration, RBAC) | **≤ 1 hour** |
| RTO (single-tenant outage) | **≤ 15 minutes** |
| RTO (regional outage) | **≤ 60 minutes** |
| RTO (national failover) | **≤ 4 hours** with degraded mode |

## Topology Tiers

GULA's existing stack scales linearly with topology tiers. The interesting
work is *which* tier each component lives in.

### Tier 1 — Primary site

- Active: api-gateway, gula-backend (3+ replicas), postgres (primary), redis,
  nhop-platform, prometheus, grafana, alert webhooks
- Edge: provincial agents and lab device bridges connect via VPN / sovereign
  link to the api-gateway
- Backup: continuous WAL streaming to Tier-2

### Tier 2 — DR site

- Standby: postgres replica (synchronous for critical-write tables;
  asynchronous for analytics tables), redis replica, gula-backend warm pool
  (0 replicas during normal operation, scaled on cutover)
- Audit: full audit-chain replica with hash-chain verifier
- Backup: hourly snapshot offsite (Tier-3)

### Tier 3 — Cold archive

- Encrypted snapshots, retained per regulatory retention policy
- Sovereign KMS-managed keys
- No live application; pure storage

## Failover Modes

| Mode | Trigger | Behaviour |
|------|---------|-----------|
| **Tenant-degraded** | Single tenant DB shard unavailable | Tenant returns 503 from `ReadinessMiddleware`; other tenants unaffected |
| **Regional-degraded** | Primary site unreachable | Cutover to Tier-2; reads served from replica; writes paused for ≤ 60 s during DNS swap |
| **Crisis** | National connectivity loss | Edge-first operation per Phase 23; central platform may be offline |

## Audit Chain Continuity (OS-1)

The audit chain MUST remain continuous across failover. The chain merge
protocol is:

1. Tier-1 stops writing (it must; cutover requires fence).
2. Tier-2 reads its last replicated chain entry.
3. Tier-2 verifies the chain to that point (hash-chain verifier).
4. Tier-2 begins writing with a continuation marker `chain_continued_from=<hash>`.
5. On Tier-1 recovery, Tier-1 syncs forward from Tier-2 (Tier-2 becomes new
   primary, or read-only Tier-1 is promoted via reverse sync). Sync verifies
   chain hashes.
6. A `dr_failover_event` audit row documents the transition with operator
   identity, timestamps, and verification result.

## Rollback Safety

A rolled-back deployment MUST NOT:

- Re-process events the new version has acknowledged.
- Drop audit rows for the rollback window.
- Re-emit interop calls (idempotency keys protect peers).

Rollback procedure:

1. Pause writes (api-gateway returns 503).
2. Snapshot current state.
3. Roll back application image only (DB schema migrations are
   forward-compatible by policy — see CLAUDE.md migration rules).
4. Resume writes.
5. Reconcile interop dead-letter queue under human review.

## Required Drills

| Drill | Frequency | Pass criteria |
|-------|-----------|---------------|
| Backup restore on test cluster | Quarterly | Restored DB passes `make health-deep`; all tenants visible |
| Tier-1 → Tier-2 cutover | Annually | RTO target met; audit chain verified intact |
| Edge offline survivability | Quarterly | 72h offline, sync on reconnect with 0 conflict loss |
| Audit chain replay | Annually | Full year of chain re-verified |
| Crisis fallback comms | Annually | SMS/USSD fallback path delivers a critical-result notification |

## Pass / Fail Gates

A failed drill blocks the corresponding deployment readiness gate in
[`../NATIONAL_DEPLOYMENT_CHECKLIST.md`](../NATIONAL_DEPLOYMENT_CHECKLIST.md).
