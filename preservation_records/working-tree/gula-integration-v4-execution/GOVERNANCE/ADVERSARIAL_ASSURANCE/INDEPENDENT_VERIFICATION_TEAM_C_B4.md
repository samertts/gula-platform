# Independent Adversarial Verification — Team C — B4 Cross-Account Security Administration

**Verifier:** Team C — Independent, fresh-context adversarial verification engineer (no participation in B4 implementation)
**Repository:** `/home/samertts/workspace/projects/gula-integration`
**Branch:** `integration/gula-unification-v1`
**Work under review (uncommitted):**
- `backend/app/identity/adaptive_auth/b4_guard.py` (new)
- `backend/app/identity/adaptive_auth/routes.py` (modified/hardened)
- `backend/tests/unit/test_b4_cross_account_security.py` (new, 24 tests)

**Governing directive:** GULA-MASTER-AUTH-2026-11-19 §4 (exact model supplied to this verifier).
**Date:** 2026-11-19
**Interpreter:** `/home/samertts/workspace/projects/gula-platform/backend/.venv/bin/python` → Python 3.12.13, pytest 9.1.1.

---

## 1. Methodology

1. **Full-source review** of all three files under review, plus the transitive dependencies that determine whether the guard can actually be trusted:
   - `app/identity/api/workspaces.py` (`NiamActor`, `get_current_niam_actor`, `_active_niam_actor_predicates`)
   - `app/identity/api/router.py` (router mounting / control-plane dependencies)
   - `app/identity/api/access.py` (`require_niam_control_plane_authority`, `_CONTROL_PLANE_AUTHORITIES`)
   - `app/identity/services/audit_service.py` (`AuditService.record` — hash-chained immutable audit)
   - `app/identity/services/step_up_service.py` (`assert_fresh` / `verify` — consumed, not re-verified)
   - `app/identity/models/{account,authorization,audit,session}.py`, `app/identity/adaptive_auth/{models,services}.py`
2. **Line-by-line trace of every account-scoped route**: confirm the authenticated actor — never the client hint — is the authorization subject, and that the server-resolved `Account.id` is what reaches every downstream service/query.
3. **Adversarial bypass hunting** against the directive's eight invariants (client-id trust, cross-account step-up skips, cross-account MFA, weak control-plane roles, expired/revoked assignments, session/account substitution, unaudited actions, evidence replay).
4. **Execution of the implementer's suite, the mandated regressions, ruff, and OpenAPI/router introspection.**
5. **Independent probe suite authored from scratch** (10 probes) placed **only** in `/tmp/opencode/team_c_b4_probes.py` — no repository file, existing report, git index, or sibling repository was modified. No migration was run against any non-disposable database (all probes use in-memory SQLite).
6. **Audit-field persistence verification** against the directive's eight mandated fields.

---

## 2. Exact commands and exit codes

All commands run from `/home/samertts/workspace/projects/gula-integration/backend` with prefix
`ENV=test RUNTIME_MODE=test PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=.:..` unless noted.

| # | Command (abridged) | Result | Exit |
|---|---|---|---|
| 1 | `python -m pytest tests/unit/test_b4_cross_account_security.py -q` | **24 passed**, 1 warning (Starlette/httpx deprecation), 49.05s | **0** |
| 2 | `python -m ruff check app/identity/adaptive_auth/ tests/unit/test_b4_cross_account_security.py` | `All checks passed!` | **0** |
| 3 | `python -m pytest tests/unit/test_niam_step_up.py tests/unit/test_aud_sec_001_control_plane_authorization.py -q` | **51 passed** (37 step-up + 14 AUD-SEC-001), 1 warning, 217.56s | **0** |
| 4 | inline introspection: `from app.main import app; len(app.openapi()["paths"])` + router dependency walk | `OPENAPI_PATH_COUNT=1815`; `ALL_MOUNTED_WITH_CONTROL_PLANE=True`; 14 adaptive-auth paths | **0** |
| 5 | `python -m pytest /tmp/opencode/team_c_b4_probes.py -q -s` | **10 passed**, ~3s | **0** |

Post-verification `git status --porcelain` on the three review targets is unchanged from the pre-verification state (`M routes.py`, `?? b4_guard.py`, `?? test_b4_cross_account_security.py`), confirming no source mutation by this review.

---

## 3. What I tried to break (and what happened)

### 3.1 Client identifier cannot become the authorization subject
- **Traced all 9 account/session/MFA-parameter routes** (`evaluate_risk`, `get_risk_history`, `create_mfa_challenge`, `verify_mfa_challenge`, `list_travel_events`, `get_active_session_count`, `detect_new_device`, `enforce_session_policy`, `is_session_valid`). Every one declares `actor: NiamActor = Depends(get_current_niam_actor)` and calls exactly one B4 resolver (`authorize_account_operation` / `resolve_own_mfa_challenge` / `resolve_session_target`). Downstream services receive `target.id` (a server-fetched row), never the raw `account_id` / `mfa_id` / `session_id` query parameter.
- **Probe 1** (independent structural enumeration of every function in `routes.py` whose signature contains a sensitive identifier) confirmed all 9 are guarded and that no raw client identifier is forwarded (`account_id=account_id` etc. absent). **No bypass.**
- `get_current_niam_actor` derives the actor strictly from the bearer token's `account_uuid` + `jti`, joined against `niam_accounts`/`niam_sessions` with fail-closed active predicates (`status active`, `is_active`, `is_locked IS FALSE`, session active). A client cannot inject an account id into this path.

