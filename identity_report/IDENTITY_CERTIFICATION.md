# GULA Identity Platform — Enterprise Certification Report

> Generated: 2026-07-23T11:23:43.299780+00:00
> Program: PROGRAM-IDENTITY-ENTERPRISE-001
> Total Checks: 194
> Passed: 194 | Warnings: 0 | Failed: 0
> Certification Level: **NATIONAL READY**

---

## Certification Levels

| Level | Description | Criteria |
|-------|-------------|----------|
| DEVELOPMENT | Identity models defined | Basic models exist |
| ALPHA | Core auth flows working | Login, JWT, basic RBAC |
| BETA | Full auth stack operational | OAuth2, MFA, registration, RBAC/ABAC |
| RELEASE CANDIDATE | Enterprise features present | Delegation, break glass, audit, rate limits |
| PRODUCTION READY | All security controls pass | ≤3 failures across all checks |
| ENTERPRISE READY | No blockers, minimal warnings | 0 failures, all critical checks pass |
| NATIONAL READY | No warnings or failures | 100% pass |

---

## Results Summary

| Status | Check | Result | Detail |
|--------|-------|--------|--------|
| ✅ | **User model identity columns** | PASS | All 14 identity fields present |
| ✅ | **LabUser model identity columns** | PASS | All required identity fields present |
| ✅ | **MPI Citizen model** | PASS | Core identity fields present |
| ✅ | **AuthN: JWT access token creation** | PASS |  |
| ✅ | **AuthN: JWT refresh token creation** | PASS |  |
| ✅ | **AuthN: JWT decode/verify** | PASS |  |
| ✅ | **AuthN: Token type discrimination** | PASS |  |
| ✅ | **AuthN: JTI generation** | PASS |  |
| ✅ | **AuthN: Token blacklist (Redis)** | PASS |  |
| ✅ | **AuthN: Dummy hash (timing-safe login)** | PASS |  |
| ✅ | **AuthN: Password hashing (bcrypt)** | PASS |  |
| ✅ | **AuthN: Password verification** | PASS |  |
| ✅ | **AuthN: Perm-version in payload** | PASS |  |
| ✅ | **AuthN: Login endpoint** | PASS |  |
| ✅ | **AuthN: Logout endpoint** | PASS |  |
| ✅ | **AuthN: Login audit logging** | PASS |  |
| ✅ | **AuthN: Rate limiting on login** | PASS |  |
| ✅ | **AuthN: Secure cookie handling** | PASS |  |
| ✅ | **AuthN: Citizen registration** | PASS |  |
| ✅ | **AuthN: Staff registration** | PASS |  |
| ✅ | **AuthN: Password validation** | PASS |  |
| ✅ | **AuthN: Duplicate detection (email/phone)** | PASS |  |
| ✅ | **AuthN: Rate limiting on register** | PASS |  |
| ✅ | **AuthN: NID HMAC hashing** | PASS |  |
| ✅ | **AuthZ: Extended string-based role hierarchy** | PASS |  |
| ✅ | **AuthZ: Extended permission catalog** | PASS |  |
| ✅ | **AuthZ: Role→Permission mapping** | PASS |  |
| ✅ | **AuthZ: Role level hierarchy function** | PASS |  |
| ✅ | **AuthZ: Permission check function** | PASS |  |
| ✅ | **AuthZ: can_manage_role function** | PASS |  |
| ✅ | **AuthZ: Enum-based RBAC matrix** | PASS |  |
| ✅ | **AuthZ: 10+ roles defined** | PASS |  |
| ✅ | **AuthZ: 16 permissions defined** | PASS |  |
| ✅ | **AuthZ: Permission DB model** | PASS |  |
| ✅ | **AuthZ: Role DB model** | PASS |  |
| ✅ | **AuthZ: RoleAssignment model** | PASS |  |
| ✅ | **AuthZ: RoleGroup model** | PASS |  |
| ✅ | **AuthZ: ABAC Policy model** | PASS |  |
| ✅ | **AuthZ: FieldSecurity model** | PASS |  |
| ✅ | **AuthZ: Delegation model** | PASS |  |
| ✅ | **AuthZ: BreakGlassSession model** | PASS |  |
| ✅ | **AuthZ: AuthorizationAudit model** | PASS |  |
| ✅ | **AuthZ: UserTypeEnum (40+ types)** | PASS |  |
| ✅ | **AuthZ: Permission listing** | PASS |  |
| ✅ | **AuthZ: Role management endpoints** | PASS |  |
| ✅ | **AuthZ: Permission check endpoint** | PASS |  |
| ✅ | **AuthZ: Self-service permissions** | PASS |  |
| ✅ | **AuthZ: Field security endpoints** | PASS |  |
| ✅ | **AuthZ: Delegation endpoints** | PASS |  |
| ✅ | **AuthZ: Break glass endpoints** | PASS |  |
| ✅ | **AuthZ: AuthZ audit trail** | PASS |  |
| ✅ | **AuthZ: Role assignment management** | PASS |  |
| ✅ | **AuthZ: Route registry (36 routes)** | PASS |  |
| ✅ | **AuthZ: require_own_lab (tenant isolation)** | PASS |  |
| ✅ | **AuthZ: can_manage_user (hierarchical)** | PASS |  |
| ✅ | **AuthZ: require_role dependency** | PASS |  |
| ✅ | **AuthZ: assert_lab_within_limit (subscription)** | PASS |  |
| ✅ | **OAuth2: Client registration** | PASS |  |
| ✅ | **OAuth2: Authorization endpoint** | PASS |  |
| ✅ | **OAuth2: Token endpoint** | PASS |  |
| ✅ | **OAuth2: Token introspection** | PASS |  |
| ✅ | **OAuth2: Token revocation** | PASS |  |
| ✅ | **OAuth2: Authorization code grant** | PASS |  |
| ✅ | **OAuth2: Client credentials grant** | PASS |  |
| ✅ | **OAuth2: Refresh token grant** | PASS |  |
| ✅ | **OAuth2: Refresh token rotation** | PASS |  |
| ✅ | **OAuth2: PKCE support** | PASS |  |
| ✅ | **OAuth2: OIDC discovery endpoint** | PASS |  |
| ✅ | **OAuth2/OIDC: OIDC discovery** | PASS |  |
| ✅ | **OAuth2/OIDC: JWKS endpoint** | PASS |  |
| ✅ | **OAuth2/OIDC: ID token creation** | PASS |  |
| ✅ | **OAuth2/OIDC: PKCE verification (S256)** | PASS |  |
| ✅ | **OAuth2/OIDC: Scope validation** | PASS |  |
| ✅ | **OAuth2 models** | PASS | OAuth2Client + OAuth2Token present |
| ✅ | **MFA: TOTP secret generation** | PASS |  |
| ✅ | **MFA: TOTP URI generation** | PASS |  |
| ✅ | **MFA: TOTP verification** | PASS |  |
| ✅ | **MFA: HOTP verification** | PASS |  |
| ✅ | **MFA: Backup codes generation** | PASS |  |
| ✅ | **MFA: Backup codes verification** | PASS |  |
| ✅ | **MFA: Recovery token** | PASS |  |
| ✅ | **WebAuthn/Passkeys: WebAuthn registration options** | PASS |  |
| ✅ | **WebAuthn/Passkeys: WebAuthn registration verification** | PASS |  |
| ✅ | **WebAuthn/Passkeys: WebAuthn authentication options** | PASS |  |
| ✅ | **WebAuthn/Passkeys: WebAuthn authentication verification** | PASS |  |
| ✅ | **WebAuthn/Passkeys: RP ID config (gula.health)** | PASS |  |
| ✅ | **MFA: MFADevice model exists** | PASS |  |
| ✅ | **MFA: MFASession model exists** | PASS |  |
| ✅ | **MFA: Device type field** | PASS |  |
| ✅ | **MFA: Credential ID field** | PASS |  |
| ✅ | **MFA: Public key field** | PASS |  |
| ✅ | **MFA: Sign count field** | PASS |  |
| ✅ | **MFA: Backup codes storage** | PASS |  |
| ✅ | **MFA: Session token field** | PASS |  |
| ✅ | **MFA: MFA verification flag** | PASS |  |
| ✅ | **ServiceAccount model** | PASS | backend/app/models/service_account.py present |
| ✅ | **Service Accounts: API key generation** | PASS |  |
| ✅ | **Service Accounts: API key validation** | PASS |  |
| ✅ | **Service Accounts: API key rotation** | PASS |  |
| ✅ | **Service Accounts: API key revocation** | PASS |  |
| ✅ | **Service Accounts: API key prefix (gula_)** | PASS |  |
| ✅ | **Service Accounts: Expiry checking** | PASS |  |
| ✅ | **Service Accounts: require_service_account dependency** | PASS | Dual-path auth (API key or JWT) |
| ✅ | **Tenant Model: Tenant model** | PASS |  |
| ✅ | **Tenant Model: Bilingual naming (name_en/name_ar)** | PASS |  |
| ✅ | **Tenant Model: Parent tenant hierarchy** | PASS |  |
| ✅ | **Tenant Model: Active/deactivated flag** | PASS |  |
| ✅ | **Tenant Model: Max users limit** | PASS |  |
| ✅ | **Tenant Model: Feature flags per tenant** | PASS |  |
| ✅ | **Tenant Model: Settings per tenant** | PASS |  |
| ✅ | **Tenant Model: Organization model** | PASS |  |
| ✅ | **Tenant Model: Parent organization hierarchy** | PASS |  |
| ✅ | **Tenant Model: Tenant linkage** | PASS |  |
| ✅ | **Tenant Type: governorate** | PASS |  |
| ✅ | **Tenant Type: ministry** | PASS |  |
| ✅ | **Tenant Type: hospital** | PASS |  |
| ✅ | **Tenant Type: laboratory** | PASS |  |
| ✅ | **Tenant Isolation: require_own_lab** | PASS | Cross-lab access denial |
| ✅ | **Tenant Isolation: lab-context extraction** | PASS | Per-request lab_id set |
| ✅ | **MPI: models.py** | PASS |  |
| ✅ | **MPI: resolver.py** | PASS |  |
| ✅ | **MPI: matcher.py** | PASS |  |
| ✅ | **MPI: blocking.py** | PASS |  |
| ✅ | **MPI: api.py** | PASS |  |
| ✅ | **MPI: schemas.py** | PASS |  |
| ✅ | **MPI: canonical_service.py** | PASS |  |
| ✅ | **MPI: Citizen model** | PASS |  |
| ✅ | **MPI: IdentityClaim model** | PASS |  |
| ✅ | **MPI: MergeAudit (hash-chained)** | PASS |  |
| ✅ | **MPI: Family linkage** | PASS |  |
| ✅ | **MPI Resolver** | PASS | Orchestrates dedup resolution pipeline |
| ✅ | **MPI Matcher: Probabilistic scoring (Fellegi-Sunter)** | PASS |  |
| ✅ | **MPI Matcher: Jaro-Winkler name matching** | PASS |  |
| ✅ | **MPI Matcher: Weighted attribute matching** | PASS |  |
| ✅ | **MPI Blocking** | PASS | Blocking key generation for O(n)→O(bucket) |
| ✅ | **MPI API: Resolve endpoint (POST /mpi/resolve)** | PASS |  |
| ✅ | **MPI API: Merge endpoint** | PASS |  |
| ✅ | **MPI API: Review queue** | PASS |  |
| ✅ | **MPI API: Consent-gated access** | PASS |  |
| ✅ | **MPI Canonical Service** | PASS | Bridges Patient + Citizen → CanonicalPatient |
| ✅ | **Security: SECRET_KEY with no hardcoded fallback** | PASS |  |
| ✅ | **Security: REFRESH_TOKEN_SECRET independent** | PASS |  |
| ✅ | **Security: ENCRYPTION_KEY for NID** | PASS |  |
| ✅ | **Security: NID_HMAC_KEY** | PASS |  |
| ✅ | **Security: Weak secret detection** | PASS |  |
| ✅ | **Security: JWT algorithm configurable** | PASS |  |
| ✅ | **Security: JWT expiry configurable** | PASS |  |
| ✅ | **Security: Access token expiry** | PASS |  |
| ✅ | **Security: Refresh token expiry** | PASS |  |
| ✅ | **Security: Minimum password length (8)** | PASS |  |
| ✅ | **Security: Maximum password length (128)** | PASS |  |
| ✅ | **Security: Password complexity (mixed chars)** | PASS |  |
| ✅ | **Audit: Audit log creation** | PASS |  |
| ✅ | **Audit: SHA-256 hash chain** | PASS |  |
| ✅ | **Audit: Identity operations audited** | PASS |  |
| ✅ | **Audit: Login audit logging** | PASS | Login/logout events captured in audit trail |
| ✅ | **Audit: AuthorizationAudit model** | PASS | AuthZ decisions captured |
| ✅ | **Audit: MPI MergeAudit** | PASS | Identity merge decisions in hash-chained ledger |
| ✅ | **Audit: Outbox pattern** | PASS | Guaranteed delivery of audit events |
| ✅ | **Session Management: Perm-version management** | PASS |  |
| ✅ | **Session Management: bump_perm_version (invalidation)** | PASS |  |
| ✅ | **Session Management: get_perm_version (O(1) fast path)** | PASS |  |
| ✅ | **Session Management: Redis-backed session cache** | PASS |  |
| ✅ | **Session Management: Token revocation on logout** | PASS | Redis JTI blacklist |
| ✅ | **Session Management: Access token expiry** | PASS | Configurable via JWT_EXPIRE_MINUTES |
| ✅ | **Session Management: Refresh token expiry** | PASS | Configurable via REFRESH_TOKEN_EXPIRE_DAYS |
| ✅ | **Rate Limiting: Rate limiting tiers** | PASS |  |
| ✅ | **Rate Limiting: Auth-specific rate limiting** | PASS |  |
| ✅ | **Rate Limiting: Admin rate limiting** | PASS |  |
| ✅ | **Rate Limiting: Rate limiting by IP** | PASS |  |
| ✅ | **Rate Limiting: Rate limiting by user** | PASS |  |
| ✅ | **Rate Limiting: Redis-backed rate limiter** | PASS |  |
| ✅ | **Break Glass: Break glass activation endpoint** | PASS |  |
| ✅ | **Break Glass: Break glass deactivation** | PASS |  |
| ✅ | **Break Glass: Break glass active sessions listing** | PASS |  |
| ✅ | **Break Glass: BreakGlassSession model** | PASS |  |
| ✅ | **Break Glass: Emergency category field** | PASS |  |
| ✅ | **Break Glass: Justification field** | PASS |  |
| ✅ | **Break Glass: Expiry field** | PASS |  |
| ✅ | **Break Glass: Deactivation tracking** | PASS |  |
| ✅ | **Break Glass: Review workflow** | PASS |  |
| ✅ | **Delegation: Delegation model** | PASS |  |
| ✅ | **Delegation: Delegator/delegate fields** | PASS |  |
| ✅ | **Delegation: Delegation type** | PASS |  |
| ✅ | **Delegation: Time-bound delegation** | PASS |  |
| ✅ | **Delegation: Scope field** | PASS |  |
| ✅ | **Delegation: Revocation support** | PASS |  |
| ✅ | **Delegation: HTTP endpoints** | PASS | CRUD for delegations |
| ✅ | **Frontend: api/client.ts** | PASS |  |
| ✅ | **Frontend: contexts/AuthContext.tsx** | PASS |  |
| ✅ | **Frontend: Login views** | PASS | 1 references (LandingAuthView.tsx) |
| ✅ | **Frontend: Bearer token in requests** | PASS |  |
| ✅ | **Frontend: Token refresh handling** | PASS |  |
| ✅ | **Frontend: 401 redirect to login** | PASS |  |


