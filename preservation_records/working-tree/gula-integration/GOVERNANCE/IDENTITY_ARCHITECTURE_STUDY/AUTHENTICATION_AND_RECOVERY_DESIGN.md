# GULA National Identity Architecture Study — Authentication & Account Recovery Design

**Program:** National Identity, Citizen Registration, Authentication & Document Intelligence — Master Architecture Study (READ-ONLY)
**Repository:** `/home/samertts/workspace/projects/gula-integration` · **Branch:** `integration/gula-unification-v1` @ `2827c1ff1032918aa2541aa0b47bb7f2e5d6cac0`
**Document status:** ARCHITECTURE STUDY / RECOMMENDATION — **not an implementation authorization**
**Release posture:** `FINAL_DECISION.md` remains **HOLD**; D-020 and D-021 remain `PENDING_APPROVAL`. This document does not change them.
**Workstream:** E (Authentication and Account Recovery), with inputs from A, J, M, P.

---

## 0. Evidence convention (applies to every section)

| Label | Meaning in this study |
|---|---|
| `VERIFIED_IN_SOURCE` | Implementation located and read directly in repository source. |
| `TEST_VERIFIED` | A dedicated test module exists targeting the capability. **Test presence is not a claim that the test was executed or passed in this study.** |
| `PARTIAL` | Source exists but is incomplete, unwired, defective, or config-gated. |
| `SOURCE_PRESENT` | Code exists but is not on the primary live authentication path. |
| `DORMANT` | Code exists with no production callers / commented-out wiring. |
| `NOT_IMPLEMENTED` | No real implementation; stub or documentation-only. |
| `BLOCKED` | Requires missing configuration or external dependency to function. |
| `UNVERIFIABLE` | Cannot be confirmed without runtime execution, a database, or external authorization. |

Every claim below is derived from **static source inspection only**. Nothing here asserts that an endpoint was exercised, a test passed, or a database was contacted during this study. Where a router is registered in `factory.py`, the wording is "routed/wired in source," never "runtime verified."

Source paths are relative to the repository root unless stated otherwise. `file:line` references were verified during this study.

---

## 1. Scope and governing owner decisions

This document covers authentication (proving the account holder), credential lifecycle, session management and account recovery. It explicitly **does not** decide patient-record access (see §12).

Owner-approved product decisions applicable here:

| Decision | Constraint applied |
|---|---|
| D-IDENTITY-01 | National Identity Card number is **not** a password or default credential; it is a protected matching attribute. |
| D-IDENTITY-09 | Zero mandatory per-authentication external service cost. No mandatory paid SMS/email OTP; no dependency on temporary free third-party services. |
| D-IDENTITY-11 | Authentication ≠ patient-record authorization. Every record access is a separate decision (user, role, organization/facility, relationship, guardian authority, legal basis, purpose, consent, audit). |
| D-IDENTITY-08 | Facility-assisted registration must never let staff acquire the citizen's private authentication credentials. |

These are **product-design decisions only**. They do not authorize implementation or change the release status.

---

## 2. Current implementation inventory (evidence-backed)

### 2.1 Password hashing — `VERIFIED_IN_SOURCE`

| Item | Evidence |
|---|---|
| bcrypt via passlib | `shared/auth/passwords.py` — `hash_password` / `verify_password` |
| Anti-enumeration dummy hash | `backend/app/routes/login.py:81-118` (dummy bcrypt hash for unknown accounts) |
| Service-account API keys | `backend/app/security/service_accounts.py:63-89` (bcrypt-hashed); rotation `:92-102`, validation `:105-116`, revocation `:119-128`; table in migration `20260716_0015_auth_security_tables.py:114-130` |
| Dependencies | `backend/requirements.txt:13-14` (`passlib[bcrypt]>=1.7.4`, `bcrypt>=4.1.3,<4.2.0` — floor pinned for passlib 1.7.4 compatibility); lock `bcrypt==4.1.3` |

No Argon2 implementation or dependency was found. This is an observation, not a defect per policy.

### 2.2 JWT access and refresh tokens — `VERIFIED_IN_SOURCE`

| Item | Evidence |
|---|---|
| Token creation/decode | `shared/auth/jwt.py:7-9` (`joserfc`), `create_access_token` `:31-44`, `create_refresh_token` `:47-57`, `decode_access_token` `:60-73` |
| Wrappers & revocation | `backend/app/security/auth.py` — issuance/decode wrappers; Redis JTI blacklist `:54-63`; refresh decode with blacklist check `:120-130` |
| Algorithm | `backend/app/config.py:178` — `JWT_ALGORITHM = "HS256"` (symmetric) |
| Access TTL | `backend/app/config.py:181` — 15-minute default (`JWT_EXPIRE_MINUTES`, legacy fallback `:182-185`) |
| Refresh secret | `backend/app/config.py:188-200` — separate `REFRESH_TOKEN_SECRET`, dev random fallback `:189-196`, hard exit in production if unset `:190-191`; TTL default 7 days constrained to 1–30 `:200-202` |
| Fail-closed dependency | `backend/app/security/dependencies.py:52-69` — HTTP 503 on `SecurityStoreUnavailable` |

