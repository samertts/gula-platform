# GULA National Identity Architecture Study — Birth, Death & Vital Events Lifecycle

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.
**Workstream:** I (Birth, Death and Vital Events), inputs from A, B, C, H, K, L.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test source exists — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification. No application file was modified; no test run; no database contacted.

---

## 1. Governing owner decision

**D-IDENTITY-06 — Birth and Death Events.** Support birth registration, birth outside healthcare facilities, newborns without documents, death notifications from authorized healthcare sources, official civil death registration, death outside hospitals, death disputes, incorrect death registration and correction. The owner-approved approach is **BOTH** (1) healthcare-source notification/confirmation **and** (2) official civil registration/confirmation, kept as **distinct evidence and states**. An unverified family report is **not** final proof of death. Medical records are **never deleted** after death.

**D-IDENTITY-03** — provisional identity for newborns / undocumented patients; no emergency care blocked by absence of documents; provisional ≠ verified civil identity; no automatic deletion.

These are product-design decisions only; legal authority and evidence requirements are `LEGAL_REVIEW_REQUIRED` (Workstream K).

---

## 2. Current implementation inventory

### 2.1 Newborn model (persisted) — `VERIFIED_IN_SOURCE`

`backend/app/national/domain/newborn.py:18-62` — `Newborn` → `national_newborns` on `NationalBase` (`backend/app/national/base.py:19`; registered `migrations/env.py:38,42,136`). Fields include:
- birth certificate number; **temporary health number** (provisional-style identifier);
- mother/father FK `national_citizens.id RESTRICT`; `guardian_id` FK `national_guardians.id RESTRICT`; `family_id` FK `national_families.id RESTRICT`;
- `converted_to_citizen_id`, `is_converted` (newborn→citizen conversion, not minor→adult transition);
- `registered_by_hospital`, `registration_days_after_birth`.

**Observation:** this model covers the hospital-birth path with family/guardian linkage. It does not by itself model birth outside a facility, unknown parent, or multiple-birth/twin separation (Workstream H). The temporary health number is a **source-present** provisional identifier, not a verified NHID (Workstream B/C).

### 2.2 Newborn registration services — `PARTIAL` (duplicate implementations)

- `backend/app/governance/services/identity_persistence_service.py:84-115` — `register_newborn` (persisted governance service, `GovernanceBase`).
- `backend/app/services/governance/identity_governance.py:166-199` — **second, in-memory** `register_newborn`.
- `backend/app/national/services/identity_service.py:15-32` — national service referencing the newborn model.

**Observation:** at least two `register_newborn` implementations exist with different persistence semantics. **Inference:** no single authoritative newborn registration path.

### 2.3 Newborn workflow — workflow stub (`VERIFIED_IN_SOURCE`, safety hazard if wired)

`backend/app/national/workflows/patient_registration.py:52-61` — `_handle_newborn_registration()` creates three `WorkflowStep`s (`birth_certificate_verification`, `guardian_assignment`, `temporary_health_number`) and sets each to `SUCCEEDED` **without performing any check or write**. Same pattern for standard (`:41-50`) and foreigner (`:63-69`) paths.

**Inference:** the workflow reports success for verification work it never performs — an identity-safety hazard if this surface is activated. The national API tree that would expose it is currently **unmounted** (§2.7), which limits present exposure but does not remove the defect.

### 2.4 Death model and status — `VERIFIED_IN_SOURCE`

- `backend/app/national/domain/death_record.py:6-44` — `DeathRecord` → `national_death_records` on `NationalBase`. Fields: citizen FK, date, place, cause, ICD-10, unique certificate number, issuer, attending practitioner FK, verification flags, `is_natural_cause`, autopsy fields, family notification fields.
- `backend/app/national/domain/citizen.py:51-52,86-89` — citizen deceased-status fields.
- `backend/app/identity/lifecycle/services.py:494-504` — `record_death()` sets `deceased_at`, `death_certificate_id`, `status="deceased"`, `is_active=False`.
- `backend/app/identity/lifecycle/routes.py:460-469` — `POST /citizen/{citizen_id}/record-death`.

