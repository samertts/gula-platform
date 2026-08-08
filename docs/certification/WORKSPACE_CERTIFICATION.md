# GULA Workspace Platform — Certification Report

> Generated: 2026-08-05T22:30:00+00:00
> Program: PROGRAM-STABLE-003
> Module: `backend/app/identity/workspaces/`

---

## Certification Verdict

**CERTIFIED — WORKSPACE READY**

The workspace platform provides the single multi-workspace compartment model for
the entire GULA platform. The user selects ONE workspace after login and
permissions never cross workspace boundaries.

## Workspace Model

| Concept | Table | Purpose |
|---|---|---|
| Workspace | `niam_workspaces` | Logical compartment owned by an identity, optionally bound to an organization |
| Workspace Role | `niam_workspace_roles` | Role scoped to a single workspace (owner/admin/manager/member/viewer) |
| Workspace Membership | `niam_workspace_members` | Identity↔workspace link with one scoped role |
| Permission Template | `niam_workspace_permission_templates` | Reusable permission sets owners can assign |
| Department | `niam_workspace_departments` | Department within a workspace's organization |
| Team | `niam_workspace_teams` | Team within a workspace, optionally under a department |
| Invitation | `niam_workspace_invitations` | Token-based invite to join under a role |
| Delegation | `niam_workspace_delegations` | Temporary authority delegation inside one workspace |

## Workspace Types

citizen, personal, professional, laboratory, pharmacy, radiology, hospital,
blood_bank, public_health, insurance, research, government.

## Isolation Guarantees (Verified by Tests)

1. **Permissions never cross workspaces** — `check_permission` resolves the
   membership inside the given workspace only; an identity with admin rights in
   ws1 receives `False` in ws2. (test `test_isolation_across_workspaces`)
2. **One active workspace per identity** — `select_active_workspace` clears all
   other selections before binding. (test `test_select_active_workspace_requires_membership`)
3. **Role-gated mutation** — `update_workspace`/`create_role`/`invite_member`
   require owner/admin role. (tests `test_update_workspace_denied_for_non_admin`,
   `test_suspend_workspace_requires_owner`)
4. **Membership state honored** — suspended members lose all roles.
   (test `test_has_role_rejects_suspended_member`)

## API Surface (23 endpoints)

`/niam/workspaces/` — CRUD, suspend, select-active, roles, members, invitations,
permission-templates, departments, teams, delegations, permission check.

## Verified Facts

- **Tests:** 16 workspace tests pass (models + service).
- **Database:** 8 tables created in `20260805_0002`; FK cascade/set-null verified on PostgreSQL.
- **Lint:** ruff clean.

## Open Items

- Frontend workspace selector UI (post-login one-workspace selection).
- Integration of `WorkspaceService.check_permission` into the authorization layer for domain routes.
