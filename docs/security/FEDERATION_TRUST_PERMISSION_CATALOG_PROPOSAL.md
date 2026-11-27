# Federation and Trust Permission Catalog Proposal

Status: `PROPOSAL ONLY / NOT APPROVED`

## Purpose

`backend/app/identity/api/authorization_guard.py` now enforces action-specific
authorization for federation and trust mutation routes through the canonical
`AuthorizationDecisionService`. The guard fails closed when a permission key is
absent from the active catalog or not explicitly assigned to the actor's active
organization membership.

This document records the permission catalog entries required to restore
intended administrative capability. It is not an applied migration, not an
owner approval, and not evidence that any role has been granted these
permissions.

## Proposed permission keys

| Permission key | Sensitivity | Proposed role |
| --- | --- | --- |
| `federation_provider.register` | critical | `security_administrator` |
| `federation_provider.update` | critical | `security_administrator` |
| `federation_identity.link` | critical | `security_administrator` |
| `federation_identity.unlink` | critical | `security_administrator` |
| `federation_trust.establish` | critical | `security_administrator` |
| `federation_trust.suspend` | critical | `security_administrator` |
| `federation_trust.terminate` | critical | `security_administrator` |
| `federation_agreement.create` | high | `security_administrator` |
| `federation_agreement.sign` | critical | `security_administrator` |
| `federated_session.create` | high | `security_administrator` |
| `federated_session.terminate` | high | `security_administrator` |
| `trust_framework.create` | critical | `security_administrator` |
| `trust_framework.update` | critical | `security_administrator` |
| `trust_framework.activate` | critical | `security_administrator` |
| `trust_assurance_profile.assign` | critical | `security_administrator` |
| `trust_assurance_profile.revoke` | critical | `security_administrator` |
| `trust_anchor.create` | critical | `security_administrator` |
| `trust_anchor.revoke` | critical | `security_administrator` |
| `institution_trust.create` | critical | `security_administrator` |
| `institution_trust.suspend` | critical | `security_administrator` |
| `institution_trust.terminate` | critical | `security_administrator` |
| `identity_proofing.create` | high | `security_administrator` |
| `identity_proofing.verify` | critical | `security_administrator` |
| `identity_proofing.reject` | critical | `security_administrator` |
| `trust_evaluation.create` | high | `security_administrator` |

## Required owner decisions before any migration

1. Confirm the authoritative role or roles for each action; do not grant all
   entries automatically.
2. Confirm whether global platform trust operations should use a designated
   organization scope or a new platform-scope authorization basis.
3. Confirm MFA step-up requirements for `assign`, `revoke`, and signing actions.
4. Confirm the deterministic permission IDs and role-permission assignments.
5. Review and approve an Alembic revision in a disposable database before any
   shared environment is changed.

No DDL, seed data, role assignment, or shared database change has been applied
by this program.
