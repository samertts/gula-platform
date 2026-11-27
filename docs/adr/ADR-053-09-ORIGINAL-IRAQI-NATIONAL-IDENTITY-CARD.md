# ADR-053-09 — Original Iraqi National Identity Card and Live Document Authenticity Policy

**Status:** `PROPOSED` — synthetic boundary `IMPLEMENTED` and `TESTED`; production activation `BLOCKED / NOT APPROVED`.
**Date:** 2026-11-25
**Deciders:** GULA engineering execution under Wave 05.3; owner, legal, national identity authority, security, schema owner, and release authority approvals remain pending.

## Context

Wave 05.2 established the canonical GULA Citizen Identifier, identity-governance state machine, extraction contracts, authorization boundary, audit builder, government-verification separation, and patient-identity safety helpers. Wave 05.3 added synthetic persistence, cryptography, access, government-adapter, and OCR/NFC boundaries. No production card-inspection route exists.

The following requirements are now explicit for the Original Iraqi National Identity Card Policy:

- The original physical card is mandatory for initial registration and authenticity inspection.
- Phone photographs, messaging-app images, email attachments, scans, printed replicas, PDFs, screenshots, digital reproductions, photocopies, and certified or uncertified copies are rejected in the original-card path unless a separate official process is approved.
- Live capture must originate from an authorized server-challenged camera session. Saved images and user uploads are not acceptable.
- Camera metadata alone is not liveness proof. Server-verifiable challenges and replay rejection are required where technically feasible.
- OCR, MRZ, NFC, field agreement, and synthetic government results never establish document authenticity or grant `VERIFIED`.
- Chip authenticity requires an officially documented, successful cryptographic procedure. None is approved in this wave.
- Uncertain, mismatched, copied, unreadable, expired, unsupported, or failed cases route to human review and are never automatically labelled counterfeit.
- Home NFC registration and the no-NFC in-person fallback require explicit approvals before activation.
- Raw card images and raw NFC payloads are not retained.

## Decision

Add `backend/app/national/services/document_authenticity.py` as a local, additive, synthetic NIDP policy boundary. It reuses the canonical identity governance state machine, document-extraction artifacts, Decision Engine wrapper, and canonical audit builder. It does not add a second identity generator, MPI, citizen database, authorization engine, audit system, OCR architecture, or state machine.

### Document authenticity states

The boundary defines nine local states:

1. `ORIGINAL_CARD_PRESENTED`
2. `LIVE_CAPTURE_COMPLETED`
3. `VISUAL_INSPECTION_COMPLETED`
4. `MRZ_READ_SUCCESSFULLY`
5. `NFC_READ_SUCCESSFULLY`
6. `CHIP_AUTHENTICITY_VERIFIED`
7. `DOCUMENT_AUTHENTICITY_CONFIRMED`
8. `DOCUMENT_AUTHENTICITY_FAILED`
9. `DOCUMENT_REVIEW_REQUIRED`

Only `DOCUMENT_REVIEW_REQUIRED` is reachable from the evaluator in this wave. `CHIP_AUTHENTICITY_VERIFIED` and `DOCUMENT_AUTHENTICITY_CONFIRMED` are structurally unreachable until an approved official procedure exists. Every decision maps to an existing canonical event and state; `VERIFIED` is never produced.

### Explicit rejection classes

`COPY_PRESENTED`, `PRINTED_REPLICA_PRESENTED`, `DIGITAL_IMAGE_PRESENTED`, `SCREENSHOT_PRESENTED`, `ORIGINALITY_UNCERTAIN`, and `SECURITY_FEATURE_MISMATCH` are recorded separately. Copy, uncertainty, mismatch, suspected forgery, expiry, unsupported chip, and NFC read failure route to human review. No uncertainty alone becomes a counterfeit finding.

### Live capture

A server-issued challenge binds session, actor, organization, facility, purpose, correlation ID, minimal device capability flags, timestamp, capture method, source, outcome, and opaque front/back evidence references. The in-process registry rejects unknown and replayed challenges. Uploads and saved-image channels are rejected. Durable replay state is `PROPOSED / NOT APPROVED`.

### Registration routes

- Home NFC requires the original physical card, NFC capability, officially documented direct NFC reading, live capture, completed authenticity checks, and an authorized final identity workflow state. All are required; none grants `VERIFIED` in this wave.
- Without NFC, only an initial incomplete account is permitted. Identity verification completes only after authorized-officer inspection of the original card at an approved institution and central workflow recording. That workflow is `PROPOSED / NOT APPROVED`.
- Synthetic government verification results never activate a citizen identity.

