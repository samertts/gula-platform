# Security Review Report

**Program:** GULA Stable v1.0.0 — Repository Unification
**Scope:** Unified backend (`backend/app`) as built on `integration/gula-unification-v1`, plus the frontend dependency surface.
**Branch:** `integration/gula-unification-v1` @ `2827c1ff` (all changes uncommitted)
**Date:** 2026-11-16
**Basis:** Static review **plus** runtime probes executed against the real app wiring.
**Verdict: NOT CERTIFIED.** Five findings block a production release; the remainder are hardening items.

> This document does **not** claim security certification. Per `GOVERNANCE/AI_AGENT_RULES.md`,
> certification requires human security review. It records the review that **found** the defects.
> Remediation for S-01…S-12 has since been implemented in the working tree and is **uncommitted,
> awaiting independent Program Director / human security review** (see §3.0 and
> `GOVERNANCE/EXECUTION_LEDGER.md` GULA-013/GULA-015). The report body below describes the
> **pre-remediation** state so the findings remain reproducible.
>
> **Update (same review cycle):** the independent post-remediation pass added **S-13**
> (self-service verification could activate a professional account — §3.1), hardened the S-06
> kill-switch fail-open residual (`app/core/kill_switch.py`, fail-closed in production/staging),
> and produced the per-endpoint evidence register `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md`
> (91 historical gaps → 0; 69 public-by-design endpoints, 11 categories, 0 unclassified;
> residuals R-01…R-11 tracked and open). **The verdict stays NOT CERTIFIED / HOLD.**

---

## 0. Key finding

The platform's **authentication layer is sound**; the **authorization layer is not uniformly applied**.

- 1 974 of 2 132 effective endpoints (92.6 %) carry an authentication dependency, and the in-body
  guards that a dependency-tree scanner cannot see were verified to be real (§4).
- But **91 endpoints have no guard at all** at review time, including anonymous *writes* to national
  governance, platform lifecycle, pilot gating and the NIAM identity store. *(All 91 are since
  remediated in the working tree — see §3.0; uncommitted, awaiting review.)*
- The control plane does require a token, but **never checks what the caller is allowed to do**: a
  `citizen`-role lab user can rewrite global configuration, poison the policy store, and deploy and
  approve a release under a body-supplied `master_admin` identity.

---

## 1. Method

Three independent layers, each producing evidence that can be re-run:

| Layer | What it answers | Artefact |
|---|---|---|
| **A. Route-surface walk** | Which endpoints have *any* auth dependency? | `/tmp/opencode/audit_auth_coverage.py` → `/tmp/opencode/auth_coverage.json` |
| **B. Static review** | For unguarded routes: is the guard in the handler body? | findings §3/§4, file references |
| **C. Runtime probes** | Does the defect actually reproduce? | 50 pytest probes (40 core + 10 supplementary, archived at `/tmp/opencode/test_security_probe.py` / `…_cp.py`) |

Layer A walks the live FastAPI app including lazy `_IncludedRouter` components via
`effective_route_contexts()`, then inspects each route's full dependency graph for auth-shaped
callables. This is deliberately *sensitive* (over-reports), so every "unguarded" hit was then
manually classified in Layer B and, where a defect was claimed, proven in Layer C.

Runtime probes were executed against the repository's own `conftest.py` fixtures (real app factory,
real middleware stack, real dependency graph, sqlite test schema):

```bash
cd backend
SECRET_KEY=test APP_ENV=development ENV=test BASE_URL=http://localhost:8000 \
REDIS_URL="redis://:testpass@127.0.0.1:6379/0" \
PYTHONPATH=/home/samertts/workspace/projects/gula-integration \
  <venv>/bin/python -m pytest tests/test_security_probe_tmp.py -q -p no:cacheprovider
# 40 passed, 6 warnings in 271.89s  (log: /tmp/opencode/security_probe3.log)
```

Supplementary control-plane read sweep (10 endpoints, `citizen` token):

```bash
SECRET_KEY=test APP_ENV=development ENV=test BASE_URL=http://localhost:8000 \
REDIS_URL="redis://:testpass@127.0.0.1:6379/0" \
PYTHONPATH=/home/samertts/workspace/projects/gula-integration \
  <venv>/bin/python -m pytest tests/test_security_probe_cp_tmp.py -q -p no:cacheprovider
# 10 passed in 151.07s  (log: /tmp/opencode/security_probe_cp.log)
```

Both temporary probe files were removed after evidence capture; the archived copies live at
`/tmp/opencode/test_security_probe.py` and `/tmp/opencode/test_security_probe_cp.py`.

---

## 2. Findings summary

