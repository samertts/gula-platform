# GULA National Identity Architecture Study — Citizen Registration Design

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test **source exists** — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification; no tests run, no DB contacted, no application file modified.

---

## 1. Governing decisions

- **D-IDENTITY-08** — Self + assisted registration; staff never acquire citizen authentication credentials.
- **D-IDENTITY-03** — Provisional healthcare identity for undocumented patients; no emergency care blocked; provisional ≠ verified; no auto-delete.
- **D-IDENTITY-05** — Child NHID independent of guardian; guardian manages until 18; history preserved.
- **D-IDENTITY-02** — Independent, stable NHID, never reused.
- **D-IDENTITY-09** — Zero mandatory per-authentication external service cost (no paid SMS/email OTP).
- **D-IDENTITY-10** — OCR extraction is advisory, non-proof.
- **D-IDENTITY-11** — Authentication ≠ patient-record access.

Product-design decisions only; no implementation authorized.

---

## 2. Current registration source inventory (verified directly)

| Surface | Path | Status | Verified detail |
|---|---|---|---|
| Self-registration | `backend/app/routes/register.py` | `PARTIAL` | MPI minting `:38-108`; raw-string NID HMAC `:335-343`; duplicate email/NID checks `:330-349`; **fail-closed unless feature enabled** `:114-119` |
| NIAM citizen register flow | `identity/api/router.py:41-64`; generated client `client.ts:182-195` (`/niam/lifecycle/citizen/register`, `/issue-health-id`, `/verify-otp`, `/guardians`) | `PARTIAL` | OTP is a **status stub** — no code generated/compared (`identity/lifecycle/services.py:391-403`; routes take no code param `routes.py:357,367`) |
| Provisional / special categories | `national/domain/{unknown_patient,newborn,foreigner,visitor}.py`; `national/services/identity_service.py:15-81`; routes `national/api/routes/identity.py:85-143` | `SOURCE_PRESENT` / `DORMANT` | aggregator unmounted; `UnknownPatient.merge_identified()` sets fields only (`:45-50`); temp number returned then overwritten (`identity_service.py:15-32` vs `citizen_service.py:74-78`) |
| Citizen identity token/QR/recovery | `backend/app/citizen_platform/identity.py:51-176` | `SOURCE_PRESENT` / `PARTIAL` | encrypted NID token, HMAC QR, recovery; no HTTP endpoints found; process-local stores (`:93,136`); QR hour overflow (`:100`); token in `national_id_hash` field (`:83-85`) |
| Assisted registration | no dedicated staff-assisted flow found | `NOT_IMPLEMENTED` | — |
| NID verification | `routes/national_identity.py:17-34` (stub gateway, fail-closed in prod) | `PARTIAL` / `BLOCKED` | no real authority (`DOCUMENT_VERIFICATION_DESIGN.md` §2.2) |
| OCR-assisted capture | `routes/id_scan.py` (wired, `needs_confirmation`) | `PARTIAL` | advisory only (`OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` §2.1) |

**Verified defect cluster:** registration is fragmented across self/NIAM/national/citizen-platform paths; NID hashing is inconsistent (canonical digit-normalized vs raw-string at `register.py:341-343`); raw NID persisted in governance `documents_json` (`identity_persistence_service.py:65-72`); NHID temp numbers overwritten; citizen-platform identifiers are in-memory and field-misnamed.

---

## 3. Target registration design (recommendations)

### 3.1 Two enrollment paths, one identity spine

```
SELF (D-IDENTITY-08)                    ASSISTED (staff, D-IDENTITY-08)
  local credential enrollment            staff captures citizen data + optional OCR
  (WebAuthn/TOTP, zero external cost)      → citizen verifies channel ownership
  → capture identity attributes            → staff NEVER receives citizen credentials
  → optional OCR assist (non-proof)        → human confirmation of extracted fields
           │                                        │
           └──────────► normalize NID once (digit-normalized HMAC)
                        → MPI resolve (see MASTER_PATIENT_INDEX_DESIGN)
                        → issue/link single NHID (D-IDENTITY-02)
                        → provisional if unverified (D-IDENTITY-03), reconciled later
                        → account identity created SEPARATELY from patient identity
```

### 3.2 Rules

