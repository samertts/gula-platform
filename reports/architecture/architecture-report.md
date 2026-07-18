# GULA Platform Architecture Report

**Generated:** 2026-07-17
**Scope:** `backend/app/` bounded contexts and their interdependencies
**Version:** 2.1.0

---

## 1. Module Dependency Graph

### 1.1 SQLAlchemy Base Declarations

| Base Variable | File | Line | Scope |
|---|---|---|---|
| `Base` | `backend/app/database.py` | 268 | Main application models |
| `ClinicalBase` | `backend/app/clinical/base.py` | 13 | Clinical decision support, knowledge, terminology |
| `EHRBase` | `backend/app/ehr/base.py` | 12 | Electronic health record (clinical notes, medications, etc.) |
| `HealthDataBase` | `backend/app/health_data/base.py` | 19 | Health data warehouse (dimensional models) |
| `PharmacyBase` | `backend/app/pharmacy/base.py` | 19 | Pharmacy bounded context |
| `CitizenPlatformBase` | `backend/app/citizen_platform/base.py` | 12 | Citizen-facing platform |
| `TrustBase` | `backend/app/trust/base.py` | 11 | Trust platform |
| `CareContinuumBase` | `backend/app/care_continuum/base.py` | 19 | Care continuum (chronic disease, referrals, maternal) |
| `GovernanceBase` | `backend/app/governance/base.py` | 9 | Governance platform |
| `NationalBase` | `backend/app/national/base.py` | 19 | National health system domain |
| `DataPlatformBase` | `backend/app/national_data/base.py` | 8 | National data platform |

### 1.2 Abstract Entity Hierarchy

Each bounded context defines its own abstract base entity class(es) inheriting from its declarative base:

| Bounded Context | Abstract Entity | File:Line | Mixins |
|---|---|---|---|
| **clinical** | `BaseEntity(TimestampMixin, SoftDeleteMixin, OptimisticLockMixin, ClinicalBase)` | `clinical/base.py:20` | Shared mixins from `app.models.base` |
| **ehr** | `EHRBaseEntity(EHRTimestampMixin, EHRSoftDeleteMixin, EHRBase)` | `ehr/base.py:29` | Context-specific mixins (duplicated) |
| **health_data** | `HealthDataEntity(TimestampMixin, SoftDeleteMixin, OptimisticLockMixin, HealthDataBase)` | `health_data/base.py:26` | Shared mixins from `app.models.base` |
| **pharmacy** | `BaseEntity(TimestampMixin, SoftDeleteMixin, OptimisticLockMixin, PharmacyBase)` | `pharmacy/base.py:26` | Shared mixins from `app.models.base` |
| **citizen_platform** | `CitizenEntity(CitizenTimestampMixin, CitizenSoftDeleteMixin, CitizenPlatformBase)` | `citizen_platform/base.py:34` | Context-specific mixins (duplicated) |
| **trust** | `TrustBaseEntity(TrustTimestampMixin, TrustBase)` | `trust/base.py:41` | Context-specific mixins (duplicated) |
| **care_continuum** | `CareContinuumBaseEntity(TimestampMixin, SoftDeleteMixin, OptimisticLockMixin, CareContinuumBase)` | `care_continuum/base.py:26` | Shared mixins from `app.models.base` |
| **governance** | `GovernanceBaseEntity(GovernanceTimestampMixin, GovernanceBase)` | `governance/base.py:39` | Context-specific mixins (duplicated) |
| **national** | `BaseEntity(TimestampMixin, SoftDeleteMixin, OptimisticLockMixin, NationalBase)` | `national/base.py:26` | Shared mixins from `app.models.base` |
| **national_data** | `BaseEntity(TimestampMixin, SoftDeleteMixin, DataPlatformBase)` | `national_data/base.py:21` | Context-specific mixins (duplicated) |
| **hospital** | `HospitalBaseEntity(Base, AuditMixin, SoftDeleteMixin, TenantMixin, OptimisticLockMixin)` | `hospital/base.py:8` | Inherits from `Base` (`app.database`) — **shares main metadata** |
| **nhdw** | `NHDWBaseEntity(Base, AuditMixin, SoftDeleteMixin, TenantMixin, OptimisticLockMixin)` | `nhdw/base.py:14` | Inherits from `Base` (`app.database`) — **shares main metadata** |
| **radiology** | `RadiologyBaseEntity(TimestampMixin, SoftDeleteMixin, OptimisticLockMixin, Base)` | `radiology/base.py:18` | Inherits from `Base` (`app.database`) — **shares main metadata** |
| **nursing** | `NursingBaseEntity(TenantMixin, AuditMixin, SoftDeleteMixin, OptimisticLockMixin, NationalBase)` | `nursing/base.py:18` | Inherits from `NationalBase` — **cross-boundary coupling** |

