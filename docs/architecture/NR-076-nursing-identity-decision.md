# NR-076 — the nursing decision gate

**Status:** BLOCKED — P0. Evidence complete; the decision is not mine to take.
**Measured:** 2026-09-26, against a database built from this branch's own lineage.
**What is blocked:** every write to all fifteen nursing tables.
**What is not blocked:** reads. They work, which is why this was never noticed.

---

## 1. The state, measured rather than described

`alembic upgrade 20260716_0002` on an empty database produces 116 tables, of which
15 are the nursing domain. That schema was then compared, column by column, with
what `app/nursing/models.py` declares. It was also verified **byte-identical** to
the nursing schema in the harness database, so — unlike the hospital tables of
NR-073 — nursing carries no foreign-lineage caveat. This is what an operator of
this branch gets.

| measure | value |
|---|---|
| nursing tables mapped by the ORM | 15 |
| nursing tables the migration creates | 15 |
| columns the ORM declares that the table lacks | **149** |
| columns the table has that the ORM ignores | **176** |
| column type mismatches | **41** |
| primary keys that disagree | **15 of 15** |
| rows in any nursing table, in either database | **0** |

The primary-key disagreement is uniform and systematic, not accumulated drift:
`NursingBaseEntity` declares `id = Column(String(26), default=_ulid)` for all
fifteen, and all fifteen physical tables are `integer` driven by a sequence.

A live write, against real PostgreSQL, with the NR-074 topology repaired:

```
session.add(NursingTask(...)); session.flush()
(psycopg2.errors.UndefinedColumn) column "encounter_id" of relation
"nursing_tasks" does not exist
```

## 2. Why this was invisible

NR-074's split foreign-key namespace made every nursing write raise
`NoReferencedTableError` while SQLAlchemy sorted the mapper's tables — before any
SQL was emitted. One defect completely masked the other. This is the second time
in this lane that has happened (NR-064 masked NR-065 identically), and the lesson
is recorded rather than relearned: **after repairing a layer, re-run the original
operation and read which error it now gives.** "The old error is gone" and "the
operation works" are different claims.

## 3. Classification

Not one defect. Five, of three different kinds:

| # | kind | extent | decidable? |
|---|---|---|---|
| 1 | **table-name mismatch** — ORM mapped two tables that exist nowhere | 2 tables | **YES — fixed, NR-077** |
| 2 | **identity mismatch** — ULID ORM vs integer+sequence tables | 15 of 15 PKs | NO — owner decision |
| 3 | **FK datatype contradiction** — 23 columns declare `String(26)` against `lab_users.id`, which is `integer` | 23 columns | direction decidable, see §6 |
| 4 | **column-set contradiction** — two different clinical field sets | 149 + 176 columns | **NO — clinical decision** |
| 5 | **FK target does not exist** — `encounter_id` references `national_encounters` | 12 columns | NO — see §5 |

Canonical owner: the Nursing Platform bounded context (`docs/nursing-platform/ADR.md`
ADR-001 establishes it as one), jointly with migration architecture. **No new owner
was created.**

## 4. What #4 actually is, and why I will not guess it

The two field sets are not the same model under different names. Some pairs look
like renames, and some are different clinical instruments.

Plausibly mechanical:

| ORM | table |
|---|---|
| `bp_systolic` / `bp_diastolic` | `systolic_bp` / `diastolic_bp` |
| `amount_ml` | `volume_ml` |
| `fluid_name` | `solution_name` |
| `start_time` / `end_time` | `started_at` / `ended_at` |
| `infusion_rate` | `rate_ml_per_hour` |
| `bag_number` | `batch_number` |

Not mechanical at all:

* **Fall risk.** The table holds the six Morse Fall Scale items
  (`history_of_falls`, `secondary_diagnosis`, `ambulatory_aid`, `iv_therapy`,
  `gait`, `medication_risk`) plus `assessment_tool`, `total_score`, `risk_level`.
  The ORM holds `fall_history_12mo`, `secondary_condition`, `assistive_device`,
  `iv_or_heparin_lock`, `gait_impaired`, `medications`, **`elimination`** and
  **`age_ge_65`** — the last two are not Morse items at all; they belong to a
  different instrument. And `total_score` is `INTEGER` in the ORM against
  `double precision` in the table, which changes what a score *is*.
* **Nursing notes.** The ORM models SOAP (`subjective`, `objective`,
  `assessment`, `plan`, `intervention`, `evaluation`, `response`,
  `patient_education`). The table has a single `content` column plus
  `is_signed`/`signed_by`/`signed_at`. ADR-004 decided *structured over free
  text*; the ORM is the structured one and the table is the free-text one, so
  here the ORM matches the recorded decision and the schema does not.
* **Nutrition.** The ORM has anthropometry and targets (`height_cm`,
  `weight_kg`, `calorie_target_kcal`, `protein_target_g`, `dysphagia_risk`,
  `feeding_method`). The table has a MUST-style scored screen
  (`total_score`, `risk_level`, `acute_disease_effect`, `food_intake`,
  `weight_change_percent`). Different clinical purposes: assessment versus
  screening.

Mapping one onto the other is inventing clinical semantics. That is prohibited
here, and it is prohibited for a good reason: a wrong mapping on a pressure-injury
stage or a fall-risk score is a patient-safety defect that no test would catch,
because both sides would be internally consistent.

## 5. The part that blocks the obvious answer

