# DATABASE OWNERSHIP & MIGRATION READINESS MATRIX

**Repository:** `gula-integration` · **Branch / HEAD:** `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (unchanged) · **Date:** 2026-11-17
**Work item:** W-074 (NAT-K) · **Change control:** CC-010 · **Evidence:** E-063 (new read-only scan) · **New finding:** F-085.
**Status:** **BLOCKED / NOT VERIFIED for migration readiness.** This is an ownership/readiness record, **not** authorization to run DDL.

---

## 0. Scope, hard constraints and non-claims

- **NO operational DDL, NO migration applied, NO `alembic stamp`, NO connection to the operational `gula` database.** No table, column or data was created, altered or dropped; the NR-011 `env.py` delta remains **`+49 / -0`** (re-verified in E-063).
- No real patient data. No production-like snapshot exists (51 rows only) — B-017.
- Authoritative drift/migration figures are **carried from existing evidence** (E-008…E-015, E-024, E-042…E-045, `W1_CHECKPOINT.md`, `MIGRATION_RECONCILIATION_MATRIX.md`) and **re-stated, not recomputed or repaired**. E-063 adds one **new, independently verified** source observation (unregistered bases).
- **RPO/RTO remain UNMEASURED / NOT VERIFIED.** No recovery or production-readiness claim. `FINAL_DECISION.md` stays **HOLD**; D-020/D-021 stay **PENDING**.

---

## 1. Table ownership (canonical: `NATIONAL_SERVICE_CONTRACTS.md` §4, rule R-DB-1 single-writer)

| Service / owner | Table prefix | Tables | Migrated | Owner status |
|---|---|---:|---:|---|
| Laboratory (LIMS) | `lims_*` | 35 | 35 | clear |
| Pharmacy | `pharmacy_*` | 27 | 27 | clear |
| Radiology | `radiology_*` | 18 | 17 | clear — 1 unmigrated |
| Emergency | `ems_*` | 12 | 12 | clear |
| Blood bank | `blood_bank_*` | 17 | 17 | clear |
| Public health | `ph_*` | 6 | 6 | clear |
| Hospital | `hospital_*`, `hospitals`, `bed_assignments` | 14 | 1 | 12 uncovered |
| Nursing | `nursing_*` | 15 | 13 | 2 uncovered |
| Critical care | `critical_care_*` | 13 | 13 | clear |
| Care continuum | `cc_*` | 45 | **0** | **BLOCKED** |
| EHR | `ehr_*` | 18 | **0** | **BLOCKED** |
| Insurance | `ins_*` | 30 | **0** | **BLOCKED + UNSERVED** |
| Billing | `billing_*` | 5 | 5 | clear |
| Payments | `payments_*` | 28 | 28 | clear |
| Biomedical | `biomed_*` | 12 | 12 | clear |
| Devices | `device_*` | 10 | 10 | clear |
| National data | `dp_*` | 36 | **0** | **BLOCKED** |
| Health data | `hd_*` | 17 | **0** | **BLOCKED** |
| Document intelligence | (its own models) | 21 | **0** | **BLOCKED — see F-085** |
| National | mixed | 106 | 8 | **BLOCKED** |

**Ambiguous ownership (no rule applied until decided — ADR-B/W-038):** `national_facilities` (two ORM declarations: `app/models/clinical_scope.py:136` and `app/national/domain/facility.py:9`); `insurance_coverages` (billing vs `ins_*`); `facilities` / `organizations` (national + identity + hospital); `patients` (LIMS/MPI/EHR/national — canonical patient identity not enforced).

**Rule R-DB-2 (no shared DB ownership):** current violations to audit before any wave — hospital-family, `insurance_coverages`, `facilities`. No ownership was changed here.

---

## 2. SQLAlchemy Base / MetaData ownership matrix (E-063, read-only source scan)

A read-only scan of `backend/app/**/*.py` found **19 runtime `declarative_base()` declarations** (plus 2 generator templates: `engineering/crud/generator.py` string template and `engineering/generators/microservice.py`). `migrations/env.py:134-151` registers **17** bases in `target_metadata`, then merges them into one `MetaData` (NR-011 part 2, zero DDL).

| # | Base | Declared at | In `env.py` target_metadata? | Notes |
|---:|---|---|---|---|
| 1 | `Base` (canonical) | `app/database.py:273` | ✅ | core tables |
| 2 | `NationalBase` | `app/national/base.py:19` | ✅ | national domain |
| 3 | `EHRBase` | `app/ehr/base.py:10` | ✅ | `ehr_*` 0 % migrated |
| 4 | `CitizenPlatformBase` | `app/citizen_platform/base.py:10` | ✅ | 0-table base (F-065) |
| 5 | `ClinicalBase` | `app/clinical/base.py:13` | ✅ | clinical terminology/CDS/knowledge/quality/research |
| 6 | `HealthDataBase` | `app/health_data/base.py:19` | ✅ | `hd_*` 0 % migrated |
| 7 | `TrustBase` | `app/trust/base.py:16` | ✅ | trust models |
| 8 | `GovernanceBase` | `app/governance/base.py:15` | ✅ | governance models |
| 9 | `CareContinuumBase` | `app/care_continuum/base.py:19` | ✅ | `cc_*` 0 % migrated |
| 10 | `IdentityBase` | `app/identity/base.py:12` | ✅ | NIAM (NR-011 addition) |
| 11 | `HospitalBase` | `app/hospital/base.py:6` | ✅ | NR-011 addition |
| 12 | `DataPlatformBase` | `app/national_data/base.py:13` | ✅ | `dp_*` 0 % migrated; NR-011 addition |
| 13 | `NHDWBase` | `app/nhdw/base.py:8` | ✅ | 0-table base (F-065); NR-011 addition |
| 14 | `NursingBase` | `app/nursing/base.py:13` | ✅ | 0-table base (F-065); NR-011 addition |
| 15 | `PharmacyBase` | `app/pharmacy/base.py:19` | ✅ | 0-table base (F-065); NR-011 addition |
| 16 | `RadiologyBase` | `app/radiology/base.py:13` | ✅ | 0-table base (F-065); NR-011 addition |
| 17 | `FinBase` | `app/financial/models.py:21` | ✅ | financial models; NR-011 addition |
| 18 | **`DocIntelBase`** | `app/document_intelligence/infrastructure/models.py:64` | **❌ NOT REGISTERED** | **21 mapped classes**; imported by `app/factory.py:157` at boot but its metadata is invisible to Alembic → **F-085** |
| 19 | **`InsBase`** | `app/insurance/domain/models.py:49` | **❌ NOT REGISTERED** | **30 mapped classes** across `models/members/referral/services/network.py` → **F-085** |

**Root cause of F-085:** NR-011 (D-003, CC-004) registered 7 previously omitted bases but did not include these two. Unregistered metadata is silently skipped by autogenerate. This is a concrete, source-verified contributor to the pre-existing "0 % migrated" gaps for document intelligence (21 tables) and insurance `ins_*` (30 tables). **No env.py edit was made** — registering them is a category-D change (D-001 wave work) requiring a fresh-clone autogenerate + strict-subset verification, and would widen autogenerate scope (70 removal findings need triage, never auto-applied). Status: **OPEN — classification + approval required.**

---

## 3. Integrity checks (carried from canonical evidence — none re-run here)

| Check | Finding | Authoritative value | Source / status |
|---|---|---|---|
| Missing ORM tables (per-base sum) | F-002 | **340** (756 ORM / 416 present) | E-008/E-013/W1 §5 — OPEN |
| Column drift | F-001 | **82 tables / 664 columns** | E-009/W1 §5 — OPEN |
| Insert-breaking drift columns | F-001 | **70** of 664 (NOT NULL, no default) | E-011 — OPEN |
| NOT NULL without default | F-001 | 1,114 columns across 339 of 340 missing tables | E-011 — OPEN |
| Migrated public tables | — | **433** at head `20261114_0006` | E-024/E-043 — current |
| Migration graph | — | single head `20261114_0006`, 107 revisions, 0 missing parents, 0 cycles | `MIGRATION_RECONCILIATION_MATRIX.md` §5.2 — current; 107 files confirmed in E-063 |
| Schema fingerprint | — | `3b2d9499d019503bf1ff5644f713cd5f272705f544862d8022887a516f973568` identical ×3 ⇒ zero DDL | E-015/E-043 — unchanged |
| FK topology | F-010 | 573 declared edges = 485 → missing tables + 88 → present | E-010 — OPEN |
| Strict functional result | F-003 | **753 / 119** on migrated schema (4 P0 workflow modules fail; all green under control) | E-001 — FAILED, no rerun trigger |
| Discovery debt | F-065 | 5 of 17 registered bases contribute 0 tables | E-045 — OPEN |
| Duplicate `national_facilities` | F-014 | 6-col `clinical_scope` (DB-matching) vs 28-col dormant | ADR-B/W-038 — OPEN |
| Unsafe rollback path | F-012/B-010 | partial rewind to `20260815_0022`: exit 0 but 7 residual tables — must never be a rollback runbook | E-024 T3 — OPEN |
| Successful rehearsals (disposable clones only) | — | forward 405→433 tables; teardown→upgrade identical fingerprint; determinism PASS | E-024 T1/T2/T4 — current |
| **Unregistered bases** | **F-085 (new)** | **2 bases / 51 mapped classes invisible to Alembic** | **E-063 — OPEN** |

**Denominator discipline (F-024):** **426** (per-context union), **340** (per-base), **284** (probe-C add_table) are different measurements — never summed or substituted. Historical corrections retained: hospital "13" (F-015/E-034; §15.3 of inventory), auth walk 2,064/69 (F-062).

**Backward compatibility:** no destructive change authored; no table/column/data dropped; partial downgrade prohibited (D-004). No migration revision was authored in this program.

---

## 4. Migration Readiness Report (verdict)

**Verdict: NOT READY — BLOCKED / NOT VERIFIED.** Readiness requires: (a) ADR-A waves W-026…W-030 adding/verifying tables+columns with per-wave strict subsets; (b) ADR-B ownership record W-038; (c) W-036 type reconciliation; (d) **F-085** registration decision + fresh-clone verification; (e) a production-like snapshot (B-017/W-039 — only 51 rows exist); (f) a repeatable strict suite at 872/872. None was performed here. Release criterion 5 (`MIG-EXISTING`) stays **NOT MET**; G-02/G-06/G-09/G-12 stay NOT MET.

**Rollback (CC-010):** this document only records facts; deleting it and the E-063 log restores the prior state. No DB object, migration file, or `env.py` line was created or changed by this work item.
