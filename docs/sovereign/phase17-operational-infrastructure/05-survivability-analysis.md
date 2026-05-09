# Phase 17-05 — Operational Survivability & Blast-Radius Analysis

## Goals

- Identify single-points-of-failure.
- Quantify blast radius per failure class.
- Confirm graceful-degradation behavior is not catastrophic.
- Confirm partial-offline survivability covers expected national scenarios.

## Component Blast Radius

| Component | Failure mode | Blast radius | Acceptable? |
|-----------|--------------|--------------|-------------|
| `gula-backend` (single replica) | Crash | Region partial outage; api-gateway routes to remaining replicas | Yes — replicas required |
| api-gateway | Crash | Region full read/write outage | Mitigated by host nginx fallback to maintenance page |
| PostgreSQL primary | Crash | Region writes paused; reads continue from replica | Yes — DR cutover process available |
| PostgreSQL replica | Crash | DR readiness reduced; primary unaffected | Yes — replica rebuild operational |
| Redis | Crash | Cache miss penalty; rate limits soften; no audit loss (audit not Redis-dependent) | Yes |
| Adapter (per peer) | Crash / circuit open | Only that adapter affected | Yes — design intent |
| Edge agent | Offline | Province operates in degraded mode (Phase 23) | Yes — designed |
| Audit chain verifier | Crash | Detection delayed; chain still emitted | Yes — operational alert raised |
| Notifications | Crash | Critical-result delivery via fallback (paper / phone) | Yes — Phase 23 fallback |

## Cascade Patterns to Prevent

### CP-1 — Adapter back-pressure → clinical write delay

Mitigation: per-adapter bulkhead; clinical writes exempt from concurrency
shedding (existing `ConcurrencyLimitMiddleware` rule); adapter outbound runs
on a separate event loop pool.

### CP-2 — DB pool exhaustion → readiness flip

Mitigation: adaptive concurrency loop already halves `_MAX_CONCURRENT` on
slow DB; DegradedModeMiddleware only blocks writes (reads continue);
clinical writes preferred.

### CP-3 — Audit DB lag → write rejection

Mitigation: audit is colocated with primary clinical DB; if separated,
audit is the synchronous side; clinical writes wait on audit, never the
reverse.

### CP-4 — Migration failure → fleet split-brain

Mitigation: `system_ready=False` until migrations consistent; staged
rollout; per-tenant migration dashboard.

### CP-5 — Adapter authentication misconfig → mass rejection

Mitigation: capability check fails closed, audit logged; operations alerted
on a denial spike.

## Degradation Ladder

GULA's degradation ladder, from least to most severe:

1. GREEN — full operation
2. YELLOW — slow DB, slightly elevated latency, non-clinical writes only
   feature-flagged-off
3. RED — DB circuit open; reads continue from replica; clinical writes
   continue if replica is fresh enough; non-clinical writes blocked
4. CRISIS — central platform unreachable; provincial / edge mode (Phase 23)
5. PAPER — full fallback; results recorded on paper; later reconciled

The ladder is monotone: the system never silently steps **down** from RED to
GREEN; recovery requires explicit health restoration.

## Survivability Tests (existing + extensions)

- Existing: `make chaos`, `tests/chaos/`, `tests/test_stress.py`, integrity
  tests.
- Extensions for sovereign readiness:
  - **Tier-1→Tier-2 cutover chaos** — annual.
  - **Provincial 72h offline** — quarterly.
  - **Audit-chain corruption injection (in test environment only)** —
    annual.
  - **Adapter failure cascade** — quarterly.

These extensions live in test plans, not in the test code yet, until Phase
17 is given coding scope.

## Failure-Mode Decision Tree (summary)

```
[detection]
   |
   v
is the issue tenant-scoped?
   |        |
  yes       no
   |        |
   v        v
RB-04 ...   is the issue region-scoped?
            |          |
           yes         no
            |          |
            v          v
          RB-09       is the issue audit-chain?
                       |     |
                      yes    no
                       |     |
                       v     v
                     RB-05  classify by symptom (RB-01 .. RB-10)
```