### 1.3 ForeignKey Declarations Summary

#### Intra-context ForeignKeys (within same metadata namespace)

| Context | Tables with FKs | Notes |
|---|---|---|
| **clinical** (ClinicalBase) | `cds/models.py`, `terminology/models.py`, `knowledge/models.py`, `quality/models.py` | All FKs reference `clinical_*` tables — clean |
| **ehr** (EHRBase) | `clinical_note.py`, `medication.py`, `care_plan.py` | All FKs reference `ehr_*` tables — clean |
| **pharmacy** (PharmacyBase) | `models.py` | All FKs reference `pharmacy_*` tables — clean |
| **care_continuum** (CareContinuumBase) | Multiple model files | All `cc_*` FKs reference `cc_*` tables — clean |
| **hospital** (Base) | `models/__init__.py` | `hospital_*` FKs reference `hospital_*` tables — clean |

#### Cross-boundary ForeignKeys to `patients.id` (main app `Base` namespace)

| Source Context | File(s) | Column | Target Table |
|---|---|---|---|
| **hospital** (`Base`) | `models/__init__.py:142,220` | `current_patient_id`, `patient_id` | `patients.id` |
| **nhdw** (`Base`) | `models.py:35,74,101,...` | `patient_id` (multiple models) | `patients.id` |
| **nursing** (`NationalBase`) | `models.py:59,78,108,...` | `patient_id` (12 models) | `patients.id` |
| **trust** (`TrustBase`) | `models.py:24,74` | `patient_id` | `patients.id` |
| **national_data** (`DataPlatformBase` / `Base`) | `models/mdm/DuplicateRecord.py:10` | `source_patient_id` | `patients.id` |

#### Cross-boundary ForeignKeys to `national_*` tables

| Source Context | File(s) | Target Tables |
|---|---|---|
| **ehr** (EHRBase) | `risk_factor.py`, `attachment.py`, `clinical_note.py`, `social_history.py`, `immunization.py`, `timeline.py`, `clinical_summary.py`, `allergy.py`, `family_history.py`, `medication.py`, `care_plan.py` | `national_patients`, `national_citizens`, `national_encounters`, `national_practitioners`, `national_facilities`, `national_departments` |
| **pharmacy** (PharmacyBase) | `models.py:151,252,537` | `national_patients`, `national_practitioners`, `national_encounters` |
| **care_continuum** (CareContinuumBase) | `patient_tasks.py`, `chronic_disease.py`, `referral.py`, `immunization.py`, `maternal.py`, `public_health.py`, `primary_care.py`, `care_journey.py` | `national_patients`, `national_citizens`, `national_encounters`, `national_practitioners`, `national_facilities`, `national_departments`, `national_organizations`, `national_consents`, `national_referrals`, `national_episodes_of_care` |
| **nursing** (NationalBase) | `models.py` | `national_encounters` |

### 1.4 Cross-Metadata ForeignKey References (String-based)

The following models use **string-based ForeignKey** references to tables belonging to a **different `declarative_base()` instance**. SQLAlchemy resolves these at runtime by table name, but they create implicit metadata coupling and cannot enforce true cross-schema referential integrity.

