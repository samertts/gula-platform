# Team A5 — Adversarial Frontend / UX Audit

**Audit ID:** A5
**Scope:** `frontend-v3` in the `gula-integration` working tree at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549` (dirty tree; audited as observed).
**Method:** READ-ONLY static adversarial review. No browser session, no build, no test execution, no network.
**Overall verdict on audited work:** **BLOCKED** for offline/UX readiness claims. Core UI is `IMPLEMENTED`; offline UX and locale-switch consistency have material gaps. No `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` status is awarded.

## 0. What was confirmed and deliberately NOT reported

Adversarial discipline: several plausible concerns were checked and **not** raised because the evidence disproves them.

- **Synthetic/demo data is largely honestly labelled.** Examples: `frontend-v3/src/pages/integration/HealthEcosystemPage.tsx:168` renders an explicit `بيانات تجريبية فقط` ("demo data only") badge; `LabOperationsWorkspacePage.tsx:145,150` show notices that actions were simulated locally and "لم تُرسل النتيجة إلى أي نظام خارجي" (nothing was sent to any external system); device pages use `SYNTHETIC_*` constants (e.g. `DeviceIntegrationWorkspacePage.tsx:51,234,248`). No finding is raised for undisclosed synthetic data.
- **RTL/Arabic-first is an explicit project invariant.** Nothing in this report recommends removing Arabic-first or RTL defaults; the finding below asks only that the *runtime locale switch* be honoured consistently.

## 1. Findings

### AUD-FE-001 — "Offline-first" PWA caches only static assets; no clinical data or API cache (HIGH)

- **Evidence**
  - `frontend-v3/src/main.tsx:6-17` — registers the service worker via `virtual:pwa-register`; this is the entire offline-related bootstrap.
  - `frontend-v3/vite.config.ts:45-47` — `globPatterns: ['**/*.{js,css,html,ico,png,svg,woff2}']` (build assets only).
  - `frontend-v3/vite.config.ts:47-70` — runtime caching covers only image extensions and Google Fonts; no API or data endpoint is cached.
  - Repo-wide search of `frontend-v3/src`: no `indexedDB`, `idb`, `Dexie`, `localforage`, `navigator.onLine`, or background-sync usage.
- **Reproduction / falsification:** Load the built app, go offline, navigate to a patient/order/results view: the shell renders but data cannot be loaded or queued. Falsify by identifying a client data store plus an offline queue that survives reload and re-syncs online.
- **Root cause:** Offline implemented at the asset layer (Workbox) and in backend in-process harnesses, with no browser persistence layer.
- **Impact:** The platform cannot satisfy offline-first clinical workflows in the browser; no offline action survives a page reload. Client offline data capability is `NOT IMPLEMENTED` (corroborates AUD-OFF-003).
- **Severity:** HIGH · **Likelihood:** HIGH (code fact) · **Status:** `DISCOVERED` · **owner_gated:** YES (offline-first is an owner/constitution invariant; any readiness claim is owner-gated).
- **Recommended remediation:** With owner approval, add an encrypted IndexedDB outbox with idempotency keys, cache only the reference/read data needed for offline workflows, wire it to the server's quarantine-based conflict path, and add an offline→online browser test.
- **Alternatives:** (a) Declare the web app online-only and scope offline to a dedicated client; (b) offer a minimal read-only offline reference cache with explicit "no clinical data offline" UX.

### AUD-FE-002 — Hardcoded Arabic/RTL in document and manifest conflicts with runtime locale switching (MEDIUM)

- **Evidence**
  - `frontend-v3/index.html:2` — `<html lang="ar" dir="rtl">` hardcoded in the initial document.
  - `frontend-v3/vite.config.ts:23-24` — PWA manifest hardcodes `lang: 'ar'`, `dir: 'rtl'`.
  - `frontend-v3/src/contexts/LocaleContext.tsx:29-31` — `document.documentElement.lang`, `.dir`, and `--gula-reading-direction` are updated at runtime by the locale context.
  - `frontend-v3/src` — 14 literal `dir="rtl"` attributes across 13 `.tsx` files (repo-wide grep), which do not follow the runtime direction.
- **Reproduction / falsification:** Switch locale to an LTR locale at runtime: the document direction updates, but 14 component-level `dir="rtl"` attributes and the manifest keep RTL, producing mixed-direction layout and an incorrect installed-PWA metadata. Falsify by showing those attributes are derived from the locale context and that the manifest is regenerated per locale.
- **Root cause:** Direction was hardcoded at the HTML/manifest/component level instead of derived from one locale source of truth.
- **Impact:** Broken layout and accessibility for non-Arabic locales; RTL flash before hydration. Arabic-first defaults are preserved, so no constitution violation — the defect is partial internationalisation.
- **Severity:** MEDIUM · **Likelihood:** MEDIUM (depends on whether LTR locales are enabled) · **Status:** `DISCOVERED` · **owner_gated:** NO.
- **Recommended remediation:** Keep Arabic/RTL as the default but derive all `dir` attributes from the locale context; make the manifest locale-aware or generate per-locale manifests; add a Playwright test switching locale and asserting consistent `dir` across document and components.
- **Alternatives:** (a) If only Arabic is supported in this release, remove the runtime switch or explicitly mark other locales `BLOCKED` rather than partially functional; (b) use CSS logical properties throughout and drop per-component `dir` attributes.

### AUD-FE-003 — No connectivity/offline UX affordance (MEDIUM)

- **Evidence**
  - `frontend-v3/src/main.tsx:6-17` — SW registration block contains no `offline`/`online` event handling and no connectivity state initialisation.
  - Repo-wide search of `frontend-v3/src`: no `navigator.onLine`, no `online`/`offline` listener, no offline banner/component.
  - `frontend-v3/vite.config.ts:45-71` — Workbox config defines no offline fallback page/route for navigations when the network fails.
- **Reproduction / falsification:** Go offline and navigate to a non-cached route: no explicit offline state is communicated; failures surface as generic request errors. Falsify by identifying a connectivity provider/banner and a Workbox `NavigationRoute` fallback.
- **Root cause:** No user-facing connectivity state was designed.
- **Impact:** Users cannot distinguish "no network" from "backend error", cannot tell whether an action is queued, and receive no guidance — a safety/usability concern in clinical workflows.
- **Severity:** MEDIUM · **Likelihood:** HIGH where connectivity is intermittent · **Status:** `DISCOVERED` · **owner_gated:** NO.
- **Recommended remediation:** Add a connectivity provider with an Arabic-first offline banner, disable or clearly mark actions that cannot be performed offline, and provide a Workbox navigation fallback. Add a browser test toggling offline/online.
- **Alternatives:** (a) Surface a minimal "connection lost — retry" toast on failed requests; (b) rely on the browser's native offline page (weak, not recommended for clinical use).

### AUD-FE-004 — Service-worker update prompt is blocking, unlocalised, and has no registration/offline-ready handling (LOW)

- **Evidence:** `frontend-v3/src/main.tsx:9-16` — uses blocking `confirm('يتوفر تحديث جديد للمنصة. هل تريد التحديث الآن؟')` with an inline Arabic string; only `onNeedRefresh` is supplied. No `onOfflineReady`, no `onRegisterError`, no i18n key.
- **Reproduction / falsification:** Inspect the `registerSW` options. Falsify by showing an i18n-backed non-blocking update UI and explicit error/offline-ready handlers.
- **Root cause:** Minimal PWA scaffold left in place without UX/i18n integration.
- **Impact:** Non-localised prompt in an i18n application; `confirm()` blocks the UI; silent SW registration failures leave stale assets without user awareness.
- **Severity:** LOW · **Likelihood:** MEDIUM · **Status:** `DISCOVERED` · **owner_gated:** NO.
- **Recommended remediation:** Replace `confirm()` with an accessible in-app dialog using i18n keys; add `onOfflineReady` and `onRegisterError` handlers with user-visible feedback; add a test for the update path.
- **Alternatives:** (a) Auto-update with `skipWaiting` and a non-blocking "new version available" toast; (b) defer update to next launch with a version indicator.

## 2. Coverage and limitations

| Area inspected | Result |
|---|---|
| PWA/service-worker configuration | AUD-FE-001, AUD-FE-003, AUD-FE-004 |
| Offline data capability (client) | AUD-FE-001 |
| i18n / RTL direction consistency | AUD-FE-002 |
| Synthetic-data honesty | Checked — honestly labelled; no finding |
| Accessibility (WCAG AA) deep audit | **NOT MEASURED** — no browser/axe run performed; out of scope for this static pass |
| Visual/responsive regression | **NOT MEASURED** — no build or browser session |
| Production readiness | **BLOCKED** — no `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` awarded |

No source, git, config, DB, or sibling-repository files were modified. The pre-existing `NR-011` FK test under `tests/identity` was not re-reported.
