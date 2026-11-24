# GULA National Module Registry V2

**Document class:** Authoritative V2 module/registry inventory (planning artifact).
**Status:** PROPOSED / PENDING OWNER APPROVAL. Registration in this document is a **candidate registry entry**, not owner acceptance, not a release authorization, and not a change to any protected governance record.
**Standing posture:** **HOLD TRUE** · `production_ready_items = 0` · **Stable v1.0.0 NOT DECLARED** · **PRODUCTION READY NOT AUTHORIZED**.
**Authority sources:** `GOVERNANCE/FINAL_DECISION.md`, `GOVERNANCE/GECS/MASTER_CONTROL.md`, `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json`, `GULA_OWNER_DECISION_REGISTER.md`.
**Repository scope:** `gula-integration` only. Sibling `gula-platform` is out of scope. No source, test, config, migration, protected record, commit, push, PR, merge, or deployment action is authorized here.
**Baseline:** branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`.

---

## 1. Registry purpose and status semantics

This registry is the single V2 inventory of modules mapped to target layers A–G and programs PRG-00…PRG-10. It answers four questions only: (1) does candidate source exist at a citable path; (2) is there test or review evidence; (3) which target layer/program/owner does it map to; (4) what prevents promotion. It does **not** declare operational readiness.

**Exclusive status vocabulary (evidence must be cited):**

| Status | Meaning in this registry | Promotion constraint |
|---|---|---|
| IMPLEMENTED | Candidate source exists at cited path | Lowest rung; no operational claim |
| TESTED | Cited test definitions or test reports exist | Does not imply PostgreSQL or E2E execution |
| INDEPENDENTLY REVIEWED | A named independent review report exists | Engineering scope only unless owner-recorded |
| ACCEPTED | Owner-recorded decision exists (`GULA_OWNER_DECISION_REGISTER.md`) | Only OD-001 accepted engineering scope; OD-002…OD-025 BLOCKED |
| PRODUCTION READY | Reserved, unreleased | `status_registry.json` = 0; requires G1–G12 + NV2-D15 |
| PARTIALLY IMPLEMENTED | Source/design present but material gaps cited | Cannot be promoted to IMPLEMENTED without gap closure |
| DOCUMENTED ONLY | Documentation/design/catalogue evidence only | No source claim |
| PLANNED | Target intent without cited implementation | NV2-D10 required |
| BLOCKED | Explicit owner/report blocker | Cannot progress without named decision |

**Distinction labels (NOT statuses; always shown in a separate column):** SOURCE · WORKING PROTOTYPE · DOCUMENTED DESIGN · TEST-ONLY · PRODUCTION-VERIFIED. No module in this registry carries PRODUCTION-VERIFIED; no production verification was executed.

**Rules that override every row:** `DECISION-READY` is not `ACCEPTED`. API existence is not clinical service completion. Historical `PRODUCTION_READY`, PLATINUM, and certification claims (`SECURITY_CERTIFICATION.md`, `ENTERPRISE_PRODUCTION_CERTIFICATION_REPORT.md`, `MASTER_RELEASE_CERTIFICATION.md`, `DEVOPS_CERTIFICATION.md`) are **conflicts requiring NV2-D09**, not current status. `P-02 / AUD-F02` is IMPLEMENTED · TESTED · INDEPENDENTLY REVIEWED with two accepted LOW residuals — not ACCEPTED, not PRODUCTION READY (`P-02_FINAL_CLOSURE_2026_11_24.md`). `P-03 / AUD-F03` is PREPARED ONLY · NOT IMPLEMENTED, D1–D5 absent, T9 deferred (`P-03_READINESS_2026_11_24.md`, `P-03_CONCURRENCY_DESIGN.md`) — this is never `PRG-03`, the Diagnostics and Laboratory Systems program.

**Owner column:** all owners below are **proposed target owners (PRG IDs), NOT APPOINTED — NV2-D03**. `GULA_OWNER_DECISION_REGISTER.md` §9 records no release authority, HOLD TRUE.

---

## 2. Module inventory by target layer

### 2.1 Layer A — National Core (PRG-00)

| Module ID | Module | Layer / program | Proposed owner | Evidence path(s) | Status | Distinction | Promotion blocker / note |
|---|---|---|---|---|---|---|---|
| REG-A01 | NIAM identity platform | A / PRG-00 | PRG-00 | `backend/app/identity/`, `backend/app/security/auth.py`, `backend/app/security/mfa_service.py`, `INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md` | IMPLEMENTED · TESTED · INDEPENDENTLY REVIEWED | SOURCE | Engineering scope only; B-tier residuals; no owner acceptance |
| REG-A02 | MPI / NHID / patient identity | A / PRG-00 | PRG-00 | `backend/app/services/mpi/`, `GULA_MPI_FINAL_INDEPENDENT_AUDIT.md`, `GULA_MPI_INDEPENDENT_AUDIT_FINDINGS.md` | IMPLEMENTED · TESTED · INDEPENDENTLY REVIEWED | SOURCE | Protected MD5s `1a02c015…` / `ea3969d0…` unchanged; not ACCEPTED |
| REG-A03 | Organization / facility registry | A / PRG-00 | PRG-00 | `backend/app/identity/`, `backend/app/services/hospital_service.py` | PARTIALLY IMPLEMENTED | SOURCE | Ownership split unresolved (NV2-D03) |
| REG-A04 | Provider / professional registry | A / PRG-00 | PRG-00 | `backend/app/capabilities/provider_management/`, `backend/app/identity/` | PARTIALLY IMPLEMENTED | SOURCE | Capability is an empty CRUD stub |
| REG-A05 | Authorization RBAC/ABAC + decision engine | A / PRG-00 | PRG-00 | `backend/app/security/rbac.py`, `backend/app/security/abac.py`, `backend/app/identity/services/authorization_decision.py`, `identity/adaptive_auth/b4_guard.py` | IMPLEMENTED · TESTED · INDEPENDENTLY REVIEWED | SOURCE | B1/B2/B3/B5 residuals; zero-trust gaps (R-04) |
| REG-A06 | Consent service | A / PRG-00 | PRG-00 | `backend/app/identity/services/consent_service_v2.py`, `backend/app/identity/models/consent.py`, `FIELD_SECURITY.md` | IMPLEMENTED · TESTED | SOURCE | Full field-level enforcement NOT independently confirmed |
| REG-A07 | Immutable audit chain | A / PRG-00 (with PRG-10) | PRG-00/PRG-10 | `backend/app/services/audit_service.py`, `scripts/audit_verifier.py`, `backend/app/identity/services/canonical_audit.py`, `P-03_READINESS_2026_11_24.md` | BLOCKED | SOURCE | HEAD unlocked-tail defect reproduced on PG16.14; WT fix uncommitted; P-03 / AUD-F03 separate |
| REG-A08 | Terminology / CodeSystem registry | A / PRG-00 | PRG-00 | `integration/standards/terminology.py` | PARTIALLY IMPLEMENTED | SOURCE | In-memory static registry, empty concepts; NV2-D11 |
| REG-A09 | Contract registry / versioning | A / PRG-00 | PRG-00/PRG-10 | `contracts/api/v1/catalog.json`, `contracts/events/catalog.json`, `contracts/export/openapi.json` (98 bytes), `contracts/routes.py` | PARTIALLY IMPLEMENTED | DOCUMENTED DESIGN | Export stubs 98/102/305 bytes; `contracts/routes.py:52` breaks 4 endpoints |
| REG-A10 | National router surface | A / PRG-00 | PRG-00 | `backend/app/national/api/routes/__init__.py` (16 sub-routers), `backend/app/factory.py` | BLOCKED | SOURCE | **Unregistered**: complete router has no factory import |

### 2.2 Layer B — Clinical Platform (PRG-01)

| Module ID | Module | Layer / program | Proposed owner | Evidence path(s) | Status | Distinction | Promotion blocker / note |
|---|---|---|---|---|---|---|---|
| REG-B01 | EHR / clinical records | B / PRG-01 | PRG-01 | `backend/app/routes/ehr.py`, `backend/app/ehr/models/`, `backend/app/services/ehr_service.py` | PARTIALLY IMPLEMENTED | SOURCE | Duplicated EHR stacks flagged in backend evidence |
| REG-B02 | Encounter management capability | B / PRG-01 | PRG-01 | `backend/app/capabilities/encounter_management/`, `backend/app/national/api/routes/encounter.py` | PARTIALLY IMPLEMENTED | SOURCE | Capability is empty CRUD stub; national route source present |
| REG-B03 | Clinical foundation capability | B / PRG-01 | PRG-01 | `backend/app/capabilities/clinical_foundation/` | PARTIALLY IMPLEMENTED | SOURCE | Empty CRUD stub |
| REG-B04 | FHIR R4 interoperability | B / PRG-01 | PRG-01 | `backend/app/capabilities/fhir_interoperability/`, `backend/app/routes/ehr_fhir.py`, `backend/app/national/fhir/**`, `health_core/fhir/{serializers,deserializers}.py` | IMPLEMENTED · TESTED | SOURCE | Registered in factory; most resources read-only; stale validation report |
| REG-B05 | Care continuum (MCH/immunization/chronic/home) | B / PRG-01 | PRG-01 | `backend/app/care_continuum/models/{maternal,immunization,chronic_disease,care_journey}.py`, `backend/app/routes/care_continuum.py` | IMPLEMENTED · TESTED | SOURCE | Strong source+test per domain evidence |
| REG-B06 | Clinical safety / alert reliability | B / PRG-01 | PRG-01 | `CLINICAL_ALERT_RELIABILITY_REPORT.md`, `GULA_COMPONENT_INVENTORY.md` §4 | DOCUMENTED ONLY | DOCUMENTED DESIGN | No complete E2E patient journey; OD-008 BLOCKED |

### 2.3 Layer C — Domain Modules (PRG-02, PRG-03, PRG-04, PRG-06)

| Module ID | Module | Layer / program | Proposed owner | Evidence path(s) | Status | Distinction | Promotion blocker / note |
|---|---|---|---|---|---|---|---|
| REG-C01 | LIMS / diagnostics | C / **PRG-03** | PRG-03 | `backend/app/lims/`, `backend/app/services/{lab_service,sample_service,test_result_service,quality_control_service}.py`, `backend/tests/blood_bank/` | IMPLEMENTED · TESTED | SOURCE | Strong source+test; result-modification safety needs C07/C11 proof |
| REG-C02 | RIS / PACS / DICOM | C / **PRG-03** | PRG-03 | `backend/app/radiology/pacs.py`, `integration/gateway/dicom_gateway.py`, `integration/standards/dicom.py` | PARTIALLY IMPLEMENTED | SOURCE | Real QIDO/WADO/STOW via httpx; no `pydicom`/`pynetdicom`; NV2-D11 |
| REG-C03 | Pharmacy + inventory | C / PRG-04 | PRG-04 | `backend/app/pharmacy/`, `backend/app/pharmacy/inventory.py` | IMPLEMENTED · TESTED | SOURCE | Strong source+test per domain evidence |
| REG-C04 | Blood bank | C / PRG-03 ↔ PRG-02 | **UNRESOLVED** | `backend/app/blood_bank/`, `backend/tests/blood_bank/` | IMPLEMENTED · TESTED | SOURCE | Owner decision required (NV2-D03) |
| REG-C05 | Hospital / HIS / bed / assets | C / PRG-02 | PRG-02 | `backend/app/services/hospital_service.py`, `backend/app/routes/hospital.py`, `backend/app/hospital/models/__init__.py` | IMPLEMENTED · TESTED | SOURCE | Strong source+test |
| REG-C06 | EMS / prehospital | C / PRG-02 | PRG-02 | `backend/app/ems/` | IMPLEMENTED · TESTED | SOURCE | Strong source+test |
| REG-C07 | Nursing | C / PRG-02 | PRG-02 | `backend/app/nursing/` | IMPLEMENTED · TESTED | SOURCE | Strong source+test |
| REG-C08 | Critical care / ICU | C / PRG-02 | PRG-02 | `backend/app/critical_care/` | IMPLEMENTED · TESTED | SOURCE | Strong source+test |
| REG-C09 | Specialty modules (oncology, cardiology, nephrology, dental, rehab, mental health) | C / PRG-06 | PRG-06 | `GULA_COMPONENT_INVENTORY.md` §4 (Dental #10, Rehabilitation #13, Mental health #14 NOT IMPLEMENTED) | DOCUMENTED ONLY | DOCUMENTED DESIGN | Analytics/enum/documentation level only; R-12 |
| REG-C10 | Pathology / microbiology / molecular | C / PRG-03 | PRG-03 | `backend/app/lims/` assay categories/catalogs (domain evidence) | PARTIALLY IMPLEMENTED | SOURCE | LIMS categories, not dedicated clinical modules |

### 2.4 Layer D — Public Health (PRG-05)

| Module ID | Module | Layer / program | Proposed owner | Evidence path(s) | Status | Distinction | Promotion blocker / note |
|---|---|---|---|---|---|---|---|
| REG-D01 | Public health core | D / PRG-05 | PRG-05 | `backend/app/public_health/` | IMPLEMENTED · TESTED | SOURCE | Strong source+test per domain evidence |
| REG-D02 | Surveillance | D / PRG-05 | PRG-05 | `backend/app/national/intelligence/public_health/surveillance.py` | IMPLEMENTED | SOURCE | National reporting legal scope NV2-D08 |
| REG-D03 | Epidemiology | D / PRG-05 | PRG-05 | `backend/app/services/epidemiology.py` | IMPLEMENTED | SOURCE | — |
| REG-D04 | Compliance / DHIS2 export | D / PRG-05 | PRG-05 | `backend/app/routes/compliance.py` (~line 551+) | PARTIALLY IMPLEMENTED | SOURCE | Reporting/legal scope unresolved |

### 2.5 Layer E — Health Operations (PRG-07)

| Module ID | Module | Layer / program | Proposed owner | Evidence path(s) | Status | Distinction | Promotion blocker / note |
|---|---|---|---|---|---|---|---|
| REG-E01 | Billing | E / PRG-07 | PRG-07 | `backend/app/billing/` | IMPLEMENTED (source) | SOURCE | Duplicated stacks flagged; no forced FHIR on administrative data |
| REG-E02 | Financial / payments | E / PRG-07 | PRG-07 | `backend/app/financial/` | IMPLEMENTED (source) | SOURCE | Duplicated stacks flagged |
| REG-E03 | Insurance | E / PRG-07 | PRG-07 | `backend/app/insurance/`, `GULA_COMPONENT_INVENTORY.md` §4 (#16) | BLOCKED | SOURCE | Owner decision pending |
| REG-E04 | Workforce / HR | E / PRG-07 | PRG-07 | `backend/app/governance/models/workforce.py` | PARTIALLY IMPLEMENTED | SOURCE | HR partial per domain evidence |
| REG-E05 | Procurement | E / PRG-07 | PRG-07 | `GULA_COMPONENT_INVENTORY.md` (partial) | PARTIALLY IMPLEMENTED | DOCUMENTED DESIGN | Partial only |
| REG-E06 | Biomedical / device management | E / PRG-07 | PRG-07 | `backend/app/biomedical/`, `backend/app/devices/`, `gateways/lab_device_gateway.py` | IMPLEMENTED (source) | SOURCE | Device outbox `simulation_only=True` |
| REG-E07 | Clinical quality | E / PRG-07 | PRG-07 | `backend/app/clinical/quality/` | IMPLEMENTED (source) | SOURCE | — |

### 2.6 Layer F — National Intelligence (PRG-09)

| Module ID | Module | Layer / program | Proposed owner | Evidence path(s) | Status | Distinction | Promotion blocker / note |
|---|---|---|---|---|---|---|---|
| REG-F01 | NHDW / health data platform | F / PRG-09 | PRG-09 | `backend/app/nhdw/`, `backend/app/health_data/` | IMPLEMENTED (source) | SOURCE | Derived-only rule not yet contractually enforced |
| REG-F02 | National data | F / PRG-09 | PRG-09 | `backend/app/national_data/`, `backend/app/domain_platform/config/dormancy.json` | DOCUMENTED ONLY | SOURCE | Dormant; untracked; preserve |
| REG-F03 | Research platform | F / PRG-09 | PRG-09 | `backend/app/research_platform/` | IMPLEMENTED (source) | SOURCE | Consent/ABAC gating required |
| REG-F04 | AI / AI fabric | F / PRG-09 | PRG-09 | `backend/app/ai/`, `backend/app/ai_fabric/`, `GULA_MASTER_EXECUTION_STATUS.md:173` | PARTIALLY IMPLEMENTED | SOURCE | R-16; DeepSeek rotation UNVERIFIED |
| REG-F05 | National intelligence | F / PRG-09 | PRG-09 | `backend/app/national/intelligence/` | IMPLEMENTED (source) | SOURCE | — |

### 2.7 Layer G — Access Channels (PRG-08)

| Module ID | Module | Layer / program | Proposed owner | Evidence path(s) | Status | Distinction | Promotion blocker / note |
|---|---|---|---|---|---|---|---|
| REG-G01 | frontend-v3 web shell | G / PRG-08 | PRG-08 | `frontend-v3/src/routes/index.tsx`, `frontend-v3/data-source-inventory.json`, `docker-compose.yml:245-247` | PARTIALLY IMPLEMENTED | WORKING PROTOTYPE | 94 paths; 72 unbound, 17 demo-only, 3 safe_bridge, 2 contract-bound; 92 non-operational, 2 blocked-until-server-enforcement |
| REG-G02 | Contract-bound web pages | G / PRG-08 | PRG-08 | `frontend-v3/src/pages/patients/PatientsPage.tsx`, `frontend-v3/src/pages/orders/OrdersPage.tsx` | IMPLEMENTED · TESTED | SOURCE | Only two contract-bound surfaces |
| REG-G03 | Generated API clients | G / PRG-08 | PRG-08 | `frontend-v3/src/api/generated/client.ts` (919 lines), `types.ts` (12,412 lines), `contracts/sdk/{python,typescript,dart,kotlin,cli}` | IMPLEMENTED (source) | SOURCE | Real generated source; consumed by only 2 pages |
| REG-G04 | Android | G / PRG-08 | PRG-08 | `mobile/android/` (43 @Test), `.github/workflows/mobile-android.yml` | IMPLEMENTED · TESTED | SOURCE | CI-managed; cert pinning + encrypted prefs + offline sync |
| REG-G05 | iOS | G / PRG-08 | PRG-08 | `mobile/ios/` (61 tests) | PARTIALLY IMPLEMENTED | SOURCE | Expected Xcode workspace/project metadata absent; CI cannot bind (G8) |
| REG-G06 | Flutter desktop | G / PRG-08 | PRG-08 | `mobile/desktop/` (24 GoRoute paths, 9 tests), `.github/workflows/mobile-flutter-desktop.yml` | IMPLEMENTED · TESTED | SOURCE | CI-managed; Drift offline queue + conflict resolver |
| REG-G07 | hospital_desktop | G / PRG-08 | PRG-08 | `hospital_desktop/` (~2,055-line views, `offline.py` 534 lines, 3 unittest methods) | PARTIALLY IMPLEMENTED | SOURCE | Not wired into CI/Compose |
| REG-G08 | platform/apps persona apps | G / PRG-08 | PRG-08 | `platform/apps/{citizen,doctor,hospital,laboratory,ministry,nurse,pharmacy,radiology}` | IMPLEMENTED (source) | SOURCE | 15–25 routes each; no test scripts/dist/CI; root `index.html` links to missing `dist` |
| REG-G09 | Expo speech module | G / PRG-08 | PRG-08 | `mobile-expo/` (4 tests), `.github/workflows/mobile-expo.yml` | PARTIALLY IMPLEMENTED | SOURCE | Narrow module only |
| REG-G10 | Reference/bridge apps | G / PRG-08 | PRG-08 | `apps/gula-platform-ui-refresh` (14 tests), `apps/gula-web-suite` (15 tests), `client/` (0 tests) | IMPLEMENTED · TESTED | TEST-ONLY | Audit reference; `gula-web-suite` marks flows incomplete |
| REG-G11 | Directorate / governorate app | G / PRG-08 | PRG-08 | NOT FOUND | PLANNED | — | No dedicated user-facing app/route; G11 gap |

---

## 3. Cross-cutting infrastructure modules

| Module ID | Module | Layer / program | Evidence path(s) | Status | Distinction | Note |
|---|---|---|---|---|---|---|
| REG-X01 | Integration gateway / connectors | PRG-10 | `backend/app/integration/connectors/{lis,pacs}.py`, `integration/connectors/__init__.py` (~28 registrations) | IMPLEMENTED (source) | SOURCE | Real httpx connectors |
| REG-X02 | External gateways (AMQP/DICOM/lab device) | PRG-10 | `integration/gateway/{amqp_gateway,dicom_gateway}.py`, `gateways/lab_device_gateway.py` | PARTIALLY IMPLEMENTED | SOURCE | Default STUB; AMQP reports success on ImportError; HL7→FHIR `simulationOnly: True` |
| REG-X03 | Offline sync (four engines — §5) | PRG-08/PRG-10 | `GULA_OFFLINE_SYNC_REASSESSMENT.md`, `health_core/`, `core/sync_engine/`, `mobile/`, `hospital_desktop/offline.py` | PARTIALLY IMPLEMENTED | SOURCE / TEST-ONLY | No durable production queue; HEAD CRDT can overwrite results; fix uncommitted |
| REG-X04 | Event/outbox (three buses + outbox — §6) | PRG-10 | `shared/events/bus.py`, `backend/app/kernel/event_bus/`, `backend/app/services/outbox_service.py`, `backend/app/models/outbox.py` | PARTIALLY IMPLEMENTED | SOURCE | No authoritative event store; R-14 |
| REG-X05 | Observability | PRG-10 | `/metrics` + `/metrics/prom`, `helm/gula-platform/`, structured JSON logs | PARTIALLY IMPLEMENTED | SOURCE | ServiceMonitor mis-target; SLO metrics not emitted; no runtime OTel instrumentation |
| REG-X06 | Notifications | PRG-10 | `backend/app/services/`, `backend/app/models/` (notification stack) | IMPLEMENTED (source) | SOURCE | Duplication flagged in backend evidence |
| REG-X07 | Parallel experimental API trees | PRG-10 | `backend/core/api/`, `backend/gateway/`, `backend/services/*/main.py`, `services/*`, `api/demo-api/`, `server/index.ts`, `docs/evolution/PLATFORM_EVOLUTION_PLAN.md:305` | DOCUMENTED ONLY | SOURCE | Experimental stubs duplicating monolith routes; preserve, do not promote |

`GULA_COMPONENT_INVENTORY.md` §4 records 18 national services as engineering IMPLEMENTED/TESTED with **0 verified E2E journeys, 0 verified frontend consumption, and 0 owner approvals** — consistent with `production_ready_items = 0`.

---

## 4. Capability scaffold finding (8/10)

`backend/app/capabilities/` contains 10 CQRS capability scaffolds. Factory registration evidence (`backend/app/factory.py`, backend audit):

| Capability | Registered in factory? | Status | Evidence path |
|---|---|---|---|
| `fhir_interoperability` | Yes | IMPLEMENTED · TESTED | `backend/app/capabilities/fhir_interoperability/` |
| `search_service` | Yes | IMPLEMENTED · TESTED | `backend/app/capabilities/search_service/` |
| `clinical_foundation` | No | PARTIALLY IMPLEMENTED — empty CRUD stub | `backend/app/capabilities/clinical_foundation/` |
| `document_management` | No | PARTIALLY IMPLEMENTED — empty CRUD stub | `backend/app/capabilities/document_management/` |
| `encounter_management` | No | PARTIALLY IMPLEMENTED — empty CRUD stub | `backend/app/capabilities/encounter_management/` |
| `healthcare_consent` | No | PARTIALLY IMPLEMENTED — empty CRUD stub | `backend/app/capabilities/healthcare_consent/` |
| `provider_management` | No | PARTIALLY IMPLEMENTED — empty CRUD stub | `backend/app/capabilities/provider_management/` |
| `reporting_service` | No | PARTIALLY IMPLEMENTED — empty CRUD stub | `backend/app/capabilities/reporting_service/` |
| `storage_service` | No | PARTIALLY IMPLEMENTED — empty CRUD stub | `backend/app/capabilities/storage_service/` |
| `workflow_engine` | No | PARTIALLY IMPLEMENTED — empty CRUD stub | `backend/app/capabilities/workflow_engine/` |

The other 8 are advertised as metadata by `backend/app/kernel/capabilities_registry_populator.py` without factory registration. **Advertising a stub as a capability is a registry defect, not a completed capability.** The canonical workflow replacement `backend/app/workflows/` is untracked while the old surface is staged for `archive/legacy/workflow_runtime/` (20 R100 renames) — see §7.

---

## 5. Four offline engines

| Engine | Evidence path | Status / distinction | Divergence |
|---|---|---|---|
| OFF-1 health_core deterministic conflict engine | `health_core/` integration/offline/conflicts modules | TEST-ONLY — never published to a real broker; `health_core/contracts/version.py` = LOCAL_SYNTHETIC_ONLY | Strongest contract logic but synthetic |
| OFF-2 core/sync_engine in-memory LWW | `core/sync_engine/` | SOURCE — in-memory last-write-wins | Not durable across workers |
| OFF-3 Native client offline engines | `mobile/android/` (Room/WorkManager), `mobile/ios/` (CoreData), `mobile/desktop/` (Drift queue + resolver) | IMPLEMENTED · TESTED / SOURCE | Three distinct conflict policies; SDK sync modules unused by frontend-v3 |
| OFF-4 Hospital desktop offline file | `hospital_desktop/offline.py` (534 lines) | PARTIALLY IMPLEMENTED / SOURCE | No CI/Compose; encrypted session only |

Additional unused implementation: SDK naive `client_wins`/`remote_wins` resolvers under `contracts/sdk/`. At HEAD, `CRDT_MERGE` is first-seen-key-wins and **can overwrite a lab result**; a `CONFLICT_QUARANTINE` fix exists only uncommitted. No durable production offline queue; primary stores are process-local. C11 convergence is **NOT VERIFIED**; risk R-08; gate G9.

---

## 6. Three event buses plus one outbox (four disconnected stacks)

| Stack | Evidence path | Status / distinction | Defect |
|---|---|---|---|
| BUS-1 Kernel in-memory bus | `backend/app/kernel/event_bus/` | SOURCE | `publish` never populates its own outbox/inbox/DLQ |
| BUS-2 Shared bus | `shared/events/bus.py` | SOURCE | Swallows handler exceptions; no authoritative store |
| BUS-3 health_core synthetic deterministic events | `health_core/` | TEST-ONLY | Never published to a real broker |
| OUT-1 Durable SQL outbox | `backend/app/services/outbox_service.py`, `backend/app/models/{outbox,integration_inbox}.py`, `worker.py` | PARTIALLY IMPLEMENTED / SOURCE | Poll 10s, batch 50, 5 attempts, 30-day purge, skip_locked; `OutboxWorker` marks done with zero successful handlers; dual worker in `core/startup.py:270-272` |

No async broker dependency (`aio_pika` missing; shared pyproject has sync pika). Inbound idempotency (`integration/inbox.py`) stages/validates but does not auto-apply. Correlation: `X-Request-ID` echoed, `X-API-Version` emitted, but no `X-Correlation-ID` header and `request.state.correlation_id` never set in middleware. C09/C10/C12 immature; R-14; gates G4/G10.

---

## 7. Unregistered national router and in-flight provenance

- `backend/app/national/api/routes/__init__.py` defines 16 sub-routers with **no `include_router` import in `backend/app/factory.py`** — a complete national API surface is unregistered (REG-A10, GAP-03).
- Static decorator scan: 2,388 route decorators including unregistered/stub surfaces; documented live counts conflict (1,442 / 1,804 / 1,815 / 1,817 paths). No live import measurement was performed; treat all counts as `NOT VERIFIED` for current live routes.
- Mixed Git provenance: 20 staged R100 renames into `archive/legacy/workflow_runtime/` (name-status MD5 `56c524d6ffe9872c3a3ac6eff8c8f203`), 162 unstaged tracked changes, 686 untracked entries before V2 documents. Canonical `backend/app/workflows/` and `backend/app/national_data/` are untracked.
- Migrations: 111 Python revisions, single head `20261119_0003`, 4 merge revisions, 0 dangling/duplicate IDs; documented counts conflict (48/110/111).
- `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json` worktree SHA-256 differs from committed HEAD blob — protected version uncommitted; preserve.

No save, merge, re-cut, or migration is permitted before NV2-D02.

---

## 8. Dormant and strategic assets — PRESERVE, DO NOT DELETE

| Asset | Evidence path | Dormancy evidence | Rule |
|---|---|---|---|
| national_data | `backend/app/national_data/` | `backend/app/domain_platform/config/dormancy.json` | PRESERVE; dormant strategic asset; no activation, no deletion |
| health_core | `health_core/` | untracked; `contracts/version.py` LOCAL_SYNTHETIC_ONLY | PRESERVE; TEST-ONLY reference for C11/C09 design |
| archive trees | `archive/legacy/`, `archive/experimental/`, `archive/scripts/`, `archive/` (182 files, no frontend source) | domain evidence | PRESERVE; archive-first; deletion requires separate owner-governed decision |
| nhop-platform | marked archived in `backend/app/domain_platform/config/dormancy.json` | dormant policy | PRESERVE DO NOT DELETE |
| edge_agent | marked archived in `dormancy.json` | dormant policy | PRESERVE DO NOT DELETE |
| ai | marked archived in `dormancy.json` | dormant policy | PRESERVE DO NOT DELETE |
| platform | `platform/apps/`, `dormancy.json` `active_development`, deferred | dormant policy | PRESERVE DO NOT DELETE; no test/CI wiring today |

Enforcement paths: `backend/app/domain_platform/policies/dormancy_policy.py`, `backend/app/domain_platform/dormancy.py`, `backend/app/domain_platform/certification.py`. **Explicit rule:** dormancy is not abandonment. Dormant modules are strategic assets retained for future national releases. This V2 registry adds no deletion authority and no activation authority.

---

## 9. Registry lifecycle states (proposed, pending owner)

| State | Entry criterion | Exit criterion | Current example |
|---|---|---|---|
| L0 IDENTIFIED | Path cited in evidence | Source confirmed | REG-G11 (no path → stays PLANNED) |
| L1 SOURCE CONFIRMED | Source file/dir exists at cited path | Test evidence cited | REG-E02 |
| L2 TEST EVIDENCE | Test definitions or reports cited | Independent review cited | REG-D01 |
| L3 INDEPENDENT REVIEW | Named review report cited | Owner-recorded decision | REG-A01, REG-A02 |
| L4 OWNER ACCEPTED | `GULA_OWNER_DECISION_REGISTER.md` decision recorded | G1–G12 passed + NV2-D15 | **None** (OD-002…OD-025 BLOCKED) |
| L5 PRODUCTION READY | G1–G12 + NV2-D15 + `status_registry.json` update | Controlled rollout authorization | **None** (`production_ready_items = 0`) |
| S1 DORMANT | `dormancy.json` / archive designation | Owner-governed reactivation | §8 assets |
| S2 BLOCKED | Explicit report/owner blocker | Named decision resolves blocker | REG-A07, REG-A10, REG-E03 |
| S3 SUPERSEDED / ARCHIVED | R100 rename or canonical replacement | Independent reversibility verification | `archive/legacy/workflow_runtime/` |

No module in this registry is above L3. A historical certification label does not move a module to L4 or L5.

---

## 10. Registration rules (mandatory for parallel teams)

1. **R1 — Path or nothing:** an entry requires at least one concrete repository-relative evidence path. Entries without one are PLANNED / NOT VERIFIED only (REG-G11).
2. **R2 — No silent upgrade:** status may move up only with a new citation; `DECISION-READY` never becomes ACCEPTED; API existence never becomes clinical completion.
3. **R3 — Distinction always shown:** SOURCE / WORKING PROTOTYPE / DOCUMENTED DESIGN / TEST-ONLY / PRODUCTION-VERIFIED must be recorded beside every status.
4. **R4 — Map to layer and program:** every entry carries target layer A–G and PRG-00…PRG-10, with owner marked `NOT APPOINTED — NV2-D03` until recorded.
5. **R5 — Conflict flags are mandatory:** historical certification vs HOLD → NV2-D09; route-count divergence → NOT VERIFIED; audit concurrency → P-03 / AUD-F03 separate package, never PRG-03.
6. **R6 — Preserve dormancy:** no entry authorizes deletion, activation, or migration of §8 assets.
7. **R7 — Registration ≠ runtime:** unregistered surfaces (REG-A10), stubs (§4), and simulated links (§5/§6) must be flagged even when source is real.
8. **R8 — No production claim:** PRODUCTION READY remains unreleased; G1–G12 inactive; any rollout requires NV2-D15.
9. **R9 — Shared semantics are serialized:** changes to C01–C15, protected governance records, or National Core semantics require contract review + version bump + G1 revalidation; parallel teams work only against approved contracts and versioned schemas.
10. **R10 — Re-register at checkpoints:** this registry must be re-verified after NV2-D02 provenance resolution and after each wave — W0 (governance/evidence baseline), W1 (National Core contracts), W2 (independent enabling work), W3 (domain vertical slices), W4 (national integration, DR, offline and rollout evidence); no edits to protected records are permitted to accomplish that.

---

## 11. Decision dependencies and gates

| Decision / gate | Registry effect |
|---|---|
| NV2-D01 / NV2-D03 | Approves layer/program boundaries and appoints owners; clears `NOT APPOINTED` and REG-C04 owner gap |
| NV2-D02 | Resolves staged R100 / untracked provenance before any registry baseline re-cut |
| NV2-D04 / G1–G12 | Activates controlled gates; no status movement before approval |
| NV2-D05 | Decides extraction vs modular monolith; affects REG-X07 and capability promotion |
| NV2-D09 | Resolves historical certification vs HOLD conflict for every row |
| NV2-D10 | Approves WS-CORE-01, WS-SEC-01, WS-AUD-01 (design only — no P-03 / P-03-CONCURRENCY execution), WS-OBS-01, WS-DB-01, WS-E2E-01, WS-API-01, WS-GOV-01 |
| NV2-D11 | DICOM/PACS and terminology strategy (REG-C02, REG-A08) |
| NV2-D12 / NV2-D13 | Separate audit-chain packages (REG-A07), outside V2 execution start |
| NV2-D14 | Test environments and synthetic data policy for L2/L3 evidence |
| NV2-D15 | Only route to L5, after G1–G12 (G1 Architecture/Contract, G2 Security/Privacy, G3 Clinical Safety, G4 API/Integration, G5 Database/Migration, G6 Backup/DR, G7 Performance, G8 Mobile/Desktop, G9 Offline/Sync, G10 Monitoring/Incident, G11 National Operations, G12 Independent Review/Final Acceptance) |

---

## 12. Evidence basis

Files and reports inspected for this registry (all under `gula-integration`, read-only):

- Authority/status: `GOVERNANCE/FINAL_DECISION.md`, `GOVERNANCE/GECS/MASTER_CONTROL.md`, `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json`, `GULA_OWNER_DECISION_REGISTER.md`, `GULA_MASTER_EXECUTION_STATUS.md`, `GULA_COMPONENT_INVENTORY.md` §4, `P-02_FINAL_CLOSURE_2026_11_24.md`, `P-02_INDEPENDENT_REVIEW_2026_11_24.md`, `P-03_READINESS_2026_11_24.md`, `P-03_CONCURRENCY_DESIGN.md`.
- Identity/authorization/audit: `backend/app/identity/`, `backend/app/security/`, `backend/app/services/mpi/`, `backend/app/services/audit_service.py`, `scripts/audit_verifier.py`, `INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md`, `INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`, `FIELD_SECURITY.md`, `GULA_MPI_FINAL_INDEPENDENT_AUDIT.md`, `GULA_MPI_INDEPENDENT_AUDIT_FINDINGS.md`.
- Capabilities/domains: `backend/app/capabilities/`, `backend/app/kernel/capabilities_registry_populator.py`, `backend/app/domain_platform/manifest.py`, `backend/app/domain_platform/config/dormancy.json`, `backend/app/domain_platform/policies/dormancy_policy.py`, `backend/tests/test_domain_platform.py`.
- Domain sources: `backend/app/{lims,radiology,pharmacy,blood_bank,hospital,ems,nursing,critical_care,public_health,care_continuum,billing,financial,insurance,biomedical,devices,nhdw,health_data,national_data,ai,research_platform,national}/`, `backend/tests/blood_bank/`.
- Integration/offline/events: `backend/app/integration/`, `integration/`, `gateways/lab_device_gateway.py`, `shared/events/bus.py`, `backend/app/kernel/event_bus/`, `backend/app/services/outbox_service.py`, `backend/app/models/{outbox,integration_inbox}.py`, `core/sync_engine/`, `health_core/`, `GULA_OFFLINE_SYNC_REASSESSMENT.md`.
- Channels: `frontend-v3/src/routes/index.tsx`, `frontend-v3/data-source-inventory.json`, `frontend-v3/src/api/generated/{client,types}.ts`, `mobile/android/`, `mobile/ios/`, `mobile/desktop/`, `mobile-expo/`, `hospital_desktop/`, `platform/apps/`, `apps/gula-platform-ui-refresh/`, `apps/gula-web-suite/`, `client/`, `docker-compose.yml`, `docker-compose.full.yml`.
- Backend/factory/migrations: `backend/app/main.py`, `backend/app/factory.py`, `backend/app/national/api/routes/__init__.py`, `backend/migrations/versions/`, `docs/evolution/PLATFORM_EVOLUTION_PLAN.md:305`, `backend/tests/conftest.py`.

All `/tmp/opencode/gula_v2_evidence_*.md` files and `/tmp/opencode/gula_v2_seed.md` were read in full. No status in this registry is derived from an unexecuted historical claim; where evidence is absent, the value is `NOT VERIFIED`.