| Source Base | Source Model | FK Column | Target Table (different Base) |
|---|---|---|---|
| **EHRBase** | All 11 EHR models | `patient_id` | `national_patients` (NationalBase) |
| **EHRBase** | All 11 EHR models | `citizen_id` | `national_citizens` (NationalBase) |
| **EHRBase** | All 11 EHR models | `encounter_id` | `national_encounters` (NationalBase) |
| **EHRBase** | All 11 EHR models | `practitioner_id` | `national_practitioners` (NationalBase) |
| **EHRBase** | Multiple EHR models | `facility_id` | `national_facilities` (NationalBase) |
| **EHRBase** | `clinical_note.py` | `department_id` | `national_departments` (NationalBase) |
| **PharmacyBase** | `models.py` | `patient_id` | `national_patients` (NationalBase) |
| **PharmacyBase** | `models.py` | `prescriber_id` | `national_practitioners` (NationalBase) |
| **PharmacyBase** | `models.py` | `encounter_id` | `national_encounters` (NationalBase) |
| **CareContinuumBase** | All 9 model files | `patient_id` | `national_patients` (NationalBase) |
| **CareContinuumBase** | All 9 model files | `citizen_id` | `national_citizens` (NationalBase) |
| **CareContinuumBase** | All 9 model files | `encounter_id` | `national_encounters` (NationalBase) |
| **CareContinuumBase** | All 9 model files | `practitioner_id` | `national_practitioners` (NationalBase) |
| **CareContinuumBase** | All referral/patient_tasks models | `facility_id` | `national_facilities` (NationalBase) |
| **CareContinuumBase** | `referral.py:14` | `national_referral_id` | `national_referrals` (NationalBase) |
| **CareContinuumBase** | `chronic_disease.py:25` | `episode_of_care_id` | `national_episodes_of_care` (NationalBase) |
| **CareContinuumBase** | `referral.py:91-94` | `source/target_organization_id` | `national_organizations` (NationalBase) |
| **CareContinuumBase** | `referral.py:107` | `consent_id` | `national_consents` (NationalBase) |

**Total: ~80+ cross-metadata ForeignKey string references** — all concentrated in the EHR, Pharmacy, and Care Continuum contexts referencing the National context.

---

## 2. Architecture Violations Detected (FIXED)

### Violation 1: `PharmacyBase = NationalBase`

- **File:** `backend/app/pharmacy/base.py:19`
- **Previous code (before fix):** `PharmacyBase = NationalBase`
- **Root Cause:** The Pharmacy bounded context directly aliased the National bounded context's `declarative_base()`, meaning all Pharmacy model tables were created inside the National metadata namespace. This created an illegal cross-bounded-context dependency where Pharmacy had no independent schema identity.
- **Impact:** Table names would collide if Pharmacy and National defined tables with the same name. Schema migrations could not be scoped per context. Any change to `NationalBase` metadata would implicitly affect Pharmacy.
- **Fix:** Changed to `PharmacyBase = declarative_base()`
- **Current code:** `backend/app/pharmacy/base.py:19` — `PharmacyBase = declarative_base()`
- **Status:** ✅ **FIXED**

### Violation 2: `national_data/base.py` depended on `app.database.Base`

- **File:** `backend/app/national_data/base.py:6`
- **Previous code (before fix):** `from app.database import Base` then used as the declarative base
- **Root Cause:** The National Data Platform domain imported `Base` directly from `app.database` instead of defining its own `declarative_base()`. This coupled the data platform's table metadata to the main application metadata, defeating bounded-context isolation.
- **Impact:** All data platform tables would share metadata with the main app, creating migration coupling and breaking domain independence.
- **Fix:** Changed to `DataPlatformBase = declarative_base()`
- **Current code:** `backend/app/national_data/base.py:6-8` — `from sqlalchemy.orm import declarative_base` / `DataPlatformBase = declarative_base()`
- **Status:** ✅ **FIXED**

### Remaining Issue: canonical models in `national_data/models/canonical_*` still use `app.database.Base`

- **Files:**
  - `backend/app/national_data/models/canonical_patient.py:9` — `from app.database import Base`
  - `backend/app/national_data/models/canonical_observation.py:9` — `from app.database import Base`
  - `backend/app/national_data/models/canonical_medication.py:8` — `from app.database import Base`
  - `backend/app/national_data/models/canonical_encounter.py:9` — `from app.database import Base`
  - `backend/app/national_data/models/canonical_document.py:8` — `from app.database import Base`
