# GULA Commands 07–08 — Identity Integration and Lifecycle Closure Report

**Author:** Manus AI
**Date:** 2026-08-17
**Repository:** `samertts/gula-platform`
**Branch:** `chore/security-ddos-hardening-clean`
**Baseline commit:** `ef84866ce786937514887efed78a17540a39a7a2`
**Candidate commit:** `ab1e2a681d22cf83a04e7107866e7bcb90f37d6a`

## Executive summary

Commands 07 and 08 were executed against the actual repository state after Commands 01–06. The safe and locally verifiable scope was implemented primarily in Web/PWA because the native Android, iOS, and Flutter toolchains are not available in this environment. The backend remained unchanged in this pass; its existing server-authoritative account recovery, membership, workspace, authorization, audit, and revocation controls were regression-tested rather than reimplemented.

The final status is **`IDENTITY_LIFECYCLE_PARTIAL`**. The Web/PWA integration is materially hardened and has passing local evidence. The backend lifecycle and isolation regression groups pass. Native parity and production alignment remain `UNVERIFIED` or `BLOCKED_EXTERNAL` where no compiler, PostgreSQL staging, or unprotected Vercel deployment is available. This is an evidence classification, not a claim that the unverified capabilities are broken.

> No production deployment, production database modification, automatic merge, security bypass, public-registration activation, government identity activation, OCR/NFC/biometrics activation, or deletion of historical audit evidence was performed.

## 1. Changes made

| Area | Problem/root cause | Change | Security evidence | Remaining risk |
|---|---|---|---|---|
| AuthContext restoration | Concurrent restore/refresh results could write state after a newer identity event. | Added a single-flight identity restore and generation checks before applying session, membership, workspace, or error results. | Existing auth-state tests plus full Web typecheck and unit suite pass. | React integration race coverage is indirect; browser/server integration still needs CI with a real API. |
| Login double-submit | Multiple login submissions could overlap and produce nondeterministic state. | Added a single-flight login promise and invalidated pending identity/context generations at login start. | TypeScript, ESLint, and auth regression tests pass. | Native login flows are not changed in this pass. |
| Logout race | Logout could overlap with refresh or context requests. | Added single-flight logout and invalidated pending identity/permission requests before clearing state. | Auth lifecycle regression suite passes; no token storage is used by Web/PWA. | Full cross-device logout-all proof requires staging and native CI. |
| Workspace switch | Old workspace context and permissions could remain visible while the server validated the new workspace. | Clear old workspace/context/permission reflection before switch; apply returned context only after server response and generation checks; prevent overlapping switches. | WorkspaceSelector tests and auth-state tests pass; backend trusted-scope tests pass. | API conflict behavior still depends on staging latency and real session state. |
| Permission refresh | Permission response could arrive after a newer workspace or membership response. | Added permission generation checks and discarded stale responses. | Command 06 authorization-context tests and Web unit suite pass. | Native permission caches require separate builds. |
| API correlation | Requests did not consistently carry frontend request/correlation IDs. | Added `X-Request-ID` and `X-Correlation-ID` headers, preserving correlation across refresh. | Static review and TypeScript compile pass; backend middleware already consumes server-side request context. | Production observability correlation requires runtime verification. |
| Refresh retry safety | Generic 401 retry could be unsafe for non-idempotent mutations. | Refresh replay is restricted to `GET`, `HEAD`, and `OPTIONS`; POST/PUT/PATCH/DELETE are not automatically replayed after refresh failure. | New `isSafeRefreshRetryMethod` regression covers safe and unsafe methods. | Some API operations may need explicit user retry UX after re-authentication. |
| API error UX | Backend error classes existed but needed integration evidence. | Kept centralized 401/403/409/429/5xx/offline mapping and aligned client/session events with it. | `errorHandling` tests pass; Playwright auth/recovery passes. | Full error matrix requires controlled backend responses in integration CI. |
| Workspace UX | Context labels and membership scope needed to remain visibly server-derived. | Workspace selector shows current organization/facility/workspace/access status and never infers authority from selection alone. | WorkspaceSelector tests pass; no client scope is treated as authoritative. | Role/Entitlement remains “not displayed” when the backend contract does not provide it; no fake entitlement was added. |
| Storage security | Browser persistence could accidentally become an auth source. | Audited Web storage; only demo markers, locale, and theme are persisted. Auth remains server-cookie based. | Repository grep found no browser storage of token/password/OTP/secret/private-key values. | Native secure-storage audit remains unverified until Android/iOS/Flutter builds run. |
| Registration UX | Public registration must remain disabled while account requests remain human/review based. | Existing RegisterPage clearly states that it submits an account request only and does not create a session or activate permissions; no public-registration activation was made. | Backend flag remains false; UI text and route behavior were reviewed. | Production flag/runtime still needs read-only staging verification. |

