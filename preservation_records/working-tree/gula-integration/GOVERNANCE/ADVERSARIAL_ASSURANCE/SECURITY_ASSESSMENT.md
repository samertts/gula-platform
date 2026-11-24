# Team A Independent Adversarial Security Assessment — GULA Integration

**Program:** GULA Extreme Adversarial Audit & Remediation Program  
**Team:** Team A (independent adversarial auditor)  
**Lane:** SECURITY (+ security-relevant deployment state)  
**Date:** 2026-11-18  
**Repository:** `gula-integration`  
**Branch:** `integration/gula-unification-v1`  
**HEAD reviewed:** `2206654dc713ea2de8c564a3207dfe05fde23549`  
**Sibling repository:** `gula-platform` @ `f478676b6fc375338648dde46fbf076c015a3f91` (read-only; no files changed)

---

## 0. Authority and constraints observed

- No source file, git index/history, config, database, or sibling repository was modified.
- No git add/commit/push/merge was performed.
- No network calls, database connections, or exploitation/runtime probes were performed.
- No secrets or real patient data were accessed or generated.
- Owner-gated decisions were preserved unchanged: **HOLD**, **MPI REJECT**, **MP-001**, **ODR-001**, **ODR-002**, **ODR-003**, **ODR-004**, **D-020**, **D-021**, **ADR-A**, **ADR-B**, **ADR-C**, **ADR-D**, **ADR-E**, **ADR-F**, **ADR-G**, **ADR-H**, **ADR-I**, **ADR-J**, **AUD-02**, **AUD-07**, **AUD-16**.
- No `INDEPENDENTLY VERIFIED` or `PRODUCTION READY` status is awarded. Team C owns that authority.
- Finding lifecycle states use the required Team A value `DISCOVERED`. Control-state statements use only the permitted vocabulary: `IMPLEMENTED`, `TESTED`, `INTEGRATED`, `INDEPENDENTLY VERIFIED`, `PRODUCTION READY`, `BLOCKED`, `NOT IMPLEMENTED`.
- The disclosed **NR-011 FK test co-collection failure** is not re-reported.

---

## 1. Executive verdict

**Security verdict: NOT CERTIFIED. Release decision: HOLD preserved.**

Nine security findings are recorded: **3 CRITICAL**, **6 HIGH**, **0 MEDIUM**, **0 LOW**. The three most material security findings are:

1. **AUD-SEC-001** — NIAM governance/trust/lifecycle/federation/certificate control planes are mounted with authentication-only dependencies.
2. **AUD-SEC-002** — JWTs carry no account-type discriminator, and identity resolution queries `LabUser` before `User`, enabling cross-table identity substitution.
3. **AUD-SEC-003** — Privileged login checks only MFA *enrollment* and issues full access/refresh tokens without an MFA challenge.

Existing owner evidence already records the same release posture: `GOVERNANCE/FINAL_DECISION.md:13` states **HOLD — do not release to production**; `:27` records that S-01…S-13 changes are uncommitted and unreviewed; `:45-47` records authorization coverage as **REMEDIATED (uncommitted, unreviewed)**, security certification as **NOT CERTIFIED**, and release candidate as **HOLD**. `GOVERNANCE/SECURITY_COVERAGE_MATRIX.md:69` likewise states **Security verdict: NOT CERTIFIED**.

---

## 2. Scope and method

Reviewed surfaces (static read-only):

| Surface | Files / evidence |
|---|---|
| Login, MFA, logout, token issuance | `backend/app/routes/login.py`, `backend/app/routes/mfa.py`, `backend/app/security/mfa_service.py` |
| Authentication / identity resolution | `backend/app/security/auth.py`, `backend/app/security/dependencies.py`, `backend/app/identity/security.py` |
| NIAM router mounting and access policy | `backend/app/identity/api/router.py`, `backend/app/identity/api/access.py`, `backend/app/identity/api/workspaces.py` |
| NIAM control planes | `backend/app/identity/{governance,trust,lifecycle,federation,certificates,adaptive_auth,professional_registry,admin,compliance}/routes.py` |
| Clinical/PHI routes and services | `backend/app/routes/patients.py`, `backend/app/services/patient_service.py`, `backend/app/models/patient.py` |
| Consent and audit | `backend/app/security/consent_dep.py`, `backend/app/services/mpi/api.py`, `backend/app/services/audit_service.py` |
| Health Core authorization | `backend/app/health_core/authorization/guard.py` and package scan |
| Interoperability evidence surface | `backend/app/interoperability/fhir_http/security.py` (reviewed; not counted as live because no factory mount was found) |
| Route wiring / deployment state | `backend/app/factory.py`, `.github/workflows/frontend-pwa.yml`, read-only `git status`/`git diff` |
| Governance evidence | `GOVERNANCE/SECURITY_COVERAGE_MATRIX.md`, `GOVERNANCE/FINAL_DECISION.md`, `SECURITY_REMEDIATION_REPORT.md` |

