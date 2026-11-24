# Functional NIAM Step-Up Authentication — B4 Prerequisite (Bounded Work Item)

**Document:** `GOVERNANCE/ADVERSARIAL_ASSURANCE/NIAM_STEP_UP_PREREQUISITE.md`
**Origin:** Owner-selected option 4 — establish functional NIAM step-up authentication as a separate bounded work item **before** B4 (`AUD-PRV-002`/`AUD-PRV-005` residual, cross-account administration).
**Date:** 2026-11-19
**Repo:** `gula-integration`, branch `integration/gula-unification-v1`, HEAD pinned `2206654dc713ea2de8c564a3207dfe05fde23549`.
**Status vocabulary:** only `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`.
**`PRODUCTION READY` is NOT awarded anywhere in this document.**

## 1. Status

| Item | Status |
|---|---|
| NIAM step-up prerequisite (this work item) | `INDEPENDENTLY VERIFIED` (engineering scope — awarded by fresh-context Team C) |
| Fresh-context Team C verification of this work item | `INDEPENDENTLY VERIFIED` — `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_STEP_UP.md` (review window 2026-11-19T06:14Z→06:35Z) |
| Owner approval of this work item | `BLOCKED` (pending) |
| B4 cross-account administration implementation | `BLOCKED` (unchanged — no B4 source modified) |
| Production deployment | `BLOCKED` (out of scope) |

This document reports engineering-scope evidence only. The implementing agent does **not** self-award `INDEPENDENTLY VERIFIED`; fresh-context Team C is authoritative for that award and has now issued it at engineering scope. `PRODUCTION READY` remains unawarded.

## 2. Problem established by read-only investigation

Before this work item, no functional NIAM step-up existed:

- `UserSession.mfa_used` is only ever written to `False` (`authentication_service.py:95`); it is never set to `True` by any NIAM login/MFA flow.
- `authorization_decision.py` reads `session.mfa_used` for step-up decisions, but the adaptive-auth routes do not use that service, so the check was unreachable in practice.
- `/login/mfa/verify` is the legacy `LabUser` staged-login MFA flow and never updates a NIAM `UserSession`.

Consequently, a "fresh MFA" signal for a NIAM administrator could not be produced or verified. B4 was therefore `BLOCKED` before any cross-account code could be implemented.

## 3. Design decisions (constrained by the owner's step-up policy)

1. **Reuse the existing MFA primitive — no duplicate engine.** The second factor is verified with `shared.auth.mfa.verify_totp` against the administrator's **own** `Account.mfa_secret`. No new TOTP/verification implementation was introduced. NIAM login, refresh, logout and `mfa_used` were left untouched.
2. **Self-only, structurally enforced.** The verify endpoint accepts only `code` and `method` in its request body. There is no client-supplied account id, session id, timestamp, MFA flag or auth claim. The principal is resolved server-side by `get_current_niam_actor` (Bearer/cookie) and every identifier is **re-read from the database** (`_resolve_principal`). Cross-account MFA completion is structurally impossible on this surface.
3. **No new authority.** No role, permission, or authentication authority was created. Step-up is an *additional* proof-of-possession dependency, separate from the `AUD-SEC-001` control-plane role guard: a privileged role establishes authority; a fresh own-account MFA event establishes recent proof of possession. Both are required for sensitive cross-account operations (enforced when B4 is eventually authorized).
4. **Server-bound evidence.** An `NiamStepUpEvent` binds: `account_id`, `session_id`, `session_jti` (exact access token), `mfa_method`, a SHA-256 `code_fingerprint` (single-use inside the window), a SHA-256 `factor_fingerprint` of the factor secret, and server-recorded `verified_at`/`expires_at`.
5. **Deny by default / fail closed.** Missing, expired, stale, future-dated (clock skew), revoked, replayed, session-substituted, token-substituted, account-substituted, factor-rotated, factor-disabled and ambiguous evidence all deny. Invalid configuration denies (HTTP 503 on verify; `StepUpConfigurationError` on assertion). Verification and assertion outcomes are written to the immutable identity audit log; a successful verification cannot be produced without its audit entry.

