# GULA National Identity Architecture Study — Master Architecture

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD** (lines 13/361); D-020 and D-021 remain `PENDING_APPROVAL`. This study does not change them.
**Method:** static, read-only source inspection. No application source, model, API, migration, test, config, database, protected repository, commit, push, merge, PR or deployment was touched.

---

## 0. Evidence convention (authoritative for all study documents)

| Label | Meaning |
|---|---|
| `VERIFIED_IN_SOURCE` | Implementation located and read directly in repository source. |
| `TEST_VERIFIED` | A dedicated test module exists targeting the capability. **Test presence is not a claim that the test was executed or passed in this study.** No test was run. |
| `PARTIAL` | Source exists but is incomplete, unwired, defective, or config-gated. |
| `SOURCE_PRESENT` | Code exists but is not on the primary/live path (secondary, stub, or in-memory). |
| `DORMANT` | Source exists with no production caller / router not mounted. |
| `NOT_IMPLEMENTED` | No real implementation; stub or documentation-only. |
| `BLOCKED` | Requires missing configuration/external dependency/authorization to function. |
| `UNVERIFIABLE` | Cannot be confirmed without runtime execution, a database, or external authorization. All runtime behavior and all test outcomes are `UNVERIFIABLE` in this study. |

**Hard rules applied throughout:**
- Source presence is **never** reported as runtime verification. Where a router is registered in `factory.py`, the wording is "routed/wired in source," never "runtime verified."
- A `TEST_VERIFIED` label means test source exists; it is never an execution/pass claim.
- No OCR benchmark, confidence threshold, cost figure, legal conclusion, government API/NFC availability, or production-readiness claim is fabricated.
- Synthetic or legally authorized de-identified data only; no E2E claim is made from contract-envelope tests.
- Every major recommendation is classified with one of: `OWNER_APPROVED`, `RECOMMENDED`, `NEEDS_OWNER_DECISION`, `LEGAL_REVIEW_REQUIRED`, `SECURITY_REVIEW_REQUIRED`, `BLOCKED_BY_EXTERNAL_DEPENDENCY`.

Source paths are relative to repository root. `file:line` references were verified during this study.

---

## 1. Study scope and governing decisions

Eleven owner-approved **product-design decisions** govern this study (they do **not** authorize implementation or change release status):

| ID | Decision |
|---|---|
| D-IDENTITY-01 | National Identity Number is a protected matching attribute, never a password/default credential. |
| D-IDENTITY-02 | Independent, stable NHID distinct from civil identity and account identity; never reused. |
| D-IDENTITY-03 | Provisional healthcare identity for undocumented patients; no emergency care blocked; provisional ≠ verified civil; no auto-delete. |
| D-IDENTITY-04 | Twins have independent NHIDs and records; relationships are attributes, not shared identifiers. |
| D-IDENTITY-05 | Child has independent NHID; guardian manages access until 18 subject to law; multiple/time-bounded guardians; history preserved. |
| D-IDENTITY-06 | Birth/death: healthcare notification/confirmation AND official civil registration kept as distinct evidence/states; unverified family report is not final proof; medical records never deleted. |
| D-IDENTITY-07 | Hybrid duplicate resolution: deterministic auto-merge only under explicit safeguards, human review otherwise, auditable merge/unmerge. |
| D-IDENTITY-08 | Self + assisted registration; staff never acquire citizen authentication credentials. |
| D-IDENTITY-09 | Zero mandatory per-authentication external service cost; no mandatory paid SMS/email OTP. |
| D-IDENTITY-10 | OCR is a core but non-proof capability: Arabic/English, Iraqi documents, quality assessment, field extraction, confidence, human review; extraction is not proof of identity or authenticity. |
| D-IDENTITY-11 | Authentication ≠ patient-record access; every access separately authorized. |

**Preservation constraints:** `FINAL_DECISION.md` HOLD unchanged; D-020/D-021 unchanged; GECS registries unchanged; no implementation change controls; prior D-023/A–O cycle and CC-010 completion program preserved; F-085 and NR-011 `env.py` delta (`+49/-0`) carried, not modified.

---

## 2. Capability map — current source reality

The platform is **mid-unification**: multiple identity sub-systems coexist, with MPI and NIAM the strongest candidates but neither yet the single authority.

