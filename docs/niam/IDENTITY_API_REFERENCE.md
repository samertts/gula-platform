# GULA Identity Platform — API Reference

> Generated: 2026-08-05T22:30:00+00:00
> Program: PROGRAM-STABLE-003
> Base prefix: `/niam`

---

This reference documents the endpoints added by PROGRAM-STABLE-003. Existing NIAM
endpoints (accounts, auth, devices, persons, sessions, governance, trust,
lifecycle, federation, certificates, workflows, notifications, adaptive-auth,
admin, compliance) remain available and are documented in the platform's
OpenAPI schema at `/docs`.

## Workspaces — `/niam/workspaces`

| Method | Path | Description |
|---|---|---|
| POST | `/niam/workspaces/` | Create a workspace (owner becomes `owner` role member) |
| GET | `/niam/workspaces/{workspace_id}` | Get a workspace |
| GET | `/niam/workspaces/identity/{identity_id}` | List workspaces for an identity |
| PATCH | `/niam/workspaces/{workspace_id}` | Update workspace (owner/admin only) |
| POST | `/niam/workspaces/{workspace_id}/suspend` | Suspend workspace (owner only) |
| POST | `/niam/workspaces/{workspace_id}/select` | Select as the identity's ONE active workspace |
| POST | `/niam/workspaces/{workspace_id}/roles` | Create a role (owner/admin) |
| GET | `/niam/workspaces/{workspace_id}/roles` | List roles |
| POST | `/niam/workspaces/{workspace_id}/members` | Add a member |
| GET | `/niam/workspaces/{workspace_id}/members` | List members |
| POST | `/niam/workspaces/{workspace_id}/members/{person_id}/remove` | Remove a member |
| POST | `/niam/workspaces/{workspace_id}/members/{person_id}/suspend` | Suspend a member |
| POST | `/niam/workspaces/{workspace_id}/members/{person_id}/role` | Assign a role |
| POST | `/niam/workspaces/{workspace_id}/invitations` | Invite a member (owner/admin) |
| POST | `/niam/workspaces/{workspace_id}/invitations/{invitation_id}/revoke` | Revoke an invitation |
| POST | `/niam/workspaces/{workspace_id}/permission-templates` | Create a permission template |
| GET | `/niam/workspaces/{workspace_id}/permission-templates` | List permission templates |
| POST | `/niam/workspaces/{workspace_id}/departments` | Create a department |
| GET | `/niam/workspaces/{workspace_id}/departments` | List departments |
| POST | `/niam/workspaces/{workspace_id}/teams` | Create a team |
| GET | `/niam/workspaces/{workspace_id}/teams` | List teams |
| POST | `/niam/workspaces/{workspace_id}/delegations` | Delegate authority within the workspace |
| GET | `/niam/workspaces/{workspace_id}/permissions/check` | Workspace-scoped permission check |

## Professional Registry — `/niam/professional-registry`

| Method | Path | Description |
|---|---|---|
| POST | `/niam/professional-registry/` | Register a professional (status=pending) |
| GET | `/niam/professional-registry/{registry_id}` | Get a registry entry |
| GET | `/niam/professional-registry/person/{person_id}` | List entries for a person |
| POST | `/niam/professional-registry/{registry_id}/verify` | Verify entry → activates privileges (authority-only) |
| POST | `/niam/professional-registry/{registry_id}/suspend` | Suspend → privileges revoked |
| POST | `/niam/professional-registry/{registry_id}/revoke` | Revoke → verification cleared |
| GET | `/niam/professional-registry/{person_id}/privileges/check` | Is this person professionally privileged? |

## Citizens — `/niam/citizens`

| Method | Path | Description |
|---|---|---|
| POST | `/niam/citizens/providers` | Register a configurable identity provider |
| GET | `/niam/citizens/providers` | List providers (optionally by country) |
| GET | `/niam/citizens/providers/default` | Get the default provider |
| POST | `/niam/citizens/verify-identifier` | Verify a citizen identifier against a provider |

## Session Security (Service-level)

Session endpoints exist under the existing NIAM sessions surface. The
PROGRAM-STABLE-003 additions are service-level:

- `SessionService.bind_workspace(session_id, workspace_id)`
- `SessionService.unbind_workspace(session_id)`
- `SessionService.get_workspace_bound_sessions(workspace_id)`
- `SessionService.enforce_max_concurrent_sessions(account_id, max_sessions, keep_current, current_session_id)`

## Authorization Guards (Service-level)

- `OrganizationAccessGuard.assert_actor_can_administer_org(actor_identity_id, org_id, operation)`
- `ProfessionalRegistryService.is_privileged(person_id, profession)`
- `WorkspaceService.check_permission(workspace_id, identity_id, permission)`
