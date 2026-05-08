# Frontend-v2 UX Audit & Hardening — May 2026

This document accompanies the UX, navigation, and reliability audit performed on
`frontend-v2/`. It records the issues we found, the modules added/changed to
address them, and the behaviour contracts a new contributor needs to follow
when extending these subsystems.

The audit was deliberately **scoped to non-breaking, modular changes**. No DB
schema, API surface, RBAC behaviour, or core architecture was altered.

---

## 1. Audit findings

### 1.1 Command palette
| # | Issue | Severity |
|---|-------|----------|
| 1 | Hardcoded patient-detail destinations (`/doctor/patient/P-9021`) that did **not match** `App.tsx` routes — clicking them silently rewrote to a 404 fallback. | High |
| 2 | Quick-action buttons used `alert()` placeholders instead of real flows (e.g. "Order CBC Panel"). | Medium |
| 3 | No arrow-key navigation, no Enter to select, no Home/End. Mouse-only. | High (a11y) |
| 4 | No focus restoration when the palette closed — a screen-reader user could end up focused on `<body>`. | High (a11y) |
| 5 | `actions` array rebuilt on every render. | Low (perf) |
| 6 | No role/wing filtering — citizens saw "Lab" actions and vice-versa. | Medium |
| 7 | Missing aria roles (combobox / listbox / option). | High (a11y) |

### 1.2 Keyboard shortcuts
| # | Issue | Severity |
|---|-------|----------|
| 8 | `?` opened the shortcuts overlay, but no Vim-style chords existed for navigation despite the modal hinting at `G L` etc. | Medium |
| 9 | Shortcut listener fired even when typing in `<input>` only by tag-name check — `contenteditable` was not handled. | Medium (a11y) |
| 10| `/` (focus search) — a near-universal pattern (Slack, GitHub, Linear) — was not implemented. | Low |

### 1.3 Loading states
| # | Issue | Severity |
|---|-------|----------|
| 11| `RecordsView`, `LabResultsView`, `WorkQueue`, and `SettingsView` had **no skeleton** — they showed completed data immediately or a blank table. | Medium (perceived perf) |
| 12| `Skeleton.tsx` exported only `Skeleton` and `DashboardSkeleton`. No table/list/card variants. | Medium |
| 13| `AppContent` shows a centred spinner during auth load — fine for ≤300 ms, but no fallback if hydration takes longer. | Low |

### 1.4 Empty states
| # | Issue | Severity |
|---|-------|----------|
| 14| No reusable `EmptyState` component. Empty surfaces either hid silently or showed raw "0 results" text. | High |
| 15| Filtered patient list with no matches gave the user no way to clear the filter except erasing manually. | Medium |

### 1.5 Error boundaries
| # | Issue | Severity |
|---|-------|----------|
| 16| **No** route-level error boundary. A render exception in any view would crash the entire shell — sidebar, topbar, palette, all gone. | High |

### 1.6 Optimistic UI
| # | Issue | Severity |
|---|-------|----------|
| 17| `LabDashboard` task mutations called `setActiveTasks` directly with no rollback on commit failure. | Medium |
| 18| No shared helper meant each view re-invented optimistic flows ad hoc. | Medium |

### 1.7 Navigation hierarchy
| # | Issue | Severity |
|---|-------|----------|
| 19| Sidebar links to `/research/analytics`, `/research/population`, `/ministry/inspections`, `/ministry/registry` — **none of which are mapped** in `App.tsx`. They redirect to `/` via the catch-all. | Medium |
| 20| The wing switcher routes to `/research/analytics` for the researcher wing, hitting the same dead-link redirect. | Medium |
| 21| `/intelligence` exists in `App.tsx` but the doctor sidebar uses the same path — fine, but no breadcrumb for it. | Low |

> The dead routes are flagged here but **were not fixed** because the constraint
> excluded route-table changes. Action item logged for a follow-up PR.

### 1.8 Mobile / RTL ergonomics
| # | Issue | Severity |
|---|-------|----------|
| 22| Patient table rows on `/patients` were clickable but lacked keyboard focusability and `role="button"`. | Medium (a11y) |
| 23| `MoreHorizontal` row action button propagated to the row click — opening the patient detail when the user expected a popover. | Medium |

---

## 2. Implemented improvements

### 2.1 New modules
| File | Role |
|------|------|
| `src/lib/commandRegistryCore.ts` | Pure (React-free) helpers: `wingsForProfile`, `filterByWings`, `scoreCommand`, `searchCommands`, `stepSequence`. Tested with `node --test`. |
| `src/lib/commandRegistry.ts` | Registry of palette commands. Every entry points to a real route in `App.tsx`. Wing/role gated. Bilingual via `t`. |
| `src/lib/useShortcut.ts` | `useShortcut` (single keystroke) and `useKeySequence` (chords). Skips editable fields and `contentEditable`. |
| `src/lib/useOptimistic.ts` | `useOptimisticAction(initial, onError?)` — apply / commit / rollback / retry. |
| `src/components/ui/EmptyState.tsx` | Reusable empty surface with up to 2 CTAs and a hint. |
| `src/components/ui/ErrorBoundary.tsx` | `RouteErrorBoundary` — auto-resets when `resetKey` (e.g. `location.pathname`) changes. |
| `src/lib/__tests__/commandRegistryCore.test.ts` | 20 pure tests for scoring, filtering, sequence machine. |
| `docs/UX_KEYBOARD_SHORTCUTS.md` | User-facing shortcut reference. |

