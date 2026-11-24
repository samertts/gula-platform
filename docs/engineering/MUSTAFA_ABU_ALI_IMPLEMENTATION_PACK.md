# GULA — Implementation Pack for Abu Ali (F1 / F2 / X-Role)

Engineering-preparation document, not a fix. Every claim below cites the
evidence it comes from — either a file/line this engagement read directly,
or one of the three prior artifacts (`MUSTAFA_PARALLEL_WORK_MAP.md`,
`MUSTAFA_FINAL_FORENSIC_PASS.md`, `MUSTAFA_TRUST_BOUNDARY_IMPACT_MAP.md`).
No new repository scan was run to produce this; one existence check
(`ls backend/app/routes/ | grep -iE "sample|order"`) was made to avoid
fabricating Mission 5's matrix, and its result changes that section's
scope (see §9). No source file is modified by this document.

---

## 1. Executive summary

Three prior passes established: nhop-platform has no authoritative
identity source of its own (`AUTHORITATIVE_SOURCE_NOT_PROVEN`); every
"auth" check in it terminates at a raw client-supplied header
(`X-Role`, `X-Actor-Role`, `X-Actor-Id`); and this pattern reaches five
route files and at least two persisted-attribution fields
(`TestResult.lab_id` via F2, `TestOrder.doctor_id` via the
`doctor/order-tests` extension). The real, verified mechanism
(`backend/app/security/auth.get_current_user`, JWT-backed) exists
elsewhere in the repo and is confirmed correctly gating
`backend/app/routes/device_results.py` — nhop-platform has simply never
been wired to it.

This document does not decide *how* that wiring happens — that is Abu
Ali's canonical-identity call. It packages what a fix would need to
satisfy (acceptance criteria), what would have to change and what must
not, the exact test cases (positive and negative) that already exist or
should exist once the real dependency lands, and a coverage/contract
picture of everything adjacent so nothing about scope has to be
re-discovered later.

**Nothing here is fixed. Nothing here should be treated as blocking a
release on its own timeline decision — that call belongs to whoever owns
`backend/app/security/auth.py`.**

---

## 2. F1 (P0) Implementation Pack — `notifications.py` / `X-Actor-Id`

- **Endpoint(s):** `GET /v1/notifications/`, `GET
  /v1/notifications/unread-count`, `PUT /v1/notifications/{id}/read`.
- **Route handler:** `nhop-platform/app/api/v1/notifications.py::
  {list_notifications, get_unread_count, mark_notification_read}`.
- **Dependency chain (as it exists today):**
  `request: Request` (FastAPI-injected, no dependency) →
  `_require_user_id(request)` (plain function call, not a `Depends`) →
  `request.headers.get("X-Actor-Id")` → returned verbatim as `user_id`.
  There is no `Depends(...)` in the signature that touches identity at
  all — `db: Session = Depends(get_db)` is the *only* FastAPI dependency
  present, and `get_db` has zero identity logic
  (`nhop-platform/app/core/database.py`).
- **Call graph:**
  `route → _require_user_id → services/notification.py::{list_for_user,
  unread_count, mark_read} → SQLAlchemy query filtered by
  Notification.recipient_id == user_id → Postgres/SQLite`.
- **Current identity source:** the `X-Actor-Id` HTTP header, read once,
  trusted for the remainder of the request.
- **Current authorization source:** none — there is no role or
  permission check anywhere in this file (contrast with every other
  nhop-platform route, all of which have *some* gate).
- **Required trusted context:** a verified caller identity (whatever
  Abu Ali's canonical mechanism resolves to — e.g. a validated JWT
  subject) that the route can use in place of the header, with no other
  change to the query shape.
- **Exact trust-boundary failure:** `_require_user_id` accepts
  attacker-supplied input as if it were an authentication result. The
  SQL-level scoping (`recipient_id == user_id`) is correct; the input
  feeding it is not authenticated.
- **Expected secure invariant:** *"A caller can only ever be evaluated as
  the identity a trusted authentication step assigned them — never an
  identity they asserted in a header."* This must hold for all three
  routes identically.
