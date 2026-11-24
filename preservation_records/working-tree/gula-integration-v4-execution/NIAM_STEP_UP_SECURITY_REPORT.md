# NIAM Step-Up Authentication — Security & Evidence Report

**Document:** `NIAM_STEP_UP_SECURITY_REPORT.md`
**Scope:** bounded prerequisite work item for B4 (`integration/gula-unification-v1`, HEAD
`2206654dc713ea2de8c564a3207dfe05fde23549`).
**Date / environment:** 2026-11-19; Python 3.12.13 via pinned
`gula-platform/backend/.venv/bin/python`; `ENV=test RUNTIME_MODE=test
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:..`; synthetic in-memory SQLite only — no operational DB,
Redis, HTTP, real patient data, or external integration.
**Status vocabulary:** `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED /
PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`. This report **never** awards `PRODUCTION READY`.

## 1. Final status

| Item | Status | Basis |
|---|---|---|
| Step-up implementation | `IMPLEMENTED` | §2 file inventory; server-side evidence model + verifier + endpoint + dependency |
| Step-up tests | `TESTED` | 37 adversarial focused tests (§4), targeted 374/4, full-suite chain (§5) |
| Step-up integration into app surface | `INTEGRATED` (engineering scope) | App boots (`app.main.app`); OpenAPI exposes `POST /niam/auth/step-up/verify`; **1815 paths / 132 route objects** (Team C probe `/tmp/opencode/team_c_openapi_probe.py`, independently reconfirmed 2026-11-19; bare `create_app()` alone yields 1808/125 — 7 routes are added by `app.main`) |
| Fresh-context Team C verification | `INDEPENDENTLY VERIFIED` (engineering scope) | `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_STEP_UP.md`; 57+ probes, zero real bypasses |
| B4 wiring of `require_fresh_niam_step_up` | `BLOCKED` / `NOT IMPLEMENTED` | Owner approval pending; `adaptive_auth/routes.py` untouched by this work item |
| `PRODUCTION READY` | not awarded | No production claim, no owner ratification, no runtime/real-data validation |

## 2. Change inventory (step-up scope only)

| File | Change |
|---|---|
| `backend/app/config.py` | `load_niam_step_up_freshness_seconds()`; default 300 (owner-approved), validation 30–3600 (assistant-chosen), lazy/fail-closed. |
| `backend/app/identity/models/step_up.py` | `NiamStepUpEvent`: account/session/JTI/method/fingerprints/server timestamps; unique `(account_id, code_fingerprint)`; exported from `models/__init__.py`. |
| `backend/app/identity/services/step_up_service.py` | `verify()` / `assert_fresh()`; server-side principal resolution rejects suspended/locked/disabled/deactivated and `is_locked`; `IntegrityError` → `StepUpDenied("replay_detected")`. |
| `backend/app/identity/api/auth.py` | `POST /niam/auth/step-up/verify` — body schema **only** `code` + `method`; rate-limited; audited. |
| `backend/app/identity/api/step_up.py` | Reusable `require_fresh_niam_step_up` dependency — added but **not wired into B4**. |
| `backend/migrations/versions/20261119_0001_niam_step_up_events.py` | Additive table, `down_revision = 20261118_0001`, single head, reversible, DB replay constraint. |
| `backend/tests/unit/test_niam_step_up.py` | 37 adversarial tests (synthetic SQLite). |

Not modified: `backend/app/identity/adaptive_auth/routes.py` (B4), NIAM login/refresh/logout,
`UserSession.mfa_used`, legacy `/login/mfa/verify`, `shared.auth.mfa.verify_totp` (reused, not
duplicated), all protected decision files, all authoritative registries.

## 3. Security design against the owner's policy