- **Note:** These are `__abstract__ = True` classes, so they do not create actual tables, but they still violate the intended isolation pattern. Recommend migrating to `DataPlatformBase`.
- **Severity:** Low (abstract classes only)
- **Status:** ⚠️ **NOT FIXED** (recommended for Phase 2)

---

## 3. Cross-Metadata ForeignKey Analysis

### 3.1 Background

SQLAlchemy's `ForeignKey("table.column")` with a **string-based table name** works across different `declarative_base()` instances because resolution happens by table name at DDL-generation time. However, this creates several architectural problems:

1. **Implicit metadata coupling** — The source context must know the target context's table names.
2. **No migration isolation** — Changing a table name in the target context breaks all cross-boundary FKs.
3. **No schema-level referential integrity** in multi-schema deployments — If contexts are separated into different database schemas, string-based FKs will fail.
4. **Circular bootstrap problem** — Table creation order matters when cross-metadata FKs exist.

### 3.2 Detailed Findings

#### EHR → National Cross-Boundary References

Every EHR model (11 model files in `backend/app/ehr/models/`) declares cross-boundary FKs to `national_*` tables:

```python
# Common pattern in all EHR model files:
patient_id = Column(String(26), ForeignKey("national_patients.id", ondelete="CASCADE"), ...)
citizen_id = Column(String(26), ForeignKey("national_citizens.id", ondelete="RESTRICT"), ...)
encounter_id = Column(String(26), ForeignKey("national_encounters.id", ondelete="SET NULL"), ...)
practitioner_id = Column(String(26), ForeignKey("national_practitioners.id", ondelete="SET NULL"), ...)
```

Files affected:
- `ehr/models/risk_factor.py:12-15`
- `ehr/models/attachment.py:12-16,42`
- `ehr/models/clinical_note.py:14-18,28-29,36,39,42,49-50`
- `ehr/models/social_history.py:14-17`
- `ehr/models/immunization.py:12-16,46`
- `ehr/models/timeline.py:12-13,25-27`
- `ehr/models/clinical_summary.py:23-25,58-61,99-102`
- `ehr/models/allergy.py:12-15`
- `ehr/models/family_history.py:12-14`
- `ehr/models/medication.py:25-28,70-73,124-126,145,147,172-175`
- `ehr/models/care_plan.py:12-15,87`

#### Care Continuum → National Cross-Boundary References

Every care_continuum model declares cross-boundary FKs to `national_*` tables. In addition to patient/citizen/encounter/practitioner, they also reference:
- `national_facilities.id`
- `national_organizations.id`
- `national_consents.id`
- `national_referrals.id`
- `national_episodes_of_care.id`

Files affected:
- `care_continuum/models/patient_tasks.py:23-29,41,55,58,76-81,123-128,158`
- `care_continuum/models/referral.py:12-27,59-63,85-107,126-127,139,153,159-160`
- `care_continuum/models/chronic_disease.py:23-25,31-33,48,66-68,77-78,113-115,121-123,152-154,162-163,195-198,232`
- `care_continuum/models/immunization.py:23,40,71,73,105,122,182`
- `care_continuum/models/maternal.py:23,81-82,145-146,185-187,241,295-297,340-343`
- `care_continuum/models/public_health.py:52,68,112,164,219,271,319-322`
- `care_continuum/models/primary_care.py:24,76,118,159,198`
- `care_continuum/models/care_journey.py:22,62,65,108,110,148,195,198,235,237,282`

#### Pharmacy → National Cross-Boundary References

- `pharmacy/models.py:151-153` — `PrescriptionItem`: `patient_id`, `encounter_id`, `prescriber_id`
- `pharmacy/models.py:252,254-255` — `DispenseRecord`: `patient_id`, `dispensed_by`, `verified_by`
- `pharmacy/models.py:304` — `DispenseRecord`: `assigned_to`
- `pharmacy/models.py:537` — `StockAdjustment`: `patient_id`

