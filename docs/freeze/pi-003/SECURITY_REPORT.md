# SECURITY REPORT — PI-003 National Applications Suite

## 1. Authentication Security

### 1.1 JWT Authentication (`shared/auth/jwt.py`, `backend/app/security/auth.py`)

The platform uses a dual-token JWT strategy:

| Token | Lifetime | Storage | Purpose |
|-------|----------|---------|---------|
| Access Token | `JWT_EXPIRE_MINUTES` (default 30 min) | Client memory | API authorization |
| Refresh Token | `REFRESH_TOKEN_EXPIRE_DAYS` (default 30 days) | HTTP-only secure cookie | Silent re-authentication |

**Token structure (`backend/app/security/auth.py:67-74`):**
```python
def build_token_payload(user) -> dict:
    return {
        "user_id": user.id,
        "lab_id": user.lab_id,
        "role": user.role,
        "perm_ver": user.perm_version or 1,
    }
```

**Security properties:**
- Algorithm: HMAC-SHA256 (`config.py:111`)
- Each token includes `jti` (unique ID) for revocation (`auth.py:78`)
- `iat` and `exp` claims enforced on decode (`shared/auth/jwt.py:49`)
- Token blacklist via Redis (`auth.py:43-52`)
- `perm_version` check invalidates all tokens on permission change (`session.py:36-76`)

**Key management (`config.py:101-149`):**
- `SECRET_KEY`: 64+ byte random, hard-fail on weak/missing in production
- `REFRESH_TOKEN_SECRET`: Independent key from access token
- Weak pattern detection (`_is_weak_secret`) rejects `default`, `changeme`, `password`, etc.

### 1.2 OAuth2 / OpenID Connect (`backend/app/security/oauth2_provider.py`)

Full authorization server implementation:

| Endpoint | Function |
|----------|----------|
| `POST /oauth2/authorize` | Authorization request |
| `POST /oauth2/token` | Token exchange |
| `POST /oauth2/introspect` | Token introspection |
| `POST /oauth2/revoke` | Token revocation |
| `GET /oauth2/jwks.json` | JWKS endpoint |
| `GET /oauth2/.well-known/openid-configuration` | OIDC discovery |

**Supported grant types:**
- Authorization Code (with PKCE)
- Client Credentials (machine-to-machine)
- Refresh Token

### 1.3 SAML 2.0 (`backend/app/security/saml_service.py`)

Government SSO integration for Iraq e-Government:

- HTTP-POST binding for SAML response
- Assertion validation: issuer, audience, conditions (NotBefore/NotOnOrAfter), Subject
- Attribute extraction for identity mapping (`saml_service.py:75-84`)
- Metadata endpoint for SP configuration (`saml_service.py:92-97`)

### 1.4 Multi-Factor Authentication (`backend/app/security/mfa_service.py`)

Three MFA methods supported:

| Method | Implementation | Strength |
|--------|---------------|----------|
| TOTP | `shared/auth/mfa.py` | 6-digit, 30s window, SHA-1 |
| WebAuthn / FIDO2 | `shared/auth/webauthn.py` | Hardware-bound, phishing-resistant |
| Backup codes | `shared/auth/mfa.py` | 8 codes, hashed storage, single-use |

MFA session TTL: 10 minutes (`mfa_service.py:28`). Devices managed via
`MFADevice` model with `device_type`, `secret`, `backup_codes`, `is_active`.

### 1.5 Brute Force Protection

| Layer | Mechanism | Threshold | Action |
|-------|-----------|-----------|--------|
| Rate limit | Fixed-window (`rate_limit.py`) | 10/min per IP (auth) | 429 + Retry-After |
| Dynamic blocking | IP block (`rate_limit.py:118-123`) | 5x rate limit | 1h block |
| Account lockout | `perm_version` bump (`session.py`) | 5 failed attempts | 15 min lockout |
| User enumeration | Dummy hash (`auth.py:56`) | N/A | Timing-safe comparison |

## 2. Data Encryption

### 2.1 Encryption at Rest (`backend/app/security/encryption.py`)

