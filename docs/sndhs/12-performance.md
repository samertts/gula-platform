# 12 — Performance Envelope

## 12.1 Load model

Reference unit: a national daily load of `N` clinical events. The
envelope is specified at three multipliers.

| Tier | Multiplier | Daily clinical events | Concurrent active sessions | Peak TPS (writes) | Peak event throughput |
|------|-----------|-----------------------|----------------------------|-------------------|----------------------|
| Baseline (1×) | 1× | 5 M | 25 k | 600 | 4 k events/s |
| Surge (10×) | 10× | 50 M | 250 k | 6 000 | 40 k events/s |
| Catastrophic (100×) | 100× | 500 M | 2.5 M | 60 000 (transient) | 400 k events/s peaks |

Mix at peak (proportions):

- 35% reads (clinical workspace, dashboards)
- 25% writes (vitals, results, notes)
- 15% events out (subscriptions)
- 10% policy/ABAC checks
- 10% triage/emergency
- 5% admin / non-clinical

The 100× tier is treated as transient (minutes to hours) — not a
sustained design point. The system MUST survive it without data loss
or audit chain breakage; it MAY operate in degraded mode (auto-shed
P3, throttle P2).

## 12.2 SLO matrix

Per route class, P99 / P999 latency budgets:

| Class | Examples | P99 | P999 | Availability |
|-------|----------|-----|------|--------------|
| P0 critical | dispatch, MCOM raise, critical declare | 1 200 ms | 2 000 ms | 99.999% |
| P1 urgent | triage, ED order, transfer custody | 800 ms | 1 800 ms | 99.99% |
| P1 streaming (ambulance vitals jitter) | vitals frame | 750 ms | 1 500 ms | 99.99% |
| P2 routine | clinic visit, follow-up, scheduling | 2 000 ms | 4 000 ms | 99.95% |
| P3 background | analytics, sampling | best-effort | — | 99.0% |

End-to-end critical path (`crit.dispatch.created` → ED reservation
held + first downstream subscriber): **P99 < 2 000 ms** at 1×, **P99
< 2 500 ms** at 10×, **P99 < 5 000 ms** at 100× (transient breach
acceptable, monitored).

Time-violation rate (request misses class budget): **< 2%** at all
sustained tiers (H2).

## 12.3 Resource allocation

### 12.3.1 Per-RSN budget (baseline 1×)

| Component | CPU | RAM | Storage |
|-----------|-----|-----|---------|
| App fleet (3 nodes × all services) | 96 cores | 768 GB | local NVMe scratch |
| PG cluster (3 nodes) | 96 cores | 1 536 GB | 30 TB NVMe usable |
| NATS cluster | 48 cores | 192 GB | 2 TB NVMe |
| Redis cluster | 48 cores | 192 GB | 2 TB NVMe |
| Audit archiver | 16 cores | 128 GB | 100 TB tape + 8 TB NVMe |
| Observability local | 32 cores | 128 GB | 16 TB SSD |

### 12.3.2 Reservation table (priority scheduler)

```
P0  → 30% of every pool, hard reservation (never queued)
P1  → 30%, soft reservation (preempts P3 first)
P2  → 30%, best within budget
P3  → 10%, first to be auto-degraded
```

Pool kinds: CPU shares, DB connection slots, NATS publish quota,
Redis ops quota, network egress bandwidth.

### 12.3.3 Concurrency limits

- Per-app instance: `MAX_CONCURRENT = 200` general, `MAX_CONCURRENT_P0
  = 50` reserved (counted separately).
- Per-DB instance: tuned so that `WEB_CONCURRENCY × pool_per_worker <
  0.6 × max_connections`.
- Adaptive halving on sustained DB read latency >300 ms (2 readings),
  restore on 3 fast (<150 ms). Critical-plane writes are exempt from
  shedding.

### 12.3.4 Auto-degrade ladder

Trigger conditions and corresponding shed steps (cumulative):

1. **Yellow** (CPU > 70% OR pool > 60%): pause non-clinical batch;
   throttle public projection stream to 50%.
2. **Orange** (CPU > 80% OR pool > 75% OR replication lag > 2 s):
   reject P3 with `BACKPRESSURE_SHED`; halve P2 concurrency; pause
   AI shadow runs.
3. **Red** (CPU > 90% OR pool > 90% OR P0 reservation breach):
   reject P2 with `BACKPRESSURE_SHED`; deepen P1 queues; preserve P0
   strictly; consider MCOM auto-advisory.

## 12.4 Hot-path optimisations

- Critical-plane services in Rust, no allocator on hot path
  (pre-allocated arenas), bounded queues, zero-copy encoding.
- ABAC pre-compiled to Cedar AOT artefacts; sub-millisecond evaluate.
- Decision-stabilizer in-memory state machine; durable log via outbox.
- Per-region read replicas for clinical reads; writes go to leader.
- HOT (heap-only-tuple) updates for high-churn fields; partial indexes
  on open states.
- Bloom filters for idempotency dedup; exact set fallback.
- Vitals stream stored as deltas; only stable observations promoted to
  `vital_sign_obs` rows.

## 12.5 Backpressure protocol

- Server emits `Retry-After` and `BACKPRESSURE_SHED` for shed
  responses. SDK retries with jitter, respects ceiling.
- Critical-plane callers (ambulance device-bridge) DO NOT back off —
  they reroute to a hot peer using the peer-list returned in the
  response header.
- Bus consumers signal lag back to producers via JetStream pull-based
  flow control; producers reduce non-essential traffic first.

## 12.6 Capacity planning

- Twice yearly load tests at 10× sustained for 4 hours.
- Quarterly chaos suite that exercises 100× transients (5-minute
  bursts) to validate auto-degrade.
- New region onboarding: model load against demographic data; size
  MSBC accordingly; deploy in shadow for 2 weeks before cutover.

## 12.7 Observability for SLOs

- `slo_event_total{class, outcome}` (good/bad).
- `slo_latency_seconds_bucket{class}`.
- Burn-rate alerts at multi-window (5 m fast, 1 h slow) to catch
  acute regressions without flapping.
- SLO error budgets per class; budget exhaustion freezes non-essential
  releases for that surface (controlled by the policy authority's
  release gate).

## 12.8 Performance regression gates in CI

- Microbench delta > 10% on critical-plane hot paths fails the gate.
- End-to-end synthetic golden-path latency P99 > MSBC target fails
  the gate.
- Memory regression > 15% fails the gate.
- Allocation count on critical-plane hot path > baseline fails the
  gate.

## 12.9 Targets summary (national, sustained)

| Property | Target |
|----------|--------|
| P99 critical path | < 2 000 ms (1×, 10×) |
| Time-violation rate | < 2% |
| Bypass rate | < 3% |
| RSN offline survivability | ≥ 72 h |
| Audit completeness | 100% of state-changing actions |
| Sync catch-up post-heal (green) | ≥ 50 k events/min/peer |
| Manual-merge SLA P0 | ≤ 30 min |
| Failover time (DB inside RSN) | ≤ 30 s |
| RTO full RSN rebuild | ≤ 4 h |
| RPO | ≤ 5 min |
