# Remaining National-Scale Risks (Ranked)

This is the **executive residual register**. It consolidates the
post-mitigation risks across phases 16–25 and ranks them by severity ×
likelihood for sovereign-scale deployment.

Use this register together with:

- [`INTEGRATION_RISK_ANALYSIS.md`](./INTEGRATION_RISK_ANALYSIS.md) for the
  cross-phase analysis
- per-phase risk files for detail
- [`NATIONAL_DEPLOYMENT_CHECKLIST.md`](./NATIONAL_DEPLOYMENT_CHECKLIST.md)
  for go/no-go gates

Severity 1 (catastrophic) → 5 (negligible). Likelihood 1 (frequent) → 5
(rare). Items are listed worst-residual first.

---

## Tier 1 — Highest residual exposure (treat as program-critical)

### N-01 — Cross-tenant identity bleed via reconciliation
- **Source:** Phase 16 + Phase 19
- **Residual:** S2 / L4
- **Why open:** Reconciliation governance is documented; coded enforcement
  awaits the implementation of the `reconciliation_events` table, the
  reviewer queue, and the chain-row commit guarantee.
- **Pre-deployment requirement:** Phase 19 reconciliation enforcement
  coded and exercised end-to-end before any cross-tenant patient
  reconciliation in production.

### N-02 — Audit chain corruption during DR cutover
- **Source:** Phase 17 + Phase 23
- **Residual:** S2 / L5
- **Why open:** Chain-merge protocol documented (RB-09); coded marker +
  rehearsed cutover not annual yet.
- **Pre-deployment requirement:** First successful Tier-1 → Tier-2 drill
  with audit-chain verification green.

### N-03 — Sovereign KMS dependency (key custody loss)
- **Source:** Phase 17 + Phase 24
- **Residual:** S2 / L4
- **Why open:** Hard fail on weak/missing secrets exists; rotation
  calendar + rehearsed re-encryption not yet codified.
- **Pre-deployment requirement:** Documented rotation calendar + rehearsed
  procedure on staging.

### N-04 — Silent AI clinical-state mutation
- **Source:** Phase 21
- **Residual:** S2 / L5
- **Why open:** AI authority class enforcement is documented; static check
  forbidding AI modules from writing to clinical tables is pending.
- **Pre-deployment requirement:** Static check in CI; capability registry
  active before any new AI capability ships.

### N-05 — Sandbox escape (clinical AI)
- **Source:** Phase 21
- **Residual:** S2 / L5
- **Why open:** Sandbox runtime not yet selected.
- **Pre-deployment requirement:** Sandbox runtime selected and
  penetration-tested before any non-trivial clinical AI ships.

### N-06 — Vendor model service compromise
- **Source:** Phase 21
- **Residual:** S2 / L5
- **Why open:** mTLS + signed responses + restricted egress documented;
  vendor security review variable.
- **Pre-deployment requirement:** Per-vendor security review on file;
  rotation calendar enforced.

### N-07 — Generative-AI hallucination in clinical context
- **Source:** Phase 21
- **Residual:** S2 / L4
- **Why open:** Generative capabilities require additional IRB-AI review;
  no such capability is currently in production.
- **Pre-deployment requirement:** No generative AI in clinical pathway
  without IRB-AI extra-review sign-off and fail-closed verification.

### N-08 — Cross-border data residency drift
- **Source:** Phase 24
- **Residual:** S2 / L4 (S1 / L4 if jurisdiction is sensitive)
- **Why open:** Documentation only; deployment-policy file enforcement
  pending.
- **Pre-deployment requirement:** Residency policy file enforced at
  startup; backups validated in jurisdiction.

### N-09 — Legal-hold unimplemented (with future retention purges)
- **Source:** Phase 18 + Phase 24
- **Residual:** S2 / L4 (latent — exposure activates if a purge job is
  introduced)
- **Why open:** No purge in production today; legal-hold registry not
  coded.
- **Pre-deployment requirement:** Implement legal-hold registry **before**
  any purge process is enabled.

### N-10 — Audit chain gap on financial event
- **Source:** Phase 22
- **Residual:** S2 / L5
- **Why open:** Coded enforcement that financial commit and chain row are
  same-transaction is required when Financial Engine Phase B+ ships.
- **Pre-deployment requirement:** Same-transaction guarantee verified
  before Financial Engine activation.

---

## Tier 2 — Material residual exposure (treat as quarterly review items)

### N-11 — Adapter privilege drift
- **Source:** Phase 16
- **Residual:** S3 / L3
- **Mitigation status:** Manifest review + static checks documented; CI
  enforcement of "no `routes/` import inside `interoperability/`" pending.

