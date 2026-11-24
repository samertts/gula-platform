# DESIGN SYSTEM AUDIT — A02 (frontend-v3)

**Program:** PROGRAM-GULA-PARALLEL-001 · **Wave:** A (READ-ONLY AUDIT)
**Agent:** A02 — Frontend Design System auditor
**Date:** 2026-11-19
**Reference project:** `frontend-v3` (sole FE reference)
**Scope:** design tokens, theme/dark mode, shared components, typography, RTL/LTR, responsive, accessibility, state patterns, frontend-level config.
**Excluded by mandate:** `frontend-v3/src/pages/**` (AGENT 03 exclusive scope), all code writes, all git state changes, all builds/tests/servers.

---

## 0. Executive summary

The `frontend-v3` design system has a **structurally split foundation**. Four CSS files exist, but **only one is imported** (`src/styles/index.css`, via `src/main.tsx:4`). The other three (`src/index.css`, `src/styles/theme.css`, `src/App.css`) are dead code. Critically, the **active** stylesheet defines one token vocabulary (shadcn-style: `--background`, `--card`, `--muted-foreground`, `--destructive`, …) while several shipped shared components use a **different** vocabulary (`bg-surface`, `border-outline`, `text-on-surface`, `bg-surface-container-high`) that is defined **only in the dead** `src/index.css`. Tailwind v4 compiles only the imported entry file, so those utilities are never generated. Modal, Skeleton and the UI-layer EmptyState therefore render without their intended surfaces.

Other systemic issues: light-theme contrast failures on widely used tokens; no pre-paint theme or direction application (flash of wrong theme / wrong direction); a duplicate `Modal` overlay with no dialog semantics or focus management; the Arabic font is downloaded but never applied; form error text is not programmatically associated; `DataTable` sortable headers and clickable rows are keyboard-inaccessible and hardcode Arabic; hardcoded color values bypass tokens throughout; RTL/LTR mirroring is inconsistent; i18n resources are incomplete in the shared shell; and vitest-axe coverage is minimal with color-contrast disabled in both existing tests.

**Counts:** 21 findings — **P0: 1 · P1: 6 · P2: 10 · P3: 4**. 4 SCOPE_REQUESTs.

**Constitution check (PROGRAM-CONSTITUTION-001):** No paid dependency is required for any proposed fix. All remediation candidates reuse existing open-source dependencies (Tailwind v4, lucide-react, i18next, vitest-axe) and existing primitives. One vendor-coupling concern is recorded (Google Fonts CDN for Tajawal); the free/open-source alternative — self-hosting the OFL-licensed WOFF2 in `public/` — is documented in A02-005 and supports the offline/PWA requirement. No clinical content was invented; no accessibility-reducing visual change is proposed.

---

## 1. Evidence base — files reviewed

**Files reviewed: 70** (source/config/test, read-only). Key paths:

| Area | Files |
|---|---|
| CSS / tokens | `src/main.tsx`, `src/index.css`, `src/App.css`, `src/styles/index.css`, `src/styles/theme.css`, `index.html` |
| Theme / locale / a11y contexts | `src/contexts/ThemeContext.tsx`, `LocaleContext.tsx`, `AccessibilityContext.tsx` |
| i18n | `src/i18n/index.ts`, `locales.ts`, `ar.ts`, `en.ts`, `ku.ts`, `tk.ts`, `syr.ts`, `mobileNavResources.test.ts` |
| UI primitives | `src/components/ui/{Button,Badge,Card,Input,Select,Textarea,DataTable,Dialog,Modal,EmptyState,Skeleton,index}.tsx` |
| Shared components | `src/components/shared/{AsyncBoundary,PageComponents,ToastContainer,UpdateGate,GulaBrand}.tsx` + `PageComponents.a11y.test.tsx` |
| Other shared surfaces | `components/accessibility/AdaptiveComponents.tsx`, `components/navigation/MobileBottomNav.tsx`, `components/workspace/WorkspaceSelector.tsx` (+2 tests), `components/auth/RoleGuard.tsx`, `components/guide/GuideAssistant.tsx` |
| Shell / infra | `src/App.tsx`, `src/routes/index.tsx` (loading boundaries only), `src/layouts/{DashboardLayout,Sidebar,AuthLayout}.tsx`, `src/lib/utils.ts`, `src/hooks/useMediaQuery.ts`, `src/test/setup.ts` |
| Config (read-only observation) | `package.json`, `vite.config.ts`, `vitest.config.ts`, `tsconfig*.json` |
| E2E evidence read | `e2e/dark-mode.spec.ts`, `e2e/mobile-layout.spec.ts` |

### 1.1 Git cleanliness of the audited area (read-only `git status --porcelain`)

Only five `frontend-v3` paths are user-modified (PROTECTED): `package.json`, `package-lock.json`, `vite.config.ts`, `src/api/endpoints.ts`, `src/components/navigation/MobileBottomNav.test.tsx`. **Every source file cited as a remediation candidate in the companion report is clean** (verified individually), with the exception of `vite.config.ts` / `package.json`, which are explicitly marked BLOCKED.

### 1.2 Which stylesheet is actually active (verified, not assumed)

- `src/main.tsx:4` → `import "@/styles/index.css";` — the **only** CSS import in the application entry.
- `e2e/dark-mode.spec.ts:45-46` asserts `rgb(16, 32, 43)` / `rgb(230, 240, 244)`, exactly `#10202b` / `#e6f0f4` from `src/styles/index.css:81-82` — independent confirmation of the active cascade.
- No import of `src/index.css`, `src/styles/theme.css` or `src/App.css` exists anywhere (repository-wide grep). Their rules are **not applied**.

