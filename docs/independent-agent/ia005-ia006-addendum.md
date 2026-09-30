# IA-005 / IA-006 — addendum: contract sweep, impact matrix, per-operation verification

Follows `cc1dba74`. Same lane (`claude/independent-audit-1`, worktree
`/home/user/gula-audit`), same database (`gula_agent2`, head `20260916_0001`,
423 tables, verified untouched). RB-4, RB-5 and RB-6 not started.

**Why this addendum exists.** The first IA-005 pass fixed the 12 ORM bases and
claimed the serializer repaired. A full sweep of *every* column-walking serializer
— which the first pass did not do — found **five more live sites** carrying the
identical defect, and **corrected a wrong conclusion** the first pass reached.

---

## 1. Correction: `col.key` is not the mapped attribute

The first pass reported `app/nursing/routes.py::_model_to_dict` as *immune* because
it reads `getattr(instance, c.key)` rather than `c.name`. **That was wrong.**

Measured on a real model:

```
AllergyIntolerance: column.name = 'metadata'   column.key = 'metadata'
mapper key for that column            = ['metadata_']
type(getattr(NursingTask(), c.key))   = MetaData
```

For `metadata_ = Column("metadata", ...)` SQLAlchemy leaves **both** `col.name` and
`col.key` as `"metadata"`; only the mapper carries `metadata_`. So `col.key` is
exactly as defective as `col.name`, and the nursing helper was returning the
registry. The original guard matched only `col.name`, which is why it passed.

Two consequences, both corrected here: the guard now matches `col.name` **and**
`col.key`, and the "two external key conventions" claim is withdrawn — there is
**one** convention, the physical column name `metadata`.

## 2. Five further sites, all on tables that physically exist

| site | lookup | tables affected | in head DB |
|---|---|---|---|
| `app/nhdw/offline.py:265` — offline device sync | `col.name` | **13 of 13** synced `nhdw_*` tables carry the column | **all 13 present** |
| `app/nursing/routes.py:40` — `_model_to_dict` | `col.key` | nursing_tasks, nursing_shifts, delegations, escalations, handovers | present |
| `app/nhdw/routes.py:56` — `_model_to_dict` | `col.key` | the `nhdw_*` hospital set | present |
| `app/routes/hospital.py:264` — `_model_to_dict` | `col.key` | the `nhdw_*` hospital set | present |
| `app/blood_bank/api/routes.py:638` — `_phase2_dict` fallback | `col.name` | any model reaching the fallback | present |

This changes IA-005's severity picture materially. The first pass concluded the
defect's reachable blast radius was mostly the dormant `/ehr` surface. It was not:
**offline clinical sync, nursing, hospital ward management and blood bank all run
on tables that exist**, so these were live failures, not latent ones.

`app/contracts/generator.py:152` was checked and is **not** a defect — it reads
`col.type` / `col.nullable` / `col.doc` for schema generation and never reads a
value off an instance.

## 3. The serialization contract, completed

The first pass established the contract from the 12 bases. This pass completes it
across the whole response surface.

| question | evidence | answer |
|---|---|---|
| is `to_dict()` the response contract, or do response models bypass it? | of **2 103** served operations, only **135** declare a response schema; **1 968** are untyped and return whatever the serializer produced | `to_dict()` **is** the contract |
| do any declared response models expose the column? | 4 declare a `metadata`-ish property, all named `safe_metadata` — a separate billing-audit field, not the physical column | **no** |
| does `/ehr` declare any response model? | **0 of 86** operations | no — raw dicts throughout |
| does any Pydantic `from_attributes` model carry `metadata_`? | 21 files declare such models; none exposes the affected column | **no** |
| what external key must be preserved? | every serializer keys by the physical column name | **`metadata`** |

So there is exactly one serialization path for affected models, and the fix
preserves its key. **No JSON key changed anywhere; only the value did, from a
schema registry to the column's value.**

## 4. Impact matrix — 137 models

Full per-model matrix (model, table, physical `metadata` column, mapped attribute,
serializer, endpoint exposure, external JSON key, risk) is in
`ia005-impact-matrix.md`. Summary:

| dimension | value |
|---|---|
| mapped classes examined | **780** |
| with a physical `metadata` column | **137** |
| mapped as `metadata_` / `extra_metadata` | 132 / 5 |
| external JSON key, all 137 | `metadata` |
| with a `to_dict()` | 119 (18 without) |
| **HIGH risk** — served endpoint **and** a serializer | **34** |
| ├─ table **present** in the head DB → was a **live** failure | **10** |
| └─ table absent → dormant behind IA-006 | 24 |
| **MEDIUM risk** — serializer, no served endpoint found | 85 |
| **LOW risk** — no serializer, unreachable by this path | 18 |

