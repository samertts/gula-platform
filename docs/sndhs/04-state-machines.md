# 04 — State Machines

All state machines are specified in TLA+ under `formal/specs/` and
model-checked in CI. The transition tables below are normative; the TLA+
specs are the authoritative formalisation. Any drift between the two is
a release blocker.

## 4.1 Referral lifecycle (closed-loop)

States:

`DRAFT` → `SUBMITTED` → `RECEIVED` → `TRIAGED` → `ACCEPTED` →
`SCHEDULED` → `IN_TRANSIT` → `ARRIVED` → `IN_CARE` → `OUTCOME_RECORDED`
→ `FEEDBACK_DELIVERED` → `CLOSED`

Side branches: `REJECTED`, `CANCELLED`, `LOST_TO_FOLLOWUP`, `EXPIRED`.

### Transition table

| From → To | Trigger | Actor role | SLA | Notes |
|-----------|---------|------------|-----|-------|
| DRAFT → SUBMITTED | submit | clinician | — | Validates payload + attachments |
| SUBMITTED → RECEIVED | gateway delivery ack | system | ≤ 30 s | Auto |
| RECEIVED → TRIAGED | receiving facility triage | clinician | priority-class SLA | P0: 5 min, P1: 30 min, P2: 4 h |
| TRIAGED → ACCEPTED | accept | clinician | — | |
| TRIAGED → REJECTED | reject(reason) | clinician | — | Reason mandatory; emits to origin |
| ACCEPTED → SCHEDULED | schedule | scheduler | priority-class SLA | |
| SCHEDULED → IN_TRANSIT | patient en-route | patient/system | — | |
| SCHEDULED → CANCELLED | cancel(reason) | clinician/patient | — | |
| IN_TRANSIT → ARRIVED | check-in | front desk | — | |
| ARRIVED → IN_CARE | encounter opened | clinician | ≤ 60 min | |
| IN_CARE → OUTCOME_RECORDED | document outcome | clinician | priority-class SLA | |
| OUTCOME_RECORDED → FEEDBACK_DELIVERED | system fan-out | system | ≤ 5 min | Closes loop |
| FEEDBACK_DELIVERED → CLOSED | acknowledged at origin | system / clinician | ≤ 7 d | Auto on read or after 7 d |
| any → EXPIRED | SLA breach + grace | system | — | Audited; alarms an MoH dashboard |
| any pre-IN_CARE → LOST_TO_FOLLOWUP | no-show + outreach failures | system | — | After three contact attempts |

### Invalid states (verified by TLA+)

- `RECEIVED → IN_CARE` is forbidden (must go through ACCEPTED + SCHEDULED).
- `OUTCOME_RECORDED → ACCEPTED` is forbidden (no rewinding the loop).
- `CLOSED` is terminal.
- `REJECTED` is terminal except via `re-submit` which creates a new
  referral entity referencing `parent_referral_id`.
- A referral cannot leave `DRAFT` without a non-null `clinical_summary`.

### Enforcement rules

- DB trigger checks `(from_state, to_state)` against
  `policy_transition_rule`.
- API layer rejects with `STATE_INVALID_TRANSITION`.
- The decision-stabilizer applies a 60 s lock window after each
  acceptance/rejection to prevent oscillation between ACCEPTED ↔ REJECTED.
- Closing the loop (FEEDBACK_DELIVERED) is mandatory — open referrals
  are audited weekly; chronic offenders escalated to facility
  governance.

### TLA+ specification (excerpt)

