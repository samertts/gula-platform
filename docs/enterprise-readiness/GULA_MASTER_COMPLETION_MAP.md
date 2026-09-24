# GULA Master Completion Map

**Version 4 · generated 2026-09-10 · branch `claude/p0-2-pharmacy-reconciliation`**
**`production_ready: false`**

Machine-readable companion: `GULA_MASTER_COMPLETION_MAP.json` (same directory).
Update both after every batch. This is an inventory, not a plan of record for
features — it says what exists and what is proven, nothing about what should.

## 0. P0 fix and canonical decisions — complete

**NR-021 is FIXED and verified.** Two corrections to how it was first recorded:
the router *does* enforce `require_permission("system:admin")` globally, so the
exposure was across laboratories for admin holders rather than every
authenticated user; and the scope was **wider** than first found — nine
route-reachable methods queried without a tenant filter, on tables that all
carry `lab_id`. The service now takes a server-supplied `lab_id`, fails closed
when it is absent, and strips client-supplied `lab_id` from payloads. Proven to
catch the defect: with the scoping neutered, 5 of 7 new tests fail.

**NR-018 is PARTIALLY fixed.** Eight bases registered; GULA-ARCH-002 falls from
10 findings to 2, and the two that remain are the authorised exclusions
(insurance DEFER, task_engine RETIRE). Duplicate-ownership verified by MetaData
identity. **The zero-diff proof could not be obtained** — see NR-023 — so it is
not claimed.

**NR-023 is new and P0.** `alembic revision --autogenerate` cannot run at all:
it fails on `ehr_allergies.practitioner_id → national_practitioners`, a table no
metadata defines. Reproduced identically before the NR-018 registrations, so it
predates them. This plausibly explains why 402 tables have no physical schema —
**the tool that would create them does not work**, and every migration in the
chain must have been written by hand. Same root cause as NR-022.

**NR-007 is confirmed with measurement.** Four state values are shared by more
than one entity enum (`completed`, `in_progress`, `expired`, `discarded`), three
of them keys in the shared table — so a donation in progress is validated
against transfusion rules. Twenty-eight table keys are not any enum value at
all: synthetic names invented to dodge collisions. NR-004 and NR-020 were both
instances. Remediation needs a clinical owner to attribute states to entities.

**Canonical decisions recorded:** Core Patient and Core Facility are canonical;
national equivalents are projections or retired. Practitioner and Encounter
remain open.

**The 293 missing tables are grouped** into B3 national core (5), B4 national
platform (29), B5 clinical record (45), B6 care continuity (47), B7 governance
and data (79), B8 hospital (9), B9 deferred until their domain exists (79).
See `GULA_BATCH_3_NATIONAL_CORE_SPEC.md`.

## 0. BATCH-2 (canonical disposition) — complete

Disposition only. **No migrations created, no schema changed, no domain built.**
Full detail: `GULA_CANONICAL_DISPOSITION_MATRIX.{md,json}` and
`GULA_CANONICAL_ARCHITECTURE_DECISIONS.md`.

All 807 mapped tables carry a rule-derived disposition:

| `KEEP` | `RECONCILE` | `CREATE_PHYSICAL` | `CROSS_DOMAIN_OWNER` | `DEFER` | `RETIRE` | `MERGE` |
|---|---|---|---|---|---|---|
| 209 | 194 | 216 | 77 | 70 | 39 | 2 |

**The structural finding, and it reorders everything.** Four of the five
most-depended-on tables in the repository do not exist: `national_practitioners`
(58 inbound references), `national_citizens` (51), `national_patients` (51),
`national_encounters` (42). The fifth, `national_facilities` (44), is the only
one that *is* physical — and is the single table mapped by two declarative bases,
which is NR-006 arrived at independently from foreign-key evidence.

`care_continuum` (45/45 tables), `ehr` (16/18), `nursing` and `national_data` all
declare foreign keys into that national core. **EHR is not the critical path; the
national core is.** Building EHR first would move the same unresolved foreign
keys one layer up and settle nothing. Recorded as **NR-022**.

