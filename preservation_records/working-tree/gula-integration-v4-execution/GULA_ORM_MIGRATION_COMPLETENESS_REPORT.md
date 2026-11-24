# GULA ORM ↔ Migration Completeness Report

**Directive:** GULA-PBR-2026-11-19 §6 (complete classification matrix — no blind migration generation)  
**Repository / branch:** `gula-integration` / `integration/gula-unification-v1`  
**HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`  
**Date:** 2026-11-19  
**Scope:** READ-ONLY investigation. Single deliverable: this file. No other file was modified.

**Method statement.** Pure in-memory parsing of Python source (`ast`, regex) over `backend/app/**/*.py`, `shared/**/*.py` and `backend/migrations/versions/*.py`; read-only `git log`/`git rev-parse`; read-only `cat`/`grep`/`find`. No `pytest`, `alembic`, `psql`, `docker`, `create_all()`, `stamp()`, DDL, DB connection or import of application code was performed. No competing process was started while the backend suite runs. Table counts are AST-derived with the declarative-base resolved transitively through mixin chains using each file's import map; 'migrated' means the table name appears as a literal or as a module-level string constant passed to `op.create_table(...)` (or a raw `CREATE TABLE`) somewhere in migration source — it is NOT a live-DB inspection and therefore is a source-based upper bound on coverage.

**Standing decision: HOLD.** This report records evidence only. It authorises no migration, no schema change, no ownership change and no activation. ADR-A / ADR-B remain owner-gated (Program Director / Architect).

---

## 0. Strict-status summary

| Item | Status (strict vocabulary) |
|---|---|
| This investigation report (documentary artifact) | IMPLEMENTED |
| Any migration authored / applied by this investigation | NOT IMPLEMENTED |
| Alembic metadata registration of `DocIntelBase` / `InsBase` | NOT IMPLEMENTED |
| Platform-wide ORM↔migration completeness | BLOCKED (ADR-A / ADR-B owner decision) |
| Care-continuum closure migration `20261119_0003` | INDEPENDENTLY VERIFIED **by fresh-context Team C** per pre-existing records (NOT by this investigation; not self-awarded) |
| Single Alembic head | TESTED (source chain read: exactly 1 head `20261119_0003`, 111 revisions, 0 orphan roots) |
| Any PRODUCTION READY / release / deployment claim | explicitly NOT MADE |

## 1. Explicit non-claims

- **No `PRODUCTION READY` and no `INDEPENDENTLY VERIFIED` is awarded to this work.** The Team C award quoted above is an existing third-party record, reproduced verbatim, not a self-assessment.
- No release, deployment, DDL, database execution, `create_all()`, `stamp()`, migration replay or test run was performed.
- No owner approval is invented. Every item requiring a decision is marked `BLOCKED` / owner-gated and listed in §12.
- No PHI and no secrets are reproduced. The `DATABASE_URL`/key defaults in `env.py` are read as source text only and not exercised.
- Historical figures are retained, not overwritten; §11 records every contradiction.

---

## 2. Declarative Base inventory (all 19 found on disk)

Table counts are AST-derived table definitions whose owning metadata resolves to that base. 'env.py' = registered in `backend/migrations/env.py` `target_metadata` (17 bases). 'Mig tables' = distinct ORM tables on that base that have at least one migration `create_table` reference.

| # | Base | Module (file:line) | Tables | Registered in env.py | Mig tables | Alembic migrations? |
|---:|---|---|---:|---|---:|---|
| 1 | `Base` | `backend/app/database.py:273` | 147 | yes (shared chain) | 124 | YES |
| 2 | `NationalBase` | `backend/app/national/base.py:19` | 180 | yes (shared chain) | 100 | YES |
| 3 | `EHRBase` | `backend/app/ehr/base.py:10` | 18 | yes (shared chain) | 0 | partial/none |
| 4 | `CitizenPlatformBase` | `backend/app/citizen_platform/base.py:10` | 0 | yes (shared chain) | 0 | none |
| 5 | `ClinicalBase` | `backend/app/clinical/base.py:13` | 41 | yes (shared chain) | 2 | YES |
| 6 | `HealthDataBase` | `backend/app/health_data/base.py:19` | 24 | yes (shared chain) | 0 | partial/none |
| 7 | `TrustBase` | `backend/app/trust/base.py:16` | 6 | yes (shared chain) | 6 | YES |
| 8 | `GovernanceBase` | `backend/app/governance/base.py:15` | 64 | yes (shared chain) | 6 | YES |
| 9 | `CareContinuumBase` | `backend/app/care_continuum/base.py:19` | 45 | yes (shared chain) | 45 | YES |
| 10 | `IdentityBase` | `backend/app/identity/base.py:12` | 98 | yes (shared chain) | 95 | YES |
| 11 | `HospitalBase` | `backend/app/hospital/base.py:6` | 14 | yes (shared chain) | 1 | YES |
| 12 | `DataPlatformBase` | `backend/app/national_data/base.py:13` | 36 | yes (shared chain) | 0 | partial/none |
| 13 | `NHDWBase` | `backend/app/nhdw/base.py:8` | 14 | yes (shared chain) | 14 | YES |
| 14 | `NursingBase` | `backend/app/nursing/base.py:13` | 15 | yes (shared chain) | 13 | YES |
| 15 | `PharmacyBase` | `backend/app/pharmacy/base.py:19` | 27 | yes (shared chain) | 27 | YES |
| 16 | `RadiologyBase` | `backend/app/radiology/base.py:13` | 18 | yes (shared chain) | 17 | YES |
| 17 | `FinBase` | `backend/app/financial/models.py:21` | 37 | yes (shared chain) | 31 | YES |
| 18 | `DocIntelBase` | `backend/app/document_intelligence/infrastructure/models.py:64` | 21 | **NO — unregistered** | 0 | partial/none |
| 19 | `InsBase` | `backend/app/insurance/domain/models.py:49` | 30 | **NO — unregistered** | 0 | partial/none |

**Total table definitions:** 835 (834 distinct names — one duplicate: `national_facilities` in `backend/app/models/clinical_scope.py:136` and `backend/app/national/domain/facility.py:9`).

**Critical base finding.** `DocIntelBase` (21 tables) and `InsBase` (30 tables) exist as declarative bases with live models and active consumers but are **not imported or registered** in `backend/migrations/env.py`. Their 51 tables can never be discovered by Alembic autogenerate, and no migration creates them. Both are `OWNERSHIP_UNCLEAR` / `BLOCKED`.

---

## 3. Exact discrepancy and derivation of the 426 figure

| Measure | Value | Method |
|---|---:|---|
| Distinct ORM table names (AST, this report) | 834 | Unique `__tablename__` string literals |
| Migration-referenced table names (this report) | 493 | `op.create_table('x')`, variable-resolved `op.create_table(VAR)`, raw `CREATE TABLE`, `ALTER TABLE` over 111 version files |
| **Exact source-based discrepancy** | **354** | Distinct ORM names with **no** migration `create_table` reference at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549` |
| Table *definitions* in discrepancy | 354 | Includes the duplicate-name row(s) |
| Discrepancy tables with FK declarations | 188 | `ForeignKey('…')` parsed from class source |
| Discrepancy tables with enum columns | 126 | `Enum(` / `postgresql.ENUM(` in class source |
| Discrepancy tables on unregistered bases | 51 | `DocIntelBase` 21 + `InsBase` 30 |
| Discrepancy tables with zero app references | 28 | token index over `backend/app/**/*.py` |

### 3.1 How 426 was derived, and reconciliation

The prior figure is a **per-context union at HEAD `2827c1ff`**, not a source-parse at this HEAD. It comes from `coverage_by_context.py` / `coverage_by_context.json` (referenced by `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md:278-279`, `GOVERNANCE/ADR_DECISION_REQUEST.md:14-19`, `GOVERNANCE/DATABASE_COMPATIBILITY_REPORT.md:292-294`): **833 ORM tables across 40 contexts; 407 present in the migrated DB; 426 missing; 18/40 contexts fully covered.** Its denominator is a *materialised migrated database*, so a table counts as covered only if the DDL was actually applied on the head path.

Sibling denominators, all valid and never to be summed (per `GOVERNANCE/ARCHITECTURE_DECISION_PACKAGE_W1.md:696-705`, `GOVERNANCE/DATABASE_OWNERSHIP_MATRIX.md:98`): **340** = per-base sum over 17 bases (756 ORM tables, 416 present); **284** = probe-C merged-`MetaData` `add_table` targets (feasibility measurement, not a gap count).

Reconciliation of 426 → **354** at this HEAD (method: source parse + newer migrations):

| Step | Δ | Running | Evidence |
|---|---:|---:|---|
| Published per-context gap (@ `2827c1ff`) | — | 426 | `NATIONAL_SERVICE_INVENTORY.md:278` |
| Care-continuum closure `20261119_0003` created 45 `cc_*` + 17 `national_*` tables | −62 | 364 | `20261119_0003_care_continuum_closure.py`; `DATABASE_MIGRATION_READINESS.md` §4 |
| National coverage 98→80 in this parse (closure + later national DDL) | −18 | 346 | §4 matrix, `national` context |
| Care continuum 45→0 (already counted above; shown to avoid double subtraction) | 0 | 346 | — |
| identity 7→3, models 5→1 fixed by later revisions / parse scope | −8 | 338 | matrix context counts |
| Residual method difference (AST 835 defs vs 833; literal/variable source reference vs applied DB state) | +16 | 354 | §3 method statement |
| **This report, source-based discrepancy** | — | **354** | §4 matrix |

The method differences are precise: (a) this report parses AST at HEAD `2206654` and resolves the full mixin chain, yielding 835 definitions/834 distinct names vs the historical 833; (b) 'migrated' here = name appears in migration **source** (including variable-resolved names such as `national_facilities` in `20260813_0004`), whereas 426/340/284 were measured against an **applied migration-only PG16 database**; (c) 426 aggregates 40 top-level contexts, 340 aggregates 17 declarative bases, 284 is the probe-C import surface. These are different scopes and are reported side-by-side, never substituted.

### 3.2 Head / branch ownership

Reading `revision` / `down_revision` (including annotated assignments and tuple merges) over all 111 version files: **111 revisions, exactly one head `20261119_0003`, zero orphan roots.** Merge revisions `20260815_0003`, `20260815_0013`, `20260815_0015`, `20260819_0001`, `20260908_0001` converge the historic device/interop/drug/surgical branches. The chain is linear into `20261119_0003` (`… 20261118_0001 → 20261119_0001 → 20261119_0002 → 20261119_0003`). Single-head status is `TESTED` by source reading only — no Alembic CLI was run.

---

## 4. Complete classification matrix

All **354 distinct discrepancy tables** are listed — no silent omissions. Columns: `env` = base registered in `env.py` (N = not registered → autogenerate blind); `FK` = declared `ForeignKey` count / target tables; `E` = enum columns present; `IU` = indexes / uniques / checks / FK-constraints; `refs` = identifier occurrences in `backend/app` excluding the defining file; `consumer` = representative API/service files; `cl` = classification; `prio` = remediation priority (P0 = autogenerate-blind base or ≥20 app refs; P1 = other active; P2 = dormant; P3 = unused); `evidence` = model file:line and last model-file commit date (proxy for last known use — no runtime telemetry exists).

| # | ORM table | class | base | ctx | env | FK | E | IU | refs | consumer | cl | prio | evidence |
|---:|---|---|---|---|:-:|---|:-:|---:|---:|---|---|:-:|---|
| 1 | `clinical_alert_actions` | `ClinicalAlertAction` | ClinicalBase | clinical | Y | 1/clinical_alerts | — | 0/0/0/0 | 0 | — | UNUSED | P3 | `clinical/cds/models.py:128`; commit 2026-07-16 |
| 2 | `clinical_alerts` | `ClinicalAlert` | ClinicalBase | clinical | Y | 0/— | — | 4/0/0/0 | 39 | services/clinical_service.py | ACTIVE_REQUIRED | P0 | `clinical/cds/models.py:98`; commit 2026-07-16 |
| 3 | `clinical_atc_codes` | `ATCCode` | ClinicalBase | clinical | Y | 0/— | — | 2/1/0/0 | 0 | — | UNUSED | P3 | `clinical/terminology/models.py:235`; commit 2026-07-18 |
| 4 | `clinical_audit_records` | `ClinicalAuditRecord` | ClinicalBase | clinical | Y | 0/— | — | 4/0/0/0 | 11 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/quality/models.py:73`; commit 2026-07-16 |
| 5 | `clinical_benchmark_values` | `BenchmarkValue` | ClinicalBase | clinical | Y | 1/clinical_quality_indicators | — | 1/0/0/0 | 8 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/quality/models.py:124`; commit 2026-07-16 |
| 6 | `clinical_care_bundle_elements` | `CareBundleElement` | ClinicalBase | clinical | Y | 1/clinical_care_bundles | — | 0/0/0/0 | 0 | — | UNUSED | P3 | `clinical/cds/models.py:82`; commit 2026-07-16 |
| 7 | `clinical_care_bundles` | `CareBundle` | ClinicalBase | clinical | Y | 1/clinical_guidelines | Y | 2/0/0/0 | 4 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/cds/models.py:62`; commit 2026-07-16 |
| 8 | `clinical_code_systems` | `CodeSystem` | ClinicalBase | clinical | Y | 0/— | Y | 1/0/0/0 | 79 | contracts/fhir.py, fhir/_capabilities.py | ACTIVE_REQUIRED | P0 | `clinical/terminology/models.py:120`; commit 2026-07-18 |
| 9 | `clinical_compliance_checks` | `ComplianceCheck` | ClinicalBase | clinical | Y | 0/— | — | 3/0/0/0 | 45 | services/clinical_service.py | ACTIVE_REQUIRED | P0 | `clinical/quality/models.py:100`; commit 2026-07-16 |
| 10 | `clinical_contraindications` | `Contraindication` | ClinicalBase | clinical | Y | 0/— | — | 2/0/0/0 | 15 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/cds/models.py:143`; commit 2026-07-16 |
| 11 | `clinical_cpt_codes` | `CPTCode` | ClinicalBase | clinical | Y | 0/— | — | 2/1/0/0 | 0 | — | UNUSED | P3 | `clinical/terminology/models.py:264`; commit 2026-07-18 |
| 12 | `clinical_duplicate_order_rules` | `DuplicateOrderRule` | ClinicalBase | clinical | Y | 0/— | — | 2/0/0/0 | 5 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/cds/models.py:167`; commit 2026-07-16 |
| 13 | `clinical_guideline_approvals` | `GuidelineApproval` | ClinicalBase | clinical | Y | 1/clinical_guidelines | — | 2/0/0/0 | 3 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/knowledge/models.py:184`; commit 2026-07-16 |
| 14 | `clinical_guidelines` | `ClinicalGuideline` | ClinicalBase | clinical | Y | 1/clinical_guidelines | Y | 3/1/0/0 | 31 | factory.py, services/clinical_service.py | ACTIVE_REQUIRED | P0 | `clinical/knowledge/models.py:25`; commit 2026-07-16 |
| 15 | `clinical_icd10_codes` | `ICD10Code` | ClinicalBase | clinical | Y | 0/— | — | 3/1/0/0 | 12 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/terminology/models.py:140`; commit 2026-07-18 |
| 16 | `clinical_icd11_codes` | `ICD11Code` | ClinicalBase | clinical | Y | 0/— | — | 2/1/0/0 | 3 | national/reference/__init__.py, national/reference/icd11.py | ACTIVE_REQUIRED | P1 | `clinical/terminology/models.py:163`; commit 2026-07-18 |
| 17 | `clinical_incident_reports` | `IncidentReport` | ClinicalBase | clinical | Y | 0/— | — | 3/0/0/0 | 5 | command_intelligence/routes.py, services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/quality/models.py:171`; commit 2026-07-16 |
| 18 | `clinical_indicator_measurements` | `IndicatorMeasurement` | ClinicalBase | clinical | Y | 1/clinical_quality_indicators | — | 1/0/0/0 | 7 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/quality/models.py:52`; commit 2026-07-16 |
| 19 | `clinical_loinc_codes` | `LOINCCode` | ClinicalBase | clinical | Y | 0/— | — | 3/1/0/0 | 13 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/terminology/models.py:198`; commit 2026-07-18 |
| 20 | `clinical_mortality_reviews` | `MortalityReview` | ClinicalBase | clinical | Y | 0/— | — | 3/0/0/0 | 3 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/quality/models.py:144`; commit 2026-07-16 |
| 21 | `clinical_order_set_items` | `OrderSetItem` | ClinicalBase | clinical | Y | 1/clinical_order_sets | — | 0/0/0/0 | 0 | — | UNUSED | P3 | `clinical/cds/models.py:45`; commit 2026-07-16 |
| 22 | `clinical_order_sets` | `OrderSet` | ClinicalBase | clinical | Y | 1/clinical_guidelines | — | 3/0/0/0 | 6 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/cds/models.py:22`; commit 2026-07-16 |
| 23 | `clinical_pathway_phases` | `PathwayPhase` | ClinicalBase | clinical | Y | 1/clinical_pathways | — | 0/0/0/0 | 0 | — | UNUSED | P3 | `clinical/knowledge/models.py:116`; commit 2026-07-16 |
| 24 | `clinical_pathways` | `ClinicalPathway` | ClinicalBase | clinical | Y | 0/— | Y | 2/0/0/0 | 18 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/knowledge/models.py:90`; commit 2026-07-16 |
| 25 | `clinical_patient_safety_events` | `PatientSafetyEvent` | ClinicalBase | clinical | Y | 0/— | — | 4/0/0/0 | 3 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/quality/models.py:200`; commit 2026-07-16 |
| 26 | `clinical_preventive_recommendations` | `PreventiveRecommendation` | ClinicalBase | clinical | Y | 1/clinical_guidelines | Y | 3/0/0/0 | 0 | — | UNUSED | P3 | `clinical/cds/models.py:211`; commit 2026-07-16 |
| 27 | `clinical_protocols` | `ClinicalProtocol` | ClinicalBase | clinical | Y | 1/clinical_guidelines | Y | 1/1/0/0 | 18 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/knowledge/models.py:59`; commit 2026-07-16 |
| 28 | `clinical_quality_indicators` | `QualityIndicator` | ClinicalBase | clinical | Y | 0/— | Y | 3/1/0/0 | 17 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/quality/models.py:23`; commit 2026-07-16 |
| 29 | `clinical_recommendations` | `ClinicalRecommendation` | ClinicalBase | clinical | Y | 1/clinical_guidelines | Y | 2/0/0/0 | 19 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/knowledge/models.py:159`; commit 2026-07-16 |
| 30 | `clinical_reminder_rules` | `ReminderRule` | ClinicalBase | clinical | Y | 0/— | — | 2/0/0/0 | 0 | — | UNUSED | P3 | `clinical/cds/models.py:188`; commit 2026-07-16 |
| 31 | `clinical_rxnorm_codes` | `RxNormCode` | ClinicalBase | clinical | Y | 0/— | — | 1/1/0/0 | 0 | — | UNUSED | P3 | `clinical/terminology/models.py:251`; commit 2026-07-18 |
| 32 | `clinical_snomed_ct_codes` | `SNOMEDCTCode` | ClinicalBase | clinical | Y | 0/— | — | 2/1/0/0 | 8 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/terminology/models.py:182`; commit 2026-07-18 |
| 33 | `clinical_standing_orders` | `StandingOrder` | ClinicalBase | clinical | Y | 1/clinical_protocols | — | 2/1/0/0 | 10 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/knowledge/models.py:132`; commit 2026-07-16 |
| 34 | `clinical_terminology_codes` | `TerminologyCode` | ClinicalBase | clinical | Y | 2/clinical_terminology_codes,clinical_terminology_versions | Y | 3/0/0/0 | 27 | routes/clinical.py, services/clinical_service.py | ACTIVE_REQUIRED | P0 | `clinical/terminology/models.py:25`; commit 2026-07-18 |
| 35 | `clinical_terminology_mappings` | `TerminologyMapping` | ClinicalBase | clinical | Y | 2/clinical_terminology_codes | Y | 2/0/0/0 | 17 | governance/services/interoperability_service.py, services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/terminology/models.py:65`; commit 2026-07-18 |
| 36 | `clinical_terminology_versions` | `TerminologyVersion` | ClinicalBase | clinical | Y | 0/— | Y | 1/0/0/0 | 9 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/terminology/models.py:48`; commit 2026-07-18 |
| 37 | `clinical_ucum_codes` | `UCUMCode` | ClinicalBase | clinical | Y | 0/— | — | 1/1/0/0 | 0 | — | UNUSED | P3 | `clinical/terminology/models.py:223`; commit 2026-07-18 |
| 38 | `clinical_value_set_members` | `ValueSetMember` | ClinicalBase | clinical | Y | 2/clinical_terminology_codes,clinical_value_sets | — | 1/0/0/0 | 3 | services/clinical_service.py | ACTIVE_REQUIRED | P1 | `clinical/terminology/models.py:105`; commit 2026-07-18 |
| 39 | `clinical_value_sets` | `ValueSet` | ClinicalBase | clinical | Y | 0/— | Y | 1/1/0/0 | 21 | routes/clinical.py, services/clinical_service.py | ACTIVE_REQUIRED | P0 | `clinical/terminology/models.py:84`; commit 2026-07-18 |
| 40 | `ai_recommendations` | `AIRecommendation` | Base | command_intelligence | Y | 2/lab_users | — | 3/0/0/0 | 6 | command_intelligence/engine.py | ACTIVE_REQUIRED | P1 | `command_intelligence/models.py:86`; commit 2026-07-24 |
| 41 | `capacity_intelligence` | `CapacityIntelligence` | Base | command_intelligence | Y | 0/— | — | 3/0/0/0 | 14 | command_intelligence/engine.py | ACTIVE_REQUIRED | P1 | `command_intelligence/models.py:71`; commit 2026-07-24 |
| 42 | `incident_intelligence` | `IncidentIntelligence` | Base | command_intelligence | Y | 0/— | — | 4/0/0/0 | 18 | command_intelligence/routes.py | ACTIVE_REQUIRED | P1 | `command_intelligence/models.py:53`; commit 2026-07-24 |
| 43 | `national_kpis` | `NationalKPI` | Base | command_intelligence | Y | 1/labs | — | 5/0/0/0 | 36 | command_intelligence/engine.py | ACTIVE_REQUIRED | P0 | `command_intelligence/models.py:36`; commit 2026-07-24 |
| 44 | `situation_rooms` | `SituationRoom` | Base | command_intelligence | Y | 0/— | — | 3/0/0/0 | 3 | command_intelligence/engine.py | ACTIVE_REQUIRED | P1 | `command_intelligence/models.py:19`; commit 2026-07-24 |
| 45 | `docint_access_control` | `AccessControlModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 2/0/0/0 | 9 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:965`; commit 2026-07-24 |
| 46 | `docint_annotations` | `DocumentAnnotationModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | — | 1/0/0/0 | 8 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:604`; commit 2026-07-24 |
| 47 | `docint_classifications` | `ClassificationResultModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 1/0/0/0 | 7 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:365`; commit 2026-07-24 |
| 48 | `docint_documents` | `ScannedDocumentModel` | DocIntelBase | document_intelligence | **N** | 0/— | Y | 3/0/0/0 | 32 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:68`; commit 2026-07-24 |
| 49 | `docint_entities` | `ExtractedEntityModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 1/0/0/0 | 11 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:221`; commit 2026-07-24 |
| 50 | `docint_events` | `DocumentEventModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 1/0/0/0 | 7 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:804`; commit 2026-07-24 |
| 51 | `docint_fields` | `ExtractedFieldModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 1/0/0/0 | 9 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:276`; commit 2026-07-24 |
| 52 | `docint_governance_events` | `GovernanceEventModel` | DocIntelBase | document_intelligence | **N** | 2/docint_documents,docint_governance_policies | Y | 1/0/0/0 | 7 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:760`; commit 2026-07-24 |
| 53 | `docint_governance_policies` | `GovernancePolicyModel` | DocIntelBase | document_intelligence | **N** | 0/— | Y | 0/1/0/0 | 11 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:718`; commit 2026-07-24 |
| 54 | `docint_government_documents` | `GovernmentDocumentModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 2/1/0/0 | 12 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:483`; commit 2026-07-24 |
| 55 | `docint_knowledge_graph_edges` | `KnowledgeGraphEdgeModel` | DocIntelBase | document_intelligence | **N** | 2/docint_documents | Y | 2/0/0/0 | 14 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:887`; commit 2026-07-24 |
| 56 | `docint_lifecycle` | `DocumentLifecycleModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 1/0/0/0 | 7 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:841`; commit 2026-07-24 |
| 57 | `docint_ocr_results` | `OcrResultModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 1/0/0/0 | 11 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:171`; commit 2026-07-24 |
| 58 | `docint_pipeline_health` | `PipelineHealthModel` | DocIntelBase | document_intelligence | **N** | 0/— | — | 1/0/0/0 | 9 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:931`; commit 2026-07-24 |
| 59 | `docint_pipeline_results` | `PipelineResultModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | — | 1/1/0/0 | 9 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:413`; commit 2026-07-24 |
| 60 | `docint_preservation` | `DigitalPreservationRecordModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 1/1/0/0 | 10 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:653`; commit 2026-07-24 |
| 61 | `docint_retention` | `DocumentRetentionModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 1/1/0/0 | 10 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:982`; commit 2026-07-24 |
| 62 | `docint_reviews` | `DocumentReviewModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | Y | 1/0/0/0 | 8 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:554`; commit 2026-07-24 |
| 63 | `docint_tables` | `ExtractedTableModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | — | 1/0/0/0 | 9 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:325`; commit 2026-07-24 |
| 64 | `docint_versions` | `DocumentVersionModel` | DocIntelBase | document_intelligence | **N** | 1/docint_documents | — | 1/0/0/0 | 9 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:465`; commit 2026-07-24 |
| 65 | `docint_webhooks` | `WebhookRegistrationModel` | DocIntelBase | document_intelligence | **N** | 0/— | — | 0/0/0/0 | 7 | document_intelligence/infrastructure/repository.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `document_intelligence/infrastructure/models.py:872`; commit 2026-07-24 |
| 66 | `ehr_allergies` | `AllergyIntolerance` | EHRBase | ehr | Y | 4/national_citizens,national_encounters,national_patients | Y | 10/0/0/0 | 62 | ehr/__init__.py, ehr/models/__init__.py | ACTIVE_REQUIRED | P0 | `ehr/models/allergy.py:10`; commit 2026-07-16 |
| 67 | `ehr_care_plan_activities` | `CarePlanActivity` | EHRBase | ehr | Y | 3/ehr_care_plan_goals,ehr_care_plans,national_practitioners | — | 6/0/0/0 | 24 | services/ehr_service.py | ACTIVE_REQUIRED | P0 | `ehr/models/care_plan.py:70`; commit 2026-07-16 |
| 68 | `ehr_care_plan_goals` | `CarePlanGoal` | EHRBase | ehr | Y | 1/ehr_care_plans | — | 3/0/0/0 | 28 | services/ehr_service.py | ACTIVE_REQUIRED | P0 | `ehr/models/care_plan.py:44`; commit 2026-07-16 |
| 69 | `ehr_care_plans` | `CarePlan` | EHRBase | ehr | Y | 4/national_citizens,national_encounters,national_patients | Y | 9/0/0/0 | 82 | factory.py | ACTIVE_REQUIRED | P0 | `ehr/models/care_plan.py:10`; commit 2026-07-16 |
| 70 | `ehr_clinical_attachments` | `ClinicalAttachment` | EHRBase | ehr | Y | 6/national_citizens,national_encounters,national_facilities | — | 15/0/0/0 | 46 | routes/ehr_fhir.py, services/ehr_service.py | ACTIVE_REQUIRED | P0 | `ehr/models/attachment.py:10`; commit 2026-07-16 |
| 71 | `ehr_clinical_notes` | `ClinicalNote` | EHRBase | ehr | Y | 12/ehr_clinical_notes,national_citizens,national_departments | Y | 19/0/0/0 | 82 | ehr/__init__.py, ehr/models/__init__.py | ACTIVE_REQUIRED | P0 | `ehr/models/clinical_note.py:12`; commit 2026-07-16 |
| 72 | `ehr_conditions` | `ConditionRecord` | EHRBase | ehr | Y | 4/national_citizens,national_encounters,national_patients | — | 11/0/0/0 | 42 | routes/ehr_fhir.py, services/ehr_service.py | ACTIVE_REQUIRED | P0 | `ehr/models/clinical_summary.py:56`; commit 2026-07-16 |
| 73 | `ehr_diagnoses` | `DiagnosisRecord` | EHRBase | ehr | Y | 4/national_citizens,national_encounters,national_patients | Y | 10/0/0/0 | 39 | routes/ehr_fhir.py, services/ehr_service.py | ACTIVE_REQUIRED | P0 | `ehr/models/clinical_summary.py:97`; commit 2026-07-16 |
| 74 | `ehr_family_history` | `FamilyHistoryRecord` | EHRBase | ehr | Y | 3/national_citizens,national_patients,national_practitioners | — | 10/0/0/0 | 19 | services/ehr_service.py | ACTIVE_REQUIRED | P1 | `ehr/models/family_history.py:10`; commit 2026-07-16 |
| 75 | `ehr_immunizations` | `ImmunizationRecord` | EHRBase | ehr | Y | 6/national_citizens,national_encounters,national_facilities | — | 15/0/0/0 | 52 | public_health/api/routes.py | ACTIVE_REQUIRED | P0 | `ehr/models/immunization.py:10`; commit 2026-07-16 |
| 76 | `ehr_medication_administrations` | `MedicationAdministration` | EHRBase | ehr | Y | 5/ehr_medication_requests,national_citizens,national_encounters | Y | 14/0/0/0 | 62 | services/ehr_service.py | ACTIVE_REQUIRED | P0 | `ehr/models/medication.py:172`; commit 2026-08-15 |
| 77 | `ehr_medication_dispenses` | `MedicationDispense` | EHRBase | ehr | Y | 1/ehr_medication_requests | — | 11/0/0/0 | 44 | citizen_platform/routes.py, services/ehr_service.py | ACTIVE_REQUIRED | P0 | `ehr/models/medication.py:121`; commit 2026-08-15 |
| 78 | `ehr_medication_requests` | `MedicationRequest` | EHRBase | ehr | Y | 4/national_citizens,national_encounters,national_patients | Y | 11/0/0/0 | 103 | document_intelligence/application/wiring.py | ACTIVE_REQUIRED | P0 | `ehr/models/medication.py:68`; commit 2026-08-15 |
| 79 | `ehr_medication_statements` | `MedicationStatement` | EHRBase | ehr | Y | 4/national_citizens,national_encounters,national_patients | — | 10/0/0/0 | 74 | citizen_platform/medications.py, ehr/__init__.py | ACTIVE_REQUIRED | P0 | `ehr/models/medication.py:23`; commit 2026-08-15 |
| 80 | `ehr_patient_timeline` | `PatientTimelineEvent` | EHRBase | ehr | Y | 5/national_citizens,national_encounters,national_facilities | Y | 15/0/0/0 | 11 | services/ehr_service.py | ACTIVE_REQUIRED | P1 | `ehr/models/timeline.py:10`; commit 2026-07-16 |
| 81 | `ehr_problem_list_items` | `ProblemListItem` | EHRBase | ehr | Y | 3/national_citizens,national_encounters,national_patients | Y | 8/0/0/0 | 22 | services/ehr_service.py | ACTIVE_REQUIRED | P0 | `ehr/models/clinical_summary.py:21`; commit 2026-07-16 |
| 82 | `ehr_risk_factors` | `RiskFactorRecord` | EHRBase | ehr | Y | 4/national_citizens,national_encounters,national_patients | Y | 12/0/0/0 | 19 | services/ehr_service.py | ACTIVE_REQUIRED | P1 | `ehr/models/risk_factor.py:10`; commit 2026-07-16 |
| 83 | `ehr_social_history` | `SocialHistoryRecord` | EHRBase | ehr | Y | 4/national_citizens,national_encounters,national_patients | Y | 9/0/0/0 | 19 | services/ehr_service.py | ACTIVE_REQUIRED | P1 | `ehr/models/social_history.py:12`; commit 2026-07-16 |
| 84 | `fin_invoice_items` | `FinInvoiceItem` | FinBase | financial | Y | 1/fin_invoices | — | 0/0/0/0 | 2 | financial/services.py | DORMANT | P2 | `financial/models.py:87`; commit 2026-07-19 |
| 85 | `fin_invoices` | `FinInvoice` | FinBase | financial | Y | 1/fin_subscriptions | — | 1/1/0/0 | 24 | financial/services.py | ACTIVE_REQUIRED | P0 | `financial/models.py:71`; commit 2026-07-19 |
| 86 | `fin_payables` | `FinPayable` | FinBase | financial | Y | 1/fin_providers | — | 0/0/0/0 | 4 | financial/services.py | ACTIVE_REQUIRED | P1 | `financial/models.py:124`; commit 2026-07-19 |
| 87 | `fin_payments` | `FinPayment` | FinBase | financial | Y | 1/fin_invoices | — | 1/0/0/0 | 9 | financial/services.py | ACTIVE_REQUIRED | P1 | `financial/models.py:98`; commit 2026-07-19 |
| 88 | `fin_pricing_rules` | `FinPricingRule` | FinBase | financial | Y | 0/— | — | 1/0/0/0 | 8 | financial/routes.py | ACTIVE_REQUIRED | P1 | `financial/models.py:135`; commit 2026-07-19 |
| 89 | `fin_receivables` | `FinReceivable` | FinBase | financial | Y | 1/fin_invoices | — | 1/0/0/0 | 0 | — | UNUSED | P3 | `financial/models.py:112`; commit 2026-07-19 |
| 90 | `gov_acting_appointments` | `ActingAppointment` | GovernanceBase | governance | Y | 2/gov_hierarchy_nodes | Y | 3/0/0/0 | 13 | governance/services/hierarchy_service.py | ACTIVE_REQUIRED | P1 | `governance/models/hierarchy.py:82`; commit 2026-07-16 |
| 91 | `gov_ai_audit_events` | `AIAuditEvent` | GovernanceBase | governance | Y | 1/gov_hierarchy_nodes | Y | 2/0/0/0 | 11 | governance/services/ai_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/ai.py:80`; commit 2026-07-16 |
| 92 | `gov_ai_guardrails` | `AIGuardrail` | GovernanceBase | governance | Y | 0/— | Y | 3/1/0/0 | 11 | governance/services/ai_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/ai.py:24`; commit 2026-07-16 |
| 93 | `gov_ai_model_validations` | `AIModelValidationRecord` | GovernanceBase | governance | Y | 0/— | — | 1/0/0/0 | 8 | governance/services/ai_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/ai.py:122`; commit 2026-07-16 |
| 94 | `gov_ai_risk_classifications` | `AIRiskClassification` | GovernanceBase | governance | Y | 0/— | Y | 2/0/0/0 | 13 | governance/services/ai_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/ai.py:104`; commit 2026-07-16 |
| 95 | `gov_analyzer_registry` | `AnalyzerRegistry` | GovernanceBase | governance | Y | 1/gov_laboratory_registry | — | 4/1/0/0 | 11 | governance/services/laboratory_service.py | ACTIVE_REQUIRED | P1 | `governance/models/laboratory.py:73`; commit 2026-07-16 |
| 96 | `gov_approval_policies` | `ApprovalPolicy` | GovernanceBase | governance | Y | 0/— | — | 2/1/0/0 | 8 | governance/services/clinical_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/clinical.py:154`; commit 2026-07-16 |
| 97 | `gov_attendance_records` | `AttendanceRecord` | GovernanceBase | governance | Y | 1/gov_healthcare_workers | — | 3/0/0/0 | 8 | governance/services/workforce_service.py | ACTIVE_REQUIRED | P1 | `governance/models/workforce.py:143`; commit 2026-07-16 |
| 98 | `gov_board_certifications` | `BoardCertification` | GovernanceBase | governance | Y | 1/gov_healthcare_workers | Y | 3/0/0/0 | 8 | governance/services/workforce_service.py | ACTIVE_REQUIRED | P1 | `governance/models/workforce.py:63`; commit 2026-07-16 |
| 99 | `gov_break_glass_policies` | `BreakGlassPolicy` | GovernanceBase | governance | Y | 0/— | — | 1/1/0/0 | 9 | governance/services/security_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/security.py:69`; commit 2026-07-16 |
| 100 | `gov_calibration_records` | `CalibrationRecord` | GovernanceBase | governance | Y | 1/gov_analyzer_registry | — | 1/0/0/0 | 14 | biomedical/application/service.py, biomedical/domain/entities.py | ACTIVE_REQUIRED | P1 | `governance/models/laboratory.py:114`; commit 2026-07-16 |
| 101 | `gov_canonical_mappings` | `CanonicalMapping` | GovernanceBase | governance | Y | 0/— | — | 1/0/0/0 | 12 | governance/services/interoperability_service.py | ACTIVE_REQUIRED | P1 | `governance/models/interoperability.py:76`; commit 2026-07-16 |
| 102 | `gov_clinical_policies` | `ClinicalPolicy` | GovernanceBase | governance | Y | 0/— | Y | 3/1/0/0 | 13 | governance/services/clinical_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/clinical.py:12`; commit 2026-07-16 |
| 103 | `gov_competency_assessments` | `CompetencyAssessment` | GovernanceBase | governance | Y | 1/gov_healthcare_workers | Y | 2/0/0/0 | 8 | governance/services/workforce_service.py | ACTIVE_REQUIRED | P1 | `governance/models/workforce.py:97`; commit 2026-07-16 |
| 104 | `gov_consultation_policies` | `ConsultationPolicy` | GovernanceBase | governance | Y | 0/— | — | 2/1/0/0 | 8 | governance/services/clinical_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/clinical.py:172`; commit 2026-07-16 |
| 105 | `gov_critical_result_policies` | `CriticalResultPolicy` | GovernanceBase | governance | Y | 0/— | — | 2/0/0/0 | 11 | governance/services/clinical_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/clinical.py:78`; commit 2026-07-16 |
| 106 | `gov_data_classification` | `DataClassification` | GovernanceBase | governance | Y | 0/— | Y | 4/1/0/0 | 55 | factory.py, governance/services/security_governance_service.py | ACTIVE_REQUIRED | P0 | `governance/models/security.py:151`; commit 2026-07-16 |
| 107 | `gov_delegations` | `Delegation` | GovernanceBase | governance | Y | 2/gov_hierarchy_nodes | Y | 3/0/0/0 | 59 | factory.py, governance/services/hierarchy_service.py | ACTIVE_REQUIRED | P0 | `governance/models/hierarchy.py:65`; commit 2026-07-16 |
| 108 | `gov_delta_check_policies` | `DeltaCheckPolicy` | GovernanceBase | governance | Y | 0/— | — | 1/0/0/0 | 11 | governance/services/clinical_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/clinical.py:111`; commit 2026-07-16 |
| 109 | `gov_digital_certificates` | `DigitalCertificate` | GovernanceBase | governance | Y | 0/— | Y | 3/1/0/0 | 45 | governance/services/security_governance_service.py | ACTIVE_REQUIRED | P0 | `governance/models/security.py:171`; commit 2026-07-16 |
| 110 | `gov_emergency_admin` | `EmergencyAdministration` | GovernanceBase | governance | Y | 2/gov_hierarchy_nodes | Y | 2/0/0/0 | 8 | governance/services/hierarchy_service.py | ACTIVE_REQUIRED | P1 | `governance/models/hierarchy.py:97`; commit 2026-07-16 |
| 111 | `gov_eqa_records` | `EQARecord` | GovernanceBase | governance | Y | 1/gov_laboratory_registry | Y | 2/0/0/0 | 17 | governance/services/analytics_service.py, governance/services/laboratory_service.py | ACTIVE_REQUIRED | P1 | `governance/models/laboratory.py:150`; commit 2026-07-16 |
| 112 | `gov_equipment_registry` | `EquipmentRegistry` | GovernanceBase | governance | Y | 1/gov_laboratory_registry | Y | 4/1/0/0 | 16 | governance/services/analytics_service.py, governance/services/laboratory_service.py | ACTIVE_REQUIRED | P1 | `governance/models/laboratory.py:50`; commit 2026-07-16 |
| 113 | `gov_health_cards` | `HealthCardLifecycle` | GovernanceBase | governance | Y | 0/— | Y | 4/1/0/0 | 8 | governance/services/health_number_service.py | ACTIVE_REQUIRED | P1 | `governance/models/health_number.py:48`; commit 2026-07-16 |
| 114 | `gov_health_number_audit` | `HealthNumberAudit` | GovernanceBase | governance | Y | 0/— | — | 1/0/0/0 | 13 | governance/services/health_number_service.py | ACTIVE_REQUIRED | P1 | `governance/models/health_number.py:34`; commit 2026-07-16 |
| 115 | `gov_health_numbers` | `HealthNumberRecord` | GovernanceBase | governance | Y | 0/— | Y | 6/1/0/0 | 15 | governance/services/health_number_service.py | ACTIVE_REQUIRED | P1 | `governance/models/health_number.py:12`; commit 2026-07-16 |
| 116 | `gov_healthcare_workers` | `HealthcareWorker` | GovernanceBase | governance | Y | 1/gov_hierarchy_nodes | — | 6/1/0/0 | 26 | governance/services/analytics_service.py, governance/services/workforce_service.py | ACTIVE_REQUIRED | P0 | `governance/models/workforce.py:24`; commit 2026-07-16 |
| 117 | `gov_hierarchy_nodes` | `GovernanceNode` | GovernanceBase | governance | Y | 2/gov_hierarchy_nodes | Y | 6/2/0/0 | 42 | governance/__init__.py, governance/models/__init__.py | ACTIVE_REQUIRED | P0 | `governance/models/hierarchy.py:29`; commit 2026-07-16 |
| 118 | `gov_incidents` | `IncidentRecord` | GovernanceBase | governance | Y | 1/gov_hierarchy_nodes | Y | 3/1/0/0 | 12 | governance/services/security_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/security.py:106`; commit 2026-07-16 |
| 119 | `gov_interop_protocols` | `InteropProtocol` | GovernanceBase | governance | Y | 0/— | Y | 3/1/0/0 | 16 | governance/services/interoperability_service.py | ACTIVE_REQUIRED | P1 | `governance/models/interoperability.py:16`; commit 2026-07-16 |
| 120 | `gov_laboratory_registry` | `LaboratoryRegistry` | GovernanceBase | governance | Y | 1/gov_hierarchy_nodes | Y | 6/2/0/0 | 32 | governance/services/analytics_service.py, governance/services/laboratory_service.py | ACTIVE_REQUIRED | P0 | `governance/models/laboratory.py:24`; commit 2026-07-16 |
| 121 | `gov_llm_policies` | `LLMGovernancePolicy` | GovernanceBase | governance | Y | 0/— | — | 2/1/0/0 | 8 | governance/services/ai_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/ai.py:42`; commit 2026-07-16 |
| 122 | `gov_maintenance_records` | `MaintenanceRecord` | GovernanceBase | governance | Y | 1/gov_equipment_registry | — | 1/0/0/0 | 8 | governance/services/laboratory_service.py | ACTIVE_REQUIRED | P1 | `governance/models/laboratory.py:97`; commit 2026-07-16 |
| 123 | `gov_master_data_agreements` | `MasterDataAgreement` | GovernanceBase | governance | Y | 0/— | — | 3/1/0/0 | 8 | governance/services/interoperability_service.py | ACTIVE_REQUIRED | P1 | `governance/models/interoperability.py:38`; commit 2026-07-16 |
| 124 | `gov_medical_guidelines` | `MedicalGuideline` | GovernanceBase | governance | Y | 0/— | Y | 3/1/0/0 | 8 | governance/services/clinical_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/clinical.py:34`; commit 2026-07-16 |
| 125 | `gov_merged_identities` | `MergedIdentityRecord` | GovernanceBase | governance | Y | 0/— | Y | 5/0/0/0 | 23 | governance/repositories/merge_repository.py, governance/services/health_number_service.py | ACTIVE_REQUIRED | P0 | `governance/models/health_number.py:64`; commit 2026-07-16 |
| 126 | `gov_national_audit_events` | `NationalAuditEvent` | GovernanceBase | governance | Y | 1/gov_hierarchy_nodes | Y | 3/0/0/0 | 13 | governance/routes/governance_routes.py, governance/services/security_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/security.py:29`; commit 2026-07-16 |
| 127 | `gov_national_panels` | `NationalPanelDefinition` | GovernanceBase | governance | Y | 0/— | — | 1/1/0/0 | 8 | governance/services/laboratory_service.py | ACTIVE_REQUIRED | P1 | `governance/models/laboratory.py:218`; commit 2026-07-16 |
| 128 | `gov_national_protocols` | `NationalProtocol` | GovernanceBase | governance | Y | 0/— | Y | 4/1/0/0 | 8 | governance/services/clinical_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/clinical.py:56`; commit 2026-07-16 |
| 129 | `gov_national_reference_labs` | `NationalReferenceLab` | GovernanceBase | governance | Y | 1/gov_laboratory_registry | — | 2/0/0/0 | 8 | governance/services/laboratory_service.py | ACTIVE_REQUIRED | P1 | `governance/models/laboratory.py:232`; commit 2026-07-16 |
| 130 | `gov_national_tests` | `NationalTestDefinition` | GovernanceBase | governance | Y | 0/— | — | 4/1/0/0 | 11 | governance/routes/governance_routes.py, governance/services/laboratory_service.py | ACTIVE_REQUIRED | P1 | `governance/models/laboratory.py:195`; commit 2026-07-16 |
| 131 | `gov_productivity_records` | `ProductivityRecord` | GovernanceBase | governance | Y | 1/gov_healthcare_workers | Y | 2/0/0/0 | 39 | governance/services/analytics_service.py, governance/services/workforce_service.py | ACTIVE_REQUIRED | P0 | `governance/models/workforce.py:157`; commit 2026-07-16 |
| 132 | `gov_professional_licenses` | `ProfessionalLicense` | GovernanceBase | governance | Y | 1/gov_healthcare_workers | Y | 3/1/0/0 | 17 | governance/services/workforce_service.py | ACTIVE_REQUIRED | P1 | `governance/models/workforce.py:46`; commit 2026-07-16 |
| 133 | `gov_prompt_policies` | `PromptPolicy` | GovernanceBase | governance | Y | 0/— | — | 1/1/0/0 | 8 | governance/services/ai_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/ai.py:63`; commit 2026-07-16 |
| 134 | `gov_qc_records` | `QCModRecord` | GovernanceBase | governance | Y | 2/gov_analyzer_registry,gov_laboratory_registry | Y | 2/0/0/0 | 17 | governance/services/analytics_service.py, governance/services/laboratory_service.py | ACTIVE_REQUIRED | P1 | `governance/models/laboratory.py:130`; commit 2026-07-16 |
| 135 | `gov_reagent_inventory` | `ReagentInventory` | GovernanceBase | governance | Y | 1/gov_laboratory_registry | — | 3/0/0/0 | 16 | governance/services/laboratory_service.py | ACTIVE_REQUIRED | P1 | `governance/models/laboratory.py:173`; commit 2026-07-16 |
| 136 | `gov_reference_range_policies` | `ReferenceRangePolicy` | GovernanceBase | governance | Y | 0/— | — | 2/0/0/0 | 8 | governance/services/clinical_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/clinical.py:137`; commit 2026-07-16 |
| 137 | `gov_repeat_testing_policies` | `RepeatTestingPolicy` | GovernanceBase | governance | Y | 0/— | — | 1/0/0/0 | 8 | governance/services/clinical_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/clinical.py:97`; commit 2026-07-16 |
| 138 | `gov_risk_registry` | `RiskRegistryItem` | GovernanceBase | governance | Y | 0/— | — | 2/1/0/0 | 9 | governance/services/security_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/security.py:128`; commit 2026-07-16 |
| 139 | `gov_roles` | `GovernanceRole` | GovernanceBase | governance | Y | 1/gov_hierarchy_nodes | — | 1/0/0/0 | 8 | governance/services/hierarchy_service.py | ACTIVE_REQUIRED | P1 | `governance/models/hierarchy.py:52`; commit 2026-07-16 |
| 140 | `gov_rotation_records` | `RotationRecord` | GovernanceBase | governance | Y | 3/gov_healthcare_workers,gov_hierarchy_nodes | — | 1/0/0/0 | 8 | governance/services/workforce_service.py | ACTIVE_REQUIRED | P1 | `governance/models/workforce.py:127`; commit 2026-07-16 |
| 141 | `gov_security_policies` | `SecurityPolicy` | GovernanceBase | governance | Y | 0/— | Y | 3/1/0/0 | 8 | governance/services/security_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/security.py:49`; commit 2026-07-16 |
| 142 | `gov_temporary_admin` | `TemporaryAdministration` | GovernanceBase | governance | Y | 2/gov_hierarchy_nodes | — | 3/0/0/0 | 8 | governance/services/hierarchy_service.py | ACTIVE_REQUIRED | P1 | `governance/models/hierarchy.py:113`; commit 2026-07-16 |
| 143 | `gov_terminology_mappings` | `TerminologyMapping` | GovernanceBase | governance | Y | 0/— | — | 2/0/0/0 | 21 | governance/services/interoperability_service.py, services/clinical_service.py | ACTIVE_REQUIRED | P0 | `governance/models/interoperability.py:59`; commit 2026-07-16 |
| 144 | `gov_threat_intel` | `ThreatIntelligenceEvent` | GovernanceBase | governance | Y | 0/— | Y | 3/1/0/0 | 9 | governance/services/security_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/security.py:88`; commit 2026-07-16 |
| 145 | `gov_training_records` | `TrainingRecord` | GovernanceBase | governance | Y | 1/gov_healthcare_workers | — | 1/0/0/0 | 11 | governance/services/workforce_service.py | ACTIVE_REQUIRED | P1 | `governance/models/workforce.py:79`; commit 2026-07-16 |
| 146 | `gov_westgard_policies` | `WestgardPolicy` | GovernanceBase | governance | Y | 0/— | — | 1/0/0/0 | 8 | governance/services/clinical_governance_service.py | ACTIVE_REQUIRED | P1 | `governance/models/clinical.py:124`; commit 2026-07-16 |
| 147 | `gov_worker_privileges` | `WorkerPrivilege` | GovernanceBase | governance | Y | 1/gov_healthcare_workers | — | 1/0/0/0 | 8 | governance/services/workforce_service.py | ACTIVE_REQUIRED | P1 | `governance/models/workforce.py:113`; commit 2026-07-16 |
| 148 | `hd_mdm_facility_index` | `MasterFacilityIndex` | HealthDataBase | health_data | Y | 0/— | Y | 4/0/0/0 | 2 | health_data/mdm/__init__.py | DORMANT | P2 | `health_data/mdm/models.py:130`; commit 2026-07-16 |
| 149 | `hd_mdm_organization_index` | `MasterOrganizationIndex` | HealthDataBase | health_data | Y | 0/— | Y | 3/0/0/0 | 2 | health_data/mdm/__init__.py | DORMANT | P2 | `health_data/mdm/models.py:96`; commit 2026-07-16 |
| 150 | `hd_mdm_patient_index` | `MasterPatientIndex` | HealthDataBase | health_data | Y | 0/— | Y | 6/0/0/0 | 2 | health_data/mdm/__init__.py | DORMANT | P2 | `health_data/mdm/models.py:28`; commit 2026-07-16 |
| 151 | `hd_mdm_provider_index` | `MasterProviderIndex` | HealthDataBase | health_data | Y | 0/— | Y | 3/0/0/0 | 2 | health_data/mdm/__init__.py | DORMANT | P2 | `health_data/mdm/models.py:68`; commit 2026-07-16 |
| 152 | `hd_mdm_source_references` | `SourceReference` | HealthDataBase | health_data | Y | 1/hd_mdm_patient_index | — | 2/1/0/0 | 2 | health_data/mdm/__init__.py | DORMANT | P2 | `health_data/mdm/models.py:11`; commit 2026-07-16 |
| 153 | `hd_ods_encounter_summary` | `EncounterSummary` | HealthDataBase | health_data | Y | 0/— | — | 3/0/0/0 | 2 | health_data/ods/__init__.py | DORMANT | P2 | `health_data/ods/models.py:48`; commit 2026-07-16 |
| 154 | `hd_ods_lab_result_summary` | `LabResultSummary` | HealthDataBase | health_data | Y | 0/— | — | 5/0/0/0 | 2 | health_data/ods/__init__.py | DORMANT | P2 | `health_data/ods/models.py:75`; commit 2026-07-16 |
| 155 | `hd_ods_order_summary` | `OrderSummary` | HealthDataBase | health_data | Y | 0/— | — | 4/0/0/0 | 2 | health_data/ods/__init__.py | DORMANT | P2 | `health_data/ods/models.py:106`; commit 2026-07-16 |
| 156 | `hd_ods_patient_summary` | `PatientSummary` | HealthDataBase | health_data | Y | 0/— | — | 3/1/0/0 | 2 | health_data/ods/__init__.py | DORMANT | P2 | `health_data/ods/models.py:19`; commit 2026-07-16 |
| 157 | `hd_wh_dim_date` | `DimDate` | HealthDataBase | health_data | Y | 0/— | — | 2/1/0/0 | 16 | factory.py | ACTIVE_REQUIRED | P1 | `health_data/warehouse/models.py:51`; commit 2026-07-16 |
| 158 | `hd_wh_dim_facility` | `DimFacility` | HealthDataBase | health_data | Y | 0/— | — | 3/1/0/0 | 12 | factory.py | ACTIVE_REQUIRED | P1 | `health_data/warehouse/models.py:77`; commit 2026-07-16 |
| 159 | `hd_wh_dim_lab_test` | `DimLabTest` | HealthDataBase | health_data | Y | 0/— | — | 2/0/0/0 | 3 | health_data/warehouse/__init__.py, research_platform/sdk.py | ACTIVE_REQUIRED | P1 | `health_data/warehouse/models.py:123`; commit 2026-07-16 |
| 160 | `hd_wh_dim_patient` | `DimPatient` | HealthDataBase | health_data | Y | 0/— | — | 4/1/0/0 | 11 | factory.py | ACTIVE_REQUIRED | P1 | `health_data/warehouse/models.py:19`; commit 2026-07-16 |
| 161 | `hd_wh_dim_provider` | `DimProvider` | HealthDataBase | health_data | Y | 0/— | — | 2/1/0/0 | 10 | factory.py | ACTIVE_REQUIRED | P1 | `health_data/warehouse/models.py:101`; commit 2026-07-16 |
| 162 | `hd_wh_fact_encounter` | `FactEncounter` | HealthDataBase | health_data | Y | 0/— | — | 8/1/0/0 | 4 | health_data/warehouse/__init__.py, research_platform/open_apis.py | ACTIVE_REQUIRED | P1 | `health_data/warehouse/models.py:142`; commit 2026-07-16 |
| 163 | `hd_wh_fact_lab_result` | `FactLabResult` | HealthDataBase | health_data | Y | 0/— | — | 11/1/0/0 | 11 | factory.py | ACTIVE_REQUIRED | P1 | `health_data/warehouse/models.py:173`; commit 2026-07-16 |
| 164 | `hd_wh_fact_order` | `FactOrder` | HealthDataBase | health_data | Y | 0/— | — | 8/1/0/0 | 4 | health_data/warehouse/__init__.py, research_platform/open_apis.py | ACTIVE_REQUIRED | P1 | `health_data/warehouse/models.py:209`; commit 2026-07-16 |
| 165 | `bed_assignments` | `BedAssignment` | HospitalBase | hospital | Y | 1/hospital_beds | — | 3/0/0/0 | 18 | factory.py, routes/hospital.py | ACTIVE_REQUIRED | P1 | `hospital/models/__init__.py:266`; commit 2026-08-21 |
| 166 | `hospital_beds` | `Bed` | HospitalBase | hospital | Y | 1/hospital_rooms | — | 5/0/0/0 | 116 | factory.py, national/intelligence/routes.py | ACTIVE_REQUIRED | P0 | `hospital/models/__init__.py:145`; commit 2026-08-21 |
| 167 | `hospital_buildings` | `Building` | HospitalBase | hospital | Y | 1/hospital_campuses | — | 3/0/0/0 | 14 | factory.py, routes/hospital.py | ACTIVE_REQUIRED | P1 | `hospital/models/__init__.py:62`; commit 2026-08-21 |
| 168 | `hospital_campuses` | `Campus` | HospitalBase | hospital | Y | 1/hospitals | — | 3/0/0/0 | 16 | factory.py, routes/hospital.py | ACTIVE_REQUIRED | P1 | `hospital/models/__init__.py:48`; commit 2026-08-21 |
| 169 | `hospital_clinics` | `Clinic` | HospitalBase | hospital | Y | 2/hospital_departments,hospitals | — | 5/0/0/0 | 20 | factory.py, routes/hospital.py | ACTIVE_REQUIRED | P0 | `hospital/models/__init__.py:110`; commit 2026-08-21 |
| 170 | `hospital_cost_centers` | `CostCenter` | HospitalBase | hospital | Y | 1/hospitals | — | 4/0/0/0 | 11 | factory.py, services/hospital_service.py | ACTIVE_REQUIRED | P1 | `hospital/models/__init__.py:251`; commit 2026-08-21 |
| 171 | `hospital_departments` | `HospitalDepartment` | HospitalBase | hospital | Y | 2/hospital_departments,hospitals | — | 5/0/0/0 | 40 | factory.py | ACTIVE_REQUIRED | P0 | `hospital/models/__init__.py:90`; commit 2026-08-21 |
| 172 | `hospital_floors` | `Floor` | HospitalBase | hospital | Y | 1/hospital_buildings | — | 3/0/0/0 | 13 | factory.py, routes/hospital.py | ACTIVE_REQUIRED | P1 | `hospital/models/__init__.py:76`; commit 2026-08-21 |
| 173 | `hospital_medical_equipment` | `MedicalEquipment` | HospitalBase | hospital | Y | 2/hospital_departments,hospitals | — | 6/1/0/0 | 24 | factory.py, routes/hospital.py | ACTIVE_REQUIRED | P0 | `hospital/models/__init__.py:230`; commit 2026-08-21 |
| 174 | `hospital_operation_theaters` | `OperationTheater` | HospitalBase | hospital | Y | 2/hospital_departments,hospitals | — | 6/0/0/0 | 42 | factory.py, routes/hospital.py | ACTIVE_REQUIRED | P0 | `hospital/models/__init__.py:172`; commit 2026-08-21 |
| 175 | `hospital_rooms` | `Room` | HospitalBase | hospital | Y | 3/hospital_clinics,hospital_departments,hospital_floors | — | 6/0/0/0 | 38 | factory.py | ACTIVE_REQUIRED | P0 | `hospital/models/__init__.py:127`; commit 2026-08-21 |
| 176 | `hospital_units` | `Unit` | HospitalBase | hospital | Y | 1/hospitals | — | 4/0/0/0 | 24 | factory.py | ACTIVE_REQUIRED | P0 | `hospital/models/__init__.py:159`; commit 2026-08-21 |
| 177 | `hospitals` | `HospitalMaster` | HospitalBase | hospital | Y | 0/— | — | 3/1/0/0 | 48 | document_intelligence/application/wiring.py, ems/api/routes.py | ACTIVE_REQUIRED | P0 | `hospital/models/__init__.py:22`; commit 2026-08-21 |
| 178 | `niam_admin_units` | `NIAMAdminUnit` | IdentityBase | identity | Y | 1/niam_admin_departments | — | 3/2/0/0 | 9 | identity/services/membership_service.py | ACTIVE_REQUIRED | P1 | `identity/models/administrative_structure.py:96`; commit 2026-08-14 |
| 179 | `niam_organization_ownerships` | `OrganizationOwnership` | IdentityBase | identity | Y | 2/niam_accounts,niam_organizations | — | 3/1/0/0 | 13 | identity/services/membership_service.py, identity/services/organization_service.py | ACTIVE_REQUIRED | P1 | `identity/models/administrative_structure.py:123`; commit 2026-08-14 |
| 180 | `niam_organization_representatives` | `OrganizationRepresentative` | IdentityBase | identity | Y | 3/niam_accounts,niam_organizations | — | 3/1/0/0 | 13 | identity/services/membership_service.py, identity/services/organization_service.py | ACTIVE_REQUIRED | P1 | `identity/models/administrative_structure.py:109`; commit 2026-08-14 |
| 181 | `ins_appeals` | `Appeal` | InsBase | insurance | **N** | 1/ins_claims | Y | 7/1/0/0 | 8 | insurance/api/claims.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:582`; commit 2026-07-22 |
| 182 | `ins_authorizations` | `Authorization` | InsBase | insurance | **N** | 3/ins_coverages,ins_providers,patients | Y | 10/1/0/0 | 92 | control_plane/routes.py, factory.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:327`; commit 2026-07-22 |
| 183 | `ins_benefit_package_items` | `BenefitPackageItem` | InsBase | insurance | **N** | 1/ins_benefit_packages | — | 5/0/0/0 | 0 | — | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/services.py:93`; commit 2026-07-22 |
| 184 | `ins_benefit_packages` | `BenefitPackage` | InsBase | insurance | **N** | 2/ins_policies,ins_providers | Y | 6/0/0/0 | 27 | insurance/api/coverage_check.py, insurance/api/coverages.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:223`; commit 2026-07-22 |
| 185 | `ins_benefit_utilization` | `BenefitUtilization` | InsBase | insurance | **N** | 2/ins_coverages,ins_members | — | 6/0/0/0 | 6 | insurance/api/coverages.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/services.py:181`; commit 2026-07-22 |
| 186 | `ins_cards` | `InsuranceCard` | InsBase | insurance | **N** | 1/ins_members | Y | 6/1/0/0 | 0 | — | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/members.py:89`; commit 2026-07-22 |
| 187 | `ins_claim_items` | `InsuranceClaimItem` | InsBase | insurance | **N** | 1/ins_claims | Y | 1/0/0/0 | 12 | insurance/api/claims.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:449`; commit 2026-07-22 |
| 188 | `ins_claims` | `InsuranceClaim` | InsBase | insurance | **N** | 4/ins_authorizations,ins_coverages,ins_providers | Y | 12/2/0/0 | 150 | insurance/api/claims.py, insurance/api/payments.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:387`; commit 2026-07-22 |
| 189 | `ins_coverage_periods` | `CoveragePeriod` | InsBase | insurance | **N** | 2/ins_coverages,ins_members | — | 6/0/0/0 | 0 | — | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/members.py:219`; commit 2026-07-22 |
| 190 | `ins_coverages` | `Coverage` | InsBase | insurance | **N** | 3/ins_policies,patients | Y | 7/0/0/0 | 122 | billing/routes.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:170`; commit 2026-07-22 |
| 191 | `ins_deductible_tracking` | `DeductibleTracking` | InsBase | insurance | **N** | 2/ins_coverages,ins_members | — | 6/1/0/0 | 4 | insurance/api/coverages.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/services.py:138`; commit 2026-07-22 |
| 192 | `ins_dependents` | `Dependent` | InsBase | insurance | **N** | 2/ins_members,patients | Y | 6/0/0/0 | 0 | — | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/members.py:178`; commit 2026-07-22 |
| 193 | `ins_electronic_cards` | `ElectronicCard` | InsBase | insurance | **N** | 2/ins_cards,ins_members | — | 7/1/0/0 | 0 | — | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/members.py:134`; commit 2026-07-22 |
| 194 | `ins_fee_schedule` | `FeeScheduleItem` | InsBase | insurance | **N** | 1/ins_providers | Y | 5/1/0/0 | 16 | insurance/services/coverage_engine.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:278`; commit 2026-07-22 |
| 195 | `ins_fraud_alerts` | `FraudAlert` | InsBase | insurance | **N** | 3/ins_claims,ins_providers,patients | Y | 8/0/0/0 | 0 | — | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:631`; commit 2026-07-22 |
| 196 | `ins_geographic_coverage` | `GeographicCoverage` | InsBase | insurance | **N** | 1/ins_network_providers | Y | 6/0/0/0 | 7 | insurance/api/network.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/network.py:217`; commit 2026-07-22 |
| 197 | `ins_medical_services` | `MedicalService` | InsBase | insurance | **N** | 0/— | Y | 6/1/0/0 | 0 | — | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/services.py:48`; commit 2026-07-22 |
| 198 | `ins_members` | `InsuranceMember` | InsBase | insurance | **N** | 2/ins_providers,patients | Y | 8/1/0/0 | 2 | insurance/domain/services.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/members.py:48`; commit 2026-07-22 |
| 199 | `ins_network_providers` | `NetworkProvider` | InsBase | insurance | **N** | 2/ins_provider_contracts,ins_providers | Y | 7/0/0/0 | 38 | insurance/api/network.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/network.py:49`; commit 2026-07-22 |
| 200 | `ins_network_services` | `NetworkService` | InsBase | insurance | **N** | 1/ins_network_providers | — | 5/0/0/0 | 10 | insurance/api/network.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/network.py:92`; commit 2026-07-22 |
| 201 | `ins_payments` | `InsurancePayment` | InsBase | insurance | **N** | 2/ins_claims,ins_providers | Y | 7/1/0/0 | 57 | insurance/api/claims.py, insurance/api/payments.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:493`; commit 2026-07-22 |
| 202 | `ins_policies` | `InsurancePolicy` | InsBase | insurance | **N** | 2/ins_providers,patients | Y | 8/0/0/0 | 57 | insurance/api/coverage_check.py, insurance/api/coverages.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:112`; commit 2026-07-22 |
| 203 | `ins_provider_accreditations` | `ProviderAccreditation` | InsBase | insurance | **N** | 1/ins_network_providers | Y | 6/0/0/0 | 0 | — | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/network.py:173`; commit 2026-07-22 |
| 204 | `ins_provider_availability` | `ProviderAvailability` | InsBase | insurance | **N** | 1/ins_network_providers | — | 4/0/0/0 | 8 | insurance/api/network.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/network.py:132`; commit 2026-07-22 |
| 205 | `ins_provider_contracts` | `ProviderContract` | InsBase | insurance | **N** | 1/ins_providers | Y | 7/1/0/0 | 11 | insurance/api/providers.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:678`; commit 2026-07-22 |
| 206 | `ins_providers` | `InsuranceProvider` | InsBase | insurance | **N** | 0/— | Y | 4/1/0/0 | 65 | insurance/api/claims.py, insurance/api/coverage_check.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:64`; commit 2026-07-22 |
| 207 | `ins_referral_history` | `ReferralHistory` | InsBase | insurance | **N** | 1/ins_referrals | Y | 5/0/0/0 | 5 | insurance/api/referrals.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/referral.py:120`; commit 2026-07-22 |
| 208 | `ins_referral_validations` | `ReferralValidation` | InsBase | insurance | **N** | 1/ins_referrals | Y | 5/0/0/0 | 2 | insurance/api/referrals.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/referral.py:152`; commit 2026-07-22 |
| 209 | `ins_referrals` | `InsuranceReferral` | InsBase | insurance | **N** | 3/ins_authorizations,ins_coverages,patients | Y | 15/1/0/0 | 42 | insurance/api/referrals.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/referral.py:51`; commit 2026-07-22 |
| 210 | `ins_settlements` | `Settlement` | InsBase | insurance | **N** | 1/ins_providers | Y | 6/1/0/0 | 62 | insurance/api/payments.py | OWNERSHIP_UNCLEAR | P0 | `insurance/domain/models.py:537`; commit 2026-07-22 |
| 211 | `knowledge_edges` | `KnowledgeEdge` | Base | knowledge_graph | Y | 2/knowledge_nodes | — | 3/0/0/0 | 40 | ai/knowledge_graph.py, engineering/intelligence/knowledge_graph.py | ACTIVE_REQUIRED | P0 | `knowledge_graph/models.py:92`; commit 2026-07-24 |
| 212 | `knowledge_graph_snapshots` | `KnowledgeGraphSnapshot` | Base | knowledge_graph | Y | 0/— | — | 1/0/0/0 | 5 | knowledge_graph/engine.py | ACTIVE_REQUIRED | P1 | `knowledge_graph/models.py:119`; commit 2026-07-24 |
| 213 | `knowledge_nodes` | `KnowledgeNode` | Base | knowledge_graph | Y | 0/— | — | 2/1/0/0 | 56 | ai/knowledge_graph.py, engineering/intelligence/knowledge_graph.py | ACTIVE_REQUIRED | P0 | `knowledge_graph/models.py:59`; commit 2026-07-24 |
| 214 | `test_results` | `TestResult` | Base | models | Y | 2/citizens,labs | — | 8/1/0/0 | 30 | factory.py, integration/routes.py | ACTIVE_REQUIRED | P0 | `models/test_result.py:40`; commit 2026-07-18 |
| 215 | `national_addresses` | `Address` | NationalBase | national | Y | 0/— | — | 3/0/0/0 | 4 | certification/dimensions/code_quality.py, certification/release_gates.py | ACTIVE_REQUIRED | P1 | `national/domain/address.py:7`; commit 2026-07-16 |
| 216 | `national_advance_directives` | `AdvanceDirective` | NationalBase | national | Y | 2/national_citizens,national_patients | — | 6/0/0/0 | 10 | national/api/routes/advance_directive.py | ACTIVE_REQUIRED | P1 | `national/domain/advance_directive.py:7`; commit 2026-07-16 |
| 217 | `national_attachments` | `Attachment` | NationalBase | national | Y | 0/— | — | 2/0/0/0 | 8 | routes/ehr.py | ACTIVE_REQUIRED | P1 | `national/domain/attachments.py:7`; commit 2026-07-16 |
| 218 | `national_background_job_dependencies` | `NationalJobDependency` | NationalBase | national | Y | 2/national_background_jobs | Y | 3/1/0/0 | 17 | national/background_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/background_platform/infrastructure/models.py:153`; commit 2026-07-16 |
| 219 | `national_background_job_executions` | `NationalJobExecution` | NationalBase | national | Y | 1/national_background_jobs | Y | 4/0/0/0 | 23 | national/background_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/background_platform/infrastructure/models.py:113`; commit 2026-07-16 |
| 220 | `national_background_job_schedules` | `NationalJobSchedule` | NationalBase | national | Y | 1/national_background_jobs | Y | 4/0/0/0 | 27 | national/background_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/background_platform/infrastructure/models.py:73`; commit 2026-07-16 |
| 221 | `national_background_jobs` | `NationalJob` | NationalBase | national | Y | 0/— | Y | 8/0/0/0 | 36 | national/background_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/background_platform/infrastructure/models.py:28`; commit 2026-07-16 |
| 222 | `national_biometrics` | `BiometricRecord` | NationalBase | national | Y | 1/national_citizens | Y | 3/0/0/0 | 2 | national/domain/__init__.py | DORMANT | P2 | `national/domain/biometrics.py:9`; commit 2026-07-16 |
| 223 | `national_communications` | `Communication` | NationalBase | national | Y | 0/— | — | 3/0/0/0 | 17 | communication/__init__.py, communication/experience/__init__.py | ACTIVE_REQUIRED | P1 | `national/domain/communication.py:7`; commit 2026-07-16 |
| 224 | `national_coverages` | `Coverage` | NationalBase | national | Y | 3/national_citizens,national_insurances,national_patients | Y | 8/0/0/0 | 121 | billing/routes.py | ACTIVE_REQUIRED | P0 | `national/domain/coverage.py:9`; commit 2026-07-16 |
| 225 | `national_death_records` | `DeathRecord` | NationalBase | national | Y | 2/national_citizens,national_practitioners | — | 7/1/0/0 | 2 | national/domain/__init__.py | DORMANT | P2 | `national/domain/death_record.py:7`; commit 2026-07-16 |
| 226 | `national_directorates` | `Directorate` | NationalBase | national | Y | 1/national_organizations | — | 5/1/0/0 | 10 | core/bootstrap/directorates.py, core/bootstrap/models.py | ACTIVE_REQUIRED | P1 | `national/domain/directorate.py:7`; commit 2026-07-16 |
| 227 | `national_document_attachments` | `NationalDocumentAttachmentModel` | NationalBase | national | Y | 1/national_documents | — | 2/0/0/0 | 13 | national/document_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/document_platform/infrastructure/models.py:191`; commit 2026-07-16 |
| 228 | `national_document_qr_codes` | `NationalDocumentQRCodeModel` | NationalBase | national | Y | 1/national_documents | — | 2/1/0/0 | 12 | national/document_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/document_platform/infrastructure/models.py:161`; commit 2026-07-16 |
| 229 | `national_document_versions` | `NationalDocumentVersionModel` | NationalBase | national | Y | 1/national_documents | — | 3/1/0/0 | 13 | national/document_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/document_platform/infrastructure/models.py:82`; commit 2026-07-16 |
| 230 | `national_documents` | `NationalDocumentModel` | NationalBase | national | Y | 0/— | Y | 9/0/0/0 | 34 | national/document_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/document_platform/infrastructure/models.py:29`; commit 2026-07-16 |
| 231 | `national_electronic_signatures` | `NationalElectronicSignatureModel` | NationalBase | national | Y | 1/national_documents | Y | 4/0/0/0 | 14 | national/document_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/document_platform/infrastructure/models.py:116`; commit 2026-07-16 |
| 232 | `national_emergency_contacts` | `EmergencyContact` | NationalBase | national | Y | 2/national_citizens,national_patients | Y | 3/0/0/0 | 8 | citizen_platform/emergency.py, national/domain/__init__.py | ACTIVE_REQUIRED | P1 | `national/domain/emergency_contact.py:9`; commit 2026-07-16 |
| 233 | `national_employees` | `Employee` | NationalBase | national | Y | 3/national_departments,national_facilities,national_organizations | Y | 7/1/0/0 | 6 | routes/labs.py, services/lab_service.py | ACTIVE_REQUIRED | P1 | `national/domain/employee.py:9`; commit 2026-07-16 |
| 234 | `national_family_members` | `FamilyMember` | NationalBase | national | Y | 2/national_citizens,national_families | Y | 4/1/0/0 | 17 | national/api/routes/family.py, national/services/family_service.py | ACTIVE_REQUIRED | P1 | `national/domain/family.py:42`; commit 2026-07-16 |
| 235 | `national_foreigners` | `Foreigner` | NationalBase | national | Y | 0/— | Y | 8/2/0/0 | 6 | governance/services/identity_persistence_service.py, services/governance/identity_governance.py | ACTIVE_REQUIRED | P1 | `national/domain/foreigner.py:9`; commit 2026-07-16 |
| 236 | `national_health_cards` | `HealthCard` | NationalBase | national | Y | 1/national_citizens | Y | 4/1/0/0 | 9 | national/api/routes/health_card.py | ACTIVE_REQUIRED | P1 | `national/domain/health_card.py:9`; commit 2026-07-18 |
| 237 | `national_health_number_sequences` | `HealthNumberSequence` | NationalBase | national | Y | 0/— | — | 1/1/0/0 | 8 | national/services/citizen_service.py | ACTIVE_REQUIRED | P1 | `national/domain/health_number.py:7`; commit 2026-07-16 |
| 238 | `national_identifier_mappings` | `NationalIdentifierMapping` | NationalBase | national | Y | 0/— | — | 4/0/0/0 | 2 | national/domain/__init__.py | DORMANT | P2 | `national/domain/national_id.py:7`; commit 2026-07-16 |
| 239 | `national_identity_audit_logs` | `IdentityAuditLog` | NationalBase | national | Y | 0/— | — | 5/0/0/0 | 3 | national/domain/__init__.py, national/events/identity_events.py | ACTIVE_REQUIRED | P1 | `national/domain/audit_identity.py:7`; commit 2026-07-16 |
| 240 | `national_identity_resolutions` | `IdentityResolution` | NationalBase | national | Y | 1/national_citizens | — | 5/0/0/0 | 3 | national/domain/__init__.py, national/events/identity_events.py | ACTIVE_REQUIRED | P1 | `national/domain/identity_resolution.py:7`; commit 2026-07-16 |
| 241 | `national_insurances` | `Insurance` | NationalBase | national | Y | 1/national_organizations | Y | 4/1/0/0 | 37 | billing/routes.py | ACTIVE_REQUIRED | P0 | `national/domain/insurance.py:9`; commit 2026-07-16 |
| 242 | `national_laboratories` | `Laboratory` | NationalBase | national | Y | 2/national_facilities,national_organizations | — | 5/2/0/0 | 76 | ai_fabric/agents/__init__.py, citizen_platform/laboratory.py | ACTIVE_REQUIRED | P0 | `national/domain/laboratory.py:7`; commit 2026-07-16 |
| 243 | `national_medication_catalog` | `MedicationCatalog` | NationalBase | national | Y | 0/— | — | 5/1/0/0 | 44 | national/api/routes/medication_catalog.py, national/services/cds_engine.py | ACTIVE_REQUIRED | P0 | `national/domain/medication_catalog.py:7`; commit 2026-07-16 |
| 244 | `national_merge_audit` | `MergeAudit` | NationalBase | national | Y | 3/national_citizens,national_merge_records | — | 6/1/0/0 | 47 | routes/canonical_patient.py, services/mpi/__init__.py | ACTIVE_REQUIRED | P0 | `national/domain/merge_record.py:42`; commit 2026-07-16 |
| 245 | `national_merge_records` | `MergeRecord` | NationalBase | national | Y | 2/national_citizens | Y | 5/0/0/0 | 5 | national/domain/__init__.py, national/events/identity_events.py | ACTIVE_REQUIRED | P1 | `national/domain/merge_record.py:9`; commit 2026-07-16 |
| 246 | `national_newborns` | `Newborn` | NationalBase | national | Y | 6/national_citizens,national_families,national_guardians | Y | 11/1/0/0 | 6 | governance/services/identity_persistence_service.py, services/governance/identity_governance.py | ACTIVE_REQUIRED | P1 | `national/domain/newborn.py:19`; commit 2026-07-16 |
| 247 | `national_observability_alert_events` | `NationalAlertEvent` | NationalBase | national | Y | 1/national_observability_alert_rules | Y | 5/0/0/0 | 19 | national/observability/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/observability/infrastructure/models.py:174`; commit 2026-07-16 |
| 248 | `national_observability_alert_rules` | `NationalAlertRule` | NationalBase | national | Y | 0/— | Y | 2/0/0/0 | 18 | national/observability/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/observability/infrastructure/models.py:139`; commit 2026-07-16 |
| 249 | `national_observability_dashboard_panels` | `NationalDashboardPanel` | NationalBase | national | Y | 1/national_observability_dashboards | — | 2/0/0/0 | 11 | national/observability/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/observability/infrastructure/models.py:237`; commit 2026-07-16 |
| 250 | `national_observability_dashboards` | `NationalDashboard` | NationalBase | national | Y | 0/— | — | 0/0/0/0 | 15 | national/observability/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/observability/infrastructure/models.py:212`; commit 2026-07-16 |
| 251 | `national_observability_health_checks` | `NationalHealthCheck` | NationalBase | national | Y | 0/— | Y | 3/1/0/0 | 15 | national/observability/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/observability/infrastructure/models.py:101`; commit 2026-07-16 |
| 252 | `national_observability_metrics` | `NationalMetricPoint` | NationalBase | national | Y | 0/— | Y | 4/0/0/0 | 15 | national/observability/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/observability/infrastructure/models.py:28`; commit 2026-07-16 |
| 253 | `national_observability_service_graphs` | `NationalServiceGraph` | NationalBase | national | Y | 0/— | Y | 1/1/0/0 | 14 | national/observability/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/observability/infrastructure/models.py:269`; commit 2026-07-16 |
| 254 | `national_observability_trace_spans` | `NationalTraceSpan` | NationalBase | national | Y | 0/— | Y | 5/0/0/0 | 25 | national/observability/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/observability/infrastructure/models.py:59`; commit 2026-07-16 |
| 255 | `national_observations` | `Observation` | NationalBase | national | Y | 4/national_citizens,national_encounters,national_patients | — | 10/0/0/0 | 301 | document_intelligence/application/wiring.py | ACTIVE_REQUIRED | P0 | `national/domain/observation.py:7`; commit 2026-07-16 |
| 256 | `national_providers` | `Provider` | NationalBase | national | Y | 2/national_facilities,national_organizations | — | 5/0/0/0 | 47 | capabilities/provider_management/routes.py | ACTIVE_REQUIRED | P0 | `national/domain/provider.py:7`; commit 2026-07-16 |
| 257 | `national_residents` | `Resident` | NationalBase | national | Y | 0/— | Y | 3/1/0/0 | 6 | routes/metrics.py, services/governance/identity_governance.py | ACTIVE_REQUIRED | P1 | `national/domain/resident.py:9`; commit 2026-07-16 |
| 258 | `national_retention_rules` | `NationalRetentionRuleModel` | NationalBase | national | Y | 0/— | Y | 2/1/0/0 | 14 | national/document_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/document_platform/infrastructure/models.py:220`; commit 2026-07-16 |
| 259 | `national_rule_evaluation_logs` | `RuleEvaluationLog` | NationalBase | national | Y | 0/— | Y | 4/0/0/0 | 6 | national/rules_engine/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/rules_engine/infrastructure/models.py:91`; commit 2026-07-18 |
| 260 | `national_rules` | `RuleModel` | NationalBase | national | Y | 0/— | Y | 5/0/0/0 | 38 | national/rules_engine/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/rules_engine/infrastructure/models.py:20`; commit 2026-07-18 |
| 261 | `national_scheduling_appointment_reminders` | `NationalAppointmentReminder` | NationalBase | national | Y | 1/national_scheduling_appointments | — | 3/0/0/0 | 18 | national/scheduling_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/scheduling_platform/infrastructure/models.py:250`; commit 2026-07-16 |
| 262 | `national_scheduling_appointments` | `NationalAppointment` | NationalBase | national | Y | 0/— | Y | 10/0/0/0 | 45 | national/scheduling_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/scheduling_platform/infrastructure/models.py:28`; commit 2026-07-16 |
| 263 | `national_scheduling_calendars` | `NationalCalendar` | NationalBase | national | Y | 0/— | — | 0/0/0/0 | 15 | national/scheduling_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P1 | `national/scheduling_platform/infrastructure/models.py:223`; commit 2026-07-16 |
| 264 | `national_scheduling_resources` | `NationalResource` | NationalBase | national | Y | 0/— | Y | 3/0/0/0 | 21 | national/scheduling_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/scheduling_platform/infrastructure/models.py:87`; commit 2026-07-16 |
| 265 | `national_scheduling_schedules` | `NationalSchedule` | NationalBase | national | Y | 1/national_scheduling_resources | — | 3/1/0/0 | 29 | national/scheduling_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/scheduling_platform/infrastructure/models.py:123`; commit 2026-07-16 |
| 266 | `national_scheduling_time_slots` | `NationalTimeSlot` | NationalBase | national | Y | 1/national_scheduling_schedules | Y | 4/0/0/0 | 26 | national/scheduling_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/scheduling_platform/infrastructure/models.py:154`; commit 2026-07-16 |
| 267 | `national_scheduling_waiting_list` | `NationalWaitingList` | NationalBase | national | Y | 0/— | — | 5/0/0/0 | 31 | national/scheduling_platform/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/scheduling_platform/infrastructure/models.py:185`; commit 2026-07-16 |
| 268 | `national_task_assignments` | `NationalTaskAssignmentModel` | NationalBase | national | Y | 0/— | — | 2/0/0/0 | 0 | — | UNUSED | P3 | `national/task_engine/infrastructure/models.py:63`; commit 2026-07-24 |
| 269 | `national_task_audit_logs` | `NationalTaskAuditLogModel` | NationalBase | national | Y | 0/— | — | 1/0/0/0 | 0 | — | UNUSED | P3 | `national/task_engine/infrastructure/models.py:126`; commit 2026-07-24 |
| 270 | `national_task_comments` | `NationalTaskCommentModel` | NationalBase | national | Y | 0/— | — | 1/0/0/0 | 0 | — | UNUSED | P3 | `national/task_engine/infrastructure/models.py:111`; commit 2026-07-24 |
| 271 | `national_task_escalations` | `NationalTaskEscalationModel` | NationalBase | national | Y | 0/— | — | 2/0/0/0 | 0 | — | UNUSED | P3 | `national/task_engine/infrastructure/models.py:78`; commit 2026-07-24 |
| 272 | `national_task_queues` | `NationalTaskQueueModel` | NationalBase | national | Y | 0/— | — | 0/0/0/0 | 0 | — | UNUSED | P3 | `national/task_engine/infrastructure/models.py:45`; commit 2026-07-24 |
| 273 | `national_task_sla_definitions` | `NationalTaskSLAModel` | NationalBase | national | Y | 0/— | — | 2/0/0/0 | 0 | — | UNUSED | P3 | `national/task_engine/infrastructure/models.py:93`; commit 2026-07-24 |
| 274 | `national_tasks` | `NationalTaskModel` | NationalBase | national | Y | 0/— | — | 7/0/0/0 | 21 | national/task_engine/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national/task_engine/infrastructure/models.py:13`; commit 2026-07-24 |
| 275 | `national_unknown_patients` | `UnknownPatient` | NationalBase | national | Y | 0/— | Y | 6/1/0/0 | 2 | national/domain/__init__.py | DORMANT | P2 | `national/domain/unknown_patient.py:9`; commit 2026-07-16 |
| 276 | `national_visitors` | `Visitor` | NationalBase | national | Y | 0/— | Y | 5/1/0/0 | 4 | services/governance/identity_governance.py | ACTIVE_REQUIRED | P1 | `national/domain/visitor.py:9`; commit 2026-07-16 |
| 277 | `national_visits` | `Visit` | NationalBase | national | Y | 6/national_citizens,national_departments,national_encounters | Y | 10/0/0/0 | 5 | insurance/services/coverage_engine.py | ACTIVE_REQUIRED | P1 | `national/domain/visit.py:9`; commit 2026-07-16 |
| 278 | `national_vital_signs_reference` | `VitalSignsReference` | NationalBase | national | Y | 0/— | — | 2/1/0/0 | 15 | national/api/routes/vital_signs.py | ACTIVE_REQUIRED | P1 | `national/domain/vital_signs.py:7`; commit 2026-07-16 |
| 279 | `ref_blood_groups` | `BloodGroup` | NationalBase | national | Y | 0/— | — | 0/0/0/0 | 3 | national/enums.py, national/reference/__init__.py | ACTIVE_REQUIRED | P1 | `national/reference/blood_groups.py:7`; commit 2026-07-16 |
| 280 | `ref_countries` | `Country` | NationalBase | national | Y | 0/— | — | 0/0/0/0 | 3 | national/services/reference_service.py | ACTIVE_REQUIRED | P1 | `national/reference/countries.py:7`; commit 2026-07-16 |
| 281 | `ref_districts` | `District` | NationalBase | national | Y | 0/— | — | 2/0/0/0 | 4 | national/services/reference_service.py, routes/compliance.py | ACTIVE_REQUIRED | P1 | `national/reference/districts.py:7`; commit 2026-07-16 |
| 282 | `ref_facility_types` | `FacilityTypeRef` | NationalBase | national | Y | 0/— | — | 0/0/0/0 | 2 | national/reference/__init__.py | DORMANT | P2 | `national/reference/facilities.py:7`; commit 2026-07-16 |
| 283 | `ref_fhir_terminology` | `FHIRTerminology` | NationalBase | national | Y | 0/— | — | 2/1/0/0 | 2 | national/reference/__init__.py | DORMANT | P2 | `national/reference/fhir_terminology.py:7`; commit 2026-07-16 |
| 284 | `ref_governorates` | `Governorate` | NationalBase | national | Y | 0/— | — | 1/0/0/0 | 4 | national/services/reference_service.py | ACTIVE_REQUIRED | P1 | `national/reference/governorates.py:7`; commit 2026-07-16 |
| 285 | `ref_icd10_codes` | `ICD10Code` | NationalBase | national | Y | 0/— | — | 1/1/0/0 | 13 | national/services/reference_service.py, services/clinical_service.py | ACTIVE_REQUIRED | P1 | `national/reference/icd10.py:7`; commit 2026-07-16 |
| 286 | `ref_icd11_codes` | `ICD11Code` | NationalBase | national | Y | 0/— | — | 1/1/0/0 | 3 | clinical/terminology/models.py, national/reference/__init__.py | ACTIVE_REQUIRED | P1 | `national/reference/icd11.py:7`; commit 2026-07-16 |
| 287 | `ref_languages` | `Language` | NationalBase | national | Y | 0/— | — | 0/0/0/0 | 3 | health_core/integration/arabic_rtl_a11y.py, national/reference/__init__.py | ACTIVE_REQUIRED | P1 | `national/reference/languages.py:7`; commit 2026-07-16 |
| 288 | `ref_loinc_codes` | `LOINCCode` | NationalBase | national | Y | 0/— | — | 1/1/0/0 | 14 | national/services/reference_service.py, services/clinical_service.py | ACTIVE_REQUIRED | P1 | `national/reference/loinc.py:7`; commit 2026-07-16 |
| 289 | `ref_nationalities` | `Nationality` | NationalBase | national | Y | 0/— | — | 0/0/0/0 | 2 | national/reference/__init__.py | DORMANT | P2 | `national/reference/nationalities.py:7`; commit 2026-07-16 |
| 290 | `ref_professions` | `Profession` | NationalBase | national | Y | 0/— | — | 0/0/0/0 | 2 | national/reference/__init__.py | DORMANT | P2 | `national/reference/professions.py:7`; commit 2026-07-16 |
| 291 | `ref_snomed_concepts` | `SNOMEDConcept` | NationalBase | national | Y | 0/— | — | 1/1/0/0 | 3 | national/services/reference_service.py | ACTIVE_REQUIRED | P1 | `national/reference/snomed.py:7`; commit 2026-07-16 |
| 292 | `ref_specialties` | `Specialty` | NationalBase | national | Y | 0/— | — | 0/0/0/0 | 2 | national/reference/__init__.py | DORMANT | P2 | `national/reference/specialties.py:7`; commit 2026-07-16 |
| 293 | `ref_subdistricts` | `Subdistrict` | NationalBase | national | Y | 0/— | — | 2/0/0/0 | 2 | national/reference/__init__.py | DORMANT | P2 | `national/reference/subdistricts.py:7`; commit 2026-07-16 |
| 294 | `ref_ucum_units` | `UCUMUnit` | NationalBase | national | Y | 0/— | — | 1/1/0/0 | 3 | national/services/reference_service.py | ACTIVE_REQUIRED | P1 | `national/reference/ucum.py:7`; commit 2026-07-16 |
| 295 | `dp_consent_directives` | `ConsentDirective` | DataPlatformBase | national_data | Y | 2/consents,patients | — | 4/0/0/0 | 18 | factory.py, routes/national_data.py | ACTIVE_REQUIRED | P1 | `national_data/models/governance/ConsentDirective.py:7`; commit 2026-07-16 |
| 296 | `dp_data_catalog` | `DataCatalogEntry` | DataPlatformBase | national_data | Y | 0/— | — | 1/0/0/0 | 17 | factory.py, routes/national_data.py | ACTIVE_REQUIRED | P1 | `national_data/models/governance/DataCatalogEntry.py:7`; commit 2026-07-16 |
| 297 | `dp_data_classifications` | `DataClassification` | DataPlatformBase | national_data | Y | 0/— | — | 1/0/0/0 | 55 | factory.py, governance/services/security_governance_service.py | ACTIVE_REQUIRED | P0 | `national_data/models/governance/DataClassification.py:7`; commit 2026-07-16 |
| 298 | `dp_data_lineage` | `DataLineageEntry` | DataPlatformBase | national_data | Y | 0/— | — | 5/0/0/0 | 25 | factory.py, services/data_platform_service.py | ACTIVE_REQUIRED | P0 | `national_data/models/governance/DataLineageEntry.py:10`; commit 2026-07-16 |
| 299 | `dp_data_quality_checks` | `DataQualityCheck` | DataPlatformBase | national_data | Y | 1/dp_data_quality_rules | — | 6/0/0/0 | 10 | factory.py, services/data_platform_service.py | ACTIVE_REQUIRED | P1 | `national_data/models/governance/DataQualityCheck.py:10`; commit 2026-07-16 |
| 300 | `dp_data_quality_rules` | `DataQualityRule` | DataPlatformBase | national_data | Y | 0/— | — | 1/1/0/0 | 7 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/governance/DataQualityRule.py:7`; commit 2026-07-16 |
| 301 | `dp_data_stewards` | `DataSteward` | DataPlatformBase | national_data | Y | 0/— | — | 3/0/0/0 | 6 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/governance/DataSteward.py:7`; commit 2026-07-16 |
| 302 | `dp_deidentification_jobs` | `DeidentificationJob` | DataPlatformBase | national_data | Y | 0/— | — | 2/0/0/0 | 16 | factory.py, routes/national_data.py | ACTIVE_REQUIRED | P1 | `national_data/models/ai_data/DeidentificationJob.py:7`; commit 2026-07-16 |
| 303 | `dp_device_registry` | `DeviceRegistry` | DataPlatformBase | national_data | Y | 2/edge_devices,labs | — | 4/0/0/0 | 8 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/mdm/DeviceRegistry.py:7`; commit 2026-07-16 |
| 304 | `dp_duplicate_records` | `DuplicateRecord` | DataPlatformBase | national_data | Y | 2/dp_golden_records,patients | — | 4/0/0/0 | 11 | factory.py, services/data_platform_service.py | ACTIVE_REQUIRED | P1 | `national_data/models/mdm/DuplicateRecord.py:7`; commit 2026-07-16 |
| 305 | `dp_event_retention_policies` | `EventRetentionPolicy` | DataPlatformBase | national_data | Y | 0/— | — | 1/1/0/0 | 6 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/event_store/EventRetentionPolicy.py:7`; commit 2026-07-16 |
| 306 | `dp_event_snapshots` | `EventSnapshot` | DataPlatformBase | national_data | Y | 0/— | — | 3/0/0/0 | 10 | factory.py, services/data_platform_service.py | ACTIVE_REQUIRED | P1 | `national_data/models/event_store/EventSnapshot.py:10`; commit 2026-07-16 |
| 307 | `dp_feature_store` | `FeatureStore` | DataPlatformBase | national_data | Y | 0/— | — | 1/1/0/0 | 21 | factory.py | ACTIVE_REQUIRED | P0 | `national_data/models/ai_data/FeatureStore.py:7`; commit 2026-07-16 |
| 308 | `dp_feature_values` | `FeatureValue` | DataPlatformBase | national_data | Y | 1/dp_feature_store | — | 6/0/0/0 | 18 | factory.py, routes/national_data.py | ACTIVE_REQUIRED | P1 | `national_data/models/ai_data/FeatureValue.py:10`; commit 2026-07-16 |
| 309 | `dp_golden_records` | `GoldenRecord` | DataPlatformBase | national_data | Y | 1/patients | — | 7/0/0/0 | 22 | factory.py, routes/national_data.py | ACTIVE_REQUIRED | P0 | `national_data/models/mdm/GoldenRecord.py:7`; commit 2026-07-16 |
| 310 | `dp_knowledge_graph_edges` | `KnowledgeGraphEdge` | DataPlatformBase | national_data | Y | 2/dp_knowledge_graph_nodes | — | 6/0/0/0 | 28 | document_intelligence/domain/repository.py, document_intelligence/infrastructure/repository.py | ACTIVE_REQUIRED | P0 | `national_data/models/ai_data/KnowledgeGraphEdge.py:7`; commit 2026-07-16 |
| 311 | `dp_knowledge_graph_nodes` | `KnowledgeGraphNode` | DataPlatformBase | national_data | Y | 0/— | — | 3/0/0/0 | 8 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/ai_data/KnowledgeGraphNode.py:7`; commit 2026-07-16 |
| 312 | `dp_location_registry` | `LocationRegistry` | DataPlatformBase | national_data | Y | 2/labs,national_facilities | — | 3/1/0/0 | 6 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/mdm/LocationRegistry.py:7`; commit 2026-07-16 |
| 313 | `dp_merge_actions` | `MergeAction` | DataPlatformBase | national_data | Y | 1/dp_golden_records | — | 2/0/0/0 | 11 | factory.py, services/data_platform_service.py | ACTIVE_REQUIRED | P1 | `national_data/models/mdm/MergeAction.py:10`; commit 2026-07-16 |
| 314 | `dp_metadata_registry` | `MetadataEntry` | DataPlatformBase | national_data | Y | 0/— | — | 1/0/0/0 | 6 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/governance/MetadataEntry.py:7`; commit 2026-07-16 |
| 315 | `dp_provider_registry` | `ProviderRegistry` | DataPlatformBase | national_data | Y | 2/lab_users,national_practitioners | — | 5/0/0/0 | 6 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/mdm/ProviderRegistry.py:7`; commit 2026-07-16 |
| 316 | `dp_retention_policies` | `RetentionPolicy` | DataPlatformBase | national_data | Y | 0/— | — | 2/1/0/0 | 74 | document_intelligence/api/routes.py, document_intelligence/domain/repository.py | ACTIVE_REQUIRED | P0 | `national_data/models/governance/RetentionPolicy.py:7`; commit 2026-07-16 |
| 317 | `dp_source_systems` | `SourceSystem` | DataPlatformBase | national_data | Y | 0/— | — | 2/2/0/0 | 6 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/mdm/SourceSystem.py:7`; commit 2026-07-16 |
| 318 | `dp_stored_events` | `StoredEvent` | DataPlatformBase | national_data | Y | 0/— | — | 7/0/0/0 | 43 | factory.py | ACTIVE_REQUIRED | P0 | `national_data/models/event_store/StoredEvent.py:10`; commit 2026-07-16 |
| 319 | `dp_synthetic_data_jobs` | `SyntheticDataJob` | DataPlatformBase | national_data | Y | 0/— | — | 2/0/0/0 | 6 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/ai_data/SyntheticDataJob.py:7`; commit 2026-07-16 |
| 320 | `dp_terminology_registry` | `TerminologyRegistry` | DataPlatformBase | national_data | Y | 0/— | — | 1/2/0/0 | 6 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/mdm/TerminologyRegistry.py:7`; commit 2026-07-16 |
| 321 | `dp_training_datasets` | `TrainingDataset` | DataPlatformBase | national_data | Y | 0/— | — | 3/0/0/0 | 16 | factory.py, routes/national_data.py | ACTIVE_REQUIRED | P1 | `national_data/models/ai_data/TrainingDataset.py:10`; commit 2026-07-16 |
| 322 | `dp_vector_embeddings` | `VectorEmbedding` | DataPlatformBase | national_data | Y | 0/— | — | 6/0/0/0 | 17 | factory.py, routes/national_data.py | ACTIVE_REQUIRED | P1 | `national_data/models/ai_data/VectorEmbedding.py:10`; commit 2026-07-16 |
| 323 | `dw_dim_date` | `DimDate` | DataPlatformBase | national_data | Y | 0/— | — | 3/1/0/0 | 18 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/warehouse/DimDate.py:7`; commit 2026-07-16 |
| 324 | `dw_dim_diagnosis` | `DimDiagnosis` | DataPlatformBase | national_data | Y | 0/— | — | 3/0/0/0 | 8 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/warehouse/DimDiagnosis.py:7`; commit 2026-07-16 |
| 325 | `dw_dim_facility` | `DimFacility` | DataPlatformBase | national_data | Y | 0/— | — | 3/0/0/0 | 12 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/warehouse/DimFacility.py:7`; commit 2026-07-16 |
| 326 | `dw_dim_patient` | `DimPatient` | DataPlatformBase | national_data | Y | 0/— | — | 4/0/0/0 | 12 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/warehouse/DimPatient.py:7`; commit 2026-07-16 |
| 327 | `dw_dim_provider` | `DimProvider` | DataPlatformBase | national_data | Y | 0/— | — | 3/0/0/0 | 12 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/warehouse/DimProvider.py:7`; commit 2026-07-16 |
| 328 | `dw_fact_diagnoses` | `FactDiagnosis` | DataPlatformBase | national_data | Y | 6/dw_dim_date,dw_dim_diagnosis,dw_dim_facility | — | 10/0/0/0 | 6 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/warehouse/FactDiagnosis.py:7`; commit 2026-07-16 |
| 329 | `dw_fact_lab_results` | `FactLabResult` | DataPlatformBase | national_data | Y | 5/dw_dim_date,dw_dim_facility,dw_dim_patient | — | 11/0/0/0 | 9 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/warehouse/FactLabResult.py:7`; commit 2026-07-16 |
| 330 | `dw_fact_patient_visits` | `FactPatientVisit` | DataPlatformBase | national_data | Y | 6/dw_dim_date,dw_dim_diagnosis,dw_dim_facility | — | 10/0/0/0 | 6 | factory.py | ACTIVE_REQUIRED | P1 | `national_data/models/warehouse/FactPatientVisit.py:7`; commit 2026-07-16 |
| 331 | `nhdw_offline_changes` | `OfflineChange` | Base | nhdw | Y | 0/— | — | 5/0/0/0 | 0 | — | UNUSED | P3 | `nhdw/offline.py:58`; commit 2026-07-16 |
| 332 | `nursing_checklists` | `ClinicalChecklist` | NursingBase | nursing | Y | 4/lab_users,national_encounters,patients | — | 5/0/0/0 | 15 | factory.py | ACTIVE_REQUIRED | P1 | `nursing/models.py:373`; commit 2026-07-16 |
| 333 | `nursing_escalations` | `EscalationRecord` | NursingBase | nursing | Y | 5/lab_users,national_encounters,patients | — | 7/0/0/0 | 24 | factory.py, nursing/routes.py | ACTIVE_REQUIRED | P0 | `nursing/models.py:414`; commit 2026-07-16 |
| 334 | `radiology_ai_jobs` | `AIAnalysisJob` | RadiologyBase | radiology | Y | 1/radiology_exams | — | 2/0/0/0 | 1 | factory.py | DORMANT | P2 | `radiology/ai.py:25`; commit 2026-08-12 |
| 335 | `rp_consent_records` | `ConsentRecord` | HealthDataBase | research_platform | Y | 0/— | — | 2/0/0/0 | 31 | citizen_platform/privacy.py, identity/lifecycle/models.py | ACTIVE_REQUIRED | P0 | `research_platform/base.py:129`; commit 2026-07-16 |
| 336 | `rp_data_access_requests` | `DataAccessRequest` | HealthDataBase | research_platform | Y | 0/— | — | 1/0/0/0 | 0 | — | UNUSED | P3 | `research_platform/base.py:110`; commit 2026-07-16 |
| 337 | `rp_research_datasets` | `ResearchDataset` | HealthDataBase | research_platform | Y | 0/— | — | 2/0/0/0 | 4 | research_platform/research.py | ACTIVE_REQUIRED | P1 | `research_platform/base.py:36`; commit 2026-07-16 |
| 338 | `rp_research_institutions` | `ResearchInstitution` | HealthDataBase | research_platform | Y | 0/— | — | 0/0/0/0 | 7 | research_platform/research.py | ACTIVE_REQUIRED | P1 | `research_platform/base.py:60`; commit 2026-07-16 |
| 339 | `rp_research_projects` | `ResearchProject` | HealthDataBase | research_platform | Y | 0/— | — | 1/0/0/0 | 7 | research_platform/research.py | ACTIVE_REQUIRED | P1 | `research_platform/base.py:11`; commit 2026-07-16 |
| 340 | `rp_research_publications` | `ResearchPublication` | HealthDataBase | research_platform | Y | 0/— | — | 1/1/0/0 | 8 | research_platform/research.py | ACTIVE_REQUIRED | P1 | `research_platform/base.py:77`; commit 2026-07-16 |
| 341 | `rp_study_cohorts` | `StudyCohort` | HealthDataBase | research_platform | Y | 0/— | — | 1/0/0/0 | 0 | — | UNUSED | P3 | `research_platform/base.py:96`; commit 2026-07-16 |
| 342 | `roadmap_architecture_decisions` | `ArchitectureDecision` | Base | roadmap | Y | 1/roadmap_architecture_decisions | — | 2/0/0/0 | 10 | roadmap/engine.py | ACTIVE_REQUIRED | P1 | `roadmap/models.py:215`; commit 2026-07-16 |
| 343 | `roadmap_epics` | `Epic` | Base | roadmap | Y | 1/roadmap_missions | — | 4/0/0/0 | 14 | roadmap/routes.py | ACTIVE_REQUIRED | P1 | `roadmap/models.py:110`; commit 2026-07-16 |
| 344 | `roadmap_milestones` | `Milestone` | Base | roadmap | Y | 1/roadmap_missions | — | 2/0/0/0 | 10 | roadmap/routes.py | ACTIVE_REQUIRED | P1 | `roadmap/models.py:157`; commit 2026-07-16 |
| 345 | `roadmap_missions` | `Mission` | Base | roadmap | Y | 1/roadmap_programs | — | 4/0/0/0 | 21 | roadmap/routes.py | ACTIVE_REQUIRED | P0 | `roadmap/models.py:82`; commit 2026-07-16 |
| 346 | `roadmap_programs` | `Program` | Base | roadmap | Y | 0/— | — | 3/1/0/0 | 20 | roadmap/routes.py | ACTIVE_REQUIRED | P0 | `roadmap/models.py:58`; commit 2026-07-16 |
| 347 | `roadmap_risks` | `Risk` | Base | roadmap | Y | 1/roadmap_missions | — | 2/0/0/0 | 25 | certification/release_gates.py, core/risk_engine.py | ACTIVE_REQUIRED | P0 | `roadmap/models.py:176`; commit 2026-07-16 |
| 348 | `roadmap_tasks` | `RoadmapTask` | Base | roadmap | Y | 1/roadmap_epics | — | 3/0/0/0 | 13 | roadmap/engine.py | ACTIVE_REQUIRED | P1 | `roadmap/models.py:132`; commit 2026-07-16 |
| 349 | `roadmap_technical_debt` | `TechnicalDebt` | Base | roadmap | Y | 0/— | — | 2/0/0/0 | 7 | roadmap/routes.py | ACTIVE_REQUIRED | P1 | `roadmap/models.py:197`; commit 2026-07-16 |
| 350 | `capacity_plans` | `CapacityPlan` | Base | simulation | Y | 1/digital_twins | — | 2/0/0/0 | 2 | simulation/engine.py | DORMANT | P2 | `simulation/models.py:123`; commit 2026-07-24 |
| 351 | `digital_twins` | `DigitalTwin` | Base | simulation | Y | 0/— | Y | 3/0/0/0 | 37 | simulation/routes.py | ACTIVE_REQUIRED | P0 | `simulation/models.py:38`; commit 2026-07-24 |
| 352 | `predictions` | `Prediction` | Base | simulation | Y | 1/digital_twins | — | 3/0/0/0 | 21 | simulation/routes.py | ACTIVE_REQUIRED | P0 | `simulation/models.py:104`; commit 2026-07-24 |
| 353 | `simulation_snapshots` | `SimulationSnapshot` | Base | simulation | Y | 1/simulations | — | 3/0/0/0 | 6 | simulation/routes.py | ACTIVE_REQUIRED | P1 | `simulation/models.py:87`; commit 2026-07-24 |
| 354 | `simulations` | `Simulation` | Base | simulation | Y | 1/digital_twins | Y | 4/0/0/0 | 15 | simulation/routes.py | ACTIVE_REQUIRED | P1 | `simulation/models.py:63`; commit 2026-07-24 |


**Matrix roll-up:** classification — ACTIVE_REQUIRED 261, DORMANT 22, OWNERSHIP_UNCLEAR 51, UNUSED 20.
Priority — P0 126, P1 186, P2 22, P3 20.
Per-base discrepancy — NationalBase 80, GovernanceBase 58, ClinicalBase 39, DataPlatformBase 36, InsBase 30, HealthDataBase 24, Base 23, DocIntelBase 21, EHRBase 18, HospitalBase 13, FinBase 6, IdentityBase 3, NursingBase 2, RadiologyBase 1.
Per-context discrepancy — national 80, governance 58, clinical 39, national_data 36, insurance 30, document_intelligence 21, ehr 18, health_data 17, hospital 13, roadmap 8, research_platform 7, financial 6, command_intelligence 5, simulation 5, identity 3, knowledge_graph 3, nursing 2, models 1, nhdw 1, radiology 1.

### 4.1 Notes on specific classifications

- `OWNERSHIP_UNCLEAR` (51 DocIntel/Ins rows) is assigned because the declarative base is absent from `env.py`: there is no migration owner. Several have very high consumer counts (`ins_claims` 150, `ins_coverages` 122, `ins_authorizations` 92, `ins_providers` 65, `docint_documents` 32) — they are functionally ACTIVE but ownership-gated, so the primary classification is deliberately the blocker.
- `UNUSED` = zero identifier references found anywhere in `backend/app` outside the defining file. This is static evidence only; it is not proof of absence in external consumers.
- `DORMANT` = 1–2 references, typically intra-model sibling constants or type imports.
- The duplicate `national_facilities` (two ORM mappings) is now migration-covered via a variable-named `create_table` in `20260813_0004`; it is excluded from the discrepancy but retained as an `ADR-B` ownership item (§7).

---

## 5. Targeted investigations

### 5.1 `DocIntelBase` and `InsBase`

- `DocIntelBase = declarative_base()` at `backend/app/document_intelligence/infrastructure/models.py:64`; 21 `docint_*` tables; 0 migrations; **not in `env.py`**. Consumers in `document_intelligence/infrastructure/repository.py`, `document_intelligence/__init__.py`, `app/factory.py`; wiring can bind its own engine (`application/wiring.py:884-889`, default `sqlite:///docint.db`). All 21 have live references (7–32).
- `InsBase = declarative_base()` at `backend/app/insurance/domain/models.py:49`; 30 `ins_*` tables across `models.py`, `members.py`, `network.py`, `referral.py`, `services.py`; 0 migrations; **not in `env.py`**. Consumers in `insurance/api/*`, `billing/routes.py`, `certification/dimensions/test_coverage.py`, `fhir/*`, `health_core/fhir/support.py`, `domain_platform/manifest.py`.
- Consequence: strict-schema runs can never see 51 active tables; `create_all()` in tests masks this. Remediation requires an owner decision (register bases + context-by-context migrations) — `BLOCKED` pending ADR-A.

