# GULA Platform — Digital DNA Atlas

> **Version:** 2.1.0 | **Last Updated:** 2026-07-17 | **Classification:** CONFIDENTIAL
> Every component in the GULA Platform genome is catalogued below with a unique Digital DNA identifier and 20-dimensional trait vector.

---

## Master Index

| Section | DNA Prefix | Entries |
|---------|-----------|---------|
| 1. Backend Core | `DNA-BC` | 4 |
| 2. Core Infrastructure | `DNA-CI` | 17 |
| 3. Security Modules | `DNA-SEC` | 15 |
| 4. Route Modules | `DNA-RT` | 51 |
| 5. ORM Models | `DNA-MD` | 25 |
| 6. Services Layer | `DNA-SV` | 34 |
| 7. AI Modules | `DNA-AI` | 17 |
| 8. Frontend Applications | `DNA-FE` | 3 |
| 9. Microservices | `DNA-MS` | 9 |
| 10. Edge Agent | `DNA-EA` | 1 |
| 11. National Platform | `DNA-NP` | 2 |
| 12. Infrastructure | `DNA-INF` | 15 |
| 13. CI/CD | `DNA-CD` | 6 |
| 14. Database Migrations | `DNA-MG` | 47 |
| 15. Scripts | `DNA-SC` | 74+ |
| 16. Configuration Categories | `DNA-CF` | 37 |
| 17. Architecture Decision Records | `DNA-ADR` | 26 |
| 18. Test Suites | `DNA-TS` | 59 |
| 19. Domain & Supporting | `DNA-DM` | 12 |
| 20. Gateway Adapters | `DNA-GW` | 8 |
| 21. Task System | `DNA-TK` | 5 |
| 22. National Platform Modules | `DNA-NM` | 19 |

---

## Section 1: Backend Core (DNA-BC)

### DNA-BC-001: main.py — Application Entrypoint
- **File:** `backend/app/main.py`
- **Owner:** Platform Core Team
- **Purpose:** FastAPI app initialization, lifespan management, 11-layer middleware stack (MaxBodySize, RequestID, DocsAuth, CORS, RequestTiming, SecurityHeaders, GZip, Readiness, DegradedMode, Kernel, ConcurrencyLimit), route registration (100+ routers), global error handler, sentry init, background loop orchestration, kernel warmup
- **Business Domain:** Platform Foundation
- **Healthcare Domain:** Healthcare Infrastructure
- **Dependencies:** config.py, database.py, core/logging_config.py, core/startup_guard.py, core/self_healing.py, security/auth.py, security/redis_client.py, all 36+ route modules, all model packages (lims, hospital, nhdw, nursing, pharmacy, radiology, national_data)
- **Consumers:** gunicorn/uvicorn process, Docker healthcheck, api-gateway nginx, Prometheus
- **Security Classification:** CRITICAL
- **Clinical Criticality:** HIGH
- **Operational Criticality:** CRITICAL
- **Availability Requirements:** 99.99%
- **Performance Requirements:** < 100ms startup, < 50ms middleware overhead
- **Privacy Classification:** HIGH
- **Compliance Requirements:** Iraqi MoH, HIPAA, ISO 15189
- **Risk Level:** CRITICAL
- **Testing Coverage:** test_comprehensive.py, test_security.py, test_stress.py
- **Documentation Coverage:** CLAUDE.md, ARCHITECTURE.md, ADR-001, ADR-002
- **Last Review:** 2026-07-17
- **Planned Evolution:** Kernel integration deepening, plugin architecture
- **Deprecation Status:** ACTIVE

### DNA-BC-002: config.py — Configuration & Secrets
- **File:** `backend/app/config.py` (326 lines)
- **Owner:** Platform Core Team
- **Purpose:** Environment variable loading, weak-secret detection (16 weak patterns), runtime mode isolation (api/worker/test/cli), feature flag config (SNDHS, Financial Engine, Kernel, AI Dataset), adapter modes (stub/live/shadow), AI provider configs (Gemini, Groq, Ollama), rate limiting, cache config, JWT/refresh token, encryption key mgmt, Supabase/Render/DO integration, Sentry DSN
- **Business Domain:** Platform Foundation
- **Healthcare Domain:** Healthcare Infrastructure
- **Dependencies:** shared/config/loader.py (AppConfig)
- **Security Classification:** CRITICAL
- **Clinical Criticality:** HIGH
- **Operational Criticality:** CRITICAL
- **Privacy Classification:** HIGH
- **Risk Level:** CRITICAL
- **Last Review:** 2026-07-15
- **Deprecation Status:** ACTIVE

### DNA-BC-003: database.py — SQLAlchemy Engine & Pool
- **File:** `backend/app/database.py` (533 lines)
- **Owner:** Platform Core Team
- **Purpose:** Engine creation (primary + read-replica), connection pool sizing (2 workers x (5 base + 10 overflow) = 40 connections), statement timeout (30s), sliding-window error tracker (5-min window), circuit escalation thresholds (L1_TIMEOUT=5, L2_CIRCUIT=20, L3_DEGRADE=50), request-correlation contextvars (request_id, endpoint, user_id, lab_id), per-error-type counters, Redis persistence for error window, edge-access runtime guard
- **Dependencies:** config.py, core/runtime_guard.py, core/self_healing.py, security/redis_client.py
- **Business Domain:** Data Layer
- **Healthcare Domain:** Healthcare Infrastructure
- **Security Classification:** CRITICAL
- **Clinical Criticality:** CRITICAL
- **Operational Criticality:** CRITICAL
- **Risk Level:** CRITICAL
- **Testing:** test_db_adaptive.py, test_resilience.py, test_stability_assertions.py
- **Status:** ACTIVE

### DNA-BC-004: worker.py — Background Worker Entrypoint
- **File:** `backend/app/worker.py` (164 lines)
- **Owner:** Platform Core Team
- **Purpose:** Separate process for 6 background loops: OutboxWorker (event delivery), RecoveryWorker (probe/auto-recovery), HealthAlertWatchdog (grade scoring), AdaptiveConcurrency (DB-latency-based adjustment), AutoRepair (GC/pool recycle), TaskWorker (discrete task queue). Resilient loops with exponential backoff (_RESTART_BASE_DELAY_S=5, _RESTART_MAX_DELAY_S=120)
- **Business Domain:** Platform Operations
- **Healthcare Domain:** Healthcare Infrastructure
- **Dependencies:** config.py, database.py, core/auto_repair.py, core/self_healing.py, services/outbox_service.py, tasks/queue.py, tasks/worker.py
- **Security Classification:** HIGH
- **Clinical Criticality:** MEDIUM
- **Operational Criticality:** HIGH
- **Risk Level:** HIGH
- **Testing:** test_task_queue.py, test_outbox_service.py
- **Status:** ACTIVE

---

## Section 2: Core Infrastructure (DNA-CI)

### DNA-CI-001: core/logging_config.py — Structured JSON Logging
- **File:** `backend/app/core/logging_config.py`
- **Owner:** Platform Core Team
- **Purpose:** Production JSON logging (structured), dev text logging, log context binding via contextvars, bind_log_context()
- **Security Classification:** LOW
- **Clinical Criticality:** LOW
- **Operational Criticality:** MEDIUM
- **Privacy:** MEDIUM — logs must not contain PHI
- **Testing:** test_observability_invariants.py
- **Status:** ACTIVE

### DNA-CI-002: core/startup_guard.py — System Readiness Guard
- **File:** `backend/app/core/startup_guard.py`
- **Owner:** Platform Core Team
- **Purpose:** 6-step startup validation: config validation, DB reachability check, migration check, critical data seeding, kernel boot. Blocks system_ready=True until all pass. ReadinessMiddleware rejects with 503 while unready
- **Security Classification:** HIGH
- **Clinical Criticality:** CRITICAL
- **Risk Level:** CRITICAL
- **Testing:** test_startup_guard.py, test_stability_assertions.py
- **Status:** ACTIVE

### DNA-CI-003: core/self_healing.py — Circuit Breaker & Degraded Mode
- **File:** `backend/app/core/self_healing.py`
- **Owner:** Platform Core Team
- **Purpose:** 3-level degradation (L1_CACHE_HEAVY, L2_READ_ONLY, L3_CRITICAL_ONLY), DB circuit breaker with failure_threshold, half-open recovery, DegradedModeMiddleware (blocks writes in L2/L3), RecoveryWorker with probe-based auto-recovery, health singleton (GREEN/YELLOW/RED scoring)
- **Dependencies:** database.py, security/redis_client.py
- **Security Classification:** HIGH
- **Clinical Criticality:** CRITICAL
- **Risk Level:** CRITICAL
- **Testing:** test_resilience.py, test_chaos_survival.py, test_stability_assertions.py
- **Status:** ACTIVE

