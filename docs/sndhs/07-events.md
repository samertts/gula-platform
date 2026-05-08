# 07 — Event-Driven Architecture

## 7.1 Bus topology

- **Per-RSN** NATS JetStream cluster (3 nodes, RAFT) — primary.
- **Per-region** mirror to NFT (async, signed envelope).
- **Public projection** stream: filtered + DLP'd; consumed by GULA,
  regulators, public-health analytics.
- **Audit** is on a dedicated cluster, isolated from clinical streams.

Subjects use a strict hierarchy: `<plane>.<domain>.<entity>.<event>.v<n>`,
e.g. `crit.dispatch.case.created.v1`, `clin.referral.lifecycle.scheduled.v1`,
`gov.policy.bundle.activated.v1`.

## 7.2 Event envelope

```json
{
  "id": "01J...",
  "specversion": "1.0",
  "type": "clin.referral.lifecycle.scheduled.v1",
  "source": "/rsn/BG/clinical/referral-engine",
  "time": "2026-05-05T12:34:56.789Z",
  "time_authority_id": "ta:rsn-bg",
  "time_quality": "TRUSTED",
  "monotonic_ns": 1714944896789012345,
  "datacontenttype": "application/json",
  "schema_version": 1,
  "stream_kind": "referral",
  "stream_id": "01HX...",
  "sequence": 14,
  "policy_version_id": "01J...",
  "decision_context_hash": "BLAKE3:...",
  "actor_principal": "p:clinician:LIC-12345",
  "attestation_id": "01J...",
  "correlation_id": "01J...",
  "causation_id": "01J...",
  "region_id": "BG",
  "source_rsn": "BG",
  "data": { ... },
  "signature": "ed25519:..."
}
```

Signatures: every event signed by the producing service identity
(SPIFFE) and counter-signed by the audit-ledger when it lands in the
chain. Events with invalid signatures land in `dead-letter-quarantine`
and trigger a P0 alert.

## 7.3 Domain catalogue (subset)

### Critical Plane

- `crit.dispatch.case.created.v1`
- `crit.dispatch.case.updated.v1`
- `crit.ambulance.unit.assigned.v1`
- `crit.ambulance.vitals.frame.v1` (rate-limited; persisted as deltas)
- `crit.encounter.critical_declared.v1`
- `crit.mcom.level_changed.v1`
- `crit.priority.reservation_taken.v1`
- `crit.priority.reservation_evicted.v1`

### Clinical Plane

- `clin.mpi.patient.registered.v1` / `merged.v1` / `legal_hold.v1`
- `clin.encounter.opened.v1` / `transitioned.v1` / `closed.v1`
- `clin.referral.lifecycle.<state>.v1`
- `clin.order.created.v1` / `dispatched.v1` / `completed.v1`
- `clin.result.recorded.v1` / `amended.v1`
- `clin.consent.given.v1` / `revoked.v1`

### Governance Plane

- `gov.policy.bundle.activated.v1`
- `gov.policy.bundle.rolled_back.v1`
- `gov.time.drift.detected.v1` / `recovered.v1`
- `gov.audit.checkpoint.signed.v1`
- `gov.ai.shadow.recorded.v1` / `gov.ai.drift.detected.v1` / `gov.ai.circuit.opened.v1`
- `gov.integrity.discrepancy.detected.v1`
- `gov.validation.sample.reviewed.v1`

### Operational

- `ops.healing.action.taken.v1`
- `ops.scaling.event.v1`
- `ops.degraded_mode.entered.v1` / `exited.v1`
- `ops.partition.started.v1` / `resolved.v1`
- `ops.kill_switch.toggled.v1`

## 7.4 Schemas & evolution

- Each event has a JSONSchema in the Contract Registry, signed.
- Backwards-compatible additions only on the same major version (`v1`).
- Breaking changes go through `v2` and a migration plan: producers
  emit both versions for a defined window; consumers migrate; old
  version is retired with a deprecation event.
- The SDK validates on publish and on subscribe. Strict mode for
  clinical events (`additionalProperties: false`).

## 7.5 Idempotency

- Producers MUST attach an `id` (ULID) and the consumer MUST dedup on
  it within a 24 h window (Redis bloom + exact set fallback).
- For commands (request/response wrapped over events), the
  `Idempotency-Key` is propagated as `id` of the resulting domain
  event.
- Outbox pattern is mandatory for any service that mutates a database
  and emits an event — the two writes share the same transaction; an
  outbox poller publishes; consumers ack.

## 7.6 Ordering

- **Per-stream order** is preserved (NATS JetStream stream + per
  `stream_kind:stream_id` consumer group + ordered consumer).
- Cross-stream order is **not** guaranteed; consumers that need
  ordering across streams must use causation/correlation IDs to sort.
- Critical-plane consumers operate on per-region partitions; ordering
  per `dispatch_case_id` is preserved.

## 7.7 Replay

- Every consumer has a durable cursor (`Last-Event-Id`).
- On restart it resumes from cursor; the SDK enforces idempotent
  application.
- **Backfill / replay** for read-model rebuilds:
  - Offline against a shadow database.
  - Speed: ≥ 50 k events/min/consumer (ordered) on warm hardware.
  - Cutover via dual-write window: project to old + new; flip read
    traffic; retire old.
- **Time-travel queries**: any read model can be rebuilt at a past
  point in time by replaying events with `recorded_at_ns ≤ T`.
- **Selective replay**: by `correlation_id` or `stream_id` for
  forensic investigation; access is itself audited.

## 7.8 Dead letter & quarantine

- `dlq.<original-subject>` — undeliverable after max retries.
- `quarantine.<original-subject>` — failed signature or contract
  validation.
- Both have on-call dashboards; an SLO is defined for clearing them
  (P0: 30 min, P1: 4 h, P2: 7 d).
- Replay from DLQ requires explicit human approval (audited).

## 7.9 Storage & retention of events

- Hot: 30 days in JetStream (per RSN), 90 days (NFT).
- Warm: PostgreSQL `domain_event` partitioned monthly per region; 7
  years.
- Cold: WORM archive; retention by retention class
  (`11-governance.md`).
- Audit events: 25 years minimum; legal hold extends.

## 7.10 Observability

- `event_publish_latency_seconds{stream}`
- `event_e2e_latency_seconds{stream, consumer}`
- `event_dedup_hit_total{stream, consumer}`
- `event_dlq_total{stream}`
- `event_quarantine_total{stream, reason}`
- `outbox_lag_events{service}`
- `consumer_lag_events{stream, consumer}`

Alerts:

- Consumer lag P0 > 5 s: page.
- DLQ growth rate > 0.5 events/s: page.
- Quarantine: any event triggers an alert (signature/contract
  violations are signals of compromise).

## 7.11 Security on the bus

- Subject ACLs derived from the policy bundle.
- Event-level encryption for confidentiality classes ≥ PHI-VIP — the
  payload is wrapped with a per-confidentiality DEK; only consumers
  whose policy permits PHI-VIP can unwrap.
- Public projection stream goes through DLP egress filter at the
  boundary mirror (NFT → external).

## 7.12 Operational rules

- A service MAY NOT consume from a subject outside its policy.
- A service MUST NOT mutate the bus directly; all writes go through
  the SDK.
- Orphan consumer groups (no progress for 7 days) are auto-archived
  with notification.
- Any new event type requires a Contract Registry PR with schema +
  example + retention class + ABAC scope; CI fails if the producer
  emits an unregistered type.