Token type is distinguished by a `type` claim (e.g. `oauth2_access` / `oauth2_refresh` in `backend/app/security/oauth2_provider.py:122,136`). Revocation state lives in Redis, not in a database table.

### 2.3 Refresh-token rotation — `VERIFIED_IN_SOURCE`

- `backend/app/routes/mobile.py:77+` — `POST /auth/refresh`: issues new tokens, then blacklists the old refresh JTI with a **30-second grace window** (concurrency tolerance). Inference: the grace window permits limited replay, a deliberate availability/security trade-off that must be documented if retained.
- `backend/app/identity/services/authentication_service.py:107-133` — NIAM-equivalent rotation.

**Reusability finding:** rotation logic is duplicated in two code paths. Consolidation is a `RECOMMENDED` change, not an owner-approved decision, and is outside this study's implementation scope.

### 2.4 Redis blacklist / token revocation — `VERIFIED_IN_SOURCE`

- `backend/app/security/auth.py:54-63` — key format `blacklist:jti:{jti}`; `:120-130` — refresh decode checks blacklist.
- `backend/app/security/dependencies.py:52-69` — membership checked on authenticated requests; store unavailable → 503 (fail-closed).
- `backend/app/security/redis_client.py:200-213` — `security_store` abstraction and degraded policy.

Revocation is entirely dependent on Redis availability; by design the system fails closed rather than accepting a revoked token. Capacity and disaster-recovery implications are carried to `CAPACITY_AND_COST_MODEL.md` and `RISKS_AND_OPEN_QUESTIONS.md`.

### 2.5 Login — `VERIFIED_IN_SOURCE` (routed/wired in source)

- `backend/app/routes/login.py:50-244` — `POST /login`, registered via `core_routes` at `backend/app/factory.py:565-568`, included `:578-579`.
- Controls present: rate limiting (`login_protection`), lockout, dummy-hash + generic 401 for unknown users, auth cookies, audit logging.
- Privileged-role MFA gate `:141-160`: `PRIVILEGED_ROLES = {"master_admin","ministry_admin","province_admin"}`; missing MFA → `403 login_denied_mfa_required` plus audit.
- A separate NIAM login exists in `backend/app/identity/services/authentication_service.py`.

### 2.6 Logout — `VERIFIED_IN_SOURCE`

- `backend/app/routes/login.py:247-299` — `POST /logout`: blacklists **both** access and refresh JTI and increments `perm_version` for immediate invalidation. NIAM equivalent in `backend/app/identity/services/authentication_service.py`.

### 2.7 Session management — `PARTIAL` / `SOURCE_PRESENT`

| Item | Evidence / status |
|---|---|
| Session inspection | `backend/app/routes/login.py:302-325` — `GET /session` |
| Session model | `backend/app/identity/models/session.py:11-47` — includes workspace-binding fields |
| Session API | `backend/app/identity/api/sessions.py:12-44` — list/revoke |
| Session service | `backend/app/identity/services/session_service.py` — `bind_workspace`, `unbind_workspace`, `get_workspace_bound_sessions`, `enforce_max_concurrent_sessions` |
| Zero-trust session tracking | `backend/app/security/zero_trust.py:14-45` — in-memory, revocation **commented out**, no production callers → `DORMANT` |

`enforce_max_concurrent_sessions` exists as a service but its invocation at login was **not confirmed** in source → `UNVERIFIABLE` in this static study. It is carried to the open-questions register.

### 2.8 Account recovery — `PARTIAL` (two confirmed defects)

- `backend/app/routes/password_reset.py:42-54` — generic forgot-password response (anti-enumeration preserved).
- `backend/app/routes/password_reset.py:80-93` — `POST /auth/change-password`:
  - **Defect A-REC-01 (verified):** line `:91` calls `bump_perm_version(db, current_user.id)` but the signature at `backend/app/security/session.py:40-47` is `bump_perm_version(user: LabUser, db: Session, *, ...)`. Arguments are transposed; the call would access `user.perm_version` on a `Session`. **Verified directly against both files during this study.**
  - **Defect A-REC-02 (verified source structure):** `backend/app/routes/mobile.py` also registers `/auth/change-password`; the `mobile` router is included at `factory.py:575` / `:578-579`, **before** `password_reset` at `:631-632`. FastAPI resolves the first matching route, so the `password_reset` implementation is shadowed. The broken line may therefore be unreachable, but route intent is ambiguous and duplicated.
  - **Password policy mismatch:** `backend/app/routes/register.py:23-35` requires ≥12 complex characters; `backend/app/services/mobile_service.py:123-130` accepts 8.

