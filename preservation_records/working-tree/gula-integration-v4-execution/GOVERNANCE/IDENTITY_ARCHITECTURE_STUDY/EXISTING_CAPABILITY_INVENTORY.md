# GULA National Identity Architecture Study — Existing Capability Inventory (Workstreams A–P)

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test **source exists** — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification; no test was run and no DB contacted. Columns: Path · Status · API · Model · Tests · Dependencies · Security controls · Defects · Reusability · Missing requirements. Paths relative to repo root; `file:line` verified during this study.

---

## A. Authentication & sessions (workstream E)

| Capability | Path | Status | API | Model | Tests (source) | Dependencies | Security controls | Verified defects | Reusability | Missing |
|---|---|---|---|---|---|---|---|---|---|---|
| Login / password | `backend/app/routes/login.py`; `shared/auth/` | `PARTIAL` | login routes wired in `factory.py` | `lab_users`, NIAM accounts | auth test modules (not executed) | bcrypt/passlib, JWT | password hashing, rate limit | See MFA/device below | Medium | Zero-cost policy enforcement |
| JWT / OAuth2 provider | `backend/app/security/oauth2_provider.py` | `PARTIAL` | OAuth2 endpoints | — | `test_*oauth*` (not executed) | joserfc | issuer/audience config | **Empty JWKS** at `oauth2_provider.py:172-178` → provider cannot sign/verify | Medium | Working key set |
| WebAuthn / passkeys | `shared/auth/webauthn.py` | `PARTIAL` | WebAuthn routes (docs claim first-class) | credential store | WebAuthn tests (not executed) | `webauthn` (declared in requirements, not pyproject main) | origin binding | **Hardcoded RP_ID/origin** (`:22-24`), **`default=str` challenge serialization** (`:50,61,86,99`) → defective | Low until fixed | Correct RP config, portable challenge type |
| TOTP / MFA | `shared/auth/` (TOTP), `routes/` | `PARTIAL` | MFA endpoints | MFA secret on user | MFA tests (not executed) | `pyotp` (declared in requirements, not pyproject main) | secret encryption (unverified) | Enrollment/recovery parity unverified | Medium | Recovery hardening |
| Password reset | `backend/app/routes/password_reset.py` | `PARTIAL` | reset endpoints | — | reset tests (not executed) | token store | token expiry | **`bump_perm_version` signature mismatch** `password_reset.py:91` vs `session.py:40-47` → raises at runtime | Low until fixed | Correct call |
| Device revocation | `backend/app/security/device_service.py` | `PARTIAL` | device endpoints | device flag | device tests (not executed) | Redis | revoke flag | **Flag-only** (`:79-85`): no session termination / token blacklist | Low | Full revocation |
| Risk-based auth | `backend/app/services/risk_based_auth_service.py` | `SOURCE_PRESENT` | — | — | tests (not executed) | — | risk score computed | Computed but **not enforced** in login path | Low | Enforcement policy |
| SAML | `backend/app/` SAML ACS handler | `PARTIAL` | ACS endpoint | — | tests (not executed) | — | ACS validation | Validation-only; not a full IdP flow | Low | Full SSO if required |

**Conclusion (A):** authentication surface is broad but defect-ridden; docs overstate readiness. No mandatory per-login external cost is inherent in the local design (D-IDENTITY-09), but OTP/MFA dependency declarations are inconsistent.

---

## B–C. Identity, NHID & Master Patient Index (workstreams B, C, D)

