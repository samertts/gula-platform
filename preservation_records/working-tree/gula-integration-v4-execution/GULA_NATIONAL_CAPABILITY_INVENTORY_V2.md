# GULA National Capability Inventory V2

**Document:** `GULA_NATIONAL_CAPABILITY_INVENTORY_V2.md` (new root-level document, planning gate only)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · branch `integration/gula-unification-v1` · HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**Program set:** PRG-00 … PRG-10 (proposed, pending owner approval)
**Status:** PROPOSED / PENDING OWNER APPROVAL — no execution authority
**Date:** 2026-11-24

---

## 1. Posture and rules of interpretation

### 1.1 Standing posture (non-negotiable)

**Standing posture: HOLD TRUE · production_ready_items = 0 · Stable v1.0.0 NOT DECLARED · PRODUCTION READY NOT AUTHORIZED.** No item in this inventory is accepted or released by this planning gate.

| Item | Current value | Authority |
|---|---|---|
| Release hold | **HOLD TRUE** — do not release | `GOVERNANCE/FINAL_DECISION.md:13,36,47,361` |
| Production-ready items | `production_ready_items = 0` | `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json`, `GULA_MASTER_EXECUTION_STATUS.md:7,142` |
| Stable v1.0.0 | **NOT DECLARED** | `GULA_MASTER_EXECUTION_STATUS.md:7` |
| PRODUCTION READY | **NOT AUTHORIZED** anywhere in this inventory | `GOVERNANCE/GECS/MASTER_CONTROL.md` §3/§7/§8 |
| This document | Evidence inventory only; no status upgrade, no release authority | `GOVERNANCE/FINAL_DECISION.md`, `GULA_OWNER_DECISION_REGISTER.md:9-11` |

### 1.2 Hard rules for reading every row

1. **Status vocabulary is exclusive** (seed §4): `IMPLEMENTED`, `TESTED`, `INDEPENDENTLY REVIEWED`, `ACCEPTED`, `PRODUCTION READY`, `PARTIALLY IMPLEMENTED`, `DOCUMENTED ONLY`, `PLANNED`, `BLOCKED`. Any other term found in a cited source is quoted as source language and mapped explicitly to this vocabulary; it is never used as a status here.
2. **Distinction labels are not statuses**: `SOURCE`, `WORKING PROTOTYPE`, `DOCUMENTED DESIGN`, `TEST-ONLY`, `PRODUCTION-VERIFIED`, `NOT VERIFIED`. `NOT VERIFIED` is used where the required evidence is absent, not as a claim of absence of code.
3. **`DECISION-READY` is not `ACCEPTED`.** `DECISION-READY` is a review verdict. P-02 / AUD-F02 is `IMPLEMENTED · TESTED · INDEPENDENTLY REVIEWED` in this inventory — **not** `ACCEPTED`, **not** `PRODUCTION READY` — with two accepted LOW residuals (`P-02_FINAL_CLOSURE_2026_11_24.md:11-12,27-42`). The owner-recorded OD-001 acceptance applies only to the narrowly defined SEC-015/F-01 engineering scope (`GULA_MASTER_EXECUTION_STATUS.md:15`) and is recorded in §13 as a conflict, not as a package-wide upgrade.
4. **P-03 / AUD-F03 is `PREPARED ONLY · NOT IMPLEMENTED`** in source records; in this vocabulary it is `PLANNED` (design prepared, D1–D5 absent, T9 deferred to P-03-CONCURRENCY). It is a separate audit package and must never be read as PRG-03 (Diagnostics and Laboratory Systems). Sources: `P-03_READINESS_2026_11_24.md:3-6`, `P-03_CONCURRENCY_DESIGN.md:1-10`, `P-03_SCOPE_AND_DEPENDENCY_REVIEW.md:7-10`, `GULA_OWNER_DECISION_REGISTER.md` §9.
5. **Historical production certificates are superseded, not current authority:** `MASTER_RELEASE_CERTIFICATION.md`, `RC_READINESS_REPORT.md`, `ENTERPRISE_PRODUCTION_CERTIFICATION_REPORT.md`, `RELEASE_READINESS_REPORT.md`, `SECURITY_CERTIFICATION.md`, `PRODUCTION_READINESS.md`, `DEVOPS_CERTIFICATION.md`, `CERTIFICATION-v1.0.md`. Current November records override: `GOVERNANCE/FINAL_DECISION.md`, `GULA_RELEASE_ACCEPTANCE_REPORT.md`, `FINAL_00_MASTER_VERDICT.md`, `FINAL_ASSURANCE_DECISION.md`, `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json`.
6. **API existence is not clinical service completion.** Route decorators, OpenAPI operations and table counts are engineering evidence only; they do not prove an E2E journey, a clinical safety control, an owner decision or a gate pass.
7. **No invented percentages, completion scores or pass results.** Counts below are static counts from read-only inspection or counts quoted from named reports. Where a test was not re-executed, the row says so (`NOT VERIFIED`).
8. **No source/test/config/migration/protected-file change** was made in producing this inventory. Sibling `gula-platform` is read-only and untouched. No production DB, service, PHI, secret or provider call was used. No SQLite result is substituted for PostgreSQL evidence.

### 1.3 Gate and contract framing

Capability areas are mapped to target programs PRG-00…PRG-10, national contracts C01–C15 and release gates G1–G12 exactly as defined in the canonical seed. Every gap in this inventory eventually requires G1 (architecture/contract), G2 (security/privacy), G3 (clinical safety), G4 (API compatibility), G5 (migration), G6 (backup/DR), G7 (performance), G8 (mobile/desktop), G9 (offline), G10 (monitoring/incident), G11 (national operations) and G12 (independent review/final acceptance) evidence. **No gate is recorded as passed in this document.**

---

## 2. Master summary — capability areas

`Distinction` = source/prototype/design/test-only/production label. `Evidence path(s)` = concrete repository-relative citations. `Not proven` = what prevents a higher status. All statuses are single-value from §1.2 rule 1.

