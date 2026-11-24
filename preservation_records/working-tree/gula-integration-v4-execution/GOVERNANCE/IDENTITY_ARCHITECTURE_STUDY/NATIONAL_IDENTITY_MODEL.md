# GULA National Identity Architecture Study — National Identity Model

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test source exists — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification. No tests run, no DB contacted, no application file modified.

---

## 1. Governing decisions

- **D-IDENTITY-01** — National Identity Number is a protected matching attribute, never a credential.
- **D-IDENTITY-02** — Independent, stable NHID, distinct from civil identity and account identity, never reused.
- **D-IDENTITY-04** — Twins: independent NHIDs; relationships are attributes, not shared identifiers.
- **D-IDENTITY-03** — Provisional healthcare identity; provisional ≠ verified civil identity; no auto-delete.
- **D-IDENTITY-11** — Authentication ≠ patient authorization.

These are product-design decisions only; no implementation or release-status change is authorized.

---

## 2. The five-concept separation (target)

| Concept | Question it answers | Authority | Lifetime | Current source |
|---|---|---|---|---|
| Civil/person identity | Who is this person in the civil registry? | Civil registry (external; not assumed) | Life | `niam_persons`, `national_citizens`, `gov_identity_records` — competing |
| NHID | Which stable health identifier follows this person across facilities? | National health authority (to confirm) | Life, never reused | 5+ formats (§3.2) — `PARTIAL` |
| Account identity | Which credential set operates on the platform? | NIAM accounts + `lab_users` | Revocable | Two login paths — `PARTIAL` |
| Authentication | Is the operator who they claim? | Local auth (zero external cost) | Per session | `shared/auth/` — `PARTIAL` w/ defects |
| Patient authorization | May THIS user see THIS record, for THIS purpose? | Authorization/consent/relationship/guardian | Per access | RBAC/ABAC/consent — `PARTIAL` |

**Inference:** collapsing any two of these (e.g. using the national ID as a password, or treating login as record access) is the root cause of most identity-safety defects found in this study.

---

## 3. Current implementation inventory

### 3.1 Iraqi National Identity Card number (NID) — `PARTIAL` (inconsistent protection)

Verified directly during this study:

| Surface | Behavior | Evidence |
|---|---|---|
| Canonical HMAC helper | Strips non-digits, then HMAC-SHA256 with `NID_HMAC_KEY` (stable across secret rotation) | `backend/app/services/identity.py:213-225` |
| Family-ID helper | HMAC with `fam:` prefix to avoid NID/family hash collisions | `backend/app/services/identity.py:228-241` |
| Self-registration | HMACs the **raw submitted string** (no digit cleanup) into `User.national_id_hash` | `backend/app/routes/register.py:335-343` |
| Governance persistence | Stores the **raw NID** in `documents_json.iraqi_national_id.document_number` while also hashing it | `backend/app/governance/services/identity_persistence_service.py:65-72` |
| Lookup API | `GET /identity/lookup?national_id=` (NID in query string) | `backend/app/routes/identity.py:67`; frontend `src/api/endpoints.ts` `identityApi` |
| Verification gateway | `POST /national-id/verify`; refuses stub gateway in production unless demo mode | `backend/app/routes/national_identity.py:17-34`; factory `:604`; test `test_national_identity_production_guard.py` (3 tests, not executed) |
| Migration key default | `NID_HMAC_KEY = "a"*64` when absent in migration env | `backend/migrations/env.py:18` |

**Confirmed defect (verified):** the canonical helper digit-normalizes before HMAC (`identity.py:222`) but self-registration HMACs the raw string (`register.py:341-343`). The same submitted NID yields **different hashes** across MPI and `User.national_id_hash`, breaking deterministic deduplication/linkage. Additionally, raw NID is persisted in governance `documents_json` (`identity_persistence_service.py:65-72`), undermining the "raw NID never in identity stores" boundary.

**Controls present:** production `NID_HMAC_KEY` required and validated (`backend/app/config.py:215-220,231-233`; `core/startup_guard.py:150-157`).

**Status:** `PARTIAL` — `RECOMMENDED` (single digit-normalized HMAC contract, no raw NID at rest, no NID in URLs/logs).

### 3.2 NHID / health number — `PARTIAL` (five incompatible formats)

Verified format inventory:

| Implementation | Format | Evidence |
|---|---|---|
| Canonical HID helper | `HID-<8hex>-<2 checksum>` | `backend/app/services/identity_matching.py:80-84,105-146` |
| Governance health number | `HN-<8>-<4>-<4>` | `backend/app/governance/services/identity_persistence_service.py:269-272` |
| Governance health-number service | `HN-<12hex>` | `backend/app/governance/services/health_number_service.py:23-36` |
| National citizen health number | `IQ<year><seq:06d>` | `backend/app/national/services/citizen_service.py:74-78` |
| Temporary national numbers | `NB…`, `FR…`, `VS…`, `EM…` | `backend/app/national/services/identity_service.py:20,39,54,70` |
| Dormant prototype | `NH-<uuid8>` | `backend/services/identity_engine/citizens_db.py:20-21` (`DORMANT`) |