---

## 2. Findings

Format per assignment: ID · Severity · Title · Evidence · Affected components · Root cause · Safe-fix possible? · Approval required?

---

### A02-001 — P0 — Split token architecture: shipped shared components reference utility classes that are never generated

**Evidence:**
- `src/main.tsx:4` imports only `@/styles/index.css`; its `@theme inline` block (`src/styles/index.css:5-42`) maps **only** the shadcn vocabulary: `--color-background`, `--color-card`, `--color-primary`, `--color-muted-foreground`, `--color-destructive`, `--radius-*` (note: no `--color-surface`, `--color-outline`, `--color-on-surface`).
- The **dead** `src/index.css:8-54` defines the Material-3 vocabulary: `--color-surface`, `--color-surface-container-high`, `--color-on-surface`, `--color-on-surface-variant`, `--color-outline`, `--color-success`, `--color-warning`, `--shadow-*` — plus `--font-sans` (`:4-6`).
- Components using the unavailable vocabulary (all live, none gated):
  - `src/components/ui/Modal.tsx:37` — `bg-surface shadow-2xl border border-outline`; `:43` `text-on-surface`; `:44` `bg-surface-container-high`.
  - `src/components/ui/EmptyState.tsx:17` `bg-surface-container-high`; `:18` `text-on-surface-variant`; `:20` `text-on-surface`; `:21` `text-on-surface-variant`.
  - `src/components/ui/Skeleton.tsx:4` `bg-surface-container-high`; `:25` `border border-outline`.
  - `src/pages/...` consumers of those components inherit the missing surface (page files themselves are A03 scope; not reported here).
- By contrast, correctly-tokened siblings exist: `src/components/ui/Card.tsx:12` (`bg-card text-card-foreground`), `src/components/shared/PageComponents.tsx:31-45` (`bg-muted text-muted-foreground`).

**Affected components:** `Modal`, `ui/EmptyState`, `Skeleton`, `TableSkeleton`, `CardSkeleton`; all downstream consumers of those primitives.
**Root cause:** Two independently authored token sets in two CSS entry files; only one is wired into the build. Tailwind v4 generates utilities from the imported entry file's theme, so `bg-surface`/`border-outline`/`text-on-surface*` produce **no CSS**.
**Safe-fix possible?** Yes — either (a) add the missing semantic aliases to the active `@theme inline` block, or (b) migrate the four components to the active shadcn vocabulary. (a) is the lower-risk single-file change.
**Approval required?** **Yes.** It changes the rendered appearance of overlay/loading/empty surfaces across the app and must be consolidated with A03 (which owns page-level usage) before Wave C.

---

### A02-002 — P1 — Light-theme token contrast failures (muted text and destructive action)

**Evidence** — computed WCAG 2.1 ratios from `src/styles/index.css:45-63` (sRGB relative luminance):

| Pair | Tokens | Ratio | Requirement | Result |
|---|---|---|---|---|
| Muted body text | `--muted-foreground:#6e8090` on `--muted:#f5f8fa` (`:56` on `:55`) | **3.82:1** | 4.5:1 (1.4.3) | FAIL |
| Destructive button label | `--destructive-foreground:#ffffff` on `--destructive:#ef4444` (`:60`/`:59`) | **3.76:1** | 4.5:1 | FAIL |
| Destructive text on page | `#ef4444` on `--background:#f5f8fa` | **3.53:1** | 4.5:1 | FAIL |
| Form control border | `--input:#d8e4e9` on background (`:62`) | **1.22:1** | 3:1 (1.4.11) | FAIL |
| Dark form border | `--input:#3c5968` on `#10202b` (`:98`/`:81`) | **2.23:1** | 3:1 | FAIL |

Usage evidence: `src/components/ui/Card.tsx:39` (`text-muted-foreground`), `src/components/ui/DataTable.tsx:59,64,86,92,119`, `src/components/shared/PageComponents.tsx:17,35,38,99`, `src/components/workspace/WorkspaceSelector.tsx:60,66,72`, `src/components/ui/Button.tsx:8` (`destructive` variant), `src/components/ui/Badge.tsx:12`. Dark-mode equivalents pass (muted 7.61:1, destructive 7.77:1, foreground 14.35:1).
**Affected components:** Button, Badge, Card, DataTable, Input/Select/Textarea, WorkspaceSelector, shared EmptyState/ErrorDisplay, most text-heavy surfaces.
**Root cause:** Light palette authored for aesthetic softness without an automated contrast gate; no token-level contrast test exists.
**Safe-fix possible?** Yes — darken `--muted-foreground` (e.g. `#586a78`) and `--destructive` (e.g. `#b91c1c` with white foreground), and raise `--border`/`--input` contrast for dark mode. Values must be re-verified with a contrast calculation.
**Approval required?** **Yes** — token value changes affect every surface; however they strictly *increase* accessibility and are therefore compatible with the mandate.

---

### A02-003 — P1 — Flash of wrong theme; no pre-paint theme application

**Evidence:**
- `src/contexts/ThemeContext.tsx:14-17` reads `localStorage["theme"]` during render (fine), but `:21-39` applies `.dark`, `resolvedTheme` and `colorScheme` inside `useEffect`, i.e. **after first paint**.
- `index.html:3-20` contains no inline boot script that sets `.dark` / `color-scheme` before the module bundle loads.
- `resolvedTheme` is initialised to `"light"` (`ThemeContext.tsx:19`) regardless of stored/OS preference, so consumers get one incorrect render frame.
- `ThemeContext.tsx:15-16` casts stored data unchecked: `stored as Theme`; an invalid value survives as `theme`, producing an invalid `colorScheme` assignment at `:29`.
- `index.html:8-9` theme-color meta keys off `prefers-color-scheme`, not the stored `theme` preference, so an explicit user choice is not reflected in browser chrome.