**Route/service mismatch (Inference; runtime `UNVERIFIABLE`):** `:467-468` calls `await svc.record_death(citizen_id, death_date, death_certificate_id)` while `services.py:494` is a synchronous `def` requiring `db: Session` first — the same class of defect as the guardian routes (`GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md` §2.3).

**Observation:** `record_death()` sets `is_active=False` on the account/person. **Inference risk:** conflating "deceased" with "inactive" may obscure the distinct healthcare-confirmation vs civil-registration states required by D-IDENTITY-06, and must not be used to delete or hide medical history.

### 2.5 Death workflow — workflow stub (`VERIFIED_IN_SOURCE`)

`backend/app/national/workflows/death_registration_workflow.py:12-24` marks five steps — `death_verification`, `certificate_issuance`, `citizen_status_update`, `family_notification`, `registrar_approval` — `SUCCEEDED` unconditionally. Same hazard class as §2.3.

### 2.6 External civil-registry connectors — stubs (`VERIFIED_IN_SOURCE`)

`backend/app/governance/services/connector_service.py`:
- `:85-95` `stub_birth_registry` — returns fixed Arabic placeholder names and hard-coded dates.
- `:98-123` `stub_death_registry` — returns hard-coded dates (`2025-01-01`, `2025-06-01`), `confidence: 1.0`, `match: True`.

**Inference:** not a real civil-registry integration; no external verification occurs. The hard-coded `confidence: 1.0` is especially dangerous if mistaken for a verification result (see `DOCUMENT_VERIFICATION_DESIGN.md`: OCR/extraction confidence is not identity proof, and a stub returning perfect confidence must never be treated as evidence).

### 2.7 Unified vital-event model — `NOT_IMPLEMENTED`

- Exhaustive scoped grep for `vital_event|VitalEvent|coming_of_age|age_transition|transferred_to_adult` under `backend/app` → **zero matches**.
- `backend/app/national/domain/vital_signs.py` is **clinical observations** (blood pressure etc.), not civil vital events; `national/api/routes/vital_signs.py:10-11` imports `Observation` + `VitalSignsReference`. These must not be conflated with civil birth/death events.
- `backend/app/national/api/routes/__init__.py:20-36` includes citizen/family/identity/health-card routers but **no vital-events router**.
- The `national_router` at `:20` is **never registered** in `factory.py` (all 91 `include_router` lines inspected) → all national citizen/identity/vital-sign APIs are `DORMANT`.

### 2.8 Broken integration import — `VERIFIED_IN_SOURCE`, `BLOCKED`

`backend/app/integration/identity/__init__.py:1-4` imports `civil_registry`, `biometric`, `digital_identity`, `national_id` modules; `:6-11` exports their classes. **No such files exist** in that directory (only `__init__.py`). **Inference:** importing this package would raise `ModuleNotFoundError`; any integration depending on it is `BLOCKED`. Runtime `UNVERIFIABLE`.

### 2.9 Audit vocabulary — `VERIFIED_IN_SOURCE`

`backend/app/identity/models/audit.py:177` includes `citizen_death_registered`; hash-chained `IdentityAuditEntry` (`:263-303`). Whether lifecycle services emit the action is `UNVERIFIABLE` (no such calls found in lifecycle services).

---

## 3. Target vital-event architecture (recommendations)

### 3.1 Four distinct evidence states (D-IDENTITY-06)

The design must separate, as first-class states with their own evidence and authority:

| State | Meaning | Evidence source | Authority | Final? |
|---|---|---|---|---|
| `HEALTHCARE_NOTIFICATION` | A healthcare source reports an event (birth/death) | Hospital/clinic staff, facility attestation | Healthcare institution | No |
| `HEALTHCARE_CONFIRMED` | Healthcare source confirms with required clinical evidence | Authorized clinician / registrar at facility | Healthcare institution | No (still awaiting civil registration) |
| `CIVIL_REGISTERED` | Official civil registration recorded | Civil registry authority | Government civil registry | Yes for civil status |
| `VERIFIED_FINAL` | Both streams reconciled and consistent | Above two | Platform governance | Yes for platform status |

