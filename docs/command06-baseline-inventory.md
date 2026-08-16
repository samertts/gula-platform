# Command 06 — Baseline Inventory

**Date:** 2026-08-17
**Repository:** `samertts/gula-platform`
**Branch:** `chore/security-ddos-hardening-clean`
**Scope:** Membership, Organization, Facility, Workspace, Role/Permission, Authorization, Delegation, Invitation, Audit, and cross-platform context.

## Baseline result

The repository contains a relatively complete NIAM identity path in `backend/app/identity`, but it also retains a separate legacy authorization stack under `backend/app/routes/authorization.py` and `backend/app/services/authorization_service.py`. The NIAM path is the canonical server-side context path for the newer `/niam/memberships`, `/niam/roles`, and `/niam/workspaces` APIs. The legacy `/authz` path still uses the older `User`/lab authorization model and accepts client-provided resource attributes and delegation scope; it is therefore a compatibility surface that must remain fail-closed and must not be treated as the authority for NIAM workspace access.

The pre-change identity regression baseline was **208 passed, 4 skipped, 0 failed** across `backend/tests/identity` (212 collected). This establishes that the previous hardening work is green but does not prove every Command 06 requirement.

## Model inventory

| Concept | Canonical implementation | Current status | Gap or risk |
|---|---|---|---|
| NiamActor | `backend/app/identity/api/workspaces.py` (`NiamActor`, `get_current_niam_actor`) | **IMPLEMENTED** | Actor is resolved from account/session/token JTI; membership and workspace remain separate server-side checks. |
| Account | `backend/app/identity/models/account.py` (`Account`) | **IMPLEMENTED** | Active/locked/session checks exist. There is no account-level `perm_version` in this model; session invalidation relies on session state and lifecycle services. |
| Membership | `backend/app/identity/models/membership.py` (`Membership`) | **IMPLEMENTED** | Unique `membership_key`, scoped foreign keys, lifecycle status, expiry/version fields. |
| Membership status | `MembershipStatus` plus `LEGAL_MEMBERSHIP_TRANSITIONS` | **PARTIAL** | Required states exist except the requested canonical `INVITED/PENDING/ACTIVE/SUSPENDED/EXPIRED/REVOKED/REJECTED` are mixed with `deactivated`; transition enforcement is service-level rather than database-level. |
| Organization | `NIAMOrganization` | **IMPLEMENTED** | Organization status/is_active and self-parent relationship exist. Organization is referenced by membership and role assignment. |
| Facility | `NIAMAdminFacility` | **IMPLEMENTED** | Organization foreign key and active flag exist. Department/unit relationships are modeled. |
| Workspace | `Workspace` and `WorkspaceSessionContext` | **IMPLEMENTED** | Workspace scope and session context exist. `facility_id` is indexed but has no foreign key; status and organization alignment require service checks. |
| Role | `Role` and `RoleAssignment` | **IMPLEMENTED** | Role catalog and scoped membership-bound assignment exist. Assignment key is unique. |
| Permission | `Permission`, `RolePermission` | **IMPLEMENTED** | Catalog is active/disabled/deprecated and role links are unique. |
| Entitlement | No separate NIAM `Entitlement` model found | **MISSING** | Effective permissions are derived from role assignments; entitlement is not a separately scoped/evaluable object. No fake entitlement provider will be introduced. |
| Delegation | Legacy `Delegation` in `backend/app/models/authorization.py` and `DelegationService` | **PARTIAL / LEGACY** | Has delegate, role, scope, reason, start/expiry/status/revocation fields, but the legacy create/revoke routes do not prove delegator authority, maximum privilege, tenant boundary, or scope ownership. |
| Invitation | `MembershipInvitation` and `MembershipService` | **IMPLEMENTED / HARDENING REQUIRED** | Token is hashed and single-use by status; recipient and expiry checks exist. Token response is explicitly limited to creation. Missing atomic row-lock proof and richer bounded audit context. |
| Authorization engine | `AuthorizationDecisionService` | **IMPLEMENTED / HARDENING REQUIRED** | Fail-closed actor/session/membership/scope/resource/policy/permission checks exist. Resource context must be server-resolved by the caller; audit fields are not fully propagated through `AuditService`. |
| Policy engine | `IdentityPolicy` matching in `AuthorizationDecisionService` plus legacy `PolicyService` | **DUPLICATE / PARTIAL** | NIAM and legacy policy evaluators coexist. The legacy evaluator is not a substitute for NIAM context authorization. |
| Context resolver | `get_current_niam_actor` plus `WorkspaceService` | **PARTIAL** | Session actor and workspace eligibility are server-side. Workspace switch audits, but policy/permission cache must be refreshed explicitly after switch. |
| Audit | `IdentityAuditEntry` + `AuditService` and legacy `AuthorizationAudit` | **DUPLICATE / PARTIAL** | Identity audit schema already has facility/workspace/decision/reason/request/correlation columns, but `AuditService.record()`/`record_event()` do not populate all of them. Legacy audit is separate. |

