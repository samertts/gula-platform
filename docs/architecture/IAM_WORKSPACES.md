# GULA IAM Workspace Architecture

**Phase status:** `PARTIAL` until previous phases, live migrations, full backend authorization, mobile parity and all security gates are complete.

## Definition

A Workspace is the operational context in which an existing GULA account interacts with the platform. It is not an account, identity, organization, role or permission. This phase deliberately does not implement memberships, RBAC or ABAC; it provides the context boundary that later phases will authorize.

The canonical relationship is:

```text
Account → Identity → Workspace Context → Membership (Phase 6) → Role/Permission (later phases)
```

A workspace never creates an account and never duplicates an identity.

## Workspace types

The type registry is extensible and currently includes `citizen`, `professional`, `organization`, `facility`, `department`, `administrative`, `government`, `audit`, `security` and `support`. These are context categories, not authorization roles. New types can be added without changing the table schema.

## Workspace lifecycle

A workspace follows a backend-only state machine: `provisioning → active`, `active → restricted|suspended|archived|deactivated`, `restricted → active|suspended|archived|deactivated`, `suspended → active|archived|deactivated`, and terminal `archived`/`deactivated` states. The frontend cannot set a status.

## Provisioning

A human active account receives one deterministic Citizen Workspace key, `citizen:{account_id}`. The unique database key and service lookup make provisioning idempotent. The current authentication flow invokes this provisioning after a successful active-account session is created; a later account lifecycle integration should invoke the same service at activation time.

A Professional Workspace requires an active, non-expired, backend-verified professional `VerificationRecord`. A selected profession is insufficient. Organization and facility workspaces are structural records created only after the organization/facility lifecycle approves them. Administrative, government, audit and security workspaces require explicit provisioning and never grant unrestricted super-admin access.

## Eligibility and switching

The backend extracts `account_uuid` and `jti` from the NIAM access token, verifies the account status, verifies the active `UserSession`, and resolves the internal session ID. `GET /niam/workspaces` returns only workspaces eligible for that account. `POST /niam/workspaces/{id}/switch` validates eligibility and writes a server-authoritative `WorkspaceSessionContext` tied to that session. The frontend cannot switch by changing localStorage alone.

Organization workspace eligibility currently uses active `OrganizationRepresentative` or `OrganizationOwnership` records. Membership and contextual authorization remain Phase 6 and later. Suspended accounts, inactive sessions, suspended workspaces, archived workspaces and unknown IDs are denied or omitted.

## Database model

`niam_workspaces` stores the workspace identity, extensible type, lifecycle status, owner account, organization/facility/department context, professional type, provisioning actor, personal flag and optimistic version. `niam_workspace_contexts` stores the active workspace for a validated NIAM session, account and identity, with a version and foreign keys.

The migration is additive and reversible. It does not alter clinical tables or copy people/accounts. Historical workspaces are archived or deactivated rather than casually deleted.

## API contract

The canonical endpoints are:

| Method | Route | Server behavior |
|---|---|---|
| `GET` | `/niam/workspaces` | Return only eligible workspaces; idempotently ensure the citizen workspace for an active human account. |
| `GET` | `/niam/workspaces/{id}` | Return one workspace only if eligible; unknown or unauthorized IDs return not found. |
| `POST` | `/niam/workspaces/{id}/switch` | Validate NIAM access token, session, account state and eligibility, then establish a versioned server context. |

No client-supplied account ID, identity ID, organization ID or assurance level is trusted for authorization.

## Frontend and mobile boundary

The frontend selector uses only the backend workspace list and backend switch response. It displays loading, empty, failure and demo-mode states and does not fabricate workspace IDs. Direct clinical reads remain blocked by the existing frontend governance gate. Mobile clients are not yet integrated with these APIs; they must consume the same contracts in a later parity phase and must not create a platform-specific workspace database.

## Audit and observability

Workspace provisioning and switching use the existing hash-chained NIAM audit service. Denied switching is recorded as a denied audit event without logging secrets or clinical data. The workspace model contains no raw medical data, documents or provider secrets.

## Security boundaries

Workspace hierarchy is not authorization. A workspace ID alone does not confer ownership. Account status, active session, direct ownership/representative eligibility and workspace status are checked server-side. The selector and API client are defensive conveniences, not the security boundary.

## Deferred work

Phase 6 must implement memberships and invitations. Later phases must implement role/permission context, complete organization/facility authorization, document storage, mobile parity, full API integration tests, concurrency tests, live migration tests, real provider integrations and production readiness. This document does not claim Iraqi Ministry of Health integration.
