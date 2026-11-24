# GULA National Identity Architecture Study — Identity Lifecycle

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test source exists — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification. No tests run, no DB contacted, no application file modified.

---

## 1. Governing decisions

- **D-IDENTITY-02** — NHID stable, never reused; survives renames/corrections.
- **D-IDENTITY-03** — Provisional identity for undocumented patients; not auto-deleted.
- **D-IDENTITY-05** — Child NHID independent; guardian until 18; history preserved.
- **D-IDENTITY-06** — Healthcare notification/confirmation and civil registration are distinct states; medical records never deleted after death.
- **D-IDENTITY-07** — Auditable merge/unmerge.

Product-design decisions only; no implementation or release-status change authorized.

---

## 2. Current lifecycle source inventory

### 2.1 Lifecycle-related models and statuses — `PARTIAL` / `SOURCE_PRESENT`

| Surface | Evidence | Status |
|---|---|---|
| NIAM `CitizenLifecycle` (identity/lifecycle models) | `backend/app/identity/lifecycle/models.py` — guardian accounts, family links, consent records, death recording; base `IdentityBase` (`env.py:102-103,144`) | `SOURCE_PRESENT`; runtime `UNVERIFIABLE` |
| National citizen deceased fields | `backend/app/national/domain/citizen.py:51-52,86-89` | `SOURCE_PRESENT` |
| NIAM death recording | `backend/app/identity/lifecycle/services.py:494-504` — sets `deceased_at`, `death_certificate_id`, `status="deceased"`, `is_active=False` | `PARTIAL` (route/service mismatch: `routes.py:460-469` await a sync `def` missing `db`) |
| NIAM audit vocabulary | `backend/app/identity/models/audit.py:177-181,218-219` — death, guardianship create/terminate, consent grant/revoke/check/withdraw | `VERIFIED_IN_SOURCE`; actual emission `UNVERIFIABLE` |
| National workflows | `national/workflows/patient_registration.py:41-69`, `death_registration_workflow.py:12-24` — steps marked `SUCCEEDED` without work | `PARTIAL` / safety hazard if mounted |
| Age transition / coming-of-age | Exhaustive grep for `vital_event\|coming_of_age\|age_transition\|transferred_to_adult` under `backend/app` → **zero matches**; only pure predicates `patient.py:54-65`, `minor_protection.py:13-32` | `NOT_IMPLEMENTED` |

### 2.2 Provisional / special-category identities — `SOURCE_PRESENT` / `PARTIAL`

- Models `UnknownPatient`, `Newborn`, `Foreigner`, `Visitor` (`national/domain/`), national `Patient.identity_type` plain string.
- `IdentityService.register_{newborn,foreigner,visitor,unknown_patient}` (`national/services/identity_service.py:15-81`); routes `national/api/routes/identity.py:85-143`, aggregator **unmounted** (`DORMANT`).
- `UnknownPatient.merge_identified()` sets fields only (`unknown_patient.py:45-50`) — no persistence/audit/MPI reconciliation.
- Temporary health numbers returned by `IdentityService` but overwritten by `CitizenService` (see `NATIONAL_IDENTITY_MODEL.md` §3.2).
- **Gaps:** no observed provisional→MPI reconciliation loop.

### 2.3 NIAM account request / lifecycle flows — `SOURCE_PRESENT`

- `/niam` subrouters include account requests, accounts, lifecycle (`identity/api/router.py:41-64`); generated frontend client includes `/niam/lifecycle/citizen/register`, `/issue-health-id`, `/verify-otp`, `/guardians` (`frontend-v3/src/api/generated/client.ts:182-195`).
- Citizen OTP in lifecycle services is a status stub — no code generated/compared (`identity/lifecycle/services.py:391-403`; routes take no code parameter at `routes.py:357,367`). → `NOT_IMPLEMENTED`.
- Guardian routes likely non-functional (async/await vs sync service + missing `db`) — `SECURITY_REVIEW_REQUIRED`.

### 2.4 Dormant / external-gated flows

