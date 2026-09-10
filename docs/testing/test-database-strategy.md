# Test Database Strategy — Schema Fidelity

**Program:** TEST-001 + TEST-001.1 · **Finding:** NR-036 · **Status:** VERIFIED —
the gate is implemented, proven, and executing in CI (§6).

> **A green test must never mean "the ORM can create this table."**
> For production-like verification it must mean: the migration chain created the
> same physical contract the application is expected to run against.

---

## 1. Root cause

`backend/tests/conftest.py` builds the shared `db` fixture like this:

```python
_ddl_meta = MetaData()
for meta in (Base.metadata, NationalBase.metadata, EHRBase.metadata, ...16 bases):
    for name, table in meta.tables.items():
        table.to_metadata(_ddl_meta)
_ddl_meta.create_all(engine)          # SQLite temp file
```

Two consequences, both load-bearing:

1. **Any ORM table exists in tests whether or not a migration builds it.**
   198 of 431 ORM tables have no migration. All 198 are present in the test
   database and absent from a migrated one.
2. **Cross-base foreign keys resolve in tests** because everything is merged
   into one MetaData — which production cannot do (NR-023).

That is how NR-026, NR-032 and NR-034 each passed CI while the same code could
not commit against a migrated database. The pharmacy POS tests even asserted
rows in `ehr_medication_dispenses`, a table no migration creates.

## 2. Current architecture, classified

| Construction site | Category | Verdict |
|---|---|---|
| `conftest.py:147` `_ddl_meta.create_all()` — the shared `db` fixture, SQLite | INTEGRATION / API / CLINICAL / TENANT / SECURITY | **the risk**: high-fidelity claims on a low-fidelity schema |
| `test_consent.py`, `test_routes_labs.py`, `test_routes_register.py`, `test_dashboard_data_minimization.py` | API | local SQLite engines, same limitation |
| `test_fx_quote_engine.py`, `test_payments_foundation.py`, `test_payment_orchestration.py`, `test_institutional_subscriptions.py` (FinBase) | UNIT | acceptable — narrow, no schema claim |
| `test_governance.py`, `test_persisted_identity_governance.py` | UNIT | acceptable |
| `test_outbox_service.py`, `test_feature_flags.py`, `integration/test_integration_inbox.py` | UNIT / INTEGRATION | acceptable — single-table scope |
| `app/engineering/testing/unit.py:60` | UNIT helper | acceptable |
| `test_alembic_metadata_registry.py`, `test_nursing_domain_contract.py`, `test_nursing_runtime.py`, `test_ehr_medication_dependency_p0.py`, `test_pharmacy_*_postgres.py`, **`test_schema_fidelity.py`** | MIGRATION / SCHEMA | **already migration-backed PostgreSQL** |

**Deliberately unchanged:** `create_all()` is not banned. It is correct for unit
tests that make no claim about the production schema, and converting the suite
would be a large change for little added truth. What changes is that it can no
longer be the *unexamined* authority.

## 3. The canonical test database

```
fresh PostgreSQL → alembic upgrade head → physical schema → test execution
```

Tests that need this resolve their URL from `GULA_SCHEMA_DATABASE_URL`, falling
back to `MIGRATION_DATABASE_URL` — the variable CI already exports for its
migrated service. `DATABASE_URL` is deliberately **not** consulted: `conftest`
pins it to in-memory SQLite, which is the exact substitution the gate exists to
detect.

## 4. The gate — `backend/tests/test_schema_fidelity.py`

Two properties, complementing the physical→ORM direction that
`test_alembic_metadata_registry.py` already guards.

### 4.1 ORM → migration
Every ORM table must be **A** built by the migration chain, or **D** named in
`DECLARED_UNBUILT_TABLES` with its disposition. (**C**, external/shared
ownership, has no case today; **B**, permanent per-table exclusion, is folded
into the same ledger.) The ledger holds 198 tables grouped by owning base:

| Base | Tables | Disposition |
|---|---:|---|
| Governance | 58 | declared, never migrated |
| National | 52 | **NR-022** — depended on by five domains, built by none |
| DataPlatform | 36 | warehouse/MDM, declared, never migrated |
| EHR | 18 | **NR-032** — blocked behind the National Core |
| HealthData | 17 | declared, never migrated |
| Hospital | 10 | declared, never migrated |
| Fin | 6 | Financial Engine beyond Phase A — schema-only by design |
| Radiology | 1 | `radiology_ai_jobs`; the other eighteen are built |

A model added without a migration adds a name here, which is a review rather
than an edit of convenience. Two staleness checks keep the ledger honest: an
entry that has since been built, or that no model declares any more, fails.

### 4.2 Cross-generation dependency — the rule that actually matters
A module in a migration-backed domain must not import a model from a domain the
chain does not build. An unbuilt domain is a deliberate state; a **built** domain
reaching into one is a live defect waiting for the first request that gets
there — precisely what a pharmacy sale naming a patient did.

