# National LIMS — Laboratory Information Management System

## Overview

The National LIMS is a comprehensive, production-ready laboratory information
management system built on the GULA Platform foundation. It implements the
canonical laboratory domain as a single bounded context that is reusable by
every hospital, laboratory, and governorate across the national healthcare
network.

**Version:** national-lims-v1.0  
**Standards:** FHIR R4, HL7 v2.x, ASTM E1394, ISO 15189, CAP, CLSI  
**Architecture:** Event-driven, Domain-Driven Design, Offline-first  
**Security:** ABAC, RBAC, JWT, Electronic Signatures, Audit Trail  

## Architecture

The LIMS is a bounded context within the GULA Platform monolith. It:

- **Reuses** existing Foundation models (Lab, LabOrder, Patient, etc.)
- **References** frozen Governance entities (LaboratoryRegistry, AnalyzerRegistry, etc.)
- **Extends** with 33 new LIMS-specific domain entities
- **Emits** domain events via the transactional outbox pattern
- **Maps** all entities to FHIR R4 resources
- **Supports** offline sync via ULID-based sync_id

### Package Structure

```
app/lims/
├── __init__.py          # Package exports
├── models.py            # 33 SQLAlchemy domain entities
├── schemas.py           # Pydantic API schemas
├── services.py          # Business logic services
├── routes.py            # FastAPI REST endpoints (90+)
├── state_machine.py     # Specimen & order state machines
├── workflows.py         # Auto-validation, critical result, correction workflows
├── quality.py           # Westgard rules, Levey-Jennings, ISO 15189 indicators
├── fhir_mappers.py      # FHIR R4 resource mappers
├── events.py            # Domain events (40+ event types)
├── exceptions.py        # Custom LIMS exceptions
├── integration/         # Analyzer integration platform
│   ├── astm.py          # ASTM E1394/E1381 protocol parser
│   ├── hl7.py           # HL7 v2.x ORU^R01 parser
│   ├── device_registry.py # Device connection registry
│   └── simulator.py     # Analyzer message simulator for testing
```

## Domain Entities

### Laboratory Structure
- **Department** — lab department (e.g., Haematology, Chemistry)
- **Section** — sub-department section/bench area
- **Workstation** — physical/named workstation

### Instruments
- **Manufacturer** — equipment/reagent manufacturer
- **InstrumentModel** — specific model with protocol support
- **Instrument** — physical analyzer instance with connection params
- **Maintenance** — maintenance records
- **Calibration** — calibration records
- **EquipmentLog** — equipment usage logs

### Quality Management
- **QCProgram** — QC program definition
- **IQC** — Internal Quality Control with Westgard evaluation
- **EQA** — External Quality Assessment
- **Lot** — reagent/control/calibrator lot tracking

### Inventory
- **Reagent** — reagent stock tracking with low-stock alerts
- **Consumable** — consumable tracking
- **Supplier** — vendor/supplier management
- **Storage** — hierarchical storage locations (fridge/rack/shelf)
- **TemperatureLog** — temperature monitoring with breach alerts

### Specimen Management
- **Specimen** — complete 14-state lifecycle (ordered → disposed)
- **SpecimenCatalog** — canonical specimen type definitions
- **Container** — container type catalog
- **Transportation** — specimen transport tracking
- **ChainOfCustody** — hash-chained custody records

### Orders & Results
- **Order** — LIMS order extension with accession numbers
- **Panel** — test panels/profiles
- **PanelTest** — panel-test associations
- **Result** — comprehensive result with auto-validation
- **ReferenceRangeDef** — age/gender/method-specific reference ranges

### Validation & Reporting
- **AutoValidationRule** — configurable auto-validation rules
- **DeltaCheckRule** — delta check thresholds
- **ResultValidation** — manual validation records
- **ResultRelease** — result release tracking
- **ElectronicSignature** — ISO 15189 compliant e-signatures
- **LabReport** — laboratory reports (draft/final/corrected)
- **ReportAttachment** — report attachments

