# GULA National Identity Architecture Study — Offline & Low-Connectivity Design

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.
**Workstream:** N (Offline and Low-Connectivity Operation), inputs from A, D, F, G, H, I, J.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED`, `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification. No tests were run, no database contacted, no application file modified.

**Institutional context (documented, not verified law):** `docs/IRAQ_HEALTH_SYSTEM_RESEARCH_NOTES.md` records a national health system of ~2,765 primary-care centres and 281 general hospitals (older WHO indicators, used with caution), HeRAMS assessment of 5,205 facilities across all governorates and the Kurdistan Region, and work on DHIS2. **Inference:** low-connectivity and low-resource facilities are a realistic operating condition, not a hypothetical. No operational connectivity measurements were verified in this study.

---

## 1. Governing constraints

| Constraint | Source |
|---|---|
| Care must continue without documents; no emergency blocked | D-IDENTITY-03 |
| Assisted registration at facilities; staff never acquire citizen credentials | D-IDENTITY-08 |
| Zero mandatory per-authentication external service cost | D-IDENTITY-09 |
| Arabic-first / RTL, low-cost devices | Program quality requirements; `frontend-v3/index.html:2` `<html lang="ar" dir="rtl">` (`VERIFIED_IN_SOURCE`) |
| **No offline device may make an unsupported final identity-verification decision** | Workstream N (explicit) |
| OCR extraction is not proof of identity or authenticity | D-IDENTITY-10 |
| Healthcare and civil evidence states remain distinct | D-IDENTITY-06 |

---

## 2. Current relevant source surfaces

| Surface | Evidence | Status |
|---|---|---|
| Edge / device integration | `backend/app/routes/edge.py` (`/edge` at `factory.py:650`); `backend/app/health_data/`, device models under canonical `Base` (`device_*` prefixes, 8 classes) | `SOURCE_PRESENT` |
| Offline sync service | `backend/app/services/offline_sync_service.py` (named in repository next-move coverage notes) | `SOURCE_PRESENT` — behavior `UNVERIFIABLE` (no tests run) |
| Facility hierarchy | `backend/app/models/organization.py:8-47` (`organizations`, `facilities`); `parent_org_id` has no FK (`:19`); ADR-B ownership pending | `PARTIAL` |
| Verification-code flow | `backend/app/routes/verification.py:35,106-128` — SHA-256 code in `security_store`, TTL 15 min | `VERIFIED_IN_SOURCE` — online-oriented |
| Citizen OTP | `backend/app/identity/lifecycle/services.py:391-403` — status-only stub, no code generated/compared | `NOT_IMPLEMENTED` |
| National router (would expose national facility/citizen APIs) | `backend/app/national/api/routes/__init__.py:20-36` — **unmounted** | `DORMANT` |
| Hardcoded WebAuthn RP/origin | `shared/auth/webauthn.py:22-24` | `PARTIAL` — blocks multiple origins/domains (A-WEB-01) |
| Workflow stubs | `national/workflows/patient_registration.py:41-69`, `death_registration_workflow.py:12-24` mark steps `SUCCEEDED` without work | `PARTIAL` — safety hazard if activated offline |

**Conclusion:** there is no verified, end-to-end offline identity architecture in source. The design below is a target, not a description of current behavior.

---

## 3. Target offline operating model

### 3.1 Modes

| Mode | Condition | Allowed actions | Forbidden actions |
|---|---|---|---|
| **Online** | Trusted connectivity to GULA | Full registration, authentication, OCR submission, verification workflow, MPI resolution, audit sync | — |
| **Degraded** | Intermittent / high-latency / partial service | Capture and queue with local encryption; view cached provisional identity; queue sync; retry with backoff | Final identity verification, final death status, merge/unmerge, credential recovery |
| **Offline** | No connectivity | Provisional identity creation for care; capture document images + evidence locally; queue encrypted events; emergency break-glass per role with post-review | Final civil-status decisions, government verification, global MPI merge, token issuance requiring central revocation check |

### 3.2 Secure local capture and temporary storage