| # | Capability area | PRG | Status | Distinction | Evidence path(s) | What is NOT proven |
|---:|---|---|---|---|---|---|
| 1 | National Core — identity (NIAM), session, adaptive auth | PRG-00 | IMPLEMENTED | SOURCE | `backend/app/identity/`, `backend/app/security/auth.py`, `shared/auth/jwt.py`, `backend/app/identity/adaptive_auth/b4_guard.py` | OIDC/JWKS (JWKS route 503); cross-worker revocation; owner acceptance |
| 2 | National Core — MPI / patient identity | PRG-00 | INDEPENDENTLY REVIEWED | SOURCE | `backend/app/services/mpi/`, `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md`, `.../MPI_INDEPENDENT_AUDIT_FINDINGS.md` | AUD-02 open HIGH (DB `UNIQUE` missing), AUD-07/AUD-16 BLOCKED; no `ACCEPTED` |
| 3 | RBAC / ABAC / authorization decisions | PRG-00 | INDEPENDENTLY REVIEWED | SOURCE | `backend/app/security/rbac.py`, `security/abac.py`, `identity/services/authorization_decision.py`, `INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md` | B1/B2/B3/B5 residuals; field-level enforcement incomplete; IDOR suite not executed |
| 4 | Consent and break-glass | PRG-00 | PARTIALLY IMPLEMENTED | SOURCE / DOCUMENTED DESIGN | `backend/app/identity/services/consent_service_v2.py`, `security/consent_dep.py`, `security/break_glass_guard.py`, `FIELD_SECURITY.md` | Full field-level runtime enforcement not independently confirmed |
| 5 | Audit chain / immutable evidence | PRG-00, PRG-10 | PARTIALLY IMPLEMENTED | SOURCE (HEAD defect; WT-only fix) | `backend/app/services/audit_service.py`, `scripts/audit_verifier.py`, `P-03_READINESS_2026_11_24.md:20-31` | HEAD concurrent-fork defect; fix uncommitted; T9 deferred; no accepted independent review of fix |
| 6 | Organization / provider registry | PRG-00 | IMPLEMENTED | SOURCE | `backend/app/capabilities/provider_management/`, `backend/app/domain_platform/manifest.py`, `backend/app/identity/organizations/` | Only partial in factory; ownership decisions ADR-A/B (OD-003/OD-004) BLOCKED |
| 7 | Clinical EHR / encounters / orders | PRG-01 | IMPLEMENTED | SOURCE | `backend/app/routes/ehr.py`, `backend/app/ehr/`, `backend/app/capabilities/encounter_management/`, `backend/app/national/api/routes/encounter.py` | No E2E journey; `encounter_management` not factory-registered |
| 8 | FHIR R4 / interoperability | PRG-01, PRG-10 | PARTIALLY IMPLEMENTED | SOURCE / TEST-ONLY | `backend/app/routes/ehr_fhir.py`, `backend/app/national/fhir/`, `backend/app/interoperability/fhir_http/router.py`, `health_core/fhir/` | Most resources read-only (`docs/release/KNOWN_LIMITATIONS.md` §2); stale validation report; 98-byte export stub |
| 9 | Diagnostics / LIMS | PRG-03 | TESTED | SOURCE | `backend/app/lims/`, `backend/app/services/{lab,sample,test_result,quality_control}_service.py`, `backend/tests/blood_bank/` (adjacent), `GULA_COMPONENT_INVENTORY.md` §4 #1 | Silent-result-modification control (R-06) not proven E2E; no national load evidence |
| 10 | RIS / PACS / DICOM | PRG-03 | PARTIALLY IMPLEMENTED | SOURCE / DOCUMENTED DESIGN | `backend/app/radiology/` incl. `pacs.py`, `backend/app/integration/connectors/pacs.py`, `backend/app/integration/gateway/dicom_gateway.py` | No pydicom/pynetdicom dependency; device-bridge DICOM absent (TD-008); DICOM strategy NV2-D11 undecided |
| 11 | Pharmacy / medication management | PRG-04 | TESTED | SOURCE | `backend/app/pharmacy/`, `backend/app/pharmacy/inventory.py`, `GULA_COMPONENT_INVENTORY.md` §4 #4 | Duplicate-prescription anti-abuse case not executed; dispensation journey unproven |
| 12 | Blood bank | PRG-03 / PRG-02 | IMPLEMENTED | SOURCE / TEST-ONLY | `backend/app/blood_bank/`, `backend/tests/blood_bank/`, `GULA_COMPONENT_INVENTORY.md` §4 #7 | Owner decision on PRG-03 vs PRG-02 ownership unresolved (seed §8); no E2E transfusion journey |
| 13 | Public health / surveillance | PRG-05 | IMPLEMENTED | SOURCE | `backend/app/public_health/`, `backend/app/national/intelligence/public_health/surveillance.py`, `backend/app/services/epidemiology.py`, `GULA_COMPONENT_INVENTORY.md` §4 #9 | Legal reporting scope (NV2-D08) undecided; DHIS2 export not live-proven |
| 14 | EMS / Nursing / ICU | PRG-02 | IMPLEMENTED | SOURCE | `backend/app/ems/`, `backend/app/nursing/`, `backend/app/critical_care/`, `GULA_COMPONENT_INVENTORY.md` §4 #2/#6 | ADR-B table ownership BLOCKED; no journey from dispatch to bed |
| 15 | Hospital / HIS / bed & asset management | PRG-02 | IMPLEMENTED | SOURCE | `backend/app/services/hospital_service.py`, `backend/app/routes/hospital.py`, `backend/app/hospital/models/__init__.py`, `hospital_desktop/` | Desktop client not in CI/Compose; no live bed-management E2E |
| 16 | Care continuum (MCH, immunization, chronic, home care, referral) | PRG-01 | TESTED | SOURCE | `backend/app/care_continuum/models/`, `backend/app/routes/care_continuum.py`, `GULA_COMPONENT_INVENTORY.md` §4 #3/#8/#11/#12/#15/#17 | ADR-C BLOCKED; prior zero-audit-write observation resolved as journey observability gap, journeys still BLOCKED |
| 17 | Specialty care — Oncology, Cardiology, Nephrology, Mental health, Dental, Rehabilitation, Pathology, Molecular, OR | PRG-06 | DOCUMENTED ONLY | DOCUMENTED DESIGN | `GULA_COMPONENT_INVENTORY.md` §4 #10/#13/#14, `backend/app/domain_platform/manifest.py`, `backend/app/lims/` assay catalogs | No dedicated clinical modules; 0 tables for Dental/Rehabilitation/Mental health; analytics/enum-level only |
| 18 | Operations — claims, financial, insurance, HR, procurement | PRG-07 | PARTIALLY IMPLEMENTED | SOURCE | `backend/app/billing/`, `backend/app/financial/`, `backend/app/insurance/`, `backend/app/governance/models/workforce.py`, `backend/app/pharmacy/inventory.py` | Insurance `BLOCKED`: 30 `ins_*` tables, 84 unserved endpoints, F-085 `InsBase` unregistered; HR/procurement partial |
| 19 | Analytics / AI / NHDW / national_data | PRG-09 | PARTIALLY IMPLEMENTED | SOURCE / DOCUMENTED DESIGN | `backend/app/health_data/`, `backend/app/nhdw/`, `backend/app/national_data/`, `backend/app/ai/`, `backend/app/ai_fabric/`, `backend/app/research_platform/` | `national_data` dormant; AI governance/clinical safety unresolved (R-16); DeepSeek rotation NOT VERIFIED |
| 20 | Channels — frontend-v3 web | PRG-08 | PARTIALLY IMPLEMENTED | SOURCE | `frontend-v3/src/routes/index.tsx`, `frontend-v3/data-source-inventory.json`, `frontend-v3/src/pages/patients/PatientsPage.tsx`, `.../orders/OrdersPage.tsx` | 94 routes but 92 non-operational; only 2 contract-bound pages; no clinical offline queue |
| 21 | Channels — Android / iOS / Flutter desktop / Expo / hospital_desktop / platform apps / apps | PRG-08 | PARTIALLY IMPLEMENTED | SOURCE / TEST-ONLY | `mobile/android/`, `mobile/ios/`, `mobile/desktop/`, `mobile-expo/`, `hospital_desktop/`, `platform/apps/`, `apps/` | iOS metadata absent; hospital_desktop/platform apps not CI-wired; root `index.html` links missing dist |
| 22 | Integration / standards / events / stub gateways | PRG-10 | PARTIALLY IMPLEMENTED | SOURCE / TEST-ONLY / DOCUMENTED DESIGN | `backend/app/integration/`, `backend/app/kernel/event_bus/`, `backend/app/services/outbox_service.py`, `contracts/export/{openapi,asyncapi,fhir}.json` | 4 disconnected event stacks, no authoritative store; external gateways default STUB; checked-in OpenAPI 0 paths; correlation header missing |
| 23 | Infrastructure HA / DR / performance | PRG-10 | BLOCKED | DOCUMENTED DESIGN / NOT VERIFIED | `config/postgres-ha/patroni.yml`, `helm/gula-platform/`, `scripts/{backup.sh,pitr-recover.sh,restore-test.sh,dr-*.sh}`, `DATABASE_RECOVERY_REPORT.md` | Config-only HA; no DR/PITR/RTO/RPO drill; performance `FAIL` / no measured national load |
| 24 | Test estate | PRG-10 | TESTED | TEST-ONLY | `backend/tests/`, `backend/tests/conftest.py`, `P-02_FINAL_CLOSURE_2026_11_24.md`, `CERTIFICATION-v1.0.md` | Static counts only; default SQLite; no executed E2E/anti-abuse/load results; full-suite re-run NOT VERIFIED |
| 25 | Governance / status authority | PRG-00 | BLOCKED | SOURCE | `GOVERNANCE/FINAL_DECISION.md`, `GULA_OWNER_DECISION_REGISTER.md`, `GOVERNANCE/GECS/MASTER_CONTROL.md`, `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json` | OD-002…OD-025 BLOCKED; HOLD not lifted; no release acceptance; mixed Git provenance (R-01) unresolved |

**Master conclusion:** no row is `ACCEPTED` or `PRODUCTION READY`; the maximum engineering status reached is `INDEPENDENTLY REVIEWED` (MPI, authorization B-series, P-02 engineering scope), and that status explicitly excludes release authority.

---

## 3. Detailed capability evidence

Each subsection lists **Verified evidence** (what was actually inspected) and **Not verified / blockers** (what is missing, with citations).

### 3.1 National Core — NIAM (PRG-00, C01/C02/C03/C05)

**Verified evidence:** `backend/app/identity/` contains identity models, repositories, services and API routes; `shared/auth/jwt.py:31-82` and `backend/app/security/auth.py:15-29` implement JWT primitives; `security/auth.py:54-100,121-131,192-209` adds signed `account_kind`/`perm_ver`/`jti` plus Redis JTI blacklist; `security/session.py:3-23` makes permission-version revocation DB-authoritative and fail-closed; refresh rotation is in `identity/services/authentication_service.py:60-130` and `identity/repositories/session_repository.py:22-24`; MFA TOTP/backup/WebAuthn in `security/mfa_service.py:13-39`; OAuth2 code/client-credentials/refresh with hashed tokens and PKCE S256 in `security/oauth2_provider.py:73-103,129-192,271-277`; hashed service-account API keys in `security/service_accounts.py:19-38`. Status: **IMPLEMENTED / SOURCE**.

