# GULA Platform — Backend Analysis
**Date:** 2026-07-17

---

## 1. Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | FastAPI | 0.139.0 |
| ASGI Server | Uvicorn | 0.51.0 |
| WSGI Server | Gunicorn | 21.2+ |
| Python | CPython | 3.11+ |
| ORM | SQLAlchemy | 2.0.51 |
| Migration | Alembic | 1.18.5 |
| Validation | Pydantic | 2.13.4 |
| DB Driver | psycopg2-binary | 2.9.9 |
| Auth | python-jose | 3.4+ (HS256) |
| Encryption | cryptography (Fernet) | 49.0.0 |
| Password | passlib[bcrypt] | bcrypt 4.1.3 |
| HTTP Client | httpx | 0.27+ |
| Cache | redis-py | 8.0.1 |
| Error Tracking | sentry-sdk | 2.65.0 |

---

## 2. Route Modules (53 confirmed)

### Core LIMS Routes
| File | LOC | Purpose |
|------|-----|---------|
| `routes/admin.py` | 37893 | Admin operations, system management |
| `routes/login.py` | 7330 | Authentication, token refresh |
| `routes/register.py` | 21530 | Lab/citizen/doctor/staff registration |
| `routes/labs.py` | 7308 | Lab CRUD and management |
| `routes/patients.py` | 8732 | Patient CRUD |
| `routes/results.py` | 11594 | Lab result access (token-based) |
| `routes/test_results.py` | 24384 | Test result management |
| `routes/samples.py` | 6349 | Sample tracking |
| `routes/dashboard.py` | 6327 | Lab dashboard (Arabic-first) |
| `routes/stats.py` | 14945 | Statistics & trends |
| `routes/patient_card.py` | 11396 | Digital QR-backed patient cards |
| `routes/quality_control.py` | 10802 | Westgard QC rules |
| `routes/critical_alerts.py` | 1118 | Critical result alerts |
| `routes/device_results.py` | 3993 | Lab device result ingestion |
| `routes/batch.py` | 3950 | Batch order processing |
| `routes/qr.py` | 2736 | QR code generation |

### Clinical Routes
| File | LOC | Purpose |
|------|-----|---------|
| `routes/clinical.py` | 40609 | Clinical services |
| `routes/clinical_orders.py` | 9855 | Clinical order management |
| `routes/clinical_documentation.py` | 11846 | Clinical documentation |
| `routes/clinical_quality.py` | 2909 | Quality indicators |
| `routes/ehr.py` | 73097 | Electronic Health Records (largest) |
| `routes/ehr_fhir.py` | 37334 | FHIR R4/R5 resource API |
| `routes/care_continuum.py` | 33957 | National care continuum |
| `routes/hospital.py` | 26515 | Hospital facility management |

### AI Routes
| File | LOC | Purpose |
|------|-----|---------|
| `routes/ai.py` | 39938 | AI interpretation + human-in-loop |
| `routes/ai_telemetry.py` | 19846 | AI interaction dataset collection |

### Security Routes
| File | LOC | Purpose |
|------|-----|---------|
| `routes/identity.py` | 2673 | Identity management |
| `routes/national_identity.py` | 755 | National ID verification |
| `routes/mfa.py` | 4486 | Multi-factor authentication |
| `routes/password_reset.py` | 2723 | Password management |
| `routes/oauth2.py` | 12106 | OAuth 2.0 / OIDC provider |
| `routes/saml.py` | 2147 | SAML 2.0 SSO |
| `routes/service_accounts.py` | 3462 | API key management |
| `routes/consent.py` | 6661 | Patient consent management |
| `routes/security.py` | 1968 | Security endpoints |

### National Platform Routes
| File | LOC | Purpose |
|------|-----|---------|
| `routes/national_data.py` | 34607 | National data exchange |
| `routes/national_streaming.py` | 9502 | FHIR/HL7 event streaming |
| `routes/compliance.py` | 47295 | Ministry of Health compliance |
| `routes/citizen_portal.py` | 17175 | Citizen-facing portal |
| `routes/claims.py` | 6316 | Insurance claims |
| `routes/insurance.py` | 550 | Insurance verification |

