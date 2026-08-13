# GULA IAM Phase 1 — Identity & Account Foundation

**Status:** `IMPLEMENTED` for the narrow foundation slice; `TESTED` for the listed tests; `UNVERIFIED` for production-wide IAM; `DEFERRED` for OTP/MFA/provider wiring and frontend rollout.

## 1. What was already present

The Phase 0 audit established that GULA already has a NIAM account model (`niam_accounts`), a separate identity model (`niam_identities`), person records, credentials, devices, sessions, organizations, assignments, trust/proofing models and a hash-chained identity audit service. Legacy `User`, `LabUser`, generic RBAC and ABAC models remain for compatibility.

## 2. What changed

This slice preserves the existing NIAM architecture and adds the following focused hardening:

| Area | Change | Status |
|---|---|---|
| Account creation | Normalize email/phone/username, require at least one identifier, enforce the existing 12-character password minimum, and remove the invalid placeholder primary-key argument | `IMPLEMENTED` |
| Account authentication | Reject pending, suspended, disabled, deactivated and inactive accounts with generic authentication failure behavior | `IMPLEMENTED` |
| Account lifecycle | Add a deny-by-default transition service for pending/active/suspended/locked/disabled/deactivated states | `IMPLEMENTED` |
| Automatic lockout | Route lock and unlock through the lifecycle state machine | `IMPLEMENTED` |
| Session creation | Remove the invalid placeholder ID from `UserSession` creation while preserving existing token/session contracts | `IMPLEMENTED` |
| Verification | Add `IdentityVerificationProvider`, explicit `NotConnectedProvider`, and centralized assurance mapping L0–L4 | `IMPLEMENTED` |
| Observability | Add Phase 1 event names to the existing `AuditAction` enum without creating a second audit log | `IMPLEMENTED` |
| Documentation | Add this report and `docs/security/IAM_ACCOUNT_FOUNDATION.md` | `IMPLEMENTED` |

## 3. Files changed

The implementation is limited to `backend/app/identity/models/account.py`, `backend/app/identity/models/audit.py`, `backend/app/identity/services/account_service.py`, `backend/app/identity/services/authentication_service.py`, the new `account_lifecycle_service.py`, the new `verification_service.py`, the new Phase 1 unit test, and the two Phase 1 documents.

No unrelated clinical module, clinical result workflow, specialized repository, production configuration or deployment file was changed.

## 4. Database migrations

No migration is required for this narrow slice. The canonical account already exists and the implementation uses existing columns. No table is created, renamed or deleted. A later migration is required only if contact-verification records, OTP digests, token-family reuse markers or provider-result persistence are added.

## 5. API and frontend changes

No API contract or frontend screen was changed in this slice. This is intentional: the existing account API exposes state-changing operations without visible endpoint authorization and requires a separate authenticated-admin hardening slice before those operations should be expanded. The backend remains authoritative; no frontend-only authorization was introduced.

## 6. Security fixes

The implementation prevents authentication for non-active account states, avoids revealing whether an unknown login exists by retaining dummy-hash verification, removes invalid placeholder IDs, prevents illegal lifecycle transitions, and ensures unavailable verification providers return `not_connected`/`L0` rather than a fabricated success. No password, OTP, access token or refresh token is added to logs by these changes.

## 7. Tests added and executed

The new unit suite covers activation from pending, suspension, prevention of reactivation from deactivated/disabled states, explicit not-connected provider behavior, and centralized assurance mapping. It passed with **5 tests**. Python `compileall` for `app/identity` passed, `ruff check` passed on all modified Python files, and `git diff --check` passed.

## 8. Migration and deployment status

No database migration was executed. No production deployment was performed. No data backfill was performed. The branch is suitable for CI review, not a production-readiness declaration.

## 9. Known limitations and remaining risks

Full OTP issuance/delivery, hashed OTP persistence, rate limiting, enumeration review across every auth endpoint, MFA/step-up, refresh-token reuse detection, HttpOnly cookie enforcement, endpoint-level authorization for lock/unlock, provider persistence, frontend registration integration, mobile parity and broad integration/security tests remain open. The repository still contains legacy authentication and authorization sources; this PR deliberately does not delete or silently merge them.

## 10. Next required phase

The next safe slice is contact verification and session hardening: add idempotent OTP challenge persistence with expiry, single-use digest storage, attempt limits, rate limits, generic responses, refresh-token family/reuse detection and endpoint authorization tests. It must be implemented as a separate reviewed change and must stop if critical security tests fail.

> Phase 1 is not being declared fully complete or production-ready. This PR completes only the safe canonical-account foundation that can be implemented without destructive migration or unrelated clinical changes.