## 2. Backend lifecycle and security evidence

The existing backend was regression-tested after the Web/PWA changes. The focused lifecycle set included account request, verification, login/session security, recovery, MFA, refresh rotation, memberships, workspaces, authorization, audit, clinical context, and tenant-isolation tests.

| Backend evidence | Result |
|---|---:|
| Focused Command 07/08 lifecycle and isolation group | **251 passed, 2 skipped** |
| Previous full backend suite after Command 06 | **2719 passed, 4 skipped, 0 failed** |
| Command 06 authorization-context regressions | **5/5 passed** |
| Role/workspace/audit regression group | **29/29 passed** |
| Recovery security group | **10/10 passed** |
| Auth/MFA/revocation regression from Command 05 | **39/39 passed** |

The backend evidence continues to support default-deny, server-resolved workspace scope, cross-organization and cross-facility isolation, role-assignment management gates, invitation single-use behavior, audit context, and revocation propagation. No new backend migration was introduced by Commands 07–08.

## 3. Full lifecycle validation

The locally reproducible lifecycle evidence covers the following server-backed transitions and denial classes. The frontend is not treated as the authority; every sensitive operation still travels through the backend contract.

| Lifecycle stage | Local evidence | Status |
|---|---|---|
| Account request | Account request security tests and request UX reviewed | PASS locally |
| Verification | Verification and OTP hardening tests pass | PASS locally |
| Approval/activation | Backend account/membership lifecycle tests pass; human approval remains a policy boundary | PARTIAL |
| Login | Auth API/security tests and Playwright auth flow pass | PASS locally |
| Session creation/refresh/rotation | Session and refresh-rotation tests pass | PASS locally |
| Workspace discovery/selection/switch | Backend workspace tests plus WorkspaceSelector/auth-state tests pass | PASS locally |
| Authorization/resource scope | Command 06 trusted-scope and tenant-isolation tests pass | PASS locally |
| Logout/logout-all/revocation | Backend revocation tests and Web logout invalidation logic pass | PARTIAL |
| Recovery/re-authentication | Command 05 recovery security and E2E pass | PASS locally |
| Suspension/lock/revocation | Backend status and session tests pass | PASS locally |
| Offline/provider failure | Central error mapping and offline UX are tested; real provider outage is not simulated in production | PARTIAL |

The following conditions were not promoted to PASS without evidence: real email-provider delivery, real PostgreSQL rollback with existing data, native lifecycle builds, protected deployment access, and live runtime configuration.

## 4. Final security audit

No new critical security failure was found in the executed local suites. The main protections are server-authoritative authorization, explicit workspace context, no frontend-only permission authority, no automatic replay of non-idempotent mutations after refresh, generation-based stale-state suppression, and no sensitive browser storage.

The following final checks were covered by existing backend tests and focused regression groups: authentication bypass, authorization bypass, cross-tenant access, cross-organization/facility/workspace access, role manipulation, privilege escalation, invitation replay, expired/revoked membership, refresh rotation, recovery replay, enumeration resistance, MFA boundaries, and authorization race-sensitive state updates. A production-like adversarial network test across every resource endpoint remains outside local evidence and must run in CI/staging.

## 5. Frontend quality and UX evidence

| Gate | Result |
|---|---:|
| TypeScript | **0 errors** |
| ESLint | **0 errors/warnings** |
| Vitest unit suite excluding Playwright files | **68 tests passed, 19 files** |
| Playwright full local suite | **55/55 passed** |
| Vite/PWA build | **PASS**, service worker generated |
| Auth, API error, workspace, storage-barrier regressions | **PASS** |
| Keyboard/semantic focus review | **PARTIAL**; existing accessible labels/roles and focus rings preserved, full screen-reader matrix needs browser CI |
| Localization source coverage | **PARTIAL**; Arabic Iraqi/standard, English, Kurdish, Turkmen, Assyrian, and Persian resources exist, but native and long-string visual QA is not fully built |
| Offline UX | **PASS for classification and safe messaging locally; PARTIAL for full offline re-entry workflow** |

