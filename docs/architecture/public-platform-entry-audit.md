# GULA Public Platform Entry — Audit

**Program:** PUBLIC-001 · **Status:** VERIFIED (investigation) · No code changed.

---

## 1. Does the current surface answer the six questions?

| Question | Answered? | Evidence |
|---|---|---|
| What is GULA? | **No** | `/` redirects to `/login`. The only description is a `<meta>` tag reading "منصة غولا - نظام معلومات المختبرات الطبية" — *a medical laboratory information system*, not a national health platform. |
| Why does GULA exist? | **No** | no public page states a purpose |
| Who is GULA for? | **Partially** | only inside the login card, as two access options |
| How does GULA work? | **No** | — |
| How does GULA protect data? | **Partially** | `/privacy-policy` exists but is reachable only from the login page |
| How do I enter GULA? | **Yes** | the login page is the entire public surface |

The document title is "جولا | مركز العمليات الصحية" while the meta description
calls it a laboratory system and the manifest name is a third variant. GULA does
not currently describe itself consistently anywhere a visitor can see.

## 2. Public information architecture — current vs proposed

**Current unauthenticated routes (4):** `/login`, `/register`, `/privacy-policy`,
`/terms-of-service`. Index → `/login`.

**Proposed (canonical, derived from the existing router — see
`public-auth-boundary.md` §5):** a `PublicLayout` sibling to the existing
`AuthLayout`/`DashboardLayout`, carrying `/`, `/about`, `/platform`,
`/for-citizens`, `/for-organizations`, `/security`, `/privacy`, `/terms`,
`/accessibility`, `/interoperability`, `/contact`. Existing legal paths keep
working as redirects. **One router, one design system, one shell** — no second
application.

`/for-organizations` is the correct name, not `/for-labs`: the platform models
hospitals, laboratories, pharmacies, primary health centres and directorates as
`niam_organizations` with `facility_id`/`department_id`, and the constitution
forbids per-profession entry points.

## 3. Homepage — proposed structure

The philosophy the homepage must carry — **people-centred, institution-powered,
government-governed** — has no expression anywhere in the repository today.

Recommended sections, ordered so a visitor understands GULA in seconds and the
page never becomes a feature list:

1. **Hero** — one sentence on what GULA is, and the two entry actions.
2. **What is GULA** — the person → institution → GULA → health system relation.
3. **How it works** — three steps, no jargon.
4. **For citizens** — your record follows you; you can see who looked at it.
5. **For organizations** — join the platform, keep your own systems.
6. **For the health system** — governance and oversight.
7. **Privacy and security** — links to `/security` and `/privacy`; claims only
   what §4 below permits.
8. **Interoperability** — FHIR/HL7 (the repository has real evidence here).
9. **Call to action** — enter, or apply for an organization account.

Deliberately excluded: the 60+ capability pages in the authenticated app. They
are product surface, not public messaging.

## 4. Legal and claims discipline

`LegalPage` renders four i18n sections per document and — importantly — a
standing `legal.reviewNotice` banner. It does **not** claim compliance with any
law, standard or certification. That is correct and must be preserved.

**No compliance claim may be added to the public site.** The repository contains
no evidence of certification against any regime. Health Data Policy, cookies,
third-party processing, AI/data processing, retention and data-minimisation
statements do not exist and are **NOT STARTED**; all of them require legal
review before publication, not engineering.

## 5. SEO — findings

| Item | State |
|---|---|
| `robots.txt` | **absent** (`frontend-v3/public/` has no robots.txt) |
| `sitemap.xml` | **absent** |
| OpenGraph / Twitter tags | **absent** |
| canonical link | **absent** |
| structured data | **absent** |
| `<html lang>` / `dir` | **hardcoded `ar` / `rtl`** — English is switched at runtime only, so a crawler always sees Arabic RTL |
| title / description | LIMS-era wording, inconsistent with the platform |
| authenticated route exclusion | not expressed — no robots.txt, no `noindex` on app routes |

Nothing is indexable today because everything redirects to `/login`, so **no
health data can leak into an index**. Once a public layout exists, `robots.txt`
plus `noindex` on the authenticated tree becomes mandatory, not optional.

## 6. Performance — findings

The security headers in `vercel.json` are strong (HSTS preload, frame-ancestors
none, object-src none, strict CSP). Two concrete issues:

* **CSP blocks the site's own fonts (P3).** `index.html` loads Tajawal from
  `fonts.googleapis.com`/`fonts.gstatic.com`, but the CSP allows
  `style-src 'self' 'unsafe-inline'` and `font-src 'self'` — neither host is
  listed. In production the font stylesheet and files are blocked and the page
  falls back to a system font. Either self-host Tajawal (which also removes a
  third-party dependency and a render-blocking round trip, and suits a sovereign
  platform) or add the hosts. **Self-hosting is the recommendation.**
* **Every route is `lazy()`-loaded but the public entry pays for the app.** The
  router imports `AuthContext`, `DashboardLayout` and the legacy route bridge
  before it can render `/login`. A public visitor should download a public
  bundle only. The proposed `PublicLayout` must not import `AuthContext`.

No new dependency is needed for any of this.

## 7. Accessibility — findings

Good, and to be preserved: an `AccessibilityContext` and a dedicated
`/settings/accessibility` centre exist; `WorkspaceSelector` has its own a11y
test; `LoginPage` uses `role="group"`, `aria-pressed`, `aria-busy`,
`role="alert"`, `sr-only` labels and visible focus rings; `LegalPage` uses
`aria-labelledby` per section.

Gaps: the language switcher is a `<select>` inside the login card only — there
is no site-level language control for a public visitor; `dir`/`lang` are
hardcoded on the document; no skip-link was found; error messages in
`WorkspaceSelector` are hardcoded Arabic strings rather than i18n keys, so an
English user sees Arabic errors.

## 8. Disposition

| Area | Decision |
|---|---|
| `AuthContext` (cookie session, server-reflected memberships) | **KEEP** |
| `backend/app/identity/api/workspaces.py` + `WorkspaceService` | **KEEP** — already correct |
| NIAM tables, `niam_legacy_account_links` | **KEEP** — the bridge is designed, not built |
| `LoginPage` two-context UI | **IMPROVE** — make the context real (AUTH-003) |
| `RoleGuard` | **IMPROVE** — one inverted condition (AUTH-001) |
| Identity bridge `/login` → NIAM | **BLOCKED** — architecture decision (AUTH-002) |
| Public website | **NOT STARTED** → PUBLIC-002 |
| Homepage | **NOT STARTED** → PUBLIC-002 |
| `robots.txt`, sitemap, OG, canonical, lang/dir | **NOT STARTED** → SEO-001 |
| Self-hosted fonts / CSP alignment | **IMPROVE** → SEO-001 |
| Privacy Centre | **BLOCKED** — see `privacy-legal-architecture.md` |
| Health Data Policy, cookies, retention, AI processing | **NOT STARTED** — legal review first |
| `/citizen/login` | **DUPLICATE / REMOVE** — after AUTH-003 |
| `citizenPortalApi` in `endpoints.ts` | **DUPLICATE / REMOVE** — no caller |
| Design system, layouts, i18n | **KEEP** — reuse, do not replace |
