# Phase 18-05 — AI Governance Constraints (Phase 18 view)

This is the **Phase-18 governance view** of AI. The technical architecture
is in Phase 21. The two phases are deliberately split: governance defines
**what is allowed**; Phase 21 defines **how it is enforced**.

## Governance Invariants (Phase 18 imposed on Phase 21)

| ID | Constraint |
|----|------------|
| AG-G1 | Every AI capability MUST exist in an AI capability registry before it can be invoked in production. |
| AG-G2 | Every AI invocation MUST be auditable to the model id + version + feature snapshot. |
| AG-G3 | An AI capability MUST declare its **authority class**: `advisory`, `assistive`, or `automated`. Only `advisory` is permitted in clinical pathways. |
| AG-G4 | An AI capability MUST declare its **scope**: tenant-scoped, regulator-scoped, or aggregate. Cross-tenant scope is prohibited outside governed analytics. |
| AG-G5 | An AI capability MUST declare its **fail mode**: must be `fail_closed`. |
| AG-G6 | An AI invocation MUST NOT mutate clinical state. State mutations (order create, result release, sample status change) are the exclusive domain of human-driven endpoints. |
| AG-G7 | An AI capability MUST be removable on operator command (kill switch). |

## IRB-AI

A standing **AI Review Board** approves new AI capabilities and reviews
existing ones. Membership:

- Clinical safety lead
- Data privacy officer
- Platform security officer
- Tenant-isolation owner
- Audit-integrity owner
- Optional: external clinical-AI ethics adviser

IRB-AI is the policy authority. It cannot deploy code; it can block
deployment.

## Capability Registry (recommended)

A row per capability:

- `capability_id` (slug)
- `name`
- `description`
- `authority_class` (`advisory`)
- `scope`
- `model_id`
- `model_version`
- `inputs_schema`
- `outputs_schema`
- `fail_mode` (`fail_closed`)
- `kill_switch_flag` (env var or DB flag)
- `governance_record` (link to IRB-AI approval)

The registry is loaded on startup. Capabilities not in the registry MUST
NOT be invoked.

## Explainability Contract

Every AI output that influences clinical or financial decisions MUST be
returned with:

- `model_id`
- `model_version`
- `confidence` (or equivalent)
- `feature_snapshot_id` (a hash referring to a stored snapshot)
- `decision_rationale` (free text or structured, as the model permits)

Without this metadata, the consumer SHOULD reject the output (and the
consumer route is the gatekeeper for this — Phase 21).

## Clinical Authority

- AI never authorises a result release.
- AI never sets a critical-result flag without human confirmation.
- AI never executes a medication or order request.
- AI never bypasses the optimistic lock on `LabResult`.
- AI never closes a state-machine transition that requires a clinician
  signature.

These are absolute. No exception path exists.

## Auditability of AI Invocations

Each AI invocation produces an audit row containing:

- `capability_id` + version
- caller `request_id`
- inputs hash
- outputs hash
- explainability metadata (above)
- consumer's downstream action (e.g., "displayed to clinician", "logged
  only", "discarded due to low confidence")

The audit row is part of the same hash chain as clinical audit. There is no
separate "AI audit silo".

## Regulatory Reporting

When a regulator requests AI evidence, the program produces:

- The capability registry snapshot at the time of question.
- The audit subset for the relevant time window.
- The explainability metadata for invocations of interest.
- The IRB-AI minutes for the capability.

A regulator's read access flows through `INTEROP_REGULATOR_READ` (Phase 16)
or a Phase-18 regulator account, never as a developer.

## Prohibitions

- AI MUST NOT receive `national_id` plaintext.
- AI MUST NOT cross tenant boundaries except in governed analytics workflows
  with anonymized data.
- AI MUST NOT call adapter peers directly; if AI output must reach a peer,
  it travels through an adapter just like any other event.
- AI MUST NOT have privileged DB credentials.

## Deferred to Phase 21

- Capability registry coding
- Sandbox infrastructure
- Explainability metadata enforcement at the route layer
- Kill-switch wiring
