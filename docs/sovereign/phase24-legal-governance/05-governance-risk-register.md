# Phase 24-05 — Unresolved Governance-Risk Register

This is the **Phase 24 view** of governance risks. Cross-phase residual
risks live in `../REMAINING_NATIONAL_RISKS.md`. Phase 18's governance
register is in `../phase18-regulatory-governance/06-governance-risk-register.md`;
this register focuses on legal / sovereignty / consent surfaces specific
to Phase 24.

## L-01 — Cross-border data residency drift

**Risk:** Backups land cross-border due to operational misconfiguration.
**Severity:** S1 (sovereignty breach).
**Mitigation:** Documentation; quarterly residency audit.
**Required action:** Codify residency in deployment policy; fail startup
on violation.
**Owner:** Operations chief.

## L-02 — Consent-revocation propagation gap

**Risk:** Consent revoked but downstream peers continue to receive data.
**Severity:** S2.
**Mitigation:** Adapter contracts include revocation handling; inbound
consent revocation triggers adapter shutoff for the subject.
**Required action:** Coded propagation.
**Owner:** Phase 19 + Phase 24 leads.

## L-03 — Legal-hold unimplemented

**Risk:** Hold policy exists; no enforcement.
**Severity:** S1 (legal exposure).
**Mitigation:** No retention purge runs in production today.
**Required action:** Implement legal-hold registry **before** any purge.
**Owner:** Governance lead.

## L-04 — Erasure vs. clinical floor conflict

**Risk:** Patient invokes erasure; clinical floor mandates retention.
**Severity:** S2 (depends on jurisdiction).
**Mitigation:** Policy resolution by regulator; redaction approach where
permitted.
**Required action:** Document redaction approach; legal review.
**Owner:** Legal counsel + privacy officer.

## L-05 — Regulator over-broad warrant

**Risk:** Warrant is broader than minimum-necessary.
**Severity:** S2.
**Mitigation:** Warrant scope reviewed by counsel; access scoped at
adapter or query layer.
**Required action:** Document warrant-scope review process.
**Owner:** Legal counsel.

## L-06 — Adapter contract drift

**Risk:** Peer changes its side; our manifest no longer matches contract.
**Severity:** S2.
**Mitigation:** Annual recertification of each adapter (Phase 16).
**Required action:** Contract change monitoring.
**Owner:** IRB-Interop.

## L-07 — Cross-jurisdiction proceedings

**Risk:** Court order from foreign jurisdiction conflicts with sovereignty.
**Severity:** S2.
**Mitigation:** Counsel-orchestrated response; data sovereignty supersedes
unless dual-authorised.
**Required action:** Jurisdictional protocol document.
**Owner:** Legal counsel.

## L-08 — Patient identity merge under hold

**Risk:** A patient under legal hold has a reconciliation event.
**Severity:** S2.
**Mitigation:** Reconciliation governance flags held subjects; merges
require legal review.
**Required action:** Hold flag visible in reviewer queue.
**Owner:** Phase 19 lead.

## L-09 — Operator account misuse

**Risk:** Operator account used for personal purposes (e.g., looking up a
relative).
**Severity:** S2 (privacy violation).
**Mitigation:** All access audited; operator agreements; periodic
access-pattern review.
**Required action:** Suspicious-access pattern detection (advisory).
**Owner:** Security officer + privacy officer.

## L-10 — Sovereign cloud SLA insufficient

**Risk:** Sovereign cloud underlying the deployment cannot meet RTO.
**Severity:** S2.
**Mitigation:** Contractual SLA; on-prem fallback if available.
**Required action:** Pre-deployment SLA review.
**Owner:** Operations chief.

## Tracking Discipline

- Closures require: artefact (policy, code, runbook, signed sign-off).
- Severity changes signed.
- An unowned risk is itself a defect.
- Quarterly review.
