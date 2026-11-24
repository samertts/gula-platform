# GULA National Identity Architecture Study — Document Verification Design

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff…`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`.

---

## 0. Evidence convention

See `MASTER_ARCHITECTURE.md` §0. Labels: `VERIFIED_IN_SOURCE`, `TEST_VERIFIED` (test source exists — **not executed here**), `PARTIAL`, `SOURCE_PRESENT`, `DORMANT`, `NOT_IMPLEMENTED`, `BLOCKED`, `UNVERIFIABLE`. Source presence is never runtime verification. No tests run, no DB contacted, no application file modified. No government ID-verification API, NFC availability, or data-sharing agreement is assumed.

---

## 1. Governing decisions

- **D-IDENTITY-10** — OCR extraction is a core but non-proof capability; extraction is not proof of identity or authenticity.
- **D-IDENTITY-01** — NID is a protected matching attribute, never a credential.
- **D-IDENTITY-15-equivalent principle (Workstream G)** — document verification is a *layered assurance* decision, never a single OCR or photo check.

---

## 2. Current verification source inventory (verified directly)

### 2.1 Verification policy — the one honest assurance map — `VERIFIED_IN_SOURCE`

`backend/app/identity/services/verification_service.py`:

| Verified detail | Evidence |
|---|---|
| `VerificationMethod` includes `phone, email, official_identity, ocr, nfc, professional_registry, organization_registry` | `:12`, `:132-148` |
| `VerificationPolicy._levels`: `phone/email → L1`, `official_identity → L2`, **`ocr → L0`**, **`nfc → L0`**, `professional_registry → L3`, `organization_registry → L4` | `:132-148` |
| `assurance_for()` returns `L0` unless status is `verified` | `:150-154` |
| `verify()` "never claims success"; delegates to `start_verification()` | `:128-130` |

**Interpretation:** the source already encodes that OCR and NFC alone confer **no** identity assurance. This is the correct foundation for D-IDENTITY-10 and must be preserved. Runtime behavior `UNVERIFIABLE`.

### 2.2 National ID verification gateway — fail-closed stub — `PARTIAL`

`backend/app/routes/national_identity.py:17-34` exposes `POST /national-id/verify`; it refuses to use a stub verification gateway in production unless demo mode is enabled. Routed at `factory.py:604`. Static test `test_national_identity_production_guard.py` (3 tests, not executed) targets this guard. **No real government verification integration exists or is assumed** → `BLOCKED_BY_EXTERNAL_DEPENDENCY`.

### 2.3 Civil-registry connectors — stubs with false confidence — `PARTIAL` / hazard

`backend/app/governance/services/connector_service.py:85-123`: civil registry connectors are stubs and emit `confidence: 1.0` without a real check. A hardcoded perfect confidence from a stub is a **safety hazard** if any downstream consumer treats it as verification. → `SECURITY_REVIEW_REQUIRED`.

### 2.4 OCR document scan — advisory only — `PARTIAL`

`/id-scan` (`routes/id_scan.py`) extracts fields with `needs_confirmation: True` (`:189-191`) and performs **no authenticity check** — a photograph of any card can be uploaded. Correctly advisory; must never be promoted to verification without separate evidence.

### 2.5 Document-intelligence "verification" claims — `NOT_IMPLEMENTED`

- `DefaultEncryptionService.verify_digital_signature()` always returns `False` (`wiring.py:93-96`); no digital-signature verification.
- Government-document registration/search (`api/routes.py:330-394`) depends on the uninitialized orchestrator (`OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` §2.2) — unreachable in source.
- Document hash verification (`hash_document` = SHA-256, `verify_hash`) exists (`wiring.py:82-88`) but can only prove byte integrity, not authenticity or identity.

### 2.6 `integration/identity/` — `BLOCKED`

`backend/app/integration/identity/__init__.py` imports non-existent modules (`civil_registry`, `biometric`, `digital_identity`, `national_id`) — no usable external identity integration.

### 2.7 National document signing & QR verification — `PARTIAL` (verified)

`backend/app/national/document_platform/application/service.py`:

- **Signature verification likely fails** — the signing input hashes one timestamp string (`:263`) while verification hashes a different one (`:322`); verification succeeds only if they coincidentally match exactly. Route `api/routes.py:278-303`.
- **QR fallback is weak** — accepts `gula:doc:` and checks only document existence (`:415-425`); does **not** validate hash, expiry or signature. QR payload includes ID/hash/timestamp (`:378`).
- **Statutory connectors are stubs** — birth (`:69-95`), death (`:98-123`), civil (`:126-151`), passport (`:154-180`) in `governance/services/connector_service.py` return hard-coded successful data with `confidence: 1.0`.
- Document categories include `national_id` and `passport` but **no birth/death certificate category** (`document_intelligence/domain/enums.py:8-34`).
- → `SECURITY_REVIEW_REQUIRED` for signing/QR repair; `BLOCKED_BY_EXTERNAL_DEPENDENCY` for real statutory connectors.

