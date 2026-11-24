# W1 Checkpoint — Strict-Schema Functional Validation

**Program:** GULA Stable v1.0.0 — Unification (W1 database gate)
**Branch:** `integration/gula-unification-v1` @ `2827c1ff` (unchanged)
**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Date:** 2026-11-17
**Verdict of `FINAL_DECISION.md`:** unchanged — **HOLD**
**Commits:** none. **Pushes/merges/PRs/deploys:** none. **`alembic stamp`:** never used.

> Purpose: make the current state sufficient to resume without repeating the W1 runs, and to stop
> exactly at the ADR-A / ADR-B approval boundary.

---

## 1. The question W1 answers

Does the existing backend suite pass against a PostgreSQL database whose schema was created
**exclusively by Alembic migrations** — no `create_all()`, no test-side DDL, no stamp?

**Answer: no.** 753 / 872 tests pass. Against the identical modules and fixtures on the repository's
SQLite `create_all()` schema, 872 / 872 pass. The difference is the migrated schema.

---

## 2. Method (what was and was not touched)

| Element | Value |
|---|---|
| Target DB | disposable clone `gula_w1_strict_20261117` of `gula_unify_full`; PG 16.14; rev `20261114_0006`; **433** public tables |
| Harness | `/tmp/opencode/strict-w1/` — **outside the repository** |
| Strict conftest | PostgreSQL only, asserts revision + table count, savepoint-only isolation, **no DDL** |
| Test corpus | **53** modules / **872** tests, byte-identical copies (sha256 manifest `sha256_manifest_full.txt`, source hash re-verified) |
| Selection rule | modules using the shared `db`/`client` fixtures and containing no own `create_engine`/`create_all()` |
| Control | the same 53 modules under the unmodified repository `tests/conftest.py` (SQLite + merged-metadata `create_all()`) |
| Schema fingerprint | `3b2d9499…6f973568` before **and** after all runs → zero DDL executed |
| Repository changes for this gate | **none** — no test, fixture, conftest, migration or production module modified, deleted, skipped or weakened |

---

## 3. Results

| Run | Outcome | Time | Exit |
|---|---|---|---|
| Strict #1 (authoritative, clean clone) | **753 passed / 119 failed / 0 skipped** | 273.09 s | 1 |
| Strict #2 (repeatability, same clone) | **750 / 122** — all 119 reproduced, +3 self-poisoned audit assertions | 281.35 s | 1 |
| SQLite control | **872 passed / 0 failed** | 297.98 s | **0** |

**19 of 53 modules** carry at least one failure; **34 of 53** are fully green.

Critical workflow verdicts: `test_clinical_safety` 33/33 PASS, `test_patient_card` 15/15 PASS,
`test_clinical_command_guard_p0` 5/5 PASS; `test_icu_lab_workflow_p0` 6/7, `test_emergency_surgery_workflow_p0`
2/4, `test_pharmacy_radiology_workflow_p0` 1/3, `test_pharmacy_pos` 0/3, `test_national_bootstrap`
33/41 — all of these are green under the control.

---

## 4. Remaining failures by class (run #1 = 119)

| Class | Count | Representative cause |
|---|---:|---|
| `MIGRATION_COLUMN_DRIFT` | 43 | `fin_providers.provider_type` ×29, `radiology_exams.exam_code` ×4, `pharmacy_drug_catalog.code` ×3 |
| `MIGRATION_MISSING_TABLE` | 33 | `gov_national_audit_events` ×10, `fin_pricing_rules` ×7, `fin_invoices` ×5, `national_patients` ×3, `ehr_conditions` ×3 |
| `RUNTIME_GUARD` | 20 | all 20 `test_edge_platform` cases raise `RuntimeIsolationError` |
| `AUDIT_APPEND_ONLY_TRIGGER` | 4 | tamper tests hit the migrated append-only trigger |
| `CASCADE_FAILURE` | 4 | national bootstrap, downstream of missing/drifted tables |
| `ID_SEQUENCE_ASSUMPTION` | 4 | `test_communication_experience` assumes sequential ids |
| `HARNESS_PATH_ARTEFACT` | 4 | external-harness-relative source reads (classified, not hidden) |
| `OTHER` | 4 | 2 × `assert 404 == 200`, `assert False is True`, `assert 0 > 0` — downstream of gaps |
| `PG_TYPE_OVERFLOW` | 2 | `disk_free_bytes` migrated as `integer` |
| `FK_ENFORCEMENT` | 1 | ICU/LIMS correction transition |

