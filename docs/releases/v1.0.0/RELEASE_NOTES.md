# GULA Platform — v1.0.0 Release Notes

> Certified: **PROGRAM-06 (Backend ↔ Frontend Parity) + PROGRAM-STABLE-001
> (Stable Readiness) + PROGRAM-STABLE-002 (Shared Core / Domain Sovereignty)**
> Tag recommendation: `v1.0.0` — branch: `remediate-security-001`
> Date: 2026-08-02 (re-verified 2026-08-03)

This is the **Stable v1.0** release of the GULA national healthcare platform.
It supersedes `v1.0.0-RC2` (certified by PROGRAM-010). Backend remains the
single source of truth; the frontend is a complete operational representation
of it (100% API/RBAC/workflow/entity parity certified).

## Certification summary

| Gate | Result |
|---|---|
| Backend full test suite | ✅ 2845 passed / 0 failed (8m00s) |
| Frontend tests | ✅ 122/122 (vitest) |
| Type check / Lint | ✅ tsc 0 errors · eslint 0 errors · ruff baseline 379 preserved |
| Production build | ✅ PASS |
| Enterprise validation | ✅ VERDICT PASS |
| STABLE harness (full) | ✅ CERTIFIED — 0 fail checks, mandatory gates green |
| API parity | ✅ 593/593 frontend calls → live backend routes |
| RBAC parity | ✅ 25 roles × 16 permissions — 0 drift |
| Workflow parity | ✅ 14/14 production workflows |
| Entity parity | ✅ 26/26 models |
| i18n parity | ✅ 399/399 keys ar↔en |
| Domain isolation | ✅ PASS (5 approved EHR-consumer read contracts + 1 risk-registered write) |
| Import cycles | ✅ 0 module-level cycles |
| Migrations | ✅ chain intact (54 revisions) |

## What's new since v1.0.0-RC2

- **Full parity certification (PROGRAM-06):** every production entity, API,
  workflow, role, permission, dashboard, report, form, search, filter, menu,
  notification, validation, error, and audit event is represented on both
  sides; zero drift.
- **Shared Core (PROGRAM-STABLE-002):** the national/EHR declarative metadata
  (`shared/models/base.SharedBase`) and the rule-engine domain
  (`shared/rules_engine`) now live in Shared Core; domains are sovereign;
  workspaces are isolated; zero cross-domain administration.
- **Import cycles eliminated:** `app.ehr ↔ app.national` and
  `app.kernel ↔ app.national` (backward-compatible re-exports).
- **Performance:** 200 foreign-key indexes added (migration
  `20260802_0002_stable_fk_indexes`); load-robust benchmark methodology.
- **Security:** health-exchange API key moved from hardcoded to
  env/key-file backed constant-time verification (deny-by-default); demo
  credential and OTP configuration audits added (`docs/audit/`).

## Fixed in this release

- `mobileApi.info()` runtime 404 (`/auth/mobile/app-info` → `/mobile/app-info`)
- Arabic-first error messages (`detail_ar` preferred by `getErrorMessage`)
- Ruff SIM102 nested-if in `identity/services/authorization_service.py`
- Flaky load-sensitive performance benchmarks (best-of-3 / min-of-3 sampling)
- STABLE harness scanner truthfulness (severity model per constitution §32.3,
  approved-contract allowlist, module-level-only cycle detection)

## Deployment

Follow the certified deployment bundle pattern:
`docs/releases/v1.0.0-RC2/DEPLOYMENT.md` (artifacts unchanged; the stable
release adds the FK-index migration which runs automatically via Alembic).
Environment template: `.env.example` / `.env.production` (placeholders only).
Backend requires `shared/` volume mount and `REDIS_URL` with password.

## Remaining (non-blocking, tracked)

- Architecture engine advisory score 21.4/100 (L2 cycles = 0) — see
  `reports/stable/MASTER_REMAINING_WORK.md` and `docs/ai/MASTER_ROADMAP.md`
- Dormant module UI activation (national release roadmap)
- 1 approved cross-domain write contract (nursing→EHR, risk-registered)