**Affected components:** ThemeProvider and every themed surface; PWA shell metadata.
**Root cause:** Theme persistence implemented entirely in React lifecycle rather than a pre-hydration inline bootstrap.
**Safe-fix possible?** Yes — a small inline `<script>` in `index.html` that reads `localStorage`, validates against `light|dark|system`, resolves `matchMedia`, and sets `documentElement.classList`/`colorScheme` before CSS paints; plus validation in `ThemeContext.tsx`.
**Approval required?** **Yes** — touches the HTML shell and global runtime behaviour; needs orchestrator sign-off and A08 awareness (PWA/CI).

---

### A02-004 — P1 — Two overlay components with divergent APIs; `Modal` has no dialog semantics or focus management

**Evidence:**
- `src/components/ui/Dialog.tsx` is complete: `role="dialog"`, `aria-modal`, `aria-labelledby`/`aria-describedby` (`:94-98`), focus trap + Escape + focus restore (`:31-77`), labelled close button (`:103-104`).
- `src/components/ui/Modal.tsx:18-51` duplicates the visual role with a different API (`isOpen` vs `open`) but has **no** `role="dialog"`, no `aria-modal`, no accessible title association (`:43` plain `<h2>`), **no focus trap**, **no focus restore**, Escape handling only (`:22-23`), and an unlabelled close button (`:44`). Its backdrop uses `onClick` only (`:35`), so it is not keyboard-operable.
- Usage: `Dialog` is used by 7 files; `Modal` by 2 files (read-only grep over `src/`), so the weaker implementation is live.

**Affected components:** `Modal`, `Dialog`; consumers of both.
**Root cause:** Feature accretion without a single overlay primitive; no API governance.
**Safe-fix possible?** Yes — highest value: port Dialog's accessibility behaviour into `Modal` without changing its public props, then deprecate one of the two in a later, separately approved step.
**Approval required?** **Yes** — changing overlay behaviour is user-visible; removing `Modal` outright requires A03 page edits.

---

### A02-005 — P1 — Tajawal (Arabic UI font) is downloaded but never applied

**Evidence:**
- `index.html:10-12` preconnects to Google Fonts and loads `Tajawal:wght@400;500;700;800`.
- `index.html:21` applies `font-sans` to `<body>`.
- The **active** stylesheet `src/styles/index.css` has **no** `--font-sans` definition (checked `:1-238`); Tailwind v4 therefore supplies its default Latin-first stack. The only `--font-sans` declaration is in the **dead** `src/index.css:4-5` (`"Tajawal", "Noto Naskh Arabic", ui-sans-serif, system-ui, sans-serif`).
- No `@font-face` for Tajawal exists anywhere in `frontend-v3/src` or `public` (repository grep).

**Affected components:** all text in the app; Arabic-first typography is a first-class platform requirement.
**Root cause:** font token was authored in the orphaned CSS entry; the CDN `<link>` was added independently, so loading and application were never connected.
**Safe-fix possible?** Yes — define `--font-sans` in the active stylesheet. **Free/open-source alternative considered (constitution):** self-host the OFL-licensed Tajawal WOFF2 in `public/fonts/` with `@font-face` + `font-display:swap`, removing the external CDN dependency and honouring the offline/PWA requirement; no paid font or service.
**Approval required?** **Yes** — global typography change. (Removing the CDN link additionally needs A08 awareness because `vite.config.ts:59-69` caches `fonts.googleapis|gstatic` — and that config is USER-OWNED, so it cannot be edited in Wave C.)

---

### A02-006 — P1 — Form error messages are not programmatically associated with their controls

**Evidence:**
- `src/components/ui/Input.tsx:11-21`: `<input>` has no `aria-invalid` and no `aria-describedby`; the error `<p>` at `:21` has no `id`.
- Same pattern in `src/components/ui/Select.tsx:13-29` and `src/components/ui/Textarea.tsx:11-20`.
- Error styling only changes `border-destructive` / `focus-visible:ring-destructive` (`Input.tsx:16`), i.e. colour-only signalling.
- Contrast of `text-destructive` on light background is 3.53:1 (see A02-002).

**Affected components:** `Input`, `Select`, `Textarea` and every form built from them.
**Root cause:** error prop implemented as a visual add-on rather than an accessibility contract.
**Safe-fix possible?** Yes — `useId()` for the message, `aria-describedby={error ? id : undefined}`, `aria-invalid={Boolean(error) || undefined}`; no visual redesign.
**Approval required?** **No** — low-risk, additive accessibility fix with no clinical, auth or layout change.

---

### A02-007 — P1 — `DataTable` sortable headers and clickable rows are keyboard-inaccessible and hardcode Arabic strings

**Evidence:**
- `src/components/ui/DataTable.tsx:61-68`: sortable `<th>` uses `onClick` + `cursor-pointer` only — no `<button>`, no `tabIndex`, no `onKeyDown`, no `aria-sort`.
- `:97-105`: `<tr onClick={() => onRowClick?.(row.original)}>` with `cursor-pointer` but no `tabIndex`, `role`, keyboard handler or accessible instructions.
- `:87` `"جاري التحميل..."`, `:93` `"لا توجد بيانات"`, `:120` template `"الصفحة X من Y"`, `:129` `"السابق"`, `:137` `"التالي"` are literal Arabic despite 5 supported locales (`src/i18n/locales.ts:1`).
- Loading and empty states are plain `<td>` text (`:84-95`) rather than the shared `Skeleton` / `EmptyState` primitives; pagination is always rendered even at zero rows.