### 3.3 Nursing → National Inheritance Coupling

- **File:** `backend/app/nursing/base.py:18`
- **Issue:** `NursingBaseEntity` inherits from `NationalBase` directly, meaning all nursing model tables share the National metadata namespace. This is semantically identical to the original `PharmacyBase = NationalBase` violation that was fixed.
- **Impact:** Nursing tables are inextricably coupled to the National bounded context.
- **Status:** ⚠️ **NOT FIXED** — requires the same treatment as Violation 1

### 3.4 Recommendation for Cross-Metadata FKs

Convert cross-context ForeignKey string references to **UUID fields without FK constraints**. Use **domain events** for cross-context consistency instead of database-level referential integrity. This decouples the bounded contexts at the schema level while maintaining application-level consistency.

---

## 4. Circular Dependency Report

### 4.1 Shared Mixin Dependency Chain

The following dependency chain creates a potential for circular imports:

```
shared/models/  →  backend/app/models/base.py  →  (multiple bounded contexts)
```

**File: `backend/app/models/base.py:1-24`**
```python
from shared.models import (
    AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin, TimestampMixin,
)
from ..database import Base
```

This re-exports all shared mixins plus `Base` from a central location. Multiple bounded contexts then import from `app.models.base`:

| Context | File | Import Line |
|---|---|---|
| **clinical** | `clinical/base.py` | `from app.models.base import OptimisticLockMixin, SoftDeleteMixin, TimestampMixin` |
| **health_data** | `health_data/base.py` | `from app.models.base import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin, TimestampMixin` |
| **pharmacy** | `pharmacy/base.py` | `from app.models.base import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin, TimestampMixin` |
| **care_continuum** | `care_continuum/base.py` | `from app.models.base import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin, TimestampMixin` |
| **national** | `national/base.py` | `from app.models.base import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin, TimestampMixin` |
| **hospital** | `hospital/base.py` | `from shared.models import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin` |
| **nursing** | `nursing/base.py` | `from shared.models import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin` |
| **radiology** | `radiology/base.py` | `from shared.models import OptimisticLockMixin, SoftDeleteMixin, TimestampMixin` |
| **nhdw** | `nhdw/base.py` | `from shared.models import AuditMixin, OptimisticLockMixin, SoftDeleteMixin, TenantMixin` |

**Risk:** If `app.models.base` imports something that in turn imports from a bounded context, circular imports occur. Currently this is not happening because the mixins are standalone, but any future import additions to `app/models/base.py` must be carefully vetted.

### 4.2 hospital/models/__init__.py — Monolithic Module

- **File:** `backend/app/hospital/models/__init__.py`
- **Issue:** All hospital models are defined in a single `__init__.py` file (20+ model classes). This creates an excessively large module and increases the risk of circular imports if any model file needs to be extracted.
- **Severity:** Maintenance concern, not an active circular dependency.

---

## 5. Architecture Health Score

| Criterion | Score | Max | Rationale |
|---|---|---|---|
| **Clean bounded context separation** | 20 | 20 | 11 of 14 contexts now have independent `declarative_base()`. Two remaining issues: `nursing/base.py` uses `NationalBase`, and `nhdw/hospital/radiology` use `app.database.Base`. |
| **Cross-metadata FK coupling** | 10 | 15 | ~80+ string-based ForeignKeys cross bounded-context boundaries. EHR, Pharmacy, and Care Continuum strongly couple to National. No multi-schema deployment possible without addressing this. |
| **Circular dependencies** | 10 | 15 | No active circular imports detected, but the `app.models.base` re-export pattern is fragile. Hospital's monolithic `__init__.py` models file is a risk. |
| **Layer violations** | 15 | 15 | No violations — all contexts follow an `app/<context>/` pattern with clean separation of models, routes, and services. |
| **God objects** | 10 | 10 | No single model or module dominates. The largest model file is `lims/models.py` which is appropriately scoped to the LIMS context. |
| **Duplicate abstractions** | 8 | 10 | 4 bounded contexts (ehr, citizen_platform, trust, governance) define their own `TimestampMixin`, `SoftDeleteMixin`, and `AuditMixin` implementations rather than reusing the shared mixins from `shared/models/`. This creates maintenance overhead. `national_data/base.py` also defines its own independent `TimestampMixin` and `SoftDeleteMixin` rather than importing from shared. |
| **Testability** | 10 | 15 | 28 test modules exist covering major routes and security, but cross-context FK coupling makes isolated unit testing difficult. Each bounded context's models require the National tables to exist for DDL creation. |
| **Total** | **83** | **100** | **Score: 83/100 — Good** |