| Capability | Best current surface | Status | Primary evidence |
|---|---|---|---|
| Person/civil identity | NIAM `niam_persons` + national `national_citizens` + governance `gov_identity_records` | `PARTIAL` — competing stores | `identity/models/`, `national/domain/citizen.py`, `governance/models/identity.py` |
| NHID / health number | 5+ incompatible formats | `PARTIAL` | `identity_matching.py:80-84` (`HID-`), `identity_persistence_service.py:269-272` (`HN-`), `citizen_service.py:74-78` (`IQ…`), `identity_service.py:20,39,54,70` (`NB/FR/VS/EM`), dormant `NH-` |
| Iraqi National ID protection | HMAC helpers + inconsistent callers | `PARTIAL` | `identity.py:213-225` (digit-normalized HMAC) vs `register.py:341-343` (raw HMAC); raw NID in `documents_json` at `identity_persistence_service.py:65-72` |
| Master Patient Index | `services/mpi/` resolve/review/merge/access | `VERIFIED_IN_SOURCE` / `PARTIAL` nationally | `mpi/api.py:35`, `mpi/matcher.py`, `mpi/resolver.py`, factory `:617` |
| Duplicate detection | 3 scoring systems | `PARTIAL` | MPI matcher, `identity_matching.py`, `health_data/mdm/matching.py` |
| Merge / unmerge | MPI manual merge; no unmerge | `PARTIAL` | `mpi/resolver.py:354-400` (claims not repointed `:367-369`); national merge stub `national/api/routes/identity.py:146-157` |
| Citizen self-registration | `routes/register.py` | `PARTIAL` | MPI minting `:38-108`, NID hashing `:335-343`, fail-closed unless enabled `:114-119` |
| Provisional/unknown/foreigner/visitor | National domain models | `SOURCE_PRESENT` / `PARTIAL` | `national/domain/{unknown_patient,newborn,foreigner,visitor}.py`; routes unmounted |
| Authentication | bcrypt + JWT + MFA + WebAuthn | `PARTIAL` | `shared/auth/`, `routes/login.py`, defects in `AUTHENTICATION_AND_RECOVERY_DESIGN.md` §2 |
| Guardian / child | 4 divergent stores | `NOT_IMPLEMENTED` as one capability | `GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md` §2 |
| Birth / death / vital events | National newborn/death models; workflow stubs | `PARTIAL` / `NOT_IMPLEMENTED` unified | `BIRTH_AND_DEATH_LIFECYCLE.md` §2 |
| Consent | Canonical `consents` + trust + fail-open stub | `PARTIAL` | `models/consent.py`, `security/consent_dep.py` (one usage), `national/security/consent_enforcement.py:16-44` |
| Audit | Canonical hash chain + NIAM hash chain | `PARTIAL` | `services/audit_service.py`, `identity/models/audit.py` |
| Document intelligence / OCR | `document_intelligence/` + `/document-intelligence` routes | `PARTIAL` — see `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` | factory `:793`; `DocIntelBase` unregistered (F-085) |
| Offline / low-connectivity | `offline_sync_service.py`, edge routes | `SOURCE_PRESENT` / behavior `UNVERIFIABLE` | `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md` §2 |

---

## 3. Target logical architecture (recommendations)

### 3.1 Separation of concerns (non-negotiable boundaries)

```
Civil/person identity  ──►  NHID (stable health identifier)  ──►  Patient master record
       │                            │                                  │
       │                            │                                  │
   [verification]             [MPI resolution]                  [facility/tenant scope]
       │                            │                                  │
       └────────────────────────────┴──────────────────────────────────┘
                                     │
Account identity ──► Authentication ──┤──► Patient-record authorization (D-IDENTITY-11)
 (credentials)      (who operates)    │      (who may see WHICH record, WHY)
                                     │
                              Guardian authority (D-IDENTITY-05)
                              Vital events (D-IDENTITY-06)
                              Document/OCR evidence (D-IDENTITY-10, advisory only)
```

**Five distinct concepts must never collapse into one identifier or one decision:**
1. **Civil/person identity** — who the person is in the civil registry.
2. **NHID** — the stable health identifier for care continuity (independent, non-reused).
3. **Account identity** — the credential set that authenticates an operator (citizen, staff, professional).
4. **Authentication** — proving the account holder (local, zero external per-login cost).
5. **Patient authorization** — per-access decision (user, role, facility, relationship, guardian authority, legal basis, purpose, consent, audit).

### 3.2 One authoritative owner per capability (target)

| Capability | Target authority | Current competing sources | Classification |
|---|---|---|---|
| Civil person identity | Single person registry | NIAM `niam_persons`, `national_citizens`, `gov_identity_records`, canonical `patients` | `NEEDS_OWNER_DECISION` |
| NHID | Single NHID service + registry | 5+ formats (§2) | `RECOMMENDED` (D-IDENTITY-02) |
| National ID matching | One HMAC contract (digit-normalized) | raw vs normalized HMAC, encrypted token, raw NID | `RECOMMENDED` |
| Patient master | MPI as national authority | MPI, national, health-data MDM, data-platform MDM, governance, canonical | `NEEDS_OWNER_DECISION` |
| Guardian | One authoritative guardianship entity | 4 stores | `NEEDS_OWNER_DECISION` |
| Vital events | Unified vital-event entity | newborn/death models + stubs | `LEGAL_REVIEW_REQUIRED` |
| Consent | One enforcement authority | canonical, trust, fail-open stub | `NEEDS_OWNER_DECISION` |
| Audit | Reconciled chain(s) | canonical + NIAM | `NEEDS_OWNER_DECISION` |
| Document/OCR | Document-intelligence models | national documents, FHIR DocumentReference | `NEEDS_OWNER_DECISION` + F-085 |

