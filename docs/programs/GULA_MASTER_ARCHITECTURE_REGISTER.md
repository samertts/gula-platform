# GULA Master Architecture Register

Status: **STATIC INVENTORY — NOT A PRODUCTION CERTIFICATION**. Baseline: `a01352578c0df205b92e58444242e1fa6ae7d77b`. Evidence timestamp: `20261126T053405Z`.

Canonical backend boundary: `backend/app/`. Canonical web app: `frontend-v3/`. `services/`, `platform/`, `nhop-platform/`, `client/`, mobile/desktop/edge roots are parallel or future-decomposition trees until explicitly reconciled (`docs/START_HERE.md:5,12-15`). `HOLD=TRUE`, G1–G12 `NOT PASSED`; every classification below is subordinate to `NOT_APPROVED`.

## Classification legend

- `IMPLEMENTED_AND_TESTED`: canonical code present, reachable through `backend/app/factory.py`, static test evidence exists. Tests were not executed by the inventory audit.
- `IMPLEMENTED_BUT_UNWIRED`: code/router exists but is not reachable through the canonical composition root.
- `SYNTHETIC_ONLY`: explicit synthetic/in-memory composition; not operational proof.
- `DESIGN_ONLY`: documentation/configuration/proposal only.
- `PARTIALLY_VERIFIED`: static implementation plus wiring/tests, but material gaps or contradictions remain.
- `BLOCKED`: explicit schema/owner/external-authority blocker.
- `NOT_IMPLEMENTED`: explicit 501/stub/missing module/standard gap.
- `NOT_APPROVED`: no owner acceptance artifact; gates/HOLD unchanged.

## 1. Cross-cutting blockers

| Blocker | Evidence | Status |
|---|---|---|
| Pharmacy primary-key divergence: ORM `String(26)` vs migration `Integer` | `backend/app/pharmacy/base.py:22-30`; `backend/migrations/versions/20260716_0003_pharmacy_platform.py:52,96,127,167`; `docs/architecture/GULA_MASTER_NEGATIVE_REGISTER.md:34,42,78` | `BLOCKED` (NR-003) |
| Dual ownership of `national_facilities` | `backend/app/models/clinical_scope.py:136`; `backend/app/national/domain/facility.py:9`; negative register `:45,108` | `BLOCKED` (NR-006) |
| Entity-agnostic clinical state machine | negative register `:46,79,93` | `BLOCKED` (NR-007) |
| Full `alembic upgrade head` | negative register `:156-158` | `BLOCKED` |
| Identity/MPI, consent, offline, FHIR/DICOM/terminology, AI safety, security, DR, capacity, several domains unaudited/not started | negative register `:127-136` | `NOT_APPROVED` / `NOT_IMPLEMENTED` |

## 2. Component inventory

### 2.1 National core and governance