**Not verified / blockers:** symmetric HS256 only (`backend/app/config.py:178`); OIDC/JWKS unavailable by design, JWKS route returns 503 (`security/oauth2_provider.py:231-263`, `routes/oauth2.py:246-250`); `backend/app/security/zero_trust.py:14-15` stores `_active_sessions` in memory "for demo", IP/UA changes are logged but revocation commented out (`:37-45`) — no cross-worker state, device posture or continuous authorization (R-06 to seed risk mapping: R-04/R-09). 91 previously unguarded endpoints and S-01/S-02/S-13 remediations exist in the working tree only (`GOVERNANCE/SECURITY_REVIEW_REPORT.md:28-38,108-134`), awaiting independent/human review. No owner acceptance (NV2-D06).

### 3.2 National Core — MPI / patient identity (PRG-00, C01)

**Verified evidence:** `backend/app/services/mpi/` (resolver, reliability, canonical service, API, models, schemas). `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md` reports a fresh independent re-inspection at HEAD `2827c1ff…`: MPI regression **127 passed / 0 failed**, full-suite log **3843 passed / 1 pre-existing order-dependent failure / 27 skipped**, real-PostgreSQL HTTP proof **28/28 checks × 2 profiles**; finding counts 0 CRITICAL, 3 HIGH (2 closed, 1 PARTIAL), 9 MEDIUM (8 closed, 1 BLOCKED), 2 LOW closed, 2 INFORMATIONAL (1 documented PASS, 1 BLOCKED), no FAIL. Earlier `MPI_INDEPENDENT_AUDIT_FINDINGS.md` verdict `REJECT`; protected MD5s recorded in seed §1 unchanged. Status: **INDEPENDENTLY REVIEWED / SOURCE** — not ACCEPTED.

**Not verified / blockers:** AUD-02 HIGH `PARTIAL` — DB `UNIQUE` not applied (MP-001 owner-gated); AUD-07 `BLOCKED` (payload-fingerprint / re-resolve, D-MPI-5 / ODR-002); AUD-16 `BLOCKED` (detection-only fork policy, D-MPI-3/4 / ODR-003). Wrong-patient linkage path described in `MPI_INDEPENDENT_AUDIT_FINDINGS.md` §2 top risk. Owner decisions D-020/D-021 pending; R-05 open.

### 3.3 RBAC / ABAC / authorization (PRG-00, C05)

**Verified evidence:** canonical RBAC re-export `shared.rbac` (`backend/app/security/rbac.py:1-6`); ABAC defaults DENY (`security/abac.py:14,52,115-126`); centralized decision engine denies on actor mismatch, inactive session, invalid purpose/scope/relationship, unverified professional, unknown permission, policy deny or audit failure (`identity/services/authorization_decision.py:199-314,559-603`); scoped roles and delegation (`authorization_service_v2.py:205-335`); B4 cross-account guard denies by default, master_admin/security_administrator only, fresh step-up, fail-closed on audit failure (`identity/adaptive_auth/b4_guard.py:14-26,55,96-111,162-252`); `security/platform_access.py:10-12,43-64` separates operational reads from master_admin writes; step-up dependency `identity/api/step_up.py:21-27`. Independent engineering-scope reports verify B1/B2/B3 and B5 re-verification with zero API-reachable bypasses (`INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md:18-23`, `INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md:23`, `EXECUTION_LEDGER.md:262`). Status: **INDEPENDENTLY REVIEWED / SOURCE**.

**Not verified / blockers:** residuals B1 seeded catalog gap, B2 category mismatch, B3 near-majority flag, B5 forged-row key attenuation and `citizen_ulid` owner-bypass provenance (`...B5_REVERIFY.md:215-222`, `...TIER_B.md:204-206`). No independent review awarded PRODUCTION READY; no runtime IDOR/cross-tenant probe (R-04).

### 3.4 Consent and privacy (PRG-00, C06)

**Verified evidence:** versioned consent unique on subject/grantee/purpose/domain/version, subject-only grant, purpose allowlist, 72-hour cap (`backend/app/identity/services/consent_service_v2.py:24-46,62-81`, `identity/models/consent.py:34-53`); grant/withdraw/check emit canonical audit (`:121-133,138-177`); server-verified break-glass is distinct from consent gating (`security/consent_dep.py:1-31`, `security/break_glass_guard.py:1-26`). Canonical Fernet plus HMAC-protected national-ID tokens (`shared/security/encryption.py:9-43`, `backend/app/security/encryption.py:1-38`); production startup exits on missing/weak secrets (`backend/app/config.py:135-165,169-198,238-266`). Status: **PARTIALLY IMPLEMENTED / SOURCE** (consent core) + **DOCUMENTED DESIGN** (field-level).

**Not verified / blockers:** `FIELD_SECURITY.md:7-24,28-38` describes field-level security; only partial runtime scaffolding exists (`models/authorization.py:158-168`, `services/authorization_service.py:834-867`, `routes/authorization.py:336`); full enforcement not independently confirmed. Consent vs emergency-access conflict (R-07) unresolved; DeepSeek key rotation NOT VERIFIED (`GULA_MASTER_EXECUTION_STATUS.md:173`).

### 3.5 Audit chain and immutable evidence (PRG-00/PRG-10, C07)

**Verified evidence:** canonical SHA-256 hash chain with HMAC anchors (`backend/app/services/audit_service.py:1-8,31-38`); legacy writers delegate (`shared/audit/service.py:1-8`); identity audit redacts secrets and verifies `previous_hash`/`entry_hash` (`identity/services/canonical_audit.py:73-80,175-178,244-255`); standalone verifier is read-only (`scripts/audit_verifier.py:3-14`, `scripts/gula_guardian.py:49-77`); PG append-only triggers reject UPDATE/DELETE (migrations `20250322_0002:73-104`, `20260505_0005:1-20`).

**HEAD defect (explicit):** `_get_last_chain_hash()` performs an unlocked tail read; concurrent PostgreSQL writers can fork the chain (`backend/app/services/audit_service.py` HEAD lines 106-112, 219-229; `P-03_CONCURRENCY_DESIGN.md:12-22`, `P-03_READINESS_2026_11_24.md:20-31`). PG16.14 reproduction: **1 failed / 1 passed**, `stored_hash 571f43b6…` vs expected `5bb1ab4d…` — defect evidence only. P-02 PG-backed evidence is separate: RED 6 failed/2 passed, GREEN 8 passed, related **224 passed / 9 skipped / 0 failed** (115.83s); verdict `DECISION-READY`, 0 CRITICAL/HIGH/MEDIUM, 2 LOW (`P-02_FINAL_CLOSURE_2026_11_24.md`, `P-02_IMPLEMENTATION_EVIDENCE_2026_11_24.md`, `P-02_AFTER_REV3.md`, `P-02_INDEPENDENT_REVIEW_2026_11_24.md`).

**WT-only fix (explicit):** advisory locking / READ COMMITTED / autocommit guards exist at `audit_service.py:48-114,284-325` but `git diff --stat` confirms `backend/app/services/audit_service.py` is modified, unstaged at HEAD; the fix is uncommitted and not accepted. Status: **PARTIALLY IMPLEMENTED / SOURCE (HEAD defect; WT-only fix)**. P-03 / AUD-F03 D1–D5 remain `PLANNED` (prepared only); T9 deferred to unapproved P-03-CONCURRENCY (R-03, R-09).

### 3.6 Clinical / EHR / FHIR (PRG-01, PRG-10; C04/C08)

**Verified evidence:** `backend/app/routes/ehr.py`, `backend/app/ehr/`, `backend/app/services/ehr_service.py`, `backend/app/capabilities/clinical_foundation/`, `backend/app/capabilities/encounter_management/`, `backend/app/national/domain/{clinic,visit,appointment,encounter}.py`, `backend/app/national/api/routes/encounter.py`. `backend/app/capabilities/` has 10 CQRS capability directories with unit/integration tests; only `fhir_interoperability` and `search_service` are registered in `backend/app/factory.py` — the other 8 (`clinical_foundation`, `document_management`, `encounter_management`, `healthcare_consent`, `provider_management`, `reporting_service`, `storage_service`, `workflow_engine`) are empty CRUD stubs advertised as metadata by `kernel/capabilities_registry_populator.py`. FHIR: real routes/mappers/serializers/tests in `routes/ehr_fhir.py`, `national/fhir/`, `interoperability/fhir_http/router.py`, `health_core/fhir/{serializers,deserializers}.py`; capability statement ~30 KB. Status: **IMPLEMENTED / SOURCE** (EHR) and **PARTIALLY IMPLEMENTED / SOURCE + TEST-ONLY** (FHIR).

