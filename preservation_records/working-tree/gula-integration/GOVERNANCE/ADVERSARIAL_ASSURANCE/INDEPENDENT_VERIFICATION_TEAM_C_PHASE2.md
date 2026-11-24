# Independent Adversarial Verification — Team C — Phase 2 Tier A

**Artifact class:** Fresh-context independent verification (falsification attempt)
**Repository:** `gula-integration` — branch `integration/gula-unification-v1`
**Audited HEAD:** `2206654dc713ea2de8c564a3207dfe05fde23549`
**Sibling (READ-ONLY):** `gula-platform` HEAD `f478676b6fc375338648dde46fbf076c015a3f91`
**Date:** 2026-11-19
**Method:** Read auditor evidence → read current source → read new adversarial tests → re-run
tests → devise and execute NEW falsification probes (synthetic/disposable data only) →
re-check backward-compatibility neighbours → re-check invariants.
**Scratch artifacts:** all ad-hoc probes were written OUTSIDE the repository under
`/tmp/opencode/teamc_*.py`. **No source file, test file or governance file was created,
edited, weakened or deleted by this reviewer.** This report is the only file written.

---

## 1. Per-finding verdict table

| Finding | Auditor's original defect | Verdict (engineering scope) | Basis |
|---|---|---|---|
| **AUD-SEC-007** | Async NIAM actor query omitted `Account.is_locked.is_(False)` present in sync path | **INDEPENDENTLY VERIFIED** | 4/4 new tests re-run PASS; shared strict predicate `_active_niam_actor_predicates()` used by both dependencies; real-SQLite async probe rejects locked/status-locked accounts and admits clean accounts; only two actor resolvers exist in the tree and both use the helper. No falsification succeeded. |
| **AUD-API-001** | `GET /integration/standards` deterministically raised `AttributeError` → HTTP 500 | **INDEPENDENTLY VERIFIED** | 5/5 new tests re-run PASS; direct handler, OpenAPI and **e2e HTTP 200 with a real admin token** all return real accessor-derived values; no phantom attributes; service classes not given alias properties. No falsification succeeded. |
| **AUD-PRV-001** | Global NID lookup returned another facility's PHI via `patient_to_dict(existing)` | **INDEPENDENTLY VERIFIED** | 6/6 new tests re-run PASS; NID query is `db.query(Patient.id)` + `Patient.lab_id == lab_id`; returns only a non-identifying conflict marker; cross-facility identical-PHI probe returns `None`; `lab_id=None` fails closed; NID canonicalisation normalises Arabic-Indic/Extended-Arabic-Indic/whitespace/dash variants to one hash (no hash-bypass). No falsification succeeded. |
| **AUD-SEC-004** | `logout` read only cookies; Bearer clients retained usable sessions | **INDEPENDENTLY VERIFIED** *(with residual R-SEC-004-A — see §5)* | 4/4 new tests re-run PASS; independent e2e proves Bearer token → 401 after logout, JTI blacklisted, saved refresh token → 401 after Bearer logout, cookie logout still works. Core claim not falsifiable. One mixed-credential residual found and reported with reproducer. |
| **AUD-PRV-003** | Client-controlled `force_create` skipped all duplicate detection with no permission/reason/audit | **INDEPENDENTLY VERIFIED** | 10/10 new tests re-run PASS; `patients:delete` (pre-existing shared permission) gate + reason ≥10 chars + denial/success audit + same-lab NID 409 all confirmed; `lab_manager` and `doctor` denied, `admin` allowed; NID canonicalisation closes representation bypass; boundary reason 9→422 / 10→201. No falsification succeeded. |
| **AUD-CLIN-003** | Auto-validation route did not persist critical/abnormal flags, so `process_critical_result` returned `skipped` | **INDEPENDENTLY VERIFIED** *(with residual R-CLIN-003-A — see §5)* | 3/3 new tests re-run PASS; real SQLite+e2e probe confirms `is_critical=True`, `is_abnormal=True`, `validation_status=flagged`, and `process_critical_result` → `notification_pending` for critical-high **and** critical-low; normal result → `skipped`. Two residuals documented. |

