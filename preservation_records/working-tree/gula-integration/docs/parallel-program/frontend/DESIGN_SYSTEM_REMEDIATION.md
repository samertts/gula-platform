# DESIGN SYSTEM REMEDIATION PLAN — A02 (frontend-v3)

**Program:** PROGRAM-GULA-PARALLEL-001
**Agent:** A02 — Frontend Design System
**Status:** **PROPOSED ONLY — NOT APPLIED. WAVE C BLOCKED.**
**Companion audit:** `docs/parallel-program/frontend/DESIGN_SYSTEM_AUDIT.md`
**Date:** 2026-11-19

---

## 0. Authorization and gating statement

This document lists **candidates**, not commits. Per `PROGRAM_CONTROL.md` §3 and `FILE_OWNERSHIP_MATRIX.md` §5, no Wave C work may begin until:

1. `MASTER_REMEDIATION_REGISTER.md` is consolidated and approved by the orchestrator;
2. each target file is confirmed to match exactly one agent's scope (A02 = shared components/tokens/theme/styles/i18n/RTL/frontend config; **never** `src/pages/**`);
3. `git status --porcelain -- <file>` is **empty** for that file;
4. no open P0 blocks the affected component;
5. the change does not alter clinical logic, auth/RBAC, API contracts, DB schema/migrations or CI semantics without independent approval.

**Current A02 P0:** A02-001 (split token architecture). It blocks candidates C-02, C-03, C-04, C-07 and C-11 until resolved or explicitly downgraded by the orchestrator.

**Eligibility legend:**
- `CLEAN` = verified clean by read-only `git status --porcelain -- <file>` on 2026-11-19.
- `USER` = pre-existing user work — **PROTECTED / NEVER TOUCHED**.
- **safe-fix eligible** = `CLEAN` **and** technically low-risk **and** no page-scope edit required.
- **needs-approval** = orchestrator sign-off (and, where noted, A03/A08/A09 or user release) before any Wave C edit.

**Constitution compliance:** every candidate below uses already-present open-source dependencies (Tailwind CSS v4, lucide-react, i18next, clsx/tailwind-merge, vitest-axe). No paid software, no new SaaS, no vendor lock-in. C-04 explicitly prefers **self-hosted OFL-licensed Tajawal WOFF2** over the current Google Fonts CDN coupling. "Reuse Before Build" is applied by consolidating existing primitives (C-09) rather than creating new ones.

---

## 1. Candidate register (summary)

