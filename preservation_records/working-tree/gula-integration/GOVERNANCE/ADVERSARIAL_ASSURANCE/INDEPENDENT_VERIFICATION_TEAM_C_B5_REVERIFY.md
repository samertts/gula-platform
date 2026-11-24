# Independent Verification — Team C — B5 Re-Verification (fresh context)

- **Report timestamp:** 2026-11-19T10:35:28Z
- **Verifier:** Independent Verification Team C — **fresh context**. No code, test, or fix in this scope was authored by this verifier. No implementer claim was accepted without independent code inspection and disposable runtime evidence.
- **Posture:** adversarial / fail-closed. The entire working tree was treated as **READ-ONLY**. No source, test, config, MD5, staged rename, branch ref, or governance record was modified, staged, committed, pushed, merged, or deployed.
- **Repo / branch / HEAD:** `/home/samertts/workspace/projects/gula-integration`, branch `integration/gula-unification-v1`, HEAD `2206654dc713ea2de8c564a3207dfe05fde23549` (verified before and after all work).
- **Sibling repo:** `/home/samertts/workspace/projects/gula-platform` — READ-ONLY; only its pinned interpreter was used.
- **Pinned interpreter:** `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python` (Python 3.12.13, pytest 9.1.1).
- **Test environment:** `cd backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned python> …`; disposable in-memory SQLite only.
- **Scope:** re-verification of the three B5 findings in `INDEPENDENT_VERIFICATION_TEAM_C_TIER_B.md` §4/§6 (authority laundering, integration gap, transitive revocation), plus two novel adversarial probes against the stated B5 invariant. B1/B2/B3 and prior residual items 1/2/3/6 are **explicitly out of scope**.

> **Non-claims.** This is an **engineering-scope** verification only. **No `PRODUCTION READY` verdict is awarded or permitted here.** No operational DB (`gula`), Redis, real patient data, external network, or deployment target was touched. Owner sign-off, production/operational release, Ministry/legal ratification, and clinical-safety gates are outside this scope and are not claimed. Statuses use only the exclusive vocabulary: `IMPLEMENTED / TESTED / INTEGRATED / INDEPENDENTLY VERIFIED / PRODUCTION READY / BLOCKED / NOT IMPLEMENTED`.

---

## 1. Verdict table

| # | Prior finding | Verdict (exclusive vocabulary) | Basis |
|---|---|---|---|
| **1** | HIGH — authority laundering: narrow-delegation holder re-delegates an unheld sibling key (`lab_result.export`) | **INDEPENDENTLY VERIFIED** (remediated) | Exact prior repro DENIED; mixed keys DENIED; depth-2 holder DENIED; scope widening DENIED; every denial audited as `permission_exceeds_holding_authority` / `scope_exceeds_authority`; legitimate direct/full and narrow/deep grants still work. **Zero real API bypasses found.** |
| **2** | HIGH — integration gap: live `/authz/delegations` used ungoverned legacy service; canonical `niam_delegations` never written | **INDEPENDENTLY VERIFIED** (remediated) | Real app OpenAPI exposes `/niam/delegations` + revoke; POST against real app wrote `niam_delegations`, changed `effective_permissions`, GET 200, revoke removed authority; all three legacy methods HTTP 410 and wrote **no** row to either table; no route imports the legacy `DelegationService`. |
| **3** | MEDIUM — transitive revocation: delegate retained authority after upstream holding was revoked | **INDEPENDENTLY VERIFIED** (remediated) | Enforcement-time chain walk denies on root revoke/expiry, intermediate revoke/expiry, role/permission deactivation, forged cycle, and depth tamper; a legitimately live depth-2 chain still grants. **Zero real bypasses found.** |
| **OVERALL B5** | delegation only into canonical authority | **INDEPENDENTLY VERIFIED** (engineering scope) | All three prior findings remediated; zero real API bypasses in genuine adversarial attempts. **One residual hardening gap** (novel probe 1, enforcement trusts a directly-forged row) is documented in §6; it requires out-of-band DB write and is therefore not an API-reachable bypass of these three findings. |