**Schema-dependent: 107 / 119 (90 %)** — 76 direct table/column + 4 cascade + 2 type + 1 FK + 20
runtime-guard + 4 trigger. The other 12 are 4 harness artefacts, 4 id assumptions, 4 downstream
assertions. Every one of the 119 passes under the control.

---

## 5. Schema gap (measured on the same clone)

| Measure | Value |
|---|---:|
| Migrated public tables | **433** |
| ORM tables per declarative base | **756** (one duplicate name: `national_facilities`) |
| Present in migrated DB | **416** |
| Missing (per-base sum) | **340** |
| Migrated tables missing ORM columns | **82 tables / 664 columns** |
| Migrated tables with extra DB-only columns | 85 |
| Type-risk tables | 4 |

Worst bases: `EHRBase` 0/18, `CareContinuumBase` 0/45, `GovernanceBase` 3/61, `DataPlatformBase`
0/36, `HealthDataBase` 0/24, `ClinicalBase` 2/41, `HospitalBase` 1/14.

The earlier per-context coverage figure (407 / 833, 426 missing) uses a **different denominator**
(union of tables per context) and is **not** superseded or contradicted — both measurements show the
majority of ORM tables are absent; the per-base figure (§5) is the one the strict suite exercised.

`national_encounters`, `ehr_conditions` and `exam_code` appear in **no migration file**;
`national_patients` and `fin_providers` are referenced once each but not on the head path.

---

## 6. NR-011 — status and corrected minimal fix

**Status: OPEN.** `alembic check` still exits 1. Root cause is **corrected** from the earlier
"one-line import" description.

Probes (isolated copies of `backend/migrations` + `alembic.ini`; repository untouched; no DDL,
no upgrade, no stamp):

| Probe | Change | Result |
|---|---|---|
| A | pristine `env.py` | exit 1 — `NoReferencedTableError` (unresolved FK varies: encounter / patient / practitioner) |
| B | `import app.national.domain` only | exit 1 — **error moves** to `national_patients` |
| C | 7 omitted bases + one merged `MetaData` | **no FK error**; `FAILED: New upgrade operations detected` — 284 distinct missing tables, 68 add / 70 remove columns |

Why B cannot work: all four `ehr_allergies` FKs are **cross-metadata**
(`EHRBase.metadata → NationalBase.metadata`); SQLAlchemy resolves FK strings only inside the owning
`MetaData`. `tests/conftest.py` hides this by merging metadata before `create_all()`.

**Corrected minimal fix (ADR-A scope, not implemented):**

1. Register the missing metadata in `migrations/env.py` — at minimum `import app.national.domain`,
   plus the 7 bases currently omitted (`HospitalBase`, `DataPlatformBase`, `NHDWBase`, `NursingBase`,
   `PharmacyBase`, `RadiologyBase`, `FinBase`).
2. Hand Alembic a **single merged `MetaData`** (or an equivalent `include_object` strategy) so
   cross-metadata FKs resolve.
3. Only then can autogenerate be used to author ADR-A revisions for `national_encounters` and the
   agreed national subset.