| Component | Evidence | Status | Notes |
|---|---|---|---|
| Canonical composition root | `backend/app/main.py:28-31`; `backend/app/factory.py:519-828` | `PARTIALLY_VERIFIED` | Single HTTP composition root; cohesion concerns at `docs/architecture/enterprise_architecture.md:150-159`. |
| NIAM identity aggregator | `backend/app/identity/api/router.py:30-55`; `factory.py:819-820`; `backend/tests/identity/test_authorization_phase8.py:121-369` | `IMPLEMENTED_AND_TESTED` | Narrow slice; OTP/MFA/recovery/step-up deferred (`docs/security/IAM_AUTHENTICATION.md:3,29`). |
| Canonical ADE | `factory.py:825-826`; `backend/app/identity/services/authorization_decision.py` | `PARTIALLY_VERIFIED` | Consent, governorate, break-glass, role matrix open; narrow null/empty fail-closed fix applied in Phase 4, not owner-accepted. |
| MPI/canonical patient | `factory.py:616-620`; `backend/app/services/mpi/matcher.py:50-103,178-190`; `test_mpi_matcher.py:36-284`; `test_wave05_1_mpi_safety.py:37-178`; `test_mpi_reliability.py:30-204` | `IMPLEMENTED_AND_TESTED` | Safety helpers unbound from mounted resolver (MGR-004). |
| National identity registration/persistence/security | `backend/app/national/services/citizen_registration.py`, `identity_persistence.py`, `document_authenticity.py:3-8,202-206` | `SYNTHETIC_ONLY` / `BLOCKED` | Real authority, approved durable store, original-document authenticity, activation route blocked. |
| National domain API aggregator | `backend/app/national/api/routes/__init__.py:20-36` | `IMPLEMENTED_BUT_UNWIRED` | 16 subrouters; no factory include. |
| Wired national platform routers | `factory.py:689-716,718-722,781-787` | `PARTIALLY_VERIFIED` | Rules, background, workflow, task, notification, document, scheduling, observability, data/streaming, ecosystem, intelligence mounted. |
| National search platform | `factory.py:712-713`; `backend/app/national/search_platform/api/routes.py:23-33`; adapter stubs `application/interfaces.py:128-188,266` | `PARTIALLY_VERIFIED` | PostgreSQL full-text path; Elasticsearch/FHIR/document-index paths return 501. |

### 2.2 Clinical platform

| Component | Evidence | Status | Notes |
|---|---|---|---|
| Canonical LIMS | `backend/app/lims/routes.py:54,831-874,1075-1201,1290`; `factory.py:686-687`; `test_lims_release_capability_gate.py:35-76`; `test_lims_tenant_isolation.py` | `IMPLEMENTED_AND_TESTED` | Outbox, critical quarantine, result-integrity gaps open. |
| Lab slice | `backend/app/lab_slice/`; `test_lab_slice_pipeline.py:20,305` | `SYNTHETIC_ONLY` | Not durable production outbox. |
| Clinical routes/orders/documentation/quality | `factory.py:670-677`; `MASTER_AUDIT_2050.md:854-862` | `PARTIALLY_VERIFIED` | State-machine and replay semantics open. |
| EHR/FHIR API | `backend/app/routes/ehr_fhir.py:53-63,801-863`; `factory.py:537,570`; `frontend-v3/e2e/fhir.spec.ts` | `PARTIALLY_VERIFIED` | Stale 501 report for Procedure at `backend/app/fhir/_validation_report.py:31-57`. |
| FHIR interoperability capability | `backend/app/capabilities/fhir_interoperability/routes.py:23,47-142`; `factory.py:656-658` | `PARTIALLY_VERIFIED` | Unguarded `/metadata`, `/health/` (MGR-017). |
| National clinical integration layer | `backend/app/national/clinical_integration.py:1-17`; `test_national_clinical_integration_e2e.py:1-5,523,658,697,740,768,799,851` | `SYNTHETIC_ONLY` | Route-free composition; imported only by test. |
| Chronic care | `backend/app/chronic_care/routes.py:19,30-32`; `factory.py:654-655` | `NOT_IMPLEMENTED` | Mounted 501 operations. |
| Clinical terminology | `MASTER_SYSTEM_ATLAS.md:306-313`; `docs/enterprise/executive/07_HEALTHCARE_ATLAS.md:51-54` | `NOT_IMPLEMENTED` | LOINC/SNOMED/ICD-10 missing or model-only; stale Active claim. |
| Capability skeletons except FHIR | `backend/app/capabilities/{clinical_foundation,encounter_management,healthcare_consent,workflow_engine,search_service,storage_service,document_management,provider_management,reporting_service}/routes.py:9` | `IMPLEMENTED_BUT_UNWIRED` | Only FHIR main router wired. Encounter and national FHIR stubs were explicitly labeled in Phase 4. |
| Sensitive clinical bridges | `docs/iam/P4_SENSITIVE_FEATURE_FLAG_INVENTORY.md:13-24` | `NOT_IMPLEMENTED` | All OFF/proposed. |

### 2.3 Domain modules

