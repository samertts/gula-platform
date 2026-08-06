# GULA Platform — Security Certification (PROGRAM-BETA Phase 1)

**Date:** 2026-08-06
**Status:** CERTIFIED with 2 verified fixes (all applied, tested, committed-ready)

---

## 1. Executive Summary

The GULA backend and frontend were subjected to real SAST (Semgrep OWASP Top Ten +
`p/default`), secret scanning, dependency auditing, and manual code review of the
authentication, authorization, session, audit, and encryption layers.

**Verdict: CERTIFIED — production security posture is strong.** One real SQL
injection was found and fixed, one dependency advisory (HIGH, react-router) was
resolved by upgrading to the patched release, and hardening was added to two
operator-run scripts and the nginx frontend configuration.

| Layer | Posture | Evidence |
|---|---|---|
| AuthN/AuthZ | STRONG | bcrypt + HS256 JWT (env secrets, weak-secret guard), per-route auth, RBAC/ABAC |
| Sessions | STRONG | server-side revocation, token blacklist, workspace binding, max concurrent sessions |
| Data at rest | STRONG | Fernet + HMAC encryption, hashed national IDs, audit hash-chain |
| Injection | **FIXED** | 1 real SQLi in AI knowledge graph + 1 operator-script hardening |
| Dependencies | **FIXED** | react-router 7.18.2 (HIGH, RSC-CSRF) → 8.3.0 patched; fast-uri fixed |
| Headers/Transport | STRONG | CSP, HSTS, nosniff, frame-ancestors=none on API middleware AND nginx |
| Secrets | CLEAN | no hardcoded secrets in source; `.env.example` uses placeholders |
| Supply chain | CLEAN | npm audit 0 vulnerabilities; bandit/semgrep/gitleaks wired in CI |

---

## 2. Fixed Findings

### 2.1 SQL Injection — `backend/app/ai/knowledge_graph.py` (REAL, CRITICAL)
**Severity:** High (CWE-89) — exploitable when `aliases`/`properties` contain a single quote.

**Root cause:** JSON payloads were serialized and string-interpolated into a raw
`sqlalchemy.text()` statement without bind parameters:

```python
aliases_json = f"'{_jsonify(aliases or [])}'::jsonb"   # json.dumps does not escape single quotes
db.execute(text(f"INSERT ... VALUES (..., {aliases_json}, {props_json})"))
```

**Fix:** payloads now flow through bind parameters with a JSONB cast:
```python
db.execute(text(
    "INSERT INTO ai_knowledge_nodes (...) "
    "VALUES (:nt, :eid, :label, :desc, CAST(:aliases AS jsonb), CAST(:props AS jsonb))"),
    {"aliases": _jsonify(aliases or []), "props": _jsonify(properties or {}), ...})
```

**Regression test:** `tests/test_ai_platform.py::TestKnowledgeGraph::test_create_node_sql_injection_safe`
captures the compiled SQL via a monkeypatched connection and asserts the payload
`x' OR '1'='1` never appears inline and is bound as a parameter. **Passes.**

### 2.2 Operator-script identifier injection — `scripts/reencrypt_encryption_key.py`
**Severity:** Medium (defense-in-depth; gated by an existence check, but identifiers
were string-concatenated into SQL).

**Fix:** `_validate_identifier()` allows only `^[a-zA-Z_][a-zA-Z0-9_]*$` and is enforced
for `--table`/`--column` before any SQL is built.

**Regression tests:** `tests/unit/test_reencrypt_script.py::TestIdentifierValidation`
(4 tests: accepts plain, rejects injection payloads, rejects quoted, main() rejects). **Pass.**

### 2.3 Dependency advisory — `react-router` (HIGH, GHSA-qwww-vcr4-c8h2)
RSC-mode CSRF bypass in `react-router >=7.12.0 <8.3.0`. The SPA does not use the
unstable RSC APIs (plain `createBrowserRouter` client-side), so it was not directly
exploitable — but best practice is to run the patched release.

**Fix:** migrated all 10 files from `react-router-dom@7.18.2` → `react-router@8.3.0`
(the patched release; `react-router-dom` 8.x is not published). The used API surface
(`createBrowserRouter`, `RouterProvider`, `Link`, `Navigate`, `Outlet`, `useLocation`,
`useNavigate`, `useParams`) is identical.