**No `PRODUCTION READY` is awarded.**

---

## 2. Focused test command (exact command, exact output tail, EXIT_CODE)

```
cd /home/samertts/workspace/projects/gula-integration/backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. /home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python -m pytest tests/unit/test_b4_cross_account_security.py tests/unit/test_b1_phi_permission_map.py tests/test_consent.py tests/unit/test_b3_verified_guardian.py tests/unit/test_b5_delegation.py tests/unit/test_b5_security_regressions.py tests/unit/test_b5_migration_drift_regression.py tests/identity/test_authorization_phase7.py tests/identity/test_authorization_phase8.py tests/health_core/test_authorization_synthetic_scope.py tests/test_citizen_relationship_workflow.py tests/unit/test_nhid_readiness.py tests/unit/test_niam_step_up.py -q
```

Verbatim output tail:

```
collected 238 items

tests/unit/test_b4_cross_account_security.py ........................    [ 10%]
tests/unit/test_b1_phi_permission_map.py .............                   [ 15%]
tests/test_consent.py ..........................                         [ 26%]
tests/unit/test_b3_verified_guardian.py ................................ [ 39%]
.........                                                                [ 43%]
tests/unit/test_b5_delegation.py ..........................              [ 54%]
tests/unit/test_b5_security_regressions.py ......                        [ 57%]
tests/unit/test_b5_migration_drift_regression.py ......                  [ 59%]
tests/identity/test_authorization_phase7.py .....                        [ 61%]
tests/identity/test_authorization_phase8.py ...................          [ 69%]
tests/health_core/test_authorization_synthetic_scope.py .......          [ 72%]
tests/test_citizen_relationship_workflow.py .....                        [ 74%]
tests/unit/test_nhid_readiness.py .......................                [ 84%]
tests/unit/test_niam_step_up.py .....................................    [100%]

=============================== warnings summary ===============================
.../fastapi/testclient.py:1: StarletteDeprecationWarning: ...
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
================== 238 passed, 1 warning in 88.61s (0:01:28) ===================
EXIT_CODE=0
```

Both new files were included: `test_b5_security_regressions.py` 6 passed, `test_b5_migration_drift_regression.py` 6 passed. A green suite is **necessary but not sufficient**; all probes below were written independently.

---

## 3. Finding 1 — authority laundering: exact re-tests and variations

### 3.1 Exact prior reproduction (unmodified probe `/tmp/opencode/tierC_probe_b5_escalation.py`)

```
cd backend && ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:.. <pinned python> /tmp/opencode/tierC_probe_b5_escalation.py
```

```
ACTOR effective permissions: set()
ACTOR holds PERM A: False  PERM B: False
RESULT: delegate_role DENIED: DelegationDenied Requested permissions exceed the actor's own holding authority
VERDICT: FAIL_CLOSED
EXIT_CODE=0
```

**The exact prior reproduction is now DENIED.** Note a difference from the 2026-11-19T09:38:19Z report: with the new enforcement-time chain walk, the prior fixture's delegator (`_OTHER`, which had no direct assignment) produces an empty effective-permission set for the narrow holder. The `delegate_role` call itself is still independently denied by the new `held_keys` guard at `delegation_service.py:229-246` with reason `permission_exceeds_holding_authority`, so the hardening is not an artifact of the chain check.

### 3.2 Independent probe `/tmp/opencode/tierC_b5_reverify_laundering.py` (valid root chain, all variations)

Same env pattern; script builds a **valid** chain (`_ACTOR` has a live direct assignment → narrow delegation to `_NARROW`), so the laundering guard is tested in isolation.