### Authorization, audit, and minimization

Every sensitive operation calls the canonical Decision Engine boundary. New audit operations reuse `build_wave053_audit_event()` and its recursive full-NID guard. Audit records contain protected references and metadata only, never a full Iraqi National ID, card image, raw NFC payload, or decrypted identity value.

### Persistence and integrations

No migration, DDL, trigger, schema change, route, government API, credential, certificate, public key, APDU, card layout, reader protocol, external OCR service, or card-image retention was introduced. A logical schema proposal is recorded in `GULA_IDENTITY_DATABASE_INTEGRITY_REPORT.md` and remains `PROPOSED / NOT APPROVED` by the schema owner.

## Alternatives Considered

### 1. Accept photographs or scans for initial registration

**Pros:** Lower citizen friction and simpler remote capture.

**Cons:** Cannot establish original-card presentation; enables copying and replay; conflicts with the stated policy and authenticity requirement.

**Status:** Rejected.

### 2. Treat successful OCR, MRZ, or NFC field agreement as document authenticity

**Pros:** Automated decision and faster registration.

**Cons:** Extracted data is reproducible from copies; NFC read success is not chip authenticity; no officially documented chip procedure exists; would produce false verification.

**Status:** Rejected.

### 3. Add a parallel NIDP identity/state engine

**Pros:** Could encode document-specific states independently.

**Cons:** Duplicates canonical governance, risks divergent transitions, weakens auditability, and violates reuse-before-build.

**Status:** Rejected. Document states remain local to the NIDP boundary and map to canonical transitions.

### 4. Activate a government-source verification path

**Pros:** Could verify identity attributes if an official source existed.

**Cons:** No approved authority, API, credentials, endpoint, status semantics, public keys, revocation feed, or transport exists. Synthetic verification is not proof.

**Status:** Rejected for this wave. The canonical adapter remains default-closed and synthetic.

### 5. Selected: additive synthetic boundary with review-only outcomes

**Pros:** Preserves canonical architecture; tests policy fail-closed; records required states and rejections; enables approval work without implying production readiness.

**Cons:** Does not deliver real card authenticity or live liveness; durable persistence and operational workflow remain blocked.

**Status:** Selected.

## Consequences

### Positive

- Original-card and live-capture requirements are explicit and synthetically tested.
- Copy, replica, screenshot, digital image, uncertainty, mismatch, expiry, and NFC failure paths are recorded without automatic counterfeit classification.
- No path from OCR, MRZ, NFC, or synthetic government verification reaches `VERIFIED`.
- Authorization and audit remain within canonical infrastructure.
- No raw identity value, card image, raw NFC payload, external dependency, migration, or production route was added.

### Negative

- `DOCUMENT_AUTHENTICITY_CONFIRMED` and chip authenticity remain unavailable.
- Anti-replay is in-process only; PostgreSQL concurrency and durable uniqueness remain proposals.
- No official card specification, chip procedure, government source, or institutional in-person workflow is approved.
- Production activation remains impossible without owner approvals and G1–G12 acceptance.

### Neutral

- Nine local NIDP states are intentionally separate from nine canonical identity states.
- Arabic and Western numeral normalization is used only for synthetic field comparison.

## Constitution and Cost Posture

Free and open-source alternatives were used first: Python standard library (`secrets`, `threading`, `re`, `dataclasses`) and existing canonical GULA helpers. Ruff and `detect-secrets` were used for static and secret scanning. No paid dependency, proprietary SDK, SaaS OCR/NFC service, vendor-specific protocol, or lock-in was introduced. Any future KMS/HSM, official reader, or authority integration requires a documented cost, license, and lock-in analysis before approval.

## References

- `backend/app/national/services/document_authenticity.py`
- `backend/tests/test_wave05_3_nidp_original_card_policy.py`
- `backend/app/national/services/identity_governance.py`
- `backend/app/national/services/document_extraction.py`
- `backend/app/national/services/identity_access.py`
- `backend/app/national/services/government_verification.py`
- Prior Wave 05.2 ADRs `ADR-052-01` through `ADR-052-08`
- `GULA_OCR_NFC_READINESS_REPORT.md`
- `GULA_IDENTITY_DATABASE_INTEGRITY_REPORT.md`
- `GULA_OWNER_DECISION_REGISTER.md`
- `WAVE05_3_FINAL_VALIDATION.txt`

Release posture remains unchanged: `HOLD = TRUE`, `production_ready_items = 0`, G1–G12 `NOT PASSED`, Stable v1.0.0 `NOT DECLARED`, and `PRODUCTION READY` `NOT DECLARED`.