### N-12 — Reviewer fatigue → low-quality reconciliation decisions
- **Source:** Phase 19
- **Residual:** S3 / L4
- **Mitigation status:** Queue-depth alerts + sampling QA documented;
  unimplemented.

### N-13 — Terminology drift causes wrong clinical interpretation
- **Source:** Phase 19
- **Residual:** S3 / L4
- **Mitigation status:** Drift monitor and quarterly review documented;
  unimplemented.

### N-14 — Edge-offline auto-link drift
- **Source:** Phase 19 + Phase 23
- **Residual:** S3 / L4
- **Mitigation status:** Edge auto-link prohibition documented; coded
  enforcement on edge agent pending.

### N-15 — Wrong-canonical-id propagation to peers
- **Source:** Phase 16 + Phase 19
- **Residual:** S3 / L4
- **Mitigation status:** Outbound corrective protocol documented;
  rehearsal pending.

### N-16 — Re-identification through combined exports
- **Source:** Phase 20 + Phase 25
- **Residual:** S3 / L4
- **Mitigation status:** Per-consumer review documented; coded budget
  pending.

### N-17 — Capability creep (interop + AI + ecosystem)
- **Source:** Phase 16, 21, 25
- **Residual:** S3 / L3
- **Mitigation status:** Quarterly governance review documented;
  capability-usage diff tooling pending.

### N-18 — Migration drift on a national fleet
- **Source:** Phase 17
- **Residual:** S3 / L4
- **Mitigation status:** CI migration-gate green; per-tenant fleet
  dashboard pending.

### N-19 — Provincial over-reliance on central platform
- **Source:** Phase 17 + Phase 23
- **Residual:** S3 / L4
- **Mitigation status:** Edge agent + offline survivability documented;
  72h drill cadence pending in some sites.

### N-20 — Telecom / payment / NHIS adapter cascade
- **Source:** Phase 16 + Phase 17 + Phase 22
- **Residual:** S3 / L4
- **Mitigation status:** Per-adapter circuit + bulkhead documented;
  national-scale chaos drill pending.

### N-21 — Bias / fairness regression in clinical AI
- **Source:** Phase 21
- **Residual:** S3 / L3
- **Mitigation status:** Per-release bias review documented; ongoing
  monitoring dashboard pending.

### N-22 — Regulator over-broad query authority
- **Source:** Phase 18 + Phase 24
- **Residual:** S3 / L4
- **Mitigation status:** Role separation documented; minimum-necessary
  enforcement pending.

### N-23 — Vendor data exfiltration via volumetric pulls
- **Source:** Phase 25
- **Residual:** S3 / L4
- **Mitigation status:** Per-vendor rate limit documented; volumetric
  alerting pending.

### N-24 — Compliance bypass via "exception" persistence
- **Source:** Phase 18 + Phase 24
- **Residual:** S3 / L4
- **Mitigation status:** Exception-TTL discipline documented;
  auto-revert tooling pending.

### N-25 — Sovereign cloud SLA insufficient for clinical RTO
- **Source:** Phase 17 + Phase 24
- **Residual:** S3 / L3
- **Mitigation status:** Pre-deployment SLA review documented;
  contractual posture varies per deployment.

---

## Tier 3 — Lower residual (treat as annual review items)

### N-26 — Standards drift (FHIR / ICD / LOINC)
- Phase 19. Residual S3 / L3.

### N-27 — Vendor abandonment leaves stale credentials
- Phase 25. Residual S4 / L4.

### N-28 — Pricing schedule misapplication
- Phase 22. Residual S4 / L4.

### N-29 — Snapshot exfiltration (AI feature snapshots)
- Phase 21. Residual S3 / L5.

### N-30 — AI rationale-only invocations (insufficient evidence lineage)
- Phase 21. Residual S3 / L4. Specific to capabilities whose explanation
  style is rule-based.

---

## Pre-Deployment Prioritisation (recommended)

For sovereign deployment, the following Tier-1 items MUST be closed
(coded + exercised) before activation:

- N-01 — reconciliation enforcement
- N-02 — audit chain DR drill
- N-03 — KMS rotation rehearsal
- N-04 — AI no-write static enforcement
- N-08 — cross-border residency enforcement
- N-09 — legal-hold registry (if any retention purge is contemplated)

Tier-2 items are accepted with quarterly review and mitigation-on-hand.

Tier-3 items are accepted with annual review.

---

## Owners & Cadence

| Tier | Cadence | Owner |
|------|---------|-------|
| 1 | Continuous + per-release gate | Program owner + Security officer |
| 2 | Quarterly review | Domain-phase owners |
| 3 | Annual review | Domain-phase owners |

The register is the authoritative residual-risk view at sovereign
deployment time. Closures and additions are themselves audit-traceable
(this file is committed; commit history is the closure log).