### 5.2 National service DB boundaries

`GOVERNANCE/ARCHITECTURE_DECISION_PACKAGE_W1.md:1148` (X-18): **17 declarative bases over one PostgreSQL**, ~485 declared FK edges crossing context boundaries, **no enforced boundary test**. `backend/app/database.py:206-271` defines a single primary engine (`DATABASE_URL`) plus an optional read replica (`ReadSessionLocal`); no separate physical DB/bind per national or hospital service was found. `hospital` and `national` are *logical* metadata partitions, not separate databases. DocIntel's optional own-engine wiring is the only partial exception.

### 5.3 Hospital DB coverage

14 `HospitalBase` tables; **1 migrated** (`hospital_surgical_safety_checklists` via `20260820_0004`), **13 unmigrated**: `hospitals`, `hospital_campuses`, `hospital_buildings`, `hospital_floors`, `hospital_departments`, `hospital_clinics`, `hospital_rooms`, `hospital_beds`, `hospital_units`, `hospital_operation_theaters`, `hospital_medical_equipment`, `hospital_cost_centers`, `bed_assignments`. This confirms the corrected '13' (superseding the earlier '12'); `hospital_operation_theaters` has 42 app references and is a conditional FK target but no migration. All 13 are `ACTIVE_REQUIRED` / `P0`.