### 2.9 OTP — two different flows that must not be conflated

| Flow | Status | Evidence |
|---|---|---|
| Citizen-lifecycle "OTP" | `NOT_IMPLEMENTED` | `backend/app/identity/lifecycle/services.py:391-403` — `send_otp` / `verify_otp` only set timestamps and `status = "otp_sent"` / `"otp_verified"`. **No code is generated, stored, or compared.** Routes at `backend/app/identity/lifecycle/routes.py:357,367` accept no OTP code parameter. |
| Verification-code flow | `VERIFIED_IN_SOURCE` / `PARTIAL` | `backend/app/routes/verification.py:35,106-128,131+` — six-digit code, SHA-256 digest in `security_store`, 15-minute TTL, generic response `:102`; demo code revealed only in demo/test environments. |

The verification-code flow is suitable for **phone/email ownership verification**, not for an OTP login factor. **There is no OTP-based login in source.**

### 2.10 TOTP / MFA — `VERIFIED_IN_SOURCE`; `TEST_VERIFIED`

- `backend/app/security/mfa_service.py:39-73` — TOTP enable/verify via `MFAService`.
- `shared/auth/mfa.py:9-22` — `pyotp` TOTP/HOTP with `valid_window=1`; `:25-39` — backup-code generation with SHA-256 hashing and HMAC comparison.
- Routes `backend/app/routes/mfa.py:55-153` (`/mfa/*`), registered `factory.py:628-629`.
- Dependency `pyotp>=2.10.0` at `backend/requirements.txt:30` (lock `PyOTP==2.10.0`) — **absent from `pyproject.toml`** (see §2.14).
- Tests present: `backend/tests/test_security.py` (MFA assertions) — presence only, not executed here.

### 2.11 WebAuthn / passkeys — `PARTIAL` (real implementation with confirmed defects)

- `shared/auth/webauthn.py:7-19` — real `webauthn` 3.x primitives; registration options `:27-50`, registration verification `:53-70`, authentication options `:73-86`, authentication verification `:89-108`.
- `backend/app/security/mfa_service.py:85-159` — challenge generation/caching/consumption; `:123` accepts device types `["webauthn","fido2","passkey"]` — i.e. **"passkey" is a stored `MFADevice.device_type` label, not a separate protocol.**
- Model `backend/app/models/mfa_device.py:11-40` — tables `mfa_devices`, `mfa_sessions`; FK `user_id → lab_users.id` **only** — no NIAM `User` FK. Migration `20260716_0015_auth_security_tables.py:41-76`.

**Confirmed defects (verified directly against source during this study):**

| ID | Defect | Evidence |
|---|---|---|
| A-WEB-01 | Hardcoded `RP_ID = "gula.health"`, `RP_ORIGIN = "https://app.gula.health"` — not configurable per environment/tenant; breaks localhost, staging and multi-domain national deployment. | `shared/auth/webauthn.py:22-24` |
| A-WEB-02 | Challenge serialization: options serialized via `json.dumps(dataclasses.asdict(options), default=str)` (`:50`, `:86`); cached as `options["challenge"]` in `mfa_service.py:94,135`; verification calls `expected_challenge.encode()` (`:61`, `:99`). The bytes→str→bytes round-trip is highly likely to produce a different challenge value. | `shared/auth/webauthn.py:50,61,86,99`; `backend/app/security/mfa_service.py:94,135` |
| A-WEB-03 | Cache failure swallowed → empty challenge: `mfa_service.py:93-106` (registration) and `:133-153` (authentication) catch cache exceptions and continue with `challenge = ""`; verification then runs against an empty expected challenge. | `backend/app/security/mfa_service.py:93-106,133-153` |

Tests present cover only `begin_*` endpoints; **no full registration/authentication round-trip test was found** → end-to-end correctness `UNVERIFIABLE`.

**Documentation divergence:** docs (`IDENTITY_ARCHITECTURE.md:65,114-117,530-532`; `backend/app/identity/__init__.py:15,25`) describe passkeys/FIDO2/smart-card/biometric as first-class capabilities. Source implements CTAP2/WebAuthn with those strings as device labels only.

### 2.12 OAuth2 / OIDC — `PARTIAL` (provider only; OIDC client absent)