The E2E runner emitted expected local proxy connection warnings for `/api/session` because the isolated frontend server had no live backend attached; the auth spec itself passed all eight tests. This warning is not treated as a production success signal.

## 6. Cross-platform matrix

| Capability | Web | PWA | Android | iOS | Flutter/Desktop | Evidence | Status |
|---|---|---|---|---|---|---|---|
| Auth state model | Implemented | Same Web bundle | Existing native code, no current build | Existing native code, startup trust gap remains | Rich state enum exists | Web source/tests/build | Web/PWA PASS; native PARTIAL/UNVERIFIED |
| Login/logout | Tested | Same bundle | Recovery/login code exists | Login/logout code exists | Login/logout code exists | Web Playwright; native source only | Web/PWA PASS; native UNVERIFIED |
| Refresh/rotation | Single-flight refresh; safe retry policy | Same bundle | Encrypted prefs/repository code | Session manager/API middleware code | Single-flight refresh exists | Web tests; native source inspection | Web/PWA PASS; native UNVERIFIED |
| Workspace selection/switch | Server response only; stale context cleared | Same bundle | No complete Command 07 evidence | No complete Command 07 evidence | Partial context support | Backend + Web tests | Web/PWA PASS; native PARTIAL/UNVERIFIED |
| Recovery | Command 05 flow and E2E | Same bundle | API contract updated in Command 05 | API contract updated in Command 05 | API contract updated in Command 05 | Recovery suite and Web E2E | Web/PWA PASS; native UNVERIFIED |
| Secure storage | HttpOnly cookie; no sensitive browser storage | Same bundle | EncryptedPrefs source exists | Keychain source exists but credential replay/startup trust require CI review | Secure storage source exists | Source inspection only | Native UNVERIFIED |
| Deep links | Recovery URL sanitization exists | Same bundle | Not compiled | Not compiled | Not compiled | Web recovery E2E | Web/PWA PASS; native NOT_BUILT/UNVERIFIED |
| Accessibility/localization | Existing labels/RTL/locales and unit evidence | Same bundle | Not built | Not built | Not built | Web source/unit only | Web/PWA PARTIAL; native NOT_BUILT |

`NOT_BUILT` is not interpreted as a technical failure, but it is not a PASS. No native parity claim is made without a successful compiler and test artifact.

## 7. Database, migration, and rollback evidence

No Command 07–08 schema migration was added. The existing Alembic chain remains single-head `20260816_0023`. Offline SQL rehearsal from the actual predecessor `20260815_0022` to `20260816_0023` and back completed successfully in the prior verified migration gate. PostgreSQL staging and existing-data compatibility remain unverified because no PostgreSQL staging connection is available locally.

A production rollback was not attempted and must not be attempted from this task. The safe rollback rehearsal evidence is therefore limited to migration SQL generation and source-level transactional behavior; a full known-good deployment → candidate → simulated failure → rollback → health/data verification requires human-approved staging infrastructure.

## 8. Production alignment, Vercel, and runtime

The local branch and remote branch were aligned at baseline `ef84866c` before this candidate pass. Vercel read-only inspection found project `gula-platform` with SSO protection enabled for `all_except_custom_domains`, password protection disabled, and trusted IP protection disabled. The latest listed deployment corresponds to Command 06 commit `ef84866c` and is `BLOCKED`; no deployment was created or modified by this task.

| Production alignment item | Evidence | Status |
|---|---|---|
| Git branch/commit | Local branch and remote baseline aligned before candidate changes | PASS for local baseline |
| Vercel project identity | Project `gula-platform` discovered read-only | PASS read-only |
| Vercel SSO protection | `enabled: true`, `deploymentType: all_except_custom_domains` | PASS read-only |
| Latest deployment | Command 06 SHA `ef84866c`, state `BLOCKED` | BLOCKED_EXTERNAL |
| Production backend/runtime config | No write performed; no live runtime inspection available | UNVERIFIED |
| Live PostgreSQL/Alembic state | No staging/live DB connection | UNVERIFIED |
| Feature flags | Local backend source confirms fail-closed registration/recovery email behavior from prior commands | PARTIAL; production runtime unverified |

## 9. Human approval list

The following items require explicit human or organizational approval and are not inferred from CI: production deployment or rollback, production database changes, Vercel SSO/protection changes, live PostgreSQL verification credentials, native CI provisioning, legal review for identity or healthcare flows, government identity integration, OCR/NFC/biometrics activation, public registration activation, email provider activation, and any breaking API contract change.