**Not verified / blockers:** FHIR R4 is read-only for most resources (`docs/release/KNOWN_LIMITATIONS.md` §2); stale validation report claims `Procedure` 501 that no longer exists; 98-byte `contracts/export/openapi.json` stub; 8/10 capability stubs not registered; no E2E registration→order→sample→result→verification→billing→report journey (OD-008 BLOCKED, `ADVERSARIAL_TEST_REPORT.md`).

### 3.7 Diagnostics / LIMS (PRG-03 — not the P-03 audit package)

**Verified evidence:** `backend/app/lims/` plus `backend/app/services/lab_service.py`, `sample_service.py`, `test_result_service.py`, `quality_control_service.py`, routes and tests; `GULA_COMPONENT_INVENTORY.md` §4 #1 records **103 live ops**, `IMPLEMENTED + TESTED`, 35 `lims` tables; ASTM real integration in `backend/app/lims/integration/`; `backend/app/integration/connectors/lis.py` and `gateways/lab_device_gateway.py` (HMAC + replay protection). Static test inventory includes 110 FHIR-named definitions. Status: **TESTED / SOURCE**.

**Not verified / blockers:** silent result modification (R-06) and unauthorized result export are not proven absent by runtime probes; no executed national-scale load test for result ingestion; instrument interface go-live not evidenced; no verified E2E journey or frontend consumption recorded (`GULA_COMPONENT_INVENTORY.md` §4 preamble: 0 verified E2E journeys). Owner decision on blood-bank ownership (§3.12) and terminology strategy (NV2-D11) pending.

### 3.8 RIS / PACS / DICOM (PRG-03)

**Verified evidence:** `backend/app/radiology/` including `pacs.py` DICOMStorageService; `backend/app/integration/connectors/pacs.py` implements QIDO/WADO/STOW via httpx; `backend/app/integration/gateway/dicom_gateway.py`; `GULA_COMPONENT_INVENTORY.md` §4 #5 records 58 live ops, `IMPLEMENTED + TESTED`, 18 tables. Status: **PARTIALLY IMPLEMENTED / SOURCE + DOCUMENTED DESIGN**.

**Not verified / blockers:** no `pydicom`/`pynetdicom` dependency for the connector; `docs/release/KNOWN_LIMITATIONS.md` §2 (TD-008) states no DICOM for the device bridge (only ASTM/HL7) and §1/§2 conflict with connector source; DICOM/PACS and terminology strategy NV2-D11 is an owner decision; no live modality worklist or study-sharing evidence.

### 3.9 Pharmacy (PRG-04)

**Verified evidence:** `backend/app/pharmacy/` and `backend/app/pharmacy/inventory.py`; `GULA_COMPONENT_INVENTORY.md` §4 #4 records 63 live ops, `IMPLEMENTED + TESTED`, 27 tables; static test inventory includes 30 stress and 30 performance definitions (not execution results). Status: **TESTED / SOURCE**.

**Not verified / blockers:** WS-SEC-01 anti-abuse scenarios (duplicate prescription, unauthorized export) are proposed, not executed; no dispensation E2E; no evidence that inventory decrements are safe under concurrent dispense; `pharmacy` is listed among 11 canonical domains but release scope remains pending E2E and owner gate.

### 3.10 Blood bank (PRG-03 / PRG-02 — ownership undecided)

**Verified evidence:** `backend/app/blood_bank/`, `backend/tests/blood_bank/`, `backend/app/domain_platform/manifest.py` canonical domain `blood_bank`; `GULA_COMPONENT_INVENTORY.md` §4 #7 records 30 live ops, `IMPLEMENTED`, 17 tables. Status: **IMPLEMENTED / SOURCE + TEST-ONLY** (test files present; no re-executed result in this audit).

**Not verified / blockers:** seed §8 assigns blood bank to PRG-03/PRG-02 "as agreed in owner decision (flag unresolved if needed)" — unresolved; no crossmatch→issue→transfusion E2E; no donor-recall or traceability drill evidence.

### 3.11 Public health (PRG-05, C09)

**Verified evidence:** `backend/app/public_health/`, `backend/app/national/intelligence/public_health/surveillance.py`, `backend/app/services/epidemiology.py`; `GULA_COMPONENT_INVENTORY.md` §4 #9 records 110 live ops, `IMPLEMENTED`, 6 + 15 `nhdw` tables; DHIS2 export at `backend/app/routes/compliance.py:551+`. Status: **IMPLEMENTED / SOURCE**.

**Not verified / blockers:** no live DHIS2/national reporting integration proof; public-health legal/scope decision NV2-D08 open; source-of-truth rule requires surveillance to derive from authorized clinical events (seed §8) — derivation lineage not evidenced end-to-end.

### 3.12 EMS / Nursing / ICU (PRG-02)

**Verified evidence:** `backend/app/ems/`, `backend/app/nursing/`, `backend/app/critical_care/`; `GULA_COMPONENT_INVENTORY.md` §4 #2/#6 records 127 hospital and 26 emergency live ops with 12 emergency, 15 nursing and 13 critical-care tables. Status: **IMPLEMENTED / SOURCE**.

**Not verified / blockers:** ADR-B table ownership is `BLOCKED` (OD-003/OD-004); no dispatch→arrival→triage→bed→ICU handover journey; no measured alarm/response latency; no ET2E evidence for emergency break-glass under outage.

### 3.13 Hospital / HIS (PRG-02)

**Verified evidence:** `backend/app/services/hospital_service.py`, `backend/app/routes/hospital.py`, `backend/app/hospital/models/__init__.py`, `backend/app/devices/`, `backend/app/biomedical/`; `GULA_COMPONENT_INVENTORY.md` §4 #2 and #18 (medical equipment, 52 live ops, 12 + 10 device tables). Status: **IMPLEMENTED / SOURCE**.

**Not verified / blockers:** `hospital_desktop/` is real source (~2,055 lines of views, 534-line `offline.py`, encrypted session, 3 unittest methods) but has no CI/Compose wiring; `platform/apps/hospital` has no test/dist/CI; no live bed/asset reconciliation proof.

### 3.14 Care continuum (PRG-01)

**Verified evidence:** `backend/app/care_continuum/models/{maternal,immunization,chronic_disease,care_journey}.py`, `backend/app/routes/care_continuum.py` (74 operations, 45 models); `GULA_COMPONENT_INVENTORY.md` §4 #3/#8/#11/#12/#15/#17 records implemented MCH, immunization, chronic disease, referral and home healthcare; audit positional fix `AUDIT-POSITIONAL-001` and `AUDIT-BYPASS-001` independently verified in engineering scope (`GULA_AUDIT_POSITIONAL_FIX_REPORT.md`, `GULA_AUDIT_BYPASS_FIX_REPORT.md`); zero-audit-write observation reassessed as journey-level observability gap, not chain bypass (`GULA_SERVICE_COVERAGE_REASSESSMENT.md`, `GULA_AUDIT_ARCHITECTURE_COMPLETENESS_REPORT.md`). Status: **TESTED / SOURCE**.

**Not verified / blockers:** fixes' commits are BLOCKED by mixed provenance; ADR-C `BLOCKED`; underlying journeys remain BLOCKED; no realized continuum journey E2E.

### 3.15 Specialty gaps (PRG-06)

**Verified evidence:** `GULA_COMPONENT_INVENTORY.md` §4 #10 Dental 0 ops / 0 tables, #13 Rehabilitation 0 ops / 0 tables, #14 Mental health 0 ops / 0 tables (analytics signals only), all marked `OUT OF SCOPE` in source language; Oncology/Cardiology/Nephrology appear at analytics/enum level in `backend/app/nhdw/`, `backend/app/health_data/`, `backend/app/national/intelligence/`; Pathology/Microbiology/Molecular exist as LIMS assay categories/catalogs in `backend/app/lims/`; OR exists at resource/safety-checklist level in `backend/app/critical_care/` and hospital models. Canonical domain registry: `backend/app/domain_platform/manifest.py` (11 canonical domains), 8-section blueprints; `backend/app/domain_platform/{core,shared_core,isolation,certification,lifecycle,versioning,binding,contracts,dormancy}.py`; tests `backend/tests/test_domain_platform.py`. Status: **DOCUMENTED ONLY / DOCUMENTED DESIGN**; LIMS assay categories are **PARTIALLY IMPLEMENTED / SOURCE**.

