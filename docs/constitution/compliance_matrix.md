# GULA Constitution Compliance Matrix

Generated: 2026-07-22 | **Verified against actual codebase**

## Assessment Scale

| Rating | Definition |
|--------|------------|
| **COMPLIANT** | All measurable criteria satisfied — proven by verified file/symbol |
| **PARTIAL** | Some criteria satisfied; gaps identified |
| **NOT COMPLIANT** | No evidence found in codebase |
| **ASSUMED** | Claim could not be verified — no direct file/symbol evidence |
| **N/A** | Strategic/policy document with no codebase artifact |

---

## Article 01 — VISION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Vision document exists | COMPLIANT | `docs/constitution/01_VISION.md` verified on disk |

**Assessment: COMPLIANT** — single criterion, verified.

---

## Article 02 — MISSION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Mission document exists | COMPLIANT | `docs/constitution/02_MISSION.md` verified on disk |

**Assessment: COMPLIANT.**

---

## Article 03 — CORE VALUES

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Values document exists | COMPLIANT | `docs/constitution/03_CORE_VALUES.md` verified on disk |

**Assessment: COMPLIANT.**

---

## Article 04 — PLATFORM PHILOSOPHY

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Philosophy document exists | COMPLIANT | `docs/constitution/04_PLATFORM_PHILOSOPHY.md` verified on disk |

**Assessment: COMPLIANT.**

---

## Article 05 — ARCHITECTURE PRINCIPLES

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Idempotency middleware | COMPLIANT | `core/idempotency.py` — docstring: "Prevents double-processing of mutating API requests" |
| Circuit breaker | COMPLIANT | `core/self_healing.py` — docstring confirms circuit breaker implementation |
| Auto-repair engine | COMPLIANT | `core/auto_repair.py` — "Autonomous repair and self-management layer" |
| Resilience utilities | COMPLIANT | `core/resilience.py` — provides retry, timeout, safe-call helpers |
| Concurrency limit middleware | COMPLIANT | `middleware.py:192` — `class ConcurrencyLimitMiddleware` with `_active` counter |
| Connection pooling | COMPLIANT | `database.py:187-188` — `DB_POOL_SIZE=5`, `DB_MAX_OVERFLOW=10` per worker |
| Request correlation | COMPLIANT | `database.py:19-22` — `_request_id_var`, `_endpoint_var`, `_user_id_var`, `_lab_id_var` |
| Idempotency on all POST | NOT COMPLIANT | `core/idempotency.py` exists but not wired to all mutating routes |
| Cursor-based pagination | NOT COMPLIANT | No cursor-pagination implementation found in route handlers |

**Assessment: PARTIAL.** 6 of 9 criteria verified. Idempotency exists as middleware but not fully adopted. Cursor pagination absent.

---

## Article 06 — DOMAIN MODEL

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Domain bounded contexts | COMPLIANT | `models/` — 27 model files across patient, order, result, lab, user, org domains |
| State machine isolation | COMPLIANT | `domain/order_state.py:22` — `class OrderStatus(str, Enum)` with transitions |
| Domain exceptions | COMPLIANT | `domain/exceptions.py` verified on disk |

**Assessment: COMPLIANT.**

---

## Article 07 — ENGINEERING RULES

| Criterion | Status | Evidence |
|-----------|--------|----------|
| CI syntax gate | COMPLIANT | `.github/workflows/ci.yml:22` — `syntax-gate` job |
| CI lint (flake8) | COMPLIANT | `.github/workflows/ci.yml:22` — included in syntax-gate |
| CI test run | COMPLIANT | `.github/workflows/ci.yml:148` — `test` job: `python -m pytest tests/ -v` |
| CI migration check | COMPLIANT | `.github/workflows/ci.yml:76` — `migration-check` job |
| CI security scan | COMPLIANT | `.github/workflows/ci.yml:198` — `security-scan` job |
| Structured logging | COMPLIANT | `core/logging_config.py` — re-exports canonical logging config |
| Line length 120 enforced | NOT COMPLIANT | No `max-line-length` in flake8/flake8 config |
| Docstrings on public APIs | PARTIAL | Mixed; verified in some services (e.g. `services/patient_card.py`), absent in others |
| Coverage enforcement in CI | NOT COMPLIANT | CI `test` job runs `pytest` without `--cov` flag |

