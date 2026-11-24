# PUBLIC ENDPOINT REGISTER — 91 → 0 real gaps, 69 public-by-design

**Program:** GULA unification security remediation (`integration/gula-unification-v1`)
**Purpose:** Program Director item 6 — reconcile the historical **91 confirmed unguarded gaps**
with the final public-by-design set and preserve a **traceable per-endpoint evidence register**.
**Verdict:** this register does **not** change `FINAL_DECISION.md`. The verdict stays **HOLD**;
no finding is marked closed while a residual risk below remains open.

---

## 1. Method and artifacts

| Layer | What it does | Artifact |
|---|---|---|
| Route-surface walk | Boots the live app, materializes every lazy `_IncludedRouter` via `effective_candidates()`, recursively walks each route's FastAPI dependency graph, flags routes with an auth-shaped callable (`require_*`, `get_current_*`, identity deps) | `/tmp/opencode/remediation/audit_auth_coverage_after.py` → `auth_coverage_after.json` |
| Classification | Deterministic path rules partition **every** unguarded route into exactly one public-by-design category; any route matching no rule becomes a `residual_gaps` entry and the script exits non-zero | `/tmp/opencode/remediation/classify_unguarded.py` → `unguarded_classification.json` |
| Manual review (this register) | For each endpoint: read the handler, confirm the control, record residual risk | §4, §5 |

The walker is deliberately *sensitive* (over-reports guarded), so "unguarded" means
"no auth dependency visible in the dependency graph" — not "public". Every unguarded hit was then
read and classified by hand (§4/§5). In-body guards (citizen portal, webhooks, token-addressed
reads, `oauth2/token` client auth) therefore stay in the unguarded bucket **by design**.

> **Evidence reconstitution note.** The original scripts and JSON artifacts under
> `/tmp/opencode/` were lost to a tmp-directory cleanup mid-review. Both scripts were
> **rewritten from the documented methodology** (`SECURITY_REVIEW_REPORT.md` §1/§9.1) and
> re-executed. The reconstructed walk reproduces the documented totals exactly for the route
> count (2 133) and differs only in the guarded/unguarded split by the two endpoints explained
> in §3. Git history, all source changes, all test files and all GOVERNANCE documents are
> unaffected (nothing was ever committed; HEAD remains `2827c1ff`).

Reproduction:

```bash
cd backend
ENV=test SECRET_KEY=test APP_ENV=development BASE_URL=http://localhost:8000 \
PYTHONPATH=$PWD:/home/samertts/workspace/projects/gula-integration \
  <venv>/bin/python /tmp/opencode/remediation/audit_auth_coverage_after.py
# → total_endpoints=2133 guarded=2064 unguarded=69

<venv>/bin/python /tmp/opencode/remediation/classify_unguarded.py
# → classified=69/69 residual_gaps=0
```

---

## 2. Reconciliation arithmetic

| | Endpoints | Guarded | Unguarded | Real gaps | Public-by-design |
|---|---|---|---|---|---|
| **Baseline** (pre-remediation, `SECURITY_REVIEW_REPORT` §9) | 2 132 | 1 974 | 158 | **91** | 67 |
| **Post-remediation** (this register) | 2 133 | 2 064 | 69 | **0** | 69 |

* `158 = 91 real gaps + 67 public-by-design` (baseline classification, `SECURITY_REVIEW_REPORT` §3.4/§7).
* `91` breaks down as governance 28, lifecycle 18, pilot-platform 14, certification 9,
  contracts 9, niam 8, `/api/ai` 3, lims 2 (`UNIFICATION_BLOCKERS.md` → `SEC-UNGUARDED`).