**Not verified / blockers:** no dedicated clinical modules, no specialty contracts, no specialty E2E journeys; `GULA_COMPONENT_INVENTORY.md` §4 preamble records 0 verified E2E journeys and 0 owner approvals for the 18 national services; R-12 open; Dormant strategic assets must be preserved (`config/dormancy.json`, `policies/dormancy_policy.py`, `archive/{legacy,experimental,scripts}/`) — gap closure must not delete them.

### 3.16 Operations — claims, financial, insurance, HR, procurement (PRG-07)

**Verified evidence:** `backend/app/billing/`, `backend/app/financial/`, `backend/app/insurance/`, `backend/app/governance/models/workforce.py`, `backend/app/pharmacy/inventory.py`, `backend/app/clinical/quality/`; `GULA_COMPONENT_INVENTORY.md` §4 #16 records insurance `BLOCKED` with 30 `ins_*` tables and 84 unserved endpoints, F-085 `InsBase` unregistered; `docs/release/KNOWN_LIMITATIONS.md` §2 says financial engine is Phase A schema only, `ENABLE_FINANCIAL_ENGINE`/`ENABLE_ADS` default off. Status: **PARTIALLY IMPLEMENTED / SOURCE**, insurance **BLOCKED**.

**Not verified / blockers:** ADR-G/I `BLOCKED` for insurance/claims; no claims adjudication E2E; HR and procurement partial (workforce model and inventory only, no independent HR/procurement module certification); no financial reconciliation evidence; seed §8 requires analytics to be derived-only, not a competing billing source.

### 3.17 Analytics / AI / NHDW / national_data (PRG-09)

**Verified evidence:** `backend/app/health_data/`, `backend/app/nhdw/`, `backend/app/national_data/`, `backend/app/national/intelligence/`, `backend/app/research_platform/`, `backend/app/ai/`, `backend/app/ai_fabric/`; `GULA_COMPONENT_INVENTORY.md` §4 #9 notes 15 `nhdw` tables alongside public health. Status: **PARTIALLY IMPLEMENTED / SOURCE + DOCUMENTED DESIGN**.

**Not verified / blockers:** `backend/app/national_data/` is dormant by `backend/app/domain_platform/config/dormancy.json`; no warehouse refresh lineage proof; AI governance/clinical safety R-16 unresolved; DeepSeek key rotation NOT VERIFIED (`GULA_MASTER_EXECUTION_STATUS.md:173`); no model-output clinical validation; derived-copy ownership rule (seed §8) not enforced by an evidenced control.

### 3.18 Channels (PRG-08)

**Verified evidence:** `frontend-v3` is the only deployed/CI web shell (`docker-compose.yml:245-247`, `docker-compose.full.yml:743-745`, `frontend-pwa.yml`, `e2e.yml`, `bundle-budget.yml`, `ci.yml:196-208`); `frontend-v3/src/routes/index.tsx` declares **94 paths** with **80 RoleGuard usages**; Arabic-first `index.html:2` (`lang=ar`, `dir=rtl`), i18n ar/en/ku/tk/syr; generated client `client.ts` 919 lines, `types.ts` 12,412 lines, `endpoints.ts` 107 KB; auth/workspace via `src/contexts/AuthContext.tsx`, `src/components/workspace/WorkspaceSelector.tsx`, `src/api/workspaceScopedReads.ts`. Native/real source: `mobile/android` (160 files, 25 Compose screens, Retrofit/Room/Hilt/WorkManager, cert pinning, encrypted prefs, 43 `@Test`; `mobile-android.yml`), `mobile/desktop` (200 files, 24 GoRoute paths, Dio/Drift/Riverpod, offline queue/conflict resolver, 9 tests; `mobile-flutter-desktop.yml`), `mobile/ios` (125 files, SwiftUI, Keychain/biometrics, CoreData, 61 tests; expected Xcode metadata absent), `mobile-expo` (speech-input module, 4 tests), `hospital_desktop/`, `platform/apps/{citizen,doctor,hospital,laboratory,ministry,nurse,pharmacy,radiology}`, `apps/gula-platform-ui-refresh` (175 files, 7 routes, 14 tests), `apps/gula-web-suite` (152 files, 15 tests, todo-marked flows), `client/`. Status: **PARTIALLY IMPLEMENTED / SOURCE + TEST-ONLY**.

**Not verified / blockers:** `frontend-v3/data-source-inventory.json` classifies the 94 surfaces as **72 unbound, 17 demo-only, 3 safe_bridge, 2 contract-bound** → **92 non-operational**, 2 blocked-until-server-enforcement; only `src/pages/patients/PatientsPage.tsx` and `src/pages/orders/OrdersPage.tsx` are contract-bound. No local clinical offline queue comparable to native clients. iOS CI cannot bind (missing Xcode workspace/project). `hospital_desktop/` and `platform/apps/*` have no CI/Compose and root `index.html` links to missing `platform/apps/*/dist`. No directorate/governorate persona app found. R-13 open; G8/G9 not passed.

### 3.19 Integration, standards, events and gateways (PRG-10; C08–C14)

**Verified evidence:** real source in `backend/app/integration/connectors/{lis,pacs}.py`, `backend/app/integration/gateway/{amqp_gateway,dicom_gateway}.py`, `backend/app/gateways/lab_device_gateway.py` (HMAC + replay), `integration/connectors/__init__.py` (~28 registrations), `shared/events/bus.py`, `backend/app/kernel/event_bus/`, `backend/app/services/outbox_service.py`, `models/{outbox,integration_inbox}.py`, `worker.py`; standards in `integration/standards/{hl7,astm,dicom,terminology,ihe}.py`, `lims/integration/`, `health_core/fhir/{serializers,deserializers}.py`; HL7 v2 generic parse/serialize/ACK plus synthetic ORU subset; ASTM real; terminology static in-memory CodeSystem registry; generated clients real (`frontend-v3/src/api/generated/*`, `contracts/sdk/{python,typescript,dart,kotlin,cli}`); live OpenAPI generated by FastAPI with `X-API-Version: 2.5.0` middleware. Status: **PARTIALLY IMPLEMENTED / SOURCE + TEST-ONLY + DOCUMENTED DESIGN**.

**Not verified / blockers (explicit conflict set):**
- Four disconnected event stacks: kernel in-memory bus, durable SQL outbox (poll 10 s, batch 50, 5 attempts, 30-day purge, `skip_locked`), `health_core` synthetic deterministic events, `core/sync_engine` in-memory LWW. No authoritative event store. `shared/events/bus.py` swallows handler exceptions; `OutboxWorker` can mark done with zero successful handlers; kernel publish never populates its own outbox/inbox/DLQ; dual outbox worker in `worker.py` and `core/startup.py:270-272`; no `aio_pika` async broker dependency.
- `contracts/export/{openapi,asyncapi,fhir}.json` are 98/102/305-byte stubs; checked-in `openapi.json` is version 2.1.0 with zero paths; `health_core/contracts/version.py:6-8` is `LOCAL_SYNTHETIC_ONLY`.
- `contracts/routes.py:52` has a wrong import breaking 4 schema endpoints; no request negotiation, `Deprecation` or `Sunset`; only `/api/v1/canonical-patients` and `/api/ai/v2` are versioned despite `/api/v1` claims.
- External gateways `backend/app/gateways/{national_identity,insurance,residency,cloudflare}_gateway.py` default to `STUB` mode in `gateways/mode.py`; HL7→FHIR returns `simulationOnly: True` (`backend/app/capabilities/fhir_interoperability/routes.py:83`, `schemas.py:86,96`); `devices/outbox.py` has `simulation_only=True`; AMQP gateway reports success on ImportError.
- Correlation: `X-Request-ID` echoed, `X-API-Version` emitted, `contracts/integration.py` has `correlation_id`, but no `X-Correlation-ID` header and `request.state.correlation_id` never set in middleware.
- Inbound idempotency via `models/integration_inbox.py` + `integration/inbox.py` stages/validates but does not auto-apply (C10/C12 not closed).
- Offline: HEAD `CRDT_MERGE` is first-seen-key-wins and can overwrite a lab result; `CONFLICT_QUARANTINE` fix is present only in the uncommitted working tree (`git diff --stat backend/app/services/offline_sync_service.py` confirms modification at HEAD; source comment `backend/app/services/offline_sync_service.py:20-25`). SDK sync modules are naive client/remote-wins and unused by frontend-v3; no durable production offline queue (R-08, G9).

### 3.20 Infrastructure — HA, backup/DR, observability, performance (PRG-10)