Method: static source inspection, read-only `grep`, read-only `git status`/`git diff`, and STRIDE/DREAD-style risk scoring. Reproduction steps below are deliberately static/falsification-oriented; no live request, database query, or exploitation was performed.

---

## 3. Observed control status (not a certification)

| Control area | Observed status | Basis |
|---|---|---|
| Privileged authentication/MFA | `BLOCKED` | AUD-SEC-003 |
| JWT identity binding | `BLOCKED` | AUD-SEC-002 |
| NIAM registry read/write authorization | `IMPLEMENTED` for persons/sessions/devices only | `backend/app/identity/api/access.py:59-75`; AUD-SEC-001 covers omitted routers |
| NIAM control-plane authorization | `NOT IMPLEMENTED` on affected routers | `backend/app/identity/api/router.py:54-63` |
| Bearer logout revocation | `BLOCKED` | AUD-SEC-004 |
| Patient PHI authorization | `BLOCKED` | AUD-SEC-005 and privacy lane |
| Adaptive-auth control-plane authorization | `NOT IMPLEMENTED` | AUD-SEC-006 |
| NIAM async actor lock enforcement | `BLOCKED` | AUD-SEC-007 |
| Health Core authorization facade runtime wiring | `NOT IMPLEMENTED` | AUD-SEC-008 |
| Release evidence integrity | `BLOCKED` | AUD-SEC-009 |
| Audit append/hash-chain code path | `IMPLEMENTED` (code presence only; no verification claimed) | `backend/app/services/audit_service.py:184-234` |

---

## 4. Findings

### AUD-SEC-001 — NIAM governance/trust/lifecycle/federation/certificate control planes accept any authenticated actor