1. **Self-service:** local credentials only (WebAuthn/TOTP/recovery); no mandatory paid SMS/email OTP (D-IDENTITY-09). Verification codes, if used, prove **channel ownership**, not login and not identity.
2. **Assisted:** staff may capture/verify data but cannot set or possess the citizen's authentication credentials (D-IDENTITY-08). All assisted actions attributed and audited.
3. **Provisional care (D-IDENTITY-03):** undocumented/unknown patients receive a provisional healthcare identity immediately; emergency care is never blocked; provisional status is explicit; no auto-delete; reconciled via MPI on verification.
4. **Child (D-IDENTITY-05):** independent NHID at birth; guardian management with time-bounded, multiple guardians and preserved history; transition at 18 (see `IDENTITY_LIFECYCLE.md`).
5. **NID handling:** one digit-normalized HMAC contract; no raw NID at rest or in URLs/logs (`NATIONAL_IDENTITY_MODEL.md` §4.1).
6. **OCR assist (D-IDENTITY-10):** advisory, needs confirmation, never proof.
7. **Separation (D-IDENTITY-11):** registration creates identity; it does not grant patient-record access — authorization is a separate per-access decision.

### 3.3 Reuse before build

- Reuse MPI for linkage, NIAM for account identity, canonical auth for credentials, `/id-scan` for OCR assist, `VerificationPolicy` for assurance. Do not activate the dormant JSON identity engine or the unmounted national router without owner approval.

---

## 4. Test requirements (design-level; no tests run here)

| Level | Coverage |
|---|---|
| Unit | NID normalization parity (registration ↔ MPI); NHID format/uniqueness; QR expiry boundary; provisional status semantics. |
| Integration (synthetic) | Self enrollment→MPI→NHID; assisted enrollment with no staff credential access; provisional→verified reconciliation; child+guardian; twin independence. |
| Security | No raw NID at rest/URLs/logs; staff cannot set citizen credentials; verification code is not a login factor; no paid OTP dependency. |
| Accessibility/i18n | Arabic-first RTL capture flow (frontend `index.html:2`). |

Synthetic / legally authorized de-identified data only.

---

## 5. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages | Legal | Security | Ops/cost | Dependencies | Failure | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| CR-01 | One registration spine (self + assisted) over MPI/NIAM | Fragmented paths | Keep parallel paths | Single flow | Consolidation | Registration law | Positive | Moderate | Owner decision | Divergent identities | Reversible | §2, §3.1 | `NEEDS_OWNER_DECISION` |
| CR-02 | Staff never holds citizen credentials | D-IDENTITY-08 | Staff sets initial password | No credential misuse | Assisted UX | None identified | Positive | Low | Auth design | Credential compromise | Reversible | §3.2 | `OWNER_APPROVED` (D-IDENTITY-08) |
| CR-03 | Provisional identity, no auto-delete, immediate care | D-IDENTITY-03 | Block until verified | Care continuity | Duplicate growth | Emergency-care duty | Positive | Storage | MPI reconciliation | Denied care | Reversible | §3.2 | `OWNER_APPROVED` (D-IDENTITY-03) |
| CR-04 | Zero mandatory per-login external cost | D-IDENTITY-09 | Mandatory SMS OTP | No recurring cost | Deliverability | None identified | Positive | Low | Local auth | Vendor cost/lock-in | Reversible | §3.2 | `OWNER_APPROVED` (D-IDENTITY-09) |
| CR-05 | Fix NID hash + raw-NID persistence | Verified defect | Leave | Deterministic, private | Migration | Data-protection law | Positive | Moderate | Key mgmt | Broken linkage/leak | Reversible | §2 | `RECOMMENDED` |
| CR-06 | Citizen-platform in-memory identifiers not used as identity source | Process-local stores | Promote | Avoids loss | Feature gap | None | Positive | Low | Persistence design | Lost identifiers | N/A | §2 | `SECURITY_REVIEW_REQUIRED` |

---

## 6. Open questions

1. Which registration path is canonical (self `register.py` vs NIAM lifecycle vs national)?
2. What is the lawful data set and consent basis for enrollment? (`LEGAL_REVIEW_REQUIRED`.)
3. How are provisional records reconciled and by whom?
4. Is any real NID verification authority available? (`BLOCKED_BY_EXTERNAL_DEPENDENCY`.)

---

## 7. Cross-references

`MASTER_ARCHITECTURE.md` · `NATIONAL_IDENTITY_MODEL.md` · `IDENTITY_LIFECYCLE.md` · `MASTER_PATIENT_INDEX_DESIGN.md` · `AUTHENTICATION_AND_RECOVERY_DESIGN.md` · `DOCUMENT_VERIFICATION_DESIGN.md` · `TESTING_AND_ACCEPTANCE_STRATEGY.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 3, 4, 7).
