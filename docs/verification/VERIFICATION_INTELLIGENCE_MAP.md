# GULA Verification Intelligence — Map

**Generated:** 2026-09-25 · **Head:** `d8c2a31b` · **production_ready:** `false`

Companions: [`INVARIANTS.md`](./INVARIANTS.md) · [`FAILURE_MODES.md`](./FAILURE_MODES.md) ·
[`EVIDENCE_ICU_INFUSION_VERIFY.md`](./EVIDENCE_ICU_INFUSION_VERIFY.md) ·
[`WORK_PACKETS.md`](./WORK_PACKETS.md)

## 0. What this layer is for, and what it is not

Engineering Intelligence (`tools/gula_intel/`) answers _what exists and what changed_.
This layer answers one different question: **can we prove it survives failure?**

It is not a second scanner. Every static detector already in `tools/gula_intel/`
is reused as-is; nothing here re-implements inventory, migration-graph analysis
or ownership detection. What this layer adds is the part none of those can
supply — evidence produced by running the real application against a real
PostgreSQL database and watching what happens when things go wrong.

The first pass found that the highest-value thing to prove was not a
concurrency subtlety. It was whether the operation runs at all.

## 1. Phase 0 — inventory of what already existed

Measured on `d8c2a31b`, not recalled.

### Present and reused

| Capability                 | Where                                                  | State                                                                                                                                                   |
| -------------------------- | ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Failure injection          | `app/clinical/failure_injection.py`                    | 5 stages, env-triple-gated (`ENV=test`, `RUNTIME_MODE=test`, explicit stage, allow-list). **9 call sites, 8 of them Blood Bank.** Reused, not replaced. |
| Clinical command guard     | `app/clinical/command_guard.py`                        | Idempotency key, `If-Match` version, durable claim, `complete`/`reject`, audit emission. Used by **8 domains**.                                         |
| Durable idempotency claims | `clinical_command_receipts`                            | Unique on `(lab_id, actor_user_id, operation, idempotency_key)` — per-actor, not per-tenant. That distinction is load-bearing; see INV-IDEM-02.         |
| Row locking                | `with_for_update` in 21 app files                      | Present; proven in 1 domain before this pass.                                                                                                           |
| Concurrency tests          | `threading.Barrier` in 7 test files                    | All Blood Bank.                                                                                                                                         |
| PostgreSQL-gated tests     | 9 files                                                | Blood Bank 7, biomedical 1, command centre 1.                                                                                                           |
| Static migration guard     | `tests/migrations/test_migration_graph_integrity.py`   | Unique revisions, single head, safety-critical table creation. 3 tests.                                                                                 |
| Audit immutability         | `audit_logs_deny_mutation` DB trigger                  | **Verified working** — see INV-AUDIT-02. Discovered by this pass, not previously recorded.                                                              |
| Static detectors           | `tools/gula_intel/detectors.py`                        | 5 rules: `GULA-MIG-001/002`, `GULA-ARCH-001`, `GULA-STATE-001`, `GULA-SCHEMA-001`.                                                                      |
| Findings register          | `docs/architecture/GULA_MASTER_NEGATIVE_REGISTER.json` | 22 findings before this pass.                                                                                                                           |
| Bounded self-repair        | `scripts/self_audit_agent.py`                          | Unchanged. This layer decides _what must be proven_; the agent may only act inside its existing limits.                                                 |

### Absent before this pass

| Gap                          | Consequence                                                                                                                                                                                                                                                                                                                        |
| ---------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| No shared PostgreSQL harness | 9 files each rolled their own behind **3 different env var names**; 7 called `create_engine` twice apiece; one imported private helpers from a _sibling test module_. No `conftest.py` fixture existed. The cost of the tenth harness equalled the cost of the first, which is why real-PostgreSQL evidence stopped at one domain. |
| No negative-proof mechanism  | The pattern was practised by hand and recorded only in commit prose. Nothing in `backend/`, `tools/` or `scripts/` referenced it.                                                                                                                                                                                                  |
| No invariant registry        | Invariants lived in reviewers' heads.                                                                                                                                                                                                                                                                                              |
| No failure-mode catalog      | Each test invented its own vocabulary.                                                                                                                                                                                                                                                                                             |
| No verification matrix       | Missing evidence could not be _computed_, only noticed.                                                                                                                                                                                                                                                                            |
| No systemic-pattern register | Repeat defects were rediscovered per domain.                                                                                                                                                                                                                                                                                       |
| No ORM↔database drift check  | The defect class that broke the first slice.                                                                                                                                                                                                                                                                                       |