The 179 unmeasured operations reduce to **61 genuinely unresolved** (58
`national`, 3 `identity`). The other 118 belong to `ai_fabric`, `kernel`,
`integration`, `platform` and `certification` — layers that map no tables at all,
so "no table" is the right answer there rather than a gap.

**Two new P0s.** NR-021: `GET /blood-bank/inventory` queries a table that has
`lab_id` without filtering it, so any authenticated user reads every laboratory's
blood inventory; `POST /blood-bank/components` mass-assigns a raw dict onto a
model that also carries `lab_id`. Both reachable. NR-022 above. **NR-019 closed**
— importing `app.ai` no longer writes to the database.

## 0a. BATCH-1 (verification truth) — complete

Scope was verification only: **no application schema, migration, ORM or route
change**. Full detail in `GULA_CI_TRUTH.md` and the `batch_1` block of the JSON.

| | Before | After |
|---|---|---|
| Tables GULA-SCHEMA-002 compares | 27 (pharmacy only) | **405**, across 20 declarative bases |
| GULA-SCHEMA-002 findings | 0 — read as clean | **1,677** |
| Mapped tables with no physical table | not detected | **402** (GULA-SCHEMA-003) |
| Cross-domain missing dependencies | not detected | **145** (GULA-SCHEMA-004) |
| Bases invisible to alembic autogenerate | not detected | **10 of 20**, 203 tables (GULA-ARCH-002) |
| Model modules unmeasured | unknown | **0** |
| Gate states | PASS/FAIL/BLOCKED | + **DID_NOT_RUN**, **UNMEASURED** |
| Full CI result on this branch | **UNKNOWN** — never ran | **GREEN**: 2,746 passed, 157 skipped, 0 failed (RED at 1 failed until NR-020 was resolved) |
| Boot-time AI seeding | failed every boot, 0 rows | succeeds, 5 rows, boot clean |

**A measurement-basis correction.** Version 1 counted `__tablename__`
declarations in source: 828 tables, 418 missing. The detector imports the model
modules and reads real mapper metadata: **807 mapped tables across 20 bases,
402 missing**. Both are accurate measurements of different things; the mapper
figure is authoritative, because it is what SQLAlchemy actually maps. The v1
domain tables below are still source-derived and are superseded by the detector
output wherever they disagree.

**Two v1 P0s are now detector findings rather than prose**: EHR's 18/18 missing
tables (GULA-SCHEMA-003) and Pharmacy's write to `ehr_medication_dispenses`
(GULA-SCHEMA-004) — the latter being the finding per-domain verification
structurally cannot make.

**MCM-P0-4 is now measured, not merely described.** 2 of 30 workflows gate every
PR; `ci.yml` gates only PRs into `main`/`staging`. Run locally, full CI was RED
on one pre-existing clinical-safety test; that blocker (NR-020) has since been
resolved and full CI now measures **green**: 2,746 passed, 157 skipped, 0 failed.
Widening the trigger is still **not done** — it changes which checks are required
on three open PRs, which is merge policy and the repository owner's call. See
`GULA_CI_TRUTH.md` §4.

## 0. How these numbers were obtained

Nothing here is inferred from naming or from the presence of code.

| Measurement | Method |
|---|---|
| Physical tables | Read from a database migrated to alembic head `20260912_0001`, not from migration source |
| Reachable endpoints | The app was **booted** and FastAPI's route tree walked, including lazy `_IncludedRouter` wrappers. Counting `@router.get` decorators overstates by 304 |
| Table backing per endpoint | Exact import-name resolution (route → same-domain service → model class → `__tablename__`). A transitive closure was tried first and rejected: it attributed unrelated tables to Pharmacy, whose 27 tables are all present |
| Status | Assigned from those measurements only. "Code exists" never yields VERIFIED |

Re-run with the scan scripts rather than re-deriving by hand.

## 1. Total inventory