**Affected components:** `DataTable` and all tables built from it.
**Root cause:** component authored as a visual table before a11y/i18n contracts were established.
**Safe-fix possible?** Yes — wrap header labels in `<button>` with `aria-sort`; add `tabIndex`/`onKeyDown` (Enter/Space) to clickable rows; route strings through `useTranslation` with keys added to all 5 resources; reuse shared state primitives.
**Approval required?** **Yes** — keyboard/a11y portions are low-risk, but new translation keys are content changes across locales and must be approved by the orchestrator/translation owner.

---

### A02-008 — P2 — Hardcoded colours and ad-hoc palettes bypass the token layer

**Evidence (representative excerpts; 125 hex literals found in `src/components`, `src/layouts`, `src/contexts`, `src/lib`, `src/styles`, `src/index.css`, `src/App.css`, `index.html`):**
- `src/components/ui/Button.tsx:5-10` — `bg-[#0D9488]`, `hover:bg-[#0F766E]`, `shadow-[0_10px_22px_-14px_rgba(13,148,136,0.9)]`, `border-slate-200`, `hover:bg-teal-50/60`, `dark:border-white/10`.
- `src/components/ui/Card.tsx:12` — `border-slate-200/80`, `dark:border-white/10`, hand-written shadow.
- `src/components/ui/Badge.tsx:14-15` — `emerald-*`/`amber-*` palettes instead of the project's semantic success/warning colours.
- `src/components/shared/GulaBrand.tsx:24` — gradient `from-[#16A394] via-[#0D9488] to-[#0F172A]`; `:58-60` amber literals.
- `src/components/shared/ToastContainer.tsx:29` — `border-emerald-500/50 text-emerald-700 dark:text-emerald-400`.
- `src/components/navigation/MobileBottomNav.tsx:107,127-128,144` — `bg-white/95`, `dark:bg-slate-950/95`, `text-[#0D9488]`, `text-[#0F172A]`.
- `src/layouts/DashboardLayout.tsx:49,63,77,93,160,178-199`, `src/layouts/Sidebar.tsx:135-136,152,211`, `src/layouts/AuthLayout.tsx:26,33-35`.
- `src/components/shared/UpdateGate.tsx:113-140` — entirely slate/teal literal palette for a blocking dialog.

**Affected components:** essentially every shared surface; `lib/utils.ts` status helpers (see A02-014).
**Root cause:** no enforced token-only lint rule; tokens exist but are not treated as the single source of truth.
**Safe-fix possible?** Yes — incremental replacement with existing semantic tokens (`--primary`, `--success`/`--warning` aliases, `--border`, `--muted`, `--ring`); no new dependency.
**Approval required?** **Yes** — broad visual change; must be sequenced after A02-001 so aliases actually resolve.

---

### A02-009 — P2 — RTL/LTR mirroring is inconsistent; physical properties and dead mirroring rules coexist

**Evidence:**
- Correct logical utilities are widely used (`ms-auto`, `pe-12`, `end-3`, `text-start`, `border-s`); e.g. `src/components/ui/Dialog.tsx:104,108`, `src/components/ui/DataTable.tsx:64`, `src/components/navigation/MobileBottomNav.tsx:107` (`inset-x-0`).
- Inconsistent physical utilities in the same shared shell:
  - `src/layouts/Sidebar.tsx:152-155` — mobile drawer `right-0`, `border-l`, `translate-x-full`; in LTR (`en`, `tk`) the drawer stays on the right and slides from the wrong edge.
  - `src/layouts/DashboardLayout.tsx:54` — skip link `focus:right-2`, whereas `src/layouts/AuthLayout.tsx:39` uses logical `focus:end-2`.
  - `src/layouts/DashboardLayout.tsx:159` — `border-r ... pr-3`.
  - `src/layouts/Sidebar.tsx:169,176` — `mr-auto`, `mr-2`.
  - `src/layouts/AuthLayout.tsx:33-35` — `-right-24`/`-left-24` decorative blobs; cosmetic only.
- `src/components/guide/GuideAssistant.tsx:37` forces `dir={isArabic ? "rtl" : "ltr"}`, so RTL locales **ku** and **syr** are rendered LTR even though `getLocaleDirection` returns `rtl` (`src/i18n/locales.ts:15-17`).
- Chevron mirroring exists **only in dead CSS**: `src/index.css:154-160` (`[dir="rtl"] .lucide-chevron-left/right`). `Sidebar.tsx:184-194` and `GuideAssistant.tsx:65` therefore implement direction manually; other icon usages have no mirroring fallback.
- `src/contexts/LocaleContext.tsx:31` sets `--gula-reading-direction`, but no CSS rule consumes it (repository grep) — dead signalling.

**Affected components:** Sidebar, DashboardLayout, AuthLayout, GuideAssistant, icon-heavy buttons, skip links.
**Root cause:** no codified "logical properties only" policy; RTL handled ad hoc at component level.
**Safe-fix possible?** Yes — replace physical utilities in shared/layout files with Tailwind logical equivalents (`end-*`, `border-s/e`, `ps/pe`, `ms/me`, `rounded-s/e`) and drive `dir` from `useLocale().isRTL`.
**Approval required?** **Yes** — direction/layout behaviour changes in the app shell must be verified for all 5 locales.

---

### A02-010 — P2 — Wrong-direction flash for LTR locales