### 2.2 Modified modules
| File | What changed |
|------|--------------|
| `src/App.tsx` | Wraps `<AnimatedRoutes>` in `<RouteErrorBoundary resetKey={location.pathname}>`. Mounts `<GlobalShortcuts>` for `g d` / `g p` / `g a` / `g i` / `g l` / `g q` / `g s` / `g h` and the `/` palette focus. Listens for the `open-shortcuts` CustomEvent so the palette can open the overlay. |
| `src/components/CommandPalette.tsx` | Rewritten. Real routes, keyboard navigation (↑↓/Home/End/Enter/Esc), focus restore on close, aria-combobox/listbox/option, role/wing filtering, scroll-into-view. |
| `src/components/ShortcutsModal.tsx` | Reflects all new shortcuts. Keyboard categories: Global / Navigation / Workflow. Adds aria-modal and Esc-on-overlay. |
| `src/components/ui/Skeleton.tsx` | Adds `TableSkeleton`, `ListSkeleton`, `CardSkeleton`, `StatGridSkeleton`. Adds `aria-busy`. |
| `src/views/RecordsView.tsx` | Wired to skeleton, empty state, and accessible row activation (Enter/Space, focus ring, role=button). |

### 2.3 Behavior preserved
- Visual identity: every new component matches the existing rounded-3xl, slate-50/indigo-600 palette.
- RTL: all new components use `dir`-agnostic Tailwind utilities or read `useLanguage().isRtl`.
- Mobile: every new surface uses fluid grids and works in <640 px.
- Offline: no new components touch network/storage.
- RBAC: palette filters by `profile.role` via the existing wing mapping.
- Bundle: zero new dependencies. `cmdk` (already installed but unused) is not pulled in to keep behaviour explicit and visual identity intact.

---

## 3. Before / after workflow impact

| Workflow | Before | After |
|----------|--------|-------|
| Doctor jumps from a patient profile to the work queue | 3 clicks: open sidebar → expand "Lab Wing" → click "Work Queue" | `g q` (2 keystrokes) |
| Lab tech opens command palette | Click TopBar search input | `Cmd K` or `/` from anywhere |
| User filters patient list with zero matches | Sees an empty table; types again or backspaces filter manually | Sees `EmptyState` with "Clear filter" CTA |
| Render error in a view | Entire app shell unmounts; user sees a blank page | Subtree shows recover/retry/home; sidebar/topbar/palette stay alive |
| Loading the records page | Brief flash of empty table → data swaps in (CLS) | `TableSkeleton` of identical column count → table replaces it without layout shift |
| Citizen accidentally sees Lab commands in palette | Listed regardless of role | Filtered out by wing |
| Screen-reader user navigates the palette | No aria roles, no live-region | combobox/listbox/option with `aria-activedescendant`, focus returns on close |

---

## 4. Tests

```bash
cd frontend-v2
node --experimental-strip-types --test src/lib/__tests__/commandRegistryCore.test.ts
```

20 tests pass: scoring, role filtering, sequence-machine timeout/reset/lowercase.

The tests deliberately avoid React/JSDOM so they run in the existing dev
container with no extra dependencies. Once `vitest` is added (small,
worth-justifying on its own), interaction tests on `<CommandPalette/>` and
`<EmptyState/>` should be added next.

---

## 5. Follow-up audit items (out of scope for this PR)

These are documented but **not implemented**, in line with the "minimal
disruption" constraint.

1. **Map orphan routes**: `/research/analytics`, `/research/population`,
   `/ministry/inspections`, `/ministry/registry`. Each is referenced from the
   sidebar but missing from `App.tsx`.
2. **Apply skeleton/empty/error treatment** to: `LabResultsView`,
   `WorkQueue`, `SampleTracking`, `MedicationCenter`, `FamilyManagement`,
   `AppointmentsView`, `SettingsView`. The primitives exist; each surface
   needs ~20–40 LOC of wiring.
3. **`useOptimisticAction` adoption**: refactor `LabDashboard`'s
   `handleAssign` / `handleUpdateStatus` / `handleBulkAction` to use it so
   transient Firestore failures roll back cleanly with a toast retry.
4. **Sidebar pin reorder**: long-press / drag to reorder pinned items.
5. **Mobile bottom-tab bar**: the sidebar collapses to a hamburger drawer on
   mobile, but the most-used 4 actions (dashboard / patients / palette /
   settings) deserve a thumb-zone bottom bar.
6. **Vitest setup**: enables interaction tests on `<CommandPalette/>` —
   small dev-dep, big test surface.
