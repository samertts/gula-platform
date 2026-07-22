# GULA National Platform Strategy

## National Vision

GULA is designed from the ground up as a national healthcare platform — not a laboratory information system that could scale, but a platform architected for nationwide deployment from day one. See Article 06 (Domain Model) for organization structure mapping.

## Organization Hierarchy

```
Ministry of Health
├── Governorate Health Directorates
│   ├── District Health Directorates
│   │   ├── Hospitals (public/private)
│   │   ├── Primary Healthcare Centers (PHCs)
│   │   ├── Specialized Centers (diabetes, renal, oncology)
│   │   ├── Blood Banks
│   │   └── Public Health Laboratories
│   └── Private Sector
│       ├── Private Hospitals
│       ├── Private Laboratories
│       └── Private Pharmacies
└── National Agencies
    ├── National Drug Authority
    ├── National Blood Bank
    └── National Disease Surveillance Center
```

## Tenant Model

1. **Each organization** in the hierarchy is a tenant or sub-tenant.

2. **Data isolation** is enforced at the organization level. Organizations cannot access each other's patient data without explicit sharing agreements.

3. **Cross-tenant operations** (patient referral, result sharing, public health reporting) use controlled data-sharing APIs with consent tracking.

4. **Super-tenants** (Ministry of Health, Governorate Directorates) have read-access to aggregated, de-identified data for public health analytics.

## National Identity

5. **National ID** is the foundation of patient identity. Every patient has a unique national identifier that links their records across all healthcare organizations.

6. **Master Patient Index (MPI)** maintains the golden patient record with cross-references to local facility IDs.

7. **Citizen health ID** is issued at birth or upon first healthcare encounter. It serves as the lifetime health identifier.

## National Services

| Service | Description | Phase |
|---------|-------------|-------|
| **National EHR** | Unified lifetime health record accessible across all providers | Wave 3 |
| **ePrescription** | Nationwide electronic prescription exchange | Wave 3 |
| **National Lab Network** | Lab result sharing across all laboratories | Wave 1 |
| **Referral Network** | Patient referral between any facilities | Wave 2 |
| **Public Health Surveillance** | Real-time disease monitoring and outbreak detection | Wave 2 |
| **Immunization Registry** | National vaccination records | Wave 3 |
| **Cancer Registry** | National cancer incidence tracking | Wave 3 |
| **Health Insurance Exchange** | Insurance eligibility and claims | Wave 4 |
| **Citizen Portal** | Personal health record access, appointment booking, prescription refill | Wave 2 |
| **National Analytics** | Population health dashboards for MoH | Wave 3 |

## Data Sovereignty

8. All patient data is stored within Iraq's borders. Cloud infrastructure, if used, must be in-region or in a jurisdiction with equivalent data protection laws.

9. Data sharing with international health organizations (WHO, CDC) is de-identified and governed by data-sharing agreements.

10. The Iraqi Ministry of Health retains full ownership and control of all health data.

## National Standards Compliance

11. GULA's national deployment complies with:
    - Iraqi Ministry of Health digital health standards
    - Iraqi data protection and privacy law
    - Arab Health Standards
    - WHO SMART Guidelines
    - HL7 FHIR Iraqi national profile (when established)