- **Severity:** CRITICAL
- **Likelihood:** HIGH
- **DREAD:** Damage 9, Reproducibility 9, Exploitability 8, Affected users 9, Discoverability 7 → **8.4**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/identity/api/router.py:34` — `_AUTH_REQUIRED = [Depends(get_current_niam_actor)]`.
- `backend/app/identity/api/router.py:54-63` — governance, trust, lifecycle, federation, certificates, notifications, adaptive-auth, admin, and compliance routers are mounted with `_AUTH_REQUIRED` or no authorization dependency.
- `backend/app/identity/api/access.py:59-75` — a stricter reader/writer policy exists but is applied only to persons/sessions/devices at `router.py:41,45,52`.
- `backend/app/identity/governance/routes.py:374-392` — `POST /niam/governance/suspensions` accepts caller-supplied `suspended_by` and suspends an identity with no permission dependency in the handler.
- `backend/app/identity/governance/routes.py:494-522` — `POST /niam/governance/registry/certify` accepts caller-supplied `verified_by`, `digital_signature`, and certification fields with no permission dependency.
- `backend/app/identity/trust/routes.py:26-51` — creates trust frameworks with no permission dependency.
- `backend/app/identity/trust/routes.py:87-109` — updates/activates frameworks with no permission dependency.
- `backend/app/identity/trust/routes.py:214-241` — creates trust anchors with caller-supplied key/certificate fields.
- `backend/app/identity/trust/routes.py:301-326` — creates federation trust relationships with no permission dependency.
- `backend/app/identity/lifecycle/routes.py:71-79` — approves enterprise registration with caller-supplied `approved_by`.
- `backend/app/identity/federation/routes.py:18-38` — registers identity providers with caller-supplied encrypted secret material.
- `backend/app/identity/certificates/routes.py:16-45,48-70` — issues, revokes, and rotates certificates with no permission dependency.
- `backend/app/identity/professional_registry/routes.py:71-87` — verifies a professional entry using `verified_by=Depends(get_actor_identity_id)`; `backend/app/identity/security.py:104-119` shows this dependency derives only the actor identity, not a role/authority check.
- `backend/app/identity/professional_registry/services.py:97-126` — `verify()` is the documented “ONLY path that activates privileges”; `services.py:152-175` is the privilege gate.

**Safe reproduction / falsification (static)**
1. Start at `router.py:54-63` and follow any listed router (for example governance).
2. Confirm the only inherited dependency is `get_current_niam_actor` (`router.py:34`).
3. Confirm the target handler has no `AuthorizationDecisionService`, role dependency, or ownership check (governance route excerpts above).
4. Confirm the mutation changes identity/trust/certificate/privilege state.
5. **Falsification:** produce code showing these routers carry an authorization dependency equivalent to `access.py:59-75` or `admin/routes.py:30-50`, and a regression test proving a non-privileged authenticated actor receives 403 for these mutations.

**Root cause:** Authentication was treated as authorization for high-impact identity control planes. Where actor identity is derived from the token, it is used as an audit label rather than as an input to an authorization decision.

**Impact:** Any authenticated NIAM identity can suspend identities, certify/federate trust, register identity providers, issue/revoke certificates, and self-verify professional privilege entries. This is a national identity-platform privilege escalation with downstream PHI and clinical authorization consequences.

**Remediation:** Mount each affected router with explicit permission dependencies (e.g. `require_niam_registry_writer`-style policy extended with a real NIAM operator role), enforce authorization inside each mutating handler using `AuthorizationDecisionService`, derive `*_by` fields from the authenticated principal, and add negative tests for non-privileged actors.

**Alternatives:** (a) Consolidate all NIAM control planes behind one gateway authorization dependency; (b) disable the routers until role catalog and tests land; (c) keep router-level auth and add service-layer guardrails. Preferred: (a) plus handler-level checks for defense in depth.

---

### AUD-SEC-002 — JWT payload has no account-type discriminator; `LabUser` is resolved before `User`

- **Severity:** CRITICAL
- **Likelihood:** HIGH
- **DREAD:** Damage 9, Reproducibility 8, Exploitability 8, Affected users 9, Discoverability 7 → **8.2**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/security/auth.py:41-48` — `_TokenUser` and `JWTClaims` contain no account-kind field.
- `backend/app/security/auth.py:79-85` — `build_token_payload()` emits only `user_id`, `lab_id`, `role`, and `perm_ver`.
- `backend/app/routes/login.py:186-193` — citizen/non-LabUser tokens are built with `"user_id": citizen.id`, `"lab_id": None`, `"role": "citizen"`, `"perm_ver": 1`.
- `backend/app/security/dependencies.py:77-84` — `get_current_user()` queries `LabUser` by `user_id` first, then `User`; it never checks the token’s `lab_id` or `role` against the selected account type.
- `backend/app/security/dependencies.py:93-98` — `perm_version` is evaluated against whichever object was selected, not the claimed account kind.

**Safe reproduction / falsification (static)**
1. Observe that `User.id` and `LabUser.id` are independent primary-key spaces.
2. Construct the code path: a token from `login.py:186-193` carries `user_id=N` and `lab_id=None`.
3. Follow it to `dependencies.py:77`: the first lookup is `LabUser.id == N`; if such a row exists and is active, that lab account is returned regardless of the token’s `lab_id=None`/`role="citizen"`.
4. **Falsification:** show that token payloads carry a signed account-kind claim and that `get_current_user()` rejects a mismatch between that claim, `lab_id`, and the selected ORM class.

**Root cause:** Token identity is a bare integer without a domain qualifier, and identity resolution uses table precedence instead of an explicit account-kind contract.

**Impact:** A token minted for one account family can resolve to a different account family when IDs collide. That can confer laboratory roles, lab scope, and permissions to a caller authenticated as a citizen/non-lab user; conversely it can misattribute audit and permission-version checks.

**Remediation:** Add a signed `account_kind` (`lab_user`, `user`, `service_account`, etc.) claim at token issuance, validate it in every dependency, and filter the lookup by the claimed kind plus `lab_id`/workspace where applicable. Reject tokens whose claims disagree with the resolved principal.