| Component | Evidence | Status | Notes |
|---|---|---|---|
| Pharmacy | `backend/app/pharmacy/routes.py:27,577-1175`; `factory.py:739-740`; `test_pharmacy_pos.py`; `test_pharmacy_radiology_workflow_p0.py` | `BLOCKED` | NR-003 schema/PK divergence blocks deployment. |
| Radiology/PACS | `backend/app/radiology/routes.py:37,499-1353`; `factory.py:742-743`; `test_radiology_tenant_isolation.py`; `test_clinical_radiology_read_gate.py` | `PARTIALLY_VERIFIED` | DICOM server `NOT IMPLEMENTED`. |
| Nursing | `factory.py:736-737`; `test_clinical_nursing_read_gate.py` | `PARTIALLY_VERIFIED` | Docs call it schema-only. |
| Hospital/NHDW | `factory.py:730-734`; `backend/app/nhdw/routes.py:47,316+` | `PARTIALLY_VERIFIED` | Docs call it schema-only. |
| Blood bank | `factory.py:795-796`; `tests/blood_bank/test_domain_safety.py:10-60`; `test_http_idempotency_postgres.py:160-360` | `PARTIALLY_VERIFIED` | Deepest certified-depth domain; full upgrade blocked by NR-003. |
| EMS, critical care, biomedical, care continuum | wired at `factory.py:789-799,663-664` | `PARTIALLY_VERIFIED` | Documentation contradictions; no complete dedicated proof. |
| Dentistry | `MASTER_AUDIT_2050.md:984-988`; `MASTER_SYSTEM_ATLAS.md:295` | `NOT_IMPLEMENTED` | No module/routes/models/clinical logic found. |

### 2.4 Public health

| Component | Evidence | Status |
|---|---|---|
| National public-health surveillance API | `backend/app/public_health/api/routes.py:23-26,42-236`; `factory.py:804-805` | `PARTIALLY_VERIFIED` |
| Layered domain/application/infrastructure | `backend/app/public_health/domain/entities.py`, `application/service.py`, `infrastructure/models.py` | `PARTIALLY_VERIFIED` |
| Vaccination → event → surveillance contract | `test_journey_contract_reliability_synthetic.py:42,53,98-246` | `SYNTHETIC_ONLY` |
| Frontend channel | `frontend-v3/src/routes/index.tsx:97,228`; `src/pages/public-health/PublicHealthApiPage.tsx:32-58` | `PARTIALLY_VERIFIED` |

Contradictory `Present`/`Live`/`SCHEMA ONLY` docs are resolved as `PARTIALLY_VERIFIED`: real wired API exists, but no production certification.

### 2.5 Health operations

| Component | Evidence | Status |
|---|---|---|
| Legacy insurance route | `backend/app/routes/insurance.py:7-10`; `factory.py:604-605` | `PARTIALLY_VERIFIED` |
| Insurance API package | `backend/app/insurance/api/{claims,coverages,coverage_check,network,payments,policies,providers,referrals}.py` | `IMPLEMENTED_BUT_UNWIRED` |
| Claims/billing/payments/finance | `factory.py:582,590-602`; `test_billing_routes.py`, `test_payments_foundation.py`, `test_financial_controls.py` | `IMPLEMENTED_AND_TESTED` static |
| Workflow/notification/document/scheduling, command center, citizen platform | `factory.py:692-710,769-770,807-817` | `PARTIALLY_VERIFIED` |
| Alternate Telegram webhook | `backend/app/routes/telegram_webhook.py:18,54,83` | `IMPLEMENTED_BUT_UNWIRED` |

### 2.6 Analytics