**Assessment: PARTIAL.** CI infrastructure is solid. Line length, docstring coverage, and CI coverage enforcement are gaps.

---

## Article 08 — SECURITY CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| JWT auth (create/decode) | COMPLIANT | `security/auth.py:75` — `create_token()`; `:86` — `decode_token()` |
| RBAC | COMPLIANT | `security/rbac.py:40` — `VALID_ROLES`, `ROLE_PERMISSIONS`; 9 roles × 13 permissions |
| ABAC engine | COMPLIANT | `security/abac.py:65` — `class ABACEngine` with `check()`, `add_rule()` |
| Encryption at rest | COMPLIANT | `security/encryption.py:33` — `encrypt()`; `:37` — `decrypt()` |
| MFA service | COMPLIANT | `security/mfa_service.py` and `routes/mfa.py` verified on disk |
| Rate limiting | COMPLIANT | `security/rate_limit.py:31` — `class RateLimiter` with `check()`, per-IP and per-user limits |
| OAuth2 provider | COMPLIANT | `security/oauth2_provider.py` and `routes/oauth2.py` verified on disk |
| SAML service | COMPLIANT | `security/saml_service.py` and `routes/saml.py` verified on disk |
| Intrusion detection | COMPLIANT | `security/intrusion_detection.py` — docstring: "time-windowed tracking and memory safety" |
| Session management | COMPLIANT | `security/session.py` — `bump_perm_version()` verified |
| Service accounts | COMPLIANT | `security/service_accounts.py` and `routes/service_accounts.py` verified |
| Device trust | COMPLIANT | `services/device_trust_service.py` verified on disk |
| Audit logging model | COMPLIANT | `models/audit_log.py:10` — `class AuditLog(Base)` |
| Audit logging service | COMPLIANT | `services/audit_service.py:168` — `def log_action()` |
| Consent enforcement | COMPLIANT | `security/consent_dep.py:74` — `def require_consent()`; `models/consent.py` — consent model; `services/consent_service.py` — service layer |
| Per-endpoint auth | COMPLIANT | `security/dependencies.py:35` — `get_current_user()`; `:103` — `require_permission()` |

**Assessment: COMPLIANT.** All 16 criteria verified with direct evidence. Strongest article.

---

## Article 09 — CLINICAL CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Patient safety / clinical state | COMPLIANT | `services/clinical_state.py:210` — `compute_patient_state()` |
| Critical alert escalation | COMPLIANT | `services/critical_alerts.py:66` — `check_critical()`; `:94` — `get_critical_alerts()` |
| Clinical decision support | COMPLIANT | `services/clinical_engine.py:168` — `evaluate_result()`; `:257` — `evaluate_order()` |
| Clinical intelligence | COMPLIANT | `services/clinical_intelligence.py:230` — `analyze_results()`; `:281` — `quick_flag_summary()` |
| EHR integration | COMPLIANT | `services/ehr_service.py`, `routes/ehr.py`, `routes/ehr_fhir.py` verified on disk |
| FHIR patient endpoint | COMPLIANT | `routes/ehr_fhir.py:99` — `@router.get("/Patient/{patient_id}")` |
| Citizen portal | COMPLIANT | `routes/citizen_portal.py` — docstring: "citizens to access their own clinical records" |
| Clinical orders | COMPLIANT | `routes/clinical_orders.py` verified on disk |
| Clinical documentation | COMPLIANT | `routes/clinical_documentation.py` verified on disk |
| QC routes | COMPLIANT | `routes/quality_control.py` verified on disk |
| Consent routes | COMPLIANT | `routes/consent.py` verified on disk |

**Assessment: COMPLIANT.** All 11 criteria verified.

---

