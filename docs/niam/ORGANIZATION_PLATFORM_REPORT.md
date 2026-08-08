# GULA Organization Platform — Report

> Generated: 2026-08-05T22:30:00+00:00
> Program: PROGRAM-STABLE-003
> Module: `backend/app/identity/organizations/` + `backend/app/identity/models/niam_organization.py`

---

## Verdict

**CERTIFIED — ZERO CROSS-DOMAIN ADMINISTRATION**

## Mandate

"Organization owners manage only their own organization." No actor may read,
mutate, or administer another organization's records through the identity
platform.

## Enforcement Point

`OrganizationAccessGuard` in `backend/app/identity/organizations/guard.py`:

```
assert_actor_can_administer_org(actor_identity_id, org_id, operation)
```

Decision rules (in order):
1. Target organization must exist and be active → else `organization_not_found`.
2. Actor must be the owner (or owner-role member) of an **active workspace bound
   to that organization** → else `OrganizationAccessDeniedError`.

Any workspace bound to a different organization is skipped. An actor whose
workspaces all belong to other organizations is always denied.

## Verified Behaviors (Tests)

| Scenario | Result |
|---|---|
| Org owner administers own org | ✅ allowed (`org_owner`) |
| Owner of workspace bound to org | ✅ allowed (`org_owner`) |
| Owner-role member of workspace bound to org | ✅ allowed (`workspace_owner`) |
| Member of a different org's workspace | ❌ denied |
| Non-member of the org | ❌ denied (raises) |
| Missing / suspended organization | ❌ denied |
| Inactive workspace | ❌ denied (grants no authority) |

## Hierarchy Compatibility

The organization hierarchy (`NIAMOrganization.parent_org_id` for ministry →
health directorates → hospitals → laboratories) is preserved. The guard operates
at the org boundary regardless of depth, ensuring zero cross-domain
administration at every hierarchy level.

## Verified Facts

- **Tests:** 8 org-guard tests pass.
- **Lint:** ruff clean.

## Open Items

- Wire `OrganizationAccessGuard` into the enterprise portal admin routes
  (`/niam/admin`) as a dependency before creating/reading org-scoped resources.