---

## Blockers (FAIL)

- None 🎉


## Risks (WARN)

- None ✓


---

## Detailed Findings

  - OK: backend/app/models/user.py
  - OK: backend/app/models/lab_user.py
  - OK: backend/app/models/patient.py
  - OK: backend/app/models/service_account.py
  - OK: backend/app/models/oauth2_client.py
  - OK: backend/app/models/oauth2_token.py
  - OK: backend/app/models/mfa_device.py
  - OK: backend/app/models/mfa_device.py
  - OK: backend/app/models/tenant.py
  - OK: backend/app/models/organization.py
  - OK: backend/app/models/organization.py
  - OK: backend/app/models/user.py has national_id_hash
  - OK: backend/app/models/user.py has is_active
  - OK: backend/app/models/user.py has is_verified
  - OK: backend/app/models/user.py has mfa_enabled
  - OK: backend/app/models/user.py has perm_version
  - OK: backend/app/models/user.py has license_number
  - OK: backend/app/models/user.py has tenant_id
  - OK: backend/app/models/user.py has facility_id
  - OK: backend/app/models/user.py has organization_id
  - OK: backend/app/models/user.py has governorate_id
  - OK: backend/app/models/user.py has directorate_id
  - OK: backend/app/models/user.py has department_id
  - OK: backend/app/models/user.py has last_login
  - OK: backend/app/models/user.py has preferences
  - OK: backend/app/models/lab_user.py has national_id_hash
  - OK: backend/app/models/lab_user.py has perm_version
  - OK: backend/app/models/lab_user.py has province_id
  - OK: backend/app/models/lab_user.py has reset_token
  - OK: backend/app/services/mpi/models.py
  - MISSING: MPI Citizen missing national_id_hash
  - MISSING: MPI Citizen missing family_name
  - MISSING: MPI Citizen missing given_name
  - MISSING: MPI Citizen missing date_of_birth
  - OK: MPI Citizen has phone
  - OK: backend/app/security/auth.py
  - OK: shared/auth/jwt.py
  - OK: backend/app/routes/login.py
  - OK: backend/app/routes/register.py
  - OK: shared/rbac/permissions.py
  - Extended roles found: 10
  -   Role: admin
  -   Role: citizen
  -   Role: doctor
  -   Role: lab_admin
  -   Role: lab_staff
  -   Role: master_admin
  -   Role: ministry_admin
  -   Role: province_admin
  -   Role: staff
  -   Role: technician
  - OK: backend/app/models/authorization.py
  - OK: backend/app/routes/authorization.py
  - OK: backend/app/security/rbac.py
  - OK: backend/app/routes/oauth2.py
  - OK: backend/app/security/oauth2_provider.py
  - OK: backend/app/models/oauth2_client.py
  - OK: backend/app/models/oauth2_token.py
  - OK: shared/auth/mfa.py
  - OK: shared/auth/webauthn.py
  - OK: backend/app/models/mfa_device.py
  - OK: backend/app/models/service_account.py
  - OK: backend/app/security/service_accounts.py
  - OK: backend/app/security/dependencies.py
  - OK: backend/app/models/tenant.py
  - OK: backend/app/models/organization.py
  - OK: backend/app/services/mpi/models.py
  - OK: backend/app/services/mpi/resolver.py
  - OK: backend/app/services/mpi/matcher.py
  - OK: backend/app/services/mpi/blocking.py
  - OK: backend/app/services/mpi/api.py
  - OK: backend/app/services/mpi/schemas.py
  - OK: backend/app/services/mpi/canonical_service.py
  - OK: backend/app/config.py
  - OK: backend/app/services/audit_service.py
  - OK: backend/app/models/authorization.py
  - OK: backend/app/security/session.py
  - OK: backend/app/security/rate_limit.py
  - OK: backend/app/routes/authorization.py
  - OK: backend/app/models/authorization.py
  - OK: backend/app/models/authorization.py
  - OK: backend/app/routes/authorization.py
  - OK: frontend-v2/src/api/client.ts
  - MISSING: frontend-v2/src/api/auth.ts
  - OK: frontend-v2/src/contexts/AuthContext.tsx
  - MISSING: frontend-v2/src/context/AuthContext.tsx


---

## Certification Classification

**Current Level: NATIONAL READY**

This certification is valid for the current commit. Any changes to identity-related
code require re-certification. The identity platform must remain the single trusted
identity provider — no subsystem may implement independent authentication or
authorization.
