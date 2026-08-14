# GULA IAM Identity Verification and Assurance

**Status:** `IMPLEMENTED` for the canonical verification-record/state-machine slice; `TESTED` for targeted unit tests; `UNVERIFIED` for production provider integrations; `DEFERRED` for real government, OCR, NFC, biometric and professional-registry connections.

## Identity separation

GULA keeps the immutable internal account and identity identifiers separate from contact fields and external references. A `VerificationRecord` links an existing `Account` to an existing `IdentityRecord`; it is evidence about verification, not a second citizen database and not an authorization grant.

The record stores the declared purpose, provider/method, state, assurance level, timestamps, opaque provider reference, optional confidence, professional metadata when applicable, and a controlled `verified_attributes` object. Raw provider responses, document images, national identifiers and secrets are not stored by this slice.

## Verification states

The backend state machine supports `not_started`, `pending`, `in_progress`, `verified`, `failed`, `expired`, `revoked` and `requires_review`. A client cannot set `verified` directly. A provider result must be applied through `VerificationRecordService`, and a record must be in `in_progress` or `requires_review` before it can become verified.

Invalid transitions raise a hard error. Revocation and expiry set assurance to `L0` and deactivate the verification record; they do not delete or deactivate the underlying account or identity.

## Assurance engine

`AssuranceEngine` is the central server-side evaluator. Contact methods map to `L1`, official identity to `L2`, professional registry verification to `L3` and organization verification to `L4`. OCR and NFC default to `L0` until a genuine provider policy explicitly establishes a higher level. `L5` is reserved and is never inferred from client input or an arbitrary provider result.

Callers must use `AssuranceEngine.require()` rather than comparing assurance strings throughout the application. The engine is not a professional or clinical authorization system; later policy phases decide what an assurance level permits.

## Provider boundary

`IdentityVerificationProvider` defines start, status, completion, cancellation and revocation operations. `ProfessionalVerificationProvider` provides the boundary for future official registries. `NotConnectedProvider` is the explicit adapter for unavailable integrations and returns `not_connected`/`L0`; it cannot fabricate success.

No Iraqi national identity, civil-status, ministry, professional-council, OCR, NFC or biometric integration is claimed. No endpoint is scraped or reverse engineered. Official providers can be added behind the adapter boundary after lawful authorization, data-protection review, runtime integration testing and retention approval.

## Professional identity

Professional information is represented as verification metadata (`professional_type`, `professional_reference`, validity timestamps and status) attached to the same GULA account/identity. A self-selected profession is not verification and does not grant professional access. Expiry and revocation downgrade assurance and preserve the identity record.

## Privacy and minimization

Only attributes necessary for a declared purpose may be persisted. Verified attributes remain distinct from submitted attributes and include provider/method context through the verification record. National identifiers and document images are not part of ordinary API responses, URLs, logs or analytics. A future document-upload feature must use private object storage, generated object identifiers, malware/content validation, signed temporary access, access audit and retention/deletion workflows.

Correction of verified attributes must be handled through a correction request and review workflow; direct client overwrite is not allowed. Provider revocation, expiry and correction must produce append-only audit events without raw identity documents or secrets.

## Current implementation limits

The repository still contains legacy verification routes tied to `User` and existing trust/proofing models. This slice does not silently merge or delete those paths. A later compatibility phase must map them to `VerificationRecord` with evidence, idempotent backfill, duplicate detection and rollback. No frontend verification UI or mobile document flow is claimed complete.

## Security and rollback

The new table is additive and has a reversible Alembic migration. It does not change clinical workflows, authorization roles or workspace policy. Rollback drops only the new verification table after dependent data is handled; no existing account or identity row is deleted by application code.