### The one that mattered

`conftest.py` **hard-assigns** `DATABASE_URL = "sqlite:///:memory:"`, overriding
whatever the environment supplies. The default suite therefore runs on SQLite
built from the ORM, where ORM/database divergence cannot exist by construction
and row-lock contention cannot be reproduced. That is not a criticism of the
fixture — it is fast and isolated, and it is why PostgreSQL-gated modules must
build their own engine. It is recorded because it bounds what the 2 733-test
suite can ever prove.

## 2. Verification knowledge model

Implemented as code where code is the right home (`backend/tests/verification/harness.py`)
and as registries where prose is (`INVARIANTS.md`, `FAILURE_MODES.md`). No new
framework, no new runner, no new config language.

| Entity                                | Representation                                                                     |
| ------------------------------------- | ---------------------------------------------------------------------------------- |
| `VerificationScenario`                | One test function, named for the invariant it earns                                |
| `Invariant`                           | `INVARIANTS.md` row, id referenced from the test docstring                         |
| `FailureMode`                         | `FAILURE_MODES.md` row, `FM-0xx`                                                   |
| `Operation`                           | HTTP route + service method                                                        |
| `Precondition` / `Mutation`           | The module fixture's seed                                                          |
| `ConcurrentActor`                     | `harness.Actor`, raced by `harness.race`                                           |
| `ExpectedOutcome` / `ObservedOutcome` | Assertion vs. recorded run                                                         |
| `Evidence`                            | Evidence level from §5, plus the command that produced it                          |
| `NegativeProof`                       | Perturb → observe failure → restore → re-observe, recorded in the evidence package |
| `FailureInjection`                    | `app/clinical/failure_injection.py` stages                                         |
| `RecoveryAction`                      | Retry / replay assertions                                                          |
| `RegressionGuard`                     | `test_schema_drift_guard.py`, and the tripwires in the slice                       |
| `Finding` / `Risk` / `Owner`          | Register entry                                                                     |

## 3. Verification matrix

Operation × failure mode × invariant × required evidence. Status is what has
actually been executed, not what is intended.

| Operation                                                   | Failure mode                | Invariant                 | Required evidence                        | Status                                                            |
| ----------------------------------------------------------- | --------------------------- | ------------------------- | ---------------------------------------- | ----------------------------------------------------------------- |
| `POST /critical-care/infusions/{id}/verify`                 | FM-004 unauthorized actor   | INV-AUTHZ-01              | REAL_HTTP_POSTGRES                       | **VERIFIED** — 403 for 5 roles                                    |
| same                                                        | — (no auth)                 | INV-AUTHN-01              | REAL_HTTP_POSTGRES                       | **VERIFIED** — 401                                                |
| same                                                        | FM-019 schema mismatch      | INV-SCHEMA-01             | POSTGRESQL                               | **VERIFIED DEFECT** — NR-023                                      |
| same                                                        | FM-005 cross-tenant         | INV-TENANT-01             | REAL_HTTP_POSTGRES + NEGATIVE_PROOF      | **VERIFIED under repair** — 404; UNKNOWN as shipped               |
| same                                                        | FM-001 duplicate request    | INV-IDEM-01               | REAL_HTTP_POSTGRES                       | **VERIFIED under repair** — 409, 1 receipt                        |
| same                                                        | FM-002 concurrent request   | INV-CONC-01               | CONCURRENCY_POSTGRES                     | **VERIFIED under repair** — [200, 409]                            |
| same                                                        | FM-003 stale version        | INV-CAS-01                | REAL_HTTP_POSTGRES                       | **VERIFIED under repair** — 409 / 428 / 400                       |
| same                                                        | FM-014 duplicate transition | INV-STATE-01              | REAL_HTTP_POSTGRES                       | **VERIFIED under repair**                                         |
| same                                                        | FM-016 missing audit        | INV-AUDIT-01              | REAL_HTTP_POSTGRES                       | **VERIFIED under repair** — 1 row; **DEFECT as shipped** (NR-024) |
| same                                                        | clinical second-actor rule  | INV-ICU-01                | REAL_HTTP_POSTGRES                       | **VERIFIED under repair** — 422                                   |
| any protected mutation                                      | —                           | INV-AUDIT-02 immutability | POSTGRESQL                               | **VERIFIED** — DB trigger refuses DELETE                          |
| all guarded clinical writes                                 | FM-019                      | INV-SCHEMA-02             | POSTGRESQL                               | **VERIFIED DEFECT** — 3 of 8 domains                              |
| `POST` login / token                                        | FM-006, FM-007 lockout      | INV-AUTHN-02              | REAL_HTTP_POSTGRES                       | **UNKNOWN** — WP-004                                              |
| `blood_bank` reserve / issue                                | FM-001/002/008/009          | INV-IDEM-01, INV-CONC-01  | CONCURRENCY_POSTGRES + FAILURE_INJECTION | **VERIFIED** pre-existing                                         |
| `lims` 7 guarded commands                                   | FM-001..003                 | INV-IDEM-01, INV-CAS-01   | REAL_HTTP_POSTGRES                       | **NOT STARTED**                                                   |
| `ems`, `radiology`, `pharmacy`, `hospital` guarded commands | FM-001..003                 | same                      | REAL_HTTP_POSTGRES                       | **NOT STARTED**                                                   |