**No fix was awarded `BLOCKED — FALSIFIED` or `BLOCKED — INSUFFICIENT EVIDENCE`.**

**IMPORTANT — package-level gate regression (not a fix defect):** two of the four engineering
claims are **FALSIFIED in the current tree** (§3). This does not change the six per-finding
verdicts above, but the integration package currently fails its own authoritative gates and
must not be treated as clean until the registry edit is corrected. **No `PRODUCTION READY`
was awarded to anything, by anyone, in this review.**

---

## 2. Exact commands run and results

All commands run from the stated working directory. Python interpreter is the pinned
`sibling venv` Python 3.12.13.

### 2.1 Re-run of the six new adversarial suites (required command)

```bash
cd /home/samertts/workspace/projects/gula-integration/backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python -m pytest \
  tests/unit/test_aud_sec_007_async_actor_lock.py \
  tests/unit/test_aud_api_001_standards_conformance.py \
  tests/unit/test_aud_prv_001_nid_duplicate_phi.py \
  tests/unit/test_aud_sec_004_bearer_logout.py \
  tests/unit/test_aud_prv_003_force_create_override.py \
  tests/unit/test_aud_clin_003_critical_flag_persistence.py \
  -q --tb=short
```
**Result:** `collected 32 items` → **32 passed, 2 warnings in 80.76s**.
Per-file: SEC-007 4, API-001 5, PRV-001 6, SEC-004 4, PRV-003 10, CLIN-003 3.

### 2.2 Combined targeted + neighbour regression (engineering claim "87 passed")

```bash
# same env/interpreter as 2.1, with five additional neighbour suites
tests/identity/test_workspace_api_hardening_phase5.py
tests/identity/test_security_audit_phase9.py
tests/unit/test_session_revocation.py
tests/unit/test_lims_critical_result_outbox.py
tests/unit/test_aud_sec_001_control_plane_authorization.py
```
**Result:** **87 passed, 4 warnings in 96.02s** — claim CONFIRMED.

### 2.3 Ruff on the 13 Phase 2 files

```bash
cd .../backend
python -m ruff check app/identity/api/workspaces.py app/integration/routes.py \
  app/services/patient_service.py app/routes/login.py \
  app/security/dependencies.py app/routes/patients.py app/lims/routes.py \
  tests/unit/test_aud_sec_007_async_actor_lock.py \
  tests/unit/test_aud_api_001_standards_conformance.py \
  tests/unit/test_aud_prv_001_nid_duplicate_phi.py \
  tests/unit/test_aud_sec_004_bearer_logout.py \
  tests/unit/test_aud_prv_003_force_create_override.py \
  tests/unit/test_aud_clin_003_critical_flag_persistence.py
```
**Result:** `All checks passed!` `RUFF_EXIT=0` — claim CONFIRMED.

### 2.4 Final-tree full regression (recorded log, as directed)

`tail /tmp/opencode/phase2_full_suite_final.log` →
`4945 passed, 27 skipped, 203 warnings in 469.50s (0:07:49)` / `EXIT=0` — log claim CONFIRMED,
**but the log is stale** (see §3.3).

### 2.5 Authoritative gates — CLAIMS FALSIFIED

```bash
cd /home/samertts/workspace/projects/gula-integration
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:backend \
  <venv-python> scripts/phase_b_gate.py
```
**Result:** `PHASE B INTEGRATION GATE: FAIL`, `GATE_EXIT=1`
```
[PASS] preservation
[FAIL] registry: undeclared status 'IMPLEMENTED / TESTED (engineering scope; Team C verification pending)'
[FAIL] focused: 3 failed, 28 passed (test_national_integration_registry.py)
[PASS] static  [PASS] types  [PASS] regression: 780 passed
```

```bash
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:backend \
  <venv-python> scripts/national_integration_verify.py
```
**Result:** `NATIONAL INTEGRATION REGISTRY VERDICT: FAIL`, `VERIFY_EXIT=1`
(the expected advisory `HEAD moved 0cb067ae → 2206654d` WARN is present, but the new ERROR is
not advisory).