1. Device must be **enrolled** (device identity, facility binding, operator identity, current credentials).
2. Document images and event payloads are encrypted at rest with a device-local key; keys protected by the device keystore where available.
3. Local retention is **short and bounded** (parameterized; no invented fixed period); data is purged after successful sync or after a configured expiry.
4. Every record carries: device ID, facility ID, operator ID, capture timestamp, idempotency key, and an integrity signature (HMAC) over the payload.
5. Raw national identity numbers are minimized and protected (D-IDENTITY-01); OCR extracts are advisory only (D-IDENTITY-10).

### 3.3 Retry queues and idempotent synchronization

- Durable outbox on the device; events synced with **idempotency keys** so retries cannot create duplicate persons, documents or events.
- **Conflict handling:** server is authoritative for final verification state; client may submit new evidence but cannot overwrite verified status. Last-writer-wins is prohibited for identity/death state.
- **Duplicate submissions:** deduplicate by idempotency key + payload hash; quarantine conflicting duplicates for human review rather than auto-resolving.
- **Interrupted OCR jobs:** persist job state locally; resume from last completed stage; re-upload only missing artifacts; never treat a partial extraction as a final result.
- **Clock skew:** use server-issued timestamps on acceptance; local timestamps are advisory and audited.
- **Sync authentication:** short-lived, scoped sync tokens; no long-lived shared device secret; expire and re-enroll on compromise (D-IDENTITY-09 — no paid per-login service).

### 3.4 Lost / compromised device

1. Remote revoke device enrollment immediately (and invalidate its sessions/tokens — note current gap: `device_service.py:79-85` only flips `is_active`).
2. Purge local encrypted cache remotely where possible; require on-site recovery of the physical device otherwise.
3. Re-enroll with fresh credentials; audit all actions taken with the device since last sync.
4. Quarantine any un-synced events from the lost device for review before acceptance.

### 3.5 Expired credentials

- Sync tokens and session tokens expire normally; re-authentication uses local platform authenticators/TOTP/recovery codes where available (D-IDENTITY-09), or supervised re-login at the facility.
- An offline device must not extend its own authority by resetting expiry locally; time is enforced by the device keystore/secure clock where available and reconciled with server time on reconnection.

### 3.6 Offline patient identity

- A provisional identity may be created offline for care continuity (D-IDENTITY-03); it is clearly marked `PROVISIONAL`, not verified civil identity, and must not be auto-deleted.
- On reconnection, the provisional record enters the MPI duplicate-resolution workflow (D-IDENTITY-07, `MASTER_PATIENT_INDEX_DESIGN.md`) — automatic merging only under explicit safeguards; uncertain matches go to human review.
- Emergency access to an existing record offline uses cached, scoped, time-limited data with break-glass logging and post-review; no offline device may change final identity/death state.

### 3.7 Explicit prohibition

> An offline device may **capture evidence** and **create provisional care identity**, but it must **never** make a final identity-verification, civil-status, death-status, or merge decision. Government-source verification (Workstream G) and civil registration (Workstream I) are online, authority-bound operations.

---

## 4. Security controls (offline-specific)

| Control | Requirement |
|---|---|
| Device enrollment | Unique device identity, facility binding, operator binding, public-key credential |
| Local encryption | At-rest encryption of cache; keystore-backed keys; no plaintext national ID |
| Integrity | HMAC-signed payloads; tamper detection; replay protection via nonce + idempotency key |
| Least privilege | Facility-scoped sync tokens; no global identity authority on device |
| Audit | Every offline action logged locally and reconciled to the central hash chain on sync |
| Retention | Bounded local retention; purge after sync/expiry; legal hold overrides purge |
| Break-glass | Role-restricted, purpose-recorded, post-reviewed (see `SECURITY_AND_PRIVACY_THREAT_MODEL.md`) |
| No credential capture | Staff cannot acquire citizen authentication secrets (D-IDENTITY-08) |

---

## 5. Arabic-first and low-cost device considerations