* All 91 are closed by S-01…S-12 with regression tests (§4).
* The post-remediation walk reports **69** unguarded, not 67: the reconstructed walker's
  auth-name pattern is purely dependency-graph based, so it additionally reports
  **`POST /oauth2/token`** and **`POST /auth/refresh`** — two endpoints the earlier heuristic
  counted as guarded (their endpoint names, `token` / `refresh_access_token`, matched a
  name-based rule). Both were read line-by-line for this register (§5, categories
  *protocol* and *authentication entry point*) and are **public by design**: each validates a
  credential in the handler (client secret + PKCE + single-use code; signed refresh token +
  rate limit). Neither exposes confidential data nor performs an unauthenticated
  state-changing operation. They are additions to the register, not new gaps.
* Post-remediation arithmetic: `2 064 + 69 = 2 133`, `0 residual gaps`.

---

## 3. Traceability — the historical 91 and how each was closed

Every row: endpoint group → finding → closure control → regression evidence.
"Closed" here means *regression-tested in the working tree, uncommitted, unreviewed* — the
release verdict remains HOLD pending independent review.

| # | Endpoint group (count) | Finding | Closure control | Regression evidence | Status |
|---|---|---|---|---|---|
| 1 | `/control-plane` registry/topology/config/policy/release reads + writes (part of 28 governance surface) | **S-01** CRITICAL — authN without authZ; any `citizen` token could rewrite global config | `require_role(master_admin, ministry_admin)` on reads; `master_admin` only on writes; `POST /policies/evaluate` treated as a read | `tests/test_control_plane_authorization.py` **21/21** | closed in tree |
| 2 | `/control-plane/releases/*` deploy/approve (S-01 surface) | **S-02** CRITICAL — actor/approver taken from request body | new `POST /releases/{id}/approve`; deploy requires `status == APPROVED` **and** `approved_by != actor`; body actor fields ⇒ `400`; actor derived from token (two-person rule) | same file **21/21** | closed in tree |
| 3 | `GET/POST /niam/persons*`, `/niam/sessions*`, `/niam/devices*` (8) | **S-03** HIGH — anonymous PII create/read, session termination, device trust/revoke | `require_niam_registry_reader` on `persons`/`sessions` reads, `require_niam_registry_writer` on `devices` + person-create/session-terminate; `accounts` stay `410` | `tests/test_niam_registry_authorization.py` **21/21** | closed in tree |
| 4 | `/lifecycle/*` (18), `/pilot-platform/*` (14), `/certification/*` (9), `/contracts/*` (9) | **S-04** HIGH (+ **S-10**, **S-11**) — anonymous national release-governance reads and writes | shared policy `app/security/platform_access.py`: reads ⇒ `require_governance_reader` (operational allow-list, citizen denied), writes ⇒ `require_governance_writer` (master/ministry/national); per-route, not blanket | `tests/test_national_governance_authorization.py` **29/29** | closed in tree |
| 5 | `POST /governance/audit-events` | **S-05** HIGH — attacker-chosen `actor_id` forged a hash-chained audit row | route authenticated; `actor_id`/`actor_role` derived server-side; forged id ⇒ `403`, nothing persisted | `tests/test_governance_audit_authorization.py` **11/11** | closed in tree |
| 6 | 24 confidential `/governance` reads (nodes/workers/health-numbers/laboratories/policy-evaluate) + 3 anonymous worker writes | **S-08** MEDIUM — anonymous organisational/personnel data | reads ⇒ `require_governance_reader`; writes ⇒ `elevated_dep`; `GET /governance/health` intentionally stays public (§5) | `tests/test_governance_anonymous_access.py` **8/8** | closed in tree |
| 7 | `GET /api/ai/operations`, `/api/ai/providers`, `/api/ai/dataset/status` (3) | **S-09** MEDIUM — anonymous AI platform internals + outbound provider probe | `require_ai_operator` (master/ministry/national/directorate/province admin, `admin`, `lab_admin`, `doctor`; citizen/technician/staff denied) | `tests/test_ai_platform_authorization.py` **8/8** | closed in tree |
| 8 | `/lims/quality/indicators`, `/…/evaluate` (2) | **S-12** LOW — unguarded (pure computation) | `Depends(get_current_user)` on both routes; 404-on-unknown-indicator semantics preserved | `tests/test_lims_quality_authorization.py` **5/5** | closed in tree |
| — | *(not endpoint gaps, but in the same review)* | **S-06** HIGH — Redis loss silently downgrades revocation/rate-limit/idempotency | `security_store()` fail-closed boundary (503 in production/staging without `ALLOW_DEGRADED_REDIS=true`) **+ kill-switch fail-closed**: unreadable shared state ⇒ switch treated ACTIVE in production/staging | `tests/test_security_store_policy.py` **12/12**; `tests/test_kill_switch_fail_closed.py` **9/9** | closed in tree (residual R-06) |
| — | *(not endpoint gaps)* | **S-07** MEDIUM — `Secure` cookie flag lost outside production | `USE_SECURE_COOKIES` derived from HTTPS in every environment via one `cookie_security_options()` helper (5 cookie-writing paths) | `tests/test_security_store_policy.py` | closed in tree |
| — | *(adjacent finding found during this review)* | **S-13** HIGH — `/auth/verification/confirm` could self-verify a professional account and skip licence approval (CWE-863) | `SELF_VERIFIABLE_ROLES = ("citizen",)`; professional roles only via `PUT /admin/doctors/{id}/approve` | `tests/test_professional_verification_authorization.py` **7/7** | closed in tree (residual R-07) |