Focused reproduction of the 3 failing tests:
```
backend/tests/unit/test_national_integration_registry.py::TestRealRegistry::test_real_registry_validates_against_repository
backend/tests/unit/test_national_integration_registry.py::TestRealRegistry::test_cli_passes_on_real_registry
backend/tests/unit/test_national_integration_registry.py::TestRealRegistry::test_every_status_in_real_registry_is_canonical
```
all fail on the single offending value; the other 28 pass.

### 2.6 New adversarial probes (scratch, outside repo)

```bash
cd .../backend
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. \
  <venv-python> -m pytest /tmp/opencode/teamc_falsify_probes.py \
  -p tests.conftest -q --tb=short -s
# → 3 failed, 10 passed (all three failures are probe-design issues or documented residuals,
#   analysed individually in §5; see follow-up runs which corrected them)
ENV=test ... <venv-python> -m pytest /tmp/opencode/teamc_probe_followup.py \
  -p tests.conftest -q --tb=short -s
# → 4 passed
ENV=test ... <venv-python> -m pytest /tmp/opencode/teamc_probe_api_e2e.py \
  -p tests.conftest -q --tb=short -s
# → login 403 (MFA-enrolment control on privileged accounts) — probe design corrected in follow-up
```

---

## 3. Falsification attempts — every one, including those that succeeded

### 3.1 AUD-SEC-007 (async actor lock)

| # | Attempt | Outcome |
|---|---|---|
| F7-1 | Real-SQLite async dependency call with `status="locked", is_locked=False` | **Rejected 401** — `Account.status == AccountStatus.active.value` predicate catches it. Two-layer defence. |
| F7-2 | Real-SQLite async call with `is_locked=True`, otherwise active | **Rejected 401**. Matches auditor's exact scenario. |
| F7-3 | Real-SQLite async call with `is_locked=NULL` | Could not construct: `niam_accounts.is_locked` is `NOT NULL`. Probe raised `sqlite3.IntegrityError`; the extra `IS FALSE` strictness is harmless. |
| F7-4 | Clean active account | **Authenticated** — no functional regression. |
| F7-5 | Static drift scan for a third actor resolver | Only `get_current_niam_actor_sync` and `get_current_niam_actor` exist; both call `_active_niam_actor_predicates`. `router.py::_AUTH_REQUIRED` uses the async one. No drift path found. |
| F7-6 | `locked_until` future but `is_locked=False` | Not a bypass: the canonical resolver (`identity/security.py:84`) also requires `is_locked` true. |
| F7-7 | Backward-compat: `locked_until` expired but `is_locked` still true | Async path now rejects where the generic resolver would allow. This is **stricter than before and matches the pre-existing sync path**; lock lifecycle (`AccountLifecycleService.transition`) clears `is_locked` on activation. Not a defect; noted as behavioural note N-SEC-007-A. |

**No falsification succeeded.**

### 3.2 AUD-API-001 (standards conformance)

| # | Attempt | Outcome |
|---|---|---|
| F1-1 | Direct handler call with all five real services | 200 body, real values (`R4`, `2.5.1`, 5 DICOM services, 11 modalities, 6 IHE profiles, 10 terminology systems). |
| F1-2 | **e2e HTTP GET with a real `master_admin` token** | **200** with the full real body (first attempt 403 was a probe artefact: privileged login correctly requires MFA enrolment; corrected by minting the token directly). |
| F1-3 | `GET /openapi.json` | 200; `/integration/standards` present — no schema-generation break. |
| F1-4 | Phantom attribute names in handler source / alias properties on service classes | None present (asserted by the 5 tests and re-checked by reading all five service classes). |
| F1-5 | JSON round-trip through FastAPI encoding | Passed; all values are lists/str. |

**No falsification succeeded.**

### 3.3 AUD-PRV-001 (cross-facility PHI)