```python
from shared.security import encrypt_value, decrypt_value

def encrypt(data: str) -> str:   # AES-256-GCM via Fernet
def decrypt(data: str) -> str:   # Reverse operation
```

**Encrypted fields:**
| Field | Table | Method | Key |
|-------|-------|--------|-----|
| `national_id` | `patients` | AES-256-GCM | `ENCRYPTION_KEY` (32-byte) |
| `national_id_hash` | `patients` | HMAC-SHA256 | `NID_HMAC_KEY` (64-byte) |
| `phone` | `patients` | AES-256-GCM | `ENCRYPTION_KEY` |
| `email` | `lab_users` | AES-256-GCM | `ENCRYPTION_KEY` |
| Local DB cache | Desktop/Mobile | AES-256-GCM | Device-derived key |

### 2.2 Encryption in Transit

| Layer | Protocol | Details |
|-------|----------|---------|
| External | TLS 1.3 | Host nginx termination |
| Internal | Plain (Docker network) | Isolated bridge network |
| Database | TLS 1.2+ | `sslmode=require` in production |
| Redis | AUTH + TLS | `REDIS_PASSWORD` + TLS when configured |

### 2.3 Key Hierarchy (`config.py:101-149`)

```
Master Key (env: ENCRYPTION_KEY)
  ├── Database encryption → AES-256-GCM on sensitive fields
  ├── JWT signing         → SECRET_KEY (HS256)
  ├── Token refresh       → REFRESH_TOKEN_SECRET
  ├── National ID HMAC    → NID_HMAC_KEY
  └── Device bridge HMAC  → DEVICE_HMAC_KEY (services/device_bridge/)
```

All keys are:
- Generated via `secrets.token_urlsafe(64)` (`config.py:106`)
- Never hardcoded in source code
- Protected by `_is_weak_secret()` detection (`config.py:96-98`)
- Validated at startup — hard exit on weak/missing in production

## 3. Audit Logging

### 3.1 Audit Log Implementation

**Model:** `AuditLog` (`app/models/`) — hash-chained, tamper-evident log.
**Service:** `app/services/audit_service.py`

```python
def log_action(db, action, resource_type, resource_id, user_id,
               user_role=None, details=None, lab_id=None):
    previous = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = previous.hash if previous else "0" * 64
    payload = f"{previous_hash}:{timestamp}:{action}:{user_id}:{json.dumps(data)}"
    audit_hash = hashlib.sha256(payload.encode()).hexdigest()
    ...
```

### 3.2 Audited Events

| Category | Events Audited |
|----------|---------------|
| **Authentication** | Login, logout, token refresh, failed login, MFA enrollment |
| **Authorization** | Permission denied, role change, break glass |
| **Patient Data** | Create, read, update, delete of any patient/PII |
| **Clinical** | Order creation, result entry, validation, critical alert |
| **Administration** | User create/deactivate, lab config, feature flags |

### 3.3 Audit Chain Verification

```python
def verify_audit_chain(db):
    entries = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    for i, entry in enumerate(entries):
        # Verify previous_hash link
        expected_previous = entries[i-1].hash if i > 0 else "0" * 64
        assert entry.previous_hash == expected_previous
        # Verify entry hash
        expected_hash = sha256(f"{entry.previous_hash}:{...}".encode()).hexdigest()
        assert entry.hash == expected_hash
    return True  # Chain intact
```

## 4. Tenant Isolation Verification

### 4.1 Database-Level Isolation

Every tenant-scoped entity has a `lab_id` foreign key:

```python
class LabUser(Base):
    __tablename__ = "lab_users"
    id = Column(Integer, primary_key=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True)
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)
```

### 4.2 Query-Level Enforcement

All patient-data queries filter by `lab_id = current_user.lab_id`:

```python
# backend/app/security/dependencies.py:get_current_user
current_user.lab_id  # Set on every authenticated request

# Every route:
db.query(Patient).filter(
    Patient.lab_id == current_user.lab_id,
    Patient.id == patient_id
).first()
```

### 4.3 Cross-Tenant Access Rules

