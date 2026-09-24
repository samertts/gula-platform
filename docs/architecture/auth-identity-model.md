# GULA Identity, Account and Session Model

**Program:** AUTH-002 · **Status:** VERIFIED · No production code changed.
**Evidence:** `app/routes/login.py`, `app/security/{auth,dependencies}.py`,
`app/identity/`, PostgreSQL at head `20260912_0001`.

---

## 1. The two stacks side by side

| | Legacy | NIAM |
|---|---|---|
| Subject table | `lab_users` **or** `users` | `niam_accounts` |
| Person layer | none | `niam_identities`, `niam_persons` |
| Primary key | `INTEGER`, **independent per table** | `String(26)` |
| Public identifier | none — the integer id is the only handle | `uuid` (`String(36)`, unique) |
| Token subject | `user_id` | `account_uuid` (+ `identity_id`) |
| Token format | JWT via `create_token` | **the same** `create_token` |
| Signing key | `SECRET_KEY` | **the same** `SECRET_KEY` |
| Session record | **none** | `niam_sessions` row per login |
| Session identifier | `jti` only, in the token | `niam_sessions.uuid` + `token_jti` |
| Revocation | blacklist a `jti`; bump `perm_version` | deactivate the session row; per-session and terminate-all |
| Device / IP / UA | not captured | captured on the session row |
| Refresh | stateless refresh JWT | refresh JWT **bound to the session row** |
| Organization context | `lab_id` on the token | `niam_organizations` + representatives / ownerships |
| Workspace | none | `niam_workspaces`, `niam_workspace_contexts` |
| Role / permission | `role` string on the token + `perm_ver` | `niam_roles`, `niam_role_assignments`, `niam_permissions` |
| MFA | `mfa_sessions` (separate) | `mfa_used` on the session, plus adaptive-auth tables |

**The two stacks share the JWT machinery and differ only in claims.** That single
fact is what makes a bridge additive rather than a second authentication system.

## 2. Canonical concept map

| Concept | Canonical owner | Key | Public id |
|---|---|---|---|
| **Person** | `niam_persons` / `niam_identities` | `String(26)` | `uuid` |
| **Identity** | `niam_identities` | `String(26)` | `uuid` |
| **Account** | `niam_accounts` (`identity_id` → identity) | `String(26)` | `uuid` |
| **Citizen** | an Account with a personal workspace (`is_personal`) — **not a separate account type** | — | — |
| **Organization** | `niam_organizations` | `String(26)` | `uuid` |
| **Facility / Department** | referenced from `Workspace` (`facility_id`, `department_id`); ownership still open under NR-006 | — | — |
| **Membership** | `niam_memberships` (+ applications, invitations) | `String(26)` | — |
| **Workspace** | `niam_workspaces` | `String(26)` | `uuid` |
| **Workspace context** | `niam_workspace_contexts` (account + identity + workspace + version) | `String(26)` | — |
| **Role** | `niam_roles`, assigned via `niam_role_assignments` | `String(26)` | — |
| **Permission** | `niam_permissions`, `niam_role_permissions` | `String(26)` | — |
| **Session** | `niam_sessions` | `String(26)` | `uuid` |
| **Token** | JWT, `app/security/auth.py` | `jti` | — |

## 3. Duplicate identity concepts found

### D1 — `users` and `lab_users` are two identity tables behind one claim
`get_current_user` (`app/security/dependencies.py:65-71`) resolves `user_id` by
querying `LabUser` **first**, then falling back to `User`. Both tables have
independent `INTEGER` primary keys, and the token carries no discriminator.
**A token claiming `user_id = 5` is ambiguous by construction**; if both tables
hold id 5, the `LabUser` silently wins.

The platform already knows this is a problem elsewhere: `get_perm_version` takes
an explicit `account_kind="user"|"lab"` argument, and `LegacyAccountLinkSource`
is exactly the enum `{user, lab_user}` — the discriminator the token lacks.

*This is a latent account-takeover class, currently unexploitable only because
`users` holds 0 rows. It becomes exploitable the moment citizens are registered.*

### D2 — three authentication endpoints on two identity stores
`POST /login`, `POST /citizen/login` (legacy), `POST /niam/auth/login` (NIAM).
See `public-auth-boundary.md`.

### D3 — `Citizen` is defined three times
`app/services/mpi/models.py:42`, `app/national/domain/citizen.py:11`, and the
`niam_*` citizen concepts (`niam_citizen_relationships`, `niam_lifecycle_citizen`).
Only the MPI one is reachable from the running app. Not in AUTH-002's scope;
recorded for the identity-consolidation batch.

## 4. Workspace eligibility — how the server actually decides

`WorkspaceService.list_eligible(account)` returns, for an **active** account only:

1. workspaces the account **owns** (`owner_account_id`) — this is the personal
   citizen workspace created by `ensure_citizen_workspace`; and
2. workspaces of organizations where the account is an active
   `OrganizationRepresentative` **or** `OrganizationOwnership`.

`switch()` re-derives eligibility, refuses anything not in that list or not
`active`, and audits the denial. **Selection grants nothing** — the constitution
holds.

**Gap worth naming:** `niam_memberships` is *not* consulted by `list_eligible`.
`GET /niam/memberships/me` exists and `AuthContext` fetches it, but a membership
alone does not currently make a workspace eligible — only representative or
ownership status does. Either memberships must feed eligibility, or the
membership concept needs a stated purpose distinct from it. **Recorded as
AUTH-F5; it is a design question, not a defect.**
