# GULA Route Inventory — 2026-08-17

هذه الحزمة تحفظ الجرد المحلي لمسارات GULA وتحليل الحماية والتكرار والعزل. تشمل الحزمة مسارات API المركبة فعلياً في OpenAPI، وruntime dependencies، وتعريفات routers الساكنة، ومسارات Web/PWA وdesktop/mobile.

| Artifact | Scope |
|---|---|
| `api-openapi.json` | OpenAPI schema exported locally in `RUNTIME_MODE=openapi` |
| `api-operations.json` | 2,029 operations with method/path/tags/security metadata |
| `runtime-routes.json` | 2,034 flattened runtime routes with dependency names |
| `backend-static-routes.csv` | AST-extracted route decorators from `backend/app` |
| `router-declarations.csv` / `router-includes.csv` | APIRouter declarations and include calls |
| `runtime-no-deps.tsv` | 54 routes without direct runtime dependencies |
| `runtime-duplicates.tsv` / `runtime-duplicate-details.txt` | Three duplicate method/path groups and implementation details |
| `frontend-routes.tsv` | 95 React route declarations from `frontend-v3/src/routes/index.tsx` |
| `mobile-desktop-routes.tsv` | 37 GoRoute declarations from desktop/mobile |
| `no-security-openapi.tsv` | 144 OpenAPI operations without operation-level security metadata |
| `route-security-report.md` | Main findings, evidence, priorities, and limitations |
| `summary.json` | Count summary for all inventories |

## Important interpretation

The inventory is a local source/runtime audit, not an external penetration test. No production requests, brute force, token guessing, authorization bypass, or database mutation were performed. A missing OpenAPI security array does not by itself prove that an endpoint is public, because an endpoint may invoke an internal authorization helper or inherit a router-level dependency. Conversely, client-side `RoleGuard` and `InstitutionalOnlyRoute` do not replace server-authoritative authorization.

The main report identifies public registration routes that conflict with the project policy requiring account-request-only onboarding, a public phone-based patient-history path, token-based public result paths, three duplicate runtime method/path groups, and operational endpoints requiring explicit security contracts.

## Security handling

No passwords, tokens, API keys, signing material, keystores, certificates, environment files, session secrets, or raw temporary logs are included in this bundle. The OpenAPI and route artifacts were checked as report data; any warnings in the report are descriptions of controls and not credential values.

## Status

This bundle does not convert any `PARTIAL`, `UNVERIFIED`, or `NOT_BUILT` result into `PASS`. It does not remove SAFE_STOP, does not start P5, and does not authorize merge or production deployment.

See [`route-security-report.md`](./route-security-report.md) for the complete analysis.
