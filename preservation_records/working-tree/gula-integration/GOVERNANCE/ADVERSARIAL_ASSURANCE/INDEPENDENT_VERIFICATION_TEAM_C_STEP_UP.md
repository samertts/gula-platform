# Independent Verification — Team C — Functional NIAM Step-Up Authentication (B4 prerequisite)

**Reviewer:** Team C — fresh-context, independent adversarial verifier (no prior conversation, no file ownership).
**Subject:** the "Functional NIAM Step-Up Authentication" prerequisite work item on `integration/gula-unification-v1`.
**Reviewed tree:** `gula-integration` HEAD `2206654dc713ea2de8c564a3207dfe05fde23549` (unchanged).
**Sibling tree:** `gula-platform` HEAD `f478676b6fc375338648dde46fbf076c015a3f91` (unchanged).
**Review window (UTC):** 2026-11-19T06:14Z → 2026-11-19T06:35Z.
**Authority:** all existing reports were treated as unverified assertions; every finding below was re-derived from the tree and re-executed by this reviewer.
**Status vocabulary:** only `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED` is used for assurance awards. `PRODUCTION READY` is **NOT** awarded.

---

## 1. Verdict table

| # | Requirement | Verdict | Concrete evidence (re-derived, not quoted from reports) |
|---|---|---|---|
| 1 | Reuse existing MFA primitive; no duplicate MFA engine | VERIFIED | `step_up_service.py:37` imports `verify_totp` from `shared.auth.mfa`; `:195` calls `verify_totp(account.mfa_secret, code)`. `shared/auth/mfa.py:20-22` is the sole primitive (pyotp + `valid_window=1`). Repo-wide grep found no new TOTP implementation in the eight step-up files; the only other `verify_totp` definitions are pre-existing legacy LabUser flows (`backend/app/routes/mfa.py:67`, `backend/app/security/mfa_service.py:62`), untouched by this work item. |
| 2 | Actor resolved server-side and re-read from DB; evidence bound to principal/account/session(id+JTI)/method/server timestamp | VERIFIED | `step_up_service.py:100-123` `_resolve_principal()` re-selects `Account` and `UserSession` by the authenticated actor's IDs, checks `session.account_id == account.id` and `session.token_jti == actor.session.token_jti`. `:205-217` binds `account_id`, `session_id`, `session_jti = session.token_jti`, `mfa_method`, `code_fingerprint`, `factor_fingerprint`, `verified_at = now` (server clock), `expires_at`. |
| 3 | Request schema only `code`+`method`; no client identity fields; cross-account structurally impossible | VERIFIED | `api/auth.py:79-83` `StepUpVerifyRequest{code: str, method: str = "totp"}` only. Live OpenAPI probe: `BODY_PROPERTIES ["code","method"]`, `BODY_REQUIRED ["code"]`. No account/session/timestamp/flag/claim field exists on the endpoint. Falsification probe "cross-account MFA code" → `StepUpDenied:factor_verification_failed`. |
| 4 | Reject missing / expired / revoked / replayed / mismatched / ambiguous; session & factor revocation; suspended/locked/disabled/deactivated/`is_locked` | VERIFIED | `assert_fresh():259-287` and `_resolve_principal():111-122` implement each denial. My probes: missing→`no_step_up_evidence`; expired→`stale_step_up_evidence`; inactive/revoked event→`no_step_up_evidence`; replay→`replay_detected`; JTI/session/account substitution→`session_substitution`/`principal_not_found`; ambiguous→`ambiguous_step_up_evidence`; all four bad statuses and `is_active=False`/`is_locked=True`→`account_inactive`; rotated secret/removed method/disabled MFA→`factor_revoked`; terminated/expired session→`session_expired`. |
| 5 | Invalid config fails closed; default 300; validated 30–3600; inclusive 300 boundary; clock skew rejected; session revocation invalidates | VERIFIED | `config.py:209-235` default 300, bounds 30/3600 inclusive, lazy `int(raw.strip())` with `ValueError`. Service `:86-92` converts `ValueError`→`StepUpConfigurationError`; API `:111-112` → HTTP 503 (probe confirmed 503). Probes: 10 malformed/out-of-range values all denied; `30` and `3600` accepted; boundary 299/300/301 verified by the focused tests; future `verified_at`→`clock_skew_rejected`; revoked session→`session_revoked`. |
| 6 | No new auth authority/role; no weakening of step-up; no changes to NIAM login/refresh/logout or `mfa_used`; no production-readiness claim | VERIFIED | `git diff HEAD -- api/auth.py` shows only the additive step-up import + endpoint; `login`, `refresh`, `logout` bodies are byte-identical. `git diff HEAD -- authentication_service.py` contains only an `account_kind` (AUD-SEC-002) change; `mfa_used` line unchanged (`False` in both HEAD and WT; grep of the diff returned no `mfa_used` hunk). No role/permission file is in the step-up diff. `require_fresh_niam_step_up` has no consumers (`grep` found only its definition) — B4 is not wired. Design doc marks B4/production `BLOCKED`; `production_ready_items == 0`. |
| 7 | Migration additive only, reversible upgrade/downgrade on disposable DB, single Alembic head, links to `20261118_0001` | VERIFIED | Migration `20261119_0001` creates one table, has idempotent `_has_table()` guards and `downgrade()` dropping only that table; no existing table/column altered. `alembic heads` → single `20261119_0001 (head)`; probe: `REV_ID 20261119_0001`, `DOWN_REVISION 20261118_0001`, `PREV_EXISTS True`. Focused test `test_step_up_migration_upgrade_and_downgrade` passes on a throwaway SQLite DB. |
| 8 | DB unique constraint `(account_id, code_fingerprint)` in model AND migration; `IntegrityError` → `StepUpDenied` | VERIFIED | Model `step_up.py:29-33` `UniqueConstraint("account_id","code_fingerprint", name="uq_niam_step_up_account_code")`; migration `:52-54` same name/columns. Service `:219-230` catches `IntegrityError`, rolls back, audits, raises `StepUpDenied("replay_detected")`. Probe "duplicate code fingerprint DB insert" was rejected; probe "replay after window" (app-level check skipped) was still denied by the DB guard. |
| 9 | B4 source `adaptive_auth/routes.py` not modified **by this work item** | VERIFIED (with attribution caveat) | `git diff HEAD -- backend/app/identity/adaptive_auth/routes.py` = exactly one line: router prefix `/niam/adaptive-auth` → `/adaptive-auth`. No step-up symbol/import appears in the file (`grep` → NONE). The step-up design doc's change inventory excludes this file and attributes its state to an earlier phase; `GOVERNANCE/CHANGE_MANIFEST.md:94` likewise attributes it to S-08. Because the whole branch is one uncommitted working tree, per-work-item attribution cannot be proven from git alone; what is proven is that **no step-up content was introduced into B4**. |
| 10 | Focused tests, Ruff, app boot/OpenAPI | VERIFIED | Focused suite: **37 passed, 1 warning, EXIT=0** (73.91 s). Ruff on the 8 changed Python files: **All checks passed!, EXIT=0**. Boot: `BOOT_OK`, 1815 paths, endpoint present, 132 routes, EXIT=0. |

