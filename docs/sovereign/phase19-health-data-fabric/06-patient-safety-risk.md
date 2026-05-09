# Phase 19-06 — Patient-Safety Risk Analysis

Patient-safety risks specific to the health data fabric. Cross-phase risks
are in `INTEGRATION_RISK_ANALYSIS.md`.

## P-01 — Wrong-patient merge (cross-tenant)

**Risk:** Two distinct people are merged into one canonical id.
**Severity:** S1.
**Mitigation:** Auto-link rules narrow (deterministic + secondary
attributes); two-person rule for cross-province; reviewer queue.
**Required action:** Implement reviewer workflow before any production
auto-link.
**Owner:** Health Data Fabric architect.

## P-02 — Wrong-patient unmerge

**Risk:** A correct link is reversed, splitting one person's record into
two.
**Severity:** S2.
**Mitigation:** Unlink requires explicit reason and reviewer; reversal
audited.
**Required action:** Reviewer training; quarterly review of unlinks.
**Owner:** Clinical safety lead.

## P-03 — Cross-tenant identifier leak

**Risk:** Reviewer or operator sees national_id from another tenant in
plaintext.
**Severity:** S2.
**Mitigation:** Reviewer UI redacts; logs redact; HMAC for matching.
**Required action:** Review reviewer UI before launch; privacy sign-off.
**Owner:** Privacy officer.

## P-04 — Longitudinal view blends across tenants without consent

**Risk:** Cross-tenant read returns data without consent scope.
**Severity:** S2.
**Mitigation:** Consent token required; default scope is local tenant only.
**Required action:** Consent token system implementation.
**Owner:** Phase 19 lead.

## P-05 — Drifted code → wrong clinical interpretation

**Risk:** Vocabulary version drift; result interpreted with stale meaning.
**Severity:** S2.
**Mitigation:** Terminology-governance committee; drift detection;
fail-closed on unmapped.
**Required action:** Drift monitor; quarterly review.
**Owner:** Terminology-governance lead.

## P-06 — Reconciliation event lost

**Risk:** A reconciliation event is written to the queue but not the audit
chain.
**Severity:** S2.
**Mitigation:** Audit chain participation mandatory; audit failure rejects
the reconciliation.
**Required action:** Coded enforcement; do not allow reconciliation commit
without chain-row commit (single transaction).
**Owner:** Audit-integrity owner.

## P-07 — Auto-merge during DR cutover

**Risk:** During DR cutover, an auto-link rule fires twice (Tier-1 then
Tier-2), producing duplicate events.
**Severity:** S2.
**Mitigation:** Auto-link is idempotent on `(constituent_ids, rule, hash)`.
**Required action:** Idempotency key on event commit.
**Owner:** Phase 19 lead.

## P-08 — Reviewer fatigue → low-quality decisions

**Risk:** Volume overwhelms reviewers; rubber-stamping.
**Severity:** S2.
**Mitigation:** Queue depth alerts; SLA tracking; minimum review time
heuristic; sampling-based QA.
**Required action:** Queue depth monitor; quarterly QA sampling.
**Owner:** Clinical safety lead.

## P-09 — Edge-offline auto-link drift

**Risk:** Edge sites perform local auto-links during offline mode; on
reconnect, the canonical id space conflicts.
**Severity:** S2.
**Mitigation:** Offline auto-link prohibited; only `proposed` events
created; reconciliation deferred.
**Required action:** Coded enforcement on edge.
**Owner:** Crisis continuity lead + Phase 19 lead.

## P-10 — Wrong-canonical-id propagation to peers

**Risk:** A wrong canonical id is shipped via adapter to MOH or NHIS; a
reversal does not propagate the correction.
**Severity:** S2.
**Mitigation:** Adapter outbound includes canonical id version; on unlink,
adapter outbound MUST send a corrective event.
**Required action:** Outbound corrective protocol; rehearse.
**Owner:** Phase 16 + Phase 19 leads.

## Risk Summary

| Risk | S | L | Residual after action |
|------|--:|--:|----------------------|
| P-01 | S1 | L3 | S2/L4 |
| P-02 | S2 | L3 | S3/L4 |
| P-03 | S2 | L4 | S3/L5 |
| P-04 | S2 | L3 | S3/L4 |
| P-05 | S2 | L3 | S3/L4 |
| P-06 | S2 | L4 | S3/L5 |
| P-07 | S2 | L4 | S3/L5 |
| P-08 | S2 | L3 | S3/L4 |
| P-09 | S2 | L3 | S3/L4 |
| P-10 | S2 | L3 | S3/L4 |
