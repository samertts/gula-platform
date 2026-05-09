# Phase 16-04 — Interoperability Governance

## Governance Body

A standing **Interop Review Board** (IRB-Interop, distinct from clinical
ethics IRBs) reviews every new adapter manifest, every change to an existing
manifest, and any change to the adapter framework itself.

Membership (minimum):

- Platform security officer
- Clinical safety lead
- Tenant-isolation owner
- Audit-integrity owner
- Regulator liaison (non-voting observer)

## Adapter Lifecycle (Governance View)

```
[1] Proposal -> [2] Risk + privacy review -> [3] Manifest authoring
   -> [4] IRB-Interop approval -> [5] Implementation
   -> [6] Pre-prod adapter test (sandbox tenant)
   -> [7] Limited rollout (1 tenant) -> [8] National rollout
   -> [9] Continuous monitoring -> [10] Annual recertification
```

Stage gates:

- **Stage 4**: explicit IRB-Interop sign-off; minutes recorded.
- **Stage 6**: sandbox demonstrates fail-closed behavior, audit emission, and
  bounded operations.
- **Stage 7**: 30-day soak with tenant-isolation regression suite green.
- **Stage 10**: each year, the manifest is re-reviewed; capability creep is
  identified and reverted.

## Change Control

Manifest changes are **not** code changes. They are policy changes.

- Every manifest revision is a separate, signed commit.
- Each revision includes a justification field.
- Each revision has its own IRB-Interop approval row in the change register.
- The audit chain includes a record of every manifest version that was active
  during a given event, so historical interop calls can be re-evaluated.

## Capability-Creep Detection

A scheduled job (out-of-scope for this phase, target Phase 18) compares
declared `allowed_operations` to invoked operations across the audit chain.
Discrepancies (declared but unused, used but undeclared — the latter being a
defect) are reported to IRB-Interop monthly.

## Incident Response (Interop-specific)

Triggers:

- Repeated adapter `interop.capability_denied` events (potential peer
  misconfiguration or attack)
- Circuit breaker open for > 30 minutes
- Audit-emission failure (the dead-letter chain receives an entry)
- Manifest validation failure on startup

Each trigger has a runbook in
[`../phase17-operational-infrastructure/02-runbooks.md`](../phase17-operational-infrastructure/02-runbooks.md).

## Documentation Requirements per Adapter

Each adapter folder MUST contain:

- `manifest.yaml`
- `README.md` (purpose, peer system, data classes, contact)
- `mapping.md` (FHIR/HL7/etc terminology mapping)
- `risk_register.md` (adapter-specific risks beyond the standard set)
- `runbook.md` (operational procedures, escalation contacts)

Without all five files, the adapter MUST NOT pass IRB-Interop stage 4.

## External Communication

Peer systems are sent a **public adapter contract**:

- Operation list (no internals)
- Required signing/encryption parameters
- SLA targets and degraded-mode behavior
- Audit transparency commitment ("every call is logged on our side")

Peers do not receive: internal data class names, internal model fields,
internal RBAC roles, or audit-chain layout. This is a privacy boundary, not
hostility — it ensures the peer cannot reason about internal state changes.

## Recertification

Annually, each adapter is recertified:

- Manifest reviewed against current data classes
- Capability usage report reviewed
- Audit-emission completeness verified
- Failure-isolation rehearsal executed
- Peer-side credentials rotated

A failed recertification suspends the adapter (manifest set to
`status: suspended`) until remediated.