**Evidence:**
- `index.html:2` hardcodes `<html lang="ar" dir="rtl">` (correct default for the Arabic-first platform).
- `src/contexts/LocaleContext.tsx:20` initialises from `getStoredLocale()`, but direction/lang/`i18n.changeLanguage` are only applied in `setLocale` (`:23-32`), invoked from a mount effect (`:34-37`). i18next itself initialises early (`src/i18n/index.ts:19`), so text can be English/LTR-language while the document is still RTL for one or more frames.
- No inline boot script sets `dir`/`lang` from `localStorage["gula.locale"]` before paint (cf. A02-003).

**Affected components:** LocaleProvider, entire shell for `en` and `tk` users.
**Root cause:** locale direction treated as a post-mount side effect.
**Safe-fix possible?** Yes — validate stored locale in an inline HTML bootstrap together with the theme script; keep React as the authority thereafter.
**Approval required?** **Yes** — HTML shell change; coordinate with A02-003 into one bootstrap.

---

### A02-011 — P2 — i18n resource and usage gaps in components owned by A02

**Evidence:**
- `src/components/workspace/WorkspaceSelector.tsx:77` calls `t("workspace.selector", "مساحات العمل")` — the key **does not exist in any of the 5 resource files** (grep: zero `selector:` entries), so the Arabic fallback is always used.
- Hardcoded Arabic strings in shared shell: `WorkspaceSelector.tsx:37,54,60-62,66,72,78,83`; `src/layouts/DashboardLayout.tsx:78,94,97,106,137-149,184-186,193`; `src/layouts/AuthLayout.tsx:41,84-96`; `src/components/shared/UpdateGate.tsx:116-140`; `src/components/shared/ToastContainer.tsx:37`; `src/components/ui/DataTable.tsx:87,93,120,129,137`.
- `t("legal.privacyTitle")` / `t("legal.termsTitle")` in `AuthLayout.tsx:125,132` exist only in `ar.ts:251-252` and `en.ts:257-258`; **missing in `ku`, `tk`, `syr`** → fallback language (`src/i18n/index.ts:20`, `fallbackLng:"en"`) leaks English into those locales.
- `src/components/accessibility/AdaptiveComponents.tsx:16-27,74-81` — all state labels/descriptions are hardcoded English with no `useTranslation`.
- `src/components/guide/GuideAssistant.tsx:27-34,39-76` implements an ar/en boolean split instead of using i18next; `ku`, `tk`, `syr` silently get English.
- `src/lib/utils.ts:76-131` — Arabic-only label maps (see A02-014).
- Positive control: `src/i18n/mobileNavResources.test.ts` verifies `mobileNav.*` keys in all 5 locales — but no equivalent test covers `legal.*`, `workspace.*`, or component-level strings.

**Affected components:** WorkspaceSelector, DashboardLayout, AuthLayout, UpdateGate, ToastContainer, DataTable, AdaptiveComponents, GuideAssistant.
**Root cause:** i18n coverage was enforced only for the navigation resource subset; no lint/test for the rest of the shared shell.
**Safe-fix possible?** Yes — add missing keys to the 3 resource files and replace literals with `t()` calls. **No clinical content may be invented**; reuse existing neutral UI terminology and require translation-owner review for `ku`/`tk`/`syr`.
**Approval required?** **Yes** — cross-locale content changes.

---

### A02-012 — P2 — Accessibility preference token coverage is incomplete

**Evidence:**
- `src/styles/index.css:167-187` high-contrast overrides cover only `--background`, `--foreground`, `--card`, `--card-foreground`, `--muted-foreground`, `--border`, `--input`, `--ring`. **Not overridden:** `--primary`, `--primary-foreground`, `--secondary*`, `--accent*`, `--destructive*`, `--chart-*`, `--sidebar-*`, `--popover*`. Thus high-contrast mode leaves whole regions (sidebar, charts, destructive controls) on the normal palette.
- `src/contexts/AccessibilityContext.tsx:6-33` exposes `font_size` and `visual_alerts`, `text_alternatives`, `captions`, etc.; `applyPreferences` (`:49-61`) applies only `text_scale`, `larger_touch_targets`, contrast/motion/dyslexia/simple-interface classes and data attributes. `font_size` is **never applied** to the DOM.
- `data-color-blind-mode` / `data-reduced-color-dependence` rules (`styles/index.css:189-199`) target `[data-status]`, but the shared `AdaptiveStatus`/`AdaptiveStateBadge` (`AdaptiveComponents.tsx:33,52`) do not set `data-status` or `data-status-label`, so the labels never appear there.
- Positive: `--gula-text-scale`/`--gula-touch-scale` set at `AccessibilityContext.tsx:55-56` are consumed at `styles/index.css:164,235-236`; reduced-motion is handled at `:211-229`.

**Affected components:** high-contrast users, colour-blind mode, status badges, font-size preference surface.
**Root cause:** preference model is broader than the CSS hooks implemented for it.
**Safe-fix possible?** Yes — extend the high-contrast blocks with the missing semantic tokens (monochrome-safe values), map `font_size` to `--gula-text-scale`, and add `data-status`/`data-status-label` to the adaptive status primitives.
**Approval required?** **Yes** — accessibility feature behaviour; must not reduce contrast in either mode.

---

### A02-013 — P2 — Fragmented Loading / Error / Empty primitives; no single unified pattern

