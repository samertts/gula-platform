# GULA IAM Organizations, Facilities and Administrative Hierarchy

**Status:** `IMPLEMENTED` for the additive administrative structure foundation; `TESTED` for state/provider unit tests; `UNVERIFIED` for live database migration and production organization workflows; `DEFERRED` for memberships, RBAC, ABAC and organization authorization.

## Reuse before extension

GULA already has `niam_organizations` and legacy `organizations`/`facilities` tables. The repository also already contains `niam_admin_branches`, `niam_admin_facilities` and `niam_admin_departments` in an earlier migration. Phase 4 maps those existing NIAM administrative tables into ORM models and adds only the missing unit, representative and ownership records. It does not create a second account or identity system and does not delete legacy data.

## Organization model

`NIAMOrganization` remains the organization identity. Its internal database identifier is separate from names, phone, email and license numbers. The existing `org_type` field remains extensible; the new registry categories are policy guidance, not a schema-enforced closed list.

Organization status follows a deny-by-default state machine:

| Current | Allowed next states |
|---|---|
| `draft` | `pending_verification` |
| `pending_verification` | `pending_approval`, `rejected` |
| `pending_approval` | `active`, `rejected` |
| `active` | `suspended`, `deactivated` |
| `suspended` | `active`, `deactivated` |
| `rejected` | `draft` |
| `deactivated` | `archived` |
| `archived` | none |

Activation requires `pending_approval`; there is no automatic activation from draft or verification submission.

## Facilities and hierarchy

The existing NIAM branch/facility/department tables represent the administrative hierarchy. Phase 4 adds `niam_admin_units` for the final `facility → department → unit` level. One organization may have multiple branches and facilities. A hierarchy relationship is structural context only; it is not authorization and does not grant access to parent, sibling or child resources.

## Representatives and ownership

`OrganizationRepresentative` links an existing GULA `Account` to an organization. It does not copy a person or create a new user database. Representative status supports pending, active, suspended, revoked and expired. `OrganizationOwnership` records sensitive authority relationships with explicit pending-to-active activation; later ownership transfer must require strong authentication, confirmation, validation and audit.

No membership, RBAC, ABAC or clinical authorization behavior is added in this phase.

## Verification boundary

Organization verification uses a separate `OrganizationVerificationProvider` boundary. The default provider returns `NOT_CONNECTED` and never approves an organization. Existing `VerificationRecord` can represent an organization verification record, preserving one canonical verification evidence model. No government registry, licensing authority or professional-body endpoint is fabricated or scraped.

## Privacy and documents

This phase stores references and structure only. It does not upload organization documents or expose public URLs. A future document workflow must use private storage, server-generated identifiers, content/type/size checks, malware scanning where available, signed temporary retrieval, access audit and retention/deletion policy.

## Rollback and deployment

The migration is additive and reversible. It creates units, representatives and ownership records only. No production deployment or data backfill is performed. A rollback must preserve existing NIAM organizations and existing legacy organization/facility records.
