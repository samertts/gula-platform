# 01 — System Architecture Specification

## 1.1 Top-level layering

```
┌──────────────────────────────────────────────────────────────────┐
│   Citizen / clinician / ambulance / lab / ministry actors       │
└───────▲──────────────────────────────────────────────▲───────────┘
        │                                              │
        │  (UI/UX only)                                │  (clinical UIs run inside SNDHS)
        ▼                                              ▼
┌────────────────────────────┐                ┌────────────────────────────┐
│   GULA platform (NCD)      │                │  SNDHS Clinical Workspace  │
│   non-clinical UI / svc /  │   ABAC GW      │  (sovereign UIs for ED,    │
│   integration              │ ─────────────► │   referral, OR, MCOM ops)  │
└─────────────▲──────────────┘                └─────────────▲──────────────┘
              │                                              │
              │ HTTPS + mTLS via Sovereign Gateway           │
              ▼                                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                      SNDHS Sovereign Gateway                     │
│   zero-trust ingress · ABAC · DLP · rate · policy binding        │
└──────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼────────────────────────────┐
        ▼                       ▼                            ▼
┌─────────────────┐   ┌────────────────────┐   ┌────────────────────────┐
│  Critical Plane │   │   Clinical Plane   │   │  Governance Plane      │
│  (P1 deterministic)│ │ (EMR/MPI/Order)    │   │ (Policy/Time/Audit/AI) │
└────────▲────────┘   └─────────▲──────────┘   └──────────▲─────────────┘
         │                      │                          │
         └──────────────────────┴──────────────────────────┘
                                │
                ┌───────────────┴────────────────┐
                ▼                                ▼
       ┌──────────────────┐            ┌──────────────────┐
       │ Regional Sovereign│           │ National Federation│
       │   Node (RSN)      │  ◄─────► │    Tier (NFT)       │
       │ autonomous, 72h   │  CRDT/   │ aggregates, MPI     │
       │ offline          │   GG-Sync │ resolves split-brain│
       └──────────────────┘            └──────────────────┘
```

Three planes, two tiers. Plane separation is enforced by network policy
(eBPF + Cilium L7 policies) and by separate signing roots — a Critical-Plane
JWT MUST NOT validate against the Clinical-Plane signing key.

## 1.2 Component breakdown

### 1.2.1 Critical Plane (P1 — deterministic real-time)

| Service | Purpose | Lang/runtime | Hard SLO |
|---------|---------|--------------|----------|
| `triage-engine` | ESI / MTS triage decisioning | Rust, no-alloc hot path | P99 < 80 ms |
| `emergency-router` | Ambulance / facility routing | Rust + OR-Tools binding | P99 < 250 ms |
| `dispatch-bridge` | Radio/dispatch protocol gateway | Rust | P99 < 150 ms |
| `mcom-controller` | MCOM 1–4 mode controller | Rust | P99 < 500 ms |
| `priority-scheduler` | Cross-service priority (PQ + reservation) | Rust | P99 < 5 ms scheduling |
| `decision-stabilizer` | Hysteresis + lock-window enforcement | Rust | P99 < 20 ms |
| `time-authority-agent` | Local monotonic clock + drift watchdog | Rust | P99 < 1 ms |

Critical Plane services have **no shared mutable state** with the Clinical
Plane. They publish events through a dedicated NATS JetStream cluster
(`crit.*`) and read snapshots from per-region read-only replicas of the
clinical store, never directly.

### 1.2.2 Clinical Plane (system of record)

| Service | Purpose | Lang/runtime | Notes |
|---------|---------|--------------|-------|
| `mpi` | Master Patient Index | Go | Probabilistic + deterministic match, ULID-based MPI ID |
| `emr-core` | FHIR R5 resources, CRUD + history | Go | All writes go through `policy-binder` |
| `referral-engine` | Closed-loop referral state machine | Go | Strict FSM, no skipping states |
| `encounter-orchestrator` | Critical-encounter lifecycle | Go | Coordinates ED→ward→OR→discharge |
| `order-engine` | Lab/imaging/medication orders | Go | Outbox-backed, idempotent |
| `result-engine` | Result intake (devices, labs, imaging) | Go | Validated against contract registry |
| `consent-service` | Patient consent ledger | Go | Append-only, granular |
| `notification-fabric` | Outbound to citizens/clinicians/ambulance | Go | Rate-limited per channel & priority |

### 1.2.3 Governance Plane

