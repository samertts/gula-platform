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

## IA-005 — P0 — `to_dict()` hands FastAPI the ORM schema registry instead of the column value

`shared/models/base.py:36` serialises by **column name**:

```python
for col in self.__table__.columns:
    val = getattr(self, col.name)
```

For a column literally named `metadata` the mapped Python attribute is
`metadata_`. So `getattr(self, "metadata")` does not read the column — it returns
the declarative base's `MetaData` registry (564 tables under `SHARED_METADATA`).
`jsonable_encoder` then walks that object graph until the stack is exhausted.

**Evidence.** Encoding one real `AllergyIntolerance` field-by-field, the only key
that recurses is `metadata`, `type=MetaData`, `repr=MetaData()`. A frame census on
`POST /ehr/allergies` shows 1 052 frames, 486 + 484 of them
`fastapi/encoders.py:307` / `:356` in `jsonable_encoder`.
`type(AllergyIntolerance.metadata).__name__ == "MetaData"` and it **is**
`SHARED_METADATA`.

**Not caused by NR-086.** `jsonable_encoder(MetaData())` on an empty registry
encodes fine, but a registry holding **one** table already recurses. NR-086
enlarged the walked object; the defect is independent of it and predates it.

**Exposure.** 59 of the 86 served `/ehr` operations (measured statically over the
AST; validated against runtime 4/4 including two negatives). Platform-wide,
**124 tables** in `SHARED_METADATA` carry a column named `metadata`; every route
returning `to_dict()` on one of them is affected. Named examples outside EHR:
`ai_conversations`, `ai_agent_executions`, `ai_embeddings`, and the `cc_*`
care-continuum cluster. **The non-`/ehr` route count is UNKNOWN — not measured.**

**Impact.** Two failure modes. Where the encoder recurses, the endpoint 500s.
Where a serialiser tolerates the object, a clinical response silently carries a
schema registry in place of the record's own metadata — a wrong value presented as
data.

**Status:** OPEN, deliberately not fixed in this lane. `shared/models/base.py` is
shared surface, and changing a serialiser used by 124 tables is an API
response-shape change, which `CLAUDE.md` puts behind human approval.

---

## IA-006 — P1 — 86 clinical operations are served over 19 tables that no migration creates

The `/ehr` surface depends on 18 `ehr_*` tables plus `national_patients`. None is
present in the RB-1 proven head database (423 tables, head `20260916_0001`), and
**none is created by any migration in the chain**. `national_patients` is named
once, at `20260811_0002_citizen_relationship_foundation.py:72`, only as a
foreign-key target inside an `if _has_table(target_table):` guard.

This is not a migration that failed, was skipped or was reverted — it was never
authored. The router is nonetheless registered unconditionally in
`factory.py:559`, behind no feature flag, so every deployment advertises 86
clinical operations that can only return `500`.

It is also the silent arm of IA-004: the FK to `national_patients` is skipped
without a trace because the target does not exist. RB-3 confirms IA-004
independently.

**Status:** OPEN. Remediation needs the schema-ownership decision RB-2 escalated,
and the options are set out in `rb3-ehr-surface-audit.md` §14. IA-004 itself
remains OPEN/P1 and was not fixed here.

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