**Evidence:**
- Two EmptyStates: `src/components/ui/EmptyState.tsx:14-24` (Material tokens — broken per A02-001; supports `className`) and `src/components/shared/PageComponents.tsx:31-46` (active tokens; no `className`). `AsyncBoundary.tsx:37` imports the **shared** one.
- Two skeletons: `src/components/shared/PageComponents.tsx:48-70` (`PageLoadingSkeleton`, accessible: `role="status"`, `aria-busy`, sr-only label — covered by `PageComponents.a11y.test.tsx:7-23`) vs `src/components/ui/Skeleton.tsx:3-33` (`Skeleton`/`TableSkeleton`/`CardSkeleton`, **no** role/live region, broken tokens).
- Two spinners: `PageComponents.tsx:72-87` (accessible) and inline SVG in `Button.tsx:54-75` (`aria-busy` on the button at `:51`, adequate for in-control loading).
- `src/components/shared/AsyncBoundary.tsx:16-41` provides the one coherent state machine (`isLoading → isError → isEmpty → children`) but has **zero usages** in `src/` (read-only grep).
- `src/components/ui/index.ts:1-8` does not export `EmptyState`, `Skeleton`, `TableSkeleton`, `CardSkeleton` or `Modal`, forcing deep imports.
- `DataTable.tsx:84-95` implements its own inline loading/empty text (see A02-007).

**Affected components:** all state-rendering surfaces.
**Root cause:** two generations of primitives coexist without deprecation or a barrel contract.
**Safe-fix possible?** Yes — designate `AsyncBoundary` + shared `PageComponents` primitives as canonical, export them from one barrel, and make `ui/*` variants thin re-exports; page import migration belongs to A03 (SCOPE_REQUEST SR-01).
**Approval required?** **Yes** — API consolidation affects consumers.

---

### A02-014 — P2 — Shared `lib/utils.ts` hardcodes semantic status colours, Arabic labels and `ar-IQ` formatting

**Evidence:**
- `src/lib/utils.ts:35-49` (`getFlagColor`) and `:52-74` (`getStatusColor`) return literal palettes (`text-red-600 bg-red-50 dark:bg-red-950`, `text-green-600 ...`, `text-blue-600 ...`) with inconsistent dark variants — a parallel, untokened semantic system that includes clinical result flags (`critical`, `H`, `L`, `normal`).
- `:124-131` `getTierColor` adds another ad-hoc palette (`gray`/`blue`/`purple`).
- `:76-122` `getGenderLabel`, `getLabTypeLabel`, `getRoleLabel`, `getTierLabel` are Arabic-only maps bypassing i18next.
- `:8-33` `formatDate`/`formatDateTime`/`formatNumber` always use `ar-IQ`, ignoring the active locale even for `en`/`tk`.
- Consumers in A02 scope: `src/layouts/Sidebar.tsx:4,221-222` (`getRoleLabel`).

**Affected components:** Sidebar plus all shared/page consumers of these helpers; clinical status presentation.
**Root cause:** legacy helper module accumulated presentation and localisation concerns.
**Safe-fix possible?** Yes — replace colour strings with semantic token-backed class constants; route labels/formatting through `useLocale`/i18next helpers. **No clinical status semantics may change** — only their visual encoding.
**Approval required?** **Yes** — shared utility behaviour and clinical status colours; also requires A03 review of page consumers.

---

### A02-015 — P2 — Two competing focus-ring languages; the Button's designated class lives only in dead CSS

**Evidence:**
- Active global focus style: `src/styles/index.css:151-158` — `2px solid var(--ring)`, `outline-offset:2px` for `button, a, select, input, textarea`.
- `src/components/ui/Button.tsx:45` applies `gula-focus-ring`; that class is defined **only** in dead `src/index.css:149-151` (`focus-visible:ring-2 focus-visible:ring-teal-500`) → **no effect at runtime**. The button therefore falls back to the global 2px outline.
- Inputs deliberately suppress the global outline (`focus-visible:outline-none`) and substitute a 1px Tailwind ring: `Input.tsx:15`, `Select.tsx:16`, `Textarea.tsx:14` (`focus-visible:ring-1 focus-visible:ring-ring`).
- Other components add a third variant: `Dialog.tsx:104` and `ToastContainer.tsx:37` use 2px ring + `outline-none`; `WorkspaceSelector.tsx:80` uses `ring-teal-500`; `GuideAssistant.tsx:70` uses `focus:ring-2 focus:ring-primary`.
- Light `--ring` contrast is 3.91:1 (A02-002) — borderline for a 2px indicator.

**Affected components:** Button, form controls, Dialog, ToastContainer, WorkspaceSelector, GuideAssistant.
**Root cause:** focus styling was re-authored per component instead of exposing one tokenised utility in the active stylesheet.
**Safe-fix possible?** Yes — define a single `.gula-focus-ring` (or equivalent) in the active stylesheet using `--ring`, remove `outline-none` overrides that weaken it, and delete the dead definition.
**Approval required?** **Yes** — global focus appearance, must be verified in both themes.

---

### A02-016 — P3 — No-op animation utility classes (missing animation plugin)

**Evidence:**
- `src/components/ui/Dialog.tsx:91` uses `animate-in fade-in-0 zoom-in-95 duration-200`.
- `src/components/shared/ToastContainer.tsx:27` uses `animate-in slide-in-from-right-full duration-300`.
- `package.json:38-60` has **no** `tailwindcss-animate` / `tw-animate-css` dependency; Tailwind v4 core does not provide these utilities, so they compile to nothing. `slide-in-from-right-full` would also be directionally wrong in RTL if it did work.
- `package.json` is USER-OWNED (PROTECTED) — adding a dependency is **blocked** in Wave C.