| Service | Purpose |
|---------|---------|
| `policy-authority` | Versioned policy store; signs every active policy bundle |
| `policy-binder` | Sidecar-injected lib that binds `policy_version_id` to every decision |
| `time-authority` | National stratum-1 NTP/PTP + signed time tokens |
| `audit-ledger` | Append-only hash-chained audit log (per-RSN + national mirror) |
| `ai-governance` | Shadow-mode runner, drift detector, AI circuit breaker |
| `clinical-governance` | Rule registry (ESI, sepsis bundle, stroke bundle, …) |
| `integrity-engine` | Reality-vs-system reconciliation, bypass detection |
| `validation-engine` | Sampling, clinical review queue, feedback injection |

### 1.2.4 Cross-cutting

- **Internal SDK (`sndhs-sdk`)** — single client lib in Rust+Go+TS bindings:
  auth, events, validation, error envelopes, retry policy, idempotency keys,
  policy binding, time stamping. Direct HTTP calls between services are
  forbidden — all calls go through the SDK.
- **Contract Registry (`contracts`)** — Avro+JSONSchema+FHIR profile registry.
  Every event and API request/response is validated at runtime by the SDK.
- **Service Mesh** — Cilium + SPIRE. mTLS everywhere. SPIFFE IDs identify
  services; ABAC uses both user and service attributes.

## 1.3 Data flow — canonical critical path (cardiac arrest, prehospital)

```
1. Bystander → 122 dispatcher → dispatch-bridge
2. dispatch-bridge.publish crit.dispatch.created (priority=P0)
3. emergency-router consumes → routes to nearest ambulance + ED
4. triage-engine pre-allocates ED bed (reservation token)
5. ambulance device-bridge streams vitals → result-engine (P1)
6. encounter-orchestrator opens encounter on ED arrival, binds
   policy_version_id of "ACLS-2025-Q1" to decision context
7. order-engine auto-creates standing orders per policy
8. audit-ledger receives every event; hash chain extended
9. mcom-controller observes regional ED occupancy; if > threshold
   triggers MCOM-2 advisory (no clinical effect, just resource posture)
10. notification-fabric notifies on-call cardiologist (priority queue)
```

Total budget: 2 s P99 from step 1 ingress to step 7 order persisted on the
RSN. Step 4 is bounded by the priority scheduler's reservation table.

## 1.4 Separation boundary — SNDHS vs GULA

| Concern | SNDHS | GULA |
|---------|-------|------|
| Patient identity (MPI) | Owns | Reads via opaque token |
| Clinical record | Owns | No read of raw clinical data; renders via signed render-bundles only |
| Triage / emergency decisions | Owns | Forbidden |
| Referral state machine | Owns | May display state, may submit transitions through gateway |
| Lab orders / results | Owns | May display; may submit on behalf of authorised user |
| Billing / scheduling | GULA owns | SNDHS exposes minimal hooks |
| Lab device integration (LabLink) | Bridge runs in GULA, but writes route through SNDHS Result Engine | — |
| UI for clinicians | Sovereign clinical workspace owns ED/OR/MCOM | GULA owns lab/citizen/admin |
| AI inference results | Owns (shadow-first) | Forbidden to surface to clinicians |

Enforcement: all GULA→SNDHS calls traverse the **Sovereign Gateway**, which
applies a deny-by-default ABAC policy. Each gateway route declares which
clinical attributes may flow back to GULA; everything else is stripped by a
DLP filter before egress (see `10-gula-integration.md`).

## 1.5 Middleware chain — Sovereign Gateway

Order is normative. Out-of-order deployment is a release blocker.

```
1.  Connection terminator (mTLS, SPIFFE ID validation)
2.  Body cap (configurable per route, default 1 MiB; emergency routes 256 KiB)
3.  Request-ID assignment + causal headers
4.  Time stamping (signed time token from time-authority)
5.  Authentication (OIDC + device attestation + WebAuthn for clinicians)
6.  Authorization (ABAC — see 06-security.md)
7.  Policy binder (attaches policy_version_id)
8.  Decision stabilizer (lock-window check)
9.  Rate limit (multi-key: principal, facility, route, plane)
10. DLP egress filter (response side; strips disallowed attributes)
11. Priority scheduler (admission control by route priority class)
12. Concurrency limiter (per-worker, exempt list = critical-plane routes)
13. Readiness/degraded-mode gate
14. Audit emit (request envelope only — body-hashes for clinical bodies)
15. Forward to upstream
```

