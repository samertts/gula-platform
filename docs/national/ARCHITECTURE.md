# National Platform Architecture — Missions 017-024

## Overview
The GULA National Digital Health Platform is an Arabic-first, FHIR R4-native, offline-first healthcare platform for Iraq. Eight missions (017-024) extend the existing foundation with complete national-scale platforms.

## Platform Architecture

### Mission 017 — National EHR Platform
- **Route prefix:** `/fhir`, `/clinical`, `/clinical-orders`, `/clinical-documentation`, `/clinical-quality`, `/ehr`
- **Modules:** `app/ehr/`, `app/clinical/`, `app/routes/ehr_fhir.py`, `app/national/fhir/`
- **FHIR Resources:** Patient, Encounter, Condition, Observation, MedicationRequest, MedicationStatement, CarePlan, Procedure, AllergyIntolerance, Immunization, DocumentReference, Composition, Bundle
- **Clinical Documentation:** SOAP notes, progress notes, consultation notes, discharge summaries, operative notes, nursing notes

### Mission 018 — National Health Data Platform
- **Route prefix:** `/national-data`, `/national-streaming`, `/canonical`
- **Modules:** `app/national_data/`, `app/health_data/`
- **Data Lake:** Canonical models (Patient, Encounter, Observation, Medication, Procedure, Document)
- **Warehouse:** FactPatientVisit, FactLabResult, FactDiagnosis, DimPatient, DimDate, DimFacility, DimProvider, DimDiagnosis
- **MDM:** GoldenRecord, DuplicateRecord, SourceSystem, ProviderRegistry, DeviceRegistry, LocationRegistry
- **Event Store:** StoredEvent, EventSnapshot, EventRetentionPolicy
- **Governance:** DataLineageEntry, DataCatalogEntry, DataQualityRule, DataSteward, DataClassification, RetentionPolicy
- **AI Data:** FeatureStore, TrainingDataset, VectorEmbedding, KnowledgeGraph, DeidentificationJob, SyntheticDataJob

### Mission 019 — National Platform Operations
- **Route prefix:** `/control-plane`, `/operations`, `/release`, `/fleet`
- **Modules:** `app/control_plane/`
- **Operations Center:** Incident management, service health, maintenance windows, escalation matrix
- **Release Management:** Version registry, rollback, blue-green deployment, canary deployment, feature flags
- **Capacity Management:** Forecasting, scaling policies, storage/DBA/CPU/RAM/network monitoring
- **Backup & DR:** Immutable backup, geo backup, PITR, failover/failback automation

### Mission 020 — National Digital Health Ecosystem
- **Route prefix:** `/ecosystem`, `/gateway`
- **Modules:** `app/national/ecosystem/`
- **Connector Framework:** REST, FHIR REST/FHIR Messaging, HL7 v2, ASTM, File Watcher, CSV/Excel Import, MQTT, AMQP, Webhook
- **Partner Platform:** PartnerRegistry, Credentials, Certificates, RateLimits, AuditLogs, Agreements
- **Transformation Engine:** Schema registry, mapping engine, validation
- **API Gateway Policies:** RateLimit, Quota, IP Whitelist/Blacklist, OAuth2, mTLS, TimeRestriction, APIKey
- **Gateway Routes:** `/ecosystem` (connectors, partners, transform, schemas), `/gateway` (routing, policies, catalog)

### Mission 021 — National Citizen Super App
- **Route prefix:** `/citizen-platform`
- **Modules:** `app/citizen_platform/`
- **Frontend:** `frontend-v2/` — React + Firebase, PWA, RTL, Arabic-first
- **Endpoints:** Dashboard, Profile, Health Summary, Appointments, Medications, Lab Results, Radiology, Family, Vaccinations, Notifications, Certificates, Emergency Contacts, Screening, Consents, Mobile Config, Adherence
- **Platforms:** Android (iOS-ready), PWA, Responsive Web
- **Offline:** Encrypted cache, background sync, conflict resolution, delta sync

### Mission 022 — National Health Intelligence & Automation
- **Route prefix:** `/intelligence`
- **Modules:** `app/national/intelligence/`
- **Automation:** TaskAutomation, RuleAutomation, ScheduleAutomation, NotificationAutomation, Escalation, Compensation, JobOrchestrator
- **Clinical Intelligence:** Recommendations, Drug Interaction, Duplicate Therapy, Preventive Care, Care Gaps, Risk Stratification, Clinical Alerts, Critical Result Escalation
- **Laboratory Intelligence:** Analyzer Health, QC Prediction, Reagent Prediction, TAT Optimization, Workload Distribution, Delta Check
- **Hospital Intelligence:** Bed/Queue/ICU/Emergency Prediction, Admission/Discharge Forecasting, Resource Utilization
- **Public Health Intelligence:** Disease Surveillance, Outbreak Detection, Vaccination Coverage, Population Risk, Mortality Analysis, Maternal/Child Health
- **AI Platform:** LLM Gateway, Prompt Registry, Model Registry, Model Router, Inference Engine, Vector Store, Knowledge Graph, RAG, Explainability, Safety Filter, Human Approval, AI Audit

### Mission 023 — National Doctor Clinical Workspace
- **Route prefix:** `/clinical`, `/clinical-orders`, `/clinical-documentation`, `/clinical-quality`
- **Modules:** `app/clinical/`, `app/routes/clinical*.py`
- **Features:** Patient summary, clinical timeline, encounters, problems, diagnoses, allergies, vitals, family history, clinical notes, care plans, risk indicators
- **Orders:** Laboratory, radiology, medication, procedure, referral, consultation, order templates, favorites, order sets
- **Communication:** Secure messaging, team collaboration, clinical handover, patient notifications

### Mission 024 — National Laboratory Desktop Professional
- **Route prefix:** `/lims`
- **Modules:** `app/lims/`
- **LIMS Routes:** 50+ endpoints covering departments, instruments, specimens, orders, panels, results, QC, inventory, reports, integrations
- **Specimen Lifecycle:** Registration, barcode, collection, receiving, acceptance/rejection, aliquot, storage, tracking, chain of custody, disposal
- **Analyzer Integration:** ASTM E1394, HL7 ORU^R01, POCT, bidirectional support, driver abstraction, queue, retry, offline buffer, health monitoring
- **Quality Management:** Internal/External QC, Westgard Rules, Levey-Jennings, calibration, maintenance, reagent monitoring, lot management, temperature monitoring
- **Result Management:** Auto-validation, manual validation, delta check, critical results, repeat rules, verification, electronic signature, amendments, version history, audit trail
- **Printing:** Result reports, barcode labels, QR labels, specimen labels, thermal/laser printers, government/hospital templates, digital signature, watermark

## Technology Stack
- **Runtime:** Python 3.11+, FastAPI, Gunicorn + Uvicorn
- **Database:** PostgreSQL 16 with SQLAlchemy 2.0 ORM
- **Cache:** Redis 7
- **Frontend:** React 18, TypeScript, Vite, Firebase
- **Desktop:** PySide6 (Windows Native)
- **Mobile:** React Native / PWA

## Deployment
- Docker Compose (primary), Kubernetes, DigitalOcean, Render
- Nginx API Gateway (api-gateway container)
- HAProxy for horizontal scaling
- Prometheus + Grafana for monitoring

## Security
- JWT-based authentication
- RBAC (9 roles × 13 permissions) + ABAC
- Tenant isolation by lab_id
- Encryption at rest (national_id)
- Audit log with hash chain
- Rate limiting, circuit breaker, degraded mode
- mTLS for partner connections