## Membership integrity baseline

`MembershipService` has explicit legal transitions and rejects invalid transitions. `membership_key` is unique and includes account, organization, scope, relationship, and all scope identifiers, which provides duplicate prevention at the canonical NIAM layer. Context validation checks organization, facility, department, unit, and workspace relationships before application or invitation creation.

The remaining integrity risks are lifecycle propagation and management proof. Revoke/suspend/reactivate operations do not visibly invalidate the affected account's active sessions or workspace context in the service shown by the baseline. Organization management checks active ownership/representation records but do not consistently validate account state and validity windows. Invitation acceptance audits invalid tokens using the accepted action name, and direct row locking/idempotent replay under concurrent acceptance is not proven by the current tests.

## Workspace/context baseline

Workspace discovery correctly derives organization workspace access from active, unexpired memberships and does not grant access from organization ownership alone. Unit-scoped memberships without an explicit workspace are prevented from broadening into a wider workspace. Switching validates the eligible set, account ownership, active workspace status, and replaces the session context row.

The frontend still auto-switches when exactly one workspace is returned and caches effective permissions by organization only. This does not prove a server-approved auto-selection policy and can leave stale organization-level permissions after a workspace switch. The safe target is explicit selection unless the server explicitly returns an approved auto-select decision; every switch must refresh the active context and scoped permissions.

## Authorization and legacy surface baseline

`AuthorizationDecisionService` is fail-closed for inactive accounts, invalid sessions, missing memberships, scope mismatch, workspace boundary mismatch, unknown/missing permissions, resource mismatch, policy deny, purpose gates, professional verification, and step-up requirements. It audits denies and sensitive allows. `RolePermissionService` binds role assignments to active memberships and explicit scopes.

The legacy `/authz` router remains a duplicate authorization surface. Its permission checks can combine role assignments with the global `shared.rbac` role mapping, and its delegation create/revoke endpoints call `DelegationService` without an explicit server-side management-authority check. Its resource attributes and delegation scope are client inputs. This is the highest-priority Command 06 compatibility gap because frontend guards and client scope must not become authoritative.

## Audit baseline

`IdentityAuditEntry` already contains the required structural columns: actor, organization, facility, workspace, action, decision, reason, request ID, correlation ID, and timestamp. The current `AuditService` accepts only a subset of these as explicit arguments and usually stores the remainder inside JSON metadata, so downstream queries cannot reliably filter every identity authorization event by facility/workspace/decision/reason/request/correlation. The audit chain hash also excludes the additional context fields.

No raw password, token, OTP, session secret, or unnecessary patient payload should be added while expanding audit context.

## Cross-platform baseline

| Surface | Baseline classification | Evidence | Immediate gap |
|---|---|---|---|
| Web/PWA | **PARTIAL** | `AuthContext`, `MembershipsPage`, `WorkspaceSelector`, and workspace API tests exist. | UI labels scope as `Role / Entitlement`; single-workspace auto-switch is not explicitly server-policy driven; permission cache is organization-level. |
| Android | **UNVERIFIED** | Command 05 native recovery contracts exist. No Command 06 membership/workspace/authorization contract evidence was found in this baseline. | Native build/toolchain was unavailable in Command 05. |
| iOS | **UNVERIFIED** | Command 05 native recovery contracts exist. No Command 06 membership/workspace/authorization contract evidence was found in this baseline. | Xcode/toolchain unavailable locally. |
| Flutter/Desktop | **UNVERIFIED** | Existing identity pages and permissions helper exist. No Command 06 server-context parity evidence was found. | Flutter/Dart toolchain unavailable locally. |

## Baseline safety position

No production deployment, production database, runtime configuration, public registration, provider activation, automatic merge, or privilege bypass is permitted. If a test exposes cross-tenant leakage, IDOR/BOLA, stale privilege after revocation, audit failure, data corruption, unsafe migration, or authorization bypass, implementation must stop at `SAFE_STOP` until the defect is isolated and fixed.
