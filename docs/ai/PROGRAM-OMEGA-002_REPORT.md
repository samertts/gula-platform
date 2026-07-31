# PROGRAM-OMEGA-002 — Frontend ↔ Backend Integration Report

**Status:** COMPLETE (core parity) — 2 follow-ups tracked
**Branch:** `remediate-security-001`
**Commits:** `24c8ff9b` (API parity gaps), `a1782e75` (generated client regeneration)
**Date:** 2026-07-31

---

## 1. Objective

Close every Frontend ↔ Backend integration gap in the GULA monorepo:

- Every frontend API call resolves against a real, registered backend route
- No mocks, no Firebase, no placeholder data paths in `frontend-v3/src`
- Contracts (paths, shapes, auth, roles) verified continuously by tests
- Evidence-based report on coverage, parity, and remaining blockers

## 2. Method

| Step | Artifact | Result |
|---|---|---|
| Backend inventory | FastAPI `app.openapi()` dump (1634 paths, 1956 method+path pairs) + raw route dump (1730 entries, incl. hidden routes via `original_router` traversal) | `/tmp/opencode/openapi.json`, `/tmp/opencode/backend_routes.json` |
| Frontend inventory | Static analysis of `frontend-v3/src`: 78 pages, 73 import API modules, 57 exported `*Api` objects in `endpoints.ts` (154 HTTP calls, 152 unique after alignment) | — |
| Mock/Firebase scan | Grep across `frontend-v3/src` | **Zero** Firebase imports; **zero** mock/placeholder data fetchers |
| Parity check | Every frontend path resolved against OpenAPI with path-param normalization | 151/152 matched; 1 intentional exception |

## 3. Results

### 3.1 Backend API coverage (verified against live app)

- 1634 OpenAPI paths / 1956 (method, path) pairs / 1730 raw route entries
- All 10 extracted service modules (lab, sample, admin, quality_control, metrics, mobile, test_result, stats, dashboard) wired and tested
- `/health` + `/health/ready` + `/health/status` + `/health/deep` added (public per repo observability invariants; shape-tested)
- `/api/ai/stats` + `/api/ai/export` added (tenant-scoped, role-gated, CSV/JSON)
- `/ehr/patient/{id}` + `/ehr/patient/{id}/summary` enriched to composite EHR payloads

### 3.2 Frontend coverage

- 78 pages, all lazy-loaded; 73 import real API modules
- No mocks / no Firebase / no dead data paths
- 57 API objects in `endpoints.ts`; 154 calls; **36 API objects not consumed by any page** (documented below)

### 3.3 API parity — frontend calls vs backend routes

| Check | Count |
|---|---|
| Frontend HTTP calls | 154 (152 unique) |
| Resolve to real backend routes | 151 |
| Unmatched | **1** — `GET /metrics/prom` (registered, intentionally `include_in_schema=False`; Prometheus-scraped, not schema-served) |
| Parity | **151/152 = 99.3%** (100% of schema-served calls) |

### 3.4 Generated API client regeneration (bonus)

The checked-in `frontend-v3/src/api/generated/*` (OpenAPI-style typed client) was **badly stale** (4372 lines behind) and its generator produced invalid TypeScript:

- dotted module names → invalid identifiers (`biomedical.apiApi`)
- `prefix + route` path assembly doubled segments — **373/531 (70%) generated calls hit wrong URLs**
- regex model extraction leaked method params (`db`, `skip`, `limit`) into model types
- DELETE calls passed `data` as axios config (type error)
- FastAPI `:path` converters emitted literal braces
- stale `identity.*` duplicate blocks pointed at moved/renamed namespaces

**Fixes (commit `a1782e75`, in `scripts/generate_frontend_client.py`):**

1. `extract_model_fields` rewritten with `ast` (deterministic; no signature leakage)
2. namespace sanitization (`re.sub` on non-identifier chars)
3. prefix/route de-duplication rule (route already full path ⇒ use route alone)
4. DELETE without body arg
5. `{module_path:path}` → `{module_path}`
6. deleted 10 stale `identity.*` duplicate blocks; corrected governance/trust/notification/workflow/certification routes to real paths (`/niam/...` namespaces)

**Result:** 439/439 generated calls match live OpenAPI; `tsc --noEmit` 0 errors; eslint 0; vitest 60/60.

### 3.5 Role parity (frontend guards vs backend permissions)

- 76 `RoleGuard` wrappers in `frontend-v3/src/routes/index.tsx`
- 51 adminRoutes (`master_admin/admin/lab_admin/ministry_admin/province_admin`), 16 readonly, 5 staff, 1 lab, 2 inline role arrays
- Backend permission model: 6 lab roles × capability matrix; JWT + tenant-scoped enforcement — covered by `test_integration_parity.py` (401/403 paths) and the 417 pre-existing security tests

### 3.6 Workflow parity

Every page's data flow: page → `@/api/endpoints.ts` → axios `client.ts` (JWT, 401 refresh) → real route. No page serves canned data. Verified per-page in inventory (78/78).

## 4. Test evidence

| Suite | Result |
|---|---|
| Backend full pytest (all suites, correct env secrets) | **2557 passed / 0 failed** |
| `tests/unit/test_integration_parity.py` (new, 16 tests) | pass — health endpoints public/shape/auth, AI stats tenant isolation, export CSV/JSON/403/422, EHR composite + 404 tenancy |
| `tests/test_observability_invariants.py` | pass |
| Frontend `tsc --noEmit` | 0 errors |
| Frontend eslint (`--max-warnings 0`) | 0 |
| Frontend vitest | 60/60 (4 files) |
| Generated client parity script | 439/439 |
| `enterprise_validation_engine.py --scope fast` | **VERDICT: PASS** (ruff 379 = baseline, tsc 0, eslint 0, brain 0.2d) |

Note: full-suite run requires strong env secrets (`SECRET_KEY` ≥32 chars, valid Fernet `ENCRYPTION_KEY` e.g. `6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=`, strong `NID_HMAC_KEY` + `AUDIT_ANCHOR_KEY`) — passing `ENCRYPTION_KEY=test` breaks `test_security`/`test_startup_guard` via env override.

## 5. Remaining blockers / exact next task

| # | Gap | Impact | Suggested next task |
|---|---|---|---|
| 1 | `ehrApi` (14 functions) and `canonicalPatientApi` exported but **unused by any page** | National EHR data not surfaced in UI; MPI canonical records invisible | Decide: (a) build an EHR detail panel on `EhrPage` (composite `/ehr/patient/{id}`), or (b) drop the exports. Requires product decision on national-patient identity linking (canonical ↔ national ↔ lab IDs) before wiring `canonicalPatientApi` — do not implement without the identity-matching domain design |
| 2 | 34 remaining unused API objects (healthApi, metricsApi, aiPlatformApi sub-sets, admin/subscription APIs, etc.) | Dead client surface; risk of drift | Either expose via existing pages (admin console, health status page) or remove exports |
| 3 | Generated client (`@/api/generated`) is now correct but still unused — pages use hand-written `endpoints.ts` | Two parallel client surfaces | Consolidation: migrate pages to generated client or delete it; needs a naming/decision pass |

**Recommended next task (highest value, no product decision needed):** add a System Health page (or panel in Dashboard) consuming `GET /health/status` + `/health/deep` + `/metrics` via the already-aligned `healthApi`/`metricsApi` objects — completes the observability loop for operators and retires part of gap #2. Then pursue gap #1 with the architecture team.