**Verified evidence:** 15 Dockerfiles, 9 Compose files, Helm chart `helm/gula-platform` (HPA 2–10, PDB, ServiceMonitor, PVCs), `k8s/`, Terraform, Cloudflare and DigitalOcean artifacts; HA config at `config/postgres-ha/patroni.yml` plus backup/PITR/cross-region replication configs; full compose has PG primary+replica, PgBouncer to primary only, Redis Sentinel quorum 1, Kafka replication factor 1, single RabbitMQ/MinIO, Keycloak `start-dev`, Vault `-dev`. Scripts exist: `scripts/backup.sh`, `continuous-backup.sh`, `pitr-recover.sh`, `restore-test.sh`, `validate-restore.sh`, `dr-*.sh`. Health and `/metrics` JSON plus `/metrics/prom` exist; Prometheus fail-closed in production; structured JSON logging real. CI hard gates: flake8/ruff E9,F, frontend lint/tsc/build, full backend pytest, safety, bandit, migration checks; baselines `REGRESSION_MINIMUM_PASSED=780`, quality index threshold 500. Status: **BLOCKED / DOCUMENTED DESIGN + NOT VERIFIED**.

**Not verified / blockers:** `DATABASE_RECOVERY_REPORT.md:7-11` says `NOT IMPLEMENTED/BLOCKED`; no restore/PITR/RPO/RTO drill; PITR dry-run unless `FORCE_PITR=true`; `validate-restore.sh` swallows pg_restore failures with `|| true`; `dr-failover.sh` has undefined `DR_IP`; `backup-verification.sh` uses mysql clients; no CI workflow invokes DR scripts (G6 fails). Observability contract gaps: Helm ServiceMonitor scrapes authenticated JSON `/metrics` instead of `/metrics/prom`; SLO metrics `gula_down` and `gula_request_duration_seconds_bucket` are not emitted by the live endpoint (`build_prometheus_response` has no call site); no runtime OTel FastAPI instrumentation; alertmanager webhook placeholder. Performance targets exist (`k6/load_test.js`: error <1%, read p95<500 ms, write p95<1000 ms, health p99<200 ms; quality-gates p50 200/p95 500/p99 1000, throughput >=100 rps) but `.benchmarks` empty, `benchmark-results.json` FAIL, `reports/production_audit_report.md` MISSION-019/020 not executed, `reports/independent-certification-report.md` no national-scale load/chaos results, `GOVERNANCE ADVERSARIOUS PERFORMANCE` BLOCKED — NOT MEASURED (G7 fails). `MIG-EXISTING` PARTIAL/NOT MET; strict schema gate **753 passed / 119 failed**. No live failover evidence; broad `0.0.0.0` publication. Drift: `DEVOPS_CERTIFICATION.md` claims python:3.14/node:24/14 Dockerfiles vs tree python:3.12-slim/node:22.13-alpine/15; `reports/ci/ci-cd-status-report.md` dated 2026-07-17 describes 6 workflows vs 32 present; root `pyproject.toml` targets py314 while `requires-python >=3.12` and CI uses 3.12.

### 3.21 Test estate (PRG-10; G1–G12 evidence supply)

**Verified evidence (static):** 353 `test_*.py` files; 2,741 `def test_`/`async def test_` definitions across 163 files; unit dir 554 definitions; integration 42; contracts 4; security-named 187; FHIR 110; migration 40; offline 43; resilience 78; concurrency 21; performance 30; stress 30; chaos 30; disaster 10. Frontend Vitest: 56 `it`/`test` definitions; documented runs 34 tests/10 files and 38 tests/11 files. Playwright: 13 specs, 22 tests, Chromium config — **no executed pass/fail count found in repo reports**. Load scripts: `k6/load_test.js`, `tests/load/*`, Locust — no execution results. PostgreSQL-specific evidence exists for P-02 (§3.5). Manifest integrity: CHECKPOINT_2026_11_20 6/6, REBUILD 4/4, REV3 3/3, P02 6/6, P03 design 3/3, P03 readiness 2/2. Status: **TESTED / TEST-ONLY** (static inventory + named P-02 PG run); full current-suite execution **NOT VERIFIED**.

**Not verified / blockers:** `backend/tests/conftest.py` forces SQLite in-memory, registers JSONB/BigInteger compilers and overrides DB dependencies — the default suite does not exercise PostgreSQL locking, sequences, isolation, triggers or PG DDL. Historical full-suite figures vary by tree/date (4913, 4947, 4984+27 skipped, 5105+27, 5124+28, 5138+28, 5151+28); 5151 is explicitly historical and not re-run; `CERTIFICATION-v1.0.md` states full suite **NOT RUN** — it cannot be used as a current pass claim. P-03 PG diagnostic RED 1 failed/1 passed (`P-03_READINESS_2026_11_24.md`) is defect evidence, not a pass. E2E: 13 Playwright specs are navigation/surface checks; patients/orders/results/samples assert "blocks direct reads until server enforcement is proven" or a safe bridge; no complete patient journey; OD-008 BLOCKED. Anti-abuse: `ADVERSARIAL_TEST_REPORT.md` §3 matrix partially covered; broker outages, runtime HTTP probes, operational migration interruption, offline convergence under network loss not run; no brute-force/enumeration results. QA gaps: A09-001 no-op security test, A09-003/008/009 Playwright wiring, A09-004 PG16 schema gate 119 failures, A09-010 a11y, A09-011 contract governance gate absent from CI, A09-013 seven migration skips without DB URL. `CRITICAL_FILE_SHA256.txt` has 3 historical failures superseded by `CHECKPOINT_2026_11_20` lines 4–6.

### 3.22 Governance and status authority (PRG-00)

**Verified evidence:** `GULA_OWNER_DECISION_REGISTER.md:9-11` — only owner-recorded decisions can move BLOCKED→ACCEPTED; OD-001 accepted for SEC-015/F-01 engineering scope only; OD-002…OD-025 remain BLOCKED; §9 records P-02/P-03 package-level AUTHORIZED with no acceptance, no release authority, HOLD TRUE. `GOVERNANCE/FINAL_DECISION.md` §1/§4/§7/§8/§9/§10: HOLD, security NOT CERTIFIED, release candidate HOLD, MIG-EXISTING NOT MET. `GOVERNANCE/GECS/MASTER_CONTROL.md` §3/§7/§8 prohibits HOLD→GO and commit/push/merge/PR/deploy and touching gula-platform. `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json`: `production_ready_items = 0`, not-authorized list, STOP before deployment; worktree SHA-256 differs from committed HEAD blob — protected version exists only uncommitted and must be preserved. Protected MD5s unchanged (seed §1). Roadmap inputs: `GULA_AUDIT_REMEDIATION_ROADMAP.md` (R0–R4, P-01…P-19), `GULA_COMPLETION_PLAN.md` (WAVE 0→12), `GULA_ARCHITECTURE_DECISIONS.md` (ADRs documented; data ownership/legal BLOCKED), `ARCHITECTURE.md`, `DESIGN.md`, `GOVERNANCE/NATIONAL_INTEGRATION_ROADMAP.md`, `docs/adr/`. Status: **BLOCKED / SOURCE**.

**Not verified / blockers:** OD-002 provenance/commit, OD-003/OD-004 ADR-A/B, OD-005 W-017 strict gate, OD-006…OD-025 security/clinical/ministry approvals, D-020/D-021, DeepSeek rotation, `STATUS/OPEN_BLOCKERS.md` older snapshot. Three status vocabularies coexist (owner register 7 terms; engineering ladder; GECS legend) — they must not be conflated (R-15, R-18).

---

## 4. Status transition ladder

**No item in this inventory is currently `PRODUCTION READY`.** Upward movement requires the evidence below and an owner-recorded decision where specified. No status may skip a rung.

| From → To | Evidence required (concrete) | Owner action | Current example |
|---|---|---|---|
| `PLANNED` → `DOCUMENTED ONLY` | Approved architecture/contract reference with versioned schema and named owner | NV2-D01/D03 | P-03 D1–D5 design records; specialty target scope |
| `DOCUMENTED ONLY` → `PARTIALLY IMPLEMENTED` | Source in the active tree with a path citation; distinction `SOURCE`; registration decision recorded | NV2-D05 | 8/10 capability stubs; field-level security scaffolding |
| `PARTIALLY IMPLEMENTED` → `IMPLEMENTED` | Complete active path, no stub/default-STUB fallback on the primary path, factory/route registration, migration on single head | NV2-D05, G1/G4/G5 | FHIR resources; DICOM device bridge; quota on 92 unbound v3 pages |
| `IMPLEMENTED` → `TESTED` | Executable tests with a recorded run (count, environment, exit status) against the relevant runtime; PG behaviour must use PostgreSQL, not SQLite substitution | G3/G5, NV2-D14 | Blood bank; HIS; public health |
| `TESTED` → `INDEPENDENTLY REVIEWED` | Independent reviewer report with scope, MD5 of reviewed source, severity counts, residuals and no unreviewed WT-only delta on the reviewed path | G12 (pre-acceptance) | MPI (`MPI_FINAL_INDEPENDENT_AUDIT.md`); B-series authorization; P-02 engineering scope |
| `INDEPENDENTLY REVIEWED` → `ACCEPTED` | Owner-recorded decision in `GULA_OWNER_DECISION_REGISTER.md` naming exact scope, residuals and commit identity; mixed-provenance conflict resolved | NV2-D02/D09, owner only | None package-wide; OD-001 is scope-limited SEC-015/F-01 only |
| `ACCEPTED` → `PRODUCTION READY` | HOLD lifted; G1–G12 passed with artifacts; real DR/load/offline/E2E/anti-abuse results; `status_registry.json` updated by owner; Stable v1.0.0 declared | NV2-D04/D07/D15, owner only | **None — `production_ready_items = 0`** |