**Validation plan after approval (no code written yet):** apply the two-part `env.py` change in a
branch → `alembic check` must stop raising `NoReferencedTableError` (it will still report the real
drift) → author context-by-context migrations → recreate a fresh clone from `gula_unify_full` →
`upgrade head` → strict suite must reach **872/872** → fingerprint before/after unchanged except the
approved migration delta → re-run twice to prove repeatability (the fixture leak, §7, must be fixed
first or the audit-chain tests will self-poison run #2).

---

## 7. Secondary defects proven, not fixed

1. **Fixture write leak (P1):** repository `client` fixture binds `SessionLocal` to the engine, not
   the savepoint connection; 12 `audit_logs` rows (ids 65–191) committed across the runs; strict #2
   reported 3 extra failures as a result. Fix belongs in the integration repo's fixtures. Production
   code untouched.
2. **Coverage hole (P1):** referrals have no functional test (one static route-guard string),
   `care_continuum` appears only in `tests/conftest.py`, hospital coverage is one module. Those
   workflows are **NOT VERIFIED** — they must not be described as passing.
3. **`disk_free_bytes` integer overflow (P1):** 2 `NumericValueOutOfRange` failures.
4. **Edge-device guard:** 20/20 `test_edge_platform` cases blocked by `RuntimeIsolationError` on the
   migrated schema — decide whether guard or schema is wrong; do not weaken the guard.
5. **Pre-existing `app.main` import-time defect:** AI registry sync fails with `syntax error at or
   near ":"`; unrelated to W1, unchanged.

---

## 8. Approval boundary — decisions that cannot be taken autonomously

| Decision | Status | Why it blocks |
|---|---|---|
| **ADR-A** — migration strategy for the unmigrated ORM tables (A1 + A3 recommended) | **PENDING** | Requires schema change; W1 proves the gap is functional, not cosmetic |
| **ADR-B** — ownership of `facilities` / `organizations` / `national_facilities` (B1 recommended) | **PENDING** | Criterion 5; `NR-006`; dropping a possibly pre-existing table is destructive |
| **Rollback procedure** — record snapshot restore or `downgrade base` + `upgrade head` | **PENDING** | Partial rewind is proven unsafe; a runbook choice, not a code change |
| **NR-011 two-part fix approval** | **PENDING** | Prerequisite for ADR-A authoring |

No schema change, ownership change, module activation or test edit will be made before these are
approved. `MIG-EXISTING` / release criterion 5 stays **NOT MET** — it is not downgraded by the
forward-upgrade PASS, and W1 adds a fifth outstanding condition.

---

## 9. Exact next action after approval

1. Get explicit approval for **NR-011 two-part fix** + **ADR-A** (and **ADR-B** for criterion 5).
2. Implement NR-011 part 1+2 in `migrations/env.py` only (no schema migration yet); re-run probes
   A/B/C to show the FK error is gone and the real diff is visible.
3. Author ADR-A migrations context-by-context (start with the 10 missing tables named by the failing
   tests), each with a fresh-clone `upgrade head` + strict-suite delta.
4. Fix the fixture write leak (§7.1) so strict runs are repeatable.
5. Re-run the strict gate twice; require **872/872** with an unchanged fingerprint except the
   approved delta.
6. Only then revisit criterion 5 with ADR-B, the recorded rollback decision and a production-like
   snapshot.

---

## 10. Evidence index (append-only; nothing overwritten)

| Artifact | Path | Integrity |
|---|---|---|
| Strict run #1 log | `/tmp/opencode/strict-w1/logs/strict_suite_20261117_063054.log` | exit 1; 753/119; 273.09 s |
| Strict run #1 exit file | `/tmp/opencode/strict-w1/logs/strict_suite_20261117_063054.exit` | `1` |
| Strict run #2 JUnit | `/tmp/opencode/strict-w1/logs/strict_run2.xml` | 872 / 122 failures / 0 errors |
| SQLite control JUnit | `/tmp/opencode/strict-w1/logs/baseline_sqlite.xml` | 872 / 0 failures |
| Classification (run #1/#2) | `/tmp/opencode/remediation/w1/strict_classification.json` | 119 run-1 nodes |
| Run1↔Run2 node diff | `/tmp/opencode/remediation/w1/run1_vs_run2_nodes.json` | 119 common, 3 only-run2, 0 lost |
| Table gap | `/tmp/opencode/remediation/w1/schema_gap_strict.json` | 756 / 416 / 340 |
| Column drift | `/tmp/opencode/remediation/w1/schema_drift_strict.json` | 82 tables / 664 columns |
| Fingerprint before / after | `/tmp/opencode/remediation/w1/fp_strict_before.txt`, `fp_strict_after_drift.txt` | both `3b2d9499…6f973568` |
| Byte-identity manifest | `/tmp/opencode/strict-w1/sha256_manifest_full.txt` | 53 modules |
| NR-011 probes | `/tmp/opencode/remediation/w1/ALEMBIC_PROBE_EVIDENCE.md` + `alembic_check_probe_{a,b,c}.log`, `alembic_probe_{b,c}_env.diff`, `alembic_check_probe_c_summary.json` | exit 1 / 1 / 1 |
| Strict harness | `/tmp/opencode/strict-w1/conftest.py`, `pytest.ini`, `tests/` | no DDL, no `create_all` |

Governance destinations (appended, not rewritten):
`DATABASE_COMPATIBILITY_REPORT.md` §11 · `PHASE_C_DATABASE_REHEARSAL_REPORT.md` §13 ·
`UNIFICATION_BLOCKERS.md` §3A · `EXECUTION_LEDGER.md` §3.3 and open blockers 18–23.

---

## 11. Explicit non-claims

* No workflow is certified by W1; four P0 patient-flow modules failed on the migrated schema.
* Passing under `create_all()` is not migration compatibility — it is the control that isolates the
  gap.
* The strict clone is a disposable rehearsal database; no operational database was touched.
* No test was deleted, skipped, weakened or rewritten; 4 harness-path failures are classified
  honestly rather than hidden.
* No commit, push, merge, PR or deploy was performed; `FINAL_DECISION.md` remains **HOLD**.
