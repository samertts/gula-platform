# GULA — Mustafa Parallel Work Map

Parallel engineering stream, isolated from the primary Abu Ali stream
(`claude/p0-2-pharmacy-reconciliation`). This document tracks isolation
status, scope classification, and findings for later integration.

## Isolation status

| Item | State |
|---|---|
| Branch | `claude/mustafa-parallel-engineering`, forked from `origin/main` (`46158e90`) |
| Abu Ali's branch | `origin/claude/p0-2-pharmacy-reconciliation` @ `1dbca8f0`, 134 commits / 417 files ahead of `main` |
| Overlap check | Abu Ali's diff touches `backend/app/**` broadly (identity, blood_bank, national, engineering, ai, clinical_gateway), `frontend-v3/**`, `docs/architecture/**`, `docs/pharmacy-platform/**`, `scripts/enterprise_readiness/**`, `tools/gula_intel/**`. All work below is outside that footprint. |
| Database | No shared DB used — new/changed tests run against per-test in-memory SQLite (`sqlite:///:memory:`), matching the existing test fixtures in `nhop-platform/tests/`. No migrations touched. |
| Redis | Not used by this work. |

## Scope classification

- **A (safe, implemented this pass):** `nhop-platform/` — untouched by Abu Ali,
  self-contained FastAPI service, own test suite, own (SQLite-backed) test DB.
- **C (conflict, avoided):** anything under `backend/app/`, `frontend-v3/`,
  `docs/architecture/`, `docs/pharmacy-platform/`, `scripts/enterprise_readiness/`,
  `tools/gula_intel/` — Abu Ali's active footprint.
- **E (read-only, documented below, not implemented):** the citizens/test-results
  authorization gap — touches "auth logic," which `CLAUDE.md` marks as requiring
  human approval.

## Findings

### 1. [FIXED] Shadow routes: `doctor` and `outbreak` routers never registered

- **File:** `nhop-platform/app/api/v1/__init__.py`
- **What:** `app/api/v1/doctor.py` and `app/api/v1/outbreak.py` each define a
  fully-implemented `APIRouter` with matching test suites
  (`tests/test_doctor_api.py`, `tests/test_outbreak_api.py`), but
  `api_router` in `__init__.py` only included `citizens`, `test_results`, and
  `notifications`. Every `/v1/doctor/*` and `/v1/outbreak/*` request 404'd in
  the actual running app — smart order-tests, patient overview, referral, and
  the ministry outbreak/heatmap/resistance-report endpoints were all
  unreachable dead code.
- **Reproduction (before fix):** `client.post("/v1/doctor/order-tests", ...)`
  → `404 Not Found` instead of the expected `403`/`201`.
- **Fix:** added `doctor_router` and `outbreak_router` to `api_router` in
  `nhop-platform/app/api/v1/__init__.py`.
- **Positive proof:** `nhop-platform/tests/test_doctor_api.py` (10 tests) and
  `test_outbreak_api.py` (5 tests) now pass against the real app wiring
  (previously they either 404'd or only passed against an ad-hoc `FastAPI()`
  instance built inside the test file itself, not the shipped app).
- **Negative proof:** reverting the one-line registration reproduces the
  original 404s (verified locally before committing).
- **Blast radius:** additive only — no existing route's path, method, or
  response shape changed. No migration, no schema, no auth-model change.

### 2. [FIXED] `tests/conftest.py` — collection-breaking bugs hiding 21 tests

- **File:** `nhop-platform/tests/conftest.py`
- **What (a):** `app_client` fixture calls `sys.modules` but the module never
  imports `sys` → `NameError` at fixture setup for every test using
  `app_client`. This silently broke all 9 tests in `test_doctor_api.py`
  before finding #1 above; they never actually ran in CI, they only ever
  errored during setup (a CI false-green: the suite reports failures, not a
  green false-pass, but nobody using `pytest -q` output casually would
  distinguish "9 errors, obscure NameError" from "flaky env" — it needed a
  root-cause read to see the fixture itself was broken).
- **What (b):** `test_outbreak_detection.py` (12 pure service-layer unit
  tests for the public-health outbreak/resistance-rate detector) requires a
  `db_session` fixture that was never defined anywhere in the suite —
  100% of that file errored at collection/setup, meaning the outbreak
  detection math (warning/critical ratio thresholds, heatmap, resistance
  report) had **zero** passing test evidence.
- **Fix:** added the missing `import sys`, and added a `db_session` fixture
  (bare SQLAlchemy session on an in-memory SQLite DB via `StaticPool`,
  mirroring the pattern already used in `test_outbreak_api.py`'s own
  `client` fixture).