| ID | Finding | Primary file(s) | Change class | Clean? | Safe-fix eligible | Needs approval |
|---|---|---|---|---|---|---|
| C-01 | A02-001 | `src/styles/index.css` | Add missing semantic aliases to active `@theme inline` | CLEAN | **Yes** | **Yes** (visual; A03 coordination) |
| C-02 | A02-001 | `src/components/ui/Modal.tsx`, `EmptyState.tsx`, `Skeleton.tsx` | Migrate 3 primitives to active token names (alternative to C-01) | CLEAN | Yes (alternative only) | **Yes** |
| C-03 | A02-018 | `src/index.css`, `src/styles/theme.css`, `src/App.css` | Quarantine/delete dead CSS after C-01/C-04/C-12 | CLEAN | Yes | **Yes** (deletion) |
| C-04 | A02-005 | `src/styles/index.css` (+ optional `src/index.html`, `public/fonts/`) | Define `--font-sans`; self-host Tajawal (OFL) | CLEAN (font dir new) | **Yes** for CSS; CDN removal needs A08 | **Yes** |
| C-05 | A02-002 | `src/styles/index.css` | Raise light `--muted-foreground`, `--destructive`, `--border`/`--input` contrast | CLEAN | Yes | **Yes** (global tokens, accessibility-improving) |
| C-06 | A02-003 + A02-010 | `index.html`, `src/contexts/ThemeContext.tsx`, `src/contexts/LocaleContext.tsx` | Pre-paint theme + direction bootstrap; validate stored values | CLEAN | Yes | **Yes** (HTML shell/runtime) |
| C-07 | A02-004 | `src/components/ui/Modal.tsx` | Add dialog role, labelling, focus trap/restore, keyboard backdrop | CLEAN | **Yes** | **Yes** (user-visible overlay) |
| C-08 | A02-006 | `src/components/ui/Input.tsx`, `Select.tsx`, `Textarea.tsx` | `useId` + `aria-invalid` + `aria-describedby` | CLEAN | **Yes** | **No** — additive a11y only |
| C-09 | A02-007 | `src/components/ui/DataTable.tsx` | Keyboard-sortable headers, `aria-sort`, clickable-row keyboard support | CLEAN | **Yes** | **No** for a11y part; **Yes** if strings are also translated |
| C-10 | A02-011 | `src/i18n/{ku,tk,syr}.ts` | Add missing `legal.*` keys; add `workspace.selector` to all 5 | CLEAN | Yes | **Yes** (translation-owner review) |
| C-11 | A02-013 | `src/components/ui/index.ts`, `ui/EmptyState.tsx`, `ui/Skeleton.tsx`, `shared/PageComponents.tsx`, `shared/AsyncBoundary.tsx` | Single state-primitive barrel + deprecation shims | CLEAN | Yes | **Yes** (API change; A03 imports) |
| C-12 | A02-015 | `src/styles/index.css`, `src/components/ui/{Button,Input,Select,Textarea}.tsx` | One tokenised `.gula-focus-ring`; remove weakening `outline-none` | CLEAN | Yes | **Yes** (global focus appearance) |
| C-13 | A02-012 | `src/styles/index.css`, `src/components/accessibility/AdaptiveComponents.tsx`, `src/contexts/AccessibilityContext.tsx` | Extend high-contrast tokens; apply `font_size`; add `data-status-label` | CLEAN | Yes | **Yes** (a11y behaviour) |
| C-14 | A02-008 + A02-014 | `src/components/ui/{Button,Badge,Card}.tsx`, `shared/GulaBrand.tsx`, `lib/utils.ts` | First batch: replace hardcoded colours with semantic tokens | CLEAN | Yes | **Yes** (broad visual change) |
| C-15 | A02-009 | `src/layouts/{Sidebar,DashboardLayout,AuthLayout}.tsx`, `components/guide/GuideAssistant.tsx` | Physical → logical utilities; `dir` from `useLocale()` | CLEAN | Yes | **Yes** (5-locale layout verification) |
| C-16 | A02-016 | `src/components/ui/Dialog.tsx`, `shared/ToastContainer.tsx` | Remove inert `animate-in` / `fade-in-0` / `zoom-in-95` / `slide-in-from-right-full` classes | CLEAN | **Yes** | **No** — classes emit no CSS today |
| C-17 | A02-017 | `src/components/shared/PageComponents.a11y.test.tsx`, `WorkspaceSelector.a11y.test.tsx` | Add axe cases; re-enable `color-contrast` where appropriate | CLEAN | Yes | **Yes** (A09 coordination, SR-04) |
| C-18 | A02-019 | `src/styles/index.css` + shared components | Introduce typography/line-height/scale tokens (no visual migration in same wave) | CLEAN | Yes | **Yes** |
| C-19 | A02-020 | `index.html` | Align meta theme-color with active tokens | CLEAN | Partial — `vite.config.ts` is USER | **Yes** + user release needed for manifest |
| C-20 | A02-021 | `src/components/navigation/MobileBottomNav.tsx`, `src/layouts/Sidebar.tsx` | Data-driven grid columns; align nav/sidebar breakpoint; raise small touch targets | CLEAN (component `.tsx`) | Yes | **Yes** (responsive behaviour) |

---

## 2. Concrete candidates — detail

### C-01 — Reconcile the token vocabulary in the active stylesheet (highest priority)

