# GULA IAM Phase 1 — Migration Map

**Status:** `IMPLEMENTATION PLANNED / NOT YET MIGRATED`
**Repository commit audited:** `98230c58`
**Principle:** extend and map existing systems; do not duplicate or delete identity data.

## Canonical mapping

| Existing entity | Target entity | Decision | Action in Phase 1 | Data safety |
|---|---|---|---|---|
| `backend/app/identity/models/account.py::Account` / `niam_accounts` | Canonical GULA Account | **KEEP** | Use as the canonical internal account identity; add only missing lifecycle/security behavior if required | Preserve `id`, `uuid`, timestamps, contacts, status and audit relationships |
| `backend/app/identity/models/identity.py::IdentityRecord` / `niam_identities` | GULA Identity | **KEEP** | Keep account/identity separation and resolve both from authentication | No national ID is required as primary key |
| `backend/app/identity/models/person.py::Person` / `niam_persons` | Individual/Citizen identity profile | **KEEP / EXTEND** | Use for person attributes and future verified references | Minimize sensitive attributes; do not copy an external national registry |
| `backend/app/models/user.py::User` / `users` | Legacy application user | **KEEP / MAP** | Preserve backward compatibility; introduce explicit mapping to canonical Account only after data validation | Never silently recreate or delete users |
| `backend/app/models/lab_user.py::LabUser` | Legacy laboratory user | **KEEP / MAP** | Continue clinical compatibility while mapping identity/account context | GULA remains clinical system of record |
| `backend/app/identity/models/credential.py::Credential` | Credential | **KEEP** | Reuse for password/passkey/provider credentials where secure | Never log or expose secrets |
| `backend/app/identity/models/session.py::UserSession` | Session/refresh session | **KEEP / HARDEN** | Reuse rotation/revocation foundation; add tests for replay/reuse and invalidation | Preserve session audit and revoke old sessions on rotation |
| `backend/app/identity/models/device.py::Device` | Device/session context | **KEEP** | Reuse for device-aware security | Do not store raw tokens or secrets |
| `backend/app/identity/models/niam_organization.py::NIAMOrganization` | Organization registry | **KEEP** | Preserve organization hierarchy and verification references | No duplicate organization registry |
| `backend/app/models/organization.py::Organization` | Clinical organization | **KEEP** | Preserve clinical FK-backed organization scope | Do not replace clinical organization tables in Phase 1 |
| `backend/app/models/organization.py::Facility` | Clinical facility | **KEEP** | Preserve clinical facility scope and bindings | Resource authorization remains server-side |
| `backend/app/identity/models/employment.py::Employment` | Employment relationship | **KEEP** | Use as evidence for professional eligibility | Expiry/revocation must restrict professional access, not delete the account |
| `backend/app/identity/models/assignment.py::Assignment` | Organization/facility assignment | **KEEP / EXTEND** | Reuse clinical assignment authorization path | Require active organization and facility context |
| `backend/app/models/authorization.py::Role` / `roles` | Existing role catalog | **KEEP / CONSOLIDATE LATER** | Do not create a second role table; inventory and version existing catalog | Prevent self-assignment and privilege escalation |
| `Permission` / `permissions` and `RolePermission` | Existing permission catalog | **KEEP / CONSOLIDATE LATER** | Treat the database catalog as source of truth after row-level audit | Do not infer count from ORM declarations |
| `RoleAssignment` / `role_assignments` | Legacy role assignment | **KEEP / MAP** | Preserve until NIAM assignment mapping is validated | No destructive backfill; reject ambiguous records |
| `IdentityPolicy` / `niam_policies` | NIAM policy source | **KEEP** | Connect to centralized assurance/authorization policy | Must not allow by default |
| `Policy` / `abac_policies` | Existing ABAC policy source | **KEEP / CONSOLIDATE LATER** | Preserve and document precedence with NIAM policies | Require deny-by-default and audit decision |
| `ClinicalPolicyEvaluator` | Clinical authorization boundary | **KEEP / PROTECT** | Preserve its explicit organization/facility/assignment checks | No specialized repository may approve clinical results |
| `PolicyEngine` | General policy abstraction | **EXTEND / HARDEN** | Replace allow-by-default behavior with explicit deny-by-default before broad use | Invalid or missing context must reject and audit |
| Existing trust/proofing/assurance models | Verification framework | **KEEP / EXTEND** | Add provider interface and status model without claiming unavailable integrations | Official/OCR/NFC providers remain `NOT_CONNECTED` unless proven |
| Existing citizen relationship models | Citizen access relationship | **KEEP** | Reuse for citizen workspace eligibility and delegated relationships | Enforce resource ownership and anti-IDOR checks |
| Existing audit models and security events | Immutable audit/security trail | **KEEP / CONSOLIDATE** | Use canonical event taxonomy and redact secrets | Append-only/tamper-evident behavior required |
| Workspace references in frontend/context only | Workspace abstraction | **DEFERRED ADDITIVE** | Do not create in this mapping phase; design after account/identity compatibility | No frontend-only authorization |
| Membership/invitation concepts without general NIAM tables | Membership/invitation | **DEFERRED ADDITIVE** | Add only after schema design and migration report | Single-use digest, expiry, revoke and audit required |

## Decisions

The canonical account for Phase 1 is the existing NIAM `Account`, not a new `User` or `Account` table. `IdentityRecord` and `Person` remain separate from the account. Existing `User` and `LabUser` records remain operational until an evidence-based mapping and rollback plan is complete.

No production data migration is authorized by this document. A later migration must first report counts, duplicates, orphaned foreign keys, incompatible credentials, ambiguous email/phone matches and audit-history dependencies. Ambiguous records must be quarantined for explicit resolution; they must never be silently deleted or merged.

The first implementation slice should therefore be additive and low-risk: canonical account/identity resolution, lifecycle transition enforcement, verification-provider interface with unavailable providers marked `NOT_CONNECTED`, secure contact-verification primitives, and tests. Workspace, membership, role catalog consolidation and broad frontend changes remain later slices unless a concrete existing contract requires them.

## Rollback strategy

All Phase 1 database changes must be additive and reversible. No existing table is dropped, renamed destructively or repopulated blindly. If a backfill is introduced, it must be idempotent, produce a migration report, preserve original identifiers, and support rollback by disabling the mapping rows rather than deleting source records.
