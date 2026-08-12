# Phase 21-05 — AI Operational Risk Analysis

Risks specific to clinical AI operation. Cross-phase risks live in
`INTEGRATION_RISK_ANALYSIS.md`.

## A-01 — Silent clinical-state mutation

**Risk:** A code path lets AI write clinical state.
**Severity:** S1.
**Mitigation:** AG-1, AG-6; sandbox lacks DB write privilege.
**Required action:** Static check forbidding `from app.models...` writes
inside `app/ai/` and `services/ai/`.
**Owner:** Clinical AI owner.

## A-02 — AI output without explainability

**Risk:** Consumer route accepts an output missing required metadata.
**Severity:** S2.
**Mitigation:** Required metadata schema; route rejects on miss;
`ai.metadata_missing` audit row.
**Required action:** Coded enforcement at consumer.
**Owner:** Clinical AI owner.

## A-03 — Cross-tenant feature leak

**Risk:** A tenant-scope capability accidentally sees rows from another
tenant.
**Severity:** S2.
**Mitigation:** Sandbox DB credentials are tenant-scoped read-only.
**Required action:** Credential issuance via tenant-bound role.
**Owner:** Security officer.

## A-04 — Drifted model on retired version

**Risk:** A retired model is still callable due to caller caching.
**Severity:** S2.
**Mitigation:** Capability registry status check on every invocation;
suspended/retired returns fail-closed.
**Required action:** Coded enforcement.
**Owner:** Clinical AI owner.

## A-05 — Kill-switch latency

**Risk:** Kill switch triggered, but invocations continue for minutes due
to caching.
**Severity:** S2.
**Mitigation:** Kill-switch flag read on every invocation; no caching of
flag.
**Required action:** Document and verify.
**Owner:** Clinical AI owner.

## A-06 — Sandbox escape

**Risk:** Capability code calls outside its sandbox.
**Severity:** S1.
**Mitigation:** Sandbox runtime + allowlist; periodic review.
**Required action:** Choose sandbox runtime in implementation phase;
penetration-test it.
**Owner:** Security officer + Clinical AI owner.

## A-07 — Capability creep

**Risk:** A capability initially advisory becomes "auto-accepted" by a
consumer through UI defaults.
**Severity:** S2.
**Mitigation:** Authority class enforcement; consumer route requires human
acceptance.
**Required action:** UX review; quarterly creep audit.
**Owner:** Clinical safety lead.

## A-08 — Bias / fairness regression

**Risk:** Model performance regresses for under-represented demographics.
**Severity:** S2.
**Mitigation:** Bias review per release; monitoring of per-demographic
error rates from accepted/rejected feedback loop.
**Required action:** Bias monitoring dashboard; quarterly review.
**Owner:** Clinical AI owner + clinical safety lead.

## A-09 — Generative-AI hallucination

**Risk:** An LLM-style capability fabricates plausible-but-wrong content.
**Severity:** S1.
**Mitigation:** No generative AI is permitted to mutate clinical state
directly; outputs reviewed; explainability + evidence lineage required;
uncertainty disclosed.
**Required action:** Generative capabilities require additional IRB-AI
review beyond the standard.
**Owner:** Clinical AI owner.

## A-10 — Snapshot exfiltration

**Risk:** Snapshot store exfiltrated.
**Severity:** S2.
**Mitigation:** Snapshots access-controlled; encrypted at rest; never
contain raw national_id.
**Required action:** Annual access audit.
**Owner:** Security officer.

## A-11 — AI in degraded mode

**Risk:** AI continues operating during platform degraded mode.
**Severity:** S2.
**Mitigation:** AG-3 fail-closed; degraded mode disables non-critical AI.
**Required action:** Capability registry knob: "operate in degraded mode?"
defaulting to false.
**Owner:** Clinical AI owner.

## A-12 — Vendor model service compromise

**Risk:** External model server compromised.
**Severity:** S1.
**Mitigation:** mTLS to model server; signed responses; per-call
verification; restricted egress.
**Required action:** Vendor security review; rotation.
**Owner:** Security officer.

## Risk Summary

| Risk | S | L | Residual |
|------|--:|--:|----------|
| A-01 | S1 | L4 | S2/L5 |
| A-02 | S2 | L3 | S3/L4 |
| A-03 | S2 | L4 | S3/L5 |
| A-04 | S2 | L3 | S3/L4 |
| A-05 | S2 | L3 | S3/L4 |
| A-06 | S1 | L4 | S2/L5 |
| A-07 | S2 | L3 | S3/L3 |
| A-08 | S2 | L3 | S3/L3 |
| A-09 | S1 | L3 | S2/L4 |
| A-10 | S2 | L4 | S3/L5 |
| A-11 | S2 | L4 | S3/L5 |
| A-12 | S1 | L4 | S2/L5 |