**File:** `frontend-v3/src/styles/index.css` · **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes** · blocks on P0 resolution.

**What would change (PROPOSED — not applied):** extend the existing `@theme inline` block (currently `:5-42`) with aliases for the vocabulary already used by shipped components:

```
--color-surface: var(--card);
--color-surface-container-lowest: var(--card);
--color-surface-container-low: var(--muted);
--color-surface-container: var(--secondary);
--color-surface-container-high: var(--accent);
--color-on-surface: var(--foreground);
--color-on-surface-variant: var(--muted-foreground);
--color-outline: var(--border);
--color-outline-variant: var(--border);
--color-success: #258b76;          /* or a new --success root token */
--color-warning: #f59e0b;
```

**Why safe:** single-file, additive; no component or page edits required; maps the second vocabulary onto already-defined theme values so both themes (`:root` `:45-78`, `.dark` `:80-113`) stay coherent. Tailwind will then actually emit `bg-surface`, `border-outline`, `text-on-surface*`.
**Verification (Wave D, not now):** assert computed `background-color` on `Modal` panel / `Skeleton` / `ui/EmptyState` icon well in both themes; confirm no unused-class regressions.

**Alternative C-02 (not recommended as first choice):** edit `Modal.tsx:37,43,44`, `EmptyState.tsx:17-21`, `Skeleton.tsx:4,25` to use `bg-card`, `border-border`, `text-foreground`, `text-muted-foreground`, `bg-muted`. More files, same visual outcome, higher merge risk.

---

### C-03 — Remove dead CSS sources

**Files:** `frontend-v3/src/index.css`, `frontend-v3/src/styles/theme.css`, `frontend-v3/src/App.css` · all **CLEAN** · safe-fix eligible: **Yes** (after porting needed definitions) · needs approval: **Yes**.

**What would change:** delete or move to a clearly named `legacy/` quarantine directory (no import remains). Before deletion, port into `styles/index.css`:
- `--font-sans` from `src/index.css:4-6` (see C-04);
- the `gula-focus-ring` utility from `src/index.css:149-151` (see C-12);
- RTL chevron mirroring from `src/index.css:154-160` (see C-15);
- success/warning semantic aliases from `src/index.css:35-41`.

**Why safe:** all three files are proven unreferenced (`main.tsx:4` is the sole CSS import; repository-wide grep finds no other reference). Deleting unreachable CSS cannot change runtime rendering. `theme.css:17,55` even contains an invalid destructive-foreground pairing that would cause red-on-red text if accidentally imported — removal eliminates a latent hazard.
**Note:** `App.css:5-7,119-131` references undefined vars (`--accent-bg`, `--text-h`, `--social-bg`, `--shadow`) and is untouched Vite template code — no value to preserve.

---

### C-04 — Make the Arabic font real, preferably self-hosted

**Files:** `frontend-v3/src/styles/index.css` (CLEAN); `frontend-v3/index.html` (CLEAN); optional new `frontend-v3/public/fonts/` (new, orthogonal) · safe-fix eligible: **Yes** for the CSS step · needs approval: **Yes**.

**What would change:** add to the active `@theme` block:

```
--font-sans: "Tajawal", "Noto Naskh Arabic", ui-sans-serif, system-ui, sans-serif;
--font-mono: "JetBrains Mono", ui-monospace, SFMono-Regular, monospace;
```

**Free/open-source alternative considered (constitution):** download the OFL-licensed Tajawal WOFF2 files once, serve them from `public/fonts/`, add `@font-face { font-display: swap; }`, and remove the Google Fonts `<link>` at `index.html:10-12`. This removes an external CDN dependency (no vendor lock-in), works offline (PWA requirement) and costs nothing. A commercial Arabic font was **not** recommended.
**Why safe:** `index.html:21` already requests `font-sans`; defining the token makes the intended typography effective. No markup or clinical change.
**Blocked portion:** `vite.config.ts:59-69` caches Google Fonts domains — USER-OWNED, so CDN removal must be deferred until the user releases that file (SR-05). Keeping the CDN link while self-hosting is harmless during transition.