The 34 HIGH-risk models are exposed on far more than `/ehr`: `/nursing`,
`/pharmacy`, `/care-continuum`, `/fhir`, `/national-data`, `/citizen-platform`,
`/radiology`, `/lims`, `/compliance`, `/patient-card`, `/test-results`, `/authz`,
`/admin`, `/health-data`, `/intelligence`, `/public-health`. This replaces the
first pass's "non-`/ehr` route exposure is UNKNOWN" with a measurement.

## 5. Runtime proof against the proven head database

Every newly-fixed serializer, exercised on a model whose table exists in
`gula_agent2`:

| serializer | table | table in head | `metadata` value | result |
|---|---|---|---|---|
| `nursing._model_to_dict` | `nursing_tasks` | yes | `{'probe': 'rb3'}` | OK |
| `nursing._model_to_dict` | `nursing_shifts` | yes | `{'probe': 'rb3'}` | OK |
| `nhdw._model_to_dict` | `nhdw_admissions` | yes | `{'probe': 'rb3'}` | OK |
| `hospital._model_to_dict` | `nhdw_clinical_tasks` | yes | `{'probe': 'rb3'}` | OK |
| `blood_bank._phase2_dict` | `nhdw_care_plans` | yes | `{'probe': 'rb3'}` | OK |
| `nhdw.offline` serializer | `nhdw_discharges` | yes | `{'probe': 'rb3'}` | OK |

No `MetaData` in any payload, and `jsonable_encoder` terminates on each.

## 6. Tests

`backend/tests/verification/test_orm_metadata_column_serialization.py` — **17
tests** (13 from the first pass, 4 added here).

| stage | result |
|---|---|
| first-pass baseline (before any fix) | 9 failed, 4 passed |
| after the base fix | 13 passed |
| after adding the 4 new tests, before the 5 new site fixes | **2 failed**, 14 passed — the sweep named `app/nhdw/offline.py:270` |
| after fixing all 5 sites | **17 passed** |
| perturbation: `offline.py` back to `col.name` | **1 failed** — site named |
| perturbation: `nursing/routes.py` back to `col.key` | **1 failed** — site named, which the *old* guard would have missed |
| restored | **17 passed** |

The sweep is pinned as an **empty set**, so any new copy of the pattern anywhere
under `app/` fails the suite.

Full backend suite: **1 failed, 2850 passed, 185 skipped** (318 s), against 2 846
passed before this addendum — the 4 new tests, no regression. The single failure is
the same pre-existing one recorded in `test-matrix.md`
(`test_no_module_is_loaded_under_two_names`, the kernel tests loading
`backend.app.integration.connectors.ntfy` under a second name), already proven
pre-existing by stashing the change and reproducing it identically. Lint: the files
this pass touched are clean of everything it introduced; `E702` and one `B904` in
`app/nursing/routes.py` pre-date it. Suite numbers remain **SQLite** evidence —
`tests/conftest.py:28` forces `DATABASE_URL`.

## 7. IA-006 — per-operation verification, unchanged verdict

Head-DB runtime re-run after all fixes: **85 × `500` `UndefinedTable`, 1 × `403`,
0 × 2xx.** Head DB still 423 tables, head `20260916_0001`.

Route↔table dependency split for the 86 operations:

| | operations |
|---|---|
| depend **only on missing** tables | **86** |
| depend on both a missing and an existing table | 0 |
| depend only on existing tables | 0 |
| depend on an external/canonical table (nhop `citizens`) | 0 — `/ehr` never references it |

Per-operation detail — class, HTTP status, DB dependency, authorization result and
serialization result for all 86 — is in `ia006-per-operation.md`. Aggregate:

| dimension | value |
|---|---|
| REAL | **0** |
| PARTIAL | **1** (the facility-scoped clinical read; authorization layer verified) |
| BROKEN | **85** |
| serialization was IA-005 exposed → now fixed | **59** |
| serialization never exposed (no record returned / no column / allowlisted) | 27 |
| authorization: authenticated but no permission check (NR-070) | 85 |
| authorization: deny-by-default gate, verified discriminating | 1 |

**Classification and migrations unchanged: A=0, B=0, C=1, D=0, E=18, F=0, and zero
migrations authored.** ADR-016 (Accepted, not superseded) forbids the tables; the
reasoning is in `ia005-ia006-remediation.md` Part 2 and is not restated here.

## 8. Blockers

| id | blocker | why it cannot be closed here |
|---|---|---|
| **IA-006** | needs an ownership decision | ADR-016's Phase 2 mandates EHR write support while forbidding new EHR tables, and never says where new clinical content persists. Architecture-committee decision. |
| **IA-006 / `national_patients`** | needs a canonical-identity decision | hub of 66 FKs; `nhop-platform` owns `citizens`; ADR-016 composes the Patient from `patients`. |
| **IA-007** | billing path | `insurance/financial/engine.py:840-842` raises `TypeError`. Two identifiers fix it, but invoice logic needs human approval per `CLAUDE.md`. |
| **IA-004** | out of scope by instruction | **remains OPEN and was not modified.** |
