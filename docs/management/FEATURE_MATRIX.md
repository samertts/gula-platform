# GULA Platform — Feature Matrix

**Version:** 1.0 | **Last Updated:** 2026-07-23

## Table of Contents

- [1. Feature Flag Overview](#1-feature-flag-overview)
- [2. Core Platform Features](#2-core-platform-features)
- [3. Clinical Features](#3-clinical-features)
- [4. National Platform Features](#4-national-platform-features)
- [5. Enterprise & Security Features](#5-enterprise--security-features)
- [6. Financial Features](#6-financial-features)
- [7. Infrastructure Features](#7-infrastructure-features)
- [8. Integration & Device Features](#8-integration--device-features)
- [9. Frontend & Portal Features](#9-frontend--portal-features)
- [10. Feature Flag Reference](#10-feature-flag-reference)

---

## 1. Feature Flag Overview

Two parallel flag systems govern feature availability:

**Per-tenant** (`backend/app/core/feature_flags.py`) — subscription-tier driven matrix with three tiers (starter, growth, enterprise), deployment mode overrides (single, multi_branch, government), and security level overrides (standard, high_security, air_gapped). Per-lab `FeatureFlag` rows can additionally enable or disable individual features.

**Deployment-wide** (`backend/app/config.py`, `backend/app/core/sndhs_flags.py`) — environment variable toggles that gate whole feature surfaces: SNDHS-lite (visits, national ID), Financial Engine, Ads, API docs, background tasks, and Kernel subsystems.

**Route modules:** 57 route modules in `backend/app/routes/` serve 500+ API endpoints.

---

## 2. Core Platform Features

| Feature | Backend | Frontend | API | Tests | Documentation | Status | Flag |
|---------|---------|----------|-----|-------|---------------|--------|------|
| User Authentication (JWT) | ✅ `routes/login.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| User Registration | ✅ `routes/register.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Multi-Factor Auth | ✅ `routes/mfa.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `two_factor_required` (per-tenant) |
| Password Reset | ✅ `routes/password_reset.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Lab Management | ✅ `routes/labs.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Patient Management | ✅ `routes/patients.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `patient_management` |
| Order Management | ✅ `routes/test_results.py`, `clinical_orders.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `basic_results` |
| Result Entry | ✅ `routes/results.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `basic_results` |
| Result Verification | ✅ `routes/results.py` | ✅ | ✅ | ✅ | ✅ | **Live** | Per-tenant (growth+) |
| Sample Tracking | ✅ `routes/samples.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `sample_tracking` |
| Quality Control | ✅ `routes/quality_control.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `quality_control` (growth+) |
| Critical Alerts | ✅ `routes/critical_alerts.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `critical_alerts` (growth+) |
| Patient Cards (QR) | ✅ `routes/patient_card.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `qr_codes` |
| Statistics & Trends | ✅ `routes/stats.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `advanced_analytics` (growth+) |
| Dashboard | ✅ `routes/dashboard.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Batch Operations | ✅ `routes/batch.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `batch_import`, `batch_export` (growth+) |
| PDF Reports | ✅ `routes/results.py` + print pipeline | ✅ | ✅ | ✅ | ✅ | **Live** | `pdf_reports` |
| QR Code Generation | ✅ `routes/qr.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `qr_codes` |
| Mobile API | ✅ `routes/mobile.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `mobile_access` |
| Notifications | ✅ `routes/notifications.py`, `notifications/` | ✅ | ✅ | ✅ | ✅ | **Live** | `notifications` |
| Device Results Import | ✅ `routes/device_results.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `device_results` (growth+) |
| Setup/Onboarding | ✅ `routes/setup.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Admin Endpoints | ✅ `routes/admin.py`, `admin_log_level.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Tier Management | ✅ `routes/tiers.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |

---

## 3. Clinical Features

| Feature | Backend | Frontend | API | Tests | Documentation | Status | Flag |
|---------|---------|----------|-----|-------|---------------|--------|------|
| Clinical AI Co-pilot | ✅ `routes/ai.py`, `ai/` | ✅ | ✅ | ✅ | ✅ | **Live** | `ai_interpretation` (enterprise) |
| Clinical AI Platform | ✅ `routes/ai_platform.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `ai_interpretation` (enterprise) |
| AI Telemetry | ✅ `routes/ai_telemetry.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Clinical Decision Support (CDS) | ✅ `routes/clinical.py` (CDSService) | ✅ | ✅ | ✅ | ✅ | **Live** | Enterprise |
| Clinical Documentation (SOAP) | ✅ `routes/clinical_documentation.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Clinical Orders (CPOE) | ✅ `routes/clinical_orders.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Clinical Quality Measures | ✅ `routes/clinical_quality.py` | ✅ | ✅ | ✅ | ✅ | **Live** | Enterprise |
| Care Continuum | ✅ `routes/care_continuum.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| EHR Integration | ✅ `routes/ehr.py`, `routes/ehr_fhir.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `ehr_integration` (growth+) |
| FHIR R4 API | ✅ `routes/ehr_fhir.py` (1469 LOC) | ✅ | ✅ | ✅ | ✅ | **Live** | `ehr_integration` |
| Terminology Service | ✅ `routes/clinical.py` (TerminologyService) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Medication Management | ✅ `routes/ehr_fhir.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Care Plans | ✅ `routes/ehr_fhir.py` (CarePlan) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| AI Anomaly Detection | ✅ `app/ai/` | ✅ | ✅ | ✅ | ✅ | **Live** | `ai_anomaly_detection` (enterprise) |
| AI Epidemiology | ✅ `app/ai/` | ✅ | ❌ | ✅ | ✅ | **Live** | `ai_epidemiology` (enterprise) |
| Hospital Management | ✅ `routes/hospital.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Identity Scan (ID) | ✅ `routes/id_scan.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Optimizer (AI System) | ✅ `routes/optimizer.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |

---

## 4. National Platform Features

| Feature | Backend | Frontend | API | Tests | Documentation | Status | Flag |
|---------|---------|----------|-----|-------|---------------|--------|------|
| SNDHS-lite Integration | ✅ Migrations + backfill script | ❌ | ✅ | ✅ | ✅ `docs/sndhs/` (22 files) | **Flagged** | `SNDHS_ENABLE_VISITS` (default off) |
| Visit Tracking | ✅ `visits` table + `lab_orders.visit_id` | ❌ | ✅ | ✅ | ✅ | **Flagged** | `SNDHS_ENABLE_VISITS` (default off) |
| National ID Support | ✅ `patients.national_id` + `sndhs_health_id` | ❌ | ✅ | ✅ | ✅ | **Flagged** | `SNDHS_ENABLE_NATIONAL_ID` (default off) |
| Enhanced Audit Log (v2) | ✅ `audit_logs_v2` table + hash chain | ✅ | ✅ | ✅ | ✅ | **Flagged** | `SNDHS_ENABLE_VISITS` / `SNDHS_ENABLE_NATIONAL_ID` |
| National Data Platform | ✅ `routes/national_data.py` (943 LOC) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| National Identity | ✅ `routes/national_identity.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| National Streaming | ✅ `routes/national_streaming.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Master Data Management | ✅ `national_data/` (GoldenRecord, MDM) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Citizen Portal | ✅ `routes/citizen_portal.py` (493 LOC) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Consent Management | ✅ `routes/consent.py`, `services/consent_service.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Compliance/Regulatory | ✅ `routes/compliance.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `government_reporting` (enterprise) |
| Claims/Insurance | ✅ `routes/claims.py`, `routes/insurance.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `insurance_integration` (growth+) |
| NHOP Integration | ✅ `nhop-platform/` (separate app) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| National Health Data Warehouse | ✅ `nhdw/` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Public Health Surveillance | ✅ `public_health/` | ✅ | ✅ | ✅ | ✅ | **Live** | Enterprise |
| Command Center | ✅ `command_center/` | ✅ | ✅ | ✅ | ✅ | **Live** | Enterprise |

---

## 5. Enterprise & Security Features

| Feature | Backend | Frontend | API | Tests | Documentation | Status | Flag |
|---------|---------|----------|-----|-------|---------------|--------|------|
| RBAC (10 roles × 16 permissions) | ✅ `security/rbac.py`, `routes/authorization.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| ABAC (Attribute-Based Access) | ✅ `security/abac.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Audit Trail (SHA-256 hash chain) | ✅ `audit/`, `services/audit_service.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `audit_log` / `audit_chain` |
| Tenant Isolation | ✅ Enforced at DB level (lab_id filter) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Break Glass Access | ✅ `routes/authorization.py` (BreakGlassService) | ✅ | ✅ | ✅ | ✅ | **Live** | Enterprise |
| Delegation | ✅ `routes/authorization.py` (DelegationService) | ✅ | ✅ | ✅ | ✅ | **Live** | Enterprise |
| Service Accounts | ✅ `routes/service_accounts.py` | ✅ | ✅ | ✅ | ✅ | **Live** | Enterprise (`api_access`) |
| OAuth2 Provider | ✅ `routes/oauth2.py` (388 LOC) | ✅ | ✅ | ✅ | ✅ | **Live** | Enterprise |
| SAML Authentication | ✅ `routes/saml.py`, `security/saml_service.py` | ✅ | ✅ | ✅ | ✅ | **Live** | Enterprise |
| Security Endpoints | ✅ `routes/security.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Identity Linking | ✅ `routes/identity.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Multi-Branch Support | ✅ DB model + overrides | ✅ | ✅ | ✅ | ✅ | **Live** | `multi_branch` (enterprise) |
| Government Reporting | ✅ `compliance.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `government_reporting` (enterprise) |
| Custom Branding | ✅ `feature_flags.py` tier def | ✅ | ✅ | ✅ | ✅ | **Live** | `custom_branding` (enterprise) |
| White Label | ✅ `feature_flags.py` tier def | ✅ | ✅ | ✅ | ❌ | **Live** | `white_label` (enterprise) |
| Priority Support | ✅ `feature_flags.py` tier def | ✅ | ❌ | ❌ | ❌ | **Live** | `priority_support` (enterprise) |
| SLA Guarantee | ✅ `feature_flags.py` tier def | ✅ | ❌ | ❌ | ❌ | **Live** | `sla_guarantee` (enterprise) |
| Identity Governance (MPI) | ✅ `services/governance/` (Fellegi-Sunter) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Family Registry | ✅ `services/governance/family_registry.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Identity Merge Engine | ✅ `services/governance/merge_engine.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |

---

## 6. Financial Features

| Feature | Backend | Frontend | API | Tests | Documentation | Status | Flag |
|---------|---------|----------|-----|-------|---------------|--------|------|
| Financial Engine (Billing) | ✅ `financial/routes.py`, `services.py`, `models.py` | ❌ | ✅ Flag-gated | ❌ | ❌ | **Phase B** (routes exist, flagged off) | `ENABLE_FINANCIAL_ENGINE` (default off) |
| Invoicing | ✅ `financial/` (InvoiceService) | ❌ | ✅ Flag-gated | ❌ | ❌ | **Phase B** | `ENABLE_FINANCIAL_ENGINE` |
| Payments | ✅ `financial/` (PaymentService) | ❌ | ✅ Flag-gated | ❌ | ❌ | **Phase B** | `ENABLE_FINANCIAL_ENGINE` |
| Pricing Rules | ✅ `financial/pricing.py` | ❌ | ✅ Flag-gated | ❌ | ❌ | **Phase B** | `ENABLE_FINANCIAL_ENGINE` |
| Provider Ranking | ✅ `financial/ranking.py` | ❌ | ✅ Flag-gated | ❌ | ❌ | **Phase B** | `ENABLE_FINANCIAL_ENGINE` |
| Campaigns/Ads | ✅ Schema (`fin_campaigns`, `fin_conversions`, `fin_fraud_flags`) | ❌ | ❌ | ❌ | ❌ | **Schema only** (Phase A) | `ENABLE_FINANCIAL_ENGINE` + `ENABLE_ADS` |
| Financial Reports | ✅ `financial/` (FinancialReportService) | ❌ | ✅ Flag-gated | ❌ | ❌ | **Phase B** | `ENABLE_FINANCIAL_ENGINE` |

---

## 7. Infrastructure Features

| Feature | Backend | Status | Notes |
|---------|---------|--------|-------|
| Self-Healing System (3-layer) | ✅ `core/self_healing.py` | **Live** | Circuit breaker + auto-repair + adaptive concurrency |
| Circuit Breaker (DB/Redis) | ✅ `core/self_healing.py` | **Live** | Isolates failing dependencies; flips to degraded mode |
| Auto-Repair Engine | ✅ `core/auto_repair.py` | **Live** | GC, pool recycle, reconnects |
| Adaptive Concurrency | ✅ `main.py::_adaptive_concurrency_loop` | **Live** | Halves `_MAX_CONCURRENT` on slow DB readings |
| Startup Guard | ✅ `core/startup_guard.py` | **Live** | Blocks readiness until config/DB/migrations/seeds validated |
| Health Endpoints (5 paths) | ✅ `/health`, `/health/live`, `/health/ready`, `/health/status`, `/health/deep` | **Live** | Liveness, readiness, diagnostic, deep probe |
| Rate Limiting | ✅ `security/rate_limit.py`, `firewall/` | **Live** | Auth (10/min), public (30/min), per-user, per-IP |
| Prometheus Metrics | ✅ `routes/metrics.py` | **Live** | Bearer-token protected in production |
| Audit Logging | ✅ `audit/` + `services/audit_service.py` | **Live** | SHA-256 hash chain, immutable |
| Outbox Pattern (Event Delivery) | ✅ `tasks/`, `services/outbox_service.py` | **Live** | Guaranteed at-least-once delivery |
| Background Task Queue | ✅ `tasks/` (Redis-backed) | **Live** | `FEATURE_BACKGROUND_TASKS` / worker runtime |
| Multi-Level Cache (L1+L2) | ✅ `core/cache_manager.py` | **Live** | In-memory (L1) + Redis (L2); `CACHE_ENABLED` |
| Read Replica Support | ✅ `config.py` (`READ_REPLICA_URL`) | **Live** | Routes reads to PgBouncer-managed replicas |
| Request ID & Correlation | ✅ Middleware + `contextvars` | **Live** | `X-Request-ID` bound to log context + DB |
| Security Headers | ✅ `SecurityHeadersMiddleware` | **Live** | CSP, HSTS, X-Frame-Options, etc. |
| GZip Compression | ✅ `GZipMiddleware` | **Live** | Response compression |
| Max Body Size Guard | ✅ `MaxBodySizeMiddleware` | **Live** | 413 above `MAX_REQUEST_BODY_MB` (default 10) |
| Degraded Mode | ✅ `DegradedModeMiddleware` | **Live** | Rejects writes when DB circuit open |
| Concurrency Limiting | ✅ `ConcurrencyLimitMiddleware` | **Live** | 50 in-flight per worker; clinical writes exempt |
| Kernel Runtime | ✅ `kernel/` (DI, event bus, plugins, config, features) | **Live** | 12-phase boot sequence; 8 subsystem flags |
| Plugin System | ✅ `kernel/` (plugin system) | **Live** | `KERNEL_ENABLE_PLUGINS` (default on) |
| Event Bus | ✅ `kernel/` (EventBus + snapshot + recovery) | **Live** | `KERNEL_ENABLE_EVENT_BUS` (default on) |
| Feature Flag Manager | ✅ `kernel/features/` (CapabilityFlagManager) | **Live** | `KERNEL_ENABLE_FEATURES` (default on) |
| Multi-Tenant Engine | ✅ `kernel/` (Tenant engine) | **Live** | `KERNEL_ENABLE_TENANT` (default on) |
| Health Alert Watchdog | ✅ `main.py::_health_alert_loop` | **Live** | GREEN/YELLOW/RED scoring + webhook alerts |
| Policy Engine | ✅ `core/policy_engine.py` | **Live** | Control layer policy enforcement |
| Backup (pg_dump) | ✅ `Makefile` (`make backup`) | **Live** | Compressed SQL dumps |
| HAProxy Load Balancing | ✅ `config/haproxy/` | **Live** | `make scale REPLICAS=N` |
| Blue-Green Deployment | ✅ `.github/workflows/blue-green-deploy.yml` | **Live** | CI/CD pipeline |
| Canary Deployment | ✅ `.github/workflows/canary-deploy.yml` | **Live** | CI/CD pipeline |
| Auto-Rollback | ✅ `.github/workflows/auto-rollback.yml` | **Live** | On health check failure |
| Kill Switch (Control Layer) | ✅ `main.py` + DigitalOcean scripts | **Live** | Emergency traffic block |
| Edge AI Platform | ✅ `routes/edge.py`, `edge/`, `edge_agent/` | **Live** | Off-site/offline edge agent for remote labs |
| Sentinel/Cluster Redis | ✅ `config.py` (`REDIS_SENTINEL_HOSTS`, `REDIS_CLUSTER_NODES`) | **Live** | HA Redis configuration |
| Cloudflare Integration | ✅ `gateways/cloudflare.py`, `cloudflare/` config | **Live** | DNS, WAF, Workers, R2 storage |
| Supabase Integration | ✅ `config.py` (`SUPABASE_URL`, `SUPABASE_*_KEY`) | **Optional** | Managed Postgres migration path |

---

## 8. Integration & Device Features

| Feature | Backend | Frontend | API | Tests | Documentation | Status | Flag |
|---------|---------|----------|-----|-------|---------------|--------|------|
| Integration Platform (ESB) | ✅ `integration/` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Connector Framework | ✅ `integration/connector/` (REST, GraphQL, WebSocket, gRPC, DICOM) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Device Bridge (ASTM/HL7) | ✅ `services/device_bridge/` (LabLink-Core) | ✅ | ✅ | ✅ | ✅ | **Live** | `device_results` |
| HL7/FHIR Integration | ✅ `integration/hl7_fhir/` | ✅ | ✅ | ✅ | ✅ | **Live** | `ehr_integration` |
| CDC Integration | ✅ `integration/` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Government Adapters (NID, Insurance, Residency) | ✅ `gateways/` (stub/live/shadow modes) | ✅ | ✅ | ✅ | ✅ | **Live** | `national_id_lookup`, `insurance_integration` |
| Cloudflare Control Plane | ✅ `gateways/cloudflare.py` | ✅ | ✅ | ✅ | ✅ | **Live** | `ADAPTER_MODE_CLOUDFLARE` |
| Google AI (Gemini) | ✅ `gateways/google_ai.py`, `config.py` | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Groq AI | ✅ `config.py` (`GROQ_API_KEY`) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Ollama Local AI | ✅ `config.py` (`OLLAMA_BASE_URL`) | ✅ | ✅ | ✅ | ✅ | **Live** | None |
| Firebase Cloud Messaging | ✅ `config.py` (`FCM_SERVER_KEY`) | ✅ | ✅ | ✅ | ✅ | **Optional** | None (push notifications) |

---

## 9. Frontend & Portal Features

| Feature | Location | Status | Notes |
|---------|----------|--------|-------|
| React SPA (Lab Dashboard) | `frontend-v2/` | **Live** | Rich React app; formerly `samertts/Front-end-` |
| Static HTML PWA | `frontend/` | **Live** | Offline-capable |
| tRPC + React SPA (Lightweight) | `client/` | **Live** | Lightweight client connected to backend API |
| Citizen Portal (React) | `frontend-v2/` | **Live** | Patient self-service: results, orders, health records |
| Ministry Command Centre | `frontend-v2/` | **Live** | National-level oversight dashboard |
| Doctor Clinical Workspace | `frontend-v2/` | **Live** | CPOE, clinical documentation, patient workspace |
| Laboratory Desktop Professional | `frontend-v2/` | **Live** | Specimen lifecycle, QC, instrument integration |
| Predictive Analytics | `frontend-v2/` | **Live** | AI-powered analytics dashboards |
| Multi-Language i18n (5 lang) | `frontend-v2/` | **Live** | Arabic-first UI |
| PWA Offline Support | `frontend-v2/` | **Live** | Offline capability for critical workflows |
| NHOP Platform UI | `nhop-platform/` | **Live** | National Health Oversight Platform UI |

---

## 10. Feature Flag Reference

### 10.1 Per-Tenant Feature Flags (Tier-Based)

| Flag | Starter | Growth | Enterprise | Description |
|------|---------|--------|------------|-------------|
| `patient_management` | ✅ | ✅ | ✅ | Patient CRUD, search, history |
| `basic_results` | ✅ | ✅ | ✅ | Lab result entry and viewing |
| `sample_tracking` | ✅ | ✅ | ✅ | Specimen lifecycle tracking |
| `pdf_reports` | ✅ | ✅ | ✅ | PDF report generation |
| `qr_codes` | ✅ | ✅ | ✅ | QR code generation and scanning |
| `notifications` | ✅ | ✅ | ✅ | Push/WhatsApp/SMS notifications |
| `audit_log` | ✅ | ✅ | ✅ | Standard audit logging |
| `mobile_access` | ✅ | ✅ | ✅ | Mobile API access |
| `quality_control` | ❌ | ✅ | ✅ | QC rules (Westgard, Levey-Jennings) |
| `batch_import` | ❌ | ✅ | ✅ | Batch data import |
| `batch_export` | ❌ | ✅ | ✅ | Batch data export |
| `ehr_integration` | ❌ | ✅ | ✅ | EHR/FHIR integration |
| `advanced_analytics` | ❌ | ✅ | ✅ | Statistics, trends, analytics API |
| `critical_alerts` | ❌ | ✅ | ✅ | Critical/panic value alerts |
| `insurance_integration` | ❌ | ✅ | ✅ | Insurance claim processing |
| `national_id_lookup` | ❌ | ✅ | ✅ | National ID verification (gov adapter) |
| `device_results` | ❌ | ✅ | ✅ | Device bridge integration |
| `multi_branch` | ❌ | ❌ | ✅ | Multi-branch lab management |
| `government_reporting` | ❌ | ❌ | ✅ | Government compliance reporting |
| `ai_interpretation` | ❌ | ❌ | ✅ | AI-powered result interpretation |
| `ai_anomaly_detection` | ❌ | ❌ | ✅ | AI anomaly detection |
| `ai_epidemiology` | ❌ | ❌ | ✅ | AI epidemiological surveillance |
| `custom_branding` | ❌ | ❌ | ✅ | Custom lab branding |
| `api_access` | ❌ | ❌ | ✅ | External API access (service accounts) |
| `sla_guarantee` | ❌ | ❌ | ✅ | SLA guarantee |
| `white_label` | ❌ | ❌ | ✅ | White-label deployment |
| `priority_support` | ❌ | ❌ | ✅ | Priority technical support |

### 10.2 Deployment Mode Overrides

| Mode | Added Features |
|------|---------------|
| `single` | (none) |
| `multi_branch` | `multi_branch`, `cross_branch_reports` |
| `government` | `government_reporting`, `compliance_dashboard`, `ministry_integration` |

### 10.3 Security Level Overrides

| Level | Added Features | Blocked Features |
|-------|---------------|------------------|
| `standard` | (none) | (none) |
| `high_security` | `two_factor_required`, `audit_chain`, `session_timeout_short` | (none) |
| `air_gapped` | `two_factor_required`, `audit_chain`, `session_timeout_short`, `air_gapped_mode` | `ai_interpretation`, `ai_anomaly_detection`, `ai_epidemiology`, `ehr_integration`, `insurance_integration`, `national_id_lookup`, `ministry_integration`, `notifications` |

### 10.4 Deployment-Wide Feature Flags (Environment Variables)

| Flag | Default | Scope | Description |
|------|---------|-------|-------------|
| `SNDHS_ENABLE_VISITS` | `false` | Deployment | Visit tracking (`visits` table + `lab_orders.visit_id`) |
| `SNDHS_ENABLE_NATIONAL_ID` | `false` | Deployment | National ID / health ID fields on patients |
| `ENABLE_FINANCIAL_ENGINE` | `false` | Deployment | Financial Engine routes (Phase B+ billing/invoicing) |
| `ENABLE_ADS` | `false` | Deployment | Advertising/campaign features (requires FINANCIAL_ENGINE) |
| `RUNTIME_MODE` | `api` | Deployment | Execution context: `api` / `worker` / `test` / `cli` |
| `FEATURE_BACKGROUND_TASKS` | `true` (worker) / `false` (api) | Deployment | Background worker startup (double-gated with RUNTIME_MODE) |
| `ENABLE_API_DOCS` | `false` | Deployment | Enable `/docs` / `/redoc` in production |
| `ADAPTER_MODE_DEFAULT` | `stub` | Deployment | External adapter mode: `stub` / `live` / `shadow` |
| `CACHE_ENABLED` | `true` | Deployment | Multi-level cache (L1+L2) |
| `READ_REPLICA_ENABLED` | `false` | Deployment | Read replica routing |
| `KERNEL_KILL_SWITCH` | `false` | Deployment | Emergency stop: blocks all autonomous kernel actions |
| `KERNEL_DEGRADED` | `false` | Deployment | Degraded mode (no plugin/module loading) |
| `KERNEL_ENABLE_PLUGINS` | `true` | Deployment | Enable plugin system |
| `KERNEL_ENABLE_EVENT_BUS` | `true` | Deployment | Enable internal event bus |
| `KERNEL_ENABLE_BACKGROUND` | `true` | Deployment | Enable background task processing |
| `KERNEL_ENABLE_FEATURES` | `true` | Deployment | Enable feature flag management |
| `KERNEL_ENABLE_CONFIG` | `true` | Deployment | Enable configuration engine |
| `KERNEL_ENABLE_TENANT` | `true` | Deployment | Enable multi-tenant engine |
| `KERNEL_ENABLE_GATEWAY` | `true` | Deployment | Enable internal API gateway |
| `GULA_ADAPTER_MODE_NID` | `stub` | Deployment | Override for gov-NID adapter |
| `GULA_ADAPTER_MODE_INSURANCE` | `stub` | Deployment | Override for insurance adapter |
| `GULA_ADAPTER_MODE_RESIDENCY` | `stub` | Deployment | Override for MoI residency adapter |
| `GULA_ADAPTER_MODE_CLOUDFLARE` | `stub` | Deployment | Override for Cloudflare control plane |

### 10.5 Resource Limits by Tier

| Resource | Starter | Growth | Enterprise |
|----------|---------|--------|------------|
| Max Patients | 500 | 5,000 | 99,999 |
| Max Staff | 5 | 20 | 999 |
| Max Branches | 1 | 1 | 50 |
| Max Orders/Day | 100 | 1,000 | 99,999 |
| Max AI Calls/Day | 0 | 0 | 500 |

---

## Appendix: Route Module Map

| Route Module | Features Served | LOC (approx) |
|-------------|-----------------|--------------|
| `routes/login.py` | Authentication | — |
| `routes/register.py` | Registration | — |
| `routes/mfa.py` | Multi-Factor Auth | — |
| `routes/password_reset.py` | Password Reset | — |
| `routes/labs.py` | Lab Management | — |
| `routes/patients.py` | Patient Management | — |
| `routes/test_results.py` | Order Management | — |
| `routes/results.py` | Result Entry/Verification | — |
| `routes/samples.py` | Sample Tracking | — |
| `routes/quality_control.py` | QC (Westgard/Levey-Jennings) | — |
| `routes/critical_alerts.py` | Critical Alerts | — |
| `routes/patient_card.py` | Patient Cards (QR) | — |
| `routes/stats.py` | Statistics & Trends | — |
| `routes/dashboard.py` | Dashboard | — |
| `routes/batch.py` | Batch Import/Export | — |
| `routes/qr.py` | QR Code Generation | — |
| `routes/mobile.py` | Mobile API | — |
| `routes/notifications.py` | Notifications (WhatsApp/SMS) | 141 |
| `routes/device_results.py` | Device Results | — |
| `routes/setup.py` | Lab Setup/Onboarding | — |
| `routes/admin.py` | Admin Endpoints | — |
| `routes/tiers.py` | Subscription Tier Management | 588 |
| `routes/authorization.py` | RBAC, ABAC, Break Glass, Delegation | 654 |
| `routes/security.py` | Security Settings | — |
| `routes/identity.py` | National ID Linking | 96 |
| `routes/service_accounts.py` | API Service Accounts | — |
| `routes/oauth2.py` | OAuth2 Provider | 388 |
| `routes/saml.py` | SAML Authentication | 74 |
| `routes/clinical.py` | CDS, Terminology, Clinical AI, Quality | 1,324 |
| `routes/clinical_orders.py` | CPOE | — |
| `routes/clinical_documentation.py` | SOAP Notes | — |
| `routes/clinical_quality.py` | Clinical Quality Measures | — |
| `routes/care_continuum.py` | Care Continuum | — |
| `routes/ehr.py` | EHR Integration | — |
| `routes/ehr_fhir.py` | FHIR R4 API | 1,469 |
| `routes/ai.py` | Clinical AI Co-pilot | — |
| `routes/ai_platform.py` | AI Platform | — |
| `routes/ai_telemetry.py` | AI Telemetry | — |
| `routes/optimizer.py` | System Optimizer | — |
| `routes/national_data.py` | National Data Platform | 943 |
| `routes/national_identity.py` | National Identity | — |
| `routes/national_streaming.py` | National Streaming | — |
| `routes/citizen_portal.py` | Citizen Portal | 493 |
| `routes/consent.py` | Consent Management | 191 |
| `routes/compliance.py` | Regulatory Compliance | — |
| `routes/claims.py` | Insurance Claims | — |
| `routes/insurance.py` | Insurance Integration | — |
| `routes/hospital.py` | Hospital Management | — |
| `routes/id_scan.py` | ID Document Scanning | — |
| `routes/canonical_patient.py` | Canonical Patient Record | — |
| `routes/integrations.py` | Integration Platform | — |
| `routes/edge.py` | Edge AI Platform | — |
| `routes/metrics.py` | Prometheus Metrics | — |
| `routes/admin_log_level.py` | Admin Log Level Control | — |
| `financial/routes.py` | Financial Engine (Phase B) | 430 |