# Phase 24-03 — Digital Health Governance Preparation

## Governance Composition

A national digital-health deployment requires a governance ecosystem with
clear roles. The platform's posture is to **support** the ecosystem with
auditable architecture, not to **be** the ecosystem.

| Role | Responsibility |
|------|----------------|
| Ministry of Health | Sets policy, ratifies standards, owns sovereignty |
| National Data Protection Authority | Sets privacy policy, audits compliance |
| Clinical-safety committee | Patient-safety oversight, AI sign-off |
| Lab accreditation body | Lab quality, ISO 15189 / CAP / CLSI |
| Insurance regulator | Insurance governance, claim-cycle oversight |
| Platform operator | Operates the platform, executes policy |
| IRB-Interop | Adapter approval and review |
| IRB-AI | AI capability approval and review |

## Digital Health Policies (national-level)

Policies the platform consumes (does not write):

- Patient consent policy (per data class)
- Cross-border transfer policy
- Retention policy floor
- AI deployment policy
- Adapter onboarding policy
- Crisis-mode policy

The platform implements / observes; the policy authority owns the policy.

## AI-Medical Governance Bridge

- AI capabilities visible to regulator via the AI registry (Phase 21).
- IRB-AI minutes filed.
- Regulator may run a regulator-scoped read of AI audit on warrant.
- A regulator can require explainability evidence for any AI-touched
  clinical event.

## Interoperability Legal-Governance Bridge

- Each adapter has a contract with the peer institution.
- Contract includes: scope, data classes, signing/encryption, retention on
  peer side, audit access.
- Adapter manifest reflects contract.
- Manifest changes require contract review where the change affects scope.

## Digital-Consent Governance

- A consent token covers a defined scope (data classes, recipients,
  TTL).
- Patients may consult their own consent record via patient-card view
  (read).
- Consent revocation halts new transfers; existing transfers are
  governed by the contract's revocation handling.
- Revocation does not erase prior data already shared (where contract
  permits retention) — but it stops further sharing.

## Operational Accountability Mapping

- Every clinical event traces to a clinician's account.
- Every adapter event traces to a manifest + a peer system.
- Every operator action traces to a session + identity.
- Every AI event traces to a capability + version.
- Every audit row participates in the chain.

A regulator's "who did what when" question is answerable from the chain.

## Continuous Governance

- Quarterly: all policies confirmed unchanged or refreshed.
- Annually: full bundle re-ratified.
- Per regulation change: corresponding policies refreshed within the
  regulator-set window.

## Out of Scope

- Drafting of national policy (regulator owns)
- Inter-ministry MOUs (legal counsel owns)
- Patient-facing legal documents (institution owns)

The platform provides the technical artefacts that make those documents
enforceable.