- Routes `backend/app/routes/oauth2.py`, registered `factory.py:634-635`: `POST /oauth2/token`, `/authorize`, `/revoke`, `/introspect`; grants `authorization_code`, `client_credentials`, `refresh_token` (`:142-158`); PKCE **S256 required** (`:114-117`); discovery `:206-213`.
- `backend/app/security/oauth2_provider.py:89-109` — OIDC ID token (HS256, `iss/sub/aud/exp/iat/auth_time/jti/nonce`); token helpers `:112-148`; decode `:151-169`.
- **AUTH-OIDC-01 (verified):** `get_jwks()` at `oauth2_provider.py:172-178` returns an empty list with a warning, because signing is symmetric HMAC. Discovery advertises a `jwks_uri` yielding `{"keys":[]}` — a conforming OIDC relying party cannot validate ID tokens via JWKS.
- **Confirmed absent:** `authlib`, `pyoidc`/`oidc`, `msal`, `pysaml2`/`python3-saml`, `OAuth2Session`, `argon2`, `PyJWT` — no dependency declaration and no source import. **This is a provider, not an OIDC login consumer**; there is no external-IdP client.
- No full grant-flow test found → `UNVERIFIABLE`.

### 2.13 SAML — `PARTIAL` / `BLOCKED` (validation primitive, not SSO)

- `backend/app/security/saml_service.py:37-71` — signature validation with safe algorithms only, `require_x509=True`, pinned IdP signing cert, issuer/audience validation; uses `signxml` + `defdefusedxml` (dependency `signxml>=4.2.0`, `defusedxml` — `requirements.txt:12,17`).
- `backend/app/routes/saml.py:47-82` — `POST /acs`:
  - `503 "SAML SSO is not configured"` if `SAML_IDP_ISSUER` / `SAML_IDP_SIGNING_CERT_PEM` absent (`:53-54`) → `BLOCKED` without config.
  - Validates response/signature/assertion (`:56-68`), extracts `name_id`/`email` (`:70-74`).
  - **Returns only booleans** `{"validated": True, "name_id_present": ..., "email_present": ..., "relay_state_present": ...}` (`:77-82`). **No user lookup, no session, no token issued.**
- Router registered `factory.py:637-638`; metadata generation near `saml.py:44`.
- **Inference:** this cannot authenticate a user end-to-end. No SAML ACS test found → `UNVERIFIABLE`.

### 2.14 Risk-based / adaptive authentication — `SOURCE_PRESENT`, not enforced (`PARTIAL`/`DORMANT`)

- `backend/app/identity/adaptive_auth/services.py` + routes — risk-scoring service registered under `/niam/adaptive-auth`; referenced only from its own routes, **not** from `AuthenticationService.login`.
- `backend/app/services/risk_based_auth_service.py` — **no production callers**; referenced only by `backend/tests/test_risk_based_auth.py`.
- `backend/app/security/zero_trust.py:14-45` — dormant (§2.7).
- `backend/app/identity/services/risk_based_auth` / device-trust modules and `backend/app/identity/models/device.py` `trust_score` provide scoring primitives.
- **Inference:** risk signals are computed but **not consumed by the login decision**. This is the largest "source-present but inert" gap.
- Tests present: `backend/tests/test_risk_based_auth.py`, `backend/tests/test_device_trust.py` (presence only).

### 2.15 Lockout / rate limiting — `VERIFIED_IN_SOURCE`; `TEST_VERIFIED`

- `backend/app/security/login_protection.py` — rate limiting / lockout (failed-attempt tracking, thresholds); applied by `backend/app/routes/login.py:50-118`.
- `backend/app/security/rate_limit.py` — rate-limit primitives; `backend/tests/test_login_protection.py` present.
- Exact storage/backoff semantics are `UNVERIFIABLE` without runtime inspection.

### 2.16 Anti-enumeration — `PARTIAL`

Controls present: dummy hash + generic 401 (`login.py:81-118`), generic forgot-password response (`password_reset.py:42-54`), generic verification response (`verification.py:102`).

State-leaking distinct responses (verified): `login.py:138` (`403 "Account verification required before login."`), `login.py:157-160` (MFA-required 403), `login.py:162+` (deactivated-lab branch). These are necessary for UX but create an account-state oracle for an unauthenticated caller. The trade-off must be documented and accepted or redesigned; it must not be assumed safe.

### 2.17 Trusted devices / device revocation — `SOURCE_PRESENT`; revocation `PARTIAL`

- `backend/app/identity/models/device.py:11-39` — `is_active`, `trust_score`.
- `backend/app/identity/api/devices.py:11-54` — device list/revoke endpoints.
- `backend/app/identity/services/device_service.py:79-85` — `revoke_device` **only sets `is_active = False`**; no session termination and no JTI blacklist. **Inference:** already-issued tokens and active sessions survive device revocation.
- `backend/tests/test_device_trust.py`, `backend/tests/identity/test_auth_session_security_phase2.py` present.

### 2.18 Dependency-manifest inconsistency — `PARTIAL`