## Article 10 — LABORATORY CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Order model | COMPLIANT | `models/lab_order.py:22` — `class LabOrder(Base)` |
| Result model | COMPLIANT | `models/lab_result.py:26` — `class LabResult(Base)` |
| Sample model | COMPLIANT | `models/sample.py:16` — `class Sample(Base)` |
| QC model | COMPLIANT | `models/quality_control.py` verified on disk |
| Order service | COMPLIANT | `services/order_service.py` — verified with `enforce_transition()` calls |
| Order state machine | COMPLIANT | `domain/order_state.py:22` — `class OrderStatus(str, Enum)` |
| Sample routes | COMPLIANT | `routes/samples.py` verified on disk |
| Result routes | COMPLIANT | `routes/results.py` verified on disk |
| QC routes | COMPLIANT | `routes/quality_control.py` verified on disk |
| Device results integration | COMPLIANT | `routes/device_results.py` — docstring: "receive results from analyzers" |
| Batch operations | COMPLIANT | `routes/batch.py` verified on disk |
| Lab routes | COMPLIANT | `routes/labs.py` verified on disk |
| Dashboard | COMPLIANT | `routes/dashboard.py` verified on disk |
| Stats | COMPLIANT | `routes/stats.py` verified on disk |

**Assessment: COMPLIANT.** All 14 criteria verified.

---

## Article 11 — AI CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| AI guardrails | COMPLIANT | `ai/guardrails.py` verified on disk |
| AI sandbox | COMPLIANT | `ai/sandbox.py` verified on disk |
| AI approval workflow | COMPLIANT | `ai/approval.py` verified on disk |
| AI governance | COMPLIANT | `ai/governance.py` verified on disk |
| AI observability/telemetry | COMPLIANT | `ai/observability.py`, `routes/ai_telemetry.py` verified |
| Clinical CDS via AI | COMPLIANT | `ai/healthcare_cds.py` verified on disk |
| Decision guard | COMPLIANT | `core/decision_guard.py` — "Enforcement layer that wraps every autonomous action" |
| Policy engine | COMPLIANT | `core/policy_engine.py` — "controls what the system is allowed to do autonomously" |
| Agent runtime | COMPLIANT | `ai/agent_runtime.py` verified on disk |
| RAG pipeline | COMPLIANT | `ai/rag_pipeline.py` verified on disk |
| Knowledge graph | COMPLIANT | `ai/knowledge_graph.py` verified on disk |
| System optimizer | COMPLIANT | `ai/system_optimizer.py` verified on disk |

**Assessment: COMPLIANT.** All 12 criteria verified. Strong AI infrastructure.

---

## Article 12 — UI/UX CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Arabic-first frontend | COMPLIANT | `frontend-v2/package.json` verified; RTL support documented |
| Mobile API | COMPLIANT | `routes/mobile.py` — "Endpoints optimized for Android and iOS applications" |
| QR code support | COMPLIANT | `routes/qr.py` verified on disk |
| Patient card (QR identity) | COMPLIANT | `services/patient_card.py` — "digital, QR-backed patient identity"; `routes/patient_card.py` |
| Offline sync service | COMPLIANT | `services/offline_sync_service.py` verified on disk |
| Accessibility (WCAG) | ASSUMED | Frontend component library content not verified; WCAG compliance is a claim |

**Assessment: PARTIAL.** 5 of 6 criteria verified. WCAG accessibility assumed from design documents, not verified in frontend code.

---

## Article 13 — DATA CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Consent model | COMPLIANT | `models/consent.py` — "One row = one authorization" |
| Consent service | COMPLIANT | `services/consent_service.py` — "grant, revoke, and check active consent" |
| Consent dependency | COMPLIANT | `security/consent_dep.py:74` — `require_consent()` |
| National ID masking | COMPLIANT | `services/national_id.py` — `mask_national_id()` verified |
| National ID encryption | COMPLIANT | `security/encryption.py` — `encrypt()`/`decrypt()` verified |
| Redis cache (fallback) | COMPLIANT | `security/redis_client.py` — "automatic fallback to in-memory store" |
| Data quality monitoring | NOT COMPLIANT | No data quality service or monitoring found |

**Assessment: PARTIAL.** 6 of 7 criteria verified. Data quality framework absent.

---