Sixteen such importers are declared: thirteen reaching `app.ehr.models.*`
(NR-032) and three reaching `app.national_data.models.*`. `pharmacy/services.py`
left that list in MED-001. A new arrival fails the gate.

### 4.3 create_all() cannot masquerade as the migration chain
The gate refuses to report a pass unless the dialect is PostgreSQL **and**
`alembic_version` exists **and** no declared-unbuilt table is present. A
`create_all()` database fails all three. Fail loudly, never silently green.

## 5. Regression proof

Each proven by making the defect real, observing the failure, and reverting:

| Case | Method | Result |
|---|---|---|
| **ORM model with no migration** (NR-026 class) | added `nursing_tst001_probe` to `NursingBase` | `AssertionError: these ORM tables have no migration and are not in the ledger: nursing_tst001_probe (owned by Nursing)` |
| **Built domain depends on unbuilt** (NR-032/034) | restored the EHR import in `pharmacy/services.py` | `AssertionError: these modules now depend on a domain the migration chain does not build: ['pharmacy/services.py']` — 2 tests failed |
| **create_all() fallback** | pointed the gate at a database with no `alembic_version` | `AssertionError: this database has no alembic_version table … Refusing to report a pass.` |

In-test classification proofs cover the remaining §6 cases — a migration-backed
table, a declared exclusion, a renamed ORM table (the NR-026 shape), and a
physical table with no ORM owner (deliberately the other guard's job) — using an
isolated `MetaData` so nothing touches a real declarative base and nothing
survives the test.

## 6. CI — bound and demonstrated

The gate runs in the **PostgreSQL migration and schema gate** job of
`.github/workflows/iam-hardening.yml`. That job already creates a
`postgres:16.4` service, runs `alembic upgrade head`, and exports
`MIGRATION_DATABASE_URL`; TEST-001.1 appended one file to the existing pytest
invocation of its *Verify workspace schema on PostgreSQL* step. No new job, no
second database, no duplicated migration setup, no other job touched.

Placement was checked, not assumed: the step runs **after** *Apply migration
head* and **before** *Verify reversible workspace migration*, which downgrades to
`20260814_0002` and back. The gate therefore reads a schema at head.

The gate is **not advisory**. This workflow carries four `continue-on-error`
flags and all four are on evidence-upload steps — the artifact quota is
exhausted, and archival must not fail the gate it documents. The pytest step
carries none, so a schema-fidelity failure fails the job.

**Demonstrated execution**, CI log for `ef58331c`:

```
collected 11 items
tests/identity/test_workspace_migration_phase5.py .                      [  9%]
tests/identity/test_membership_migration_phase6.py .                     [ 18%]
tests/identity/test_security_audit_migration_phase9.py .                 [ 27%]
tests/identity/test_clinical_gateway_migration_phase10b.py .             [ 36%]
tests/test_schema_fidelity.py .......                                    [100%]
======================= 11 passed, 2 warnings in 10.31s ========================
```

Collected items went from 4 to 11, on Python 3.12.14 with `ENV=migration`,
`RUNTIME_MODE=migration` and no `BASE_URL` — the job's real environment, which
differs from the one earlier local runs used. Job conclusion: **success**.

**Correction this batch resolved.** BATCH-3 claimed the nursing tests would
"actually execute in CI rather than skip" once they resolved
`MIGRATION_DATABASE_URL`. That was wrong: the variable is exported by a job that
runs a named list of files, not one that would collect them. Only
`test_schema_fidelity.py` is bound today.

**Still unbound**, recommended for the same one-line treatment:
`test_alembic_metadata_registry.py`, `test_nursing_domain_contract.py`,
`test_nursing_runtime.py`, `test_ehr_medication_dependency_p0.py`.

## 7. Performance

| Step | Cost |
|---|---|
| `alembic upgrade head` on a fresh database (106 migrations) | **13.5 s** — already paid by the existing job |
| The schema-fidelity gate, 7 tests | **11.7 s** |
| A comparable `create_all()` unit file | 4.2 s |

Marginal cost of making the gate binding: **~12 s**, because the migrated
database already exists in that job. No optimisation is warranted.

## 8. Security

The gate reads schema metadata only. It creates no rows, alters no schema, and
holds no credentials. It cannot weaken a tenant or authorization test because it
runs none — and it refuses SQLite outright, so it can never certify PostgreSQL
semantics it did not observe.

## 9. Remaining limitations

1. **Only one suite is bound.** Four other migration-backed suites still run
   locally only; see §6.
2. **The shared `db` fixture is unchanged.** Tests claiming API, clinical,
   tenant and security fidelity still run on SQLite built by `create_all()`.
   The gate stops *new* unbuilt tables and *new* cross-generation dependencies;
   it does not convert those tests. Doing so is a much larger batch and was
   explicitly out of scope.
3. **Table-level, not column-level.** A table that exists in both places but
   whose columns disagree is caught for Nursing by
   `test_nursing_domain_contract.py`; there is no platform-wide equivalent yet.
4. **The 198-entry ledger is a snapshot of a decision, not an endorsement.**
   Seven whole domains are declared and unbuilt.