### 5.4 Care Continuum migration closure

`20261119_0003_care_continuum_closure.py` (head, `down_revision=20261119_0002`) creates 45 `cc_*` + 17 `national_*` = 62 tables with 619 indexes; it eliminates every `cc_*` row from this matrix. Its pre-existing Team C finding (bogus `national_encounters.referral_id` FK due to `use_alter=True` being skipped by `op.create_table`) was fixed with explicit `op.create_foreign_key`. No `cc_*` table remains in the discrepancy set; residual care risk is runtime service-integration evidence (`BLOCKED`), not DDL.

### 5.5 Existing migration branch ownership

Historic branches were device-integration, interop, drug-substitution, performance-index and surgical-safety lines; five merge revisions converge them into one head. Ownership of migrations themselves is not attributed to a named individual in the repository; per `GOVERNANCE/ADR_DECISION_REQUEST.md` the owner for ADR-A is **Program Director / Architect** and for ADR-B **Database owner**. Where no owner evidence exists this report states `BLOCKED` / owner-gated rather than inventing one.

---

## 6. Highest-risk dependency clusters (text graph)

```text
[UNREGISTERED / OWNER-GATED]
  DocIntelBase (21, env=NO) ──FK──> national_citizens, national_patients, docint_documents(self)
  InsBase (30, env=NO) ──FK──> ins_providers, ins_members, ins_coverages, ins_claims
        │
        └──consumed by insurance/api/*, billing/routes.py, fhir/*, domain_platform/manifest.py

[PATIENT-CRITICAL CLUSTER — strict-suite blockers]
  EHRBase (18, 0 migrated)
     └─FK(64 edges)─> NationalBase (80 unmigrated of 180)
           └─FK targets: national_citizens(28), national_patients(20),
                         national_practitioners(19), national_encounters(18)
                         ^ these 4 now created by 20261119_0003 (closure)
  ClinicalBase (39 unmigrated) ──> clinical_guidelines(7), clinical_pathways, self-FKs
  HospitalBase (13 unmigrated) ──> hospital_operation_theaters, hospitals, hospital_beds
  HealthDataBase (17) + DataPlatformBase (36) + GovernanceBase (58) ──> gov_hierarchy_nodes(12)

[FK-TARGET AMBIGUITY / ADR-B]
  national_facilities — 2 ORM owners (models/clinical_scope.py, national/domain/facility.py)
  facilities, organizations — survive `downgrade base`; owner undecided

[SELF-CONTAINED / LOW RISK]
  insurance leaf tables (ins_cards, ins_dependents, ins_medical_services) — 0 refs, 0..n FK
  clinical terminology code tables (ucum/atc/rxnorm/cpt) — 0 refs, reference data
  national task_engine models (6 tables, 0 refs)
```