| Capability | Path | Status | API | Model | Tests (source) | Dependencies | Security controls | Verified defects | Reusability | Missing |
|---|---|---|---|---|---|---|---|---|---|---|
| Master Patient Index | `backend/app/services/mpi/{matcher,blocking,resolver,models,api}.py` | `VERIFIED_IN_SOURCE` / `PARTIAL` nationally | `/mpi/resolve`, `/citizens/{ulid}`, `/merge`, `/review*`, `/citizens/{ulid}/access` (`api.py:35,41,101,142,182,226,313`; `factory.py:617`) | `citizens`, `identity_claims`, `mpi_merge_audit` (`models.py:42-48,115-122,150-158`) | `test_mpi_matcher.py` (35), `test_security_merge_regression_synthetic.py` (8) (not executed) | Jaro-Winkler, blocking | auth, rate limit, lab ABAC, admin-only merge, consent-gated cross-lab read | Merge leaves claims unrepointed (`resolver.py:354-400`, comment `:367-369`); no unmerge | **High** — strongest MPI candidate | National authority decision, unmerge, claim repointing |
| NID hashing | `backend/app/services/identity.py:213-225` | `PARTIAL` | — | `national_id_hash` | identity tests (not executed) | HMAC-SHA256, `NID_HMAC_KEY` | stable-key HMAC | Canonical helper digit-normalizes (`:222`) but `routes/register.py:341-343` hashes raw → inconsistent; raw NID in `identity_persistence_service.py:65-72` | Medium | One hash contract, no raw NID |
| NHID / health numbers | `identity_matching.py:80-84`; `identity_persistence_service.py:269-272`; `citizen_service.py:74-78`; `identity_service.py:20,39,54,70`; dormant `services/identity_engine/citizens_db.py:20-21` | `PARTIAL` | — | multiple formats | tests (not executed) | — | checksums (some) | 5+ formats; temp number returned then overwritten (`identity_service.py:15-32` vs `citizen_service.py:22-29,74-78`) | Low | Single NHID authority |
| Duplicate detection | `services/{mpi/matcher,identity_matching,health_data/mdm/matching,data_platform_service}.py` | `PARTIAL` | — | — | tests (not executed) | Fellegi-Sunter / Jaro-Winkler / weighted rules | MDM name-only safety (`:56-72`) | 3 divergent scorers, thresholds differ | Medium | One configurable matcher |
| Self-registration | `backend/app/routes/register.py` | `PARTIAL` | register endpoints (`:38-108,335-349`) | `User`, MPI `Citizen` | register tests (not executed) | MPI, HMAC | fail-closed unless enabled (`:114-119`) | NID hash inconsistency (above) | Medium | Assisted-registration flow |
| NIAM identity platform | `backend/app/identity/{api,models,services}/`, `identity/api/router.py:32,41-64` | `VERIFIED_IN_SOURCE` / `PARTIAL` | `/niam/*` 24 subrouters (`factory.py:819-820`) | `niam_identities`, 11 IdentityType values (`models/identity.py:9-21`) | `test_niam.py` (44), `test_niam_v2.py` (45), `test_niam_registry_authorization.py` (14) (not executed) | NIAM | registry guards deny all `Account` (`api/access.py:42-49,59-75`) | No NIAM-native registry-admin path | High (for staff/professional identity) | Registry-admin role, type alias map |
| Citizen-platform identity | `backend/app/citizen_platform/identity.py:51-176` | `SOURCE_PRESENT` / `PARTIAL` | no HTTP endpoints found | in-memory dicts | `test_citizen_platform_security.py` (8) (not executed) | encryption, HMAC | encrypted NID token, HMAC QR | QR hour overflow (`:100`); process-local stores (`:93,136`); encrypted token in `national_id_hash` (`:83-85`) | Low | Persistence, field semantics |
| Provisional identities | `national/domain/{unknown_patient,newborn,foreigner,visitor}.py` | `SOURCE_PRESENT` / `DORMANT` | routes defined `national/api/routes/identity.py:85-143`, aggregator unmounted | national tables | tests (not executed) | — | — | `merge_identified()` sets fields only (`unknown_patient.py:45-50`) | Medium | MPI reconciliation |
| Dormant JSON identity engine | `backend/services/identity_engine/` | `DORMANT` | none | JSON file | `test_identity.py` (not executed) | plaintext NID (`citizen_registry.py:4-18`) | none | Plaintext NID, unprefixed imports | Very low | Formal archival; do not activate |

---

## D. Guardian, child & vital events (workstreams H, I)

| Capability | Path | Status | API | Model | Tests (source) | Security controls | Verified defects | Reusability | Missing |
|---|---|---|---|---|---|---|---|---|---|
| NIAM lifecycle (guardian/consent/death) | `backend/app/identity/lifecycle/{models,services,routes}.py` | `SOURCE_PRESENT` / `PARTIAL` | `/niam/lifecycle/*` (`factory.py:819-820`; client `client.ts:182-195`) | `IdentityBase` (`env.py:102-103,144`), guardian/consent/death tables | NIAM tests (not executed) | audit actions (`models/audit.py:177-181,218-219`) | route↔service async/sync mismatch + missing `db` (`routes.py:460-469` vs `services.py:494-504`); OTP is status stub (`services.py:391-403`) | Medium | Fix wiring; real OTP |
| Guardian stores | 4 divergent stores (NIAM lifecycle, national, governance, citizen) | `NOT_IMPLEMENTED` as one capability | — | — | tests (not executed) | — | Fragmented authority | Low | One guardianship entity |
| Age transition (18) | `NOT_IMPLEMENTED` — zero matches for `coming_of_age`/`age_transition` in `backend/app` | `NOT_IMPLEMENTED` | — | pure predicates only (`patient.py:54-65`, `minor_protection.py:13-32`) | — | — | No transition job | — | Legal decision + job |
| Birth/death workflows | `national/workflows/{patient_registration,death_registration_workflow}.py` | `PARTIAL` (hazard if mounted) | — | — | tests (not executed) | — | steps marked `SUCCEEDED` without work (`:41-69`, `:12-24`) | Low | Real evidence per step |
| Civil registry connectors | `governance/services/connector_service.py:85-123` | `BLOCKED` | — | — | tests (not executed) | — | stubs with `confidence: 1.0` | Low | External agreement |

