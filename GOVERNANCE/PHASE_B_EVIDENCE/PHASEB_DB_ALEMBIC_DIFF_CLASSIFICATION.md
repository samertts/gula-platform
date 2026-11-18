# Phase B — Alembic diff classification (284 unmigrated ORM tables)

**Artifact owner:** DATABASE analysis agent (read-only Phase B workstream)  
**Output path:** `GOVERNANCE/PHASE_B_EVIDENCE/PHASEB_DB_ALEMBIC_DIFF_CLASSIFICATION.md`  
**Repository:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0` (verified at start)  
**Status:** `BLOCKED` — classification and proposal only; ADR-A migration strategy and the 284-table gap remain undecided.

## 1. Executive summary

| Item | Result |
|---|---|
| Evidence source | **Live disposable PostgreSQL 16.14 database** (`gula_phaseb_diff_verify`), not static analysis |
| `alembic upgrade head` | exit **0** |
| `alembic check` | exit **255** (non-zero: drift detected); full output captured under `/tmp/opencode/phaseb_db_diff/` |
| Distinct missing-table differences | **284** (`add_table` operations, 284 occurrences / 284 distinct names, identical on the `ERROR` and `FAILED` lines) |
| `NoReferencedTableError` markers | **0** |
| `Traceback` markers | **0** |
| Tables already present in the disposable DB / present as views | **0 / 0** |
| FK targets missing from both the gap set and the migrated DB | **0** |
| Migration-history mentions among the 284 | **3** (all NR-009 *conditional FK* guards, not table creations) |
| Other drift operation classes | see §7 — **not** part of the 284-table classification |
| Operational / production DB touched | **NO** — disposable DB created and dropped in this session |

The prior-cycle figure of **284** is reproduced exactly. NR-011 (17 registered bases + merged `MetaData`) is present in `backend/migrations/env.py`; this work did **not** duplicate, modify or re-test it.

## 2. Evidence and reproduction

Toolchain: `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python` (Python 3.12.13) and `alembic` 1.18.5. Running from `gula-integration/backend` requires `PYTHONPATH=/home/samertts/workspace/projects/gula-integration` so that top-level `shared/` resolves.

```bash
# 1. create a uniquely named disposable DB (PG at 172.18.0.2:5432)
PGPASSWORD=*** createdb -h 172.18.0.2 -p 5432 -U postgres gula_phaseb_diff_verify

# 2. apply the full chain
cd /home/samertts/workspace/projects/gula-integration/backend
PYTHONPATH=/home/samertts/workspace/projects/gula-integration \
  DATABASE_URL='postgresql://postgres:***@172.18.0.2:5432/gula_phaseb_diff_verify' \
  /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/alembic upgrade head
# -> exit 0

# 3. capture the drift
PYTHONPATH=/home/samertts/workspace/projects/gula-integration \
  DATABASE_URL='postgresql://postgres:***@172.18.0.2:5432/gula_phaseb_diff_verify' \
  /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/alembic check \
  > /tmp/opencode/phaseb_db_diff/alembic_check.log 2>&1
# -> exit 255; 284 add_table ops; 0 NoReferencedTableError; 0 Traceback

