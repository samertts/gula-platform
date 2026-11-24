# GULA National Identity Architecture Study — Guardian & Child Identity Design

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.
**Workstream:** H (Child and Guardian Management), inputs from A, B, J, L, P.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0 and `AUTHENTICATION_AND_RECOVERY_DESIGN.md` §0 for the full label table. Summary: `VERIFIED_IN_SOURCE` (source read directly), `TEST_VERIFIED` (dedicated test source exists — **not executed in this study**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never treated as runtime verification. No application file was modified and no test was run.

---

## 1. Governing owner decisions

| Decision | Constraint applied |
|---|---|
| D-IDENTITY-05 | Child has an independent NHID; guardian manages account/healthcare-access permissions until 18 **subject to Iraqi law and legally required exceptions**; support father, mother, legally appointed guardians, multiple guardians where legally supported, differing permission levels, guardian changes/revocation, custody disputes, transition to independent management at 18, and preservation of the complete medical history. Child must not depend on guardian's NHID. |
| D-IDENTITY-03 | Provisional healthcare identity for newborns/children without documents; absence of documents must never block emergency care; provisional ≠ verified civil identity; do not auto-delete provisional records. |
| D-IDENTITY-04 | Each twin has an independent NHID and patient record; explicit twin/family relationships without shared identifiers. |
| D-IDENTITY-11 | Authentication ≠ patient authorization; biological parenthood does not automatically grant every legal or clinical permission. |

These are product-design decisions only; they do not authorize implementation or change release status. Guardian *legal* authority is `LEGAL_REVIEW_REQUIRED` (Workstream K).

---

## 2. Current implementation inventory

### 2.1 Canonical patient-level guardian fields — `VERIFIED_IN_SOURCE`

`backend/app/models/patient.py`:
- `:17-18` `class Patient(Base)`, table `patients`; canonical `Base` at `backend/app/database.py:273`, registered in `migrations/env.py:22,135`.
- `:30-32` `family_id_hash` — HMAC-SHA256 with `fam:` prefix; raw civil family number not persisted (positive privacy control).
- `:33-36` `guardian_id` — self-FK `patients.id ON DELETE SET NULL`, nullable, indexed.
- `:46-52` `dependents` relationship via `backref("guardian", remote_side=[id])`, `lazy="dynamic"`.
- `:54-65` `is_minor` property — computed from `birth_date`, threshold `< 18` (pure predicate; no persistence, no enforcement).

API `backend/app/routes/patients.py`:
- `:200` writes `guardian_id` on patient create/update.
- `:210-226` `GET /patients/family/{family_id}`.
- `:229-245` `GET /patients/{patient_id}/children`.

Service delegation: `backend/app/services/patient_service.py:304-319`. The `patients` router is in the mounted `core_routes` loop (`factory.py:579`).

**Observation:** a single `guardian_id` cannot represent dual legal guardianship, time-bounded guardianship, delegatedpermissions, or custody disputes. **Inference:** the canonical patient model alone cannot satisfy D-IDENTITY-05.

### 2.2 National guardian rule engine — `SOURCE_PRESENT` / `DORMANT`

`backend/app/national/security/guardian_rules.py`:
- `:6-13` `GuardianRule` flags: `can_consent`, `can_access_records`, `can_make_appointments`, `can_receive_results`, `can_authorize_treatment`, `restrictions`.
- `:16-29` `GuardianRulesService.get_guardian_rules()` — `parent`/`legal_guardian` unrestricted; `grandparent` loses result receipt; `sibling` loses treatment authorization at age ≥16; unknown types lose consent + treatment authorization (deny-by-default).
- `:31-40` `validate_guardian_action()` maps action names to flags; unknown action → `False`.

`backend/app/national/security/minor_protection.py`:
- `:13-15` `MINOR_AGE = 18`, `EMANCIPATED_AGE = 16`; `:17-22` `is_minor()`; `:24-29` `get_protection_level()`; `:31-32` `requires_guardian()`.
- **Observation:** `EMANCIPATED_AGE = 16` is declared but never used; `get_protection_level` keys off a caller-supplied `is_emancipated` boolean, not the constant.

**Status:** high-reuse pure service (no DB/framework dependency), but it lives under `app/national/`, whose router tree is **unmounted** (§2.7). No dedicated test module was located; governance records (`AUTONOMOUS_ENGINES_INVENTORY.md:103`, `NATIONAL_CAPABILITY_REGISTRY.md:89`) classify it `SOURCE_PRESENT` with "no dedicated test module located." Reachability `UNVERIFIABLE`.

### 2.3 NIAM guardian accounts (persisted) — `VERIFIED_IN_SOURCE`, runtime `UNVERIFIABLE`

**Model** `backend/app/identity/lifecycle/models.py`:
- `:130-147` `GuardianAccount` → `niam_lifecycle_guardians`: `guardian_person_id` and `dependent_person_id` both FK `niam_persons.id ON DELETE CASCADE`; `relationship`, `guardian_type`, `start_date`, `end_date`, `delegated_access` (JSON), `consent_inheritance`, `status`, `verified_by`, `verified_at`, `documents`, `is_active`.
- `:150-160` `FamilyLink` → `niam_lifecycle_family_links`; `:163-177` `ConsentRecord` → `niam_lifecycle_consents`.
- Base `IdentityBase` at `backend/app/identity/base.py:12`; imported at `migrations/env.py:102-103`, registered `:144`.
- **Caveat:** `env.py:103` imports `app.identity.models`; transitive import of `identity/lifecycle/models.py` was not verified → autogenerate visibility of `niam_lifecycle_*` is `UNVERIFIABLE`.

**Service** `backend/app/identity/lifecycle/services.py`:
- `:422-442` `CitizenService.link_guardian()` (sync, `db: Session`).
- `:520-540` `GuardianService.create_guardianship()`; `:542-548` `terminate_guardianship()`; `:550-554` `get_dependents()`; `:556-560` `get_guardians()`; `:562-569` `delegate_access()`; `:571-576` `verify_guardianship()`; `:578-584` `_get_guardian()`. All synchronous `def` requiring `db`.

**Routes** `backend/app/identity/lifecycle/routes.py`:
- `:485-502` `POST /guardians`; `:505-512` `GET /guardians/dependents/{guardian_person_id}`; `:515-522` `GET /guardians/guardians/{dependent_person_id}`; `:525-533` `POST /guardians/{guardian_id}/terminate`; `:536-544` `POST /guardians/{guardian_id}/delegate-access`; `:547-555` `POST /guardians/{guardian_id}/verify`.
- Also `:399` `POST /citizen/{citizen_id}/link-guardian`.
- Mounted: `identity/api/router.py:56` includes the lifecycle router; `factory.py:820` includes `get_niam_router()` under `/niam` → **the NIAM router tree is mounted** (`VERIFIED_IN_SOURCE`).

**Confirmed source mismatch (Inference; runtime `UNVERIFIABLE`):**
- `routes.py:486-554` handlers are `async def` and call `await svc.<method>(...)` with **no `db` argument**; services are synchronous `def` requiring `(self, db: Session, ...)`. Routes depend on `db: AsyncSession = Depends(get_db)` while services annotate `Session`. **Inference:** every guardian endpoint would fail on invocation (`TypeError` for missing `db`; and/or awaiting a non-awaitable `Session`). No request was issued, so this remains a source-level finding, not a runtime-verified failure.

**Frontend mismatch (documented in `GOVERNANCE/FRONTEND_INTEGRATION_REPORT.md:164`):** frontend pages call `GET` where the backend guardian endpoint is `POST` (`/niam/lifecycle/guardians`). Client/server mismatch carried to `RISKS_AND_OPEN_QUESTIONS.md`.

### 2.4 Second guardian store — in-memory — `VERIFIED_IN_SOURCE`

`backend/app/citizen_platform/family.py`:
- `:70-113` `GuardianService` with `_guardians: dict[str, list[dict]]` — `assign_guardian()`, `remove_guardian()`, `get_guardians()`, `is_guardian()`.
- `:27-68` `FamilyAccountService`; `:116-166` `ConsentManager` (same in-memory pattern; `check_consent()` at `:149-158` checks `status == "active"` only, no expiry).
- Wiring: `citizen_platform/integration.py:94,120-145`; router mounted at `factory.py:769-770`. Exposed routes are only `GET /family/{citizen_id}` (`citizen_platform/routes.py:362-365`) and `GET /consents/{citizen_id}` (`:450-454`) — no guardian assignment/removal endpoint found.
- **Observation:** process-local state, lost on restart, not shared across workers. **Inference:** cannot be authoritative for a national platform.

### 2.5 Third and fourth guardian persistence — `VERIFIED_IN_SOURCE`

- `backend/app/governance/models/citizen_platform.py:36-47` — `GuardianRecord` → `gov_guardians`, `GovernanceBase`, registered `env.py:48,96,142`; repository `governance/repositories/citizen_platform_repositories.py:70-74`; persistence `governance/services/citizen_platform_persistence.py:136-199`.
- `backend/app/national/domain/guardian.py:8-35` — `Guardian` → `national_guardians`, `NationalBase`, includes `guardian_type`, `is_legal_guardian`; unmounted national tree.

### 2.6 Unified capability verdict

**Guardian management is `NOT_IMPLEMENTED` as a single authoritative capability.** Four divergent stores exist (canonical patient FK, NIAM persisted accounts, in-memory citizen service, governance/national models) with no reconciling ownership, no tested integration, and a likely route/service defect in the only mounted guardian API.

### 2.7 Organization hierarchy context — `PARTIAL`

- `backend/app/models/organization.py:8,11-29` — `Organization` → `organizations`, canonical `Base`; bilingual names `:16-17`; `org_type`; `parent_org_id` (`:19`, plain `String(100)` with index, **no FK constraint**); `tenant_id`, `governorate_id`, `directorate_id`.
- `:32-47` `Facility` → `facilities`, `organization_id` FK `ON DELETE CASCADE`.
- Ministry seed `backend/app/core/bootstrap/ministry.py:16` `MINISTRY_ORG_ID = "org-iraq-moh"`, `:19-48`; directorates `core/bootstrap/directorates.py:40-55`.
- **Observation:** hierarchy integrity is not DB-enforced; inference: orphaned or cyclic trees are possible. `facilities` ownership is flagged unresolved in `GOVERNANCE/DATABASE_OWNERSHIP_MATRIX.md:45`.

### 2.8 Audit vocabulary — `VERIFIED_IN_SOURCE`

`backend/app/identity/models/audit.py`: `:177` `citizen_death_registered`; `:178-179` `guardianship_created`/`guardianship_terminated`; `:180-181` `consent_granted`/`consent_revoked`; `:218-219` `consent_checked`/`consent_withdrawn`. `IdentityAuditEntry` → `niam_audit_entries` with `entry_hash` unique and `previous_hash` (`:263-303`).
**Observation:** the vocabulary anticipates the required events; **Inference:** whether lifecycle services actually emit them is `UNVERIFIABLE` — no such calls were found in `identity/lifecycle/services.py:422-584`.

---

## 3. Target child-identity model (recommendations)

### 3.1 Identity separation (D-IDENTITY-02/04/05)

1. **Person identity** (civil/person registry) is distinct from **NHID** (stable health identifier), **account identity** (credentials), and **patient authorization** (D-IDENTITY-11).
2. A child receives an **independent NHID at birth registration or provisional registration**, not derived from a guardian's NHID or any phone number.
3. Twins receive **separate NHIDs and separate patient records**; a `twin_group_id`/multiple-birth linkage is a *relationship attribute*, never a shared identifier (D-IDENTITY-04).
4. Guardian relationship is a **separate, time-bounded, evidence-backed relation** between two person identities — not a column that redefines the child's identity.

### 3.2 Guardianship record (target shape)

A single authoritative guardianship entity must carry, at minimum:

| Field | Purpose |
|---|---|
| `guardian_person_id`, `child_person_id` | Both reference independent person/NHID identities (FK to person registry, not to patient accounts) |
| `guardian_type` | mother, father, legally appointed guardian, other legally recognized (enumerated; not free text) |
| `relationship_evidence_ref` | Reference to verified document/court order (no raw document stored in this table) |
| `scope` / permission set | Which permissions are delegated (see §4) |
| `start_date`, `end_date` | Time-bounded authority; `end_date` nullable for ongoing |
| `verification_status`, `verified_by`, `verified_at` | Evidence verification state (distinct from document OCR — see `DOCUMENT_VERIFICATION_DESIGN.md`) |
| `custody_case_ref` | Optional link to a custody/dispute record |
| `status`, `is_active` | Active / suspended / revoked / superseded |
| `revoked_at`, `revoked_by`, `revocation_reason` | Auditable revocation |

**Owner decision required:** whether guardianship for a given `guardian_type` is self-asserted, document-verified, or authority-verified. This is `LEGAL_REVIEW_REQUIRED` (Workstream K).

### 3.3 Reuse decision

The NIAM `niam_lifecycle_guardians` table (§2.3) is the **best structural starting point** because it already models multiple guardians, time bounds, delegated access, verification, and documents. The canonical `patients.guardian_id` should be retained as a **denormalized convenience pointer** (single "primary guardian" for display), not the authority. Consolidation of the four stores is `NEEDS_OWNER_DECISION` (data ownership), and any migration is outside this study.

### 3.4 Age transition at 18 — `NOT_IMPLEMENTED` (target design)

No `vital_event`, coming-of-age, age-transition, guardian-termination-on-majority, or re-consent logic exists anywhere under `backend/app` (exhaustive scoped grep returned zero matches). Only pure predicates exist (`patient.py:54-65`, `minor_protection.py:13-32`).

Target behavior:
1. On reaching the legally defined age of majority (owner states 18, subject to Iraqi law and legally required exceptions), the child's account transitions to self-management.
2. Guardian delegated permissions are **reviewed and revoked or converted**; the child is re-consented where consent is the legal basis.
3. The complete medical history is preserved and remains linked to the same NHID.
4. Transition is an auditable event with before/after permission snapshots; reversal (e.g. court-ordered extension of guardianship) is supported.
5. A transition job must be idempotent, resumable, and run in a controlled window with rollback capability.

Implementation of the job is **not** authorized by this study.

---

## 4. Guardian permission matrix (target)

Deny by default. Biological relationship alone does not grant every permission (D-IDENTITY-11). `R` = permitted, `L` = permitted only with a legally verified guardian record, `—` = not permitted, `H` = human review required.

| Action on child | Mother (verified) | Father (verified) | Legally appointed guardian | Other authorized adult (delegated) | Unverified claimant | Notes |
|---|---|---|---|---|---|---|
| View child's demographic summary | R | R | L | L (scoped) | — | Purpose + audit required (D-IDENTITY-11) |
| View laboratory results | R | R | L | L (scoped) | — | Sensitive-result policy may further restrict |
| Receive critical-result notification | R | R | L | L (scoped) | — | Emergency exception logged |
| Book / manage appointments | R | R | L | L (scoped) | — | |
| Consent to routine care | R | R | L | — | — | Legal basis must be recorded |
| Authorize treatment / procedures | L | L | L | H | — | Highest-risk permission |
| Access mental-health / reproductive records | H | H | H | — | — | `LEGAL_REVIEW_REQUIRED`; may require adolescent-confidentiality rules |
| Export/download full medical record | H | H | H | — | — | Data-portability + privacy review |
| Manage child's authentication credentials | R | R | L | — | — | Never share the child's secret with staff (D-IDENTITY-08) |
| Change child's NHID / identity data | — | — | — | — | — | Identity corrections require separate verified process (Workstream B) |
| Add/remove another guardian | H | H | H | — | — | Separation of duties; two-person approval |
| Child's own access after age 18 | R (self) | R (self) | — | — | — | Guardian access revoked/reviewed (§3.4) |
| Emergency access (unconscious child, guardian absent) | H | H | H | H | H | Break-glass, role-restricted, audit + post-review |

**Source alignment:** the target matrix generalizes the existing `GuardianRulesService` flags (`can_consent`, `can_access_records`, `can_make_appointments`, `can_receive_results`, `can_authorize_treatment`, `restrictions` — §2.2) and its deny-by-default behavior, while adding time bounds, delegation, verified evidence, and auditable review. The existing service's `EMANCIPATED_AGE = 16` constant is unused; the age threshold must be resolved by legal review rather than silently defaulting.

---

## 5. Guardian abuse and safety controls (input to threat model)

- **Guardian abuse:** a verified guardian can still misuse access. Controls: purpose-of-access recording, least-privilege scopes, time-bounded delegations, anomalous-access alerting, and a child/second-guardian dispute channel that can suspend guardian access pending review.
- **Custody disputes:** guardianship records support multiple concurrent guardians with per-scope authority and a `custody_case_ref`; a dispute suspends contested permissions without deleting history.
- **Emergency access:** never blocked by a custody dispute; break-glass is role-restricted, audited, and post-reviewed.
- **Death of guardian:** dependent's access is not deleted; guardianship ends by `end_date`/revocation with audit, and an alternative guardian may be appointed (Workstream I).
- **Offline:** an offline device may capture relationship evidence but must not make a final guardianship-verification decision (see `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md`).

---

## 6. Test requirements (design-level; no tests run in this study)

| Level | Required coverage |
|---|---|
| Unit | `GuardianRulesService` all guardian types and actions; unknown type/action deny-by-default; `is_minor` boundary at 18; `EMANCIPATED_AGE` usage decision; permission-matrix evaluation for every cell in §4. |
| Integration | NIAM guardian route↔service invocation (the async/sync + missing-`db` mismatch must be proven or disproven by an executed test); creation/termination/delegation/verification round-trips; audit emission for each guardianship event. |
| Identity | Twin separation (two NHIDs, no shared identifiers); newborn provisional identity; child NHID independent of guardian; age-transition at 18 with history preservation and reversal. |
| Security | Guardian-abuse scenarios; custody dispute suspension; unverified-claimant denial; break-glass logging; purpose-of-access enforcement; no credential capture during assisted enrollment. |
| Data | Reconciliation of the four guardian stores (§2); confirm `niam_lifecycle_*` appears in Alembic autogenerate; no raw civil family number persisted. |
| Cross-platform/frontend | Align frontend `GET`/`POST` method with backend `/niam/lifecycle/guardians` (`FRONTEND_INTEGRATION_REPORT.md:164`). |

Synthetic data only. Do not claim E2E from contract-envelope tests (`TESTING_AND_ACCEPTANCE_STRATEGY.md`).

---

## 7. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages / risks | Legal | Security | Ops / cost | Dependencies | Failure scenario | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CH-01 | One authoritative guardianship entity (NIAM `niam_lifecycle_guardians` as base), canonical patient FK as denormalized pointer | Four divergent stores, no authority | Keep patient FK only; keep in-memory service | Multiple/time-bounded guardians; clear ownership | Consolidation/migration effort | Guardian law must define who may be a guardian | Positive (single control point) | Migration cost | Owner decision on data ownership; env.py metadata visibility fix | Conflicting guardianship state persists | Reversible via migration | §2.1-2.6 | `NEEDS_OWNER_DECISION` |
| CH-02 | Independent child NHID; twin separation | D-IDENTITY-02/04/05 | Derive from guardian; share twin identity | Stable, private, no misattribution | Registration complexity | None identified | Reduces sample/result misattribution | Low | Workstream B/C design | Twin/lab misattribution | Reversible | §3.1 | `OWNER_APPROVED` (D-IDENTITY-02/04/05) |
| CH-03 | Deny-by-default permission matrix with verified evidence + time bounds | Biological relation ≠ permission | All permissions to any claimed guardian | Least privilege; abuse resistance | Usability friction | **Requires legal definitions of guardian authority** | Positive | Moderate | Guardian verification process | Unauthorized access or care delay | Reversible | §2.2, §4 | `LEGAL_REVIEW_REQUIRED` |
| CH-04 | Age-transition job at 18 with auditable revocation/reversal | Coming-of-age `NOT_IMPLEMENTED` | Manual process; no transition | Consistent, preserve history | Job correctness risk | Age-of-majority exceptions require legal ruling | Positive | Moderate | Legal decision on threshold/exceptions | Wrongful revocation of access | Reversible | §3.4 | `LEGAL_REVIEW_REQUIRED` |
| CH-05 | Fix NIAM guardian route/service async-sync mismatch before trusting any guardian API | Endpoints likely non-functional | Leave as-is | Working API | Test + code change (implementation out of scope) | None identified | Positive | Low | Executed integration test | Guardian API unusable | Reversible | §2.3 | `SECURITY_REVIEW_REQUIRED` |
| CH-06 | Preserve provisional child identity; no auto-delete | D-IDENTITY-03 | Delete unresolved records | Care continuity | Duplicate growth | Child-protection duties | Positive | Storage cost | MPI design (Workstream C) | Lost care continuity | Reversible | D-IDENTITY-03 | `OWNER_APPROVED` (D-IDENTITY-03) |

---

## 8. Open questions

1. Which authority verifies guardianship, and what evidence is sufficient? (`LEGAL_REVIEW_REQUIRED`.)
2. Is the age-of-majority threshold exactly 18 for all cases, and what are the legally required exceptions (emancipation, court orders)? (`LEGAL_REVIEW_REQUIRED`; note unused `EMANCIPATED_AGE = 16`.)
3. Are the NIAM guardian routes actually broken at runtime? Requires an executed integration test (§2.3).
4. Which of the four guardian stores is authoritative, and how are existing records reconciled? (`NEEDS_OWNER_DECISION`, CH-01.)
5. Should `facilities`/`organizations`/`national_facilities` ownership (ADR-B pending) be resolved before guardian-facility scoping is trusted?
6. How should adolescent-confidentiality and reproductive/mental-health access be handled (§4)?

---

## 9. Cross-references

`MASTER_ARCHITECTURE.md` · `NATIONAL_IDENTITY_MODEL.md` · `IDENTITY_LIFECYCLE.md` · `BIRTH_AND_DEATH_LIFECYCLE.md` · `MASTER_PATIENT_INDEX_DESIGN.md` (twins, provisional records, merge safety) · `SECURITY_AND_PRIVACY_THREAT_MODEL.md` (guardian abuse) · `DATABASE_OWNERSHIP_AND_DATA_MODEL.md` (bases, F-085, ADR-B) · `IRAQI_LEGAL_AND_INSTITUTIONAL_ASSESSMENT.md` · `API_AND_INTEGRATION_CONTRACTS.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 7, 8).