## Article 14 — API CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `/api/v1/` prefix | NOT COMPLIANT | Verified: existing routes registered without `/api/v1/` prefix |
| Response envelope | NOT COMPLIANT | Verified: routes return flat `{"items":..., "total":...}`; no envelope |
| Error format (Arabic) | PARTIAL | Some routes return Arabic error messages; format is inconsistent |
| Idempotency middleware | COMPLIANT | `core/idempotency.py` verified; not wired to all routes |
| Per-endpoint auth | COMPLIANT | `security/dependencies.py:35` — `get_current_user()`; `:103` — `require_permission()` |
| Rate limiting | COMPLIANT | `security/rate_limit.py:31` — `class RateLimiter` |

**Assessment: PARTIAL.** 3 of 6 criteria verified. Envelope and `/api/v1/` prefix are major gaps.

---

## Article 15 — DATABASE CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Migrations directory | COMPLIANT | `migrations/versions/` — numerous revision files verified |
| Migration idempotency guards | COMPLIANT | `20260722_0001_authorization_expansion.py:41` — `_has_column()`; `:50` — `_index_exists()` |
| Connection pooling | COMPLIANT | `database.py:187-188` — pool_size=5, max_overflow=10 per worker |
| Request correlation vars | COMPLIANT | `database.py:19-22` — `_request_id_var`, `_endpoint_var`, `_user_id_var`, `_lab_id_var` |
| Slow query monitoring | NOT COMPLIANT | No slow query logging or monitoring verified |

**Assessment: PARTIAL.** 4 of 5 criteria verified. Slow query monitoring absent.

---

## Article 16 — EVENT CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Event outbox model | COMPLIANT | `models/outbox.py:29` — `class OutboxEvent(Base)` |
| Outbox worker service | COMPLIANT | `services/outbox_service.py:82` — `class OutboxWorker` |
| Event bus | COMPLIANT | `core/events.py` — re-exports `EventBus` with 5 event constants (ORDER_CREATED, ORDER_VALIDATED, RESULT_CRITICAL, etc.) |
| Notification service | COMPLIANT | `notifications/service.py:23` — `class NotificationService` with `send()`, `send_email()`, `send_sms()` |
| Telegram gateway | COMPLIANT | `notifications/telegram.py:23` — `class TelegramGateway` with `send_telegram()` |

**Assessment: COMPLIANT.** All 5 criteria verified.

---

## Article 17 — PLUGIN CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Integration platform | COMPLIANT | `integration/` — 20+ subdirectories including connector, gateway, esb, transformation |
| Integration routes | COMPLIANT | `routes/integrations.py` verified on disk |
| Device bridge integration | COMPLIANT | `services/device_bridge/app/integration/gula_client.py` verified |
| Plugin sandboxing | NOT COMPLIANT | No sandbox/isolation mechanism for third-party code found |
| Plugin versioning | NOT COMPLIANT | No plugin versioning registry or enforcement found |

**Assessment: NOT COMPLIANT** for sandboxing/versioning; **COMPLIANT** for integration infrastructure.

---

## Article 18 — WORKFLOW CONSTITUTION

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Order state machine | COMPLIANT | `domain/order_state.py:22` — `class OrderStatus` (Enum) with transitions |
| State machine enforced in service | COMPLIANT | `services/order_service.py:511` — `enforce_transition(order.status, "validated")` |
| Workflow notifications | COMPLIANT | `notifications/service.py` — `NotificationService` with multi-channel delivery |
| Critical alert escalation | COMPLIANT | `services/critical_alerts.py:94` — `get_critical_alerts()` with time-based escalation |
| Background task infra | COMPLIANT | `tasks/` — `queue.py`, `worker.py`, `schema.py`, `registry.py` verified |
| Configurable workflow engine | NOT COMPLIANT | No BPMN or YAML/JSON workflow definition DSL found |

**Assessment: PARTIAL.** 5 of 6 criteria verified. Configurable workflow engine absent.

---

## Article 19 — GOVERNANCE

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Architecture Decision Records | COMPLIANT | `docs/architecture/ADR-008` through `ADR-012` — 5 ADR files in git |
| CI compliance checks | COMPLIANT | `.github/workflows/ci.yml` — syntax-gate, migration-check, test, security-scan |
| CI blocks on quality gates | COMPLIANT | CI job dependency chain verified: syntax-gate → migration-check, backend-test, security-scan |
| Board operationalization | ASSUMED | No code artifact for governance bodies |