### Other Routes
`routes/edge.py` (32912), `routes/metrics.py` (12801), `routes/mobile.py` (13349), `routes/ehr.py` (73097), `routes/id_scan.py` (6163), `routes/notifications.py` (4632), `routes/tiers.py` (21577), `routes/integrations.py` (4425), `routes/setup.py` (1021), `routes/optimizer.py` (3069), `routes/canonical_patient.py` (7890)

---

## 3. Service Layer (34+ files)

| Service | LOC | Purpose |
|---------|-----|---------|
| `interpretation.py` | 1100+ | Smart medical interpretation (30+ tests, Arabic/English) |
| `clinical_service.py` | 1336 | Terminology, CDS, quality, research, AI |
| `ehr_service.py` | 1324 | Longitudinal health record |
| `care_continuum_service.py` | 1084 | National care continuum |
| `clinical_intelligence.py` | ~500 | Multi-test pattern detection (15 syndromes) |
| `clinical_state.py` | ~350 | Clinical state management |
| `clinical_engine.py` | ~400 | 4 sub-engines orchestrator |
| `hospital_service.py` | ~800 | Hospital management |
| `data_platform_service.py` | ~700 | Data platform integration |
| `audit_service.py` | ~250 | Hash-chained audit |
| `outbox_service.py` | ~300 | Transactional outbox |

---

## 4. Core Infrastructure (15 modules)

| File | LOC | Purpose |
|------|-----|---------|
| `startup_guard.py` | 713 | System readiness orchestration |
| `self_healing.py` | 458 | Circuit breaker, degradation |
| `auto_repair.py` | 330 | Repair engine (GC, pool, reconnect) |
| `feature_flags.py` | 340 | Per-tenant feature matrix |
| `sndhs_flags.py` | 171 | Deployment-wide SNDHS toggles |
| `policy_engine.py` | 277 | Governance policy enforcement |
| `logging_config.py` | 24 | JSON logging setup |

---

## 5. Key Architectural Decisions (from code evidence)

1. **Monolith-first**: All business logic in `backend/app/`; microservices are stubs
2. **Lifespan pattern**: Uses `@asynccontextmanager` lifespan (not deprecated `on_event`)
3. **Context var correlation**: `contextvars` for request_id, endpoint, user_id, lab_id
4. **Sliding window monitoring`: 5-minute DB event window with Redis persistence
5. **Optimistic locking**: `version` column on LabOrder and LabResult
6. **Transactional outbox**: `OutboxEvent` table with FOR UPDATE SKIP LOCKED
7. **Hash chain audit**: SHA-256 chain with HMAC-anchored checkpoint files
8. **Dual-read rule**: national_id and sndhs_health_id may be None
9. **Edge guard**: Blocks edge_* table access from API/test/cli runtimes

---

## 6. Background Worker Architecture

Entry point: `python -m app.worker` (RUNTIME_MODE=worker)

6 resilient loops with crash isolation and exponential backoff (5s→120s max):
1. `OutboxWorker.background_loop` — dispatch pending events (10s poll)
2. `RecoveryWorker.background_loop` — probe failed services (30s poll)
3. `_health_alert_loop` — GREEN/YELLOW/RED scoring (60s)
4. `_adaptive_concurrency_loop` — dynamic throttle adjustment
5. `auto_repair.run` — GC, pool recycle, reconnect
6. `TaskWorker` — discrete task queue

---

## 7. Key Findings

| Finding | Evidence | Impact |
|---------|----------|--------|
| Version divergence | config.py: 2.1.0, CHANGELOG.md: 2.3.2 | Tracking confusion |
| Massive EHR route file | `routes/ehr.py` at 73,097 bytes | Maintainability risk |
| 2 clinical engines | `backend/app/routes/ai.py` (Ollama/Gemini/Groq) vs `services/ai/main.py` (Ollama-only) | Duplication |
| 7 microservice stubs | No tests, basic CRUD only | Not production-ready |
| Routes far exceed CLAUDE.md count | 53 vs documented 36 | Documentation stale |
| 54% test coverage | Routes 35%, Services 30% | Below enterprise threshold |
| Edge/interop coverage | 0% | Critical gap |
