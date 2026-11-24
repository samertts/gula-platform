# Frontend-v3 bounded operationalization — 2026-11-24

## Scope and authority

The mandate requested operationalization of the 92 non-operational frontend-v3
surfaces. Exploration established that **no clinical or business page can be
safely activated** without owner policy decisions, registry expansion, or a
server-side rollout decision. This batch therefore operationalizes the only
defensible first batch: **session plus three registered authorization bootstrap
reads**. It does not activate patient, order, result, sample, billing, device,
pharmacy, or citizen data surfaces.

Status: `BOUNDED ENGINEERING OPERATIONALIZATION · CLINICAL SURFACES STILL
NON-OPERATIONAL · NOT ACCEPTED`.

## Operationalized contracts

| Contract | Path | Frontend change | Authority boundary |
| --- | --- | --- | --- |
| `session.read` | `GET /session` | Existing live call retained; explicit regression evidence added | Already live and allowlisted; no policy change |
| `authorization.context.read` | `GET /authz/me` | Added exact typed GET method and allowlisted read | UX context only; backend remains sole authority |
| `authorization.permissions.read` | `GET /authz/me/permissions` | Added exact typed GET method and allowlisted read | Flat permission list is not reinterpreted as local grant authority |
| `authorization.menu.read` | `GET /authz/me/menu` | Added exact typed GET method and allowlisted read | Menu data is non-authoritative in this batch |

The three authorization reads are loaded only for a confirmed live session.
Demo mode issues no `/authz/*` request. Any failure or malformed response
clears the reflected context and yields empty permissions/menu. No RoleGuard,
RBAC map, clinical gateway rollout, or server-side permission rule was changed.

## Changed files

* `frontend-v3/src/api/client.ts` — added the three registered GET reads to
  `INITIALIZATION_READ_ALLOWLIST`; write barrier unchanged.
* `frontend-v3/src/api/endpoints.ts` — added `authorizationApi` with exact
  paths and conservative response types.
* `frontend-v3/src/contexts/AuthContext.tsx` — live-only bootstrap, fail-closed
  handling, and reflected context exposed through `useAuth`.
* `frontend-v3/src/api/client.writeBarrier.test.ts` — allows the three reads
  and asserts all corresponding writes remain blocked.
* `frontend-v3/src/api/authorizationApi.test.ts` — exact path/GET-only tests
  and malformed-response safety.
* `frontend-v3/src/contexts/AuthContext.authorization.test.tsx` — live success,
  live failure, and demo isolation.
* `frontend-v3/e2e/session-authorization.spec.ts` — RTL and responsive checks
  at 320px, 390px, and 1440px with no `/authz/*` request in demo mode.

## Verification commands and results

Commands ran from `frontend-v3` with Node `v24.18.0`.

| Command | Result | Exit | Evidence |
| --- | --- | --- | --- |
| `./node_modules/.bin/tsc --noEmit` | clean | `0` | `V4_FRONTEND_TYPECHECK_GREEN_2026_11_24.txt` |
| `./node_modules/.bin/vitest run --passWithNoTests --exclude 'e2e/**'` | `18` files, `62` tests passed | `0` | `V4_FRONTEND_UNIT_GREEN_2026_11_24.txt` |
| `node scripts/verify-data-source-governance.mjs` | `94` surfaces explicitly classified | `0` | `V4_FRONTEND_DATA_SOURCE_GOVERNANCE_GREEN_2026_11_24.txt` |
| `node scripts/verify-contract-governance.mjs` | contract governance passed | `0` | `V4_FRONTEND_CONTRACT_GOVERNANCE_GREEN_2026_11_24.txt` |
| `PLAYWRIGHT_CHROMIUM_EXECUTABLE=/home/samertts/.cache/ms-playwright/chromium-1228/chrome-linux64/chrome ./node_modules/.bin/playwright test` | `56 passed (3.8m)` | `0` | `V4_FRONTEND_E2E_FULL_GREEN_2026_11_24.txt` |

No unit-test warnings or skips were reported. No frontend lint or production
build was claimed in this batch.

## Preserved failures and classification

1. `V4_FRONTEND_PNPM_INSTALL_TIMEOUT_2026_11_24.txt` — `pnpm typecheck` first
   invoked a registry install and timed out after supply-chain verification.
   Classification: package-manager/environment failure, not a TypeScript
   failure. Rerun with the local `tsc` binary passed.
2. `V4_FRONTEND_E2E_SESSION_BOOTSTRAP_TIMEOUT_2026_11_24.txt` — the first E2E
   version waited on an absent backend `/session` proxy and timed out at
   320px. Classification: harness dependency on unavailable backend.
3. `V4_FRONTEND_E2E_SESSION_DESKTOP_TIMEOUT_2026_11_24.txt` — a later run timed
   out on the third viewport during session bootstrap. Classification:
   harness timing flake; isolated desktop case passed
   (`V4_FRONTEND_E2E_DESKTOP_ISOLATED_GREEN_2026_11_24.txt`).
4. `V4_FRONTEND_E2E_FULL_FAILURE_2026_11_24.txt` — `44 passed`, `12 failed`
   because two pre-existing specs hardcode `/usr/bin/chromium`, which is absent.
   Classification: harness/browser-path defect. Rerun with the installed
   Playwright Chromium path fixed 11 failures; the remaining single failure was
   a pre-existing reports-spec timing flake.
5. `V4_FRONTEND_E2E_FULL_BROWSER_ONE_FLAKE_2026_11_24.txt` — `55 passed`,
   `1 failed` on the reports heading at 390px. Classification: flaky existing
   E2E assertion; all nine reports cases passed in isolation
   (`V4_FRONTEND_E2E_REPORTS_ISOLATED_GREEN_2026_11_24.txt`), and the full
   suite passed on rerun.

The final green new-spec evidence is
`V4_FRONTEND_E2E_SESSION_GREEN_2026_11_24.txt` (`3 passed`).

## Residual status

* Operationalized: 4 bootstrap surfaces (`session.read` plus three
  authorization reads).
* Still non-operational/blocked: the remaining 90 of the original 94 inventoried
  surfaces, including all clinical and business data pages.
* No PHI or real patient data was used. No server rollout flag was changed.
* Owner acceptance and Stable v1.0.0 remain out of scope.
