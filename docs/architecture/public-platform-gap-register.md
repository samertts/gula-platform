# Public Platform Gap Register (PUBLIC-001)

Every finding carries ID, Severity, Area, Evidence, Current State, Risk,
Canonical Owner, Dependency, Recommended Action, Status.
Companion documents: `public-auth-boundary.md`, `public-platform-entry-audit.md`,
`privacy-legal-architecture.md`.

---

## P1 — identity / auth / authorization / architectural correctness

### PUB-001 · Two identity systems, and the app is on the wrong one
* **Area** authentication / identity
* **Evidence** `POST /login` (`app/routes/login.py:191`) mints
  `{user_id, lab_id, role, perm_ver, jti}`. `get_current_niam_actor`
  (`app/identity/api/workspaces.py`) requires `payload["account_uuid"]` **and** a
  matching `niam_sessions.token_jti`. `niam_accounts`=0, `niam_identities`=0,
  `niam_workspaces`=0, `niam_memberships`=0; `lab_users`=6.
* **Current state** every `/niam/*` call from a real session returns 401.
  `WorkspaceSelector` shows a permanent Arabic error.
* **Risk** the workspace, membership, consent, session, device and audit
  platforms are all built and all unreachable. Any feature built on them today
  would have to fabricate data or fork the identity model.
* **Canonical owner** Identity Platform (NIAM)
* **Dependency** `niam_legacy_account_links` exists (with `status`,
  `collision_reason`, `rollback_token`) — the bridge was designed, never run.
* **Action** AUTH-002. **Architecture decision required — do not guess** whether
  `/login` mints NIAM tokens or `/niam/*` accepts legacy ones.
* **Status** VERIFIED

### PUB-002 · `RoleGuard` is inert outside demo mode
* **Area** frontend authorization
* **Evidence** `frontend-v3/src/components/auth/RoleGuard.tsx`:
  `if (demoMode && !roles.includes(user.role as UserRole))`.
* **Current state** outside demo mode every authenticated user passes every
  guard — `/admin/users`, `/national-data`, `/niam/*`, `/financial`,
  `/command-center` and 60+ other routes.
* **Risk** the route policy is cosmetic. The server still gates data, so no
  breach is confirmed, but the guard must never be mistaken for authorization.
* **Canonical owner** frontend platform
* **Dependency** none
* **Action** AUTH-001 — invert one condition; verify against the server's own
  role checks before changing behaviour.
* **Status** VERIFIED

### PUB-003 · `/citizen/login` is parallel authentication
* **Area** authentication
* **Evidence** `app/routes/citizen_portal.py:137` re-implements lookup, password
  verification, rate limiting and token issuance on the same `users` table.
  Its own docstring calls it "a thin wrapper around the main login flow".
* **Current state** live and mounted; no frontend-v3 caller.
* **Risk** a second front door on one identity; divergent lockout, audit and
  enumeration behaviour.
* **Canonical owner** Identity Platform
* **Dependency** PUB-005 (citizen routing) must land first
* **Action** AUTH-004 — retire, or reduce to a genuine delegation.
* **Status** VERIFIED

## P2 — reliability / operational

### PUB-004 · No public website exists
* **Area** public surface
* **Evidence** `frontend-v3/src/routes/index.tsx` — 4 unauthenticated routes;
  index is `<Navigate to="/login" replace />`.
* **Current state** a first-time visitor reaches a password form.
* **Risk** GULA cannot explain itself, recruit organizations, or be found.
* **Canonical owner** frontend platform
* **Dependency** none — independent of the identity work
* **Action** PUBLIC-002 — a `PublicLayout` sibling to the existing layouts. One
  router, one design system.
* **Status** NOT STARTED

### PUB-005 · Citizens are routed into the institutional shell
* **Area** UX / workspace
* **Evidence** `LoginPage.handleSubmit` → `navigate("/dashboard")`
  unconditionally; `/citizen` is guarded by an inert `RoleGuard`.