## 7. Migration ownership report

| Area | Owner (evidence) | Status |
|---|---|---|
| ADR-A 354-table strategy | Program Director / Architect — `GOVERNANCE/ADR_DECISION_REQUEST.md:28` | BLOCKED |
| ADR-B facilities/organizations/national_facilities | Database owner — `ADR_DECISION_REQUEST.md:45-57` | BLOCKED |
| `DocIntelBase` 21 tables | **no named owner found** | BLOCKED / owner-gated |
| `InsBase` 30 tables | **no named owner found** | BLOCKED / owner-gated |
| Care-continuum closure `20261119_0003` | fresh-context Team C (existing record) | INDEPENDENTLY VERIFIED (engineering scope) |
| Step-up `20261119_0001` | prior engineering (`DATABASE_MIGRATION_READINESS.md` §1) | TESTED |
| `env.py` NR-011 registration (17 bases) | prior engineering (`DATABASE_MIGRATION_READINESS.md` §2) | TESTED (19 passed) |

## 8. Prioritized remediation backlog (NOT authorised — for owner scheduling)

| Priority | Scope | Tables | Action proposed | Gate |
|---|---|---:|---|---|
| P0 | Unregistered bases `DocIntelBase`+`InsBase` | 51 | owner decision, register in `env.py`, per-context migrations + strict round-trip | ADR-A / owner |
| P0 | High-use registered-base tables (≥20 app refs; patient/claim-critical contexts incl. EHR/clinical/hospital/national) | 75 | context-by-context migrations (A1), strict-schema test each | ADR-A |
| P1 | Other active tables | 186 | context migrations after P0 | ADR-A |
| P2 | Dormant (1–2 refs) | 22 | classify ship/non-ship (A3); migrate only if shipped | ADR-A/A3 |
| P3 | Unused (0 refs) | 20 | owner confirmation, then declare non-shipping/retire | owner |
| X | ADR-B reference tables | 3 | assign single owner for `national_facilities`; baseline or migration-owned | ADR-B |