**Confirmed defect (verified):** `IdentityService.register_newborn()` computes and returns a temporary number (e.g. `NB…`) but `CitizenService.register_citizen()` **overwrites** `citizen.health_number` with the `IQ…` format (`identity_service.py:15-32` vs `citizen_service.py:22-29,74-78`). The returned temporary number is therefore not the persisted one.

**Missing national requirement:** no single NHID authority, namespace, checksum, issuance registry, or lifecycle. → `RECOMMENDED` (owner D-IDENTITY-02).

### 3.3 Master Patient Index — `VERIFIED_IN_SOURCE`; `PARTIAL` nationally

| Item | Evidence |
|---|---|
| Models `Citizen`→`citizens`, `IdentityClaim`→`identity_claims`, `MergeAudit`→`mpi_merge_audit` | `backend/app/services/mpi/models.py:42-48,115-122,150-158` |
| `Citizen.canonical()` follows `merged_into_id` up to 10 hops | `mpi/models.py:99-112` |
| Routes `/mpi/resolve`, `/citizens/{ulid}`, `/merge`, `/review`, `/review/{claim}/decide`, `/citizens/{ulid}/access` | `mpi/api.py:41,101,142,182,226,313`; prefix `:35`; factory `:617` |
| Fellegi-Sunter weights, NID short-circuit, Jaro-Winkler, thresholds, blocking | `mpi/matcher.py:32-46,108-114,147-154,178-187`; `mpi/blocking.py:29-76` |
| Resolver idempotency `(lab_id, local_patient_id)`, hash-chained audit | `mpi/resolver.py:183-200,93-140` |
| Controls: `get_current_user`, rate limit, lab ABAC, admin-only merge/projection, consent-gated cross-lab read | `mpi/api.py:45,53,55,104-110,145-150,313-318` |
| Static tests | `test_mpi_matcher.py` (35), `test_security_merge_regression_synthetic.py` (8) — not executed |

MPI is the **strongest candidate** for national patient-identity authority but is lab-centric and not the only source of truth. See `MASTER_PATIENT_INDEX_DESIGN.md`.

### 3.4 IdentityType fragmentation — `PARTIAL`

- NIAM `IdentityType`: `citizen`, `government_workforce`, `private_workforce`, `enterprise`, `machine`, `temporary`, `guest`, `external_federation` (`backend/app/identity/models/identity.py:9-17`; model `niam_identities` `:20-21`).
- National `IdentityType`: `IRAQI_CITIZEN`, `NEWBORN`, `FOREIGNER`, `RESIDENT`, `VISITOR`, `UNKNOWN_PATIENT` (`backend/app/national/enums.py:12-18`).
- **Gap:** no canonical/legacy alias map between the two; national patient stores `identity_type` as a plain string (`national/domain/patient.py:47-49`).
- → `NEEDS_OWNER_DECISION`.

### 3.5 NIAM identity platform — `VERIFIED_IN_SOURCE`; `PARTIAL` vs national patient identity

- Router `/niam` with 24 sub-routers (`backend/app/identity/api/router.py:32,41-64`); factory `:819-820`; health `:67-69`.
- Registry guards `require_niam_registry_reader/writer` (`identity/api/access.py:59-75`) **deny any `Account`**, deliberately, until a NIAM registry-admin role exists (`access.py:42-49`). Security-preserving, but leaves no NIAM-native registry administration path → `NEEDS_OWNER_DECISION`.
- Static tests: `test_niam.py` (44), `test_niam_v2.py` (45), `test_niam_professional_registry.py` (12), `test_niam_registry_authorization.py` (14) — not executed.

### 3.6 Duplicate detection — three scoring systems — `PARTIAL`

| System | Evidence |
|---|---|
| MPI matcher (Fellegi-Sunter + Jaro-Winkler) | `mpi/matcher.py:32-46,147-187` |
| LIMS `identity_matching.py` (name .40 / DOB .30 / mother .20 / gov .10) | `backend/app/services/identity_matching.py:151-157,231-321`; queries `Patient`, not MPI `Citizen` (`:270-292`) |
| Health-data MDM (exact/fuzzy/probabilistic; name-only never auto-matches) | `backend/app/health_data/mdm/matching.py:31-325`; safety control `:56-72` |
| Data-platform duplicate check (persists supplied probability; no computation) | `backend/app/services/data_platform_service.py:75-99` |

