# Command 05 — Account Recovery and Security Lifecycle Hardening Report

**Date:** 2026-08-16
**Repository:** `samertts/gula-platform`
**Branch:** `chore/security-ddos-hardening-clean`
**Base commit:** `480eb7e3` (Command 04 final)
**Scope:** Recovery Request → Verification → Risk Decision → Recovery → Session Revocation → Re-authentication → Account Restored, with Web/PWA/Android/iOS/Flutter Desktop contract parity.

## Executive decision

> **Final status: `RECOVERY_PARTIAL`**

Command 05 materially hardens the implemented password-recovery lifecycle and closes the principal identity-isolation, token-replay, session-revocation, audit, and high-risk bypass gaps found during the baseline. The result is deliberately **not** marked `RECOVERY_REMEDIATED`: high-risk operations remain `PENDING_REVIEW` because no stronger verified provider or step-up contract is available; native SDK compilation is not available in this environment; PostgreSQL migration execution was rehearsed offline only; and recovery email delivery is disabled and fail-closed.

No production database, environment variable, provider, deployment setting, registration setting, or government/biometric/OCR/NFC integration was activated or modified.

## Implemented recovery architecture

The canonical aggregate is `AccountRecoveryRequest` in `backend/app/models/account_recovery.py`. It carries a server-generated `request_id`, `correlation_id`, account kind and account identifier, operation, assurance and risk metadata, hashed token digest, HMAC-derived idempotency digest, expiry, attempt counters, state timestamps, and audit context.

The password-reset state path is:

```text
REQUESTED → VERIFYING → VERIFIED → APPROVED → RECOVERED
```

The aggregate also supports terminal and safe-stop states: `FAILED`, `EXPIRED`, `REJECTED`, `LOCKED`, `SUSPICIOUS`, `CANCELLED`, and `PENDING_REVIEW`. Password recovery uses a 32-byte URL-safe server secret, stores only SHA-256 digest material, enforces a configurable 5–60 minute TTL (default 15 minutes), enforces a configurable 3–10 attempt bound (default 5), and invalidates the token after completion.

At the recovery completion boundary, `perm_version` is bumped and a `session_revoked` audit event is written before the recovery is committed as `RECOVERED`. Existing access and refresh tokens therefore require re-authentication. A new password must be 12–256 characters and non-blank after normalization.

## Findings and remediation evidence

