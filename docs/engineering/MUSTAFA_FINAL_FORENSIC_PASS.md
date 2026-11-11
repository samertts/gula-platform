# GULA — Mustafa Final Cross-Cutting Forensic Pass

Scope: independently reachable code touched or discovered during this
engagement (`nhop-platform/`, `services/device_bridge/`, `edge_agent/`,
`client/`, `server/`, plus read-only references into
`backend/app/routes/device_results.py` and `backend/app/routes/edge.py`).
No broad new exploration, no product decisions, no changes to Abu Ali's
identity/auth work. Branch: `claude/mustafa-parallel-engineering`.

---

## 1. Trust boundaries — findings

### F1 — P0 — `notifications.py`: `X-Actor-Id` directly grants data access, zero role gate

- **Location:** `nhop-platform/app/api/v1/notifications.py` (all 3 routes),
  backed by `nhop-platform/app/services/notification.py`.
- **Reachability:** live — router registered in `api/v1/__init__.py` since
  before this engagement began.
- **Observed behavior:** `_require_user_id()` returns
  `request.headers.get("X-Actor-Id")` verbatim as an authenticated
  `user_id`, with no session/token verification at all — not even the
  weak `X-Role` gate that `citizens.py`/`test_results.py` now have.
  `services/notification.py` correctly filters every query by
  `recipient_id == user_id` — the SQL-level scoping is real — but nothing
  verifies the caller *is* that `user_id`.
- **Minimal reproduction:** `GET /v1/notifications/` with
  `X-Actor-Id: <any string>` returns exactly that recipient's
  notifications; a different header value returns different (or no)
  data — proven in
  `nhop-platform/tests/test_notifications_actor_id_is_not_a_trust_boundary.py`
  (3 tests, all passing, i.e. all three exploitable behaviors are live
  right now).
- **Security/data-integrity impact:** direct PHI/PII exposure and
  tampering. `test_results.py::_fire_critical_alert` sends citizens their
  own critical-result alerts with `recipient_id=citizen.health_id` — and
  `health_id` is exactly what `citizens.py`'s own `/search` and
  `/{health_id}` endpoints return, i.e. a non-secret, discoverable
  identifier. Anyone who can search the registry (or is handed a health
  card) can read that citizen's critical-result notification content
  (test code, value, direction) and silently mark it read — suppressing a
  clinical alert before the real recipient ever sees it — with no
  authentication step at all.
- **Existing control:** none (no role check, no session, no token).
- **Why insufficient:** there is no control to evaluate — the identity
  input itself is unauthenticated.
- **Recommended owner:** whoever lands the identity/session stack in
  nhop-platform (same owner as finding #11 in the main work map).
- **Dependency on Abu Ali:** yes — same root cause and same blocker as
  the already-documented `X-Role` finding: `backend/app/security/auth.py`
  + the identity services are actively being rewritten by his stream
  right now. Fixing this for real means depending on that work, not
  building a second identity mechanism ahead of it.
- **Disposition: COORDINATION.** Not fixed (would require inventing a
  competing partial-auth mechanism, explicitly out of scope this pass).
  Proven and documented only.

### F2 — P1 — `test_results.py::create_test_result`: `lab_id` is client-supplied with no ownership check (BOLA/IDOR)

- **Location:** `nhop-platform/app/api/v1/test_results.py:204`.
- **Reachability:** live, behind the (already-known-unsafe) `_lab_staff`
  role gate.
- **Observed behavior:** `payload.lab_id` (from the request body) is used
  directly to select which `Lab` authored the result — no check that the
  caller is affiliated with that lab.
- **Minimal reproduction:**
  `nhop-platform/tests/test_results_lab_id_is_not_ownership_checked.py`
  — a caller successfully attributes a result to a lab it has no
  declared relationship with.
- **Security/data-integrity impact:** misattribution of clinical results
  to the wrong lab; undermines lab-level accountability for a result's
  provenance. Lower severity than F1 (requires clearing the role gate
  first; doesn't expose another party's private data directly), but a
  genuine object-level authorization gap independent of the role-header
  question.
- **Existing control:** `_lab_staff` role gate (already proven
  spoofable) + "lab must exist and be active" — neither checks caller-lab
  affiliation.
- **Why insufficient:** same missing-identity root cause as F1 — there is
  no trusted per-caller lab_id to check `payload.lab_id` against.
- **Recommended owner:** same as F1/finding #11.
- **Dependency on Abu Ali:** yes, same blocker.
- **Disposition: COORDINATION.** Proven, documented, not fixed.

### F3 — P3 (cosmetic/consistency, not security-blocking) — two incompatible role-header schemes coexist in nhop-platform

- **Location:** `doctor.py` uses its own `X-Actor-Role` /
  `_require_doctor`; `citizens.py`/`test_results.py`/`outbreak.py` use
  `core.rbac.require_roles` / `X-Role`.
- **Observed behavior:** a caller must know which of two different header
  names applies to which endpoint in the same service — no security
  impact beyond what F1/F2/finding #11 already cover (both schemes are
  equally unauthenticated), but it's an inconsistency between sibling
  endpoints worth a single line so nobody designs a "fix" around only one
  of the two names.
