# P4 Phase 4 — UX Audit v1.0 (frontend-v3)

**Platform:** GULA National Health Platform
**Branch:** `remediate-security-001` (commit `eb6cf022`)
**Date:** 2026-08-02

## Scope

Automated + targeted audit of `frontend-v3` (Arabic-first, RTL): i18n parity,
hardcoded strings, accessibility (ARIA on interactive elements), and loading/
error/empty state coverage on the 9 active workflow pages.

## Results

### 1. i18n parity — PASS

| Metric | Value |
|---|---|
| Arabic keys | 508 |
| English keys | 508 |
| Parity | 100% (ar ↔ en identical key sets) |

Audit tool: `/tmp/opencode/i18n_audit.py` (recursive TS-object key extractor).
The earlier 354-key parity grew to 508 as new pages shipped keys; parity held.

### 2. Hardcoded strings — 1 found, fixed

- `OrdersPage` notification channel `<option>` values (`SMS` / `Email` / `Push`)
  were hardcoded English. Fixed with `order.channelSms/Email/Push` keys
  (Arabic: رسالة نصية / بريد إلكتروني / إشعار فوري).
- No other hardcoded UI strings found in `src/pages` (regex scan for
  `>[A-Za-z ...]<` excluded translation calls).

### 3. Accessibility — 44 tab patterns fixed

44 pages (capabilities, systems, national docs) shared an identical tab-button
pattern with no ARIA semantics. All now emit `role="tab"` +
`aria-selected={activeTab === tab.id}` — WCAG 4.1.2 (name, role, value).

Additional a11y findings:
- `<input>` elements: 0 rendered without `aria-label`/`placeholder`/`id`+`name`
- `<button>` elements: 62 without explicit `aria-label`; all 62 carry visible
  text content (`>{label}`) so they are nameable per WCAG — acceptable.
- `DashboardPage` `aria-busy` on the stat grid during loading.

### 4. Loading / error states

| Page | loading | error | empty | Notes |
|---|---|---|---|---|
| DashboardPage | ✓ (fixed) | ✓ (fixed) | — | was raw `...` + silent failure |
| PatientsPage | ✓ | ✓ | ✓ | DataTable pattern |
| OrdersPage | ✓ | ✓ | ✓ | DataTable pattern |
| ResultsPage | ✓ | ✓ | — | |
| SamplesPage | ✓ | ✓ | — | |
| QcPage | ✓ | ✓ | ✓ | |
| ProfilePage | ✓ | ✓ | — | |
| SettingsPage | — | — | — | form-only page |

Dashboard was the only gap: it rendered `...` during loading and had no error
path. Now shows a retryable error card (`common.error` + `common.retry`) and an
`aria-busy` em-dash placeholder.

## Verification

- `tsc --noEmit`: 0 errors
- `eslint`: 0 errors
- `vitest`: 122/122 pass (9 files)
- i18n parity gate: 508 = 508
- Production build: OK

## Verdict

**UX AUDIT v1.0: PASS** — i18n parity 100%, hardcoded strings eliminated from
active pages, tab ARIA across 44 pages, dashboard loading/error states added.
Remaining items are documented non-blocking observations (62 nameable
icon-buttons, empty-state polish on Results/Samples).
