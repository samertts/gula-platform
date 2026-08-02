# Enterprise Certification — Identity & Access Management v1.0

**Platform:** GULA National Health Platform
**Date:** 2026-08-02
**Level:** Enterprise Certification (P4 program)

## Scope

NIAM identity platform, authentication (MFA/WebAuthn/OTP), authorization
(RBAC/ABAC), session management, and live verification.

## 1. Identity Platform (NIAM) — CERTIFIED

- Module `backend/app/identity/` — password, passkeys, FIDO2, OTP, OAuth2,
  OIDC, smart cards (`identity/__init__.py:23`).
- Credential model incl. `otp_secret`, `biometric` types
  (`identity/models/credential.py:13-18`).
- Session model with expires_at, mfa_used, revoked
  (`identity/models/session.py:11`); permission-version JWT invalidation on
  role/password change (`security/session.py bump_perm_version`).
- Password reset flow: `routes/password_reset.py`.

## 2. Multi-Factor Authentication — CERTIFIED (live)

- Privileged-login MFA challenge: `POST /login` → `mfa_pending` →
  `POST /mfa-verify` (single-use session + rate limit; ASVS 2.4).
- **DB-driven privileged-role MFA** (P4 fix `48b0cc69`): roles flagged
  `requires_mfa` enforced for auditor, security_officer, pathologist +
  master/ministry admins — verified by
  `test_db_driven_mfa_roles_cover_auditor` and live role E2E (160/160).
- TOTP with backup codes: `routes/mfa.py`; **WebAuthn/FIDO2 passkeys**
  register/authenticate; adaptive/risk-based MFA challenges
  (`identity/adaptive_auth/` — `AdaptiveMFASession`, risk-scored).

## 3. RBAC — CERTIFIED (live)

- 25-role model canonical in `shared/rbac/permissions.py`, mirrored in
  backend (`admin_service.VALID_ROLES`), frontend (`permissions/index.ts`),
  TS `UserRole` — lockstep enforced by 10 parity tests
  (`test_role_parity.py` + `roleParity.test.ts`).
- 16 enterprise roles verified live: login, MFA enrollment enforcement,
  role round-trip, per-route 403 isolation (P4 role E2E 160/160).
- Ministry/directorate-scoped roles (`core/bootstrap/roles.py:27,43`).

## 4. ABAC & Consent — CERTIFIED

- Attribute enforcement: consent dependency `require_consent`
  (`security/consent_dep.py`, 403 `consent_required`), break-glass emergency
  override (`:150`, `BREAK_GLASS_POLICY.md`).
- Consent model: no open-ended consents — `expires_at NOT NULL`, API cap 72h
  (`models/consent.py`); grant/revoke/check audited (`routes/consent.py`).

## 5. Session & Token Security — CERTIFIED

- Access/refresh token separation, secure cookies in production
  (`secure=IS_PRODUCTION`), Redis-backed invalidation, rate limiting
  (auth: 10/min default), startup fail-fast on weak secrets.

## Verdict

**IDENTITY & ACCESS MANAGEMENT: CERTIFIED v1.0** — NIAM platform with
FIDO2/TOTP/OTP, DB-driven privileged MFA, 25-role RBAC parity, ABAC consent
with break-glass, audited session lifecycle — verified live via 160-check
role E2E and dedicated regression tests.