| # | Finding | Problem / root cause | Fix implemented | Security evidence and tests | Remaining risk / boundary |
|---:|---|---|---|---|---|
| 1 | No canonical recovery aggregate | Legacy reset was a one-table helper and could not represent risk, lifecycle, correlation, or terminal states. | Added `AccountRecoveryRequest` plus explicit state constants and timestamps. | `tests/identity/test_account_recovery_security.py` validates state transitions, expiry, lock, replay, and completion. | Non-password high-risk operations intentionally stop at `PENDING_REVIEW`. |
| 2 | Reset-token lookup was O(N) | Legacy code scanned all active reset hashes because no indexed digest lookup existed. | Added indexed `token_digest` and direct lookup, with request-id scoping and row locking. | Recovery suite covers valid lookup, invalid token, cross-account request-id mismatch, and replay rejection. | PostgreSQL lock behavior still requires staging/production-like verification; no production DB was changed. |
| 3 | No atomic single-use completion | The old route cleared a token after mutation but lacked a canonical state/consume boundary. | Verification and completion are state-gated; completion clears `token_digest`, sets `consumed_at`, and commits the recovered state under a row lock. | HTTP verify→reset single-use test and replay test pass; recovery suite is 10/10. | SQLite/local test locking is not equivalent to a multi-worker PostgreSQL race test. |
| 4 | Session families survived password reset | Password reset did not invalidate existing sessions. | `complete_password_recovery()` bumps `perm_version`; `session_revoked` is audited. | Audit evidence regression and auth/MFA/revocation suite pass; full backend is 2714 passed, 4 skipped. | Native clients must complete their normal re-authentication handling in native CI. |
| 5 | MFA device removal lacked step-up | A normal authenticated session could remove a stronger security control. | MFA removal requires a bounded MFA session token and TOTP/step-up validation, then bumps `perm_version` and audits revocation. | Auth/MFA regression is 39/39; input bounds are statically checked. | Provider and hardware-backed MFA behavior remains outside this local environment. |
| 6 | MFA removal did not revoke sessions | Device removal left existing sessions active. | Permission-version revocation is applied after removal and a `session_revoked` event is recorded. | Post-removal token rejection and audit regression pass. | End-to-end native session invalidation requires Android/iOS/Flutter CI. |
| 7 | Change-password audit was incomplete | The mutation did not produce an explicit session-revocation event. | Change-password now bumps permission version and records both `session_revoked` and `password_changed`. | Auth regression and audit assertions pass. | Existing legacy audit storage keeps request/correlation fields in details rather than dedicated columns. |
| 8 | Account enumeration risk | Unknown and known addresses could receive distinguishable recovery behavior. | `/auth/forgot-password` returns the same generic response for both branches and is rate-limited. | Enumeration-resistant HTTP test and frontend E2E test pass. | A real email provider is not enabled; delivery is intentionally fail-closed. |
| 9 | Missing idempotency | Repeated recovery submissions could create multiple concurrent recovery paths. | `Idempotency-Key` is normalized and stored only as a SHA-256 digest; an existing digest returns the existing request. Older active password-reset requests are cancelled when a new one is accepted. | Idempotency and supersession assertions pass. | Distributed replay behavior should be verified with the production database and rate-limit store. |
| 10 | Cross-account isolation was not proven | The previous route did not expose a canonical request/account binding contract. | Token verification can be scoped by `request_id`; the server compares the digest and binds the aggregate to account kind/id. Status lookup requires the current account and matching kind. | New cross-account token/request-id regression passes; ownership test returns no cross-account status. | Tenant-level staging tests should cover every concrete organization/lab authorization dependency. |
| 11 | High-risk recovery bypass gap | Contact change, lost device, MFA reset, passkey recovery, and account unlock had no safe stronger-assurance path. | Added authenticated `POST /auth/security/recovery-request`; all five operations create `PENDING_REVIEW` only and explicitly change no account security state. | High-risk PENDING_REVIEW ownership test passes; server is authoritative. | These operations remain incomplete until an approved provider/manual-review workflow exists. No bypass was introduced. |
| 12 | Recovery token URL leakage in web UX | Token could remain in browser history or client storage. | `RecoveryPage.tsx` reads the URL once, removes token parameters with `history.replaceState`, and never stores the secret in localStorage. | Recovery E2E includes URL sanitization and verify→reset behavior; Playwright auth spec is 8/8 for the recovery additions. | Browser history/referrer behavior must still be checked in deployed production headers and browser matrix. |
| 13 | Frontend was single-step | The UI did not model server-authoritative request, verification, pending-review, and reset states. | Web/PWA `RecoveryPage` implements request→verify→reset; `SecurityPage` exposes safe high-risk review requests; writes are allowlisted. | TypeScript 0 errors, ESLint 0 warnings, Vitest 61/61, build PASS, Playwright full suite 53/53 plus recovery auth spec 8/8. | Native UI screens were not built in this command; native API contracts were updated. |
| 14 | Native recovery parity missing | Android, iOS, and Flutter had no canonical recovery API methods. | Updated Android `AuthApi`/DTOs, iOS endpoints/client structs, and Flutter Desktop endpoints/auth manager for forgot, verify, reset, and request-id contracts. | Source-level endpoint/DTO inspection completed. | Android SDK, Xcode, and Flutter/Dart toolchains are unavailable locally; native compilation is unverified. |
| 15 | Secrets in logs/audit risk | Recovery tokens, passwords, OTPs, or session secrets must not be emitted. | Audit details contain operation/state/reason/request/correlation/account metadata only; raw secrets are not logged or persisted. Token rate keys use a digest prefix. | Grep review found no token/password/OTP logger arguments; Bandit passes on recovery/MFA files. | Production log aggregation and redaction rules still require environment validation. |
| 16 | Migration safety was unverified | The new aggregate requires a schema table and indexes. | Added `20260816_0023_account_recovery_requests.py`, registered metadata, and preserved one Alembic head. | Single head is `20260816_0023`; offline upgrade/downgrade SQL rehearsal for 0022→0023 passes. | PostgreSQL apply/rollback and lock/index timing remain unverified because no staging database is available. |

## Recovery operation inventory

The inventory below distinguishes **safe contract coverage** from full operational availability. A `PARTIAL` result is intentional where the server refuses to perform a high-risk mutation without a stronger approved control.