"VERIFIED under repair" is a deliberate, narrow status: the invariant was proven
on a database with the two missing columns added by hand to a disposable
instance. It is evidence that the control is correct and that the fix is
sufficient. It is **not** evidence about any database an operator can build
today, and must never be shortened to VERIFIED.

### Missing verification, computed

Guarded clinical commands per domain vs. real-PostgreSQL evidence:

| Domain        | Guarded commands | PostgreSQL tests  | Concurrency tests |
| ------------- | ---------------- | ----------------- | ----------------- |
| blood_bank    | 13               | 7                 | 5                 |
| critical_care | 8                | **1 (this pass)** | 0                 |
| lims          | 7                | 0                 | 0                 |
| radiology     | 4                | 0                 | 0                 |
| pharmacy      | 2                | 0                 | 0                 |
| ems           | 1                | 0                 | 0                 |
| hospital      | 1                | 0                 | 0                 |

## 4. Systemic failure patterns

| ID      | Pattern                                                           | Sev | Occurrences                 | Domains                                             | Detector                     | Status                         |
| ------- | ----------------------------------------------------------------- | --- | --------------------------- | --------------------------------------------------- | ---------------------------- | ------------------------------ |
| PAT-001 | ORM declares columns the migrated database lacks                  | P0  | **84 tables / 692 columns** | pharmacy 23, radiology 17, nhdw 14, nursing 13, +17 | `test_schema_drift_guard.py` | **DETECTED, OPEN**             |
| PAT-002 | Mapped table with no physical table on the only applicable build  | P0  | **405 of 781**              | platform-wide                                       | `harness.drift_report`       | **DETECTED, OPEN**             |
| PAT-003 | Verification harness duplicated per domain                        | P2  | 9 files, 3 env names        | tests                                               | this map                     | **CLOSED** by `harness.py`     |
| PAT-004 | Evidence exists for one domain only, then stops                   | P1  | 7 of 8 guarded domains      | clinical                                            | §3 matrix                    | **OPEN**                       |
| PAT-005 | In-handler controls masked by an earlier 500                      | P1  | 1 proven, class-wide        | clinical                                            | slice tripwires              | **DETECTED**                   |
| PAT-006 | A failing protected command writes no audit row                   | P0  | 1 proven                    | clinical                                            | slice tripwire               | **DETECTED, OPEN** (NR-024)    |
| PAT-007 | One physical table, two ORM owners that disagree about its schema | P1  | 1 (`national_facilities`)   | national + core                                     | `drift_report.multi_owned`   | **DETECTED** (sharpens NR-006) |
| PAT-008 | SQLite-only verification for a PostgreSQL-semantic claim          | P1  | suite default               | platform                                            | this map §1                  | **RECORDED**                   |

## 5. Evidence levels

