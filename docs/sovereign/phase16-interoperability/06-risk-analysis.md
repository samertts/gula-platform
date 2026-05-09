# Phase 16-06 — Interoperability Risk Analysis

Phase-specific risk analysis. The platform-wide risk register lives in
[`../INTEGRATION_RISK_ANALYSIS.md`](../INTEGRATION_RISK_ANALYSIS.md).

## I-01 — Manifest forgery

**Threat:** A malicious or compromised commit ships a manifest that grants an
adapter broader operations than IRB-Interop approved.
**Mitigations:** Manifest-change governance requires IRB-Interop sign-off
recorded in commit; protected branch on `main`; CI compares manifest checksum
to a signed allowlist file maintained by the IRB.
**Residual:** Low, gated by code-review rigor.

## I-02 — Capability bypass via direct call

**Threat:** A new code path imports an adapter and calls `_session.post(...)`
directly, bypassing `call_outbound`.
**Mitigations:** AdapterBase keeps the underlying client `_private`; static
check forbids access to `_private` from outside `interoperability/`; lint
rule.
**Residual:** Low if static check enforced.

## I-03 — Peer credential compromise

**Threat:** Ministry / insurer / telco credentials issued to GULA are stolen.
**Mitigations:** Per-adapter credential isolation (no shared OAuth client);
short-lived tokens; rotation calendar; sovereign KMS custody preferred over
.env.
**Residual:** Medium — depends on operational hygiene.

## I-04 — Inbound replay

**Threat:** An attacker replays a captured signed inbound message.
**Mitigations:** Manifest requires JWS with `nonce` and `iat`; reject `iat`
older than configured skew; deduplicate by `(jti, peer)` for the dedup
window.
**Residual:** Low.

## I-05 — Cross-tenant data leak via reconciliation

**Threat:** A peer triggers a reconciliation that exposes patient data from
tenant A to tenant B.
**Mitigations:** TI-3, TI-5; reconciliation events go through Phase 19's
reconciliation governance, two-person rule for non-deterministic merges.
**Residual:** Medium — Phase 19 is documentation-only; coding follow-up
required.

## I-06 — Adapter-driven concurrency starvation

**Threat:** A flaky peer causes a backlog of in-flight requests; clinical
writes starve.
**Mitigations:** Per-adapter bulkhead; clinical writes exempt from
concurrency cap (CS-1); circuit breaker.
**Residual:** Low.

## I-07 — Audit drop on adapter crash

**Threat:** Adapter crashes mid-call; audit event never written.
**Mitigations:** Audit event written **before** outbound call (intent log)
and updated on result; if crash, intent log is the source of truth.
**Residual:** Low.

## I-08 — Terminology drift

**Threat:** A peer sends LOINC codes from a newer release than our active
mapping; data quietly degrades.
**Mitigations:** Unmapped codes fail closed; dead-letter for review;
terminology-governance refresh cycle.
**Residual:** Medium — operational vigilance required.

## I-09 — Privilege widening through "exception" paths

**Threat:** An emergency clinical scenario justifies a manifest that allows
broader operations "just for now"; exception persists.
**Mitigations:** No exception path exists in framework; exceptions are new
manifests with TTL and sunset clause.
**Residual:** Low if governance discipline upheld.

## I-10 — Peer-side observability becomes attack surface

**Threat:** A peer observes our timing patterns or error responses to infer
internal state.
**Mitigations:** Constant-time error responses for capability-denied;
deliberately uniform `503` for any degraded internal state; no internal model
field names appear in error messages.
**Residual:** Low.

## Phase-Local Risk Score Summary

| Risk | Severity | Likelihood | Residual |
|------|---------:|-----------:|----------|
| I-01 Manifest forgery | S2 | L4 | S3/L5 |
| I-02 Capability bypass | S2 | L4 | S3/L4 |
| I-03 Peer credential | S2 | L3 | S3/L4 |
| I-04 Inbound replay | S2 | L4 | S3/L5 |
| I-05 Cross-tenant leak via reconciliation | S1 | L3 | S2/L4 (until Phase 19 implemented) |
| I-06 Concurrency starvation | S2 | L3 | S3/L4 |
| I-07 Audit drop | S2 | L4 | S3/L5 |
| I-08 Terminology drift | S3 | L3 | S3/L3 |
| I-09 Privilege widening | S2 | L3 | S3/L4 |
| I-10 Peer-side observability | S3 | L3 | S4/L4 |

The risk most worth tracking continuously is **I-05** until Phase 19's
reconciliation enforcement is coded and exercised end-to-end.