```
---- MODULE Referral ----
EXTENDS Naturals, Sequences, FiniteSets

CONSTANTS Referrals

VARIABLES state, history

States == { "DRAFT","SUBMITTED","RECEIVED","TRIAGED","ACCEPTED",
            "SCHEDULED","IN_TRANSIT","ARRIVED","IN_CARE",
            "OUTCOME_RECORDED","FEEDBACK_DELIVERED","CLOSED",
            "REJECTED","CANCELLED","LOST_TO_FOLLOWUP","EXPIRED" }

Init == /\ state   = [ r \in Referrals |-> "DRAFT" ]
        /\ history = [ r \in Referrals |-> << >> ]

Allowed(s, t) == \/ s = "DRAFT"            /\ t \in {"SUBMITTED","CANCELLED"}
                 \/ s = "SUBMITTED"        /\ t \in {"RECEIVED","CANCELLED","EXPIRED"}
                 \/ s = "RECEIVED"         /\ t \in {"TRIAGED","CANCELLED","EXPIRED"}
                 \/ s = "TRIAGED"          /\ t \in {"ACCEPTED","REJECTED","CANCELLED","EXPIRED"}
                 \/ s = "ACCEPTED"         /\ t \in {"SCHEDULED","CANCELLED","EXPIRED"}
                 \/ s = "SCHEDULED"        /\ t \in {"IN_TRANSIT","CANCELLED","LOST_TO_FOLLOWUP","EXPIRED"}
                 \/ s = "IN_TRANSIT"       /\ t \in {"ARRIVED","LOST_TO_FOLLOWUP"}
                 \/ s = "ARRIVED"          /\ t \in {"IN_CARE"}
                 \/ s = "IN_CARE"          /\ t \in {"OUTCOME_RECORDED"}
                 \/ s = "OUTCOME_RECORDED" /\ t \in {"FEEDBACK_DELIVERED"}
                 \/ s = "FEEDBACK_DELIVERED" /\ t \in {"CLOSED"}

Step(r, t) == /\ Allowed(state[r], t)
              /\ state'   = [state EXCEPT ![r] = t]
              /\ history' = [history EXCEPT ![r] = Append(@, t)]

Spec == Init /\ [][ \E r \in Referrals, t \in States: Step(r, t) ]_<<state, history>>

Safety  == \A r \in Referrals: state[r] \in States
NoLoopSkip == \A r \in Referrals:
    Len(history[r]) > 0 =>
      ~( "OUTCOME_RECORDED" \in {history[r][i] : i \in 1..Len(history[r])}
         /\ \E i \in 1..(Len(history[r])-1):
              history[r][i] = "OUTCOME_RECORDED" /\ history[r][i+1] = "ACCEPTED" )
====
```

CI runs `tlc Referral.tla -workers auto` and asserts `Safety` and
`NoLoopSkip` hold for `|Referrals| ≤ 4`.

## 4.2 Critical encounter lifecycle

States:

`OPENED` → `RESUSCITATION` (optional) → `STABILISATION` →
`DEFINITIVE_CARE` → `OBSERVATION` → `DISPOSITION_DECIDED` →
`HANDOVER` → `DISCHARGED` | `ADMITTED` | `TRANSFERRED` | `EXPIRED`.

Critical encounters carry `is_critical = true` and bind to a clinical
bundle (e.g., STEMI, sepsis, stroke). The bundle is named in the
encounter record and **immutable** for that encounter once bound.

### Transition table

| From → To | Trigger | Notes |
|-----------|---------|-------|
| OPENED → RESUSCITATION | acuity ≤ 1 OR explicit resus call | Two-person rule |
| OPENED → STABILISATION | acuity = 2 / 3 | |
| RESUSCITATION → STABILISATION | ROSC / sustained vitals | |
| STABILISATION → DEFINITIVE_CARE | bundle entered | |
| DEFINITIVE_CARE → OBSERVATION | bundle goal met | |
| OBSERVATION → DISPOSITION_DECIDED | clinician decision | |
| DISPOSITION_DECIDED → HANDOVER | accepting team confirmed | |
| HANDOVER → DISCHARGED \| ADMITTED \| TRANSFERRED | outcome | |
| any → EXPIRED | death | Special audit + coroner notification |

### Invariants (TLA+ + DB triggers)

- `EXPIRED` is terminal.
- An encounter with `is_critical = true` cannot leave `OPENED` without a
  bound `bundle_id`.
- `DISPOSITION_DECIDED` cannot occur unless `OBSERVATION` was entered or
  acuity was 1 with a directly-observed disposition path (e.g.,
  cath-lab activation).
