# provider_management Capability

**Domain:** clinical | **Layer:** application | **Version:** 1.0.0

## Description

Healthcare provider management: doctors, nurses, technicians, pharmacists, licensing, specialties, schedules, availability, permissions

## Dependencies

- authentication
- authorization_rbac

## API

-
 
`
/
p
r
o
v
i
d
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

- `ProviderRegistered`
- `LicenseUpdated`
- `ProviderDeactivated`

## Commands

- `register_provider`
- `update_license`
- `deactivate_provider`

## Queries

- `search_providers`
- `get_provider`
- `list_by_specialty`

## Quality

- Quality Score: 0.0
- Security Score: 0.0
- Performance Score: 0.0
- Reuse Score: 1.0

## License

Proprietary - GULA Platform
