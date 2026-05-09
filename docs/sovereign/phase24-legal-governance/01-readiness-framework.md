# Phase 24-01 — Legal-Governance Readiness Framework

## Scope

The framework is the bridge between (a) the platform's technical controls
and (b) the legal/regulatory obligations of operating a sovereign-grade
healthcare system. It does not replace legal counsel; it organises the
artefacts a legal review will request.

## Domains

1. **Healthcare-data sovereignty** — residency, cross-border, retention.
2. **Digital-consent** — patient consent for processing, sharing,
   research.
3. **Medico-legal traceability** — clinician + AI accountability, evidence
   preservation.
4. **Records governance** — retention, legal hold, archiving.
5. **Interoperability legal-governance** — adapter contracts,
   data-sharing agreements with peers.
6. **Operational accountability** — clear ownership of decisions and
   incidents.
7. **Regulator/auditor access** — separation, scope, audit of access.

## Artefact Inventory

For each domain, the program maintains a current artefact bundle:

- **Policy** — a written policy ratified by the appropriate authority.
- **Implementation map** — code/config/process implementing the policy.
- **Evidence** — auditable records demonstrating conformity.
- **Gap register** — items where the policy is documented but not yet
  implemented.

A complete bundle is the precondition for legal sign-off on national
deployment.

## Sign-off Authorities

| Domain | Authority |
|--------|-----------|
| Sovereignty | National Ministry of Health + Data Protection authority |
| Consent | National Ministry of Health + Privacy officer |
| Medico-legal | Clinical-safety committee + legal counsel |
| Records governance | Regulator + program owner |
| Interoperability | IRB-Interop + legal counsel |
| Operational accountability | Operations chief |
| Regulator access | Regulator + security officer |

## Annual Review

- All policies re-ratified annually or on regulation change.
- Implementation maps refreshed.
- Evidence sampled (regulator-style audit).
- Gap register reviewed; SEV-1 gaps trigger remediation plans.

## Linkages

This framework is the consumer of:

- `STANDARDS_MAPPING_MATRIX.md` (which standards apply)
- `phase18-regulatory-governance/...` (governance architecture)
- `phase19-health-data-fabric/...` (identity policies)
- `phase21-clinical-ai-governance/...` (AI accountability)
- `phase23-crisis-continuity/...` (crisis governance)

It is the producer of:

- A legal-readiness brief for any national deployment proposal
- A regulator-facing summary
- An institutional-counterparty pack (used in adapter onboarding under
  Phase 16)