| # | Attempt | Outcome |
|---|---|---|
| P1-1 | Cross-facility NID match with **identical name, phone and birth date** at victim facility | `_check_duplicates(lab_id=1, …)` → `None`. No leak. |
| P1-2 | `lab_id` passed as string `"1"` instead of int | → `None`. No leak. |
| P1-3 | Same-facility match response inspected for all PHI/internal-id keys | Only `{"duplicate": True, "message": …, "message_ar": …, "conflict": {"scope":"national_id","facility_scoped":True}}`; no `id`, `health_id`, `full_name`, `existing_patient`, facility, etc. |
| P1-4 | NID representation bypass (Arabic-Indic `١٢٣…`, Extended-Arabic-Indic `۱۲۳…`, whitespace, dashes) | All normalise to `123456789012` and one identical HMAC — no hash divergence bypass. |
| P1-5 | `lab_id=None` | Lookup skipped — fail-closed. |
| P1-6 | Same-facility phone/name duplicate detection | Still returns 409 with `matches` (within-tenant PHI only) — no functional regression. |

**No falsification succeeded.**

### 3.4 AUD-SEC-004 (Bearer logout) — residual found

| # | Attempt | Outcome |
|---|---|---|
| S4-1 | Bearer-only logout → same token on `/session` | **401** — core fix works. |
| S4-2 | Bearer JTI blacklist check | `False → True` — works. |
| S4-3 | **Saved refresh token after Bearer logout** via `POST /auth/refresh` | Baseline 200 → after logout **401**. Layer-2 perm bump covers the refresh token even though the mobile client never sends a refresh cookie. Strong evidence the fix is effective end-to-end. |
| S4-4 | Cookie (web) logout still works | 200, then Bearer session 401 — no regression. |
| S4-5 | Static guard: `logout` uses `_extract_token` + `HTTPAuthorizationCredentials` | Present. |
| **S4-6** | **Invalid Bearer header + valid access-token cookie** | **PARTIAL FALSIFICATION of logout's general success semantics — see R-SEC-004-A below.** `logout` returns `200 {"message":"Logged out successfully"}`, but the JTI is **not** blacklisted and `perm_version` is **not** bumped; re-arming the access cookie yields **200** on `/session`. |

S4-6 is reported as a **residual**, not a falsification of this finding: the presented credential
on *every* route in that request context is the invalid Bearer, and the pure Bearer-only scenario
named in the finding is definitively fixed (S4-1…S4-4). Minimal reproducer in §5.

### 3.5 AUD-PRV-003 (force_create override)

| # | Attempt | Outcome |
|---|---|---|
| P3-1 | `doctor` role + force_create + valid reason | **403** + `patient_duplicate_override_denied` audit. |
| P3-2 | `lab_manager` role (new probe) + force_create + valid reason | **403**. |
| P3-3 | `admin` + missing / `""` / `"short"` / whitespace-padded short reason | **422** for all; boundary probe: 9 chars → 422, 10 chars → 201, 10-chars-with-one-nonspace → 422. |
| P3-4 | `admin` + valid reason | 201 + `patient_duplicate_override` audit containing reason. |
| P3-5 | Direct service call with `force_create=True`, no reason | 422 — defence in depth holds. |
| P3-6 | Exact same-lab NID collision via force_create | 409, patient count unchanged. |
| P3-7 | NID Unicode/whitespace/dash variants | One canonical hash — no representation bypass of the 409 guard. |
| P3-8 | Permission provenance | `patients:delete` already exists in read-only sibling `shared/rbac/permissions.py:139`; **no new permission added**, sibling tree clean. |

**No falsification succeeded.**

### 3.6 AUD-CLIN-003 (critical flag persistence)