**Affected components:** Dialog, ToastContainer.
**Root cause:** classes copied from a Tailwind-animate-based template without the matching plugin.
**Safe-fix possible?** Yes — remove the inert classes (zero visual change since they currently do nothing), or use existing `motion-safe:` + CSS transitions. Do **not** add a dependency while `package.json` is user-owned.
**Approval required?** **No** — removing classes that generate no CSS is behaviour-neutral.

---

### A02-017 — P2 — vitest-axe coverage is minimal and disables the colour-contrast rule

**Evidence:**
- Only two axe assertions exist: `src/components/shared/PageComponents.a11y.test.tsx:13-16` and `src/components/workspace/WorkspaceSelector.a11y.test.tsx:53-56`; both pass `{ rules: { "color-contrast": { enabled: false } } }` — exactly the rule that would catch A02-002.
- `src/components/ui/Button.test.tsx:5-24` tests only `aria-busy`.
- `vitest-axe` is installed (`package.json:59`) and wired in `src/test/setup.ts:2`, so the gap is coverage, not tooling.
- No axe test covers `Input`/`Select`/`Textarea` error states, `DataTable` sorting, `Dialog`/`Modal`, `ToastContainer`, `UpdateGate`, or dark/high-contrast modes.
- E2E coverage exists for dark palette and mobile overflow (`e2e/dark-mode.spec.ts`, `e2e/mobile-layout.spec.ts`) but those are Playwright tests (Wave D gate, not run in Wave A).

**Affected components:** shared component test suite.
**Root cause:** accessibility tooling adopted for a narrow pilot only.
**Safe-fix possible?** Yes — add focused axe tests to the existing shared component test files (all clean) and re-enable `color-contrast` with an explicit token-contrast unit check.
**Approval required?** **Yes** — Wave C test ownership must be coordinated with A09 (SCOPE_REQUEST SR-04).

---

### A02-018 — P2 — Dead CSS files contain conflicting token definitions and stale template code

**Evidence:**
- `src/styles/theme.css:1-37` defines a full `:root` oklch shadcn palette; `:39-74` a `.dark` palette. It is never imported. Its `--destructive-foreground` equals `--destructive` (`theme.css:17,55`: both `oklch(0.577 0.245 27.325)`), which would be an unreadable red-on-red foreground **if it ever became active**. The active file uses `#ffffff` / `#2a1112`.
- `src/index.css:1-160` is a second complete theme (Material tokens, RTL body rule `:74-80`, component utilities `:132-152`, chevron mirroring `:154-160`). Never imported.
- `src/App.css:1-184` is untouched Vite template CSS (`.counter`, `.hero`, `#next-steps`) referencing undefined variables `--accent`, `--accent-bg`, `--accent-border`, `--text-h`, `--social-bg`, `--shadow` (`:5-7,119-131`). Never imported.
- Consequence: four competing "sources of truth" for the same token names; a future import of any one of them silently changes the app's appearance.

**Affected components:** build-time maintainability; A02-001/A02-005/A02-009 are all downstream of this duplication.
**Root cause:** migration from an earlier token system left old files in place.
**Safe-fix possible?** Yes — delete or clearly quarantine the three unreferenced files after porting any still-needed definitions (`--font-sans`, semantic aliases, `gula-focus-ring`, chevron mirroring) into `src/styles/index.css`.
**Approval required?** **Yes** — file deletion and token consolidation need orchestrator sign-off; all three files are currently CLEAN of user modifications.

---

### A02-019 — P3 — No centralised typography scale, line-height or spacing/breakpoint tokens

**Evidence:**
- Active `src/styles/index.css:5-42` defines only colours and radii (`:38-41`). No `--text-*`, `--leading-*`, `--space-*`, or breakpoint tokens.
- Ad-hoc font sizes in shared surfaces: `GulaBrand.tsx:42` `text-[9px]`; `Sidebar.tsx:169` / `DashboardLayout.tsx:77` `text-[10px]`; `AuthLayout.tsx:116` and `WorkspaceSelector.tsx:60,66,72` `text-[11px]`; `MobileBottomNav.tsx:125,144` `text-[10px]`.
- Line heights are set per component (`leading-none`, `leading-tight`, `leading-5`, `leading-6`) with no scale; `src/components/accessibility/AdaptiveComponents.tsx:56` uses `leading-5`, `GuideAssistant.tsx:55` `leading-6`.
- Arbitrary spacing appears in layout chrome: `DashboardLayout.tsx:63` `min-h-[4.5rem]`, `:199` `pb-[calc(5.5rem+env(safe-area-inset-bottom))]`, `MobileBottomNav.tsx:104` `pb-[max(0.75rem,env(safe-area-inset-bottom))]`.
- Only Tailwind default breakpoints (`sm`, `md`, `lg`) are used; the dead `src/App.css:67,81,92,101,139,159` hardcodes `max-width:1024px`. `useMediaQuery.ts:3-13` accepts arbitrary query strings with no shared breakpoint constants.

**Affected components:** all shared surfaces.
**Root cause:** typography/spacing treated as component-local concerns.
**Safe-fix possible?** Yes — introduce a small documented scale in the active `@theme` and migrate shared components incrementally; no new dependency.
**Approval required?** **Yes** — global visual metrics.

---

### A02-020 — P3 — Browser/PWA theme colours disagree with the actual theme tokens

**Evidence:**
- Active tokens: light `--background:#f5f8fa`, dark `--background:#10202b` (`src/styles/index.css:45,81`).
- `index.html:8-9` declares meta theme-color `#ffffff` (light) and `#0f172a` (dark) — neither matches.
- `vite.config.ts:18-19` PWA manifest uses `theme_color:'#0f172a'`, `background_color:'#0f172a'` for both modes (**USER-OWNED / BLOCKED**, see §1.1).
- Consequence: browser chrome and installed-PWA splash colour differ from the app surface; also tied to A02-003 (meta keys off OS preference, not stored theme).