**Result: 91 → 0 real unguarded gaps.** No endpoint regressed to unguarded; the
post-remediation unguarded set is exactly the public-by-design set (§5).

---

## 4. Public-by-design register — 69 endpoints, 11 categories

Legend: **Control** = the actual mechanism that makes public exposure safe.
**Residual** = risk that remains open (tracked in §6; not a data-exposure gap).

### 4.1 Liveness/readiness probe — no data (13)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `GET /health` | `app.main.health` | static liveness + non-sensitive counters | R-01 |
| `GET /health/ready` | `app.main.readiness` | dependency readiness | R-01 |
| `GET /health/live` | `app.main.liveness` | static | — |
| `GET /health/status` | `app.main.health_status` | dependency status | R-01 |
| `GET /health/deep` | `app.main.health_deep` | read-only metrics (db/redis ms, queue backlog, RSS, circuits), always HTTP 200 | R-01 |
| `GET /health/kernel` | `app.main.kernel_health` | kernel component state | R-01, R-02 |
| `GET /edge/health` | `app.routes.edge.edge_health` | edge feature flags/timeouts only | — |
| `GET /fhir-interoperability/health/` | `app.capabilities.fhir_interoperability.routes.health` | static `{"status":"ok"}` | — |
| `GET /governance/health` | `app.governance.routes.governance_routes.governance_health` | static domain list, explicitly public (comment in router) | — |
| `GET /lifecycle/health` | `app.lifecycle_platform.api.routes.health` | static module/version | — |
| `GET /pilot-platform/health` | `app.pilot_platform.api.routes.health` | static module/version | — |
| `GET /national/tasks/health` | `app.national.task_engine.api.routes.health` | static module/version | — |
| `GET /niam/health` | `app.identity.api.router.niam_health` | static domain/version | — |

**Confirmed:** no patient data, no identifiers, no state change. Version/env/pool/circuit/queue
details are operational telemetry (R-01, documented below — not a confidentiality gap).

### 4.2 API documentation / schema (4)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `GET /docs` | FastAPI `swagger_ui_html` | `DocsAuthMiddleware` requires `admin`/`master_admin` JWT **when `IS_PRODUCTION`** (`factory.py:446`) | R-03 |
| `GET /redoc` | FastAPI `redoc_html` | same middleware | R-03 |
| `GET /openapi.json` | FastAPI `openapi` | same middleware | R-03 |
| `GET /docs/oauth2-redirect` | FastAPI `swagger_ui_redirect` | static Swagger HTML (no data, no state); **not** in the middleware `_PROTECTED` set | R-04 |

**Confirmed:** in development/test they are open by design (schema is not confidential there);
in production `/docs`, `/redoc`, `/openapi.json` are behind admin auth.