**Falsified:** none. **Not verifiable:** none of the required items; the one caveat is recorded in row 9 (work-item attribution of a pre-existing unrelated one-line prefix change).

---

## 2. Commands executed and exact results

All commands used the pinned interpreter `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python` (Python 3.12.13, pytest 9.1.1). Working dir for backend commands: `/home/samertts/workspace/projects/gula-integration/backend`.

| # | Command | Exact result | Exit |
|---|---|---|---|
| C1 | `git -C …/gula-integration rev-parse HEAD` / `--abbrev-ref HEAD` | `2206654dc713ea2de8c564a3207dfe05fde23549`, `integration/gula-unification-v1` | 0 |
| C2 | `git -C …/gula-platform rev-parse HEAD` | `f478676b6fc375338648dde46fbf076c015a3f91` (`remediate-security-001`) | 0 |
| C3 | `git status --porcelain \| wc -l` / `grep -c '^R'` | 379 lines at review start (390 later — concurrent agent writing report files, see §6); **20 staged `R` renames** throughout | 0 |
| C4 | `ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <py> -m pytest tests/unit/test_niam_step_up.py -q --tb=short` | `collected 37 items`; `37 passed, 1 warning in 73.91s` (Starlette/httpx deprecation warning only) | 0 |
| C5 | `<py> -m ruff check app/config.py app/identity/models/step_up.py app/identity/models/__init__.py app/identity/services/step_up_service.py app/identity/api/step_up.py app/identity/api/auth.py migrations/versions/20261119_0001_niam_step_up_events.py tests/unit/test_niam_step_up.py` | `All checks passed!` | 0 |
| C6 | `<py> /tmp/opencode/team_c_openapi_probe.py` (app boot) | `BOOT_OK`; `TOTAL_PATHS 1815`; `PATH_PRESENT True`; `BODY_REF #/components/schemas/StepUpVerifyRequest`; `BODY_PROPERTIES ["code","method"]`; `BODY_REQUIRED ["code"]`; `OPERATION_ID verify_step_up_niam_auth_step_up_verify_post`; `SECURITY [{"HTTPBearer":[]}]`; `ROUTE_COUNT 132` | 0 |
| C7 | `<py> -m alembic heads` | `20261119_0001 (head)` | 0 |
| C8 | `<py> /tmp/opencode/team_c_alembic_probe.py` | `HEADS ['20261119_0001']`; `REV_ID 20261119_0001`; `DOWN_REVISION 20261118_0001`; `PREV_EXISTS True`; `TOTAL_REVISIONS 109`; historical branch points converge to one head | 0 |
| C9 | `<py> /tmp/opencode/team_c_falsification_probe.py` (57 adversarial cases) | 56 OK, 1 apparent bypass traced to a bug in **my probe** (sentinel passed the real JTI); corrected in C10 | 0 |
| C10 | `<py> /tmp/opencode/team_c_falsification_probe2.py` | All 5 corrected JTI/account substitution cases → `StepUpDenied:session_substitution`; unauthenticated API → HTTP 401 | 0 |
| C11 | `<py> /tmp/opencode/team_c_api_probe2.py` (auth dependency overridden) | `auth + invalid config -> 503` (generic error envelope; still fail-closed). DB-dependent follow-up could not run without an operational DB (not permitted) | 0/1 (see §6) |
| C12 | `<py> /tmp/opencode/team_c_defect_repro*.py` (7 variants) | Isolated the one stderr anomaly: `ObjectDeletedError` in `_audit` after `rollback()` occurs **only when the synthetic Account row was inserted in the same uncommitted transaction**; with a committed account (`repro7`) `AUDIT_ROWS 1`, reason `replay_detected_concurrent`, no error | 0 |
| C13 | `git diff HEAD -- <B4/auth/authentication_service/config/models-init>` | B4 = 1-line prefix change; auth.py = additive endpoint only; authentication_service = `account_kind` change, no `mfa_used` hunk; config = S-07 cookie change + step-up loader; models-init adds `IdentityAuthorityRecord` + `NiamStepUpEvent` | 0 |
| C14 | `md5sum` of 3 protected files; `grep production_ready_items status_registry.json` | `effdfeaf…`, `1a02c015…`, `ea3969d0…`; both occurrences `0` (lines 480, 600) | 0 |
| C15 | Final `git rev-parse` + `sha256sum` of 7 step-up files + `grep -c '^R'` | Both HEADs unchanged; all seven SHA-256 values identical to the mid-review snapshot; 20 renames | 0 |