| # | Attempt | Outcome |
|---|---|---|
| C3-1 | Critical high (7.2 vs critical_high 6.5) e2e | flags `['high','critical_high']`; persisted `is_critical=True`, `is_abnormal=True`, `flag='high'`, `validation_status='flagged'`; `process_critical_result` → `notification_pending`. |
| C3-2 | **Critical low (2.0 vs critical_low 2.5)** — new boundary probe | flags `['low','critical_low']`; persisted `is_critical=True` → alert path reached. Both critical directions covered. |
| C3-3 | Normal value (4.0) | `is_critical=False` → `skipped`. No spurious alert. |
| C3-4 | Flag ordering → FHIR interpretation | `flag='high'` (first flag) maps to FHIR code `H`, not a critical code. **Pre-existing behaviour of the create path** (`lims/services.py` uses `validation["flags"][0]` too) — not introduced by this fix. Recorded as residual R-CLIN-003-B. |
| **C3-5** | Re-run auto-validation after out-of-band value change 7.2 → 4.0 | `flags=[]` but persisted `is_critical`, `is_abnormal`, `flag='high'` remain; `process_critical_result` → **`notification_pending`** for a now-normal result. Recorded as residual R-CLIN-003-A. No in-tree route found that mutates `value_numeric` after creation (static scan: 0 `value_numeric =` assignments in LIMS routes/services); reachable only via out-of-band/corrected-result tooling. |

**No falsification of the stated fix succeeded.**

### 3.7 Engineering-claim falsifications (successful)

**F-CLAIM-1 — `scripts/phase_b_gate.py PASS 6/6` is FALSE in the current tree.**
Actual: 4 PASS / 2 FAIL, exit 1. Root cause below.

**F-CLAIM-2 — `scripts/national_integration_verify.py PASS` is FALSE in the current tree.**
Actual verdict `FAIL`, exit 1, same root cause.

**F-CLAIM-3 — "final-tree full regression 4945 passed / EXIT=0" is stale as a claim about the
final tree.** `stat` shows the full-suite log finished at `01:24:08`, while
`GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json` (and the findings/closeout docs) were
written at `01:24:32` — 24 s later. The three registry tests that now fail are part of
`tests/`, so the recorded 4945/0-failed tree is no longer the current tree. I did **not**
re-run the ~8-minute suite (directed not to); the 3 focused failures are reproduced above and
are sufficient evidence.

**Root cause / minimal reproducer for F-CLAIM-1 and F-CLAIM-2 (single change):**
```
File: GOVERNANCE/NATIONAL_INTEGRATION/status_registry.json
Path: adversarial_assurance.phase2_tier_a.status
Current value: "IMPLEMENTED / TESTED (engineering scope; Team C verification pending)"
Allowed values (pinned in scripts/national_integration_verify.py: CANONICAL_STATUS):
  IMPLEMENTED | TESTED | INTEGRATED | INDEPENDENTLY VERIFIED | PRODUCTION READY |
  BLOCKED | NOT IMPLEMENTED
```
Reproduce:
```bash
cd /home/samertts/workspace/projects/gula-integration
ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:backend \
  <venv-python> -m pytest backend/tests/unit/test_national_integration_registry.py -q --tb=short
# → 3 failed, 28 passed
ENV=test ... <venv-python> scripts/national_integration_verify.py
# → NATIONAL INTEGRATION REGISTRY VERDICT: FAIL
```
A status string carrying a parenthetical annotation is not in the exact status vocabulary.
The annotation belongs in a sibling `basis`/`note` field. **I did not edit this file** —
reporting only, per my mandate.

---

## 4. Residuals found by this reviewer