```
[A] root chain: d1.depth= 1  narrow eff= {'lab_result.read'}  holds A= True  holds B= False
[A1-exact-prior-unheld-B] DENIED DelegationDenied: Requested permissions exceed the actor's own holding authority rows_before=1 rows_after=1 EXPECT_DENIED=True MATCH=True
[A1-exact-prior-unheld-B] audit(action,outcome,reason)=[('delegation_denied', 'denied', 'permission_exceeds_holding_authority'), ('delegation_granted', 'success', None)]
[A2-mixed-A+B] DENIED DelegationDenied: Requested permissions exceed the actor's own holding authority rows_before=1 rows_after=1 EXPECT_DENIED=True MATCH=True
[A2-mixed-A+B] audit(...)=[... 'permission_exceeds_holding_authority' x2 ...]
[A3-legitimate-A] ALLOWED keys=['lab_result.read'] depth=2 rows_before=1 rows_after=2 EXPECT_DENIED=False MATCH=True
[B] h1.depth= 1  h2.depth= 2  OTHER eff= {'lab_result.read'}
[B1-depth2-unheld-B] DENIED DelegationDenied: Requested permissions exceed the actor's own holding authority rows_before=2 rows_after=2 EXPECT_DENIED=True MATCH=True
[B2-depth2-legit-A] ALLOWED keys=['lab_result.read'] depth=3 rows_before=2 rows_after=3 EXPECT_DENIED=False MATCH=True
[C1-scope-widen-FAC-OTHER] DENIED DelegationDenied: Delegated scope exceeds the actor's holding scope rows_before=0 rows_after=0 EXPECT_DENIED=True MATCH=True
[C1-scope-widen-FAC-OTHER] audit(...)=[('delegation_denied', 'denied', 'scope_exceeds_authority')]
[C2-scope-allowed-FAC-ALLOWED] ALLOWED keys=['lab_result.read'] depth=1 ... MATCH=True
[D1-direct-holder-full-catalog] ALLOWED keys=['lab_result.read', 'lab_result.export'] depth=1 ... MATCH=True
[D] delegate eff= {'lab_result.read', 'lab_result.export'}
FAILED_CASES: []
PROBE_VERDICT: ALL_EXPECTATIONS_MET
EXIT_CODE=0
```

**Observed vs expected:** each escalation attempt was denied with no new `niam_delegations` row and an explicit deny audit; legitimate direct-holder full-catalog and narrow/multi-hop grants still succeeded. Expected behaviour matched exactly. **No false-deny of valid chains.**

### 3.3 Code inspection (no trust in tests alone)

- `delegation_service.py:187-208` — requested keys must be a subset of the **active role catalog**; unknown keys audited as `permission_not_in_role`.
- `delegation_service.py:210-246` — `held_keys` derives from canonical records: depth 0 → whole active catalog; depth ≥1 → `holder.permission_keys ∩ allowed_keys`. Exceeded keys → `DelegationDenied`, audited `permission_exceeds_holding_authority`. This is the exact determinative guard; it does not read any caller claim.
- `delegation_service.py:248-268` — scope containment and depth cap with separate audited denials.
- `delegation_service.py:270-302` — only the canonical `NiamDelegation` is written; grant audited via canonical `AuditService`.

**Finding 1 confirmation: REMEDIATED / `INDEPENDENTLY VERIFIED`.**

---

## 4. Finding 2 — integration gap: HTTP and OpenAPI re-test

Probe `/tmp/opencode/tierC_b5_reverify_integration.py` — uses the **real** `app.main.app` (not a stand-in) for OpenAPI and HTTP, with only auth/db dependencies overridden to disposable SQLite and a synthetic NIAM actor.

