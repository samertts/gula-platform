# GULA National Identity Architecture Study — Architectural Decisions Register

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD** (md5 `effdfeaf10234678d83b2668c4489552`); D-020 and D-021 remain `PENDING_APPROVAL` and are **unchanged** by this study.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Decision classifications used: `OWNER_APPROVED`, `RECOMMENDED`, `NEEDS_OWNER_DECISION`, `LEGAL_REVIEW_REQUIRED`, `SECURITY_REVIEW_REQUIRED`, `BLOCKED_BY_EXTERNAL_DEPENDENCY`. `OWNER_APPROVED` here means **owner-approved as product design** — it does **not** authorize implementation or a release-status change. Per-document registers in the workstream files are authoritative for their own scope; this is the consolidated cross-reference.

---

## 1. Owner-approved product decisions (D-IDENTITY-01…11)

These govern the study as product-design decisions only.

| ID | Decision | Classification |
|---|---|---|
| D-IDENTITY-01 | NID is a protected matching attribute, never a password/default credential | `OWNER_APPROVED` |
| D-IDENTITY-02 | Independent, stable NHID, distinct from civil/account identity, never reused | `OWNER_APPROVED` |
| D-IDENTITY-03 | Provisional healthcare identity; no emergency care blocked; provisional ≠ verified; no auto-delete | `OWNER_APPROVED` |
| D-IDENTITY-04 | Twins have independent NHIDs and records; relationships are attributes | `OWNER_APPROVED` |
| D-IDENTITY-05 | Child NHID independent; guardian manages until 18 (law permitting); history preserved | `OWNER_APPROVED` |
| D-IDENTITY-06 | Healthcare birth/death evidence distinct from civil registration; medical records never deleted | `OWNER_APPROVED` |
| D-IDENTITY-07 | Hybrid duplicate resolution; auditable merge/unmerge | `OWNER_APPROVED` |
| D-IDENTITY-08 | Self + assisted registration; staff never acquire citizen credentials | `OWNER_APPROVED` |
| D-IDENTITY-09 | Zero mandatory per-authentication external service cost; no mandatory paid OTP | `OWNER_APPROVED` |
| D-IDENTITY-10 | OCR core but non-proof: Arabic/English, quality, extraction, confidence, human review | `OWNER_APPROVED` |
| D-IDENTITY-11 | Authentication ≠ patient-record access | `OWNER_APPROVED` |

**Preserved governance artifacts:** `GOVERNANCE/FINAL_DECISION.md` (HOLD), D-020 / D-021 (`PENDING_APPROVAL`), GECS registries, CC-010 completion program, prior D-023/A–O cycle, F-085 and NR-011 `env.py` delta (`+49/-0`). None modified.

---

## 2. Consolidated architecture decision register

Each row: ID · Decision · Classification · Source document. Full problem/alternatives/evidence are in the cited per-document register.

### Identity & lifecycle
| ID | Decision | Classification | Source |
|---|---|---|---|
| NI-01 | One digit-normalized NID HMAC contract; no raw NID at rest/in URLs | `RECOMMENDED` | `NATIONAL_IDENTITY_MODEL.md` |
| NI-02 | One NHID service/namespace/checksum/lifecycle; never reused | `OWNER_APPROVED` (D-IDENTITY-02) | `NATIONAL_IDENTITY_MODEL.md` |
| NI-03 | MPI as national patient authority after consolidation | `NEEDS_OWNER_DECISION` | `NATIONAL_IDENTITY_MODEL.md` |
| NI-04 | Canonical IdentityType vocabulary with NIAM↔national aliases | `NEEDS_OWNER_DECISION` | `NATIONAL_IDENTITY_MODEL.md` |
| NI-05 | NIAM-native registry-admin role | `NEEDS_OWNER_DECISION` | `NATIONAL_IDENTITY_MODEL.md` |
| NI-06 | Consolidate matchers into one configurable engine | `NEEDS_OWNER_DECISION` | `NATIONAL_IDENTITY_MODEL.md` |
| NI-07 | Archive/remove dormant plaintext-NID JSON engine | `SECURITY_REVIEW_REQUIRED` | `NATIONAL_IDENTITY_MODEL.md` |
| NI-08 | No government ID-verify gateway assumed | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | `NATIONAL_IDENTITY_MODEL.md` |
| IL-01 | Explicit lifecycle states (provisional/verified/suspended/corrected/deceased) | `LEGAL_REVIEW_REQUIRED` | `IDENTITY_LIFECYCLE.md` |
| IL-02 | Provisional identity never auto-deleted; reconciled via MPI | `OWNER_APPROVED` (D-IDENTITY-03) | `IDENTITY_LIFECYCLE.md` |
| IL-03 | Age transition at 18 with reversal + history | `LEGAL_REVIEW_REQUIRED` | `IDENTITY_LIFECYCLE.md` |
| IL-04 | Death = distinct vital status, not `is_active=False`; no record deletion | `OWNER_APPROVED` (D-IDENTITY-06) | `IDENTITY_LIFECYCLE.md` |
| IL-05 | Merge with claim repointing + unmerge/split | `SECURITY_REVIEW_REQUIRED` | `IDENTITY_LIFECYCLE.md` |
| IL-06 | Fix lifecycle route/service async-sync mismatch before trusting API | `SECURITY_REVIEW_REQUIRED` | `IDENTITY_LIFECYCLE.md` |

