# National Healthcare Platform — Master Architecture Document

## System Overview

The National Healthcare Platform is a multi-platform healthcare information system
comprising five integrated platforms that together form a national-scale health
data ecosystem. Every platform is built as a domain module within the GULA
backend monolith (`backend/app/`), sharing common infrastructure while
maintaining strict domain boundaries.

### The Five Platforms

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      NATIONAL HEALTHCARE PLATFORM                       │
│                                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │
│  │   EHR       │  │   Hospital   │  │    Care      │  │  Clinical  │  │
│  │  Platform   │  │   Platform   │  │  Continuum   │  │  Platform  │  │
│  │             │  │              │  │   Platform   │  │            │  │
│  │ • Patient   │  │ • Master     │  │ • Referrals  │  │ • Termino- │  │
│  │   Summary   │  │   Data       │  │ • Chronic    │  │   logy     │  │
│  │ • Problem   │  │ • Bed Mgmt   │  │   Disease    │  │ • CDS      │  │
│  │   List      │  │ • ADT        │  │ • Maternal   │  │ • Know-    │  │
│  │ • Allergies │  │ • Scheduling │  │ • Immuniz.   │  │   ledge    │  │
│  │ • Meds      │  │ • OR Mgmt    │  │ • Public     │  │ • Quality  │  │
│  │ • Care Plan │  │ • Equipment  │  │   Health     │  │ • Research │  │
│  │ • Timeline  │  │ • Cost Ctr   │  │ • Patient    │  │ • AI       │  │
│  │ • FHIR API  │  │              │  │   Tasks      │  │            │  │
│  └──────┬──────┘  └──────┬───────┘  └──────┬───────┘  └──────┬─────┘  │
│         │                │                  │                 │        │
│         └──────────┬─────┴──────────────────┴──────────┬──────┘        │
│                    │                                    │              │
│           ┌────────▼────────────────────────────────────▼────────┐     │
│           │              National Health Data Platform           │     │
│           │                                                      │     │
│           │  • Canonical Data Model   • MDM (Golden Records)     │     │
│           │  • Event Store            • Data Lake / Warehouse    │     │
│           │  • Streaming Pipeline     • Governance & Consent     │     │
│           └──────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────┘
```

### Platform Boundaries

| Platform | Module Location | Domain | Data Ownership |
|----------|----------------|--------|----------------|
| **EHR Platform** | `app/ehr/` | Clinical patient record | Patient-level longitudinal |
| **Hospital Platform** | `app/hospital/` | Facility master data | Hospital/institutional |
| **Care Continuum** | `app/care_continuum/` | Cross-facility care | Episode/continuum |
| **Clinical Platform** | `app/clinical/` | Medical knowledge | Reference/standards |
| **Health Data Platform** | `app/health_data/` | Analytics & integration | Aggregate/governed |

---

## Layered Architecture

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          PRESENTATION LAYER                              │
│  REST API (FastAPI)  │  FHIR R4 API  │  Streaming (SSE/WebSocket)        │
│  Routes: /ehr/*      │  /fhir/*      │  /national-data/streaming/*       │
│  Routes: /hospital/* │  /clinical/*  │  /national-data/*                 │
│  Routes: /care-continuum/*           │                                   │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
┌──────────────────────────────────────────────────────────────────────────┐
│                          APPLICATION LAYER                               │
│  ┌─────────────────┐  ┌──────────────┐  ┌──────────────────────────┐    │
│  │   CQRS Command   │  │    CQRS      │  │      Services            │    │
│  │     Handlers     │  │   Queries    │  │  (Business Logic)        │    │
│  │ • create_*       │  │ • get_*      │  │ • ehr_service.py         │    │
│  │ • update_*       │  │ • list_*     │  │ • hospital_service.py    │    │
│  │ • delete_*       │  │ • search_*   │  │ • care_continuum_service │    │
│  │ • validate_*     │  │ • aggregate_*│  │ • clinical_service.py    │    │
│  └────────┬─────────┘  └──────┬───────┘  │ • data_platform_service  │    │
│           │                   │           └──────────────────────────┘    │
│           └───────────────────┴──────────────────────┘                    │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
┌──────────────────────────────────────────────────────────────────────────┐
│                          DOMAIN LAYER                                    │
│  ┌────────────┐ ┌───────────┐ ┌───────────┐ ┌──────────┐ ┌──────────┐ │
│  │   EHR      │ │  Hospital │ │  Care     │ │ Clinical │ │National  │ │
│  │  Models    │ │  Models   │ │ Continuum │ │ Models   │ │ Domain   │ │
│  │            │ │           │ │ Models    │ │          │ │ Models   │ │
│  │ Problem    │ │ Hospital  │ │ Referral  │ │ Termino- │ │ Citizen  │ │
│  │ Allergy    │ │ Campus    │ │ Chronic   │ │ logy     │ │ Patient  │ │
│  │ Medication │ │ Building  │ │ Maternal  │ │ CDS      │ │ Encounter│ │
│  │ Care Plan  │ │ Ward/Room │ │ Immuniz.  │ │ Quality  │ │ Facility │ │
│  │ Immuniz.   │ │ Bed/Equip │ │ Primary   │ │ Know-    │ │ Provider │ │
│  │ Notes      │ │ Dept/Unit │ │ Care      │ │ ledge    │ │ Identity │ │
│  │ Timeline   │ │ Clinic    │ │ Pub Health│ │ Research │ │ Family   │ │
│  └────────────┘ └───────────┘ └───────────┘ └──────────┘ └──────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
                                    │
┌──────────────────────────────────────────────────────────────────────────┐
│                          INFRASTRUCTURE LAYER                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │PostgreSQL │ │  Redis   │ │  Event   │ │  Object  │ │   Search     │ │
│  │    16     │ │    7     │ │  Bus     │ │ Storage  │ │  (Elastic)   │ │
│  │          │ │          │ │ (RabbitMQ)│ │ (S3/MinIO)│ │              │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘ │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Module Dependency Graph

```
                         app.main
                            │
        ┌───────────────────┼───────────────────────┐
        │                   │                       │
   app.routes          app.services           app.database
        │                   │                       │
        ├── ehr.py          ├── ehr_service.py      └── SQLAlchemy
        ├── ehr_fhir.py     ├── hospital_service.py
        ├── hospital.py     ├── care_continuum_service.py
        ├── care_continuum  ├── clinical_service.py
        ├── clinical.py     └── data_platform_service.py
        ├── national_data
        ├── national_streaming
        └── ... (labs, etc)
             │                   │
             └───────────────────┘
                         │
        ┌────────────────┼────────────────────┐
        │                │                    │
   app.ehr         app.hospital        app.care_continuum
   app.clinical     app.national        app.health_data
                         │
                    app.security
                    (RBAC, ABAC, JWT, Audit)