Thresholds and feature sets differ; no single canonical matcher → `NEEDS_OWNER_DECISION`.

### 3.7 Provisional identities — `SOURCE_PRESENT` / `PARTIAL`

Models: `UnknownPatient`/`national_unknown_patients`, `Newborn`/`national_newborns`, `Foreigner`/`national_foreigners`, `Visitor`/`national_visitors` (`national/domain/{unknown_patient,newborn,foreigner,visitor}.py`), national `Patient.identity_type` (`national/domain/patient.py:47-49`).
Services: `IdentityService.register_{newborn,foreigner,visitor,unknown_patient}` (`national/services/identity_service.py:15-81`). Routes defined at `national/api/routes/identity.py:85-143` but the aggregate `national_router` is **unmounted** (`DORMANT`).
**Gaps:** no observed link from these models to MPI `Citizen` or canonical patient; `UnknownPatient.merge_identified()` only sets fields with no persistence/audit/MPI reconciliation (`unknown_patient.py:45-50`). → `OWNER_APPROVED` (D-IDENTITY-03) for the principle; reconciliation design `RECOMMENDED`.

### 3.8 Governance health-number & raw NID — `PARTIAL`

Models `gov_identity_records`, `gov_health_numbers`, `gov_health_number_audit`, `gov_health_cards`, `gov_merged_identities` (`governance/models/{identity,health_number}.py`); services `identity_persistence_service.py`, `health_number_service.py`. Raw NID in `documents_json` (verified §3.1). Static tests `test_persisted_identity_governance.py` (35), `test_identity_governance.py` (9) — not executed.

### 3.9 Citizen-platform identity (encrypted token / QR / recovery) — `SOURCE_PRESENT` / `PARTIAL`

`backend/app/citizen_platform/identity.py`: `HealthIdentityService` (`:51-86`, encrypted NID token via `encrypt_national_id`), `EmergencyQRService` (`:89-131`, HMAC-signed QR), `IdentityRecoveryService` (`:134-176`).
**Defects (verified in source by inventory; runtime `UNVERIFIABLE`):**
1. QR expiry `created.replace(hour=created.hour + self._qr_expiry_hours)` can overflow when result > 23 (`:100`).
2. QR and recovery stores are process-local dictionaries (`:93`, `:136`) — lost on restart, not shared across workers.
3. Encrypted NID token written into `national_id_hash` field (`:83-85`) — field-name collision with the documented hash semantics (`national/domain/citizen.py:14`).
4. No HTTP endpoints exposing these services found in citizen-platform routes.
Static tests `test_citizen_platform_security.py` (8) — not executed.

### 3.10 Dormant JSON identity engine — `DORMANT`

`backend/services/identity_engine/{citizens_db,citizen_registry,health_identity_engine,test_identity}.py`: JSON file store, **plaintext NID** (`citizen_registry.py:4-18`), unprefixed imports; no FastAPI wiring. → `SECURITY_REVIEW_REQUIRED` (archive/remove or formally mark dormant; no activation).

---

## 4. Target national identity model (recommendations)

### 4.1 Person identity entity (authoritative)
- One registry of person identities with: stable internal ID, verified civil reference (protected), NHID link, aliases/provenance, vital status, verification level, and audit.
- Civil number stored as HMAC (digit-normalized) only; raw value never persisted in identity stores; no NID in URLs/logs.
- IdentityType: one canonical vocabulary with legacy aliases mapping NIAM ↔ national values; NHID stable across renames/corrections.

### 4.2 NHID contract
- Single namespace + checksum + issuance registry + lifecycle (issued → active → suspended → retired/deceased; **never reused**).
- Independent of civil number, account, phone, and guardian (D-IDENTITY-02/03/05).
- Child NHID independent of guardian; twins get separate NHIDs (D-IDENTITY-04/05).
- Temporary/provisional numbers are a **distinct namespace** and must be reconciled on verification — never silently overwritten (§3.2 defect).

### 4.3 Registration → MPI flow (target)
```
Self / assisted capture (D-IDENTITY-08)
   → digit-normalize NID once → HMAC → canonical hash contract
   → MPI resolve (deterministic NID fast path + blocking + probabilistic)
   → AUTO-MERGE only under explicit safeguards (D-IDENTITY-07), else HUMAN REVIEW
   → issue/link NHID
   → account identity created separately (credentials never shared with staff)
```
Assisted registration never gives staff the citizen's credentials (D-IDENTITY-08). Verification codes are channel-ownership only, not login OTP (`AUTHENTICATION_AND_RECOVERY_DESIGN.md` §2.9).

