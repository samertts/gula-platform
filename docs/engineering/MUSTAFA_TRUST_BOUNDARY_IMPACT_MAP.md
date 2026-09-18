# GULA — Trust Boundary Impact Map

Discovery-and-evidence-only pass. No fixes, no auth redesign, no migration,
no `.github/workflows/` changes. Scope: `nhop-platform/` (primary — this is
where F1/F2/X-Role live) plus `services/device_bridge/`, `edge_agent/`,
`server/` checked for the same pattern classes. Static/deterministic
analysis first; two tiny reachability tests added only where a newly
discovered path needed runtime confirmation (see §13).

---

## 1. Executive summary

F1, F2, and the already-documented `X-Role` finding are not three
independent bugs — they are three visible symptoms of one fact:
**nhop-platform has no authoritative identity source at all.** Every
"authorization" check in this service terminates at a raw HTTP header the
client supplies (`X-Role`, `X-Actor-Role`, `X-Actor-Id`), with nothing
between the header and the decision — no session, no token, no signature,
no lookup against a trusted store. This isn't one weak control; it's the
absence of the layer a control would sit on.

The pattern is not confined to notifications.py and test_results.py. This
pass found it also governs **who a `TestOrder` is attributed to**
(`doctor.py::order_tests` writes the caller-claimed `X-Actor-Id` directly
into `TestOrder.doctor_id`) and **which lab a doctor's order is routed to**
(`doctor.py::order_tests`'s `preferred_lab_id`, structurally identical to
F2's `lab_id`, on the order side rather than the result side). Three
non-interoperating authorization mechanisms coexist in the same five-file
service, none of them backed by verification.

The main GULA backend (`backend/app/security/auth.py`) does have a real,
JWT-backed `get_current_user` — CLAUDE.md calls it out explicitly and this
engagement independently confirmed `backend/app/routes/device_results.py`
correctly depends on it. **nhop-platform has simply never been wired to
it.** That is the fix's shape, when it happens — not something to build
here, and not something this pass invents.

No new P0 was found beyond F1. One new P1-adjacent instance of F2's exact
pattern was found (`doctor.py`'s `doctor_id`/`preferred_lab_id`). No
reachable bypass of a route that otherwise has a gate was found — the gap
is in routes that never had one, not in a control someone can route
around.

---

## 2. F1 (P0) impact map — `notifications.py`

```
REQUEST (X-Actor-Id: <any string>)
  ↓
ROUTER  nhop-platform/app/api/v1/notifications.py
  ↓
DEPENDENCY  _require_user_id(request) → request.headers.get("X-Actor-Id")
            (nhop-platform/app/api/v1/notifications.py:35-42)
  ↓
"AUTHORIZATION DECISION"  none — the header value IS accepted as the
            authenticated identity; no verification step exists
  ↓
SERVICE  services/notification.py::list_for_user / unread_count / mark_read
            — correctly filters SQL by recipient_id == user_id
  ↓
DATABASE QUERY  SELECT/UPDATE notifications WHERE recipient_id = :user_id
  ↓
RESOURCE  another party's notification rows, including citizens' own
            critical-result clinical alerts (test_results.py's
            _fire_critical_alert sends recipient_id=citizen.health_id —
            a non-secret, discoverable identifier returned by citizens.py's
            own /search and /{health_id} endpoints)
```

**Reachable endpoints:** `GET /v1/notifications/`,
`GET /v1/notifications/unread-count`, `PUT /v1/notifications/{id}/read`.
**Existing control:** none (no role check of any kind — weaker than every
other route file in the service).
**Proof:** `nhop-platform/tests/test_notifications_actor_id_is_not_a_trust_boundary.py`
(unchanged this pass, re-run — still passes, still demonstrates the live
behavior).

---

## 3. F2 (P1) impact map — `test_results.py`

```
REQUEST  POST /v1/test-results/  { health_id, lab_id, test_code, ... }
  ↓
ROUTER  nhop-platform/app/api/v1/test_results.py::create_test_result
  ↓
DEPENDENCY  role: str = Depends(_lab_staff)  → core.rbac.require_roles
            (X-Role header, itself unverified — see §5)
  ↓
"AUTHORIZATION DECISION"  role name checked against an allow-list; no
            check that the caller is affiliated with payload.lab_id
  ↓
DATA SELECTION  lab = db.query(Lab).filter(Lab.id == payload.lab_id).first()
            (test_results.py:204) — lab_id taken directly from the request
            body, no caller↔lab binding anywhere upstream
  ↓
DATABASE WRITE  INSERT test_results (lab_id=payload.lab_id, ...)
  ↓
RESOURCE  the new TestResult row is permanently attributed to
            payload.lab_id, readable by anyone with clinical-staff/
            ministry role via GET /v1/test-results/citizen/{health_id}
            (no lab-level filtering on read either — see §7, this is
            correct-by-construction for a cross-lab national view, not a
            second defect, but it does mean a misattributed result is
            visible platform-wide, not confined to a mistake nobody sees)
```

**Reachable endpoint:** `POST /v1/test-results/`.
**Existing control:** `_lab_staff` role gate (LAB/ADMIN) — same
unverified-header root cause as F1, plus "lab must exist and be active."
Neither checks caller↔lab affiliation.
**Proof:** `nhop-platform/tests/test_results_lab_id_is_not_ownership_checked.py`
(unchanged this pass, re-run — still passes).

**New this pass — same pattern, adjacent surface:**
`doctor.py::order_tests` (lines ~160-166) takes `payload.preferred_lab_id`
from the request body and uses it to decide which lab a new `TestOrder` is
dispatched to, with the identical "lab must exist and be active, no
caller↔lab check" shape. Severity note: routing a *future* order to a lab
is not equivalent to *misattributing a completed result's provenance* —
the write-side integrity impact of F2 is more severe than this adjacent
instance — but it is the same code pattern, present a second time in the
same service, and confirms F2 is not an isolated one-off.

Same file, same route, same root cause, worse: `_require_doctor()`
(doctor.py:69-87) returns the raw, unverified `X-Actor-Id` header value as
`doctor_id`, which `order_tests` then writes directly into
`TestOrder.doctor_id` (doctor.py:171). Any caller who satisfies the
(equally spoofable) `X-Actor-Role: DOCTOR` check can claim to be *any*
doctor and have that claim permanently recorded as who ordered a clinical
test. This is F1's exact defect class (client-controlled identity
persisted as an attribution field), independently discovered on the write
side of `doctor.py` rather than the read side of `notifications.py`.

---

## 4. X-Role relationship

`core.rbac.require_roles()` (`nhop-platform/app/core/rbac.py`) is the
mechanism behind F2's `_lab_staff` gate and `citizens.py`'s gates from the
previous batch. It shares F1's exact root cause — a raw header taken at
face value — but is structurally distinct from F1 in one respect: F1 has
**no gate at all**; `X-Role`-gated routes have a gate, it is simply
unauthenticated. Both converge on the same missing layer (§6).

---

## 5. Trust-context data-flow table (Mission 1)

Only reachable, security-relevant flows are listed. Query-parameter uses
that merely *filter* a data set the caller is already permitted to see in
full (e.g. `outbreak.py`'s `province` parameter, gated by
`_ministry_or_admin` before the parameter is ever read) are not included —
they don't establish authority, they narrow an already-granted one.

| Pattern | Source | Endpoint | File | Function | Sink | Auth decision | Trust | Reachability | Severity | Existing control | Affected domains | Evidence |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `X-Actor-Id` | header | `GET/PUT /v1/notifications/*` | `api/v1/notifications.py` | `_require_user_id` | `Notification.recipient_id` filter | **is** the decision | Client-controlled | Reachable, no gate | **P0** | none | notifications, citizen PHI (critical alerts) | `test_notifications_actor_id_is_not_a_trust_boundary.py` |
| `X-Role` | header | `POST/PUT/GET /v1/citizens/*` | `api/v1/citizens.py` | `core.rbac.require_roles` | role allow-list check | gates the route | Client-controlled | Reachable, behind gate | P0 (documented prior batch, finding #11) | `require_roles` (unauthenticated) | citizen registry PII | `test_rbac_is_not_a_trust_boundary.py` |
| `X-Role` | header | `POST /v1/test-results/`, `PUT .../verify`, reads | `api/v1/test_results.py` | `core.rbac.require_roles` | role allow-list check | gates the route | Client-controlled | Reachable, behind gate | P0 (finding #11) | same | lab results | same file |
| `X-Actor-Role` + `X-Actor-Id` | header | `POST /doctor/order-tests`, `/refer`, `GET /doctor/patient/*` | `api/v1/doctor.py` | `_require_doctor` | role check + `doctor_id` attribution | gates the route **and** feeds a write | Client-controlled | Reachable, behind gate | **P1 (new this pass)** | `_require_doctor` (unauthenticated) | test orders, citizen clinical read | this pass, §3 |
| `payload.lab_id` | request body | `POST /v1/test-results/` | `api/v1/test_results.py` | `create_test_result` | `Lab` selection for write | not evaluated (no ownership check) | Client-controlled | Reachable, behind (unauthenticated) role gate | **P1 (F2)** | "lab active" existence check only | lab result provenance | `test_results_lab_id_is_not_ownership_checked.py` |
| `payload.preferred_lab_id` | request body | `POST /doctor/order-tests` | `api/v1/doctor.py` | `order_tests` | `Lab` selection for order dispatch | not evaluated | Client-controlled | Reachable, behind (unauthenticated) role gate | **P1 (new this pass)** | "lab active" existence check only | order routing | this pass, §3 |
| `user_id`/`account_id` from request data | — | — | — | — | — | — | — | **NOT FOUND** beyond `X-Actor-Id` above — nhop-platform has no separate `user_id`/`account_id` request field anywhere; the same header serves both roles | — | — | grep: no `user_id`/`account_id` field in any Pydantic schema in `nhop-platform/app/schemas/` |
| `organization_id`/`facility_id` from request data | — | — | — | — | — | — | — | **NOT FOUND** — nhop-platform has no organization/facility hierarchy concept anywhere in its models or schemas | — | — | `grep -rln "facility_id\|organization_id\|account_id\|org_id" nhop-platform/app` → no matches |
| `device_id` (request body, `services/device_bridge`) | request body | `/ingest`, `/devices/{id}/*` | `services/device_bridge/app/main.py` | route handlers | logging, session-buffer keying, command routing | gated by a single shared API key (`verify_api_key`), not per-device | Client-controlled *within* an already-authenticated deployment | Reachable, behind gate | **Not a new finding** — device_bridge has no internal multi-tenancy; one API key = one deployment = one lab already, by architecture, so "any device_id" within that key's scope isn't a cross-tenant boundary crossing the way F1/F2 are. Noted, not elevated. | shared API key (device_bridge-wide) | device attribution within one deployment | reviewed this pass, no new test added (not the same defect class) |

---

## 6. Shared root-cause analysis (Mission 2)

**A. What is the current authoritative identity source?**
None exists inside `nhop-platform`'s own code. `core/database.py::get_db`
is a bare SQLAlchemy session factory with zero identity logic. No
middleware, session store, or token-verification layer exists anywhere in
this service. The main GULA backend has one
(`backend/app/security/auth.py`'s JWT `get_current_user`, confirmed in a
prior batch to correctly gate `backend/app/routes/device_results.py`) —
but nhop-platform has never been connected to it.

**B. Where does it stop being authoritative?**
Trick premise: it never starts, within nhop-platform. From the first
point any identity is referenced (`request.headers.get(...)`), it is
already client-controlled. There is no earlier point at which it was
authoritative and later became untrusted.

**C. Which layer first accepts client-controlled identity?**
The route/dependency layer itself — `core/rbac.py::require_roles`'s inner
`_dep`, and each route file's own `_actor_id` / `_require_doctor` /
`_require_user_id` helpers. There is no layer upstream of these (no
gateway auth, no session middleware) that could have validated the header
before the route saw it.

**D. Which endpoints bypass the canonical security context?**
Reframed by (A): there is no canonical security context in nhop-platform
to bypass. Every endpoint in this service currently operates without one.
The question becomes moot until nhop-platform is wired to the backend's
real one.

**E. Are there multiple competing authorization mechanisms?**
Yes, three, none interoperating, none verified:
1. `core.rbac.require_roles()` / `X-Role` — `citizens.py`, `test_results.py`, `outbreak.py`.
2. `doctor.py`'s own inline `_require_doctor()` / `X-Actor-Role` + `X-Actor-Id`.
3. `notifications.py`'s bare `_require_user_id()` / `X-Actor-Id` with no role concept at all.

**Verdict: `AUTHORITATIVE_SOURCE_NOT_PROVEN`** (for nhop-platform's
reachable code). Not asserted as unfixable or as requiring a new
architecture invented here — the shape of the eventual fix already exists
elsewhere in the repo (`backend/app/security/auth.py`), unconnected.

---

## 7. Control coverage table (Mission 3)

Only security boundaries, not general API completeness. `UNKNOWN` is used
verbatim where this pass could not establish a value from static evidence
— never silently upgraded to a pass.

| Endpoint | Authn | Identity binding | Org binding | Role binding | Permission | Tenant/resource ownership | Audit | Idempotency (if mutation) | Result |
|---|---|---|---|---|---|---|---|---|---|
| `POST /v1/citizens/register` | CLIENT_CONTROLLED | CLIENT_CONTROLLED | UNREACHABLE (no org concept) | CLIENT_CONTROLLED | N/A (no fine-grained permission layer beyond role) | N/A (creates new resource) | VERIFIED (`log_action`, actor field unverified) | PARTIAL (fuzzy dup-detection, TOCTOU window — see main forensic pass idempotency matrix) | Known (finding #11, prior batch) |
| `GET /v1/citizens/search`, `/{id}`, `/{id}/summary` | CLIENT_CONTROLLED | CLIENT_CONTROLLED | UNREACHABLE | CLIENT_CONTROLLED | N/A | N/A (national registry, correct by construction) | VERIFIED | N/A (read) | Known (#11) |
| `PUT /v1/citizens/{id}` | CLIENT_CONTROLLED | CLIENT_CONTROLLED | UNREACHABLE | CLIENT_CONTROLLED | N/A | VERIFIED (immutable-field rejection via `extra="forbid"`) | VERIFIED | VERIFIED (naturally convergent update) | Known (#11) |
| `POST /v1/test-results/` | CLIENT_CONTROLLED | CLIENT_CONTROLLED | UNREACHABLE | CLIENT_CONTROLLED | N/A | **MISSING** (F2) | VERIFIED | PARTIAL (main forensic pass: no dedup on retry/resubmit) | **F2 — this + prior pass** |
| `PUT /v1/test-results/{id}/verify` | CLIENT_CONTROLLED | CLIENT_CONTROLLED | UNREACHABLE | CLIENT_CONTROLLED | N/A | N/A (path-scoped, not lab-scoped by design) | VERIFIED | VERIFIED (status-machine 409 guard) | Known (#11) |
| `GET /v1/test-results/citizen/{id}`, `/timeline`, `/{id}` | CLIENT_CONTROLLED | CLIENT_CONTROLLED | UNREACHABLE | CLIENT_CONTROLLED | N/A | N/A (cross-lab read, correct by construction) | VERIFIED | N/A | Known (#11) |
| `GET/PUT /v1/notifications/*` | **MISSING** | **MISSING** | UNREACHABLE | **MISSING** (no role concept at all) | N/A | **MISSING** (the `recipient_id` filter is real SQL but fed by unverified input) | VERIFIED (actor field unverified) | VERIFIED (`mark_read`'s `is_read` guard) | **F1 — this pass** |
| `POST /doctor/order-tests` | CLIENT_CONTROLLED | CLIENT_CONTROLLED (see §3, `doctor_id` write) | UNREACHABLE | CLIENT_CONTROLLED | N/A | **MISSING** (`preferred_lab_id`, see §3) | VERIFIED (actor field unverified) | UNKNOWN (not tested this pass — duplicate-order suppression exists for the *same* lab/test/window, per prior batch's test suite, but concurrent double-submission wasn't re-verified here) | **New this pass** |
| `POST /doctor/refer` | CLIENT_CONTROLLED | CLIENT_CONTROLLED | UNREACHABLE | CLIENT_CONTROLLED | N/A | N/A (references an existing citizen only, no lab attribution) | VERIFIED | UNKNOWN (not exercised this pass) | Reviewed, no new finding |
| `GET /doctor/patient/{id}/overview`, `/timeline/{code}` | CLIENT_CONTROLLED | CLIENT_CONTROLLED | UNREACHABLE | CLIENT_CONTROLLED | N/A | N/A (read, cross-lab by design) | VERIFIED | N/A | Reviewed, no new finding |
| `GET /v1/outbreak/alerts`, `/heatmap/*`, `/resistance` | CLIENT_CONTROLLED | CLIENT_CONTROLLED | N/A (aggregate, no per-citizen identity in response — spot-checked schema, not exhaustively) | CLIENT_CONTROLLED (`_ministry_or_admin`) | N/A | N/A (aggregate counts, ministry-level by design) | VERIFIED | N/A | Reviewed, no new finding |

---

## 8. Alternate/bypass entry points (Mission 6)

| Candidate | Disposition | Evidence |
|---|---|---|
| Reaching citizen clinical data via `doctor.py` instead of `citizens.py`/`test_results.py` | **ALREADY PROTECTED** (by a different, equally unverified mechanism — not a bypass of the `X-Role` gate, a parallel gate with the same root weakness) | `_require_doctor` is present on every `doctor.py` route; it is not *absent* the way `notifications.py`'s check is |
| Reaching notification data via any route other than `notifications.py` | **DEAD CODE / NOT FOUND** — no other router queries the `Notification` model | `grep -rn "Notification" nhop-platform/app/api` → only `notifications.py` |
| A second, unregistered router reaching the same models (repeat of the batch-1 shadow-route pattern) | **FALSE POSITIVE** — `api/v1/__init__.py` registers exactly five routers (`citizens`, `test_results`, `notifications`, `doctor`, `outbreak`); no sixth file exists in `api/v1/` | `ls nhop-platform/app/api/v1/*.py` |
| Direct service-layer calls bypassing the route/dependency layer entirely | **UNREACHABLE from outside the process** — `services/notification.py`, `services/duplicates.py`, etc. are plain Python functions with no HTTP exposure of their own; the only way to reach them is through the routers already covered | inspected each `services/*.py` file's callers |
| Admin-only or internal-only routes | **NOT FOUND** — no `/admin`, `/internal`, or `/_debug` prefix exists anywhere in `nhop-platform/app/api` | `grep -rn "APIRouter(prefix=" nhop-platform/app/api/v1/*.py` → five prefixes, all customer-facing |
| Test/demo routes accidentally reachable in production | **NOT FOUND in nhop-platform** — no demo/test route exists in this service (contrast with `server/`'s explicitly-labeled, already-reviewed demo mode, out of this pass's scope) | grep for `demo`/`test` route prefixes in `nhop-platform/app/api` → none |
| Background jobs writing `Notification`/`TestResult` rows outside the request path | **UNKNOWN** — no background-job runner was found referencing these models in the files this engagement has read, but nhop-platform's full `services/` directory was not exhaustively re-audited this pass for scheduled/cron entry points beyond what earlier batches already covered | not exhaustively verified — flagged rather than asserted safe |

No true reachable bypass of an *existing* gate was found. The gap is
entirely in routes that never had a gate (`notifications.py`) or gates
that don't check the specific field in question (`lab_id`/`preferred_lab_id`
ownership) — not in a control that can be routed around.

---

## 9. Notifications impact detail (Mission 4)

- **Who can create notifications:** no client-facing endpoint exists;
  the only caller is `test_results.py::_fire_critical_alert`, itself
  behind `_lab_staff` (unauthenticated `X-Role`, per F2's root cause, but
  at least gated). Not directly client-triggerable.
- **Who can read them:** anyone who supplies any `X-Actor-Id` matching
  (or guessing) a real `recipient_id` — see F1.
- **Who can mark them read:** same — see F1, second proof test.
- **Notification ID enumerability:** `Notification.id` is a random
  `uuid.uuid4()` (`nhop-platform/app/models/notification.py:51-55`), not
  sequential or predictable. This does **not** meaningfully limit the F1
  exploit, because the primary attack path (`GET /v1/notifications/`,
  listing by `recipient_id`) never requires knowing an individual `id` —
  an attacker who lists first is handed every `id` for that recipient
  anyway. Recorded factually, not treated as a mitigating control.
- **PHI/clinical content in payloads:** yes — confirmed via
  `test_results.py::_fire_critical_alert`'s `title`/`body` construction,
  which includes the test name, code, value, unit, and direction of a
  critical lab result.
- **Downstream trust of notification actor identity:** none found — no
  code reads `Notification.recipient_id` back out and treats it as a
  verified identity for a further decision; it is a terminal sink, not a
  propagation point, in the code this pass could reach.
- **Cross-user leak via unread-count:** yes, same mechanism as the list
  endpoint — `GET /v1/notifications/unread-count` returns a count scoped
  by the same unverified `user_id`.
- **Other routers using the same actor-header pattern:** yes — all five
  route files use `X-Actor-Id` for audit-log attribution (see main
  forensic pass report, §5); `doctor.py` additionally uses it as a
  persisted `doctor_id` foreign-key-equivalent value (see §3, new this
  pass).

---

## 10. Test-results impact detail (Mission 5)

- **Exact fields accepted** (`TestResultCreate`,
  `nhop-platform/app/schemas/test_result.py`): `health_id`, `lab_id`,
  `test_code`, `test_name`, `category`, `value_numeric`, `value_text`,
  `unit`, `reference_min`, `reference_max`, `performed_at`.
- **How `lab_id` is selected:** directly from the request body, checked
  only for existence and `is_active` — see F2.
- **How caller identity is selected:** `role` from `X-Role` (F2's
  precondition); no per-caller identity is captured on the `TestResult`
  row itself (unlike `TestOrder.doctor_id` in `doctor.py`).
- **Cross-lab readability:** yes, by design — `GET
  /v1/test-results/citizen/{health_id}` and `/timeline` filter by
  `citizen_id` only, not `lab_id` (confirmed correct-by-construction in
  the main forensic pass, §2 tenant-isolation section — NHOP is
  deliberately a cross-lab aggregator). This means a misattributed result
  (F2) is visible to every subsequent reader platform-wide, not confined
  to whoever created it.
- **`lab_id` in audit records:** yes —
  `log_action(..., metadata={"lab_id": str(lab.id), ...})`
  (`test_results.py:137` area) — the audit trail faithfully records the
  (potentially spoofed) `lab_id`, meaning the audit log itself would show
  the misattribution as fact, not flag it as unverified.
- **Downstream workflow trust:** `_recompute_lab_metrics(db, lab,
  tat_minutes)` (`test_results.py`) increments the *selected* lab's
  `total_tests`/`avg_tat_minutes` counters — i.e. a misattributed result
  also pollutes that lab's own operational metrics, not just its audit
  trail.
- **Same pattern in adjacent result/order/specimen endpoints:** yes —
  `doctor.py::order_tests`'s `preferred_lab_id`, detailed in §3. No
  "specimen" endpoint exists in nhop-platform to check (no `Sample`/
  `Specimen` model in this service — that concept lives in the main GULA
  backend, out of this pass's scope).

---

## 11. Detector proposals (Mission 7) — design only, not implemented

| # | Name | Input | Detection rule | Expected false positives | Expected false negatives | Severity | CI suitability | Runtime proof required |
|---|---|---|---|---|---|---|---|---|
| 1 | Client-controlled identity detector | Route function source (AST) | Flag any function where a value read from `request.headers.get(...)` (or a `Header(...)` default parameter) is: (a) returned from an auth-named helper (`_require_*`, `_actor_id`, `get_current_*`), AND (b) that return value is later passed as a `filter()`/`==` argument to an ORM query, OR assigned to a model field on `.add()`/`db.add()`. | A helper that reads a header purely for logging/telemetry (no query/write use) would still match rule (a) alone — must require both (a) and (b) to avoid flagging benign header reads | A helper that launders the header through an intermediate variable/dict before reaching the query (data-flow, not direct assignment) would evade a shallow AST match — needs real dataflow tracking, not regex-on-AST-node-names, to avoid missing this | High (this is exactly F1/F2's shape) | Yes, as a fast static check (no runtime needed) | No — this is a static-analysis detector; a runtime test is a separate, complementary check, not required for the detector itself to fire |
| 2 | Client-controlled authorization-role detector | Route function source (AST) + a project-maintained list of "known-real" auth dependencies (e.g. `backend/app/security/auth.get_current_user`) | Flag any `Depends(X)` or in-body call where `X` (or the function it calls) ultimately reads its decision-relevant value from `Header(...)`/`request.headers` **and** is not itself a call into the maintained real-auth allowlist | A legitimately internal, single-shared-secret API-key check (e.g. device_bridge's `verify_api_key`) would match the rule's letter but is a different, deliberately-simpler trust model (one secret, not per-actor identity) — must exempt anything that checks a value against `os.getenv`/a config secret rather than treating the header value itself as an identity | A role check hidden behind a dynamically-constructed dependency (`Depends(factory(...))` where `factory` isn't statically resolvable) could evade — same dataflow limitation as #1 | High | Yes | No |
| 3 | Request-body tenant-authority detector | Route function source (AST) + Pydantic model field names matching `*_id` that also appear as a foreign key / relationship target in the ORM models directory | Flag any route where a Pydantic field named `lab_id`/`organization_id`/`facility_id`/`account_id` (etc.) is read from the validated request body and used in a `.filter(Model.id == <that field>)` **without** a preceding check that ties the *caller's own* verified identity to that same id (e.g. via a real auth dependency's returned object having a matching field) | A legitimate cross-entity reference where the caller is *supposed* to be able to name any valid target (e.g. `citizens.py`'s `health_id` path parameter, which is the resource being acted on, not a claimed *authority* over a third party) would false-positive if the rule can't distinguish "the resource itself" from "an authority claim about who the caller is" — this is exactly the "do not report mere string matches as vulnerabilities" caution from Mission 1; the rule must special-case path-parameter resource identifiers | A tenant field passed through a service-layer function before reaching the query (one hop removed from the route file) would evade a route-file-only scan | High (this is F2's and the new `preferred_lab_id`/`doctor_id` findings' exact shape) | Partially — needs a maintained "known resource-id fields" vs "known authority-claim fields" list to stay low-noise, which is curation work, not zero-config | No |
| 4 | Protected-endpoint-missing-trusted-context detector | Every `@router.<verb>` decorated function in the repo | Flag any route whose parameter list contains **no** dependency (by signature or in-body call, per the doctor.py lesson learned this pass) resolving to the project's real-auth allowlist, where the route also performs a DB write or reads a field commonly treated as sensitive (name-match against a maintained PII/PHI field list) | A genuinely public, non-sensitive route (e.g. `GET /health`) would match "no auth dependency" and must be exempted by an explicit public-route allowlist, not by absence of a write | An in-body auth check that isn't a recognizable name pattern (unlike `_require_doctor`, `_require_user_id`) could evade a name-based scan | **Critical for catching another `notifications.py`-shaped gap** — this is the single highest-value detector of the five, because F1 is "missing", not "present but weak" | Yes | No for the static flag; **yes** for confirming the flagged route is truly reachable and truly ungated (a cheap `TestClient` call asserting 401/403 is absent) before treating the static hit as confirmed rather than a lead |
| 5 | Alternate-entry-point authorization-coverage detector | The full route registry (every `include_router` call, transitively) + the ORM model graph | For each ORM model touched by a "protected" route (one with a real-auth dependency), enumerate every *other* route that touches the same model/table, and flag any without an equivalent-or-stronger dependency | A read-only, intentionally-public aggregate endpoint over the same table (e.g. `outbreak.py`'s counts over `DiseaseCase`) would false-positive against a stricter per-record endpoint over the same table unless the rule accounts for aggregation (no individually-identifiable row returned) | A model touched only via a service-layer function never called from a route (dead code) would be silently correctly excluded, but a model touched via a *dynamically dispatched* router (constructed at runtime rather than a static `include_router` call) could evade | Medium (this pass found no live instance of this specific bypass shape, but the shadow-route pattern from batch 1 — an unregistered router — is exactly what this detector generalizes) | Yes, as a nightly/periodic check rather than a per-PR gate (the model-graph enumeration is heavier than #1-4) | Yes — confirming "no equivalent dependency" requires an actual request to the flagged route, not just AST absence, to rule out an in-body check the AST pass missed |

No detector above proposes distinguishing "data" from "security authority"
by field name alone without the resource-vs-authority carve-out in #3 —
that carve-out is the one place this pass explicitly declined to propose
a fully-automated rule, because getting it wrong in either direction
(over-flagging every `*_id` path parameter, or under-flagging every
`*_id` body field) would make the detector worse than no detector.

---

## 12. Evidence limitations

- Static/deterministic analysis was the primary method; the two runtime
  facts newly asserted this pass (`doctor_id` write, `preferred_lab_id`
  selection) were confirmed by direct source reading of
  `doctor.py:69-87` and `:160-171`, not by a new executable test — no new
  test was added for them this pass, per the "no broad new test suites"
  instruction and because the existing `test_doctor_api.py` suite (prior
  batch) already exercises `order_tests` successfully, which is
  sufficient reachability proof without duplicating it.
- `backend/app/routes/edge.py`'s full field-level contract with
  `edge_agent` was confirmed at the path level only (prior forensic
  pass), not re-verified field-by-field this pass — out of this pass's
  one-hour scope.
- Background-job/scheduled-task coverage for `nhop-platform` was not
  exhaustively re-audited this pass (§8, last row) — flagged as UNKNOWN,
  not asserted safe.
- `outbreak.py`'s response schemas were spot-checked, not exhaustively
  read field-by-field, for accidental per-citizen identifiability in an
  otherwise-aggregate report.
- This pass did not attempt to determine whether `backend/app`'s real
  `get_current_user` could be wired into nhop-platform with a small
  adapter or requires the identity-service refactor Abu Ali's stream is
  mid-way through — that is a design question for whoever picks up F1/F2,
  explicitly out of scope here.

---

## 13. Exact files / endpoints / functions (index)

**Files read/analyzed this pass (none modified except this document):**
`nhop-platform/app/api/v1/{citizens,test_results,doctor,outbreak,notifications}.py`,
`nhop-platform/app/core/{rbac,database}.py`,
`nhop-platform/app/services/notification.py`,
`nhop-platform/app/models/notification.py`,
`nhop-platform/app/schemas/{notification,test_result,doctor}.py`,
`services/device_bridge/app/main.py`,
`edge_agent/gula_edge_agent/{agent,cli}.py`, `server/index.ts`,
`backend/app/routes/edge.py` (path-level, read-only, prior pass).

**Functions of record:**
`notifications.py::_require_user_id` (defect, F1),
`test_results.py::create_test_result` (defect, F2),
`doctor.py::_require_doctor` and `doctor.py::order_tests` (new this pass),
`core/rbac.py::require_roles._dep` (prior finding, X-Role),
`services/notification.py::{list_for_user,unread_count,mark_read}` (SQL
scoping — correct, not the defect).

**Endpoints of record:** see §7's table in full.

---

## 14. Recommended future verification sequence

1. Confirm (with whoever owns the identity refactor) whether
   nhop-platform is meant to eventually depend directly on
   `backend/app/security/auth.get_current_user`, or receive claims via a
   separate token-introspection call — this determines the shape of
   everything after it and is a design decision, not a static-analysis
   output.
2. Once a real identity dependency exists, extend
   `test_rbac_is_not_a_trust_boundary.py`,
   `test_notifications_actor_id_is_not_a_trust_boundary.py`, and
   `test_results_lab_id_is_not_ownership_checked.py` to assert
   **rejection** of a spoofed header / unowned `lab_id` against the real
   dependency — do not delete them; flip their assertions and confirm
   they fail against the *current* code first (proving they'd have
   caught this), then pass against the fix.
3. Apply the same fixed dependency to `doctor.py`'s `_require_doctor`
   (retiring the second, `X-Actor-Role`-based mechanism) and
   `notifications.py`'s `_require_user_id`, closing all three competing
   mechanisms into one.
4. Add caller↔lab ownership validation to `test_results.py::
   create_test_result` and `doctor.py::order_tests`'s `preferred_lab_id`,
   once the identity dependency can supply a trusted "caller's own
   lab(s)" value to check against.
5. Only after 1-4: consider Detector #4 (protected-endpoint-missing-
   trusted-context) as a CI gate, using the now-real dependency as the
   allowlist target — building the detector before the real dependency
   exists would have nothing authoritative to check *for*.
