# Phase 22-04 — Healthcare-Financial Risk Analysis

## F-01 — Autonomous reimbursement execution

**Risk:** A code path causes automatic claim execution without human
approval.
**Severity:** S2.
**Mitigation:** Documentation; default-off feature gates; human-approval
workflow; static check that no AI module imports `fin_*` write functions.
**Required action:** Coded enforcement.
**Owner:** Health-economics lead.

## F-02 — Double payment via retry

**Risk:** Adapter retry submits a claim twice; insurer pays twice.
**Severity:** S2.
**Mitigation:** Idempotency keys per claim; outbox-pattern de-duplication.
**Required action:** Verify on each adapter integration.
**Owner:** Phase 16 lead + Phase 22 lead.

## F-03 — Cross-tenant insurer routing

**Risk:** A response from insurer routes to the wrong tenant.
**Severity:** S2.
**Mitigation:** Strict claim id ↔ tenant mapping; inbound rejected if
mapping unknown.
**Required action:** Enforce in adapter inbound handler.
**Owner:** Phase 16 lead.

## F-04 — Reimbursement of clinically inappropriate care

**Risk:** Fraud/waste claim processed.
**Severity:** S2.
**Mitigation:** Validation rules; FWA flagger; human approval; audit.
**Required action:** Define policy thresholds; quarterly FWA review.
**Owner:** Health-economics lead + clinical lead.

## F-05 — Recoupment loss

**Risk:** Recoupment notification dropped; books go out of sync.
**Severity:** S2.
**Mitigation:** Inbound idempotency; reconciliation queue for
non-matching settlements.
**Required action:** Reconciliation dashboard.
**Owner:** Health-economics lead.

## F-06 — AI-flagged claim auto-blocked

**Risk:** A claim is auto-blocked because AI flagged it; operator never
sees it.
**Severity:** S3 (financial latency, not direct loss).
**Mitigation:** Flags do NOT block; reviewer must confirm.
**Required action:** Coded enforcement that flag does not gate execution.
**Owner:** Phase 22 lead.

## F-07 — Treasury-side compromise

**Risk:** Treasury credentials compromised; spoofed settlement.
**Severity:** S2.
**Mitigation:** mTLS, signing, idempotency.
**Required action:** Annual rotation; vendor security review.
**Owner:** Security officer.

## F-08 — Coverage verification spoof

**Risk:** A spoofed insurer coverage response incorrectly grants coverage.
**Severity:** S2 (affects patient finances, not clinical).
**Mitigation:** Signed responses; freshness check (TTL).
**Required action:** Implement freshness in inbound handler.
**Owner:** Phase 16 lead.

## F-09 — Pricing schedule misapplication

**Risk:** Old schedule applied to a current period.
**Severity:** S3.
**Mitigation:** Schedule period boundaries enforced; tests; quarterly
review.
**Required action:** Test coverage of period transitions.
**Owner:** Phase 22 lead.

## F-10 — Audit chain gap on financial event

**Risk:** A financial event written without chain row.
**Severity:** S1 (audit integrity).
**Mitigation:** Chain row commit in same transaction as financial row.
**Required action:** Coded enforcement; verifier covers `fin_*`.
**Owner:** Audit-integrity owner.

## Risk Summary

| Risk | S | L | Residual after action |
|------|--:|--:|----------------------|
| F-01 | S2 | L4 | S3/L5 |
| F-02 | S2 | L3 | S3/L4 |
| F-03 | S2 | L3 | S3/L4 |
| F-04 | S2 | L3 | S3/L3 |
| F-05 | S2 | L3 | S3/L4 |
| F-06 | S3 | L3 | S4/L4 |
| F-07 | S2 | L4 | S3/L5 |
| F-08 | S2 | L3 | S3/L4 |
| F-09 | S3 | L3 | S4/L4 |
| F-10 | S1 | L4 | S2/L5 |
