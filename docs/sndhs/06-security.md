# 06 — Security Model (Zero-Trust)

## 6.1 Threat model (summary)

In scope: insider abuse, compromised endpoints, partial network
compromise, leaked credentials, hostile state actor on the link layer,
disgruntled administrators, supply-chain compromise of a single image,
ransomware on a single RSN.

Out of scope: physical destruction of all RSNs simultaneously; rooted
HSM on multiple regions simultaneously (mitigated by shamir-split key
hierarchy across geographies + offline air-gapped roots).

Adversary capabilities assumed: full network observation, transient MITM,
ability to phish a single clinician account, ability to compromise one
endpoint device.

## 6.2 Identity model

### 6.2.1 Principals

- **Citizen** (`p:citizen:{mpi_id}`)
- **Clinician** (`p:clinician:{license_id}`)
- **Allied health / staff** (`p:staff:{employee_id}`)
- **Lab technician** (`p:lab:{license_id}`)
- **Ambulance crew** (`p:ambulance:{crew_id}`)
- **Dispatcher** (`p:dispatch:{employee_id}`)
- **Administrator** (`p:admin:{employee_id}`)
- **Legal officer** (`p:legal:{employee_id}`)
- **Auditor** (`p:auditor:{employee_id}`) — read-only, cannot
  authorise clinical actions
- **Service** (`p:service:{spiffe_id}`)
- **Device** (`p:device:{attestation_id}`)
- **System** (`p:system:{component}`) — for autonomous actions

### 6.2.2 Authentication assurance

| Action class | Required AAL | Required authenticators |
|--------------|--------------|--------------------------|
| Read non-clinical | AAL2 | Password + OTP |
| Read clinical | AAL2 + WebAuthn | + WebAuthn |
| Write clinical | AAL3 | + WebAuthn (resident key) + recent re-auth (15 min) |
| Critical-encounter declare, MCOM raise | AAL3 + two-person | Two distinct AAL3 sessions |
| Legal-hold / merge / delete | AAL3 + two-person + role | Two distinct legal-officer sessions |
| Sign release of cohort data | AAL3 + ministry quorum (3-of-5) | HSM-backed signing |

Re-authentication required on:

- New session,
- Role / facility switch,
- After 15 min of inactivity for clinical writes,
- Step-up for any decision flagged `severity ≥ S2`.

### 6.2.3 Service identity

- SPIFFE/SPIRE issues 15 min X.509-SVIDs per workload.
- Workload ID encodes plane (`crit/clin/gov`), service, region.
- Cross-plane service calls require an explicit policy permit.
- All inter-service traffic is mTLS; the SPIFFE ID is the identity used
  by ABAC.

### 6.2.4 Device identity

- TPM 2.0 attestation for clinician workstations and shared kiosks.
- Sovereign HSM-backed device keys for ambulance and lab devices.
- Devices that cannot attest are quarantined to a "kiosk" persona with
  read-only access to non-PHI views.

## 6.3 Authorization (ABAC)

See `03-api.md` §3.2.3 for the engine and example policies. Additional
constraints:

- **Default deny** at every plane.
- **Two-person rule** for: legal hold toggle, MPI merge with score <
  0.95, critical declaration without device-bridge actor, MCOM raise to
  3+, AI promotion, irreversible deletes.
- **Break-glass** is a defined role — auditable, time-boxed (max 60
  min), requires a recorded justification, triggers a real-time alert
  to the patient's primary clinician and to compliance.
- **Quorum policies** for ministry-level actions (3-of-5 deputy signers
  required to release cohort data, change retention class, freeze a
  national register).

### Continuous authorisation

ABAC is re-evaluated on every request and every event. A long-running
WebSocket subscription is dropped immediately if the policy bundle
changes such that the principal would be denied.

## 6.4 Audit ledger

### 6.4.1 What is audited

- Every state-changing API call (request envelope + body hash, response
  status + body hash).
- Every emitted domain event (full event).
- Every ABAC decision (allow/deny + rule id).
- Every break-glass usage (full keystroke timeline).
- Every policy bundle change (signing chain).
- Every legal hold / unhold / data export.
- Every AI inference at the boundary (input feature hash + output +
  model artefact hash).
- Every sync custody handoff and every manual merge.

### 6.4.2 Hash chain

```
prev_hash       = audit_entry[i-1].hash
canonical_bytes = canonicalize_jcs(entry_without_hash)
this_hash       = blake3(prev_hash || canonical_bytes)
```

- Per-RSN local chain.
- National chain at NFT references regional chain heads at hourly
  checkpoints, signed by Ministry HSM.
- Chain heads published daily to a sovereign transparency log (sigstore
  rekor-equivalent) and cross-signed by an independent body.

### 6.4.3 Integrity verification

- Verifier walks the chain on demand and at scheduled intervals.
- Any break: P0 incident; suspends writes on the affected segment until
  cleared; triggers Ministry-level investigation.
- Auditors have a read-only view; they cannot mutate the ledger or the
  source events.

### 6.4.4 Storage

- Hot: PostgreSQL (`audit_entry`).
- Warm: object store with WORM lock (object-lock retention period set
  per retention class).
- Cold: WORM tape, off-site, sovereign control.

