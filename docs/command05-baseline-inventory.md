# Command 05 — Baseline Inventory

**Date:** 2026-08-16
**Branch:** `chore/security-ddos-hardening-clean`
**Scope:** Account Recovery + Security Lifecycle Hardening

## Evidence collected

| Area | Current evidence | Classification |
|---|---|---|
| Forgot Password | `POST /auth/forgot-password` exists in `backend/app/routes/password_reset.py`; returns generic response and is rate-limited. It searches only `LabUser`, hashes a reset token into `reset_token`, and sets a one-hour expiry. No provider delivery contract is present in the route. | **PARTIAL** |
| Password Reset | `POST /auth/reset-password` exists; it loads every non-expired `LabUser` reset row and verifies the supplied token against each hash. It clears the token after success, but has no atomic consume primitive, no session-family revocation, no explicit risk decision, and no password policy schema. | **PARTIAL / HIGH-RISK GAP** |
| Change Password | `POST /auth/change-password` requires the current authenticated user and current password, hashes the new password, bumps legacy `perm_version`, and commits. It does not expose a complete recovery audit/request/correlation contract. | **PARTIAL** |
| Canonical NIAM Recovery | No canonical NIAM recovery route was found alongside the existing NIAM account/session/workspace APIs. Existing account lifecycle is separate from legacy password reset. | **MISSING / UNVERIFIED** |
| Phone/Email Change | No dedicated server route named contact-change/email-change/phone-change was found in the registered route inventory. | **MISSING** |
| Lost Device | No dedicated lost-device/revoke-device recovery flow was found. `MFADevice` management exists, but removal is only `DELETE /mfa/devices/{device_id}` and is authenticated by the normal session without an explicit higher-assurance recovery/step-up contract. | **PARTIAL / HIGH-RISK GAP** |
| MFA Recovery | TOTP setup generates backup codes and stores hashed codes in `MFADevice.backup_codes`; TOTP verification consumes backup codes. There is no dedicated MFA recovery/reset route or manual-review state. | **PARTIAL** |
| Passkey Recovery | WebAuthn registration/authentication and device removal exist. No passkey recovery/reset process or lost-device state machine exists. Private key material is not stored by the backend route. | **PARTIAL / UNVERIFIED** |
| Session Revocation | NIAM session list/terminate/terminate-all and legacy `perm_version` revocation exist. Command 04 added commits, idle timeout, refresh replay family revocation, and server-authoritative logout. Password reset does not yet invoke the full high-risk revocation policy. | **PARTIAL** |
| Account Lock/Unlock | Legacy lockout fields and login lockout exist. No safe self-service unlock flow or separate security-lock vs administrative-lock state machine was found. | **PARTIAL** |
| Security Alerts | Audit logging exists and SecurityPage consumes an administrative summary. A dedicated recovery/security-alert delivery contract for new login, recovery started/completed, MFA/passkey/contact changes, and device/session revocation was not found. | **PARTIAL** |
| Audit | `AuditLog` supports actor/user role/lab/action/resource/details/IP/timestamp/chain hash. `log_action()` hashes the audit chain but does not have first-class request_id/correlation_id/scope columns; recovery routes currently use only basic action/resource/user fields. | **PARTIAL** |
| Authorization | Existing dependencies are server-side, but high-risk MFA device removal and password reset lack a distinct recovery assurance/step-up policy. Frontend routes do not constitute authorization. | **PARTIAL** |
| Data protection | Reset token is hashed at rest; MFA backup codes are hashed; WebAuthn private keys are not stored. The reset route scans all reset hashes, which is a performance and abuse risk. Citizen `IdentityRecoveryService` is an in-memory UUID-token helper and is not a production recovery mechanism. | **PARTIAL / BLOCKED for production use of helper** |
| Frontend | `SecurityPage` shows server-derived MFA and sessions and can terminate all sessions. `authApi` exposes forgot/reset/change password calls, but no `/recovery`, `/recovery/verify`, `/devices`, `/mfa recovery`, `/contact-change`, or pending-review UX contract was found in the main route inventory. | **PARTIAL** |
| Mobile/Desktop | Command 04 source changes establish native login/refresh/logout contracts. No dedicated recovery parity flow was found in Android/iOS/Flutter source inventory. | **UNVERIFIED** |
| Migrations | Existing Alembic head from Command 04 is `20260815_0022`; no Command 05 migration has been created. A schema migration should be avoided unless strictly required and tested with upgrade/downgrade. | **UNVERIFIED until final gate** |

## Immediate root-cause candidates

1. The legacy password-reset route is a one-table implementation rather than a canonical recovery aggregate, so it cannot represent `REQUESTED → VERIFYING → VERIFIED → APPROVED → RECOVERED` or `FAILED/EXPIRED/REJECTED/LOCKED/SUSPICIOUS/CANCELLED` safely.
2. Reset token lookup is O(number of reset rows) because the database stores only a password hash and the route verifies the candidate against every active row. This creates avoidable CPU load under brute force and makes atomic single-winner consumption difficult.
3. Password reset does not revoke existing session families or require post-recovery re-authentication, leaving a potential session-persistence gap after a sensitive recovery.
4. High-risk MFA/passkey device removal has no explicit step-up or manual-review policy and therefore may rely on a normal authenticated session that is weaker than the security control being removed.
5. Contact-change, lost-device, passkey-recovery, account-unlock, and recovery-alert contracts are absent or not proven in the registered API/UI inventory.
6. The in-memory citizen identity recovery helper creates and returns plaintext UUID tokens and has no TTL, rate limit, persistence, audit, atomic consume, or authorization boundary; it must not be exposed as production recovery.

## Safety position before implementation

No production database, environment variable, provider, or deployment setting has been modified. No Government Identity, OCR, NFC, biometric, or fake provider will be activated. Any high-risk recovery path that cannot meet an assurance level at least as strong as the control being bypassed will remain `PENDING_REVIEW` or `BLOCKED` rather than using a bypass.