| Manifest | State |
|---|---|
| `backend/requirements.txt:13-18,27,29-30` | Declares `passlib[bcrypt]`, `bcrypt`, `joserfc`, `cryptography`, `signxml`, `redis`, `webauthn>=3.0.0`, `pyotp>=2.10.0` |
| `backend/requirements-lock.txt:6,48,53,69` | `bcrypt==4.1.3`, `PyOTP==2.10.0`, `joserfc==1.7.6`, `webauthn==3.0.0` |
| `backend/pyproject.toml:21-32` | Main dependencies **omit `webauthn` and `pyotp`**; `webauthn>=2.0.0` is a **dev extra** at `:42`; `pyotp` absent entirely |

**Inference:** a `[project.dependencies]`-only install can lack MFA/WebAuthn runtime libraries. The two manifests also disagree on the WebAuthn major version (`>=3.0.0` vs `>=2.0.0`). Resolution is a packaging change, outside this study's scope.

---

## 3. Target authentication architecture (recommendations)

### 3.1 Design principles

1. **Zero mandatory per-authentication external cost (D-IDENTITY-09).** The primary path must use credentials verified locally: WebAuthn/passkeys and TOTP. No paid SMS or email OTP is required for any authentication event.
2. **Phishing-resistant first.** Prefer origin-bound public-key credentials (WebAuthn/passkeys) over shared secrets. Passwords, if retained, are a fallback, not the primary factor for privileged accounts.
3. **Authentication is not authorization (D-IDENTITY-11).** A successful login establishes an account session only; every patient-record access is separately authorized (see §12).
4. **No citizen credential capture by staff (D-IDENTITY-08).** Assisted registration may verify documents and enroll hardware-bound credentials, but staff must never learn or hold the citizen's secrets or complete a login on the citizen's behalf.
5. **Sovereign, replaceable components.** Prefer self-hosted, open-source primitives already present (passlib/bcrypt, `pyotp`, `webauthn`, `joserfc`, Redis). No vendor-specific identity service; no new orchestration engine.
6. **Fail closed on revocation state.** Preserve the existing 503-on-store-unavailable behaviour; do not serve authentication decisions from stale revocation data.

### 3.2 Mechanism comparison (evidence-based, not benchmark claims)

| Mechanism | Phishing resistance | Per-login external cost | Device/internet requirement | Source state | Target role |
|---|---|---|---|---|---|
| WebAuthn / passkeys (platform or roaming authenticator) | High (origin-bound) | Zero | Android/iOS/Windows/Linux/browser platform authenticators or security key; no internet beyond GULA itself | `PARTIAL` with defects A-WEB-01..03 (§2.11) | **Primary credential** where device supports it |
| TOTP (`pyotp`, `valid_window=1`) | Medium (code can be phished) | Zero | Any device with a TOTP app or hardware token; clock accuracy required | `VERIFIED_IN_SOURCE` (§2.10) | **Required second factor / primary fallback** |
| Recovery codes (SHA-256 hashed, HMAC compare) | Low (bearer secret) | Zero | Printed or stored offline | `VERIFIED_IN_SOURCE` (§2.10) | **Break-glass recovery**, single-use, audited |
| Password (bcrypt/passlib) | Low | Zero | Any device | `VERIFIED_IN_SOURCE` (§2.1) | **Optional fallback only**; uniform ≥12-character policy; privileged accounts require MFA |
| Citizen-lifecycle "OTP" | n/a | n/a | n/a | `NOT_IMPLEMENTED` stub (§2.9) | **Must not be treated as an OTP login factor.** Rename/redefine to "verification status" or implement real OTP separately |
| Verification code (SHA-256 in `security_store`, 15-min TTL) | Low–medium | Zero local; **SMS/email would introduce per-message cost** | Phone/email ownership | `VERIFIED_IN_SOURCE` (§2.9) | **Channel-ownership verification only**, not an authentication factor; no mandatory paid delivery |
| SMS / email OTP | Low | **Non-zero if paid provider used** | Phone number / email / network | `NOT_IMPLEMENTED` as login factor | **Excluded from mandatory path.** Operator-funded SMS gateway, if ever approved, is optional and costed separately |
| OAuth2/OIDC provider | Depends on client | Zero locally | Relying party support | `PARTIAL`; empty JWKS (AUTH-OIDC-01) | **Internal provider only** until asymmetric keys + JWKS are implemented |
| SAML ACS | n/a | n/a | n/a | Validation-only, `BLOCKED` absent config (§2.13) | **Not an SSO login.** Retain as assertion-validation primitive only |

### 3.3 Platform and device compatibility