- Registration and emergency workflows must be Arabic-first/RTL (`frontend-v3/index.html:2`, `i18n/locales.ts:11,20`), with low-bandwidth payloads and progressive rendering.
- Where a platform authenticator is unavailable on a low-cost device, TOTP/recovery codes and assisted paths remain available (D-IDENTITY-09, `AUTHENTICATION_AND_RECOVERY_DESIGN.md` §3.3).
- Document capture must guide the user in Arabic for image quality (see `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md`) without transmitting more data than necessary.

---

## 6. Test requirements (design-level; no tests run in this study)

| Level | Required coverage |
|---|---|
| Unit | Idempotency-key dedup; payload HMAC verification; local retention expiry; conflict classification. |
| Integration | Online→degraded→offline→online transitions; interrupted OCR resume; duplicate submission handling; provisional→MPI workflow on reconnect. |
| Security | Tampered payload rejected; replayed event rejected; compromised-device revoke + cache purge; expired credential cannot extend authority; offline device cannot set final verification/death/merge state. |
| Operational | Lost-device drill; sync after extended outage; clock-skew reconciliation; bounded cache verification. |
| Accessibility | Arabic/RTL flow on low-cost device; no-smartphone assisted path. |

Synthetic data only. Do not claim E2E from contract-envelope tests.

---

## 7. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages / risks | Legal | Security | Ops / cost | Dependencies | Failure scenario | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| OFF-01 | Three-mode operation (online/degraded/offline) with explicit forbidden actions | Facilities with intermittent connectivity | Online-only; full offline authority | Care continuity without over-trust | Mode-transition complexity | None identified | Positive | Moderate | Facility device model | Offline device over-reaches | Reversible | §3.1, §3.7 | `RECOMMENDED` |
| OFF-02 | Encrypted bounded local cache + signed payloads + idempotent outbox | Tamper/duplicate/lost device | Plain local storage | Integrity, dedup, data minimization | Key management on device | Data-protection law (unverified) | Strong positive | Low–moderate | Device keystore | Tampered/duplicate data accepted | Reversible | §3.2-3.3 | `SECURITY_REVIEW_REQUIRED` |
| OFF-03 | No final verification/merge/death decision offline | Workstream N explicit requirement | Allow offline finalization | Prevents unsupported decisions | Delayed finalization | Civil-status authority required | Positive | Low | Workstreams G/I | Wrongful final status | Reversible | §3.7 | `OWNER_APPROVED` (program requirement) |
| OFF-04 | Provisional identity offline, reconciled via MPI on reconnect | D-IDENTITY-03 | Block offline registration | No care blocked | Duplicate growth | Child/provisional rules | Positive | Storage cost | MPI design (Workstream C) | Lost care continuity | Reversible | §3.6 | `OWNER_APPROVED` (D-IDENTITY-03) |
| OFF-05 | Remote device revoke + purge + quarantine on loss | Lost/compromised device | No revocation | Contains breach | Requires connectivity for remote purge | None identified | Positive | Low | Device revocation fix (AUTH-06) | Stolen device data leak | Reversible | §3.4 | `SECURITY_REVIEW_REQUIRED` |

---

## 8. Open questions

1. What is the measured connectivity profile of target facilities? (No verification in this study — assumed intermittent.)
2. What bounded local retention period is acceptable under applicable data-protection law? (`LEGAL_REVIEW_REQUIRED`.)
3. Which device keystore capabilities are available on the lowest-cost supported Android devices?
4. How are offline break-glass events reviewed when connectivity returns days later?
5. Should the existing `offline_sync_service.py` be reused, replaced, or verified first? (Source present, behavior `UNVERIFIABLE`.)

---

## 9. Cross-references

`MASTER_ARCHITECTURE.md` · `CITIZEN_REGISTRATION_DESIGN.md` · `AUTHENTICATION_AND_RECOVERY_DESIGN.md` · `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` · `DOCUMENT_VERIFICATION_DESIGN.md` · `MASTER_PATIENT_INDEX_DESIGN.md` · `BIRTH_AND_DEATH_LIFECYCLE.md` · `SECURITY_AND_PRIVACY_THREAT_MODEL.md` · `CAPACITY_AND_COST_MODEL.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 3, 5, 9, 11).