| Item | Count |
|---|---|
| Backend domain packages (`backend/app/*/`) | 63 |
| Backend Python files / lines | 1,901 / 274,400 |
| Endpoint decorators declared | 2,406 |
| **Reachable operations (booted app)** | **2,102** across 1,789 distinct paths |
| ORM models with `__tablename__` | 829 (828 distinct tables) |
| **Physical tables at head** | **423** |
| **ORM tables with no physical table** | **418** |
| Physical tables with no ORM model | 13 |
| `declarative_base()` instances | 24 |
| Alembic migrations / head | 106 / `20260912_0001` |
| Backend test files / test functions | 217 / 2,766 |
| CI workflows | 30 |
| Documentation markdown files | 633 |
| Frontend-v3 routes / frontend workspaces | 94 / 4 |
| Security modules (`app/security/`) | 21 |
| Infrastructure | k8s 37, terraform 68, helm 38, config 102 files |
| DR/backup scripts | 10 (`backup`, `pitr-recover`, `dr-failover`, `dr-failback`, `restore-test`, …) |

## 2. The headline finding

**418 of 828 ORM-declared tables (50.5%) do not exist in a fully migrated
database, and 870 of 2,102 reachable operations touch one.**

| Endpoint backing | Operations |
|---|---|
| All tables present | 1,053 |
| **Touch at least one missing table** | **870** |
| No ORM class resolved statically — **unmeasured, not clean** | 179 |

Verified empirically: `select 1 from ehr_allergies` → `UndefinedTable`, and
`POST /ehr/allergies` is registered in `factory.py` `feature_routes` and reaches
`ehr_service.create_allergy` → `AllergyIntolerance(__tablename__="ehr_allergies")`.

There is exactly one `Base.metadata.create_all` in `backend/app/`, in
`engineering/testing/unit.py` — a test helper. Nothing creates these tables at
runtime. This is the same defect class P0-2 fixed for Pharmacy's 27 tables,
at 418 tables' scale.

## 3. Completion by domain

Full table in the JSON. `serving` = reachable operations touching that domain's
tables wherever defined; `broken` = those touching one of its missing tables.
The two differ from a domain's own operation count when its routes live in the
flat `app/routes/` package (ehr, clinical, care_continuum, hospital,
national_data), which is why per-package counting alone would have
misclassified EHR as unstarted rather than broken.

### BROKEN — P0 (13 domains, 949 operations serving them)

| Domain | Tables | Missing | Serving | Broken |
|---|---|---|---|---|
| `ehr` | 18 | 18 | 275 | 275 |
| `national_data` | 36 | 36 | 239 | 239 |
| `national` | 113 | 105 | 176 | 145 |
| `clinical` | 41 | 39 | 135 | 135 |
| `governance` | 64 | 58 | 112 | 112 |
| `hospital` | 14 | 10 | 101 | 101 |
| `care_continuum` | 45 | 45 | 74 | 74 |
| `nursing` | 15 | 2 | 157 | 66 |
| `document_intelligence` | 21 | 21 | 50 | 50 |
| `roadmap` | 8 | 8 | 22 | 22 |
| `knowledge_graph` | 3 | 3 | 13 | 13 |
| `command_intelligence` | 5 | 5 | 9 | 9 |
| `simulation` | 5 | 5 | 8 | 8 |

### PARTIALLY_VERIFIED — P1 (7)

| Domain | Evidence |
|---|---|
| `pharmacy` | 27/27 tables present, GULA-SCHEMA-002 0 findings — **but** `services.py:1344` writes `ehr_medication_dispenses`, which does not exist |
| `models` (core: patients, labs, orders, results) | 67/68 tables present, 1,239 operations served, 1 missing table unreferenced |
| `radiology` | 17/18 present, 108 served, missing table unreferenced |
| `nhdw` | 14/15 present, 90 served |
| `health_data` | 17/17 missing but **11 reachable operations resolved no model — unmeasured** |
| `research_platform` | 7/7 missing, 49 reachable operations resolved no model — **unmeasured** |
| `financial` | 6/9 missing; Phase A is schema-only by design, routes gated off |

### NOT_STARTED — P2 (1)

`insurance` — 30 ORM tables, none exist, no reachable operation resolves to them.

### IMPLEMENTED (42)

Includes `identity` (87 tables, 0 missing, 355 operations), `lims`, `payments`,
`blood_bank`, `ems`, `biomedical`, `critical_care`, `kernel`, `control_plane`,
`devices`, `citizen_platform`, `public_health`, `security`, `core`, `audit`.
IMPLEMENTED here means *its tables exist and its endpoints resolve to them* —
it is not a claim that behaviour is verified.

