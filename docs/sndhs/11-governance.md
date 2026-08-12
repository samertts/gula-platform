# 11 — Policy, Time & Data Lifecycle Governance

## 11.1 Policy authority

### 11.1.1 Model

A **policy bundle** is an immutable, signed artefact containing:

- ABAC rules (Cedar + OPA Rego mirror).
- FSM transition tables (encounter, referral, MCOM, sync custody).
- Decision-stabilizer parameters per `decision_class`.
- Clinical rules (sepsis, stroke, STEMI bundles; ESI weights).
- Retention classes (per data type).
- Rate / concurrency / reservation parameters.
- AI promotion list (which models are advisory, with version pin and
  thresholds).
- MCOM mappings (which routes are restricted at which level).
- Cryptographic suite version.
- Manifest of allowed image hashes (admission control).

Bundles are produced by the policy authority service from source
documents in a Git-backed monorepo (`policy-source/`). The build
pipeline:

1. Lint & type-check Rego/Cedar.
2. Run TLA+ model checks for any FSM change.
3. Run policy-against-traces tests (replay last 30 days of decisions
   and confirm allowed → still allowed, except where a new forbid
   intentionally narrows).
4. Sign with the policy authority key (HSM-rooted).
5. Publish to the bundle store (national + regional mirrors).

### 11.1.2 Versioning

- `policy_version_id` is a ULID per bundle (lexicographically sortable).
- Bundles are immutable. Re-signing produces a new id.
- Every clinical row and every event carries the
  `policy_version_id` under which the decision was taken.
- Active bundle is selected by an **activation pointer** per region.
  Pointers are set by canary rollout (see §11.1.4).

### 11.1.3 Binding

Every decision MUST be bound to a `policy_version_id` at the moment
it is taken; the binder is part of the SDK and the gateway. Any code
path that produces a clinical effect without a bound id is a CI
failure.

### 11.1.4 Safe rollout (canary + regional)

- New bundle is first deployed to **shadow** in 1 region: the region
  evaluates both old and new bundles for every decision; differences
  recorded; no behaviour change.
- After ≥ 7 days shadow with no severity-≥-S2 differences, **canary**
  in 1 region (real behaviour). Monitored against SLOs; auto-rollback
  on regression > defined thresholds.
- Staged rollout to remaining regions over 14 days unless an
  emergency-override (security or clinical safety) shortens the
  window. Emergency override requires Ministry CISO + CMO signature.
- Rollback is a pointer flip back to the previous bundle. Decisions
  taken under the rolled-back bundle remain bound to it (no
  rewriting).

### 11.1.5 Auditability

- Every bundle activation, rollback, and shadow-mode entry is an event
  on `gov.policy.bundle.*` and an audit ledger entry.
- A read-only public dashboard shows the current active bundle per
  region, its hash, and the activation timeline. Auditors can request
  the full bundle artefact for any historical id.

## 11.2 Trusted time system

### 11.2.1 Architecture

- **National time authority** (NFT): two stratum-1 GPS receivers +
  Rb oscillator + chrony peers + an air-gapped Cs reference for
  forensic anchoring.
- **Regional time authority agents** (RSN): stratum-2; sync to
  national; fall back to GPS-only on uplink loss; fall back to Rb +
  monotonic on GPS loss.
- **Service time client** (SDK): exposes `signed_now()` →
  `(monotonic_ns, wall_utc, time_authority_id, time_quality, signature)`.

### 11.2.2 Signed time tokens

- Tokens issued by the time authority for state-changing requests, 60
  s validity, signed Ed25519. The gateway validates and forwards.
- The token binds the request to a quality level. Critical-plane
  routes accept `TRUSTED` only; clinical routes accept `TRUSTED` and
  `DRIFTED` (with annotation); under `LOCAL_FALLBACK`, only safety
  critical writes accepted.

### 11.2.3 Drift detection

- Continuous comparison: regional vs national; service vs regional.
- Thresholds:
  - `wall_skew_ns > 100 ms` for 30 s → `DRIFTED`.
  - `wall_skew_ns > 500 ms` or unsigned for 60 s → `LOCAL_FALLBACK`.
- Auto-remediation: re-discipline chrony; re-acquire GPS; if both
  fail, escalate.

### 11.2.4 Safe-mode on desync