**Alternatives:** (a) Use globally unique ULIDs/UUIDs across account tables and still validate `account_kind`; (b) namespace the `user_id` claim (`lab:<id>` / `user:<id>`). Preferred: (a)+(b) if token format versioning is acceptable; otherwise (a) alone with strict dependency checks.

---

### AUD-SEC-003 — Privileged login checks MFA enrollment only and issues full tokens without a challenge

- **Severity:** CRITICAL
- **Likelihood:** HIGH
- **DREAD:** Damage 9, Reproducibility 8, Exploitability 8, Affected users 8, Discoverability 8 → **8.2**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/routes/login.py:141-160` — for `master_admin`, `ministry_admin`, `province_admin`, login only checks `mfa.has_mfa_enabled(user.id)`.
- `backend/app/routes/login.py:197-198` — full access and refresh tokens are created immediately after that check.
- `backend/app/routes/login.py:211-244` — tokens and session response are returned to the caller.
- `backend/app/security/mfa_service.py:48-60` — `setup_totp()` creates an active `MFADevice` at enrollment time.
- `backend/app/security/mfa_service.py:255-262` — `has_mfa_enabled()` only checks for an active device row; it does not verify a challenge or session.
- `backend/app/routes/mfa.py:55-75,107-131` — TOTP/WebAuthn verification endpoints depend on `get_current_user`, i.e. they require an already authenticated session.

**Safe reproduction / falsification (static)**
1. Trace a privileged-role login through `login.py:141-160`.
2. Confirm the only MFA condition is “an active device row exists.”
3. Confirm `login.py:197-198` issues full tokens without consulting `verify_totp`, `complete_webauthn_authentication`, or `verify_mfa_session`.
4. Confirm the challenge endpoints (`mfa.py:55-131`) cannot run before a token exists.
5. **Falsification:** show a pre-token challenge state (short-lived MFA session) that must be verified before `create_token()` at `login.py:197`, with a regression test rejecting password-only privileged login.

**Root cause:** MFA is modeled as an enrollment attribute rather than as a second authentication step in the login state machine.

**Impact:** Password compromise, credential reuse, or phishing against a privileged account yields a fully authenticated session even when MFA is enrolled. The control creates a false assurance of MFA enforcement.

**Remediation:** Split privileged login into two stages: credential verification → short-lived, scoped MFA challenge token → MFA verification → full access/refresh token issuance. Enforce in `login.py` and add negative tests for privileged password-only login and challenge replay/expiry.

**Alternatives:** (a) Use WebAuthn as a primary passwordless factor for privileged roles; (b) require step-up MFA at every privileged API call via `AuthorizationDecisionService` sensitivity rules. Preferred: staged login plus step-up for critical actions.

---

### AUD-SEC-004 — Logout revokes only cookie tokens; Bearer clients retain usable sessions

- **Severity:** HIGH
- **Likelihood:** MEDIUM
- **DREAD:** Damage 7, Reproducibility 8, Exploitability 7, Affected users 5, Discoverability 7 → **6.8**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/security/dependencies.py:27-35` — `_extract_token()` accepts `Authorization: Bearer` first, then `access_token` cookie.
- `backend/app/routes/login.py:257-267` — logout reads the access token only from `request.cookies.get("access_token")`.
- `backend/app/routes/login.py:269-278` — refresh-token revocation also reads only the cookie.
- `backend/app/routes/login.py:280-295` — DB `perm_version` bump depends on `user_id`, which remains `None` for Bearer-only logout.
- `backend/app/routes/login.py:297-299` — only cookies are deleted from the response.

**Safe reproduction / falsification (static)**
1. Compare `dependencies.py:32-34` with `login.py:258` and `login.py:270`.
2. Observe that a Bearer-only client presents no `access_token`/`refresh_token` cookie.
3. Therefore no JTI is blacklisted and no `user_id` is derived, so neither revocation layer runs.
4. **Falsification:** show logout extracting the same token via `_extract_token()` (or a shared helper) and a test proving a previously issued Bearer token receives 401 after logout.

**Root cause:** Token extraction logic is duplicated and inconsistent between request authentication and logout.

**Impact:** Logout is ineffective for native/mobile/Bearer clients. Stolen or retained tokens remain valid until expiry, defeating session termination, incident response, and user-controlled logout.

