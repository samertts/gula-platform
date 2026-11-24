# SECURITY & IDENTITY REMEDIATION PLAN — PROGRAM-GULA-PARALLEL-001 (AGENT 04)

**Platform:** GULA National Healthcare Platform | Iraq  
**Wave:** A output for a future, approval-gated Wave C  
**Agent:** A04 — Security & Identity Auditor  
**Date:** 2026-11-19  
**Status:** **PLAN ONLY — NO REMEDIATION AUTHORIZED**

Companion evidence report: `docs/parallel-program/security/SECURITY_AUDIT.md` (all file:line evidence is recorded there).

---

## 0. Authority and non-negotiable constraints

| Constraint | Effect on this plan |
|---|---|
| A04 is a **reviewer** in Wave C (`AGENT_ASSIGNMENTS.md:64-66`) | A04 does **not** implement any item below. |
| Wave C is **BLOCKED** until the master register is approved, ownership is confirmed, and each file is verified clean (`PROGRAM_CONTROL.md:147-152,205`; `AGENT_ASSIGNMENTS.md:56-62`) | Every code item below is `BLOCKED` today, not `FIXED`. |
| No auth/RBAC/API/session/identity behavior change without independent approval (`PROGRAM_CONTROL.md:211-216`; `FILE_OWNERSHIP_MATRIX.md:76-77`) | All identity, OAuth2, password, rate-limit and audit changes require explicit approval. |
| 378 paths of pre-existing user work are protected | All files in `SECURITY_AUDIT.md §5` are **DO NOT REMOVE / DO NOT REPLACE**. Fixes must be surgical and in place, if ever authorized. |
| No secret values may be reproduced | A04-010/A04-011 reference only path:line and token shape; no value is copied into this plan or the audit. |
| No source/config edits, tests, services, migrations or git state changes by A04 | This document and `SECURITY_AUDIT.md` are the only A04 writes. |

**Arabic status (حالة):** هذه خطة تصحيح فقط. لم يتم تعديل أي ملف مصدر أو إعداد. أي تغيير في الهوية أو الصلاحيات أو واجهات البرمجة يحتاج موافقة مستقلة.

---

## 1. Decisions required before any remediation (scope requests)

| ID | Request | Blocks | Decision owner | If denied / deferred |
|---|---|---|---|---|
| SR-A04-01 | Confirm whether `require_fresh_niam_step_up` is intended to be enforced, and on the **exact** sensitive route list | A04-001 | Orchestrator + security/IAM owner | Keep control inert; document as accepted risk; do **not** wire blindly |
| SR-A04-02 | Assign regression tests for NIAM logout ownership, session-bound identity auth, OAuth2 registration authorization, step-up and password policy | Wave D acceptance for A04-001…A04-009 | Orchestrator → A07/A09 | No change may be called complete without tests |
| SR-A04-03 | Ask A08 to verify CI pinning claims and to evaluate anchor-failure observability | A04-013 and prior-report assurance | Orchestrator → A08 | Keep A04-013 as P3 accepted risk |
| SR-A04-04 | Confirm no Wave C agent may touch `SECURITY_AUDIT.md §5` protected files until the user explicitly releases them | All code items | Orchestrator + file owner/user | Status remains `BLOCKED — PROTECTED FILE` |

Additional decision needed for A04-007: frontend/client contract owner must approve moving the NIAM refresh token out of the query string.  
Additional decision needed for A04-009: migration owner must approve any reset-token storage change; no migration may be executed in this phase.

---

## 2. Prioritized queue

All rows are currently **PLAN_ONLY / BLOCKED**. Severity order follows the audit: P1 → P2 → P3.

