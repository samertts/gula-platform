# 10 — GULA Integration Layer

## 10.1 Boundary statement

GULA is a non-clinical layer. It MUST NOT:

- Persist clinical data of any kind (FHIR resources, observations,
  results, orders, encounters, referrals, MPI demographics, audit
  entries).
- Make any clinical decision (triage, escalation, eligibility,
  contraindication, dosage).
- Drive emergency workflows (dispatch, MCOM, ambulance assignment).

GULA MAY:

- Render clinical UIs by composing **render-bundles** signed by SNDHS
  (the bundle is opaque-by-default; GULA only displays).
- Provide non-clinical services: facility administration, lab billing,
  citizen self-service for non-clinical data, scheduling support,
  document upload routed straight to SNDHS.
- Submit user-initiated transitions to SNDHS through the gateway (with
  the user's decision token).
- Operate the LabLink device bridge for lab equipment integration —
  but the canonical write of any result lands in SNDHS Result Engine,
  not in GULA.

## 10.2 Sovereign Gateway

A dedicated ingress fronting GULA → SNDHS calls.

### 10.2.1 Position in the architecture

```
GULA front-end ──► GULA service ──► Sovereign Gateway ──► SNDHS plane
                                       │
                                       ├── mTLS termination, SPIFFE-validated
                                       ├── Authn (citizen / clinician)
                                       ├── Authz (ABAC; deny-by-default)
                                       ├── Policy binder
                                       ├── Decision stabiliser
                                       ├── Rate limit
                                       ├── DLP egress filter
                                       ├── Audit emit
                                       └── Forward
```

Every GULA→SNDHS call is mediated. There is **no** other path.

### 10.2.2 DLP egress filter

The filter strips any field not on the per-route allow-list before the
response leaves SNDHS. Default: reject fields. Allow-listed fields are
typed (e.g., `mpi_id`, `appointment_at_utc`). Free-text clinical
content cannot be allow-listed for GULA without a Ministry exception.

The filter is implemented as a contract-driven projector: each route's
response schema declares `gula_visible: true|false` per field; the
projector emits only the visible subset.

### 10.2.3 Render-bundles

For UIs that need to display clinical content (e.g., a doctor reviewing
results in GULA), SNDHS issues a signed render-bundle:

- Composed server-side from canonical data.
- Sealed (encrypted to the user's session key).
- Bound to a single session and a single time window (≤ 5 min).
- Carries display metadata (Arabic-first formatting, units, ABAC
  decision id).
- Verified and rendered by a sandboxed component in the GULA UI; the
  raw content does not enter GULA storage.

GULA may cache the *rendered DOM tree* for the duration of the session
but MUST NOT persist the underlying clinical bytes.

## 10.3 API restrictions

| Action | Permitted via gateway? | Notes |
|--------|-----------------------|-------|
| Create patient registration request | Yes | Goes to SNDHS MPI; GULA never owns MPI |
| Read MPI demographics | Limited | Only redacted fields (e.g., name initial + DOB year) unless a render-bundle is requested |
| Submit lab order | Yes | Idempotency key from GULA accepted; SNDHS authoritative |
| Display lab result | Render-bundle | No raw transport |
| Trigger triage | No | Forbidden |
| Change MCOM | No | Forbidden |
| Issue dispatch | No | Forbidden |
| Manage facility schedule | Yes (non-clinical) | Slot management; clinical pre-conditions enforced by SNDHS |
| Bill / invoice | Yes (non-clinical) | Pricing rules in GULA; anchors to encounter id without clinical detail |
| Lab device management (LabLink) | Yes | Device telemetry routed; clinical results pushed to SNDHS |
| Notifications | Limited | Non-clinical content only; clinical comms originate from SNDHS notification fabric |

## 10.4 Identity bridging

- The user authenticates with the national IdP. The same IdP issues
  tokens for both GULA and SNDHS, but with different audiences and
  different `acr` requirements.
- GULA never sees a SNDHS decision token. It calls the gateway; the
  gateway exchanges the user's session token for a decision token.
- A clinician logging into GULA does NOT thereby get clinical write
  authority — that requires the dedicated SNDHS clinical workspace
  with WebAuthn step-up.

## 10.5 UI flow examples

### 10.5.1 Lab tech enters a new sample

1. Lab tech in GULA scans the sample barcode.
2. GULA POSTs `/v1/orders/sample-receipt` to gateway.
3. Gateway authn → ABAC permit (lab role + facility match) → policy
   bind → decision token.
4. Forwarded to SNDHS Order Engine which records the receipt and
   emits `clin.order.sample_received.v1`.
5. SNDHS returns minimal payload to GULA (`order_id`, `status`).
6. GULA UI shows confirmation.

### 10.5.2 Clinician reviews critical result

1. Clinician opens the result list in the SNDHS clinical workspace
   (NOT in GULA). GULA is bypassed entirely for the read.
2. If the clinician must operate a non-clinical workflow (e.g., bill),
   GULA fetches a *render-bundle* via the gateway for display
   alongside the bill.

### 10.5.3 Citizen books an appointment

1. Citizen in GULA picks a slot and submits.
2. Gateway authn → policy bind → forward to SNDHS Encounter
   Orchestrator (slot reservation route).
3. SNDHS confirms; GULA shows confirmation, sends a non-clinical
   reminder via its own notification path. Clinical reminders (e.g.,
   pre-procedure fasting instructions) come from SNDHS.

## 10.6 Fail-safe behaviour

- **GULA down**: clinical operations are unaffected — clinicians use
  the SNDHS clinical workspace. Lab device telemetry queued at the
  device-bridge buffer (24 h hot, 7 d warm) and flushed on recovery.
- **Gateway down**: GULA shows a "service degraded" banner; clinical
  workspace remains available directly. Critical-plane is unaffected
  (gateway is not on the critical path).
- **SNDHS partition (regional)**: GULA's regional instance follows
  the RSN's safe-mode posture: read-only views; non-clinical writes
  queued; clinical writes blocked.
- **Decision token denied**: GULA shows a localised reason ("not
  permitted in current MCOM level", "step-up required"); never the
  raw policy id.
- **DLP filter cannot strip**: response 422 to GULA with
  `LEAKAGE_PREVENTED`; SNDHS team alerted; the route's allow-list is
  reviewed.

## 10.7 Audit and traceability

- Every GULA→SNDHS call is audited at the gateway (request envelope,
  body hashes for clinical bodies, response status, ABAC decision).
- GULA's own actions on its own non-clinical data are audited inside
  GULA's audit log; the two logs are correlated via `correlation_id`
  but live in separate stores (GULA's audit log is not legally
  authoritative for clinical claims).
- Cross-system reports for compliance are produced by joining the two
  on correlation_id, never by mixing the records.

## 10.8 Testing & enforcement

- Static gate: any GULA service that imports SNDHS internal modules,
  or directly accesses SNDHS data stores, fails CI.
- Network policy: GULA pods cannot reach SNDHS planes except via the
  gateway IP/port set; verified by network-policy unit tests.
- Schema gate: any GULA route that returns a payload containing
  fields tagged `phi=true` or `clinical=true` fails CI.
- Runtime DLP probe: synthetic clinical fields injected periodically;
  if any leak through to GULA, the gateway is auto-frozen and a P0
  incident raised.

## 10.9 Versioning of the contract

- The GULA-facing surface of the gateway has its own SemVer.
- Breaking changes (field removals, narrowing types, ABAC tightening)
  follow a 12-month deprecation, with both versions live during the
  window.
- All GULA clients must handle gateway 451/423/503 with localised UX;
  the SDK provides typed helpers.