**Affected components:** HTML shell, PWA manifest metadata.
**Root cause:** PWA metadata authored independently from the design tokens.
**Safe-fix possible?** Partial — `index.html` is clean and can be aligned; `vite.config.ts` cannot be touched without user release.
**Approval required?** **Yes** (and BLOCKED for the manifest portion pending user release of `vite.config.ts`).

---

### A02-021 — P3 — Mobile shell breakpoint and grid edge cases

**Evidence:**
- `src/components/navigation/MobileBottomNav.tsx:100-102` filters then `.slice(0, 4)`; `:109` hardcodes `grid-cols-5` (4 destinations + "More"). If fewer than 4 destinations are permitted for a role, empty grid cells appear. Verified with the role/permission filter at `:70-83`.
- `MobileBottomNav.tsx:107` hides at `md:hidden` (≥768px) while `Sidebar.tsx:152-156` becomes static only at `lg:` (≥1024px). Between 768–1023px neither a bottom nav nor a visible sidebar is present; access is via the header menu button (`DashboardLayout.tsx:64-72`) — functional, but an undocumented breakpoint discontinuity.
- `e2e/mobile-layout.spec.ts:3-7,27-35` tests 320/390/1440 only, so the 768–1023px band is untested.
- `src/styles/index.css:231-238` sets a coarse-pointer minimum target of `calc(2.75rem * --gula-touch-scale)` — good — but `MobileBottomNav` uses `min-h-12` (3rem) and some icon-only controls use `h-7 w-7` (`DashboardLayout.tsx:191`), which is below the coarse-pointer minimum once that override applies.

**Affected components:** MobileBottomNav, Sidebar, DashboardLayout.
**Root cause:** breakpoints chosen per component without a shared responsive contract.
**Safe-fix possible?** Yes — align the nav/sidebar switch at one breakpoint and make the grid columns data-driven; raise small touch targets.
**Approval required?** **Yes** — responsive behaviour change; needs A08/QA verification at 768–1023px.

---

## 3. Cross-cutting observations (not separate findings)

- **Positive controls worth preserving:** single-entry Tailwind v4 setup with `@custom-variant dark` (`src/styles/index.css:1-3`); `@theme inline` indirection (`:5-42`); logical properties already dominant (80 logical vs ~20 physical usages in shared/layout files); `prefers-reduced-motion` handling in both active CSS and `AccessibilityContext`; route-level accessible Suspense/loading boundaries (`src/routes/index.tsx:5,101-112`); `role="status"`/`aria-live` on shared loading states; i18n key test for navigation resources.
- **No clinical content was invented.** Findings about clinical flags/statuses (A02-014) concern visual encoding only.
- **No accessibility-reducing remediation is proposed.** All token contrast changes increase legibility.
- **Protected files observed only:** `package.json`, `package-lock.json`, `vite.config.ts`, `src/api/endpoints.ts`, `src/components/navigation/MobileBottomNav.test.tsx`. `AccessibilityContext.tsx:3` imports `userPreferencesApi` from the user-modified `endpoints.ts`; this dependency is reported, not touched.

---

## 4. SCOPE_REQUESTs (for the orchestrator)

| ID | To | Request | Why |
|---|---|---|---|
| SR-01 | A03 | Migrate page imports from `ui/EmptyState` / `ui/Skeleton` deep paths to the single canonical barrel once A02 consolidates it (A02-013). | Page files are A03-exclusive; A02 must not edit them. |
| SR-02 | A03 / A09 | Confirm whether page-level hardcoded colours/Arabic literals (observed incidentally, e.g. `OrdersPage.tsx:3` importing `ui/EmptyState`) should be folded into the same token/i18n remediation track. | A02 did not audit `src/pages/**`; no findings are asserted there. |
| SR-03 | A04 / ORCH | Review `src/components/shared/UpdateGate.tsx:24-28` hardcoded external manifest URL and forced-reload behaviour. A02 reports only its visual/a11y defects. | Security/config behaviour outside A02 mandate. |
| SR-04 | A09 | Add axe coverage for shared overlays/forms/DataTable and re-enable `color-contrast`; coordinate test-file ownership in Wave C. | A09 owns QA remediation; A02 only authored this audit. |
| SR-05 | ORCH / USER | Release or confirm protection of `frontend-v3/package.json` and `vite.config.ts` before any dependency addition (font self-hosting, animation plugin) or PWA theme-colour change. | Both are pre-existing user work; Wave C must not touch them. |

---

## 5. Recommended sequencing (Wave C only, after approval)

1. **A02-001** — reconcile token vocabularies (unblocks everything visual).
2. **A02-002, A02-005, A02-015** — contrast, font, focus tokens (verify with computed contrast + axe).
3. **A02-003 + A02-010** — one pre-paint bootstrap script for theme and direction.
4. **A02-006, A02-007, A02-004** — form a11y, DataTable a11y/i18n, Modal semantics (lowest-risk high-value a11y first).
5. **A02-013, A02-018** — consolidate primitives and remove dead CSS.
6. **A02-008, A02-009, A02-011, A02-012, A02-014** — systemic migration batches.
7. **A02-016, A02-017, A02-019, A02-020, A02-021** — cleanup, coverage and responsive polish.

Concrete file-by-file change lists, eligibility flags and approval gates are in `DESIGN_SYSTEM_REMEDIATION.md`. **No change in this audit has been applied.**