| ID | Severity | Finding | CWE | Runtime proof |
|---|---|---|---|---|
| **S-01** | **CRITICAL** | Control plane has authentication but no authorization — any authenticated user (incl. `citizen`) can read the registry/topology, rewrite global config, create policies, and deploy releases | CWE-862 | yes (15 probes) |
| **S-02** | **CRITICAL** | Release deploy/approve takes the actor and approver identity from the request body (`data.get("user")`, `approve_first`) | CWE-290 / CWE-639 | yes |
| **S-03** | **HIGH** | NIAM persons / sessions / devices routes have no guard: anonymous PII create+read, session termination, device register/trust/revoke | CWE-306 | yes (6 probes, handler reached DB) |
| **S-04** | **HIGH** | National governance, lifecycle, pilot-platform writes are anonymous: release approval, go/no-go gate decisions, component registration, deprecation notices, phase transitions | CWE-306 | yes |
| **S-05** | **HIGH** | `POST /governance/audit-events` is anonymous and accepts an attacker-chosen `actor_id` → audit-trail forgery | CWE-778 / CWE-306 | yes (write + list readback) |
| **S-06** | **HIGH** | Redis degraded mode silently falls back to per-process memory: token revocation, rate limits and `set_if_absent` become per-worker | CWE-636 | no (static) |
| **S-07** | MEDIUM | `USE_SECURE_COOKIES = IS_PRODUCTION or DEMO_MODE` — staging/pilot over HTTPS sets auth cookies without `Secure` | CWE-614 | no (static) |
| **S-08** | MEDIUM | Anonymous read of governance org/worker/health-number data (ministry hierarchy, worker productivity, national test catalog) | CWE-306 / CWE-200 | yes |
| **S-09** | MEDIUM | Anonymous read of AI platform internals: `/api/ai/operations`, `/api/ai/providers`, `/api/ai/dataset/status` | CWE-200 | yes |
| **S-10** | MEDIUM | `/certification/*` (9 routes) unguarded — anonymous certification/release-check computation | CWE-306 | yes |
| **S-11** | MEDIUM | `POST /contracts/export` anonymous; bounded to a server-owned temp dir, so impact is disk/CPU abuse, not traversal | CWE-306 / CWE-400 | yes |
| **S-12** | LOW | `/lims/quality/indicators` + `/…/evaluate` unguarded (pure computation, no persistence) | CWE-306 | yes |
| **S-13** | **HIGH** | `POST /auth/verification/confirm` set `is_verified=True` on **any** `User`, so a self-declared `doctor` could self-verify (code goes to their own email/phone) and skip the medical-licence approval that `/register/doctor` promises — privilege escalation to the `doctor` role | CWE-863 | yes (7 regression tests) |

Severity is assigned on **exploitability × blast radius**, not on scanner score. S-01/S-02 are
critical because together they let any self-registered account take the release path.

---

## 3. Findings in detail

### 3.0 Remediation status (implemented in the working tree, uncommitted, awaiting review)

| Finding | Status | Fix (working tree) | Regression evidence |
|---|---|---|---|
| S-01 | REMEDIATED (unreviewed) | `/control-plane` reads ⇒ `master_admin`/`ministry_admin`; writes ⇒ `master_admin` only; `POST /policies/evaluate` treated as a read | `tests/test_control_plane_authorization.py` 21/21 |
| S-02 | REMEDIATED (unreviewed) | New `POST /releases/{id}/approve`; deploy requires `status == APPROVED` and `approved_by != actor`; body actor/approver fields rejected `400`; actor derived from the token | same file |
| S-03 | REMEDIATED (unreviewed) | `require_niam_registry_reader`/`_writer` via `get_current_identity`; reader on `persons`/`sessions`, writer on `devices` and the person-create/session-terminate writes; NIAM `accounts` stay `410` | `tests/test_niam_registry_authorization.py` 21/21 |
| S-04 | REMEDIATED (unreviewed) | Shared policy `app/security/platform_access.py`: reads ⇒ explicit operational allow-list (citizen denied), writes ⇒ `master_admin`; applied to lifecycle 18, pilot-platform 14, certification 9, contracts 9 | `tests/test_national_governance_authorization.py` 29/29 |
| S-05 | REMEDIATED (unreviewed) | `POST /governance/audit-events` authenticated; `actor_id`/`actor_role` derived server-side; forged `actor_id` ⇒ `403`, nothing persisted | `tests/test_governance_audit_authorization.py` 11/11 |
| S-06 | REMEDIATED (unreviewed) | `security_store()` fail-closed boundary for revocation/rate-limit/idempotency/verification when the store is process-local in production/staging without `ALLOW_DEGRADED_REDIS=true`; 503 at the dependency/limiter. **Follow-up (this cycle):** `app/core/kill_switch.py` no longer fails open — an unreadable shared kill-switch state is treated as **ACTIVE** in production/staging (`IS_PRODUCTION` covers production+staging), with a CRITICAL log and `status()["shared_state_readable"]=false`; dev/test keep fail-open | `tests/test_security_store_policy.py` 12/12; `tests/test_kill_switch_fail_closed.py` **9/9** |
| S-07 | REMEDIATED (unreviewed) | `USE_SECURE_COOKIES` now true whenever `BASE_URL` is HTTPS; single `cookie_security_options()` helper used by all five cookie-writing paths | same file |
| S-08 | REMEDIATED (unreviewed) | 24 confidential `/governance` reads ⇒ `require_governance_reader`; 3 anonymous worker writes ⇒ `elevated_dep`; `/governance/health` stays public | `tests/test_governance_anonymous_access.py` 8/8 |
| S-09 | REMEDIATED (unreviewed) | `require_ai_operator` on `/api/ai/operations`, `/api/ai/providers`, `/api/ai/dataset/status` | `tests/test_ai_platform_authorization.py` 8/8 |
| S-10 / S-11 | REMEDIATED (unreviewed) | Covered by S-04 (certification + contracts routers) | `tests/test_national_governance_authorization.py` |
| S-12 | REMEDIATED (unreviewed) | `get_current_user` on both `/lims/quality/indicators` routes | `tests/test_lims_quality_authorization.py` 5/5 |
| **S-13** | REMEDIATED (unreviewed) | `app/routes/verification.py`: `SELF_VERIFIABLE_ROLES = ("citizen",)`; `_find_user()` filters `User.role.in_(…)` so a professional identifier is indistinguishable from an unknown one; professional activation only via `PUT /admin/doctors/{id}/approve` | `tests/test_professional_verification_authorization.py` **7/7** |