| Platform | WebAuthn platform authenticator | Passkey sync / cross-device | TOTP | Notes |
|---|---|---|---|---|
| Android (including low-cost devices) | Generally available via platform authenticator on supported devices; **device capability must be detected at enrollment** | Cross-device via QR/adjacent-phone flows where supported by the platform | Available via app | Some low-cost devices lack a platform authenticator or biometric sensor; TOTP + recovery codes must remain viable. No assumption that every citizen owns a smartphone. |
| iOS | Platform authenticator available on supported versions | iCloud Keychain passkey sync where user opts in | Available via app | Cross-device flows depend on Apple ecosystem; must not be the only path. |
| Windows | Windows Hello where configured | Roaming security key / cross-device where supported | Available via app/desktop | Enterprise workstations may enforce their own authenticator policy. |
| Linux | Browser + roaming security key; platform authenticator support varies | Roaming key | Available via app/desktop | Do not rely on a platform authenticator being present. |
| Web browsers | WebAuthn where browser + OS support it; origin binding requires stable RP ID/origin (see A-WEB-01) | Via platform/provider | Web TOTP or external app | A single hardcoded RP ID/origin cannot serve localhost, staging and multiple national domains. |
| Feature phone / no smartphone | Not available | Not available | Not available | Assisted registration with staff-observed document capture; **staff never receive credentials**. Use printed recovery codes or an institution-held hardware token issued under audited custody rules. Authentication for such citizens must still incur no mandatory paid per-login external service. |

**Inference from source:** a national deployment with multiple origins cannot use the current hardcoded WebAuthn configuration. Making RP ID/origin configurable is a prerequisite for any multi-domain rollout.

---

## 4. Target authentication flows (design-level, not implemented)

### 4.1 Enrollment

1. Establish the account identity (separate from NHID and civil identity — D-IDENTITY-01/02).
2. Detect available authenticators on the device; offer WebAuthn platform authenticator or security key first.
3. Require at least **two** enrolled credential types before granting privileged roles: e.g. WebAuthn + TOTP, or TOTP + recovery codes where no WebAuthn-capable device exists.
4. Generate single-use recovery codes (hashed at rest) and require the user to acknowledge safe storage.
5. Record device registration (`is_active`, `trust_score`) with audit.
6. Never require the National Identity Card number as a credential (D-IDENTITY-01).

### 4.2 Login (target)

1. Accept identifier; apply rate limiting and lockout (`login_protection`).
2. Use dummy-hash verification for unknown identifiers to equalize timing.
3. Verify the presented credential: WebAuthn assertion (preferred) or TOTP/password fallback.
4. Evaluate risk signals from the existing `adaptive_auth` / `risk_based_auth_service` / device-trust primitives **in the login decision** (currently inert — §2.14). Risk may step up the required factor; it must not silently deny care-critical access, and emergency access is governed separately (D-IDENTITY-03, §12).
5. Issue access + refresh tokens with the existing type claim; enforce the 15-minute access TTL and 7-day refresh TTL (§2.2).
6. Bind the session to the selected workspace (NIAM session model) and record the device.
7. Audit successful and failed attempts with consistent, minimal account-state disclosure.

### 4.3 Session rotation and revocation

- Preserve refresh rotation with old-JTI blacklisting; review the 30-second grace window and document its replay tolerance (§2.3).
- On logout: blacklist both JTIs and bump `perm_version` (existing behaviour, `login.py:247-299`).
- On password/credential change: bump `perm_version` **with the correct call signature** (fix A-REC-01) and terminate other sessions deliberately.
- Device revocation must invalidate associated sessions **and** blacklist their tokens — current `device_service.py:79-85` only flips a flag (§2.17).
- Enforce `enforce_max_concurrent_sessions` at login once its invocation is confirmed/implemented (currently `UNVERIFIABLE`, §2.7).
- Keep the fail-closed 503 behaviour when the security store is unavailable (§2.4).

### 4.4 Lost device

1. User authenticates with a remaining factor (TOTP or recovery code) or completes assisted identity proofing at an authorized facility (D-IDENTITY-08, no credential capture).
2. Revoke the lost device's sessions and blacklist its tokens (fix §2.17 gap).
3. Enroll a replacement credential; invalidate unused recovery codes.
4. Audit the entire sequence.

### 4.5 Lost all authenticators / account takeover (ATO) response

- **Recovery:** step-up via an independently verified official identity attribute (D-IDENTITY-01) and/or supervised facility-assisted proofing, with two-person approval for privileged accounts. No SMS/email OTP dependency. Every recovery is audited and notifies the account holder through a previously verified channel where one exists.
- **ATO response:** immediately blacklist all JTIs, bump `perm_version`, revoke all devices/sessions, freeze privileged roles pending review, preserve forensic audit, and trigger the breach-response process in `SECURITY_AND_PRIVACY_THREAT_MODEL.md`. Re-issuance requires re-proofing, not a password reset alone.
- **Residual risk:** if all authenticators and the verified channel are lost simultaneously, recovery depends on facility-assisted proofing; its legal authority and evidence requirements are `LEGAL_REVIEW_REQUIRED` (Workstream K).

