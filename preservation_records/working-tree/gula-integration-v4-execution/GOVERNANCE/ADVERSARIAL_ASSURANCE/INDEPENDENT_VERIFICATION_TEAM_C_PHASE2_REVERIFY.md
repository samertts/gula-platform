# Independent Verification Team C — Phase 2 Tier A Post-Review Re-Verification (Addendum)

**Report:** `GOVERNANCE/ADVERSARIAL_ASSURANCE/INDEPENDENT_VERIFICATION_TEAM_C_PHASE2_REVERIFY.md`
**Predecessor:** `INDEPENDENT_VERIFICATION_TEAM_C_PHASE2.md` (six fixes independently verified at engineering scope; four residuals reported)
**Reviewer mode:** fresh-context adversarial re-verification of the three corrections; documentation-only confirmation of the fourth
**Scope:** focused tests + static inspection only. The ~8-minute full suite was **not** re-run (a fresh one is running separately by others).
**Boundaries:** no source/test/registry edits by the reviewer; no commit, push, PR, merge, deploy, external access, or operational DB. Synthetic data only. `gula-platform` was read-only.
**Status vocabulary:** unchanged. **No `PRODUCTION READY` was awarded.**

## Verdict summary

| Residual | Correction under review | Verdict |
|---|---|---|
| R-GOV-001 (HIGH, package blocker) | gate defect: non-canonical status string in registries | **VERIFIED CORRECTED** |
| R-SEC-004-A (medium) | invalid Bearer shadowing a valid access cookie on logout | **VERIFIED CORRECTED** |
| R-CLIN-003-A (low) | stale critical/abnormal/flag surviving re-validation | **VERIFIED CORRECTED** |
| R-CLIN-003-B (low, pre-existing) | documentation only — flag-ordering in create path | **VERIFIED CORRECTED (documentation confirmed; no fix intended or made)** |

No correction was falsified. No reproducer of a surviving defect was found.

---

## 1. R-GOV-001 — VERIFIED CORRECTED

### Static inspection (Python 3.12 pinned venv)
```
cd /home/samertts/workspace/projects/gula-integration
/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python -c "<registry inspection>"
```
Results:
- `status_registry.json → adversarial_assurance.phase2_tier_a.status == "INDEPENDENTLY VERIFIED"` (exact canonical value); the parenthetical annotation is now in a sibling `basis` field.
- `FINDINGS_REGISTER.json → phase2_tier_a.status == "INDEPENDENTLY VERIFIED"` with annotation in `basis`.
- Counts: `FINDINGS_REGISTER.independently_verified_count = 11`, `production_ready_count = 0`; `status_registry` IV fields `11 / 15 / 0`; `REMEDIATION_REGISTER.summary.independent_verification_awarded = 15`, `independent_verification_pending = 0`, `production_ready = 0`.
- All six Phase 2 findings/remediations carry `independent_verification = "INDEPENDENTLY VERIFIED"` and `verification_record = "INDEPENDENT_VERIFICATION_TEAM_C_PHASE2.md"`.

### Canonical-status scan of all three registries
```
/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python -c "<walk status-like string fields against 7-value vocabulary>"
```
- `status_registry.json`: 49 status-like string fields, **0 non-canonical**
- `FINDINGS_REGISTER.json`: 406 status-like string fields, **0 non-canonical in the assurance-status axis**
- `REMEDIATION_REGISTER.json`: 60 status-like string fields, **0 non-canonical**

Transparency note: the scan's raw walker also flags 81 `findings[i].status = "DISCOVERED"` values. These are **not** assurance-status values: both registers declare `status_vocabulary_used = ['IMPLEMENTED','TESTED','INTEGRATED','INDEPENDENTLY VERIFIED','PRODUCTION READY','BLOCKED','NOT IMPLEMENTED']`, and `FINDINGS_REGISTER.finding_status_note` explicitly states `DISCOVERED` is the Team A audit-discovery marker, not an assurance award ("No finding has been awarded INDEPENDENTLY VERIFIED or PRODUCTION READY" at the finding level). Within the documented status vocabulary there are zero violations, and the canonically awarded statuses are confined to the remediation/registry axis.

### Gate re-runs (from repo root, pinned venv)
```
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:backend <venv-python> scripts/phase_b_gate.py
```
→ `PHASE B INTEGRATION GATE: PASS`, `PHASE_B_GATE_EXIT=0`; 6/6 checks, regression `780 passed, 1 warning in 5.30s`; static `All checks passed!`; types `0 new MyPy errors`.