**Remediation:** Reuse `_extract_token(credentials, request)` in logout, accept both Bearer and cookie access/refresh tokens, blacklist both JTIs, derive `user_id` from either source, and always bump `perm_version` when an identity is known. Add tests for Bearer-only, cookie-only, and mixed clients.

**Alternatives:** (a) Server-side session store with explicit session IDs; (b) short access-token TTL plus refresh-token rotation. Preferred: shared extraction plus both revocation layers; short TTL is defense in depth.

---

### AUD-SEC-005 — Patient PHI routes require authentication but no per-action authorization or consent

- **Severity:** HIGH
- **Likelihood:** HIGH
- **DREAD:** Damage 8, Reproducibility 9, Exploitability 8, Affected users 8, Discoverability 8 → **8.2**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/routes/patients.py:159-175` — `GET /patients` depends only on `get_current_user`.
- `backend/app/routes/patients.py:178-207` — `POST /patients` depends only on `get_current_user`; `force_create` is passed through unguarded.
- `backend/app/routes/patients.py:210-226`, `:229-245`, `:248-257`, `:260-286` — family, children, read-by-id, and update routes depend only on `get_current_user`.
- `backend/app/security/dependencies.py:37-41` — `get_current_user()` authenticates and performs lab-active/perm-version checks but does not authorize a patient action.
- `backend/app/capabilities/fhir_interoperability/routes.py:34-39` — a stricter pattern exists (`require_institutional_permission("lab:read"/"lab:manage")`) but is not used by `/patients`.
- `backend/app/security/consent_dep.py:74-195` — consent dependency exists; see privacy lane for deployment gap.

**Safe reproduction / falsification (static)**
1. Inspect the route decorators/signatures listed above.
2. Confirm no `require_institutional_permission`, `require_niam_*`, `require_consent`, or `AuthorizationDecisionService` dependency appears on any `/patients` handler.
3. Confirm the returned DTO includes name, phone, birth date, gender, email, health ID, and guardian ID (`backend/app/services/patient_service.py:53-68`).
4. **Falsification:** show router-level or handler-level authorization enforcing `patient:read`/`patient:manage` and scope/consent checks, with negative tests for citizen/low-privilege actors.

**Root cause:** `get_current_user` is used as a substitute for authorization; no per-resource policy is attached to the legacy patient surface.

**Impact:** Any authenticated account that can obtain a token may enumerate, read, create, or update patient PHI within the lab scope implied by the token, without role, purpose, or consent checks.

**Remediation:** Add explicit `patient:read`, `patient:manage`, and `patient:create` dependencies to every route; bind reads/writes to institutional workspace/facility scope; apply consent where cross-lab/citizen data is involved; add negative authorization tests.

**Alternatives:** (a) Wrap the legacy patient router in a policy-enforcing facade; (b) migrate to the clinical gateway/Health Core authorized facade once it is actually wired (see AUD-SEC-008). Preferred: (a) now, (b) as target state.

---

### AUD-SEC-006 — Adaptive-auth policy/MFA/session control plane is mounted authentication-only

- **Severity:** HIGH
- **Likelihood:** HIGH
- **DREAD:** Damage 8, Reproducibility 9, Exploitability 8, Affected users 9, Discoverability 7 → **8.2**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/identity/api/router.py:61` — adaptive-auth router mounted with `_AUTH_REQUIRED` only.
- `backend/app/identity/adaptive_auth/routes.py:35-43` — risk history for any `account_id` is readable.
- `backend/app/identity/adaptive_auth/routes.py:46-68` — MFA challenge creation/verification accepts caller-supplied `account_id`/`mfa_id` with no owner or permission check.
- `backend/app/identity/adaptive_auth/routes.py:90-143` — risk policies can be created and arbitrarily updated.
- `backend/app/identity/adaptive_auth/routes.py:165-213` — session policies can be created and updated.
- `backend/app/identity/adaptive_auth/routes.py:261-280` — session policy enforcement and expiry checks are callable without authorization.

**Safe reproduction / falsification (static)**
1. Follow `router.py:61` to `adaptive_auth/routes.py`.
2. Confirm no role/permission dependency in the listed handlers.
3. Confirm parameters include arbitrary `account_id`, policy thresholds, MFA IDs, and session control actions.
4. **Falsification:** show explicit authorization plus actor/account binding and tests denying non-security administrators.