| Component | Evidence | Status |
|---|---|---|
| Governance analytics | `backend/app/governance/routes/analytics_routes.py:10-60`; `factory.py:682-684` | `PARTIALLY_VERIFIED` |
| Constitution governance routes | `backend/app/governance/routes/constitution_routes.py:18-19,57-139`; omitted from `routes/__init__.py:1-4` | `IMPLEMENTED_BUT_UNWIRED` |
| National intelligence | `backend/app/national/intelligence/routes.py:68,119-460`; `factory.py:786-787` | `PARTIALLY_VERIFIED`; AI safety audit NOT STARTED |
| Health data/warehouse/ODS/MDM | `backend/app/health_data/routes.py:25,53-346`; `factory.py:757-758` | `PARTIALLY_VERIFIED` |
| Research platform | `backend/app/research_platform/routes.py:18,41-335`; `factory.py:775-776` | `PARTIALLY_VERIFIED` |
| Reporting capability | `backend/app/capabilities/reporting_service/routes.py:9` | `IMPLEMENTED_BUT_UNWIRED` |
| Certification coverage reports | `docs/certification/*coverage_report.md:9,34-38`; `api_hook_coverage_report.md:9,34-38` | `PARTIALLY_VERIFIED` static; NOT_APPROVED stands |

### 2.7 Access channels

| Component | Evidence | Status |
|---|---|---|
| Primary web app `frontend-v3` | `docs/START_HERE.md:5,12-15`; 95 page components; 29 unit/e2e/spec files statically found | `PARTIALLY_VERIFIED` |
| Role-guarded lazy routes for NIAM, FHIR, hospital, national, public health, blood bank, pharmacy | `frontend-v3/src/routes/index.tsx:31,41-56,80-97,161-228` | `PARTIALLY_VERIFIED` |
| Frontend e2e suite | `frontend-v3/e2e/{auth,billing-insurance,fhir,orders,patients,results,samples}.spec.ts` | `IMPLEMENTED_AND_TESTED` static |
| Parallel web/mobile/desktop/edge roots | `client/`, `apps/gula-platform-ui-refresh/`, `apps/gula-web-suite/`, `nhop-platform/`, `mobile/`, `mobile-expo/`, `hospital_desktop/`, `edge_agent/`, `platform/apps/` | `IMPLEMENTED_BUT_UNWIRED` |
| Government gateways | `backend/app/gateways/mode.py:45-77`; `backend/app/national/services/government_verification.py` | `BLOCKED` |
| Sensitive access bridges | `docs/iam/P4_SENSITIVE_FEATURE_FLAG_INVENTORY.md:4,13-24` | `NOT_IMPLEMENTED` |

## 3. Confirmed unwired router register

- `national_router` and 16 subrouters at `backend/app/national/api/routes/__init__.py:3-18,20-36`: `advance_directive`, `cds`, `citizen`, `consent`, `encounter`, `family`, `fhir`, `health_card`, `identity`, `interop`, `medication_catalog`, `observation`, `reference`, `referral`, `security`, `vital_signs`.
- Insurance API package (`backend/app/insurance/api/*.py`); factory wires only legacy route at `factory.py:605`.
- Governance constitution routes (`backend/app/governance/routes/constitution_routes.py:18-19,57-139`).
- Alternate Telegram webhook (`backend/app/routes/telegram_webhook.py:18,54,83`).
- Kernel runtime integration helper (`backend/app/kernel/runtime_integration.py:45-46`).
- Capability routers except FHIR main router; capability health routers (`backend/app/capabilities/*/health.py:5`, ten packages).

Important: `backend/app/identity/api/*` IS wired via `identity/api/router.py:30-55`, `identity/__init__.py:34-40`, `factory.py:819-820`.

## 4. Duplicate/parallel implementation register