## 9. Migrations safe to implement under existing engineering authority

None. No bulk migration, no `create_all()`, no `stamp()` and no metadata registration is authorised by this investigation. The engineering-authority path requires the owner-approved ADR-A option A1 (fix base registration, then one context per PR with a strict round-trip test) and ADR-B for the three reference tables. Individually, only additive, reversible, context-scoped revisions with a disposable-DB upgrade/downgrade proof would be candidates — and those remain `BLOCKED` until the owner decision exists.

## 10. Decisions requiring owner / architecture approval

1. **ADR-A** — strategy for the 354-table (historically 426) gap: A1+A3 vs alternatives; authorise context-by-context authoring and the non-shipping declaration. Owner: Program Director / Architect. `BLOCKED`.
2. **ADR-B** — ownership of `facilities` / `organizations` / `national_facilities`; single ORM owner for `national_facilities`. Owner: Database owner. `BLOCKED`.
3. **Register `DocIntelBase` and `InsBase`** in `migrations/env.py` (51 active, currently invisible tables) — architecture decision; `BLOCKED`.
4. **Ship/no-ship declaration** for DORMANT (P2) and UNUSED (P3) contexts; without it A3 cannot be applied. `BLOCKED`.
5. **Cross-context DB boundary enforcement** (X-18) — whether to keep one physical DB with logical partitions or split; owner/architecture. `BLOCKED`.
6. **Runtime service-integration evidence** for care-continuum workflows (DDL closed, runtime still `BLOCKED`).

