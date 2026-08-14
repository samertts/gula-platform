# GULA IAM Phase 4 — Organizations, Facilities and Administrative Hierarchy

**Overall status:** `IMPLEMENTED` for the additive administrative foundation; `TESTED` for targeted unit tests; `UNVERIFIED` for live database migration and production workflows; `DEFERRED` for memberships, RBAC, ABAC and organization authorization.

## 1. Existing state audited

The repository already contains NIAM `niam_organizations`, legacy `organizations` and `facilities`, and migration-created NIAM administrative tables for branches, facilities and departments. There are also clinical scope bridges that must remain separate from IAM structure. Phase 4 reuses the NIAM organization and administrative tables rather than creating duplicate organization/facility systems.

## 2. Changes made

| Area | Change | Status |
|---|---|---|
| Organization registry | Add extensible policy categories without closing the existing `org_type` field | `IMPLEMENTED` |
| Existing hierarchy | Add ORM mapping for NIAM branches, facilities and departments already present in schema | `IMPLEMENTED` |
| Units | Add `NIAMAdminUnit` and additive migration | `IMPLEMENTED` |
| Representatives | Link existing GULA accounts to organizations with explicit status | `IMPLEMENTED` |
| Ownership | Add explicit pending/active/ended/revoked authority record | `IMPLEMENTED` |
| Organization status | Add deny-by-default state machine with pending verification and approval | `IMPLEMENTED` |
| Organization verification | Add provider boundary with `NOT_CONNECTED` default | `IMPLEMENTED` |
| Audit vocabulary | Add organization verification/activation/suspension/representative events | `IMPLEMENTED` vocabulary |
| Authorization | No RBAC/ABAC/membership/clinical authorization grant | `DEFERRED` by design |

## 3. Database changes

Migration `20260814_0002_organization_structure` creates `niam_admin_units`, `niam_organization_representatives` and `niam_organization_ownerships`. Existing NIAM branch/facility/department tables are reused. The migration is additive and reversible; no existing organization, account, identity or clinical row is deleted or rewritten.

## 4. Security controls

Organizations cannot jump from draft to active. Activation is permitted only from pending approval. Organization verification has no connected government or licensing provider and therefore cannot approve an organization. Representatives and ownership relationships point to existing accounts and have explicit lifecycle states. Hierarchy is structural context only and does not grant access to sibling, parent or child resources.

## 5. Facilities and departments

Facilities remain distinct from organizations and can be multiple per organization. Departments remain under facilities, and units are under departments. The model supports hospital, laboratory, pharmacy, radiology, clinic and primary-health-center types as extensible strings rather than a closed schema enum.

## 6. Verification and documents

Organization verification can reuse the canonical `VerificationRecord` with `record_type=organization`. No provider response, government endpoint, organization document or public document URL is fabricated. Secure document storage and organization application APIs remain deferred until storage, legal and review requirements are approved.

## 7. Tests executed

Targeted Phase 1, Phase 3 and Phase 4 identity suites passed with **17 tests**. They cover organization activation workflow, rejection of skipped approval, archived-state protection, representative transitions, revoked-representative protection, explicit ownership activation, and not-connected organization verification. Python compilation, Ruff and the existing Phase 3 checks passed. Live migration execution and full repository regression remain `UNVERIFIED` until CI completes.

## 8. Remaining risks and deferred items

Legacy organization/facility APIs and NIAM administrative tables need a compatibility review before new endpoints are exposed. Organization registration, document upload, manual review UI, ownership transfer API, representative authorization, multi-organization membership, RBAC/ABAC and clinical scope enforcement are not claimed complete. No professional or clinical privileges are granted by this phase.

## 9. Deployment and rollback

No production deployment was performed. Before deployment, CI must run migration tests against supported databases, verify foreign-key ordering, and run integration/security suites. Rollback reverts code and drops only the three additive Phase 4 tables; existing organizations, accounts, identities and legacy facilities remain intact.

## 10. Next phase

The next safe phase is organization registration and verification workflow integration: authenticated applicant ownership checks, idempotent application records, manual-review decisions, audit emission and private document storage. Membership and authorization remain later phases as required by the Phase 4 boundary.
