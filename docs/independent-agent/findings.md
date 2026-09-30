# Independent findings

Severity: **P0** patient/data/security catastrophic · **P1** major production
risk · **P2** significant defect · **P3** moderate · **P4** minor.

A finding is only as strong as the thing it was measured against. Where a claim
rests on a grep it says so, because a grep over 780 mapped classes and 1794
served paths is a candidate generator, not a proof.

---

## IA-001 — P2 — `app/reference` derives its tenant scope from client input

**Component:** `backend/app/reference/routes/{orders,patients,results}.py`

**Evidence, measured:**

| handler | parameter | kind |
|---|---|---|
| `orders.py::create_order` | `lab_id: str = Query(...)` | **write** |
| `patients.py::create_patient` | `lab_id: str = Query(...)` | **write** |
| `patients.py::search_patients` | `lab_id: str \| None = Query(None)` | read |
| `results.py::list_critical_results` | `lab_id: str = Query(...)` | read |

`current_user` and `get_current_user` appear **nowhere** in the whole
`app/reference` package. That is the structural part: these handlers could not
compare the requested laboratory against the authenticated one even if they tried,
because they never obtain the principal. CLAUDE.md Security Invariant #1 is *"All
patient-data queries MUST filter by `lab_id = current_user.lab_id`"*; here it is
`lab_id = <client input>`, across patients, laboratory orders and critical
results. Two of the four are writes, so a caller does not merely read another
laboratory's data — it names the laboratory a new patient or order is filed into.

**Why this is NOT currently a breach**, and the reason severity is P2 rather than
P0: the reference routers are **mounted nowhere**. The assembled app serves 1794
paths and **0** begin with `/reference`. All three routers also carry
`dependencies=[Depends(require_permission("system:admin"))]`, so even mounted they
would not be anonymous.

**Impact:** latent. One `app.include_router(...)` turns it into a live
cross-tenant read *and write* over clinical data. The risk is that the package
reads as finished code.

**Fix:** derive `lab_id` from the authenticated principal and delete the query
parameter. Do not "validate" the client value against the principal — an endpoint
that accepts a tenant id it then has to check is a boundary waiting to be
widened.

**Status:** REPORTED + TRIPWIRED, not fixed. Fixing it means adding a principal
dependency to four handlers in a package with no principal anywhere, which is a
design change to an unserved subsystem — the wrong trade against live work.

**Tripwire:** `backend/tests/independent/test_reference_package_tenant_scope.py`
(3 tests): the package still never reads the principal; the set of
client-scoped handlers has not grown; and the package is still not served. The
third fails the moment someone mounts it as-is. Asserted against the OpenAPI
surface, not `app.routes`, because the platform mounts through a lazy
`_IncludedRouter` and a flat scan of `app.routes` reports nothing — reading one
would be exactly how this test passes while the routes are in fact served.

---

## IA-002 — P2 — 70 served operations take a tenant identifier from the client; 68 unverified

**Evidence:** over the assembled app's 1794 served paths, operations declaring a
tenant identifier as a `query` or `path` parameter:

| parameter | in path | in query |
|---|---|---|
| `lab_id` | 16 | 8 |
| `facility_id` | 2 | 9 |
| `org_id` | 10 | 5 |
| `organization_id` | — | 20 |
| **total** | | **70** |

**This is an inventory, not 70 defects.** Two were read in full and are
**correct**:

* `GET /citizen-platform/me/lab-results` — scope comes from
  `relationship.citizen_id` via `Depends(get_authorized_citizen_relationship)`;
  `lab_id` is a filter, not the authorization scope.
* `GET /citizen-platform/lab-results/{citizen_id}` and the 16 other
  `{citizen_id}` routes — the **router-level**
  `dependencies=[Depends(require_citizen_relationship)]` binds its own
  `citizen_id` parameter to the *path* id and requires an active, non-revoked,
  in-window relationship to that citizen, with per-resource scope via
  `relationship.allows(resource, write=...)` and a denied-decision audit row. Its
  docstring states it does not fall back to phone, national-ID hash or role-only
  checks, and the code matches. A per-route signature scan flags all 17 as
  unguarded; that scan is wrong.

**The remaining 68 are unverified.** That is the honest state and the highest-value
queue for the next pass. Ranked by blast radius: `GET /niam/audit` and
`/niam/audit/export` (audit trail scoped by client input), `GET
/blood-bank/inventory`, the five `/niam/certificates/...organization/{org_id}`
reads, and the `POST /niam/admin/...` writes.

**Status:** OPEN — inventory recorded, verification debt named. Nothing is
claimed broken.

---

## IA-003 — P2 — a killed database is indistinguishable from a code regression

**Component:** test/verification environment, `backend/tests/verification/harness.py`

**Evidence:** the same command
(`pytest tests/verification tests/kernel tests/kernel_hardening`) produced:

| run | result |
|---|---|
| with PostgreSQL killed mid-run | 17 failed / 370 passed / **83 errors** |
| baseline `203c85aa`, also degraded | 14 failed / 391 passed / **65 errors** |
| PostgreSQL verified up before and after | **13 failed / 457 passed / 0 errors** |

The first two readings look exactly like an 18-error regression introduced by the
commit under test. They were an environment failure. It was caught by running
`pg_isready`, not by reading the diff — the container reclaims PostgreSQL, and
`Removed stale pid file` on restart is the only trace.

**Impact:** an agent or engineer comparing suite counts across commits will
attribute an environment failure to code, and the natural next move — "fix the
regression" — changes working code to chase a phantom.

**Fix:** a session-scoped preflight that asserts the verification database is
reachable *before* collection and fails with an explicit ENVIRONMENT_FAILURE, so
the run aborts instead of producing 83 plausible errors.

**Status:** OPEN, deliberately not implemented here. The natural home is
`tests/verification/harness.py`, which `claude/autonomous-run-1` is actively
changing; a new `conftest` hook in that package would collide. Recorded for
integration rather than raced.

---

## Verified negatives

Recorded because a sweep that publishes only its hits hides its false-positive
rate, and three of this pass's five leads died on reading.

| probe | result |
|---|---|
| f-string / `%`-format interpolation inside `text(...)` or `execute(...)` over `app/` | **0 sites** |
| `pickle.loads`, `eval(`, `exec(`, `yaml.load` without `SafeLoader` | **0 uses**; the single hit is a *detector* in `certification/metrics.py` searching for them |
| Invariant #6, the `LabResult` optimistic lock | a real compare-and-swap at `services/order_service.py:583-597` (`filter(LabResult.version == expected_version)` with `version + 1`); no `.update()` on a `LabResult` query bypasses it, and the other writes are creates, which have no prior version |
| `app/reference/routes/results.py:64-65` mutating `result.is_critical` / `result.flagged` in a route | **not** an ORM write: `result` is a `LabResultDomain` in-memory object in an exception handler, serialised to the response. No optimistic-lock bypass |
| the 17 `/citizen-platform/{citizen_id}` routes | correctly authorized by the router-level dependency (see IA-002) |
