# NATIONAL SERVICE INVENTORY — GULA as a patient-centred national health platform

**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1`
**Date:** 2026-11-17
**Status of `GOVERNANCE/FINAL_DECISION.md`:** **HOLD** (unchanged)
**Scope of this document:** *inventory and assessment only.* No service was implemented,
unified, migrated, committed, pushed, merged or deployed to produce it.

> **Method note — directories are not evidence.** A service is only recorded as
> present when code, a live API operation, a data model, and a migration/test
> trail can be shown. A directory or a keyword hit alone is explicitly *not*
> accepted (⟨zero⟩ rows below prove the rule was applied).

---

## 1. Evidence sources (all read-only)

| Source | Artifact | What it proves |
|---|---|---|
| Static model/route/migration scan (833 `__tablename__` vs 421 `create_table`) | `/tmp/opencode/remediation/inventory_scan.json` | models, endpoints, migration coverage, auth/audit/test signals |
| Per-context migration coverage | `/tmp/opencode/remediation/coverage_by_context.json` | which contexts are actually covered by Alembic |
| **Live OpenAPI** (`create_app()` → `app.openapi()`, exit 0) | `/tmp/opencode/remediation/openapi_20261117_084342.json` | **authoritative** API surface: **2116 operations / 1804 paths**, **2060 secured / 56 without declared security** |
| OpenAPI analysis (prefix + public list) | `/tmp/opencode/remediation/openapi_analysis.txt` | per-prefix operation counts, public operation list |
| Hospital family reconciliation | `/tmp/opencode/remediation/hospital_prefix_tables.txt` | 12 `hospital_*` tables, migration status |
| Migration topology | `backend/migrations/versions/` (107 files), `backend/migrations/env.py` | 12 metadata namespaces registered; head chain |

Commands used (examples):

```bash
# authoritative API surface
cd backend && PYTHONPATH=.. <py312>/bin/python -c "from app.factory import create_app; ... app.openapi()"
# ORM vs migration coverage
python /tmp/opencode/remediation/coverage_by_context.py
```

---

## 2. Status taxonomy used in this document

| Code | Meaning |
|---|---|
| **IMPLEMENTED** | Live API + models + **migrations** + authentication + audit-log writes + dedicated tests |
| **PARTIAL** | Real API/model code exists, but at least one of {migrations, audit-log, tests} is missing |
| **CROSS_CUTTING** | Genuinely implemented, but hosted **inside another bounded context** rather than as its own service |
| **DATA/ANALYTICS ONLY** | Only columns, enums, or reporting queries — no service, no API |
| **NOT_IMPLEMENTED** | Nothing beyond incidental enum/string references |

---

## 3. Executive summary — the 18 target services

| # | Service | Verdict | Live ops | Models (tables) | Migration coverage | Audit-log | Dedicated tests |
|---|---|---|---:|---:|---|:--:|---:|
| 01 | Laboratory | **IMPLEMENTED** | 103 | 35 (`lims/`) | **100 %** | ✅ | 6 files |
| 02 | Hospital | **PARTIAL** | 127 | 14 + nursing 15 + critical 13 | 1/14 · 13/15 · 13/13 | ⚠️ mixed | 4 files |
| 03 | Primary healthcare | **CROSS_CUTTING / PARTIAL** | 13 | 5 (`cc_*`) | **0 %** | ❌ | **0** |
| 04 | Pharmacy & medication | **IMPLEMENTED** | 63 | 27 | **100 %** | ✅ | 3 files |
| 05 | Radiology & imaging | **IMPLEMENTED** | 58 | 18 | 94.4 % | ✅ | 5 files |
| 06 | Emergency & ambulance | **IMPLEMENTED** | 26 | 12 | **100 %** | ✅ | 2 files |
| 07 | Blood bank | **PARTIAL** | 30 | 17 | **100 %** | ❌ (columns only) | 8 files |
| 08 | Immunization | **CROSS_CUTTING / PARTIAL** | 13 | 6 (`cc_*`) + 1 (`ehr_*`) | **0 %** | ❌ | **0** |
| 09 | Public health & surveillance | **PARTIAL** | 110 | 6 + `nhdw` 15 | 100 % · 93.3 % | ❌ | 2 files |
| 10 | Dental | **NOT_IMPLEMENTED** | **0** | **0** | — | — | 0 |
| 11 | Maternal & child health | **CROSS_CUTTING / PARTIAL** | 9 | 7 (`cc_*`) | **0 %** | ❌ | **0** |
| 12 | Chronic disease mgmt | **PARTIAL** | 15 | 5 (`cc_*`) | **0 %** | ❌ | 1 file |
| 13 | Rehabilitation / physio | **NOT_IMPLEMENTED** | **0** | **0** | — | — | 0 |
| 14 | Mental health | **DATA/ANALYTICS ONLY** | **0** | 0 dedicated | — | — | 0 |
| 15 | Referral & continuity | **CROSS_CUTTING / PARTIAL** | 18 | 12 (`cc_*`) | **0 %** | ❌ | **0** |
| 16 | Insurance & claims | **PARTIAL** | 62 | 30 (`ins_*`) | **0 %** (ins) / 100 % (billing, payments) | ✅ | 3 files |
| 17 | Home healthcare | **CROSS_CUTTING / PARTIAL** | 4 | 2 (`cc_*`) | **0 %** | ❌ | **0** |
| 18 | Medical equipment | **PARTIAL** | 52 | 12 + devices 10 | **100 %** | ❌ | 1 file |

**Headline:** of 18 target services, **4 are effectively complete** (laboratory,
pharmacy, radiology, emergency), **9 are real but partial**, **3 exist only as
signals** (dental, rehabilitation, mental-health analytics), and **the dominant
cross-service defect is missing migrations**, not missing code.

---

## 4. Cross-cutting backbone — `care_continuum` (read this before §5)

`backend/app/care_continuum/` is the single most important discovery of this
inventory. It is **not** a placeholder: it hosts **45 models** across 8 files and
backs **74 live operations** under `/care-continuum` (`backend/app/routes/care_continuum.py`,
`backend/app/services/care_continuum_service.py`, 33 986 B each, registered at
`backend/app/factory.py:666-667`).

| Sub-domain | Model file | Tables | Live routes (sample) |
|---|---|---:|---|
| Primary care | `models/primary_care.py` | 5 | `/primary-care-encounters`, `/family-medicine-records`, `/community-clinic-records`, `/health-assessments`, `/preventive-care-records` |
| Referral / continuity | `models/referral.py`, `models/care_journey.py` | 5 + 7 | `/referrals` (+accept/reject/complete/cross-org/timeline/analytics), `/care-journeys`, `/follow-up-plans`, `/care-coordination`, `/transitions-of-care`, `/clinical-handovers` |
| Home care | `models/care_journey.py` | 2 | `/home-care-plans`, `/community-care-records` |
| Maternal & child | `models/maternal.py` | 7 | `/pregnancy-records`, `/antenatal-care-visits`, `/delivery-records`, `/postnatal-care-visits`, `/growth-monitoring`, `/breastfeeding-records`, `/child-development-records` |
| Immunization | `models/immunization.py` | 6 | `/vaccination-records`, `/immunization-schedules`, `/reminder-schedules`, `/cold-chain-monitors`, `/immunization-coverage`, `/vaccinations/missed`, `/coordinate/ehr-immunization` |
| Chronic disease | `models/chronic_disease.py` | 5 | `/chronic-disease-registry`, `/disease-management-plans`, `/risk-stratifications`, `/self-monitoring-records` |
| Public health | `models/public_health.py` | 7 | `/health-programs`, `/screening-campaigns`, `/school-health-visits`, `/occupational-health-records`, `/community-visits`, `/health-promotion-activities`, `/program-enrollments` |
| Patient tasks | `models/patient_tasks.py` | 3 | `/patient-tasks`, `/educational-material-assignments`, `/self-follow-up-tasks` |

**Authentication:** present — every handler takes `current_user: LabUser = Depends(get_current_user)`
and scopes by `user.lab_id` (`_lab_id()` at `routes/care_continuum.py:99-100`).

**Three defects, all evidenced:**

1. **Zero migration coverage.** `CareContinuumBase` is imported by
   `backend/migrations/env.py:45,83-84,125`, but **no migration creates any `cc_*`
   table** (verified against all 107 migration files; only command-centre
   `cc_emergency_declarations` / `cc_resource_requests` exist, which are a
   different namespace). A fresh `alembic upgrade head` therefore does **not**
   create the schema these 74 endpoints require.
2. **Why CI is green anyway.** `backend/tests/conftest.py:104-148` builds the
   schema with `_ddl_meta.create_all(engine)` from combined metadata — this
   *synthesises* the missing tables in tests, masking the gap. (This is the same
   root cause pattern behind the hospital-family finding.)
3. **No audit-log writes and no dedicated tests.** `grep -c audit` in both the
   route and service modules = **0**; `grep -rl care_continuum backend/tests/test_*.py` = **0**.

---

## 5. Per-service detail

### 01 · Laboratory — **IMPLEMENTED**
* **Code:** `backend/app/lims/` (35 tables), `backend/app/routes/` lab/result routes, `services/lab`.
* **API:** `/lims` (57 ops) plus `/samples`, `/orders`, `/test-results`, `/qc`, `/labs`, `/test-profiles`, `/history`, `/patient-history`, `/batch` — 103 ops total.
* **Migrations:** **35/35 (100 %)** — the best-covered clinical context.
* **Auth:** yes. **Audit-log:** yes (`log_action` ×9).
* **Tests:** 6 files (`test_lab_service`, `test_lims_*`, quality-control suites).
* **Gaps:** 6 public operations use token/phone access (`/qr/{token}`, `/qr-medical/{token}`, `/r/{token}`, `/r/{token}/pdf`, `/history/{phone}`, `/test-profiles`) — **must be re-verified in Phase 7 (R-series)**, not assumed safe.

### 02 · Hospital — **PARTIAL**
* **Code:** `backend/app/hospital/` (models **only**, 14 tables), `nursing/` (15), `critical_care/` (13); API in `backend/app/routes/hospital.py`, `/nursing`, `/critical-care`.
* **API:** 127 ops (`/hospital` 25, `/nursing` 62, `/critical-care` 20 levels).
* **Migrations:** `hospital/` **1/14 (7.1 %)** — **12 uncovered hospital-related tables = 11 `hospital_*` + `hospitals`** (exactly reproducible; `hospital_operation_theaters` is only FK-referenced by `20260820_0004`, never created). Additionally `bed_assignments` is unmigrated. `nursing/` 13/15 (86.7 %), `critical_care/` 13/13 (100 %).
* **Audit-log:** `hospital` **0**, `critical_care` **0**, `nursing` 16 → inconsistent.
* **Tests:** 1 + 1 + 2 files — thin for 127 operations.
* **Gaps:** unmigrated hospital hierarchy (buildings/campuses/floors/rooms/beds/units/departments/clinics/cost-centres/equipment), no immutable audit for hospital & critical-care writes.

### 03 · Primary healthcare — **CROSS_CUTTING / PARTIAL**
* **Code:** `care_continuum/models/primary_care.py` (5 tables) + routes (13 ops).
* **Migrations:** **0 %**. **Audit-log:** none. **Tests:** none.
* **Gaps:** cannot be deployed on a freshly migrated database; no audit trail for clinical encounters.

### 04 · Pharmacy & medication — **IMPLEMENTED**
* `backend/app/pharmacy/` (27 tables, **100 % migrated**), 63 ops, audit via `log_action` (inventory/dispensing), 3 test files. *Strongest sub-service after laboratory.*

### 05 · Radiology & imaging — **IMPLEMENTED**
* `backend/app/radiology/` (18 tables, 17 migrated = 94.4 %), 58 ops, audit ×4, 5 test files. One table unmigrated (identify in Phase C).

### 06 · Emergency & ambulance — **IMPLEMENTED**
* `backend/app/ems/` full DDD layout (12 tables, **100 % migrated**), 26 ops, audit ×2, 2 test files. Tests thin relative to surface.

### 07 · Blood bank — **PARTIAL**
* `backend/app/blood_bank/` (17 tables, **100 % migrated**), 30 ops, **8 test files**.
* **Gap:** **no immutable audit-log writes** — migration `20260901_0003` only adds `updated_by` columns (AuditMixin alignment). Transfusion traceability without audit-log events is a clinical-safety gap.

### 08 · Immunization — **CROSS_CUTTING / PARTIAL**
* **Code:** `care_continuum/models/immunization.py` (6 tables) + 13 live ops; `ehr` immunization model; FHIR mapper `national/fhir/immunization.py` (`FHIRImmunizationMapper`).
* **Migrations:** **0 %** (both `cc_*` and `ehr_*`). **Audit-log:** none. **Tests:** none dedicated.
* **Gaps:** no migration, no audit, no tests; FHIR mapping exists but is not exercised by an integration test here.

### 09 · Public health & surveillance — **PARTIAL**
* **Code:** `public_health/` (6 tables, 100 % migrated), `nhdw/` (15 tables, 93.3 %), `national/intelligence/public_health/surveillance.py`, FHIR/`research` analytics.
* **API:** 110 ops (`/public-health` 14, `/nhdw` 51, `/intelligence` 28).
* **Gap:** **no audit-log writes**; only 2 test files for the surveillance surface.

### 10 · Dental — **NOT_IMPLEMENTED**
* `dental` appears **only** as an enum value: `biomedical/domain/enums.py:17`, `insurance/domain/enums.py:64,149`. Other hits are the word "accidentally" in comments. **0 ops, 0 tables.**

### 11 · Maternal & child health — **CROSS_CUTTING / PARTIAL**
* `care_continuum/models/maternal.py` (7 tables), 9 live ops (pregnancy → child development), **0 % migrated, no audit, no tests**.

### 12 · Chronic disease management — **PARTIAL**
* Dedicated `backend/app/chronic_care/` package (`alerts.py`, `baselines.py`, `care_plans.py`, `routes.py`, registered `factory.py:654-655`, 7 ops) **plus** `care_continuum/models/chronic_disease.py` (5 tables, 0 % migrated). 15 ops. 1 test file. No audit-log.

### 13 · Rehabilitation / physiotherapy — **NOT_IMPLEMENTED**
* Only: `insurance`/`biomedical` enum values, one JSON column `rehabilitation_exercises` (`care_continuum/models/care_journey.py:258`), and `"physiotherapist"` as a profession string (`identity/professional_registry/models.py:15`). **0 ops, 0 tables.**

### 14 · Mental health — **DATA/ANALYTICS ONLY**
* No service. Evidence of *signals only*: encounter-type enum (`care_continuum/enums.py:33,89`), `mental_health_screening` JSON column (`primary_care.py:224`), `mental_health_screened` boolean (`maternal.py:218`), and read-only population analytics (`research_platform/population_health.py:342-362`). **0 ops, 0 tables.**

### 15 · Referral & continuity of care — **CROSS_CUTTING / PARTIAL**
* `care_continuum/models/{referral,care_journey}.py` (12 tables), **18 live ops** including accept/reject/complete/cross-org/timeline/analytics and transitions/handovers. **0 % migrated, no audit, no tests.**
* *This is the most functionally complete of the `cc_*` sub-domains and a strong early candidate for migration + audit + tests.*

### 16 · Insurance & claims — **PARTIAL**
* **Code:** `insurance/` (30 tables), `billing/` (5, 100 %), `payments/` (28, 100 %). **API:** 62 ops (`/insurance` 1, `/claims` 4, `/billing` 11, `/payments` 38, `/tiers` 4).
* **Migrations:** **`ins_*` 0/30 (0 %)** — the largest unmigrated live API domain after `care_continuum`; billing/payments fully migrated.
* **Audit-log:** insurance ×59 (good). **Tests:** 1 insurance + 2 billing.
* **Gap:** insurance schema cannot be provisioned from migrations.

### 17 · Home healthcare — **CROSS_CUTTING / PARTIAL**
* `cc_home_care_plans`, `cc_community_care_records` (2 tables) + `nursing/coordination.py`; 4 live ops (`/home-care-plans`, `/community-care-records`). **0 % migrated, no audit, no tests** in the care-continuum layer (nursing has 16 audit writes).

### 18 · Medical equipment & maintenance — **PARTIAL**
* `biomedical/` (12 tables, **100 % migrated**), `devices/` (10, 100 %), API 52 ops (`/biomedical` 17, `/device-integration` 24, `/device`). **Gap:** **no immutable audit-log** for equipment/maintenance actions; 1 test file.

---

## 6. Shared dependencies (across all services)

| Capability | Implementation (evidence) | Notes |
|---|---|---|
| Identity / authentication | `backend/app/identity/` (85 tables, 78 migrated = 91.8 %), `/niam` 229 ops | the single identity platform |
| Authorization (RBAC/ABAC) | `/authz` 25 ops, `backend/app/security/`, `domain_platform/` | enforcement varies per service (see §9) |
| Patient identity (MPI) | `backend/app/services/mpi/` (+ `canonical_service.py`, `matcher.py`, `resolver.py`, `blocking.py`), `/api/v1/canonical-patients`, `/mpi` | shared patient matching |
| Immutable audit | `backend/app/audit/audit_log.py`, `services/audit_service.py::log_action` | **not used by 7 of 18 services** (§9) |
| Event bus / outbox | `backend/app/kernel/event_bus/outbox.py`, `services/outbox_service.py`, `models/outbox.py` | transactional outbox |
| Offline clinical mode | `services/offline_sync_service.py`, `integration/offline.py`, `citizen_platform/offline.py`, `backend/app/national/tests/offline` | partial; national-level untested here |
| FHIR R4 | `backend/app/fhir/`, `national/fhir/*`, `/fhir` 28 ops | mappers exist per resource |
| Tenant isolation | `TenantMixin` on `cc_*`, `lab_id` scoping in routes | inconsistent (see §9) |
| Search | `capabilities/search_service/` | shared core |
| Notifications | `backend/app/notifications/` | shared core |
| Domain platform | `backend/app/domain_platform/` (6 tables, 100 % migrated) | 11 canonical domains |

---

## 7. Duplicate functionality / duplicated ownership

| Finding | Evidence | Risk |
|---|---|---|
| **`national_facilities` modelled twice** | declared in `backend/app/models/clinical_scope.py` **and** `backend/app/national/domain/facility.py` | conflicting ownership (ties to open DB question on `facilities`/`organizations`/`national_facilities`) |
| **Multiple laboratory surfaces** | `lims/`, `services/lab`, `routes/test_results.py`, `routes/stats.py`, `routes/qc` | overlapping lab read paths; needs contract consolidation (Phase 6) |
| **Laboratory logic in two layers** | `app/services/*_service.py` vs `lims/` package | service-extraction legacy (9 services) alongside new bounded context |
| **Patient data in `national/` vs `ehr/` vs `national_data/`** | 106 national tables, 18 ehr tables, 36 `dp_*` tables | patient-record ownership ambiguity |

No **table-name** duplication elsewhere (only `national_facilities`), per
`inventory_scan.json._duplicate_tables`.

---

## 8. Missing APIs

| Service | Missing / thin API |
|---|---|
| Dental | none at all |
| Rehabilitation | none at all |
| Mental health | none (analytics only) |
| Primary care / maternal / immunization / chronic / referral / home care | **read** coverage is thin: most `cc_*` resources expose only `POST` and sometimes `GET list` — **no update/delete/lifecycle** endpoints (e.g. `vaccination-records` POST+GET only; `antenatal-care-visits` POST only) |
| Insurance | only `/insurance/{id}` — no full coverage/authorization/appeal API despite 30 tables |
| Hospital | hospital-hierarchy CRUD is missing (models exist, `/hospital` covers 25 ops, not hierarchy) |

---

## 9. Authorization, audit and test gaps (must not be closed by documentation)

### 9.1 Immutable audit-log writes — absent in 7 services

`grep log_action|AuditLog` per module: `care_continuum` **0**, `hospital` **0**,
`critical_care` **0**, `blood_bank` **0**, `biomedical` **0**, `chronic_care` **0**,
`public_health` **0** (present: lims 9, nursing 16, pharmacy 6, radiology 4, ems 2, insurance 59).

*AuditMixin columns (`created_by`/`updated_by`) are **not** an immutable audit
log; they do not satisfy the constitutional audit requirement.*

### 9.2 56 operations with no declared OpenAPI security (verify, do not assume)

Potentially sensitive and **must be re-verified in Phase 7**:

| Operation | Concern |
|---|---|
| `GET /citizen/health-record`, `/citizen/results`, `/citizen/orders`, `/citizen/profile` | health data under citizen session — confirm session enforcement |
| `GET /history/{phone}`, `/r/{token}`, `/r/{token}/pdf`, `/qr/{token}`, `/qr-medical/{token}`, `/test-profiles` | token/phone-based result access — enumeration & entitlement risk |
| `POST /niam/accounts/`, `/niam/accounts/{uuid}/lock|unlock`, `/niam/account-requests/` | account lifecycle without declared security |
| `POST /demo/access`, `GET /setup/status` | environment-dependent |
| `POST /edge/agent/*`, `/device-integration/wearables/webhook/{provider}` | machine-to-machine; confirm signature auth |

**No finding is closed here.** Declared-security absence is a *review trigger*, not proof of vulnerability (some flows authenticate via cookies/signatures outside OpenAPI).

### 9.3 Dedicated tests — absent for the biggest cross-cutting surface

`care_continuum` = **0 test files** for **74 ops / 45 tables**; insurance 1,
biomedical 1, hospital 1, nursing 1. Laboratory (6), blood bank (8), radiology (5) are the better-tested services.

---

## 10. Missing migrations — the systemic defect

**407 of 833 ORM tables (48.9 %) are covered by Alembic; 426 are not.**
(`coverage_by_context.py`, `coverage_by_context.json`.)

| Context | Tables | Covered | Missing | Coverage |
|---|---:|---:|---:|---:|
| `national` | 106 | 8 | 98 | 7.5 % |
| `governance` | 64 | 6 | 58 | 9.4 % |
| **`care_continuum`** | **45** | **0** | **45** | **0 %** |
| `clinical` | 41 | 2 | 39 | 4.9 % |
| `national_data` | 36 | 0 | 36 | 0 % |
| **`insurance`** | **30** | **0** | **30** | **0 %** |
| `document_intelligence` | 21 | 0 | 21 | 0 % |
| **`ehr`** | **18** | **0** | **18** | **0 %** |
| `health_data` | 17 | 0 | 17 | 0 % |
| `hospital` | 14 | 1 | 13 | 7.1 % |
| `identity` | 85 | 78 | 7 | 91.8 % |
| `models` | 71 | 66 | 5 | 93.0 % |
| `lims` | 35 | 35 | 0 | 100 % |
| `pharmacy` | 27 | 27 | 0 | 100 % |
| `payments` | 28 | 28 | 0 | 100 % |
| `radiology` | 18 | 17 | 1 | 94.4 % |
| `blood_bank` | 17 | 17 | 0 | 100 % |
| `ems` | 12 | 12 | 0 | 100 % |
| `biomedical` | 12 | 12 | 0 | 100 % |

> **Why this matters:** the previously reported *12 uncovered hospital tables*
> is **correct and reproducible** (11 `hospital_*` + `hospitals`) — but it is a
> **symptom**, not the whole problem. The same class of gap affects 426 tables,
> including **every** table behind primary care, maternal care, immunization,
> chronic disease, referrals, home care, insurance, and the EHR.

**Root cause (evidenced):** schema history includes databases bootstrapped via
`create_all()`, and `backend/tests/conftest.py:104-148` still creates all tables
from combined metadata. Migrations were then layered on top of an
already-created schema, so coverage was never completed. `20250322_0000_create_base_schema.py`
explicitly documents this ("fully idempotent on databases that were
bootstrapped via create_all()").

**Disposition is an architectural/operational decision → escalated in §12, not decided here.**

---

## 11. Cross-service dependency map (for workflow design)

```
Identity/NIAM ──> Authorization ──> every service
        │
        ├── MPI / canonical patient ──> EHR ──> Laboratory, Radiology, Pharmacy,
        │                                        Blood bank, Hospital, Care-continuum
        │
        ├── care_continuum ──> primary care ──> laboratory ──> pharmacy
        │                 └──> referrals ──> hospital ──> feedback
        │                 └──> maternal ──> laboratory ──> pharmacy
        │                 └──> immunization ──> public health surveillance
        │                 └──> chronic ──> primary care ──> pharmacy
        │
        ├── blood bank ──> laboratory (compatibility) ──> hospital (transfusion)
        ├── EMS ──> hospital (admission) ──> radiology ──> laboratory
        ├── insurance ──> billing/payments ──> claims
        └── equipment (biomedical) ──> devices ──> every clinical service
Event bus / outbox: all cross-service state changes are intended to flow here.
```

**Critical dependency risk:** `ehr` (18 tables) and `care_continuum` (45 tables)
are the shared clinical substrate for almost every patient journey, and **both
have 0 % migration coverage**. No patient-centred workflow can be certified
against a freshly provisioned database until this is resolved.

---

## 12. Architectural decisions requiring approval (ADR candidates)

| # | Decision | Why it cannot be decided here |
|---|---|---|
| ADR-A | **Migration strategy for 426 unmigrated tables** — backfill migrations vs accept-as-legacy vs retire dormant contexts | affects every existing database; destructive-migration policy applies |
| ADR-B | **Ownership of `facilities`, `organizations`, `national_facilities`** (and the duplicate `national_facilities` model) | unbounded architectural ownership question |
| ADR-C | **`care_continuum` as a bounded context vs decomposition** into primary-care / maternal / immunization / chronic / referral / home-care services | determines contracts and whether unification is in scope |
| ADR-D | **Audit enforcement model** — central audit interceptor vs per-service `log_action` | constitutional (immutable audit) requirement; cross-cutting |
| ADR-E | **Public token/phone result access** (`/r/{token}`, `/history/{phone}`) — retain, harden, or retire | security vs citizen-access policy |
| ADR-F | **Dual lab implementation** (`lims/` + `services/*_service.py`) consolidation | must preserve four-service compatibility contracts |
| ADR-G | **Insurance schema provisioning** (30 `ins_*` tables, 0 migrations) | financial data; migration risk |
| ADR-H | **`Shared Core` boundary** — must not become a global store for service data | constitutional architecture rule |

---

## 13. Prioritised roadmap (assessment only — no implementation authorised yet)

Ranking = (patient impact × MoH relevance × readiness) ÷ (clinical risk × architecture dependency).

| Wave | Services | Why first | Preconditions |
|---|---|---|---|
| **W1 — Foundation** | Migrations + audit for `care_continuum` (45) and `ehr` (18); MPI/EHR patient-record test | unblocks *every* patient journey; highest structural risk | ADR-A, ADR-B, ADR-D |
| **W2 — High-readiness clinical** | Laboratory ✔, Pharmacy ✔, Radiology ✔, Emergency ✔ | already implemented; wire into end-to-end journeys + contract tests | service contracts (§Phase C) |
| **W3 — Primary & maternal** | Primary care, Maternal & child, Immunization | highest MoH/patient impact; all built, need schema+audit+tests | W1 |
| **W4 — Referral & chronic** | Referral/continuity, Chronic disease, Home care | transitional care + NCD burden; strong existing API | W1, W3 |
| **W5 — Hospital depth** | Hospital hierarchy migrations, critical-care audit | 12 uncovered tables; audit gaps | ADR-A |
| **W6 — Blood bank & equipment hardening** | Blood bank audit-log, biomedical audit-log | safety-critical traceability | ADR-D |
| **W7 — Public health integration** | Surveillance ↔ immunization ↔ notifiable disease | national reporting | W3 |
| **W8 — Insurance** | `ins_*` migrations + claims contract | financial continuity | ADR-G |
| **W9 — New builds** | Dental, Rehabilitation, Mental health (only if approved) | genuinely absent; large new scope | ADR + funding decision |

**Patient-centred journeys to test as they become available** (synthetic data only):
1. Primary care → Laboratory → Pharmacy → Follow-up
2. Emergency → Hospital → Radiology → Laboratory → Discharge
3. Maternal care → Laboratory → Pharmacy → Referral
4. Chronic disease → Primary care → Laboratory → Medication → Follow-up
5. Immunization → Patient record → Public-health surveillance
6. Blood request → Compatibility → Hospital transfusion record
7. Referral → Receiving facility → Clinical feedback

---

## 14. What this inventory does **not** claim

* It does **not** certify any service as production-ready or clinically safe.
* It does **not** close the 56 public operations as safe or unsafe — they are queued for Phase 7.
* It does **not** decide the migration or ownership questions in §12.
* It does **not** authorise implementation of the 18 services.

**`FINAL_DECISION.md` remains HOLD.**

---

## 15. Post-inventory re-verification (additive corrections — 2026-11-17)

Prepared while writing `GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md`. **No prior finding
in §3–§13 was deleted or rewritten**; the corrections below supersede specific numbers
with new evidence and are recorded here for traceability.

### 15.1 Insurance (row 16 in §3, §5 §16) — `PARTIAL` → `UNSERVED / BLOCKED`

* **Live operations = 5, not 62.** OpenAPI tag census of
  `/tmp/opencode/remediation/openapi_20261117_084342.json`: `insurance` **1**,
  `claims` **4**. The `/billing` (11), `/payments` (38) and `/tiers` (4) operations
  belong to **Billing / Payments / Subscriptions**, not to Insurance. The earlier 62
  was a prefix-attribution error.
* **84 coded endpoints are unserved.** `backend/app/insurance/api/` defines
  `claims` 14, `coverages` 8, `coverage_check` 6, `network` 10, `payments` 18,
  `policies` 9, `providers` 7, `referrals` 12 = **84 endpoints**, and the package is
  **never imported** anywhere (`grep` for `insurance.api` in `backend/app` +
  `backend/tests` returns no import). `factory.py:541,605` registers
  `backend/app/routes/insurance.py` (1 endpoint), not the package.
* **Duplicate claims implementations:** `routes/claims.py` (4 live ops →
  `services/claims_service.py`) vs `insurance/api/claims.py` (14 unserved ops →
  `insurance/domain/services.py`).
* Unchanged: 30 `ins_*` tables, **0 % migration coverage**, 1 test file.
* **Requires decision:** ADR-I (register or archive the unserved package), ADR-G
  (schema provisioning). Escalated, not implemented.

### 15.2 Everything else stands

Hospital (12 uncovered = 11 `hospital_*` + `hospitals`), `care_continuum` (45 tables,
0 %, 74 ops, 0 audit, 0 tests), the 426-table systemic gap, and the 56 OpenAPI /
69 walker public-operation reconciliation are all unchanged and are now carried into
`GOVERNANCE/NATIONAL_SERVICE_CONTRACTS.md` §5 and §6.

### 15.3 Hospital (row 02) — corrected from **12** to **13** uncovered tables

The earlier count "12 uncovered = 11 `hospital_*` + `hospitals`" **omitted `bed_assignments`**.
Re-verified directly against all 107 migrations:

* hospital ORM tables: **14**;
* migrated: **1** — `hospital_surgical_safety_checklists` (created by `20260820_0004`);
* **unmigrated: 13** — `hospitals`, `bed_assignments`, and 11 `hospital_*`
  (`beds`, `buildings`, `campuses`, `clinics`, `cost_centers`, `departments`, `floors`,
  `medical_equipment`, `operation_theaters`, `rooms`, `units`);
* `hospital_operation_theaters` is **not** created by any migration; it is only the target of a
  conditional FK in `20260820_0004`. The earlier wording implying it exists was incorrect.

This supersedes the arithmetic only; no prior finding is deleted. It makes the blocker **worse**.

### 15.4 Phase C database rehearsal (2026-11-17) — how it changes this inventory

See `GOVERNANCE/PHASE_C_DATABASE_REHEARSAL_REPORT.md` and
`GOVERNANCE/DATABASE_COMPATIBILITY_REPORT.md` §10. In inventory terms:

* The 426-table gap is confirmed at **407 / 833** ORM tables across **40** contexts
  (`national` 98, `governance` 58, `care_continuum` 45, `clinical` 39, `national_data` 36,
  `insurance` 30, `document_intelligence` 21, `ehr` 18, `health_data` 17).
* Every service judged `BLOCKED` for a 0 % migration rate is still `BLOCKED` (no verdict upgraded).
* The forward upgrade from `20260815_0022` **passes** (405→433, data reconciled), but partial rollback
  to that revision is **not** clean (§5 of the Phase C report), and `alembic check` **cannot run**
  because `national_encounters` is missing from metadata (**NR-011**).

---

## 16. Phase 4 re-verification (2026-11-17, additive — CC-006)

This section records the approval-activation Phase 4 review of the same 18 services and seven
patient journeys. **No prior section was rewritten; no service verdict was upgraded from API/model
existence.** Method: read-only re-check of the inventory's status taxonomy (§2), the 18-row table
(§3), the per-service detail (§5), and the earlier corrections (§15), plus the bounded engine
evidence gathered in Phase 3 (E-046…E-052).

| Check | Result |
|---|---|
| 18 services still enumerated with the §2 taxonomy | **PASS** — all 18 rows (01–18) and their original verdicts retained verbatim, including the insurance correction (§15.1); counts quoted only as written in §3, never recomputed from API/model existence |
| Readiness derived from API/model existence only | **Rejected** — `IMPLEMENTED` still requires migrations + authentication + audit writes + dedicated tests; no row changed |
| Seven journeys (J1–J7 in `NATIONAL_SERVICE_CONTRACTS.md` §7) | **PASS** — all seven retained with their evidence-based blockers; none marked ready |
| Capability map / audit / test gaps (§9) | unchanged — no new audit writes or tests were added in this phase |
| Migration gap (§10, 407/833 across 40 contexts; 426-denominator) | unchanged — no migration, DDL or `alembic stamp` executed |
| `FINAL_DECISION.md` / D-020 / D-021 | **HOLD / PENDING / PENDING** — unchanged |

### 16.1 Additive correction to §15.4 (NR-011 is now executed)

§15.4 stated that "`alembic check` **cannot run** because `national_encounters` is missing from
metadata (NR-011)". That statement was accurate at the time but is **superseded by Phase 2 evidence
E-042/E-045**: after the verified NR-011 `env.py` change (CC-004, W-024 closed), `alembic check`
completes without `NoReferencedTableError` and reaches `FAILED: New upgrade operations detected`
(the ADR-A diff). Autogenerate output is byte-equivalent to probe C (12 op-count series and 284
`add_table` names identical). **This is a tooling/metadata correction only — it does not upgrade any
service verdict, close the 407-table gap, or make any migration schema-compatible.**
The original §15.4 wording is preserved above as history.

### 16.2 Cross-reference to Phase 3 engine evidence (no verdict change)

- Workflow journeys J1/J2/J4/J7: synthetic workflow tests passed (E-048 65, E-050 9) for the
  canonical workflow engine, but migration-built-schema P0 workflow failures (F-003/B-007) remain;
  no journey is certified.
- FHIR/HL7 interoperability (services 01/05): synthetic ORU→FHIR and R4 tests passed (E-051 4,
  E-047 24); this is not migration or production verification.
- CDS for services 12/15 and national CDS: the national engine is unverifiable (F-068, D-021 PENDING).
- Offline behaviour (all 18 rows, contract R-OFF-1): `CRDT_MERGE` is first-wins (F-069) and the
  queue remains in memory (F-028) — offline-first is still **NOT SATISFIED**.
- Laboratory (01): Westgard QC 26 tests (E-046) and LIMS authorization 8 tests (E-046) passed in
  isolation; lab service remains IMPLEMENTED per §3, with strict-schema failures still open.

**Conclusion of Phase 4:** inventory and contracts are accurate and evidence-backed as written;
only the §15.4 NR-011 tooling statement needed an additive supersession. No service was activated,
no verdict was changed, and `FINAL_DECISION.md` remains **HOLD**.