Post-remediation route walk (re-run, **reconstructed walker** — see `PUBLIC_ENDPOINT_REGISTER.md`
§1): **2 133 endpoints, 2 064 guarded, 69 unguarded**, and those 69 are exactly the
public-by-design/in-body set — **0 residual gaps**. Relative to the original review (2 132
endpoints, 1 974 guarded, 158 unguarded = 91 real gaps + 67 public), every real gap is closed; the
one added endpoint is the new guarded `POST /control-plane/releases/{id}/approve`, and the +2
unguarded delta is `POST /oauth2/token` + `POST /auth/refresh` — the earlier name-based heuristic
counted them as guarded, both were re-reviewed as credential-validating (register §2/§4.3/§4.4).
**No endpoint regressed to unguarded.** Classification artifact:
`/tmp/opencode/remediation/unguarded_classification.json` (11 categories, 69/69 partitioned,
0 residual gaps).

### S-01 — Control plane: authentication without authorization (CRITICAL)

`backend/app/control_plane/routes.py` mounts 21 endpoints under `/control-plane`. Every handler
depends on `_user`, which is only:

```python
def _user(request_user=Depends(get_current_user)):
    return request_user
```

No role, permission, scope or tenant check follows. Runtime evidence (all with a **`citizen`**-role
lab user token):

| Probe | Result |
|---|---|
| `GET /control-plane/registry/components` | `200` — full component inventory |
| `GET /control-plane/registry/topology`, `/fleet/nodes`, `/health`, `/policies`, `/operations/dashboard`, `/releases`, `/audit-log`, `/kpis`, `/digital-twin/service` | `200` (10/10, supplementary run) |
| `PUT /control-plane/config/global/emergency-kill-switch` `{"config":{"enabled":false}}` | `200`, `{"status":"updated"}` |
| `POST /control-plane/policies` (effect `allow`) then `POST /policies/evaluate` | `200`, policy persisted |
| `POST /control-plane/releases` → `POST /releases/deploy` | `200`, `status in ("deployed","deploying")` |
| `GET /control-plane/registry/components` **without any token** | `401` (positive control) |

The registry is a process-wide singleton (`ControlPlaneSDK.get_instance()`), so a poisoned
configuration or policy is visible to every worker until restart.

**Impact:** configuration tampering (e.g. disabling kill switches, redirecting components),
policy-store poisoning, and unauthorised release deployment. `CWE-862 Missing Authorization`.
`OWASP API5:2023 Broken Function Level Authorization`.

### S-02 — Release approval identity is caller-supplied (CRITICAL)

```python
# control_plane/routes.py — /releases/deploy
data.get("user")          # actor
data.get("approve_first") # self-approval flag
```

The probe created a release as a `citizen`, then deployed it with `{"user": "master_admin",
"approve_first": true}` and received `200`. The audit trail therefore records a *chosen* identity,
and the two-person rule is reduced to a JSON field.

`CWE-290 Authentication Bypass by Spoofing`, `CWE-639 Authorization Bypass Through User-Controlled
Key`. **Fix shape:** derive actor/approver from the authenticated principal only; require a
distinct approver with an explicit role; make `approve_first` a server-side state transition.

### S-03 — NIAM identity store unguarded (HIGH)

`backend/app/identity/api/router.py` requires authentication for most sub-routers:

```python
router.include_router(governance_routes.router, dependencies=_AUTH_REQUIRED)
router.include_router(trust_routes.router, dependencies=_AUTH_REQUIRED)
... 10 more ...
router.include_router(persons.router)   # ← no guard
router.include_router(sessions.router)  # ← no guard
router.include_router(devices.router)   # ← no guard
router.include_router(auth.router)      # intended: login/refresh
router.include_router(accounts.router)  # returns 410
```

Proven anonymously (the reduced sqlite schema omits `niam_*` tables, so the probes assert the
request reached the SQL layer — no auth dependency returned 401/403 first):

| Endpoint | Evidence |
|---|---|
| `POST /niam/persons/` | handler reached `INSERT INTO niam_persons` |
| `GET /niam/persons/{uuid}` | handler reached `SELECT … niam_persons` (PII: name, national-id hash, phone, address) |
| `GET /niam/sessions/account/{id}` | reached `niam_sessions` |
| `POST /niam/sessions/account/{id}/terminate-all` | reached `niam_sessions` |
| `POST /niam/sessions/{uuid}/terminate` | reached `niam_sessions` |
| `POST /niam/devices/register` | reached `niam_devices` |
| `POST /niam/devices/{uuid}/trust`, `/revoke` | (same router, same absent guard) |