**Additional gate-specific ladders (required before any `PRODUCTION READY`):**

- Audit chain: WT advisory-lock fix must be committed, then independently reviewed under PG16.14 concurrency, then P-03-CONCURRENCY approved separately (NV2-D13), then T9 closed — only then can `PARTIALLY IMPLEMENTED` be reconsidered (R-03).
- MPI: AUD-02 DB `UNIQUE` applied via owner-authorized migration; AUD-07/AUD-16 owner decisions; then re-review (R-05).
- Offline: `CONFLICT_QUARANTINE` fix committed, CRDT first-seen-key-wins removed from HEAD, SDK/v3 convergence proven under network loss (G9, R-08).
- Integration: single authoritative event store or documented equivalent; checked-in OpenAPI regenerated with non-zero paths; `contracts/routes.py:52` fixed; external gateways moved off default STUB with live-mode proof; correlation header implemented (G1/G4/G10, R-14).
- Infrastructure: executed DR/PITR/RTO/RPO drill; ServiceMonitor→`/metrics/prom`; emitted SLO metrics; reproducible load artifacts meeting k6 targets; migration gate failures resolved (G5/G6/G7/G10).
- Channels: v3 contract-bound page count increased with server enforcement, native CI bindings fixed, platform apps wired or formally deferred (G8, R-13).

---

## 5. Explicit conflicts requiring owner decision

| ID | Conflict | Evidence A | Evidence B | Required decision |
|---|---|---|---|---|
| C-01 | Route counts irreconcilable | 1,815 paths / 132 route objects (`TEAM_C_INDEPENDENT_VERIFICATION_REPORT.md:32`, `NIAM_STEP_UP_SECURITY_REPORT.md:19`); 1,817 paths / 2,130 ops (`GOVERNANCE/WAVE_0_BASELINE.md:29`); 2,116 ops / 1,804 paths (`GULA_MASTER_BASELINE.md:53`) | 1,442 endpoints / 111 tags (`docs/constitution/runtime/02_route_registration_certification.md:14`); static scan 2,388 decorators; ~100 `include_router` in `factory.py:519-836`; MPI report 1,805 paths / 125 routes at HEAD `2827c1ff` | NV2-D01/D04 — adopt one measurement method; no live import measurement performed in this audit |
| C-02 | Capability stubs advertised as real | 10 directories under `backend/app/capabilities/` with tests (`GULA_COMPONENT_INVENTORY` domain evidence) | only 2 registered in factory; 8 empty CRUD stubs advertised by `kernel/capabilities_registry_populator.py` | NV2-D05 — extraction vs modular-monolith threshold |
| C-03 | External gateways default STUB | `backend/app/gateways/{national_identity,insurance,residency,cloudflare}_gateway.py`, `gateways/mode.py` | `docs/release/KNOWN_LIMITATIONS.md` §2 admits all adapters default to `stub` with uncommitted credentials; `simulationOnly: True` in FHIR routes | NV2-D06/D08 — live integration scope and credentials policy |
| C-04 | Offline CRDT fix uncommitted | HEAD first-seen-key-wins `CRDT_MERGE` can overwrite lab result (integration evidence §13) | `CONFLICT_QUARANTINE` at `backend/app/services/offline_sync_service.py:20-25,200,238`; unstaged diff confirmed | NV2-D02 — provenance/commit decision, then G9 |
| C-05 | Audit-chain concurrency fix uncommitted; P-03 packages | HEAD defect `audit_service.py:106-112,219-229` reproduced on PG16.14 | WT fix `:48-114,284-325` unstaged; P-03 `PREPARED ONLY`, T9 in separate P-03-CONCURRENCY | NV2-D12/D13 — approve packages separately; do not confuse with PRG-03 |
| C-06 | OpenAPI contract artifacts empty | generated live OpenAPI exists via FastAPI; `contracts/api/v1/catalog.json` 202 KB, `contracts/events/catalog.json` 183 KB | `contracts/export/{openapi,asyncapi,fhir}.json` 98/102/305 bytes; checked-in openapi.json 2.1.0, 0 paths; `contracts/routes.py:52` broken import | NV2-D03/D04 — contract owner and G1/G4 |
| C-07 | DR scripts exist vs DR status | `scripts/{backup.sh,pitr-recover.sh,restore-test.sh,validate-restore.sh,dr-*.sh}`, Patroni config, Helm PVCs | `DATABASE_RECOVERY_REPORT.md:7-11` NOT IMPLEMENTED/BLOCKED; `|| true` swallows pg_restore failures; undefined `DR_IP`; mysql clients in backup-verification | NV2-D07 — RTO/RPO targets and drill authority (G6) |
| C-08 | Performance targets vs no results | k6 thresholds and quality-gate thresholds documented | `.benchmarks` empty, benchmark-results.json FAIL, MISSION-019/020 not executed, performance advisory/warning-only | NV2-D07 — measurement plan (G7) |
| C-09 | HA configuration vs single points | Patroni, replica, Sentinel, Kafka configs | PgBouncer to primary only, Sentinel quorum 1, Kafka RF 1, single RabbitMQ/MinIO, Keycloak start-dev, Vault -dev | NV2-D04 — HA target and G11 |
| C-10 | Historical certifications vs HOLD | `SECURITY_CERTIFICATION.md` (PLATINUM/PASS 100%), `MASTER_RELEASE_CERTIFICATION.md`, `RC_READINESS_REPORT.md`, `ENTERPRISE_PRODUCTION_CERTIFICATION_REPORT.md`, `DEVOPS_CERTIFICATION.md`, `CERTIFICATION-v1.0.md` | `GOVERNANCE/FINAL_DECISION.md:13,361`, `GULA_RELEASE_ACCEPTANCE_REPORT.md`, `FINAL_00_MASTER_VERDICT.md`, `status_registry.json` `production_ready_items = 0` | NV2-D09 — supersede older certificates formally |
| C-11 | OD-001 scope vs P-02 status | `GULA_MASTER_EXECUTION_STATUS.md:15` records OD-001 `ACCEPTED` for SEC-015/F-01 engineering scope only | seed §4 fixes P-02 / AUD-F02 at `IMPLEMENTED · TESTED · INDEPENDENTLY REVIEWED`, not `ACCEPTED` | NV2-D09 — confirm acceptance boundary; this inventory follows the seed |
| C-12 | Frontend breadth vs operability | 94 routes, 80 RoleGuard usages, generated client 919/12,412 lines | `data-source-inventory.json`: 72 unbound, 17 demo-only, 3 safe_bridge, 2 contract-bound → 92 non-operational | NV2-D10 — channel workstream funding |
| C-13 | DICOM capability vs limitations | `pacs.py` DICOMStorageService and QIDO/WADO/STOW connector | TD-008 says device bridge supports only ASTM/HL7; no pydicom/pynetdicom dependency | NV2-D11 — DICOM/PACS strategy |
| C-14 | Parallel trees vs active monolith | `backend/core/api/`, `backend/gateway/`, `backend/services/*/main.py`, `services/*`, `api/demo-api/`, `server/index.ts` | `docs/evolution/PLATFORM_EVOLUTION_PLAN.md:305` calls these experimental stubs; unregistered `national/api/routes/__init__.py` with 16 sub-routers | NV2-D05 — service extraction thresholds |
| C-15 | Test evidence strength | static 2,741 test definitions; historical full-suite figures up to 5151+28 | default conftest SQLite; `CERTIFICATION-v1.0.md` full suite NOT RUN; no E2E/load/anti-abuse execution results | NV2-D14 — environments and synthetic data policy |
| C-16 | Mixed Git provenance | 20 staged R100 renames (name-status MD5 `56c524d6…`) into `archive/legacy/workflow_runtime/`, 162 unstaged tracked, 686 untracked before V2 docs (collapsed 313) | canonical `backend/app/workflows/` untracked; 62 untracked `backend/app` entries, 10 untracked migrations; protected SHA differences in status registry | NV2-D02 — resolve before any save/merge |