### MPI, registration & verification
| ID | Decision | Classification | Source |
|---|---|---|---|
| MPI-01 | MPI as national patient-identity authority after consolidation | `NEEDS_OWNER_DECISION` | `MASTER_PATIENT_INDEX_DESIGN.md` |
| MPI-02 | Hybrid auto-merge + human review + auditable unmerge | `OWNER_APPROVED` (D-IDENTITY-07) | `MASTER_PATIENT_INDEX_DESIGN.md` |
| MPI-03 | Fix claim repointing on merge | `SECURITY_REVIEW_REQUIRED` | `MASTER_PATIENT_INDEX_DESIGN.md` |
| MPI-04 | One configurable matcher; retire 3 scorers | `NEEDS_OWNER_DECISION` | `MASTER_PATIENT_INDEX_DESIGN.md` |
| MPI-05 | Calibrate thresholds on authorized data | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | `MASTER_PATIENT_INDEX_DESIGN.md` |
| MPI-06 | Twins never share NHID; relationships as attributes | `OWNER_APPROVED` (D-IDENTITY-04) | `MASTER_PATIENT_INDEX_DESIGN.md` |
| CR-01 | One registration spine (self + assisted) over MPI/NIAM | `NEEDS_OWNER_DECISION` | `CITIZEN_REGISTRATION_DESIGN.md` |
| CR-02 | Staff never holds citizen credentials | `OWNER_APPROVED` (D-IDENTITY-08) | `CITIZEN_REGISTRATION_DESIGN.md` |
| CR-03 | Provisional identity, no auto-delete, immediate care | `OWNER_APPROVED` (D-IDENTITY-03) | `CITIZEN_REGISTRATION_DESIGN.md` |
| CR-04 | Zero mandatory per-login external cost | `OWNER_APPROVED` (D-IDENTITY-09) | `CITIZEN_REGISTRATION_DESIGN.md` |
| CR-05 | Fix NID hash + raw-NID persistence | `RECOMMENDED` | `CITIZEN_REGISTRATION_DESIGN.md` |
| CR-06 | Citizen-platform in-memory identifiers not an identity source | `SECURITY_REVIEW_REQUIRED` | `CITIZEN_REGISTRATION_DESIGN.md` |
| DV-01 | Preserve OCR/NFC = L0 in VerificationPolicy | `OWNER_APPROVED` (D-IDENTITY-10) | `DOCUMENT_VERIFICATION_DESIGN.md` |
| DV-02 | Gate/remove stub `confidence:1.0` civil connectors | `SECURITY_REVIEW_REQUIRED` | `DOCUMENT_VERIFICATION_DESIGN.md` |
| DV-03 | No assumed government verification API | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | `DOCUMENT_VERIFICATION_DESIGN.md` |
| DV-04 | Fail-closed verification with attribution/audit | `RECOMMENDED` | `DOCUMENT_VERIFICATION_DESIGN.md` |
| DV-05 | Digital-signature verification real or explicitly absent | `RECOMMENDED` | `DOCUMENT_VERIFICATION_DESIGN.md` |

