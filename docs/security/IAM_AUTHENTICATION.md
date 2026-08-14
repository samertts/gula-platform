# GULA IAM Authentication and Session Security

**Status:** `IMPLEMENTED` for the narrow authentication hardening slice; `TESTED` for the listed checks; `UNVERIFIED` for complete production-wide authentication; `DEFERRED` for full OTP/MFA/password-reset rollout.

## Architecture

GULA retains the existing NIAM authentication path. Authentication resolves an NIAM `Account`, creates a `UserSession`, and places only minimal account/identity references in access-token claims. Authorization and clinical resource access remain separate concerns and are not redesigned by Phase 2.

## Login

The NIAM login endpoint remains `/auth/login`. It uses the existing password hashing and dummy-hash path for unknown identifiers, returns a generic authentication failure, rejects pending/suspended/disabled/deactivated/inactive accounts, and now applies the existing Redis-backed `rate_limit_auth` protection. The rate limiter is keyed by client IP and returns standard 429 headers.

## Session and token model

`niam_sessions` stores the account, access-token JTI, refresh-token JTI, lifecycle timestamps, activity metadata and revocation state. The refresh path now decodes and validates the refresh token before database lookup, requires a refresh JTI, blacklists the consumed JTI for the remaining session lifetime, terminates the old session, and creates a new session. A second use of the consumed token is rejected by the blacklist/session checks.

The access token contains only the account UUID and identity ID in the NIAM path. No medical data, password, OTP, or secret is added to the claims by this change. The existing shared JWT decoder remains responsible for signature/type/expiration validation; a separate JWT implementation was not introduced.

## Account protection

Phase 1 lifecycle enforcement remains active. Authentication respects `pending_verification`, `active`, `suspended`, `locked`, `disabled` and `deactivated`. Failed password attempts use the existing threshold and temporary lockout, while state changes now pass through the central lifecycle service.

## Rate limiting and enumeration

Login and refresh are rate-limited. Unknown login identifiers use the dummy hash and the endpoint returns the same generic 401 response as invalid passwords. A full account-enumeration audit of registration, password reset, OTP, email and phone verification is still required.

## MFA, OTP and recovery

The repository contains an existing legacy TOTP route and adaptive-auth components, but Phase 2 does not claim a unified NIAM MFA implementation. Full OTP challenge persistence, single-use digest storage, expiry, concurrent verification controls, password-reset token rotation, MFA enrollment/recovery and step-up flows remain `DEFERRED` until they can be implemented with database-backed tests and without creating a second authentication system. Unsupported providers must remain explicitly `NOT_CONNECTED` or `NOT_IMPLEMENTED`.

## Security events

The existing hash-chained NIAM audit model has been extended with names for login success/failure, logout, password reset, contact verification, OTP, session refresh/reuse detection, account suspension and account disablement. These are event vocabulary additions; emitting them from every endpoint is a follow-up integration task. Secrets must never be placed in event metadata.

## Frontend and mobile behavior

No frontend or mobile token-storage contract was changed in this slice. The backend remains authoritative. Browser cookie policy, session-expired UX, secure session listing, mobile Keychain/Keystore integration and MFA parity require separate verified changes.

## Threat model and known limitations

The current change addresses a concrete refresh-token misuse path and login rate limiting. It does not certify resistance to all brute-force, OTP flooding, MFA bypass, password-reset replay, CSRF/CORS misconfiguration or concurrent security mutations. Those remain explicit quality gates before production.

## Rollback

Rollback is a code revert only; no database migration is included. Existing sessions and accounts are not rewritten. If the refresh hardening must be reverted, the old service behavior can be restored without a data migration, but the security regression must be documented and approved.
