# FHIR R4 Coverage — National Healthcare Platform

## Overview

The platform implements FHIR R4 as the canonical interoperability format.
The FHIR layer resides in `app/national/fhir/` (mappers) and
`app/routes/ehr_fhir.py` (API). All FHIR endpoints are prefixed with `/fhir`.

---

## Resource Coverage

### 1. Patient Resource

**FHIR Route:** `GET /fhir/Patient/{id}`  
**Search:** `GET /fhir/Patient?identifier=...&name=...&birthdate=...`  
**Mapper:** `app/national/fhir/patient.py — FHIRPatientMapper`

**Profile:** [FHIR R4 Patient](https://hl7.org/fhir/R4/patient.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | Citizen.fhir_id or Citizen.id | Direct |
| `identifier` | Citizen.health_number, national_id_hash | Health number as "usual", national_id_hash as "official" |
| `name` | Citizen.first_name, father_name, last_name | HumanName with given/family |
| `name` (Arabic) | Citizen.full_name_ar | _text extension with lang=ar |
| `gender` | Citizen.gender | AdministrativeGender |
| `birthDate` | Citizen.date_of_birth | date |
| `address` | Citizen.governorate, district, etc. | Address with extensions |
| `telecom` | Citizen.phone, email | ContactPoint |
| `maritalStatus` | Citizen.marital_status | CodeableConcept |
| `deceasedDateTime` | Citizen.deceased_date | If is_deceased |
| `generalPractitioner` | Patient.created_by | Practitioner reference |
| `managingOrganization` | Patient.lab_id | Organization reference |
| `active` | Not Citizen.is_deleted | Boolean |

**Supported search parameters:**
- `_id` — match by resource ID
- `identifier` — match by health number or national ID hash
- `name` — match by name components (exact + fuzzy)
- `birthdate` — match by date of birth
- `gender` — match by gender
- `given` — match by given name
- `family` — match by family name
- `phone` — match by telecom
- `email` — match by email

---

### 2. Encounter Resource

**FHIR Route:** `GET /fhir/Encounter/{id}`  
**Search:** `GET /fhir/Encounter?patient=...&date=...`  
**Mapper:** `app/national/fhir/encounter.py — FHIREncounterMapper`

**Profile:** [FHIR R4 Encounter](https://hl7.org/fhir/R4/encounter.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | Encounter.fhir_id or Encounter.id | Direct |
| `status` | Encounter.encounter_status | EncounterStatus |
| `class` | Encounter.encounter_class | Coding (AMB, EMER, IMP, etc.) |
| `type` | Encounter.encounter_type | CodeableConcept array |
| `subject` | Encounter.patient_id | Patient reference |
| `participant` | Encounter.practitioners | Practitioner references |
| `period` | Encounter.start_date, end_date | Period |
| `reasonCode` | Encounter.reason | CodeableConcept |
| `diagnosis` | Diagnosis records | Condition references |
| `hospitalization` | Encounter.admission_date, discharge_date | Hospitalization component |
| `location` | Encounter.facility_id | Location reference |
| `serviceProvider` | Encounter.organization_id | Organization reference |

**Supported search parameters:**
- `_id` — match by resource ID
- `patient` — match by patient reference
- `subject` — match by subject reference
- `date` — match by period (before, after, between)
- `status` — match by encounter status
- `type` — match by encounter type
- `location` — match by location reference
- `practitioner` — match by participant reference

---

### 3. Condition Resource

**FHIR Route:** `GET /fhir/Condition/{id}`  
**Search:** `GET /fhir/Condition?patient=...&code=...`  
**Mapper:** Inline in `ehr_fhir.py`

**Profile:** [FHIR R4 Condition](https://hl7.org/fhir/R4/condition.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | ConditionRecord.fhir_id or id | Direct |
| `clinicalStatus` | ConditionRecord.clinical_status | CodeableConcept |
| `verificationStatus` | ConditionRecord.verification_status | CodeableConcept |
| `category` | ConditionRecord.category | CodeableConcept array |
| `severity` | ConditionRecord.severity | CodeableConcept |
| `code` | ConditionRecord.code_display | CodeableConcept |
| `subject` | ConditionRecord.patient_id | Patient reference |
| `encounter` | ConditionRecord.encounter_id | Encounter reference |
| `recordedDate` | ConditionRecord.recorded_date | dateTime |
| `recorder` | ConditionRecord.practitioner_id | Practitioner reference |
| `onsetDateTime` | ConditionRecord.onset_date | dateTime |
| `abatementDateTime` | ConditionRecord.abatement_date | dateTime |
| `bodySite` | ConditionRecord.body_site | CodeableConcept array |

**Supported search parameters:**
- `_id` — match by resource ID
- `patient` — match by patient reference
- `subject` — match by subject reference
- `code` — match by condition code
- `clinical-status` — match by clinical status
- `severity` — match by severity
- `onset-date` — match by onset date
- `recorded-date` — match by recorded date
- `encounter` — match by encounter reference

---

### 4. Observation Resource

**FHIR Route:** `GET /fhir/Observation/{id}`  
**Search:** `GET /fhir/Observation?patient=...&code=...&date=...`  
**Mapper:** `app/national/fhir/observation.py — FHIRObservationMapper`

**Profile:** [FHIR R4 Observation](https://hl7.org/fhir/R4/observation.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | LabResult.fhir_id or id | Direct |
| `status` | LabResult.status | ObservationStatus |
| `category` | LabResult.category | CodeableConcept array |
| `code` | TestType.code, name | CodeableConcept (LOINC) |
| `subject` | LabResult.patient_id | Patient reference |
| `encounter` | LabResult.order.encounter_id | Encounter reference |
| `effectiveDateTime` | LabResult.result_date | dateTime |
| `issued` | LabResult.recorded_at | instant |
| `performer` | LabResult.performer_id | Practitioner reference |
| `valueQuantity` | LabResult.value, unit | Quantity |
| `valueString` | LabResult.text_value | string |
| `valueCodeableConcept` | LabResult.coded_value | CodeableConcept |
| `interpretation` | LabResult.interpretation | CodeableConcept |
| `referenceRange` | TestType.ref_range_low/high | Range |
| `note` | LabResult.notes | Annotation array |

**Supported search parameters:**
- `_id` — match by resource ID
- `patient` — match by patient reference
- `subject` — match by subject reference
- `code` — match by LOINC code
- `date` — match by effective date
- `status` — match by status
- `category` — match by category
- `encounter` — match by encounter reference
- `performer` — match by performer reference

---

### 5. MedicationRequest Resource

**FHIR Route:** `GET /fhir/MedicationRequest/{id}`  
**Search:** `GET /fhir/MedicationRequest?patient=...&status=...`  
**Mapper:** Inline in `ehr_fhir.py`

**Profile:** [FHIR R4 MedicationRequest](https://hl7.org/fhir/R4/medicationrequest.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | MedicationRequest.fhir_id or id | Direct |
| `status` | MedicationRequest.status | MedicationRequestStatus |
| `intent` | MedicationRequest.intent | RequestIntent |
| `priority` | MedicationRequest.priority | RequestPriority |
| `medicationCodeableConcept` | MedicationRequest.medication_code, name | CodeableConcept |
| `subject` | MedicationRequest.patient_id | Patient reference |
| `encounter` | MedicationRequest.encounter_id | Encounter reference |
| `authoredOn` | MedicationRequest.authored_on | dateTime |
| `requester` | MedicationRequest.prescriber_id | Practitioner reference |
| `dosageInstruction` | MedicationRequest.dosage_instructions | Dosage array |
| `dispenseRequest` | MedicationRequest.quantity, duration | DispenseRequest |
| `substitution` | MedicationRequest.substitution_allowed | Substitution |
| `note` | MedicationRequest.note | Annotation array |

**Supported search parameters:**
- `_id` — match by resource ID
- `patient` — match by patient reference
- `subject` — match by subject reference
- `status` — match by status
- `intent` — match by intent
- `priority` — match by priority
- `authored-on` — match by authored date
- `requester` — match by prescriber reference
- `encounter` — match by encounter reference

---

### 6. MedicationStatement Resource

**FHIR Route:** `GET /fhir/MedicationStatement/{id}`  
**Search:** `GET /fhir/MedicationStatement?patient=...&status=...`  
**Mapper:** Inline in `ehr_fhir.py`

**Profile:** [FHIR R4 MedicationStatement](https://hl7.org/fhir/R4/medicationstatement.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | MedicationStatement.fhir_id or id | Direct |
| `status` | MedicationStatement.status | MedicationStatementStatus |
| `medicationCodeableConcept` | MedicationStatement.medication_code, name | CodeableConcept |
| `subject` | MedicationStatement.patient_id | Patient reference |
| `encounter` | MedicationStatement.encounter_id | Encounter reference |
| `effectiveDateTime` | MedicationStatement.date_started | dateTime |
| `dateAsserted` | MedicationStatement.date_recorded | dateTime |
| `informationSource` | MedicationStatement.practitioner_id | Practitioner reference |
| `derivedFrom` | MedicationStatement.medication_request_id | MedicationRequest reference |
| `reasonCode` | MedicationStatement.reason_code | CodeableConcept |
| `note` | MedicationStatement.note | Annotation array |

---

### 7. CarePlan Resource

**FHIR Route:** `GET /fhir/CarePlan/{id}`  
**Search:** `GET /fhir/CarePlan?patient=...&status=...`  
**Mapper:** Inline in `ehr_fhir.py`

**Profile:** [FHIR R4 CarePlan](https://hl7.org/fhir/R4/careplan.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | CarePlan.fhir_id or id | Direct |
| `status` | CarePlan.status | CarePlanStatus |
| `intent` | CarePlan.intent | CarePlanIntent |
| `title` | CarePlan.title | string |
| `description` | CarePlan.description | string |
| `subject` | CarePlan.patient_id | Patient reference |
| `encounter` | CarePlan.encounter_id | Encounter reference |
| `period` | CarePlan.period_start, period_end | Period |
| `author` | CarePlan.practitioner_id | Practitioner reference |
| `goal` | CarePlanGoal[] | Goal references |
| `activity` | CarePlanActivity[] | Activity references |
| `note` | CarePlan.notes | Annotation array |
| `category` | CarePlan.category | CodeableConcept array |
| `supportingInfo` | CarePlan.supporting_info | Reference array |

---

### 8. Procedure Resource

**FHIR Route:** `GET /fhir/Procedure/{id}`  
**Search:** `GET /fhir/Procedure?patient=...&code=...&date=...`  
**Mapper:** Inline in `ehr_fhir.py`

**Profile:** [FHIR R4 Procedure](https://hl7.org/fhir/R4/procedure.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | Procedure.fhir_id or id | Direct |
| `status` | Procedure.status | EventStatus |
| `code` | Procedure.code | CodeableConcept |
| `subject` | Procedure.patient_id | Patient reference |
| `encounter` | Procedure.encounter_id | Encounter reference |
| `performedDateTime` | Procedure.performed_date | dateTime |
| `performer` | Procedure.practitioner_id | Practitioner reference |
| `location` | Procedure.facility_id | Location reference |
| `reasonCode` | Procedure.reason | CodeableConcept |
| `bodySite` | Procedure.body_site | CodeableConcept array |
| `outcome` | Procedure.outcome | CodeableConcept |
| `note` | Procedure.notes | Annotation array |

---

### 9. AllergyIntolerance Resource

**FHIR Route:** `GET /fhir/AllergyIntolerance/{id}`  
**Search:** `GET /fhir/AllergyIntolerance?patient=...&status=...`  
**Mapper:** Inline in `ehr_fhir.py`

**Profile:** [FHIR R4 AllergyIntolerance](https://hl7.org/fhir/R4/allergyintolerance.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | AllergyIntolerance.fhir_id or id | Direct |
| `clinicalStatus` | AllergyIntolerance.status | CodeableConcept |
| `verificationStatus` | AllergyIntolerance.verification_status | CodeableConcept |
| `type` | AllergyIntolerance.allergy_type | AllergyIntoleranceType |
| `category` | AllergyIntolerance.category | AllergyIntoleranceCategory |
| `criticality` | AllergyIntolerance.criticality | Criticality |
| `code` | AllergyIntolerance.code_display | CodeableConcept |
| `subject` | AllergyIntolerance.patient_id | Patient reference |
| `encounter` | AllergyIntolerance.encounter_id | Encounter reference |
| `onsetDateTime` | AllergyIntolerance.onset_date | dateTime |
| `recordedDate` | AllergyIntolerance.recorded_date | dateTime |
| `recorder` | AllergyIntolerance.practitioner_id | Practitioner reference |
| `reaction` | AllergyIntolerance.reaction_details | Reaction array |
| `lastOccurrence` | AllergyIntolerance.last_occurrence_date | dateTime |

---

### 10. Immunization Resource

**FHIR Route:** `GET /fhir/Immunization/{id}`  
**Search:** `GET /fhir/Immunization?patient=...&vaccine=...&date=...`  
**Mapper:** Inline in `ehr_fhir.py`

**Profile:** [FHIR R4 Immunization](https://hl7.org/fhir/R4/immunization.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | ImmunizationRecord.fhir_id or id | Direct |
| `status` | ImmunizationRecord.status | ImmunizationStatus |
| `vaccineCode` | ImmunizationRecord.vaccine_code, name | CodeableConcept |
| `patient` | ImmunizationRecord.patient_id | Patient reference |
| `encounter` | ImmunizationRecord.encounter_id | Encounter reference |
| `occurrenceDateTime` | ImmunizationRecord.administration_date | dateTime |
| `recorded` | ImmunizationRecord.recorded_date | dateTime |
| `primarySource` | Boolean | true |
| `manufacturer` | ImmunizationRecord.manufacturer | Reference |
| `lotNumber` | ImmunizationRecord.lot_number | string |
| `expirationDate` | ImmunizationRecord.expiry_date | date |
| `doseQuantity` | ImmunizationRecord.dose_quantity, unit | Quantity |
| `performer` | ImmunizationRecord.administrator_id | Practitioner reference |
| `route` | ImmunizationRecord.route | CodeableConcept |
| `site` | ImmunizationRecord.site | CodeableConcept |
| `protocolApplied` | ImmunizationRecord.dose_number, series | ProtocolApplied |
| `reaction` | ImmunizationRecord.adverse_event | Reaction |

---

### 11. DocumentReference Resource

**FHIR Route:** `GET /fhir/DocumentReference/{id}`  
**Search:** `GET /fhir/DocumentReference?patient=...&type=...&date=...`  
**Mapper:** Inline in `ehr_fhir.py`

**Profile:** [FHIR R4 DocumentReference](https://hl7.org/fhir/R4/documentreference.html)

| FHIR Field | Source Model | Mapping |
|------------|-------------|---------|
| `id` | ClinicalNote.fhir_id or id | Direct |
| `status` | ClinicalNote.is_final → CURRENT | DocumentReferenceStatus |
| `docStatus` | ClinicalNote.is_signed → FINAL | DocumentReferenceStatus |
| `type` | ClinicalNote.note_type | CodeableConcept |
| `subject` | ClinicalNote.patient_id | Patient reference |
| `author` | ClinicalNote.author_id | Practitioner reference |
| `created` | ClinicalNote.authored_at | dateTime |
| `indexed` | ClinicalNote.updated_at | instant |
| `description` | ClinicalNote.title | string |
| `content.attachment.data` | ClinicalNote.content | Attachment (base64) |
| `content.attachment.contentType` | ClinicalNote.content_format | MimeType |
| `context.encounter` | ClinicalNote.encounter_id | Encounter reference |
| `context.facility` | ClinicalNote.facility_id | Location reference |
| `context.related` | ClinicalNote.encounter_id | Reference array |

---

### 12. Composition Resource

**FHIR Route:** Built from Patient Summary  
**Profile:** [FHIR R4 Composition](https://hl7.org/fhir/R4/composition.html)

The patient summary endpoint (`/ehr/patients/{id}/summary`) can return a
FHIR Composition document that aggregates:

| Section | Source |
|---------|--------|
| `section.title` = "Problems" | ProblemListItem[] |
| `section.title` = "Allergies" | AllergyIntolerance[] |
| `section.title` = "Medications" | MedicationStatement[] |
| `section.title` = "Immunizations" | ImmunizationRecord[] |
| `section.title` = "Conditions" | ConditionRecord[] |

---

### 13. Bundle Resource

**FHIR Route:** `GET /fhir/Bundle` (search all resource types)  
**Mapper:** `app/national/fhir/bundle.py`

**Profile:** [FHIR R4 Bundle](https://hl7.org/fhir/R4/bundle.html)

The bundle mapper wraps any FHIR resource list into a Bundle with:

| Bundle Field | Value |
|-------------|-------|
| `resourceType` | "Bundle" |
| `type` | "searchset" |
| `timestamp` | Current UTC time |
| `total` | Total matching resources |
| `entry[].resource` | Individual FHIR resources |
| `entry[].search.mode` | "match" |
| `link[].relation` | "self", "next", "previous" |
| `link[].url` | Pagination URLs |

---

## FHIR API Summary

| Endpoint | Methods | Purpose |
|----------|---------|---------|
| `/fhir/Patient` | GET, POST | Patient CRUD |
| `/fhir/Patient/{id}` | GET, PUT, DELETE | Patient by ID |
| `/fhir/Patient/_search` | POST | Patient search |
| `/fhir/Encounter` | GET, POST | Encounter CRUD |
| `/fhir/Encounter/{id}` | GET, PUT | Encounter by ID |
| `/fhir/Condition` | GET, POST | Condition CRUD |
| `/fhir/Condition/{id}` | GET, PUT | Condition by ID |
| `/fhir/Observation` | GET, POST | Observation CRUD |
| `/fhir/Observation/{id}` | GET | Observation by ID |
| `/fhir/MedicationRequest` | GET, POST | Medication Request CRUD |
| `/fhir/MedicationRequest/{id}` | GET, PUT | Medication Request by ID |
| `/fhir/MedicationStatement` | GET, POST | Medication Statement CRUD |
| `/fhir/MedicationStatement/{id}` | GET | Medication Statement by ID |
| `/fhir/CarePlan` | GET, POST | Care Plan CRUD |
| `/fhir/CarePlan/{id}` | GET, PUT | Care Plan by ID |
| `/fhir/Procedure` | GET, POST | Procedure CRUD |
| `/fhir/Procedure/{id}` | GET | Procedure by ID |
| `/fhir/AllergyIntolerance` | GET, POST | Allergy CRUD |
| `/fhir/AllergyIntolerance/{id}` | GET, PUT | Allergy by ID |
| `/fhir/Immunization` | GET, POST | Immunization CRUD |
| `/fhir/Immunization/{id}` | GET | Immunization by ID |
| `/fhir/DocumentReference` | GET | Document Reference list |
| `/fhir/DocumentReference/{id}` | GET | Document Reference by ID |
| `/fhir/Bundle` | GET | Multi-resource search |
| `/fhir/_capabilities` | GET | FHIR CapabilityStatement |
| `/fhir/_metadata` | GET | Server metadata |

## Terminology Services

| Endpoint | Methods | Purpose |
|----------|---------|---------|
| `/fhir/ConceptMap` | GET | Cross-system code mappings |
| `/fhir/ValueSet` | GET, POST | Value set management |
| `/fhir/ValueSet/{id}/$expand` | GET | Value set expansion |
| `/fhir/CodeSystem` | GET, POST | Code system lookup |
| `/fhir/$lookup` | GET | Code system lookup (code + system) |
| `/fhir/$validate-code` | GET | Code validation |

## FHIR Compliance

| Capability | Support |
|-----------|---------|
| FHIR Version | R4 (4.0.1) |
| JSON Format | Full |
| XML Format | Not implemented |
| Search | Partial (key parameters per resource) |
| Transactions | Bundle transaction |
| History | Not implemented |
| Patch | Not implemented |
| Conditional Operations | Not implemented |
| Subscriptions | Via streaming pipeline |
| Operations | $expand, $lookup, $validate-code |