### 4.3 Authentication entry point — rate-limited / credential-validating (14)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `POST /login` | `app.routes.login.login` | password verify + audit + verification gate (`is_verified`) + MFA for privileged roles; rate-limited | — |
| `POST /logout` | `app.routes.login.logout` | revokes own jti (requires presented token/cookie); idempotent | — |
| `POST /register` | `app.routes.register.register_lab` | `PUBLIC_SELF_REGISTRATION_ENABLED` default **false** (403), rate-limited; lab + admin created **inactive** pending `PUT /admin/labs/{id}/activate` | — |
| `POST /register/citizen` | `app.routes.register.register_citizen` | same onboarding gate; `is_verified=False` | — |
| `POST /register/doctor` | `app.routes.register.register_doctor` | same gate; creates `role=doctor, is_active=True, is_verified=False` — activation only via `PUT /admin/doctors/{id}/approve` (licence review) | R-07 |
| `POST /auth/verification/request` | `app.routes.verification.request_verification` | rate-limited; **S-13**: only `SELF_VERIFIABLE_ROLES = ("citizen",)` are found; generic response for unknown/professional identifiers (no oracle) | R-07 |
| `POST /auth/verification/confirm` | `app.routes.verification.confirm_verification` | rate-limited, 5 attempts, SHA-256-digested code, 15-min TTL; same role scope as above | R-07 |
| `POST /auth/forgot-password` | `app.routes.password_reset.forgot_password` | rate-limited; generic response (no enumeration); token stored bcrypt-hashed, 1 h expiry | R-05 |
| `POST /auth/reset-password` | `app.routes.password_reset.reset_password` | rate-limited; constant-time token verify against stored digest; single-use | R-05 |
| `POST /auth/refresh` | `app.routes.mobile.refresh_access_token` | rate-limited; **signed** refresh token verified (`decode_refresh_token`), user must be `is_active` (+`is_verified` for `User`), 401 otherwise | — |
| `POST /demo/access` | `app.routes.demo.start_demo_session` | **404 unless `DEMO_MODE` and not `IS_PRODUCTION`**; rate-limited; synthetic persona accounts in an isolated "GULA Synthetic Demo Lab", random password | — |
| `POST /niam/auth/login` | `app.identity.api.auth.login` | rate-limited per identifier; credential verification in service | — |
| `POST /niam/auth/refresh` | `app.identity.api.auth.refresh` | rate-limited (20/min); signed refresh token, 401 on invalid | — |
| `POST /niam/auth/logout` | `app.identity.api.auth.logout` | revokes presented session | — |

**Confirmed:** these are credential-validating entry points. **S-13** closed the one
privilege-escalation path found in this category (self-verification of professional accounts).
No confidential data is returned; state changes are limited to session/verification/password
state of the caller's own account (or 404/403 fail-closed paths).

### 4.4 Protocol discovery / metadata / client-authenticated token issuance (9)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `POST /oauth2/token` | `app.routes.oauth2.token` | **`_authenticate_client`** — client secret verified with `verify_password` (constant-time) or `client_secret` Basic auth; authorization code **single-use** (revoked on exchange), expiry checked, **PKCE** verified, code bound to `client_id` | R-08 |
| `POST /oauth2/introspect` | `app.routes.oauth2.introspect` | token looked up by **SHA-256 hash**; returns `active:false` for unknown/expired | R-08 |
| `POST /oauth2/revoke` | `app.routes.oauth2.revoke` | token looked up by hash; revocation only affects the presented token | R-08 |
| `GET /oauth2/.well-known/openid-configuration` | `app.routes.oauth2.openid_config` | static discovery document | — |
| `GET /oauth2/jwks.json` | `app.routes.oauth2.jwks_json` | public keys by design | — |
| `GET /auth/saml/metadata` | `app.routes.saml.metadata` | static SP metadata | — |
| `POST /auth/saml/acs` | `app.routes.saml.acs` | **fails closed** (503) if `SAML_IDP_ISSUER`/signing cert unset; SAML signature verified against IdP cert before any session is issued | — |
| `GET /.well-known/smart-configuration` | `app.routes.advanced_integrations.smart_configuration` | static SMART discovery constants | — |
| `GET /fhir-interoperability/metadata` | `app.capabilities.fhir_interoperability.routes.capability_metadata` | static capability statement (supported resource types) | — |