- An encounter cannot have more than one active resuscitation
  declaration in `OPEN` state.

### Hysteresis

- Acuity flip (e.g., ESI-2 → ESI-3) requires sustained signal change for
  10 minutes OR a clinician-attested override. See decision-stabilizer
  policy `acuity_flip`.
- Disposition flip-flops: max 2 in 30 minutes; third triggers human
  escalation (`OSCILLATING`).

## 4.3 MCOM (Mass Casualty Operating Mode)

Levels:

- **MCOM-1 — Normal**: routine ops; full feature surface.
- **MCOM-2 — Heightened**: surge expected. Non-urgent referrals
  deprioritised; analytics throttled.
- **MCOM-3 — Mass casualty**: triage-pathway switches from ESI to
  START/SALT field triage. Ambulance routing reroutes to designated
  hubs. Non-clinical UIs go read-only. AI advisories suspended.
- **MCOM-4 — Catastrophic / national emergency**: paper-fallback
  protocols pre-printed and pushed; only safety-critical write paths
  remain (vitals, declared death, transfers). National federation
  switches to async-only (RSNs operate fully autonomously).

### Transition rules

| From → To | Trigger | Authorisation | Side effects |
|-----------|---------|---------------|--------------|
| 1 → 2 | regional ED occupancy > 90% for 15 min OR manual | regional health authority | Throttle background, page surge team |
| 2 → 3 | declared mass-casualty incident OR ED occupancy > 110% | regional director + ministry duty officer | Switch triage protocol, lock non-clinical writes, broadcast to all clinicians |
| 3 → 4 | ministry declaration | minister + duty cabinet | Activate paper fallback, sever non-essential federation, freeze AI |
| 4 → 3 | de-escalation | minister | Restore federation gradually |
| 3 → 2 | regional director + ministry duty officer | Restore non-clinical writes | |
| 2 → 1 | regional health authority | Resume normal | |

Down-transitions cannot skip levels. Up-transitions can (e.g., 1 → 3
during a confirmed catastrophic event), but require the top-level
authoriser of the target level + audit.

### MCOM enforcement points

- `policy-binder` consults the active MCOM level and selects a different
  policy bundle (`MCOM3-bundle-2025-Q1` etc.).
- Gateway adds a `forbid` rule for routes flagged
  `mcom_max_level` < current level.
- Clinical UIs receive a real-time push and re-render with the new
  level's affordances.
- AI governance forces the AI circuit open for `level ≥ 3`.

### Decision stabilization

MCOM levels are themselves a `decision_class`. Hysteresis prevents rapid
flapping: each up-transition sets a 30-minute `T_lock`; each
down-transition sets 60 minutes. Flapping detection: more than two
transitions in 24 h escalates to the National Health Operations Centre.

## 4.4 Cross-machine invariants

- An encounter referenced by a referral must reach at least
  `OBSERVATION` before the referral can be `OUTCOME_RECORDED`.
- A patient declared `DECEASED` in MPI invalidates all open referrals
  and encounters automatically (transition to `EXPIRED`/`CANCELLED`,
  with audit; legal hold preserves the records).
- During `MCOM ≥ 3`, no referral can transition to `DRAFT → SUBMITTED`
  unless `priority_class = P0` (mass-casualty cross-region transfer).

## 4.5 Verification matrix

| Spec | Property | Tool | Result gate |
|------|----------|------|-------------|
| Referral.tla | safety, no-loop-skip, terminal closure | TLC | exhaustive ≤ 4 entities |
| Encounter.tla | safety, single-resus, bundle-bound | TLC | exhaustive ≤ 3 |
| MCOM.tla | level monotonicity, no skip-down, freeze on AI under L≥3 | TLC | exhaustive |
| Stabilizer.tla | bounded oscillation, lock-window enforced | TLC | exhaustive |
| Sync.tla | eventual ownership, no double-write | TLC | bounded model |

CI fails the build on any new transition not present in the
corresponding TLA+ allowed-transitions set.