**Root cause:** Security-control configuration endpoints were treated as ordinary authenticated APIs.

**Impact:** Any authenticated identity can weaken or manipulate risk thresholds, disable/suspend session policies via updates, forge MFA challenges for other accounts, terminate sessions, and read risk history. This undermines compensating controls relied on elsewhere.

**Remediation:** Require a dedicated security-admin permission for all adaptive-auth mutations and reads; bind `account_id` to the actor unless the actor is a clearly authorized operator; audit every policy/MFA/session mutation; add negative tests.

**Alternatives:** (a) Move these endpoints under the NIAM admin router where `_require_permission` exists (`admin/routes.py:30-50`); (b) make them internal-only and remove from the public API. Preferred: (a) with dedicated permission keys.

---

### AUD-SEC-007 — Async NIAM actor dependency omits the account-lock check present in the sync dependency

- **Severity:** HIGH
- **Likelihood:** MEDIUM
- **DREAD:** Damage 7, Reproducibility 8, Exploitability 7, Affected users 7, Discoverability 7 → **7.2**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/identity/api/workspaces.py:37-62` — sync `get_current_niam_actor_sync()` filters on `Account.is_locked.is_(False)` at `:54`.
- `backend/app/identity/api/workspaces.py:65-89` — async `get_current_niam_actor()` filters status and `is_active` at `:80-81` but omits `is_locked`.
- `backend/app/identity/security.py:84-92` — generic NIAM identity resolver checks `is_locked and locked_until`, but the async workspace actor path does not call this logic.
- `backend/app/identity/api/router.py:34` — all `_AUTH_REQUIRED` control-plane routers use the async dependency.

**Safe reproduction / falsification (static)**
1. Diff the two queries at `workspaces.py:47-58` and `:75-85`.
2. Confirm `Account.is_locked.is_(False)` appears only in the sync query.
3. Confirm the async dependency is the one used by `router.py:34`.
4. **Falsification:** show the async query includes the same lock predicate (or an equivalent fail-closed check) and a test proving a locked account receives 401/403 on an async NIAM route.

**Root cause:** Duplicated authentication logic drifted between sync and async implementations.

**Impact:** A locked NIAM account can continue to access all async NIAM routes, including the control planes in AUD-SEC-001 and AUD-SEC-006, until its token expires or is separately revoked.

**Remediation:** Consolidate both dependencies on one canonical predicate builder; always require `is_active`, non-inactive status, `is_locked == false`, valid session, and JTI revocation check. Add parity tests.

**Alternatives:** (a) Add the missing predicate directly; (b) replace both with a shared account/session validator. Preferred: (b), with (a) as immediate hotfix.

---

### AUD-SEC-008 — Health Core deny-by-default authorization facade is not wired into runtime routes

- **Severity:** HIGH
- **Likelihood:** MEDIUM
- **DREAD:** Damage 8, Reproducibility 8, Exploitability 6, Affected users 7, Discoverability 5 → **6.8**
- **Owner-gated:** false
- **Status:** DISCOVERED

**Evidence**
- `backend/app/health_core/authorization/guard.py:1-11` — module docstring explicitly states: “Nothing in this module is wired into a route or `factory.py`.”
- `backend/app/health_core/authorization/guard.py:78-79` — `AuthorizedHealthCore` is described as the authorization gate callers must use.
- `backend/app/health_core/authorization/__init__.py:27-28,54` — the facade is exported.
- `backend/app/factory.py:640-679` — representative route mounting block includes many routers but no `AuthorizedHealthCore` integration.
- Read-only package scan found `AuthorizedHealthCore` references only inside the `health_core.authorization` package/tests, not in application route wiring.

**Safe reproduction / falsification (static)**
1. Read `guard.py:3-4`, which self-declares no route/factory wiring.
2. Search application route modules and `factory.py` for `AuthorizedHealthCore`; no runtime consumer was found.
3. **Falsification:** show a factory/route composition that constructs `AuthorizedHealthCore` and routes clinical/lab reads and mutations exclusively through it, with tests proving unwrapped services are unreachable from HTTP.

**Root cause:** A strong authorization component was delivered as a library/facade without a composition-root integration step.

**Impact:** The deny-by-default policy engine, scope index, and audited authorization decisions are not applied to HTTP traffic. Any claimed clinical authorization guarantee based on this facade is `NOT IMPLEMENTED` at runtime.

**Remediation:** Wire the facade into the clinical gateway composition root; replace direct synthetic/unwrapped service calls with `AuthorizedHealthCore`; add route-level integration tests and architecture tests preventing bypass imports.

**Alternatives:** (a) Keep facade dormant and explicitly exclude it from security claims; (b) expose it through a thin FastAPI dependency wrapper; (c) migrate routes to the canonical clinical gateway. Preferred: (c) with (b) as transition.

---

### AUD-SEC-009 — Security-relevant fixes and evidence remain uncommitted; release evidence is internally inconsistent

- **Severity:** HIGH
- **Likelihood:** HIGH
- **DREAD:** Damage 8, Reproducibility 9, Exploitability 6, Affected users 9, Discoverability 8 → **8.0**
- **Owner-gated:** true
- **Status:** DISCOVERED

**Evidence**
- `GOVERNANCE/FINAL_DECISION.md:13` — **HOLD — do not release to production**.
- `GOVERNANCE/FINAL_DECISION.md:20-27` — remediation for S-01…S-13 and S-13/kill-switch fixes are described as implemented **in the working tree** and **uncommitted and not yet independently reviewed**.
- `GOVERNANCE/FINAL_DECISION.md:45-47` — authorization coverage `REMEDIATED (uncommitted, unreviewed)`, security certification `NOT CERTIFIED`, release candidate `HOLD`.
- `SECURITY_REMEDIATION_REPORT.md:274` — `DEP-AUDIT-BACKEND → VERIFIED` is recorded in an uncommitted addendum.
- `SECURITY_REMEDIATION_REPORT.md:280` — the same addendum states it **does not certify production readiness or clinical safety** and the release remains **HOLD**.
- `.github/workflows/frontend-pwa.yml:82-85` — uncommitted change sets `VITE_API_BASE_URL` from origin-only to `https://api.gula-platform.org/api` with a gateway-path justification.
- Read-only `git status --short` at HEAD `2206654…` showed large modified/untracked security-relevant sets including `backend/app/config.py`, `backend/app/factory.py`, `backend/app/routes/login.py`, all `backend/app/health_core/**`, NIAM governance/trust/professional-registry code, dependency manifests, and governance reports.