**Decision status:** all NV2-D01…NV2-D15 are `PLANNED` (proposed, pending owner approval). No conflict above is silently resolved in this document.

---

## 6. Risk and gate exposure summary (index only)

- Risks most directly evidenced here: R-01 (provenance), R-02 (contract immaturity), R-03 (audit concurrency), R-04 (authorization bypass/IDOR), R-05 (MPI merge conflict), R-06 (silent result modification), R-07 (consent/emergency), R-08 (offline conflict), R-09 (PG/audit availability), R-10 (unmeasured load), R-11 (DR unproven), R-12 (specialty gaps), R-13 (channel divergence), R-14 (event/outbox), R-15 (status conflict), R-16 (AI governance), R-17 (CI trust), R-18 (owner decisions).
- Gates with no passing evidence recorded in this inventory: G1–G12. G6, G7, G8, G9 and G12 are the most clearly unsupported (see §3.20, §3.21, §3.18, §3.19).
- Workstreams proposed to close evidence gaps: WS-CORE-01, WS-SEC-01, WS-AUD-01 (documentation/test design only — no P-03 implementation), WS-OBS-01, WS-DB-01, WS-E2E-01, WS-API-01, WS-GOV-01. All are `PLANNED`.
- Critical path remains W0 → NV2-D01/D02/D03/D04/D07 → W1 (C01–C09) → W3 → W4 → G1–G12 → owner acceptance. **Execution is not authorized.**

---

## 7. Evidence basis

All sources below were read in `/home/samertts/workspace/projects/gula-integration` only; no sibling repository file was read for drafting beyond the read-only HEAD identifier in the seed. No source, test, config, migration or protected file was modified.

**Governance and posture:** `GOVERNANCE/FINAL_DECISION.md`; `GOVERNANCE/GECS/MASTER_CONTROL.md`; `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json`; `GOVERNANCE/NATIONAL_INTEGRATION/06_IDENTITY_MPI_SURVEY.md`; `GULA_OWNER_DECISION_REGISTER.md`; `GULA_MASTER_EXECUTION_STATUS.md`; `GULA_RELEASE_ACCEPTANCE_REPORT.md`; `FINAL_00_MASTER_VERDICT.md`; `FINAL_ASSURANCE_DECISION.md`; `STATUS/OPEN_BLOCKERS.md`; `GULA_COMPONENT_INVENTORY.md` §4; `GOVERNANCE/NATIONAL_SERVICE_INVENTORY.md` (as cited by `GULA_COMPONENT_INVENTORY.md`); `GOVERNANCE/WAVE_0_BASELINE.md`; `GOVERNANCE/ADVERSARIAL_ASSURANCE/MPI_AND_IDENTITY_AUDIT.md`; `docs/evolution/PLATFORM_EVOLUTION_PLAN.md`; `docs/adr/`; `GULA_ARCHITECTURE_DECISIONS.md`.

**Identity, MPI and security:** `backend/app/identity/`; `backend/app/security/`; `backend/app/config.py`; `shared/auth/jwt.py`; `shared/security/encryption.py`; `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md`; `GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md`; `GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_VERIFICATION_REPORT.md`; `INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md`; `INDEPENDENT_VERIFICATION_TEAM_C_B5_REVERIFY.md`; `EXECUTION_LEDGER.md`; `GOVERNANCE/SECURITY_REVIEW_REPORT.md`; `FIELD_SECURITY.md`; `ADVERSARIAL_TEST_REPORT.md`.

**Audit and P-02/P-03 packages:** `backend/app/services/audit_service.py` (HEAD and uncommitted diff inspected read-only); `scripts/audit_verifier.py`; `scripts/gula_guardian.py`; `backend/app/identity/services/canonical_audit.py`; `backend/migrations/versions/20250322_0002_*.py`; `backend/migrations/versions/20260505_0005_*.py`; `P-02_FINAL_CLOSURE_2026_11_24.md`; `P-02_IMPLEMENTATION_EVIDENCE_2026_11_24.md`; `P-02_AFTER_REV3.md`; `P-02_INDEPENDENT_REVIEW_2026_11_24.md`; `P-03_READINESS_2026_11_24.md`; `P-03_CONCURRENCY_DESIGN.md`; `P-03_SCOPE_AND_DEPENDENCY_REVIEW.md`; `PACKET_REVIEW_2026_11_20.md`.

**Domain and capability source:** `backend/app/domain_platform/` (`manifest.py`, `core.py`, `shared_core.py`, `isolation.py`, `certification.py`, `lifecycle.py`, `versioning.py`, `binding.py`, `contracts.py`, `dormancy.py`, `config/dormancy.json`, `policies/dormancy_policy.py`); `backend/tests/test_domain_platform.py`; `backend/app/capabilities/`; `backend/app/factory.py`; `backend/app/lims/`; `backend/app/radiology/`; `backend/app/pharmacy/`; `backend/app/blood_bank/`; `backend/tests/blood_bank/`; `backend/app/public_health/`; `backend/app/ems/`; `backend/app/nursing/`; `backend/app/critical_care/`; `backend/app/hospital/`; `backend/app/care_continuum/`; `backend/app/routes/care_continuum.py`; `backend/app/billing/`; `backend/app/financial/`; `backend/app/insurance/`; `backend/app/governance/models/workforce.py`; `backend/app/health_data/`; `backend/app/nhdw/`; `backend/app/national_data/`; `backend/app/ai/`; `backend/app/ai_fabric/`; `backend/app/research_platform/`; `archive/{legacy,experimental,scripts}/`.

**Integration and standards:** `backend/app/integration/`; `backend/app/gateways/`; `backend/app/kernel/event_bus/`; `backend/app/services/outbox_service.py`; `backend/app/services/offline_sync_service.py` (HEAD and uncommitted diff inspected read-only); `backend/app/models/{outbox,integration_inbox}.py`; `backend/app/worker.py`; `backend/app/core/startup.py`; `shared/events/bus.py`; `backend/app/integration/standards/`; `backend/app/health_core/fhir/`; `backend/app/interoperability/fhir_http/router.py`; `contracts/export/{openapi,asyncapi,fhir}.json`; `contracts/api/v1/catalog.json`; `contracts/events/catalog.json`; `contracts/routes.py`; `contracts/sdk/`; `frontend-v3/src/api/generated/`; `docs/release/KNOWN_LIMITATIONS.md`.

**Channels:** `frontend-v3/src/routes/index.tsx`; `frontend-v3/data-source-inventory.json`; `frontend-v3/index.html`; `frontend-v3/src/pages/patients/PatientsPage.tsx`; `frontend-v3/src/pages/orders/OrdersPage.tsx`; `frontend-v3/src/contexts/AuthContext.tsx`; `frontend-v3/src/components/workspace/WorkspaceSelector.tsx`; `frontend-v3/src/api/workspaceScopedReads.ts`; `docker-compose.yml`; `docker-compose.full.yml`; `mobile/android/`; `mobile/ios/`; `mobile/desktop/`; `mobile-expo/`; `hospital_desktop/`; `platform/apps/`; `apps/gula-platform-ui-refresh/`; `apps/gula-web-suite/`; `client/`; `index.html`.

**Infrastructure, tests and reports:** `config/postgres-ha/patroni.yml`; `helm/gula-platform/`; `k8s/`; `scripts/backup.sh`; `scripts/continuous-backup.sh`; `scripts/pitr-recover.sh`; `scripts/restore-test.sh`; `scripts/validate-restore.sh`; `scripts/dr-*.sh`; `DATABASE_RECOVERY_REPORT.md`; `DEVOPS_CERTIFICATION.md`; `reports/ci/ci-cd-status-report.md`; `reports/production_audit_report.md`; `reports/independent-certification-report.md`; `k6/load_test.js`; `tests/load/`; `.benchmarks/`; `benchmark-results.json`; `backend/tests/`; `backend/tests/conftest.py`; `frontend-v3/vite.config.ts`; `CERTIFICATION-v1.0.md`; `CHECKPOINT_2026_11_20`; `CRITICAL_FILE_SHA256.txt`; `QA_AUDIT` findings A09-001/003/004/008/009/010/011/013 (as cited in the test-evidence audit).

**Planning inputs:** `/tmp/opencode/gula_v2_seed.md` (canonical identifiers and constraints); `/tmp/opencode/gula_v2_draft_instructions.md`; `gula_v2_evidence_{domain,backend,tests,security,integration,infra,channels,governance}.md` (read-only audit evidence files).

---

**End of inventory. No status in this document authorizes release, commit, merge or deployment. HOLD TRUE.**