### OCR, API & testing
| ID | Decision | Classification | Source |
|---|---|---|---|
| OCR-01 | `/id-scan` as near-term OCR capability + confidence/quality gates | `RECOMMENDED` | `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` |
| OCR-02 | Do not activate `document_intelligence/` until blockers cleared | `SECURITY_REVIEW_REQUIRED` | `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` |
| OCR-03 | OCR always L0 / needs-confirmation; never proof | `OWNER_APPROVED` (D-IDENTITY-10) | `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` |
| OCR-04 | Calibrate Arabic/Iraqi accuracy on authorized data | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` |
| OCR-05 | Declare/pin OCR deps; self-hosted worker pool | `RECOMMENDED` | `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` |
| OCR-06 | Remove dummy-byte benchmarks; measure real docs | `RECOMMENDED` | `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` |
| API-01 | Remove NID from query strings | `SECURITY_REVIEW_REQUIRED` | `API_AND_INTEGRATION_CONTRACTS.md` |
| API-02 | Versioned, structured-error, idempotent contracts | `RECOMMENDED` | `API_AND_INTEGRATION_CONTRACTS.md` |
| API-03 | Per-operation scopes instead of blanket admin | `RECOMMENDED` | `API_AND_INTEGRATION_CONTRACTS.md` |
| API-04 | No contract treated as E2E evidence | `RECOMMENDED` | `API_AND_INTEGRATION_CONTRACTS.md` |
| API-05 | External verification contracts defined but not activated | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | `API_AND_INTEGRATION_CONTRACTS.md` |
| TST-01 | Contract-envelope tests are not E2E evidence | `RECOMMENDED` | `TESTING_AND_ACCEPTANCE_STRATEGY.md` |
| TST-02 | Regression tests for each verified defect | `RECOMMENDED` | `TESTING_AND_ACCEPTANCE_STRATEGY.md` |
| TST-03 | Synthetic/authorized de-identified data only | `RECOMMENDED` | `TESTING_AND_ACCEPTANCE_STRATEGY.md` |
| TST-04 | Runtime E2E + RPO/RTO before release claim | `NEEDS_OWNER_DECISION` | `TESTING_AND_ACCEPTANCE_STRATEGY.md` |
| TST-05 | Calibrate OCR thresholds on authorized data | `BLOCKED_BY_EXTERNAL_DEPENDENCY` | `TESTING_AND_ACCEPTANCE_STRATEGY.md` |

### Additional workstream registers
`AUTHENTICATION_AND_RECOVERY_DESIGN.md` (auth decisions, incl. `AUTH-REC-01` perm-version fix), `GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md`, `BIRTH_AND_DEATH_LIFECYCLE.md`, `DATABASE_OWNERSHIP_AND_DATA_MODEL.md`, `IRAQI_LEGAL_AND_INSTITUTIONAL_ASSESSMENT.md`, `SECURITY_AND_PRIVACY_THREAT_MODEL.md`, `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md`, `CAPACITY_AND_COST_MODEL.md` each retain their own decision registers; those are authoritative for their scopes and are not duplicated here.

---

## 3. Decision-status summary

- `OWNER_APPROVED` (product design only): D-IDENTITY-01…11, NI-02, IL-02, IL-04, MPI-02, MPI-06, CR-02, CR-03, CR-04, DV-01, OCR-03.
- `NEEDS_OWNER_DECISION`: NI-03/04/05/06, IL (age/authority via legal), MPI-01/04, CR-01, TST-04.
- `LEGAL_REVIEW_REQUIRED`: IL-01, IL-03, plus all statutory/assurance questions in `IRAQI_LEGAL_AND_INSTITUTIONAL_ASSESSMENT.md`.
- `SECURITY_REVIEW_REQUIRED`: NI-07, IL-05/06, MPI-03, CR-06, DV-02, OCR-02, API-01.
- `BLOCKED_BY_EXTERNAL_DEPENDENCY`: NI-08, MPI-05, DV-03, OCR-04, API-05, TST-05.
- `RECOMMENDED`: the remaining engineering recommendations across all documents.

No decision in this study changes `FINAL_DECISION.md` from HOLD, D-020/D-021 status, GECS registries, or authorizes implementation.

---

## 4. Cross-references

`MASTER_ARCHITECTURE.md` §1, §6 · all 22 study documents · `GOVERNANCE/FINAL_DECISION.md` (read-only) · `GOVERNANCE/GECS/GECS_CHECKPOINT.md` (read-only) · `RISKS_AND_OPEN_QUESTIONS.md` · `IMPLEMENTATION_ROADMAP.md`.