| Order | ID | Severity | Title (short) | Approval gate | Current status |
|---:|---|---|---|---|---|
| 1 | A04-003 | P1 | Terminated-session NIAM tokens still accepted | Independent IAM/auth approval + protected-file release | BLOCKED |
| 2 | A04-002 | P1 | Unauthenticated NIAM logout terminates arbitrary sessions | Independent auth/session approval + protected-file release | BLOCKED |
| 3 | A04-001 | P1 | Step-up dependency defined but unused | SR-A04-01 route inventory + IAM approval | BLOCKED |
| 4 | A04-004 | P2 | Self-service OAuth2 client registration | API authorization approval | BLOCKED |
| 5 | A04-005 | P2 | OAuth2 introspect/revoke unauthenticated | API authentication approval | BLOCKED |
| 6 | A04-006 | P2 | Password policy bypass on reset/change | Credential-policy approval | BLOCKED |
| 7 | A04-007 | P2 | NIAM refresh token in query string | API contract + frontend approval | BLOCKED |
| 8 | A04-008 | P2 | Professional national-scope match flaw | Authorization logic approval | BLOCKED |
| 9 | A04-009 | P2 | Reset-token full-table bcrypt scan | Credential flow + migration approval | BLOCKED |
| 10 | A04-010 | P3 | No committed secret; local `.env` key | No code approval; operational only | INFORMATIONAL |
| 11 | A04-011 | P3 | Weak default DB password in maintenance script | User release for script file | BLOCKED — PROTECTED USER WORK |
| 12 | A04-012 | P3 | Proxy headers trusted from any private peer | Backend change approval or infrastructure approval | BLOCKED |
| 13 | A04-013 | P3 | Audit anchor failures logged only | Backend/observability approval | BLOCKED |
| 14 | A04-014 | P3 | NIAM `perm_ver` revocation gap | IAM/token design decision | BLOCKED |

**Sequencing note:** A04-003 and A04-002 should be designed as one identity-session hardening change set. A04-001 must not be wired until session binding and logout ownership are corrected, because step-up evidence is session-bound.

---

## 3. Detailed approval-gated remediation plans

### A04-003 — Terminated-session tokens still accepted on identity-registry routes

- **Severity:** P1
- **Title:** `get_current_identity` does not bind identity tokens to an active `UserSession`.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-003`; primary: `backend/app/identity/security.py:70-93`, `backend/app/identity/api/workspaces.py:37-57,81-99`, `backend/app/identity/services/authentication_service.py:139-146`.
- **Affected components:** `/niam/persons`, `/niam/sessions`, `/niam/devices`, all consumers of `get_current_identity`.
- **Root cause:** Two auth dependencies for the same token family enforce different invariants; the canonical actor path checks active session + JTI, the identity path checks account state only.
- **Safe-fix possible?** Yes — reuse `_active_niam_actor_predicates()` instead of inventing a new check.
- **Approval required?** **YES** — identity authentication behavior on protected user work.

**Plan (after approval):**
1. In `backend/app/identity/security.py`, align the identity-domain branch with the active-session predicate used in `backend/app/identity/api/workspaces.py`: require a `UserSession` row matching the signed `token_jti` with `is_active=True` and no termination marker.
2. In `backend/app/identity/services/authentication_service.py` / `backend/app/identity/repositories/session_repository.py`, blacklist the access-token JTI when `logout()` / `terminate_session()` runs, or return the JTI from the service so the caller can blacklist it. Do not remove existing DB-flag termination.
3. Preserve account status, lock and active checks. Do not broaden access to lab/citizen token domains.
4. Tests (A07/A09): logout → previously issued access token gets `401` on `/niam/persons`; active session → `200`; terminated-but-blacklisted → `401`; wrong account kind → rejected.

**Acceptance:** No PII registry route accepts a token from a terminated session. Prior successful responses for legitimate active sessions remain unchanged.

---

### A04-002 — Unauthenticated NIAM logout terminates arbitrary sessions

- **Severity:** P1
- **Title:** `POST /niam/auth/logout` accepts any `session_uuid` from any anonymous caller.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-002`; primary: `backend/app/identity/api/auth.py:69-76`, `backend/app/identity/services/authentication_service.py:139-146`, `backend/app/identity/repositories/session_repository.py:41-53`.
- **Affected components:** All NIAM sessions; step-up evidence bound to terminated sessions.
- **Root cause:** Identifier-only service call exposed as an unauthenticated route; no actor or ownership parameter exists.
- **Safe-fix possible?** Yes — require the authenticated actor and terminate only that actor's session.
- **Approval required?** **YES** — authentication/session behavior change on a protected, untracked file.