- **Before → after:** `pytest nhop-platform/tests/` went from
  **5 passed / 21 errors** → **26 passed / 0 errors** (before finding #1),
  then **47 passed / 0 errors** after adding the new coverage in finding #3.

### 3. [FIXED] Zero test coverage on the citizen registry and test-results APIs

- **Files added:** `nhop-platform/tests/test_citizens_api.py` (12 tests),
  `nhop-platform/tests/test_results_api.py` (9 tests).
- **Why:** `app/api/v1/citizens.py` (register/search/read/update/summary —
  the core national citizen registry: national ID, phone, address, chronic
  diseases, allergies) and `app/api/v1/test_results.py` (create/validate/
  verify/list/timeline lab results, including the critical-alert path) had
  **no test file at all**. Covered: national-ID conflict (409), fuzzy
  duplicate-candidate detection (409), national-ID validation (422), exact
  vs. substring search semantics, immutable-field rejection on update (422),
  implausible-value rejection, lab-must-be-active check, verify-is-one-shot
  (409 on second verify), abnormal-result filtering, and timeline grouping.
- **Always-safe per `CLAUDE.md`:** "Add test cases for untested business
  logic" — no production behavior changed by this file addition.

### 4. [FINDING ONLY — D, requires human approval] `citizens.py` and `test_results.py` have no authorization check at all

- **Files:** `nhop-platform/app/api/v1/citizens.py`,
  `nhop-platform/app/api/v1/test_results.py`
- **Evidence:** `nhop-platform/app/core/rbac.py` already exists and is used
  by `outbreak.py` (`require_roles(Role.MINISTRY, Role.ADMIN)`); `doctor.py`
  has its own `_require_doctor` dependency (403 on wrong/missing role, 401 on
  missing actor id). Neither `citizens.py` nor `test_results.py` has any
  such dependency — every endpoint (register a citizen, search the entire
  registry by name/national ID, read any citizen's full record including
  national ID/phone/address/chronic diseases/allergies, update any citizen,
  create/read/verify lab results, read the critical-alert path) is callable
  with **no header, no token, nothing**. `core/rbac.py`'s own module
  docstring says "routes that need authorisation" use this pattern —
  citizen PII and lab results plainly need it, and the sibling route files
  in the same package already do it, which points to this being an
  oversight rather than a deliberate phased rollout.
- **Reproduction:** `client.get("/v1/citizens/search", params={"q": "any name"})`
  with no headers at all returns `200` with full citizen records, in the
  existing (now-passing) test suite — see any test in
  `test_citizens_api.py` that omits headers entirely and still gets `200`.
- **Recommended fix:** apply `require_roles(...)` (or the `doctor.py`-style
  actor-id dependency, per endpoint) to `citizens.py` and `test_results.py`,
  matching the existing per-endpoint role needs (e.g. `LAB`/`ADMIN` for
  result creation, broader read access gated by role for citizen lookup).
- **Test design for the fix:** for each endpoint, a 401 case (missing
  role/actor header) and a 403 case (wrong role), plus the existing 2xx
  happy-path tests re-run with the now-required header attached.
- **Why not fixed here:** this is an authorization-logic change to
  patient-PII endpoints and would change the API's response contract for
  any existing caller that doesn't send the new header —
  `CLAUDE.md`'s "Requires human approval" bucket covers both "Changes to
  JWT/auth logic" and "API response-shape changes," and this finding sits
  at the intersection of both. Classified **D — protected**, not touched.

## Verification (this pass)

```
cd nhop-platform && PYTHONPATH=<repo-root> python3 -m pytest tests/ -q
# 47 passed, 3 warnings (Starlette httpx/deprecation warnings, pre-existing)
```

## Integration notes

- No migration impact, no DB schema impact, no change to any endpoint's
  request/response shape (findings #1–#3 are additive/test-only).
- Finding #4 needs a human decision on role model before implementation —
  flagging for the primary stream or a follow-up approved task rather than
  guessing at the intended role matrix.
- No file in this change set overlaps Abu Ali's active diff (verified via
  `git diff --stat origin/main...origin/claude/p0-2-pharmacy-reconciliation`).

## Next independent work (not started this pass)

- `services/device_bridge/` (LabLink-Core): no raw SQL found on first pass;
  worth a closer concurrency/idempotency look at ASTM/HL7 ingestion.
- `nhop-platform` citizen registry vs. `backend/app` patient registry: two
  separate "patient" concepts (`Citizen`/`LabTest` here vs. `Patient`/
  `LabResult` in the monolith) with no visible reconciliation — worth an
  architecture-contradiction writeup once Abu Ali's active identity/MPI
  work settles enough to compare against.
- `edge_agent/`, `client/`, `frontend/`, `frontend-v2/` remain unaudited and
  are outside Abu Ali's current footprint.