An **unverified family report** may open a `FAMILY_REPORTED` *notification* state but can never set `CIVIL_REGISTERED` or `VERIFIED_FINAL`. Corrections and disputes create new evidence records and state transitions with full history — never in-place overwrites.

### 3.2 Birth events

- **In facility:** notification + confirmation from the delivering facility; issue provisional/child NHID (D-IDENTITY-03/05); create newborn patient record; record twin/multiple-birth relationships with **separate NHIDs** (D-IDENTITY-04).
- **Outside facility / delayed registration:** notification state; provisional identity; assisted evidence capture; **no final civil status** until official registration. No auto-deletion of provisional records.
- **Unknown parent:** provisional identity with `unknown_parent` evidence state; guardian linkage only when legally established.
- **Document-free newborn:** eligible for care immediately; provisional ≠ verified civil identity.

### 3.3 Death events

- **In hospital:** healthcare notification + confirmation from authorized clinician; distinct from civil death registration.
- **Outside hospital / forensic:** notification state; do not treat as final; route to authorized authority; forensic cases require specialist evidence.
- **Death disputes / incorrect registration:** create a dispute/ correction record; suspend final-status propagation to downstream consumers; preserve prior state; never delete medical records.
- **Reversal of erroneous death status:** supported via auditable transition with reason, evidence, approver, and downstream notification; NHID is **never reused** after death (D-IDENTITY-02).

### 3.4 Data model guidance

- Persist `person_id`/`NHID`, event type, event timestamp, place, evidence references (document/attestation IDs, never raw PII in the event row), reporting source (facility/authority), `state`, `verification_level`, `attested_by`, `registered_by_authority`, `civil_reference`, `dispute_ref`, `correction_of`, `created_at`, `superseded_by`, and full audit.
- Replace `is_active=False` semantics for deceased persons with an explicit `vital_status` and `deceased_at` while preserving the patient record and history.
- Never use workflow-step `SUCCEEDED` markers as evidence of verification (§2.3/§2.5). Each step must produce a real, verifiable artifact or a recorded failure.

### 3.5 External integration prerequisites

Real civil-registry integration is `BLOCKED_BY_EXTERNAL_DEPENDENCY`: it requires a lawful agreement, an authoritative interface, and verified availability. The stubs (§2.6) must remain clearly labeled `STUB` and must not return `confidence: 1.0`. Until a real interface exists, civil registration is recorded from authorized user input with evidence, not queried from a nonexistent government API. Do not assume Iraqi National Identity Card NFC or government API access (Workstreams G/K).

---

## 4. Security, privacy and safety controls

- **Death-status abuse:** changing a person to deceased can deny care and benefits. Controls: two-person approval for final death status, role restriction, immutable audit, dispute/reversal, and alerting on bulk status changes.
- **Birth-record abuse:** false birth registration can create identity fraud vectors. Controls: facility attestation, evidence linkage, separation of notification from civil registration.
- **No emergency blockage:** provisional identity always available (D-IDENTITY-03).
- **Audit:** every event creation, state transition, correction and reversal is hash-chained and attributable (`SECURITY_AND_PRIVACY_THREAT_MODEL.md`).
- **Offline:** an offline facility may capture a notification with evidence and queue it, but cannot set final verified civil status (see `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md`).

---

## 5. Test requirements (design-level; no tests run in this study)

| Level | Required coverage |
|---|---|
| Unit | State machine transitions for all four states; family report cannot reach final; NHID non-reuse after death; no-record-deletion invariant; twin separation. |
| Integration | In-facility and out-of-facility birth; unknown parent; death in/outside hospital; dispute; incorrect-registration correction; reversal of erroneous death status; downstream status propagation. |
| Security | Unauthorized death-status change denied; two-person approval; audit completeness; bulk-change alerting; offline device cannot finalize. |
| Workflow | Each `WorkflowStep` must produce a real artifact — regression test that no step is marked `SUCCEEDED` without evidence (§2.3/§2.5). |
| Integration stub | Assert `stub_birth_registry`/`stub_death_registry` are labeled STUB and never return `confidence: 1.0` as verification (§2.6). |
| Import health | `integration/identity` package import test (currently `BLOCKED`, §2.8). |

