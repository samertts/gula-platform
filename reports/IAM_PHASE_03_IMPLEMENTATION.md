# GULA IAM Phase 3 — Identity Verification and Professional Identity

**Overall status:** `IMPLEMENTED` for the additive verification-record foundation and assurance state machine; `TESTED` for targeted tests; `UNVERIFIED` for real external providers; `DEFERRED` for government/OCR/NFC/biometric integrations and full frontend/mobile UX.

## 1. Existing architecture audited

The repository already contains `IdentityRecord`, `Person`, `Account`, trust/assurance/proofing models, legacy `User` verification routes, an OCR ID-scan route and a Phase 1 provider protocol. The legacy verification route is tied to `User`, and the existing trust/proofing layer is broader than a canonical verification evidence record. This PR does not delete or silently merge those systems.

## 2. Changes made

| Area | Change | Status |
|---|---|---|
| Canonical evidence | Add `VerificationRecord` linked to existing account and identity rows | `IMPLEMENTED` |
| Verification states | Add backend-only state machine for pending/in-progress/verified/failed/expired/revoked/review | `IMPLEMENTED` |
| Assurance | Add centralized `AssuranceEngine` and method policy L0–L4 | `IMPLEMENTED` |
| Providers | Add start/status/complete/cancel/revoke provider boundary and professional provider protocol | `IMPLEMENTED` |
| Unavailable integrations | Return explicit `not_connected`/L0 through `NotConnectedProvider` | `IMPLEMENTED` |
| Professional identity | Support professional type/reference/validity/revocation metadata without granting authorization | `IMPLEMENTED` foundation |
| Audit vocabulary | Add verification, professional review and attribute correction event names | `IMPLEMENTED` vocabulary |
| Privacy | Avoid raw provider responses, secrets, document images and national identifiers in the new record | `IMPLEMENTED` by model design |
| Migration | Add reversible additive migration `20260814_0001_verification_records` | `IMPLEMENTED` file; runtime migration `UNVERIFIED` |

## 3. Files changed

The implementation adds `backend/app/identity/models/verification_record.py`, `backend/app/identity/services/verification_record_service.py`, extends `verification_service.py`, exports the new models, adds Phase 3 audit event names, adds the Alembic migration, adds targeted tests and adds the Phase 3 documentation/report. No clinical, workspace, RBAC, ABAC or organization authorization module is changed.

## 4. Provider and national identity status

No Iraqi national identity, civil-status, ministry, professional-council, OCR, NFC or biometric integration is claimed. The adapter boundary is ready for a lawful, runtime-tested provider. `NotConnectedProvider` is fail-safe and cannot produce a successful verification result.

## 5. Professional identity status

Professional identity is represented as verification metadata attached to the same account/identity. A selected profession is not a verified profession and cannot establish L3. A future provider must return authoritative evidence, validity and revocation state. This PR does not implement clinical authorization or professional privileges.

## 6. Database and migration

The migration creates only `niam_verification_records` with foreign keys to `niam_accounts` and `niam_identities`, state/assurance/provider fields, timestamps, opaque references, professional metadata and controlled JSON attributes. It is additive and reversible. No existing table is deleted or rewritten. Migration application against a live database is `UNVERIFIED` until CI/database integration runs.

## 7. Security fixes

The backend state machine denies invalid state transitions and does not allow a client to set `VERIFIED`. Revocation/expiry downgrade assurance to L0 without deleting the account or identity. OCR/NFC default to L0 and cannot claim proof merely because a payload was received. Provider absence is explicit `NOT_CONNECTED`, not simulated success. Assurance checks are centralized and deny by default.

## 8. Tests created and executed

The Phase 1 and Phase 3 identity suites passed with **10 tests**. They cover account lifecycle regression, verification state progression, invalid transitions, backend-only verified application, not-connected provider behavior, revocation downgrade and centralized assurance requirements. Python `compileall` passed for `app/identity`, and Ruff passed on the modified files. Migration execution, full backend tests, frontend/mobile tests and external provider tests remain `UNVERIFIED`.

## 9. Privacy and data minimization

The new record intentionally excludes raw provider responses, document images, secrets and national identifiers. Verified attributes are controlled JSON tied to a purpose field and are not treated as ordinary profile data. Document storage, correction workflow, retention/deletion jobs and access-controlled retrieval remain `DEFERRED` until the platform storage and legal requirements are confirmed.

## 10. Remaining risks and deferred work

Legacy `User` verification and trust/proofing routes remain separate and require a compatibility mapping. There is no claim of real OCR/NFC/biometric/government integration, no complete frontend/mobile verification UX, no production provider, no full concurrency suite and no professional authorization change. These are explicit follow-up phases.

## 11. Deployment and rollback

No production deployment was performed. Before deployment, CI must validate the migration on supported databases, run integration/security suites, and review privacy/retention controls. Rollback is a migration downgrade plus code revert; existing accounts and identities are preserved.

## 12. Next phase

The next safe step is a compatibility and integration phase: map legacy verification events to canonical records idempotently, add authenticated endpoints with ownership checks and audit emission, then implement only a real provider after lawful credentials and runtime tests are available.