```
[LEDGER] before any HTTP: {'niam_delegations': 0, 'delegations': 0}
[CHECK] OpenAPI /niam/delegations: PASS
[CHECK] OpenAPI /niam/delegations/{delegation_id}/revoke: PASS
[CHECK] OpenAPI /authz/delegations retained: PASS
[HTTP] POST /niam/delegations status= 201 body= {"id":"46EC4006...","delegator_account_id":"ACT...001","delegate_account_id":"ACT...002","role_id":"ROLE...0001","organization_id":"ORG...0001","permission_keys":["lab_result.read"],"depth":1,"status":"active",...}
[CHECK] canonical POST returns 201: PASS
[CHECK] niam_delegations row written: PASS
[EFFECTIVE] delegate after grant: {'lab_result.read'}
[CHECK] effective_permissions changed by HTTP grant: PASS
[HTTP] GET /niam/delegations status= 200
[CHECK] canonical GET returns 200: PASS
[LEDGER] immediately before legacy calls: {'niam_delegations': 1, 'delegations': 0}
[HTTP] POST /authz/delegations status= 410 detail= {"code":"HTTP_ERROR","message":"Legacy /authz/delegations is disabled: it wrote an ungoverned delegation table that canonical authorization never reads. Use the canonical account-based /niam/delegatio...
[HTTP] GET /authz/delegations status= 410 detail= ...same...
[HTTP] DELETE /authz/delegations/1 status= 410 detail= ...same...
[CHECK] legacy POST /authz/delegations is 410: PASS
[CHECK] legacy GET /authz/delegations is 410: PASS
[CHECK] legacy DELETE /authz/delegations/1 is 410: PASS
[LEDGER] after legacy calls: {'niam_delegations': 1, 'delegations': 0}
[CHECK] legacy calls wrote NO row to either table: PASS
[HTTP] POST revoke status= 200 body= {"id":"46EC4006...",...}
[CHECK] canonical revoke returns 200: PASS
[CHECK] row status revoked: PASS actual=revoked
[EFFECTIVE] delegate after revoke: set()
[CHECK] revoke removed authority: PASS
[STATIC] DelegationService references:  (app/services/authorization_service.py:888 class only; app/identity/api/delegations.py:25,77,127 canonical only)
[CHECK] no route imports legacy DelegationService: PASS
FAILED_CASES: []
PROBE_VERDICT: ALL_EXPECTATIONS_MET
EXIT_CODE=0
```

Additional static checks (exact commands):

```
cd backend && grep -rn 'DelegationService' --include='*.py' app/
# app/services/authorization_service.py:888:class DelegationService:   (definition only)
# app/identity/services/delegation_service.py:68:class DelegationService:
# app/identity/api/delegations.py:25,77,127  (canonical imports/uses)
# => zero route/DI references to the legacy service

cd backend && grep -rn 'NiamDelegation(' --include='*.py' . | grep -v '/tests/'
# app/identity/services/delegation_service.py:270   (the single production writer)
```

Other live `delegation`-named endpoints were examined and are **distinct domain surfaces**, not the authorization-delegation control: `app/governance/routes/governance_routes.py:138` writes `gov_delegations` (`app/governance/models/hierarchy.py:65`); `app/nursing/routes.py:1021` writes `nursing_delegations` (`app/nursing/models.py:392`). Neither writes `niam_delegations` or feeds `RolePermissionService.effective_permissions()`.

**Finding 2 confirmation: REMEDIATED / `INDEPENDENTLY VERIFIED`.**

---

## 5. Finding 3 — transitive revocation: enforcement-time re-test

Probe `/tmp/opencode/tierC_b5_reverify_transitive.py` (disposable SQLite; real `DelegationService` for creation, real `RolePermissionService` for enforcement via both `effective_permissions()` and `has_permission()`):

```
[SETUP] depth1= 1  depth2= 2
[CHECK] live depth-2 chain grants at enforcement: PASS
[CHECK] root role revoke -> intermediate and leaf denied: PASS
[CHECK] root role expiry -> leaf denied: PASS
[CHECK] intermediate delegation revoke -> leaf denied: PASS
[CHECK] parent expiry -> leaf denied: PASS
[CHECK] role deactivation -> leaf denied: PASS
[CHECK] permission deactivation -> leaf denied: PASS
[CHECK] forged cycle -> fail closed: PASS
[INFO] depth tamper blocked at DB CHECK constraint: IntegrityError
[CHECK] depth tamper > cap -> DB CHECK constraint fails closed: PASS IntegrityError
FAILED_CASES: []
PROBE_VERDICT: ALL_EXPECTATIONS_MET
EXIT_CODE=0
```