* **Risk** the citizen experience is unreachable by default.
* **Canonical owner** frontend platform
* **Dependency** PUB-001
* **Action** AUTH-003
* **Status** VERIFIED

### PUB-006 · The Privacy Centre backend is complete and unreachable
* **Area** privacy
* **Evidence** `/niam/consents` (grant/me/check/withdraw), `/niam/sessions`
  (list/terminate/terminate-all), `/niam/devices`, `/niam/audit`
  (list/export/integrity), `/niam/memberships/me` — all present, all requiring a
  NIAM token. `niam_consents`, `niam_sessions`, `niam_devices`,
  `niam_audit_entries` all exist and are empty.
* **Risk** building the UI before the bridge means fabricating data or forking
  consent. Both forbidden.
* **Canonical owner** Identity Platform
* **Dependency** PUB-001
* **Action** PRIVACY-001 / PRIVACY-002, after AUTH-002.
* **Status** BLOCKED

### PUB-007 · The citizen workspace's medication panels cannot load
* **Area** citizen experience / cross-batch
* **Evidence** `CitizenWorkspacePage` calls `/citizen-platform/me/medications`
  and `/me/medication-dispenses`; `app/citizen_platform/medications.py` and
  `routes.py` import `MedicationStatement`/`MedicationDispense`, whose tables do
  not exist (NR-032, BATCH-3.1).
* **Risk** the citizen surface fails on two of its seven panels.
* **Canonical owner** Pharmacy (dispensing) — see
  `nursing-medication-ownership.md`
* **Dependency** NR-032 / MED-001
* **Action** covered by MED-001; no separate work.
* **Status** VERIFIED

## P3 — performance / maintainability

### PUB-008 · CSP blocks the site's own fonts
* **Area** performance / security headers
* **Evidence** `index.html` loads Tajawal from `fonts.googleapis.com` /
  `fonts.gstatic.com`; `vercel.json` CSP allows `style-src 'self' 'unsafe-inline'`
  and `font-src 'self'` — neither host listed.
* **Current state** in production the font stylesheet and files are blocked; the
  page falls back to a system font.
* **Risk** degraded Arabic typography; a silent third-party dependency on a
  sovereign platform.
* **Canonical owner** frontend platform
* **Dependency** none
* **Action** SEO-001 — **self-host Tajawal** (removes the dependency, the
  render-blocking round trip and the CSP conflict at once).
* **Status** VERIFIED

### PUB-009 · No SEO surface at all
* **Area** SEO
* **Evidence** no `robots.txt`, no `sitemap.xml`, no OpenGraph, no canonical, no
  structured data; `<html lang="ar" dir="rtl">` hardcoded; title/description are
  LIMS-era and mutually inconsistent.
* **Risk** invisible platform. Once a public layout exists, the absence of
  `robots.txt` and `noindex` becomes a **privacy** risk, not just a marketing one.
* **Canonical owner** frontend platform
* **Dependency** PUBLIC-002
* **Action** SEO-001
* **Status** NOT STARTED

### PUB-010 · The public entry pays for the application bundle
* **Area** performance
* **Evidence** `routes/index.tsx` imports `AuthContext`, `DashboardLayout`,
  `LegacyRouteBridge` eagerly before `/login` can render.
* **Action** PUBLIC-002 — `PublicLayout` must not import `AuthContext`.
* **Status** VERIFIED

## P4 — UX / cosmetic

### PUB-011 · The entry context is decorative
* **Area** authentication UX
* **Evidence** `LoginPage` has `AccessPath = "citizen" | "institution"`, but
  `accessPath` only changes copy and a placeholder; `handleSubmit` sends
  `{email, password}` and navigates to `/dashboard` either way.
* **Note** the constitution's shape is already in the UI — this is a gap between
  intent and wiring, not a wrong design.
* **Action** AUTH-003
* **Status** VERIFIED

### PUB-012 · Hardcoded Arabic error strings in an i18n app
* **Evidence** `WorkspaceSelector.tsx` — four user-visible Arabic literals.
* **Action** fold into AUTH-003.
* **Status** VERIFIED