### 3.2 Cross-account step-up skip
- `authorize_account_operation` places `StepUpService.assert_fresh(actor, purpose=...)` **after** the role check and **before** the fail-closed audit write / return. There is no cross-account branch that returns without it. Self-service returns earlier only when the target row equals the server-resolved actor account. **No bypass.**
- **Probe 4** attempted to reuse step-up evidence produced in admin session A from admin session B (different JTI). Denied with `fresh_step_up_required` — `assert_fresh` binds evidence to account + session + session JTI. **No cross-session replay.**
- **Probe 5** revoked the step-up event (`is_active=False`) after creation; the subsequent cross-account attempt was denied. **No revoked-evidence bypass.**
- (Step-up internals — 300s window, 299/300/301 boundary, config bounds — were explicitly out of scope and were not re-verified; the mandated `test_niam_step_up.py` regression still passed 37/37.)

### 3.3 Cross-account MFA challenge/verification
- `create_mfa_challenge` passes `mfa_self_only=True`; `authorize_account_operation` denies any target that is not the actor's own account **even with an elevated role and fresh step-up**.
- `verify_mfa_challenge` calls `resolve_own_mfa_challenge`, which loads the challenge by `mfa_id` and requires `challenge.account_id == actor_account.id`, denying (and auditing) otherwise. An admin cannot target another account's challenge. **No bypass.**

### 3.4 Weak control-plane role escalation
- `B4_CROSS_ACCOUNT_ROLES = {"master_admin", "security_administrator"}` is a strict subset of the broader AUD-SEC-001 set (which also contains `ministry_admin`, `organization_administrator`, `compliance_officer`). A weak role passes the router-level guard but is rejected by B4's own `_has_cross_account_role`.
- **Probe 2** granted `ministry_admin` and `organization_administrator` (with fresh step-up) and attempted cross-account: both denied with `cross_account_role_denied`. The implementer's test covers `compliance_officer`. **No bypass.**

### 3.5 Expired / revoked / suspended assignments and actors
- `_has_cross_account_role` requires `RoleAssignment.status == active`, `revoked_at IS NULL`, `expires_at IS NULL OR > now`, `Role.status == active`, and narrow `role_key`. `_load_actor_state` re-reads account + session and rejects non-active/locked accounts, revoked/expired/substituted sessions. The implementer's parametrized test covers suspended/revoked/expired/disabled variants; **Probe 3** additionally forged a *valid session id with a tampered JTI* → `session_substitution`. **No bypass.**

### 3.6 Session/account substitution and IDOR
- **Probe 7** requested `session-valid/{session_id}` semantics via `resolve_session_target` using another account's session id; the owning account was derived from the DB row and the unprivileged actor was denied `cross_account_role_denied`. The client cannot nominate the owning account. **No IDOR.**

### 3.7 Unaudited cross-account action / audit failure
- `_audit_decision(required=True)` is invoked on the successful cross-account allow **before** the target is returned to the route/service. **Probe 6** monkeypatched `AuditService.record` to raise; the cross-account authorization aborted with the propagated error — i.e., fail-closed, no unaudited success. Denials for privilege escalation and step-up failure are also audited (best-effort). **No unaudited cross-account success.**
- **Probe 9** confirmed all eight directive-mandated fields are persisted on the allow entry (see §5).

### 3.8 Competing authorization engine / duplicate Phase 1 protections
- `b4_guard.py` introduces **no** new role catalog, permission engine, MFA engine, or audit store. `B4_CROSS_ACCOUNT_ROLES` is a filter over canonical `niam_roles`; authority comes from `NiamActor` + canonical RBAC + `StepUpService` + `AuditService`. Consistent with ADR_AUD_ARCH_003 (single authorization authority). **No competing engine found.**

---

## 4. Findings

**No REAL bypass of the B4 model was found.** The following are residual risks / hardening observations, none of which constitutes a verified bypass of the directive's account-scoped cross-account model.