| Scenario | Allowed? | Requirement |
|----------|----------|-------------|
| Read own lab's patients | ✓ | Default |
| Read another lab's patient | ✗ | Requires consent directive |
| Referral between labs | ✓ | Consent + purpose of use = "treatment" |
| National registry lookup | ✓ | Citizen data only (no clinical) |
| Admin across tenants | ✓ | `super_admin` role only |

### 4.4 Isolation Test Coverage

Tenant isolation is verified by:
- `test_tenant_isolation_matrix.py` — matrix of cross-tenant access scenarios
- `test_security.py` — JWT, auth, encryption invariants
- `test_tiers_privilege.py` — privilege escalation prevention
- `test_abac.py` — attribute-based access control rules
- `test_consent.py` — consent enforcement for cross-tenant access

## 5. Security Headers (`backend/app/main.py:518-553`)

| Header | Value | Notes |
|--------|-------|-------|
| `Content-Security-Policy` | `default-src 'self'; script-src 'self' 'unsafe-inline'; ...` | Protects against XSS |
| `X-Content-Type-Options` | `nosniff` | Prevents MIME sniffing |
| `X-Frame-Options` | `DENY` | Prevents clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Legacy XSS filter |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` | HSTS 1 year |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Referrer leakage protection |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` | Feature restriction |
| `Cross-Origin-Opener-Policy` | `same-origin` | COOP isolation |

## 6. Request Security

### 6.1 Input Validation

- **Body size limit:** 10MB (`MaxBodySizeMiddleware`, `main.py:350`)
- **Content-Type:** JSON enforced (Pydantic validation)
- **SQL injection:** Prevented by SQLAlchemy ORM parameterized queries
- **Path traversal:** File attachment paths validated against allowed directory
- **IDOR:** All mutations verify resource ownership via `lab_id`

### 6.2 Rate Limiting (`backend/app/security/rate_limit.py`)

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| Auth (login/register) | 10/min | 60s | Per IP |
| Public (links) | 30/min | 60s | Per IP |
| Authenticated | 60/min | 60s | Per user + IP |
| Admin | 20/min | 60s | Per user + IP |
| Dynamic block | 5x limit exceeded | 1h | IP block |

Rate limiter uses Redis for cross-worker consistency (`rate_limit.py:111-114`).
Returns standard `X-RateLimit-*` headers and `Retry-After`.

## 7. CI Security Scanning

| Tool | Configuration | Runs On |
|------|--------------|---------|
| `bandit` | `-ll -ii` (medium+ confidence, high+ severity) | CI (`security-scan` job) |
| `safety` | CVE database | CI |
| `gitleaks` | Pre-commit secret scanning | CI + pre-commit hook |
| `trivy` | Container image scan | CI (`build-and-push` job) |
| `hadolint` | Dockerfile linting | CI |

## 8. Security Compliance Matrix

| Requirement | Status | Evidence |
|------------|--------|----------|
| JWT authentication | ✓ | `shared/auth/jwt.py`, `app/security/auth.py` |
| OAuth2 / OIDC | ✓ | `app/security/oauth2_provider.py` |
| SAML 2.0 SSO | ✓ | `app/security/saml_service.py` |
| MFA (TOTP + WebAuthn) | ✓ | `app/security/mfa_service.py`, `shared/auth/mfa.py` |
| RBAC (9+ roles) | ✓ | `app/security/rbac.py`, `shared/rbac/` |
| ABAC (attribute-based) | ✓ | `app/security/abac.py` |
| Encryption at rest | ✓ | `app/security/encryption.py` |
| TLS 1.3 | ✓ | Host nginx configuration |
| Audit chain (hash) | ✓ | `app/services/audit_service.py` |
| Tenant isolation | ✓ | `lab_id` FK on all tenant entities |
| Rate limiting | ✓ | `app/security/rate_limit.py` |
| Security headers | ✓ | `middleware` in `app/main.py:518` |
| Break glass | ✓ | Emergency access workflow |
| Token revocation | ✓ | Redis blacklist (`auth.py:43`) |
| Permission versioning | ✓ | `perm_version` (`session.py`) |