**Confirmed:** no confidential data (static documents or hash-lookup responses);
`/oauth2/token` performs no state change without client authentication.
**Residual R-08:** RFC 7662/7009 recommend *client* authentication on introspection/revocation;
this implementation authenticates only by token possession (256-bit token ⇒ infeasible to
guess, and the response discloses only metadata about the presented token). Recorded as a
conformance residual, not a data-exposure gap.

### 4.5 Token-addressed resource — possession = credential (5)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `GET /r/{token}` | `app.routes.results.get_public_result_route` | rate-limited 30/min; token hashed (`hash_token`) lookup; `Cache-Control: no-store`, `Referrer-Policy: no-referrer`, `X-Robots-Tag: noindex`; 404 on miss | — |
| `GET /r/{token}/pdf` | `app.routes.results.download_result_pdf_route` | rate-limited 10/min; same token + expiry checks; PDF download headers | — |
| `GET /qr/{token}` | `app.routes.qr.generate_qr_route` | rate-limited 20/min; **encodes only the URL** — no data read | — |
| `GET /qr-medical/{token}` | `app.routes.qr.generate_medical_qr` | rate-limited 10/min; hashed token + **expiry check** → 404 ("Not found", no oracle) | — |
| `GET /api/ai/interpret/{token}` | `app.routes.ai.interpret_result_public` | token format validated (`[A-Za-z0-9_-]{10,}`), hashed lookup, **expiry check**, 120 s response cache (cost limit); returns only Arabic plain-language interpretation | — |

**Confirmed:** the unguessable, expiring token *is* the credential (the same QR-token model the
lab hands to the patient). No session privilege, no cross-patient listing, no state change.

### 4.6 Signed webhook — signature verified in handler (5)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `POST /edge/agent/heartbeat` | `app.routes.edge.agent_heartbeat` | `_resolve_agent_device`: `Bearer` HMAC token (`compare_digest`), unknown device ⇒ 401, revoked/kill-switched ⇒ 403, signature failure penalizes device trust | — |
| `POST /edge/agent/tasks/{task_uid}/result` | `app.routes.edge.agent_task_result` | same agent-token + device-state gate | — |
| `POST /edge/agent/telemetry` | `app.routes.edge.agent_telemetry` | same | — |
| `POST /device-integration/wearables/webhook/{provider}` | `app.devices.routes.ingest_wearable_webhook` | `X-Signature-256` HMAC + `X-Webhook-Timestamp` freshness window, `compare_digest`; **503 if secret unset** (fail closed) | — |
| `POST /api/v1/telegram/webhook` | `app.notifications.telegram_chat.telegram_webhook` | `X-Telegram-Bot-Api-Secret-Token` constant-time compare (**503 if unset**), chat allowlist (**503 if empty**), sender allowlist; error responses never echo internals | — |

**Confirmed:** signature verification is in the handler (invisible to the dependency walker —
this is the intended "unguarded by the scanner" case). No unauthenticated state change.

### 4.7 Citizen portal — signed session cookie checked in handler (6)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `POST /citizen/login` | `app.routes.citizen_portal.citizen_login` | credential check; sets `httpOnly` `SameSite=Strict` (+`Secure` per S-07) cookies | — |
| `POST /citizen/logout` | `app.routes.citizen_portal.citizen_logout` | revokes own tokens, clears cookies | — |
| `GET /citizen/profile` | `…citizen_profile` | `_current_citizen()`: cookie JWT decode, jti revocation check (fail-closed 503 on store outage), `role == "citizen"`, DB row must be `is_active` **and** `is_verified` | — |
| `GET /citizen/results` | `…citizen_results` | same gate; rows scoped to the citizen's own linked patients across labs | — |
| `GET /citizen/orders` | `…citizen_orders` | same gate + same scoping | — |
| `GET /citizen/health-record` | `…citizen_health_record` | same gate + same scoping | — |