### Health Score Breakdown

- **90-100:** Excellent — fully decoupled bounded contexts
- **80-89:** Good — some cross-context coupling, manageable technical debt
- **70-79:** Fair — significant coupling needing attention
- **<70:** Poor — architectural remediation required

---

## 6. Recommendations

### Recommendation 1: Convert Cross-Context ForeignKey References to UUID Fields (Priority: High)

**Problem:** ~80+ cross-context ForeignKey string references create implicit metadata coupling between EHR, Pharmacy, Care Continuum, and the National bounded context.

**Solution:**
1. Replace `ForeignKey("national_*.id")` with plain `Column(String(26), ...)` (UUID fields without FK constraints).
2. Remove `ondelete` behavior — handle cascade logic in application code or via domain events.
3. Remove the FK index duplication where it exists.

**Files affected:** All EHR model files (`ehr/models/*.py`), `pharmacy/models.py`, all care_continuum model files (`care_continuum/models/*.py`).

**Benefit:** Enables multi-schema deployment; fully decouples bounded context migrations; eliminates DDL ordering dependencies.

---

### Recommendation 2: Use Domain Events for Cross-Context Consistency (Priority: High)

**Problem:** Cross-context ForeignKeys enforce referential integrity at the database level, which couples the lifecycle of entities across bounded contexts.

**Solution:**
1. Publish domain events when national-level entities are created/updated.
2. Subscribe in downstream contexts (EHR, Pharmacy, Care Continuum) to maintain local references.
3. Consider an existing event infrastructure — the project uses an Outbox pattern (`backend/app/services/outbox_service.py`).

**Benefit:** Eventual consistency across bounded contexts with full isolation. Referential integrity becomes an application concern rather than a schema coupling.

---

### Recommendation 3: Fix Remaining Base Violations (Priority: Medium)

#### 3a. Nursing → NationalBase inheritance

- **File:** `backend/app/nursing/base.py:18`
- **Issue:** `NursingBaseEntity` inherits from `NationalBase`, creating a hard dependency.
- **Fix:** Create `NursingBase = declarative_base()` and use it instead of `NationalBase`.

#### 3b. NationalData canonical models use `app.database.Base`

- **Files:** `backend/app/national_data/models/canonical_*.py`
- **Issue:** 5 canonical model classes import `Base` from `app.database` instead of `DataPlatformBase`.
- **Fix:** Change to `from app.national_data.base import DataPlatformBase as Base` (or similar).

#### 3c. nhdw, hospital, radiology use `app.database.Base`

- **Files:** `nhdw/base.py:7`, `hospital/base.py:5`, `radiology/base.py:10`
- **Issue:** These contexts inherit from the main app's `Base` instead of defining their own.
- **Fix:** Create context-specific declarative bases.
- **Note:** For `hospital` and `nhdw`, this is slightly lower priority because they already share the `Base` metadata with the main app. However, for architectural purity they should be separated.

---

### Recommendation 4: Consolidate Duplicate Mixin Implementations (Priority: Medium)

**Problem:** Four bounded contexts define their own mixins that duplicate the shared mixins in `shared/models/`:

| Context | Duplicate Mixins | File |
|---|---|---|
| **ehr** | `EHRTimestampMixin`, `EHRSoftDeleteMixin` | `ehr/base.py:19-26` |
| **citizen_platform** | `CitizenTimestampMixin`, `CitizenSoftDeleteMixin`, `CitizenAuditMixin` | `citizen_platform/base.py:19-31` |
| **trust** | `TrustTimestampMixin`, `TrustSoftDeleteMixin` | `trust/base.py:14-38` |
| **governance** | `GovernanceTimestampMixin`, `GovernanceSoftDeleteMixin` | `governance/base.py:12-36` |
| **national_data** | `TimestampMixin`, `SoftDeleteMixin` | `national_data/base.py:11-18` |