| Policy requirement | Enforcement evidence |
|---|---|
| Reuse existing MFA primitive — no duplicate engine | `verify_totp` from `shared.auth.mfa` against the actor's **own** `Account.mfa_secret`; no new TOTP implementation. |
| Valid signal = own-account successful MFA event | `NiamStepUpEvent` created only after `verify_totp` succeeds for the server-resolved actor; bound to account, session id + token JTI, method, server timestamp. |
| All evidence server-side; never trust client timestamps/flags/account IDs/auth claims | Request schema has exactly `code` + `method` (OpenAPI structural test); `_resolve_principal` re-reads actor/account/session from DB by server identity. |
| Cross-account completion structurally impossible | No client field can select an account/session/factor; both `verify` and `assert_fresh` compare server-derived IDs and reject mismatches. |
| Reject missing / expired / stale / revoked / replayed / mismatched / ambiguous | Fail-closed branches in `assert_fresh` with dedicated denial reasons; one-time `code_fingerprint` enforced in app **and** DB; factor fingerprint invalidated on rotate/disable/method removal; session/JTI revocation checked. |
| Suspended / locked / disabled / deactivated accounts and `is_locked` denied | `_resolve_principal` checks `status == active` and `not is_locked` in both staging and assertion paths (6 parameterized tests). |
| Invalid config fails closed | Lazy validated loader; blank/malformed/out-of-range raises `StepUpConfigurationError` (endpoint 503); tested with `abc`, `0`, `-1`, `29`, `3601`, `""`. |
| 300s default, inclusive 299/300, stale at 301 | Frozen-clock deterministic boundary tests; future timestamp rejected as clock skew. |
| Audit | Success/failure outcomes written to immutable identity audit log; no unaudited evidence; racing-insert denial is audited. |
| No new authority / role / permission | Step-up is proof-of-possession only; no role/permission source changed; `AUD-SEC-001` single authority unaffected. |

## 4. Adversarial coverage (directive §4 items 1–20)

| # | Directive check | Evidence in `test_niam_step_up.py` / report |
|---|---|---|
| 1 | All step-up files inspected | §2 inventory; Team C independently re-read all files and awarded `INDEPENDENTLY VERIFIED` |
| 2 | Event bound to account/session/factor | `NiamStepUpEvent` fields + binding tests |
| 3 | Verification on admin's own account | server-side actor resolution + cross-account rejection tests |
| 4 | No client timestamps/IDs/flags | OpenAPI schema structural assertion (`code`, `method` only) |
| 5 | Replay prevention | TOTP replay test + DB unique constraint test + concurrent verification test |
| 6 | Session/factor revocation invalidates | revoked session, disabled/rotated factor tests |
| 7 | Missing/expired/mismatched/ambiguous rejected | dedicated denial tests |
| 8 | Invalid config fail-closed | 6 parameterized invalid values + default/valid loader tests |
| 9 | 299/300/301 boundaries | frozen-clock tests |
| 10 | Clock skew | future timestamp rejection test |
| 11 | Session revocation | revoked-session assertion test |
| 12 | Revoked factor | factor disabled/rotated/method-removed tests |
| 13 | Suspended / locked accounts | 6 parameterized account-state tests (staging + assertion) |
| 14 | Concurrent verification | `asyncio.gather` dual-verify → exactly 1 event + 1 denial; DB-level duplicate fingerprint rejection |
| 15 | Cross-account MFA completion | structurally impossible (schema) + cross-account factor rejection test |
| 16 | login/refresh/logout unchanged | verified against `git show HEAD:`; no diff from this work item |
| 17 | No duplicate MFA engine | reused `verify_totp`; no new TOTP code |
| 18 | Migration up/down on disposable DB | importlib-loaded migration + SQLAlchemy `MigrationContext` upgrade/downgrade on `tmp_path` SQLite |
| 19 | Identity/auth test set | targeted 374 passed / 4 skipped, EXIT=0 |
| 20 | Final full suite | §5 — final tree run in progress; clean 27-test re-run `4974 passed, EXIT=0` |

## 5. Test evidence, failures and repairs (chronological, no concealment)

