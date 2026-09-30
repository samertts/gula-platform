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

**Status: RESOLVED** — see `ia005-ia006-remediation.md` Part 1 **and
`ia005-ia006-addendum.md`**, which found five further live sites and corrected a
wrong conclusion this entry first recorded.

**Correction — `col.key` is not the mapped attribute.** This entry first reported
`app/nursing/routes.py::_model_to_dict` as immune because it reads
`getattr(instance, c.key)`. That was wrong: for `metadata_ = Column("metadata", ...)`
SQLAlchemy leaves **both** `col.name` and `col.key` as `"metadata"`, and only the
mapper carries `metadata_`. Measured: `type(getattr(NursingTask(), c.key))` is
`MetaData`. So `col.key` was equally defective, and the first guard — which matched
only `col.name` — passed it. The guard now matches both.

**Five further sites, all on tables that physically exist:**
`app/nhdw/offline.py:265` (offline device sync; **all 13** synced `nhdw_*` tables
carry the column), the three `_model_to_dict` helpers in `app/nursing/routes.py:40`,
`app/nhdw/routes.py:56` and `app/routes/hospital.py:264`, and the
`app/blood_bank/api/routes.py:638` fallback. All five now delegate to
`serialize_columns`, which gained `exclude` and `isoformat_dates` so each caller's
behaviour is preserved exactly. `app/contracts/generator.py:152` was checked and is
**not** a defect — it reads column types, never instance values.

This raises IA-005's real severity: the reachable blast radius was **not** mostly
the dormant `/ehr` surface. Offline clinical sync, nursing, hospital ward management
and blood bank all run on tables that exist, so these were live failures.

**Exposure, now measured rather than UNKNOWN:** of the 137 affected models, **34**
are HIGH risk (served endpoint + serializer), of which **10** sit on tables present
in the head database. Exposure spans `/nursing`, `/pharmacy`, `/care-continuum`,
`/fhir`, `/national-data`, `/citizen-platform`, `/radiology`, `/lims`, `/compliance`,
`/patient-card`, `/test-results`, `/authz`, `/admin`, `/health-data`,
`/intelligence`, `/public-health` — not just `/ehr`. Full matrix in
`ia005-impact-matrix.md`.

**Contract completed:** of 2 103 served operations only **135** declare a response
schema and **1 968** are untyped, so `to_dict()` *is* the response contract; `/ehr`
declares **0**. The 4 declared schemas with a metadata-ish property use
`safe_metadata`, a separate billing field. No JSON key changed anywhere — only the
value, from a schema registry to the column's value.

Original first-pass record follows. One canonical
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

**Severity corrected from P1 to P3, and reachability established** — the first report
asserted the failure without checking whether the code runs.

* `generate_invoice` has **no caller** except `batch_invoices`, which itself has no
  caller. No route, no service and no test invokes either. `InvoiceGenerator` is
  exported from `app/insurance/financial/__init__.py` and never used.
* `ins_claims` **does not exist** in the head database — the whole `ins_*` family is
  absent (only the unrelated `insurance_coverages` is present). So the model is one of
  the 371 absent-table models from RB-2.

So the `TypeError` is real and proven, but unreachable today. Calling it a live billing
failure was wrong. It is a latent defect that would become **silent data loss** the
moment the `ins_*` tables are migrated: even without the exception,
`claim.metadata = …` sets an instance attribute that never reaches the column, so the
following `commit()` would persist nothing.

**Status: FIXED.** `stamped = dict(claim.extra_metadata or {})` … `claim.extra_metadata
= stamped`, with a comment recording why. Business semantics were already established
by the surrounding code and needed no guess: the invoice dict is built entirely from
claim fields *before* these lines, so **no financial figure can move** — a test pins
that explicitly (`subtotal`, `allowed_amount`, `tax`, `total_with_tax`, `currency`).
`dict(...)` also stops the stamp mutating a caller's dict in place.

Proof: `backend/tests/verification/test_invoice_number_is_persisted.py`, 5 tests —
4 failed on the exact `TypeError` before the fix, 5 passed after, and perturbing the
two identifiers back reproduced the failure (`'MetaData' object is not iterable`).
The test needs no schema: the defect is attribute resolution, so a stub session stands
in for the absent tables.

---

## IA-004 — re-verified after new evidence — one arm CLOSED, one arm BLOCKED

Re-checked against `gula_agent2`, because the user asked and because new evidence appeared.
**IA-004's own migration was not modified.**

`20260811_0002_citizen_relationship_foundation.py` declared four FKs behind `_has_table`.
Physical state now:

| declared FK | target | present in head DB? |
|---|---|---|
| `fk_citizen_relationship_user` → `users` | exists | **yes, created** |
| `fk_citizen_relationship_lab_user` → `lab_users` | exists | **yes, created** |
| `fk_citizen_relationship_citizen` → `national_citizens` | absent | **superseded** — see below |
| `fk_citizen_relationship_patient` → `national_patients` | absent | **no FK on the column** |

**`citizen_id` arm: CLOSED — ALREADY_FIXED by Account 1, INDEPENDENTLY_VERIFIED here.**
`20260914_0001_citizen_relationship_person_fk.py` (NR-064) re-pointed it to `niam_persons`,
on NR-022's finding that a natural person is `niam_persons`. Both sides are `VARCHAR(26)`,
so the constraint is enforceable. Verified present in `gula_agent2` as
`fk_citizen_relationship_person (citizen_id -> niam_persons)`. That migration is **not in
this lane** (IA-008) — it exists only in the integration lineage.

**`patient_id` arm: BLOCKED architectural, owned by NR-022.** No FK exists on the column.
The migration author deliberately left it, and states why in the docstring — the built
clinical patient table keys on `INTEGER` against this `VARCHAR(26)` column, so there is no
target until NR-022 decides the clinical subject. This lane reached the same conclusion
independently from the physical schema; the convergence is recorded as corroboration, not
as a new finding.

**So IA-004 should no longer be carried as one item.** Its silent-skip *mechanism* remains
worth a guard (a migration that cannot create a declared FK should say so, not pass), but
its two concrete arms now have different states.

**Next action:** none for this lane. The `patient_id` arm moves to NR-022; the mechanism
question is Account 1's migration-policy call.

---

## IA-008 — P1 — this lane cannot measure ORM↔schema conformance, because the head database was built from a different lineage

`gula_agent2` was migrated from the integration lineage `ce097a0c`
(`claude/p0-2-pharmacy-reconciliation`). This lane is `claude/independent-audit-1`, based
on `claude/autonomous-run-1`. **176 commits exist in that lineage and not here**, and
every clinical domain diverges (`national/` 282 differing files, `identity/` 193,
`nursing/` 17, `ehr/` 17, `pharmacy/` 14, `nhdw/` 13). Migrations differ too: 102 here
versus 112 there.

**Consequence:** any comparison of *this lane's ORM* against *that database* is a
cross-lane comparison and is not evidence about the platform.

**A finding this produced, and its retraction.** Measuring this lane's pharmacy ORM
against `gula_agent2` showed 216 ORM columns the tables lack, 228 physical columns the
ORM ignores, 178 type mismatches, and all 27 pharmacy tables unwritable — with
`pharmacy_prescriptions.patient_id` declared `String(26) → national_patients.id` against
a physical `INTEGER → patients.id`. That reads as a P0.

**It is not a platform defect and is retracted as such.** The integration lineage's own
`app/pharmacy/models.py` already declares `Column(Integer, nullable=True)` and is 1 292
lines against this lane's 954. The drift is this lane lacking the pharmacy
reconciliation (`20260910_0001`…`20260916_0001`, ten migrations). Caught before it was
written up as a defect, by diffing the two worktrees.

**What is genuinely true and actionable:** schema-conformance audits in this programme
must be run on the lineage that produced the database under test. Running them here
produces false positives at scale.

**Correction to IA-005's report.** That report said 10 affected models sat on tables
present in the head DB and were therefore *live* failures. The four pharmacy ones
(`pharmacy_prescriptions`, `pharmacy_stock_levels`, `pharmacy_stores`,
`pharmacy_warehouses`) are lane-dependent: in this lane those endpoints cannot work at
all for unrelated reasons. The IA-005 **fix** is unaffected — it resolves a Python
attribute through the mapper and touches neither schema nor dialect — and its test and
serializer-level evidence stand. Only the word "live" was overstated for those four.
The nursing and nhdw sites remain live: both domains are conformant on the matched pair.

**Status:** OPEN as a methodology constraint. No code change. The remedy is procedural.

---

## IA-009 — P1 — 26 physically present tables cannot be written through the ORM, measured on the matched lineage pair

Measured correctly this time: integration lineage `ce097a0c` against `gula_agent2`
(head `20260916_0001`), which is the matched pair.