### 6.4.5 Retention

- 25 years for clinical-action audit (paediatric extends to 25 y from
  age of majority).
- 10 years for non-clinical operations audit.
- Indefinite for legal-hold + 7 years post-release.
- Retention is set by `retention_class` in `11-governance.md` and
  enforced by the lifecycle service. Deletes require a signed deletion
  order from the Data Lifecycle Authority and are themselves audited.

## 6.5 Data segmentation

### 6.5.1 Confidentiality classes

- `PUBLIC`,
- `INTERNAL`,
- `PHI` (default for clinical),
- `PHI-VIP` (sensitive — political, celebrity, security force),
- `PHI-MENTAL`,
- `PHI-SEXUAL` (including GBV cases),
- `PHI-PEDIATRIC`,
- `PHI-INFECTIOUS-NOTIFIABLE`,
- `LEGAL-HOLD`.

Each class has its own ABAC predicate and may have stricter access
constraints (e.g., VIP requires an explicit role grant per encounter).

### 6.5.2 Network segmentation

- Critical Plane network is physically separate from Clinical Plane in
  the data centre and at the edge (separate VRFs / VLANs).
- Governance Plane sits on a third VRF.
- GULA platform is in a fourth VRF outside SNDHS; it accesses SNDHS
  only via the Sovereign Gateway DMZ.
- Ambulance / dispatch links use a private APN with mandatory VPN to
  the regional dispatch-bridge.
- East-west traffic is mTLS + Cilium L7 policies; no plaintext intra-
  cluster traffic.

### 6.5.3 Tenant isolation

- Every clinical row carries `region_id`; row-level security enforces
  per-region read by default. Cross-region read is a permission grant
  that emits a high-severity audit event.
- Backups are per-region; cross-region restore requires Ministry
  authorisation.
- Logs are tagged with `region_id`; aggregation upstream is filtered
  for PHI; PHI never enters the central observability stack — only
  hashed identifiers.

### 6.5.4 Encryption keys

```
Ministry Root (offline, Shamir 3-of-5)
  ├── Region Root (HSM, online, rotated yearly)
  │     ├── Service KEK (rotated quarterly)
  │     │     ├── Column DEK (rotated monthly)
  │     │     └── Object DEK (per object, wrapped)
  │     └── Audit KEK (separate; auditors never get plaintext data keys)
  └── Federation Root (NFT signing)
```

Key access policy:

- A service can decrypt only what its policy permits.
- DEK rotation is hot — new writes use the new DEK; old reads decrypt
  with the old DEK referenced in the column metadata.
- HSM operator role separated from infra admin role.

## 6.6 Cryptographic suite

| Use | Primitive |
|-----|-----------|
| Identity / signing | Ed25519 (and Ed448 reserved for ministry roots) |
| KEX | X25519 |
| Symmetric AEAD | XChaCha20-Poly1305 |
| Hashing (perf) | BLAKE3 |
| Hashing (FIPS audit) | SHA-256 |
| TLS | TLS 1.3 (kyber-768 hybrid for transitional PQ) |
| Long-term storage encryption | XChaCha20-Poly1305 with per-object nonce + AAD |
| Code signing | sigstore-equivalent + Ministry-rooted Fulcio analogue |

Algorithm agility is enforced by policy bundle version; any
deprecation is staged and audited.

## 6.7 Secrets management

- Vault (or sovereign equivalent) per RSN, sealed by HSM.
- No plaintext secrets in env vars on disk; container env is populated
  from Vault on start via short-lived AppRole.
- Secret access is audited; secrets cannot be read by humans except via
  the break-glass workflow.
- Hardcoded fallbacks are forbidden (CI scans block).

## 6.8 Application security

- All inputs validated by the SDK contract layer (no
  `additionalProperties: true` on clinical types).
- Output encoding for any UI uses safe templating (no string-concat
  HTML).
- SQL: parameterised queries only; no dynamic SQL execution from
  user-controlled values; `LIKE` on user-controlled patterns
  forbidden.
- Authorization is re-checked at the data layer (RLS) — never trust the
  app layer alone.
- CSRF: state-changing requests require an `Origin`-bound token (web
  clients) or carry a signed Decision Token (services).
- CSP: strict, no inline scripts; nonce-based.
- HSTS, COOP, COEP, X-Frame-Options DENY, Referrer-Policy
  no-referrer.

## 6.9 Supply chain

- Reproducible builds for every SNDHS service.
- SLSA level 3 minimum.
- SBOM (CycloneDX) for every release; signed and stored for the life
  of the release.
- Image signature verification at admission (Cosign + sovereign
  Fulcio).
- Dependency pinning + automated CVE scan; release cadence: critical
  CVE → 24 h, high → 7 d, medium → 30 d.

## 6.10 Incident response

- Security IR runbook in `09-failure-scenarios.md`.
- Compromise indicators are events on the `gov.security.*` topic; the
  on-call IR team subscribes.
- Containment uses pre-approved actions (revoke service identity,
  rotate keys, isolate RSN, kill switch). Each action has a
  pre-authorised signed runbook artefact.
- Post-incident report mandatory within 14 days; root cause + control
  improvements added to the policy authority.