---

### C-05 — Fix light-theme token contrast

**File:** `frontend-v3/src/styles/index.css` · **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes**.

**What would change (PROPOSED values — must be re-verified before merge):**
- `:56` `--muted-foreground: #6e8090` → a darker slate (e.g. `#566977`) to reach ≥4.5:1 on `#f5f8fa` (current 3.82:1).
- `:59` `--destructive: #ef4444` → a deeper red (e.g. `#b91c1c`) so `#ffffff` foreground reaches ≥4.5:1 (current 3.76:1). Also improves destructive text on background (current 3.53:1).
- `:61-62` `--border`/`--input: #d8e4e9` slightly darker in light; `:97-98` dark `#3c5968` lighter — target ≥3:1 against adjacent surfaces for WCAG 1.4.11.
- Keep dark palette values (already passing: muted 7.61:1, destructive 7.77:1).

**Why safe:** monotonic accessibility improvement; token-only; no component edits. Values must be recomputed with the same luminance method used in the audit and re-checked against `gula-high-contrast` overrides (`:167-187`).

---

### C-06 — Pre-paint theme and direction bootstrap

**Files:** `frontend-v3/index.html`, `src/contexts/ThemeContext.tsx`, `src/contexts/LocaleContext.tsx` · all **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes**.

**What would change:**
- Add a tiny inline script in `<head>` (before the module script at `index.html:23`) that: reads `localStorage["theme"]`, validates `light|dark|system`, resolves `matchMedia("(prefers-color-scheme: dark)")`, toggles `documentElement.classList("dark")`, sets `documentElement.style.colorScheme`; reads `localStorage["gula.locale"]`, validates against the 5 codes, and sets `documentElement.lang` / `.dir` using the same RTL set `{ar, ku, syr}`.
- Add the same validation in `ThemeContext.tsx:14-17` (reject unknown stored values) and remove duplicate `colorScheme` writes if redundant.
- Keep `LocaleContext.tsx:23-32` as the runtime authority after mount.

**Why safe:** no visual redesign; it removes incorrect transient frames. Mirrors the exact logic already present in `ThemeContext.tsx:25-30` and `locales.ts:12-28`, so behaviour stays consistent. `index.html` is clean.
**Coordination:** A08 (PWA/CI) — the shell is part of the PWA build; also influences `index.html:8-9` meta theme-color (C-19).

---

### C-07 — Give `Modal` real dialog semantics

**File:** `frontend-v3/src/components/ui/Modal.tsx` · **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes**.

**What would change:**
- Add `role="dialog"`, `aria-modal="true"`, `aria-labelledby` wired to the existing `<h2>` (`:43`) via `useId()`.
- Move the Escape listener off bare `window` logic into the same pattern as `Dialog.tsx:44-68` (Tab trap, first/last focus wrap), capture and restore `document.activeElement`, focus the panel/first control on open.
- Label the close button (`:44`) with `aria-label` (translate once C-10 lands).
- Make backdrop dismissal keyboard-reachable — keep `onClick` but ensure Escape covers keyboard users.

**Why safe:** reuses the already-proven implementation in `Dialog.tsx` (same repo, same dependency set); no prop/API change, so the 2 consumer files need no edits in this wave. Pure accessibility improvement.
**Do not** delete `Modal` in the same candidate — that would require page edits (A03, SR-01/SR-02).

---

### C-08 — Associate form errors with controls

**Files:** `frontend-v3/src/components/ui/{Input,Select,Textarea}.tsx` · all **CLEAN** · safe-fix eligible: **Yes** · needs approval: **No**.

