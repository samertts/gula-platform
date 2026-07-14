# clinical_foundation Capability

**Domain:** clinical | **Layer:** application | **Version:** 1.0.0

## Description

Clinical data foundation: diagnoses, problems, allergies, medications, procedures, observations, vitals, immunizations, clinical history

## Dependencies

- patient_management
- encounter_management

## API

-
 
`
/
c
l
i
n
i
c
a
l
-
f
o
u
n
d
a
t
i
o
n
/
`
 
—
 
R
E
S
T
 
A
P
I

## Events

- `DiagnosisAdded`
- `MedicationPrescribed`
- `VitalsRecorded`
- `AllergyRecorded`

## Commands

- `add_diagnosis`
- `add_medication`
- `record_vitals`
- `add_allergy`

## Queries

- `get_clinical_history`
- `get_active_problems`
- `get_medication_list`

## Quality

- Quality Score: 0.0
- Security Score: 0.0
- Performance Score: 0.0
- Reuse Score: 1.0

## License

Proprietary - GULA Platform