# 4. teardown
PGPASSWORD=*** dropdb -h 172.18.0.2 -p 5432 -U postgres gula_phaseb_diff_verify
```

Live-DB cross-checks (`information_schema.tables`, read-only): 433 objects in the migrated clone, **0** of the 284 names present, **0** views, **0** non-default ORM schemas declared in the diff.

## 3. Classification rules (deterministic, first-match)

1. **RENAMED_OR_SUPERSEDED** — the table name has a plausible old/new relationship to an already-migrated table (prefix-normalised identical stem). Naming evidence only; no ownership claim is made.
2. **INTENTIONAL_SCHEMA_DIFFERENCE** — the owning module is explicitly documented as dormant and a different authoritative stack exists (`GOVERNANCE/NATIONAL_PLATFORM_STABILIZATION_REPORT.md` §63: `health_data/mdm` dormant; `app/services/mpi/` authoritative).
3. **NEEDS_OWNER_DECISION** — ADR-B/W1 ownership ambiguity, immutable audit, identity/MPI/strong identifiers, PHI-heavy analytics, consent, break-glass/privilege, NR-009 conditional FK, or analytics/DW/ODS/event-store/AI-data whose Alembic ownership is undocumented.
4. **MISSING_MIGRATION_HISTORY** — all remaining additive ORM tables: no migration mention, no documented intentional exclusion, no safety-specific marker. Candidate for a new forward migration, subject to ADR-A scope approval.

Ordinary clinical tables that merely carry a `patient_id` foreign key are **not** automatically escalated: adding an empty table is non-destructive. Escalation requires an explicit governance or strong-identifier marker as listed above.

## 4. Category summary (reconciles to 284)

| Category | Count | Proposed action |
|---|---:|---|
| MISSING_MIGRATION_HISTORY | 191 | CREATE_FORWARD (after ADR-A scope approval) |
| INTENTIONAL_SCHEMA_DIFFERENCE | 5 | DOCUMENT_INTENTIONAL |
| RENAMED_OR_SUPERSEDED | 6 | INVESTIGATE |
| NEEDS_OWNER_DECISION | 82 | DEFER_TO_OWNER |
| **TOTAL** | **284** | — |

## 5. Classified inventory (every one of the 284 differences)

Repeated patterns are grouped into a single row with an explicit count; the table-name column lists every member. Counts sum to 284.

| # | Category | Tables (count) | Owning module / domain | Dependency / FK notes | Destructive risk | Proposed action |
|---:|---|---|---|---|---|---|
| 1 | **RENAMED_OR_SUPERSEDED**<br/>Plausible old/new naming overlap with an already-migrated table (naming evidence only; owner confirmation required) | (6) `clinical_protocols`, `ehr_care_plans`, `fin_invoices`, `gov_delegations`, `gov_roles`, `hospital_departments` — pairs: `clinical_protocols` → existing `radiology_protocols`; `ehr_care_plans` → existing `nhdw_care_plans`; `fin_invoices` → existing `pay_invoices`; `gov_delegations` → existing `delegations`; `gov_roles` → existing `roles / niam_roles`; `hospital_departments` → existing `lims_departments` | `backend/app/clinical/knowledge/models.py`, `backend/app/ehr/models/care_plan.py`, `backend/app/financial/models.py`, `backend/app/governance/models/hierarchy.py`, `backend/app/hospital/models/__init__.py` | 10 FK edge(s): 9 to gap-set tables, 1 to already-migrated tables, 0 unresolved | **YES** — possible dual ownership / name collision with an existing migrated table | INVESTIGATE — `clinical_protocols`→`radiology_protocols`; `ehr_care_plans`→`nhdw_care_plans`; `fin_invoices`→`pay_invoices`; `gov_delegations`→`delegations`; `gov_roles`→`roles / niam_roles`; `hospital_departments`→`lims_departments` |
| 2 | **INTENTIONAL_SCHEMA_DIFFERENCE**<br/>Documented dormant `health_data/mdm` stack — authoritative identity stack is `app/services/mpi/` | (5) `hd_mdm_facility_index`, `hd_mdm_organization_index`, `hd_mdm_patient_index`, `hd_mdm_provider_index`, `hd_mdm_source_references` | `backend/app/health_data/mdm/models.py` | 1 FK edge(s): 1 to gap-set tables, 0 to already-migrated tables, 0 unresolved | **YES** — carries patient/provider index data (PHI) although dormant; document, never auto-migrate | DOCUMENT_INTENTIONAL |
| 3 | **NEEDS_OWNER_DECISION**<br/>ADR-B / W1 `duplicate` / `unresolved_ownership` set — ownership undecided | (4) `hospitals`, `national_hospitals`, `national_identity_resolutions`, `national_organizations` | `backend/app/hospital/models/__init__.py`, `backend/app/national/domain/hospital.py`, `backend/app/national/domain/identity_resolution.py`, `backend/app/national/domain/organization.py` | 3 FK edge(s): 2 to gap-set tables, 1 to already-migrated tables, 0 unresolved | **YES** — safety-sensitive / ownership-ambiguous; DDL must not be auto-generated or auto-applied | DEFER_TO_OWNER |
| 4 | **NEEDS_OWNER_DECISION**<br/>Immutable audit / security-event table — append-only, hash-chain / evidentiary concerns | (6) `clinical_audit_records`, `gov_ai_audit_events`, `gov_health_number_audit`, `gov_national_audit_events`, `national_identity_audit_logs`, `national_merge_audit` | `backend/app/clinical/quality/models.py`, `backend/app/governance/models/ai.py`, `backend/app/governance/models/health_number.py`, `backend/app/governance/models/security.py`, `backend/app/national/domain/audit_identity.py`, `backend/app/national/domain/merge_record.py` | 4 FK edge(s): 4 to gap-set tables, 0 to already-migrated tables, 0 unresolved | **YES** — safety-sensitive / ownership-ambiguous; DDL must not be auto-generated or auto-applied | DEFER_TO_OWNER |
| 5 | **NEEDS_OWNER_DECISION**<br/>Identity / MPI / strong-identifier / PHI-bearing table | (21) `dp_duplicate_records`, `dp_golden_records`, `dp_merge_actions`, `dp_provider_registry`, `gov_health_numbers`, `gov_healthcare_workers`, `gov_merged_identities`, `national_biometrics`, `national_citizens`, `national_death_records`, `national_employees`, `national_foreigners`, `national_guardians`, `national_health_number_sequences`, `national_identifier_mappings`, `national_merge_records`, `national_newborns`, `national_patients`, `national_practitioners`, `national_unknown_patients`, `national_visitors` | `backend/app/governance/models/health_number.py`, `backend/app/governance/models/workforce.py`, `backend/app/national/domain/biometrics.py`, `backend/app/national/domain/citizen.py`, `backend/app/national/domain/death_record.py`, `backend/app/national/domain/employee.py`, `backend/app/national/domain/foreigner.py`, `backend/app/national/domain/guardian.py`, `backend/app/national/domain/health_number.py`, `backend/app/national/domain/merge_record.py`, `backend/app/national/domain/national_id.py`, `backend/app/national/domain/newborn.py`, `backend/app/national/domain/patient.py`, `backend/app/national/domain/practitioner.py`, `backend/app/national/domain/unknown_patient.py`, `backend/app/national/domain/visitor.py`, `backend/app/national_data/models/mdm/DuplicateRecord.py`, `backend/app/national_data/models/mdm/GoldenRecord.py`, `backend/app/national_data/models/mdm/MergeAction.py`, `backend/app/national_data/models/mdm/ProviderRegistry.py` | 22 FK edge(s): 17 to gap-set tables, 5 to already-migrated tables, 0 unresolved | **YES** — safety-sensitive / ownership-ambiguous; DDL must not be auto-generated or auto-applied | DEFER_TO_OWNER |
| 6 | **NEEDS_OWNER_DECISION**<br/>Consent / directive table — legal and clinical-safety sensitivity | (2) `dp_consent_directives`, `national_consents` | `backend/app/national/domain/consent.py`, `backend/app/national_data/models/governance/ConsentDirective.py` | 4 FK edge(s): 2 to gap-set tables, 2 to already-migrated tables, 0 unresolved | **YES** — safety-sensitive / ownership-ambiguous; DDL must not be auto-generated or auto-applied | DEFER_TO_OWNER |
| 7 | **NEEDS_OWNER_DECISION**<br/>Break-glass / temporary-admin / privilege policy table | (5) `gov_break_glass_policies`, `gov_emergency_admin`, `gov_security_policies`, `gov_temporary_admin`, `gov_worker_privileges` | `backend/app/governance/models/hierarchy.py`, `backend/app/governance/models/security.py`, `backend/app/governance/models/workforce.py` | 3 FK edge(s): 3 to gap-set tables, 0 to already-migrated tables, 0 unresolved | **YES** — safety-sensitive / ownership-ambiguous; DDL must not be auto-generated or auto-applied | DEFER_TO_OWNER |
| 8 | **NEEDS_OWNER_DECISION**<br/>NR-009 conditional-FK target — migration already contains a guarded FK hook | (1) `hospital_operation_theaters` | `backend/app/hospital/models/__init__.py` | 2 FK edge(s): 2 to gap-set tables, 0 to already-migrated tables, 0 unresolved | **YES** — safety-sensitive / ownership-ambiguous; DDL must not be auto-generated or auto-applied | DEFER_TO_OWNER |
| 9 | **NEEDS_OWNER_DECISION**<br/>Analytics / DW / ODS / event-store / AI-data table with no documented Alembic ownership decision | (43) `dp_data_catalog`, `dp_data_classifications`, `dp_data_lineage`, `dp_data_quality_checks`, `dp_data_quality_rules`, `dp_data_stewards`, `dp_deidentification_jobs`, `dp_device_registry`, `dp_event_retention_policies`, `dp_event_snapshots`, `dp_feature_store`, `dp_feature_values`, `dp_knowledge_graph_edges`, `dp_knowledge_graph_nodes`, `dp_location_registry`, `dp_metadata_registry`, `dp_retention_policies`, `dp_source_systems`, `dp_stored_events`, `dp_synthetic_data_jobs`, `dp_terminology_registry`, `dp_training_datasets`, `dp_vector_embeddings`, `dw_dim_date`, `dw_dim_diagnosis`, `dw_dim_facility`, `dw_dim_patient`, `dw_dim_provider`, `dw_fact_diagnoses`, `dw_fact_lab_results`, `dw_fact_patient_visits`, `hd_ods_encounter_summary`, `hd_ods_lab_result_summary`, `hd_ods_order_summary`, `hd_ods_patient_summary`, `hd_wh_dim_date`, `hd_wh_dim_facility`, `hd_wh_dim_lab_test`, `hd_wh_dim_patient`, `hd_wh_dim_provider`, `hd_wh_fact_encounter`, `hd_wh_fact_lab_result`, `hd_wh_fact_order` | `backend/app/health_data/ods/models.py`, `backend/app/health_data/warehouse/models.py`, `backend/app/national_data/models/ai_data/DeidentificationJob.py`, `backend/app/national_data/models/ai_data/FeatureStore.py`, `backend/app/national_data/models/ai_data/FeatureValue.py`, `backend/app/national_data/models/ai_data/KnowledgeGraphEdge.py`, `backend/app/national_data/models/ai_data/KnowledgeGraphNode.py`, `backend/app/national_data/models/ai_data/SyntheticDataJob.py`, `backend/app/national_data/models/ai_data/TrainingDataset.py`, `backend/app/national_data/models/ai_data/VectorEmbedding.py`, `backend/app/national_data/models/event_store/EventRetentionPolicy.py`, `backend/app/national_data/models/event_store/EventSnapshot.py`, `backend/app/national_data/models/event_store/StoredEvent.py`, `backend/app/national_data/models/governance/DataCatalogEntry.py`, `backend/app/national_data/models/governance/DataClassification.py`, `backend/app/national_data/models/governance/DataLineageEntry.py`, `backend/app/national_data/models/governance/DataQualityCheck.py`, `backend/app/national_data/models/governance/DataQualityRule.py`, `backend/app/national_data/models/governance/DataSteward.py`, `backend/app/national_data/models/governance/MetadataEntry.py`, `backend/app/national_data/models/governance/RetentionPolicy.py`, `backend/app/national_data/models/mdm/DeviceRegistry.py`, `backend/app/national_data/models/mdm/LocationRegistry.py`, `backend/app/national_data/models/mdm/SourceSystem.py`, `backend/app/national_data/models/mdm/TerminologyRegistry.py`, `backend/app/national_data/models/warehouse/DimDate.py`, `backend/app/national_data/models/warehouse/DimDiagnosis.py`, `backend/app/national_data/models/warehouse/DimFacility.py`, `backend/app/national_data/models/warehouse/DimPatient.py`, `backend/app/national_data/models/warehouse/DimProvider.py`, `backend/app/national_data/models/warehouse/FactDiagnosis.py`, `backend/app/national_data/models/warehouse/FactLabResult.py`, `backend/app/national_data/models/warehouse/FactPatientVisit.py` | 24 FK edge(s): 17 to gap-set tables, 7 to already-migrated tables, 0 unresolved | **YES** — safety-sensitive / ownership-ambiguous; DDL must not be auto-generated or auto-applied | DEFER_TO_OWNER |
| 10 | **MISSING_MIGRATION_HISTORY**<br/>Care-continuum model family (`cc_*`), 0% migrated — plain additive ORM table | (45) `cc_antenatal_care_visits`, `cc_breastfeeding_records`, `cc_care_coordination`, `cc_care_journeys`, `cc_child_development_records`, `cc_chronic_disease_registry`, `cc_clinical_handovers`, `cc_clinical_pathway_enrollments`, `cc_cold_chain_monitors`, `cc_community_care_records`, `cc_community_clinic_records`, `cc_community_visits`, `cc_contraindications`, `cc_cross_org_referrals`, `cc_delivery_records`, `cc_disease_management_plans`, `cc_educational_material_assignments`, `cc_family_medicine_records`, `cc_follow_up_plans`, `cc_growth_monitoring`, `cc_health_assessments`, `cc_health_programs`, `cc_health_promotion_activities`, `cc_home_care_plans`, `cc_immunization_schedules`, `cc_occupational_health_records`, `cc_patient_tasks`, `cc_postnatal_care_visits`, `cc_pregnancy_records`, `cc_preventive_care_records`, `cc_primary_care_encounters`, `cc_program_enrollments`, `cc_referral_attachments`, `cc_referral_requests`, `cc_referral_responses`, `cc_referral_timelines`, `cc_reminder_schedules`, `cc_risk_stratification`, `cc_school_health_visits`, `cc_screening_campaigns`, `cc_self_follow_up_tasks`, `cc_self_monitoring_records`, `cc_transitions_of_care`, `cc_vaccination_records`, `cc_vaccine_inventory` | `backend/app/care_continuum/models/care_journey.py`, `backend/app/care_continuum/models/chronic_disease.py`, `backend/app/care_continuum/models/immunization.py`, `backend/app/care_continuum/models/maternal.py`, `backend/app/care_continuum/models/patient_tasks.py`, `backend/app/care_continuum/models/primary_care.py`, `backend/app/care_continuum/models/public_health.py`, `backend/app/care_continuum/models/referral.py` | 227 FK edge(s): 188 to gap-set tables, 39 to already-migrated tables, 0 unresolved | NO — additive `CREATE TABLE` only; no drop, rename or alter of existing objects | CREATE_FORWARD |
| 11 | **MISSING_MIGRATION_HISTORY**<br/>National domain / scheduling model family — plain additive ORM table | (32) `national_addresses`, `national_admissions`, `national_appointments`, `national_attachments`, `national_clinics`, `national_communications`, `national_coverages`, `national_departments`, `national_directorates`, `national_discharges`, `national_emergency_contacts`, `national_encounters`, `national_episodes_of_care`, `national_families`, `national_family_members`, `national_health_cards`, `national_insurances`, `national_laboratories`, `national_medication_catalog`, `national_observations`, `national_providers`, `national_referrals`, `national_residents`, `national_scheduling_appointment_reminders`, `national_scheduling_appointments`, `national_scheduling_calendars`, `national_scheduling_resources`, `national_scheduling_schedules`, `national_scheduling_time_slots`, `national_scheduling_waiting_list`, `national_visits`, `national_wards` | `backend/app/national/domain/address.py`, `backend/app/national/domain/admission.py`, `backend/app/national/domain/appointment.py`, `backend/app/national/domain/attachments.py`, `backend/app/national/domain/clinic.py`, `backend/app/national/domain/communication.py`, `backend/app/national/domain/coverage.py`, `backend/app/national/domain/department.py`, `backend/app/national/domain/directorate.py`, `backend/app/national/domain/discharge.py`, `backend/app/national/domain/emergency_contact.py`, `backend/app/national/domain/encounter.py`, `backend/app/national/domain/episode_of_care.py`, `backend/app/national/domain/family.py`, `backend/app/national/domain/health_card.py`, `backend/app/national/domain/insurance.py`, `backend/app/national/domain/laboratory.py`, `backend/app/national/domain/medication_catalog.py`, `backend/app/national/domain/observation.py`, `backend/app/national/domain/provider.py`, `backend/app/national/domain/referral.py`, `backend/app/national/domain/resident.py`, `backend/app/national/domain/visit.py`, `backend/app/national/domain/ward.py`, `backend/app/national/scheduling_platform/infrastructure/models.py` | 69 FK edge(s): 58 to gap-set tables, 11 to already-migrated tables, 0 unresolved | NO — additive `CREATE TABLE` only; no drop, rename or alter of existing objects | CREATE_FORWARD |
| 12 | **MISSING_MIGRATION_HISTORY**<br/>Governance model family (`gov_*`) — plain additive ORM table | (45) `gov_acting_appointments`, `gov_ai_guardrails`, `gov_ai_model_validations`, `gov_ai_risk_classifications`, `gov_analyzer_registry`, `gov_approval_policies`, `gov_attendance_records`, `gov_board_certifications`, `gov_calibration_records`, `gov_canonical_mappings`, `gov_clinical_policies`, `gov_competency_assessments`, `gov_consultation_policies`, `gov_critical_result_policies`, `gov_data_classification`, `gov_delta_check_policies`, `gov_digital_certificates`, `gov_eqa_records`, `gov_equipment_registry`, `gov_health_cards`, `gov_hierarchy_nodes`, `gov_incidents`, `gov_interop_protocols`, `gov_laboratory_registry`, `gov_llm_policies`, `gov_maintenance_records`, `gov_master_data_agreements`, `gov_medical_guidelines`, `gov_national_panels`, `gov_national_protocols`, `gov_national_reference_labs`, `gov_national_tests`, `gov_productivity_records`, `gov_professional_licenses`, `gov_prompt_policies`, `gov_qc_records`, `gov_reagent_inventory`, `gov_reference_range_policies`, `gov_repeat_testing_policies`, `gov_risk_registry`, `gov_rotation_records`, `gov_terminology_mappings`, `gov_threat_intel`, `gov_training_records`, `gov_westgard_policies` | `backend/app/governance/models/ai.py`, `backend/app/governance/models/clinical.py`, `backend/app/governance/models/health_number.py`, `backend/app/governance/models/hierarchy.py`, `backend/app/governance/models/interoperability.py`, `backend/app/governance/models/laboratory.py`, `backend/app/governance/models/security.py`, `backend/app/governance/models/workforce.py` | 21 FK edge(s): 21 to gap-set tables, 0 to already-migrated tables, 0 unresolved | NO — additive `CREATE TABLE` only; no drop, rename or alter of existing objects | CREATE_FORWARD |
| 13 | **MISSING_MIGRATION_HISTORY**<br/>Clinical terminology / CDS / quality / knowledge model family — plain additive ORM table | (37) `clinical_alert_actions`, `clinical_alerts`, `clinical_atc_codes`, `clinical_benchmark_values`, `clinical_care_bundle_elements`, `clinical_care_bundles`, `clinical_code_systems`, `clinical_compliance_checks`, `clinical_contraindications`, `clinical_cpt_codes`, `clinical_duplicate_order_rules`, `clinical_guideline_approvals`, `clinical_guidelines`, `clinical_icd10_codes`, `clinical_icd11_codes`, `clinical_incident_reports`, `clinical_indicator_measurements`, `clinical_loinc_codes`, `clinical_mortality_reviews`, `clinical_order_set_items`, `clinical_order_sets`, `clinical_pathway_phases`, `clinical_pathways`, `clinical_patient_safety_events`, `clinical_preventive_recommendations`, `clinical_quality_indicators`, `clinical_recommendations`, `clinical_reminder_rules`, `clinical_rxnorm_codes`, `clinical_snomed_ct_codes`, `clinical_standing_orders`, `clinical_terminology_codes`, `clinical_terminology_mappings`, `clinical_terminology_versions`, `clinical_ucum_codes`, `clinical_value_set_members`, `clinical_value_sets` | `backend/app/clinical/cds/models.py`, `backend/app/clinical/knowledge/models.py`, `backend/app/clinical/quality/models.py`, `backend/app/clinical/terminology/models.py` | 18 FK edge(s): 18 to gap-set tables, 0 to already-migrated tables, 0 unresolved | NO — additive `CREATE TABLE` only; no drop, rename or alter of existing objects | CREATE_FORWARD |
| 14 | **MISSING_MIGRATION_HISTORY**<br/>EHR model family (`ehr_*`) — plain additive ORM table | (17) `ehr_allergies`, `ehr_care_plan_activities`, `ehr_care_plan_goals`, `ehr_clinical_attachments`, `ehr_clinical_notes`, `ehr_conditions`, `ehr_diagnoses`, `ehr_family_history`, `ehr_immunizations`, `ehr_medication_administrations`, `ehr_medication_dispenses`, `ehr_medication_requests`, `ehr_medication_statements`, `ehr_patient_timeline`, `ehr_problem_list_items`, `ehr_risk_factors`, `ehr_social_history` | `backend/app/ehr/models/allergy.py`, `backend/app/ehr/models/attachment.py`, `backend/app/ehr/models/care_plan.py`, `backend/app/ehr/models/clinical_note.py`, `backend/app/ehr/models/clinical_summary.py`, `backend/app/ehr/models/family_history.py`, `backend/app/ehr/models/immunization.py`, `backend/app/ehr/models/medication.py`, `backend/app/ehr/models/risk_factor.py`, `backend/app/ehr/models/social_history.py`, `backend/app/ehr/models/timeline.py` | 66 FK edge(s): 62 to gap-set tables, 4 to already-migrated tables, 0 unresolved | NO — additive `CREATE TABLE` only; no drop, rename or alter of existing objects | CREATE_FORWARD |
| 15 | **MISSING_MIGRATION_HISTORY**<br/>Hospital model family — plain additive ORM table | (10) `bed_assignments`, `hospital_beds`, `hospital_buildings`, `hospital_campuses`, `hospital_clinics`, `hospital_cost_centers`, `hospital_floors`, `hospital_medical_equipment`, `hospital_rooms`, `hospital_units` | `backend/app/hospital/models/__init__.py` | 14 FK edge(s): 14 to gap-set tables, 0 to already-migrated tables, 0 unresolved | NO — additive `CREATE TABLE` only; no drop, rename or alter of existing objects | CREATE_FORWARD |
| 16 | **MISSING_MIGRATION_HISTORY**<br/>Financial model family (`fin_*`) — plain additive ORM table | (5) `fin_invoice_items`, `fin_payables`, `fin_payments`, `fin_pricing_rules`, `fin_receivables` | `backend/app/financial/models.py` | 4 FK edge(s): 3 to gap-set tables, 1 to already-migrated tables, 0 unresolved | NO — additive `CREATE TABLE` only; no drop, rename or alter of existing objects | CREATE_FORWARD |

**Reconciliation:** 16 rows × explicit counts = **284** differences = the 284 observed `add_table` operations. No difference was omitted or double-counted.

### 5.1 Migration-history evidence for the 3 mentioned tables

- `hospital_operation_theaters` — mentioned only in `backend/migrations/versions/20260820_0004_surgical_safety_checklists.py` as a **conditional FK target guarded by a table-existence check**; no `create_table` for it exists in any migration. Not a rename; it remains MISSING_MIGRATION_HISTORY / NEEDS_OWNER_DECISION as classified above.
- `national_citizens` — mentioned only in `backend/migrations/versions/20260811_0002_citizen_relationship_foundation.py` as a **conditional FK target guarded by a table-existence check**; no `create_table` for it exists in any migration. Not a rename; it remains MISSING_MIGRATION_HISTORY / NEEDS_OWNER_DECISION as classified above.
- `national_patients` — mentioned only in `backend/migrations/versions/20260811_0002_citizen_relationship_foundation.py` as a **conditional FK target guarded by a table-existence check**; no `create_table` for it exists in any migration. Not a rename; it remains MISSING_MIGRATION_HISTORY / NEEDS_OWNER_DECISION as classified above.

## 6. Dependency-ordered migration proposal (not executed)

FK analysis of the 284 tables: 173 tables have FK edges; **0 targets are missing** from both the gap set and the migrated DB. After removing 7 self-referential hierarchies and collapsing the single mutual pair `national_encounters` ↔ `national_referrals`, the dependency graph is a DAG with 284/284 nodes orderable in 9 layers:

| Layer | Tables | Representative tables |
|---:|---:|---|
| 1 | 120 | `clinical_alerts`, `clinical_atc_codes`, `clinical_audit_records`, `clinical_code_systems`, `clinical_compliance_checks`, `clinical_contraindications`, `clinical_cpt_codes`, `clinical_duplicate_order_rules` … |
| 2 | 52 | `clinical_alert_actions`, `clinical_care_bundles`, `clinical_guideline_approvals`, `clinical_order_sets`, `clinical_preventive_recommendations`, `clinical_protocols`, `clinical_recommendations`, `clinical_pathway_phases` … |
| 3 | 33 | `clinical_care_bundle_elements`, `clinical_order_set_items`, `clinical_standing_orders`, `clinical_terminology_mappings`, `clinical_value_set_members`, `gov_attendance_records`, `gov_board_certifications`, `gov_competency_assessments` … |
| 4 | 21 | `gov_calibration_records`, `gov_qc_records`, `gov_maintenance_records`, `hospital_floors`, `cc_community_care_records`, `cc_contraindications`, `cc_pregnancy_records`, `cc_preventive_care_records` … |
| 5 | 31 | `hospital_rooms`, `cc_immunization_schedules`, `cc_breastfeeding_records`, `cc_antenatal_care_visits`, `cc_child_development_records`, `cc_community_clinic_records`, `cc_delivery_records`, `cc_family_medicine_records` … |
| 6 | 15 | `hospital_beds`, `cc_vaccination_records`, `cc_postnatal_care_visits`, `ehr_care_plan_goals`, `ehr_medication_administrations`, `ehr_medication_dispenses`, `cc_referral_requests`, `national_admissions` … |
| 7 | 9 | `bed_assignments`, `ehr_care_plan_activities`, `cc_cross_org_referrals`, `cc_referral_responses`, `cc_referral_timelines`, `national_discharges`, `cc_educational_material_assignments`, `cc_self_follow_up_tasks` … |
| 8 | 2 | `cc_referral_attachments`, `cc_transitions_of_care` |
| 9 | 1 | `cc_clinical_handovers` |

**Required sequencing:**

1. Layer 1 first (terminology, reference, governance-policy and root national tables; no gap-set FK prerequisites).
2. Layers 2–9 in ascending order; each layer's FK targets must exist before that layer is created.
3. Seven self-referential hierarchies (`cc_health_programs`, `cc_patient_tasks`, `clinical_guidelines`, `clinical_terminology_codes`, `ehr_clinical_notes`, `gov_hierarchy_nodes`, `hospital_departments`) must be created in a **two-phase** step: `CREATE TABLE` with the self-FK deferred, then `ADD CONSTRAINT`.
4. The mutual pair `national_encounters` ↔ `national_referrals` (the only non-trivial SCC) also requires two-phase FK creation.
5. Only `CREATE_FORWARD` tables from the MISSING_MIGRATION_HISTORY category enter a wave; every deferred category stays out until its owner ruling is recorded in ADR-A/ADR-B.

The full deterministic order is at `/tmp/opencode/phaseb_db_diff/topo_order.json` and per-layer membership at `/tmp/opencode/phaseb_db_diff/layers.json` (external evidence, not in-repo).

## 7. Destructive-looking changes that MUST NOT be auto-applied

These are **not** part of the 284-table classification. They are the non-`add_table` operation classes present in the same `alembic check` output. Autogenerating or applying them could drop columns, constraints, indexes or foreign keys on migrated tables:

| Operation class | Count | Scope / note |
|---|---:|---|
| `remove_index` | 1156 | index churn from type/ondelete normalisation — still a DDL drop |
| `remove_constraint` | 93 | unique-constraint drops on migrated identity/tenant tables |
| `modify_type` | 45 | includes BOOLEAN↔Integer and VARCHAR↔Enum changes on `patients`, `oauth2_*`, `trust_*`, `niam_*` |
| `remove_column` | 35 | 16 migrated tables affected (see below) |
| `modify_nullable` | 28 | 18 migrated tables affected |
| `remove_fk` | 7 | foreign-key drops |
| `add_index` | 1876 | additive, but bundled with the drops above |
| `add_column` | 34 | additive |
| `add_fk` | 8 | additive |
| `add_constraint` | 1 | additive |

`remove_column` targets (16): `blood_bank_crossmatches`, `fin_providers`, `fin_subscriptions`, `fin_transactions`, `lab_orders`, `niam_audit_entries`, `oauth2_clients`, `organizations`, `patients`, `service_accounts`, `trust_compliance_checks`, `trust_compliance_evidence`, `trust_consent_records`, `trust_retention_policies`, `trust_service_logs`, `trust_sovereignty_rules`.

`modify_type` targets (27): `ai_interactions`, `blood_bank_discards`, `blood_bank_patient_samples`, `blood_bank_reactions`, `blood_bank_reservations`, `blood_bank_returns`, `blood_bank_traceability_events`, `canonical_patients`, `citizens`, `edge_events`, `edge_tasks`, `edge_telemetry`, `fin_providers`, `fin_subscriptions`, `fin_transactions`, `medical_terminology_normalized`, `niam_audit_entries`, `oauth2_clients`, `oauth2_tokens`, `patients`, `service_accounts`, `trust_compliance_checks`, `trust_compliance_evidence`, `trust_consent_records`, `trust_retention_policies`, `trust_service_logs`, `trust_sovereignty_rules`.

`modify_nullable` targets (18): `clinical_research_cohorts`, `clinical_research_registries`, `consents`, `facilities`, `fin_providers`, `fin_subscriptions`, `fin_transactions`, `lab_orders`, `lab_users`, `labs`, `niam_audit_entries`, `niam_licenses`, `oauth2_clients`, `organizations`, `quality_controls`, `samples`, `upgrade_requests`, `users`.

**Rule:** none of these may be auto-applied. Any future revision must be reviewed table-by-table, with an explicit data-preservation and rollback decision. This is consistent with the recorded W1 decision that the 70 removal findings be triaged, never auto-applied.

## 8. Top risks

1. **Ownership ambiguity** — 4 tables (`hospitals`, `national_hospitals`, `national_organizations`, `national_identity_resolutions`) sit in the ADR-B / W1 duplicate-or-unresolved set; creating them now would cement a second owner.
2. **Immutable audit / identity / PHI** — 6 audit tables and 21 identity/strong-identifier/PHI tables need Data Steward and clinical-safety sign-off before any DDL.
3. **NR-009 conditional hooks** — `national_citizens`, `national_patients`, `hospital_operation_theaters` are FK targets of guarded migrations; creating them changes runtime behaviour of those migrations on future fresh builds.
4. **Non-reversible-looking drift** — 1,364 destructive-looking operations in the same diff (index/constraint/column/type/nullable/FK changes) must remain excluded from any forward wave.
5. **Cycle-sensitive ordering** — 8 FK-cycle roots need two-phase creation; a single bulk revision (ADR-A option A2) would be unreviewable and unsafe.
6. **Scope honesty** — the earlier 426-table figure and this measured 284 differ because of metadata/scope revisions; this report classifies only what `alembic check` actually reports **now**.

## 9. Honest boundary

- This is **classification and proposal only**. No migration revision was generated, no DDL was applied, and no source file was modified.
- Only a uniquely named disposable database (`gula_phaseb_diff_verify`) was created; it was dropped after evidence capture. **No operational or production database was touched**.
- Files under `GOVERNANCE/NATIONAL_INTEGRATION/` (frozen during independent review) and reports 13/14 were not edited. This is the only file written by this agent.
- The prior NR-011 metadata fix was verified as **present and already tested** by other work; this report neither duplicates nor re-tests it and makes no `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` claim.
- **ADR-A (migration strategy) remains `BLOCKED`** pending owner decisions on the `NEEDS_OWNER_DECISION` rows and on the destructive-looking drift; the **284-table gap remains open**.
- Status labels used here: `BLOCKED` for ADR-A and the gap; no other status label is awarded by this agent.