| Operation | Status | Evidence | Decision rationale |
|---|---|---|---|
| Forgot password request | **COMPLETE** | Generic response, rate limit, idempotency digest, recovery aggregate, no token in response. | Server behavior is enumeration-resistant and fail-closed. |
| Recovery token verification | **COMPLETE** | `/auth/recovery/verify`, digest lookup, request-id scoping, expiry/attempt lock, audit. | Token possession is verified server-side and replay is blocked by state. |
| Password reset completion | **COMPLETE** | `/auth/reset-password`, password policy, `perm_version` bump, session revocation, token consume. | Full implemented password-recovery lifecycle is covered by regression tests. |
| Re-authentication after reset | **COMPLETE** | Permission-version invalidation of existing sessions and explicit response contract. | Old sessions require the normal login/refresh path again. |
| Recovery status | **COMPLETE** | Authenticated `GET /auth/recovery/{request_id}` with account-kind and account-id ownership scope. | Cross-account status reads are denied. |
| Contact/email/phone change recovery | **PARTIAL** | Safe request contract exists and returns `PENDING_REVIEW`; no mutation occurs. | No weaker recovery path is allowed; provider/manual-review implementation is absent. |
| Lost-device recovery | **PARTIAL** | Safe `PENDING_REVIEW` request contract exists. | Device control is not bypassed without equivalent assurance. |
| MFA reset/recovery | **PARTIAL** | MFA removal has step-up and revocation; broad MFA reset remains manual-review only. | No automatic recovery bypass is permitted. |
| Passkey recovery | **PARTIAL** | Passkey-related high-risk operation is manual-review only. | No backend private-key recovery or unsafe replacement path exists. |
| Account unlock | **PARTIAL** | Manual-review request contract exists. | Security lock versus administrative lock workflow is not fully implemented. |
| Security-alert delivery | **PARTIAL** | Audit events exist for recovery and revocation. | External notification/provider contract is not enabled. |
| Legacy in-memory citizen identity helper | **BLOCKED** | Not used as production account recovery. | It has no durable persistence, TTL, rate limiting, atomic consume, or production authorization boundary. |
| Native mobile/desktop build proof | **UNVERIFIED** | Contracts were updated, source review completed. | Required SDKs/toolchains are unavailable in this environment. |
| PostgreSQL migration execution | **UNVERIFIED** | Offline SQL rehearsal passes. | No staging/production database access was used or changed. |
| Recovery email delivery | **BLOCKED / FAIL-CLOSED** | `ACCOUNT_RECOVERY_EMAIL_ENABLED=false`; absent SMTP host moves request to `PENDING_REVIEW`. | Delivery cannot be claimed as successful without a configured provider. |

## Cross-platform parity matrix

| Surface | Status | Implemented evidence | Verification boundary |
|---|---|---|---|
| Web React | **PASS** | `RecoveryPage.tsx`, `SecurityPage.tsx`, canonical endpoints, URL sanitization, pending-review UX. | TypeScript, ESLint, Vitest, Vite build, and Playwright pass. |
| PWA | **PASS** | Uses the same Vite/PWA frontend route and server-authoritative API client as Web. | Build and browser E2E prove the shared bundle; no separate PWA backend was introduced. |
| Android | **PARTIAL** | `AuthApi.kt` and `AuthDtos.kt` use forgot-password, recovery/verify, reset-password, request-id, and optional refresh-token contracts. | Android SDK is unavailable locally; compile and device E2E remain unverified. |
| iOS | **PARTIAL** | `APIEndpoint.swift` and `APIClient.swift` include typed recovery request/verify/reset methods. | Xcode/iOS SDK is unavailable locally; compile and device E2E remain unverified. |
| Flutter Desktop | **PARTIAL** | `api_endpoints.dart` and `auth_manager.dart` include request/verify/reset methods and request-id flow. | Flutter/Dart toolchain is unavailable locally; compile and desktop E2E remain unverified. |
| Backend API | **PASS for implemented contract** | Canonical routes, server-side authorization, rate limits, state machine, audit, revocation. | Full backend and targeted security suites pass. |

`PARTIAL` on native surfaces means **contract parity is present but native build evidence is missing**; it does not mean a client-side bypass was added.

## Validation record

| Gate | Result | Evidence |
|---|---|---|
| Full backend pytest | **PASS** | 2714 passed, 4 skipped, 0 failed; 2718 collected; 302.88 seconds. |
| Recovery security suite | **PASS** | 10/10 passed, including enumeration, idempotency, transitions, expiry, lock, replay, cross-account isolation, HTTP single-use, audit revocation, and PENDING_REVIEW ownership. |
| Auth/MFA/revocation regression | **PASS** | 39/39 passed. |
| Frontend TypeScript | **PASS** | 0 errors. |
| Frontend ESLint | **PASS** | 0 warnings. |
| Frontend Vitest | **PASS** | 61/61 passed. |
| Frontend build | **PASS** | Production build completed successfully. |
| Playwright | **PASS** | Full auth spec 53/53 from the frontend gate; recovery additions 8/8. |
| Ruff | **PASS** | Targeted Command 05 files passed `E9,F,I001`. |
| Bandit | **PASS** | Recovery/MFA files passed security scan. |
| `git diff --check` | **PASS** | No whitespace errors. |
| Alembic topology | **PASS** | Single head `20260816_0023`. |
| Alembic offline rehearsal | **PASS** | Upgrade/downgrade SQL rehearsal 0022→0023. |
| Android compile | **BLOCKED / UNVERIFIED** | Android SDK unavailable locally. |
| Flutter/Dart compile | **BLOCKED / UNVERIFIED** | Flutter/Dart unavailable locally. |
| iOS/Xcode compile | **BLOCKED / UNVERIFIED** | Xcode unavailable locally. |
| PostgreSQL rehearsal | **UNVERIFIED** | No PostgreSQL/staging environment available; offline SQL only. |