| Concern | Canonical candidate | Parallel implementations | Disposition |
|---|---|---|---|
| Identity/NIAM | `backend/app/identity/` | `national/domain/identity_resolution.py`, `national/services/identity_*.py`, `national/api/routes/identity.py`, `services/identity.py`, `services/governance/identity_governance.py`, `citizen_platform/identity.py`, `edge/identity.py`, `platform/identity.py`, `routes/identity.py`, `routes/national_identity.py`, `gateways/national_identity_gateway.py`, `integration/identity_bundle.py`, `integration/identity/`, `backend/services/identity_engine/`, `backend/services/identity_service/`, `shared/identity/`, `gula_rbac_manager.py`, `gula_registration_portal.py` | No second engine (D-001). |
| MPI/patient linkage | `backend/app/services/mpi/` | `services/identity_matching.py`, `national/workflows/merge_identity_workflow.py`, SDK MPI models | Safety helpers unbound (MGR-004). |
| LIMS/lab | `backend/app/lims/` | `lab_slice/` synthetic, legacy `routes/labs.py`, `routes/samples.py`, `routes/results.py`, `routes/test_results.py`, `services/lab/`, `platform/apps/laboratory/` | Reuse canonical; do not promote synthetic. |
| Consent | `routes/consent.py`, NIAM consents | capability/national/legal/security/identity-model surfaces | ADE binding open. |
| Audit | `shared/audit/`, `services/audit_service.py:1-6`, `identity/services/canonical_audit.py:90-182` | many parallel audit paths | Two surfaces and unkeyed chain open. |
| Event bus | `shared/events/bus.py`, `backend/app/core/events.py:3,16` | kernel bus/store/outbox, platform core, integration inbox, outbox model | Choose one authority. |
| FHIR | `routes/ehr_fhir.py`, `capabilities/fhir_interoperability/routes.py:23` | national FHIR, national stub route (now labeled), integration exchange/gateway/transformation, contracts, frontend pages | Structural validation only. |

## 5. Safe-to-extend canonical components

Extend only without touching blocked schema/ownership/authority decisions:

- Canonical composition root (`main.py:28-31`, `factory.py:519-828`).
- NIAM narrow slice (`identity/api/router.py:30-55`, wired at `factory.py:819-820`).
- MPI service/resolver (`backend/app/services/mpi/`, wired at `factory.py:616-620`).
- Shared event bus and backend re-export (`shared/events/bus.py`, `backend/app/core/events.py:16`).
- Shared audit foundation/backend audit service (single-authority decision still open).
- LIMS service/routes excluding pharmacy and critical-release policy changes.
- Wired national operational routers (`factory.py:689-716,781-787`).
- Public-health API with corrected status wording.
- Governance analytics (not constitution routes).
- `frontend-v3` route/page structure.

Do not extend without owner decision: any new identity/MPI/LIMS/consent/audit/FHIR engine; dormant router mount; pharmacy schema/model; `national_facilities` ownership; clinical state-machine semantics; consent/ADE binding; break-glass; governorate scope; sensitive clinical bridges.

## 6. Status contradictions and resolution

| Topic | Contradiction | Resolution |
|---|---|---|
| Public health | Present/Active/Live vs SCHEMA ONLY | `PARTIALLY_VERIFIED`; no production certification |
| Domain modules | Master atlas Complete/Present vs healthcare/data atlases SCHEMA ONLY | Wired routers `PARTIALLY_VERIFIED`; explicit missing modules `NOT_IMPLEMENTED` |
| FHIR | 501 report vs current Procedure routes | `PARTIALLY_VERIFIED`; 501 report stale |
| Capabilities | Business-neutral building blocks vs only one mounted router | Most `IMPLEMENTED_BUT_UNWIRED` |
| Certification | Coverage reports PASS vs gates NOT PASSED | Static evidence only; global `NOT_APPROVED` stands |
| Canonical migration | Bridged/Extracted/Consolidated claims vs duplicate trees | Declared boundary, not proof of cleanup |

## 7. Architecture conclusion

The strongest canonical components are NIAM narrow slice, MPI, LIMS, shared audit/event foundation, wired national operational routers, public-health API, governance analytics, and `frontend-v3`. The largest structural risk is not absence of code but parallel implementations plus unwired routers. The largest release blockers are pharmacy NR-003, `national_facilities` ownership, clinical state-machine semantics, absent authority connectors, unkeyed/retention-incomplete audit, consent/ADE gaps, and failed gates/HOLD. No production release claim is supported.
