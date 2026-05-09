# Phase 25-05 — Ecosystem Survivability

## Survivability Goals

- An ecosystem failure does not affect clinical operation.
- A misbehaving vendor is contained.
- Recovery from an ecosystem-wide event is orderly.

## Containment Patterns

- Per-vendor circuit breaker (Phase 16) — a flaky vendor doesn't propagate.
- Per-vendor bulkhead — vendor concurrency is isolated.
- Per-vendor rate limit — runaway vendor capped.
- Per-vendor credential — compromise contained to one vendor.

## Ecosystem-Wide Events

If a class of vendors degrades simultaneously (e.g., a shared cloud
outage on their side):

- Each vendor's circuit opens independently.
- Clinical workflows continue.
- Inbound integrations queue at the vendor's side; we don't accumulate
  internal state.
- Outbound queues drain on recovery.

## Sandbox Isolation

Sandbox tenants run on the same code base but on segregated tenant ids
and (recommended) segregated DB schemas / databases.

A sandbox failure CANNOT affect a production tenant. Verified via:

- different `lab_id` namespace
- segregated credentials
- DB-level separation in production deployment topology

## Patient-App Survivability

If a patient app degrades:

- Patient cannot receive results through that app.
- Lab and clinician workflows unaffected.
- Patient gets fallback delivery (per facility policy: SMS, paper).

## Research-Consortium Survivability

If an aggregator goes offline:

- The export pipeline buffers; no in-clinical-flight effect.
- Aggregator re-pulls when it returns.

## Operational Tooling Survivability

If a monitoring vendor degrades:

- Internal monitoring (`make health-deep`, prometheus) takes over.
- The vendor's recovery is independent.

## Ecosystem Recovery Discipline

After a multi-vendor incident:

- Per-vendor recovery audit.
- Affected vendors recertified before full traffic restore.
- Lessons-learned feed Phase 25 governance review.

## Limitations

- This phase does NOT solve the "national patient app marketplace"
  scaling problem; that's an institutional concern.
- This phase does NOT promise vendor-side resilience; vendor SLAs are
  contractual.

## Verification

- Annual: vendor-failure drill (synthetic vendor down).
- Quarterly: vendor traffic + capability creep review.
- Continuous: alerting on vendor circuit-open events.