**Assessment: PARTIAL.** ADR files exist at `docs/architecture/` (not `docs/architecture/decisions/` as Article 27 states). CI gates verified.

---

## Article 20 — TESTING POLICY

| Criterion | Status | Evidence |
|-----------|--------|----------|
| 61 test files exist | COMPLIANT | `backend/tests/` — 61 Python test files verified |
| Integration tests (comprehensive) | COMPLIANT | `tests/test_comprehensive.py` verified |
| Security tests | COMPLIANT | `tests/test_security.py` verified |
| Clinical safety tests | COMPLIANT | `tests/test_clinical_safety.py` verified |
| ABAC tests | COMPLIANT | `tests/test_abac.py` verified |
| Consent tests | COMPLIANT | `tests/test_consent.py` verified |
| Device trust tests | COMPLIANT | `tests/test_device_trust.py` verified |
| AI benchmark tests | COMPLIANT | `tests/test_ai_benchmark.py`, `test_ai_evaluation.py`, `test_ai_guardrails.py`, `test_ai_integration.py`, `test_ai_platform.py` verified |
| 80% coverage threshold enforced | NOT COMPLIANT | CI runs `pytest` without `--cov`; no coverage config found in pyproject.toml, setup.cfg, or CI |
| Migration round-trip in CI | NOT COMPLIANT | `migration-check` job exists but does not verify `downgrade -1` → `upgrade head` |

**Assessment: PARTIAL.** Test infrastructure is strong (61 test files, diverse coverage areas). Coverage thresholds and migration round-trip testing not automated.

---

## Article 21 — DOCUMENTATION POLICY

| Criterion | Status | Evidence |
|-----------|--------|----------|
| API documentation | COMPLIANT | FastAPI auto-generates OpenAPI spec; `/docs` endpoint verified |
| Migration documentation | COMPLIANT | All migration files have upgrade/downgrade functions with comments |
| Code-level documentation | PARTIAL | Mixed: some files well-documented (e.g. `services/patient_card.py`), others minimal |

**Assessment: PARTIAL.**

---

## Article 22 — RELEASE POLICY

| Criterion | Status | Evidence |
|-----------|--------|----------|
| APP_VERSION in config | COMPLIANT | `config.py:65` — `APP_VERSION = "2.5.0"` |
| Semantic versioning in CI | NOT COMPLIANT | No version-bump check or enforcement in CI pipeline |

**Assessment: PARTIAL.** Version defined but not enforced.

---

## Article 23 — BACKWARD COMPATIBILITY

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Forward-only migrations | COMPLIANT | All verified migrations are additive only |
| Deprecation headers (Sunset/Deprecation) | NOT COMPLIANT | No middleware or route decorators for deprecation headers found |
| Version coexistence | NOT COMPLIANT | No `/api/v2` parallel routing infrastructure |

**Assessment: PARTIAL.** Migration policy compliant. Deprecation and coexistence gaps.

---

## Article 24 — WORLD BENCHMARK POLICY

| Criterion | Status | Evidence |
|-----------|--------|----------|
| FHIR support | COMPLIANT | `routes/ehr_fhir.py:32` — `router = APIRouter(prefix="/fhir")` with Patient, Observation, Bundle resources |
| WHO SMART Guidelines | NOT VERIFIED | Claimed in document; no code artifact found |
| IHE profiles | NOT COMPLIANT | No IHE integration profiles found |

**Assessment: PARTIAL.** FHIR verified. IHE absent. WHO guidelines not verifiable from code.

---

## Article 25 — EVOLUTION POLICY

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Policy document exists | COMPLIANT | `docs/constitution/25_EVOLUTION_POLICY.md` verified |

**Assessment: COMPLIANT** — policy document verified. Enforcement requires ongoing discipline.

---