| Level                  | Meaning                                                                   |
| ---------------------- | ------------------------------------------------------------------------- |
| `STATIC`               | Read or parsed. Never a runtime proof.                                    |
| `UNIT`                 | Ran in isolation. Never a PostgreSQL proof.                               |
| `SQLITE`               | Ran on SQLite. **Never** a concurrency, locking, FK or drift proof.       |
| `POSTGRESQL`           | Ran against migration-built PostgreSQL.                                   |
| `REAL_HTTP`            | Through the real app and routes.                                          |
| `REAL_HTTP_POSTGRES`   | Both.                                                                     |
| `CONCURRENCY_POSTGRES` | Two actors, two connections, barrier-released, one row.                   |
| `FAILURE_INJECTION`    | With an explicit stage failure.                                           |
| `NEGATIVE_PROOF`       | Protection perturbed, failure observed, protection restored, re-observed. |
| `RECOVERY_PROOF`       | Survived interruption without violating an invariant.                     |
| `PRODUCTION_OBSERVED`  | Seen in production. Nothing here carries this.                            |

Rules, restated because they are the point: a happy path is not a failure proof;
a sequential test is not a concurrency proof; possessing a permission is not an
authorization proof; a field existing is not tenant isolation; and a green
SQLite suite says nothing about PostgreSQL.

## 6. Prioritisation

Ranked by blast radius × clinical or security impact × evidence weakness — not
by how easy the test is to write.

1. **PAT-001 / PAT-002** — the platform cannot be deployed to a state its own
   code expects. Everything below is measured on a partial build until fixed.
2. **NR-024** — a failing clinical command leaving no audit row defeats
   reconstruction after an incident.
3. **INV-AUTHN-02** — account lockout has nowhere to store its state on both
   identity tables.
4. **The 7 guarded domains with zero evidence** — 23 protected clinical
   commands, mostly untested against PostgreSQL.
5. **NR-019** — adaptive-auth IDOR, still awaiting a policy decision.

## 7. Performance

| Step                                                 | Measured                              |
| ---------------------------------------------------- | ------------------------------------- |
| `alembic upgrade 20260908_0002` on an empty database | ~4 min, 391 tables, exit 0            |
| `alembic upgrade head` on an empty database          | **fails** at `20260505_0005` (NR-003) |
| Verification package, 25 tests, real PostgreSQL      | **13.4 s**                            |
| Same package with no database configured             | **0.19 s**, 25 skipped                |
| Platform-wide drift report, 781 classes × 391 tables | < 2 s                                 |
| Full backend suite (SQLite) for comparison           | 276 s, 2 733 tests                    |

The ratio is the point: 13 seconds of real-PostgreSQL evidence found a P0 that
276 seconds of SQLite could not, because the defect is invisible to a schema
built from the ORM.

## 8. Self-audit boundary

`scripts/self_audit_agent.py` is unchanged and ungranted. This layer decides
what is wrong, what must be proven and whether evidence suffices; the agent may
act only inside its existing limits. It is not given migration, deployment,
security-bypass, clinical-policy or merge authority, and nothing here asks it to
generate a migration — that needs a human, per `CLAUDE.md`.

## 9. Comparison against existing evidence

| Prior record                                                            | This pass                                                                                                        | Classification                             |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| NR-003 "pharmacy PK divergence blocks `upgrade head`"                   | Blast radius measured: a fresh deploy stops at `20260505_0005`; 405 mapped tables never created; 84 tables drift | **AGREE, materially widened**              |
| NR-006 "`national_facilities` mapped by two ORM classes"                | The two owners _disagree about the schema_: one drifts by 24 columns, the other is clean                         | **AGREE, sharpened**                       |
| Task #74 "retire the duplicate `national_facilities` owner" — completed | Both classes still load in one process                                                                           | **CONFLICT** — recorded, not resolved here |
| `tests/migrations/test_migration_graph_integrity.py`                    | Passes; cannot see branch reachability                                                                           | **AGREE, gap identified**                  |
| Blood Bank Wave 1 idempotency / concurrency evidence                    | Re-read, not re-run; unchanged                                                                                   | **AGREE**                                  |
| "8 domains use ClinicalCommandGuard"                                    | Confirmed; 3 of the 8 have drift on their core table                                                             | **AGREE, extended**                        |
| NR-019 adaptive-auth IDOR                                               | Untouched, still static-only                                                                                     | **UNVERIFIED** (unchanged)                 |

Nothing previous was overwritten. Prior evidence is archived, per the platform's
no-operational-delete principle.
