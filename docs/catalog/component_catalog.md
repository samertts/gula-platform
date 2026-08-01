# Component Catalog

> All shared components with usage.

| Component | Lines | API usage | Notes |
|---|---|---|---|
| `components/__tests__/DataTable.test.tsx` | 40 | — |  |
| `components/__tests__/ui-components.test.tsx` | 198 | — |  |
| `components/auth/RoleGuard.tsx` | 25 | — | route-level role gate |
| `components/shared/PageComponents.tsx` | 77 | — | LoadingSpinner/EmptyState/ErrorDisplay |
| `components/shared/ToastContainer.tsx` | 42 | — | no aria-live |
| `components/ui/Badge.tsx` | 30 | — | status badges |
| `components/ui/Button.tsx` | 51 | — | base button, variants |
| `components/ui/Card.tsx` | 34 | — | card container |
| `components/ui/DataTable.tsx` | 160 | — | loading/error/empty built-in; no caption/scope/aria-sort |
| `components/ui/Dialog.tsx` | 63 | — | Escape + scroll-lock; NO role/aria-modal/focus trap |
| `components/ui/Input.tsx` | 27 | — | has error prop - used by 0 pages |
| `components/ui/Select.tsx` | 35 | — | has error prop - used by 0 pages |
| `components/ui/Textarea.tsx` | 26 | — | basic |
| `components/ui/index.ts` | 8 | — |  |

## Findings

- UI kit is small (10 files) and consistent; DataTable centralizes loading/error/empty.
- No specialized components: no DatePicker, no Autocomplete, no Pagination, no Chart wrapper (0 charts anywhere), no FileUpload, no Print button, no Export button.
- Dialog lacks accessibility semantics; DataTable lacks table semantics.
- No reusable form field wrapper with validation.
- `error` props on Input/Select are never used - dead API surface.
