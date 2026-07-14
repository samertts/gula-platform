# fhir_interoperability Capability

**Domain:** integration | **Layer:** infrastructure | **Version:** 1.0.0

## Description

FHIR/HL7 interoperability: FHIR R4 resources, HL7 v2 messages, LOINC coding, SNOMED CT, ICD-10, ICD-11 ready, UCUM units, IHE profiles, terminology services

## Dependencies

- patient_management
- clinical_foundation

## API

-
 
`
/
f
h
i
r
-
i
n
t
e
r
o
p
e
r
a
b
i
l
i
t
y
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

- `FhirResourceCreated`
- `Hl7MessageReceived`
- `TerminologyUpdated`

## Commands

- `convert_to_fhir`
- `convert_from_hl7`
- `validate_resource`

## Queries

- `search_fhir`
- `read_fhir_resource`
- `expand_value_set`
- `lookup_code`

## Quality

- Quality Score: 0.0
- Security Score: 0.0
- Performance Score: 0.0
- Reuse Score: 1.0

## License

Proprietary - GULA Platform
