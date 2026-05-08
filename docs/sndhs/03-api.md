# 03 — API Specification

## 3.1 General principles

- Transport: HTTPS/2 + mTLS for all S2S; TLS 1.3 for client traffic.
- Encoding: JSON (UTF-8) for clinical APIs; CBOR available for ambulance
  / device endpoints with strict size budgets.
- Versioning: URL prefix `/v{major}` and `Schema-Version` header for
  minor/patch; never remove a field without a deprecation cycle (≥ 12
  months for clinical fields; ≥ 24 months for FHIR-mapped fields).
- Idempotency: every state-changing request MUST carry
  `Idempotency-Key: <ULID>`. The server stores `(principal_id, route,
  idempotency_key) → result` for ≥ 24 h.
- Tracing: request MUST carry `Traceparent`, `Request-Id`,
  `Correlation-Id`, `Causation-Id`.
- Time: every state-changing request MUST carry `Time-Token: <signed
  token>` issued by `time-authority` within the last 60 s.
- Errors: single envelope (`ErrorEnvelope` — see 1.12). Status codes
  follow RFC 9457 problem details for 4xx/5xx.

```json
{
  "type": "https://errors.sndhs/clinical/CONTRACT_VIOLATION",
  "title": "Payload failed contract validation",
  "status": 422,
  "code": "CONTRACT_VIOLATION",
  "severity": "S1",
  "retryable": false,
  "correlation_id": "01J9ZQ...",
  "policy_version_id": "01J5...",
  "details": [
    { "field": "$.observations[3].value_quantity", "reason": "must be >= 0" }
  ]
}
```

## 3.2 Authentication & Authorization (Zero Trust)

### 3.2.1 Identity

- **Workforce**: OIDC (national IdP) → step-up via FIDO2/WebAuthn for any
  clinical write. `acr` and `amr` claims reach the policy engine.
- **Citizens**: OIDC + FIDO2 + national-ID-backed assurance level
  (LoA-2 / LoA-3).
- **Devices**: SPIFFE workload identity + hardware attestation (TPM 2.0
  or sovereign HSM). No password-based auth for devices.
- **Service-to-service**: SPIFFE/SPIRE — short-lived (15 min) X.509-SVIDs,
  rotated automatically.

### 3.2.2 Token model

Two token classes — never interchangeable:

- **Session token (JWT, 15 min, refreshable)** — for client APIs.
- **Decision token (JWT, 60 s)** — minted at the gateway after ABAC
  evaluation, bound to a single decision (`decision_class`,
  `subject_id`). Carried internally to enforce that downstream services
  apply the same decision context the gateway authorised.

Claims (decision token):

```json
{
  "iss": "sndhs:gateway:bg",
  "sub": "principal:01J...",
  "aud": ["sndhs:emr-core","sndhs:audit-ledger"],
  "iat": 1714944000,
  "exp": 1714944060,
  "amr": ["pwd","webauthn"],
  "acr": "loa3",
  "principal_attrs": {
    "role": ["clinician"],
    "specialty": ["emergency"],
    "facility_id": "01HX...",
    "region_id": "BG",
    "license_status": "ACTIVE"
  },
  "decision": {
    "class": "encounter.write",
    "subject_kind": "encounter",
    "subject_id": "01HY...",
    "policy_version_id": "01J5..."
  },
  "constraints": {
    "deny_export": true,
    "max_resources": 1
  },
  "attestation_id": "01J..."
}
```

### 3.2.3 ABAC

ABAC engine: OPA + Cedar hybrid. Cedar for high-throughput sync checks,
OPA for policy management UI and bulk evaluation. The same policy bundle
compiles to both (policy authority emits both artefacts).

Attribute sources:

- Principal: IdP claims, license registry, role assignment store.
- Resource: tags from the entity (`region_id`, `owning_rsn`, `mpi_id`,
  `confidentiality`, `legal_hold`).
- Context: time-of-day, MCOM level, geo, device attestation, network
  posture, decision class, recent override count.

Sample Cedar policy:

```cedar
permit (
  principal,
  action == Action::"encounter.write",
  resource is Encounter
) when {
  principal.role.contains("clinician") &&
  principal.license_status == "ACTIVE" &&
  resource.facility_id == principal.facility_id &&
  context.amr.contains("webauthn") &&
  context.mcom_level <= 2 &&
  resource.confidentiality != "VIP" || principal.role.contains("vip-cleared")
};

forbid (
  principal,
  action,
  resource is Patient
) when {
  resource.legal_hold &&
  !principal.role.contains("legal-officer")
};

forbid (
  principal,
  action,
  resource
) when {
  context.recent_override_count > 5 &&
  context.bypass_pattern_score >= 0.7
};
```