---

## 5. Residual dependencies and operational costs (D-IDENTITY-09)

| Dependency | Mandatory per login? | Cost / note |
|---|---|---|
| Local bcrypt/JWT/JTI verification | Yes | Compute only; no external fee |
| Self-hosted Redis (`security_store`) | Yes, for revocation/blacklist and verification codes | Self-hosted infrastructure cost; fail-closed if unavailable. Must be sized for HA/DR (see capacity model) |
| WebAuthn / TOTP / recovery codes | Yes (primary factors) | No per-login external fee; device cost is the citizen's or facility's |
| SMS / email delivery | **No** | Excluded from mandatory path. Any operator-funded gateway is optional, separately approved and costed |
| External IdP / OIDC / SAML | **No** | Provider/integration primitives only; no external service dependency in the primary path |
| Government identity API / NFC | **No** | Not assumed available (Workstream G/K). Used only for optional step-up if legally authorized and technically verified |

**Conclusion:** the target architecture can satisfy D-IDENTITY-09 with zero mandatory per-authentication external service cost, **provided** the self-hosted security store is highly available and the WebAuthn/configuration and revocation defects in §2 are fixed. Those fixes are prerequisites, not achievements of this study.

---

## 6. Separation from patient authorization (D-IDENTITY-11)

A successful authentication establishes *who is operating the account*. It does **not** grant access to any patient record. Each patient-data access must separately evaluate:

- user identity and account state;
- role and privilege;
- organization and facility scope;
- patient relationship (including guardian authority where applicable);
- legal basis and purpose of access;
- consent requirements where applicable;
- immutable audit.

This boundary is implemented by the existing authorization/consent surfaces (`backend/app/security/consent_dep.py`, `backend/app/national/security/consent_enforcement.py`, `backend/app/routes/consent.py`, `backend/app/legal/consent.py`, `backend/app/identity/api/consents.py`) and is further specified in `SECURITY_AND_PRIVACY_THREAT_MODEL.md` and `API_AND_INTEGRATION_CONTRACTS.md`. Weaknesses found in those surfaces are carried there, not silently assumed resolved by authentication.

---

## 7. Test requirements (design-level; no tests were run in this study)

| Level | Required coverage |
|---|---|
| Unit | Password hashing/dummy hash; JWT type claims and TTL; TOTP window and backup-code hashing; challenge serialization round-trip; WebAuthn RP/origin configuration; `bump_perm_version` signature; recovery-code single-use. |
| Integration | Enrollment → login → refresh rotation → logout for each credential type; change-password path with no route shadowing; device revocation kills sessions and tokens; max-concurrent sessions enforced; fail-closed 503 on store outage. |
| Security | WebAuthn full registration/authentication round-trip (currently missing); replay of used challenges; refresh-token replay during/after grace window; anti-enumeration oracle testing; lockout bypass; ATO response drill. |
| Cross-platform | Android (low-cost device), iOS, Windows, Linux, browsers; WebAuthn unavailable fallback; assisted enrollment with no credential capture. |
| Operational | Redis outage, key rotation, secret absence in production (hard-exit behaviour), audit completeness, recovery drill. |

Use synthetic accounts and synthetic identity data only. Do not claim E2E verification from contract-envelope tests (see `TESTING_AND_ACCEPTANCE_STRATEGY.md`).

---

## 8. Architecture decisions register

Each decision below is classified per the study mandate. None is an owner approval.