**Verification:** `tsc --noEmit` 0 errors, `vite build` 2.4s, 122/122 frontend tests pass,
eslint 0 errors. `npm audit` = 0 vulnerabilities (fast-uri transitive also fixed).

### 2.4 nginx frontend security headers — `config/nginx/frontend.conf`
The containerized SPA nginx server block lacked the security headers already present
on the API nginx config. Added `X-Content-Type-Options`, `X-Frame-Options: DENY`,
`Referrer-Policy`, `Permissions-Policy`, `Content-Security-Policy`
(`default-src 'self'`, `frame-ancestors 'none'`, `form-action 'self'`), and
`Strict-Transport-Security`. Syntax validated with `nginx -t` (include-context wrapper).

---

## 3. Verified-Safe Findings (False Positives reviewed)

| Location | Finding | Assessment |
|---|---|---|
| `reference/infrastructure/repositories.py:131,135` | `text(f"...")` | Safe — conditions are static `text()` fragments; all values via bind params (`literal_binds: False`) |
| `shared/audit/service.py:93` | `text(f"...")` | Safe — WHERE fragments static; values via `params` dict |
| `ai/vector_store.py:161,264` | `text(f"...")` | Safe — fragments static; `:lab`, `:ct`, `:vec` bound |
| `security/auth.py:55` | bcrypt hash literal | Intentional timing-safe dummy hash to prevent user enumeration |
| `generate_demo_data.py` | `text(f"...")` | Demo tool; identifiers are constants/DB-derived ints |
| `reencrypt_encryption_key.py:125,129,148` | `text(f"...")` | Now guarded by `_validate_identifier()` (see 2.2) |

---

## 4. Verified-Strong Posture

- **CORS:** strict allowlist (`https://gula-platform.org` + localhost dev), credentials
  only on the trusted origin; methods/headers/ expose-headers explicitly listed
  (`factory.py:408`).
- **Security headers middleware:** CSP, HSTS `max-age=31536000; includeSubDomains`,
  `nosniff`, `X-Frame-Options: DENY`, Referrer-Policy, Permissions-Policy
  (`middleware.py:162`).
- **Rate limiting:** in-process `RateLimiter` + applied to auth endpoints
  (`rate_limit_auth` on login); nginx `limit_req` zones (`api` 30r/s, `general` 10r/s);
  `ConcurrencyLimitMiddleware`, `MaxBodySizeMiddleware` (50 MB).
- **Password storage:** bcrypt (`shared/auth/passwords.py`).
- **Secrets:** `SECRET_KEY`/`REFRESH_TOKEN_SECRET`/`ENCRYPTION_KEY`/`NID_HMAC_KEY`/
  `AUDIT_ANCHOR_KEY` all from env; production exits (code 1) on missing or weak
  secrets (`config.py:109-116`, `_is_weak_secret`).
- **Sessions:** server-side `sessions` table, logout revokes + blacklists JWT jti,
  `logout_all_sessions`, max concurrent sessions, workspace binding.
- **Audit integrity:** SHA-256 hash-chain with `previous_hash` + `verify_chain_integrity()`
  (`identity/services/audit_service.py`).
- **No dangerous patterns:** zero `pickle.loads`/`yaml.unsafe_load`/`os.system`/`shell=True`
  across `backend/app`, `shared/`, `scripts/`.
- **CI gates:** `security-gate.py` (bandit/semgrep/safety/gitleaks/trivy/checkov),
  `architecture-check` HARD gate.

---

## 5. Residual Risk (tracked, not blocking)

| Risk | Severity | Mitigation |
|---|---|---|
| `react-router` advisory was RSC-only; SPA verified non-RSC | Info | Upgraded to patched 8.3.0 regardless |
| Startup imports 119 route modules eagerly (~20 s once per worker) | Low | Documented; once-per-process, not per-request |
| Operator scripts run with elevated DB access | Low | `_validate_identifier` + least-privilege DB roles recommended in runbook |
| Trivy/container scan not run in this session (tool not installed) | Low | Wired in CI security gate; run on next release build |

---

## 6. Conclusion

The platform is **production-certifiable on security**. All real findings were fixed
with regression tests; every remaining Semgrep/bandit signal was manually reviewed and
either provably safe or guarded. No critical vulnerabilities remain in the verified scope.