`CWE-306 Missing Authentication for Critical Function`. This is the national identity platform; a
single unauthenticated `POST /niam/devices/{uuid}/trust` is a device-trust elevation primitive.

### S-04 — National platform surfaces fully open (HIGH)

`app/lifecycle_platform/api/routes.py` (19 routes), `app/pilot_platform/api/routes.py` (15),
`app/certification/routes.py` (9), `app/contracts/routes.py` (9) declare routers with **no**
`dependencies=` and no auth in any handler signature.

Proven anonymous and successful (`200`) for reads, and handler-reachable for writes:

- `GET /lifecycle/components|releases|deprecations|upgrade-paths|dashboard` → `200` (probed)
- `POST /lifecycle/releases/{id}/approve` → not 401/403 (404 for a missing row ⇒ handler reached; probed)
- Other lifecycle writes (`POST /components|releases|deprecations|upgrade-paths`,
  `PUT /components/{id}/stage`) → **no auth dependency exists on the router** (inspected)
- `GET /pilot-platform/pilots|deployments|dashboard` → `200` (probed)
- `POST /pilot-platform/gates` → `IntegrityError: NOT NULL constraint failed: pilot_go_no_go_gates.lab_id`
  (i.e. the INSERT executed — a go/no-go gate decision is writable anonymously; probed)
- `GET /certification/dimensions|metrics`, `POST /certification/evaluate/{path}`, `/release/check`
  (reads probed; writes inspected)
- `GET /contracts/catalog|openapi.json|asyncapi.json` → `200` (probed); `fhir/*`, `graphql/schema`,
  `POST /export` inspected

`CWE-306`. These are the national release-governance controls; "who may approve a release" is the
control being bypassed.

### S-05 — Audit-event forgery (HIGH)

```python
@router.post("/audit-events")           # no dependencies
def log_audit_event(event_type: str, actor_id: str, action: str, ...):
```

Probe: anonymous `POST /governance/audit-events` with `actor_id=master_admin` and a unique action
marker returned `200`; a subsequent `GET /governance/audit-events?limit=200` returned the forged row
with the attacker-chosen actor. `CWE-778 Insufficient Logging`, `CWE-306`.

Because `app/services/audit_service.py` and `identity/services/canonical_audit.py` implement a real
SHA-256 chain with HMAC anchors (§5), a forged row is *cryptographically* chained — integrity
protects against post-hoc edits, not against authorised-path forgery by an unauthenticated writer.

### S-06 — Security state silently downgraded when Redis is unavailable (HIGH)

`backend/app/security/redis_client.py` wraps Redis and, on connection failure, falls back to
`_MemoryStore` (thread-safe, process-local). Callers never learn that they are in degraded mode:

- `blacklist_token()` / `is_token_blacklisted()` → a revoked access token remains valid on every
  worker that did not process the logout.
- `rate_limit._check()` → per-worker budgets; the effective global limit becomes `N × limit`.
- `set_if_absent()` → idempotency and replay protection become per-worker.

The startup logs a warning (`REDIS_URL not set — using in-memory store`), but a *runtime* Redis drop
does not fail closed. `CWE-636 Not Failing Securely`.

**Fix shape:** in production, treat Redis unavailability as fatal for auth-revocation checks (fail
closed) or emit a hard readiness failure; never silently downgrade.

### S-07 — Cookies lose `Secure` outside production (MEDIUM)

```python
USE_SECURE_COOKIES = IS_PRODUCTION or DEMO_MODE   # app/config.py:25
```

`backend/app/routes/login.py` sets `access_token`/`refresh_token` with
`httponly=True, samesite="strict", secure=USE_SECURE_COOKIES`. A staging or pilot deployment served
over HTTPS with `APP_ENV=staging` emits cookies **without** `Secure`, so any plaintext request to the
same host can leak them. `CWE-614 Sensitive Cookie Without 'Secure' Attribute`.

### S-08 — Anonymous read of national governance data (MEDIUM)

Of the 29 unguarded `/governance` routes, the following are *reads of confidential organisational
and personnel data*, not just public catalogues. Only `/governance/audit-events` was exercised at
runtime (S-05); the rest are **inspected**: every one of them is declared on the governance router
with no `admin_dep`/`elevated_dep` and no handler-body guard.

`GET /governance/nodes/{id}`, `…/subtree`, `…/path`, `…/children`, `…/by-type/{type}` (ministry →
directorate → hospital → laboratory hierarchy), `GET /governance/workers/{id}`,
`…/productivity`, `…/stats`, `…/ranking`, `…/by-node/{id}`, `GET /governance/health-numbers/{n}`,
`…/history`, `GET /governance/laboratories*`, `GET /governance/policy/evaluate`,
plus anonymous **writes** `POST /governance/workers/{id}/trainings|competencies|productivity`.

`CWE-306` + `CWE-200 Exposure of Sensitive Information`.

### S-09 — AI platform internals exposed (MEDIUM)

`GET /api/ai/operations`, `/api/ai/providers`, `/api/ai/dataset/status` are unguarded (inspected —
no dependency and no body guard) and return provider/runtime/dataset state.
`GET /api/ai/interpret/{token}` and the Telegram webhook are token/signature-based (see §4). `CWE-200`.