The obvious answer to "the ORM declares 149 columns the table lacks" is *add the
columns*. For `encounter_id` — 12 of those columns, across 12 tables — that is
not available:

* `national_encounters` exists in **neither** database.
* **No migration on this branch creates it.** It is not even mentioned in one.
* It *is* ORM-mapped (`app/national/domain/encounter.py`), which is why NR-074's
  topology guard passes: the foreign key resolves in the ORM namespace and fails
  only against a real database.

This is NR-073's class, and measuring it generally: **222 of 564 ORM-mapped
tables do not exist in the richest reachable database, and none of them is
created by any migration** — see NR-079. Four of those absent tables are the
targets of foreign keys on tables that *do* exist: `national_encounters` (13
columns), `national_patients` (4), `national_practitioners` (4),
`national_citizens` (1).

So `encounter_id` cannot be added until `national_encounters` can be created,
and that is a separate, larger decision.

## 6. The options, costed

### Option A — the ORM yields to the schema

Rewrite the 15 nursing models from the physical columns. This is the **exact
precedent** the platform already set: NR-072/PR #258 did it for all 27 pharmacy
tables and took drift from 243 to 0, and Mustafa's `0083480c` settled that where
a ULID table references an integer-keyed legacy table, **integer is canonical**.
Both point the same way, and §3 item 3 is decided by the same logic: `lab_users.id`
and `patients.id` are `integer`, and `app/nursing/models.py` *already* declares
`patient_id` as `Integer` against `patients.id` — so the file's own convention for
a legacy integer target is integer. The 23 `String(26)` declarations against
`lab_users.id` are simply wrong, whichever generation wins.

* **Cost, measured:** **174 of 179** ORM-only attributes are referenced by served
  code (`routes.py`, `services.py`, `medication.py`). So this rewrites the request
  and response schemas of 66 mounted routes.
* **Gate crossed:** CLAUDE.md — *"API response-shape changes (breaks mobile
  clients)"* → requires human approval.
* **Clinical cost:** deletes 149 declared clinical fields from the API, including
  the SOAP note structure that ADR-004 appears to mandate. Honest, but a product
  decision.
* **Data cost:** none. All fifteen tables are empty.

### Option B — the schema yields to the ORM

Add 149 columns, convert 15 primary keys from `integer`+sequence to
`String(26)`, convert ~23 FK columns, rename nothing.

* **Gate crossed:** CLAUDE.md — *"DB schema changes"* → requires human approval.
  A primary-key type conversion is not additive, so the migration policy's
  *"new columns must be nullable or have a server_default"* does not cover it.
* **Blocked sub-part:** `encounter_id` cannot be added at all (§5).
* **Knock-on:** converting FK columns to `String(26)` to match the ORM would
  require `lab_users.id` to become ULID — a platform-wide identity change
  reaching authentication. Out of all proportion to nursing.
* **Data cost:** none today — all fifteen tables are empty, which is the single
  thing that makes this option even arguable. `test_no_nursing_row_exists_anywhere_so_no_backfill_is_owed`
  fails the day that stops being true.

### Option C — map both

Rejected without needing a decision. It is `extend_existing` masking by another
name, and the platform has just paid for that once: NR-006's duplicate
`national_facilities` owner silently unioned two column sets into a 30-column
table with 24 phantom columns.

## 7. Recommendation, and what it is not

On evidence alone, **Option A is the cheaper and better-precedented direction**,
and §3 item 3 (the 23 FK datatype errors) is decidable within it today. But Option
A's cost is an API-shape change across 66 mounted clinical routes, which is
explicitly a human gate, and it would delete clinical fields that ADR-004 may
require. So the recommendation is a recommendation, not an action, and nothing in
§4 or §6 has been executed.

**What was executed:** only NR-077 — two `__tablename__` strings now name the
tables that actually exist. That is decided by three independent signals (the only
migration that creates them uses the long names; its docstring names them; the ORM
classes are named after them) against one (the strings themselves). It does **not**
make those two tables writable, and the pin says so.

## 8. The decision needed, in one question each

1. **Identity:** is the nursing primary key integer (matching the deployed tables
   and every other legacy table) or ULID (matching `NursingBaseEntity` and the
   other seven ULID domain bases)? *This is the root; everything else follows.*
2. **Field sets:** for each of the five assessment tables, which clinical
   instrument is canonical — the ORM's or the table's? ADR-004 mandates
   standardised tools but does not name which.
3. **Encounters:** should `national_encounters` exist? Until it does, twelve
   `encounter_id` columns cannot be added and the nursing→encounter link is
   unrepresentable.

## 9. Verification of everything above

`backend/tests/verification/test_nursing_schema_contradiction.py` — 5 tests
against real PostgreSQL:

* every nursing model maps a table that exists (NR-077; must stay fixed);
* a nursing write still fails, **and fails for the recorded reason** — asserting
  the error kind, so a regression of NR-074 is distinguishable from NR-076;
* all 15 primary keys disagree, and a *partial* conversion fails (a mixed state
  is worse than either generation);
* the contradiction does not grow — subset semantics, with a guard against the
  measurement silently reaching zero;
* no nursing row exists anywhere, so no backfill is owed.

Negative proof: reverting NR-077 fails 2 of the 5; a half-done ULID→integer
conversion fails the identity test; both files restored byte-identically
afterwards.

When the gate is resolved, the write-fails pin must be **deleted, not relaxed** —
an assertion that a write fails has no honest weakened form.