```
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:backend <venv-python> scripts/national_integration_verify.py
```
→ `NATIONAL INTEGRATION REGISTRY VERDICT: PASS`, `NIV_EXIT=0`. Only the expected advisory WARN: `HEAD moved since baseline (recorded 0cb067ae, current 2206654d)`.

```
cd backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <venv-python> -m pytest tests/unit/test_national_integration_registry.py -q --tb=short
```
→ `31 passed, 1 warning in 1.51s` (the three previously failing tests now pass).

---

## 2. R-SEC-004-A — VERIFIED CORRECTED

### Static inspection
`backend/app/routes/login.py::logout` now revokes **every presented credential independently**:
- `_revoke(_extract_token(credentials, request))` — shared Bearer-or-cookie extractor (Bearer precedence)
- `_revoke(credentials.credentials)` — raw Bearer credential
- `_revoke(request.cookies.get("access_token"))` — access cookie
- `_revoke(request.cookies.get("refresh_token"), refresh=True)` — refresh cookie
- `_revoke` decodes with `decode_token`, falls back to `decode_refresh_token` (covers refresh in Bearer slot), blacklists JTI for the remaining TTL, and captures `user_id`; `bump_perm_version(...)` + `db.commit()` follow for the authoritative DB-layer revocation.

### Regression file (integrator's 5 tests)
```
cd backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <venv-python> -m pytest tests/unit/test_aud_sec_004_bearer_logout.py -q --tb=short
```
→ `5 passed, 1 warning in 70.68s`, `SEC004_EXIT=0`. Includes `test_invalid_bearer_does_not_shadow_valid_access_cookie`.

### NEW adversarial probes (reviewer-authored; `/tmp/opencode/teamc_sec004_reverify_probes.py`)
Loaded with the repo conftest as a plugin (`-p tests.conftest`), never written into the repo:
```
cd backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <venv-python> -m pytest -p tests.conftest /tmp/opencode/teamc_sec004_reverify_probes.py -q --tb=short
```
→ `4 passed in 72.78s`, `PROBES_EXIT=0`.

| Probe | Setup | Assertions / result |
|---|---|---|
| P1 valid Bearer + invalid cookie | cookie `access_token=garbage-cookie-value`, header `Bearer <valid>` | logout 200; Bearer JTI blacklisted; **perm_version bump proven** by a brand-new token carrying the old `perm_ver` claim receiving 401 on `/session` (JTI not blacklisted) |
| P2 refresh token only in Bearer slot + invalid cookie | header `Bearer <refresh>`, garbage access cookie | logout 200; refresh JTI (decoded independently with the refresh secret) blacklisted; fresh old-`perm_ver` access token → 401 |
| P3 expired Bearer + valid cookie | self-signed expired HS256 token (exp −60s, `decode_token` returns None precondition), valid access cookie | logout 200; valid cookie JTI blacklisted; re-armed cookie → 401; fresh old-`perm_ver` token → 401 |
| P4 duplicate JTI across all four transports | header `Bearer <access>`, cookies `access_token=<same access>` and `refresh_token=<refresh>` | logout 200 (idempotent); both access and refresh JTIs blacklisted; fresh old-`perm_ver` token → 401 |

The perm-version layer was isolated deliberately: each probe mints a **new**, unblacklisted token with the old `perm_ver`, so a 401 cannot be explained by the JTI blacklist alone. All four probes confirm both layers fire.

---

## 3. R-CLIN-003-A — VERIFIED CORRECTED

### Static inspection
`backend/app/lims/routes.py::run_auto_validation` now has an explicit `else` branch for `validation["flags"] == []`:
```
if result.is_critical or result.is_abnormal or result.flag:
    result.is_critical = False
    result.is_abnormal = False
    result.flag = None
    changed = True
```
with the comment that previously emitted outbox events are immutable and deliberately untouched. `git diff -- backend/app/lims/routes.py` confirms this branch is the only change to the flag-persistence block; the `result.flag = validation["flags"][0]` line is unchanged from the Phase 2 fix.

