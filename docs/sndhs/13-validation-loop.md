# 13 — Continuous Validation Loop

## 13.1 Purpose

A clinical platform must continuously verify that its outputs match
ground truth and clinical intent. The validation loop is a
production-embedded feedback system that:

1. Samples real decisions (clinical, AI shadow, ABAC).
2. Routes them to clinical reviewers.
3. Captures structured judgments.
4. Injects feedback into rule registry, AI training, and policy
   bundles.
5. Closes the loop with measurable improvements.

The loop is mandatory; SLOs cover its throughput and reviewer SLAs.

## 13.2 Sampling engine

### 13.2.1 Strata

Sampling is stratified to avoid blind spots:

| Stratum | Examples | Min sample rate |
|---------|----------|-----------------|
| Outcome-impacting clinical decisions | triage acuity, sepsis bundle entry, MCOM-3 escalation | 100% S2+; ≥ 5% S1 |
| AI shadow outputs | every promoted advisory | 100% (logged); reviewer batch on stratified slice |
| ABAC denies on clinical routes | denied reads/writes | ≥ 5% |
| ABAC permits at break-glass | every break-glass | 100% |
| Sync conflicts (manual queue) | every entry | 100% |
| Random clinical sample (background) | encounters of any type | ≥ 0.5% |
| Adversarial / known-hard cases | curated by clinical board | 100% on update |
| User behavioral anomalies | bypass-pattern flagged users' actions | 100% within window |

### 13.2.2 Sampler

- Lives in `validation-engine`.
- Subscribes to event bus topics; applies sampling rules; writes
  `validation_sample` records with the relevant context (input
  features, decision, policy version, AI artefact hash if any,
  outcome if known).
- Uses reservoir sampling for the 0.5% random stream and stratum-aware
  weighted sampling for the rest.
- Idempotent on `(stream_kind, stream_id, sequence)`.

## 13.3 Clinical review workflow

### 13.3.1 Reviewer roles

- **Specialty reviewer** — clinician with the relevant board
  certification.
- **Senior reviewer** — adjudicator for disagreement.
- **Clinical board** — promotes/demotes AI advisories, accepts rule
  changes, signs off bundles.

### 13.3.2 Queue

- Each sample lands in a typed queue (e.g., `triage`, `sepsis`,
  `imaging`, `medication`).
- SLA per priority:
  - S0 (severe, recent) — ≤ 4 h.
  - S1 — ≤ 24 h.
  - S2 — ≤ 7 d.
  - Background — best-effort.
- Reviewers pull items; the system never assigns auto-ownership to a
  reviewer who took the original action (no self-review).

### 13.3.3 Review form (structured)

```
- Sample id
- Original decision summary (input features, output, policy_version)
- Reviewer judgment:
  - agree | disagree | not_evaluable
  - severity_of_disagreement: none | minor | moderate | severe | catastrophic
  - error_class: missed_diagnosis | wrong_acuity | wrong_disposition |
                 inappropriate_order | drug_safety | timing |
                 ABAC_too_strict | ABAC_too_lax | bypass | other
  - corrective_action_proposed: rule_update | training_data | UX_change |
                                policy_change | none
  - free_text_comments (max length capped; structured tags preferred)
```

Two reviewers required for severity ≥ moderate; a senior reviewer
adjudicates if they disagree.

### 13.3.4 Outcomes & metrics

- `validation_agreement_rate{class}` = agree / (agree + disagree).
- `validation_severity_distribution`.
- `validation_throughput_per_reviewer`.
- `validation_overdue` per SLA.

Per-class drift in agreement rate triggers a clinical board review.

## 13.4 Feedback injection

### 13.4.1 Rule updates

- Disagreements that propose a rule change land in
  `clinical-governance` as proposed bundle changes.
- Each proposal is accompanied by the supporting samples.
- The clinical board approves; policy authority bumps the bundle;
  rollout follows §11.1.4 (shadow → canary → staged).

### 13.4.2 AI training data

- AI training is **not** done on raw production data. The feedback
  loop produces a curated dataset:
  - Inputs are reproducible from canonical events at a given point in
    time.
  - Labels are reviewer-judged outcomes.
  - PHI removed via deterministic pseudonymisation per `13.4.5`.
- Training is performed in an isolated environment; resulting models
  go through shadow → canary like any other policy change.

### 13.4.3 UX changes

- Disagreements with `corrective_action_proposed = UX_change` are
  routed to the SNDHS clinical workspace team for design review.
- Tracked changes shipped through the regular release pipeline.

### 13.4.4 ABAC tuning

- "Too strict" / "too lax" findings feed the policy authority. ABAC
  changes go through replay tests against the last 30 days of audit
  before activation.

### 13.4.5 PHI handling in the loop

- Reviewer UI shows minimum-necessary clinical content. Identifiers
  are pseudonymised per the reviewer's purpose.
- Reviewers cannot export samples; copy/paste is suppressed; screen
  capture is logged.
- Free-text comments are stored with the sample and included in
  audit.

## 13.5 Throughput targets

- ≥ 99% of S0 samples reviewed within SLA.
- ≥ 95% of S1 within SLA.
- ≥ 90% of S2 within SLA.
- Backlog growth alarm: any class with > 7-day growth trend triggers
  staffing review.

## 13.6 Closed-loop verification

For every accepted policy change, the validation engine creates a
**verification cohort**:

- A pre-change baseline metric (e.g., median time to triage for
  acuity-2 patients).
- A post-change measurement window.
- Statistical comparison and reviewer-judged effect.
- Result fed back to clinical board; published in compliance dashboard.

Without observable improvement, changes are reverted.

## 13.7 Adversarial sample seeding

- Curated test cases (ground-truthed historical events with known
  challenging characteristics) are silently seeded into the live
  decision stream at low rate (< 0.1%) to keep human reviewers
  calibrated.
- Seeded samples never affect real patients; clinically equivalent
  synthetic stubs are used.
- Reviewers' performance on seeds is tracked privately and used for
  calibration / training, not punitive measures.

## 13.8 Connection to integrity & AI governance

- Reviewer findings of `bypass` link to `14-integrity.md` —
  systematic bypass is a behavioural finding even if the individual
  decision was correct.
- AI model performance findings link to `01-architecture.md` §1.6
  (drift detector + circuit breaker).
- Recurring patterns trigger a **systemic incident** review, not just
  a per-sample correction.
