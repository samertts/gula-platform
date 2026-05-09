# Phase 21-03 — AI Auditability Assumptions

## Audit Surfaces

| Surface | Source | Required content |
|---------|--------|------------------|
| Capability registry change | IRB-AI approval | who, when, change diff, approval reference |
| AI invocation | Consumer route | capability id+version, request id, inputs hash, outputs hash, explainability metadata, downstream action |
| AI output rejection | Consumer route | reason (metadata missing, low confidence, kill switch active) |
| Kill switch trigger | Operator | who, when, reason, capability id |
| Sandbox event | Sandbox runtime | capability id, sandbox event type, severity |

All surfaces participate in the audit chain (AI-2 invariant) — there is no
separate "AI audit silo".

## Per-Invocation Audit Row

Minimum content:

```
{
  "subject": "ai.invocation",
  "request_id": "...",
  "capability_id": "critical-result-triage",
  "model_id": "...",
  "model_version": "1.4.2",
  "inputs_hash": "...",
  "outputs_hash": "...",
  "explainability": {...},
  "downstream_action": "displayed_to_clinician",
  "tenant": "lab_id",
  "scope": "tenant",
  "result_status": "accepted | rejected | kill_switch | metadata_missing"
}
```

The audit row participates in the chain hash; an entry hashed wrong is
visible through the chain verifier.

## Failure-Mode Auditing (AI-4)

If AI invocation fails (model server unreachable, timeout, schema
mismatch), an audit row is still written:

```
{
  "subject": "ai.invocation_failed",
  "capability_id": "...",
  "request_id": "...",
  "failure_class": "model_timeout | model_5xx | schema_mismatch | sandbox_violation"
}
```

The consumer route MUST treat the failure as fail-closed; clinical
workflow proceeds without the AI advice.

## Audit Retention

Same retention policy as clinical audit. AI audit rows do not have a
shorter floor.

## Read Access

- Tenant clinicians: their own tenant's AI invocations (subject to RBAC).
- Tenant administrators: aggregate metrics; no payload contents.
- Regulators: read full AI audit on warrant or compliance event.
- IRB-AI: full read on IRB review windows.

Read access is itself audited.

## Kill-Switch Audit

Triggering a kill switch produces:

- a kill-switch audit row
- a propagation row when in-flight invocations are forced to a fail-closed
  state
- a "capability suspended" row in the capability registry

The kill-switch trigger does not auto-clear; clearing requires IRB-AI
approval.

## Auditability vs. Privacy

Some AI inputs may be PHI. The audit row stores **hashes** of inputs, not
raw inputs; raw inputs live in the snapshot store with stricter access.

A regulator with appropriate scope can fetch the snapshot; a tenant
administrator cannot.

## Verification

- The chain verifier verifies AI rows alongside everything else.
- A monthly job samples N invocations, refetches snapshots, and verifies
  reproducibility (same inputs + same model version → expected outputs).
- Reproducibility deviations are SEV-2.