- **Disposition: FALSE POSITIVE as a *security* finding** (no additional
  exposure beyond what's already documented) — **noted as a minor
  contract-consistency observation only.**

### Audit-identity note (ties to §5 below)

`_actor_id(request) = request.headers.get("X-Actor-Id")` is used as the
audit-log `actor_id` in **all five** nhop-platform route files
(`citizens.py`, `test_results.py`, `doctor.py`, `outbreak.py`,
`notifications.py`). Every audit entry's recorded actor is exactly as
forgeable as F1's access-control identity — see §5.

---

## 2. Tenant / organization isolation

- **`Citizen` (citizens.py):** no lab_id/tenant column at all —
  **correct by construction.** NHOP is deliberately the *national*,
  cross-lab registry (CLAUDE.md: "GULA owns the per-lab LIMS view; NHOP
  owns the national citizen registry" — independently confirmed in the
  previous batch via `nhop_lab_code`/`nhop_code`/`trust_domain.py`
  evidence). Not a defect.
- **`TestResult` reads (`list_citizen_results`, `citizen_timeline`):**
  filtered by `citizen_id` only, not `lab_id` — **correct by
  construction** for the same reason: a citizen's cross-lab history is
  the entire point of a national aggregator. Not a defect.
- **`TestResult` writes (`create_test_result`):** see F2 above — this is
  where the missing tenant/ownership check actually bites (on write, not
  read).
- **`Notification`:** SQL-level scoping by `recipient_id` is real and
  correct (see F1) — the defect is upstream of the query, in what feeds
  `recipient_id`.
- **device_bridge:** no persistent tenant-bearing storage at all
  (`InMemoryDB` — plain in-process lists, no SQL, no tenant column to
  check). N/A, not a defect, not ambiguous.
- **`backend/app/routes/device_results.py`** (read-only reference, not
  owned): `Sample` query is correctly scoped by
  `LabOrder.lab_id == current_user.lab_id`, and `current_user` comes from
  `Depends(get_current_user)` — a real, trusted, verified dependency.
  **VERIFIED SAFE** on this specific point. (Its *separate*, already-
  documented idempotency gap is §3/§4 below, not a tenant-isolation
  issue.)

No new tenant-isolation defects beyond F2 above.

---

## 3. Idempotency matrix (reachable mutations only — no new framework proposed)

| Operation | Mechanism | Key source | Tenant scope | Persistence | Uniqueness constraint | Retry behavior | Concurrent behavior | Disposition |
|---|---|---|---|---|---|---|---|---|
| `POST /v1/citizens/register` | Application-level duplicate detection (`services/duplicates.py`, Jaro-Winkler fuzzy match) + exact `national_id` conflict check | none (no client-supplied idempotency key) | N/A (national registry) | Postgres via SQLAlchemy | `national_id` not unique at DB level — enforced only by pre-insert query (TOCTOU-able under true concurrency) | none — a retried POST after a timeout could create a near-duplicate if the fuzzy-match score lands under threshold | **not verified under real concurrent load this pass** — the pre-check-then-insert pattern is a classic race window; flagging as **DEFERRED**, not proven, per this pass's "no speculative implementation" instruction (would need a concurrent-connections test against real Postgres, which the current SQLite-only test fixtures can't exercise) | DEFERRED |
| `PUT /v1/citizens/{id}` | none | path param | N/A | Postgres | none | naturally idempotent in effect (same payload → same end state) even without a formal mechanism | benign — last-write-wins on a single row, no double-effect risk | VERIFIED SAFE (no idempotency mechanism needed — updates are naturally convergent) |
| `POST /v1/test-results/` | none | none | `payload.lab_id` (see F2) | Postgres | none on (citizen, lab, test_code, performed_at) | a retried/duplicated submission creates a second, indistinguishable `TestResult` row | **not concurrency-tested this pass** | DEFERRED (same root gap as backend's `/device/results`, finding #8 in the main work map — reuse that recommendation, don't invent a second one) |
| `PUT /v1/test-results/{id}/verify` | Status-machine guard (`if row.status == verified: 409`) | path param | N/A | Postgres | implicit via status field | a retried verify after the first succeeded gets a clean 409, not a silent double-effect | **this one is genuinely safe**: the 409 guard makes a retry a no-op from the caller's point of view | VERIFIED SAFE |
| `PUT /v1/notifications/{id}/read` | `is_read` flag check before mutating | path param + spoofable `X-Actor-Id` (F1) | `recipient_id` (see F1) | Postgres | implicit via `is_read` | retry-safe (no double `read_at` overwrite storm — only sets if not already read) | safe | VERIFIED SAFE *for idempotency specifically* — authorization is the defect (F1), not this |
| device_bridge `process_chunk` → `gula_client.send_results` | `retry_queue.content_key()` (sha256 over device_id+patient_id+test_code+value+timestamp) — **local to device_bridge only, never sent to the backend** | derived from parsed device data | none (in-memory only) | none (in-memory, lost on restart) | dict keyed by content hash in `sync_engine` (dedupes *device_bridge's own* re-staging) | fixed this engagement (findings #6/#7 in main work map): retry_queue now drains once, sync_engine dedupes by stable key, `/edge/sync` performs a real resend | fixed this engagement — see main work map findings #6/#7 for full detail | FIXED (this engagement, prior batches) |
| `backend/app/routes/device_results.py::POST /device/results` (read-only reference) | none | none | `current_user.lab_id` (trusted — see §2) | Postgres | none | a retried/duplicated `DeviceSubmission` creates duplicate `LabResult` rows | not tested this pass (not owned) | Already documented as finding #8 in the main work map (needs a migration; canonical mechanism — `backend/app/integration/inbox.py`'s `idempotency_key` pattern — already exists and should be reused, not reinvented). **No new information this pass** — re-confirmed, not re-investigated further. |
| `server` `POST /api/v1/demo/session` | Rate limit (`canStartDemo`, 8/IP/60s) — not idempotency, a volume cap | client IP | N/A (demo, no tenant) | in-memory `Map` | none — each call creates a fresh signed token/cookie | intentionally NOT idempotent — every call is meant to mint a new demo session | benign — worst case is extra demo sessions, capped by the rate limit | VERIFIED SAFE (idempotency is not the right property to want here — confirmed by design intent, not a gap) |
| `server` `DELETE /api/v1/demo/session` | `revokedDemoSessions` map write | signed cookie claims (server-verified — see finding #15) | N/A | in-memory `Map` | none — but revocation is naturally idempotent (revoking twice is a no-op) | safe | safe | VERIFIED SAFE |

**No new idempotency mechanism proposed or implemented anywhere in this
matrix**, per instruction. Two rows (`register_citizen`,
`create_test_result`) are marked **DEFERRED** rather than measured
"safe" or "unsafe" under concurrency — proving or disproving a true race
condition would require a real concurrent-Postgres test harness this
pass doesn't have set up, and asserting either way without that evidence
would violate this pass's "no speculative" instruction. `create_test_result`'s
underlying gap is already covered by finding #8 in the main work map;
`register_citizen`'s TOCTOU window is new information, logged here for
whoever next touches concurrent-registration testing.

---

## 4. API / contract boundaries

| Arrow | Status | Evidence |
|---|---|---|
| `device_bridge` → GULA backend | **FIXED this engagement** (main work map finding #7) | Payload shape now matches `backend/app/routes/device_results.py`'s actual `DeviceSubmission` contract; auth-token pass-through hook added (not a full fix — real credential issuance depends on Abu Ali's machine-identity work, documented, not attempted) |
| `edge_agent` → backend | **VERIFIED SAFE** (new this pass) | `backend/app/routes/edge.py` implements exactly the three paths `EdgeAgent`/`cli.py` call: `POST /edge/devices/register`, `POST /edge/agent/heartbeat`, `POST /edge/agent/tasks/{task_uid}/result` (confirmed by direct grep of both sides). Not exhaustively field-by-field verified (would mean reading deep into `edge.py`'s Pydantic models, which sits closer to Abu Ali's general `backend/app` territory than this pass's remaining budget justified) — path-level contract is real, not phantom, unlike the device_bridge case. |
| `client` → `server` | **VERIFIED SAFE** (previous batch, re-confirmed) | `client/src/App.tsx`'s three `fetch()` calls (`/api/v1/demo/status`, `/api/v1/demo/session`, `/api/v1/demo/dashboard`) match `server/index.ts`'s route definitions exactly; covered by this pass's new `server/tests/demoSession.test.ts`. |
| `server` → downstream services | **N/A** | `server/index.ts` has no real downstream service calls — `healthCheck.ts` no longer queries a real DB (already fixed elsewhere for a prior Dependabot SQL-injection alert, confirmed by reading its own docstring) and is a synthetic status shim. Nothing to check. |

No new field-mismatch, silent-drop, enum-incompatibility, or
false-success defects found beyond what's already fixed/documented.

---

## 5. Audit / security evidence

- **Actor identity is client-authored, not verified**, across all five
  nhop-platform route files (`_actor_id()` = raw `X-Actor-Id` header).
  This means the audit trail itself — the thing you'd reach for after an
  incident — can be forged: an attacker exploiting F1 or F2 can also
  simply put someone else's name in `X-Actor-Id` and have the audit log
  attribute their own action to an innocent party. This is the same root
  cause as F1/F2/finding #11 (no verified identity anywhere in
  nhop-platform yet), not a separate defect to fix independently —
  fixing audit-actor integrity requires the exact same identity binding
  as fixing authorization. Filed as part of F1/F2's disposition, not a
  standalone finding, to avoid inflating the count with a duplicate root
  cause.
- **No security exceptions are swallowed** in the code touched this
  engagement: `require_roles()` raises (401/403) rather than catching and
  continuing; `verify_api_key()` (device_bridge) raises after this
  engagement's fix (previously `sys.exit(1)`, which is a crash, not a
  swallow — also already fixed); `readDemoClaims()` (server) returns
  `null` on any parse/verify failure and every caller correctly treats
  `null` as "not authenticated" (401), never as a silent pass. No new
  finding here.
- **Mutations do generate audit evidence** in every nhop-platform route
  (via `log_action`) and in device_bridge (`add_audit_event`,
  `save_log`) — coverage exists, only the actor-identity field feeding it
  is unverified (see above).

---

## 6. CI false-green — paths affected by Mustafa's work

### F4 — P1 — None of the three Python services this engagement fixed are executed by CI at all

- **Location:** `.github/workflows/ci.yml`.
- **Reachability:** this is the actual CI pipeline for the repository —
  maximally reachable.
- **Observed behavior:** the only test-execution job in the entire
  workflow is `test` ("Backend Tests"), which runs
  `cd backend && python -m pytest tests/` — nothing else. The one
  `nhop-platform`/`edge_agent`/`services` reference anywhere in the file
  (`syntax-gate`'s "Check service Python syntax" step) only calls
  Python's `compile()` on each file — a bare syntax check, not an import
  walk and not a test run (contrast with `backend/app`, which CLAUDE.md
  documents as getting a full import-walk in the same gate). The root
  `Makefile` has zero references to any of the three service directories
  either.
- **Minimal reproduction:** `grep -n "pytest" .github/workflows/ci.yml`
  → exactly two lines, both under `cd backend`. `grep -n "nhop\\|device_bridge\\|edge_agent" Makefile` → no output.
- **Security/data-integrity impact:** all 116 tests fixed or added this
  engagement across `nhop-platform` (58), `services/device_bridge` (36),
  and `edge_agent` (22) — including the three new proof-of-vulnerability
  tests in this very pass — currently provide **zero CI enforcement**. A
  regression in any of these three services, including silently
  reverting one of this engagement's fixes, would merge with a fully
  green pipeline.
- **Existing control:** the `syntax-gate` step catches syntax errors only
  (would not have caught, for example, the `DEFAULT_API_KEY` `ImportError`
  that broke device_bridge's entire test suite before this engagement,
  since `compile()` doesn't execute imports).
- **Why insufficient:** a syntax check cannot catch a logic regression,
  an import error, or a test failure — the exact three classes of defect
  this engagement found and fixed in these services.
- **Recommended owner:** whoever owns `.github/workflows/ci.yml` /
  overall CI policy.
- **Dependency on Abu Ali:** none identified — this is a CI-configuration
  gap, not an identity/auth architecture question.
- **Disposition: BLOCKED.** `CLAUDE.md`'s own "Autonomous Task
  Boundaries" table lists "CI pipeline modifications (`.github/workflows/`)"
  under **Requires human approval** — a bright-line rule, not a judgment
  call to weigh against severity. Not modified. Documented with the exact
  missing job definition a human would need to add (three `pytest`
  invocations, one per service directory, each isolated per this
  engagement's own working pattern — `cd <service> && PYTHONPATH=...
  python -m pytest tests/`).

### Verification of Mustafa's own new tests (not CI-wide, per instruction scope)

- `nhop-platform/tests/` (58 tests, including this pass's 2 new proof
  files): collected and passing via the documented run command
  (`cd nhop-platform && PYTHONPATH=<root> pytest tests/ -q`).
- `services/device_bridge/tests/` (36 tests): same, via
  `PYTHONPATH=<root> pytest services/device_bridge/tests/ -q`.
- `edge_agent/tests/` (22 tests): same, via
  `PYTHONPATH=<root>:<root>/edge_agent pytest edge_agent/tests/ -q`.
- `server/tests/` (17 tests): via `cd server && npx vitest run` (its own
  scoped `vitest.config.ts`, added this engagement specifically because
  the inherited root config would otherwise hide it — see main work map
  finding #15).
- All four confirmed green in this pass, immediately before this report.

---

## INTEGRATION_HANDOFF

Machine-readable handoff block. F1 and F2 are **not** resolved, safe, or
passing — they are proven-live defects whose fix is out of this
engagement's ownership. Neither is fixable without either (a) building a
second, competing identity/authorization mechanism ahead of the canonical
one Abu Ali's stream is actively building, or (b) waiting for that
canonical mechanism to land and wiring nhop-platform to it. A finding
being blocked on another stream's architecture does not make it safe —
it means ownership is transferred pending coordination, not that the
exposure has closed.

```
F1:
  severity: P0
  owner: Abu-Ali-auth
  status: BLOCKED_BY_CANONICAL_IDENTITY
  required_outcome: actor identity MUST be derived from trusted authenticated context, never request-controlled actor ID
  no_competing_auth_implementation: true
  proof: nhop-platform/tests/test_notifications_actor_id_is_not_a_trust_boundary.py
  location: nhop-platform/app/api/v1/notifications.py

F2:
  severity: P1
  owner: Abu-Ali-auth/backend
  status: BLOCKED_BY_SERVER_AUTH_CONTEXT
  required_outcome: lab ownership MUST be derived/validated server-side; request_lab_id MUST NOT itself establish authority
  proof: nhop-platform/tests/test_results_lab_id_is_not_ownership_checked.py
  location: nhop-platform/app/api/v1/test_results.py:204

F4:
  severity: P1
  owner: GULA-CI/HUMAN-APPROVAL
  status: COORDINATION
  required_outcome: affected service tests (nhop-platform, services/device_bridge, edge_agent) must execute in CI
  do_not_modify_workflow: true
  location: .github/workflows/ci.yml
```

**Explicit non-status:** F1 and F2 remain **BLOCKED / COORDINATION**, not
`PASS`, `SAFE`, or `RESOLVED`, until a trusted server-side identity/
authorization control is proven at runtime against them (i.e. until the
proof tests above are updated to assert the *rejection* of a spoofed
`X-Actor-Id` / unowned `lab_id`, and that updated assertion passes against
real code, not until they are merely deprioritized or reclassified).