| ID | Severity | Finding | Residual |
|---|---|---|---|
| **R-SEC-004-A** | Medium (edge case) | AUD-SEC-004 | Mixed credentials: a **valid access-token cookie shadowed by an invalid/stale `Authorization: Bearer` header** causes `logout` to return 200 while blacklisting nothing and bumping no `perm_version`. Minimal reproducer: (1) login as a non-privileged user; (2) `client.cookies.clear(); client.cookies.set("access_token", access)`; (3) `POST /logout` with header `Authorization: Bearer not-a-jwt` → `200`; (4) inspect `is_token_blacklisted(jti)` → still `False`; (5) re-set the same access cookie and `GET /session` → `200`. Cause: `_extract_token` gives Bearer precedence and `_revoke()` has no fallback to the cookie when Bearer decoding fails. Suggested (NOT implemented): on failed/decode-less Bearer, also revoke the cookie token, or derive `user_id` from the refresh cookie independently. |
| **R-CLIN-003-A** | Low / clinical-safety-adjacent | AUD-CLIN-003 | Re-running the manual auto-validation after an out-of-band change of `value_numeric` from critical to normal leaves stale `is_critical/is_abnormal/flag` and produces a false `notification_pending` (details in C3-5). No in-tree route performs such a value mutation. |
| **R-CLIN-003-B** | Low, pre-existing | AUD-CLIN-003 | `flag` is set from `validation["flags"][0]`; for `['high','critical_high']` the persisted flag is `'high'` and FHIR interpretation maps to `H`. Identical logic exists in the create path, so the fix did not introduce this; recorded for clinical-owner awareness. |
| **N-SEC-007-A** | Informational | AUD-SEC-007 | The shared strict `is_locked IS FALSE` is stricter than the generic resolver's `is_locked AND locked_until > now`; an account past `locked_until` but not yet auto-transitioned is rejected on async NIAM routes. This matches the pre-existing sync path and fails closed. |
| **R-GOV-001** | **HIGH — package-level blocker** | Cross-cutting | Both authoritative gates FAIL and 3 registry tests FAIL because of the single non-canonical status string (§3.7). Must be corrected before the integration tree can be considered gate-clean. |

Residuals already declared by engineering (Redis-only cross-worker revocation; no DB unique
constraint for NID; MPI merge path for same-lab collision; no clinician recipient policy) are
acknowledged and not repeated here.

---

## 5. Invariant re-check results

| Invariant | Result |
|---|---|
| Integration HEAD `2206654dc713ea2de8c564a3207dfe05fde23549` unchanged | **PASS** |
| Exactly 20 staged entries, all `R100` under `archive/legacy/workflow_runtime/`, untouched | **PASS** (`STAGED_COUNT=20`, `STAGED_NON_R100=0`) |
| `GOVERNANCE/FINAL_DECISION.md` MD5 `effdfeaf10234678d83b2668c4489552` | **PASS** |
| `.../MPI_FINAL_INDEPENDENT_AUDIT.md` MD5 `1a02c01563c93b07a7cdb92c0462bf36` | **PASS** |
| `.../MPI_INDEPENDENT_AUDIT_FINDINGS.md` MD5 `ea3969d09aaf7b0b28a065838b44a594` | **PASS** |
| Sibling `gula-platform` HEAD `f478676b6fc375338648dde46fbf076c015a3f91` unchanged; working tree clean; no new commit | **PASS** |
| `production_ready_items == 0` and `production_ready_count == 0` (both registers) | **PASS** |
| Owner-gated decisions (HOLD, MPI REJECT, MP-001, ODR-001…004, D-020/D-021, ADR-A…J, AUD-02/07/16, AUD-API-002, AUD-ARCH-003) untouched | **PASS** (no diff in the protected decision documents/bytecode; protected MD5s intact) |
| AUD-SEC-008 not implemented before owner ratification of AUD-ARCH-003 | **PASS** (`status=DISCOVERED`, `engineering_status=NOT IMPLEMENTED`) |
| No new permission added to `shared.rbac` | **PASS** — `patients:delete` pre-exists at `shared/rbac/permissions.py:139`; sibling tree clean |
| No commit / push / PR / merge / deploy / external service / operational DB / Redis / real patient data used by this reviewer | **PASS** |
| No test weakened, deleted or skipped by this reviewer | **PASS** |

---

## 6. Final assurance statement

Six Phase 2 Tier A fixes were subjected to a genuine fresh-context falsification attempt.
None of the six was falsified at its stated engineering scope; each is awarded
**INDEPENDENTLY VERIFIED (engineering scope only)**. This award explicitly excludes runtime,
operational-DB, external-integration, clinical, regulatory and deployment validation.

The engineering package around them is **not clean**: two authoritative gates and three
registry tests currently fail on a non-canonical status value added after the recorded full
suite ran (§3.7, R-GOV-001). That defect is reported, not fixed, per my mandate.

**No `PRODUCTION READY` status was awarded to any finding, fix, gate or workstream by this
reviewer. No self-award was made. Owner-gated decisions remain untouched.**

---

*Reviewer: Team C — independent adversarial verification subagent (fresh context).*