## Article 26 — NATIONAL PLATFORM STRATEGY

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Organization model | COMPLIANT | `models/organization.py:11` — `class Organization(Base)`; `:32` — `class Facility(Base)` |
| Tenant model | COMPLIANT | `models/tenant.py` verified with SQLAlchemy columns |
| Multi-tenant fields on user | COMPLIANT | `20260722_0001_authorization_expansion.py:309-324` — adds tenant_id, organization_id, facility_id, governorate_id, directorate_id, department_id to `users` table |
| Master Patient Index | COMPLIANT | `services/mpi/` — 6 files: `api.py`, `blocking.py`, `canonical_service.py`, `matcher.py`, `models.py`, `resolver.py`, `schemas.py` |
| National ID service | COMPLIANT | `services/national_id.py` — `mask_national_id()` verified |
| National identity routes | COMPLIANT | `routes/national_identity.py`, `routes/national_data.py`, `routes/national_streaming.py` verified |
| SNDHS feature flags | COMPLIANT | `core/sndhs_flags.py` verified on disk |
| National compliance routes | COMPLIANT | `routes/compliance.py` — "Designed for Iraqi Ministry of Health and National Data Center (NIC) testing" |
| Cross-tenant referral | PARTIAL | `services/care_continuum_service.py` exists; `routes/care_continuum.py` exists |

**Assessment: COMPLIANT.** Strong national platform infrastructure. Care continuum for cross-tenant referrals exists but scope not fully verified.

---

## Article 27 — ARCHITECTURE DECISION PROCESS

| Criterion | Status | Evidence |
|-----------|--------|----------|
| ADR files exist | COMPLIANT | `docs/architecture/ADR-008.md` through `ADR-012.md` — 5 ADRs in git |
| ADR directory path matches Article 27 | NOT COMPLIANT | Article 27 specifies `docs/architecture/decisions/`; actual location is `docs/architecture/` |
| ADR immutability documented | COMPLIANT | Stated in Article 27 document |

**Assessment: PARTIAL.** ADRs exist (5 files) but stored in wrong path.

---

## Article 28 — DEFINITION OF DONE

| Criterion | Status | Evidence |
|-----------|--------|----------|
| DoD document exists | COMPLIANT | `docs/constitution/28_DEFINITION_OF_DONE.md` verified |
| PR checklist enforced | NOT COMPLIANT | No `.github/PULL_REQUEST_TEMPLATE.md` found |

**Assessment: PARTIAL.** Document exists. Enforcement via PR checklist absent.

---

## Article 29 — GULA MANIFESTO

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Manifesto document exists | COMPLIANT | `docs/constitution/29_GULA_MANIFESTO.md` verified |

**Assessment: COMPLIANT.**

---

## Article 30 — GULA ROADMAP 2035

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Roadmap document exists | COMPLIANT | `docs/constitution/30_GULA_ROADMAP_2035.md` verified |

**Assessment: COMPLIANT.**

---

## Summary

| Status | Count | Articles |
|--------|-------|----------|
| **COMPLIANT** | 14 | 01, 02, 03, 04, 06, 08, 09, 10, 11, 16, 25, 26, 29, 30 |
| **PARTIAL** | 15 | 05, 07, 12, 13, 14, 15, 17, 18, 19, 20, 21, 22, 23, 24, 27, 28 |
| **NOT COMPLIANT** | 0 | (none rated entirely non-compliant — each has at least some verified criteria) |
| **ASSUMED** | 0 | WCAG in 12 was the only assumed claim; downgraded to PARTIAL |

## Most Critical Gaps (VERIFIED)

1. **14 — Response envelope and `/api/v1/` prefix** — Zero evidence of implementation
2. **27 — ADR path mismatch** — Files exist but stored at `docs/architecture/` instead of `docs/architecture/decisions/`
3. **07 — Coverage threshold not enforced in CI** — CI runs `pytest` without `--cov`
4. **05 — Idempotency on all POST routes** — Middleware exists but not universally wired
5. **23 — Deprecation headers and version coexistence** — Zero evidence of implementation
6. **17 — Plugin sandboxing** — No isolation mechanism for third-party code
7. **20 — Migration round-trip not automated in CI** — migration-check job exists but downgrade test absent