A request is allowed iff **all** `permit`s match and **no** `forbid`
matches. Decisions are explained: every deny carries the policy id and
matching forbid rule id back to the audit ledger.

## 3.3 MPI APIs

Base: `/v1/mpi`.

### POST `/patients/match`

- Returns probabilistic match candidates without disclosing demographics
  if confidence < threshold. Used by registration UIs.
- Action: `mpi.match`. Allowed roles: `registrar`, `clinician`.

```yaml
RequestBody:
  schema_version: 1
  given_name: string (required)
  family_name: string (required)
  dob: string (date, required)
  sex: enum [F, M, U]
  national_id: string (optional)
  phone: string (optional, E.164)

Responses:
  200:
    candidates:
      - mpi_id: string
        score: number      # 0..1
        decision_hint: enum [MATCH, POSSIBLE, NO_MATCH]
        masked_summary: string  # e.g., "F**, 19**, ****-321"
  422: ContractViolation
```

### POST `/patients`

- Action: `mpi.create`. Idempotent on `(national_id, source_facility)`.
- Side effect: emits `mpi.patient.registered`.

### POST `/patients/{mpi_id}/merge`

- Action: `mpi.merge`. Two-person rule when score < 0.95.
- Side effect: emits `mpi.patient.merged`. The losing record becomes
  `MERGED`, all references updated via projection.

### GET `/patients/{mpi_id}`

- Action: `mpi.read`. ABAC will strip fields based on principal role.

### POST `/patients/{mpi_id}/legal-hold`

- Action: `mpi.legal_hold`. Role: `legal-officer` only. Sets/unsets the
  flag on the MPI record and on derived clinical resources by event.

## 3.4 EMR APIs (FHIR R5 compliant)

Base: `/v1/fhir`. The only HTTP surface for FHIR. Internal services do
not consume FHIR — they consume canonical events.

| Resource | Operations |
|----------|-----------|
| Patient | read, search (no `_text`), history |
| Encounter | read, create, update (state machine), search |
| Observation | read, create (vitals, results), search, `$lastn` |
| Condition | CRUD |
| AllergyIntolerance | CRUD (CRDT-safe) |
| MedicationRequest | create, read, update (state machine) |
| ServiceRequest | create, read, update (state machine — orders, referrals) |
| DiagnosticReport | create, read |
| DocumentReference | create, read (attachments) |
| Consent | create, read |

Search constraints:

- Patient search MUST filter by exact `identifier`, `birthdate`, or
  `family+given+birthdate`. Wildcard / token search is forbidden.
- Page size capped at 50 for clinical resources; cursor-based paging
  (`_cursor=` instead of `_offset=`).
- `_include` allow-list per role (e.g., a billing role cannot
  `_include=Observation`).

All FHIR responses include `meta.versionId`, `meta.lastUpdated` (UTC
from the time authority), `meta.tag.policy_version_id`, and
`meta.security` with confidentiality.

## 3.5 Referral APIs

Base: `/v1/referrals`.

### POST `/referrals`

- Body: `from_facility`, `to_facility`, `specialty`, `priority_class`,
  `clinical_summary`, `attachments[]`.
- Side effects: persists referral; emits
  `referral.created`; reserves an appointment slot if `auto_book = true`.

### POST `/referrals/{id}/accept`

- Receiving facility accepts. Emits `referral.accepted`.

### POST `/referrals/{id}/schedule`

- Emits `referral.scheduled` with appointment details.

### POST `/referrals/{id}/arrival`

- Emits `referral.patient_arrived`.

### POST `/referrals/{id}/outcome`

- Emits `referral.outcome_recorded`. Closes the loop by sending
  `referral.feedback_to_origin` to the origin facility.

### POST `/referrals/{id}/cancel`

- Reason code mandatory; emits `referral.cancelled`.

State transitions are validated at the API layer **and** by the DB
trigger from `02-database.md` §2.3.2. See `04-state-machines.md` §4.1.

## 3.6 Triage APIs (Critical Plane)

Base: `/v1/triage`. Hard P99 < 80 ms.

### POST `/encounters/{id}/triage/assess`

- Body: chief complaint, vital snapshot, free-text optional.
- Engine: deterministic ESI-5 implementation (no AI on hot path).
- Returns: `acuity_class`, `disposition`, `recommended_pathway`,
  `policy_version_id`, `decision_id`.
- Side effect: emits `triage.assessed`.

### POST `/encounters/{id}/triage/reassess`

- Same shape; produces a new assessment that the decision-stabilizer
  evaluates (hysteresis prevents oscillation between ESI-3↔ESI-2).