**Remediated:** all three now require an authenticated AI operator (`require_ai_operator` —
clinician/administrator allow-list, `citizen` and future roles denied). `/api/ai/providers` also
stops anonymous callers from making the server issue an outbound probe to the configured provider
host. The token-addressed `/api/ai/interpret/{token}` remains public by design.
`tests/test_ai_platform_authorization.py` (8).

### S-10 / S-11 / S-12 — Remaining unguarded surfaces (MEDIUM/LOW)

| Case | Detail |
|---|---|
| `/certification/*` (9) | Evaluation and release-check endpoints run without auth (`GET /dimensions` and `/metrics` probed `200`; writes inspected). No persistence observed; impact is compute + disclosure of internal quality metrics. |
| `POST /contracts/export` | Anonymous (inspected). **Mitigated in depth:** `ContractExport.output_dir` is regex-bounded and `_new_export_directory()` writes to a server-owned `tempfile.mkdtemp(dir=GULA_EXPORT_ROOT)` — no traversal, no arbitrary write. Residual risk is disk/CPU exhaustion (`CWE-400`). |
| `/lims/quality/indicators` (2) | Returns static ISO 15189 / CAP indicator definitions; `/evaluate` is pure computation (inspected). `LOW`. |

All three cases are **remediated**: `/certification/*` and `/contracts/*` by the S-04 policy
(reads ⇒ operational allow-list, writes ⇒ `master_admin`); the two LIMS indicator routes by the same
`get_current_user` contract every other `/lims` route uses. Evidence:
`tests/test_national_governance_authorization.py` (29) and `tests/test_lims_quality_authorization.py`
(5, including the 404-on-unknown-indicator semantics being preserved).

---

### S-13 — Self-service verification of professional accounts (HIGH) — found in the post-remediation pass

`POST /register/doctor` creates `User(role="doctor", is_active=True, is_verified=False)` and its
docstring promises that "a ministry or province admin must verify the account before the doctor can
access sensitive endpoints" (`app/routes/register.py`). The self-service flow broke that promise:

```python
# app/routes/verification.py — before the fix
def _find_user(db, identifier):                       # no role filter
    return db.query(User).filter((User.email == identifier) | (User.phone == identifier)).first()
```

`POST /auth/verification/confirm` delivered the 6-digit code to the identifier the registrant
**themselves** supplied, then set `is_verified = True`. Because `login.py` and `get_current_user`
both gate on `User.is_verified`, a self-declared "doctor" could verify their own account and obtain
every `doctor`-role API privilege with **zero licence review** — the administrative approval path
(`PUT /admin/doctors/{id}/approve`, ministry/province admin) became optional. `CWE-863 Incorrect
Authorization`; authentication was present, authorization was not.

**Policy (defined before the fix):** code possession proves control of a contact channel, nothing
more. It must never confer professional privilege.

**Fix:** `SELF_VERIFIABLE_ROLES = ("citizen",)` in `app/routes/verification.py`; `_find_user()`
filters `User.role.in_(SELF_VERIFIABLE_ROLES)`, so a professional identifier is handled exactly like
an unknown one (generic response, no code issued, `confirm` ⇒ 400, nothing written). The legitimate
workflow is unchanged: register → pending → `PUT /admin/doctors/{id}/approve` → login succeeds.

**Evidence:** `tests/test_professional_verification_authorization.py` **7/7** — doctor cannot
self-verify and login stays 403; doctor identifier indistinguishable from unknown (no oracle);
admin approval still activates and login succeeds (legitimate workflow); citizen self-verification
still works (no over-restriction); parametrized denial for `doctor`/`lab_admin`/`ministry_admin`.
Adjacent suites after the fix: security demo contract + register + login protection + identity
authentication + public demo security → **44 passed**.

**Residual (tracked, open):** R-07 in `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md` — unverified
`doctor` rows still exist after registration (login-blocked); consider `is_active=False` until
approval. **S-13 is therefore recorded as fixed-with-residual, not "fully closed".**

---

## 4. False-positive register (unguarded to the scanner, guarded in reality)

The dependency walker cannot see guards implemented in handler bodies. The table below records, for
every such hit, the actual control and whether it was **P**roven by a runtime probe (§9) or verified
by handler **I**nspection. None of them is a finding.

