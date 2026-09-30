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
**137 tables** across every registry carry a column named `metadata` (RB-3 said 124,
which counted only `SHARED_METADATA`); every route
returning `to_dict()` on one of them is affected. Named examples outside EHR:
`ai_conversations`, `ai_agent_executions`, `ai_embeddings`, and the `cc_*`
care-continuum cluster. **The non-`/ehr` route count is UNKNOWN — not measured.**

**Impact.** Two failure modes. Where the encoder recurses, the endpoint 500s.
Where a serialiser tolerates the object, a clinical response silently carries a
schema registry in place of the record's own metadata — a wrong value presented as
data.

**Status: RESOLVED** — see `ia005-ia006-remediation.md` Part 1. One canonical
mapper-driven `serialize_columns()` in `shared/models/base.py`; the other 11 ORM
bases delegate to it (14 files, net −21 lines). The output key stays the physical
column name, so no response shape changed. Proven by
`tests/verification/test_orm_metadata_column_serialization.py`: 9 failed before,
13 passed after, 9 failed again on a one-line perturbation, 13 passed on restore.
119 of 119 affected models with a `to_dict()` now serialise safely with no schema
object anywhere in any payload; the `/ehr` code-path probe went from 27
`RecursionError`s to 1 (a harness limitation).

**Count corrected:** this entry first said 124 tables, which counted only
`SHARED_METADATA`. With every registry walked and the app assembled it is **137**
tables / 137 models, of which 119 have a `to_dict()`. Direction and severity were
right; the number was low.

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

**Status: OPEN, and deliberately without migrations.** `docs/adr/ADR-016-national-ehr.md`
(Status **Accepted**, 2026-07-15, not superseded) decides the opposite of what a
migration would build: *"Zero database duplication — **No new EHR tables**"*, and
*"Must not duplicate or replace existing GULA database tables."* Authoring 18
`ehr_*` migrations would implement precisely the data silo that accepted ADR
forbids.

The real contradiction is inside ADR-016: its Phase 2 mandates *"write support"*
for Condition / Medication / Immunization resources while also forbidding new EHR
tables, and it never says where a newly authored clinical note or allergy is
persisted — GULA's existing schema is lab-centric and cannot hold one. Phase 2 as
written is unsatisfiable under the ADR's own constraint. Either the constraint or
the phase must move, and that is an architecture-committee decision.

Classification of all 19 absent tables, on evidence: **A=0, B=0, C=1, D=0, E=18,
F=0**. Only class A may receive a migration and it is empty, so **none was
authored**. `ehr_patient_timeline` is class C — a projection with no projector
anywhere in `app/`. `national_patients` is class E with its own decision: hub of
66 foreign keys, while `nhop-platform` owns `citizens` per `CLAUDE.md` and ADR-016
composes the Patient from `patients`/`lab_results`/`lab_orders`/`visits`, never
from it. Full matrix in `ia005-ia006-remediation.md` Part 2.

IA-004 itself remains OPEN/P1 and was not modified.

---

## IA-007 — P1 — invoice generation crashes on the same `metadata` attribute collision

`app/insurance/financial/engine.py:840-842`:

```python
metadata = claim.metadata or {}          # the MetaData registry, and it is truthy
metadata["invoice_number"] = invoice_number
claim.metadata = metadata                 # never reaches the column
```

`InsuranceClaim` maps table `ins_claims`, whose physical `metadata` column is
mapped as `extra_metadata`. Executed, line 841 raises:

```
TypeError: 'MetaData' object does not support item assignment
```

So `generate_invoice()` cannot return, and `batch_invoices()` fails with it. Had
the assignment succeeded it would still have been lost: `claim.metadata = ...`
shadows a class attribute and never reaches the mapped column, so the following
`self._db.commit()` would persist no invoice number — the NR-064/065 shape again.

IA-005's fix does not reach this: direct attribute access never goes through
`to_dict()`. The repair is two identifiers (`claim.extra_metadata`), but invoice
generation is billing logic, which `CLAUDE.md` places behind human approval.

A systematic AST sweep over `app/` for the same shape found 13 other candidate
sites; **all 13 are correct** (`model.metadata_ = domain.metadata` in the national
platform repositories, reading a domain dataclass and writing the mapped
attribute). This is the one live instance found.

**Status:** OPEN, not fixed in this lane. Patch specified above.

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
| `integration/base.py::UplinkBase.to_dict()` and `research_platform/research.py`, both hard-coding `"metadata": self.metadata` | **not defects** — both classes are dataclasses, so `.metadata` is a genuine field |
| `governance/identity_governance.py::IdentityRecord.metadata[...]` and `rules_engine/api/routes.py:217` `rule.metadata = ...` | **not defects** — `IdentityRecord` and `RuleDefinition` are dataclasses |
| `document_intelligence/.../wiring.py:602` `field.metadata.get("unit")` | **not a defect** — `field` is an extracted-field domain object, not a mapped instance |
| the 13 `.metadata` sites in `app/national/*/infrastructure/repository.py` | **correct code** — each pairs `model.metadata_ =` with a read from a domain dataclass, which is how the contract is meant to be used |
| any physical column other than `metadata` whose name differs from its mapped attribute | **none** across all 780 mapped classes, and no column is unmapped — which is why the IA-005 fix has no collateral effect |

