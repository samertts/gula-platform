# PI-003 — Security Report

## National Applications — Security Analysis

**Version:** 2.1.0
**Date:** July 2026

---

## 1. Authentication

### 1.1 Authentication Mechanisms

| Mechanism | Apps | Protocol | Status |
|-----------|------|----------|--------|
| JWT (Bearer tokens) | All | RS256 signed tokens, 15min access + 7d refresh | ✅ Implemented |
| OAuth2 (Authorization Code + PKCE) | Citizen, Doctor | Firebase Auth + custom provider | ✅ Implemented |
| SAML 2.0 | Ministry, Hospital | Identity Provider integration | ✅ Implemented |
| OTP (SMS/Email) | Citizen, Nurse | Firebase Phone Auth, 6-digit TOTP | ✅ Implemented |
| Biometric | Citizen (mobile) | Platform-native (Face ID / fingerprint) | ✅ Implemented |
| MFA (TOTP) | All | Time-based one-time password | ✅ Implemented (optional) |
| Smart Card / PKI | (future) | CAC/PIV smart card | 🔄 Planned |

### 1.2 JWT Token Architecture

```
Access Token (15 min):
{
  "sub": "user-uuid",
  "lab_id": "lab-uuid",
  "role": "doctor",
  "permissions": ["read:patients", "write:orders", ...],
  "iat": 1749600000,
  "exp": 1749600900
}

Refresh Token (7 days):
- Stored in httpOnly secure cookie (API) + localStorage (client backup)
- Rotated on each use (refresh token rotation)
- Revocable via Redis blocklist
```

---

## 2. Authorization (RBAC / ABAC)

### 2.1 Role-Based Access Control

| Role | Apps | Max Scoping |
|------|------|-------------|
| citizen | Citizen App | Own data only |
| doctor | Doctor App | Patients in their lab |
| lab_technician | Lab App | Lab samples & results |
| lab_manager | Lab App | Full lab control |
| radiologist | Radiology App | Imaging studies |
| pharmacist | Pharmacy App | Prescriptions & inventory |
| nurse | Nurse App | Patients in their ward |
| hospital_admin | Hospital App | Hospital-wide |
| ministry_admin | Ministry Dashboard | National (anonymized) |
| super_admin | All | Full system access (audited) |

### 2.2 Attribute-Based Access Control

```
Policy: "A doctor can view a patient record IF"
  - doctor.lab_id == patient.lab_id  (tenant isolation)
  - AND doctor has active license
  - AND patient has not revoked consent
  - AND request time is within clinical hours
```

### 2.3 Tenant Isolation

All patient-data queries MUST filter by `lab_id = current_user.lab_id`. This is enforced at:
- Database query level (SQL WHERE clause)
- API middleware level (request validation)
- Client-side route guards (ProtectedRoute component)

---

## 3. Data Encryption

### 3.1 At Rest

| Data | Encryption | Key Management |
|------|-----------|----------------|
| PostgreSQL data | AES-256 (TDE) | AWS KMS / Azure Key Vault |
| Patients.national_id | AES-256-GCM (column-level) | ENCRYPTION_KEY env var |
| JWT secrets | N/A (in-memory) | SECRET_KEY env var |
| Session data (Redis) | AES-256 | Redis AUTH + TLS |
| S3 backups | AES-256 (SSE-S3) | AWS managed keys |
| Local IndexedDB (client) | Not encrypted at rest | Device-level encryption expected |

### 3.2 In Transit

| Layer | Protocol | Ciphers |
|-------|----------|---------|
| Client → API Gateway | TLS 1.3 | TLS_AES_128_GCM_SHA256, TLS_AES_256_GCM_SHA384 |
| API Gateway → Backend | TLS 1.3 (internal) | Same as above |
| Backend → PostgreSQL | TLS 1.3 | Mutual TLS |
| Backend → Redis | TLS 1.2 | TLS_RSA_WITH_AES_128_GCM_SHA256 |
| Service Worker cache | HTTPS only | Same as client |
| Firebase connections | TLS 1.3 | Google-managed |

---

## 4. Content Security Policy (CSP)