Exact prior transitive probe (`/tmp/opencode/tierC_probe_b5_transitive.py`) against current code:

```
before: delegate has PERM A: True
after delegator's role revoked: delegate still has PERM A: False
delegation row status: active
EXIT_CODE=0
```

Code inspection: `authorization_service_v2.py:205-254::_delegation_chain_valid` walks `delegation → parent delegation → … → live direct RoleAssignment`, fails closed on cycle (`seen`), depth out of `[1,3]`, missing parent, missing/expired/revoked direct assignment; called from `effective_permissions()` at line 314 before any delegated key is unioned (line 332). `Role.status`, `RolePermission.status`, `Permission.status` and expiry are re-checked at enforcement time (lines 282-284, 318-328).

**Finding 3 confirmation: REMEDIATED / `INDEPENDENTLY VERIFIED`.**

---

## 6. Novel adversarial probes (beyond the three assigned)

### Novel probe 1 — enforcement-time key attenuation with a directly forged delegation row

- **Location:** `/tmp/opencode/tierC_b5_reverify_novel1.py`; targets `authorization_service_v2.py:312-333` (`effective_permissions` delegated-key union).
- **Steps:** (1) build a valid chain where `_NARROW` legitimately holds only `lab_result.read`; (2) insert, by direct SQLAlchemy `session.add(NiamDelegation(...))` — i.e. **outside** `DelegationService.delegate_role` — a depth-2 active delegation from `_NARROW` to `_DELEGATE` whose `permission_keys=[lab_result.export]`; (3) query `effective_permissions(_DELEGATE)`.
- **Expected (strict invariant):** unheld key refused because the parent only carries `lab_result.read`.
- **Observed:** `DELEGATE effective_permissions = {'lab_result.export'}`; unheld key **granted**; `VERDICT: FAIL_OPEN_AT_ENFORCEMENT`; `EXIT_CODE=1` (probe's own assertion).
- **Assessment:** `effective_permissions()` re-validates the chain's *liveness* (finding 3) and each key's presence in the *role catalog*, but does **not** re-validate that each hop's `permission_keys` are a subset of its parent's keys. This is a genuine **defense-in-depth gap at the enforcement boundary**.
- **Why it does not block these three findings (explicit trust-boundary reasoning):** repository-wide search confirms `app/identity/services/delegation_service.py:270` is the **only production writer** of `NiamDelegation`; no route, migration, seed, or script constructs one. Producing the forged row requires write access to the canonical authorization table itself — at which point an attacker can equally write `niam_role_permissions`, `niam_role_assignments`, or `niam_permissions` and needs no delegation bug. No API caller or narrow-delegation holder can create this state. It is therefore **not a real API-reachable bypass** of findings 1–3; it is recorded as a **residual hardening gap** with recommended follow-up: carry/attest the parent's key set in the chain walk and intersect at enforcement.

### Novel probe 2 — cross-tenant / cross-catalog laundering via the canonical API

- **Location:** `/tmp/opencode/tierC_b5_reverify_novel2.py`; exercises `app/identity/api/delegations.py` with real router + real service.
- **Steps:** actor holds role R in ORG1 only; attempt (1) grant into ORG2, (2) grant another role's catalog key `patient_record.export`, (3) self-delegation, (4) unknown key, (5) delegation-based holder granting cross-org.
- **Observed vs expected:**

```
[N2.1] delegate into ORG2 where actor holds nothing: 403 {"detail":"Actor does not hold the delegated canonical role"}
[N2.2] delegate other role's catalog key: 403 {"detail":"Actor does not hold the delegated canonical role"}
[N2.3] self-delegation via canonical API: 403 {"detail":"Self-delegation is not allowed"}
[N2.4] unknown key: 403 {"detail":"Requested permissions are not part of the canonical role"}
[N2.5] unheld scope dimension: 201 ... (holder direct assignment is org-wide facility=None, so scope is contained — by design)
[CHECK] delegation-based holder cannot grant cross-org: PASS DelegationDenied: Actor does not hold the delegated canonical role
[AUDIT] denial reasons: ['no_holding_authority', 'no_holding_authority', 'self_delegation', 'permission_not_in_role', 'no_holding_authority']
[CHECK] all denials audited: PASS
FAILED_CASES: []
PROBE_VERDICT: ALL_EXPECTATIONS_MET
EXIT_CODE=0
```

- **Result:** every cross-tenant/cross-catalog/self/unknown-key attempt failed closed and was audited with the correct machine reason. No bypass.

---

## 7. Lint / diff / invariants (exact commands and exit codes)

### 7.1 Ruff — changed B5 scopes

```
cd backend && <pinned python> -m ruff check app/identity/services/delegation_service.py app/identity/api/delegations.py app/identity/api/router.py app/identity/services/authorization_service_v2.py app/routes/authorization.py tests/unit/test_b5_security_regressions.py tests/unit/test_b5_migration_drift_regression.py
```
```
All checks passed!
RUFF_CHANGED_SCOPE_EXIT=0
```

### 7.2 Ruff — including the legacy service (baseline comparison)

```
cd backend && <pinned python> -m ruff check ... app/services/authorization_service.py
```
```
SIM102 Use a single `if` statement instead of nested `if` statements
   --> app/services/authorization_service.py:284:9
Found 1 error.
RUFF_EXIT=1
```

This is **pre-existing at HEAD**: running Ruff against `git show HEAD:backend/app/services/authorization_service.py` reports the same `SIM102` at line 284 (plus an `I001` import-order issue that the working tree has already fixed). `app/services/authorization_service.py` is **not modified** by the B5 fix (`git status` shows no `M` for it). This is not a regression of the reviewed change.

### 7.3 `git diff --check`

```
cd /home/samertts/workspace/projects/gula-integration && git diff --check
```
```
(no output)
GIT_DIFF_CHECK_EXIT=0
```

### 7.4 Protected MD5s, HEAD, staged renames, no commit

```
md5sum GOVERNANCE/FINAL_DECISION.md GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md
```
```
effdfeaf10234678d83b2668c4489552  GOVERNANCE/FINAL_DECISION.md
1a02c01563c93b07a7cdb92c0462bf36  GOVERNANCE/IDENTITY_REMEDIATION/MPI_FINAL_INDEPENDENT_AUDIT.md
ea3969d09aaf7b0b28a065838b44a594  GOVERNANCE/IDENTITY_REMEDIATION/MPI_INDEPENDENT_AUDIT_FINDINGS.md
```
All three match the values pinned in `GOVERNANCE/NATIONAL_INTEGRATION/01_PHASE_A_BASELINE.md` §3 / `status_registry.json`.

```
git rev-parse HEAD
2206654dc713ea2de8c564a3207dfe05fde23549

git diff --cached --name-status | grep -c '^R100'
20
```
The same 20 staged R100 renames (workflow-runtime archive) were present before and after; none was changed or unstaged. No commit, push, PR, merge, deploy, or branch ref change was performed. No operational DB, Redis, real patient data, or external network was touched. All probe scripts and their captures live only under `/tmp/opencode/`. The only repository file written by this engagement is this report.

---

## 8. Final statement

- Findings **1, 2, and 3** from the prior Team C Tier B report §4/§6 are each **confirmed remediated** and awarded **`INDEPENDENTLY VERIFIED`** in engineering scope. Overall B5: **`INDEPENDENTLY VERIFIED`**.
- Zero real API-reachable bypasses were found after the adversarial attempts in §3–§6.
- One residual defense-in-depth gap (§6 novel probe 1) is documented with a concrete reproduction and a recommended follow-up; it requires out-of-band write access to the canonical delegation table and does not bypass any of the three remediated findings.
- **No `PRODUCTION READY` verdict is awarded.** B1/B2/B3 and prior residual items 1/2/3/6, plus owner/production/legal/clinical gates, are **out of scope** and explicitly not claimed.