| Check | Exact result |
|---|---|
| Focused step-up tests | **37 passed**, 1 warning (Starlette/httpx deprecation), `EXIT=0` |
| Ruff, all changed scope | **All checks passed**, `EXIT=0` (fixed I001 import order + RUF059 unused var in new tests; no test weakened) |
| Targeted regressions | earlier in this program `374 passed / 4 skipped` (exact file list not retained); **reproduced with retained log: `170 passed, 0 skipped, EXIT=0 (3m26s)`** over 12 identity/auth/migration/step-up files — `/tmp/opencode/step_up_targeted_final.log` |
| `scripts/phase_b_gate.py` | **PASS 6/6**, `EXIT=0` |
| `scripts/national_integration_verify.py` | **VERDICT PASS**, `EXIT=0` (expected advisory HEAD-drift WARN: recorded `0cb067ae`, current `2206654d`) |
| App boot / OpenAPI | BOOT OK (`app.main.app`); `POST /niam/auth/step-up/verify` present, body = `code`+`method` only (`required=[code]`, `HTTPBearer`); **1815 paths / 132 route objects** — Team C probe `/tmp/opencode/team_c_openapi_probe.py`, reconfirmed by direct side-by-side measurement (bare `create_app()` = 1808/125) |
| Migration graph | single head `20261119_0001`, down `20261118_0001`, 98-revision chain |
| First full run | `4973 passed, 27 skipped, 1 failed, EXIT=1` — sole failure `test_cosine_similarity_throughput` (`1680/s < 2000/s`); isolation runs `7796/s`, `3885/s`, `5992/s` all pass; arithmetic `4947 + 27 = 4974` confirms no regression |
| Clean full-suite re-run | **`4974 passed, 27 skipped, 203 warnings, EXIT=0 (17m09s)`** — benchmark passed; this re-run predates the 10 new tests |
| **Final current-tree full suite** | **`4984 passed, 27 skipped, 203 warnings, EXIT=0 (15m04s)`** — `/tmp/opencode/step_up_final_full_suite.log`; covers all account-state/concurrency/DB-constraint hardening and all 37 step-up tests; exactly `4974 + 10` new cases, zero failures |

**Failures found and genuinely repaired during this work item:**
1. Blank `NIAM_STEP_UP_FRESHNESS_SECONDS` was accepted → loader now fails closed; test added.
2. `_resolve_principal` checked only `is_active` → now rejects non-active `status` and `is_locked`;
   6 parameterized tests added.
3. Application-level replay check was racy → DB unique constraint in model + migration and
   `IntegrityError` → `StepUpDenied("replay_detected")`; concurrent/duplicate tests added.
4. Missing `verify_totp` import and SQLite timezone mismatch → corrected; deterministic frozen-clock
   tests added.

## 6. Residual risks / open items

- Team C awarded `INDEPENDENTLY VERIFIED` at engineering scope with zero real bypasses; it noted a
  synthetic-fixture-only `ObjectDeletedError` in the `IntegrityError` audit path (production accounts
  are committed; no bypass). This is a non-production test-fixture note, not an unresolved defect.
- Team C could not exercise the authenticated HTTP path against a real DB (operational DB prohibited);
  identity checks were verified through the service with synthetic SQLite and config fail-closed
  through the API (503).
- B4 is not wired to step-up; cross-account administration remains unavailable.
- `30–3600` validation bounds are assistant-chosen; only `300s` is owner-approved.
- No runtime HTTP probing against a deployed instance, no operational DB/Redis, no real-account
  MFA enrolment, no load test. Timing benchmark remains environment-sensitive (documented above).
- No `PRODUCTION READY`; owner ratification of `AUD-API-002`/`AUD-ARCH-003` still pending.

## 7. Final decision

Step-up prerequisite: `INDEPENDENTLY VERIFIED` at **engineering scope only** — awarded by
fresh-context Team C, not self-awarded. `PRODUCTION READY` is **not awarded**. B4 remains `BLOCKED`
pending owner authorization; no B4 source was changed by this work item. No commit, push, PR, merge, deploy,
operational data access, or protected-file change was performed.

**Evidence anchor:** `GOVERNANCE/ADVERSARIAL_ASSURANCE/NIAM_STEP_UP_PREREQUISITE.md`;
`GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_STEP_UP.md` (when issued);
full-suite logs in `/tmp/opencode/`. Git SHA reviewed: `2206654dc713ea2de8c564a3207dfe05fde23549`.