## 4. P0 blockers

| ID | Blocker | Evidence |
|---|---|---|
| **MCM-P0-1** | 418 ORM tables have no physical table; 870 reachable operations touch one | Migrated DB at head; booted app; exact name resolution |
| **MCM-P0-2** | The entire EHR domain is registered and reachable with zero backing tables (275 operations, 18/18 tables missing) | `feature_routes` includes `ehr`, `ehr_fhir`, `cds_hooks`; `select 1 from ehr_allergies` → UndefinedTable |
| **MCM-P0-3** | **Patient-attributed pharmacy sales fail.** `pharmacy/services.py:1344` constructs `MedicationDispense` (`ehr_medication_dispenses`) when a sale carries a patient or citizen id; that table does not exist. Anonymous sales are unaffected | Import + table probe confirmed; conditional on `record_patient_id` |
| **MCM-P0-4** | **The full CI pipeline never runs on the stacked PRs.** `ci.yml` (syntax-gate, migration-check, lint, 2,766-test `test` job, security-scan, build) triggers only on PRs into `main`/`staging`. #256/#257/#258 target each other, so the only gate is `iam-hardening.yml`, which runs a narrow pytest selection (identity, clinical_gateway, security_regression, tenant_isolation_matrix, 4 migration tests) | Workflow `on:` blocks; #258's 6 checks all originate from `iam-hardening.yml`, `frontend-bundle-budget.yml` and Vercel |

**MCM-P0-4 is why "6/6 green" must not be read as "CI green".** It is a
verification-integrity defect of the same family as NR-016.

## 5. P1 blockers

| ID | Blocker | Evidence |
|---|---|---|
| ~~MCM-P1-1~~ | **FIXED in BATCH-1.** The detector now discovers all 20 declarative bases (405 tables compared), and GULA-SCHEMA-004 catches cross-domain dependencies | 41 tests in `tools/gula_intel/tests/` |
| **MCM-P1-2** | 179 reachable operations resolve to no ORM class: unmeasured, not clean | Exact-resolution pass |
| ~~MCM-P1-3~~ | **FIXED in BATCH-1.** 17 `:param::cast` collisions across `ai/governance.py`, `ai/memory.py`, `ai/vector_store.py` rewritten as `CAST(:param AS type)`; boot now seeds 5 rows | `backend/tests/test_ai_sql_placeholder_regression.py` (3 tests) + clean boot |
| **MCM-P1-6** | `model_registry = ModelRegistry()` runs at **import** time (`ai/governance.py:108`), so importing `app.ai` writes to whatever `DATABASE_URL` names. Harmless while the statement was broken; live now that MCM-P1-3 is fixed | Observed during detector runs and in the test suite |
| ~~MCM-P1-7~~ | **FIXED (NR-020).** The transfusion state machine had no `verified` state at all, so `start_transfusion_safely` — which requires `status == VERIFIED` and targets `in_progress` — could never succeed. One key added; full CI now green | `tests/blood_bank/test_domain_safety.py` (2 new tests); suite 2,746 passed, 0 failed |
| **MCM-P1-4** | 20 declarative bases (19 hand-written + generators); **10 are absent from alembic `target_metadata`**, covering 203 mapped tables, so autogenerate reports no drift for any of them — an empty diff indistinguishable from an accurate one. Registering a base changes what autogenerate emits, so it is a schema decision and was not made here | GULA-ARCH-002, resolved by MetaData identity |
| **MCM-P1-5** | Negative-register status drift: NR-003 still reads `OPEN — BLOCKED` though PR #256 carries its fix | Register vs. PR stack |
| NR-006 | `national_facilities` mapped by two ORM classes on different bases | Existing register entry |
| NR-007 | Clinical state machine is entity-agnostic by construction | Existing register entry |

## 6. P2–P5 backlog

