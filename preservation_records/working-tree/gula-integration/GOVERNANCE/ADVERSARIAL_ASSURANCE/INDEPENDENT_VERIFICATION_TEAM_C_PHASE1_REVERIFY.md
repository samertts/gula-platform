# Independent Verification — Team C (Fresh Context), Phase 1 RE-VERIFICATION

**Date:** 2026-11-19
**Verifier:** Team C — fresh-context, independent adversarial verifier (no reliance on implementer claims)
**Repository under test:** `/home/samertts/workspace/projects/gula-integration`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549`
**READ-ONLY sibling:** `/home/samertts/workspace/projects/gula-platform` (HEAD `f478676b6fc375338648dde46fbf076c015a3f91`) — not modified.
**Interpreter:** `gula-platform/backend/.venv/bin/python` (Python 3.12, pinned by the mandate).
**Predecessor report:** `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_PHASE1.md` (same date), which FALSIFIED AUD-SEC-003 and recorded a residual against AUD-API-002 / AUD-SEC-002.

## 1. Scope, mandate, and explicit statement

- This is a **follow-up re-verification of two previously FALSIFIED defects only**: (a) AUD-SEC-003 staged-privileged-login `datetime.UTC` crash; (b) the AUD-API-002 / AUD-SEC-002 legacy domain-less OAuth2 token collision residual recorded in predecessor §4 item 2.
- **AUD-SEC-001, AUD-SEC-002 (original forgery probe), and AUD-ARCH-003 are explicitly OUT OF SCOPE** — unchanged and already `INDEPENDENTLY VERIFIED`; they were not re-tested.
- **ENGINEERING SCOPE ONLY**, falsification-first: static inspection of the real diff, ≥1 independent concrete adversarial probe per finding, the exact targeted test command, and Ruff. **No operational DB, no network, no external/government/clinical/regulatory validation, no deploy.**
- Probes were written ONLY to `/tmp/opencode/probe_sec003_reverify.py` and `/tmp/opencode/probe_sec002_reverify.py`. **No source file, staging area, git metadata, config, sibling repo, or owner-gated artifact was modified.** The only file written in this repo is this report.
- **No status of `PRODUCTION READY` was awarded to any finding.** Owner-gated items remain owner-gated; no owner decision was altered.

## 2. Per-finding results

Mandated control-state vocabulary used for final verdicts: `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`.

| Finding | Original falsification (Phase 1) | Fix inspected in current tree | New falsification attempt + observed outcome | Targeted test (exact command) | Ruff | Final verdict |
|---|---|---|---|---|---|---|
| **AUD-SEC-003** (CRITICAL) staged privileged login | `login.py:77` called `datetime.now(datetime.UTC)` while line 4 imported only `from datetime import datetime`; the `datetime` **class** has no `UTC` attribute. A correct TOTP factor raised `AttributeError: type object 'datetime.datetime' has no attribute 'UTC'` before tokens/JTI-blacklist → happy path 500, no tokens. Implementer's "13 passed" was contradicted (11 passed / 2 FAILED). | `login.py:4` now `from datetime import UTC, datetime`; `login.py:77` now `datetime.now(UTC).timestamp()` — the imported module-level `UTC` constant, never the class attribute. No other logic changed. Test file inspected: `test_password_only_returns_pending_not_full_tokens`, `test_correct_code_issues_full_tokens`, `test_pending_token_is_single_use` still assert (i) password-only yields no access/refresh, (ii) correct TOTP yields both full tokens, (iii) pending JTI is single-use / replay rejected — assertions NOT weakened. | Independent probe `/tmp/opencode/probe_sec003_reverify.py`: module imports OK; confirmed `hasattr(datetime,'UTC') is False` yet the imported `UTC` constant works; `_pending_ttl_seconds({"exp": now+300}) -> 299` (int, no `AttributeError`); missing-exp fallback `{} -> 300`; adversarial expired/`0`/`-1`/`1` exp clamp to `1` without crash. The exact prior crash input no longer raises. `mfa_pending` path, real factor verification, and single-use blacklist still present in source. **Falsification attempt FAILED (fix holds).** | `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned-python> -m pytest tests/unit/test_aud_sec_003_staged_privileged_login.py -q --tb=short` → **13 passed, 1 warning in 132.89 s** (first 120 s attempt timed out; rerun with 300 s timeout). | `ruff check app/routes/login.py` → **All checks passed!** | **INDEPENDENTLY VERIFIED** (narrow engineering scope) |
| **AUD-API-002 / AUD-SEC-002 residual** (HIGH, `owner_gated`) legacy domain-less OAuth2 collision | `_resolve_oauth2_user_claims()` correctly returned `{}` for NULL/unknown `account_kind`, but grant/refresh handlers passed the bare `user_id` straight into the mint. With neither `account_kind` nor `lab_id`, `resolve_token_account_kind()` defaults to the **USER** family (`auth.py:85`), so a legacy LabUser subject on an ID collision could bind to the colliding User account. Migration docstring inaccurately claimed such records "cannot mint a canonical user token." | New helper `_has_resolvable_account_domain(payload)` at `oauth2_provider.py:25-38` requires a signed `account_kind in {lab,user}` OR `lab_id is not None`. Both `create_access_token_oauth2` (line 161) and `create_refresh_token_oauth2` (line 187) now embed `user_id` **only** when that helper passes; claims are merged before the check, so a userless domain-less token is minted and `get_current_user()` rejects it (fail closed). Migration `20261118_0001` docstring (lines 10-20) now accurately describes NULL-domain records as introspection/revocation-only until re-authorized. Four new tests inspected: bare-user_id refusal, signed-domain retention, refresh subject refusal, and end-to-end NULL-`account_kind` authorization-code grant with LabUser/User ID collision asserting **no `user_id`** and **protected route 401** — assertions NOT weakened. | Independent probe `/tmp/opencode/probe_sec002_reverify.py` (synthetic id `95002`, no DB): helper truth table **9/9** correct (`{}`, `account_kind=None`, unknown kind, `lab_id=None`, both-null → `False`; `lab`/`user`, `lab_id=42`, `lab_id`+unknown kind → `True`). **Forced domain-less mint** with `user_id=95002, claims={}` → decoded token has `user_id=None` (absent); `resolve_token_account_kind()` still returns `user` for that payload, confirming the residual was real but is now unreachable through the mint (no subject to bind). Unknown `account_kind="bogus"` also fails closed. Backward compat: signed `account_kind=user` retains `user_id`; grounded legacy `lab_id=77` retains `user_id` and resolves LAB; refresh with `account_kind=None` has no `user_id`, with `account_kind=lab` retains it. **Falsification attempt FAILED (fix holds).** | `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned-python> -m pytest tests/unit/test_aud_api_002_oauth2_token_usable.py -q --tb=short` → **10 passed, 1 warning in 81.52 s** (includes the four new adversarial tests and `test_claims_without_account_kind_do_not_invent_a_domain` happy-path). | `ruff check app/security/oauth2_provider.py tests/unit/test_aud_api_002_oauth2_token_usable.py migrations/versions/20261118_0001_oauth2_account_kind.py` → **All checks passed!** | **INDEPENDENTLY VERIFIED** (narrow engineering scope; **owner ratification still required — no production claim**) |

## 3. Invariant re-confirmation

All invariants re-checked at baseline and again after all probes (only this report file was added).

| Invariant | Expected | Observed | Status |
|---|---|---|---|
| Repo HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` | `2206654dc713ea2de8c564a3207dfe05fde23549` | **PASS** |
| Staged change count | 20 | 20 | **PASS** |
| Staged status | all `R100` | unique status set = `R100` | **PASS** |
| Protected MD5 — `GOVERNANCE/FINAL_DECISION.md` | `effdfeaf10234678d83b2668c4489552` | identical | **PASS** |
| Protected MD5 — `MPI_FINAL_INDEPENDENT_AUDIT.md` | `1a02c01563c93b07a7cdb92c0462bf36` | identical | **PASS** |
| Protected MD5 — `MPI_INDEPENDENT_AUDIT_FINDINGS.md` | `ea3969d09aaf7b0b28a065838b44a594` | identical | **PASS** |
| Sibling repo HEAD (read-only) | `f478676b6fc375338648dde46fbf076c015a3f91` | identical | **PASS** |
| `production_ready_items` counters | `0` (2 occurrences: nested + top-level) | 2 matches of `"production_ready_items": 0` | **PASS** |
| `production_ready_count` counter | `0` (1 occurrence) | 1 match of `"production_ready_count": 0` | **PASS** |
| Owner-gated decisions | unchanged | no existing governance artifact modified; HOLD / MPI REJECT / MP-001 / ODR-001..004 / D-020/D-021 / ADR-A..J / AUD-02/07/16 untouched | **PASS** |
| Git writes | none | no commit / stage / git mutation performed | **PASS** |
| Data / connectivity | synthetic only | no operational DB, no network, no sibling modification | **PASS** |