**What would change (same pattern in all three):**
- `const errorId = useId();`
- `<p id={errorId} ...>` on the existing error paragraph (`Input.tsx:21`, `Select.tsx:29`, `Textarea.tsx:20`).
- On the control: `aria-invalid={error ? true : undefined}`, `aria-describedby={error ? errorId : undefined}`.

**Why safe:** additive ARIA only; no layout, colour or business logic change; no props changed. This is the clearest "safe-fix eligible, no approval" candidate and should be batched with C-17 axe tests.

---

### C-09 — Keyboard-accessible DataTable interactions

**File:** `frontend-v3/src/components/ui/DataTable.tsx` · **CLEAN** · safe-fix eligible: **Yes** · needs approval: **No** for a11y; **Yes** if i18n strings are converted in the same change.

**What would change:**
- `:61-78` — render the sortable header content inside a `<button type="button">` with `aria-sort` on the `<th>` (`ascending`/`descending`/`none`) and remove the raw `<th onClick>`.
- `:97-105` — when `onRowClick` is supplied, add `tabIndex={0}`, `onKeyDown` for Enter/Space, and an `aria-label`/instruction via a visually hidden cell or `title`.
- **(separate, approval-gated)** replace the 5 Arabic literals at `:87,93,120,129,137` with `t()` keys added to all 5 i18n resources; reuse the shared `Skeleton`/`EmptyState` primitives for `:84-95`.

**Why safe:** no data, sorting algorithm or clinical semantics change — only input modalities and accessibility metadata.

---

### C-10 — Fill i18n resource gaps in the shared shell

**Files:** `frontend-v3/src/i18n/{ku,tk,syr}.ts` and `src/i18n/{ar,en,ku,tk,syr}.ts` for `workspace.*` · all **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes** (translation owner).

**What would change:**
- Add `legal.privacyTitle` / `legal.termsTitle` to `ku.ts`, `tk.ts`, `syr.ts` (currently only `ar.ts:251-252`, `en.ts:257-258`) to stop English fallback leaking into those locales via `i18n/index.ts:20`.
- Add a `workspace.selector` key to all 5 resources; `WorkspaceSelector.tsx:77` already calls it, but the key is absent today.
- Add key-parity assertions for `legal.*`/`workspace.*` to the existing `mobileNavResources.test.ts` pattern (test file is CLEAN; coordinate with A09).

**Why safe:** additive resource entries only; no code paths change. No clinical terminology is invented — reuse existing neutral UI terms and obtain native-speaker review for `ku`/`tk`/`syr`.

---

### C-11 — Unify Loading / Error / Empty primitives

**Files:** `src/components/ui/index.ts`, `ui/EmptyState.tsx`, `ui/Skeleton.tsx`, `src/components/shared/PageComponents.tsx`, `src/components/shared/AsyncBoundary.tsx` · all **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes** (API/import change; A03 page edits follow separately).

**What would change:**
- Export `EmptyState`, `Skeleton`, `TableSkeleton`, `CardSkeleton`, `Modal`, `AsyncBoundary` and the state helpers from one barrel (`ui/index.ts` currently exports only 8 symbols at `:1-8`).
- Make `ui/EmptyState` a thin re-export of the accessible, correctly tokened shared `EmptyState` (`PageComponents.tsx:31-46`), preserving its `className` prop as an optional passthrough; make `ui/Skeleton.tsx` re-export/forward to primitive with `role`/`aria-hidden` semantics consistent with `PageLoadingSkeleton` (`:48-70`).
- Keep `AsyncBoundary`'s precedence `isLoading → isError → isEmpty → children` (`AsyncBoundary.tsx:28-40`) as the documented pattern.

**Why safe:** consolidation reuses existing implementations; no new component code. Deep-import pages continue to work during a deprecation window; migration of their imports is SR-01 (A03).

---

### C-12 — One focus-ring language

**Files:** `src/styles/index.css`, `src/components/ui/{Button,Input,Select,Textarea}.tsx` · all **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes**.