### DNA-CI-004: core/auto_repair.py — Auto-Repair Engine
- **File:** `backend/app/core/auto_repair.py`
- **Owner:** Platform Core Team
- **Purpose:** Periodic GC collection, connection pool recycling (every poll cycle), Redis reconnection, sliding window persistence to Redis, adaptive maintenance scheduling
- **Testing:** test_resilience.py, test_db_adaptive.py
- **Status:** ACTIVE

### DNA-CI-005: core/feature_flags.py — Per-Tenant Feature Matrix
- **File:** `backend/app/core/feature_flags.py`
- **Owner:** Platform Product Team
- **Purpose:** Per-lab feature flag resolution from LabSubscription/FeatureFlag models. Controls AI features, clinical features, SNDHS, Financial Engine access based on subscription tier
- **Dependencies:** models/subscription.py
- **Security Classification:** MEDIUM
- **Clinical Criticality:** MEDIUM
- **Testing:** test_feature_flags.py
- **Status:** ACTIVE

### DNA-CI-006: core/sndhs_flags.py — SNDHS Deployment Flags
- **File:** `backend/app/core/sndhs_flags.py`
- **Owner:** Government Compliance Team
- **Purpose:** SNDHS-lite toggles for visits (SNDHS_ENABLE_VISITS), national ID (SNDHS_ENABLE_NATIONAL_ID), audit v2. Controlled via env vars from config.py
- **Compliance:** Iraqi MoH, SNDHS Phase 1
- **Testing:** test_feature_flags.py
- **Status:** ACTIVE — Phase 1

### DNA-CI-007: core/events.py — Internal Event Bus
- **File:** `backend/app/core/events.py`
- **Owner:** Platform Core Team
- **Purpose:** Decoupled event dispatch between modules, pub/sub pattern
- **Status:** ACTIVE

### DNA-CI-008: core/cache_manager.py — Multi-Level Cache (L1+L2)
- **File:** `backend/app/core/cache_manager.py`
- **Owner:** Platform Core Team
- **Purpose:** L1 in-memory cache (default TTL 60s, max 10k items) + L2 Redis cache (default TTL 300s), hit/miss metrics, configurable via CACHE_ENABLED, CACHE_L1_TTL, CACHE_L2_TTL
- **Dependencies:** security/redis_client.py
- **Status:** ACTIVE

### DNA-CI-009: core/policy_engine.py — Policy Enforcement
- **File:** `backend/app/core/policy_engine.py`
- **Owner:** Security Team
- **Purpose:** Business policy validation, clinical governance policies, regulatory compliance checks
- **Testing:** test_compliance_integrity.py
- **Status:** ACTIVE

### DNA-CI-010: core/decision_guard.py — Clinical Decision Guard
- **File:** `backend/app/core/decision_guard.py`
- **Owner:** Platform Core Team
- **Purpose:** Guard for AI-assisted diagnostic decisions, safety checks before clinical AI outputs are returned
- **Status:** ACTIVE

### DNA-CI-011: core/kill_switch.py — Emergency Kill Switch
- **File:** `backend/app/core/kill_switch.py`
- **Owner:** SRE Team
- **Purpose:** Emergency stop mechanism, DigitalOcean-level traffic block (make kill-switch-on)
- **Status:** ACTIVE

### DNA-CI-012: core/idempotency.py — Idempotency Middleware
- **File:** `backend/app/core/idempotency.py`
- **Owner:** Platform Core Team
- **Purpose:** Idempotency-key deduplication for POST/PUT, prevents duplicate order submission
- **Dependencies:** security/redis_client.py
- **Testing:** test_idempotency.py
- **Status:** ACTIVE

### DNA-CI-013: core/resilience.py — Resilience Utilities
- **File:** `backend/app/core/resilience.py`
- **Owner:** Platform Core Team
- **Purpose:** Retry, timeout, circuit breaker utility functions
- **Testing:** test_resilience.py, test_resilience_smoke.py
- **Status:** ACTIVE

### DNA-CI-014: core/runtime_guard.py — Runtime Mode Guard
- **File:** `backend/app/core/runtime_guard.py`
- **Owner:** Platform Core Team
- **Purpose:** Edge table access restriction by runtime mode, blocks API/test processes from accessing edge_* tables via engine event listeners
- **Status:** ACTIVE

### DNA-CI-015: core/risk_engine.py — Risk Scoring Engine
- **File:** `backend/app/core/risk_engine.py`
- **Owner:** Security Team
- **Purpose:** Risk scoring for risk-based authentication (RBA), evaluates device fingerprint, IP reputation, behavior patterns
- **Dependencies:** security/redis_client.py
- **Testing:** test_risk_based_auth.py
- **Status:** ACTIVE

### DNA-CI-016: core/ai_dataset_flags.py — AI Dataset Flags
- **File:** `backend/app/core/ai_dataset_flags.py`
- **Owner:** AI Team
- **Purpose:** Controls for AI interaction dataset collection pipeline (Phase 3+4), flag-gated
- **Status:** ACTIVE

### DNA-CI-017: core/logging_config.py — (see CI-001)

---

## Section 3: Security Modules (DNA-SEC)

### DNA-SEC-001: security/auth.py — JWT Authentication
- **File:** `backend/app/security/auth.py`
- **Owner:** Security Team
- **Purpose:** Token encode/decode (HS256), get_current_user FastAPI dependency, refresh token logic, token validation with expiry checking
- **Dependencies:** config.py (SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRE_MINUTES), models/user.py, models/lab_user.py
- **Security Classification:** CRITICAL
- **Clinical Criticality:** CRITICAL
- **Compliance:** Iraqi MoH, HIPAA
- **Testing:** test_security.py, test_auth_infrastructure.py
- **Status:** ACTIVE

### DNA-SEC-002: security/rbac.py — Role-Based Access Control
- **File:** `backend/app/security/rbac.py`
- **Owner:** Security Team
- **Purpose:** 9 roles (patient, lab_technician, lab_supervisor, lab_admin, doctor, admin, master_admin, ministry_officer, system) x 13 permissions matrix
- **Testing:** test_security.py, test_tiers_privilege.py
- **Status:** ACTIVE

### DNA-SEC-003: security/abac.py — Attribute-Based Access Control
- **File:** `backend/app/security/abac.py`
- **Owner:** Security Team
- **Purpose:** Fine-grained attribute-based policy evaluation (user attributes, resource attributes, environment context)
- **Testing:** test_abac.py
- **Status:** ACTIVE

### DNA-SEC-004: security/encryption.py — Data at Rest Encryption
- **File:** `backend/app/security/encryption.py`
- **Owner:** Security Team
- **Purpose:** Symmetric Fernet encryption for PII/national_id at rest, encrypt_value/decrypt_value functions
- **Dependencies:** config.py (ENCRYPTION_KEY)
- **Security Classification:** CRITICAL
- **Status:** ACTIVE

### DNA-SEC-005: security/session.py — Session Management
- **File:** `backend/app/security/session.py`
- **Owner:** Security Team
- **Purpose:** Session tracking, invalidation, device tracking, concurrent session limits
- **Dependencies:** security/redis_client.py
- **Status:** ACTIVE

### DNA-SEC-006: security/rate_limit.py — Rate Limiting
- **File:** `backend/app/security/rate_limit.py`
- **Owner:** Security Team
- **Purpose:** Token-bucket algorithm per-endpoint, per-user, per-IP. Auth endpoints: 10/min, public: 30/min. Configurable via RATE_LIMIT_AUTH, RATE_LIMIT_PUBLIC
- **Dependencies:** security/redis_client.py, config.py
- **Testing:** test_security_regression.py
- **Status:** ACTIVE

### DNA-SEC-007: security/redis_client.py — Redis Client
- **File:** `backend/app/security/redis_client.py`
- **Owner:** Platform Core Team
- **Purpose:** Redis connection management with Sentinel/Cluster support (REDIS_SENTINEL_HOSTS, REDIS_CLUSTER_NODES), in-memory dict fallback when Redis unavailable
- **Status:** ACTIVE

### DNA-SEC-008: security/mfa_service.py — Multi-Factor Auth
- **File:** `backend/app/security/mfa_service.py`
- **Owner:** Security Team
- **Purpose:** TOTP (time-based one-time password), WebAuthn/FIDO2, backup codes (10 recovery codes)
- **Dependencies:** models/mfa_device.py
- **Status:** ACTIVE