| ID | Decision | Problem | Alternatives | Advantages | Disadvantages / risks | Legal | Security | Ops / cost | Dependencies | Failure scenario | Reversibility | Evidence | Classification |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AUTH-01 | WebAuthn/passkeys as primary credential where device supports it | Phishable shared secrets | Password only; TOTP only; WebAuthn-first | Origin-bound, phishing-resistant, no per-login fee | Device capability gaps; defect A-WEB-01..03 must be fixed | None identified beyond general data-protection duties | Strong | Enrollment support; device replacement | Configurable RP ID/origin; challenge fix; full round-trip test | Broken challenge → all WebAuthn logins fail | Reversible: retain TOTP/password fallback | §2.11; `shared/auth/webauthn.py` | `RECOMMENDED` |
| AUTH-02 | TOTP + recovery codes as universal fallback | No smartphone / no platform authenticator | Mandatory SMS OTP; paid email OTP | Zero external cost; broad device support | TOTP phishable; recovery codes are bearer secrets | None identified | Medium; protect codes at rest | Low | Existing `pyotp` + hashed backup codes | Lost codes → assisted recovery | Reversible | §2.9-2.10 | `OWNER_APPROVED` (D-IDENTITY-09) |
| AUTH-03 | No mandatory paid SMS/email OTP | Cost + dependency + phone-number exclusion | Paid SMS as primary | Citizen inclusion (no phone/email required) | Some citizens need assisted paths | Data-protection duties for any channel | Avoids SMS interception | Zero per-login external fee | Assistive registration model (D-IDENTITY-08) | Citizens without any device need facility path | Reversible | §5; D-IDENTITY-09 | `OWNER_APPROVED` (D-IDENTITY-09) |
| AUTH-04 | Asymmetric signing keys + populated JWKS before OIDC reliance | Empty JWKS breaks conforming RPs | Keep HS256 and hide JWKS | Standards-conformant ID tokens | Key management/rotation complexity | None identified | Positive | HSM/KMS or file-based keys | `oauth2_provider.py:172-178` | RP cannot validate ID tokens | Reversible | §2.12 | `SECURITY_REVIEW_REQUIRED` |
| AUTH-05 | Wire risk signals into login decision | Risk engines computed but inert | Leave inert; delete them | Step-up without new engine | Policy errors could block care | Purpose/legal-basis checks required | Positive | Low; reuse existing modules | `adaptive_auth`, `risk_based_auth_service`, device trust | False positives deny access | Reversible | §2.14 | `RECOMMENDED` |
| AUTH-06 | Device revocation must kill sessions + blacklist tokens | Current flag-only revocation leaves live tokens | Keep flag-only | Prevents token survival after theft | More state coordination | None identified | Positive | Low | `device_service.py:79-85`, session/JTI store | Revoked device still accesses data | Reversible | §2.17 | `SECURITY_REVIEW_REQUIRED` |
| AUTH-07 | Single change-password path + uniform ≥12-char policy | Shadowed route, 8-char mismatch, signature defect | Keep both | Removes two confirmed defects | Migration of callers | None identified | Positive | Low | `password_reset.py:80-93`, `mobile.py`, `factory.py:575,631-632` | Runtime error / policy bypass | Reversible | §2.8 | `RECOMMENDED` |
| AUTH-08 | NIAM WebAuthn credential ownership extended to non-lab users | MFA FK only to `lab_users.id` | Lab-only WebAuthn | Citizens/other identities can use passkeys | Model/migration change required | None identified | Positive | Migration cost | `mfa_device.py:11-40` | Non-lab accounts cannot enroll passkeys | Reversible via migration | §2.11 | `NEEDS_OWNER_DECISION` |
| AUTH-09 | External IdP / SAML SSO integration | Source is validation-only / provider-only | Build full SSO client | Enterprise federation | New external dependency conflicts with zero-cost/inclusion goals | **Data-sharing/legal authority required** | New attack surface | Integration + assurance cost | Legal authority, IdP contract, config | Unauthorized external authentication | Reversible | §2.12-2.13 | `BLOCKED_BY_EXTERNAL_DEPENDENCY` |

---

## 9. Open questions

1. Is `enforce_max_concurrent_sessions` actually invoked at login? (§2.7 — `UNVERIFIABLE` statically.)
2. Should the 30-second refresh grace window be retained, shortened, or replaced with a single-use rotation ledger? (§2.3.)
3. Which national domains/origins must WebAuthn support, and who owns RP ID/origin configuration? (A-WEB-01.)
4. What is the lawful, auditable procedure for facility-assisted re-proofing after loss of all authenticators? (`LEGAL_REVIEW_REQUIRED`, Workstream K.)
5. Should asymmetric keys be generated/held in a self-hosted KMS or file-based store, and who rotates them? (AUTH-04.)
6. How should the account-state oracle from distinct 403 responses be reduced without harming legitimate UX? (§2.16.)
7. Is the `webauthn` / `pyotp` dependency-manifest divergence a packaging defect to fix before any MFA rollout? (§2.18.)

---

## 10. Cross-references

- `MASTER_ARCHITECTURE.md` — identity/account/authentication separation and capability map.
- `NATIONAL_IDENTITY_MODEL.md` — account identity vs. civil identity vs. NHID.
- `DOCUMENT_VERIFICATION_DESIGN.md` — optional step-up verification; OCR is not proof of identity.
- `SECURITY_AND_PRIVACY_THREAT_MODEL.md` — ATO, insider, lost-device, offline-sync threats.
- `API_AND_INTEGRATION_CONTRACTS.md` — auth contract shapes, idempotency, rate limits, error codes.
- `OFFLINE_AND_LOW_CONNECTIVITY_DESIGN.md` — no offline device makes a final identity-verification decision.
- `TESTING_AND_ACCEPTANCE_STRATEGY.md` — test levels; no E2E claim from contract-envelope tests.
- `IMPLEMENTATION_ROADMAP.md` — Phase 4 (Authentication and account recovery) and Phase 10 (Security and privacy hardening).
