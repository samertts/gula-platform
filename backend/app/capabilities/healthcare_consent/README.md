# healthcare_consent Capability

**Domain:** identity_security | **Layer:** application | **Version:** 1.0.0

## Description

Healthcare-specific consent: patient privacy preferences, access policies, break-glass emergency override, purpose of use enforcement, granular data sharing controls

## Dependencies

- consent_management
- patient_management

## API

-
 
`
/
h
e
a
l
t
h
c
a
r
e
-
c
o
n
s
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

- `ConsentGranted`
- `ConsentRevoked`
- `BreakGlassActivated`

## Commands

- `grant_consent`
- `revoke_consent`
- `break_glass`

## Queries

- `check_consent`
- `get_consent_history`
- `get_active_consents`

## Quality

- Quality Score: 0.0
- Security Score: 0.0
- Performance Score: 0.0
- Reuse Score: 1.0

## License

Proprietary - GULA Platform