### DNA-SEC-009: security/oauth2_provider.py — OAuth2 Server
- **File:** `backend/app/security/oauth2_provider.py`
- **Owner:** Security Team
- **Purpose:** Authorization code grant, client credentials grant, refresh token grant, PKCE support
- **Dependencies:** models/oauth2_client.py, models/oauth2_token.py
- **Status:** ACTIVE

### DNA-SEC-010: security/saml_service.py — SAML2 SP
- **File:** `backend/app/security/saml_service.py`
- **Owner:** Security Team
- **Purpose:** SAML2 authentication flow, assertion parsing, attribute mapping, ACS endpoint
- **Status:** ACTIVE

### DNA-SEC-011: security/service_accounts.py — API Keys
- **File:** `backend/app/security/service_accounts.py`
- **Owner:** Security Team
- **Purpose:** Machine-to-machine API key generation, rotation, permission scoping
- **Dependencies:** models/service_account.py
- **Status:** ACTIVE

### DNA-SEC-012: security/intrusion_detection.py — IDS
- **File:** `backend/app/security/intrusion_detection.py`
- **Owner:** Security Team
- **Purpose:** Anomaly detection for auth patterns, brute force detection, credential stuffing detection, IP reputation scoring
- **Dependencies:** security/redis_client.py
- **Status:** ACTIVE

### DNA-SEC-013: security/dependencies.py — Auth Dependencies
- **File:** `backend/app/security/dependencies.py`
- **Owner:** Security Team
- **Purpose:** Common FastAPI dependency injection: get_current_user, get_current_lab, require_role, require_permission, tenant isolation filter
- **Status:** ACTIVE

### DNA-SEC-014: security/consent_dep.py — Consent Dependency
- **File:** `backend/app/security/consent_dep.py`
- **Owner:** Legal/Compliance Team
- **Purpose:** Patient consent verification as FastAPI dependency, checks consent before returning patient data
- **Status:** ACTIVE

### DNA-SEC-015: firewall/api_firewall.py — API Firewall
- **File:** `backend/app/firewall/api_firewall.py`
- **Owner:** Security Team
- **Purpose:** Application-layer firewall, IP allowlist/blocklist, request pattern filtering, SQL injection pattern detection
- **Status:** ACTIVE

---

## Section 4: Route Modules (DNA-RT) — 51 Modules

### Core Routes (10)
| DNA | File | Prefix | Key Endpoints | Clinical Criticality |
|-----|------|--------|---------------|---------------------|
| RT-001 | routes/login.py | /login | POST /login, POST /auth/refresh | CRITICAL |
| RT-002 | routes/register.py | /register | POST /register | MEDIUM |
| RT-003 | routes/setup.py | /setup | POST /setup | MEDIUM |
| RT-004 | routes/metrics.py | /metrics | GET /metrics/prom | LOW |
| RT-005 | routes/patients.py | /patients | CRUD, search, dedup | CRITICAL |
| RT-006 | routes/results.py | /results | CRUD, validate, lock | CRITICAL |
| RT-007 | routes/test_results.py | /test-results | Per-test operations | HIGH |
| RT-008 | routes/dashboard.py | /dashboard | Lab aggregations | MEDIUM |
| RT-009 | routes/labs.py | /labs | Lab CRUD, config | HIGH |
| RT-010 | routes/samples.py | /samples | Lifecycle tracking | HIGH |

### Feature Routes (7)
| DNA | File | Prefix | Purpose |
|-----|------|--------|---------|
| RT-011 | routes/qr.py | /qr | QR code generation for patient cards |
| RT-012 | routes/id_scan.py | /id-scan | National ID OCR scanning |
| RT-013 | routes/identity.py | /identity | Identity verification workflows |
| RT-014 | routes/notifications.py | /notifications | Push notification management |
| RT-015 | routes/ehr.py | /ehr | EHR integration endpoints |
| RT-016 | routes/security.py | /security | Security settings, password change |
| RT-017 | routes/device_results.py | /device-results | Lab instrument device results |

### Advanced Lab (3)
| DNA | File | Prefix | Purpose |
|-----|------|--------|---------|
| RT-018 | routes/quality_control.py | /quality-control | IQC, EQA, Levey-Jennings |
| RT-019 | routes/critical_alerts.py | /critical-alerts | Critical value alerting |
| RT-020 | routes/batch.py | /batch | Batch operations |

### Admin & Platform (8)
| DNA | File | Prefix | Purpose |
|-----|------|--------|---------|
| RT-021 | routes/admin.py | /admin | Platform administration |
| RT-022 | routes/mobile.py | /mobile | Mobile API (Android + iOS) |
| RT-023 | routes/compliance.py | /compliance | Government compliance reports |
| RT-024 | routes/tiers.py | /tiers | Subscription tier management |
| RT-025 | routes/citizen_portal.py | /citizen | Patient/citizen portal |
| RT-026 | routes/claims.py | /claims | Insurance claims |
| RT-027 | routes/national_identity.py | /national-id | National ID integration |
| RT-028 | routes/insurance.py | /insurance | Insurance verification |

### AI Routes (3)
| DNA | File | Prefix | Purpose |
|-----|------|--------|---------|
| RT-029 | routes/ai.py | /ai | Clinical AI inference |
| RT-030 | routes/ai_telemetry.py | /ai/telemetry | AI dataset collection |
| RT-031 | routes/optimizer.py | /optimizer | AI system optimizer |

### Clinical Routes (4)
| DNA | File | Prefix | Purpose |
|-----|------|--------|---------|
| RT-032 | routes/clinical.py | /clinical | Clinical core |
| RT-033 | routes/clinical_orders.py | /clinical/orders | Clinical orders |
| RT-034 | routes/clinical_documentation.py | /clinical/docs | Clinical docs |
| RT-035 | routes/clinical_quality.py | /clinical/quality | Quality metrics |

### Identity & Access (5)
| DNA | File | Prefix | Purpose |
|-----|------|--------|---------|
| RT-036 | routes/mfa.py | /mfa | Multi-factor auth |
| RT-037 | routes/password_reset.py | /password-reset | Password reset |
| RT-038 | routes/oauth2.py | /oauth2 | OAuth2 server |
| RT-039 | routes/saml.py | /saml | SAML2 SSO |
| RT-040 | routes/service_accounts.py | /service-accounts | API key mgmt |

### Integration & National (11)
| DNA | File | Prefix | Purpose |
|-----|------|--------|---------|
| RT-041 | routes/integrations.py | /integrations | External integration health |
| RT-042 | routes/edge.py | /edge | Edge AI platform |
| RT-043 | routes/patient_card.py | /patient-card | QR digital patient card |
| RT-044 | routes/care_continuum.py | /care-continuum | National care continuum |
| RT-045 | routes/canonical_patient.py | /canonical-patient | Unified patient records |
| RT-046 | routes/consent.py | /consent | Patient consent |
| RT-047 | routes/national_data.py | /national-data | National health data exchange |
| RT-048 | routes/national_streaming.py | /national-streaming | National data streaming |
| RT-049 | routes/hospital.py | /hospital | Hospital IS |
| RT-050 | routes/stats.py | /stats | Statistics & trends |
| RT-051 | routes/ehr_fhir.py | /ehr/fhir | FHIR-compliant EHR |

---

## Section 5: ORM Models (DNA-MD) — 25 Modules

| DNA | File | Key Tables | Clinical Criticality |
|-----|------|-----------|---------------------|
| MD-001 | models/user.py | users | CRITICAL |
| MD-002 | models/lab_user.py | lab_users | HIGH |
| MD-003 | models/lab.py | labs | HIGH |
| MD-004 | models/patient.py | patients (encrypted national_id) | CRITICAL |
| MD-005 | models/lab_order.py | lab_orders | CRITICAL |
| MD-006 | models/lab_result.py | lab_results (optimistic lock version) | CRITICAL |
| MD-007 | models/test_type.py | test_types | HIGH |
| MD-008 | models/test_result.py | test_results | CRITICAL |
| MD-009 | models/sample.py | samples | HIGH |
| MD-010 | models/audit_log.py | audit_logs (hash chain) | CRITICAL |
| MD-011 | models/outbox.py | outbox_events | HIGH |
| MD-012 | models/subscription.py | subscriptions, feature_flags, upgrade_* | MEDIUM |
| MD-013 | models/quality_control.py | quality_control | HIGH |
| MD-014 | models/consent.py | consent | HIGH |
| MD-015 | models/claim.py | claims | MEDIUM |
| MD-016 | models/edge.py | edge_devices, edge_events, edge_model, etc. | MEDIUM |
| MD-017 | models/mfa_device.py | mfa_devices | HIGH |
| MD-018 | models/oauth2_client.py | oauth2_clients | HIGH |
| MD-019 | models/oauth2_token.py | oauth2_tokens | HIGH |
| MD-020 | models/service_account.py | service_accounts | HIGH |
| MD-021 | models/ai_interaction.py | ai_interactions, ai_feedback, etc. | MEDIUM |
| MD-022 | models/organization.py | organizations | MEDIUM |
| MD-023 | models/canonical_patient.py | canonical_patients | CRITICAL |
| MD-024 | models/base.py | Declarative bases | N/A |
| MD-025 | models/__init__.py | Model registry | N/A |

