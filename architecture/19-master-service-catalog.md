# GULA Platform — Master Service Catalog

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Clinical Domain Services](#1-clinical-domain-services)
2. [Lab Domain Services](#2-lab-domain-services)
3. [National Domain Services](#3-national-domain-services)
4. [Platform Services](#4-platform-services)
5. [Integration Services](#5-integration-services)
6. [AI Services](#6-ai-services)
7. [Notifications Services](#7-notifications-services)
8. [Infrastructure Services](#8-infrastructure-services)
9. [Device Bridge Services](#9-device-bridge-services)

---

## 1. Clinical Domain Services

### 1.1 Clinical Engine

| Attribute | Value |
|-----------|-------|
| **Name** | Clinical Engine |
| **Module** | `backend/app/services/clinical_engine.py` |
| **Purpose** | Clinical decision support, order validation, interpretation |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Clinical Team |
| **Version** | 1.0.0 |
| **API Endpoints** | Internal (called by routes/clinical.py) |
| **Events Emitted** | `clinical.interpretation.completed` |
| **Events Consumed** | `result.finalized`, `order.completed` |
| **Databases** | PostgreSQL (clinical_*, knowledge_* tables) |
| **Dependencies** | `backend/app/clinical/`, `shared/ai/` |
| **SLA** | P95 < 500ms |
| **Certification** | Gold |

### 1.2 Clinical Intelligence

| Attribute | Value |
|-----------|-------|
| **Name** | Clinical Intelligence |
| **Module** | `backend/app/services/clinical_intelligence.py` |
| **Purpose** | Advanced clinical pattern detection and trends |
| **Status** | 🟡 BETA |
| **Owner** | Clinical AI Team |
| **API Endpoints** | Internal |
| **Events Emitted** | `clinical.anomaly.detected` |
| **Databases** | PostgreSQL |
| **Dependencies** | Clinical Engine, `shared/ai/` |
| **SLA** | P95 < 2s |
| **Certification** | Silver |

### 1.3 Clinical State Manager

| Attribute | Value |
|-----------|-------|
| **Name** | Clinical State Manager |
| **Module** | `backend/app/services/clinical_state.py` |
| **Purpose** | Patient clinical state tracking and transitions |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Clinical Team |
| **Version** | 1.0.0 |
| **Databases** | PostgreSQL |
| **Dependencies** | Clinical Engine |

### 1.4 Clinical Service

| Attribute | Value |
|-----------|-------|
| **Name** | Clinical Service |
| **Module** | `backend/app/services/clinical_service.py` |
| **Purpose** | Clinical workflow orchestration |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Clinical Team |
| **API Endpoints** | Used by `routes/clinical.py` |

---

## 2. Lab Domain Services

### 2.1 Order Service

| Attribute | Value |
|-----------|-------|
| **Name** | Order Service |
| **Module** | `backend/app/services/order_service.py` |
| **Purpose** | Lab order creation, validation, lifecycle management |
| **Status** | 🟢 PRODUCTION |
| **Owner** | LIMS Team |
| **Version** | 2.1.0 |
| **API Endpoints** | `POST /api/orders`, `GET /api/orders/{id}`, `PUT /api/orders/{id}`, `POST /api/orders/{id}/validate` |
| **Events Emitted** | `order.created`, `order.completed`, `order.validated`, `order.cancelled` |
| **Events Consumed** | `patient.updated`, `result.finalized` |
| **Databases** | PostgreSQL (`lab_orders` table) |
| **Dependencies** | `backend/app/domain/order_state.py`, `backend/app/models/lab_order.py`, Outbox Service |
| **SLA** | P95 < 200ms |
| **Certification** | Gold |

### 2.2 Patient Service

| Attribute | Value |
|-----------|-------|
| **Name** | Patient Service |
| **Module** | `backend/app/services/patient_service.py` |
| **Purpose** | Patient management, demographics, MPI integration |
| **Status** | 🟢 PRODUCTION |
| **Owner** | LIMS Team |
| **Version** | 2.0.0 |
| **API Endpoints** | `POST /api/patients`, `GET /api/patients/{id}`, `PUT /api/patients/{id}` |
| **Events Emitted** | `patient.created`, `patient.updated`, `patient.merged` |
| **Events Consumed** | `citizen.resolved` |
| **Databases** | PostgreSQL (`patients` table) |
| **Dependencies** | MPI Service, Identity Service |
| **SLA** | P95 < 200ms |
| **Certification** | Gold |

### 2.3 Result Service

| Attribute | Value |
|-----------|-------|
| **Name** | Result Service |
| **Module** | Internal (in `routes/results.py` + services) |
| **Purpose** | Lab result entry, validation, and finalization |
| **Status** | 🟢 PRODUCTION |
| **Owner** | LIMS Team |
| **Version** | 2.0.0 |
| **API Endpoints** | `POST /api/results`, `GET /api/results/{id}`, `POST /api/results/{id}/validate` |
| **Events Emitted** | `result.created`, `result.finalized`, `result.validated` |
| **Databases** | PostgreSQL (`lab_results` table) |
| **Dependencies** | Order Service, `backend/app/domain/order_state.py` |
| **SLA** | P95 < 200ms |
| **Certification** | Gold |

### 2.4 Sample Service

| Attribute | Value |
|-----------|-------|
| **Name** | Sample Service |
| **Module** | `backend/app/services/` (in `routes/samples.py`) |
| **Purpose** | Sample tracking, barcode, chain of custody |
| **Status** | 🟢 PRODUCTION |
| **Owner** | LIMS Team |
| **Version** | 2.0.0 |
| **API Endpoints** | `POST /api/samples`, `GET /api/samples/{id}`, tracking endpoints |
| **Databases** | PostgreSQL (`samples` table) |
| **Dependencies** | Order Service |

### 2.5 Quality Control Service

| Attribute | Value |
|-----------|-------|
| **Name** | Quality Control Service |
| **Module** | `backend/app/routes/quality_control.py`, `backend/app/lims/quality.py` |
| **Purpose** | Lab quality control, calibration, delta checks |
| **Status** | 🟢 PRODUCTION |
| **Owner** | LIMS Team |
| **Version** | 1.0.0 |
| **API Endpoints** | Quality control routes |
| **Databases** | PostgreSQL (`qc_*` tables) |
| **Dependencies** | LIMS domain |

### 2.6 Claims Service

| Attribute | Value |
|-----------|-------|
| **Name** | Claims Service |
| **Module** | `backend/app/services/claims_service.py` |
| **Purpose** | Insurance claims processing |
| **Status** | 🟡 BETA |
| **Owner** | Financial Team |
| **API Endpoints** | Claims routes |
| **Databases** | PostgreSQL (`claims` table) |
| **Dependencies** | Order Service, Insurance Gateway |

---

## 3. National Domain Services

### 3.1 MPI Service (Master Patient Index)

| Attribute | Value |
|-----------|-------|
| **Name** | MPI Service |
| **Module** | `backend/app/services/mpi/` |
| **Purpose** | Patient identity resolution, deduplication, cross-lab linking |
| **Status** | 🟢 PRODUCTION |
| **Owner** | National Team |
| **Version** | 1.0.0 |
| **API Endpoints** | `POST /mpi/resolve`, `POST /mpi/match`, `GET /mpi/claims/{id}` |
| **Events Emitted** | `citizen.registered`, `citizen.merged`, `identity.claimed` |
| **Events Consumed** | `patient.created`, `patient.updated` |
| **Databases** | PostgreSQL (`citizens`, `identity_claims`, `mpi_merge_audit`) |
| **Dependencies** | Identity Service, Blocking (`blocking.py`), Matcher (`matcher.py`) |
| **SLA** | P95 < 500ms |
| **Certification** | Gold |

### 3.2 Citizen Service

| Attribute | Value |
|-----------|-------|
| **Name** | Citizen Service |
| **Module** | `backend/app/national/services/citizen_service.py` |
| **Purpose** | Canonical citizen record management |
| **Status** | 🟢 PRODUCTION |
| **Owner** | National Team |
| **Version** | 1.0.0 |
| **API Endpoints** | `GET /national/citizens/{id}`, `PUT /national/citizens/{id}` |
| **Events Emitted** | `citizen.updated`, `citizen.deceased`, `citizen.merged` |
| **Databases** | PostgreSQL (`national_citizens` table) |
| **Dependencies** | `backend/app/national/domain/citizen.py`, National Identity Gateway |
| **SLA** | P95 < 200ms |
| **Certification** | Gold |

### 3.3 Identity Service

| Attribute | Value |
|-----------|-------|
| **Name** | Identity Service |
| **Module** | `backend/app/services/identity_service.py`, `backend/app/platform/identity.py` |
| **Purpose** | Platform-level identity management |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **Version** | 1.0.0 |
| **API Endpoints** | Internal |
| **Events Emitted** | `identity.verified`, `identity.revoked` |
| **Databases** | Redis (session), PostgreSQL (users) |
| **Dependencies** | `backend/app/security/auth.py` |
| **SLA** | P95 < 100ms |
| **Certification** | Gold |

### 3.4 Identity Matching Service

| Attribute | Value |
|-----------|-------|
| **Name** | Identity Matching |
| **Module** | `backend/app/services/identity_matching.py` |
| **Purpose** | Identity matching strategies |
| **Status** | 🟢 PRODUCTION |
| **Owner** | National Team |
| **API Endpoints** | Internal (used by MPI) |
| **Dependencies** | MPI Service |

### 3.5 Encounter Service

| Attribute | Value |
|-----------|-------|
| **Name** | Encounter Service |
| **Module** | `backend/app/national/services/encounter_service.py` |
| **Purpose** | Clinical encounter tracking |
| **Status** | 🟡 BETA |
| **Owner** | National Team |
| **Databases** | PostgreSQL (`encounters` table) |
| **Events Emitted** | `encounter.created`, `encounter.completed` |

### 3.6 Family Service

| Attribute | Value |
|-----------|-------|
| **Name** | Family Service |
| **Module** | `backend/app/national/services/family_service.py` |
| **Purpose** | Family-linked citizen management |
| **Status** | 🟡 BETA |
| **Owner** | National Team |
| **Databases** | PostgreSQL (`family_*` tables) |

---

## 4. Platform Services

### 4.1 Identity Platform Service

| Attribute | Value |
|-----------|-------|
| **Name** | Platform Identity |
| **Module** | `backend/app/platform/identity.py` |
| **Purpose** | Standardized identity interface wrapping security/auth |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **Dependencies** | `backend/app/security/auth.py` |

### 4.2 Caching Service

| Attribute | Value |
|-----------|-------|
| **Name** | Caching Service |
| **Module** | `backend/app/platform/caching.py`, `backend/app/core/cache_manager.py` |
| **Purpose** | Multi-tier caching |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **Dependencies** | Redis |
| **SLA** | P95 < 5ms (local), < 20ms (Redis) |

### 4.3 Search Service

| Attribute | Value |
|-----------|-------|
| **Name** | Platform Search |
| **Module** | `backend/app/platform/search.py` |
| **Purpose** | Cross-entity search |
| **Status** | 🟡 BETA |
| **Owner** | Platform Team |
| **Dependencies** | PostgreSQL full-text search |

### 4.4 Sync Service

| Attribute | Value |
|-----------|-------|
| **Name** | Platform Sync |
| **Module** | `backend/app/platform/sync.py` |
| **Purpose** | Edge-to-cloud synchronization |
| **Status** | 🟡 BETA |
| **Owner** | Platform Team |

### 4.5 Audit Service

| Attribute | Value |
|-----------|-------|
| **Name** | Audit Service |
| **Module** | `backend/app/services/audit_service.py`, `backend/app/audit/audit_log.py` |
| **Purpose** | Audit logging with hash chain |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Security Team |
| **Databases** | PostgreSQL (`audit_logs` table) |
| **SLA** | P95 < 50ms (write), sync |

### 4.6 Outbox Service

| Attribute | Value |
|-----------|-------|
| **Name** | Outbox Service |
| **Module** | `backend/app/services/outbox_service.py` |
| **Purpose** | Transactional outbox for reliable event delivery |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **Version** | 2.0.0 |
| **Events Emitted** | All domain events |
| **Databases** | PostgreSQL (`outbox_events` table) |
| **Dependencies** | `backend/app/kernel/event_bus/`, `backend/app/models/outbox.py` |
| **SLA** | Event delivery within 10s |
| **Certification** | Gold |

### 4.7 PDF Report Service

| Attribute | Value |
|-----------|-------|
| **Name** | PDF Report Service |
| **Module** | `backend/app/services/pdf_report.py`, `shared/pdf/generator.py` |
| **Purpose** | PDF report generation |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **Dependencies** | ReportLab |
| **SLA** | PDF generation < 3s |

### 4.8 Patient Card Service

| Attribute | Value |
|-----------|-------|
| **Name** | Patient Card Service |
| **Module** | `backend/app/services/patient_card.py` |
| **Purpose** | QR-backed digital patient cards |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **API Endpoints** | `GET /api/patient-card/{token}` |
| **Dependencies** | `backend/app/security/encryption.py` (HMAC signing) |

### 4.9 Critical Alerts Service

| Attribute | Value |
|-----------|-------|
| **Name** | Critical Alerts Service |
| **Module** | `backend/app/services/critical_alerts.py` |
| **Purpose** | Critical result alerts |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Clinical Team |
| **Events Emitted** | `alert.critical.result` |
| **Dependencies** | Notifications Service |

### 4.10 Care Continuum Service

| Attribute | Value |
|-----------|-------|
| **Name** | Care Continuum |
| **Module** | `backend/app/services/care_continuum_service.py` |
| **Purpose** | Patient care continuity tracking |
| **Status** | 🟡 BETA |
| **Owner** | Clinical Team |

---

## 5. Integration Services

### 5.1 EHR Service

| Attribute | Value |
|-----------|-------|
| **Name** | EHR Service |
| **Module** | `backend/app/services/ehr_service.py`, `backend/app/ehr/` |
| **Purpose** | Electronic Health Record integration |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Integration Team |
| **API Endpoints** | `GET /api/ehr/patients/{id}`, FHIR endpoints |
| **Events Emitted** | `ehr.record.updated`, `ehr.share.consented` |
| **Dependencies** | National Service, FHIR Mappers |

### 5.2 Data Platform Service

| Attribute | Value |
|-----------|-------|
| **Name** | Data Platform Service |
| **Module** | `backend/app/services/data_platform_service.py` |
| **Purpose** | Data aggregation and analytics platform |
| **Status** | 🟡 BETA |
| **Owner** | Analytics Team |

### 5.3 Hospital Service

| Attribute | Value |
|-----------|-------|
| **Name** | Hospital Service |
| **Module** | `backend/app/services/hospital_service.py`, `backend/app/hospital/` |
| **Purpose** | Hospital information system integration |
| **Status** | 🟡 BETA |
| **Owner** | Integration Team |

---

## 6. AI Services

### 6.1 Ali Reza Engine

| Attribute | Value |
|-----------|-------|
| **Name** | Ali Reza Engine |
| **Module** | `backend/app/services/ali_reza_engine.py`, `backend/app/services/ali_reza.py` |
| **Purpose** | Arabic-first clinical diagnostic support AI |
| **Status** | 🟡 BETA |
| **Owner** | AI Team |
| **API Endpoints** | `POST /api/ai/interpret`, `POST /api/ai/diagnose` |
| **Dependencies** | `shared/ai/client.py`, `backend/app/ai/guardrails.py` |
| **SLA** | P95 < 5s |
| **Certification** | Silver |

### 6.2 SAMIR Engine

| Attribute | Value |
|-----------|-------|
| **Name** | SAMIR Engine |
| **Module** | `backend/app/services/samir_engine.py`, `backend/app/services/samir.py` |
| **Purpose** | Predictive analytics and epidemiology AI |
| **Status** | 🟡 BETA |
| **Owner** | AI Team |
| **Dependencies** | `shared/ai/`, Clinical Intelligence |

### 6.3 Interpretation Service

| Attribute | Value |
|-----------|-------|
| **Name** | Interpretation Service |
| **Module** | `backend/app/services/interpretation.py` |
| **Purpose** | Clinical result interpretation |
| **Status** | 🟢 PRODUCTION |
| **Owner** | AI Team |
| **Dependencies** | `shared/ai/client.py` |

### 6.4 Epidemiology Service

| Attribute | Value |
|-----------|-------|
| **Name** | Epidemiology Service |
| **Module** | `backend/app/services/epidemiology.py` |
| **Purpose** | Disease surveillance and outbreak detection |
| **Status** | 🟡 BETA |
| **Owner** | Public Health Team |

---

## 7. Notifications Services

### 7.1 Notification Service

| Attribute | Value |
|-----------|-------|
| **Name** | Notification Service |
| **Module** | `backend/app/notifications/service.py` |
| **Purpose** | Multi-channel notification delivery |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **Version** | 1.0.0 |
| **Channels** | SMS, Email, Push, Telegram |
| **Databases** | PostgreSQL (notification log) |
| **Dependencies** | `shared/notifications/`, Circuit Breaker |
| **SLA** | Delivery within 30s |
| **Certification** | Gold |

### 7.2 Telegram Gateway

| Attribute | Value |
|-----------|-------|
| **Name** | Telegram Gateway |
| **Module** | `backend/app/notifications/telegram.py` |
| **Purpose** | Telegram notification delivery |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **Dependencies** | `backend/app/gateways/base.py` |

---

## 8. Infrastructure Services

### 8.1 Config Service

| Attribute | Value |
|-----------|-------|
| **Name** | Config Service |
| **Module** | `backend/app/config.py`, `backend/app/kernel/config/` |
| **Purpose** | Environment-based configuration management |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |

### 8.2 Database Service

| Attribute | Value |
|-----------|-------|
| **Name** | Database Service |
| **Module** | `backend/app/database.py` |
| **Purpose** | Connection pool, session management, context vars |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **SLA** | Connection acquisition < 5ms |

### 8.3 Self-Healing Service

| Attribute | Value |
|-----------|-------|
| **Name** | Self-Healing Service |
| **Module** | `backend/app/core/self_healing.py` |
| **Purpose** | Circuit breaker, degraded mode, health monitoring |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **Version** | 2.0.0 |
| **SLA** | Circuit detection < 3 failures |
| **Certification** | Gold |

### 8.4 Auto-Repair Service

| Attribute | Value |
|-----------|-------|
| **Name** | Auto-Repair Service |
| **Module** | `backend/app/core/auto_repair.py` |
| **Purpose** | Automatic GC, pool recycle, leak detection |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |

### 8.5 Kill Switch Service

| Attribute | Value |
|-----------|-------|
| **Name** | Kill Switch Service |
| **Module** | `backend/app/core/kill_switch.py`, `backend/app/kernel/features/kill_switch.py` |
| **Purpose** | Emergency feature/access termination |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Security Team |

### 8.6 Policy Engine

| Attribute | Value |
|-----------|-------|
| **Name** | Policy Engine |
| **Module** | `backend/app/core/policy_engine.py` |
| **Purpose** | Business policy enforcement |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |

### 8.7 Risk Engine

| Attribute | Value |
|-----------|-------|
| **Name** | Risk Engine |
| **Module** | `backend/app/core/risk_engine.py` |
| **Purpose** | Clinical and operational risk assessment |
| **Status** | 🟡 BETA |
| **Owner** | Clinical Safety Team |

### 8.8 Feature Flags Service

| Attribute | Value |
|-----------|-------|
| **Name** | Feature Flags Service |
| **Module** | `backend/app/core/feature_flags.py`, `backend/app/kernel/features/` |
| **Purpose** | Per-tenant feature gating |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **SLA** | Feature resolution < 50ms |
| **Certification** | Gold |

### 8.9 Kernel Services

| Attribute | Value |
|-----------|-------|
| **Name** | Kernel |
| **Module** | `backend/app/kernel/` |
| **Purpose** | Module registry, plugin system, event bus, tenant management |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Platform Team |
| **SLA** | Internal |
| **Certification** | Gold |

---

## 9. Device Bridge Services

### 9.1 Device Bridge (LabLink-Core)

| Attribute | Value |
|-----------|-------|
| **Name** | Device Bridge |
| **Module** | `services/device_bridge/` |
| **Purpose** | Lab instrument integration (ASTM/HL7) |
| **Status** | 🟢 PRODUCTION |
| **Owner** | Device Integration Team |
| **Version** | 1.0.0 |
| **Protocols** | ASTM E1381-02, HL7 v2.5.1 |
| **Devices** | Sysmex, Roche, Mindray, generic |
| **Events Emitted** | `device.result.received`, `device.connected`, `device.disconnected` |
| **Databases** | Edge SQLite (local), forwards to GULA API |
| **Dependencies** | `shared/device/astm.py`, `shared/device/adapters.py`, `app/integration/gula_client.py` |
| **SLA** | Result forwarding < 5s |
| **Certification** | Silver |

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial master service catalog |

**Review Cycle**: This document must be updated when new services are added or existing services change significantly.