## Specimen Lifecycle

The specimen state machine defines 14 states with clear transitions:

```
ordered → registered → collected → transporting → received
    → accepted → aliquoted → processing → analyzing
    → analyzed → verified → validated → released → archived → disposed
```

Rejection is valid at: received, accepted, aliquoted, processing, analyzing.

## Quality Engine

The Westgard rules engine implements 8 standard rules:
- **1-2s** — warning (1 value exceeds ±2SD)
- **1-3s** — out of control (1 value exceeds ±3SD)
- **2-2s** — 2 consecutive outside ±2SD on same side
- **R-4s** — 2 consecutive differ by ≥4SD
- **4-1s** — 4 consecutive beyond ±1SD on same side
- **10x / 8x / 12x** — consecutive bias rules

ISO 15189 quality indicators are pre-configured with targets.

## API Endpoints

All endpoints are prefixed with `/lims` and protected by JWT authentication.

| Group | Endpoints | Description |
|-------|-----------|-------------|
| Departments | GET/POST /lims/departments | Department management |
| Sections | GET /lims/sections | Section listing |
| Instruments | CRUD /lims/instruments | Instrument lifecycle |
| Specimens | POST /lims/specimens, GET, PUT status | Specimen lifecycle |
| Orders | CRUD /lims/orders | LIMS order management |
| Results | POST/GET /lims/results, validate, release | Result management |
| QC | POST /lims/qc/run, GET /lims/qc/* | Quality control |
| QC Statistics | GET /lims/qc/statistics/{test_code} | Levey-Jennings stats |
| QC Indicators | GET /lims/quality/indicators | ISO 15189/CAP indicators |
| Panels | GET/POST /lims/panels | Panel management |
| Inventory | GET/POST /lims/reagents, /lots, /suppliers | Inventory management |
| Reports | POST/GET /lims/reports, finalize, correct | Report management |
| Integration | POST /lims/integration/astm, /hl7 | Device message ingestion |
| Simulator | POST /lims/integration/simulate | Test message generation |
| FHIR | GET /lims/results/{id}/fhir, /specimens/{id}/fhir | FHIR R4 resources |
| Dashboard | GET /lims/dashboard | Lab operational overview |

## Migration

```bash
cd backend && alembic upgrade head
```

The migration `20260714_0001_national_lims_tables.py` creates all 33 LIMS
tables idempotently with `_table_exists()` guards.

## Testing

```bash
cd backend && python -m pytest tests/ -v -k lims
```

## FHIR Mapping

All major entities map to FHIR R4:
- **Specimen** → `Specimen`
- **Result** → `Observation`
- **LabReport** → `DiagnosticReport`
- **Order** → `ServiceRequest`
- **Instrument** → `Device`

## Standards Compliance

- **ISO 15189**: Quality indicators, electronic signatures, audit trail
- **CAP**: Proficiency testing, result correction tracking
- **CLSI**: EP05, EP09, EP15, EP23, EP24, C28, GP41, H56
- **FHIR R4**: DiagnosticReport, Observation, Specimen, ServiceRequest, Device
- **HL7 v2.x**: ORU^R01 message parsing
- **ASTM E1394**: Complete frame parsing and serialization

## Key Design Decisions

1. **No duplication** — All entities reference existing Foundation models via FK
2. **Governance frozen** — Governance entities (LaboratoryRegistry, etc.) are referenced not modified
3. **Tenant isolation** — Every query filters by `lab_id` from JWT
4. **Optimistic locking** — `version` column on every mutable entity
5. **Soft delete** — `is_deleted` + `deleted_at` on all entities
6. **Offline sync** — `sync_id` (ULID) on every entity
7. **Event-driven** — All state changes emit events to the outbox
8. **State machines** — Specimen and Order have enforced state transitions