- National router tree (citizen, family, identity, vital-signs, consent) defined but not mounted (`national/api/routes/__init__.py:20-36`) — all `DORMANT`.
- Civil registry connectors are stubs (`governance/services/connector_service.py:85-123`, `confidence: 1.0`) — `BLOCKED_BY_EXTERNAL_DEPENDENCY`.

---

## 3. Target lifecycle state model (recommendations)

### 3.1 Person/NHID lifecycle

```
PROVISIONAL ──verify──► VERIFIED ──suspend──► SUSPENDED ──restore──► VERIFIED
    │                      │                                          │
    │ (no auto-delete)     ├──correct──► VERIFIED (aliases preserved)  │
    ▼                      └──decease──► DECEASED (history preserved) ─┘
  (reconcile via MPI on verification)
```
- **PROVISIONAL** — created for undocumented patients/offline care; clearly not verified civil identity; eligible for care; never auto-deleted (D-IDENTITY-03). Reconciled via MPI on verification (D-IDENTITY-07).
- **VERIFIED** — identity proofed; NHID issued/linked; stable across corrections; aliases/provenance retained.
- **SUSPENDED** — temporary restriction (e.g. dispute, suspected duplicate); access limited but history preserved.
- **CORRECTION** — a new version with before/after snapshot, reason, evidence, approver; NHID unchanged; alias retained.
- **DECEASED** — distinct from "inactive"; medical records never deleted; NHID never reused (D-IDENTITY-02/06).

### 3.2 Vital status — distinct evidence states (D-IDENTITY-06)

`FAMILY_REPORTED` (notification only) → `HEALTHCARE_NOTIFICATION` → `HEALTHCARE_CONFIRMED` → `CIVIL_REGISTERED` → `VERIFIED_FINAL`. An unverified family report never reaches final status. Corrections/disputes create new evidence records and transitions, never in-place overwrites. See `BIRTH_AND_DEATH_LIFECYCLE.md` §3.

### 3.3 Minor → adult transition (age 18) — `NOT_IMPLEMENTED` (target)

- On reaching majority (owner states 18, subject to law and legally required exceptions), the child's account moves to self-management; guardian delegated permissions are reviewed/revoked/converted; re-consent where consent is the basis; full history preserved; NHID unchanged.
- Transition is an auditable event with before/after permission snapshots and reversal support (e.g. court-ordered extension).
- Job must be idempotent, resumable, controlled-window, rollback-capable. Threshold/exceptions are `LEGAL_REVIEW_REQUIRED`.

### 3.4 Account lifecycle (authentication) — target

- Credential enrollment (WebAuthn/TOTP/recovery) → active → lost-device recovery → revoked/compromised → re-enrolled.
- Device revocation must terminate sessions and blacklist tokens (current gap: `device_service.py:79-85` flag-only).
- All credential changes bump `perm_version` with the correct signature (AUTH-REC-01) and audit.
- See `AUTHENTICATION_AND_RECOVERY_DESIGN.md`.

### 3.5 Merge/unmerge lifecycle (D-IDENTITY-07) — `PARTIAL`

- `Citizen.canonical()` follows `merged_into_id` up to 10 hops (`mpi/models.py:99-112`); MPI manual merge sets `merged_into_id`/`status="merged"` but **does not repoint claims** (`resolver.py:354-400`, explicit comment `:367-369`); no unmerge/split endpoint found.
- Target: automatic merge only under explicit safeguards; human review otherwise; claims repointed atomically; auditable unmerge/split with downstream notification. See `MASTER_PATIENT_INDEX_DESIGN.md`.

---

## 4. Transition governance requirements (all transitions)

| Requirement | Implementation note |
|---|---|
| Authorization | Role-restricted; two-person approval for final death, merge, guardian change, identity correction (target) |
| Evidence | Every transition references a verifiable artifact — never a workflow `SUCCEEDED` marker alone |
| Audit | Hash-chained, attributable, with reason + before/after snapshot (`audit_service.py`, NIAM `niam_audit_entries`) |
| Reversibility | Reversal transition supported with reason/approver; original history preserved |
| Downstream notification | Consumers of identity/vital status notified of corrections/reversals |
| Idempotency | Replaying a transition yields no duplicate effect |
| Offline | No offline device sets a final verification/death/merge state (`OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md`) |

