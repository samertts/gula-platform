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
- **E (read-only, documented below):** batch 1 flagged the citizens/test-results
  authorization gap as D/protected; batch 2 revisited it under corrected
  guidance and implemented the role-based part (see finding #9) — the one
  piece still E is citizen self-access, which needs an identity binding
  that doesn't exist yet anywhere in nhop-platform.

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

### 4. [RESOLVED — see Batch 2 §9] `citizens.py` and `test_results.py` have no authorization check at all

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

## Batch 2 — device_bridge forensic sweep + authorization decision + NHOP/Patient resolution

Isolation re-checked before starting: re-ran
`git diff --stat origin/main...origin/claude/p0-2-pharmacy-reconciliation`
— still zero overlap with `services/device_bridge/`, `nhop-platform/`, or
`docs/engineering/`. One file this batch touches sits formally under
`backend/app/` scope (`backend/app/routes/device_results.py` was *read*,
not edited — see §8) but is untouched by Abu Ali's diff and is a different
capability (lab device ingestion) from his pharmacy-reconciliation work.

### 5. [FIXED] device_bridge: auth footgun + whole test suite never ran

- **Files:** `services/device_bridge/app/security/auth.py`,
  `services/device_bridge/tests/conftest.py` (new),
  `test_sync_and_auth.py`, `test_device_onboarding_api.py`.
- **What:** `verify_api_key()` called `sys.exit(1)` when `LABLINK_API_KEY`
  was unset — killing the whole process (every other device's in-flight
  connection along with it), not just failing the one request. It also
  compared the key with `!=` (timing side-channel). Separately, two test
  files imported `DEFAULT_API_KEY` from `app.security.auth`, which has
  never existed on any branch in this repo's history — an `ImportError` at
  collection that took the entire 12-file suite down with it (0 tests
  collected).
- **Evidence a fix already existed, unmerged:** commit `3f7aba82` ("fix:
  enforce truthful data preservation and security gates") already applied
  `hmac.compare_digest` + `HTTPException(503)` on two abandoned branches
  (`fix/main-migration-graph-20260822`,
  `fix/migration-sqlite-compatibility-20260826`, neither an ancestor of
  `main` or of Abu Ali's branch) — ported that exact fix rather than
  re-deriving it. Neither branch defines `DEFAULT_API_KEY` either, and for
  good reason: a hardcoded default key in production code is itself the
  vulnerability the rest of that fix was removing. The correct fix for the
  tests is a test-only fixture, not a production constant.
- **Fix:** `hmac.compare_digest` + 503-not-crash in `auth.py`;
  `tests/conftest.py` gained an autouse fixture that sets `LABLINK_API_KEY`
  to a test-only value, plus an `api_key_headers` fixture used at every
  call site that previously imported the dead constant.
- **Before → after:** 0 collected (2 collection errors) → 29 passed.

### 6. [FIXED] device_bridge: failed-delivery retry path silently dropped data

- **Files:** `services/device_bridge/app/core/retry_queue.py`,
  `app/pipeline/data_pipeline.py`, `app/pipeline/normalizer.py`,
  `app/main.py`; test: `tests/test_retry_and_sync_recovery.py` (new, 4
  tests).
- **Three compounding bugs**, found by tracing what actually happens after
  a GULA send fails (not just reading the retry_queue class in isolation):
  1. `retry_queue.enqueue()` stored only `[test_code, ...]` strings — no
     patient_id, value, unit, or timestamp survived, so even a working
     retry mechanism would have nothing left to resend.
  2. `main.py` read `retry_queue.list_all()` (which never removes
     anything) after every `/ingest` call. One persistent failure got
     re-staged into `sync_engine` again on every subsequent request,
     forever, each time under a fresh `uuid.uuid4()` — which also defeated
     `sync_engine`'s own item_id-based dedup, so the queue grew
     unboundedly across the life of the process.
  3. `POST /edge/sync`'s `sender` moved the item into `pipeline.edge_buffer`
     and unconditionally returned `{"status": "ok"}`. `sync_engine`
     treated that as a real delivery and dropped the item from its queue —
     but nothing had actually called GULA. A "successful retry" was
     indistinguishable from silent data loss from the operator's point of
     view (the health check would show `remaining: 0`, looking recovered).
- **Fix:** `NormalizedResult` now carries `barcode` (was already flowing
  through the pipeline, just never attached); `retry_queue.enqueue()`
  stores `asdict()` of the full result plus a content-derived
  `idempotency_key` (`retry_queue.content_key()` — sha256 over
  device_id + patient_id + test_code + value + timestamp, so re-staging
  the same failure collapses instead of piling up); `RetryQueue.drain()`
  (list+clear, mirroring the existing `EdgeAgentBuffer.drain()` pattern)
  replaces `list_all()`; `/edge/sync`'s sender reconstructs
  `NormalizedResult` objects and calls the real `gula_client.send_results()`.
- **Before → after:** 29 passed → 33 passed (4 new).

### 7. [FIXED] device_bridge -> GULA payload contract was 100% incompatible

- **File:** `services/device_bridge/app/integration/gula_client.py`; test:
  `tests/test_gula_client_contract.py` (new, 3 tests, no backend import
  required — see its docstring for why).
- **What:** `GulaClient.send_results()` posted
  `{"lab_id", "results": [{"patient_id", "test_code", "value", "unit",
  "timestamp"}]}` with **no auth header at all**. The real, already-live
  backend endpoint — `backend/app/routes/device_results.py`'s
  `POST /device/results` — expects `DeviceSubmission`:
  `{"barcode", "device_id", "results": [{"test_name", "value",
  "value_text", "unit", "normal_range_low", "normal_range_high"}]}` and
  requires `Depends(get_current_user)` (a JWT-bearing `LabUser`); it
  doesn't read `lab_id` from the body at all (tenant scope comes from the
  authenticated user). Every real submission would 422 on the missing
  `barcode` field alone, before auth was even checked — the two services'
  wiring together was completely non-functional, not just missing
  hardening.
- **Fix (device_bridge side only, matching the backend's unchanged,
  live contract — confirmed not in Abu Ali's diff):** send the correct
  shape using the barcode from finding #6; fail fast with
  `{"status": "failed", "error": "missing_barcode"}` (no network call) when
  a batch has no barcode; add an optional bearer-token pass-through
  (`GULA_DEVICE_BEARER_TOKEN` env var / `auth_token` constructor arg).
- **Before → after:** 33 passed → 36 passed (3 new).

### 8. [FINDING ONLY — D, needs a migration] `POST /device/results` has no idempotency protection

- **File:** `backend/app/routes/device_results.py` (read, not edited —
  see the isolation note above).
- **Evidence:** the endpoint has no idempotency_key field, and no
  natural-key dedup check before `db.add(LabResult(...))` — a resend of
  the identical `DeviceSubmission` (which finding #6 shows was a real risk
  before this pass: the retry path could stage the same failure more than
  once) creates a second, indistinguishable `LabResult` row every time.
  The canonical mechanism for exactly this already exists in this repo —
  `backend/app/integration/inbox.py`'s `IntegrationInboxEvent` +
  `idempotency_key`, with `stage_event()` already implementing "same
  event_id, different idempotency_key -> reject" and "same
  idempotency_key, different event_id -> reject" — reuse that design
  rather than invent a second one.
- **Why not fixed here:** wiring `device_results.py` through to that
  pattern means either adding an `idempotency_key` column (a migration —
  `CLAUDE.md`: "DB schema changes... Requires human approval") or a
  heuristic dedup on existing columns, which risks silently rejecting a
  legitimate distinct-but-same-value re-test for a clinical result — worse
  than the bug it would fix. Classified **D — protected**.
- **Recommended fix:** add `DeviceSubmission.idempotency_key: str`
  (client-generated, e.g. device_bridge's own `content_key()` from
  finding #6), a migration adding a unique `idempotency_key` column to
  `lab_results` or a new dedup table modeled on `IntegrationInboxEvent`,
  and a pre-insert check mirroring `stage_event()`'s logic.

### 9. [DECIDED + IMPLEMENTED] Citizen/results authorization — derived from existing policy, not left as a punt

Per corrected guidance: investigated whether the role model was actually
derivable from existing architecture before defaulting to "needs a human."
It was — `core.rbac.require_roles` already exists and is already used by
two sibling files in this same package (`outbreak.py`:
`require_roles(Role.MINISTRY, Role.ADMIN)`; `doctor.py`: its own
`_require_doctor` dependency). Implemented (see the commit for the full
per-endpoint role table): mutations -> LAB/DOCTOR/ADMIN
(`create_test_result` -> LAB/ADMIN only, matching doctor.py's own
division of labor: a lab produces results, a doctor orders/verifies);
reads -> add MINISTRY, matching outbreak.py's oversight precedent.

**Deliberately left unmodeled:** a citizen reading only their own record.
nhop-platform has no session/identity binding anywhere that could prove
"this caller IS this health_id" — that's a new policy semantic (subject/
ownership-based access control layered on top of role-based control), not
an inference from what already exists, so `Role.CITIZEN` is excluded from
every allowed set below rather than guessed at. This is the one piece of
the original finding that stays **D — protected**; the rest is fixed.

### 10. [INVESTIGATED, RESOLVED — E, no action needed] nhop `Citizen` vs. backend `Patient`: separate bounded contexts, not duplication

Question from batch 1: are `nhop-platform`'s `Citizen`/`LabTest` and
`backend/app`'s `Patient`/`LabResult` a duplicate domain, a compatibility
layer, or genuinely separate systems? Resolved by evidence, not
assumption:

- `CLAUDE.md` itself documents the intended split: "`nhop-platform/` —
  National Health Oversight Platform... Owns the national citizen
  registry; GULA owns the per-lab LIMS view." This is a designed
  national-HIE-over-per-facility-LIMS pattern, not an accident.
- The backend already models NHOP as an external system with a
  cross-reference code, not an internal duplicate:
  `backend/app/governance/models/laboratory.py:42` and
  `backend/app/national/domain/laboratory.py:29` both carry a
  `nhop_lab_code` column; `backend/app/national/domain/organization.py:33`
  carries `nhop_code`; `backend/app/interoperability/trust_domain.py:27`
  lists `NHOP = "nhop"` as one of the recognized external trust domains.
- No code anywhere in `backend/app` calls `nhop-platform`'s API (or vice
  versa) — the cross-reference columns exist, but live data sync between
  a GULA `Patient` and an NHOP `Citizen` is not implemented yet. That's a
  legitimate future-integration gap (worth its own ticket once someone
  needs it), not a bug and not something to merge/delete toward — per the
  Mustafa brief's own instruction, nothing here was merged or deleted;
  ownership was proven first, and ownership is: separate, intentional,
  not yet wired together.

## Verification (Batch 2)

```
cd nhop-platform && PYTHONPATH=<repo-root> python3 -m pytest tests/ -q
# 51 passed (was 47)

PYTHONPATH=<repo-root> python3 -m pytest services/device_bridge/tests/ -q
# 36 passed (was 0 collected — 2 collection errors)
```

## Batch 3 — security review of Batch 2's authorization fix

Requested before continuing: review whether finding #9's `require_roles`
gate on citizens.py/test_results.py is real access control, since "callers
must send some header" is not the same claim as "callers are
authenticated."

### 11. [CONFIRMED DEFECT, DOCUMENTED — coordination finding, not fixed here] `X-Role` is client-controlled input, not verified server-side context

- **Files:** `nhop-platform/app/core/rbac.py` (existing, unchanged by me);
  `nhop-platform/app/api/v1/citizens.py`,
  `nhop-platform/app/api/v1/test_results.py` (my finding #9 fix, now
  re-documented — see below).
- **Verdict: unsafe, confirmed.** `require_roles()`'s dependency reads the
  raw `X-Role` HTTP header (`Header(default=None, alias="X-Role")`),
  uppercases it, and checks set membership. That is the entire check —
  no JWT decode, no signature, no session lookup, no cross-reference to
  any other request field. The module's own docstring already says this
  plainly: "The production auth stack (JWT-backed) lives in the GULA
  platform. Until NHOP shares that identity surface, routes... read the
  caller's role from the X-Role request header." `outbreak.py` and
  `doctor.py` (my two precedents for finding #9) share the exact same
  property — this was never a security boundary anywhere in this
  package, only a shape/consistency pattern.
- **Runtime proof:**
  `nhop-platform/tests/test_rbac_is_not_a_trust_boundary.py` (3 tests, all
  passing — i.e. all three vulnerable behaviors are reproducible right
  now): (1) the identical request with no authentication material at all,
  differing only in a self-declared `X-Role`, flips 403->200; (2) a
  request with zero prior auth step and a made-up `X-Role: ADMIN` header
  successfully registers a new citizen; (3) the only actually-enforced
  property is that *some* value is present (401 if it's missing) — not
  that it's true.
- **Why not fixed here:** the real fix is verifying a token against the
  GULA identity stack — `backend/app/security/auth.py` and
  `backend/app/identity/services/{authentication_service,
  authorization_service_v2,authorization_decision}.py`. Checked before
  writing this off as protected (per corrected guidance: don't assume,
  verify): `git diff --stat origin/main...origin/claude/p0-2-pharmacy-reconciliation`
  shows Abu Ali's branch is *actively editing all four of those files*
  right now (96 lines changed across them). Building nhop-platform's own
  JWT verification today means either depending on an identity surface
  that is mid-refactor elsewhere, or inventing a second one that will
  need reconciling with his the moment it merges — both are real
  conflict, not caution for its own sake. Classified **C — conflict with
  Abu Ali's active stream**, not D: the blocker isn't "needs a human
  decision," it's "the canonical mechanism to depend on is being rewritten
  under us right now."
- **What was safe to do without touching his work, and was done:** the
  module docstrings in `citizens.py` and `test_results.py` (written during
  finding #9) have been corrected — they described the `require_roles`
  gate as "implemented authorization" without qualification, which
  overstates what it provides. They now say plainly that this is a role
  gate, not verified access control, and point at the proof test and at
  the real fix's location for whoever picks this up once Abu Ali's
  identity work lands.
- **Explicitly not done, per instruction:** the pattern was not expanded
  to any further endpoint while this is unresolved.
- **Recommended fix (for whenever the identity stack settles):** nhop
  gains a dependency that verifies a bearer token against
  `backend/app/security/auth.py`'s (post-refactor) verification logic —
  either by importing it directly (if nhop and backend end up sharing a
  process/deployment boundary) or via a lightweight introspection call to
  the backend — and derives role/membership/organization/scope from the
  verified token's claims, never from a client-supplied header. Delete
  `test_rbac_is_not_a_trust_boundary.py`'s premise at that point: its
  tests are written to fail once real verification lands, by design.

## Verification (Batch 3)

```
cd nhop-platform && PYTHONPATH=<repo-root> python3 -m pytest tests/ -q
# 54 passed (was 51) — 3 new characterization tests proving the X-Role gap
```

## Batch 4 — edge_agent (zero test coverage, one startup-crash bug)

Isolation re-checked: `git diff --stat origin/main...origin/claude/p0-2-pharmacy-reconciliation -- edge_agent/` returns nothing — untouched by Abu Ali.

### 12. [FIXED] edge_agent config loader crashed on Python <3.11 (unreachable fallback)

- **File:** `edge_agent/gula_edge_agent/cli.py::_load_config`.
- **What:** the function read
  `import tomllib; with cfg_path.open("rb") as f: return tomllib.load(f)`
  followed by a second `import tomli` + `with` block that could never
  execute — the `return` above it always exits the function first.
  `edge_agent/requirements.txt` declares
  `tomli>=2.2.1; python_version < "3.11"`, meaning the agent is meant to
  run on Python <3.11 too, but `tomllib` is stdlib-only from 3.11 — on any
  older interpreter, `import tomllib` raises immediately with no
  surrounding `try/except`, so the CLI would crash on every invocation
  before ever reaching the (dead) `tomli` branch.
- **Fix:** standard `try: import tomllib / except ImportError: import
  tomli as tomllib` pattern (caught `ImportError`, not the narrower
  `ModuleNotFoundError`, since a test-simulated absence via
  `sys.modules["tomllib"] = None` raises the former).
- **Positive proof:** `test_load_config_falls_back_to_tomli_when_tomllib_is_unavailable`
  simulates the missing-tomllib case via `sys.modules` and confirms the
  file still loads correctly through the `tomli` path.
- **Negative proof:** reverted the fix locally and re-ran that one test —
  fails with the exact `ModuleNotFoundError` this fix removes (verified
  before committing).

### 13. [ADDED] edge_agent test coverage — 0 -> 22 tests

- **Files:** `edge_agent/tests/{test_state,test_security,test_agent,test_cli_config}.py` (all new — the package had no tests directory at all).
- **What's covered:** `state.py`'s encrypted-at-rest storage (round-trip,
  0600 file permissions on both the state and key files, corrupt-file
  handling, persistence across new `AgentState` instances); `security.py`'s
  keypair generation (valid 2048-bit RSA, distinct per call); and —
  highest value — `agent.py`'s own documented "Sandboxing rules enforced
  here (NOT delegated to the runtime)": unknown `kind` rejected before
  ever reaching the runtime, oversized payload rejected the same way, a
  runtime that exceeds `timeout_s` is reported failed (not left to hang),
  and the CPU/battery resource gate (`_can_take_work`) across five
  telemetry scenarios.

### 14. [FINDING ONLY — low severity, not fixed] `security.ALLOWED_KINDS` advertises 5 kinds `OllamaRuntime` cannot run

- **Files:** `edge_agent/gula_edge_agent/security.py` (`ALLOWED_KINDS`),
  `edge_agent/gula_edge_agent/runtime.py` (`OllamaRuntime.run`).
- **What:** `ALLOWED_KINDS` lists 12 task kinds; `OllamaRuntime.run()`
  only implements 7 of them (`ai.summarize_report`, `ai.translate`,
  `ai.classify`, `ai.extract_lab_values`, `ai.embed`, `diag.ping`,
  `diag.benchmark`). The other 5 — `image.thumbnail`, `pdf.extract_text`,
  `agent.self_update`, `agent.warmup_model`, `agent.gc` — fall through to
  `raise RuntimeError(f"runtime cannot handle kind={kind}")`, which
  `_execute_task`'s `except Exception` catches and reports as an ordinary
  failed task. So this is **not a security hole** (the sandbox in
  `agent.py` still gates every call, and an unimplemented kind fails
  safely, reported back to the control plane) — it's a capability
  contract mismatch: the heartbeat's `capabilities.kinds` tells the
  server the agent can do things it can't, so the server may keep
  dispatching tasks that are guaranteed to fail.
- **Why not fixed here:** the fix isn't a bug fix, it's a design decision
  — either narrow `ALLOWED_KINDS` to what's implemented, or implement the
  5 missing kinds. The last three (`agent.self_update`, `agent.gc`,
  `agent.warmup_model`) are agent-lifecycle operations, not AI-runtime
  calls — `agent.self_update` in particular is a genuinely
  security-sensitive operation (how the agent fetches/verifies/applies a
  new version) that shouldn't be designed from scratch as a side effect
  of a contract-drift fix. Flagging for whoever owns the edge agent
  roadmap rather than guessing at scope.

## Next independent work (not started yet)

- `client/`, `frontend/`, `frontend-v2/` remain unaudited and outside
  Abu Ali's current footprint — next up.
- `services/device_bridge/` concurrency: `DataPipeline.sessions[device_id]`
  (an `ASTMDeviceSession` buffer) is shared across concurrent `/ingest`
  requests for the same device_id with no lock. In practice a device has
  one physical connection at a time, so this is lower-confidence/lower
  demonstrated impact than findings #5–#7 and wasn't chased further —
  worth a concurrent-asyncio-request test if two ingest paths for the same
  device_id ever become a real scenario.
- Finding #8 (backend idempotency on `/device/results`) needs a human
  decision on the migration before implementation.
- Finding #11 (X-Role trust boundary) needs Abu Ali's identity/auth
  refactor to land before nhop-platform can verify tokens for real.
- Finding #14 (edge_agent capability/runtime mismatch) needs a product
  decision on the 5 unimplemented kinds.
