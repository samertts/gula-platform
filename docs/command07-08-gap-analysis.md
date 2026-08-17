# GULA Commands 07–08 — Gap Analysis

**Baseline commit:** `ef84866ce786937514887efed78a17540a39a7a2`
**Branch:** `chore/security-ddos-hardening-clean`
**Scope:** Frontend identity integration, cross-platform auth/session parity, and final lifecycle QA/closure.

## Executive classification

The current repository already has a server-authoritative recovery and workspace model, but the frontend and native clients do not yet provide equal evidence of that authority. The safest implementation boundary is therefore to harden the Web/PWA contract first, add tests for server-state precedence and session races, and classify native compilation/storage/deep-link claims as `UNVERIFIED` until their toolchains run in CI.

| Area | Baseline finding | Classification | Safe action |
|---|---|---|---|
| Web auth state | `AuthContext` models most backend states and does not auto-select a workspace, but refresh calls and identity restoration are not single-flight and lack request-generation guards. | PARTIAL | Add single-flight identity refresh, stale-result suppression, and explicit context invalidation. |
| Web route guards | `ProtectedRoute` improves UX but most protected pages still use hard-coded role arrays. | PARTIAL | Keep guards non-authoritative; render `WORKSPACE_REQUIRED`, forbidden, and service states without implying security authority. |
| API client refresh | Refresh is single-flight, but request correlation headers and an explicit non-idempotent retry policy are incomplete. | PARTIAL | Add request/correlation IDs, preserve one retry only for safe replayable requests, and never retry mutations automatically after refresh. |
| API error mapping | Central mapping exists for 401/403/409/429/5xx/offline. | PASS with tests pending | Align AuthContext and UI behavior to this classifier and add regression coverage. |
| Storage | Web auth uses HttpOnly server cookies; demo markers use sessionStorage. | PARTIAL | Keep demo markers non-sensitive and clear them on terminal session events; verify no tokens/secrets in browser storage. |
| Recovery UX | Web recovery flow is server-backed and enumeration-resistant from Command 05. | PASS on Web | Add final lifecycle regression and ensure all terminal/error states are visible without secret disclosure. |
| Membership/workspace UX | Membership lifecycle and context labels exist; role/entitlement is intentionally not fabricated. | PARTIAL | Add explicit empty/error/offline/access status treatment and preserve backend authority. |
| Android | Encrypted token storage and refresh repository exist; full workspace lifecycle parity is not evidenced. | UNVERIFIED | Do not claim parity; compile and instrumentation evidence required. |
| iOS | Startup trust is reconstructed partly from local metadata/keychain presence; full server session validation and credential replay concerns remain. | PARTIAL/UNVERIFIED | Avoid broad native refactor without Xcode/CI; document and test only safe contract changes. |
| Flutter/Desktop | Rich auth state and single-flight refresh exist, but effective permissions/workspace object parity is incomplete. | PARTIAL/UNVERIFIED | Verify Dart build and align typed context only where backend contract exists. |
| Lifecycle closure | Backend regression suites prove many isolated transitions, but a single production-like full lifecycle across all platforms is unavailable locally. | PARTIAL | Add deterministic backend lifecycle regression and classify environment-dependent stages explicitly. |
| Production alignment | Production DB/runtime and Vercel protected deployment cannot be fully inspected locally. | UNVERIFIED/BLOCKED_EXTERNAL | Read-only verification only; no deployment or production DB changes. |

## Stop conditions

A cross-tenant read or write, authorization bypass, stale privilege after revocation, token/session leakage, audit failure, unsafe migration, or production configuration drift is a `SAFE_STOP`. No UI change may be used to compensate for a missing backend contract, and no native parity claim may be promoted to `PASS` without a successful native build/test artifact.

## Planned implementation order

The implementation will proceed in this order: first harden the Web/PWA auth state and API client; next add regression tests for refresh/logout/context races and error states; then run backend lifecycle and security suites; then run available Web/PWA quality gates; finally classify Android/iOS/Flutter and production evidence without inventing results. Any backend dependency discovered during frontend work will be documented as `BACKEND_DEPENDENCY` rather than implemented as a client-side bypass.

## Follow-up verification after the initial closure commit

A read-only GitHub Actions review was performed for commit `856e2734fa07f818875c4c49e956b4960b3ff392`. The repository Actions permission is enabled and allows all actions, but the representative reruns for Formatting, CI Syntax, Android, iOS, and Flutter completed with `runner_id: 0`, an empty runner name, zero reported steps, and no accessible logs through the configured GitHub integration. These runs are therefore classified as `BLOCKED_EXTERNAL`; source changes must not be inferred from an unavailable job log.

The local reproduction separated code from environment. `npm ci --dry-run` succeeds against the existing `frontend-v3/package-lock.json`; changed Web files pass TypeScript, ESLint, unit tests, and Vite build. Repository-wide Prettier and Ruff-format checks still identify legacy formatting outside the Command 07–08 change set, so broad auto-formatting was intentionally not committed.

The correct offline Alembic range rehearsal is `20260815_0022:20260816_0023` for upgrade and `20260816_0023:20260815_0022` for downgrade. Both generated SQL successfully without a database connection. No local PostgreSQL server, Docker, psql, or pg_isready tool is available; live/staging PostgreSQL remains `UNVERIFIED`.