### 3.3 Deployment shape

- **Modular monolith first:** `factory.py` registers 91 routers in one app; scale horizontally before adding services. No new orchestration engine (reuse existing queue/outbox).
- **Separate OCR worker pool:** CPU/GPU-bound, queue-driven; benchmark before engine selection (no engine asserted).
- **HA self-hosted Redis:** revocation store; auth fails closed when unavailable.
- **Single relational cluster** with read replicas for MPI lookup; no sharding before measurement.
- **Self-hosted S3-compatible object storage** for documents; no vendor lock-in; open-source preferred.

---

## 4. Cross-cutting principles

- **Arabic-first / RTL:** `frontend-v3/index.html:2` `<html lang="ar" dir="rtl">` (`VERIFIED_IN_SOURCE`); `i18n/locales.ts:11,20` (`ar` default, `rtl`).
- **Low-connectivity:** three-mode operation; no offline device makes a final verification/merge/death decision (`OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md`).
- **Low external data exposure:** HMAC matching, minimization, all PHI encrypted at rest (currently partial — `LEGAL_MASTER_PLAN.md:202`), no government API assumed.
- **No duplicate engines / no new orchestration engine:** reuse MPI, NIAM, canonical consent/audit, existing outbox/queue.
- **Enterprise preservation:** FHIR R4, multi-tenancy, RBAC/ABAC, immutable audit, offline-first, national deployment compatibility, Arabic-first, ministry/directorate/hospital/lab hierarchy — none removed by this study.

---

## 5. Completion-baseline honesty (carried, not re-verified)

`GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md` records: **0 services E2E/RUNTIME/PRODUCTION verified**; 7 journeys contract-envelope only; RPO/RTO **UNMEASURED**; no production-like snapshot. This study does not improve that status. Every runtime claim here is `UNVERIFIABLE`.

---

## 6. Document index (22-document package)

| # | Document | Workstream | Status |
|---|---|---|---|
| 1 | `MASTER_ARCHITECTURE.md` | Cross-cutting | This document |
| 2 | `EXISTING_CAPABILITY_INVENTORY.md` | A–P | Workstream inventory |
| 3 | `NATIONAL_IDENTITY_MODEL.md` | B | Civil/NHID/account separation |
| 4 | `IDENTITY_LIFECYCLE.md` | B | Lifecycle states & transitions |
| 5 | `MASTER_PATIENT_INDEX_DESIGN.md` | C | Matching, merge/unmerge |
| 6 | `CITIZEN_REGISTRATION_DESIGN.md` | D | Self + assisted registration |
| 7 | `AUTHENTICATION_AND_RECOVERY_DESIGN.md` | E | Login, MFA, recovery |
| 8 | `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` | F | OCR capability + benchmark strategy |
| 9 | `DOCUMENT_VERIFICATION_DESIGN.md` | G | Verification; OCR ≠ proof |
| 10 | `GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md` | H | Child/guardian |
| 11 | `BIRTH_AND_DEATH_LIFECYCLE.md` | I | Vital events |
| 12 | `SECURITY_AND_PRIVACY_THREAT_MODEL.md` | J | STRIDE + controls |
| 13 | `IRAQI_LEGAL_AND_INSTITUTIONAL_ASSESSMENT.md` | K | Legal/institutional |
| 14 | `DATABASE_OWNERSHIP_AND_DATA_MODEL.md` | L | Bases, migrations, ownership |
| 15 | `API_AND_INTEGRATION_CONTRACTS.md` | M | Contract shapes |
| 16 | `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md` | N | Offline operation |
| 17 | `CAPACITY_AND_COST_MODEL.md` | O | Sizing + cost structure |
| 18 | `TESTING_AND_ACCEPTANCE_STRATEGY.md` | P | Test levels |
| 19 | `ARCHITECTURAL_DECISIONS.md` | Cross-cutting | Consolidated ADR register |
| 20 | `RISKS_AND_OPEN_QUESTIONS.md` | Cross-cutting | Risk + owner questions |
| 21 | `IMPLEMENTATION_ROADMAP.md` | Cross-cutting | 12-phase roadmap |
| 22 | `EXECUTIVE_SUMMARY_AR.md` | Cross-cutting | Arabic executive summary |

---

## 7. Cross-references

All documents in `GOVERNANCE/IDENTITY_ARCHITECTURE_STUDY/`. Governing baselines read-only: `GOVERNANCE/FINAL_DECISION.md`, `GOVERNANCE/GECS/GECS_CHECKPOINT.md`, `GOVERNANCE/NATIONAL_HEALTH_PLATFORM_COMPLETION_REPORT.md`, `GOVERNANCE/DATABASE_OWNERSHIP_MATRIX.md`, `reports/LEGAL_MASTER_PLAN.md`, `docs/IRAQ_HEALTH_SYSTEM_RESEARCH_NOTES.md`.