## 10. P0/P4/P5 decision

| Program | Current status | Rationale |
|---|---|---|
| P0 Identity & Account Lifecycle | **PARTIAL** | Web/PWA and backend local evidence is strong, but native builds, live DB/runtime, provider delivery, and production deployment remain unverified or blocked. |
| P4 | **Not declared complete** | Acceptance criteria require production-aligned evidence and governance approvals not available here. |
| P5 | **GATED / DO NOT START** | P4 is not complete and Command 08 explicitly forbids starting the next command automatically while critical/high evidence gaps remain. |

## 11. Exact next action

The exact next action is a human-approved CI/staging verification gate: run Android Gradle, iOS Xcode, Flutter/Dart, PostgreSQL migration and rollback rehearsal, and protected staging E2E against the candidate commit. Only after those artifacts are reviewed should a human decide whether to merge PR #226 or open a follow-up remediation task. No automatic merge or production deployment should occur.

## References

[1]: `command07-08-gap-analysis.md` — actual Command 07/08 baseline and safe implementation boundary.
[2]: `command06-authorization-context-hardening-report.md` — prior authorization-context evidence and residual risks.
[3]: `../frontend-v3/src/contexts/AuthContext.tsx` — Web/PWA auth/session/context implementation.
[4]: `../frontend-v3/src/api/client.ts` — request correlation and refresh retry policy.
[5]: `../frontend-v3/src/api/client.writeBarrier.test.ts` — API barrier and safe-retry regression tests.
[6]: `../frontend-v3/src/components/workspace/WorkspaceSelector.tsx` — server-derived workspace UX.
[7]: `../backend/tests/identity/test_account_recovery_security.py` — recovery security regression evidence.
[8]: `../backend/tests/identity/test_authorization_context_command06.py` — server-side context and revocation evidence.
[9]: `/home/ubuntu/.mcp/tool-results/2026-08-17_07-48-11.519455690_vercel_get_project_deployment_protection_33817840.json` — Vercel deployment protection read-only result.
[10]: `/home/ubuntu/.mcp/tool-results/2026-08-17_07-48-25.490851603_vercel_list_deployments_a82a8533.json` — Vercel deployments read-only result.

## 12. Follow-up execution after the initial closure commit

A read-only GitHub Actions review and representative rerun were performed for commit `856e2734fa07f818875c4c49e956b4960b3ff392`. Actions is enabled for the private repository and allows all actions. Nevertheless, the rerun jobs for Formatting, CI Syntax, Android, iOS, and Flutter completed with `runner_id: 0`, an empty runner name, zero reported steps, and no accessible logs through the configured GitHub integration. The outcome is classified as **`BLOCKED_EXTERNAL`**, not as a source-code failure. A human with repository Actions/check-run access must inspect runner service and billing/policy diagnostics before treating those checks as required evidence.

The local reproduction separated code failures from environment failures. `npm ci --dry-run` succeeds against the existing `frontend-v3/package-lock.json`. The changed Web files pass TypeScript, ESLint, targeted unit tests, and the Vite build. Repository-wide Prettier and Ruff-format checks still report legacy formatting outside the Command 07–08 change set; broad auto-formatting was intentionally not committed because it would create an unrelated high-volume diff.

The correct offline Alembic rehearsal was executed with the actual adjacent revisions: upgrade `20260815_0022:20260816_0023` and downgrade `20260816_0023:20260815_0022`. Both generated SQL successfully without connecting to a database. No local PostgreSQL server, Docker/Podman runtime, `psql`, or `pg_isready` is available, so live/staging PostgreSQL remains **`UNVERIFIED`**.

Additional safe Web/PWA evidence was added. The recovery page now uses a tested helper that removes query and fragment material from recovery deep links before replacing browser history; the error classifier has explicit 401/403/409/422/429/5xx/offline coverage; and the locale contract verifies supported locale identity and direction declarations. These changes do not create a client-side authorization path.

The complete local Vitest suite excluding Playwright files passed **68/68 tests across 19 files**. The complete local Playwright suite passed **55/55 tests** across authentication, recovery, navigation, responsive layouts, workspace safety, billing/insurance, FHIR, reporting, and RTL surfaces. TypeScript, targeted ESLint, and the PWA build also passed after the minimal-diff reapplication.