P2: NR-008 (`signxml` unpinned), NR-009 (artifact quota), NR-010 (`if:always()`
masks the failing step), NR-011 (mobile nav accessible name), **NR-017**
(pharmacy warehouse undecided), `insurance` domain, dead models in
`health_data`/`research_platform`.
P3: NR-013 (narrow audit coverage), NR-014 (no verified capacity numbers),
NR-015 (local Postgres stoppage — local only).
P4/P5: none recorded. No entry was invented to fill these tiers.

## 7. Production readiness

A score never hides a P0. Any row touched by MCM-P0-1..4 is capped at BLOCKED.

| Dimension | Status | Basis |
|---|---|---|
| Architecture | **BLOCKED** | ORM and physical schema disagree on 418 tables |
| Security | PARTIALLY VERIFIED | 21 modules, RBAC/ABAC, tenant-isolation matrix green — but only on the narrow gate (MCM-P0-4) |
| Identity | PARTIALLY VERIFIED | 87 tables all present, 355 operations, dedicated certification script; behaviour proven only for the identity suite |
| Authorization | PARTIALLY VERIFIED | `authz` reachable, ABAC tests exist; not exercised across broken domains |
| Data integrity | **BLOCKED** | 870 operations can fail mid-transaction on a missing table |
| Migration safety | **VERIFIED** | 106 revisions, single head, round-trip enforced, fail-closed identity migrations demonstrated refusing on non-empty tables |
| Concurrency | PARTIALLY VERIFIED | Proven for Pharmacy stock on two real connections; unproven elsewhere |
| Reliability | PARTIALLY VERIFIED | Circuit breaker, auto-repair, adaptive concurrency, degraded mode implemented; no chaos evidence at this head |
| Observability | PARTIALLY VERIFIED | 5 health endpoints, Prometheus + Grafana provisioned, structured logging; no SLO evidence |
| Performance | NOT STARTED | No benchmark at this head |
| Backup/restore | PARTIALLY VERIFIED | 10 scripts including `restore-test.sh`/`validate-restore.sh`; no execution evidence |
| Disaster recovery | PARTIALLY VERIFIED | `dr-failover`/`dr-failback`/`dr-test` exist; untested here |
| Infrastructure / HA | PARTIALLY VERIFIED | k8s, terraform, helm, HAProxy scaling present; not exercised |
| Interoperability | **BLOCKED** | FHIR/HL7 surfaces sit on EHR tables that do not exist |
| Testing | **BLOCKED** | 2,766 tests exist; the PR gate runs a narrow subset (MCM-P0-4) |
| Operations | PARTIALLY VERIFIED | Makefile, kill switch, diagnostics, runbooks |
| Governance | PARTIALLY VERIFIED | Negative register, ADRs, constitution gate — with status drift (MCM-P1-5) |
| Documentation | VERIFIED | 633 markdown files; the reconciliation trail is evidence-linked |

## 8. National-scale readiness

No capability is marked complete on the strength of a prototype. NR-014 already
records that no verified national capacity numbers exist.

| Capability | Status | Basis |
|---|---|---|
| National identity integration | PARTIALLY VERIFIED | `identity` 87/87 tables, 355 operations; `national_identity` route registered |
| Multi-tenant scale | PARTIALLY VERIFIED | `lab_id` isolation enforced and tested; not measured at scale |
| Population scale | NOT STARTED | Demo generator claims 100K patients in twin mode; unmeasured here |
| Facility scale | **BLOCKED** | NR-006: `national_facilities` double-mapped |
| Workforce scale | PARTIALLY VERIFIED | 65+ roles in the demo generator; RBAC 10×16 |
| Laboratory network | PARTIALLY VERIFIED | `lims` 35/35 tables, 69 operations |
| Pharmacy network | PARTIALLY VERIFIED | 27/27 tables; MCM-P0-3 blocks patient-attributed sales |
| Hospital network | **BLOCKED** | 10/14 tables missing, 101 operations affected |
| Emergency / EMS | PARTIALLY VERIFIED | 12/12 tables, 26 operations |
| Public health | PARTIALLY VERIFIED | tables present, 19 operations |
| Epidemiology | NOT STARTED | No verified surveillance pipeline at this head |
| Supply chain | **BLOCKED** | NR-017: warehouse/store modelled, implemented nowhere |
| Interoperability | **BLOCKED** | See production matrix |
| Offline operation | PARTIALLY VERIFIED | `edge_agent`, `edge` tables present, 22 operations |
| Synchronization | PARTIALLY VERIFIED | Outbox pattern implemented and tested |
| National analytics | **BLOCKED** | `nhdw` present but `national_data` 36/36 tables missing, 239 operations |
| Disaster recovery | PARTIALLY VERIFIED | Scripts exist, untested |
| Security operations | PARTIALLY VERIFIED | Intrusion detection, firewall, zero-trust modules present |
| Operational governance | PARTIALLY VERIFIED | Register + certification scripts; MCM-P1-5 drift |