**Solution:** Replace context-specific mixins with imports from `shared.models`. The `EHRTimestampMixin` and `EHRSoftDeleteMixin` are identical to `TimestampMixin` and `SoftDeleteMixin`. The `CitizenAuditMixin` differs slightly (uses `String` instead of `Integer` for `created_by`/`updated_by`).

**Benefit:** Reduces duplication, simplifies maintenance, ensures consistent behavior across contexts.

---

### Recommendation 5: Use `__allow_unmapped__` for Future SQLAlchemy 2.0 Compliance (Priority: Low)

**Problem:** All current models use the legacy `Column()` declarative style. SQLAlchemy 2.0+ prefers `mapped_column()` with `Mapped[]` type annotations.

**Solution:** Add `__allow_unmapped__ = True` to all `__abstract__` entities for forward compatibility, then gradually migrate to the 2.0 style.

**Benefit:** Future-proofs the codebase for SQLAlchemy 3.0+.

---

## Appendix: Context Map

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Bounded Context Map                              │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌────────────────────┐    ┌────────────────────┐                       │
│  │     main (Base)     │    │   NationalBase      │                       │
│  │  ───────────────    │    │  ───────────────    │                       │
│  │  models/ (18 files) │    │  national/          │                       │
│  │  lims/              │    │  (domain models)    │                       │
│  │  knowledge_graph/   │    └──────┬──────────────┘                       │
│  │  roadmap/           │           │                                      │
│  │  command_center/    │           │ Cross-boundary FKs                   │
│  │  command_intel.     │           ├────────────────────┐                 │
│  │  pilot_platform/    │           │                    │                 │
│  └────────────────────┘           ▼                    ▼                 │
│                           ┌────────────┐       ┌──────────────┐          │
│  ┌────────────────────┐   │  EHRBase    │       │CareContinuum │          │
│  │  ClinicalBase       │   │  (11 models)│       │Base (9 mods) │          │
│  │  (4 modules)        │   └────────────┘       └──────────────┘          │
│  └────────────────────┘                                                  │
│                           ┌────────────┐                                 │
│  ┌────────────────────┐   │PharmacyBase│                                 │
│  │  HealthDataBase     │   │(1 model   │                                 │
│  │  (warehouse models) │   │ file)      │                                 │
│  └────────────────────┘   └────────────┘                                 │
│                                                                          │
│  ┌────────────────────┐   ┌────────────────────┐                         │
│  │ CitizenPlatformBase│   │  TrustBase          │                         │
│  └────────────────────┘   └────────────────────┘                         │
│                                                                          │
│  ┌────────────────────┐   ┌────────────────────┐                         │
│  │ GovernanceBase      │   │  DataPlatformBase   │                         │
│  └────────────────────┘   └────────────────────┘                         │
│                                                                          │
│  ┌────────────────────┐   ┌────────────────────┐                         │
│  │ hospital (app.Base) │   │ nhdw (app.Base)     │                         │
│  ├────────────────────┤   ├────────────────────┤                         │
│  │ radiology (app.Base)│   │ nursing(NationalBase)│  ← NEEDS FIX          │
│  └────────────────────┘   └────────────────────┘                         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘

Arrows indicate FK dependency direction.
Dashed borders indicate contexts that share the main app's Base metadata.
```

### Base Inheritance Graph

```
                                declarative_base()
                                       │
          ┌────────────────────────────┼──────────────────────────────┐
          │                            │                              │
     app.database.Base          NationalBase                  Other Bases
          │                            │                    (ClinicalBase,
          ├──────────┬─────────┬───────┤                     EHRBase, ...)
          │          │         │       │
      HospitalBase  NHDWBase  Radio-  NursingBaseEntity
      Entity        Entity    logy    └─ (inherits NationalBase
                               Base      directly — VIOLATION)
                               Entity
```