### PUB-013 · Dead client-side API surface
* **Evidence** `citizenPortalApi` is exported from `endpoints.ts` with no caller
  in `frontend-v3`.
* **Action** remove with AUTH-004.
* **Status** VERIFIED

---

## Architectural contradictions (first-class findings)

| Contradiction | Evidence | Verdict |
|---|---|---|
| **duplicate identity** | `users`/`lab_users` vs `niam_accounts`/`niam_identities` | **CONFIRMED** — PUB-001 |
| **duplicate authentication** | `/login`, `/citizen/login`, `/niam/auth/login` | **CONFIRMED** — PUB-001, PUB-003 |
| **citizen vs professional** | modelled correctly server-side (`is_personal`, `professional_type` on one `Workspace`); the frontend still branches on a single `user.role` | **PARTIAL** — server right, client behind |
| **workspace vs authorization** | `switch()` returns 403 + audits denial; selection grants nothing | **NO CONTRADICTION** — correct |
| **frontend vs backend authority** | `AuthContext` documents memberships as "never a local authorization fallback"; but `RoleGuard` is inert | **PARTIAL** — PUB-002 |
| **consent vs authorization** | `niam_consents` is separate from `niam_role_assignments`/`niam_permissions` | **NO CONTRADICTION** — correct, and must stay so |
| **organization vs facility** | one `Workspace` carries `organization_id`, `facility_id`, `department_id` | **NO CONTRADICTION** — but NR-006 (`national_facilities` ownership) is still open |
| **public vs authenticated** | no public surface exists at all | **NOT APPLICABLE YET** — PUB-004 |
| **duplicate privacy / consent** | exactly one consent store (`niam_consents`); no second one found | **NO CONTRADICTION** |

## Duplicate / parallel systems

| System | Duplicate? | Action |
|---|---|---|
| `/citizen/login` | **yes** — parallel auth on one identity | retire (AUTH-004) |
| `citizenPortalApi` client | **yes** — dead | remove |
| NIAM vs legacy identity | **yes** — two stores, bridge designed not built | AUTH-002 |
| Consent | no — single store | — |
| Workspace | no — single service | — |
| Design system / layouts | no | reuse |

## Recommended implementation sequence

| Order | Batch | Why here | Blocking |
|---|---|---|---|
| 1 | **AUTH-001** — fix `RoleGuard` | highest severity, smallest diff, no dependency | no |
| 2 | **PUBLIC-002** — public layout + homepage + IA | fully independent of identity work; unblocks all public messaging | no |
| 3 | **AUTH-002** — identity bridge | **decision required first**; unblocks workspaces, privacy, memberships | **yes** |
| 4 | **AUTH-003** — real entry context + citizen routing | needs AUTH-002 | no |
| 5 | **PRIVACY-001** — access history, sessions, devices | needs AUTH-002 | no |
| 6 | **SEO-001** — robots, sitemap, OG, lang/dir, self-hosted fonts | needs PUBLIC-002 | no |
| 7 | **PRIVACY-002** — consent view and withdrawal | needs PRIVACY-001 | no |
| 8 | **LEGAL-001** — security / accessibility / cookies statements | independent | no |
| 9 | **AUTH-004** — retire `/citizen/login` and dead client API | needs AUTH-003 | no |
| — | **LEGAL-002** — Health Data Policy, retention, AI processing | **legal review, not engineering** | — |

## National-scale compatibility requirements (identified, not implemented)

The architecture is compatible, provided the bridge lands: `niam_identities` is
distinct from `niam_accounts` (identity vs account, the right separation for
civil-identity integration); `niam_organizations` + `niam_verification_records` +
`niam_trust_*` cover organization verification; `niam_fed_*` covers federation;
`niam_licenses`/`niam_credentials` cover provider identity; Pharmacy and Nursing
tables already carry `fhir_id`/`fhir_resource_type`. Two open items constrain it:
NR-006 (`national_facilities` ownership) and NR-022 (the National Core tables).
Neither is in PUBLIC-001's scope.