## 9. Critical-path dependency graph

```
verification gate (MCM-P0-4)          HARD BLOCKER on every batch below
        │                             nothing can be proven while the gate is narrow
        ▼
schema truth: ORM ⇄ physical          HARD BLOCKER on ehr, clinical, national,
  (MCM-P0-1)                          national_data, governance, hospital,
        │                             care_continuum, document_intelligence
        ├────────────► ehr (275 ops)  HARD BLOCKER on interoperability (FHIR/HL7,
        │                             cds_hooks) and on pharmacy MCM-P0-3
        ├────────────► clinical (135) HARD BLOCKER on care_continuum
        ├────────────► national_data  HARD BLOCKER on national analytics
        │              (239)
        └────────────► governance     SOFT DEPENDENCY for clinical delivery
                       (112)
identity (87/87, 355 ops)             SOFT DEPENDENCY — already satisfied
core models (67/68, 1,239 ops)        SOFT DEPENDENCY — already satisfied
migration chain (106, single head)    SOFT DEPENDENCY — already satisfied
NR-017 warehouse                      OPTIONAL FUTURE CAPABILITY — decision, not code
performance / epidemiology            OPTIONAL FUTURE CAPABILITY
```

Hard blockers: MCM-P0-4, then MCM-P0-1 and its four dependents.
Everything else is a soft dependency or optional.

## 10. Queues

**QUEUE A — must fix before further feature development**
A1 MCM-P0-4 verification gate · A2 MCM-P0-1 schema-truth triage (decide per
domain: build the schema, or delete the models) · A3 MCM-P0-3 pharmacy→EHR
dispense · A4 MCM-P1-1 detector scope · A5 MCM-P1-3 boot seeding ·
A6 MCM-P1-5 register drift.

**QUEUE B — build next**
B1 EHR + interoperability schema (275 ops) · B2 clinical + care_continuum (209)
· B3 national + national_data + governance (496) · B4 hospital (101).

**QUEUE C — later**
NR-017 decision, `insurance`, dead models in `health_data`/`research_platform`,
`roadmap`/`simulation`/`knowledge_graph`/`command_intelligence` (52 ops),
performance benchmarking, epidemiology, NR-008/009/010/011/013/014/015.

## 11. Batch plan

Not started. No batch below has been implemented.

| Batch | Objective | Domains | Depends on | Outputs | Verification gate | Complexity |
|---|---|---|---|---|---|---|
| **BATCH-1 · Verification truth** | Make the PR gate capable of proving anything: run the real pipeline on stacked PRs; extend GULA-SCHEMA-002 beyond Pharmacy to all 63 domains so the 418-table gap is a detector finding, not a manual discovery; fix boot seeding; correct register drift | CI, detectors, `ai` | — | ci.yml/quality-changed-files triggers; detector scope; `CAST(:p AS jsonb)`; NR-003 status | Detector reports the 418 gap; full suite runs on a stacked PR | **MEDIUM** |
| **BATCH-2 · Schema-truth triage** | For each of the 418 tables decide, with evidence, *build* or *delete* — never both. Produce a per-domain disposition matrix like P0-2 Phase 2A. **Decision batch: no schema change** | all 13 BROKEN + 3 dead-model domains | BATCH-1 | Disposition matrix + ADR per domain | Every one of the 418 has a recorded disposition | **HIGH** |
| **BATCH-3 · EHR + interoperability** | Give EHR a physical schema, or retire it. Unblocks FHIR/HL7/cds_hooks and MCM-P0-3 | `ehr`, `fhir`, `interoperability`, `pharmacy` | BATCH-2 | Migrations, ORM reconciliation, fail-closed identity pattern | 275 operations resolve; patient-attributed sale succeeds | **CRITICAL** |
| **BATCH-4 · Clinical + care continuum** | 209 operations | `clinical`, `care_continuum` | BATCH-3 | as above | 209 operations resolve | **HIGH** |
| **BATCH-5 · National platform** | 496 operations, the largest surface | `national`, `national_data`, `governance` | BATCH-2 | as above | 496 operations resolve | **CRITICAL** |
| **BATCH-6 · Hospital** | 101 operations; resolve NR-006 first | `hospital` | BATCH-2, NR-006 | as above | 101 operations resolve | **MEDIUM** |