Critical-plane routes (`/critical/*`) skip steps 9 (rate limit) and 12
(concurrency limiter) — they are governed instead by the priority-scheduler
reservation. They never skip 6, 7, 8, 14.

## 1.6 AI subsystem (strict shadow-first)

```
┌────────────────┐  inputs   ┌───────────────────┐
│ live decision  │──────────►│ ai-governance     │
│ point          │           │ (shadow runner)   │
└──────▲─────────┘           └────────┬──────────┘
       │                              │ writes shadow predictions
       │                              ▼
       │                     ┌───────────────────┐
       │   no surface        │ shadow_predictions│
       │ ◄───────────────── │  (audit only)     │
       │                     └────────┬──────────┘
       │                              │
       │                     ┌────────▼──────────┐
       │                     │ drift detector    │
       │                     │ + circuit breaker │
       │                     └────────┬──────────┘
       │                              │
       │              promotion gate (clinical board sign-off)
       └──────────────────────────────┘
```

- **Shadow mode** is mandatory. An AI model can be promoted to advisory only
  after ≥ 90 days of shadow with predefined performance gates and a signed
  Clinical Board attestation. Promotion to autonomous is forbidden by policy
  for any decision with `clinical_severity ≥ S2`.
- **Inputs/outputs/version are logged** via `ai-governance` to the audit
  ledger with the input feature hash, the model artefact hash (sha256 of the
  weights), the prompt template version, and the output.
- **Drift detection** runs on rolling 24 h windows comparing prediction
  distribution + input feature distribution against the calibration baseline.
  Detected drift > threshold opens the AI circuit (model marked offline; no
  further inferences, but logged shadows continue from a frozen snapshot).
- **Circuit breaker** — three independent signals (drift, latency anomaly,
  human-flagged regression). Two-of-three opens it.
- **Patient boundary** — no AI-derived field may leave SNDHS towards GULA or
  any client without `ai_advisory_promoted = true` on the active policy.

## 1.7 Decision stabilization (hysteresis & lock windows)

A decision (e.g., "discharge", "MCOM level", "triage acuity") may flip only
if either:

1. Sustained signal change for `T_hold` seconds AND the new state passes a
   higher threshold than the old (hysteresis), OR
2. A human override with appropriate role authorises the flip.

`decision-stabilizer` sits in front of any service that emits a decision
event. Each decision class has a `(threshold_up, threshold_down, T_hold,
T_lock, oscillation_window, oscillation_max_flips)` tuple in the policy
bundle. If `oscillation_max_flips` is exceeded inside `oscillation_window`,
the decision class is **frozen** and a human escalation is required.

State table:

| State | Entry | Allowed exit | Escalation |
|-------|-------|--------------|------------|
| `STABLE` | initial / after lock window | `EVALUATING` | none |
| `EVALUATING` | signal crosses upper threshold for < T_hold | `STABLE`, `LOCKED` | none |
| `LOCKED` | flip committed | after T_lock → `STABLE` | none |
| `OSCILLATING` | > N flips in window | only via human override → `STABLE` | mandatory |
| `FROZEN` | manual freeze | only via two-person rule | mandatory |

## 1.8 Operational integrity layer

`integrity-engine` cross-references three streams:

1. **System events** — what the platform recorded.
2. **Reality probes** — sampled from device telemetry, ambulance GPS, badge
   readers, lab specimen barcodes, drug dispensary logs.
3. **User behaviour traces** — keystroke timing, navigation entropy,
   override frequency, copy-paste patterns.

Discrepancies generate `integrity.discrepancy.detected` events, classified
into:

- `phantom_action` (system says X happened, reality says it did not)
- `ghost_action` (reality says X happened, system has no record)
- `bypass_pattern` (user systematically skirts a control)
- `behavioral_anomaly` (unusual but not necessarily malicious)

Forced recalibration: a user accumulating ≥ N `bypass_pattern` events in a
rolling window enters **restricted mode**: write actions require co-signature
from a peer of equal or higher role until a supervisor clears the flag.

## 1.9 Real-time performance control

`priority-scheduler` is global and per-region. It enforces:

| Class | Examples | Reservation | Behaviour under load |
|-------|----------|-------------|----------------------|
| P0 critical | dispatch, MCOM mode change | 30% of every pool | Never queued; if no slot, evict P3 |
| P1 urgent | triage decision, ED order | 30% | Bounded queue; SLO 99% < 800 ms |
| P2 routine | clinic visit, follow-up | 30% | SLO 95% < 2 s |
| P3 background | analytics, sampling, batch | 10% | Best-effort; first to be auto-degraded |

