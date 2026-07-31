# PROGRAM-009B Phase 2 Report — API Certification (Live PG + Redis)

Status: **COMPLETE** | Branch: `remediate-security-001` | Commits: `ba1f836d` (audit fix), plus `e572f787`, `4e8eb062`, `17c88991` (P1 residue)
Verified against: live PostgreSQL 16 (`172.18.0.2:5432`, 337 tables) + Redis 7 (`172.18.0.3:6379`), full app startup with lifespan.

## Objective

Certify the production API surface end-to-end against the real database:
OpenAPI contract completeness, standardized error shapes (404/401/422/429),
rate limiting under load, immutable audit trail, and traceability headers.

## Results

| Check | Result |
|---|---|
| OpenAPI version | 3.1.0, `GET /openapi.json` → 200 |
| Endpoints | **1,641 paths / 1,963 operations** / 483 schemas |
| Security schemes | HTTPBearer (1) |
| Operations missing responses | **0** |
| `/docs`, `/redoc` | 200 / 200 |
| Unknown path | 404, `{"detail": "Not Found"}`, `application/json` |
| Protected endpoint (no token) | 401, `{"detail": "Not authenticated"}` |
| Public endpoints | `/setup/status`, `/test-profiles` → 200 (no auth leak) |
| Validation errors | 422 RFC-style Pydantic body (`type/loc/msg/input`) on `/login`, `/register`, `/register/citizen`, `/register/doctor` |
| Authz boundary | `/register/staff` → 401 (staff provisioning requires auth) |
| Rate limiting | 10×401 then **429** `{"detail": "Too many login attempts. Please wait a moment."}` with `X-RateLimit-Limit/Remaining/Reset` + `Retry-After` |
| Traceability | `X-Request-ID` present on API responses |
| Health | `/health`, `/health/live`, `/health/ready` → 200; DB circuit `closed`, pool healthy |
| Audit chain (live PG) | **22/22 entries intact**, `verify_audit_chain` → `status: intact` |
| Audit tamper resistance | UPDATE on `audit_logs` → blocked by trigger (`RestrictViolation`) |

## Critical Defect Found & Fixed (ba1f836d)

**`log_action()` crashed every audit write on live PostgreSQL.** The service
performed `INSERT` + `flush()` + `UPDATE ... SET chain_hash=...`, but the
`audit_logs_immutable` trigger forbids UPDATE on `audit_logs` →
`RestrictViolation` → login completely broken on the real DB (SQLite tests
never saw it because no trigger exists there).

**Fix** (`backend/app/services/audit_service.py`): on the PostgreSQL dialect,
pre-assign `entry.id` from `audit_logs_id_seq` (`nextval`), compute the chain
hash against the full row, then perform a **single INSERT**. Hash input
contract unchanged (id included), so chain anchors stay compatible.

**Verified live**: 12 failed-login attempts → 12 `audit_logs` rows, each with
a chained hash; `verify_audit_chain` confirms integrity; direct UPDATE/DELETE
attempts rejected by trigger; chain verification still reports `intact`.

## Rate-Limit Certification Notes

- `ENV=test` probes exercise the limiter's code path but do not trip 429s —
  `rate_limit.py::_check()` intentionally bypasses counting in test mode
  (keeps HTTP integration suites stable). This was confirmed by code
  inspection and by the 30×/patients probe (all 401, no 429).
- **Production-mode probe** (`ENV=production`, live PG/Redis, strong
  secrets): 10 login failures → 401, then requests **429** with full
  `X-RateLimit-*` + `Retry-After` headers. Limiter correctly counts failures
  per identity (email HMAC) with Redis persistence and block expiry.
- `app/config.py` silently `exit(1)`s on weak/missing secrets in production —
  probes must supply strong `SECRET_KEY`/`REFRESH_TOKEN_SECRET`/
  `ENCRYPTION_KEY`/`NID_HMAC_KEY` (generated at `/tmp/opencode/strong_keys.env`).

## Findings / Notes

1. `/health` responses carry no `X-Request-ID` — intentional: health paths are
   in `middleware._SILENT_PATHS` (no logging/headers on health probes).
2. Governance bootstrap at startup logs `ai_model_registry` sync failure when
   the live DB predates the AI-platform migration — non-fatal warning; the
   table exists in the schema (migration `20260719_0001`). Deferred.
3. First 3 `audit_logs` sequence values are gaps (id starts at 4) — consumed
   by pre-fix crashed transactions. Harmless; chain hash covers each written row.
4. `health_body` confirms circuit breakers (db/redis) closed, pool sized 5,
   no degraded mode — the live instance is fully healthy.

## Artifacts

- `/tmp/opencode/p2_api_validate.py` — repeatable probe harness
  (OpenAPI, auth/404/422 shapes, health, headers, X-Request-ID)
- `/tmp/opencode/ratelimit_probe.py` — 14-request login hammer (ENV=production)
- `/tmp/opencode/p2_api_report.json` — full evidence payload

## Next Phase

P3 — End-to-end clinical workflows on the live DB (order → sample → result →
verify → audit chain), offline/recovery drill, notification fan-out, and
mobile token lifecycle.