## 4. Owner-approved freshness policy

- **Default window: 300 seconds (5 minutes)** — owner-approved and documented as policy.
- Configurable via `NIAM_STEP_UP_FRESHNESS_SECONDS`; **unset → 300**.
- Value is validated lazily at use time (never cached at import). Blank, malformed or out-of-range → `ValueError` → step-up fails closed.
- The `30–3600` bounds are implementation validation limits chosen by the implementing agent; the **only owner-approved duration is 300 seconds**.
- Freshness starts from the **server-recorded** successful MFA event time. The signal is valid while `0 <= elapsed <= 300` (inclusive at exactly 300); beyond 300 it is stale. Future-dated evidence is rejected as clock skew.
- Boundary tests assert 299 / 300 / 301 seconds using a frozen clock, plus clock-skew and session-revocation cases.

## 5. Change inventory (step-up scope only)

| File | Change |
|---|---|
| `backend/app/config.py` | Added `load_niam_step_up_freshness_seconds()` + default/bounds; validated lazy loader. |
| `backend/app/identity/models/step_up.py` | New `NiamStepUpEvent` evidence model (new table only; no existing table/column altered). |
| `backend/app/identity/models/__init__.py` | Export `NiamStepUpEvent`. |
| `backend/app/identity/models/audit.py` | No change by this work item — reuses the pre-existing `mfa_verified`/`mfa_failed`/`policy_enforced` audit actions. |
| `backend/app/identity/services/step_up_service.py` | New `StepUpService.verify/assert_fresh` with fail-closed validation; principal resolution also rejects suspended/locked/disabled/deactivated accounts and `is_locked`; racing inserts are converted to `StepUpDenied("replay_detected")`. |
| `backend/app/identity/api/step_up.py` | New `require_fresh_niam_step_up` FastAPI dependency (available for B4; **not wired into B4**). |
| `backend/app/identity/api/auth.py` | Added `POST /niam/auth/step-up/verify` + request/response schemas (additive only). |
| `backend/migrations/versions/20261119_0001_niam_step_up_events.py` | New `niam_step_up_events` table; `down_revision = 20261118_0001`; single Alembic head; additive/reversible; DB-level unique constraint `uq_niam_step_up_account_code(account_id, code_fingerprint)` as a cross-process replay guard. |
| `backend/tests/unit/test_niam_step_up.py` | 37 adversarial tests (synthetic SQLite, no operational DB/Redis/HTTP/patient data). |

`backend/app/identity/adaptive_auth/routes.py` (the B4 surface) was **not** modified by this work item. Its pre-existing modifications belong to earlier phases.

## 6. AUD-SEC-001 / AUD-SEC-003 impact

- **AUD-SEC-001 (single authorization authority):** unaffected. Step-up does not create a second authorization authority; the `require_fresh_niam_step_up` dependency is an independent proof-of-possession check layered alongside the existing control-plane role guard. No role/permission source was changed.
- **AUD-SEC-003 (session/security controls):** additive only. The new endpoint is rate-limited per account and writes to the immutable audit log. No existing session lifecycle, token, logout or refresh behavior was changed. `mfa_used` and the legacy LabUser MFA route were not modified.

## 7. Test evidence (engineering scope)

All commands used `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:..` and the pinned `gula-platform/backend/.venv/bin/python`; synthetic/disposable data only.