---

## 5. Test requirements (design-level; no tests run here)

| Level | Coverage |
|---|---|
| Unit | Every state transition including invalid ones; NHID stability across correction; no auto-delete of provisional; death ≠ inactive; age-18 boundary. |
| Integration | Provisional→verified with MPI reconciliation; correction with alias preservation; merge with claim repointing; unmerge/split; death notification/confirmation/civil separation; reversal of erroneous death. |
| Security | Two-person approval; unauthorized transition denial; audit completeness; workflow-step regression (no SUCCEEDED without artifact); offline device cannot finalize. |
| Data | NHID never reused; history preserved after death; no raw NID introduced by transitions. |

Synthetic data only.

---

## 6. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages | Legal | Security | Ops/cost | Dependencies | Failure | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| IL-01 | Explicit lifecycle states (provisional/verified/suspended/corrected/deceased) | Fragmented statuses | Single `is_active` flag | Faithful identity semantics | State-machine work | Legal status definitions required | Positive | Moderate | Workstream K | Wrongful state | Reversible | §2, §3.1 | `LEGAL_REVIEW_REQUIRED` |
| IL-02 | Provisional identity never auto-deleted; reconciled via MPI | D-IDENTITY-03 | Auto-delete unresolved | Care continuity | Duplicate growth | Child/provisional duties | Positive | Storage | MPI design | Lost continuity | Reversible | §2.2, §3.1 | `OWNER_APPROVED` (D-IDENTITY-03) |
| IL-03 | Age-transition at 18 with reversal + history preservation | `NOT_IMPLEMENTED` | Manual | Consistent, auditable | Job correctness | Age-of-majority exceptions | Positive | Moderate | Legal decision | Wrongful revocation | Reversible | §2.1, §3.3 | `LEGAL_REVIEW_REQUIRED` |
| IL-04 | Death = distinct vital status, not `is_active=False`; no record deletion | D-IDENTITY-06 | Reuse inactive flag | Correct semantics, no data loss | Migration | Death-registration law | Positive | Low | Workstream I/K | Record loss | Effectively irreversible if deleted | §2.1, §3.1/3.2 | `OWNER_APPROVED` (D-IDENTITY-06) |
| IL-05 | Merge with claim repointing + unmerge/split | MPI merge incomplete | Leave claims orphaned | Correct linkage | Implementation effort | Merge authority | Positive | Moderate | Owner D-IDENTITY-07 | Orphaned claims | Reversible | §2.5, §3.5 | `SECURITY_REVIEW_REQUIRED` |
| IL-06 | Fix lifecycle route/service async-sync mismatch before trusting API | Routes await sync service w/o db | Leave broken | Working API | Test + code change | None | Positive | Low | Executed test | Lifecycle API unusable | Reversible | §2.1/2.3 | `SECURITY_REVIEW_REQUIRED` |

---

## 7. Open questions

1. What are the lawful status definitions and transition authorities for each state (Workstream K)?
2. Is age-of-majority exactly 18, and what exceptions apply (unused `EMANCIPATED_AGE = 16`)?
3. Are the NIAM lifecycle routes actually broken at runtime? (Requires an executed test.)
4. How are provisional records reconciled to MPI, and who approves automatic merges?
5. Which downstream systems consume death/correction status?
6. Should the dormant national router ever be mounted, and only after workflows produce real evidence?

---

## 8. Cross-references

`MASTER_ARCHITECTURE.md` · `NATIONAL_IDENTITY_MODEL.md` · `MASTER_PATIENT_INDEX_DESIGN.md` · `CITIZEN_REGISTRATION_DESIGN.md` · `GUARDIAN_AND_CHILD_IDENTITY_DESIGN.md` · `BIRTH_AND_DEATH_LIFECYCLE.md` · `AUTHENTICATION_AND_RECOVERY_DESIGN.md` · `SECURITY_AND_PRIVACY_THREAT_MODEL.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 1–3, 7–8).