| Family | Guard | Evidence |
|---|---|---|
| `/citizen/profile`, `/results`, `/health-record` | `_current_citizen()` validates the signed cookie in-body | **P** — `401` |
| `/citizen/orders` | same in-body cookie check | **I** |
| `/edge/agent/heartbeat`, `/telemetry` | per-device HMAC token (`_resolve_agent_device`, `hmac.compare_digest`, revoke/kill-switch checks) | **P** — `401` |
| `/edge/agent/tasks/{uid}/result` | same agent-token resolution | **I** |
| `/device-integration/wearables/webhook/{provider}` | HMAC-SHA256 signature + 300 s timestamp window; **fails closed** when the secret is unset | **P** — `503` (unconfigured) |
| `/history/{phone}` | feature flag off → explicit `410` | **P** — `410` |
| `/niam/accounts/*` (3) | deliberate `410 GONE` stubs | **P** — `410` |
| `/niam/account-requests/` | `rate_limit_auth` + idempotency key | **I** |
| `/register`, `/register/citizen`, `/register/doctor` | `rate_limit_auth` + `_require_approved_onboarding()` | **I** |
| `/demo/access` | `DEMO_MODE` and not production | **P** — `404` |
| `/setup/status` | constant outside setup mode | **I** |
| `/auth/refresh` | refresh token required, decoded with a separate secret | **P** — `401` |
| `/auth/forgot-password`, `/auth/reset-password` | `Depends(rate_limit_auth)` | **I** |
| `/auth/verification/request`, `/auth/verification/confirm` | OTP attempt cap + rate limit | **I** |
| `/r/{token}`, `/r/{token}/pdf`, `/qr/{token}`, `/qr-medical/{token}` | capability token in path + rate limit | **I** |
| `/api/ai/interpret/{token}` | capability token | **I** |
| `/api/v1/telegram/webhook` | secret-token header + chat allowlist | **I** |
| `/tiers`, `/test-types`, `/test-profiles`, `/app-updates`, `/compliance/time-sync`, `/fhir-interoperability/metadata` | public catalogues / version metadata (intentional) | **I** |
| `/oauth2/introspect`, `/oauth2/revoke`, `/oauth2/.well-known/openid-configuration`, `/oauth2/jwks.json`, `/.well-known/smart-configuration` | OAuth client authentication in-body; discovery documents must be public | **I** |
| `/auth/saml/metadata`, `/auth/saml/acs` | ACS fails closed (`503`) unless the IdP cert + issuer are configured, then verifies the XML signature with `signxml` before parsing the assertion (`app/routes/saml.py:47`) | **I** |
| `/login`, `/logout`, `/niam/auth/login`, `/niam/auth/logout`, `/niam/auth/refresh`, `/citizen/login`, `/citizen/logout`, `/auth/mobile/app-info` | session establishment endpoints / app version metadata | **I** |
| `/health*`, `/national/tasks/health`, `/fhir-interoperability/health/`, `/edge/health`, `/niam/health`, `/governance/health`, `/lifecycle/health`, `/pilot-platform/health` | liveness probes, intentionally unauthenticated (`GlobalRateLimitMiddleware` keeps them available) | **I** |
| `/metrics/prom` | open in dev/test for scraping; **in production** requires `Authorization: Bearer $METRICS_BEARER_TOKEN` and returns `503` when the token is unset (fail-closed) — `app/routes/metrics.py:130` | **I** |
| `/docs`, `/redoc`, `/openapi.json` | open in dev/test; in production `DocsAuthMiddleware` requires a blacklist-checked token with role `admin`/`master_admin` (`factory.py:445`, `middleware.py:303`) | **I** |

**P** = proven by runtime probe (§9). **I** = verified by handler inspection (no probe; the route was
correctly identified as unguarded by the walker, but its in-body control was assessed by reading the
code). No entry in this register is claimed as runtime-verified without a matching probe.

**Coverage arithmetic:** at review time, 158 endpoints carried no auth dependency. **91 were real
gaps** (§3); the other **67** are in this register (public by design or guarded in-body).

**After remediation:** 2 133 endpoints, 2 064 guarded, **69 unguarded = the public-by-design set,
0 real gaps** (67 original entries + `POST /oauth2/token` + `POST /auth/refresh`, both reviewed —
register §2). Each of the 69 is classified (11 categories) in
`/tmp/opencode/remediation/unguarded_classification.json`, and the set partitions exactly (no
unclassified/stale entry); the per-endpoint handler/control/residual table lives in
`GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md` §4.

---

## 5. Verified controls (what is already sound)

| Control | Evidence |
|---|---|
| Password hashing | bcrypt (`shared/auth/passwords.py`, `bcrypt.gensalt()` + `checkpw`); a pre-computed dummy bcrypt hash equalises work on unknown-user login (`app/security/auth.py:68`) |
| JWT integrity | algorithm pinned `[JWT_ALGORITHM]` (HS256) — no `alg=none`/confusion; `type` claim enforced (`decode_token`, `type != "access" → None`); **separate `REFRESH_TOKEN_SECRET`** |
| Session cookies | `httponly=True`, `samesite="strict"`, scoped `path="/"` (`app/routes/login.py:205`) |
| CSRF | `CSRFMiddleware` (`app/security/csrf.py`) — mutating requests with an auth cookie must carry an allow-listed `Origin`/`Referer`; browser-like UA with neither header is rejected (fail-closed) |
| Audit integrity | SHA-256 hash chain with `_GENESIS_HASH`, per-entry anchors and HMAC anchor files (`app/services/audit_service.py`, `app/identity/services/canonical_audit.py`); `verify_audit_chain()` available |
| Rate limiting | `GlobalRateLimitMiddleware` on every non-health path (`app/middleware.py:96`) + 26 route-level limiter call sites (3 `Depends(rate_limit_*)`, 23 direct calls) |
| Request hardening | `MaxBodySizeMiddleware`, `TrustedHostMiddleware` (when configured), `SecurityHeadersMiddleware`, `RequestIDMiddleware`, `RequestTimingMiddleware` |
| Metrics endpoint hardening | `/metrics/prom` returns `401` unless `Authorization: Bearer $METRICS_BEARER_TOKEN` matches in production, and `503` when the token is unset — it fails closed rather than exposing platform-wide telemetry (`app/routes/metrics.py:130`) |
| Docs exposure | In production `DocsAuthMiddleware` requires a blacklist-checked token with role `admin`/`master_admin` for `/docs`, `/redoc`, `/openapi.json` (`app/factory.py:445`, `app/middleware.py:303`) |
| Production secret hygiene | `_validate_production_secret()` refuses `< 32` char or weak `SECRET_KEY`; `SECRET_KEY` unset in production → process exits |
| Secret leakage | No secret in tracked files. Pattern sweep for AWS keys, private keys, `gsk_*`, `sk-*`, `ghp_*` produced 4 hits — all benign (a scanner pattern list, two documentation placeholders, one `os.getenv("AWS_SECRET_ACCESS_KEY")` read). `.env` is gitignored and untracked |
| Edge / device authentication | per-device HMAC token with `compare_digest`, trust penalty on signature failure, revoke + kill-switch enforcement |
| Webhooks | HMAC + timestamp window; unset secret ⇒ `503` (fails closed) rather than open |
| Frontend dependencies | `npm audit --omit=dev` → **0 vulnerabilities** (axios 1.18.1 → 1.21.1, follow-redirects 1.16.0 → 1.16.3) |