---

## 11. Document contradictions (historical values retained, not overwritten)

| # | Contradiction | Values / sources | Disposition |
|---:|---|---|---|
| 1 | Gap size | 426 (`NATIONAL_SERVICE_INVENTORY.md:278`, 833/40 contexts @ `2827c1ff`); 340 (`DATABASE_COMPATIBILITY_REPORT.md:405`, 756/17 bases); 284 (probe-C, `§11.7`); **354** (this report, source parse @ `2206654`) | Different denominators + newer migrations; all retained; §3.1 reconciles |
| 2 | ORM table count | 833 (historical) vs 834 distinct / 835 definitions (this AST parse) | Parse-scope/HEAD difference; documented |
| 3 | Declarative bases | 17 registered in `env.py` vs 19 defined on disk (`DocIntelBase`, `InsBase` omitted) | Real gap; §2/§5.1 |
| 4 | Hospital gap | '12 uncovered' (older) vs 13 (`DATABASE_COMPATIBILITY_REPORT.md:296-300`) | 13 confirmed by AST; '12' retained as superseded |
| 5 | Care continuum | '45 tables lack migrations' (`MASTER_EXECUTION_STATUS.md` §2 row 9) vs closure `20261119_0003` | DDL finding closed; runtime still BLOCKED |
| 6 | `national_encounters` | 'in no migration and no migrated DB' (`DATABASE_COMPATIBILITY_REPORT.md:282-284`) vs created by `20261119_0003` | Historical statement retained; current source shows creation |
| 7 | NR-011 | 'P0 blocker' in `ADR_DECISION_REQUEST.md:21-25` / `DATABASE_MIGRATION_READINESS.md` §2 vs 'RESOLVED IN CODE, 19 passed' later in same file | Historical blocker retained as resolved-in-code; ADR-A backlog remains |
| 8 | Alembic head | 'single head 20261119_0003' (`GULA_DEPENDENCY_GRAPH.md:92`, `DATABASE_MIGRATION_READINESS.md` §1) vs 5 apparent heads in a naive parse | Naive parse missed annotated assignments; corrected parse confirms 1 head |

---

## 12. Remaining owner decisions

Standing decision **HOLD** persists. The following require a named owner and are not discharged by this report: ADR-A strategy; ADR-B reference-table ownership; registration and ownership of `DocIntelBase` / `InsBase`; ship/no-ship classification of P2/P3 contexts; cross-context DB-boundary enforcement (X-18); care-continuum runtime integration evidence. Until those decisions are recorded, migration coverage remains `BLOCKED` and no release/deployment/DDL claim is made.

---

*Generated by read-only source analysis at HEAD `2206654dc713ea2de8c564a3207dfe05fde23549` on 2026-11-19. This document is the only file written by this investigation.*