### 4.4 Data minimization and protection
- NID/family ID HMAC-only (one key, rotation-safe); all PHI encrypted at rest (currently partial — `LEGAL_MASTER_PLAN.md:202`); no government API assumed.
- Document OCR extracts advisory and minimized (`DOCUMENT_VERIFICATION_DESIGN.md`).

---

## 5. Test requirements (design-level; no tests run here)

| Level | Coverage |
|---|---|
| Unit | Single NID hash contract (digit-normalized) equality across surfaces; NHID format/checksum; IdentityType alias map; QR expiry boundary; twin/child NHID independence. |
| Integration | Registration→MPI resolve→issue NHID; temporary-number persistence (regression for overwrite defect); HMAC consistency between MPI and `User`; no raw NID in `documents_json` or logs. |
| Security | Raw-NID exposure scan; registry guard behavior; dormant engine remains unactivated; encrypted-token field semantics. |
| Data | No raw NID at rest; NHID never reused; provisional reconciliation. |

Synthetic data only.

---

## 6. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages | Legal | Security | Ops/cost | Dependencies | Failure | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| NI-01 | One digit-normalized HMAC NID contract; no raw NID at rest; no NID in URLs | Inconsistent hashing + raw NID in JSON | Keep per-surface hashing | Deterministic dedup, privacy | Migration of existing hashes | Data-protection law (unverified) | Positive | Low–moderate | Key management | Broken linkage / exposure | Reversible via migration | §3.1 | `RECOMMENDED` |
| NI-02 | One NHID service, namespace, checksum, lifecycle; never reused | 5+ formats; temp overwrite bug | Keep multiple formats | Care continuity | Issuance complexity | NHID mandate to confirm | Positive | Moderate | Owner D-IDENTITY-02 | Misattribution | Reversible via migration | §3.2 | `OWNER_APPROVED` (D-IDENTITY-02) |
| NI-03 | MPI as national patient authority after consolidation | Competing identity stores | Multiple authorities | Single truth | Consolidation effort | Ownership law | Positive | High | Owner decision | Conflicting records | Reversible via migration | §3.3, §3.6 | `NEEDS_OWNER_DECISION` |
| NI-04 | Canonical IdentityType vocabulary with NIAM↔national aliases | Disjoint enums; plain string | Keep both | Interoperability | Mapping effort | None identified | Neutral | Low | Owner decision | Type confusion | Reversible | §3.4 | `NEEDS_OWNER_DECISION` |
| NI-05 | NIAM-native registry-admin role | Guards deny all NIAM principals | Leave deny-all | Native administration | New role definition | None identified | Positive (least privilege) | Low | Role design | No admin path | Reversible | §3.5 | `NEEDS_OWNER_DECISION` |
| NI-06 | Consolidate matchers into one configurable engine | 3 divergent scorers | Keep all | Consistent thresholds | Migration effort | None identified | Positive | Moderate | Owner decision; synthetic calibration | Wrong merges | Reversible | §3.6 | `NEEDS_OWNER_DECISION` |
| NI-07 | Archive/remove dormant plaintext-NID JSON engine | Plaintext NID, unprefixed imports | Activate | Reduces exposure | None material | None identified | Positive | Low | Formal archival decision | NID leak | N/A (removal) | §3.10 | `SECURITY_REVIEW_REQUIRED` |
| NI-08 | No government ID-verify gateway assumed | Stub gateway in prod guard exists | Assume availability | Honest capability | No external verification | Legal agreement required | Positive | Low | Workstream G/K | Unauthorized integration | Reversible | §3.1 | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |

---

## 7. Open questions

1. Which registry is authoritative for civil person identity (NIAM vs national vs governance vs canonical)?
2. Who owns NHID issuance and what is the national namespace/checksum? (`LEGAL_REVIEW_REQUIRED`.)
3. How are existing per-surface NID hashes reconciled to one contract?
4. What is the lawful basis for NID collection/matching and raw-value prohibition? (`LEGAL_REVIEW_REQUIRED`.)
5. Should the national ID verification stub gateway ever be replaced by a real authority interface? (`BLOCKED_BY_EXTERNAL_DEPENDENCY`.)
6. How should provisional identities reconcile to MPI on verification?

---

## 8. Cross-references

`MASTER_ARCHITECTURE.md` · `IDENTITY_LIFECYCLE.md` · `MASTER_PATIENT_INDEX_DESIGN.md` · `CITIZEN_REGISTRATION_DESIGN.md` · `AUTHENTICATION_AND_RECOVERY_DESIGN.md` · `DOCUMENT_VERIFICATION_DESIGN.md` · `DATABASE_OWNERSHIP_AND_DATA_MODEL.md` · `IRAQI_LEGAL_AND_INSTITUTIONAL_ASSESSMENT.md` · `SECURITY_AND_PRIVACY_THREAT_MODEL.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 1–3).