**Plan (after approval):**
1. Add `Depends(get_current_niam_actor)` to `POST /niam/auth/logout` in `backend/app/identity/api/auth.py`.
2. Preferred contract: ignore caller-supplied `session_uuid` for normal actors and terminate `actor.session.id` only. If an explicit UUID must remain for administrative use, require (a) an approved privileged role and (b) `session.account_id == actor.account.id` ownership verification before termination.
3. Reuse existing rate limiting for logout; key it on the trusted client IP from A04-012 once that is corrected, not on a raw spoofable header.
4. Combine with A04-003 JTI blacklisting so logout has immediate effect on access tokens.
5. Tests (A07/A09): anonymous logout → `401`; actor terminating another account's session → `403/404`; self logout → success; repeated abuse → rate-limited.

**Acceptance:** Anonymous callers cannot terminate any session. Cross-account termination is impossible without an explicitly approved admin capability.

---

### A04-001 — Step-up dependency defined but enforced on no route

- **Severity:** P1
- **Title:** `require_fresh_niam_step_up` and its verification endpoint exist, but no sensitive operation consumes the signal.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-001`; primary: `backend/app/identity/api/step_up.py:21`, `backend/app/identity/api/auth.py:94-121`, `backend/app/identity/services/step_up_service.py:237-293`, `backend/app/identity/api/router.py:38-74`; repo-wide grep found only the definition.
- **Affected components:** NIAM trust/governance/lifecycle/federation/certificate/notification/adaptive-auth/professional-registry sensitive operations.
- **Root cause:** Final integration step was never performed; the control is inert.
- **Safe-fix possible?** Yes, but only after a route inventory decision — **no global blind wiring**.
- **Approval required?** **YES** — IAM behavior change plus SR-A04-01.

**Plan (after SR-A04-01 and approval):**
1. Orchestrator/IAM owner signs an explicit list of "sensitive cross-account operations". Read-only control-plane routes stay unstepped unless explicitly listed.
2. Attach `Depends(require_fresh_niam_step_up)` only to the approved routes in `backend/app/identity/api/router.py` / the relevant `identity/api/*.py` modules.
3. Confirm the dependency calls `StepUpService.assert_fresh()` and binds evidence to the same account/session as `get_current_niam_actor`.
4. Failure behaviour: `403` with no side effects; do not fall back to role-only success.
5. Tests (A07/A09): fresh evidence → allowed; expired/missing evidence → `403`; evidence from another account/session → `403`; non-sensitive route → unchanged.

**Acceptance:** Every approved sensitive route denies privileged actions without fresh step-up. No unapproved route gains a new auth requirement.

---

### A04-004 — Self-service OAuth2 client registration

- **Severity:** P2
- **Title:** Any authenticated principal can register a client with arbitrary redirect URIs, scopes and `token_endpoint_auth_method="none"`.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-004`; primary: `backend/app/routes/oauth2.py:74-110,273-274`, `backend/app/security/oauth2_provider.py:272`.
- **Affected components:** OAuth2 authorize/token lifecycle; downstream API consumers.
- **Root cause:** Client onboarding has no trust tiering or approval workflow.
- **Safe-fix possible?** Yes — operator role or approval state, plus validation.
- **Approval required?** **YES** — API authorization behavior change.

**Plan (after approval):**
1. Restrict `POST /oauth2/register` to an approved operator/admin permission, or add an `is_approved` state checked in `/authorize` and `/token`.
2. Validate redirect URIs: HTTPS-only outside local development; no wildcards; exact registered values; loopback exceptions explicit and documented.
3. Validate requested scopes against an allowlist per client tier; reject scope escalation.
4. Reject `token_endpoint_auth_method="none"` for confidential clients; if public clients are required, define an explicit profile (PKCE + no client credentials) and document it.
5. Inventory existing registered clients before enforcement so legitimate integrations are not broken.
6. Tests (A07/A09): ordinary user registration → `403`; operator registration → approved state; wildcard redirect → rejected; `"none"` confidential client → rejected.

**Acceptance:** New clients require approved trust tiering. No existing legitimate client silently loses token issuance.

---

### A04-005 — OAuth2 introspection and revocation are unauthenticated

- **Severity:** P2
- **Title:** `/oauth2/introspect` and `/oauth2/revoke` accept anonymous requests.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-005`; primary: `backend/app/routes/oauth2.py:194-219,222-236` versus `181`.
- **Affected components:** OAuth2 token lifecycle; RFC 8412 / RFC 7009 compliance.
- **Root cause:** Client authentication was applied to `/token` only.
- **Safe-fix possible?** Yes — reuse `_authenticate_client()`.
- **Approval required?** **YES** — API authentication behavior change.

**Plan (after approval):**
1. Apply `_authenticate_client()` (or an equivalent RFC 8412-protected dependency) to both endpoints in `backend/app/routes/oauth2.py`.
2. For introspection, return only fields the authenticated client is entitled to see; do not expand disclosure beyond `active`, `client_id`, `scope`, `token_type`, `exp` and a non-sensitive subject reference unless approved.
3. For revocation, verify the token belongs to the authenticated client before marking revoked.
4. Publish the contract change to OAuth2 consumers; provide a transition window if approved.
5. Tests (A07/A09): anonymous → `401`; wrong client → `401/403`; owner client → allowed.

**Acceptance:** Anonymous introspection/revocation is impossible; legitimate clients retain lifecycle operations.

---

### A04-006 — Password policy bypass on reset/change

- **Severity:** P2
- **Title:** `_validate_password()` is enforced at registration only.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-006`; primary: `backend/app/routes/register.py:24-36`, `backend/app/routes/password_reset.py:57-82,85-100`.
- **Affected components:** `LabUser` credential strength; reset/change flows.
- **Root cause:** Policy implemented locally in the registration module instead of a shared validator.
- **Safe-fix possible?** Yes — move/reuse, do not duplicate.
- **Approval required?** **YES** — credential-policy behavior change.

**Plan (after approval):**
1. Make the existing ≥12-character + upper/lower/digit/special rule a shared helper (reuse `shared/auth/passwords.py` or an in-repo validator module; **no new dependency**).
2. Call it before `hash_password()` in both `reset_password()` and `change_password()` in `backend/app/routes/password_reset.py`, and in any other password-setting service found by A07.
3. Return the same validation error shape/registration behaviour; do not silently accept weak values.
4. Tests (A07/A09): weak reset → rejected; weak change → rejected; compliant password on all three paths → accepted.

**Acceptance:** No path can set a LabUser password that registration would reject.

---

### A04-007 — NIAM refresh token in query string

- **Severity:** P2
- **Title:** `POST /niam/auth/refresh` binds `refresh_token` as a query parameter.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-007`; primary: `backend/app/identity/api/auth.py:55-66`.
- **Affected components:** NIAM refresh-token confidentiality; proxy/access logs; browser history/referrers.
- **Root cause:** Bare FastAPI scalar defaults to query binding; no explicit body/cookie model.
- **Safe-fix possible?** Yes — Pydantic body model or httpOnly cookie.
- **Approval required?** **YES** — API contract change; frontend/client coordination required.

**Plan (after approval):**
1. Change `backend/app/identity/api/auth.py` to accept the refresh token through a Pydantic body model or an httpOnly cookie, matching the step-up endpoint pattern at `auth.py:79-84`.
2. Explicitly reject query-string tokens (e.g. `422`) during the transition so the insecure path does not remain silently supported.
3. Confirm audit/log redaction does not record refresh tokens; check access logs at the ingress (A08).
4. Coordinate client deployment; do not deploy backend-only contract change.
5. Tests (A07/A09): query token → rejected; body/cookie token → success; token never appears in test log captures.

**Acceptance:** Refresh tokens are absent from URLs and logs; approved clients continue refreshing.

---

### A04-008 — Professional authorization national-scope match flaw

- **Severity:** P2
- **Title:** `scope_matches()` returns True when the requested scope is national, regardless of the authorization's scope.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-008`; primary: `backend/app/identity/professional_registry/authorization.py:63-74,297,334`.
- **Affected components:** `backend/app/identity/professional_registry/**` (local-only protected user work).
- **Root cause:** Likely duplicated/inverted branch: a facility/district authorization satisfies a national request.
- **Safe-fix possible?** Yes — remove or invert the `requested_type == national` branch; currently latent (no external call sites found).
- **Approval required?** **YES** — authorization logic change; do not edit this tree in Wave C without release.

**Plan (after approval):**
1. Correct `scope_matches()` so a national request requires an authorization whose `scope_type` is national; preserve the rule that a national authorization may satisfy narrower requests if that is the intended design.
2. Re-check call sites (`is_authorized()`, `matching_authorization()`) before and after; if new callers appear, reassess severity.
3. Add a 2×2 unit matrix: national/national, national/facility, facility/national, facility/facility, including `scope_id` equality cases.
4. Fix in place; do not remove or replace the protected local-only tree.

**Acceptance:** Facility/district credentials cannot satisfy a national-scope check. Existing correct matches remain correct.

---

### A04-009 — Reset-token verification scans all active tokens with bcrypt

- **Severity:** P2
- **Title:** Every reset attempt runs bcrypt against every active reset token.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-009`; primary: `backend/app/routes/password_reset.py:64-68`, `shared/auth/passwords.py:13-16`.
- **Affected components:** Password-reset endpoint; worker CPU availability.
- **Root cause:** Bcrypt-hashed tokens cannot be indexed for value lookup.
- **Safe-fix possible?** Yes — keyed/indexable digest lookup, or bounded candidate set plus per-token rate limiting.
- **Approval required?** **YES** — credential-flow change and possible migration.

**Plan (after approval):**
1. Preferred design: store an HMAC-SHA-256 digest using a server-side key for lookup (indexed column) and compare in constant time; keep bcrypt only for any legacy rows during a reviewed transition.
2. If a schema change is required, prepare the migration for review only. **Do not execute it in Wave C.** Obtain migration owner approval.
3. Interim mitigation if schema change is deferred: strict per-token/per-IP rate limit and bounded candidate query; document residual O(N) cost.
4. Never log raw reset tokens; ensure `canonical_audit.py` redaction remains intact.
5. Tests (A07/A09): valid token → one candidate; invalid token → bounded work; expired token → rejected; concurrent attempts remain within CPU budget.

**Acceptance:** Reset verification cost is independent of the number of outstanding reset requests (or explicitly accepted with interim limits).

---

### A04-010 — No committed live secrets (informational)

- **Severity:** P3
- **Title:** Full-tree scan found no live credential in tracked source/config; one provider-shaped key exists only in gitignored local `.env`.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-010`; 145 candidates triaged; `.env` untracked/ignored (`.gitignore:2:.env`). **Value intentionally not reproduced.**
- **Affected components:** Repository secret hygiene (positive result).
- **Root cause:** N/A — verified control, recorded for completeness.
- **Safe-fix possible?** N/A for repository code.
- **Approval required?** N/A for code; rotation is an operational decision.

**Plan:**
1. No repository edit. Do not copy `.env` values into reports, tickets or logs.
2. Operational owner: confirm the local key is development-only; rotate it if it was ever shared outside the workstation.
3. Optional hardening for A08: add/verify secret scanning in CI and a pre-commit hook using existing free tooling; no SaaS dependency.

**Acceptance:** No secret value is committed or reproduced; local ignored secret handling remains intact.

---

### A04-011 — Weak default database password in maintenance script

- **Severity:** P3
- **Title:** Static default DSN in `scripts/create_master_admin.py`; dev fallback DSNs contain defaults.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-011`; primary: `scripts/create_master_admin.py:41-44`, `backend/app/config.py:129,125-127,169-176,188-198`. **Value redacted.**
- **Affected components:** Maintenance tooling; local development.
- **Root cause:** Convenience default retained in operator script. Production config already fails closed.
- **Safe-fix possible?** Yes — require `DATABASE_URL` explicitly.
- **Approval required?** **NO** for IAM rules, but **YES** for user work release; do not edit without explicit user permission.

**Plan (after user release):**
1. Remove the static default DSN from `scripts/create_master_admin.py`; fail with a clear message if `DATABASE_URL` is absent.
2. Keep `backend/app/config.py` production fail-closed behaviour; make the dev fallback explicitly local-only and documented rather than silently reusable.
3. Do not introduce a secret store or paid dependency; read from the existing environment/secret mechanism.
4. Test: running the script without `DATABASE_URL` exits before any DB connection; with env set it behaves as before.

**Acceptance:** No operator script silently connects using a shipped credential.

---

### A04-012 — Reverse-proxy headers trusted from any private peer

- **Severity:** P3 (deployment-dependent)
- **Title:** `get_client_ip()` trusts `X-Real-IP` / `X-Forwarded-For` whenever the direct peer is RFC-1918.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-012`; primary: `backend/app/security/rate_limit.py:54-78,132-136,204-217`.
- **Affected components:** Rate limiting, audit IP attribution, IP blocking.
- **Root cause:** Trust boundary inferred from address class, not explicit proxy configuration.
- **Safe-fix possible?** Yes — ingress trust list plus application-side explicit trusted-proxy CIDRs.
- **Approval required?** **YES** for `backend/app/security/**` changes; infrastructure fix also needs orchestrator approval.

**Plan (after approval):**
1. Preferred first step: configure ingress to strip/overwrite forwarded headers from untrusted peers and forward only known values.
2. Application-side hardening in `backend/app/security/rate_limit.py`: use an explicit trusted-proxy CIDR configuration; walk `X-Forwarded-For` from the right and select the first untrusted address; fall back to the direct peer when all hops are trusted.
3. Validate header values; never use a raw client-supplied header as a security key without validation.
4. Tests (A07/A09): spoofed header from untrusted peer ignored; legitimate chain behind trusted proxy resolves correctly; rate-limit rotation no longer succeeds.

**Acceptance:** Rate-limit and audit IP values cannot be controlled by arbitrary private-network peers.

---

### A04-013 — Audit anchor write failures are logged only

- **Severity:** P3
- **Title:** Failed HMAC anchor checkpoint writes do not block or alert.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-013`; primary: `backend/app/services/audit_service.py:115-124,232-234,82-103,238-270`.
- **Affected components:** Tamper-evidence anchoring for `audit_logs`.
- **Root cause:** Checkpoint durability treated as best-effort; DB hash chain remains intact.
- **Safe-fix possible?** Yes — metric/alert and health exposure.
- **Approval required?** **YES** for backend changes; observability work may be assigned to A08 with approval.

**Plan (after approval):**
1. In `backend/app/services/audit_service.py`, keep request behaviour unchanged unless a fail-closed policy is explicitly approved; always emit a structured metric/event on `_write_anchor()` failure.
2. Surface `hmac_failures` / last successful anchor timestamp from `get_latest_anchor()` in the existing health/readiness mechanism.
3. Alert threshold agreed with operations (A08); no SaaS monitoring dependency.
4. Tests (A07/A09): simulated anchor failure increments metric and sets health degradation without losing the audit entry.

**Acceptance:** Sustained anchor failure is visible within the agreed alerting window; hash-chain verification still passes.

---

### A04-014 — NIAM `perm_ver` revocation gap

- **Severity:** P3
- **Title:** Identity-domain tokens carry no `perm_ver`; canonical permission-version revocation cannot apply to NIAM.
- **Evidence:** `SECURITY_AUDIT.md §2 / A04-014`; primary: `backend/app/identity/security.py:55-101`, `backend/app/identity/services/authentication_service.py:67-74`, `backend/app/security/dependencies.py:109-126`.
- **Affected components:** NIAM role-change revocation semantics.
- **Root cause:** Two token families with separate revocation models. This is a design gap, not a demonstrated bypass.
- **Safe-fix possible?** Yes — either extend the token model or document the authoritative model.
- **Approval required?** **YES** — IAM/token design decision.

**Plan (after decision):**
1. **Option A (minimal, preferred first):** Declare session state + JTI blacklist + account status as the authoritative NIAM revocation model; ensure A04-003 lands; document explicitly that `perm_ver` applies only to canonical lab/citizen tokens.
2. **Option B (full parity):** Add `perm_ver` to identity token payloads and enforce it in `get_current_identity` against the account's authoritative version. Requires token-schema change, rollout coordination and tests.
3. Do not assume canonical `perm_ver` protection covers NIAM until one option is approved and implemented.
4. Tests (A07/A09): Option A — role change plus session termination revokes access; Option B — stale `perm_ver` token rejected.

**Acceptance:** The chosen revocation model is documented, implemented consistently and covered by tests.

---

## 4. Reuse, free/open-source and self-hosted compliance

| Platform rule | Application to this plan |
|---|---|
| Free First / Zero Paid Dependency | No paid product, SaaS or commercial security tool is proposed. |
| Open Source First | Reuse existing in-repo Apache/MIT-style stack: FastAPI, Pydantic, SQLAlchemy, Redis, bcrypt/HMAC, existing test tooling. No new dependency is required for any fix above. |
| Self-Hosted First | All proposed controls stay in the existing self-hosted backend, database, Redis and ingress. |
| No Vendor Lock-In | No provider-specific claim, hosted identity service or proprietary token format is introduced. OIDC/JWKS remains fail-closed and unchanged. |
| Reuse Before Build | Reuse `get_current_niam_actor`, `_active_niam_actor_predicates()`, `SecurityStore`, `StepUpService.assert_fresh()`, `_authenticate_client()`, `_validate_password()` and existing audit redaction instead of creating parallel implementations. |
| Local AI First | Not relevant to this phase; no AI inference component is touched. |
| Free Security First | Continue using existing HMAC/JWT/bcrypt/constant-time primitives and Let's Encrypt/OpenSSL-style ingress controls already in the platform; no commercial security product introduced. |

---

## 5. Validation and acceptance plan (Wave D — not executed by A04)

| IDs | Verification to be assigned to A07/A09 or A08 |
|---|---|
| A04-003, A04-002, A04-001 | NIAM logout ownership tests; terminated-session token rejection on `/niam/persons`; step-up positive/negative and cross-account evidence tests |
| A04-004, A04-005 | OAuth2 registration authorization matrix; redirect/scope validation; anonymous introspect/revoke rejection; owner-client success |
| A04-006, A04-009 | Weak-password rejection on register/reset/change; bounded-cost reset-token tests; no token logging |
| A04-007 | Refresh token absent from query strings and logs; approved client contract works |
| A04-008 | 2×2 professional scope matrix; no facility→national match |
| A04-011 | Maintenance script fails closed without `DATABASE_URL` |
| A04-012 | Spoofed proxy-header tests; rate-limit key stability behind trusted proxy |
| A04-013 | Anchor failure metric/health degradation; hash-chain verification still passes |
| A04-014 | Chosen revocation model test; documentation updated |

Validation must use the project's existing gate commands discovered in `PROGRAM_CONTROL.md §5`; no new command or dependency is assumed. No test, migration, service or deployment was run by A04.

---

## 6. Change-control status labels

| Label | Meaning |
|---|---|
| `PLAN_ONLY` | This document records evidence and a proposed change only. |
| `BLOCKED` | Approval, clean-file verification or wave authorization is missing. |
| `BLOCKED — PROTECTED FILE` | Target is pre-existing user work / absent from `origin/main`; explicit user release required. |
| `APPROVED_PENDING_IMPLEMENTATION` | Orchestrator and required independent approvers have signed off; still not implemented. |
| `IMPLEMENTED_PENDING_VERIFICATION` | Wave D verification pending. Never use `FIXED` before verification. |

No item above has progressed beyond `PLAN_ONLY / BLOCKED`.

**Arabic summary (ملخص خطة التصحيح):** لا توجد إجراءات تصحيح مسموح بها الآن. أولوية العمل بعد الموافقة: ربط رموز NIAM بجلسة نشطة، ثم منع تسجيل الخروج دون مصادقة، ثم تفعيل التحقق المتقدم على المسارات الحساسة. جميع الملفات المحمية تبقى كما هي حتى إذن صريح. لم يتم العثور على تسريب سر في المستودع.
