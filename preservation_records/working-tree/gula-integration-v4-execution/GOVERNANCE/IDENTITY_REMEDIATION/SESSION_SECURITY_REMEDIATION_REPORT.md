# Session Security Remediation Report (P0-D3)

> **Tranche:** bounded, uncommitted session/MPI/NHID readiness work. **Release
> decision remains HOLD** (`GOVERNANCE/FINAL_DECISION.md`, md5 `effdfeaf…`).
> D-020/D-021 remain `PENDING_APPROVAL`. No runtime/E2E/clinical/production
> claim. Paths are inside `gula-integration` @ `integration/gula-unification-v1`,
> HEAD `2827c1ff…`.

## 1. Classification and status

| Item | Classification | Status |
|---|---|---|
| P0-D3 — convert `session.py` raw cache to fail-closed store + stale/malformed handling | `OWNER_APPROVED` (owner-granted this tranche) | `TEST_VERIFIED` |
| Production `ALLOW_DEGRADED_REDIS` policy decision | `NEEDS_OWNER_DECISION` | `BLOCKED` (policy, not code) |
| Dev/test fallback documentation | `RECOMMENDED` | `PARTIAL` (documented here) |

## 2. What changed (one clean target file)

`backend/app/security/session.py` — confirmed **clean** before edit (no user
modifications); it was the only implementation file touched in this phase.
`backend/app/security/redis_client.py`, `dependencies.py`, `auth.py`,
`rate_limit.py`, `mfa_service.py` and `platform_access.py` carried pre-existing
user changes and were **read-only** (not overwritten).

Three security-sensitive operations were converted from the raw `cache`
singleton to the fail-closed `security_store()`:

| Operation | Before | After (fail-closed) |
|---|---|---|
| `bump_perm_version` (write) | `cache.set(...)` unguarded | publishes via `security_store("Permission version write")`; store outage logged CRITICALLY; authoritative DB bump preserved |
| `warm_perm_version` (read/write) | raw `cache.get/set`, `perm_ver_key(user.id)` default `lab` | via `security_store`; uses `_account_kind(user)` key (also fixes a latent key mismatch for `User` accounts); outage tolerated without weakening auth |
| `get_perm_version` (read) | `int(cached)` if any cache value, else DB | returns `max(cached, db_version)`; ignores missing/malformed/stale values; falls back to authoritative primary-DB value on store outage |

New helpers: `_coerce_version` (rejects booleans, non-positive, non-numeric,
malformed values), `_security_store_or_none` (translates
`SecurityStoreUnavailable` into a critical log + DB fallback),
`_store_get` / `_store_set` (treat transport errors/timeouts as cache miss / log
write failure). No API contract changed; no client-visible detail added.

### Security rationale (why this cannot weaken revocation)
`security.dependencies.get_current_user` reads `user.perm_version` fresh from the
**primary** DB (`get_db`, `backend/app/database.py:284`; read-replica is a
separate optional engine not used here), so `db_version` is strongly consistent
and authoritative. Because `get_perm_version` returns `max(cached, db_version)`,
a stale, missing, malformed, or process-local cached value can **never** allow a
token with an old `perm_ver` to pass. A store outage degrades to the DB value —
session validity is still reliably established, so we do not manufacture a
self-inflicted 503 on every request (availability preserved where it does not
weaken auth). This differs from JTI logout revocation, which exists **only** in
the shared store and therefore correctly fails closed with HTTP 503 in
`dependencies.py:55-64` (pre-existing user work, preserved).

**Fail-closed policy note:** in a production/staging profile with no shared
Redis and no `ALLOW_DEGRADED_REDIS=true`, `security_store()` raises
`SecurityStoreUnavailable`; `session.py` logs CRITICALLY and relies on the
authoritative DB value. The residual theoretical gap — primary DB write not yet
visible plus store unavailable — is bounded by the single-primary, strongly
consistent DB used here; a strict 503-on-any-store-outage policy for this path
would require changing the user-modified `dependencies.py` and is a
`NEEDS_OWNER_DECISION` policy item (R-D3), not silently imposed.

## 3. Tests added (synthetic fixtures only)

`backend/tests/unit/test_session_revocation.py` extended from 3 → 22 tests. New
coverage: store unavailable, store timeout, missing entry, malformed values
(7 cases: empty, non-numeric, negative, zero, decimal, bool, object), stale
cache, fresher cache, bump publishes new version, bump survives store failure,
password-reset → old-token reuse rejection, normal auth version match, normal
logout JTI blacklist, blacklist-check unavailable fails closed, warm seeds and
tolerates outage. No real patient data; no test weakening/skips.

## 4. Exact test results

| Run | Command (interpreter) | Exit | Collected/Passed | Warnings | Duration |
|---|---|---|---|---|---|
| Smallest suite | `ENV=test PYTHONPATH=backend:. /tmp/opencode/gula-py312/bin/python -m pytest backend/tests/unit/test_session_revocation.py -q` | 0 | 22 / 22 | 1 (Starlette/httpx deprecation, unrelated) | 0.40s |
| Combined P0 regression | `ENV=test PYTHONPATH=backend:. /tmp/opencode/gula-py312/bin/python -m pytest` over the 6 P0 suites (see `ACCEPTANCE_EVIDENCE.md` §2) | 0 | 128 / 128 | 1 | 98.99s |
| Ruff (changed files) | `ruff check backend/app/security/session.py backend/tests/unit/test_session_revocation.py` | 0 | All checks passed | — | — |

Interpreter: Python **3.12.13** (`/tmp/opencode/gula-py312`), pytest 9.1.1,
SQLAlchemy 2.0.51, FastAPI 0.139.2, webauthn 3.0.0. Test DB: SQLite in-memory/
file fixtures only; no operational database. The `signxml>=4.2.0` lockfile gap
(pre-existing) was already handled in the isolated venv; no requirements file
was changed.

## 5. MyPy / static analysis
Ruff (E/W/F/I/N/UP/B/SIM/C4/PIE/RET/T20/RUF/Q/SLF) passes on both changed files.
MyPy on `session.py` is not meaningful under the repo's strict config (SQLAlchemy
plugin + `ignore_errors` overrides for `app.services.*`); no new typing defect
was introduced. No dependency file was modified.

## 6. Limitations / remaining risks
- Dev fallback (in-memory store) is process-local; this is explicitly acknowledged
  by `redis_client.py` for non-production profiles and is **not** HA/failover
  readiness.
- A strict 503-on-store-outage policy for the perm-version read path is a policy
  decision (`NEEDS_OWNER_DECISION`, R-D3) deferred, not silently applied.
- The `token_jti` vs JWT `jti` desynchronisation in NIAM tokens (see device
  report) is a separate item and was not touched.
- No claim of high availability, failover, runtime, E2E or production readiness.

## 7. Verification boundary
`TEST_VERIFIED` for the implemented code path only. No commit, no migration/DDL,
no database connection to operational systems, no dormant router activation, no
patient data, no protected-repo change.