| ID | Severity | Finding | Notes / recommendation |
|---|---|---|---|
| R-1 | **MEDIUM (residual, out of B4's hardened set)** | Global adaptive-auth policy routes `create_risk_policy`, `update_risk_policy`, `create_session_policy`, `update_session_policy`, `check_session_expiry` have **no actor dependency and no B4 guard** (Probe 8 output). They are protected only by the router-level AUD-SEC-001 control-plane guard, whose `_CONTROL_PLANE_AUTHORITIES` includes `ministry_admin`, `organization_administrator`, `compliance_officer`. | These mutate global session/security policy (MFA requirements, timeouts, IP/geo restrictions, risk thresholds) affecting all accounts. If "cross-account security administration" is read to include global policy mutation, a weak control-plane role could act outside the narrow master/security-admin model. These routes are not account-scoped and were not part of B4's mandate; recommend gating them behind `B4_CROSS_ACCOUNT_ROLES` in a follow-up decision. |
| R-2 | **LOW (residual)** | `_has_cross_account_role` does not constrain `RoleAssignment.scope_type` / `organization_id` (e.g. an org/facility/workspace-scoped `master_admin` assignment grants cross-account authority over any account). | `Account` has no direct organization column, so scope enforcement requires membership resolution. Directive did not explicitly require scope binding; recommend enforcing `scope_type == platform` or target-in-scope checks. |
| R-3 | **LOW (residual)** | Certain denial paths raise `B4Denied` without an audit entry: `target_not_found`, `session_not_found`, `actor_ineligible`, `session_substitution`, `session_revoked`, `session_expired`, `cross_account_not_allowed`. | Privilege-escalation and step-up-failure denials **are** audited. The unaudited paths are pre-authorization/actor-state failures; recommend auditing ID-probe denials (`target_not_found`, `session_not_found`) for detection. |
| R-4 | **LOW (residual, step-up internals out of scope)** | `assert_fresh(actor, purpose=purpose)` uses `purpose` only in audit metadata; step-up evidence is not cryptographically bound to a specific purpose, so evidence obtained for one purpose can satisfy another within the 300s window. | Step-up was explicitly verified separately and is out of scope for this engagement; recorded for completeness/confused-deputy defense in depth. |

---

## 5. Audit-field persistence evidence

`test_probe_9_all_directive_audit_fields_persisted` performed a real successful cross-account authorization against in-memory SQLite and inspected the persisted `IdentityAuditEntry` (`AUTHZ_ALLOW_SENSITIVE`):

```
AUDIT_FIELD_PRESENCE= {'actor': True, 'target': True, 'purpose': True,
                       'action': True, 'result': True, 'timestamp': True,
                       'session': True, 'evidence': True}
```

Mapping to the directive: **actor** = `actor_id` (+`actor_type`), **target** = `target_id` (+`target_type`), **purpose** = `metadata.purpose`, **action** = `action` value + `metadata.operation`, **result** = `outcome`, **timestamp** = `occurred_at`, **session** = `session_id` + `metadata.session_jti`, **evidence** = `metadata.evidence_event_id`. The entry is hash-chained (`entry_hash`/`previous_hash`) through the canonical `AuditService`. All eight fields are genuinely persisted.

---

## 6. Probe evidence (authored independently; `/tmp/opencode/team_c_b4_probes.py`)

```
SENSITIVE_ROUTES_GUARDED= ['create_mfa_challenge', 'detect_new_device', 'enforce_session_policy',
 'evaluate_risk', 'get_active_session_count', 'get_risk_history', 'is_session_valid',
 'list_travel_events', 'verify_mfa_challenge']
GLOBAL_POLICY_ROUTES(name,actor,b4guard)= [('create_risk_policy', False, False),
 ('update_risk_policy', False, False), ('create_session_policy', False, False),
 ('update_session_policy', False, False), ('check_session_expiry', False, False)]
AUDIT_FIELD_PRESENCE= {'actor': True, 'target': True, 'purpose': True,
 'action': True, 'result': True, 'timestamp': True, 'session': True, 'evidence': True}
10 passed in 2.98s   (exit 0)
```

Probe list: (1) structural completeness of sensitive-param routes; (2) weak roles `ministry_admin`/`organization_administrator` denied at runtime; (3) session JTI substitution denied; (4) step-up evidence session-bound; (5) revoked step-up evidence denied; (6) audit write failure fails closed; (7) session IDOR denied; (8) global policy routes lack B4 guard (residual-risk evidence); (9) full audit-field persistence; (10 — parametrized) both weak roles. All passed; **no probe exposed a real bypass.**

---

## 7. Verdict

**Status: INDEPENDENTLY VERIFIED — at ENGINEERING SCOPE.**

B4's account-scoped cross-account security administration model is correctly implemented and enforces all eight owner-directive invariants: self-only MFA, narrow active RBAC roles, server-side subject resolution, fresh session-bound step-up, ineligible-actor rejection, complete fail-closed auditing, IDOR/substitution/replay/escalation prevention, and reuse of canonical NIAM primitives with no competing authorization engine. The implementer's 24 tests, the 51 mandated regressions, ruff, the unchanged OpenAPI path count (1815), the mounted router-level AUD-SEC-001 control-plane guard, and 10 fresh independent probes all pass. No real bypass was found. Residual risks R-1…R-4 are recorded above and do not invalidate this engineering-scope verdict.

**PRODUCTION READY is explicitly NOT awarded.** Production readiness requires operational, clinical, and legal evidence outside this scope — including deployment/runtime authorization configuration, PKI/token issuance controls, monitoring/alerting for the audited denial paths, data-protection and clinical-safety sign-off, and validation against a real NIAM/RBAC dataset. This verdict addresses engineering correctness only.