- **Positive test cases (already exist, unmodified, still passing):**
  `nhop-platform/tests/test_notifications_actor_id_is_not_a_trust_boundary.py`
  currently encodes the *vulnerable* behavior as its positive assertions
  (by design — see §7's "flip, don't delete" plan). Concretely:
  1. A caller presenting `X-Actor-Id: HID-VICTIM` sees exactly that
     recipient's notifications.
  2. A different value sees a disjoint set (proves the SQL scoping
     itself is sound and worth keeping).
  3. A caller can mark another party's notification read given only that
     party's id.
- **Negative test cases (do not yet exist — described, not written, per
  "no speculative implementation binding to Abu Ali's changing auth
  API"):**
  1. A request with no valid session/token at all → `401`, and **no**
     query is ever issued (verify via a spy/mock on the DB session, not
     just the HTTP status, so a "200 with empty results" regression
     can't masquerade as a pass).
  2. A request with a *valid* session for user A, attempting to read
     user B's notifications by any means (header, query param, path — once
     the real mechanism lands, there should be no field left that can
     override the session's own identity) → `403` or the resource is
     simply not in the result set, never a data leak.
  3. A request with an expired/revoked session → `401`, not silently
     treated as anonymous or as a stale-but-valid identity.
- **Runtime verification plan:** once the real dependency exists, run
  the existing 3-test file with its assertions flipped (see §7) against
  it; all three must go from "pass because vulnerable" to "pass because
  rejected." Do this *before* declaring the fix complete — a green suite
  with the old assertions proves nothing.
- **Regression test plan:** keep the flipped file permanently in
  `nhop-platform/tests/` as the standing regression guard; do not delete
  it once it starts passing for the right reason.
- **Dependencies on Abu Ali:** total — there is no independent fix.
  `backend/app/security/auth.py` and the identity services
  (`authentication_service.py`, `authorization_service_v2.py`,
  `authorization_decision.py` — all confirmed in his active diff in a
  prior pass) are the canonical mechanism this must eventually depend on.
- **Files expected to change (when this is fixed, not now):**
  `nhop-platform/app/api/v1/notifications.py` (replace
  `_require_user_id` with the real dependency);
  possibly a new `nhop-platform/app/core/auth.py` or equivalent adapter,
  depending on how Abu Ali's mechanism is meant to be consumed
  cross-service — **that shape is his call, not proposed here.**
- **Files that MUST NOT be changed by this pack or its eventual fix
  without separate sign-off:** `backend/app/security/auth.py`,
  `backend/app/identity/services/*` (Abu Ali's active work — do not
  modify to "help" this fix land), `.github/workflows/*`.

---

## 3. F2 (P1) Implementation Pack — `test_results.py` / `payload.lab_id`

- **Endpoint:** `POST /v1/test-results/`.
- **Route handler:** `nhop-platform/app/api/v1/test_results.py::
  create_test_result`.
- **Dependency chain (as it exists today):** `role: str =
  Depends(_lab_staff)` → `_lab_staff = require_roles(Role.LAB,
  Role.ADMIN)` (`nhop-platform/app/core/rbac.py`) → reads `X-Role`
  header, checks set membership only. **Separately**, `payload.lab_id`
  (request body, `TestResultCreate.lab_id: UUID`) is read with **no
  dependency at all** — it goes straight from the validated Pydantic
  model into a query.
- **Call graph:**
  `route → require_roles._dep (role check only) → db.query(Lab).filter(
  Lab.id == payload.lab_id) (existence + is_active check only) →
  TestResult(lab_id=payload.lab_id, ...) → db.add/commit →
  _recompute_lab_metrics(db, lab, tat_minutes) (writes back into the
  SAME selected lab's own counters) → log_action(metadata={"lab_id":
  str(lab.id), ...})`.
- **Current identity source:** `X-Role` header (role only — no
  per-caller lab affiliation is captured anywhere upstream).
- **Current authorization source:** role-name allow-list membership;
  **no object-level check** that the caller is affiliated with
  `payload.lab_id` at all.
- **Required trusted context:** a verified caller identity that also
  carries (or can be resolved to) the set of lab(s) that caller is
  actually affiliated with, so `payload.lab_id` can be checked against
  it rather than trusted outright.
- **Exact trust-boundary failure:** the request body itself is treated
  as establishing authority over a third-party resource (`Lab`), rather
  than the resource ownership being derived from the caller's own
  verified context.
- **Expected secure invariant:** *"`lab_id` on a written `TestResult` must
  be a lab the authenticated caller is verified to belong to — never a
  value the caller merely names."*
- **Positive test cases (exist, unmodified):**
  `nhop-platform/tests/test_results_lab_id_is_not_ownership_checked.py`
  — a caller with the `_lab_staff` role successfully attributes a result
  to a lab it declares no relationship with. This is the vulnerable
  behavior, kept as-is until the fix lands (see §7).
- **Negative test cases (described, not written):**
  1. A caller verified as affiliated with Lab A submits a result with
     `lab_id = Lab B's id` → rejected (403 or 422, Abu Ali's convention
     to pick), and no `TestResult` row is created for Lab B.
  2. A caller with no lab affiliation at all (e.g. a `MINISTRY` or
     `ADMIN`-only identity, if such an identity is meant to be able to
     submit results at all — **policy question, not decided here**) —
     behavior needs an explicit decision, not an assumption.
  3. A caller affiliated with Lab A submitting `lab_id = Lab A's own id`
     → succeeds unchanged (this must keep working — it's the correct
     case, not a regression target).
- **Runtime verification plan:** flip
  `test_results_lab_id_is_not_ownership_checked.py`'s assertion once the
  real ownership check exists; confirm it fails against current
  `main`/this branch first (proving it would have caught the gap), then
  passes against the fix.
- **Regression test plan:** keep the flipped test permanently; add case
  3 above (the "own lab, still works" happy path) alongside it so a
  future over-broad fix that blocks *legitimate* same-lab submissions is
  also caught.
- **Dependencies on Abu Ali:** total, same mechanism as F1, plus one
  additional design question that's specifically his: what "a caller's
  own lab(s)" resolves to in the canonical identity model (one lab per
  user? many? via a membership table?) — **not something this pack
  proposes an answer to.**
- **Files expected to change (when fixed):**
  `nhop-platform/app/api/v1/test_results.py::create_test_result`
  (add the ownership check once the trusted-context shape exists).
- **Files that MUST NOT be changed:** same list as §2.

---

## 4. X-Role trust boundary (existing finding, contextualized)

- **Location:** `nhop-platform/app/core/rbac.py::require_roles`.
- **Relationship to F1/F2:** F2's `_lab_staff` gate *is* an instance of
  this mechanism; F1 has no gate of any kind, which is a **stronger**
  defect (missing vs. present-but-unauthenticated), not a variant of the
  same severity.
- **Already proven:**
  `nhop-platform/tests/test_rbac_is_not_a_trust_boundary.py` (3 tests,
  unmodified, still passing) — an identical request differing only in a
  self-declared `X-Role` value flips `403 → 200`; a request with no prior
  authentication step at all can register a citizen by claiming `ADMIN`.
- **Fix location, when it happens:** `require_roles`'s inner `_dep`
  would derive `role` from the same trusted context as F1/F2's fix,
  rather than `Header(alias="X-Role")`. **This pack does not propose
  that implementation** — it is the same canonical-identity dependency,
  applied a third time.

---

## 5. `doctor/order-tests` extensions (new evidence from the prior pass, not a new severity class)

- **Endpoint:** `POST /doctor/order-tests`.
- **Route handler:** `nhop-platform/app/api/v1/doctor.py::order_tests`.
- **Dependency chain:** `_require_doctor(request)` — an **in-body
  function call**, not a `Depends(...)` parameter — reads `X-Actor-Role`
  (must equal `DOCTOR`) and `X-Actor-Id` (returned as `doctor_id`, no
  verification of either).
- **Two distinct sub-findings, both already documented, neither new
  severity:**
  1. **F1-shaped:** `doctor_id` (the unverified `X-Actor-Id`) is written
     directly into `TestOrder.doctor_id` (`doctor.py:171` area) —
     persisted attribution from an unverified source, same shape as
     notifications.py's identity trust, on the write side instead of the
     read side.
  2. **F2-shaped:** `payload.preferred_lab_id` (request body) selects
     which `Lab` a new order is dispatched to, checked only for
     existence/`is_active`, no caller↔lab affiliation check
     (`doctor.py:160-166`).
- **Why this matters for Abu Ali's planning, not as new work:** any fix
  to F1/F2's shared root cause should be designed to cover this file too
  — a fix scoped only to `notifications.py` and `test_results.py` would
  leave two structurally identical gaps in `doctor.py` unaddressed.
- **Detection note:** `_require_doctor` is an **in-body call**, not a
  signature-visible `Depends(...)`. A naive "does the route have an auth
  dependency in its signature" check would incorrectly treat `doctor.py`
  as *worse* than `notifications.py` (both would show zero
  signature-level dependencies), when in fact `doctor.py` has *a* gate
  (weak) and `notifications.py` has *none*. Any tooling built to verify
  this fix's coverage must account for in-body checks, not just
  signatures.
- **Test status:** no new test added for this (per the prior pass's
  own note — `test_doctor_api.py`'s existing suite already proves
  `order_tests` is reachable and functional; that's sufficient
  reachability evidence without duplicating it). Negative/ownership
  tests for `doctor_id`/`preferred_lab_id` are described, not written,
  same rationale as §2/§3.

---

## 6. Authorization coverage map

`UNKNOWN` is used verbatim wherever this pack cannot establish a value
from evidence already gathered — never upgraded to a pass.

| Endpoint | Authentication | Identity source | Role source | Org source | Lab source | Object ownership | Tenant predicate | Audit | Status |
|---|---|---|---|---|---|---|---|---|---|
| `POST /v1/citizens/register` | CLIENT_CONTROLLED | `X-Actor-Id` | `X-Role` | UNKNOWN (no org concept in nhop-platform) | N/A | N/A (creates new resource) | N/A (national registry, correct by construction) | VERIFIED (actor field unverified) | CLIENT_CONTROLLED |
| `GET /v1/citizens/{search,id,summary}` | CLIENT_CONTROLLED | `X-Actor-Id` | `X-Role` | N/A | N/A | N/A (correct by construction) | N/A | VERIFIED | CLIENT_CONTROLLED |
| `PUT /v1/citizens/{id}` | CLIENT_CONTROLLED | `X-Actor-Id` | `X-Role` | N/A | N/A | VERIFIED (immutable fields rejected via `extra="forbid"`) | N/A | VERIFIED | CLIENT_CONTROLLED |
| `POST /v1/test-results/` | CLIENT_CONTROLLED | `X-Actor-Id` | `X-Role` | N/A | `payload.lab_id`, **unchecked** | **MISSING** | N/A | VERIFIED (audit records the unverified `lab_id` as fact) | **F2** |
| `PUT /v1/test-results/{id}/verify` | CLIENT_CONTROLLED | `X-Actor-Id` | `X-Role` | N/A | N/A (path-scoped) | N/A (status-machine guard, not lab-scoped by design) | N/A | VERIFIED | CLIENT_CONTROLLED |
| `GET /v1/test-results/*` (reads) | CLIENT_CONTROLLED | `X-Actor-Id` | `X-Role` | N/A | N/A | N/A (cross-lab read, correct by construction) | N/A | VERIFIED | CLIENT_CONTROLLED |
| `GET/PUT /v1/notifications/*` | **MISSING** | `X-Actor-Id`, unverified | **MISSING** | N/A | N/A | **MISSING** (SQL filter real, input feeding it is not) | N/A | VERIFIED (actor field unverified) | **F1** |
| `POST /doctor/order-tests` | CLIENT_CONTROLLED | `X-Actor-Id` (also persisted as `doctor_id`) | `X-Actor-Role` (in-body check) | N/A | `payload.preferred_lab_id`, **unchecked** | **MISSING** | N/A | VERIFIED (actor field unverified) | **New evidence, same class as F1+F2** |
| `POST /doctor/refer` | CLIENT_CONTROLLED | `X-Actor-Id` | `X-Actor-Role` | N/A | N/A (references existing citizen only) | N/A | N/A | VERIFIED | CLIENT_CONTROLLED |
| `GET /doctor/patient/{id}/*` | CLIENT_CONTROLLED | `X-Actor-Id` | `X-Actor-Role` | N/A | N/A | N/A (cross-lab read by design) | N/A | VERIFIED | CLIENT_CONTROLLED |
| `GET /v1/outbreak/*` | CLIENT_CONTROLLED | `X-Actor-Id` | `X-Role` (`_ministry_or_admin`) | N/A | N/A | N/A (aggregate, ministry-level by design) | N/A | VERIFIED | CLIENT_CONTROLLED |

`backend/app/routes/device_results.py` (read-only reference, outside
nhop-platform, not owned by this engagement) is included for contrast
only: **VERIFIED** authentication (`Depends(get_current_user)`) and
**VERIFIED** tenant predicate (`LabOrder.lab_id ==
current_user.lab_id`) — proving the canonical pattern already exists and
works correctly elsewhere in the repo; nhop-platform has simply never
been connected to it.

---

## 7. Security test matrix

Per the explicit instruction, tests below are **specified, not
implemented**, wherever they would bind to Abu Ali's not-yet-landed auth
API. Rows marked "EXISTS" are already in the repository, unmodified.

| Scenario | Setup | Request | Expected authz result | Expected data effect | Expected audit effect | Status |
|---|---|---|---|---|---|---|
| Cross-user (notifications) | Two notifications, different `recipient_id` | `GET /v1/notifications/` with `X-Actor-Id` = one of the two | Should reject unless the header *is* the trusted identity | Currently: returns that recipient's data. Should: 401 without a real session | Currently: none. Should: no query issued pre-auth | **EXISTS** (proves current vulnerable behavior) |
| Cross-lab (test-results) | Two labs, caller has no declared affiliation with either | `POST /v1/test-results/` with `lab_id` = a lab the caller isn't affiliated with | Currently: succeeds. Should: reject | Currently: `TestResult` row created under wrong lab. Should: no row created | Currently: audit records the wrong lab as fact. Should: audit records a rejected attempt | **EXISTS** (proof test) for the vulnerable case; rejected case SPECIFIED only |
| Spoofed actor | none | Any nhop-platform mutating/reading route with an arbitrary `X-Actor-Id` | Currently: accepted. Should: 401 without real credential | See per-endpoint rows above | Actor field in audit is exactly the spoofed value either way, until fixed | **EXISTS** across F1/F2/`X-Role` proof files |
| Spoofed role | none | `X-Role: ADMIN` (or `X-Actor-Role: DOCTOR`) with no other credential | Currently: accepted. Should: 401/403 without real credential | Full write/read access currently granted | n/a | **EXISTS** (`test_rbac_is_not_a_trust_boundary.py`) |
| Spoofed lab | Lab A and Lab B both exist and are active | `payload.lab_id` = Lab B while caller (once real auth exists) is only affiliated with Lab A | Should reject | Should: no row/attribution change | Should: audit records rejection, not the spoofed lab as fact | SPECIFIED only — requires the real dependency to express "caller's own lab(s)" |
| Missing session | none | Any protected route, no `X-Actor-Id`/`X-Role` at all | 401 today (the one thing these mechanisms DO enforce — *some* value must be present) | No data returned | No mutation performed | **EXISTS** (`test_register_requires_a_role`, `test_create_result_requires_a_role`, `test_missing_x_actor_id_is_the_only_thing_actually_enforced`, per prior batches) |
| Expired session | N/A — nhop-platform has no session/token concept at all today, so "expiry" cannot be expressed or tested against current code | — | — | — | — | **UNKNOWN / NOT APPLICABLE YET** — cannot be specified further until a session/token with an expiry claim exists |
| Revoked membership | N/A — no membership model exists in nhop-platform (confirmed: no `organization_id`/`facility_id`/membership table anywhere in `nhop-platform/app/models`) | — | — | — | — | **UNKNOWN / NOT APPLICABLE YET** |
| Inactive organization/lab | `Lab.is_active = False` | `POST /v1/test-results/` with an inactive lab's id | 400 today (`"lab is not active"`) | No row created | No mutation, so no misleading audit entry | **EXISTS** (`test_create_result_requires_active_lab`) — this one control already works correctly and should not regress |

---

## 8. CI enforcement specification (F4 — documentation only, no workflow file touched)

- **Affected services:** `nhop-platform/`, `services/device_bridge/`,
  `edge_agent/`. (`server/` is Node/vitest, tracked separately below —
  it is also uncovered by root `npm test`, per the prior forensic pass,
  but is not a Python `pytest` gap.)
- **Test locations:** `nhop-platform/tests/`, `services/device_bridge/tests/`,
  `edge_agent/tests/`, `server/tests/` (vitest, own scoped config).
- **Required commands** (each already verified working, this engagement):
  - `cd nhop-platform && PYTHONPATH=<repo-root> python -m pytest tests/ -q`
  - `PYTHONPATH=<repo-root> python -m pytest services/device_bridge/tests/ -q`
  - `PYTHONPATH=<repo-root>:<repo-root>/edge_agent python -m pytest edge_agent/tests/ -q`
  - `cd server && npx vitest run` (uses `server/vitest.config.ts`, added
    this engagement specifically because the repo-root `vite.config.ts`'s
    `root: "client"` would otherwise hide it)
- **Dependencies:** `nhop-platform`/`device_bridge`/`edge_agent` each need
  `fastapi`, `sqlalchemy`, `pydantic[email]`, `httpx`, `pytest`,
  `pytest-asyncio`; `edge_agent` additionally needs `cryptography`,
  `psutil`, and (for Python <3.11 parity) `tomli`. None of these are
  currently installed by any CI job for these paths.
- **Environment assumptions:** all four suites run against in-memory
  SQLite or in-process fakes — **no Postgres/Redis service container is
  required** for any of them (unlike the existing `backend` `test` job,
  which provisions both). This makes them cheap to add.
- **Current CI coverage:** exactly one Python-syntax `compile()` check
  over `services/`, `nhop-platform/`, `edge_agent/` in the `syntax-gate`
  job (`.github/workflows/ci.yml`, "Check service Python syntax" step) —
  no import walk, no test execution. The only `pytest` invocations in the
  entire workflow are under `cd backend`.
- **Missing CI coverage:** test *execution* for all three Python
  services and for `server/`'s vitest suite — confirmed via direct
  inspection (`grep -n "pytest" .github/workflows/ci.yml` → two hits,
  both under `backend`; `grep -n "nhop\|device_bridge\|edge_agent"
  Makefile` → no output).
- **Path-filter risks:** none observed *specific to a filter excluding
  these paths* — the simpler, more basic issue is that no job targets
  them at all, so there is no filter to misconfigure yet. If a job is
  added, standard risk applies: scope it to `push`/`pull_request` on
  paths touching these directories (or run unconditionally, given how
  cheap the suites are) rather than accidentally gating it behind an
  unrelated label/branch filter.
- **Expected CI jobs (specification only — not implemented, per explicit
  instruction not to touch `.github/workflows/`):** one job (or one
  step per service in an existing job) per the four `pytest`/`vitest`
  invocations above, each with no service containers, each fast (all
  four together ran in under 20 seconds locally this engagement).

---

## 9. Idempotency matrix

**Scope note, evidence-derived rather than assumed:** Mission 5 named
`POST /samples`, a "batch order path", and `POST /orders` as targets.
This pack's own quick existence check found `backend/app/routes/
samples.py` and `clinical_orders.py` do exist in `backend/app/routes/`
— but **neither was read or examined at any point during this
engagement**, and the same check surfaced a commit on Abu Ali's own
branch, `f5e6edb3` — *"feat(idempotency): one canonical claim, and the
two clinical writes that lacked it"* — indicating idempotency work in
this exact area is **already active on his stream**. Per this pack's
"using already discovered evidence only" and "do not decide policy"
instructions, those two files are recorded as **NOT EXAMINED / ACTIVE ON
ABU ALI'S STREAM** rather than populated from speculation. The matrix
below covers only mutation endpoints this engagement actually traced.

| Operation | Retry behavior | Idempotency mechanism | Key source | Tenant scope | Persistence | Uniqueness | Concurrency | Offline replay | Duplicate consequence |
|---|---|---|---|---|---|---|---|---|---|
| `POST /v1/citizens/register` | none — a retried POST after a timeout can create a near-duplicate if the fuzzy-match score lands under threshold | App-level fuzzy dup detection (`services/duplicates.py`, Jaro-Winkler) + exact `national_id` conflict check | none (no client-supplied idempotency key) | N/A (national registry) | Postgres via SQLAlchemy | `national_id` not unique at DB level — pre-insert query only (TOCTOU-able) | **DEFERRED** — not measured under real concurrent load; would need a concurrent-Postgres harness this engagement didn't have | N/A (online-only endpoint) | A near-duplicate citizen record, manually reconcilable via the existing duplicate-detection UI path |
| `POST /v1/test-results/` | none | none | none | `payload.lab_id` (see F2 — itself unverified) | Postgres | none on (citizen, lab, test_code, performed_at) | not tested this engagement | N/A | A second, indistinguishable `TestResult` row on retry/resubmission |
| `PUT /v1/test-results/{id}/verify` | safe — retried verify after success gets `409`, not a silent double-effect | Status-machine guard (`if row.status == verified: 409`) | path param | N/A | Postgres | implicit via `status` field | VERIFIED SAFE | N/A | None — retry is a clean no-op |
| `PUT /v1/notifications/{id}/read` | safe | `is_read` flag check before mutating | path param + spoofable `X-Actor-Id` (F1) | `recipient_id` (see F1) | Postgres | implicit via `is_read` | VERIFIED SAFE for idempotency specifically — authorization is F1's separate defect | N/A | None — retry is a clean no-op |
| device_bridge `process_chunk → gula_client.send_results` | fixed this engagement: `retry_queue.content_key()` (sha256 over device_id+patient_id+test_code+value+timestamp) dedupes device_bridge's own re-staging | content-hash key, local to device_bridge only, **never sent to the backend** | derived from parsed device data | none (in-memory only, lost on restart) | none (in-memory) | dict keyed by content hash in `sync_engine` | fixed this engagement | fixed this engagement (`/edge/sync` now performs a real resend instead of a fake no-op success) | Pre-fix: silent data loss reported as success. Post-fix: genuine retry or genuine, visible failure |
| `backend/app/routes/device_results.py::POST /device/results` (read-only reference, not owned) | none | none | none | `current_user.lab_id` (trusted — real dependency) | Postgres | none | not tested (not owned) | N/A | Duplicate `LabResult` rows on a retried/duplicated submission — already documented (main work map finding #8); canonical mechanism to reuse (`backend/app/integration/inbox.py`'s `idempotency_key` pattern) already exists in the repo, not reused here yet |
| `POST /samples`, batch order path, `POST /orders` | **NOT EXAMINED THIS ENGAGEMENT** | **NOT EXAMINED** | **NOT EXAMINED** | **NOT EXAMINED** | **NOT EXAMINED** | **NOT EXAMINED** | **NOT EXAMINED** | **NOT EXAMINED** | **NOT EXAMINED — flag for Abu Ali directly: his own branch has an in-flight idempotency commit touching "two clinical writes" in this area; do not duplicate that work from this pack's evidence, which doesn't include having read these files** |

No new idempotency framework is proposed anywhere in this table, and no
policy (e.g. "should a duplicate result overwrite or append") is decided.

---

## 10. Service contract maps

| | device_bridge → GULA | edge_agent → backend | client → server |
|---|---|---|---|
| **Producer** | `services/device_bridge/app/integration/gula_client.py::GulaClient.send_results` | `edge_agent/gula_edge_agent/agent.py::EdgeAgent._post` | `client/src/App.tsx`'s three `fetch()` calls |
| **Consumer** | `backend/app/routes/device_results.py::POST /device/results` | `backend/app/routes/edge.py::POST /edge/agent/heartbeat`, `POST /edge/agent/tasks/{uid}/result`, `POST /edge/devices/register` | `server/index.ts`'s `/api/v1/demo/{status,session,dashboard}` routes |
| **Schema** | `DeviceSubmission {barcode, device_id, results: [{test_name, value, unit, ...}]}` — fixed this engagement to match the backend's actual contract (previously sent `{lab_id, results: [{patient_id, test_code, ...}]}`, a total mismatch) | Path-level match confirmed (three paths on both sides); full field-level schema **not** re-verified this engagement | Matches exactly (`server/tests/demoSession.test.ts` covers it) |
| **Required fields** | `barcode` (must be present or the client now fails fast locally rather than sending a guaranteed-422 request) | Not exhaustively re-verified | `gula_demo` signed cookie for `/dashboard` and `DELETE /session` |
| **Optional fields** | `value_text`, `normal_range_low/high` (backend accepts them; device_bridge doesn't currently populate them — `NormalizedResult` has no distinct low/high fields, only a single unparsed `reference_range` string) | Not exhaustively re-verified | none beyond the cookie |
| **Authentication metadata** | Backend requires `Depends(get_current_user)` (JWT bearer). device_bridge has an optional `auth_token`/`GULA_DEVICE_BEARER_TOKEN` pass-through hook added this engagement, but **no actual credential issuance** — that depends on the machine/device-identity work also active on Abu Ali's stream (`backend/app/identity/repositories/device_repository.py`, `machine_identity_attestation_columns` migration, both seen in his diff in a prior pass) | Real per-device bearer token (`agent_token`), issued at registration, stored encrypted at rest (`state.py`) — **this arrow is the one place in this pack with genuine, verified, non-spoofable authentication** | Signed, `httpOnly`, `sameSite=strict`, HMAC-verified cookie; **not** a header-based identity claim — a materially different (and sound, per manual review) mechanism from nhop-platform's |
| **Tenant context** | Backend derives `lab_id` from `current_user`, not from the request body (correct) | Not exhaustively re-verified | N/A — demo mode is explicitly non-clinical, no tenant concept |
| **Error semantics** | Backend: `404`/`400`/`422` per-field; device_bridge treats any non-2xx as `{"status": "failed", ...}` and queues for retry (fixed this engagement — previously the retry path silently discarded data on "success") | Not exhaustively re-verified | `401` on invalid/missing/expired/revoked demo session; rate-limited `429` on excessive session creation |
| **Retry semantics** | Fixed this engagement (see §9's device_bridge row) | `EdgeAgent`'s own heartbeat loop retries naturally (stateless per-tick) | N/A — demo sessions are short-lived by design, not retried |
| **Idempotency** | See §9 | Not examined this engagement | N/A (see §9's notifications/verify row pattern — demo session creation is intentionally *not* idempotent, confirmed by design intent in the prior forensic pass) |
| **PII** | `patient_id`/health values cross this boundary; auth is the open question above, not encryption-in-transit (assumed HTTPS at deployment, not verified here) | Telemetry (CPU/battery/task results) — no clinical PII by design (`NoopRuntime`/`OllamaRuntime` handle only lab-report text the caller supplies) | None — demo data is entirely synthetic, explicitly labeled as such in the UI |
| **Version compatibility** | Not versioned — a future backend contract change would silently break device_bridge again the way this engagement found it already broken, unless a contract test is added (not done — would require importing backend's Pydantic models, which pulls in its full config/secrets stack; noted as a gap, not fixed) | Not examined | N/A (single-process, same deploy) |

---

## 11. Dependencies / Blockers

- **F1, F2, X-Role, and the `doctor.py` extensions all block on the same
  thing:** a canonical, verified identity/session mechanism reachable
  from `nhop-platform`, which is Abu Ali's active work
  (`backend/app/security/auth.py` + identity services). No independent
  fix exists.
- **F2 additionally blocks on a design decision** only Abu Ali (or
  whoever owns the identity model) can make: what "a caller's own
  lab(s)" resolves to — one lab per user, many, via a membership table,
  etc.
- **F4 blocks on human approval** for `.github/workflows/ci.yml`
  changes, per `CLAUDE.md`'s own task boundaries — not an Abu Ali
  dependency specifically, but a human-approval gate regardless of who
  picks it up.
- **§9's `POST /samples`/orders row blocks on avoiding duplicate work** —
  Abu Ali's branch already has an in-flight idempotency commit in this
  area; this pack deliberately did not investigate further to avoid
  colliding with it.

---

## 12. Exact acceptance criteria

For F1 (`notifications.py`):
1. Every one of the three routes rejects a request lacking a real,
   verified session/credential with `401`, **before** any database query
   runs.
2. No request field (header, query param, or body) can select a
   different identity than the one the verified session/credential
   establishes.
3. `test_notifications_actor_id_is_not_a_trust_boundary.py`'s three
   assertions are flipped to expect rejection and pass against the fix.
4. The existing SQL-level scoping (`recipient_id == user_id`) is
   preserved — the fix replaces *what feeds* `user_id`, not the query
   shape.

For F2 (`test_results.py`):
1. `create_test_result` rejects a `lab_id` the verified caller is not
   affiliated with.
2. A verified caller submitting their own lab's `id` continues to
   succeed unchanged (no regression on the legitimate path).
3. `test_results_lab_id_is_not_ownership_checked.py`'s assertion is
   flipped to expect rejection for an unaffiliated lab, plus a new
   passing case for the affiliated-lab path, both passing against the
   fix.
4. Audit log entries for `create_test_result` continue to fire on every
   call, success or rejection, so a rejected attempt is still visible
   in the trail (currently only successes are logged — worth deciding
   explicitly when this lands, not decided here).

For X-Role and `doctor.py` (§4/§5): same shape as F1/F2, applied to
`require_roles` and `_require_doctor` respectively, using whatever single
canonical dependency F1/F2 land on — **not three separate
reimplementations.**

---

## 13. Files expected to change (once the canonical mechanism lands — not now)

- `nhop-platform/app/api/v1/notifications.py`
- `nhop-platform/app/api/v1/test_results.py`
- `nhop-platform/app/api/v1/doctor.py`
- `nhop-platform/app/core/rbac.py`
- Possibly a new `nhop-platform/app/core/auth.py` (or equivalent) —
  shape not proposed here
- `nhop-platform/tests/test_rbac_is_not_a_trust_boundary.py`,
  `test_notifications_actor_id_is_not_a_trust_boundary.py`,
  `test_results_lab_id_is_not_ownership_checked.py` (assertions flipped,
  not deleted)

## 14. Files protected from change (by this pack, and recommended to stay untouched by any fix landing without separate review)

- `backend/app/security/auth.py`
- `backend/app/identity/services/*`
- `.github/workflows/*`
- `backend/migrations/versions/*` (no migration is implied by anything
  in this pack)
- `backend/app/routes/samples.py`, `backend/app/routes/clinical_orders.py`
  (not examined this engagement; active on Abu Ali's own stream per
  §9 — leave to him)
- Abu Ali's branch, `claude/p0-2-pharmacy-reconciliation`, in its
  entirety — not read for modification purposes at any point in this
  engagement, only inspected via `git diff --stat`/`git log` for
  isolation checks