**Safe reproduction / falsification (static)**
1. Run read-only `git status --short` and compare with `git rev-parse HEAD`.
2. Note that the controls claimed as remediated in `FINAL_DECISION.md:20-27` are not in HEAD.
3. Note the contradictory assurance signals at `SECURITY_REMEDIATION_REPORT.md:274` versus `:280`.
4. **Falsification:** provide a clean committed tree whose HEAD contains the cited fixes, with CI evidence, an updated decision record, and no contradictory `VERIFIED`/`HOLD` statements.

**Root cause:** Remediation evidence was written into a governance report before the corresponding code was committed and independently reviewed.

**Impact:** A release evaluator cannot reproduce the certified state from HEAD. Uncommitted changes can be lost, overwritten, or deployed selectively, and assurance claims cannot be tied to an immutable revision.

**Remediation:** Commit the complete reviewed change-set atomically, regenerate/re-run all gates against that commit, update decision records with the exact commit hash, and reconcile the `DEP-AUDIT-BACKEND` status language with the still-`HOLD` release decision. Owner approval is required before changing release status.

**Alternatives:** (a) Revert uncommitted security changes and reapply under review; (b) create a signed evidence bundle bound to the working tree. Preferred: (a) for release integrity; (b) only for interim internal testing, never as production certification.

---

## 5. Items reviewed but not counted as live findings

- `backend/app/interoperability/fhir_http/security.py:1-16,118-135` uses synthetic unsigned headers for authorization. This is explicitly a test/evidence surface, and no `include_router` mount was found in `factory.py`; it is therefore excluded from live-production findings. Do not count it as a compensating control.
- `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md` and owner-decision artifacts were treated as owner-gated evidence and left unchanged.
- NR-011 is intentionally not re-reported.

---

## 6. Handoff

All findings are `DISCOVERED`, not verified, not integrated-approved, and not production-ready. Team C must independently verify remediation before any status promotion. The release decision remains **HOLD**.
