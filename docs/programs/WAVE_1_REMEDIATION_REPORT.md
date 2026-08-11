# GULA Wave 1 Remediation Report

**Program:** GULA repository audit + remediation (branch `remediate-security-001`)
**Date:** 2026-08-11
**Status:** Wave 1 complete (6/6 planned items); 5 remaining P1 items deferred to later waves
**Change record:** `GULA_CHANGE_CONTROL.md` CR-11..CR-16

---

## 1. Wave 1 Scope

Executed the Wave 1 items from `GULA_MASTER_EXECUTION_PLAN.md` that were
approved as part of the audit follow-up ("keep working" direction from the
Program Director), plus documented deferrals D-1/D-2.

| # | Item | Class | Status |
|---|---|---|---|
| S1 | AI admin endpoints unauthorized | D (security fix) | **DONE** `dde4faec` |
| S2 | Insurance lookup endpoint unauthorized | D (security fix) | **DONE** `d1c5b1f7` |
| F-07/L-01 | Missing web legal pages (privacy/terms) | D (feature) | **DONE** `173a9350` |
| S7 | Duplicate `push:` keys in `build-images.yml` | D (CI fix) | **DONE** `bb50c60f` |
| S8 | Missing `lighthouse.config.json` | D (CI fix) | **DONE** `eecd74d3` |
| S9 | iOS workflow builds despite missing workspace | D (CI fix) | **DONE** `b6be6ecf` |
| D-1 | iOS rebuild | deferred (P2) | **DOCUMENTED** — CI now fails fast with reference |
| D-2 | Desktop drift fix | deferred (P2) | **DOCUMENTED** — `GULA_CURRENT_REPOSITORY_STATE.md` |
| S3 | `/auth/oauth2/callback` missing auth | P2 | PENDING (next wave) |
| S5 | No `security_opt` in compose | P2 | PENDING (next wave) |
| S6 | No ingress authn | P2 | PENDING (next wave) |
| C4 | GitHub Actions unpinned actions | P2 | PENDING (next wave) |

## 2. Changes Delivered

### S1 — AI admin authorization (`dde4faec`)
- `backend/app/routes/ai.py`: both admin endpoints (`/api/ai/operations`,
  `/api/ai/providers`) now require `require_permission("system:admin")`
  (master_admin-only, matching `backend/app/routes/admin.py:33`).
- Active Ollama probing removed — no more outbound `/api/tags` calls at
  runtime; legacy provider detection is config-only.
- `/providers` response trimmed to the declared `AIProviderStatus` contract:
  `name`, `type`, `configured`, `reachable`, `model`. Removed leak of
  `base_url`, `available_models`, `cost`, `source`.
- **Why `system:admin`:** runtime permissions live in
  `shared/rbac/permissions.py`. `ai:access` exists only in
  `backend/app/core/bootstrap/permissions.py` and is NOT in runtime
  `EXTENDED_ROLE_PERMISSIONS` — it would 403 everyone. `system:admin` is the
  only permission the master_admin role actually holds for this surface.
- **Regression tests:** `backend/tests/unit/test_ai_admin_routes_auth.py` (7).
  Ruff clean. OpenAPI now shows `security: [{"HTTPBearer": []}]` on both paths.
- **Frontend impact:** `AIPage.tsx:67` is the only consumer of `aiApi`
  (`.pending()`); `operations`/`providers` are unused by the UI → safe.

### S2 — Insurance lookup authorization (`d1c5b1f7`)
- `backend/app/routes/insurance.py`: `require_permission("patients:read")`
  (receptionist/doctor/lab_manager/pathologist/admin — the clinical roles that
  legitimately need it; technician excluded).
- Every lookup now writes an immutable audit record
  (`action="insurance_lookup"`, actor role + IP) and commits, satisfying the
  audit-trail requirement for PHI-bearing lookups.
- **Regression tests:** `backend/tests/unit/test_insurance_route_auth.py` (6).
  Ruff clean.