Synthetic data only. Do not claim E2E from contract-envelope tests.

---

## 6. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages / risks | Legal | Security | Ops / cost | Dependencies | Failure scenario | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| VIT-01 | Four distinct evidence states (notification / healthcare-confirmed / civil-registered / verified-final) | D-IDENTITY-06 requires separation | Single `is_active`/status flag | Prevents unverified report becoming final; auditable | State-machine complexity | **Legal authority per state required** | Positive | Moderate | Workstream K; owner decision on authorities | False death declared final | Reversible | §2.4, §3.1 | `LEGAL_REVIEW_REQUIRED` |
| VIT-02 | Never delete medical records after death; preserve history | D-IDENTITY-06 | Delete/anonymize | Continuity, medico-legal defensibility | Storage growth | Retention law applies | Positive | Storage cost | Retention policy (`LEGAL_MASTER_PLAN.md`) | Data loss | Effectively irreversible if deleted | §1, §3.3 | `OWNER_APPROVED` (D-IDENTITY-06) |
| VIT-03 | NHID never reused after death | D-IDENTITY-02 | Reuse identifiers | Prevents identity collision | None material | None identified | Positive | Low | NHID service (Workstream B) | Reuse → record collision | Reversible policy change | §3.3 | `OWNER_APPROVED` (D-IDENTITY-02) |
| VIT-04 | Replace workflow-step `SUCCEEDED` stubs with real evidence-producing steps | Workflows falsely report verification | Leave stubs | Safety | Implementation effort | None identified | Positive | Moderate | Owner implementation authorization | False verification if activated | Reversible | §2.3, §2.5 | `SECURITY_REVIEW_REQUIRED` |
| VIT-05 | Real civil-registry integration only after lawful agreement + verified interface | Stubs return fake high-confidence matches | Assume API/NFC availability | Honest capability; no fabrication | External dependency | **Data-sharing agreement required** | Positive | Integration cost | Government authority interface | Wrongful verification | Reversible | §2.6, §3.5 | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| VIT-06 | Consolidate duplicate newborn-registration services | Two implementations with different persistence | Keep both | Single authority | Migration effort | None identified | Positive | Moderate | Owner data-ownership decision | Divergent records | Reversible via migration | §2.2 | `NEEDS_OWNER_DECISION` |
| VIT-07 | Fix death route/service async-sync mismatch before trusting API | Endpoint likely non-functional | Leave as-is | Working API | Test + code change | None identified | Positive | Low | Executed integration test | Death status cannot be recorded | Reversible | §2.4 | `SECURITY_REVIEW_REQUIRED` |

---

## 7. Open questions

1. Which government authority issues civil birth/death registration, and what is the lawful evidence set? (`LEGAL_REVIEW_REQUIRED`.)
2. Who may confirm a death in a healthcare facility, and what two-person approval is required for final status?
3. How are out-of-hospital and forensic deaths routed to the correct authority?
4. Should the temporary health number (`newborn.py`) be promoted to the independent child NHID, or remain a provisional local identifier? (`NEEDS_OWNER_DECISION`, coordinate with Workstreams B/C.)
5. What downstream systems consume deceased status, and how are corrections/reversals propagated?
6. What retention rules apply to vital-event records and medical history after death?

---

## 8. Cross-references

`MASTER_ARCHITECTURE.md` · `NATIONAL_IDENTITY_MODEL.md` · `IDENTITY_LIFECYCLE.md` · `GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md` · `MASTER_PATIENT_INDEX_DESIGN.md` · `IRAQI_LEGAL_AND_INSTITUTIONAL_ASSESSMENT.md` · `DOCUMENT_VERIFICATION_DESIGN.md` (OCR ≠ proof; stub confidence) · `DATABASE_OWNERSHIP_AND_DATA_MODEL.md` · `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 1, 8).
