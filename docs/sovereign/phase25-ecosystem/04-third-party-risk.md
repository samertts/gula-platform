# Phase 25-04 — Third-Party Risk Analysis

## E-01 — Third-party credential compromise

**Risk:** A vendor's credentials stolen.
**Severity:** S2.
**Mitigation:** Per-vendor credential isolation; rotation; audit on
suspicious patterns.
**Required action:** Per-vendor rotation calendar.
**Owner:** Security officer.

## E-02 — Vendor unauthorised capability use

**Risk:** Vendor calls operations beyond manifest.
**Severity:** S2.
**Mitigation:** Capability whitelist; fail-closed; audit row.
**Required action:** Coded enforcement (Phase 16 base).
**Owner:** Phase 16 lead.

## E-03 — Vendor data exfiltration

**Risk:** Vendor pulls more data than intended (e.g., loops through pages
beyond business need).
**Severity:** S2.
**Mitigation:** Rate limit per vendor; max-rows-per-window; abnormal
volume alerts.
**Required action:** Volumetric alerts implemented.
**Owner:** Phase 16 lead + security officer.

## E-04 — Patient consent confusion

**Risk:** Patient app retains data after consent revoked.
**Severity:** S2.
**Mitigation:** Server-side consent revocation rejects subsequent token
use; vendor contract requires retention compliance with revocation.
**Required action:** Server-side revocation tested.
**Owner:** Privacy officer.

## E-05 — Sandbox-to-production data leak

**Risk:** A sandbox vendor accidentally given production access.
**Severity:** S2.
**Mitigation:** Sandbox tenant explicitly labelled; production credentials
issued by separate process; promotion is governance-led.
**Required action:** Two-environment discipline; deployment review.
**Owner:** Phase 25 lead.

## E-06 — Third-party AI

**Risk:** Vendor brings their own AI; outputs treated as advisory but the
clinician trusts blindly.
**Severity:** S2.
**Mitigation:** Vendor-supplied AI MUST be presented as third-party with
explicit notice; explainability metadata still required by consumer
route.
**Required action:** UI policy: "AI: Vendor X" badge.
**Owner:** Clinical AI owner.

## E-07 — Aggregate-DEID mis-aggregation

**Risk:** Research consortium queries enable re-identification through
combined exports.
**Severity:** S2.
**Mitigation:** Phase 20 anonymisation governance; per-consumer budget;
re-identification testing.
**Required action:** Per-consumer query review.
**Owner:** Privacy officer.

## E-08 — Vendor abandonment

**Risk:** Vendor stops operating; we still trust their endpoint.
**Severity:** S3.
**Mitigation:** Heartbeat checks; auto-suspend on extended unreachability.
**Required action:** Coded heartbeat.
**Owner:** Operations.

## E-09 — Unsolicited inbound traffic

**Risk:** Old vendor credential reused by attacker.
**Severity:** S2.
**Mitigation:** Credential rotation; revocation propagation; audit.
**Required action:** Rotation calendar enforced.
**Owner:** Security officer.

## E-10 — Marketplace fraud

**Risk:** A vendor publishes misleading capabilities to gain access.
**Severity:** S2.
**Mitigation:** Governance review; capability claims verified during
sandbox stage.
**Required action:** Governance discipline.
**Owner:** Phase 25 lead.

## Risk Summary

| Risk | S | L | Residual after action |
|------|--:|--:|----------------------|
| E-01 | S2 | L3 | S3/L4 |
| E-02 | S2 | L4 | S3/L5 |
| E-03 | S2 | L3 | S3/L4 |
| E-04 | S2 | L3 | S3/L4 |
| E-05 | S2 | L4 | S3/L5 |
| E-06 | S2 | L3 | S3/L4 |
| E-07 | S2 | L3 | S3/L4 |
| E-08 | S3 | L3 | S4/L4 |
| E-09 | S2 | L3 | S3/L4 |
| E-10 | S2 | L3 | S3/L4 |