---

## 6. Latent risks (present in code, not reachable today)

| Risk | Assessment |
|---|---|
| **SSRF sink in `HealthAggregator.check_component`** | `app/control_plane/registry/health.py` fetches `comp.health_endpoint` with `httpx`. `GET /control-plane/health` calls `aggregate()`, which **only reads the cache**; a registered component's status stays `"registered"`. Runtime probe confirms **no outbound request** is made. The sink is real but unreachable — it becomes exploitable the moment anyone wires `check_component` to a route or a scheduler. Treat as **latent critical** and add an allow-list before enabling. |
| **`POST /contracts/export`** | Server-owned temp dir + regex-bounded label ⇒ disk/CPU abuse only (§3 S-11). |
| **`USE_SECURE_COOKIES`** | Build-time boolean; also affects `DEMO_MODE` deployments. |
| **No authorization framework on the control plane** | Even after adding role checks, there is no scoped capability model for platform operations (release, config, policy). Medium-term design work, not a one-line fix. |

---

## 7. Coverage numbers (regenerable)

| Metric | Value |
|---|---|
| Effective endpoints (all methods, lazy routers expanded) | **2 132** |
| With an auth dependency in the graph | **1 974 (92.6 %)** |
| Without any auth dependency | **158 (7.4 %)** |
| └ Real gaps | **91** |
| └ Public-by-design or in-body-guarded | **67** |
| OpenAPI surface (runtime) | **1 810 paths / 2 122 operations** — fully covered by the walk, plus 10 non-schema routes (docs UI, `/metrics/prom`, health probes) |
| Runtime probes executed | **50 — 50 passed** (40 core + 10 supplementary control-plane reads) |

Post-remediation (re-derived from the same walker after S-01…S-13 — **reconstructed walker**, see
`GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md` §1 for the tmp-cleanup reconstitution note):

| Metric | Value |
|---|---|
| Effective endpoints | **2 133** (+1: guarded `POST /control-plane/releases/{id}/approve`) |
| With an auth dependency | **2 064 (96.8 %)** |
| Without any auth dependency | **69 (3.2 %)** |
| └ Real gaps | **0** |
| └ Public-by-design or in-body-guarded | **69** — 67 unchanged + `POST /oauth2/token` and `POST /auth/refresh`, which the earlier name-based heuristic counted as guarded; both read line-by-line and confirmed credential-validating (register §4.3/§4.4) |

Per-family real gaps: `governance` 28, `lifecycle` 18, `pilot-platform` 14, `certification` 9,
`contracts` 9, `niam` 8, `/api/ai` 3, `lims` 2.

**Per-endpoint evidence register:** `GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md` — all 69 endpoints
with handler, control and residual risk; the 91 → 0 closure map (§3 there); residuals **R-01…R-11**
open.

---

## 8. What this report does **not** certify

1. **Remediation is implemented but unreviewed.** S-01…S-12 are coded in the working tree and backed
   by regression tests, but the changes are **uncommitted** and have **not** had independent human
   security review. This report is the finding record, not a fix certification.
2. **No penetration test.** Probes are logic-level (route reachability, identity spoofing,
   persistence), not fuzzing, injection or business-logic abuse.
3. **No infrastructure review.** TLS termination, WAF, network policy, secrets manager, Redis/KMS
   topology and backup encryption are out of scope here.
4. **No third-party audit of the GLOSI registry** (unchanged from `SECURITY_COVERAGE_MATRIX.md`).
5. **No existing-database rehearsal** (`MIG-EXISTING` remains `NOT VERIFIED`).
6. **Backend dependency advisories: 55 known vulnerabilities in 6 runtime packages.** The frontend
   tree is audit-clean (`npm audit --omit=dev` → 0). The backend runtime lock was scanned with
   `pip-audit 2.10.1` (isolated venv): **55 advisories across `pillow` (42), `pyasn1` (4),
   `urllib3` (3), `joserfc` (2), `dnspython` (2), `certifi` (2)** — every one has a fixed version
   available in `requirements-lock.txt`. Log: `/tmp/opencode/remediation/pip_audit_backend.log`
   (exit 1). This stays on the release-blocker register until the pins are upgraded and a clean
   scan is recorded (or the risk is formally accepted).