### Additional Model Packages (from main.py imports):
- **lims/models/** — EQA, IQC, AutoValidationRule, Calibration, ChainOfCustody, Consumable, DeltaCheckRule, ElectronicSignature, EquipmentLog, Instrument, InstrumentModel, LabReport, Lot, Maintenance, Manufacturer, Order, Panel, PanelTest, QCProgram, Reagent, ReferenceRangeDef, ReportAttachment, Result, ResultRelease, ResultValidation, Section, Specimen, SpecimenCatalog, Storage, Supplier, TemperatureLog, Transportation, Workstation
- **hospital/models/** — Bed, BedAssignment, Building, Campus, Clinic, CostCenter, Floor, HospitalDepartment, HospitalMaster, MedicalEquipment, OperationTheater, Room, Unit
- **nhdw/models/** — Admission, CarePlan, ClinicalTask, DashboardConfiguration, Discharge, HospitalAlert, HospitalMessage, QueueEntry, ResourceSchedule, ShiftReport, TelemedicineSession, Transfer, WaitingListEntry, WardRound
- **nursing/models/** — ClinicalChecklist, Delegation, EscalationRecord, FallRiskAssessment, FluidBalance, NursingCarePlan, NursingNote, NursingShift, NursingTask, NutritionAssessment, PainAssessment, PatientAssignment, PressureInjuryAssessment, ShiftHandover
- **pharmacy/models/** — AllergyRule, ClinicalGuideline, ContraindicationRule, DispenseQueue, DispenseRecord, DoseGuideline, DrugBatch, DrugCatalog, DrugInteractionRule, DrugMonitoring, DrugReturn, DrugSupplier, InventoryForecast, InventoryTransfer, InventoryTransferItem, Prescription, PrescriptionItem, Recall, StockLevel, StockMovement, Store, Warehouse, WasteRecord
- **radiology/models/** — MPPS, CriticalFinding, DICOMStorage, DICOMStudy, ImageAnnotation, ImageMeasurement, ImageShare, ModalityDevice, Protocol, RadiologyAppointment, RadiologyExam, RadiologyImage, RadiologyOrder, RadiologyReport, RadiologySeries, ReportTemplate, WorklistEntry
- **national_data/models/** — CanonicalDocument, CanonicalEncounter, CanonicalMedication, CanonicalObservation, CanonicalPatient, CanonicalProcedure, ai_data/*, event_store/*, governance/*, mdm/*, warehouse/*
- **ems/models/** — AmbulanceCrew, Ambulance, CrewShift, DispatchAssignment, EmergencyIncident, HospitalStatus, IncidentCommand, MassCasualtyIncident, Shelter, TriageAssessment, ePCR
- **blood_bank/models/** — BloodComponent, BloodDonation, BloodDonor, BloodInventory, BloodRequest, Crossmatch, DonorDeferral, Transfusion
- **critical_care/models/** — ContinuousInfusion, CriticalAlert, DailyChecklist, DeviceIntegration, EarlyWarningScore, FluidBalance, ICUAdmission, ICUAssessment, ICUBed, ICUScore, RoundRecord, VentilatorSetting, VitalSignsRecord
- **biomedical/models/** — CalibrationRecord, DeviceIncident, DeviceRecall, MaintenanceSchedule, MedicalDevice, PerformanceVerification, SafetyInspection, ServiceContract, SparePart, Technician, Vendor, WorkOrder
- **public_health/models/** — DiseaseCase, EnvironmentalHealth, ImmunizationRecord, OutbreakAlert, PublicHealthReport, SurveillanceSignal
- **command_center/models/** — AfterActionReport, EmergencyDeclaration, SituationReport
- **pilot_platform/models/** — DeploymentRecord, GoNoGoGate, PilotFacility, PilotProgram, ReadinessChecklist
- **lifecycle_platform/models/** — CompatibilityMatrix, ComponentRegistry, DeprecationNotice, Release, UpgradePath

---

## Section 6: Services Layer (DNA-SV) — 34 Modules

| DNA | File | Purpose | Clinical Criticality |
|-----|------|---------|---------------------|
| SV-001 | services/outbox_service.py | Outbox pattern — guaranteed event delivery with retry | HIGH |
| SV-002 | services/order_service.py | Lab order business logic, state machine enforcement | CRITICAL |
| SV-003 | services/patient_service.py | Patient CRUD, deduplication, search | CRITICAL |
| SV-004 | services/audit_service.py | Immutable audit logging with hash chain | CRITICAL |
| SV-005 | services/pdf_report.py | PDF report generation (Arabic-first) | MEDIUM |
| SV-006 | services/ehr_service.py | EHR integration (FHIR, custom) | HIGH |
| SV-007 | services/clinical_service.py | Clinical business logic | HIGH |
| SV-008 | services/clinical_engine.py | Clinical decision support engine | HIGH |
| SV-009 | services/clinical_intelligence.py | Clinical intelligence aggregation | MEDIUM |
| SV-010 | services/clinical_state.py | Clinical state management | MEDIUM |
| SV-011 | services/interpretation.py | Result interpretation logic | HIGH |
| SV-012 | services/identity.py | Identity management and verification | CRITICAL |
| SV-013 | services/identity_matching.py | Patient identity matching (MPI) | CRITICAL |
| SV-014 | services/national_id.py | National ID encryption/lookup | CRITICAL |
| SV-015 | services/patient_card.py | QR patient card HMAC generation | MEDIUM |
| SV-016 | services/consent_service.py | Patient consent management | HIGH |
| SV-017 | services/critical_alerts.py | Critical value alert engine | CRITICAL |
| SV-018 | services/claims_service.py | Insurance claims processing | MEDIUM |
| SV-019 | services/epidemiology.py | Epidemiological tracking | MEDIUM |
| SV-020 | services/device_trust_service.py | Device trust scoring | MEDIUM |
| SV-021 | services/risk_based_auth_service.py | Risk-based auth evaluation | HIGH |
| SV-022 | services/offline_sync_service.py | Offline data synchronization | MEDIUM |
| SV-023 | services/data_platform_service.py | National data platform operations | HIGH |
| SV-024 | services/care_continuum_service.py | Care continuum coordination | HIGH |
| SV-025 | services/hospital_service.py | Hospital IS integration | HIGH |
| SV-026 | services/samir.py | SAMIR AI assistant | MEDIUM |
| SV-027 | services/samir_engine.py | SAMIR AI engine core | MEDIUM |
| SV-028 | services/ali_reza.py | Ali Reza AI assistant | MEDIUM |
| SV-029 | services/ali_reza_engine.py | Ali Reza AI engine core | MEDIUM |
| SV-030 | services/mpi/__init__.py | Master Patient Index | CRITICAL |
| SV-031 | services/mpi/matcher.py | MPI probabilistic matching | CRITICAL |
| SV-032 | services/mpi/resolver.py | MPI conflict resolution | CRITICAL |
| SV-033 | services/mpi/canonical_service.py | Canonical patient creation | CRITICAL |
| SV-034 | services/mpi/api.py | MPI API router | CRITICAL |

---

## Section 7: AI Modules (DNA-AI) — 17 Modules

### Backend AI (backend/app/ai/)
| DNA | File | Purpose |
|-----|------|---------|
| AI-001 | ai/sandbox.py | AI model sandbox for safe execution |
| AI-002 | ai/system_optimizer.py | System performance optimization via AI |
| AI-003 | ai/guardrails.py | AI output guardrails, hallucination prevention, clinical safety checks |
| AI-004 | ai/approval.py | AI-assisted approval workflows |

### Top-Level AI (ai/)
| DNA | File | Purpose |
|-----|------|---------|
| AI-005 | ai/ai_agent.py | AI agent framework for orchestrating AI tasks |
| AI-006 | ai/ai_service.py | AI service orchestrator |
| AI-007 | ai/ali_reza_engine.py | Ali Reza clinical AI engine |
| AI-008 | ai/anomaly_detection.py | Anomaly detection in lab results |
| AI-009 | ai/lab_brain.py | Lab intelligence brain |
| AI-010 | ai/performance_analysis.py | Performance analysis AI |
| AI-011 | ai/population_health.py | Population health analytics |
| AI-012 | ai/preventive_engine.py | Preventive care AI |
| AI-013 | ai/clinical/ | Clinical AI sub-modules |
| AI-014 | ai/outbreak/ | Outbreak detection AI |
| AI-015 | ai/population/ | Population health models |
| AI-016 | ai/preventive/ | Preventive care models |
| AI-017 | ai/lab_business_ai/ | Lab business intelligence AI |

---

## Section 8: Frontend Applications (DNA-FE) — 3 Apps

### DNA-FE-001: frontend-v2/ — Rich React + Firebase
- **Location:** `frontend-v2/`
- **Tech:** React, Firebase (Auth + Firestore), Vite, TypeScript
- **Purpose:** Citizen portal, Ministry Command Centre, predictive analytics, doctor/lab dashboards, multi-portal SPA
- **Clinical Criticality:** HIGH — patient data displayed
- **Status:** ACTIVE

### DNA-FE-002: client/ — tRPC + React SPA
- **Location:** `client/`
- **Tech:** React, tRPC, Vite, TypeScript
- **Purpose:** Lightweight SPA connected to gula-backend via tRPC
- **Clinical Criticality:** MEDIUM
- **Status:** ACTIVE

### DNA-FE-003: frontend/ — Static HTML PWA
- **Location:** `frontend/`
- **Tech:** Vanilla JS, Service Worker (sw.js), HTML/CSS, PWA manifest
- **Purpose:** Offline-capable PWA for result viewing, login, registration, tier display
- **Files:** index.html, login.html, register.html, result.html, tiers.html, manifest.json
- **Clinical Criticality:** MEDIUM
- **Status:** ACTIVE

---

## Section 9: Microservices (DNA-MS) — 9 Services

| DNA | Service | Location | Role | Status |
|-----|---------|----------|------|--------|
| MS-001 | device_bridge | services/device_bridge/ | ASTM/HL7 lab instrument integration (LabLink-Core) | ACTIVE — production |
| MS-002 | lab | services/lab/ | Decomposed lab management | STUB |
| MS-003 | order | services/order/ | Decomposed order processing | STUB |
| MS-004 | patient | services/patient/ | Decomposed patient management | STUB |
| MS-005 | result | services/result/ | Decomposed result management | STUB |
| MS-006 | sample | services/sample/ | Decomposed sample tracking | STUB |
| MS-007 | notification | services/notification/ | Decomposed notification dispatch | STUB |
| MS-008 | ai | services/ai/ | Decomposed AI services | STUB |
| MS-009 | autonomous_manager | services/autonomous_manager/ | Autonomous operations management | STUB |

### Device Bridge Detail (MS-001)
- **Components:** app/main.py, app/app.py, parsers/astm_basic.py, pipeline/ (parser_engine, data_pipeline, patient_matching, test_mapping, normalizer, smart_router), adapters/ (vendors, base, registry), connectors/base.py, core/ (device_registry, device_manager, device_onboarding, connection_pool, retry_queue, alerting, modes), security/auth.py, storage/ (result_repository, db), edge/ (sync_engine, agent), emulator/tcp_device_emulator.py, integration/gula_client.py

---

## Section 10: Edge Agent (DNA-EA) — 1 Agent

### DNA-EA-001: edge_agent/ — Offline Edge Computing Agent
- **Location:** `edge_agent/gula_edge_agent/`
- **Tech:** Python, TOML config
- **Purpose:** Offline computing for remote lab sites, sync with cloud when connectivity available
- **Clinical Criticality:** MEDIUM
- **Status:** ACTIVE

---

## Section 11: National Platform (DNA-NP) — 2 Components

### DNA-NP-001: nhop-platform/ — National Health Oversight Platform
- **Location:** `nhop-platform/`
- **Tech:** FastAPI, PostgreSQL, Docker, Alembic
- **Purpose:** National citizen registry companion service, SNDHS integration
- **Status:** ACTIVE — Phase 1

### DNA-NP-002: docs/sndhs/ — SNDHS Integration Documentation
- **Location:** `docs/sndhs/` (22 files)
- **Purpose:** Full spec for Iraqi National Health Data System integration (Phase 1)
- **Key Docs:** RUNBOOK.md, architecture, DB schema, API spec, offline sync, security, governance
- **Status:** ACTIVE — Phase 1

---

## Section 12: Infrastructure (DNA-INF) — 15 Components

| DNA | Component | Category | Tech | Production Criticality |
|-----|-----------|----------|------|----------------------|
| INF-001 | docker-compose.yml | Container Orchestration | Docker Compose | CRITICAL |
| INF-002 | docker-compose.full.yml | Container Orchestration | Docker Compose | OPTIONAL |
| INF-003 | docker-compose.scale.yml | Container Orchestration | Docker Compose + HAProxy | OPTIONAL |
| INF-004 | Dockerfile | Container Build | Multi-stage Python | CRITICAL |
| INF-005 | k8s/base/ | Kubernetes | K8s manifests | FUTURE |
| INF-006 | k8s/overlays/ | Kubernetes | Kustomize overlays | FUTURE |
| INF-007 | terraform/ | IaC | Terraform modules | FUTURE |
| INF-008 | cloudflare/ | Edge/CDN | DNS, WAF, Workers, R2 | HIGH |
| INF-009 | digitalocean/app.yaml | PaaS | DO App Platform | HIGH |
| INF-010 | render.yaml | PaaS | Render | OPTIONAL |
| INF-011 | supabase/ | BaaS | Supabase config | OPTIONAL |
| INF-012 | config/nginx/ | Reverse Proxy | nginx configs | CRITICAL |
| INF-013 | config/postgres/ | Database | PostgreSQL configs | CRITICAL |
| INF-014 | config/redis/ | Cache | Redis config | HIGH |
| INF-015 | config/haproxy/ | Load Balancer | HAProxy | OPTIONAL |

---

## Section 13: CI/CD (DNA-CD) — 6 Workflows

| DNA | Workflow | Purpose | Gate |
|-----|----------|---------|------|
| CD-001 | syntax-gate | py_compile + flake8 E9/F821 on every push | BLOCKING |
| CD-002 | migration-check | Alembic upgrade/downgrade on fresh postgres:16 | BLOCKING |
| CD-003 | smoke-test | Boot uvicorn + curl /health, /health/ready, /health/deep, /test-types | BLOCKING |
| CD-004 | backend-test | pytest tests/ against postgres:14.11 + redis:7.2 | BLOCKING |
| CD-005 | security-scan | safety (CVE), bandit -ll -ii, hadolint, gitleaks, /tmp write check | BLOCKING |
| CD-006 | build-and-push | Matrix build of 8 images to GHCR + Trivy scan | BLOCKING |

### Additional Workflows:
- **blue-green-deploy.yml** — Zero-downtime blue/green deployments
- **deploy.yml** — Standard deployment pipeline

---

## Section 14: Database Migrations (DNA-MG) — 47 Revisions

### Foundation (6 — 2025-03-22)
| DNA | File | Description |
|-----|------|-------------|
| MG-001 | 20250322_0000_create_base_schema.py | Bootstrap snapshot (IMMUTABLE) |
| MG-002 | 20250322_0001_add_roles_hierarchy.py | User roles hierarchy |
| MG-003 | 20250322_0002_perf_indexes_audit_protection.py | Performance indexes |
| MG-004 | 20250322_0003_order_validation_state.py | Order validation states |
| MG-005 | 20250323_0004_core_enforcement.py | Core constraint enforcement |
| MG-006 | 20250323_0005_citizen_email_nullable.py | Citizen email nullable |

### Phase 2 (7 — 2026-03-24/29)
| DNA | File | Description |
|-----|------|-------------|
| MG-007 | 20260324_0006_patient_family_guardian.py | Patient family/guardian fields |
| MG-008 | 20260324_0007_lab_type_director_website.py | Lab metadata fields |
| MG-009 | 20260324_0008_lab_result_test_type_fk_set_null.py | FK set null on delete |
| MG-010 | 20260324_0009_audit_chain_hash_result_engine_version.py | Audit hash chain |
| MG-011 | 20260324_0010_production_indexes.py | Production query indexes |
| MG-012 | 20260329_0011_subscription_tiers_feature_flags.py | Subscription + feature flags |
| MG-013 | 20260329_0012_lab_result_version_citizen_indexes.py | Optimistic lock + citizen indexes |

### Feature Expansion (5 — 2026-04)
| DNA | File | Description |
|-----|------|-------------|
| MG-014 | 20260407_0001_claims_tables.py | Insurance claims |
| MG-015 | 20260413_0001_mpi_citizen_registry.py | MPI citizen registry |
| MG-016 | 20260417_0001_consent_table.py | Patient consent |
| MG-017 | 20260428_0001_edge_platform.py | Edge platform tables |
| MG-018 | 20260503_0001_stats_trends_perf_indexes.py | Stats performance indexes |

### SNDHS Phase 1 (6 — 2026-05-05)
| DNA | File | Description |
|-----|------|-------------|
| MG-019 | 20260505_0001_sndhs_phase1_extend_patients.py | SNDHS patient fields |
| MG-020 | 20260505_0002_sndhs_phase1_index_national_id.py | SNDHS national_id index |
| MG-021 | 20260505_0003_sndhs_phase1_visits_table.py | SNDHS visits table |
| MG-022 | 20260505_0004_sndhs_phase1_lab_orders_visit_id.py | lab_orders.visit_id |
| MG-023 | 20260505_0005_sndhs_phase1_audit_logs_v2.py | SNDHS audit v2 |
| MG-024 | 20260505_0006_sndhs_phase1_constraints.py | SNDHS constraints |

### AI + Financial (3 — 2026-05-06/11)
| DNA | File | Description |
|-----|------|-------------|
| MG-025 | 20260506_0001_financial_engine_phase_a.py | Financial Engine Phase A |
| MG-026 | 20260511_0001_ai_interactions_dataset.py | AI interactions dataset |
| MG-027 | 20260511_0002_ai_safety_hallucination_columns.py | AI safety columns |

### National Platform (18 — 2026-07-14/16)
| DNA | File | Description |
|-----|------|-------------|
| MG-028 | 20260714_0001_national_lims_tables.py | National LIMS |
| MG-029 | 20260715_0001_national_ecosystem_partners.py | Ecosystem partners |
| MG-030 | 20260716_0001_nhdw_platform.py | Hospital Desktop Workspace |
| MG-031 | 20260716_0002_nursing_platform.py | Nursing Platform |
| MG-032 | 20260716_0003_pharmacy_platform.py | Pharmacy Platform |
| MG-033 | 20260716_0004_radiology_platform.py | Radiology + PACS |
| MG-034 | 20260716_0005_national_ems_disaster_response.py | EMS & Disaster Response |
| MG-035 | 20260716_0006_national_blood_bank.py | Blood Bank & Transfusion |
| MG-036 | 20260716_0007_national_critical_care.py | Critical Care |
| MG-037 | 20260716_0008_national_biomedical_engineering.py | Biomedical Engineering |
| MG-038 | 20260716_0009_national_public_health.py | Public Health Surveillance |
| MG-039 | 20260716_0010_national_command_center.py | Health Command Center |
| MG-040 | 20260716_0011_national_pilot_readiness.py | Pilot Deployment Readiness |
| MG-041 | 20260716_0012_national_lifecycle_governance.py | Platform Lifecycle Governance |
| MG-042 | 20260716_0013_national_trust_platform.py | National Trust Platform |
| MG-043 | 20260716_0014_governance_identity_persistence.py | Governance Identity |
| MG-044 | 20260716_0015_auth_security_tables.py | Auth Security Tables |
| MG-045 | 20260716_0016_canonical_patient_unification.py | Canonical Patient Unification |

---

## Section 15: Scripts (DNA-SC) — 74+ Scripts

### Python Scripts (16)
| DNA | File | Purpose |
|-----|------|---------|
| SC-001 | scripts/self_audit_agent.py | Claude-powered self-audit agent |
| SC-002 | scripts/sndhs_phase1_backfill.py | SNDHS Phase 1 data backfill |
| SC-003 | scripts/dependency_guardian.py | Dependency health monitoring |
| SC-004 | scripts/gula_monitor.py | Platform monitoring daemon |
| SC-005 | scripts/architecture_guardian.py | Architecture policy enforcement |
| SC-006 | scripts/constitution_enforcer.py | Engineering constitution enforcement |
| SC-007 | scripts/self_heal.py | Self-healing trigger |
| SC-008 | scripts/chaos_test.py | Chaos engineering test suite |
| SC-009 | scripts/fix_datetime_utc.py | UTC datetime fixer |
| SC-010 | scripts/dive.py | Deep inspection tool |
| SC-011 | scripts/export_openapi.py | OpenAPI schema export |
| SC-012 | scripts/create_master_admin.py | Master admin account creation |
| SC-013 | scripts/generate-final-report.py | Final audit report generator |
| SC-014 | scripts/generate-performance-report.py | Performance report generator |
| SC-015 | scripts/gula_autofix.py | Automated fix application |
| SC-016 | scripts/__init__.py | Package init |

### Shell Scripts (58+)
| DNA | File | Purpose |
|-----|------|---------|
| SC-017 | scripts/deploy.sh | Production deployment |
| SC-018 | scripts/start.sh | Application startup |
| SC-019 | scripts/start-dev.sh | Development startup |
| SC-020 | scripts/backup.sh | Database backup (pg_dump → gzip) |
| SC-021 | scripts/continuous-backup.sh | Continuous backup daemon |
| SC-022 | scripts/backup-verification.sh | Backup integrity verification |
| SC-023 | scripts/restore-test.sh | Backup restore testing |
| SC-024 | scripts/diagnose.sh | System diagnostics |
| SC-025 | scripts/diagnose-droplet.sh | DigitalOcean droplet read-only diagnostics |
| SC-026 | scripts/repair-droplet.sh | Droplet repair (destructive) |
| SC-027 | scripts/preflight.sh | Deployment preflight checks |
| SC-028 | scripts/setup-deployment.sh | Deployment environment setup |
| SC-029 | scripts/server-setup.sh | Server provisioning |
| SC-030 | scripts/setup-https.sh | HTTPS certificate setup (Let's Encrypt) |
| SC-031 | scripts/cert-renew.sh | Certificate renewal |
| SC-032 | scripts/setup-venv.sh | Python virtualenv setup |
| SC-033 | scripts/setup-secrets.sh | Secret initialization |
| SC-034 | scripts/generate-launch-secrets.sh | Launch secret generation |
| SC-035 | scripts/rotate-keys.sh | Key rotation |
| SC-036 | scripts/rotate-secrets.sh | Secret rotation |
| SC-037 | scripts/change-master-password.sh | Master password change |
| SC-038 | scripts/monitor.sh | System monitoring |
| SC-039 | scripts/gula_health.sh | Platform health check |
| SC-040 | scripts/auto_heal.sh | Auto-healing trigger |
| SC-041 | scripts/emergency-fix.sh | Emergency fix procedure |
| SC-042 | scripts/fix-server.sh | Server fix routine |
| SC-043 | scripts/check_platform.sh | Platform verification |
| SC-044 | scripts/check_migration_policy.sh | Migration policy compliance |
| SC-045 | scripts/smoke-bootstrap.sh | Smoke test bootstrap |
| SC-046 | scripts/test-api.sh | API test runner |
| SC-047 | scripts/load-test.sh | Load testing |
| SC-048 | scripts/integration_test.sh | Integration test runner |
| SC-049 | scripts/dr-test.sh | Disaster recovery test |
| SC-050 | scripts/dr-failover.sh | DR failover procedure |
| SC-051 | scripts/dr-failback.sh | DR failback procedure |
| SC-052 | scripts/dr_recovery.sh | DR recovery procedure |
| SC-053 | scripts/pg_failover.sh | PostgreSQL failover |
| SC-054 | scripts/pitr-recover.sh | Point-in-time recovery |
| SC-055 | scripts/manage-snapshots.sh | Snapshot management |
| SC-056 | scripts/validate-restore.sh | Restore validation |
| SC-057 | scripts/sndhs_phase1_disable_flags.sh | SNDHS flag disable |
| SC-058 | scripts/tag-release.sh | Release tagging |
| SC-059 | scripts/production-freeze.sh | Production freeze management |
| SC-060 | scripts/generate-sbom.sh | SBOM generation |
| SC-061 | scripts/validate-sbom.sh | SBOM validation |
| SC-062 | scripts/generate-metrics-token.sh | Metrics token generator |
| SC-063 | scripts/generate-contracts.sh | Contract generation |
| SC-064 | scripts/supabase_bootstrap.sh | Supabase bootstrap |
| SC-065 | scripts/setup-ollama.sh | Ollama model setup |
| SC-066 | scripts/pull-ollama-model.sh | Ollama model pull |
| SC-067 | scripts/init-kafka-topics.sh | Kafka topic initialization |
| SC-068 | scripts/nginx-ensure.sh | Nginx configuration ensure |
| SC-069 | scripts/digitalocean-manage.sh | DigitalOcean management |
| SC-070 | setup-production.sh | Production environment setup |
| SC-071 | emergency-recover.sh | Emergency recovery |
| SC-072 | gula_update.sh | Platform update |
| SC-073 | gula_health.sh | Health check wrapper |
| SC-074 | gula_autofix.sh | Auto-fix wrapper |

---

## Section 16: Configuration Categories (DNA-CF) — 37 Categories

| DNA | Path | Category | Files |
|-----|------|----------|-------|
| CF-001 | config/postgres/ | Database | postgresql.conf, audit.sql, init.sql, partitions.sql, pg_hba.conf |
| CF-002 | config/redis/ | Cache | redis.conf |
| CF-003 | config/nginx/ | Reverse Proxy | nginx.conf, conf.d/api.conf, frontend.conf, api-threat-protection.conf, system/*.conf |
| CF-004 | config/haproxy/ | Load Balancer | haproxy.cfg |
| CF-005 | config/prometheus/ | Metrics | prometheus.yml, prometheus-full.yml, rules/gula.yml, rules/slo.yml, rules/gula-full.yml |
| CF-006 | config/grafana/ | Dashboards | dashboards/gula-platform-full.json, dashboards/gula-hospital.json, dashboards/gula-capacity.json, provisioning/ |
| CF-007 | config/alertmanager/ | Alerting | alertmanager.yml, templates/slack.tmpl, templates/pagerduty.tmpl |
| CF-008 | config/loki/ | Log Aggregation | loki-config.yml |
| CF-009 | config/promtail/ | Log Shipping | promtail-config.yml |
| CF-010 | config/tempo/ | Distributed Tracing | tempo-config.yml, docker-compose.tempo.yml |
| CF-011 | config/opentelemetry/ | OpenTelemetry | otel-collector-config.yml, python-instrumentation.md |
| CF-012 | config/rabbitmq/ | Message Queue | rabbitmq.conf, definitions.json |
| CF-013 | config/rabbitmq-cluster/ | HA Messaging | rabbitmq.conf, definitions.json, docker-compose.rabbitmq-ha.yml |
| CF-014 | config/redis-sentinel/ | HA Redis | sentinel.conf, docker-compose.redis-ha.yml |
| CF-015 | config/redis-cluster/ | Redis Cluster | redis-cluster.conf |
| CF-016 | config/postgres-ha/ | HA PostgreSQL | patroni.yml, backup-config.sh, failover.sh, pitr-config.sh, read-replicas.sh |
| CF-017 | config/minio-ha/ | Object Storage HA | minio-config.json, nginx-minio.conf, replication-rules.json, docker-compose.minio-ha.yml |
| CF-018 | config/caching/ | Cache Strategy | redis-cache-strategy.md |
| CF-019 | config/streaming/ | Streaming | kafka-optimization.md |
| CF-020 | config/vault/ | Secrets Management | vault.hcl, vault-prod.hcl |
| CF-021 | config/cert-manager/ | Certificates | certificate-template.yaml, cluster-issuer.yaml |
| CF-022 | config/security/ | Security Scanning | sast-config.yml, dast-config.yml, container-scan.yml, secret-scanning.yml, checkov-config.yml, dependency-check.yml, iac-scan.yml, license-config.yml, zap-api-scan.py |
| CF-023 | config/siem/ | SIEM | elastic-security-config.yml, wazuh-agent-config.yml |
| CF-024 | config/ids/ | IDS/IPS | fail2ban-config.local, snort-rules/local.rules |
| CF-025 | config/runtime-protection/ | Runtime Security | apparmor-profile, seccomp-profile.json |
| CF-026 | config/zero-trust/ | Zero Trust | zero-trust-policy.yaml, linkerd-policy.yaml |
| CF-027 | config/nginx/maintenance/ | Maintenance | maintenance.html |
| CF-028 | config/postgres-ha/ | HA Postgres | patroni.yml, failover.sh, pitr-config.sh |
| CF-029 | config/workers/ | Workers | worker-config.yml |
| CF-030 | config/system/ | System Tuning | 99-gula-sysctl.conf, gula-limits.conf |
| CF-031 | config/dr/ | Disaster Recovery | cross-region-replication.yml |
| CF-032 | config/quality-gates/ | Quality Gates | api-gate.py, architecture-gate.py, database-gate.py, security-gate.py, performance-gate.py, fhir-gate.py, scalability-gate.py, offline-gate.py, accessibility-gate.js |
| CF-033 | config/clickhouse/ | Analytics | init.sql |
| CF-034 | .env.example | Env Template | All environment variables documented |
| CF-035 | .env.production | Production Env | Production template (no secrets) |
| CF-036 | docker-compose.yml | Compose MVP | 4 services |
| CF-037 | docker-compose.full.yml | Compose Full | Full observability stack |

---

## Section 17: Architecture Decision Records (DNA-ADR) — 26 Records

| DNA | File | Title | Status |
|-----|------|-------|--------|
| ADR-001 | ADR-001-engineering-constitution.md | Engineering Constitution | ACTIVE |
| ADR-002 | ADR-002-monolith-first.md | Monolith-First Architecture | ACTIVE |
| ADR-003 | ADR-003-multi-tenant-isolation.md | Multi-Tenant Isolation | ACTIVE |
| ADR-004 | ADR-004-skill-platform.md | Skill Platform | ACTIVE |
| ADR-005 | ADR-005-postgresql-redis-stack.md | PostgreSQL + Redis Stack | ACTIVE |
| ADR-006 | ADR-006-clinical-ai-integration.md | Clinical AI Integration | ACTIVE |
| ADR-007 | ADR-007-device-bridge-astm-hl7.md | Device Bridge ASTM/HL7 | ACTIVE |
| ADR-008 | ADR-008-patient-card-system.md | Patient Card System | ACTIVE |
| ADR-009 | ADR-009-self-healing-infrastructure.md | Self-Healing Infrastructure | ACTIVE |
| ADR-010 | ADR-010-sndhs-government-integration.md | SNDHS Government Integration | ACTIVE |
| ADR-011 | ADR-011-notification-platform.md | Notification Platform | ACTIVE |
| ADR-012 | ADR-012-identity-platform.md | Identity Platform | ACTIVE |
| ADR-012 | ADR-012-engineering-automation.md | Engineering Automation | ACTIVE |
| ADR-013 | ADR-013-production-platform.md | Production Platform | ACTIVE |
| ADR-014 | ADR-014-observability-stack.md | Observability Stack | ACTIVE |
| ADR-015 | ADR-015-disaster-recovery.md | Disaster Recovery | ACTIVE |
| ADR-016 | ADR-016-national-ehr.md | National EHR | ACTIVE |
| ADR-017 | ADR-017-national-data-platform.md | National Data Platform | ACTIVE |
| ADR-018 | ADR-018-national-operations.md | National Operations | ACTIVE |
| ADR-019 | ADR-019-national-ecosystem.md | National Ecosystem | ACTIVE |
| ADR-020 | ADR-020-citizen-super-app.md | Citizen Super App | ACTIVE |
| ADR-021 | ADR-021-national-intelligence.md | National Intelligence | ACTIVE |
| ADR-022 | ADR-022-doctor-workspace.md | Doctor Workspace | ACTIVE |
| ADR-023 | ADR-023-laboratory-desktop.md | Laboratory Desktop | ACTIVE |
| ADR-024 | ADR-024-Platform-Constitution.md | Platform Constitution | ACTIVE |

---

## Section 18: Test Suites (DNA-TS) — 59 Files

| DNA | File | Coverage Area |
|-----|------|---------------|
| TS-001 | test_comprehensive.py | Full integration across all major routes |
| TS-002 | test_stress.py | Stress & performance under load |
| TS-003 | test_system_improvements.py | Clinical interpretation, AI, stats |
| TS-004 | test_security.py | JWT, auth, encryption invariants |
| TS-005 | test_patient_card.py | QR card, scanning, HMAC tokens |
| TS-006 | test_mpi_matcher.py | MPI deduplication |
| TS-007 | test_outbox_service.py | Event outbox guaranteed delivery |
| TS-008 | test_feature_flags.py | Per-tenant feature matrix |
| TS-009 | test_edge_platform.py | Edge site synchronization |
| TS-010 | test_stability_assertions.py | Data integrity checks |
| TS-011 | test_security_regression.py | Security regression tests |
| TS-012 | test_abac.py | Attribute-based access control |
| TS-013 | test_risk_based_auth.py | Risk-based authentication |
| TS-014 | test_idempotency.py | Idempotency key deduplication |
| TS-015 | test_resilience.py | Resilience patterns |
| TS-016 | test_resilience_smoke.py | Resilience smoke tests |
| TS-017 | test_startup_guard.py | Startup guard validation |
| TS-018 | test_db_adaptive.py | DB adaptive behavior |
| TS-019 | test_chaos_survival.py | Chaos engineering survival |
| TS-020 | test_consent.py | Patient consent |
| TS-021 | test_compliance_integrity.py | Compliance & integrity |
| TS-022 | test_tiers_privilege.py | Tier privilege escalation |
| TS-023 | test_domain.py | Domain logic |
| TS-024 | test_hard_scenarios.py | Hard scenario edge cases |
| TS-025 | test_break_scenarios.py | Break/failure scenarios |
| TS-026 | test_concurrency_safety.py | Concurrency safety |
| TS-027 | test_clinical_safety.py | Clinical safety invariants |
| TS-028 | test_ai_guardrails.py | AI guardrails |
| TS-029 | test_tenant_isolation_matrix.py | Tenant isolation matrix |
| TS-030 | test_migrations.py | Migration integrity |
| TS-031 | test_migration_resilience.py | Migration resilience |
| TS-032 | test_routes_labs.py | Lab route testing |
| TS-033 | test_routes_register.py | Registration route testing |
| TS-034 | test_financial.py | Financial Engine testing |
| TS-035 | test_gateway_modes.py | Adapter mode testing |
| TS-036 | test_device_trust.py | Device trust scoring |
| TS-037 | test_offline_sync.py | Offline synchronization |
| TS-038 | test_auth_infrastructure.py | Auth infrastructure |
| TS-039 | test_observability_invariants.py | Observability invariants |
| TS-040 | test_runtime_isolation.py | Runtime mode isolation |
| TS-041 | test_governance.py | Governance layer testing |
| TS-042 | test_persisted_identity_governance.py | Identity governance |
| TS-043 | test_national_notification_platform.py | National notifications |
| TS-044 | test_control_layer.py | Control layer testing |
| TS-045 | test_elite_improvements.py | Elite improvements |
| TS-046 | test_task_queue.py | Task queue |
| TS-047 | test_performance_budgets.py | Performance budgets |
| TS-048 | test_disaster_recovery.py | Disaster recovery |
| TS-049 | test_identity_matching.py | Identity matching |
| TS-050 | conftest.py | Test fixtures and configuration |

---

## Section 19: Domain & Supporting (DNA-DM) — 12 Modules

| DNA | Path | Purpose |
|-----|------|---------|
| DM-001 | domain/order_state.py | Order state machine (pending→completed→validated, pending→cancelled) |
| DM-002 | audit/audit_log.py | Immutable audit trail with SHA-256 hash chain |
| DM-003 | notifications/service.py | Push notification dispatch (FCM, APNS) |
| DM-004 | notifications/telegram.py | Telegram bot notifications |
| DM-005 | legal/consent.py | Legal consent framework |
| DM-006 | tasks/queue.py | Discrete task queue (outbox-backed) |
| DM-007 | tasks/worker.py | Task worker consumer |
| DM-008 | tasks/registry.py | Task registry for worker dispatch |
| DM-009 | tasks/schema.py | Task schemas |
| DM-010 | integration/integration.py | Integration platform orchestration |
| DM-011 | integration/monitoring.py | Integration monitoring |
| DM-012 | integration/offline.py | Offline integration support |

---

## Section 20: Gateway Adapters (DNA-GW) — 8 Modules

| DNA | File | External System | Mode Support |
|-----|------|----------------|--------------|
| GW-001 | gateways/base.py | Abstract adapter base class | stub/live/shadow |
| GW-002 | gateways/mode.py | Mode resolution logic | stub/live/shadow |
| GW-003 | gateways/national_identity_gateway.py | Iraqi MoI NID API | stub/live/shadow |
| GW-004 | gateways/insurance_gateway.py | NHI Insurance API | stub/live/shadow |
| GW-005 | gateways/residency_gateway.py | MoI Residency API | stub/live/shadow |
| GW-006 | gateways/cloudflare_gateway.py | Cloudflare control plane | stub/live/shadow |
| GW-007 | gateways/lab_device_gateway.py | Lab device integration | stub/live/shadow |
| GW-008 | gateways/google_ai.py | Google AI / Gemini API | live |

---

## Section 21: Task System (DNA-TK) — 5 Modules

| DNA | File | Purpose |
|-----|------|---------|
| TK-001 | tasks/queue.py | Task queue management (priority, scheduling, retry) |
| TK-002 | tasks/worker.py | Task consumer with concurrent execution |
| TK-003 | tasks/registry.py | Task type registry for routing |
| TK-004 | tasks/schema.py | Pydantic schemas for task payloads |
| TK-005 | tasks/__init__.py | Task system initialization |

---

## Section 22: National Platform Modules (DNA-NM) — 19 Runtime Modules

| DNA | Module | Path | Mission |
|-----|--------|------|---------|
| NM-001 | Governance | governance/ | Healthcare governance layer |
| NM-002 | National LIMS | lims/ | National LIMS management |
| NM-003 | Rules Engine | national/rules_engine/ | Business rules execution |
| NM-004 | Background Platform | national/background_platform/ | Background job orchestration |
| NM-005 | Workflow Runtime | national/workflow_runtime/ | Workflow engine |
| NM-006 | Task Engine | national/task_engine/ | Distributed task execution |
| NM-007 | Notification Platform | national/notification_platform/ | National notification system |
| NM-008 | Document Platform | national/document_platform/ | Document management |
| NM-009 | Scheduling Platform | national/scheduling_platform/ | Resource scheduling |
| NM-010 | Search Platform | national/search_platform/ | Unified search |
| NM-011 | Observability | national/observability/ | Platform observability |
| NM-012 | Platform Foundation | platform/ | MISSION-017A |
| NM-013 | Contracts | contracts/ | MISSION-017A |
| NM-014 | Integration Connectors | integration/connectors/ | PHASE 11 |
| NM-015 | Integration Platform | integration/ | MISSION-018 |
| NM-016 | Citizen Platform | citizen_platform/ | MISSION-019 |
| NM-017 | AI Fabric | ai_fabric/ | MISSION-020 |
| NM-018 | Research Platform | research_platform/ | MISSION-021 |
| NM-019 | Ecosystem | national/ecosystem/ | MISSION-020 |
| NM-020 | Intelligence | national/intelligence/ | MISSION-022 |

---

## Section 23: Kernel (DNA-KR) — 15 Modules

| DNA | File | Purpose |
|-----|------|---------|
| KR-001 | kernel/integration.py | Kernel bootstrap, warmup, middleware |
| KR-002 | kernel/routes.py | Kernel management API routes |
| KR-003 | kernel/runtime_routes.py | Runtime kernel extensions (MISSION-017D) |
| KR-004 | kernel/event_bus/ | Internal event bus |
| KR-005 | kernel/plugin/ | Plugin loading system |
| KR-006 | kernel/module/ | Module management |
| KR-007 | kernel/config/ | Configuration engine |
| KR-008 | kernel/features/ | Feature flag management |
| KR-009 | kernel/tenant/ | Multi-tenant engine |
| KR-010 | kernel/gateway/ | Internal API gateway |
| KR-011 | kernel/background/ | Background task scheduling |
| KR-012 | kernel/policy_runtime.py | Policy runtime execution |
| KR-013 | kernel/rules_runtime.py | Rules runtime execution |
| KR-014 | kernel/validation/ | Validation framework |
| KR-015 | kernel/ai_runtime.py | AI runtime integration |

---

*End of Digital DNA Atlas — 400+ DNA entries catalogued across 23 sections.*