### Regression file (integrator's 4 tests)
```
cd backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <venv-python> -m pytest tests/unit/test_aud_clin_003_critical_flag_persistence.py -q --tb=short
```
→ `4 passed, 2 warnings in 77.86s`, `CLIN003_TEST_EXIT=0`. Includes `test_revalidation_clears_stale_critical_flags`.

### NEW adversarial probes (reviewer-authored; `/tmp/opencode/teamc_clin003_reverify_probes.py`)
```
cd backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <venv-python> -m pytest -p tests.conftest /tmp/opencode/teamc_clin003_reverify_probes.py -q --tb=short
```
→ `3 passed, 2 warnings in 90.33s`, `CLIN003_PROBES_EXIT=0`.

| Probe | Setup | Assertions / result |
|---|---|---|
| P1 abnormal(high) → normal | ref range 3.5–5.0, critical_high 6.5; value 5.6 → `flags=['high']`, persisted `is_abnormal=True`, `flag='high'`; out-of-band correction to 4.0 | re-validation `flags=[]`; `is_abnormal=False`, `is_critical=False`, `flag=None`; `OutboxEvent` count unchanged |
| P2 critical-low → normal | ref range with `critical_low=2.5`; value 2.0 → `flags` contains `critical_low`, `is_critical=True`; `process_critical_result` → `notification_pending`; outbox count captured | correction to 4.0 → `flags=[]`, all three stale markers cleared; previously emitted outbox event still present (count unchanged); downstream `process_critical_result` → `skipped` |
| P3 repeated re-validation idempotence | critical-high 7.2 → emitted outbox event; corrected to 4.0; re-validated **three** times | every pass returns `flags=[]`, markers stay cleared, outbox count unchanged; downstream `skipped` |

Outbox invariance was checked directly via `db.query(OutboxEvent).count()` before and after the clearing re-validation in all three probes.

---

## 4. R-CLIN-003-B — VERIFIED CORRECTED (documentation-only; no fix intended)

Confirmed in both target registries:
- `FINDINGS_REGISTER.json → findings[AUD-CLIN-003].remediation.residual` contains: `R-CLIN-003-B (low, pre-existing): flag uses first emitted flag, so ['high','critical_high'] persists 'high' (FHIR 'H'); identical in the create path — clinical-owner awareness only, not introduced by this fix.`
- `REMEDIATION_REGISTER.json → remediations[REM-CLIN-003].residual` contains the identical text.
- `team_c_verification.phase2.residuals_reported` includes `R-CLIN-003-B`; the note records it as pre-existing and documentation-only.

No source change was made for it: `git diff -- backend/app/lims/services.py` is empty (the create path at `services.py:272` still uses `validation["flags"][0] if validation["flags"] else None`), and `routes.py:2192` retains the same first-flag expression from the Phase 2 fix. No fix was requested, and none was attempted by this reviewer.

---

## Invariants (re-checked at start and end of this review)

| Invariant | Expected | Observed | Result |
|---|---|---|---|
| Integration repo HEAD | `2206654dc713ea2de8c564a3207dfe05fde23549` | identical | PASS |
| Staged R100 entries | 20, all `R100`, 0 non-R100 | `STAGED=20`, `NON_R100=0` | PASS |
| Protected MD5s | `effdfeaf…`, `1a02c015…`, `ea3969d0…` | identical | PASS |
| Sibling `gula-platform` HEAD | `f478676b6fc375338648dde46fbf076c015a3f91` | identical; `SIBLING_DIRTY=0` | PASS |
| `production_ready` | 0 everywhere | 0 `production_ready": true` occurrences in all three registries; `FR.production_ready_count=0`, `RR.summary.production_ready=0` | PASS |

Reviewer-authored probe files exist **only** in `/tmp/opencode/` (`teamc_sec004_reverify_probes.py`, `teamc_clin003_reverify_probes.py`). No repo source, test, or registry file was edited by this reviewer. No commit, push, PR, merge, deploy, external access, or operational DB was used.

## Final statement

All three corrected residuals survived fresh-context falsification attempts and are marked **VERIFIED CORRECTED**; the fourth is confirmed as documented-only with no source fix. **No `PRODUCTION READY` was awarded** — this addendum certifies only focused engineering/static/targeted-test re-verification of the four listed items. The fresh full-suite run being performed separately is outside this addendum's scope; no conclusion about it is drawn here. Owner-gated decisions, clinical/regulatory validation, runtime, and operational-DB verification remain out of scope and untouched.