**What would change:**
- Define the canonical `.gula-focus-ring` in the **active** stylesheet using `--ring` and a consistent width/offset; remove `outline-none` from `Input.tsx:15`, `Select.tsx:16`, `Textarea.tsx:14` so the global rule (`styles/index.css:151-158`) is not suppressed, or replace their `ring-1` with the shared class.
- Remove reliance on the dead `src/index.css:149-151` definition (Button.tsx:45 will then resolve).
- Verify light `--ring` remains ≥3:1 against adjacent surfaces (current 3.91:1) after C-05.

**Why safe:** accessibility-only; no layout shift (outline/ring widths are visually subtle), high value for keyboard users.

---

### C-13 — Complete accessibility-preference token hooks

**Files:** `src/styles/index.css`, `src/components/accessibility/AdaptiveComponents.tsx`, `src/contexts/AccessibilityContext.tsx` · all **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes**.

**What would change:**
- Extend `.gula-high-contrast` and `.dark.gula-high-contrast` (`styles/index.css:167-187`) to override `--primary*`, `--secondary*`, `--accent*`, `--destructive*`, `--chart-*`, `--sidebar-*`, `--popover*` with monochrome-safe pairs.
- Map `font_size` to `--gula-text-scale` in `applyPreferences` (`AccessibilityContext.tsx:49-61`), keeping `text_scale` authoritative if both are present (document the precedence).
- Add `data-status` and `data-status-label` to `AdaptiveStateBadge`/`AdaptiveStatus` (`AdaptiveComponents.tsx:33,52`) so the existing CSS at `styles/index.css:189-199` actually renders text labels in colour-blind/reduced-colour-dependence mode.
- Add `dark:` variants or token-backed classes to `STATE_META` (`AdaptiveComponents.tsx:16-27`).

**Why safe:** strictly increases non-colour signalling and contrast; no clinical state semantics change.

---

### C-14 — First batch of hardcoded-colour → token replacements

**Files:** `src/components/ui/{Button,Badge,Card}.tsx`, `src/components/shared/GulaBrand.tsx`, `src/lib/utils.ts` · all **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes** (broad visual change).

**What would change (first, lowest-risk batch only):**
- `Button.tsx:5-10` — replace `bg-[#0D9488]`/`hover:bg-[#0F766E]` with a semantic `--primary`/`--primary-hover` token pair; replace `border-slate-200`/`hover:bg-teal-50/60` with `border-border`/`bg-accent`; keep the existing variant API.
- `Badge.tsx:14-15` — use `--success`/`--warning` aliases from C-01 instead of literal emerald/amber palettes.
- `Card.tsx:12` — `border-slate-200/80 dark:border-white/10` → `border-border`.
- `GulaBrand.tsx:24` — use brand tokens (gradient may remain a deliberate brand exception, but centralise the values).
- `lib/utils.ts:35-74,124-131` — replace status colour strings with token-backed class constants; **do not change which status maps to which semantic**.

**Why safe:** token substitution preserves component APIs and behaviour; visual output should be equal or more consistent. Must land **after C-01** so aliases resolve.
**Deferred:** layouts (`:49,63,93,160,178-199` etc.), `UpdateGate`, `ToastContainer`, `MobileBottomNav` — same approach, later batch with screenshot comparison.

---

### C-15 — Logical properties for RTL/LTR

**Files:** `src/layouts/{Sidebar,DashboardLayout,AuthLayout}.tsx`, `src/components/guide/GuideAssistant.tsx` · all **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes**.

**What would change:**
- `Sidebar.tsx:152-155` — drawer `right-0`/`border-l`/`translate-x-full` → logical `end-0`/`border-s`/appropriate `translate-x` with `[dir]` awareness; keep mobile-open/off-canvas semantics.
- `DashboardLayout.tsx:54` — `focus:right-2` → `focus:end-2` (match `AuthLayout.tsx:39`); `:159` `border-r ... pr-3` → `border-e ... pe-3`.
- `Sidebar.tsx:169,176` — `mr-auto`/`mr-2` → `ms-auto`/`ms-2`.
- `GuideAssistant.tsx:37` — derive `dir` from `useLocale().isRTL` so `ku`/`syr` remain RTL; `:65` chevron selection from the same flag.
- Reintroduce chevron mirroring into the active CSS (ported from dead `src/index.css:154-160`) or keep explicit icon logic consistently.

