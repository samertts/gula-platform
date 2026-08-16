# Command 04 — Auth Inventory Working Notes

## Baseline

- Branch: `security/p0-bootstrap-alembic`
- HEAD before Command 04: `f39ed730`
- Alembic head: `20260815_0024`
- Working tree was clean before Command 04.

## Effective auth surfaces

| Surface | Evidence | Initial classification |
|---|---|---|
| Legacy `/login` | `backend/app/routes/login.py` | PARTIAL: timing-safe password verification, account verification gate, privileged MFA gate, HttpOnly/Secure/SameSite cookies; uses legacy `LabUser`/`User`, not canonical NIAM Account/UserSession. |
| Legacy `/auth/refresh` | `backend/app/routes/mobile.py` | PARTIAL: body or HttpOnly cookie, JWT expiry and Redis JTI blacklist; does not persist NIAM session rows, has inconsistent 30-second grace comment, no family invalidation. |
| Legacy `/logout` | `backend/app/routes/login.py` | PARTIAL: blacklists access/refresh JTI and bumps global `perm_version`, so current logout invalidates all sessions for the account; no current-vs-all session distinction. |
| Legacy `/session` | `backend/app/routes/login.py` | PARTIAL: returns legacy user identity from authenticated token; no canonical NIAM workspace/session context. |
| Canonical NIAM login | `backend/app/identity/api/auth.py` + `AuthenticationService` | PARTIAL/UNVERIFIED: service creates `UserSession` with access/refresh JTIs and rotates refresh tokens; route uses `AsyncSession` through sync `get_db` typing and returns bearer JSON without cookie semantics. |
| Canonical NIAM refresh | `AuthenticationService.refresh_session` | PARTIAL: active-session lookup, expiry check, blacklist old JTI, soft-delete old row, create new session; no family ID, idle timeout, replay family invalidation, or audit event in the service. |
| Canonical NIAM logout | `backend/app/identity/api/auth.py` | MISSING/HIGH RISK: accepts `session_uuid` without authenticated NiamActor/ownership, terminates DB row only, no cookie clearing or access-token blacklist. |
| NIAM session API | `backend/app/identity/api/sessions.py` | MISSING/HIGH RISK: account/session paths accept caller-supplied account IDs, no actor/ownership/permission enforcement. |
| NIAM actor/workspace | `backend/app/identity/api/workspaces.py` | PARTIAL: server-side Account/UserSession join and server-side workspace switching; sync actor lacks explicit blacklist/expiry/idle checks; async actor lacks `is_locked`, blacklist, expiry/idle checks. |
| Web frontend | `frontend-v3/src/api/client.ts`, `AuthContext.tsx`, `endpoints.ts` | PARTIAL: `withCredentials=true`, no localStorage/sessionStorage secrets, 401 refresh retry posts empty body to legacy `/auth/refresh`, auth API still targets legacy `/login` and `/logout`; workspace switching is server-backed. |
| MFA/WebAuthn | `backend/app/routes/mfa.py` | PARTIAL: management/authentication for already-authenticated users; not a complete primary NIAM login factor. Device biometrics are not national identity. |
| Account status gate | `AccountService.authenticate` | IMPLEMENTED at service level: dummy hash, rejects pending verification/suspended/disabled/deactivated/inactive, temporary lockout after five failures. |
| Rate limiting | `rate_limit_auth` on legacy and NIAM routes | PARTIAL: login/refresh have limits; recovery/Passkey coverage needs verification. |

## Critical gaps to address locally

1. Secure canonical logout must require the current NiamActor and only terminate an owned current session, with a separate actor-guarded logout-all path.
2. Canonical session actor checks must include access JTI blacklist, `expires_at`, idle timeout, and account locked status.
3. Refresh rotation needs a persistent `refresh_family_id` and replay detection that terminates the whole family.
4. Canonical auth routes need cookie-aware refresh/login/logout contracts while preserving secure bearer response for native clients.
5. Session list/terminate routes need ownership or governed admin authorization; no client-supplied account ID may be authoritative.
6. Frontend should explicitly use cookie refresh safely and expose session/forbidden/expired states without storing secrets; do not replace the legacy stack without a migration contract.

## Safety decision at inventory stage

No production configuration, deployment, database, public registration, government identity, OCR, NFC, biometrics, merge, or push actions are permitted. If authentication security, session integrity, tenant isolation, or authorization boundary cannot be proven, final decision must be `SAFE_STOP` and `AUTHENTICATION_PARTIAL` or `AUTHENTICATION_BLOCKED`.