Timestamps: boot probe logged 2026-11-19 09:17:55–09:18:22 +0300 (= 06:17:55–06:18:22 UTC); final re-check 2026-11-19T06:35:16Z.

---

## 3. Falsification attempts and their outcomes

Synthetic SQLite, disposable data only. Probes live in `/tmp/opencode/` (outside both repositories).

| Attempt | Outcome |
|---|---|
| Cross-account completion (attacker submits victim's TOTP code) | DENIED — `factor_verification_failed` |
| Replay inside window | DENIED — `replay_detected` (app-level) |
| Replay **after** window (event aged > freshness, same code resubmitted) | DENIED — DB unique constraint → `StepUpDenied:replay_detected` |
| Session-ID substitution on `assert_fresh` | DENIED — `principal_not_found` |
| Token-JTI substitution on same session (`assert_fresh`) | DENIED — `session_substitution` |
| Token-JTI substitution at `verify` (`None`, `""`, `"jti-other"`) | DENIED — `session_substitution` (all three) |
| Actor account ID substituted for victim while keeping attacker's session | DENIED — `session_substitution` |
| Forged event row bound to a different session | DENIED — `no_step_up_evidence` |
| Future `verified_at` (clock skew) | DENIED — `clock_skew_rejected` |
| event `is_active=False` / `revoked_at` set | DENIED — `no_step_up_evidence` |
| `status` ∈ {suspended, locked, disabled, deactivated}, `is_active=False`, `is_locked=True` (verify and assert) | DENIED — `account_inactive` in every case |
| Factor rotation / method removal / MFA disabled after evidence | DENIED — `factor_revoked` |
| Session expired / terminated | DENIED — `session_expired` / `session_revoked` |
| Invalid config: `abc`, `0`, `-1`, `29`, `3601`, `""`, `"   "`, `300.0`, `1e9`, huge int | DENIED — `StepUpConfigurationError` (service); HTTP 503 (API) |
| Config bounds `30` and `3600` | ALLOWED as designed (inclusive bounds) |
| Duplicate `(account_id, code_fingerprint)` raw insert | DENIED — `IntegrityError` from DB constraint |
| Ambiguous same-instant evidence | DENIED — `ambiguous_step_up_evidence` |
| Malformed codes (`12345`, `1234567`, `abcdef`, full-width digits, whitespace-padded) | DENIED — `invalid_factor_code` or `factor_verification_failed` |
| Unsupported methods (`sms`, `SMS`, `totp `, `""`, `webauthn`) | DENIED — `unsupported_factor` |
| Ghost principal (account/session absent from DB) | DENIED — `principal_not_found` |
| Unauthenticated API POST | DENIED — HTTP 401 `AUTHENTICATION_REQUIRED` |
| Extra client identity claims (`account_id`, `session_id`, `verified_at`, `mfa_used`, `is_admin`) in request body | Structurally ignored: OpenAPI body has only `code`+`method`; service derives all identity from DB. Authenticated DB-path could not be exercised without an operational DB (not permitted). |
| One stderr `ObjectDeletedError` in the IntegrityError audit path | Investigated: reproducible **only** when the synthetic account is inserted in the same uncommitted transaction that `verify()` rolls back. With a committed account (production-like) the audit row is written (`replay_detected_concurrent`). **Not a production defect; no bypass in either case.** |

**Real bypasses found: 0.** The single initial "BYPASS" flag was a defect in my own probe (its `sess_jti=None` sentinel fell back to the real JTI); the corrected probe denies all JTI/identity substitutions.

---

## 4. Side-effect / API-compatibility / migration findings

- **API compatibility:** the new endpoint is purely additive. `login`, `refresh`, `logout` handler bodies in `api/auth.py` are byte-identical to HEAD. `mfa_used` remains `False` at assignment in `authentication_service.py` (HEAD line 91 → WT line 95). No existing route signature changed by this work item.
- **Unrelated co-resident changes (not attributed to step-up):** `config.py` also carries an S-07 secure-cookie change; `models/__init__.py` also exports `IdentityAuthorityRecord`; `authentication_service.py` carries an AUD-SEC-002 `account_kind` token change; `adaptive_auth/routes.py` carries a one-line router-prefix change. These were present in the shared uncommitted working tree and contain no step-up behavior.
- **Duplicate MFA engine:** none introduced; `shared.auth.mfa.verify_totp` is the only verifier used.
- **New authority:** none. `require_fresh_niam_step_up` is defined but has zero consumers; B4 remains unwired by design.
- **OpenAPI:** `POST /niam/auth/step-up/verify`, request body `StepUpVerifyRequest` = `{code, method}`, `required=[code]`, security `HTTPBearer`. 1815 total paths; 132 route objects.
- **Migration:** one head (`20261119_0001`), `down_revision=20261118_0001` exists, 109 revisions in the graph; upgrade/downgrade verified on a disposable SQLite DB; unique constraint name matches the model.

---

## 5. Invariant checks

| Invariant | Expected | Observed | Verdict |
|---|---|---|---|
| `gula-integration` HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` | identical at start and end | intact |
| `gula-platform` HEAD (read-only sibling) | `f478676b6fc375338648dde46fbf076c015a3f91` | identical at start and end | intact |
| 20 staged `R100` renames under `archive/legacy/workflow_runtime/` | 20 | 20 at every check | intact |
| `GOVERNANCE/FINAL_DECISION.md` md5 | `effdfeaf10234678d83b2668c4489552` | identical | intact (HOLD) |
| `MPI_FINAL_INDEPENDENT_AUDIT.md` md5 | `1a02c01563c93b07a7cdb92c0462bf36` | identical | intact (REJECT) |
| `MPI_INDEPENDENT_AUDIT_FINDINGS.md` md5 | `ea3969d09aaf7b0b28a065838b44a594` | identical | intact (REJECT) |
| `production_ready_items` in `GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json` | 0 | 0 at lines 480 and 600 | intact |
| Step-up file content during review | unchanged | SHA-256 of 7 core files identical mid- and end-review | intact |
| No repo writes by this reviewer | only the one allowed report | all probes in `/tmp/opencode/`; no commit/stage/push/merge/deploy; no operational DB/Redis | intact |

Note: the working-tree status line count rose from 379 to 390 during the review because a concurrent agent was writing report files (e.g. `NIAM_STEP_UP_SECURITY_REPORT.md`, `ADVERSARIAL_TEST_REPORT.md`). No step-up implementation file changed; all hashes above were re-checked after that activity.

---

## 6. Residual risks and open items

1. **B4 remains `BLOCKED`.** No cross-account administration endpoint was implemented or wired; `require_fresh_niam_step_up` is unused. Step-up is a prerequisite mechanism only.
2. **Owner approval pending.** Only the 300-second default is owner-approved; the 30–3600 validation bounds were assistant-chosen and still need owner ratification.
3. **No production claim.** `PRODUCTION READY` is not awarded; `production_ready_items == 0`; design doc and registry keep HOLD/REJECT verdicts intact.
4. **Full backend suite not re-run by this reviewer.** The mandate was the focused verification; I did not re-execute the ~5000-test suite. The implementation report's note of an unrelated CPU-timing benchmark failure remains an unverified assertion from my perspective.
5. **Authenticated HTTP path with a real DB not exercised** (no operational DB/Redis permitted). Fail-closed config behavior was verified through the API (503) and all identity checks through the service with synthetic SQLite; the combination of a genuine `get_current_niam_actor` + `get_db` was not run.
6. **Audit-write fragility in synthetic fixtures (non-production):** an `ObjectDeletedError` in `_audit` after `rollback()` occurs if the Account row was created in the same uncommitted transaction. Production accounts are committed, and the committed-account probe writes the audit row correctly; no bypass in either case. Worth noting if future tests assert on the `replay_detected_concurrent` audit entry without committing the fixture account.
7. **Attribution limitation (row 9):** per-work-item provenance of the one-line B4 prefix change is documented, not git-provable in a single uncommitted tree.
8. **Concurrent edits** to report files by another agent were observed; this report reflects the implementation SHA-256 values listed in §8, not any subsequent changes.

---

## 7. Final status line

`INDEPENDENTLY VERIFIED` is **awarded** to the Functional NIAM Step-Up Authentication prerequisite at **engineering scope only** — I personally re-read every file in scope, re-ran the focused tests (37/37, exit 0), Ruff (clean), app boot/OpenAPI, and the migration graph, and executed 57+ independent falsification probes with zero real bypasses and no unresolved defect. `PRODUCTION READY` is **NOT awarded**. B4 cross-account administration remains `BLOCKED`; owner approval of the work item and of the assistant-chosen 30–3600 bounds is pending; this is not a production, clinical, or regulatory claim.

---

## 8. Git SHA of tree reviewed and time of review

- `gula-integration` branch `integration/gula-unification-v1`, HEAD: **`2206654dc713ea2de8c564a3207dfe05fde23549`** (unchanged before and after review).
- `gula-platform` read-only sibling HEAD: **`f478676b6fc375338648dde46fbf076c015a3f91`** (unchanged).
- Review window: **2026-11-19T06:14Z → 2026-11-19T06:35Z** (final re-check `2026-11-19T06:35:16Z`).
- Reviewed file SHA-256 (identical at start/end of review):
  - `backend/app/config.py` — `97b5ab755868f4e854476305b481dc4bf2d12e8cd0dc17b0ec47b350f7d37377`
  - `backend/app/identity/services/step_up_service.py` — `b196485c5e31aa1f83ee582c126f8d2664583eaa5032c8c8076ea67c199fb34c`
  - `backend/app/identity/api/step_up.py` — `aa9d699fe373825a61d0d877898943074bc50df0eb3c346e8258939ca0363b95`
  - `backend/app/identity/api/auth.py` — `7dc7015690a9f7c7e4bef91a9640baeea6aac21090c3346d7c062cb2a26ec253`
  - `backend/app/identity/models/step_up.py` — `9f593d698055a348a6c03f4edbe89f6a97fcba60afa53b03caf955d675e9c771`
  - `backend/migrations/versions/20261119_0001_niam_step_up_events.py` — `37ccae55acc9d3853ca81877a03ae72bfdbcf029c30bf861c598cddf924d81ed`
  - `backend/tests/unit/test_niam_step_up.py` — `177189f5887e1fb809aab0bef92799c2ce6e7ae12d0938219a9979c6bd6def3c`