## 4. Overall verdict

Both corrected defects **survived renewed falsification** at narrow engineering scope:

- **AUD-SEC-003 → `INDEPENDENTLY VERIFIED`** (engineering scope). The prior `BLOCKED` availability regression is resolved: the exact `datetime.UTC` crash input no longer raises, the three security-critical assertions (no password-only tokens, full tokens on correct TOTP, single-use pending JTI) remain intact, and the targeted test is green at 13/13.
- **AUD-API-002 / AUD-SEC-002 residual → `INDEPENDENTLY VERIFIED`** (engineering scope; **owner-gated**). The fail-closed minting invariant holds across access and refresh tokens; a forced NULL-domain grant with a LabUser/User ID collision mints **no subject**, backward-compatible signed-domain and grounded `lab_id` paths still work, and the migration docstring is now accurate.

**No `PRODUCTION READY` status was awarded to any finding.** AUD-API-002 remains `owner_gated`; this engineering-scope re-verification does not ratify it for production. Owner-gated decisions remain unchanged and `production_ready` counters remain `0`. All invariants PASS.

## 5. Honest gaps / residual limitations

1. **Scope was deliberately narrow.** Only the two corrected findings were re-run; SEC-001/002/ARCH-003 were not re-tested (per mandate). No full backend suite was run (it requires an operational DB and exceeds engineering scope).
2. **Route-level proof for the OAuth2 residual** comes from the inspected adversarial test `test_legacy_null_account_kind_grant_cannot_bind_to_colliding_user` (asserts 401), not a separately written independent TestClient probe; my independent probe verified the mint/decode invariant and the subject-guess behavior at the pure-function level. This is complementary, not contradictory.
3. **Deliberate availability trade-off:** legacy OAuth2 records with NULL/unknown `account_kind` are now unusable against the API (fail closed) until re-authorized. This is the intended security fix, but it is a behavior change for such records and should be noted by the owner.
4. **Redis cross-worker single-use** of the MFA pending JTI was not re-verified — the blacklist uses an in-memory fallback when Redis is absent, so cross-worker single-use remains infrastructure-dependent (carried forward from predecessor report; unchanged by this fix).
5. **`resolve_token_account_kind()` still defaults to USER** when neither signed `account_kind` nor `lab_id` is present (`auth.py:85`). Safety now depends on the provider never emitting a `user_id` in that state (verified here). Any future code path that mints a bare `user_id` outside `oauth2_provider.py` would reintroduce the collision; this invariant is enforced at the single minting point inspected.
6. **Timing:** SEC-003 targeted test needed ~133 s; a default 120 s harness timeout would report a false timeout. Use an extended timeout.
7. This verdict reflects exactly the working tree observed at verification time; no fix was re-run after any further correction (none was permitted).