---

## 9. Reproduction

```bash
# A. Rebuild the route-surface numbers
cd backend
ENV=test SECRET_KEY=test APP_ENV=development \
PYTHONPATH=$PWD:/home/samertts/workspace/projects/gula-integration \
  <venv>/bin/python /tmp/opencode/audit_auth_coverage.py
# → total_endpoints=2132 guarded=1974 unguarded=158  (+ /tmp/opencode/auth_coverage.json)

# B. Re-run the 50 runtime probes (copy back from /tmp first)
cp /tmp/opencode/test_security_probe.py tests/test_security_probe_tmp.py
cp /tmp/opencode/test_security_probe_cp.py tests/test_security_probe_cp_tmp.py
SECRET_KEY=test APP_ENV=development ENV=test BASE_URL=http://localhost:8000 \
REDIS_URL="redis://:testpass@127.0.0.1:6379/0" \
PYTHONPATH=/home/samertts/workspace/projects/gula-integration \
  <venv>/bin/python -m pytest tests/test_security_probe_tmp.py tests/test_security_probe_cp_tmp.py \
  -q -p no:cacheprovider
# → 40 passed (security_probe3.log) + 10 passed (security_probe_cp.log)
# Both temporary files were deleted after evidence capture; remove them again after re-running.

# C. Frontend dependency surface
cd frontend-v3 && npm audit --omit=dev    # → 0 vulnerabilities
```

The probe file asserts the **current defective behaviour** on purpose. Each assertion is a
regression tripwire: it fails the moment the corresponding hole is closed, at which point the
assertion must be inverted.

### 9.1 Post-remediation re-walk (after S-01…S-13)

```bash
cd backend
ENV=test SECRET_KEY=test APP_ENV=development BASE_URL=http://localhost:8000 \
PYTHONPATH=$PWD:/home/samertts/workspace/projects/gula-integration \
  <venv>/bin/python /tmp/opencode/remediation/audit_auth_coverage_after.py
# → total_endpoints=2133 guarded=2064 unguarded=69  (/tmp/opencode/remediation/auth_coverage_after.json)

<venv>/bin/python /tmp/opencode/remediation/classify_unguarded.py
# → classified=69/69 partitioned into 11 public-by-design categories; residual_gaps=0
#   (/tmp/opencode/remediation/unguarded_classification.json)
```

Both scripts and JSON artifacts were **reconstructed** in this cycle after a tmp-directory cleanup
removed the originals; methodology unchanged (§1). The 69-vs-67 delta is explained in
`GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md` §2 and both added endpoints are reviewed there (§4.3/§4.4).

`PYTHONPATH` must list the integration `backend` **before** the repository root, otherwise the
virtualenv's editable install of the sibling `gula-platform/backend` wins and boot fails on
`shared.models.base.SharedBase`.

---

## 10. Remediation order (implemented in the working tree; awaiting review)

| Order | Action | Findings | Effort | Status |
|---|---|---|---|---|
| 1 | Add role/scoped authorization to `/control-plane` (admin-only writes; distinct approver from the token) | S-01, S-02 | M | **done** (`test_control_plane_authorization.py`) |
| 2 | Add auth + role deps to `persons`, `sessions`, `devices`; keep `auth`/`accounts` as-is | S-03 | S | **done** (`test_niam_registry_authorization.py`) |
| 3 | Guard lifecycle / pilot-platform / governance (write ⇒ admin, read ⇒ authenticated staff); per-route, not blanket | S-04, S-05, S-08 | M | **done** (`test_national_governance_authorization.py`, `test_governance_audit_authorization.py`, `test_governance_anonymous_access.py`) |
| 4 | Fail closed (or hard-fail readiness) when Redis is unavailable in production | S-06 | S | **done** (`test_security_store_policy.py`) |
| 5 | `USE_SECURE_COOKIES` derived from HTTPS in every environment | S-07 | XS | **done** (`cookie_security_options()`) |
| 6 | Guard AI operations/providers/dataset, certification, contracts export, LIMS indicators | S-09…S-12 | S | **done** (`test_ai_platform_authorization.py`, `test_lims_quality_authorization.py`, S-04 suite) |
| 6b | Kill-switch shared state **fails closed** in production/staging (unreadable ⇒ ACTIVE, CRITICAL log, `shared_state_readable` in `status()`) | S-06 residual | S | **done** (`test_kill_switch_fail_closed.py`, 9/9) |
| 6c | Restrict self-service verification to `citizen`; professional activation only via admin licence approval | **S-13** | S | **done** (`test_professional_verification_authorization.py`, 7/7; residual R-07 open) |
| 6d | Per-endpoint evidence register: 91 → 0 closure map + all 69 public endpoints with control and residual | evidence | M | **done** (`GOVERNANCE/PUBLIC_ENDPOINT_REGISTER.md`, residuals R-01…R-11 open) |
| 7 | Add an SSRF allow-list before any code path can call `HealthAggregator.check_component` | latent | S | **open** |

---

_Static analysis + 40 runtime probes at review time; remediation implemented in the working tree
(uncommitted, awaiting independent review). No certification is claimed._
