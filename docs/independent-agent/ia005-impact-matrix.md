# IA-005 — impact matrix for all 137 affected models

Every mapped class whose table has a physical column named `metadata`. Measured
against the fully assembled app (780 mapped classes examined) in worktree
`/home/user/gula-audit` at `cc1dba74`+.

`physical metadata col` is `yes` for every row by construction — that is the
selection criterion. `external JSON key` is `metadata` for every row: all
serializers key by physical column name, so the fix changed no key.

Risk: **HIGH** = served endpoint + a serializer (was a reachable failure);
**MEDIUM** = serializer but no served endpoint found; **LOW** = no serializer,
unreachable by this path.

| # | model | table | physical `metadata` col | mapped attribute | serializer | endpoint exposure | external JSON key | risk |
|---|---|---|---|---|---|---|---|---|
| 1 | `AIAgentExecution` | `ai_agent_executions` | yes | `extra_metadata` | (none) | — | `metadata` | LOW |
| 2 | `AIConversationMessage` | `ai_conversation_messages` | yes | `extra_metadata` | (none) | — | `metadata` | LOW |
| 3 | `AIConversation` | `ai_conversations` | yes | `extra_metadata` | (none) | — | `metadata` | LOW |
| 4 | `AIEmbedding` | `ai_embeddings` | yes | `extra_metadata` | (none) | — | `metadata` | LOW |
| 5 | `AntenatalCareVisit` | `cc_antenatal_care_visits` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 6 | `BreastfeedingRecord` | `cc_breastfeeding_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 7 | `CareCoordination` | `cc_care_coordination` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 8 | `CareJourney` | `cc_care_journeys` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 9 | `ChildDevelopmentRecord` | `cc_child_development_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 10 | `ChronicDiseaseRegistry` | `cc_chronic_disease_registry` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 11 | `ClinicalHandover` | `cc_clinical_handovers` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 12 | `ClinicalPathwayEnrollment` | `cc_clinical_pathway_enrollments` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 13 | `ColdChainMonitor` | `cc_cold_chain_monitors` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 14 | `CommunityCareRecord` | `cc_community_care_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 15 | `CommunityClinicRecord` | `cc_community_clinic_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 16 | `CommunityVisit` | `cc_community_visits` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 17 | `Contraindication` | `cc_contraindications` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 18 | `CrossOrgReferral` | `cc_cross_org_referrals` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 19 | `DeliveryRecord` | `cc_delivery_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 20 | `DiseaseManagementPlan` | `cc_disease_management_plans` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 21 | `EducationalMaterialAssignment` | `cc_educational_material_assignments` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 22 | `FamilyMedicineRecord` | `cc_family_medicine_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 23 | `FollowUpPlan` | `cc_follow_up_plans` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 24 | `GrowthMonitoring` | `cc_growth_monitoring` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 25 | `HealthAssessment` | `cc_health_assessments` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 26 | `HealthProgram` | `cc_health_programs` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 27 | `HealthPromotionActivity` | `cc_health_promotion_activities` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 28 | `HomeCarePlan` | `cc_home_care_plans` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 29 | `ImmunizationSchedule` | `cc_immunization_schedules` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 30 | `OccupationalHealthRecord` | `cc_occupational_health_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 31 | `PatientTask` | `cc_patient_tasks` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 32 | `PostnatalCareVisit` | `cc_postnatal_care_visits` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 33 | `PregnancyRecord` | `cc_pregnancy_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 34 | `PreventiveCareRecord` | `cc_preventive_care_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 35 | `PrimaryCareEncounter` | `cc_primary_care_encounters` | yes | `metadata_` | CareContinuumBaseEntity | `/care-continuum` | `metadata` | HIGH |
| 36 | `ProgramEnrollment` | `cc_program_enrollments` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 37 | `ReferralAttachment` | `cc_referral_attachments` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 38 | `ReferralRequest` | `cc_referral_requests` | yes | `metadata_` | CareContinuumBaseEntity | `/nursing` | `metadata` | HIGH |
| 39 | `ReferralResponse` | `cc_referral_responses` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 40 | `ReferralTimeline` | `cc_referral_timelines` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 41 | `ReminderSchedule` | `cc_reminder_schedules` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 42 | `RiskStratification` | `cc_risk_stratification` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 43 | `SchoolHealthVisit` | `cc_school_health_visits` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 44 | `ScreeningCampaign` | `cc_screening_campaigns` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 45 | `SelfFollowUpTask` | `cc_self_follow_up_tasks` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 46 | `SelfMonitoringRecord` | `cc_self_monitoring_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 47 | `TransitionsOfCare` | `cc_transitions_of_care` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 48 | `VaccinationRecord` | `cc_vaccination_records` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 49 | `VaccineInventory` | `cc_vaccine_inventory` | yes | `metadata_` | CareContinuumBaseEntity | — | `metadata` | MEDIUM |
| 50 | `StoredEvent` | `dp_stored_events` | yes | `metadata_` | BaseEntityMixin | `/national-data/streaming` | `metadata` | HIGH |
| 51 | `VectorEmbedding` | `dp_vector_embeddings` | yes | `metadata_` | BaseEntityMixin | `/national-data` | `metadata` | HIGH |
| 52 | `Partner` | `ecosystem_partners` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 53 | `AllergyIntolerance` | `ehr_allergies` | yes | `metadata_` | BaseEntityMixin | `/ehr`, `/fhir` | `metadata` | HIGH |
| 54 | `CarePlanActivity` | `ehr_care_plan_activities` | yes | `metadata_` | BaseEntityMixin | `/ehr` | `metadata` | HIGH |
| 55 | `CarePlanGoal` | `ehr_care_plan_goals` | yes | `metadata_` | BaseEntityMixin | `/ehr` | `metadata` | HIGH |
| 56 | `CarePlan` | `ehr_care_plans` | yes | `metadata_` | BaseEntityMixin | `/ehr`, `/fhir` | `metadata` | HIGH |
| 57 | `ClinicalNote` | `ehr_clinical_notes` | yes | `metadata_` | BaseEntityMixin | `/ehr`, `/fhir` | `metadata` | HIGH |
| 58 | `ConditionRecord` | `ehr_conditions` | yes | `metadata_` | BaseEntityMixin | `/ehr`, `/fhir` | `metadata` | HIGH |
| 59 | `DiagnosisRecord` | `ehr_diagnoses` | yes | `metadata_` | BaseEntityMixin | `/ehr`, `/fhir` | `metadata` | HIGH |
| 60 | `ImmunizationRecord` | `ehr_immunizations` | yes | `metadata_` | BaseEntityMixin | `/care-continuum`, `/ehr`, `/fhir`, `/public-health` | `metadata` | HIGH |
| 61 | `MedicationAdministration` | `ehr_medication_administrations` | yes | `metadata_` | BaseEntityMixin | `/ehr` | `metadata` | HIGH |
| 62 | `MedicationDispense` | `ehr_medication_dispenses` | yes | `metadata_` | BaseEntityMixin | `/citizen-platform`, `/ehr` | `metadata` | HIGH |
| 63 | `MedicationRequest` | `ehr_medication_requests` | yes | `metadata_` | BaseEntityMixin | `/ehr`, `/fhir` | `metadata` | HIGH |
| 64 | `MedicationStatement` | `ehr_medication_statements` | yes | `metadata_` | BaseEntityMixin | `/ehr`, `/fhir` | `metadata` | HIGH |
| 65 | `PatientTimelineEvent` | `ehr_patient_timeline` | yes | `metadata_` | BaseEntityMixin | — | `metadata` | MEDIUM |
| 66 | `ProblemListItem` | `ehr_problem_list_items` | yes | `metadata_` | BaseEntityMixin | `/ehr` | `metadata` | HIGH |
| 67 | `RiskFactorRecord` | `ehr_risk_factors` | yes | `metadata_` | BaseEntityMixin | `/ehr` | `metadata` | HIGH |
| 68 | `SocialHistoryRecord` | `ehr_social_history` | yes | `metadata_` | BaseEntityMixin | `/ehr` | `metadata` | HIGH |
| 69 | `NationalJob` | `national_background_jobs` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 70 | `Citizen` | `national_citizens` | yes | `metadata_` | BaseEntity | `/admin`, `/admin/citizen-relationships`, `/citizen`, `/citizen-platform`, `/demo`, `/governance`, `/lifecycle`, `/patient-card`, `/radiology`, `/test-results` | `metadata` | HIGH |
| 71 | `NationalDocumentModel` | `national_documents` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 72 | `Encounter` | `national_encounters` | yes | `metadata_` | BaseEntity | `/care-continuum`, `/fhir`, `/national-data` | `metadata` | HIGH |
| 73 | `EpisodeOfCare` | `national_episodes_of_care` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 74 | `MedicationCatalog` | `national_medication_catalog` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 75 | `Observation` | `national_observations` | yes | `metadata_` | BaseEntity | `/compliance`, `/fhir`, `/lims`, `/national-data` | `metadata` | HIGH |
| 76 | `Organization` | `national_organizations` | yes | `metadata_` | BaseEntity | `/compliance`, `/fhir` | `metadata` | HIGH |
| 77 | `Patient` | `national_patients` | yes | `metadata_` | BaseEntity | `/admin`, `/api/ai`, `/api/ai/v2`, `/auth`, `/authz`, `/batch`, `/citizen`, `/clinical/orders`, `/compliance`, `/contracts`, `/ehr`, `/fhir`, `/identity`, `/intelligence`, `/lims`, `/national-data`, `/national/search`, `/notify`, `/nursing`, `/patient-card`, `/patients`, `/radiology`, `/stats`, `/test-results` | `metadata` | HIGH |
| 78 | `RuleModel` | `national_rules` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 79 | `NationalAppointment` | `national_scheduling_appointments` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 80 | `NationalResource` | `national_scheduling_resources` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 81 | `NationalSearchResult` | `national_search_results` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 82 | `Admission` | `nhdw_admissions` | yes | `metadata_` | (none) | `/nhdw` | `metadata` | LOW |
| 83 | `CarePlan` | `nhdw_care_plans` | yes | `metadata_` | (none) | `/ehr`, `/fhir` | `metadata` | LOW |
| 84 | `ClinicalTask` | `nhdw_clinical_tasks` | yes | `metadata_` | (none) | `/nhdw` | `metadata` | LOW |
| 85 | `Discharge` | `nhdw_discharges` | yes | `metadata_` | (none) | `/hospital`, `/nhdw` | `metadata` | LOW |
| 86 | `HospitalAlert` | `nhdw_hospital_alerts` | yes | `metadata_` | (none) | `/nhdw` | `metadata` | LOW |
| 87 | `HospitalMessage` | `nhdw_hospital_messages` | yes | `metadata_` | (none) | `/nhdw` | `metadata` | LOW |
| 88 | `QueueEntry` | `nhdw_queue_entries` | yes | `metadata_` | (none) | `/nhdw` | `metadata` | LOW |
| 89 | `ResourceSchedule` | `nhdw_resource_schedules` | yes | `metadata_` | (none) | — | `metadata` | LOW |
| 90 | `ShiftReport` | `nhdw_shift_reports` | yes | `metadata_` | (none) | — | `metadata` | LOW |
| 91 | `TelemedicineSession` | `nhdw_telemedicine_sessions` | yes | `metadata_` | (none) | — | `metadata` | LOW |
| 92 | `Transfer` | `nhdw_transfers` | yes | `metadata_` | (none) | `/hospital`, `/nhdw`, `/pharmacy` | `metadata` | LOW |
| 93 | `WaitingListEntry` | `nhdw_waiting_list_entries` | yes | `metadata_` | (none) | `/nhdw` | `metadata` | LOW |
| 94 | `WardRound` | `nhdw_ward_rounds` | yes | `metadata_` | (none) | `/nhdw` | `metadata` | LOW |
| 95 | `CitizenRelationship` | `niam_citizen_relationships` | yes | `metadata_` | IdentityBaseEntity | `/admin/citizen-relationships`, `/citizen-platform` | `metadata` | HIGH |
| 96 | `NursingCarePlan` | `nursing_care_plans` | yes | `metadata_` | NursingBaseEntity | — | `metadata` | MEDIUM |
| 97 | `ClinicalChecklist` | `nursing_clinical_checklists` | yes | `metadata_` | NursingBaseEntity | — | `metadata` | MEDIUM |
| 98 | `Delegation` | `nursing_delegations` | yes | `metadata_` | NursingBaseEntity | `/authz`, `/nursing` | `metadata` | HIGH |
| 99 | `EscalationRecord` | `nursing_escalation_records` | yes | `metadata_` | NursingBaseEntity | `/nursing` | `metadata` | HIGH |
| 100 | `FallRiskAssessment` | `nursing_fall_risk_assessments` | yes | `metadata_` | NursingBaseEntity | — | `metadata` | MEDIUM |
| 101 | `FluidBalance` | `nursing_fluid_balance` | yes | `metadata_` | NursingBaseEntity | — | `metadata` | MEDIUM |
| 102 | `NursingNote` | `nursing_notes` | yes | `metadata_` | NursingBaseEntity | — | `metadata` | MEDIUM |
| 103 | `NutritionAssessment` | `nursing_nutrition_assessments` | yes | `metadata_` | NursingBaseEntity | — | `metadata` | MEDIUM |
| 104 | `PainAssessment` | `nursing_pain_assessments` | yes | `metadata_` | NursingBaseEntity | — | `metadata` | MEDIUM |
| 105 | `PressureInjuryAssessment` | `nursing_pressure_injury_assessments` | yes | `metadata_` | NursingBaseEntity | — | `metadata` | MEDIUM |
| 106 | `ShiftHandover` | `nursing_shift_handovers` | yes | `metadata_` | NursingBaseEntity | `/nursing` | `metadata` | HIGH |
| 107 | `NursingShift` | `nursing_shifts` | yes | `metadata_` | NursingBaseEntity | `/nursing` | `metadata` | HIGH |
| 108 | `NursingTask` | `nursing_tasks` | yes | `metadata_` | NursingBaseEntity | `/nursing` | `metadata` | HIGH |
| 109 | `VitalSignsRecord` | `nursing_vital_signs` | yes | `metadata_` | NursingBaseEntity | — | `metadata` | MEDIUM |
| 110 | `Organization` | `organizations` | yes | `extra_metadata` | (none) | `/compliance`, `/fhir` | `metadata` | LOW |
| 111 | `AllergyRule` | `pharmacy_allergy_rules` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 112 | `ClinicalGuideline` | `pharmacy_clinical_guidelines` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 113 | `ContraindicationRule` | `pharmacy_contraindication_rules` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 114 | `DispenseQueue` | `pharmacy_dispense_queue` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 115 | `DispenseRecord` | `pharmacy_dispense_records` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 116 | `DoseGuideline` | `pharmacy_dose_guidelines` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 117 | `DrugBatch` | `pharmacy_drug_batches` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 118 | `DrugCatalog` | `pharmacy_drug_catalog` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 119 | `DrugInteractionRule` | `pharmacy_drug_interaction_rules` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 120 | `DrugMonitoring` | `pharmacy_drug_monitoring` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 121 | `DrugReturn` | `pharmacy_drug_returns` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 122 | `DrugSubstitutionRequest` | `pharmacy_drug_substitution_requests` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 123 | `DrugSubstitutionRule` | `pharmacy_drug_substitution_rules` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 124 | `DrugSupplier` | `pharmacy_drug_suppliers` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 125 | `InventoryForecast` | `pharmacy_inventory_forecasts` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 126 | `InventoryTransferItem` | `pharmacy_inventory_transfer_items` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 127 | `InventoryTransfer` | `pharmacy_inventory_transfers` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 128 | `PrescriptionItem` | `pharmacy_prescription_items` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 129 | `Prescription` | `pharmacy_prescriptions` | yes | `metadata_` | BaseEntity | `/pharmacy` | `metadata` | HIGH |
| 130 | `Recall` | `pharmacy_recalls` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 131 | `PharmacySaleLine` | `pharmacy_sale_lines` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 132 | `PharmacySale` | `pharmacy_sales` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 133 | `StockLevel` | `pharmacy_stock_levels` | yes | `metadata_` | BaseEntity | `/pharmacy` | `metadata` | HIGH |
| 134 | `StockMovement` | `pharmacy_stock_movements` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
| 135 | `Store` | `pharmacy_stores` | yes | `metadata_` | BaseEntity | `/auth`, `/health-data`, `/intelligence`, `/national-data` | `metadata` | HIGH |
| 136 | `Warehouse` | `pharmacy_warehouses` | yes | `metadata_` | BaseEntity | `/health-data` | `metadata` | HIGH |
| 137 | `WasteRecord` | `pharmacy_waste_records` | yes | `metadata_` | BaseEntity | — | `metadata` | MEDIUM |