| | value |
|---|---|
| mapped tables | 780 |
| present in head DB | 409 |
| absent | 371 (RB-2's figure, confirmed on the matched pair) |
| **present but unwritable** (≥1 ORM column the table lacks) | **26** |
| ORM columns absent physically | **293** |

Concentrated in two domains nobody has claimed:

| domain | present | unwritable |
|---|---|---|
| `radiology_*` | 17 | **17 of 17** |
| `nhdw_*` | 14 | **9 shown, 14 flagged** |
| `fin_*` | 3 | 3 |

Worst offenders: `radiology_reports` (17 ORM columns missing), `nhdw_transfers` (15, of
which **3 NOT NULL without a default**), `radiology_dicom_storage` (15, **4 NOT NULL**),
`nhdw_queue_entries` (13, 2 NOT NULL). A NOT NULL ORM column that the table lacks means
the insert fails outright, not silently.

The most frequently missing columns are base-mixin fields — `extra_metadata` (17
tables), `extension` (14), `metadata` (13), `fhir_id`/`fhir_resource_type` (7 each),
`version` (6), `is_deleted`/`deleted_at` (5 each) — plus real domain columns
(`department_id` 8, `encounter_id` 7). So the migrations created these tables without
the base entity columns their models declare.

This is the same shape as RB-5 (nursing, 15 tables) but in **radiology and nhdw**, and
unlike RB-5 every table here physically exists. It also intersects IA-005: the
`nhdw/offline.py` offline-sync serialiser reads 13 `nhdw_*` tables, and those tables
cannot hold the rows the ORM expects.

**Not fixed here.** Reconciling 26 tables is a schema decision of the scale RB-2
escalated, it is in a different lineage from this worktree (IA-008), and it belongs to
whoever owns radiology and nhdw. **Status: OPEN, evidence complete, awaiting owner.**

---

## IA-010 — P2 — NEEDS_DECISION — the audit chain resists modification but not the insertion of unverifiable rows

**What was verified to work, first.** The audit trail has genuinely strong controls, and
this is positive evidence the programme has little of:

* `audit_logs` is **append-only at the database level**. Two triggers,
  `trg_audit_logs_no_update` and `trg_audit_logs_no_delete`, call
  `audit_logs_deny_mutation()` which raises
  `audit_logs is append-only: UPDATE operation is not permitted`. A probe that tried to
  overwrite one row's `chain_hash` was refused by PostgreSQL, not by application code.
  **RUNTIME VERIFIED** against `gula_agent2`.
* the chain itself is soundly built: SHA-256 over the previous hash plus a canonical
  record, dialect-independent UTC timestamps so write-time and verify-time hashes agree,
  and HMAC-signed anchor files.
* `tests/test_compliance_integrity.py` already covers field tampering and silent record
  deletion.

**The gap.** `verify_audit_chain` (`app/services/audit_service.py:238`) skips any row
whose `chain_hash` is NULL:

```python
for entry in entries:
    if entry.chain_hash is None:
        prev_hash = entry.chain_hash or prev_hash   # carries the previous hash forward
        continue
```

so an unhashed row is counted but never validated, and it does not break the chain for
the rows after it. Proven at runtime against `gula_agent2`, everything rolled back:

| state | verifier says |
|---|---|
| 3 rows written through `log_action` | `status=intact verified=True checked=3` |
| + 1 row inserted with `chain_hash = NULL` | `status=intact verified=True checked=4 broken=0` |

The table held 4 rows, one with a NULL hash, and the verifier called it **intact**. So
history cannot be *altered* — the triggers prevent that — but it can be *appended to
unverifiably*, and the verification that exists to detect that reports success.

**Why this is not a mechanical fix.** `chain_hash` has been nullable since
`20250322_0000_create_base_schema.py`, and `20260324_0009_audit_chain_hash_result_engine_version.py`
added it to already-populated databases. **Pre-chain historical rows therefore have NULL
legitimately.** Failing on NULL would report every upgraded deployment as tampered for
all of its pre-2026-03-24 history. Skipping NULL is a deliberate backward-compatibility
choice, not an oversight.

**The decision required:** what marks the boundary between legacy unhashed rows and rows
that must be hashed? The remedy shape follows from the answer — record, per deployment,
the first chained `audit_logs.id` (or the chain's start timestamp), treat NULL below that
boundary as legacy and NULL at or above it as a chain break. That boundary is deployment
data this lane cannot determine.

**Exposure today:** low. `app/services/audit_service.py:203` is the only site
constructing the canonical `AuditLog`, and it always assigns a hash; the other
`*AuditLog` classes found (`PortalAuditLog`, `PartnerAuditLog`, `TaskAuditLog`,
`IdentityAuditLog`) are different models on different tables. So no current code path
produces a NULL hash. The risk is a future direct write, a partial failure, or anyone
with database write access.

**Also missing:** no test covers the NULL case. The guard to add alongside the fix:

```python
# once the legacy boundary is known
report = verify_audit_chain(db)
assert not report["verified"], "an unhashed row at or above the chain boundary must break verification"
```

**Status:** OPEN / NEEDS_DECISION. Not fixed — the legacy boundary is a data decision,
and changing the verifier without it would turn every upgraded database red.

---

## IA-011 — P2 — NEEDS_DECISION — two FHIR Observation builders with different contracts, and no canonical lab-result flag vocabulary

FHIR contract audit of **path A** (lab data → FHIR), the one FHIR path whose source
tables exist and therefore the one that could ship for v1.0.0. Investigation only.

### The root cause: `lab_results.flag` has no agreed vocabulary

Measured across the writers:

| value written | written by |
|---|---|
| `"H"`, `"L"`, `"N"` | `app/lims/integration/simulator.py:82,84` — the analyser path |
| `"unknown"` | `app/services/order_service.py:405`, `app/routes/test_results.py:351` |
| `"normal"`, `"H"` | `app/core/bootstrap/demo_data.py:192` |
| `""` | `app/lims/integration/simulator.py:124` |
| `"critical"` | queried at `app/routes/stats.py:113` |

There is no enum, no constant, and no validation. Both defects below follow from this.

### Builder A — served, and non-conformant for some flags

`app/routes/ehr_fhir.py:388` `_lab_result_to_observation` is the one an endpoint reaches.
It passes the raw flag through as both code and display inside a declared HL7 system:

```python
obs["interpretation"] = [_codeable_concept(result.flag, result.flag,
    "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation")]
```

**RUNTIME VERIFIED** per flag:

| flag | emitted code | valid `v3-ObservationInterpretation`? |
|---|---|---|
| `H`, `L`, `N` | `H`, `L`, `N` | **yes** — correct |
| `critical`, `unknown`, `normal`, `high`, `critical_high` | passed through verbatim | **no — non-conformant** |
| `""` | none emitted | n/a, the branch is skipped |

So a consumer receives an unrecognised code inside a system it trusts. Its timestamps
are correct (`_fmt_fhir_datetime` yields `2026-01-01T12:00:00`). Severity **P2,
conformance** — not a clinical inversion.

### Builder B — not served, and it would invert clinical meaning

`app/national/fhir/observation.py:42` `FHIRObservationMapper.from_lab_result` defaults
every unrecognised flag to Normal:

```python
mapping = {"high": "H", "low": "L", "critical_high": "HH", "critical_low": "LL", "normal": "N"}
return [{"coding": [{"code": mapping.get(flag, "N"), ...}]}]
```

Its keys are the long lowercase forms, which almost nothing writes. **RUNTIME VERIFIED:**
`H` → `N`, `L` → `N`, `critical` → `N`. A full Observation built from a realistic row —
glucose 180 mg/dL, reference range 70–110, analyser flag `H` — is emitted as
**interpretation Normal**.

Three further defects in the same builder:

* `code.coding[0].code` comes from `result.get("test_code")`, and **`lab_results` has no
  `test_code` column** — it lives on `test_types`, one join away. The emitted LOINC code
  is `""`.
* `"issued": str(result.get("created_at"))` yields `2026-01-01 12:00:00` — a space, not
  `T`. Invalid FHIR `instant`.
* `value_text` is never read, so qualitative results (Positive/Negative) are silently
  dropped; and `_build_reference_range` can emit `{"low": null, …}`, which FHIR JSON
  does not permit.

**It has no production caller.** Only `app/fhir/__init__.py` and
`app/national/fhir/__init__.py` re-export it, and one unit test
(`app/national/tests/unit/test_fhir.py:113`) calls it. So the clinical inversion is
**latent, in unreached code** — severity **P2**, not P0. Saying otherwise would repeat
the IA-007 mistake of asserting a failure without establishing reachability.

The danger is that it looks like the canonical mapper: it sits in `app/national/fhir/`
alongside the ten mappers that *are* wired up, and it is exported from two packages.
Whoever wires it up inherits a builder that reports abnormal results as normal.

### The decision required

Three things, none of which this lane may guess — mapping a flag to a clinical
interpretation is exactly the semantics prohibition:

1. **What is the canonical `lab_results.flag` vocabulary?** Today four writers disagree.
2. **How does each value map to `v3-ObservationInterpretation`?** `H`/`L`/`N` are
   already right. `critical` could be `HH`, `LL`, `AA` or `A` depending on what it means,
   and `unknown` has no interpretation code at all — it may warrant emitting none.
3. **Which builder is canonical?** Two exist with different contracts; one is served and
   one is exported but unreached. Keeping both guarantees they drift again.

**Status:** OPEN / NEEDS_DECISION. Nothing changed. A safe fix is not available without
(1) and (2), and deleting a builder is a deletion this lane does not take.

---

## IA-012 — P2 — CONFIRMED_DEFECT — a served pharmacy read declares a string patient id against an INTEGER column

**Found in the lineage that ships**, not in this lane — so unlike the retracted pharmacy
drift (IA-008) this one is real where it counts.

| field | value |
|---|---|
| **ID** | IA-012 |
| **severity** | P2 |
| **state** | CONFIRMED_DEFECT (RUNTIME_VERIFIED) — not fixed |
| **file** | `backend/app/pharmacy/routes.py:1262-1264`, lineage `ce097a0c` |
| **symbol / route** | `get_dispense_records` — `GET /pharmacy/dispense/dispense-records/{patient_id}` |
| **owner** | **Account 1** (pharmacy is their active area) |

**Reproduction**, against `gula_agent2`, ORM `DispenseRecord.patient_id` is `INTEGER`:

| filter value | result |
|---|---|
| `"5"` (numeric string) | OK, 0 rows — PostgreSQL assignment-casts it |
| `"01ARZ3NDEKTSV4RRFFQ69G5FAV"` (ULID) | **`DataError: (psycopg2.errors.InvalidTextRepresentation) invalid input syntax for type integer`** |
| `5` (int) | OK, 0 rows |

The path parameter is declared `patient_id: str`, and the served OpenAPI schema confirms
`('patient_id', 'string')`. So any caller passing a national/ULID patient id gets an
unhandled `DataError` — a 500, where 404 or 422 is the correct answer.

**Why it is live and not cross-lane.** The rest of the pharmacy write surface in that same
lineage correctly declares `patient_id: int | None`. The file is split **5 `str` against 5
`int`**, and this is one of the `str` sites on a served route.

**Affected data / users:** read-only, no data loss and no cross-tenant exposure — the
query still filters by the service's own scope. The impact is availability and contract
correctness: a documented endpoint answers 500 for an id shape the platform itself mints
elsewhere (`POSSaleCreate.patient_id: str | None`).

**Existing mitigation:** none found. No `DataError` handler converts it to 4xx.

**Tests:** none cover this route with a non-numeric id.

**Architectural dependency:** the correct declared type follows from **NR-022** — if the
clinical subject becomes `patients.id INTEGER`, this should be `int`; if it becomes a ULID
table, the column changes instead. So the *type* is NR-022's, but **rejecting a
non-integer with 422 rather than 500 is correct under either outcome**.

**Next action:** Account 1 — either declare `patient_id: int` (FastAPI then answers 422
automatically) or validate and return 404. This lane did not change it: pharmacy routes are
Account 1's active area and the file is theirs.

---

## IA-013 — P1 — CONFIRMED_DEFECT — the kernel event bus loses events silently while presenting outbox, retry and dead-letter APIs

| field | value |
|---|---|
| **ID** | IA-013 |
| **severity** | P1 |
| **state** | CONFIRMED_DEFECT (RUNTIME_VERIFIED); not fixed |
| **files** | `backend/app/kernel/event_bus/bus.py:40-42`, `dispatcher.py:13-24`, `outbox.py:31`, `store.py:12`, `retry_queue.py:23` |
| **symbol** | `EventBus.publish`, `EventDispatcher.dispatch` |
| **owner** | **Human decision** (which events may be lost) + Account 2 implementation once decided |

### What it does

`EventBus.publish` is two lines: save to an in-memory store, then dispatch to subscribers.

```python
def publish(self, event: Event) -> None:
    self.store.save(event)
    self.dispatcher.dispatch(event, self._subscribers.get(event.name, []))
```

The bus constructs `OutboxPattern`, `InboxPattern`, `RetryQueue`, `DeadLetterQueue`,
`RecoveryEngine`, `EventReplay`, `SnapshotEngine` and `EventVersioning` in `__init__` —
**and `publish` uses none of them.** `EventDispatcher.dispatch` catches every handler
exception into a log line, so a failed handler is neither retried nor dead-lettered. Async
handlers are fire-and-forget: `asyncio.create_task(result)` with a done-callback that only
logs, so the task is never awaited or tracked.

Every store is a plain Python container: `EventStore._events: dict`,
`OutboxPattern._messages: list`, `RetryQueue._entries: list`. Nothing is durable, and
`EventStore` is never evicted.

### Reproduction — RUNTIME VERIFIED

```
5 × publish("probe.ok")      -> handler invoked 5 times
1 × publish("probe.fail")    -> handler invoked, raised RuntimeError
retry_queue entries          : 0
dead_letter_queue entries    : 0
outbox messages              : 0    (publish never enqueues)
inbox entries                : 0
EventStore after 6 publishes : 6
EventStore after 506         : 506  -> unbounded
```

The failed event is in **no** queue. Delivery is at-most-once, in-process, non-durable,
and `EventStore` grows without bound — a memory leak on any hot publish path.

### Reachability — it is live, not scaffolding

**Publishers (8+):** `app/kernel/runtime_sdk.py:101` (plugin API) and `:277` (SDK), plus six
national services — `rules_engine`, `observability`, `document_platform`,
`scheduling_platform`, `background_platform`, `search_platform`, each holding this exact
`EventBus`. **`search_platform`'s tables are present** in the head DB
(`national_search_results`, `national_search_saved_searches`), so at least one publisher
sits on live schema.

**CORRECTION (2026-09-30, during IA-014/IA-015/IA-016).** The original text of this
finding claimed kernel-bus subscribers exist and cited two sites. Both citations were
wrong, and I withdraw the claim:

- `app/identity/events.py` does **not** use the kernel bus. It defines its own 20-line
  `IdentityEventBus` with its own `_handlers` dict and a different signature
  (`publish(event_type, payload)` vs the kernel's `publish(event)`). Its three handlers
  never touch `app.kernel.event_bus`.
- `app/health_data/streaming/pipeline.py:35` does subscribe on a kernel `EventBus`, but
  the subscription lives in `EventBusSource.start()`, and `EventBusSource` has **zero
  construction sites** anywhere in the repository. It never runs.

Measured correctly: **there are no kernel-`EventBus` subscribers in production code at
all.** Every `.subscribe()` on a kernel bus in the tree is inside `backend/tests/`.

This makes the finding *worse*, not better, but differently worse than I first wrote.
No handler can fail, because no handler is registered — so the failure mode is not
"a handler raises and the event is dropped", it is "every publish in the platform is
delivered to nobody." The retry/DLQ gap below is still real, but it is currently
unreachable for want of a subscriber; the *delivery* gap is what is live.

### The architectural duplication

GULA already has a **durable** outbox, and it is the one the important paths use:
`app/services/outbox_service.py`, backed by the **present** `outbox_events` table, with
`OutboxWorker` started at `app/worker.py:86` and `app/core/startup.py:270`, and
`emit_to_outbox` called from `claims_service`, `data_platform_service` and
`routes/national_streaming.py`.

So there are two event systems: a durable DB-backed one for claims, data platform and
national streaming, and this in-memory one for identity and health-data streaming. The
weaker one carries the identity events.

### Impact

* **affected data:** any event published on the kernel bus whose handler fails, or any
  event in flight at shutdown. Identity lifecycle events (`person.created`,
  `account.created`, `identity.verified`) are on this bus.
* **affected users/tenants:** not tenant-scoped — the bus has no tenant concept at all,
  which is itself worth noting for a multi-tenant platform.
* **integrity impact:** a consumer can miss a state transition with no trace beyond a log
  line, and no mechanism exists to detect or replay the gap. `EventReplay` and
  `RecoveryEngine` operate on the in-memory store, so they cannot recover across a restart.
* **availability impact:** unbounded `EventStore` growth.
* **existing mitigation:** none on this bus. The durable outbox mitigates only the paths
  that use it, which are different paths.
* **tests:** none found asserting delivery, retry or dead-lettering on the kernel bus.

### Next action — decision first, then implementation

Not fixed, because the fix depends on a question this lane must not answer: **which of the
events on the kernel bus are load-bearing?**

* if identity lifecycle events must not be lost → they belong on the durable
  `outbox_service`, and the kernel bus should either delegate to it or be removed;
* if they are advisory only → the bus is adequate, but the `OutboxPattern`,
  `RetryQueue` and `DeadLetterQueue` APIs should be removed rather than left implying a
  guarantee they do not provide.

Either way, two independent findings can be fixed without the decision: `publish` should
not construct eight unused components, and `EventStore` needs eviction.

**Status:** OPEN. Decision required on event criticality; implementation is Account 2's
once decided.

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
| the 216/228/178 pharmacy drift measured in this lane | **retracted** — cross-lane artefact, see IA-008; the integration lineage's pharmacy ORM is already reconciled |
| pharmacy and nursing conformance on the matched pair | **clean** — neither appears among the 26 unwritable tables |
| `audit_logs` resistance to UPDATE and DELETE | **verified present and effective** — PostgreSQL triggers `trg_audit_logs_no_update` / `trg_audit_logs_no_delete` refuse both; an attempted overwrite was rejected by the database |
| the audit chain's hash construction | **sound** — SHA-256 over previous hash + canonical record, UTC-normalised so write and verify agree, with HMAC-signed anchors |
| other `*AuditLog` models as NULL-hash sources | **not sources** — `PortalAuditLog`, `PartnerAuditLog`, `TaskAuditLog` and `IdentityAuditLog` are separate models on separate tables, outside the canonical chain |
| the served Observation builder's timestamps | **correct** — `_fmt_fhir_datetime` emits ISO-8601 with `T`, unlike the unreached builder |
| the served Observation builder's `H`/`L`/`N` interpretations | **correct and conformant** v3-ObservationInterpretation codes |
| `FHIRObservationMapper.from_lab_result` reachability | **no production caller** — two `__init__` re-exports and one unit test; the clinical inversion is latent, not live |
| `app/services/outbox_service.py` — the DB-backed outbox | **real and wired** — `outbox_events` present, `OutboxWorker` started from both `worker.py` and `core/startup.py`, `emit_to_outbox` used by claims, data platform and national streaming |
| kernel-bus subscribers | **none exist in production code** — WITHDRAWN AND CORRECTED, see the correction note in IA-013. `identity/events.py` uses a separate `IdentityEventBus` class; `EventBusSource` (the only kernel-bus subscriber) is never constructed. Every kernel-bus `.subscribe()` in the tree is in `backend/tests/`. |


---

## IA-014 — P2 — CONFIRMED_DEFECT — two served admin endpoints report the event pipeline as healthy by construction

| Field | Value |
|---|---|
| **ID** | IA-014 |
| **Severity** | P2 (false-green observability; no data loss of its own) |
| **State** | CONFIRMED_DEFECT — RUNTIME VERIFIED — **not fixed**, needs a response-shape decision |
| **File** | `backend/app/kernel/routes.py:112-138` |
| **Symbol / route** | `kernel_outbox` → `GET /kernel/events/outbox`; `kernel_dead_letter_queue` → `GET /kernel/events/dlq` |
| **Owner** | Human Decision (response shape) |

### What it is

Both endpoints are served (confirmed in the app's own OpenAPI schema, 1794 paths) and
both are gated on `require_permission("system:admin")`, so they are operator-facing:

```python
pending = len(eb.outbox.list_pending())      # /kernel/events/outbox
for entry in eb.dead_letter_queue.list_all() # /kernel/events/dlq
```

`EventBus.publish()` writes to neither `outbox` nor `dead_letter_queue` (IA-013). So both
endpoints return a hard-coded-by-construction zero for the life of the process, no matter
what happens to any event.

### Evidence — RUNTIME VERIFIED, in-process, no DB

Registered a handler that raises, published 10 events into it, then read exactly what the
two endpoints read:

```
failing handler invocations                  : 10
outbox pending (what /events/outbox reports) : 0
dlq entries  (what /events/dlq reports)      : 0
retry_queue entries                          : 0
```

### Why this is not just a restatement of IA-013

IA-013 is about events being lost. IA-014 is about the **operator's only view of that loss
reporting the opposite.** An admin watching `/kernel/events/dlq` for trouble sees a
permanently empty dead-letter queue and concludes the event pipeline is healthy. That is
the false-green pattern the standing rules forbid, on a monitoring surface.

### Correction to my own earlier note

In the IA-013 report I listed "`publish` should not construct eight unused components" as
safe, unblocked work. **That was wrong and I am withdrawing it.** Two of the eight —
`outbox` and `dead_letter_queue` — are read by these two served admin endpoints. Deleting
them would delete the only operator-facing view of the event pipeline and turn a
misreporting endpoint into a 500. They are not *unused*; they are **read but never
written**, which is precisely the defect. The correct disposition is to wire the writes or
to make the endpoints state their own wiring — not to remove the components.

### Why I did not fix it

The honest fix is for each endpoint to report that the outbox is not wired, rather than
report `0`. That changes a served response shape, which `CLAUDE.md` places under "Requires
human approval". Two shapes are defensible (`{"pending": 0, "wired": false}` vs. a 501),
and picking one is the committee's call, not mine. Pinned by
`test_documented_gap_admin_endpoints_read_components_publish_never_writes`.

### Next action

Decide the response shape for an unwired pipeline. Blocked by the IA-013 decision: if
`publish` is wired to the outbox, IA-014 closes on its own.

---

## IA-015 — P2 — CONFIRMED_DEFECT — FIXED — six served route groups published onto a throwaway event bus

| Field | Value |
|---|---|
| **ID** | IA-015 |
| **Severity** | P2 (no clinical data loss — the bus has no subscribers; wasted work and a dead branch on 115 served operations) |
| **State** | CONFIRMED_DEFECT → **FIXED** — RUNTIME VERIFIED + TEST VERIFIED with negative proof both directions |
| **Files** | `app/national/{rules_engine,observability,document_platform,scheduling_platform,background_platform,search_platform}/api/routes.py` |
| **Symbol** | `_get_service` (the FastAPI dependency provider in each) |
| **Owner** | Account 2 — done |

### Root cause

All six resolved the bus with the same line:

```python
event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else EventBus(kernel)
```

`Kernel` keeps its subsystems in `self._components` and hands them out through
`get_component()`. It **never** assigns them as attributes. The bootloader registers the
bus with `self.kernel.register_component("event_bus", eb)`. So `hasattr(kernel,
"event_bus")` is False for the entire life of the process — before boot, after boot, and
after registration — and the preferred branch is unreachable code. Every request took the
fallback, built a fresh `EventBus`, published into it, and dropped it at end of request.

### Evidence — RUNTIME VERIFIED

```
hasattr(kernel, 'event_bus')       : False
kernel.__dict__ keys               : ['_components','_services','_start_time','config','state']
after register_component, hasattr  : False          <- registration does not create the attribute
get_component('event_bus') is bus  : True
chosen is the registered bus       : False
chosen is a fresh throwaway bus    : True
throwaway bus subscribers          : {}
throwaway bus still alive after req: False          <- garbage-collected with the request
```

### Blast radius — measured against the served OpenAPI schema

| Module | Prefix | Served paths | Served ops building a bus |
|---|---|---|---|
| rules_engine | `/national/rules` | 11 | 13 |
| observability | `/national/observability` | 19 | 26 |
| document_platform | `/national/documents` | 14 | 18 |
| scheduling_platform | `/national/scheduling` | 20 | 27 |
| background_platform | `/national/jobs` | 14 | 17 |
| search_platform | `/national/search` | 11 | 14 |
| **Total** | | **89** | **115** |

### The fix

One canonical resolver, `resolve_event_bus(kernel)` in `app/kernel/event_bus/bus.py`,
which asks `get_component("event_bus")` and falls back to a standalone bus only when the
kernel genuinely has none (`enable_event_bus=False`, or a pre-boot kernel). Each of the
six modules gained a three-line `_resolve_event_bus` wrapper that keeps the existing
lazy-import discipline, and the dead `hasattr` branch and its now-unused `EventBus` import
were removed.

### Coupling: this fix required IA-013a

Repairing the probe means 115 served operations now publish onto the **process-wide**
bus instead of a per-request one. With `EventStore` unbounded, that converts a
per-request throwaway dict into a process-lifetime leak. The `EventStore` bound below is
therefore a **precondition** of this fix, not an independent tidy-up. Both landed
together.

### Honest limit on the benefit

Because there are no kernel-bus subscribers at all (see the IA-013 correction), this fix
changes nothing observable today beyond bounded memory and a working guard. Its value is
that the branch the author wrote now actually runs, and that any future subscriber will
receive events rather than watching them vanish. I am not claiming a delivery improvement
that no subscriber can observe.

### Negative proof

```
BASELINE (before fix)  : 13 failed, 3 passed
AFTER fix              : 17 passed
REVERT store.py bound  :  5 failed (all four bound tests + the bus-usability test)
RESTORE                : 17 passed
REVERT search_platform :  3 failed (its behavioural test, the spread guard, the fallback test)
RESTORE                : 17 passed
```

---

## IA-016 — P1 — CONFIRMED_DEFECT — NOT FIXED — 130 served operations pass `event_bus=None` permanently, and the obvious repair breaks clinical routes

| Field | Value |
|---|---|
| **ID** | IA-016 |
| **Severity** | P1 — **as a trap**, not as a live failure. Nothing fails today; the plausible one-line fix causes `AttributeError` on served clinical write paths. |
| **State** | CONFIRMED_DEFECT — RUNTIME VERIFIED — **deliberately not fixed** |
| **Files** | `app/{biomedical,blood_bank,command_center,critical_care,ems,lifecycle_platform,pilot_platform,public_health}/api/routes.py` |
| **Symbol** | `_get_service` in each; `<Service>._emit` in the matching `application/service.py` |
| **Owner** | Human Decision |

### What it is

These eight carry the same unsatisfiable probe as IA-015, but with a **different
fallback**:

```python
event_bus = kernel.event_bus if hasattr(kernel, "event_bus") else None
```

So `event_bus` is always `None`. The services are typed `event_bus: Any = None` and emit
through:

```python
def _emit(self, event) -> None:
    if self.event_bus:
        self.event_bus.emit(event.event_type, event.__dict__)
```

The guard is always False, so `_emit` is a permanent no-op and every domain event in these
eight domains is discarded before it reaches anything.

### The trap

The kernel `EventBus` public API is `publish` / `subscribe` / `unsubscribe`. **There is no
`emit`.** So the moment anyone repairs the probe the way IA-015 was repaired, `if
self.event_bus:` becomes True and `.emit()` raises `AttributeError` — on served clinical
routes.

### Evidence — RUNTIME VERIFIED

```
kernel EventBus public API: ['publish', 'subscribe', 'unsubscribe']
hasattr(bus, 'emit')      : False

public_health  event_bus=None  -> _emit() silently no-ops (event lost)
public_health  event_bus=BUS   -> AttributeError: 'EventBus' object has no attribute 'emit'   <-- REGRESSION
blood_bank     event_bus=None  -> _emit() silently no-ops (event lost)
blood_bank     event_bus=BUS   -> AttributeError: 'EventBus' object has no attribute 'emit'   <-- REGRESSION
critical_care  event_bus=None  -> _emit() silently no-ops (event lost)
critical_care  event_bus=BUS   -> AttributeError: 'EventBus' object has no attribute 'emit'   <-- REGRESSION
```

### Blast radius — measured against the served OpenAPI schema

| Module | Prefix | Served paths | Served ops passing `event_bus=None` |
|---|---|---|---|
| biomedical | `/biomedical` | 17 | 20 |
| blood_bank | `/blood-bank` | 29 | 11 |
| command_center | `/command-center` | 9 | 12 |
| critical_care | `/critical-care` | 20 | 12 |
| ems | `/ems` | 21 | 25 |
| lifecycle_platform | `/lifecycle` | 15 | 18 |
| pilot_platform | `/pilot-platform` | 13 | 14 |
| public_health | `/public-health` | 14 | 18 |
| **Total** | | **138** | **130** |

Four of the eight are clinical or emergency domains: blood bank, critical care, EMS,
public-health surveillance.

### Why I did not fix it

Two protocols are in the tree (`publish(Event)` and `emit(name, dict)`) and choosing which
one the kernel bus speaks is an architecture decision with a real blast radius. Options,
not recommendations:

- **A.** Adapt at the boundary: inject a thin adapter exposing `emit(name, dict)` that
  builds an `Event` and calls `publish`. Smallest change; leaves two protocols alive.
- **B.** Add `emit` to the kernel `EventBus` as an alias. Simple; blesses a second public
  protocol on the kernel's own API.
- **C.** Convert the eight services to `publish(Event)`. Cleanest end state; touches eight
  service modules including four clinical ones, so it needs its own test pass.

None of these can be chosen without also settling IA-013 (does the kernel bus deliver
durably?), because option C's value depends on the answer.

### How the finding is protected from a well-meaning fix

`test_the_hasattr_event_bus_probe_has_not_spread` pins the offender set to exactly these
eight files with a comment pointing here, so:

- a **ninth** module growing the probe fails the test;
- one of the eight **disappearing** fails the test, forcing whoever repaired it to read
  IA-016 and confirm they did more than flip the probe.

`test_documented_gap_emit_protocol_services_cannot_accept_the_kernel_bus` asserts
`not hasattr(EventBus, "emit")`, so if someone takes option B the test fails and points at
this finding for closure.

I deliberately did **not** write a guard demanding these eight be repaired. A guard that
pressures an engineer into a change I have runtime proof breaks clinical routes would be
worse than no guard.

### Next action

Committee picks A, B or C, jointly with the IA-013 decision.

---

## IA-013a — P2 — CONFIRMED_DEFECT — FIXED — the kernel EventStore grew without bound

| Field | Value |
|---|---|
| **ID** | IA-013a (sub-item of IA-013, independently fixable) |
| **Severity** | P2 — unbounded memory on a process-lifetime singleton |
| **State** | CONFIRMED_DEFECT → **FIXED** — TEST VERIFIED with negative proof |
| **File** | `backend/app/kernel/event_bus/store.py` |
| **Symbol** | `EventStore.__init__`, `EventStore.save` |
| **Owner** | Account 2 — done |

`EventStore` was a plain `dict` with no eviction. Measured before the fix: 506 events
retained after 506 publishes, growing linearly forever. The store is held by the kernel's
process-wide bus, so this is a worker-lifetime leak, and it is what made the IA-015 repair
unsafe until fixed.

Fixed with `DEFAULT_MAX_EVENTS = 10_000` and oldest-first eviction, plus an
`evicted_count` property and a one-time warning when the bound is first reached.

**Collateral check — STATIC VERIFIED.** Nothing in `app/` reads the kernel `EventStore`
except `bus.publish` → `store.save`. `grep` for `.store.`, `list_by_name` and
`KernelEventStore` across `app/` returns only `bus.py:41`. `HealthEventStore` accepts a
`kernel_store` argument but keeps its own dicts and never reads it, and
`app/health_data/event_store/subscriptions.py` replays from `HealthEventStore`, not from
the kernel store. So bounding the kernel store cannot truncate anything another component
depends on.

---

## IA-017 — P2 — CONFIRMED_DEFECT — the served offline-sync endpoint cannot sync anything, and reports itself active

| Field | Value |
|---|---|
| **ID** | IA-017 |
| **Severity** | P2 — no data loss today (nothing reaches it); false capability + false health on an admin surface. One method is a latent fake-green write-discard. |
| **State** | CONFIRMED_DEFECT — RUNTIME VERIFIED — not fixed (disposition is a decision, see below) |
| **File** | `backend/app/integration/offline.py`; `backend/app/integration/routes.py:250`; `backend/app/platform/sync.py` |
| **Symbol / route** | `OfflineSyncEngine.sync_all` → `POST /integration/offline/sync`; `EdgeSyncEngine.sync_to_edge`; `ConflictResolver.resolve` |
| **Auth** | `require_permission("system:admin")` at router level — **correctly gated**, 401 without a token (verified) |
| **Owner** | Human Decision (retire vs. wire) |

### Reachability — measured, not assumed

The whole platform serves exactly **one** offline-sync path. From the served OpenAPI schema
(1794 paths): `sync` matches 3 paths, of which `/compliance/time-sync` and
`/contracts/asyncapi.json` are unrelated, leaving **`POST /integration/offline/sync`**.
`offline` matches 2, the second being `/lims/instruments/{id}/offline`, a different feature.

`configure()` **is** called — `IntegrationPlatform.register_routes` invokes it — so the
engine is live at import time, not `None`:

```
AFTER IMPORT  _offline_sync is: <app.integration.offline.OfflineSyncEngine object ...>
AFTER STARTUP _offline_sync is: <same object>
POST /integration/offline/sync (no auth) -> 401 AUTHENTICATION_REQUIRED
```

### What the endpoint does — RUNTIME VERIFIED

```
sync_all() -> {'synced': 0, 'failed': 0, 'results': []}
sync_all() -> {'synced': 0, 'failed': 0, 'results': []}
sync_all() -> {'synced': 0, 'failed': 0, 'results': []}
store_forward queue size: {}
get_status(): {'queue': {}, 'sync': {...}, 'edge_nodes': 0, 'engine': 'active'}
```

It drains `StoreForwardEngine._queue`, an in-memory list. **Nothing populates that queue.**
STATIC VERIFIED: `OfflineQueueEntry` is constructed nowhere outside
`app/integration/offline.py`, and `store_forward` is referenced nowhere outside it. The one
producer is `EdgeSyncEngine.sync_from_edge`, which has **no callers** anywhere in `app/` or
`services/`. And no edge node can be registered, because `register_edge_node` has no
callers either, so both edge methods fail closed on an unregistered node:

```
sync_to_edge("node-1", [...])   -> {'success': False, 'error': 'Unknown edge node: node-1'}
sync_from_edge("node-1", [...]) -> {'success': False, 'error': 'Unknown edge node: node-1'}
```

So `POST /integration/offline/sync` is **structurally incapable of a non-zero result**, and
`get_status()` nevertheless reports `"engine": "active"` while `/integration/health` reports
`"offline_engine": true`. Same shape as IA-014: an admin surface whose only possible answer
is the healthy one.

### The latent write-discard — `sync_to_edge`

Forcing the unreachable state (registering a node directly) shows the payload is dropped:

```
sync_to_edge("node-1", [2 records]) -> {'success': True, 'node_id': 'node-1', 'records_synced': 2}
store_forward queue after sync_to_edge: {}
EdgeSyncEngine attrs: ['_conflict_resolver', '_edge_nodes', '_last_sync', '_store_forward']
```

It reports **2 records synced**, stores nothing, and has no attribute in which it could
have. The method body only stamps `_last_sync[node_id]` and returns `len(data)`. This is
the NR-084 pattern (`POST /fhir` bundles reporting 201 and discarding every write), and it
is latent only because nothing calls it. Whoever wires edge sync inherits it silently.

### Conflict resolution is never consulted

`ConflictResolver` supports `last_write_wins`, `first_write_wins`, `merge` and `manual`.
Instrumenting `resolve` and running a full enqueue-then-sync cycle:

```
ConflictResolver.resolve call count during a full enqueue+sync cycle: 0
```

`sync_all()` never calls it. There is no conflict detection in the served sync path at all
— no version compare, no vector clock, nothing. `ConflictResolver` is constructed, held by
two objects, and never invoked. `app/platform/sync.py::SyncService.resolve_conflicts`
(version-compare LWW) is likewise never called from `sync_all`.

### The real capability is elsewhere

`/edge/*` serves 15 paths from `app/routes/edge.py` and is genuinely database-backed
(`db.query(EdgeDevice)`, `db.commit()`, `db.refresh()`). So GULA does have a real
edge/offline surface; `app/integration/offline.py` is a second, non-functional one beside
it. Nothing here says the platform lacks offline sync — it says this endpoint is not it.

### Why I did not fix it

Two defensible dispositions, and choosing is not mine:

- **Retire** the `app/integration/offline.py` surface (or the one endpoint), since `/edge/*`
  already provides the capability. Removing a served admin endpoint is an API-shape change.
- **Wire** it: give `StoreForwardEngine` persistence, call `sync_from_edge` from a real
  ingress, and make `sync_all` consult `ConflictResolver`. That is a subsystem build, and
  it needs the conflict-resolution semantics decided first (see IA-018).

Either way, `sync_to_edge` returning `records_synced: N` while discarding the payload should
not survive: it is a fake-green regardless of which disposition wins.

### Next action

Decide retire vs. wire. Under the PERMANENT DATA RULE, "retire" means retire/supersede the
module, not delete data — there is no data here to lose, the queues are in-memory.

---

## IA-018 — P2 — CONFIRMED_DEFECT — four different classes named `OfflineSyncEngine`, and the most credible one is dead code with real defects

| Field | Value |
|---|---|
| **ID** | IA-018 |
| **Severity** | P2 — latent. The defective engine has zero production importers; the hazard is adoption. |
| **State** | CONFIRMED_DEFECT — STATIC VERIFIED (reachability) — not fixed |
| **Files** | `app/services/offline_sync_service.py`, `app/integration/offline.py`, `app/core/sync_engine.py`, `app/citizen_platform/offline.py` |
| **Owner** | Human Decision (canonical owner), then Account 2 |

### Four classes, one name, four meanings

| # | Class | Semantics | Production importers |
|---|---|---|---|
| 1 | `app/services/offline_sync_service.py:74` | vector clocks, LWW / timestamp-merge / "CRDT" / manual resolution, per-operation signatures | **0** — only `tests/test_offline_sync.py` |
| 2 | `app/integration/offline.py:166` | store-and-forward + edge sync | 2 (`integration.py`, `routes.py`) — **served**, see IA-017 |
| 3 | `app/core/sync_engine.py:19` | — | **0** |
| 4 | `app/citizen_platform/offline.py:109` | a read-through **cache** (`cache_data`/`get_cached_data`), not a sync engine at all | 2 (`sdk.py`, `integration.py`) |

This is the R-16 trap in its sharpest form, and I walked into it: I read and analysed #1
first — it is in `app/services/`, the documented "Business logic layer", it is the most
sophisticated of the four, and it is the only one with a dedicated test file — and drew
conclusions before checking that **nothing imports it.** The served engine is #2, which is
far cruder. Severity assessed from sophistication and location would have been badly wrong.

### Defects in #1 — real, and latent because nothing calls it

Recorded so that adoption does not inherit them silently. Not fixed: fixing dead code ahead
of a canonical-owner decision would be work aimed at the wrong artefact.

1. **The "signature" is unauthenticated by default.**
   `_sign_operation` = `sha256(op_id : json(data) : device_id : self._device_secret)` and
   the constructor default is `device_secret=""`. With the default, every input is public,
   so any client can compute a valid value and `_verify_signature` establishes nothing. It
   is also a bare SHA-256 of concatenated fields, not an HMAC, and the secret is **one per
   engine**, so even when set, device A can forge device B's operations. The platform
   already mandates a `DEVICE_HMAC_KEY` with no fallback (`CLAUDE.md` security invariant 7);
   this module does not use it.
2. **Conflict resolution does not converge.** `receive_operation` sets the incoming op to
   `CONFLICT` and stores a `ConflictRecord`, but never adds the op to `_operations` and
   never advances the vector clock. `resolve_conflict` then writes the merge into
   `conflict.merged_data` and returns it — and updates neither `_operations` nor
   `_vector_clocks`. So a resolved conflict is invisible to every subsequent
   `_detect_conflict`, which still compares against the pre-conflict operation. Resolution
   produces a return value and a log line, and no state any later sync can read.
3. **`CRDT_MERGE` is not a CRDT.** It is first-writer-wins per key, iterating
   `(operation_a, operation_b)` in tuple order and keeping `a`'s value on collision.
   `operation_a` is whichever operation happened to be in `_operations` first, so the
   result depends on arrival order — the exact property a CRDT exists to eliminate. Two
   replicas resolving the same conflict can diverge. The name asserts a guarantee the code
   does not provide.
4. **LWW is decided by the device's wall clock.** `create_operation` stamps
   `timestamp=time.time()` on the device, and `LAST_WRITE_WINS` — the default set by
   `_detect_conflict` — picks the larger. A device with a fast clock wins every conflict it
   enters, indefinitely, and the loser's data is discarded with no archive. Against the
   PERMANENT DATA RULE ("archive/deactivate/retire/supersede instead"), discarding the
   losing write is the part to decide deliberately, not a detail.
5. **`EncryptedSyncStore` stores plaintext by default.** `_encrypt` returns its input
   unchanged when `self._key` is falsy, and the constructor default is `encryption_key=""`.
   A store named "Encrypted", used for an offline device cache, is a no-op cipher unless a
   key is passed. `_derive_key` is also `base64(sha256(key))` with no KDF or salt.

### What is NOT claimed

- No claim that offline sync is broken in production: **nothing runs this module.**
- No claim that patient data is exposed: `EncryptedSyncStore` has no production caller
  either.
- No claim about `#4` beyond its name — it is a cache and behaves like one.

### Next action

Name the canonical offline-sync owner among the four, then retire/supersede the rest per
the PERMANENT DATA RULE. If #1 is chosen, defects 1–5 are blockers and belong to Account 2.
If #2 is chosen, IA-017's disposition applies. The `OfflineSyncEngine` name collision
itself is the same class of problem as NR-087/NR-088/NR-081 ("one module, one import path").

---

## Lab Result Workflows — audit scope and the NR-164 premise

Workflow traced end to end: Order → TestType → Specimen → result creation →
validation → update → finalization → report → audit/event. Every production
construction site of `LabResult` was enumerated (4), plus the served FHIR
exporters, the canonical national projection, the statistics and compliance
readers, the critical-alert service, and the analyzer ingress.

**Correction to the task premise, measured in all three lineages.** The brief
states that `LabResult.test_type_id` cannot be NULL after NR-164. That is not
true of any lineage available to this container:

| worktree | head | `test_type_id` |
|---|---|---|
| `gula-audit` (this lane) | `375be931` | `nullable=True`, `ondelete="SET NULL"` |
| `gula-platform` (sibling lane, owns NR-164) | `203c85aa` | `nullable=True` |
| `gula-p02-proof` (integration lineage) | `ce097a0c` | `nullable=True` |

And in the migrated database (`gula_agent2`, head `20260916_0001`),
`information_schema.columns` reports `is_nullable = YES`, with no CHECK
constraint — `pg_constraint` for `lab_results` lists only the two foreign keys,
the primary key, and the two token uniques. Two migrations mention
`test_type_id` and neither applies NOT NULL. So nothing at the schema level
prevents a NULL test-type link, and the guarantee has to come from the write
paths. It did not. NR-164 itself belongs to the sibling lane's register and is
not re-audited here; this records only what is measurable in this container.

---

## IA-019 — P1 — CONFIRMED_DEFECT — FIXED — three of four result write paths stored no test-type link, and a category-filtered clinical history silently dropped them

| Field | Value |
|---|---|
| **ID** | IA-019 |
| **Severity** | P1 — silent clinical data incompleteness on a served, tenant-scoped PHI endpoint |
| **State** | CONFIRMED_DEFECT → **FIXED** — RUNTIME VERIFIED (PostgreSQL) + TEST VERIFIED with negative proof |
| **Files** | `app/services/order_service.py:420`, `app/routes/device_results.py:96`, `app/core/bootstrap/demo_data.py:185` (defective); `app/routes/test_results.py:362` (correct) |
| **Affected table** | `lab_results.test_type_id` |
| **Owner** | Account 2 — done |

### The write-path matrix

| path | served route | set `test_type_id`? |
|---|---|---|
| `app/routes/test_results.py:362` | `POST /test-results/` | **yes** — `tt.id if tt else None`, after a catalog lookup |
| `app/services/order_service.py:420` | `POST /batch/orders`, `/results` (via `create_order`) | **no** — keyword omitted entirely |
| `app/routes/device_results.py:96` | `POST /device/results` (analyzer) | **no** — keyword omitted entirely |
| `app/core/bootstrap/demo_data.py:185` | boot-time seeding, production models | **no** — keyword omitted entirely |

### Reproduction and consequence — RUNTIME VERIFIED in PostgreSQL

`/test-results/citizen/{health_id}` (`:603`) and `.../timeline` (`:685`) outer-join
`TestType` and then filter `TestType.category == category`. For a row with a NULL
link that predicate evaluates to NULL, which is not true, so the row is dropped.
One patient, three glucose results, one per write path:

```
=== ALL results for this patient (no category filter) ===
 id | value | test_type_id | category
  1 |   180 |            1 | Chemistry     <- POST /test-results/
  2 |   190 |              |               <- order_service.create_order
  3 |   200 |              |               <- POST /device/results

=== THE SERVED QUERY with category=Chemistry ===
 id | value | test_type_id | category
  1 |   180 |            1 | Chemistry

 total_results | visible_with_category_filter
             3 |                            1
```

A clinician filtering a patient's lab history by category sees one of three
results, with nothing to indicate the other two exist. `TestType` is also the
only owner of `test_code`, `category` and the Arabic/English interpretation
text; `lab_results` denormalises just `unit` and the two range bounds. So a
NULL link also empties `test_code` in `CanonicalObservation`
(`app/national_data/models/canonical_observation.py:60`, served under
`/national-data/...`), the national reporting projection.

### The fix

The resolution convention already existed, privately, inside the one correct
route: `test_code` exact match first (the column is unique), else a
case-insensitive `test_name` match, and never overwrite a caller-supplied value.
That function is moved to `app/services/test_catalog.py::resolve_test_type` —
unchanged in behaviour — and applied to all four paths. No new clinical
semantics: three paths now behave the way the fourth already did. `None` after
an honest lookup is still legitimate for an uncatalogued test; what is no longer
possible is writing NULL without asking.

No schema change, no migration, no response-shape change.

---

## IA-020 — P1 — CONFIRMED_DEFECT — FIXED — a critically abnormal analyzer result was stored unflagged, and every critical-alert consumer reads that flag

| Field | Value |
|---|---|
| **ID** | IA-020 |
| **Severity** | P1 — patient safety. A critical value ingested from an analyzer was invisible to every alerting and dashboard consumer. |
| **State** | CONFIRMED_DEFECT → **FIXED** — RUNTIME VERIFIED + TEST VERIFIED with negative proof |
| **Files** | `app/routes/device_results.py:79-107`, `app/services/order_service.py:398-418`, `app/services/interpretation.py:1253` |
| **Route** | `POST /device/results` (authenticated, tenant-filtered, rate-limited) |
| **Owner** | Account 2 — done |

### Mechanism

`get_flag` returns `"unknown"` on its **first** branch when either reference
bound is None — before it ever reaches its `check_critical` call:

```python
if normal_low is None or normal_high is None:
    return "unknown"
# the critical-threshold check lives below this line
```

Analyzers send values; reference ranges live in the lab's `TestType` catalog.
Neither the analyzer path nor the order path consulted that catalog, so:

- **analyzer path**: ranges stay NULL, the `if` guard means `get_flag` is never
  called at all, and `flag` is stored as **NULL**;
- **order path**: `get_flag` is called and returns **`"unknown"`**.

Meanwhile `check_critical(test_name, value)` needs **only a name and a value** —
both already in hand on every path. It consults a 37-test medical threshold
table and is independent of reference ranges.

### Evidence — RUNTIME VERIFIED, in-process

```
--- potassium = 7.5 (critical_low=2.5, critical_high=6.5) ---
  check_critical(name, value)                 -> CRITICAL: critical_high
  ANALYZER  /device/results, no ranges sent   -> flag = None   (get_flag not called at all)
  MANUAL /test-results/, catalog ranges       -> flag = 'critical'
  get_flag(value, None, None, test_name)      -> 'unknown'   <- returns before the critical check
```
Identical outcome for glucose 500 (critical_high=500) and haemoglobin 4.0
(critical_low=5.0).

### Why the stored flag is what matters

`RESULT_CRITICAL` events are emitted by the order and manual paths — into a bus
with no subscribers (see IA-022), so the events change nothing. The **persisted
`flag`** is the real mechanism, and it is read widely:

| consumer | predicate |
|---|---|
| `app/services/critical_alerts.py:108,157,179` | `LabResult.flag == "critical"` (three queries) |
| `app/routes/stats.py:169,332,363` | critical counts, dashboards |
| `app/citizen_platform/laboratory.py:93` | citizen-facing critical results |
| `app/routes/citizen_portal.py:477` | citizen portal |
| `app/routes/compliance.py:569-571` | MoH abnormality statistics (see IA-021) |

So a critically high potassium arriving from the analyzer — the primary route by
which a real laboratory produces results — was stored with `flag = NULL` and
therefore absent from the critical-alert service, the dashboards and the
patient's own portal.

### The fix

The same `resolve_test_type` call. With the catalog range in place, the existing
`get_flag` call on each path reaches its critical check and stores
`"critical"`. The change does not alter `get_flag`, does not invent a
threshold, and cannot manufacture a critical flag for a normal value —
`check_critical` fires only on the medical threshold table.

### Negative proof (covers IA-019 and IA-020 together)

```
BASELINE (resolver extracted, 3 paths unfixed) : 6 failed, 9 passed
AFTER the fix                                  : 15 passed
REVERT the analyzer path                       : 2 failed  (its two guards)
RESTORE                                        : 15 passed
ADD a duplicate resolver copy                  : 1 failed  (single-resolver guard)
RESTORE                                        : 15 passed
```

Relevant regression: `tests/test_device_routes.py`, `test_comprehensive.py`,
`test_compliance_integrity.py`, `test_fhir_comprehensive.py`,
`test_clinical_safety.py`, `tests/verification/` → **326 passed, 145 skipped**.

---

## IA-021 — P1 — CONFIRMED_DEFECT — NEEDS_DECISION — the Ministry of Health export cannot report an abnormal result, and counts unflagged criticals as normal

| Field | Value |
|---|---|
| **ID** | IA-021 |
| **Severity** | P1 — national reporting integrity. Not fixed: the correct bucket set is a response-shape decision. |
| **State** | CONFIRMED_DEFECT — RUNTIME VERIFIED (PostgreSQL) — **not fixed** |
| **File** | `backend/app/routes/compliance.py:569-571` |
| **Route** | `GET /compliance/dhis2/aggregate` — "DHIS2 aggregate data export for MoH reporting" |
| **Owner** | Human Decision |

### The vocabulary does not exist

`get_flag` is the only writer of computed flags. Its complete output vocabulary
is `{"normal", "H", "L", "critical", "unknown"}`. The export classifies:

```python
abnormal_high = case((LabResult.flag.in_(["high", "critical_high"]), 1), else_=0)
abnormal_low  = case((LabResult.flag.in_(["low",  "critical_low"]),  1), else_=0)
normal        = case(((LabResult.flag == "normal") | (LabResult.flag.is_(None)), 1), else_=0)
```

`"high"`, `"critical_high"`, `"low"` and `"critical_low"` are **never produced by
any writer**. So `abnormal_high` and `abnormal_low` are structurally zero, and
`flag IS NULL` — which is exactly what the analyzer path used to store for a
critical value — is counted as **normal**.

### Evidence — RUNTIME VERIFIED in PostgreSQL

Six results in the real flag vocabulary, including an analyzer-ingested critical
potassium of 8.1 with `flag = NULL`:

```
=== what is actually stored ===
 H | 1 ; L | 1 ; critical | 1 ; normal | 1 ; unknown | 1 ; (null) | 1

=== THE MoH DHIS2 EXPORT as compliance.py:569-571 computes it ===
 test_name | count | abnormal_high | abnormal_low | normal
 Potassium |     6 |             0 |            0 |      2

=== how many stored rows land in NO bucket at all ===
 4
```

Four of six rows are counted in none of the three buckets, so the buckets do not
sum to the count; the one genuinely critical result is reported as neither high
nor low; and the unflagged critical is reported as normal. This is an export
described in its own docstring as feeding "the MoH DHIS2 national health
information system" across "1,848 health institutions".

IA-020's fix reduces how often `flag IS NULL` occurs but does not repair this
query: `H`, `L`, `critical` and `unknown` still fall outside every bucket.

### Why I did not fix it

Aligning the reader to the writer is mechanical for three of the five values
(`normal`, `H` → high, `L` → low). `"critical"` is not: `get_flag` returns a
bare `"critical"` that does not say high or low, so it cannot be assigned to
either bucket from the flag alone, and `"unknown"` is a fourth state the export
has no field for. Doing this correctly adds response fields — an API
response-shape change, which `CLAUDE.md` places under "Requires human
approval". Guessing a bucket for `"critical"` would put fabricated
directionality into a ministry submission.

This is the same root cause as **R-17**: `lab_results.flag` is unconstrained
free text with four writers and no closed vocabulary.

### Next action

Decide the bucket set for the MoH export (options: add `critical` and `unknown`
fields; or emit a flag-distribution map keyed by the real vocabulary, as
`stats.py:222-230` already does). Whichever is chosen, `flag IS NULL` must stop
being counted as normal.

---

## IA-022 — P2 — CONFIRMED_DEFECT — NEEDS_DECISION — GULA has three in-process event buses and not one production subscriber on any of them

| Field | Value |
|---|---|
| **ID** | IA-022 |
| **Severity** | P2 — every domain event emitted by the platform is delivered to nobody. Extends IA-013/IA-014 from the kernel bus to all three. |
| **State** | CONFIRMED_DEFECT — STATIC VERIFIED — not fixed |
| **Owner** | Human Decision (jointly with IA-013) |

| bus | module | emit API | production subscribers |
|---|---|---|---|
| kernel `EventBus` | `app/kernel/event_bus/bus.py` | `publish(Event)` | **0** (IA-013 correction) |
| `IdentityEventBus` | `app/identity/events.py` | `publish(type, payload)` | **0** — the three `on_*` decorators are never applied |
| `shared.events` | `shared/events/bus.py`, re-exported by `app/core/events.py` | `emit(name, payload)` | **0** |

For `shared.events`, the only `@events.on(...)` occurrence anywhere in
`backend/app/` or `shared/` is **inside a docstring** — the usage example at
`app/core/events.py:9`. So `ORDER_CREATED`, `ORDER_VALIDATED`, `ORDER_CANCELLED`,
`RESULT_CRITICAL` and `SAMPLE_REJECTED` are emitted into a bus with no handlers.

This is why IA-020's severity rests on the persisted `flag` and not on the
missing `RESULT_CRITICAL` emission: adding that emission to the analyzer path
would have changed nothing observable. It also means the critical-alert
*notification* path, as distinct from the stored flag, does not exist on any
route.

### Next action

Fold into the IA-013 decision: three buses, one of which (`outbox_service.py`
over the present `outbox_events` table, with a running worker) is the only
durable mechanism that works. Deciding which survives is one decision, not
three.

---

## Lab Result Workflows — verified negatives (NO DEFECT FOUND, with evidence)

Recorded because absence of a finding is a result. Each was probed adversarially.

| probe | outcome |
|---|---|
| **Analyzer tenant isolation** | **NO DEFECT FOUND.** `POST /device/results` resolves the sample via `.join(LabOrder).filter(Sample.barcode == …, LabOrder.lab_id == current_user.lab_id)`. A barcode belonging to another lab cannot be written to. |
| **Analyzer authentication** | **NO DEFECT FOUND.** `Depends(get_current_user)`; unauthenticated calls are rejected. Rate-limited to 100/min per IP, max 100 results per submission. |
| **Order state machine on ingestion** | **NO DEFECT FOUND.** `assert_not_locked`, `assert_not_cancelled`, `enforce_transition(order.status, "completed")` all run before any result is created; rejected samples are refused with 400. |
| **Analyzer audit trail** | **NO DEFECT FOUND.** `log_action(action="device_results", resource_type="lab_order", resource_id=order.id, user_id=…, user_role=…)` on every submission. |
| **Served FHIR Observation exporter** | **NO DEFECT FOUND, and better than its unreached sibling.** `/compliance/fhir/observation/{order_id}` emits `"code": {"text": r.test_name}` with no `coding` block, so it makes no LOINC claim it cannot support, and it filters by `LabOrder.lab_id == current_user.lab_id`. |
| **`FHIRObservationMapper` LOINC claim** | **latent, already covered by IA-011.** `app/national/fhir/observation.py:17` emits `{"system": "http://loinc.org", "code": result.get("test_code", "")}` — asserting LOINC for what is GULA's own `test_types.test_code`, and `None` when unresolved. Its only caller is `app/national/tests/unit/test_fhir.py`; **no production caller**, so this is IA-011's unreached mapper, not a live defect. Re-confirmed rather than re-raised. |
| **Optimistic locking column** | **present and correct in shape.** `lab_results.version` is `NOT NULL DEFAULT 1` physically. Result *creation* is an insert, so the version column is not in play on the paths audited here; the update paths were not exercised in this batch and remain open (see next action). |

### Open, carried forward from this batch (not yet classified)

| item | state |
|---|---|
| `POST /device/results` has no idempotency: no dedup key, and the only uniques on `lab_results` are the two per-row random tokens. A retried analyzer submission creates duplicate results. | **DISCOVERED** — needs reachability/impact work and comparison with the canonical idempotency helper the programme built in §32-A/B |
| `device_id` is accepted as free text, stored nowhere, and written into the audit-log detail string as if it were provenance. `DEVICE_HMAC_KEY` is a mandated platform secret (`CLAUDE.md` invariant 7) that this route does not use. | **DISCOVERED** — analyzer identity is unauthenticated; needs its own pass |
| Result **update** and **validation/finalization** paths (optimistic locking, status transitions, audit on mutation) were mapped but not adversarially exercised. | **not audited in this batch** |

---

## IA-023 — P1 — CONFIRMED_DEFECT — NEEDS_DECISION — the analyzer trust boundary exists, is fully implemented, and nothing calls it

| Field | Value |
|---|---|
| **ID** | IA-023 |
| **Severity** | P1 — the served analyzer ingress has no device authentication, no replay protection and no idempotency, while the module that implements all three is unreachable. |
| **State** | CONFIRMED_DEFECT — STATIC VERIFIED (reachability) + RUNTIME VERIFIED (duplicate behaviour) — **not fixed** |
| **Files** | `app/gateways/lab_device_gateway.py` (hardened, unreached); `app/routes/device_results.py` (served, unhardened); `app/services/device_trust_service.py` (unreached) |
| **Route** | `POST /device/results` |
| **Owner** | Human Decision |

### Two analyzer boundaries, and the wrong one is served

`app/gateways/lab_device_gateway.py` documents and implements a four-layer
security model:

1. input validation — type, length, numeric range (`±1_000_000`, 100-char strings);
2. device whitelist — `ALLOWED_DEVICE_IDS`;
3. **HMAC-SHA256** over `"{device_id}:{sample_id}:{test}:{value}:{timestamp}"` keyed
   with `DEVICE_HMAC_KEY`;
4. **replay protection** — a `REPLAY_WINDOW_SECONDS` timestamp window plus a
   per-message `nonce`, tracked in Redis with a TTL.

`DEVICE_HMAC_KEY` is one of the five secrets `CLAUDE.md` invariant 7 says must
have no fallback. **`lab_device_gateway` has zero importers** anywhere in `app/`,
and it persists nothing — `receive_device_result` validates, authenticates and
returns a normalised dict with `"status": "received"`.

The served ingress, `POST /device/results`, has none of the four layers:

| control | hardened gateway (unreached) | served route |
|---|---|---|
| device whitelist | `ALLOWED_DEVICE_IDS` | **none** |
| message HMAC | `DEVICE_HMAC_KEY` | **none** |
| replay window | `REPLAY_WINDOW_SECONDS` | **none** |
| nonce / dedup | Redis nonce with TTL | **none** |
| numeric range validation | `±1_000_000` | Pydantic `float | None` only |
| `device_id` handling | required and verified when keyed | free text, **never stored** |

`app/services/device_trust_service.py` (fingerprinting, trust levels, trusted
device registry) also has **zero importers**. `app/devices/` → `/device-integration/*`
**is** served (14 paths, wired at `app/factory.py:652`) but owns a separate model
tree (`integrated_devices`, `device_gateways`, `device_connectors`,
`device_protocol_profiles`, `device_events`, `device_outbox_messages`, …) and does
**not** write `LabResult`.

### `device_id` is recorded as provenance without being verified

`DeviceSubmission.device_id` is `str | None = None`. It is written into the audit
trail —

```python
details=f"Device {data.device_id or 'unknown'}: {len(created)} results via barcode {data.barcode}",
```

— and stored nowhere else. So the immutable, hash-chained audit log records an
unauthenticated, caller-supplied string as the identity of the instrument that
produced a clinical result. Any authenticated lab user can submit results
claiming any analyzer. This is not anonymous spoofing — the route requires a
valid session and is correctly tenant-scoped — but *device* provenance in the
audit trail is unverifiable while being presented as fact.

### No idempotency: a retry duplicates clinical results

`lab_results` carries three uniqueness constraints in the migrated database
(`gula_agent2`): the primary key, `lab_results_token_key` and
`lab_results_token_hash_key`. **Both token uniques are per-row random values**
(`secrets.token_urlsafe(32)` generated inside the loop), so neither can collide
across submissions, and nothing keys on submission identity —
`(barcode, device_id, nonce)` or `(order_id, test_name, value)`. Re-posting the
same submission therefore inserts fresh rows:

```
=== a retried analyzer submission: same barcode, same test, same value, three times ===
 rows_for_one_logical_result
                           3
```

(RUNTIME VERIFIED in PostgreSQL on an isolated probe database. The constraint
list printed by that probe is the probe table's own, not production's; the
production constraint set was read separately from `gula_agent2` and is as
described above.)

An analyzer that retries on a timeout — the normal behaviour of instrument
middleware — produces duplicate results for one specimen. Combined with IA-020's
fix, a duplicated critical result now also duplicates the critical flag.

The programme already built a canonical idempotency helper (§32-A/B, applied to
`/samples` and `/batch/orders`). `POST /device/results` does not use it.

### Why I did not fix it

Every remedy changes the contract devices must satisfy:

- **A. Wire the existing gateway.** Call `receive_device_result` from the route.
  Correct, and it is what the module was written for — but with `DEVICE_HMAC_KEY`
  set, devices must send `signature`, `timestamp` and `nonce`, which the current
  `DeviceResult` schema has no fields for. Existing analyzers would break until
  reconfigured. That is a deployment decision, not a code decision.
- **B. Apply the §32-A/B idempotency helper only.** Closes the duplicate-result
  half without touching authentication. Needs a submission identity chosen
  (`barcode + device_id + nonce`? a client-supplied `Idempotency-Key`?), which is
  an API contract addition.
- **C. Persist `device_id` on the result** so provenance is at least recorded
  rather than only narrated in an audit string. Needs a migration — a schema
  change, which `CLAUDE.md` places under "Requires human approval".
- **D. Retire `lab_device_gateway` and `device_trust_service`** as superseded, if
  the decision is that session authentication is the intended boundary. Under the
  PERMANENT DATA RULE that is retire/supersede, not delete.

Guessing here would either break live instruments or bless an unauthenticated
boundary by silence. This is the same shape as IA-018: a hardened implementation
sits unreached beside a crude served one.

### Next action

Decide A–D. If A, the `DeviceResult`/`DeviceSubmission` schemas need
`signature`/`timestamp`/`nonce` and a rollout plan for already-deployed analyzers.

---

## Analyzer Integration — verified negatives (NO DEFECT FOUND, with evidence)

| probe | outcome |
|---|---|
| **Cross-tenant result injection by barcode** | **NO DEFECT FOUND.** The sample lookup joins `LabOrder` and filters `LabOrder.lab_id == current_user.lab_id`; another lab's barcode is a 404. |
| **Unauthenticated submission** | **NO DEFECT FOUND.** `Depends(get_current_user)`; 401 without a token. |
| **Submission volume** | **NO DEFECT FOUND.** `rate_limit_public(request, max_per_minute=100)` and a hard 400 above 100 results per submission. |
| **Writing to a locked, cancelled or rejected workflow** | **NO DEFECT FOUND.** `assert_not_locked`, `assert_not_cancelled`, `enforce_transition(order.status, "completed")` run before any insert; a rejected sample is refused with 400. |
| **Audit coverage of the ingestion itself** | **NO DEFECT FOUND.** `log_action` is called on every submission with actor id and role. Only the *device* identity within it is unverified (IA-023). |
| **`/device-integration/*` writing lab results** | **NO DEFECT FOUND** — it does not touch `LabResult`; it is a separate device-management surface, not a result ingress. |
