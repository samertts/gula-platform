# GULA IAM Phase 2 — Authentication and Session Security

**Overall status:** `IMPLEMENTED` for the narrow hardening slice; `TESTED` for targeted tests; `UNVERIFIED` for full Phase 2 quality gates; `DEFERRED` for full OTP/MFA/password-reset implementation.
**Base:** Phase 1 branch `feat/iam-account-workspaces`
**Scope:** authentication and account security only. No organization, workspace, RBAC, ABAC or clinical authorization redesign.

## 1. Existing architecture

The repository already contained NIAM `Account`, `UserSession`, shared JWT helpers, Redis-backed JTI blacklist, IP/user rate limiting, legacy TOTP routes, adaptive-auth components, password-reset routes and separate legacy authentication paths. This implementation extends the existing NIAM path rather than introducing a second authentication system.

## 2. Changes made

| Area | Change | Status |
|---|---|---|
| Login protection | Apply existing `rate_limit_auth` to NIAM `/auth/login` | `IMPLEMENTED` |
| Refresh protection | Decode/validate refresh token, require JTI, consume and blacklist old JTI, terminate old session, create rotated session | `IMPLEMENTED` |
| Replay resistance | A consumed refresh token is rejected by blacklist/session checks | `IMPLEMENTED` in the NIAM path |
| Security vocabulary | Add Phase 2 event names to existing `AuditAction` | `IMPLEMENTED` vocabulary; endpoint emission remains `DEFERRED` |
| Documentation | Add `docs/security/IAM_AUTHENTICATION.md` and this report | `IMPLEMENTED` |

## 3. Files changed

The Phase 2 slice changes `backend/app/identity/api/auth.py`, `backend/app/identity/services/authentication_service.py` and `backend/app/identity/models/audit.py`, and adds the Phase 2 security documentation and report. It does not modify clinical modules, organizations, workspaces, roles, permissions, ABAC or frontend/mobile source.

## 4. API and database changes

The NIAM login and refresh endpoints retain their response contracts. Login and refresh now have request-based rate limiting. No database migration was added: the existing `niam_sessions` fields and Redis JTI blacklist are reused. No data backfill or deployment was performed.

## 5. Security fixes

The refresh endpoint no longer treats the raw refresh-token string as a database JTI. It validates the signed refresh token, extracts the JTI, requires an active matching session, blacklists the consumed JTI for the remaining session lifetime, terminates the old session and rotates to a new session. Login and refresh are rate-limited, and existing generic login errors and dummy-hash behavior are preserved.

## 6. OTP, MFA and recovery

The repository has legacy TOTP/adaptive-auth pieces, but this PR does not claim that a unified NIAM OTP/MFA/password-reset architecture is complete. Secure OTP digest persistence, expiry, single-use semantics, concurrent verification protection, MFA enrollment/recovery, step-up authentication and reset-token family invalidation remain `DEFERRED`, because implementing them safely requires additional schema-backed tests and endpoint integration.

## 7. Tests executed

The targeted Phase 1 identity suite passed with **5 tests**. Python `compileall` passed for `app/identity` and `app/security`. Ruff passed for all modified Python files. `git diff --check` passed. Full Phase 2 backend/frontend/integration/security quality gates remain `UNVERIFIED` until CI completes on the pull request.

## 8. Remaining risks

Full enumeration review across registration/recovery/OTP, endpoint-level audit emission, HttpOnly cookie enforcement in the NIAM endpoint, CSRF/CORS validation, password-reset replay protection, MFA bypass resistance, concurrent refresh tests and mobile/frontend parity remain open. The existing legacy auth paths require separate compatibility review.

## 9. Deployment and rollback

No production deployment is authorized. Rollback is a code revert because no database migration is included. Any rollback must record the resulting refresh-replay regression and be approved through security review.

## 10. Next phase

After this PR and Phase 1 are reviewed, the next safe slice is database-backed contact verification and recovery hardening: OTP/reset challenge records with hashed secrets, expiry, attempt limits, rate limits, idempotent verification, generic responses and tests for replay/concurrency. Full MFA/step-up follows only after that foundation.