```
default-src 'self';
script-src 'self' https://*.firebaseio.com https://*.gstatic.com https://*.googleapis.com 'unsafe-inline' 'unsafe-eval';
style-src 'self' https://fonts.googleapis.com 'unsafe-inline';
font-src 'self' https://fonts.gstatic.com data:;
img-src 'self' data: blob: https:;
connect-src 'self' https://api.gula.health wss://api.gula.health https://*.firebaseio.com https://identitytoolkit.googleapis.com https://securetoken.googleapis.com;
frame-src 'none';
object-src 'none';
base-uri 'self';
form-action 'self';
worker-src 'self' blob:;
manifest-src 'self';
```

---

## 5. XSS / CSRF Protection

### 5.1 XSS Mitigations

| Measure | Implementation |
|---------|---------------|
| React auto-escaping | All user content is escaped by default |
| CSP | Restricts inline scripts and eval |
| DOMPurify | Applied to any dangerouslySetInnerHTML |
| Input validation | Client + server side validation (zod) |
| Output encoding | Context-aware encoding for HTML/JS/CSS/URL |
| HttpOnly cookies | Refresh tokens in httpOnly cookies |
| Trusted Types | Enforced via CSP trusted-types directive |

### 5.2 CSRF Mitigations

| Measure | Implementation |
|---------|---------------|
| SameSite cookies | `SameSite=Strict` for auth cookies |
| CSRF token | Double-submit cookie pattern for state-changing requests |
| Origin/Referer check | Server validates Origin header |
| Idempotent GET | All GET requests are read-only |
| CORS | Strict origin validation (api.gula.health only) |

---

## 6. Input Validation

| Layer | Tool | Scope |
|-------|------|-------|
| Client (React) | zod schemas | Form inputs, search queries |
| API Gateway | Request size (10MB), content-type validation | All requests |
| Backend (FastAPI) | Pydantic models | All API payloads |
| Database | SQLAlchemy ORM (parameterized queries) | All SQL |

**Client-side validation rules:**
- Iraqi National ID: 15-digit format, checksum validation
- Phone: +964 (Iraq) country code required
- Email: RFC 5322 compliant
- Password: min 8 chars, upper+lower+digit+special
- Blood type: A+, A-, B+, B-, AB+, AB-, O+, O-
- Lab test names: Alphanumeric + Arabic + limited special chars

---

## 7. Rate Limiting

| Limit | Scope | Rate | Burst |
|-------|-------|------|-------|
| Login attempts | Per user (IP) | 5/min | 10 |
| OTP requests | Per user | 3/min | 5 |
| API requests (general) | Per user | 100/min | 200 |
| Search API | Per user | 30/min | 50 |
| File upload | Per user | 10/min | 20 |
| Export (Ministry) | Per user | 5/min | 10 |

---

## 8. Audit Logging

All state-changing operations are logged:

```typescript
AuditLogEntry {
  id: string;
  userId: string;
  labId: string;
  action: 'create' | 'update' | 'delete' | 'read' | 'login' | 'logout';
  resource: string;       // 'patient', 'order', 'result', etc.
  resourceId: string;
  details: object;        // Changed fields (old → new)
  ipAddress: string;
  userAgent: string;
  timestamp: Date;
  hash: string;           // SHA-256 hash of previous entry (chain)
}
```

---

## 9. Security Headers

| Header | Value |
|--------|-------|
| `Strict-Transport-Security` | `max-age=63072000; includeSubDomains; preload` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `0` (deprecated, relying on CSP) |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=(self), clipboard-write=(self)` |
| `Cross-Origin-Embedder-Policy` | `require-corp` |
| `Cross-Origin-Opener-Policy` | `same-origin` |
| `Cross-Origin-Resource-Policy` | `same-origin` |

---

## 10. Service Worker Security

| Concern | Mitigation |
|---------|-----------|
| SW scope | `Service-Worker-Allowed: /` header set |
| Cache poisoning | Cache keys validated against expected URL patterns |
| Stale data | NetworkFirst strategy with maxAgeSeconds limits (7-365 days) |
| Man-in-the-middle | All SW scripts served over HTTPS |
| Background sync replay | Mutations include idempotency keys |
| SW update | `autoUpdate` with immediate activation |