### F-07/L-01 — Legal pages (`173a9350`)
- `frontend-v3/src/pages/legal/LegalPage.tsx`: shared public layout
  (brand header, locale/theme toggles, back-to-login, footer with cross-links)
  parameterized by document kind.
- `PrivacyPolicyPage` (6 sections) + `TermsPage` (10 sections).
- Routes `/privacy` and `/terms` registered as **top-level public routes**
  outside the authenticated shell (no `ProtectedRoute`).
- `AuthLayout` footer now links to both pages → reachable from the
  unauthenticated login page.
- Full ar/en translations (30 keys per language) under `legal` scope.
- **Verified:** `tsc --noEmit` 0 errors, `vite build` OK (2.51 s),
  `vitest` 171/171 pass, `eslint` 0.

### S7/S8/S9 — CI fixes (`bb50c60f`, `eecd74d3`, `b6be6ecf`)
- S7: `build-images.yml` had two `push:` keys; the second silently overrode
  the first. Merged into a single `push:` (branches `main` + tags `v*` +
  paths) → main-branch image build trigger restored.
- S8: `frontend-v3/lighthouse.config.json` created (referenced by
  `frontend-pwa.yml` but absent): `staticDistDir: ./build`, preset
  `lighthouse:no-pwa`, perf/a11y/best-practices/seo thresholds.
- S9: `mobile-ios.yml` gains `check-build-system` job that fails fast when
  `mobile/ios/Gula.xcworkspace` is absent (references D-1 deferral);
  `lint`/`test`/`ui-test` now `needs: [check-build-system, ...]`.
  Job graph verified: check-build-system → lint/test/ui-test → build →
  upload-to-testflight.
- All 26 workflows still parse via `yaml.safe_load`.

## 3. Verification Summary

| Gate | Result |
|---|---|
| Backend regression tests (S1/S2 scope) | 13/13 pass |
| Ruff on changed backend files | clean |
| OpenAPI security annotation | HTTPBearer present on both AI paths |
| Frontend `tsc --noEmit` | 0 errors |
| Frontend `vite build` | success (2.51 s) |
| Frontend `vitest` | 171/171 pass |
| Frontend `eslint` (changed scope) | 0 |
| Workflow YAML parse | 26/26 OK |
| iOS job graph | correct (check-build-system gates all) |
| Pre-commit hook | PASS on all 6 commits |

## 4. Commits (branch `remediate-security-001`)

```
05fd61df  docs(program): GULA audit program set (9 docs)
dde4faec  fix(auth): gate AI admin endpoints + trim provider response (S1)
d1c5b1f7  fix(auth): gate insurance lookup + audit trail (S2)
bb50c60f  ci: merge duplicate push keys in build-images.yml (S7)
eecd74d3  ci: add missing lighthouse config (S8)
b6be6ecf  ci: gate iOS builds on workspace presence (S9)
173a9350  fix(frontend): public privacy policy + terms of use pages (F-07/L-01)
```

All commits individually revertible (single `git revert` restores prior state).

## 5. Remaining Work (P1/P2 not in Wave 1)

- **S3** — `/auth/oauth2/callback` (evidence `backend/app/routes/oauth2.py:201`)
  missing authorization → next wave.
- **S5** — `docker-compose.full.yml` has zero `security_opt` entries.
- **S6** — no ingress-level authentication in the stack.
- **C4** — GitHub Actions uses unpinned (mutable `@v3`/`@v4`) actions.
- **D-1/D-2** — documented deferrals awaiting PD final decision.

## 6. Risks / Notes

- `ai:access` remains dead in runtime RBAC (harmless; not promoted). When the
  AI provider admin surface is built out, decide the runtime role mapping.
- No DB migrations, no model changes, no API removals in this wave — behavior
  of all other endpoints unchanged.
- Push of `remediate-security-001` to `origin` performed after this report.

---

*Companion: `GULA_CHANGE_CONTROL.md` (CR-11..CR-16), `GULA_MASTER_EXECUTION_PLAN.md`,
`GULA_FINAL_REPORT.md`, `GULA_RISK_REGISTER.md`.*
