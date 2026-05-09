# Phase 18-06 — Unresolved Governance Risk Register

This register lists **governance-specific** risks. Cross-phase risks are in
[`../INTEGRATION_RISK_ANALYSIS.md`](../INTEGRATION_RISK_ANALYSIS.md) and
[`../REMAINING_NATIONAL_RISKS.md`](../REMAINING_NATIONAL_RISKS.md).

## G-01 — Documented-only legal hold

**Risk:** Legal-hold policy exists only as documentation. A retention purge
job (when added) could ignore holds.
**Severity:** S1 (legal exposure if data is purged that should have been
held).
**Mitigation today:** No retention purge runs in production.
**Required action:** Implement legal-hold registry **before** any purge
process is enabled.
**Owner:** Governance lead.

## G-02 — Regulator over-broad query authority

**Risk:** A regulator account is granted broad read; no minimum-necessary
enforcement.
**Severity:** S2.
**Mitigation:** PB-4 / PB-5 separations; audit of regulator session.
**Required action:** Define minimum-necessary fields per regulator role;
enforce at adapter or route.
**Owner:** Security officer.

## G-03 — Documented-only AI governance

**Risk:** AI governance is documented (Phase 21 deferred). A new clinical AI
could ship without IRB-AI sign-off.
**Severity:** S2.
**Mitigation:** Existing feature flags; release review.
**Required action:** Capability registry coded; release gate "no AI without
registry".
**Owner:** Clinical AI owner + IRB-AI.

## G-04 — Audit chain continuity gap during DR cutover

**Risk:** Without coded chain-merge protocol, a DR cutover could produce a
chain segment that's correct but not auditable as continuous.
**Severity:** S2.
**Mitigation:** RB-09 documents the manual procedure.
**Required action:** Code the chain-merge marker; rehearse annually.
**Owner:** Audit-integrity owner.

## G-05 — Reconciliation audit lineage

**Risk:** Phase 19 reconciliation events need chain-friendly audit format;
defined but not coded.
**Severity:** S2.
**Mitigation:** No automatic merge in production today.
**Required action:** Implement reconciliation audit format before enabling
auto-merge.
**Owner:** Health Data Fabric architect.

## G-06 — Role-separation drift

**Risk:** Custom roles created by an operator could violate PB-5 (no role
unions clinical+audit).
**Severity:** S2.
**Mitigation:** Existing RBAC matrix; review at access-policy quarterly.
**Required action:** Implement an "incompatible-roles" matrix; enforce at
role assignment.
**Owner:** Security officer.

## G-07 — Sovereign KMS dependency

**Risk:** KMS unreachability degrades critical services (RB-10).
**Severity:** S2.
**Mitigation:** RB-10 documented.
**Required action:** Test rotation rehearsal annually; document local cache
TTL with regulator-acceptable bound.
**Owner:** Security officer.

## G-08 — Cross-border data residency

**Risk:** Operator chooses a backup destination outside sovereign
jurisdiction.
**Severity:** S2 to S1 depending on jurisdiction.
**Mitigation:** Documentation only.
**Required action:** Encode a deployment-policy file enforcing residency;
fail startup if violated.
**Owner:** Operations chief.

## G-09 — Compliance bypass via "exception"

**Risk:** Operational exceptions (e.g., emergency manual override) become
durable bypasses.
**Severity:** S2.
**Mitigation:** Every exception is itself audited; quarterly review.
**Required action:** TTL on exceptions; auto-revert.
**Owner:** Governance lead.

## G-10 — Standards drift

**Risk:** Standards (FHIR, ICD, LOINC) update faster than mappings refresh.
**Severity:** S3.
**Mitigation:** Quarterly standards-mapping review.
**Required action:** Subscribe to vendor change feeds; auto-flag mapping
drift.
**Owner:** Terminology-governance lead.

## Tracking Discipline

- Each risk is reviewed quarterly.
- Closure requires: implemented control, signed verification, removal from
  this register (not editing it post-hoc).
- Severity changes require sign-off.
- Risks are assigned an owner; an unowned risk is itself a defect.

The register is the input to the deployment checklist's governance items.
