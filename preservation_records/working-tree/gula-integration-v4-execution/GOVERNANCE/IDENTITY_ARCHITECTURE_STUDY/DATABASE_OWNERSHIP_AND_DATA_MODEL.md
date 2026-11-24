# GULA National Identity Architecture Study — Database Ownership & Data Model

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`. `backend/migrations/env.py` remains at its existing `+49/-0` NR-011 delta — **this study does not edit it**.
**Workstream:** L (Database and Data Ownership), inputs from A, B, C, F, G, H, I.

---

## 0. Evidence convention and read-only boundary

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED`, `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. All figures below are from static source/governance-record inspection. **Actual applied DB head, table presence, column drift and test outcomes are `UNVERIFIABLE` in this study** — no database was contacted and no test executed. Model/migration files were not modified.

---

## 1. Declarative base inventory — `VERIFIED_IN_SOURCE`

AST resolution of full inheritance chains across `backend/app/**/*.py` yields **19 runtime bases** plus **2 generator string templates**. (A shallow direct-subclass scan produces false zeros because most domains use per-domain abstract entity classes.) Mapped-class counts are source counts, not DB-verified.

| # | Base | Declaration | Mapped classes | Dominant table prefixes | In `env.py` target_metadata? |
|---|---|---|---:|---|---|
| 1 | `Base` | `backend/app/database.py:273` | 147 | `lims_*`, `ai_*`, `device_*`, `roadmap_*`, `edge_*`, `billing_*`, `lab_*`, `clinical_*`, `national_*`(2), `oauth2_*` | YES (`:135`) |
| 2 | `NationalBase` | `backend/app/national/base.py:19` | 185 | `national_*`(84), `blood_*`, `ref_*`, `critical_*`, `biomed_*`, `ems_*`, `cc_*`(4) | YES (`:136`) |
| 3 | `EHRBase` | `backend/app/ehr/base.py:10` | 18 | `ehr_*` | YES (`:137`) |
| 4 | `CitizenPlatformBase` | `backend/app/citizen_platform/base.py:10` | **0** | — (no concrete subclass found) | YES (`:138`) |
| 5 | `ClinicalBase` | `backend/app/clinical/base.py:13` | 41 | `clinical_*` | YES (`:139`) |
| 6 | `HealthDataBase` | `backend/app/health_data/base.py:19` | 24 | `hd_*`, `rp_*` | YES (`:140`) |
| 7 | `TrustBase` | `backend/app/trust/base.py:16` | 6 | `trust_*` | YES (`:141`) |
| 8 | `GovernanceBase` | `backend/app/governance/base.py:15` | 64 | `gov_*` | YES (`:142`) |
| 9 | `CareContinuumBase` | `backend/app/care_continuum/base.py:19` | 45 | `cc_*` | YES (`:143`) |
| 10 | `IdentityBase` | `backend/app/identity/base.py:12` | 95 | `niam_*` | YES (`:144`) |
| 11 | `HospitalBase` | `backend/app/hospital/base.py:6` | 14 | `hospital_*`, `hospitals`, `bed_assignments` | YES (`:145`) |
| 12 | `DataPlatformBase` | `backend/app/national_data/base.py:13` | 36 | `dp_*`, `dw_*` | YES (`:146`) |
| 13 | `NHDWBase` | `backend/app/nhdw/base.py:8` | 14 | `nhdw_*` | YES (`:147`) |
| 14 | `NursingBase` | `backend/app/nursing/base.py:13` | 15 | `nursing_*` | YES (`:148`) |
| 15 | `PharmacyBase` | `backend/app/pharmacy/base.py:19` | 27 | `pharmacy_*` | YES (`:149`) |
| 16 | `RadiologyBase` | `backend/app/radiology/base.py:13` | 18 | `radiology_*` | YES (`:150`) |
| 17 | `FinBase` | `backend/app/financial/models.py:21` | 37 | `pay_*`, `fin_*` | YES (`:151`) |
| 18 | **`InsBase`** | `backend/app/insurance/domain/models.py:49` | 30 | `ins_*` | **NO** |
| 19 | **`DocIntelBase`** | `backend/app/document_intelligence/infrastructure/models.py:64` | 21 | `docint_*` | **NO** |

**Totals (source observation):** 19 runtime bases, 837 mapped classes; raw `__tablename__ =` grep count 838 (one extra non-AST/template occurrence).

**Generator templates (NOT runtime bases):** `backend/app/engineering/crud/generator.py:61,63` and `backend/app/engineering/generators/microservice.py:126,132` — emitted source-string templates only.

### 1.1 F-065 discrepancy (observation vs governance claim)

Governance `DATABASE_OWNERSHIP_MATRIX.md:58,67-70,92` and `STABILIZATION_PHASE_L_M_N_ASSESSMENT.md:70` record F-065 ("5 of 17 registered bases contribute 0 tables"). Source inspection shows only `CitizenPlatformBase` is genuinely 0-table; `NHDWBase` (14), `NursingBase` (15), `PharmacyBase` (27), `RadiologyBase` (18) demonstrably own concrete tables (e.g. `backend/app/nhdw/models.py:31` `class Admission(NHDWBaseEntity)` → `nhdw_admissions`; `nursing/models.py:106` `nursing_vital_signs`). **Inference:** F-065 is likely an artifact of shallow subclass scanning; it requires triage against source, not a behavior change. This is a study finding, not a correction to governance registries (which are out of scope).

---

## 2. Alembic `env.py` registration — `VERIFIED_IN_SOURCE`

- `backend/migrations/env.py:131-133` — comment: "BEGIN NR-011 REGISTERED BASES (17) — regression-tested by `backend/tests/unit/test_nr011_metadata_discovery.py`; do not reorder: order fixes duplicate-table resolution (first registration wins)."
- `:134-152` — `target_metadata = [` with exactly **17** `.metadata` entries in the order shown in §1 (bases 1–17 above).
- `:153` — END marker.
- `:155-176` — merge block: `:161` imports `sqlalchemy.MetaData as _MetaData`; `:163` `_combined = _MetaData()`; `:164-167` copies tables with `if _tname not in _combined.tables: _tbl.to_metadata(_combined)` → **first registration wins**; `:168-174` deduplicates index names; `:175` `target_metadata = _combined`.
- `:183` / `:202` — merged metadata passed to `context.configure()` in offline/online modes.
- Cross-metadata support imports at `:38-60` (17 base modules), `:42` `import app.national.domain`, `:66-77` dynamic `importlib` of 8 national infra model modules under `suppress(ImportError)`, `:80-99` clinical/health-data/trust/governance/care-continuum models, `:102-103` `IdentityBase` + `app.identity.models`.

**Unregistered (confirmed):** `DocIntelBase` and `InsBase` are neither imported nor present in `target_metadata`. Their 21 + 30 = **51 mapped classes are invisible to Alembic autogenerate**. This matches governance finding **F-085** (`DATABASE_OWNERSHIP_MATRIX.md:72-82`, status OPEN).

**Note:** the `ADR_DECISION_REQUEST.md` hard-prerequisite text ("`migrations/env.py:38` imports only `app.national.base`") is **stale relative to current source** — the 17-base registration and merge already exist. Governance confirms the NR-011 delta is `+49/-0`. This study does **not** modify `env.py`.

**UNVERIFIABLE caveat:** `env.py:103` imports `app.identity.models`; the transitive import of `identity/lifecycle/models.py` was not inspected, so autogenerate visibility of `niam_lifecycle_*` tables specifically is not confirmed.

---

## 3. Migration surface — `VERIFIED_IN_SOURCE` (source parse; no DB connection)

- **107** migration `.py` files; **107** unique revision ids; **0** files missing a revision id.
- **Single head revision: `20261114_0006`** (`backend/migrations/versions/20261114_0006_unify_authorization_indexes.py:10`); no other revision is unreferenced as a `down_revision`. This aligns with governance (`DATABASE_OWNERSHIP_MATRIX.md:85`).
- **4 merge migrations** (tuple `down_revision`): `20260815_0003_merge_device_and_interop_heads.py`, `20260815_0015_merge_monitoring_and_legacy_heads.py`, `20260819_0001_merge_drug_substitution_and_performance_indexes.py`, `20260908_0001_merge_heads.py`.
- Main lineage from head via first parent = 96 revisions; 11 branch-side revisions merged via the 4 merge nodes (inference only).

### 3.1 Identity/auth/NHI-relevant migrations (selected)

| Migration (under `backend/migrations/versions/`) | Revision | Relevance |
|---|---|---|
| `20250323_0005_citizen_email_nullable.py` | `20250323_0005` | citizen |
| `20260324_0006_patient_family_guardian.py` | `20260324_0006` | guardian fields |
| `20260413_0001_mpi_citizen_registry.py` | `20260413_0001` | MPI/citizen registry |
| `20260716_0014_governance_identity_persistence.py` | `20260716_0014` | **NHI** — only migration with `health_number` literal; creates `gov_identity_records`, `gov_health_numbers`, `gov_health_cards`, `gov_merged_identities` |
| `20260716_0015_auth_security_tables.py` | `20260716_0015` | auth/security (`mfa_devices`, `mfa_sessions`, service accounts) |
| `20260723_0001_niam_identity_platform_tables.py` | `20260723_0001` | NIAM core (persons, orgs, identities, accounts, devices, sessions, employments, assignments, licenses, credentials, policies, audit) |
| `20260723_0002_niam_completion_tables.py` | `20260723_0002` | NIAM completion |
| `20260811_0001_wave3_identity_mapping.py` | `20260811_0001` | identity mapping |
| `20260811_0002_citizen_relationship_foundation.py` | `20260811_0002` | citizen relationships |
| `20260814_0003_workspace_architecture.py` | `20260814_0003` | workspaces |
| `20260814_0005_role_permission_engine.py` | `20260814_0005` | RBAC |
| `20260815_0021_account_lockout.py` | `20260815_0021` | lockout |
| `20261114_0004_unify_professional_identity.py` | `20261114_0004` | professional identity |
| `20261114_0006_unify_authorization_indexes.py` | `20261114_0006` | **HEAD** — authorization indexes |

**Observation:** no migration file named or containing a literal `NHI` / `national_health_id` token; the NHI-equivalent construct is `health_number` in `20260716_0014` only → **PARTIAL** dedicated NHI migration surface.

**Readiness context (carried, not re-verified):** `DATABASE_OWNERSHIP_MATRIX.md:3` states "BLOCKED / NOT VERIFIED for migration readiness"; F-085 remains OPEN; the NR-011 `env.py` delta is `+49/-0`; overall release remains HOLD.

---

## 4. Duplicate table ownership — `VERIFIED_IN_SOURCE`

Exactly **one** duplicated `__tablename__` string exists across the backend: **`national_facilities`** (declared twice).

| Owner | Source | Class | Base | Shape |
|---|---|---|---|---|
| A | `backend/app/national/domain/facility.py:9` (`class Facility` at `:8`) | `Facility` | `NationalBase` (via `AuditEntity`) | ~28-column national reference facility (governance F-014 "dormant 28-col") |
| B | `backend/app/models/clinical_scope.py:136` (`class NationalFacility` at `:133`) | `NationalFacility` | canonical `Base` | 6-column, `UniqueConstraint("facility_code")`, "canonical national EHR facility resource" |

**Consequences:**
- `env.py:135` registers `Base.metadata` first, `NationalBase.metadata` second; the merge at `:164-167` uses first-wins. **Inference:** the merged autogenerate view sees owner B and silently skips owner A.
- 30+ `ForeignKey("national_facilities.id", ...)` references exist across `national/domain/{visit,laboratory,appointment,referral,provider,admission,ward,encounter,department,discharge,practitioner,employee,hospital,clinic}.py`, `care_continuum/models/*.py`, `ehr/models/*.py`, `national_data/models/mdm/LocationRegistry.py:9`.
- Governance cross-reference: `DATABASE_OWNERSHIP_MATRIX.md:47` "Ambiguous ownership"; `:90` F-014 (6-col clinical_scope DB-matching vs 28-col dormant); `ADR_DECISION_REQUEST.md` **ADR-B** (ownership of `facilities`/`organizations`/`national_facilities`) **PENDING**, recommendation B1 + single authoritative ORM owner. Also flagged: `insurance_coverages`, `facilities`, `organizations`, `patients` (non-exact conflicts).

No other duplicate table name found among 831 distinct `__tablename__` values.

---

## 5. Identity-domain field ownership map (target)

The study must prevent competing sources of truth. Proposed authoritative owner per capability (recommendations; not implemented):

| Field / entity | Candidate authoritative owner | Competing sources observed | Classification |
|---|---|---|---|
| Person identity (civil) | NIAM person registry (`niam_persons`, `IdentityBase`) | `national_citizens` (NationalBase), `gov_identity_records` (GovernanceBase), canonical `patients` | `NEEDS_OWNER_DECISION` |
| NHID / health number | Single NHID service; migration surface to be created | `gov_health_numbers` (`20260716_0014`) only; `Newborn.temporary_health_number` | `RECOMMENDED` (owner D-IDENTITY-02) |
| Iraqi National Identity Card number | Protected matching attribute (HMAC), identity registry | `identity/lookup?national_id=` frontend client; various `national_id` fields | `RECOMMENDED` (owner D-IDENTITY-01) |
| Account identity / credentials | NIAM accounts + `lab_users` | Two login paths (NIAM service and `routes/login.py`) | `NEEDS_OWNER_DECISION` |
| Patient master record | Canonical `patients` (`Base`) | `national_patients` (NationalBase), `cc_*` FKs to `national_patients` | `NEEDS_OWNER_DECISION` |
| Guardian relationship | Single authoritative guardianship entity (see `GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md` CH-01) | 4 stores (patient FK, NIAM, in-memory citizen, governance/national) | `NEEDS_OWNER_DECISION` |
| Documents / OCR extraction | Document-intelligence models (`DocIntelBase`) | `national/documents`, `shared/pdf`, FHIR DocumentReference | `NEEDS_OWNER_DECISION` + F-085 |
| Verification results | Single verification authority | Consent/trust/national duplication (see §6) | `NEEDS_OWNER_DECISION` |
| Vital events (birth/death) | Unified vital-event entity (see `BIRTH_AND_DEATH_LIFECYCLE.md`) | `national_newborns`, `national_death_records`, `record_death()` | `LEGAL_REVIEW_REQUIRED` |
| Sessions / authenticators | NIAM sessions/devices + canonical security tables | `zero_trust.py` in-memory (dormant), `mfa_devices` (lab_users FK only) | `RECOMMENDED` |
| Audit | Canonical hash-chain `audit_logs` + NIAM `niam_audit_entries` | Two chains; attribution questions (ADR-D pending) | `NEEDS_OWNER_DECISION` |
| Consent | Canonical `consents` (see §6) | Trust + national + citizen in-memory | `NEEDS_OWNER_DECISION` |
| Identity matching / merge history | MPI + `gov_merged_identities` | Duplicates across MPI and governance | `NEEDS_OWNER_DECISION` |

---

## 6. Consent and verification authority duplication — `PARTIAL`

- Canonical consent `backend/app/models/consent.py:32-62` → `consents` (`Base`), invariants documented `:1-13` (no PII, 72h cap, no wildcard scope, one-way active→revoked/expired, unique active tuple); service `backend/app/services/consent_service.py:45-53` (`ALLOWED_SCOPES` `read:*`), `:56` `MAX_CONSENT_HOURS = 72`, `:69-98` `check_active_consent()`; API `backend/app/routes/consent.py:35` prefix `/consent`, mounted `factory.py:622-623`; enforcement `backend/app/security/consent_dep.py:74-90`, fail-closed `:97-102`, emergency break-glass restricted to `doctor` role `:121-134`. **Actual usage: only** `backend/app/services/mpi/api.py:316` (`Depends(require_consent("read:citizen"))`) — enforcement is wired into one route only.
- Trust consent `backend/app/trust/models.py:20-36` → `trust_consent_records` (`TrustBase`), service `trust/services.py:32-124`, routes prefix `/api/v1/trust` mounted `factory.py:816-817` — a second authority with no reconciliation.
- Fail-open stub `backend/app/national/security/consent_enforcement.py:16-44` — `check_consent()` returns `granted=True` unconditionally (`:24`), `log_consent_check()` is `pass` (`:43-44`).
- National consent API `:7-26` static CRUD, **unmounted** → `DORMANT`; healthcare-consent capability routes `backend/app/capabilities/healthcare_consent/routes.py:9-51` return empty/success stubs, not mounted.
- Purpose vocabulary `backend/app/trust/enums.py:14-21` `ConsentPurpose` (TREATMENT/PAYMENT/OPERATIONS/PUBLIC_HEALTH/RESEARCH/NATIONAL_REPORTING/EMERGENCY) is **not mapped** to canonical `read:*` scopes — no mapping found.

---

## 7. Route registration context — `VERIFIED_IN_SOURCE`

`backend/app/factory.py` `_register_routes()` spans `:520-835`; **91 `include_router(...)` calls** plus two non-router registrations (`:589-590` financial, `:766-767` integration platform). Priority mounts for this study:

| Concern | Factory line | Router | Prefix |
|---|---|---|---|
| Login/register/verification | `:579` (`core_routes`) | `login`, `register`, `verification` | none / `/auth/verification` |
| MFA/password/OAuth2/SAML/service accounts | `:629,632,635,638,641` | respective routers | `/mfa`, `/auth`, `/oauth2`, `/auth/saml`, `/service-accounts` |
| MPI | `:617` | `mpi_router` | `/mpi` |
| Consent | `:623` | `consent_routes.router` | `/consent` |
| National identity verify | `:604` | `national_identity.router` | none (`/national-id/verify`) |
| Document platform | `:707` | `document_router` | `/national/documents` |
| Document intelligence / OCR | `:793` | `doc_intel_router` | `/document-intelligence` |
| NIAM platform | `:820` | `get_niam_router()` | `/niam` |
| Domain platform | `:824` | `get_domain_platform_router()` | `/niam/domains` |
| Authorization | `:834` | `authorization_router` | `/authz` |

**Orphaned router — `DORMANT`/NOT_REGISTERED:** `backend/app/national/api/routes/__init__.py:20` defines `national_router = APIRouter(prefix="/national", ...)` with 17 sub-routers (`:21-36`: advance_directive, cds, citizen, consent, encounter, family, fhir, health_card, identity, interop, medication_catalog, observation, reference, referral, security, vital_signs). Whole-repo search found **no registration** in `factory.py` or any `main.py`; the only `national_*` registrations are unrelated (`national_identity`, `national_data`, `national_streaming`). **Inference:** the entire `/national/*` citizen-facing identity/vital-sign/encounter/referral/health-card surface is defined but never mounted.

**Frontend gap:** neither `frontend-v3/src/api/endpoints.ts` nor `src/api/generated/client.ts` contains any `/mpi`, `/ocr`, `/document-intelligence`, or `/national/documents` call (targeted grep returned zero) — backend-only surfaces (see `API_AND_INTEGRATION_CONTRACTS.md`).

---

## 8. Test requirements (design-level; no tests run in this study)

| Level | Required coverage |
|---|---|
| Metadata | Regression of NR-011 17-base registration and first-wins merge (existing `backend/tests/unit/test_nr011_metadata_discovery.py` — source-referenced, not executed); verify `DocIntelBase`/`InsBase` registration once authorized (F-085). |
| Ownership | Assert exactly one authoritative class per `__tablename__`; resolve `national_facilities` (ADR-B) with a single owner. |
| Migration | Linear chain to head `20261114_0006`; no orphan revisions; rehearsal of downgrades (governance `PHASE_C_DATABASE_REHEARSAL_REPORT.md` carries prior evidence). |
| Identity data | HMAC protection of national ID / family ID (raw values never persisted); NHID stability and non-reuse; provenance and alias preservation. |
| Consent | Single enforcement authority; deny-by-default; fail-open stub removed from any enforcement path; purpose↔scope mapping. |
| Integration | No cross-base FK breakage after merge; `niam_lifecycle_*` metadata discoverability. |

No destructive migration or DDL is authorized by this study.

---

## 9. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages / risks | Legal | Security | Ops / cost | Dependencies | Failure scenario | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DB-01 | Assign one authoritative owner per identity-bearing field (§5) | Competing sources of truth | Keep multi-store | Single truth; simpler authorization | Ownership decisions + reconciliation | Data-ownership law may constrain | Positive (least privilege) | Migration effort | Owner decisions; ADR-B/D/E | Conflicting records | Reversible via migration | §5 | `NEEDS_OWNER_DECISION` |
| DB-02 | Register `DocIntelBase` + `InsBase` in `env.py` (F-085) once authorized | 51 classes invisible to Alembic | Leave unregistered | Autogenerate coverage | NR-011 delta change (currently +49/-0) | None identified | Positive (schema drift detection) | Low | Explicit implementation authorization; env.py edit | Undetected schema drift | Reversible | §2, §1 | `RECOMMENDED` |
| DB-03 | Resolve `national_facilities` duplicate with single owner (ADR-B) | First-wins hides 28-col owner | Keep both | Deterministic ownership | Migration/test impact | None identified | Positive | Moderate | ADR-B approval | Silent schema mismatch | Reversible via migration | §4 | `NEEDS_OWNER_DECISION` |
| DB-04 | Consolidate consent to one enforcement authority | Canonical + trust + fail-open stub | Keep all | Consistent deny-by-default | Migration/integration effort | Consent legal basis required | Positive | Moderate | Owner decision; purpose↔scope mapping | Unauthorized access via fail-open | Reversible | §6 | `NEEDS_OWNER_DECISION` |
| DB-05 | Do not mount `national_router` until each endpoint is verified | 17 dormant routers with workflow stubs | Mount as-is | Avoids false-verification exposure | Delayed capability | None identified | Positive | Low | Endpoint verification program | False `SUCCEEDED` workflows exposed | Reversible | §7 | `SECURITY_REVIEW_REQUIRED` |
| DB-06 | Treat F-065 as source-vs-governance discrepancy requiring triage | Governance says 5 zero-table bases; source disagrees | Accept claim | Accurate inventory | Governance record update needed (out of scope) | None identified | None | Low | Governance owner triage | Misleading inventory | N/A | §1.1 | `RECOMMENDED` |

---

## 10. Open questions

1. Which base/person registry is authoritative for civil identity: NIAM `niam_persons` vs `national_citizens` vs canonical `patients`? (`NEEDS_OWNER_DECISION`.)
2. Will F-085 be remediated, and who authorizes the `env.py` edit (currently `+49/-0`)? (`RECOMMENDED`, DB-02.)
3. ADR-B (`facilities`/`organizations`/`national_facilities` ownership) — pending owner decision (DB-03).
4. Is `niam_lifecycle_*` reachable by Alembic autogenerate (transitive import unverified)?
5. Which consent authority is canonical, and how do `ConsentPurpose` values map to `read:*` scopes (DB-04)?
6. Should the dormant `/national` router tree ever be mounted, and only after each endpoint is verified (DB-05)?

---

## 11. Cross-references

`MASTER_ARCHITECTURE.md` · `DATABASE_OWNERSHIP_MATRIX.md` (governance baseline, read only) · `NATIONAL_IDENTITY_MODEL.md` · `MASTER_PATIENT_INDEX_DESIGN.md` · `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` (F-085 / DocIntelBase) · `GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md` · `BIRTH_AND_DEATH_LIFECYCLE.md` · `API_AND_INTEGRATION_CONTRACTS.md` · `RISKS_AND_OPEN_QUESTIONS.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 1, 10).
