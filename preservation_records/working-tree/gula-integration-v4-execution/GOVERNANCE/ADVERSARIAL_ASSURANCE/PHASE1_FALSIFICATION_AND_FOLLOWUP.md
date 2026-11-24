# Phase 1 — Falsification Result and Integrator Follow-up

**Artifact class:** Assurance record — honest disclosure of a successful falsification and its correction
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Date:** 2026-11-19
**Independent report:** `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1.md` (fresh-context, falsification-first)
**Re-verification:** `INDEPENDENT_VERIFICATION_TEAM_C_PHASE1_REVERIFY.md` — COMPLETE; both defects survived renewed falsification, no new defect found

## 1. Why this document exists

The adversarial assurance model worked as designed. Fresh-context Team C **successfully falsified**
one Phase 1 remediation (AUD-SEC-003) and exposed a narrower residual defect in a second
(AUD-API-002 / AUD-SEC-002 interaction). This document records exactly what was found, what the
integrator changed, and what evidence exists so far. **No status is upgraded here** — the correction
must itself survive fresh-context falsification before any `INDEPENDENTLY VERIFIED` award.

Team C's original report is a historical snapshot of the tree it observed and is left **byte-identical**.

## 2. Falsification 1 — AUD-SEC-003 (CRITICAL): staged login completion crashed

### What Team C found
`backend/app/routes/login.py:77` called `datetime.now(datetime.UTC)`, but line 4 imported only
`from datetime import datetime`. The `datetime` **class** has no `UTC` attribute (the *module* does):
`hasattr(datetime, "UTC") == False`. After a correct MFA factor was verified, `_pending_ttl_seconds()`
raised `AttributeError` → HTTP 500, no full tokens issued, pending JTI not consumed. Targeted suite
observed **11 passed / 2 FAILED**:
`test_correct_code_issues_full_tokens`, `test_pending_token_is_single_use`. Team C verdict: **BLOCKED**.

### Root cause (integrator's own error)
The full regression (`4909 passed`) had been executed while the line read
`datetime.now(timezone.utc)` with `from datetime import datetime, timezone`. A **subsequent cosmetic
Ruff fix** (UP017) replaced it with `datetime.now(datetime.UTC)` but removed the `timezone` import
without adding a `UTC` import. Ruff accepted the result (it is a valid module-level idiom), but at
runtime the class attribute does not exist. The defect was therefore introduced **after** the
recorded full-suite pass, by the integrator's own post-regression cleanup — not present in the
originally verified implementation.

### Correction applied
- `backend/app/routes/login.py`: `from datetime import UTC, datetime` and `datetime.now(UTC)` —
  the same idiom already used correctly in `app/health_core/authorization/engine.py`.
- Verified locally: Ruff clean; targeted suite **13 passed**, including both previously failing tests.

### Residual (unchanged, honestly recorded by Team C)
- Pending token is not blacklisted on a *failed* factor verification (allows retry — acceptable).
- Blacklist uses a per-process in-memory store when Redis is absent, so cross-worker single-use is
  infrastructure-dependent and was not verified (no operational Redis in scope).

## 3. Falsification 2 — AUD-API-002 / AUD-SEC-002: legacy NULL-domain token guessed a family

### What Team C found
`_resolve_oauth2_user_claims()` correctly returns `{}` when `account_kind` is NULL/unknown (fail
closed for *claims*). However, the authorization-code and refresh handlers passed the bare
`token_record.user_id` / `payload["user_id"]` **directly** into `create_access_token_oauth2()`, which
unconditionally injected it. With neither `account_kind` nor `lab_id` on the token,
`resolve_token_account_kind()` falls back to `ACCOUNT_KIND_USER` — a **guess**. A legacy LabUser
subject on an ID collision could therefore bind to the wrong User account, reintroducing the
AUD-SEC-002 cross-family collision through the OAuth2 path. Team C also noted the migration
docstring inaccurately claimed legacy records "cannot mint a canonical user token".

### Correction applied (at the single minting point)
`backend/app/security/oauth2_provider.py`:
- added `_has_resolvable_account_domain(payload)` — true only when a signed `account_kind` in
  `{lab, user}` or a signed `lab_id` is present;
- `create_access_token_oauth2()` and `create_refresh_token_oauth2()` now embed `user_id` **only**
  when that predicate passes. A domain-less token is minted **userless**, and `get_current_user()`
  rejects it — fail closed, never guess.
- Migration `20261118_0001` docstring rewritten to state this behavior and the collision rationale
  accurately.

Four new adversarial tests added to `tests/unit/test_aud_api_002_oauth2_token_usable.py` (6 → 10):
1. provider refuses a bare `user_id` with no signed domain;
2. provider retains `user_id` when a signed domain is present (backward compatibility);
3. refresh token carries no subject without `account_kind`;
4. end-to-end legacy NULL-`account_kind` authorization-code grant with a LabUser/User ID collision:
   token has no `user_id` and the protected route returns 401.

Verified locally: Ruff clean; targeted suite **10 passed**. The existing grounded legacy `lab_id`
derivation test still passes — that path is *derived* from a signed claim, not guessed.

## 4. Assurance status (deliberately not upgraded yet)

| Finding | Team C original verdict | Integrator action | Status now |
|---|---|---|---|
| AUD-SEC-001 | INDEPENDENTLY VERIFIED | unchanged | INDEPENDENTLY VERIFIED (engineering scope) |
| AUD-SEC-002 | INDEPENDENTLY VERIFIED | unchanged | INDEPENDENTLY VERIFIED (engineering scope) |
| AUD-SEC-003 | **BLOCKED** (falsified) | defect corrected; 13/13 local | **`INDEPENDENTLY VERIFIED`** (13 passed; survived renewed falsification) |
| AUD-API-002 | INDEPENDENTLY VERIFIED (eng. scope, owner-gated) | residual corrected; 10/10 local | **`INDEPENDENTLY VERIFIED`** for corrected residual (10 passed; owner-gated) |
| AUD-ARCH-003 | INDEPENDENTLY VERIFIED (eng. scope, owner-gated) | unchanged | INDEPENDENTLY VERIFIED (engineering scope) |

No `PRODUCTION READY` awarded. Owner-gated items remain owner-gated. `production_ready_items == 0`.

## 5. Process lesson

A cosmetic static-analysis cleanup changed runtime semantics after the regression run and defeated
a passing test suite. Going forward, any post-regression edit — however small — requires the full
regression to be re-executed against the final tree, and the result recorded against that exact tree.
The final-tree full-suite re-run is therefore mandatory before Phase 1 closeout.
