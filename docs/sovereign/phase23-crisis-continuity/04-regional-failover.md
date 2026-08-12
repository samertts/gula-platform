# Phase 23-04 — Regional Failover Assumptions

## Failover Triggers

- Primary site (Tier-1) unreachable beyond RTO.
- Primary site partial corruption with unclear blast radius.
- Cyber incident requiring isolation of Tier-1.

## Failover Modes

### Mode A — Tier-1 → Tier-2 cutover (RB-09)

- DNS swap; Tier-2 becomes primary.
- Audit chain merge per RB-09 protocol.
- Tier-1 quarantined for review.

### Mode B — Provincial isolation

- Province cut from central; province operates standalone.
- Outbound queue grows; replayed on reconnect.
- Patients in province unaffected; cross-tenant features paused.

### Mode C — Multi-region partial

- Region A serves regions A+B because B is down.
- Tenants in B return to read-only-from-replica state until B recovers.
- Writes paused for B's tenants if synchronous replication is lost.

## Tenant-Safety Discipline During Failover

- A failover MUST NOT cause cross-region tenant bleed (OS-2).
- A tenant in region B remains a tenant of region B even when served from
  region A.
- Audit rows preserve `lab_id` accurately regardless of which region wrote
  them.

## Audit Chain Continuity

Each failover protocol carries:

- chain hash before failover (recorded on Tier-1)
- chain hash continuity marker (recorded on Tier-2 first row)
- verification step before resuming writes

A chain mismatch halts the cutover — the failover is incomplete until
investigated.

## Edge Failover

Edge → central failover already covered in Phase 23-02 (COOP). Central →
edge "failover" is not a thing — central can only be replaced by Tier-2,
not by edges.

## Recovery from Failover

- Tier-1 brought back online after investigation.
- Tier-1 syncs forward from Tier-2.
- Promotion swap (Tier-2 demoted to standby; Tier-1 primary again) is a
  separate, scheduled operation — never automatic, never under pressure.
- All transitions audit-chained.

## Drill Cadence

- Annual full Tier-1 → Tier-2 cutover (Phase 17).
- Quarterly provincial-isolation drill.
- Annual multi-region partial drill (where multi-region applies).

## Cross-Border Failover

For sovereign deployments, **never cross border** in failover unless the
deployment policy explicitly allows it. Cross-border data residency is
honoured even in crisis.

## Handover

Each drill produces:

- handover summary (what cutover took)
- gaps identified
- timeline metrics (RTO actual vs target)
- post-drill audit-chain check

Drill reports feed the deployment checklist.