---

## 3. Target verification model (recommendations)

### 3.1 Layered assurance — never one signal

```
Layer 0  OCR / photo / NFC read            → advisory only (L0), needs confirmation
Layer 1  Channel ownership (phone/email)   → L1, not identity proof
Layer 2  Official identity document check  → L2, requires real authority or authorized manual check
Layer 3  Professional / organization reg.  → L3/L4, authoritative registry
Cross-cutting: document integrity (hash/signature), liveness (if lawfully used),
               human review, full attribution + audit, no silent confidence=1.0 stubs
```

- Preserve the existing `VerificationPolicy` L0-for-OCR/NFC behavior; **remove or gate** any stub that emits `confidence: 1.0` (`connector_service.py`) so it cannot be mistaken for verification.
- Any real government verification integration is `BLOCKED_BY_EXTERNAL_DEPENDENCY` pending legal agreement and owner approval; do not fabricate availability.
- Document verification evidence is **distinct** from civil identity proof and from patient-record authorization (D-IDENTITY-11).

### 3.2 Rules

1. Extraction ≠ verification ≠ authorization — three separate records and decisions.
2. Every verification result carries: method, assurance level, evidence reference, verifier identity (human or system), timestamp, and revocation path.
3. Failed/unavailable verifiers fail closed; no default "verified".
4. Re-verification on document expiry/correction; history preserved.
5. All personal data minimized; no raw NID at rest; no document images retained unless separately authorized.

---

## 4. Test requirements (design-level; no tests run here)

| Level | Coverage |
|---|---|
| Unit | `VerificationPolicy` mapping (ocr/nfc = L0); stub gateway production guard; no `confidence:1.0` from unimplemented connectors. |
| Integration | OCR scan → confirmation → verification (must remain L0 until real evidence); signature verification false-safe; revocation. |
| Security | Photo of a card cannot raise assurance; no raw NID/image at rest; external verifier unavailability fails closed. |
| Legal | Each method's lawful basis and required assurance recorded (`LEGAL_REVIEW_REQUIRED`). |

Synthetic / legally authorized de-identified data only.

---

## 5. Architecture decisions register

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages | Legal | Security | Ops/cost | Dependencies | Failure | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| DV-01 | Preserve OCR/NFC = L0 in VerificationPolicy | Correct non-proof semantics | Promote OCR | Prevents wrongful verification | UX friction | Proofing law | Positive | Low | None | False verification | Reversible | §2.1 | `OWNER_APPROVED` (D-IDENTITY-10) |
| DV-02 | Gate/remove stub `confidence:1.0` civil connectors | Stub emits perfect confidence | Leave | Removes false assurance | Connector work | Data-sharing law | Positive | Low | Owner decision | Mis-trust stub | Reversible | §2.3 | `SECURITY_REVIEW_REQUIRED` |
| DV-03 | No assumed government verification API | Stub gateway only | Assume availability | Honest capability | No external verification | Legal agreement | Positive | Low | External authority | Unauthorized integration | Reversible | §2.2, §2.6 | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |
| DV-04 | Fail-closed verification with full attribution/audit | Default-verified risk | Default allow | Safety, accountability | Extra handling | Audit/retention law | Positive | Low–moderate | Audit service | Wrongful access | Reversible | §3.2 | `RECOMMENDED` |
| DV-05 | Digital-signature verification must be real or explicitly absent | Always-False stub misleads | Keep stub | No false claim | Crypto work | None identified | Positive | Moderate | PKI | False authenticity | Reversible | §2.5 | `RECOMMENDED` |

---

## 6. Open questions

1. What lawful basis and assurance level is required for each verification method? (`LEGAL_REVIEW_REQUIRED`.)
2. Is any official government verification interface legally available? (`BLOCKED_BY_EXTERNAL_DEPENDENCY`.)
3. Who may perform/manage assisted verification, and what evidence is retained? (`NEEDS_OWNER_DECISION`.)
4. Should document images ever be retained, and for how long? (`LEGAL_REVIEW_REQUIRED`.)

---

## 7. Cross-references

`MASTER_ARCHITECTURE.md` · `OCR_AND_DOCUMENT_INTELLIGENCE_DESIGN.md` · `NATIONAL_IDENTITY_MODEL.md` · `CITIZEN_REGISTRATION_DESIGN.md` · `SECURITY_AND_PRIVACY_THREAT_MODEL.md` · `IRAQI_LEGAL_AND_INSTITUTIONAL_ASSESSMENT.md` · `IMPLEMENTATION_ROADMAP.md` (Phases 4, 8, 10).
