# encounter_management Capability

**Domain:** clinical | **Layer:** application | **Version:** 1.0.0

## Description

Clinical encounter management: outpatient, emergency, inpatient, home visit, telemedicine, referral, admission, discharge, transfer, clinical notes

## Dependencies

- patient_management
- provider_management

## API

-
 
`
/
e
n
c
o
u
n
t
e
r
-
m
a
n
a
g
e
m
e
n
t
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

- `EncounterCreated`
- `PatientAdmitted`
- `PatientDischarged`
- `PatientTransferred`
- `NoteAdded`

## Commands

- `create_encounter`
- `admit`
- `discharge`
- `transfer`
- `add_clinical_note`

## Queries

- `get_encounter`
- `list_encounters`
- `get_patient_timeline`

## Quality

- Quality Score: 0.0
- Security Score: 0.0
- Performance Score: 0.0
- Reuse Score: 1.0

## License

Proprietary - GULA Platform