**Why safe:** no content or behaviour change; logical properties are already the dominant convention (80 logical usages). Requires manual verification in all 5 locales before approval.

---

### C-16 — Remove no-op animation classes

**Files:** `src/components/ui/Dialog.tsx:91`, `src/components/shared/ToastContainer.tsx:27` · **CLEAN** · safe-fix eligible: **Yes** · needs approval: **No**.

**What would change:** delete `animate-in`, `fade-in-0`, `zoom-in-95`, `slide-in-from-right-full` (and keep `duration-*` only if paired with a real transition). No dependency addition: `package.json` is USER-OWNED (SR-05), and adding `tailwindcss-animate` is **not** authorized.

**Why safe:** these classes compile to nothing today (no animation plugin in `package.json:38-60`), so removal is visually neutral. It also removes a latent RTL bug (`slide-in-from-right-full` would animate from the wrong edge if a plugin were later added).

---

### C-17 — Expand vitest-axe coverage

**Files:** `src/components/shared/PageComponents.a11y.test.tsx`, `src/components/workspace/WorkspaceSelector.a11y.test.tsx` (both CLEAN); optional new a11y tests beside `Input.tsx`/`Select.tsx`/`Textarea.tsx`/`Dialog.tsx`/`DataTable.tsx` · safe-fix eligible: **Yes** · needs approval: **Yes** (A09 coordination, SR-04).

**What would change:**
- Add cases for error-state form controls (after C-08), dialog semantics (after C-07), sortable headers (after C-09), and Toast/UpdateGate roles.
- Replace blanket `rules: { "color-contrast": { enabled: false } }` (both test files) with either enabled contrast checks or an explicit unit test over token pairs from C-05; document why any rule remains disabled.

**Why safe:** test-only additions; no production code change.

---

### C-18 — Typography / spacing scale tokens (definition only)

**File:** `src/styles/index.css` · **CLEAN** · safe-fix eligible: **Yes** · needs approval: **Yes**.

**What would change:** add a documented minimal scale to `@theme` (e.g. `--text-2xs…--text-2xl`, `--leading-tight/normal/relaxed`, `--space-*`) and reference it in the shared components that currently use `text-[9px]`, `text-[10px]`, `text-[11px]` (`GulaBrand.tsx:42`, `Sidebar.tsx:169`, `DashboardLayout.tsx:77`, `AuthLayout.tsx:116`, `MobileBottomNav.tsx:125,144`).

**Why safe if split:** defining tokens changes nothing; component migration is a second, separately approved batch. Keep minimum readable sizes and Arabic line-height ≥1.6 for body text.

---

### C-19 — Align meta theme-color

**File:** `frontend-v3/index.html:8-9` · **CLEAN** · safe-fix eligible: **Partial** · needs approval: **Yes** (+ user release for `vite.config.ts`).

**What would change:** `#ffffff` → `#f5f8fa` and `#0f172a` → `#10202b` to match active tokens (`styles/index.css:45,81`); consider updating the dark media query to follow the stored theme (linked to C-06). `vite.config.ts:18-19` PWA manifest values are **USER-OWNED/BLOCKED** and are explicitly excluded.

**Why safe:** metadata-only; no rendering change.

---

### C-20 — Mobile shell breakpoints and touch targets

**Files:** `src/components/navigation/MobileBottomNav.tsx`, `src/layouts/Sidebar.tsx` · **CLEAN** (the component `.tsx`; its test file is USER — **do not touch `MobileBottomNav.test.tsx`**) · safe-fix eligible: **Yes** · needs approval: **Yes**.

