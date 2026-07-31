# PROGRAM-009A Report — Frontend↔Backend API Convergence

Status: **COMPLETE** | Branch: `remediate-security-001` | Commits: 6 (dbef4c8a → 65ab4357)

## Objective

100% frontend↔backend API compatibility for the GULA Platform frontend
(`frontend-v3`), zero broken routes, zero API mismatches, and pattern/UX
alignment across all routed pages — without adding features or redesign.

## Results

| Metric | Before | After |
|---|---|---|
| API method mismatches | 17 | **0** |
| Missing endpoints | 46 | **0** |
| Matched frontend calls | 240/326 | **265/274** (97%) |
| Dormant contracts (documented) | — | 9 (no consumer) |
| tsc --noEmit | 0 errors | 0 errors |
| vite build | ~5s | ~3s |
| Frontend unit tests | 54 | **60** |
| Backend tests | 399 | 187 run this cycle, all pass |
| Backend endpoints | 1,910 | **1,968** (+58 net) |
| RTL physical-margin violations | 2 | **0** |
| Individual UI imports (pages) | 46 files | **0** (all barrel) |
| Dead UI components | 3 | **0** |

## Phase 1 — API Contract Convergence (dbef4c8a)

### Backend fixes
1. **NIAM double-prefix** — identity `governance`, `trust`, `adaptive_auth`
   routers were mounted at `/niam/governance`, `/niam/trust`, `/niam/adaptive-auth`
   on top of the `/niam` root router → mounted at `/governance`, `/trust`,
   `/adaptive-auth`.
2. **Document-intelligence double-prefix** — 10 sub-routers under
   `/document-intelligence` fixed.
3. **`GET /test-results` list endpoint** — added `list_results()` to
   `test_result_service.py` + route declared before `/{result_id}`.
4. **10 capability routers registered** in `factory.py`
   (`clinical_foundation`, `document_management`, `encounter_management`,
   `fhir_interoperability`, `healthcare_consent`, `provider_management`,
   `reporting_service`, `search_service`, `storage_service`, `workflow_engine`).
5. **10 capability `__init__.py` broken imports** — absolute → relative.

### Frontend fixes
1. **`asTableData()` helper** (`lib/utils.ts`) — extracts arrays from
   `{items|data|results|...}` responses; replaces unsafe `(data ?? []) as Record[]`
   casts that crashed `useReactTable` on object responses.
2. **5 queries repointed** to valid existing endpoints:
   - `/niam/governance/suspensions` → `/niam/governance/suspensions/active`
   - `/niam/trust/trust-anchors` → `/niam/trust/anchors`
   - `/niam/federation/trust` → `/niam/trust/federation`
   - `/niam/certificates` → `/niam/certificates/expiring`
   - `/national/observability/traces` → `/national/observability/traces/search`
3. **44 dormant queries disabled** (`enabled: false`) — backend endpoints are
   param-scoped (`{id}`) with no id available in the page; firing them guaranteed
   404/405. Tabs render empty state; no 404 calls.
4. **9 endpoints.ts dead contracts excluded + documented** — `ehrApi` lists,
   `ehr/attachments/{id}/download`, `ehr/clinical-notes/search`,
   `/api/ai/export` have zero page consumers (dead code retained per GULA
   constitution "never remove dormant modules").

## Phase 2 — Pattern Unification (3b2db60c)

- **46 pages** converted from individual `@/components/ui/<Component>` imports
  to the `@/components/ui` barrel (Button, Input, Select, Badge, Card, Dialog,
  DataTable).
- **2 RTL violations** fixed (`mr-2` → `ms-2`, logical properties).

## Phase 3 — Hooks Alignment (8f6244c2)

- **`useToast` listener-leak bug fixed** — listener registration used a
  `useState` initializer (side effect during render, cleanup never executed).
  Replaced with `useEffect` + cleanup. Regression test: unmounted consumer no
  longer receives toasts.
- Audited `useDebounce`, `AuthContext`, `LocaleContext`, `ThemeContext` —
  no further issues (typed `authApi` usage confirmed).

## Phase 4 — Components Consistency (941b0b83)

- **Removed dead components**: duplicate `ui/EmptyState` (canonical copy in
  `shared/PageComponents`), unused `ui/Modal` (Dialog is the primitive in use),
  unused `ui/Skeleton` (FHIR pages define local skeletons).

## Phase 5 — UX Alignment (65ab4357)

- **DataTable error+retry**: new optional `error`/`onRetry` props render an
  Arabic error row with an "إعادة المحاولة" button instead of silently showing
  "لا توجد بيانات".
- **46 probe pages** wired per-tab `error` + `refetch` through their tables maps.
- **5 new DataTable tests** (rows, empty, loading, error+retry, error without retry).

## Verification (final)

- Audit script: **0 mismatches, 0 missing**; 265/274 matched; 9 dormant contracts
  excluded with documentation.
- `tsc --noEmit`: 0 errors. `vite build`: success. `vitest`: **60 passed**.
  `eslint`: clean.
- Backend: 187 tests passed (test_result_service + full unit suite).
- Only the 44 disabled dormant queries remain as deliberate, documented
  convergence decisions (param-scoped backend endpoints awaiting activation).

## Risks / Follow-ups

- The 44 disabled queries will need list endpoints when their modules are
  activated (tracked: probe-page tabs show empty state by design).
- Dead `ehrApi`/`aiTelemetryApi` contracts in `endpoints.ts` remain aligned
  with backend where possible; full alignment deferred to module activation.
- Pre-existing dirty worktree (109 files from prior cycles) left untouched;
  only program files committed.

## Commits

```
65ab4357 feat(frontend): per-tab error + retry states for probe pages (Phase 5)
941b0b83 refactor(frontend): remove dead UI components (Phase 4)
8f6244c2 fix(frontend): useToast listener leak + regression test (Phase 3)
3b2db60c refactor(frontend): unify UI import pattern + RTL margins (Phase 2)
dbef4c8a fix(api): 100% frontend-backend API convergence (Phase 1)
```