## 3.7 Emergency APIs (Critical Plane, P0)

Base: `/v1/emergency`. Hardest SLA: P99 < 250 ms ingress to ack,
P99 < 2 s to first downstream subscriber.

### POST `/dispatch/calls`

- Used by 122 dispatch & ambulance MDT.
- Body: caller info, geo, severity hint, ambulance assignment.
- Side effect: opens a `dispatch_case`; emits `crit.dispatch.created`.
- Reservation: pre-allocates an ED bed slot via priority-scheduler.

### POST `/dispatch/calls/{id}/route`

- Recomputes routing under live conditions; respects MCOM level (e.g.,
  MCOM-3 reroutes to designated mass-casualty hubs).

### POST `/ambulance/{unit}/vitals`

- Streaming endpoint (CBOR + WebTransport for cellular ambulances; HTTP
  long-poll fallback). Each frame ≤ 256 B.
- Maximum jitter: 750 ms server-to-display.

### POST `/encounters/{id}/critical/declare`

- Declares a critical encounter (e.g., STEMI activation). Triggers the
  bound bundle (orders + notifications) atomically. Two-person rule
  unless ambulance device-bridge is the actor.

### POST `/mcom/level`

- Action: `mcom.set_level`. Body: `level (1-4)`, `reason_code`,
  `effective_until`. Two-person rule for raising; single-person for
  lowering. See `04-state-machines.md` §4.3.

## 3.8 Event-streaming APIs

External consumers (regulators, analytics, GULA) receive a filtered
event stream:

- Transport: NATS JetStream over WebSocket with mTLS, or gRPC server
  streaming.
- Topics expose a *projection*, not the canonical bus. Every event
  passes the DLP filter and is signed by the gateway with a
  `gateway-egress` key.
- Consumers MUST send `Last-Event-Id` (durable cursor) on reconnect.
  At-least-once delivery; duplicates dedup by `(stream_kind, stream_id, sequence)`.
- Backfill window: 7 days. Beyond 7 days, consumers must request a
  backfill plan via `POST /v1/events/backfill` (audited).

Public projection topics:

- `pub.referrals.v1` (no PHI; opaque IDs)
- `pub.encounters.v1` (no PHI)
- `pub.mcom.v1` (regional level changes)
- `pub.public-health.v1` (aggregate, k-anonymous ≥ 5)

Internal full-fidelity topics (`crit.*`, `clin.*`, `gov.*`) are not
exposed externally.

## 3.9 Rate limiting

- Per-principal token bucket, per-route refill rate.
- Per-facility hard cap.
- Critical-plane P0 routes are exempt; instead they are governed by the
  reservation table.
- Burst policy: `burst = 2 × refill_rate`. On violation: 429 with
  `Retry-After` and `policy_version_id`.

## 3.10 Idempotency & retries

- `Idempotency-Key` mandatory on all POST/PATCH/DELETE.
- Retries: clients MUST use exponential backoff with jitter (50 ms,
  100 ms, 200 ms, 400 ms, cap 2 s, 4 attempts). The SDK enforces this.
- Server: replays return the original response with header
  `Idempotent-Replay: true`.

## 3.11 OpenAPI & contract publishing

- The Contract Registry publishes OpenAPI 3.1 + JSONSchema + FHIR
  profiles per route, all signed.
- The SDK fetches the bundle at start-up and pins it; mismatches fail
  closed.
- Public OpenAPI is published only for routes whose `public=true` flag
  is set in the registry.

## 3.12 Error code taxonomy (excerpt)

| Code | Meaning | HTTP |
|------|---------|------|
| `CONTRACT_VIOLATION` | Payload failed schema | 422 |
| `POLICY_DENIED` | ABAC deny | 403 |
| `STATE_INVALID_TRANSITION` | FSM rejects | 409 |
| `DECISION_LOCKED` | Stabilizer lock window active | 423 |
| `DECISION_OSCILLATING` | Frozen, human required | 423 |
| `TIME_TOKEN_INVALID` | Time token expired/forged | 401 |
| `IDEMPOTENCY_CONFLICT` | Same key, different body | 409 |
| `MCOM_RESTRICTED` | Disabled at this MCOM level | 423 |
| `LEGAL_HOLD` | Action blocked by legal hold | 451 |
| `AI_NOT_PROMOTED` | AI advisory not visible | 451 |
| `OWNERSHIP_FOREIGN` | RSN does not own this entity | 409 |
| `BACKPRESSURE_SHED` | Auto-degrade rejected non-critical | 503 |
| `RECONCILIATION_PENDING` | Proposal awaits owner | 409 |
