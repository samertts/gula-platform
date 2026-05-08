# 14 — Operational Integrity System

## 14.1 Goal

Detect and respond to behaviour that bypasses controls, falsifies
records, or operates outside intended use. Integrity is enforced
*after* authentication and authorization — even authorised users can
misuse the system, and every system records actions that may not have
happened in reality.

Target metric: **bypass rate < 3%** (H3). Bypass rate is defined as
the proportion of clinical actions that the integrity engine flags as
having a `bypass_pattern` higher than the threshold within a rolling
window.

## 14.2 Core principle: reality vs system reconciliation

Every action recorded in the system is cross-checked against
independent reality probes whenever feasible:

| System claim | Reality probe |
|--------------|---------------|
| "Patient checked in at 09:14" | Badge reader at front desk; queue ticket scan; CCTV time-anchor (selective, audited) |
| "Vitals taken at 09:20" | Monitor device telemetry; ambulance vitals stream |
| "Drug administered at 09:35" | Smart pump telemetry; barcode-scanned dispense at pharmacy; nurse RFID at bedside |
| "Sample drawn at 09:40" | Lab specimen barcode + lab device ingest time |
| "Ambulance dispatched 09:00" | GPS track; dispatcher console keystrokes; CAD log |
| "Consent obtained" | E-signature device telemetry; biometric capture (where consented) |

Discrepancies are events on `gov.integrity.discrepancy.detected.v1`.
The classifier assigns:

- `phantom_action` — system says X happened, no reality evidence.
- `ghost_action` — reality evidence, no system record.
- `time_misalignment` — both exist but timestamps disagree beyond
  tolerance.
- `out_of_order` — reality and system disagree on sequence of
  related events.
- `unattributed_change` — record changed under a service principal
  during a window when no human action was expected.

## 14.3 Behavioural anomaly detection

For every workforce principal, a behaviour vector is maintained:

- Login geo / device / hours.
- Navigation entropy (variety of pages visited).
- Action mix (read vs write, by type).
- Override frequency by class.
- Co-signature partners (network analysis).
- Copy-paste density in free-text fields.
- Median dwell time per screen (too fast → automated tooling).
- Rate of accessing patients with no encounter relationship.
- Break-glass usage rate.

Anomalies are scored against a per-role baseline:

```
anomaly_score = w_geo * z_geo + w_overrides * z_overrides +
                w_dwell * (1/z_dwell) + w_strangers * z_strangers + ...
```

Score > τ_warn raises a soft warning (logged); score > τ_act enters
**restricted mode** (§14.5).

## 14.4 Bypass-pattern detection

Patterns that indicate systematic circumvention of controls:

- Repeated ESI downgrades against AI shadow / peer disagreement.
- "Click-through" patterns on safety prompts (e.g., dosage warnings)
  with sub-second dwell.
- Use of break-glass on patients without a documented care
  relationship after-hours.
- Selecting `data_quality=unknown` to skip required fields, then
  filling them seconds later in a separate edit.
- Setting `provisional_complete=true` then never finalising.
- Out-of-order documentation: closing notes before vitals exist.
- Routinely overriding interaction warnings.
- Unusual cluster of `Idempotency-Key` reuse across patients.

Each pattern has a detector. Patterns aggregate into a
`bypass_pattern_score` per principal per rolling window (24 h, 7 d, 30
d). Scores in higher windows decay slowly so that intermittent abuse
is detectable.

## 14.5 Forced recalibration (user restriction)

Restricted mode triggers:

- `bypass_pattern_score > τ_restrict` over any window.
- Confirmed phantom/ghost action (severity ≥ moderate).
- Anomaly score > τ_act sustained ≥ 60 min.

While restricted, the principal:

- Still authenticates and logs in.
- Reads continue (audited as usual).
- Writes require a co-signature by a peer of equal or higher role
  who must explicitly review the action.
- Break-glass is disabled.
- AI advisories (where promoted) are still visible.
- A banner is shown to the user explaining the state and the path to
  clear it.

Clearing restriction requires:

- Compliance interview AND supervisor sign-off, OR
- A defined cool-down with no further patterns triggering (≥ 30 days)
  AND clean reviewer feedback (`13-validation-loop.md`).

Restriction state is itself audited; clearing actions require dual
sign-off.

## 14.6 Enforcement logic

### 14.6.1 Pre-write hook

Each clinical write passes through an integrity hook (gateway-side):

```
if principal.restricted and not co_signature_present:
    deny POLICY_DENIED reason="restricted_co_signature_required"
if principal.recent_bypass_score > τ_pause:
    require_step_up_webauthn()
if action.class in {"override_warning"}:
    require_reason_code from canonical list
    log to integrity engine with severity=tracked
```

### 14.6.2 Post-write reconciliation

A reconciler subscribes to writes and reality probes. Discrepancies
generate events; severity drives the response (alert, restriction,
audit annotation, manual review).

### 14.6.3 Aggregation & escalation

- Per-facility integrity dashboard.
- Top-N principals by bypass score (privacy-preserving — only
  pseudonymous IDs to ops; compliance can de-pseudonymise on
  authorised investigation).
- Pattern epidemics (a sudden cluster of similar bypass patterns
  across many users) trigger a systemic review — likely a UX or
  policy issue, not individual misuse.

## 14.7 Anti-tampering controls

- Reality probes are themselves device-attested; their telemetry is
  signed.
- The integrity engine's state is append-only and hash-chained
  similarly to the audit ledger.
- A separate operational team manages the integrity engine; the
  engine's writes go to a bus topic readable only by compliance and
  ministry oversight.
- Configuration of detectors is part of the policy bundle; tuning is
  governed and audited.

## 14.8 Privacy & due process

- Integrity findings are not visible to peers; only to compliance
  and to the affected user (with the structured reason).
- All restrictions are time-boxed and have an explicit clearance
  path.
- Statistical anomalies alone never justify disciplinary action;
  they trigger investigation, not punishment.
- An appeals workflow allows users to dispute findings; the appeal is
  reviewed by an independent panel.

## 14.9 Metrics & SLOs

- `integrity_discrepancy_rate{class}`.
- `integrity_phantom_actions_total`.
- `integrity_ghost_actions_total`.
- `integrity_bypass_score_p95`.
- `integrity_restricted_users_active`.
- `integrity_resolution_latency_seconds_p95`.

SLO: median resolution of moderate findings ≤ 24 h; severe findings
≤ 1 h; critical (patient-safety) ≤ 15 min.

## 14.10 Connection to other layers

- ABAC (§3.2.3): `context.bypass_pattern_score` is an attribute used
  in ABAC `forbid` rules.
- Validation loop (§13): integrity findings feed structured reviewer
  judgement; reviewer findings feed integrity baselines.
- Failure scenarios (§9.7): the human-misuse scenario calls out
  integrity engine actions.
- Policy authority (§11): detector parameters and thresholds live in
  the policy bundle and are versioned.