**Confirmed:** authentication *and* authorization in the handler; tenant/patient scoping is
per-citizen (no cross-citizen read path). State change limited to login/logout of self.

### 4.8 Public intake — rate-limited, review-gated, no account created (1)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `POST /niam/account-requests/` | `app.identity.api.account_requests.submit_account_request` | rate-limited 5/min, mandatory `Idempotency-Key` (16–200 chars), control-char rejection, `extra="forbid"`, **503 fail-closed** if intake config missing; service stores a *request row only* — never creates or activates an account | — |

**Confirmed:** creates only a reviewable intake record; the response contains
`accepted/status/request_id/message` — no account, no credentials, no PII disclosure.

### 4.9 Disabled stub — 410 GONE / feature flag off by default (4)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `GET /history/{phone}` | `app.routes.results.get_patient_history_route` | **410 unless `ENABLE_PUBLIC_PATIENT_HISTORY`** (default false); even then rate-limited 5/min; documented to require the authenticated citizen portal before enabling | R-09 |
| `POST /niam/accounts/` | `app.identity.api.accounts.create_account` | unconditional **410** — directs callers to the review-gated intake | — |
| `POST /niam/accounts/{uuid}/lock` | `…lock_account` | unconditional **410** (unscoped mutation disabled) | — |
| `POST /niam/accounts/{uuid}/unlock` | `…unlock_account` | unconditional **410** | — |

**Confirmed:** no path reaches data or mutation while the flags are at their defaults.

### 4.10 Public catalogue / config — no patient data (7)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `GET /test-types` | `app.main.list_test_types` | static reference catalogue (5-min cache) | — |
| `GET /test-profiles` | `app.routes.results.list_test_profiles` | static composite profiles + reference ranges | — |
| `GET /tiers` | `app.routes.tiers.list_tiers` | static tier/feature matrix (`/tiers/my`, `/tiers/upgrade` etc. **are** authenticated) | — |
| `GET /app-updates` | `app.routes.app_updates.get_update_manifest` | static version/force-update policy | — |
| `GET /auth/mobile/app-info` | `app.routes.mobile.get_app_info` | static app config + feature flags | — |
| `GET /compliance/time-sync` | `app.routes.compliance.time_sync_status` | server time + NTP status only (audit-timestamp trust anchor for auditors) | — |
| `GET /setup/status` | `app.routes.setup.setup_status` | **production always returns `needs_setup:false`** (no deployment-state disclosure); boolean only | R-10 |

**Confirmed:** reference/configuration data only — no identifiers, no tenant data, no state change.

### 4.11 In-handler bearer gate — production fail-closed (1)

| Endpoint | Handler | Control | Residual |
|---|---|---|---|
| `GET /metrics/prom` | `app.routes.metrics.prometheus_metrics` | **production:** requires `Authorization: Bearer $METRICS_BEARER_TOKEN`; **503 if the token is not configured** (fail closed); dev/test open by design | R-11 |

**Confirmed:** platform-wide telemetry (order stats, queue backlog, kill-switch gauge) is not
exposed in production without key material.

---

## 5. Residual risks (open — this register does **not** close them)