```

### Dependency Rules

1. **Routes depend on Services** — route modules call service functions, never models directly
2. **Services depend on Models** — services orchestrate model CRUD and business rules
3. **Models depend on Base** — all domain models inherit from `BaseEntity` mixins
4. **Domains may reference National** — EHR models reference `national_patients`, `national_citizens`, etc.
5. **Domains may NOT cross-reference each other** — EHR never imports Hospital models directly
6. **Clinical Platform is standalone** — terminology/knowledge models have no domain dependencies
7. **Data Platform consumes events** — reads from event store, does not import domain models

---

## API Gateway Pattern

```
Internet ──► Host Nginx (TLS) ──► api-gateway (Docker nginx :8080)
                                      │
                        ┌─────────────┼─────────────────┐
                        │             │                  │
                   /ehr/*       /hospital/*         /fhir/*
                   /care-continuum/*  /clinical/*        │
                        │             │                  │
                        └─────────────┼──────────────────┘
                                      │
                              gula-backend
                           (FastAPI, port 8000)
```

The gateway enforces:
- TLS termination
- Request routing by path prefix
- Rate limiting (per-IP, per-route)
- Request logging
- Health-check pass-through (`/health`, `/health/ready`)

---

## Database Per-Service Pattern

Rather than a literal database per service (which would require distributed
transactions), the monolith implements **logical database separation** within a
single PostgreSQL instance:

| Schema | Owner | Tables |
|--------|-------|--------|
| `public` | GULA core | `labs`, `lab_users`, `patients`, `lab_orders`, `lab_results` |
| `ehr` | EHR Platform | `ehr_problem_list_items`, `ehr_allergies`, `ehr_medication_*`, `ehr_care_plans`, `ehr_clinical_notes`, `ehr_immunizations`, `ehr_family_history`, `ehr_social_history`, `ehr_risk_factors`, `ehr_patient_timeline`, `ehr_clinical_attachments`, `ehr_conditions`, `ehr_diagnoses` |
| `hospital` | Hospital Platform | `hospitals`, `hospital_campuses`, `hospital_buildings`, `hospital_floors`, `hospital_rooms`, `hospital_beds`, `hospital_bed_assignments`, `hospital_departments`, `hospital_units`, `hospital_clinics`, `hospital_operation_theaters`, `hospital_equipment`, `hospital_cost_centers` |
| `cc` | Care Continuum | `cc_referral_requests`, `cc_care_journeys`, `cc_chronic_disease_registry`, `cc_pregnancy_records`, `cc_immunization_schedules`, `cc_primary_care_encounters`, `cc_health_programs`, `cc_patient_tasks` |
| `clinical` | Clinical Platform | `clinical_terminology_codes`, `clinical_terminology_versions`, `clinical_terminology_mappings`, `clinical_value_sets`, `clinical_guidelines`, `clinical_order_sets`, `clinical_quality_indicators` |
| `national` | Identity | `national_citizens`, `national_patients`, `national_encounters`, `national_facilities`, `national_organizations`, `national_practitioners` |
| `national_data` | Data Platform | `canonical_*`, `mdm_golden_records`, `event_store_events`, `data_*` |

Each schema has its own Alembic migration branch or version prefix.

---

## Event-Driven Architecture

```
┌──────────┐     ┌──────────────┐     ┌──────────────┐
│ Service A │────►│  Event Bus   │────►│  Service B   │
│ (Producer)│     │  (RabbitMQ)  │     │ (Consumer)   │
└──────────┘     └──────┬───────┘     └──────────────┘
                        │
               ┌────────▼────────┐
               │   Event Store   │
               │   (PostgreSQL)  │
               └─────────────────┘
```

### Event Types

| Event | Producer | Consumers | Purpose |
|-------|----------|-----------|---------|
| `PatientRegistered` | Identity Service | EHR, MDM | Create EHR record |
| `EncounterStarted` | Encounter Service | EHR, Billing | Open clinical context |
| `ReferralCreated` | Referral Service | Notification, MDM | Trigger referral workflow |
| `ReferralAccepted` | Referral Service | Notification | Notify referring clinician |
| `MedicationPrescribed` | EHR Service | Pharmacy, CDS | Check interactions |
| `ConditionDiagnosed` | EHR Service | Chronic Disease Registry | Enroll in care program |
| `LabOrderPlaced` | Order Service | Lab, Result Service | Process lab order |
| `LabResultReady` | Result Service | EHR, Alerting | Update clinical record |
| `DischargeCompleted` | ADT Service | Notification, MDM | Close episode |
| `IdentityMerged` | Identity Service | All consumers | Update all references |
| `BreakGlassAccessed` | Security Service | Audit, Alerting | Emergency access notification |

### Outbox Pattern

All events follow the **Transactional Outbox** pattern to guarantee delivery:

```
1. BEGIN transaction
2. Write domain data
3. Write OutboxEvent record (same DB)
4. COMMIT transaction
5. Background worker reads OutboxEvent
6. Publish to Event Bus
7. Delete OutboxEvent or mark sent
```

The outbox is implemented in `app/services/outbox_service.py` with the
`outbox_events` table.

---

## CQRS Pattern Usage

The platform uses **Command Query Responsibility Segregation** at the module level:

```
┌─────────────────┐         ┌─────────────────┐
│   Commands      │         │    Queries       │
│                 │         │                  │
│ app/ehr/commands│         │ app/ehr/queries  │
│ app/hospital/   │         │ app/hospital/    │
│   commands      │         │   queries        │
│ app/care_       │         │ app/care_        │
│ continuum/      │         │ continuum/       │
│   commands      │         │   queries        │
└────────┬────────┘         └────────┬─────────┘
         │                           │
         │  ┌──────────────────┐     │
         └──►  Domain Models   ◄─────┘
            └──────────────────┘
```

- **Commands** handle mutations: create, update, delete, validate
- **Queries** handle reads: get, list, search, aggregate
- Commands return success/failure; Queries return data projections
- The pattern enables future segregation into read replicas for reporting

---

## Offline-First Design

Healthcare facilities in remote areas may have intermittent connectivity.
The platform is designed for offline-first operation:

1. **ULID Primary Keys** — all entities use 26-char case-insensitive ULIDs
   generated client-side, enabling offline entity creation without conflicts
2. **Version-based Optimistic Locking** — every table has a `version` column;
   updates check `version = old_version` to detect conflicts
3. **Conflict Resolution** — on sync, the server applies last-writer-wins
   with manual merge for identity conflicts
4. **Batch Synchronization** — endpoints accept `POST /sync` with change sets
   and return server-side conflicts
5. **Eventual Consistency** — the system guarantees eventual consistency;
   read-your-writes is provided within a single facility's session

---

## Multi-Tenant Isolation

Tenant isolation is implemented at the database query level:

1. **`lab_id` Column** — every tenant-scoped entity carries a `lab_id` foreign key
2. **Row-Level Security** — all queries filter by `lab_id = current_user.lab_id`
3. **Cross-Tenant Referencing** — national identity (Citizen, Patient) is shared
   across tenants; care data (EHR, Hospital) is per-tenant
4. **National Reference Data** — terminology, codes, and standards are
   global/shared, not per-tenant

The `tenant_mixin` in `app/models/base.py` enforces `lab_id` on all
tenant-owned entities.

---

## Security Architecture

```
┌────────────┐     ┌──────────────┐     ┌──────────────┐
│  Request   │────►│  RBAC Check  │────►│  ABAC Engine  │
└────────────┘     └──────────────┘     └──────┬───────┘
                                                │
                          ┌─────────────────────┼──────────────┐
                          │                     │              │
                    ┌─────▼─────┐       ┌───────▼──────┐ ┌────▼────┐
                    │ Purpose of │       │  Minimum     │ │ Consent │
                    │   Use      │       │  Necessary   │ │Enforce. │
                    └───────────┘       └──────────────┘ └─────────┘
                                                │
                          ┌─────────────────────┼──────────────┐
                          │                     │              │
                    ┌─────▼─────┐       ┌───────▼──────┐ ┌────▼────┐
                    │   Break    │       │    VIP       │ │  Minor  │
                    │   Glass    │       │  Protection  │ │Protect. │
                    └───────────┘       └──────────────┘ └─────────┘
```

Security modules (in `app/national/security/`):

| Module | Purpose |
|--------|---------|
| `rbac.py` | Role-based access (16 roles x 42 permissions) |
| `abac.py` | Attribute-based context evaluation |
| `purpose_of_use.py` | Enforces data access purpose |
| `minimum_necessary.py` | Limits data returned to minimum required |
| `consent_enforcement.py` | Checks patient consent directives |
| `break_glass.py` | Emergency override with audit trail |
| `vip_protection.py` | Extra privacy for VIP patients |
| `minor_protection.py` | Guardian authorization for minors |
| `sensitive_records.py` | Flags sensitive record types |
| `guardian_rules.py` | Guardian relationship access rules |
| `foreign_patient_rules.py` | Special rules for foreign patients |
| `emergency_access.py` | Time-limited emergency access tokens |

---

## FHIR Integration

The platform implements **FHIR R4** as the canonical interoperability format:

```
┌──────────────┐    ┌─────────────────┐    ┌──────────────┐
│  Internal     │    │   FHIR Mapper    │    │  FHIR API    │
│  Domain Models│───►│   Layer          │───►│  /fhir/*     │
│  (SQLAlchemy) │    │   (app/national/ │    │              │
│               │    │    fhir/)        │    │  JSON:R4     │
└──────────────┘    └─────────────────┘    └──────────────┘
```

FHIR Mapper modules:

| Module | FHIR Resource |
|--------|---------------|
| `patient.py` | Patient |
| `practitioner.py` | Practitioner |
| `organization.py` | Organization |
| `encounter.py` | Encounter |
| `observation.py` | Observation |
| `bundle.py` | Bundle (searchset, transaction) |
| `search.py` | FHIR search parameter handling |
| `validation.py` | FHIR resource validation |
| `terminology.py` | Terminology service ($expand, $lookup) |

The FHIR API is exposed through `app/routes/ehr_fhir.py` at the `/fhir` prefix.

---

## HL7/ASTM Bridge

Lab instrument integration uses HL7 v2 and ASTM protocols through the
**LabLink-Core** device bridge in `services/device_bridge/`:

```
┌────────────┐    ┌──────────────────┐    ┌──────────────┐
│  Sysmex    │───►│                  │    │              │
│  Roche     │───►│  Device Bridge   │───►│  GULA API    │
│  Mindray   │───►│  (ASTM/HL7)      │    │  (REST)      │
│  Generic   │───►│                  │    │              │
└────────────┘    └──────────────────┘    └──────────────┘
```

- ASTM protocol via serial/TCP for hematology/chemistry analyzers
- HL7 v2 via MLLP for laboratory information systems
- Normalised results forwarded to `gula-backend` via `gula_client.py`
- Supports Sysmex, Roche, Mindray, and generic ASTM instruments