**What would change:** derive `grid-cols-{n}` from the number of rendered items + 1 instead of hardcoded `grid-cols-5` (`:109` with `:100-102`); align the nav hide breakpoint with the sidebar static breakpoint (currently `md:hidden` vs `lg:static`, leaving 768–1023px without either); raise sub-44px icon targets such as `DashboardLayout.tsx:191` `h-7 w-7` (that specific file is a separate candidate) to respect the coarse-pointer rule at `styles/index.css:231-238`.

**Why safe:** layout-only; no permission or navigation-target logic changes. Must be verified at 320/390/768/1023/1440 by A09/A08 (existing E2E at 320/390/1440 only).

---

## 3. Explicitly excluded / blocked files

| Path | Reason |
|---|---|
| `frontend-v3/src/pages/**` | A03 exclusive scope (CR-005). No A02 candidate edits here. |
| `frontend-v3/package.json`, `package-lock.json` | USER-OWNED (`git status` M). Blocks adding `tailwindcss-animate` or any new dependency. |
| `frontend-v3/vite.config.ts` | USER-OWNED (M). Blocks PWA manifest theme-colour alignment and font-cache changes. |
| `frontend-v3/src/api/endpoints.ts` | USER-OWNED (M). `AccessibilityContext.tsx:3` imports it; read-only dependency. |
| `frontend-v3/src/components/navigation/MobileBottomNav.test.tsx` | USER-OWNED (M). C-20 touches only `MobileBottomNav.tsx`. |
| Any git state operation | Forbidden by program rules; none performed. |

---

## 4. Dependency and cost analysis (constitution)

| Need | Chosen approach | Cost | Alternatives considered | Decision |
|---|---|---|---|---|
| Arabic typography | Self-host OFL Tajawal WOFF2 (C-04) | Free; existing static hosting | Google Fonts CDN (current, external coupling); paid Arabic font | **Free/open-source, self-hosted** — satisfies "Free First", "Open Source First", "Self-Hosted First", "No Vendor Lock-In". |
| Theme tokens | Plain CSS custom properties + Tailwind v4 `@theme inline` | Free; already installed | Runtime CSS-in-JS library; commercial design-token SaaS | Reuse existing stack. |
| Dialog a11y | Port logic from existing `Dialog.tsx` | Free | New headless UI dependency | Reuse before build. |
| Animations | Remove inert classes (C-16) | Free | Add `tailwindcss-animate` (MIT, free) — **blocked by user-owned manifest** | No dependency needed. |
| A11y tests | Existing `vitest-axe` | Free, already installed | Commercial a11y scanner | Reuse existing tool. |

**Zero paid dependencies introduced. No clinical content invented. No accessibility-reducing visual change proposed.**

---

## 5. Verification checklist for Wave D (not executed in Wave A)

1. `pnpm typecheck` / `pnpm lint` — no new errors (gates exist per `package.json:11-12`; execution reserved for Wave D).
2. Computed-style assertions in both themes for `--background`, `--foreground`, `--primary`, `--destructive`, `--muted-foreground`, `--border`, `--input`.
3. Contrast recomputation for every changed token pair (target ≥4.5:1 text, ≥3:1 UI components).
4. `vitest-axe` on Input/Select/Textarea error states, Dialog/Modal, DataTable, ToastContainer, UpdateGate, high-contrast and RTL modes.
5. Playwright dark-mode spec still passes (`e2e/dark-mode.spec.ts:45-47`) — note C-05 must not alter `--background`/`--foreground` or that assertion needs an approved update.
6. Mobile overflow spec at 320/390/1440 (`e2e/mobile-layout.spec.ts`) plus manual 768/1023 checks.
7. `git status --porcelain` re-verification of every touched file before Wave C, and confirmation no protected path appears in the diff.

---

**End of remediation plan. Nothing in this document has been applied.**