- Rate-sensitive features (e.g., billing windows) suspended.
- AI advisories suspended.
- All writes annotated with `time_quality`.
- UIs display a banner.
- Recovery: when a TRUSTED epoch is re-established, a `time.recovered`
  event is emitted; affected events are revalidated (e.g., medication
  dose timing windows are recomputed and any over-window entries are
  flagged for clinical review).

### 11.2.5 Forensic anchoring

- Daily, the national authority writes a signed
  `(monotonic_ns, wall_utc, audit_chain_head_hash)` triple to a
  cross-border timestamp service (Ministry-approved) so post-hoc
  manipulation of clocks would also require collusion with that
  service.

## 11.3 Data lifecycle governance

### 11.3.1 Retention classes

| Class | Hot retention | Warm retention | Archive | Purge eligible | Notes |
|-------|---------------|---------------|---------|----------------|-------|
| `R-CLINICAL-ADULT` | 90 d | 7 y | 25 y WORM | After archive expiry | Default for adult clinical |
| `R-CLINICAL-PED` | 90 d | 7 y | until age 25 + 25 y WORM | After archive expiry | Paediatric extends |
| `R-CLINICAL-LEGAL-HOLD` | indefinite | indefinite | indefinite | Only after release order + 7 y | Legal hold |
| `R-AUDIT` | 365 d | 7 y | 25 y WORM | Never (within retention) | Hash-chained |
| `R-OPS-LOG` | 30 d | 1 y | 3 y | Yes | Non-PHI ops logs |
| `R-AI-INFERENCE` | 90 d | 1 y | 7 y | Yes | Inference logs (input hash + output) |
| `R-NOTIFY` | 30 d | 1 y | — | Yes | Comm receipts |
| `R-PUBHEALTH-AGG` | hot | warm | indefinite, anonymised | k-anonymous ≥ 5 | National stats |
| `R-DEVICE-TELEMETRY` | 7 d | 90 d | 1 y | Yes | Device frames; result events have own class |

Each table/event type declares its retention class; lifecycle service
moves data through stages by class.

### 11.3.2 Archival strategy

- Hot: NVMe in PG, latest months.
- Warm: PG with cheaper storage tier; partitions detached and
  compressed at boundary.
- Cold: WORM object store; encrypted with archival KEK (separate from
  hot path); access requires elevated role + audit.
- Air-gapped tape: WORM LTO; quarterly write + verify; off-site.

### 11.3.3 Legal hold

- `legal_hold = true` flips on the entity and propagates to derived
  records and events.
- All deletion / archival pipelines skip held entities.
- Hold is set by `p:legal:` role only. Two-person rule for setting
  AND clearing.
- Held entities visible to legal officers in a dedicated UI; clinical
  access continues normally with audit.

### 11.3.4 Data purging rules

- Purges are batch jobs run by the lifecycle service, not by humans.
- A purge requires:
  - Signed deletion order (HSM-backed) by Data Lifecycle Authority.
  - No `legal_hold` on any candidate.
  - Past retention end for the candidate's class.
- Purge actions are themselves audited; the audit entry includes a
  hash of the deleted payload (so the fact of deletion remains
  verifiable while the content is gone).
- "Right-to-be-forgotten" requests follow the same rules but originate
  from the citizen portal; only non-clinical / non-public-health
  records are eligible for full erasure; clinical records are
  redacted/anonymised in line with statute, never silently deleted.

### 11.3.5 Cross-cutting governance

- Quarterly external audit on retention policy adherence.
- Monthly internal reconciliation: count of expected purges vs
  performed, with deltas explained.
- Retention class changes require Ministry sign-off and a 90-day
  transition window where existing data follows the old class.

## 11.4 Configuration control

- All non-secret runtime configuration is declared in the policy
  bundle. Local config files are reserved for bootstrap only (e.g.,
  bundle store URL, HSM PKCS#11 path).
- Environment variables for clinical components are restricted; CI
  fails on unapproved env-var names.
- A change to a value that influences clinical behaviour is a policy
  bundle release, not a config edit.

## 11.5 Compliance dashboards

- Active policy version per region, age, and pending rollout state.
- Time-quality posture per region (TRUSTED/DRIFTED/LOCAL_FALLBACK
  uptime).
- Retention SLO adherence (purges performed on time, no
  over-retention beyond grace).
- Legal-hold population & ageing.
- Audit chain integrity.
