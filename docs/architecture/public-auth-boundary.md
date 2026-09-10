# GULA Public / Authentication Boundary

**Program:** PUBLIC-001 · **Status:** VERIFIED (investigation) · No code changed.
**Authoritative sources:** `frontend-v3/src/routes/index.tsx`, `backend/app/routes/login.py`,
`backend/app/identity/`, PostgreSQL at head `20260912_0001`.

---

## 1. The single most important finding

**GULA has three login endpoints and two identity systems, and the application
is wired to the one that cannot reach the workspace model.**

| Endpoint | Identity store | Token claims | Used by |
|---|---|---|---|
| `POST /login` | `users` / `lab_users` | `user_id`, `lab_id`, `role`, `perm_ver`, `jti` | **the frontend** (`AuthContext.login`) |
| `POST /citizen/login` | `users` (role='citizen') | same shape | exported in `endpoints.ts`, **no caller in frontend-v3** |
| `POST /niam/auth/login` | `niam_accounts` / `niam_identities` | `account_uuid`, `jti` | **nothing in the frontend** |

`GET /niam/workspaces` requires `payload["account_uuid"]` *and* a matching
`niam_sessions.token_jti` row. A token minted by `/login` carries neither.
**Every workspace call from a real session therefore returns 401**, which
`WorkspaceSelector` renders as the permanent Arabic error
"تعذر تحميل مساحات العمل المصرح بها من الخادم."

This is not a missing feature. The workspace model is **built and correct** —
it is simply unreachable from the door users come through.

## 2. What already exists and is right

`backend/app/identity/api/workspaces.py` implements the constitution almost
exactly, and should be **KEPT**:

* `WorkspaceService.list_eligible(account)` — the **server** decides eligibility.
* `ensure_citizen_workspace(account)` — every account gets a personal citizen
  workspace; the citizen context is the floor, not a separate account.
* `switch()` raises `WorkspaceAccessDenied` → **403 and an audit record of the
  denial**. Selection cannot grant anything.
* `Workspace` carries `workspace_type`, `organization_id`, `facility_id`,
  `department_id`, `professional_type`, `is_personal` — one identity, many
  contexts, exactly as §1 of the constitution requires.

85 `niam_*` tables exist physically, including `niam_memberships`,
`niam_role_assignments`, `niam_permissions`, `niam_consents`, `niam_sessions`,
`niam_devices`, `niam_audit_entries` — and `niam_legacy_account_links`, whose
columns (`legacy_account_id`, `canonical_account_id`, `status`,
`collision_reason`, `rollback_token`, `migrated_at`, `rolled_back_at`) show the
bridge between the two identity systems was **designed and never executed**.

All of them are empty: `niam_accounts` 0, `niam_identities` 0,
`niam_workspaces` 0, `niam_memberships` 0. `lab_users` holds the live users.

`AuthContext` is also right and should be kept: httpOnly cookie session, no
token in browser storage, memberships and effective permissions fetched from the
server, with an explicit comment that they are "server-reflected UX context,
never a local authorization fallback."

## 3. What is wrong

### AUTH-F1 — the entry context is decorative (P4)
`LoginPage` already offers the two contexts the constitution mandates
(`AccessPath = "citizen" | "institution"`). But `accessPath` only changes copy
and a placeholder: `handleSubmit` calls `login({ email, password })` and then
`navigate("/dashboard")` unconditionally. A citizen who chooses **Citizen** lands
on the institutional dashboard. The correct instinct is already in the code; it
just does not reach the server or the post-login route.

### AUTH-F2 — `RoleGuard` is inert outside demo mode (P1)
```ts
if (demoMode && !roles.includes(user.role as UserRole)) return <Navigate to={fallback} />;
```
Outside demo mode **every authenticated user passes every `RoleGuard`**. All 60+
`adminRoles`-guarded routes — `/admin/users`, `/national-data`, `/niam/*`,
`/financial`, `/command-center` — render for any logged-in user. The server still
gates the data, so this is not a confirmed data breach, but the route policy is
cosmetic and must not be mistaken for authorization. Frontend guards are UX;
this one does not even do that.

### AUTH-F3 — `/citizen/login` is parallel authentication (P1)
It re-implements credential lookup, password verification, rate limiting and
token issuance against the same `users` table rather than delegating to the main
flow, despite a docstring calling itself "a thin wrapper around the main login
flow." No frontend calls it. It is a second front door on the same identity.

### AUTH-F4 — citizens are routed into the institutional shell (P2)
`/citizen` is guarded by `RoleGuard roles={["citizen"]}` — inert per AUTH-F2 —
and login always navigates to `/dashboard`. There is no workspace-aware landing.

## 4. The boundary that does not exist

```
PUBLIC WEBSITE → PUBLIC INFORMATION → AUTHENTICATION ENTRY → GULA APPLICATION
     ✗                   ✗                     ✓                    ✓
```

`frontend-v3/src/routes/index.tsx` has exactly four unauthenticated routes:
`/login`, `/register`, `/privacy-policy`, `/terms-of-service`. The index route
is `<Navigate to="/login" replace />`.

**There is no public website.** Not a thin one — none. `/about`, `/platform`,
`/for-citizens`, `/for-organizations`, `/security`, `/interoperability`,
`/contact` do not exist. A visitor who has never heard of GULA reaches a
password form.

The upside: the public/authenticated boundary cannot leak health data, because
there is no public surface at all. The cost: GULA is invisible and unexplained.

## 5. Target boundary (proposed, not implemented)

Keep one application shell and one router. Add a third, public layout sibling to
the existing `AuthLayout` / `DashboardLayout` pair — no second app, no framework
change:

```
PublicLayout   (indexable, no session required, no API calls)
  /  /about  /platform  /for-citizens  /for-organizations
  /security  /privacy  /terms  /accessibility  /interoperability  /contact
AuthLayout     (exists)
  /login  /register  /recovery
DashboardLayout (exists, session required, noindex)
  /dashboard  /citizen  /workspaces  … everything else
```

`/privacy-policy` and `/terms-of-service` move under the public layout and keep
their paths as redirects. `/` stops redirecting to `/login`.

## 6. Recommended sequence

| Batch | Scope | Depends on |
|---|---|---|
| **AUTH-001** | Fix `RoleGuard` (AUTH-F2). One condition. Highest severity, smallest diff. | — |
| **AUTH-002** | Bridge the identity systems: issue `account_uuid` + a `niam_sessions` row from `/login` via `niam_legacy_account_links`, or make `/niam/workspaces` accept a legacy token. **Architecture decision required — do not guess.** | — |
| **AUTH-003** | Make the entry context real: carry it to the server, route citizens to their workspace. | AUTH-002 |
| **PUBLIC-002** | The public layout and its routes. | — (independent) |
| **AUTH-004** | Retire `/citizen/login` once nothing calls it. | AUTH-003 |