Deliberately not split further: each batch is one domain group reconciled
whole, the M3/M4 pattern that worked — a narrow standalone conversion was
explicitly rejected there and is rejected here.

## 12. Exact next batch

**BATCH-1 — Verification truth.** It is first because every other batch's
evidence is worthless until the gate can produce it, and because extending
GULA-SCHEMA-002 converts the 418-table gap from a one-off discovery into a
standing regression signal. It is also the cheapest: no schema change, no
migration, no domain decision.

BATCH-2 cannot start before BATCH-1 and is a **decision** batch — it must not
create migrations.

## 13. Deliberately deferred

Performance benchmarking; epidemiology; `insurance`; NR-017 (awaiting your
decision); NR-013/014; NR-015 (local only); mobile/desktop workspaces (4 tsx
files in `mobile-expo`, no reachable backend dependency); `apps/` and
`packages/` (140 + 10 tsx, not on the critical path); P4/P5 (none exist —
none were invented).

## 14. New contradictions and intersections

1. **A verified domain depends on a non-existent one.** Pharmacy is
   schema-clean at 27/27 yet writes an EHR table that does not exist. Domain-scoped
   verification cannot see across a domain boundary.
2. **Declared ≠ reachable.** 2,406 decorators, 2,102 reachable operations. Any
   count taken from decorators overstates by 304.
3. **Green ≠ tested.** #258's 6/6 comes from a narrow gate; the 2,766-test suite
   has never run on this branch stack.
4. **Package location ≠ domain.** Routes in the flat `app/routes/` package serve
   `ehr`, `clinical`, `care_continuum`, `hospital` and `national_data`. Attributing
   by package would have called EHR unstarted rather than broken.
5. **Model count ≠ capability.** `insurance` has 30 models and zero reachable
   operations; `identity` has 87 models and 355.

## 15. Existing defects that must NOT be rediscovered

Recorded in `docs/architecture/GULA_MASTER_NEGATIVE_REGISTER.json` (17 findings):
NR-003 (pharmacy PK divergence — fix is in PR #256, status drift per MCM-P1-5),
NR-006 (`national_facilities` double-mapped), NR-007 (entity-agnostic clinical
state machine), NR-008, NR-009 (artifact quota), NR-010, NR-011, NR-012
(accepted design), NR-013, NR-014, NR-015 (local Postgres stoppage; use the
`pgup.sh` helper), NR-016 (quality gate false PASS — **fixed**), NR-017
(pharmacy warehouse — awaiting decision).

Also settled and not to be re-litigated: `store_id`/`batch_id` nullability on
`pharmacy_stock_levels` is by design; `warehouse_id` stays out of
`uq_pharmacy_stock`; `patient_id`/`citizen_id`/`encounter_id`/
`medication_dispense_id` remain `String(26)` because they point out of Pharmacy;
`tests/test_security.py::TestEncryption` fails locally on an invalid Fernet key
and fails identically at the parent commit.

## 16. Files created or modified by this scan

Created: `docs/enterprise-readiness/GULA_MASTER_COMPLETION_MAP.md`,
`docs/enterprise-readiness/GULA_MASTER_COMPLETION_MAP.json`.

**No application code, schema, migration, ORM, service, API, test or CI file was
modified.** This was an inventory and planning task.