Auto-degrade triggers: CPU > 80%, DB pool > 75% utilised, replication lag >
2 s, P0 reservation breach. `gula-platform` shedding is preferred over
clinical degradation; explicit ordering is encoded in the policy bundle.

## 1.10 Distributed sovereign operation

- **Regional Sovereign Node (RSN)** — every governorate runs an independent
  RSN that is functionally complete: it can register patients, accept
  encounters, run triage, persist orders/results, and make every decision
  for which it owns the canonical data. Each RSN holds a `sovereignty
  manifest` (signed by the Ministry root + the regional health authority)
  which lists: jurisdiction, owned domains (e.g. `region=BG`), allowed
  cross-region operations, fallback peers, root keys.
- **National Federation Tier (NFT)** — aggregates and resolves cross-region
  cases (referrals, transfers, MPI merges across regions). It is **not**
  authoritative for any record an RSN owns.
- **Split-brain handling** — see `05-offline-sync.md`. Each entity has
  exactly one **owning RSN**. Cross-RSN mutations require a two-phase
  custody handoff. During partition, the owning RSN remains authoritative;
  the other side may only create proposals which reconcile on heal.
- **Reconciliation** — CRDT for additive structures (allergies, problem
  list); event-log replay with deterministic resolver for FSM-bound entities
  (encounter, referral). On unresolvable conflict, the entity is parked in
  `manual-merge` queue and a human medical-records officer must merge.

## 1.11 Self-healing & observability

- Metrics: OpenTelemetry → Prometheus (regional) → Mimir (national).
- Tracing: OTel → Tempo. All clinical traces carry `policy_version_id`,
  `encounter_id`, `mpi_id`, `decision_class`.
- Logs: structured JSON → Loki (regional) → cold archive (S3-compatible
  sovereign object store) with WORM retention per `11-governance.md`.
- Auto-recovery workflows in `recovery-engine`: pool recycle, replica
  failover, cache warm, queue drain, AI circuit open, MCOM auto-raise.
- Escalation tree: see `09-failure-scenarios.md` §9.6.

## 1.12 Internal SDK (`sndhs-sdk`)

Mandatory entry point for every SNDHS service and for the GULA gateway
client. Exposes:

- `Auth` — token acquisition, attestation, refresh, principal model.
- `Events` — typed publish/subscribe with schema validation, idempotency
  keys, automatic causal-id propagation.
- `Validation` — runtime contract enforcement for every payload.
- `ErrorEnvelope` — single error type with `code`, `severity`, `retryable`,
  `redacted`, `correlation_id`, `policy_version_id`.
- `Time` — `signed_now()`, `monotonic_ns()`, `safe_mode_active()`.
- `PolicyBinding` — `with_policy(decision_class).run(fn)`.
- `Resilience` — circuit breaker, bulkhead, retry-with-jitter (no retry on
  non-idempotent unless idempotency key carried).

Direct HTTP / native DB access from a service to anything outside its own
ownership boundary is a CI failure.

## 1.13 Data contract validation

- Every API and event has a JSONSchema **and** a FHIR profile (where
  applicable). The Contract Registry is the source of truth.
- The SDK validates payloads on both ingress and egress. A failure produces
  `ContractViolation` (severity `S1`) and the request is rejected before
  any side effect. For events, a violating event lands in the
  `dead-letter-quarantine` topic and triggers an alert.
- **Strict mode for clinical payloads:** unknown fields are rejected (no
  `additionalProperties: true`). Versioning is explicit (`schema_version`
  field) and migrations are handled by the Contract Registry's translator.

## 1.14 Deployment topology summary

- 1 NFT (active/active across two data centres, ≥ 200 km apart).
- N RSNs (one per governorate). Each RSN deploys: full Critical Plane, full
  Clinical Plane, partial Governance Plane (audit, time agent, integrity,
  policy mirror). The remaining Governance services run only in NFT but
  every RSN holds a signed mirror sufficient for 72 h offline.
- Per RSN: 3-node PG cluster (Patroni + sync replicas), 3-node NATS,
  3-node Redis, 3-node app fleet, 1 air-gapped audit archiver.
- Ministry-only: `policy-authority` master, `time-authority` master,
  national MPI federation, AI governance master, validation engine master.

The Minimal Sovereign Build Core (`08-msbc.md`) defines the smallest
deployable RSN that still meets H1–H5.