| ID | Residual | Severity | Status |
|---|---|---|---|
| **R-01** | Health probes disclose operational diagnostics: app version, `ENV`, DB/Redis latency, pool counters, circuit-breaker names, queue backlog, RSS/uptime (`/health`, `/health/status`, `/health/deep`, `/health/kernel`). Read-only, no identifiers — but useful for target reconnaissance. | LOW | open — hardening candidate (aggregate/gate detail behind auth or a `METRICS`-style token) |
| **R-02** | `/health/kernel` returns `str(e)` in its error payload — exception text may leak internals if the kernel fails to load. | LOW | open — hardening candidate (fixed error string + log the detail server-side) |
| **R-03** | `/docs`, `/redoc`, `/openapi.json` are gated only in production (`DocsAuthMiddleware` registered `if IS_PRODUCTION`); staging/dev expose the full schema. | LOW | open — accepted for dev; staging exposure is a deployment decision |
| **R-04** | `/docs/oauth2-redirect` is **not** in `DocsAuthMiddleware._PROTECTED` (`{"/docs","/redoc","/openapi.json"}`). It is static Swagger HTML with no data or state, so exposure is harmless today — but it is an inconsistency with R-03. | INFO | open — add to `_PROTECTED` as a one-line consistency fix |
| **R-05** | Password reset covers **`LabUser` only** (citizen/`User` accounts have no reset path), and `forgot-password` never delivers the token through a channel in this code path (no mail/SMS send). Also `reset-password` bcrypt-verifies the presented token against *every* pending row (bounded by rate limiting, but O(pending)). Functional/availability gap, not an exposure. | MEDIUM (functional) | open — product decision |
| **R-06** | Kill-switch fail-closed now depends on `IS_PRODUCTION` (production **+ staging**) and a readable shared store; in dev/test the switch still fails open by design. A total Redis outage in production blocks autonomous actions (desired) but also makes `/admin/kill-switch/status` report `shared_state_readable:false` — operators must treat that as ACTIVE. | MEDIUM | open — documented behaviour; alerting on `shared_state_readable=false` is a hardening candidate |
| **R-07** | S-13 closed self-verification of professional accounts, but `/register/doctor` still creates `is_active=True` accounts that exist (unverified) before licence review; login is blocked at `is_verified`, and self-service verification can no longer flip it. Residual is account-enumeration/persistence only (409 on duplicate email is pre-existing). | LOW | open — consider `is_active=False` until approval (product decision) |
| **R-08** | `POST /oauth2/introspect` / `POST /oauth2/revoke` do not authenticate the calling *client* (RFC 7662 §2.1 / RFC 7009 §2.1 recommend client auth). Mitigated: SHA-256 token lookup, 256-bit token entropy, response discloses metadata only about the presented token, revocation affects only that token. | LOW | open — conformance hardening |
| **R-09** | `ENABLE_PUBLIC_PATIENT_HISTORY` (default false) would re-expose longitudinal history by phone+name. Guarded by flag + rate limit, but enabling it without the citizen-portal migration would reintroduce a privacy gap. | MEDIUM if enabled | open — must stay false until the portal migration is verified |
| **R-10** | `/setup/status` returns a boolean deployment hint outside production (harmless), always `false` in production. | INFO | accepted |
| **R-11** | `/metrics/prom` is open in dev/test (by design) and bearer-gated in production; a deployment that sets `APP_ENV` incorrectly could expose telemetry. Fail-closed only when `IS_PRODUCTION` is true. | LOW | open — deployment verification item |

**Nothing in §4/§5 exposes patient identifiers, clinical results, credentials, or performs an
unauthenticated state-changing operation** at default configuration. The residuals above are
documented, tracked, and deliberately left open.

---

## 6. Verdict impact

* Historical **91** real gaps → **0** (§3), each closed with named regression tests.
* Public-by-design set: **69** endpoints across **11** categories, 69/69 classified,
  **0 unclassified** (`unguarded_classification.json` → `residual_gaps: []`).
* **11 residual risks (R-01…R-11)** remain open — therefore no finding is declared
  "fully closed with no residual", and `FINAL_DECISION.md` stays **HOLD**.
* Release-blocker register unchanged: DB compatibility (`MIG-EXISTING`), MyPy (71 scoped
  pre-existing errors), frontend contract drift (101 unresolved calls / 28 verb mismatches),
  backend Python dependency advisories (**scan run: 55 known vulnerabilities in 6 runtime
  packages — pillow/pyasn1/urllib3/joserfc/dnspython/certifi, all with available fixes**), and
  service extraction (gated on explicit API-contract + exception/response mapping).