| Check | Result |
|---|---|
| `pytest tests/unit/test_niam_step_up.py -q` | **37 passed**, 1 warning (Starlette/httpx deprecation), `EXIT=0` |
| Ruff on all 9 step-up scope files | **All checks passed**, `EXIT=0` |
| App boot + OpenAPI | BOOT OK (`app.main.app`); **1815 paths / 132 route objects** (Team C probe `/tmp/opencode/team_c_openapi_probe.py`, reconfirmed directly); `/niam/auth/step-up/verify` present, body properties exactly `code`, `method` (`required=[code]`, `HTTPBearer`) |
| Migration graph | single head `20261119_0001`; down `20261118_0001` exists; 98-revision chain |
| Targeted regressions (identity, NIAM, session/risk-based auth, migrations, AUD-SEC-001…007, step-up — 12 files) | **retained-log re-run: `170 passed, 0 skipped, EXIT=0 (3m26s)`** — `/tmp/opencode/step_up_targeted_final.log`; an earlier broader selection reported `374 passed / 4 skipped` (exact file list not retained) |
| `scripts/phase_b_gate.py` | **PASS (6/6 gates)**, `EXIT=0` |
| `scripts/national_integration_verify.py` | **VERDICT PASS**, `EXIT=0` (expected advisory HEAD-drift WARN: recorded `0cb067ae`, current `2206654d`) |

The 37 step-up tests cover: legitimate self MFA; immutable audit write; 299/300/301 freshness boundary; clock skew; TOTP replay; session/token/account substitution; revoked/expired session; suspended/locked/disabled/deactivated accounts and `is_locked` (both evidence assertion and new staging); concurrent same-code verification; DB-level duplicate-fingerprint rejection; migration upgrade/downgrade on a disposable SQLite database; factor disabled/rotated/method-removed; missing evidence; cross-account factor rejection; invalid code/method; ambiguous evidence; invalid config fail-closed; config default/valid override; and an OpenAPI structural assertion that the endpoint accepts no client identity claims.

**Full-suite evidence (honest record):** the first full run after the initial step-up changes produced `4973 passed, 27 skipped, 203 warnings, 1 failed, EXIT=1`; the single failure was the CPU-timing benchmark `test_ai_benchmark.py::TestEmbeddingBenchmarks::test_cosine_similarity_throughput` (`1680/s < 2000/s`), which has no connection to step-up. It passed three consecutive isolation runs at `7796/s`, `3885/s`, `5992/s` (`EXIT=0`). The count arithmetic is consistent with no regression: pre-step-up `4947 passed` + `27 new step-up tests` = `4974` executed, matching `4973 passed + 1 failed`. A clean **full-suite re-run** then completed with `4974 passed, 27 skipped, 203 warnings, EXIT=0 (17m09s)` — confirming the benchmark failure was environmental and no regression. That re-run still contained the earlier 27-test version of the step-up file; the 10 newly added adversarial tests and the account-state/concurrency/DB-constraint hardening landed afterwards. The authoritative **final-tree** full suite covering all current changes (account-state guard, concurrency/replay guard, DB unique constraint, 37 step-up tests) then completed with **`4984 passed, 27 skipped, 203 warnings, EXIT=0 (15m04s)`** — exactly `4974 + 10` newly added cases, zero failures. No test threshold was weakened or test skipped to obtain any of these results.

## 8. Invariants reconfirmed

- Integration HEAD unchanged: `2206654dc713ea2de8c564a3207dfe05fde23549`.
- Sibling `gula-platform` HEAD unchanged: `f478676b6fc375338648dde46fbf076c015a3f91`.
- The 20 staged `R100` renames under `archive/legacy/workflow_runtime/` were not touched.
- No commit, push, PR, merge, deploy, external government integration, or operational DB/Redis access was performed.
- No `PRODUCTION READY` awarded. `status_registry.json` not edited for this work item.

## 9. B4 readiness decision

B4 remains **`BLOCKED`**. This work item establishes the prerequisite mechanism only. Before B4 may proceed:

1. **Satisfied:** the final-tree full suite passed (`4984 passed, 27 skipped, 203 warnings, EXIT=0`).
2. **Satisfied:** fresh-context Team C awarded `INDEPENDENTLY VERIFIED` at engineering scope
   (`INDEPENDENT_VERIFICATION_TEAM_C_STEP_UP.md`), with zero real bypasses across 57+ probes.
3. **Still blocking:** the owner must explicitly approve the step-up prerequisite and authorize B4
   implementation under the previously selected Self + Security Administration model. The
   assistant-chosen `30–3600` validation bounds also await owner ratification (only `300s` is
   owner-approved).

No B4 implementation, role/permission change, or cross-account endpoint wiring was performed here.