---

## F–G. OCR & document intelligence (workstreams F, G)

| Capability | Path | Status | API | Model | Tests (source) | Dependencies | Security controls | Verified defects | Reusability | Missing |
|---|---|---|---|---|---|---|---|---|---|---|
| ID card scan | `backend/app/routes/id_scan.py` | `PARTIAL` | `POST /id-scan/scan` (`factory.py:539,570`) | none (image not stored) | id-scan tests (not executed) | pytesseract/cv2 optional | rate limit 5/min, MIME/size, `needs_confirmation` | no confidence value; year cap 2025; no authenticity | **High (near-term)** | Confidence + quality gates |
| Document intelligence platform | `backend/app/document_intelligence/` | `BLOCKED` | `/document-intelligence/*`, `system:admin` (`api/routes.py:39-43`; `factory.py:792-793`) | `DocIntelBase` 21 models (`infrastructure/models.py:64-886`) | doc-int tests (not executed) | undeclared OCR libs | admin permission | orchestrator never initialized; encryption/audit/events stubs; dummy benchmarks; base unregistered (F-085) | Low until rehabilitated | Startup wiring, real services, migrations |
| Verification policy | `identity/services/verification_service.py:132-154` | `VERIFIED_IN_SOURCE` | `verify()`/`start_verification()` | — | verification tests (not executed) | — | assurance mapping | OCR/NFC correctly L0 | High | Preserve semantics |
| National ID verify gateway | `routes/national_identity.py:17-34` | `PARTIAL` / `BLOCKED` | `POST /national-id/verify` (`factory.py:604`) | — | `test_national_identity_production_guard.py` (3, not executed) | stub gateway | production guard | no real authority | Low | External integration |

Full detail: `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md`, `DOCUMENT_VERIFICATION_DESIGN.md`.

---

## L–N. Data ownership, offline & frontend (workstreams L, N)

| Capability | Path | Status | Verified detail | Reusability | Missing |
|---|---|---|---|---|---|
| Migration base registration | `backend/migrations/env.py` | `PARTIAL` | 17 bases; NR-011 delta `+49/-0` (preserved, not modified); first-wins merge; F-014 duplicate `national_facilities` | — | Correct merge strategy |
| Unregistered bases (F-085) | `DocIntelBase` (21), `InsBase` (30) | `BLOCKED` | 2 bases / 51 classes unregistered (`DATABASE_OWNERSHIP_MATRIX.md`) | — | Register or archive |
| National API router tree | `national/api/routes/__init__.py:20-36` | `DORMANT` | aggregator defined, never mounted (all 91 `include_router` calls inspected) | — | Owner decision to mount |
| Offline sync | `backend/app/services/offline_sync_service.py`, edge routes | `SOURCE_PRESENT`; behavior `UNVERIFIABLE` | see `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md` §2 | Medium | Runtime evidence |
| Arabic-first frontend | `frontend-v3/index.html:2`, `i18n/locales.ts:11,20` | `VERIFIED_IN_SOURCE` | `<html lang="ar" dir="rtl">`, `ar` default | High | — |

---

## Cross-cutting summary

- **Strongest reusable assets:** MPI (`services/mpi/`), NIAM identity platform, `VerificationPolicy`, `/id-scan`, Arabic-first frontend.
- **Systemic defects:** inconsistent NID hashing + raw NID at rest; unmounted national router; unregistered migration bases (F-085); doc-intelligence orchestrator never initialized with stub encryption/audit; WebAuthn/password-reset/device-revocation defects; 3 divergent matchers; 4 guardian stores; no unmerge/split.
- **Runtime posture:** all runtime behavior `UNVERIFIABLE`; no test executed; completion baseline records **0 services E2E/RUNTIME/PRODUCTION verified**, RPO/RTO **UNMEASURED**.
- **Preservation:** no source, model, API, migration, test or config changed by this study.

---

## 1. Cross-references

All documents in `GOVERNANCE/IDENTITY_ARCHITECTURE_STUDY/`. Baselines (read-only): `GOVERNANCE/DATABASE_OWNERSHIP_MATRIX.md`, `GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md`, `GOVERNANCE/FINAL_DECISION.md`, `GOVERNANCE/GECS/GECS_CHECKPOINT.md`.