Known test warnings are pre-existing ecosystem/deprecation warnings and did not produce failures. They are not treated as Command 05 security acceptance failures.

## Production safety gate

The deployment review was read-only. Vercel SSO Protection remains enabled with `all_except_custom_domains`; the latest relevant deployment is externally **BLOCKED** by SSO protection rather than by an identified Command 05 code failure. The state is not bypassed and no deployment protection was disabled.

The safety-critical feature flags remain conservative:

| Control | Effective value / position | Safety interpretation |
|---|---|---|
| `PUBLIC_SELF_REGISTRATION_ENABLED` | `false` | No public registration activation. |
| `ENABLE_API_DOCS` | `false` | API documentation remains disabled in the protected environment. |
| `ACCOUNT_RECOVERY_EMAIL_ENABLED` | `false` | No unverified delivery claim; recovery delivery fails closed to manual review. |
| `ACCOUNT_RECOVERY_MANUAL_REVIEW_ENABLED` | `true` | High-risk operations stop at `PENDING_REVIEW`. |
| Government Identity / OCR / NFC / biometrics | Not activated | No provider, security architecture, or legal-basis shortcut was introduced. |
| Production DB/environment changes | None | No production state was modified. |

## Required follow-up before `RECOVERY_REMEDIATED`

The next acceptance gate should run native Android, iOS, and Flutter/Desktop compile plus device-level session-revocation tests in their supported CI environments. A PostgreSQL staging rehearsal should apply and roll back migration `20260816_0023`, exercise concurrent verification/completion, verify index plans, and confirm audit persistence under the actual database isolation level.

A real recovery notification provider may be enabled only after its credentials, delivery failure behavior, privacy review, rate-limit integration, redaction rules, and operational monitoring are approved. The provider must never turn a delivery or provider failure into verification success. High-risk contact, lost-device, MFA-reset, passkey-recovery, and unlock operations require a reviewed workflow with assurance no weaker than the control being bypassed.

## Files changed by Command 05

| Area | Files |
|---|---|
| Backend recovery | `backend/app/models/account_recovery.py`, `backend/app/security/recovery.py`, `backend/app/routes/password_reset.py`, `backend/app/config.py`, `backend/app/models/__init__.py`, `backend/app/security/mfa_service.py` |
| MFA/session/audit | `backend/app/routes/mfa.py`, `backend/tests/test_auth_infrastructure.py` |
| Migration | `backend/migrations/env.py`, `backend/migrations/versions/20260816_0023_account_recovery_requests.py` |
| Security tests | `backend/tests/identity/test_account_recovery_security.py` |
| Web/PWA | `frontend-v3/src/pages/auth/RecoveryPage.tsx`, `frontend-v3/src/pages/security/SecurityPage.tsx`, `frontend-v3/src/api/client.ts`, `frontend-v3/src/api/endpoints.ts`, `frontend-v3/e2e/auth.spec.ts` |
| Android | `mobile/android/app/src/main/java/io/gula/android/data/remote/api/AuthApi.kt`, `mobile/android/app/src/main/java/io/gula/android/data/remote/dto/AuthDtos.kt` |
| iOS | `mobile/ios/Gula/Core/Networking/APIEndpoint.swift`, `mobile/ios/Gula/Core/Networking/APIClient.swift` |
| Flutter Desktop | `mobile/desktop/lib/core/api/api_endpoints.dart`, `mobile/desktop/lib/core/auth/auth_manager.dart` |
| Documentation | `docs/command05-baseline-inventory.md`, this report |

**Conclusion:** Command 05 is safe to commit as a hardening change. It closes the verified server-side recovery gaps without introducing a recovery bypass, public registration, provider impersonation, cross-account access, token logging, or production drift. The correct release label remains **`RECOVERY_PARTIAL`** until the documented external verification gates are completed.
