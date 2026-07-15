# Security — National Healthcare Platform

## Authentication (JWT)

### Token Format

The platform uses **JSON Web Tokens (JWT)** for API authentication.

**Header:**
```json
{
  "alg": "HS256",
  "typ": "JWT"
}
```

**Payload:**
```json
{
  "sub": "user_id",
  "lab_id": 1,
  "role": "doctor",
  "permissions": ["patient:read", "patient:write", "medication:prescribe"],
  "facility_id": "FAC001",
  "purpose_of_use": "treatment",
  "iat": 1700000000,
  "exp": 1700086400,
  "jti": "unique-token-id"
}
```

### Token Lifecycle

| Token Type | Lifetime | Storage | Refresh |
|-----------|----------|---------|---------|
| Access Token | 2 hours | Client memory | Via refresh token |
| Refresh Token | 30 days | HTTP-only cookie | Via login |
| Break Glass Token | 4 hours | Client memory | Via break glass workflow |
| Service Token | 1 year | Server env | Manual rotation |

### Key Management

- `SECRET_KEY` — 64+ byte random, stored in `.env`, never hardcoded
- `REFRESH_TOKEN_SECRET` — separate key from access token
- `ENCRYPTION_KEY` — 32-byte key for AES-256-GCM
- `NID_HMAC_KEY` — separate key for national ID hashing
- `DEVICE_HMAC_KEY` — separate key for device bridge HMAC

### Token Validation

All protected endpoints verify:
1. Token signature (HMAC-SHA256)
2. Token expiry (`exp` claim)
3. Token not blacklisted (Redis set of revoked JWT IDs)
4. User account active
5. Lab/tenant active
6. Purpose of use valid for requested operation

---

## Authorization (RBAC + ABAC)

### Role-Based Access Control (RBAC)

The platform implements a dual RBAC/ABAC model.

**RBAC Module:** `app/national/security/rbac.py`  
**ABAC Module:** `app/national/security/abac.py`

### Roles

| Role | Scope | Description |
|------|-------|-------------|
| `super_admin` | System | Full system access, all tenants |
| `national_admin` | National | National-level administration |
| `facility_admin` | Facility | Single facility administration |
| `chief_medical_officer` | Facility | Clinical leadership |
| `department_head` | Department | Department management |
| `attending_physician` | Patient panel | Patient care |
| `resident` | Assigned patients | Supervised care |
| `nurse` | Ward/unit | Nursing care |
| `pharmacist` | Facility | Medication management |
| `lab_technician` | Lab | Laboratory operations |
| `radiologist` | Facility | Imaging interpretation |
| `medical_records` | Facility | Records management |
| `billing` | Facility | Financial operations |
| `read_only` | Assigned scope | View-only access |
| `emergency` | Temporary | Break glass access |
| `patient` | Self | Patient portal access |

### Permissions (42 defined)

| Permission | Description |
|-----------|-------------|
| `patient:read` | Read patient demographics |
| `patient:write` | Update patient demographics |
| `patient:merge` | Merge patient records |
| `patient:delete` | Soft-delete patient |
| `ehr:read` | Read EHR records |
| `ehr:write` | Write EHR records |
| `ehr:delete` | Delete EHR records |
| `medication:prescribe` | Create medication orders |
| `medication:dispense` | Dispense medications |
| `medication:administer` | Administer medications |
| `allergy:read` | Read allergy data |
| `allergy:write` | Record allergies |
| `condition:read` | Read conditions |
| `condition:write` | Record conditions |
| `careplan:read` | Read care plans |
| `careplan:write` | Create/update care plans |
| `clinical_note:read` | Read clinical notes |
| `clinical_note:write` | Write clinical notes |
| `clinical_note:sign` | Sign clinical notes |
| `immunization:read` | Read immunization records |
| `immunization:write` | Record immunizations |
| `encounter:read` | Read encounters |
| `encounter:write` | Create/update encounters |
| `referral:read` | Read referrals |
| `referral:write` | Create/manage referrals |
| `referral:accept` | Accept incoming referrals |
| `admission:write` | Manage admissions |
| `discharge:write` | Manage discharges |
| `transfer:write` | Manage transfers |
| `bed:assign` | Assign beds |
| `schedule:read` | View schedules |
| `schedule:write` | Manage schedules |
| `terminology:read` | Read terminology |
| `terminology:write` | Manage terminology |
| `quality:read` | Read quality indicators |
| `quality:write` | Manage quality indicators |
| `report:read` | Read reports |
| `report:generate` | Generate reports |
| `audit:read` | Read audit logs |
| `admin:system` | System administration |
| `admin:tenant` | Tenant administration |
| `break_glass` | Emergency access override |

### Attribute-Based Access Control (ABAC)

ABAC adds context-aware decisions beyond role checks:

**Evaluated Attributes:**
- **Subject:** user role, department, facility, clearance level
- **Resource:** resource type, sensitivity level, patient VIP status, patient minor status
- **Action:** read, write, delete, sign, administer
- **Environment:** time of day, location (on-site/remote), emergency mode
- **Purpose of Use:** treatment, payment, operations, research, public health

**ABAC Rules (examples):**
- A nurse can read medications for patients on their assigned ward
- A resident can write clinical notes only when cosigned by attending
- Only chief_medical_officer can read VIP patient records
- Patient data access for research requires explicit consent directive
- Break glass access requires immediate notification and 24-hour review

---

## Tenant Isolation

### Model-Level Isolation

Every tenant-scoped entity carries a `lab_id` foreign key:

```python
class TenantMixin:
    lab_id = Column(Integer, ForeignKey("labs.id"), nullable=False, index=True)
```

### Query-Level Filtering

All tenant-scoped queries automatically filter by `lab_id`:

```python
# Via middleware — injected into every query
db.query(Entity).filter(Entity.lab_id == current_user.lab_id)
```

### Shared Data

The following data is **shared across tenants** (not tenant-isolated):
- National identity (Citizen, Patient, Encounter) — shared national registry
- Reference data (governorates, terminology, ICD codes) — global standards
- Practitioners — practitioners may work across multiple facilities
- Organizations — healthcare organization registry

### Cross-Tenant Access

Cross-tenant data access (e.g., referral across facilities) requires:
1. Explicit consent from the patient
2. Purpose of use = "treatment"
3. Audit trail recording both source and target tenant
4. Minimum necessary data sharing (only relevant clinical data)

---

## Audit Logging

### Audit Log Model

**Table:** `audit_logs` (hash-chained)  
**Module:** `app/national/security/audit.py`

### Audit Events

All of the following are audited:

| Category | Events |
|----------|--------|
| **Patient Access** | Any read of patient demographics, EHR, or clinical data |
| **Data Mutations** | Create, update, delete of any clinical record |
| **Authentication** | Login, logout, token refresh, failed login |
| **Authorization** | Denied access, permission elevation, role change |
| **Sensitive Actions** | Break glass, VIP access, minor data access |
| **Administrative** | User creation/deactivation, tenant config changes |
| **Clinical** | Medication administration, lab result verification, discharge |
| **Identity** | Patient merge, identity resolution, health number assignment |

### Hash Chain Integrity

Each audit entry is linked to the previous entry via a hash chain:

```python
def create_audit_entry(action, user_id, data, db):
    previous = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    previous_hash = previous.hash if previous else "0" * 64
    payload = f"{previous_hash}:{timestamp}:{action}:{user_id}:{json.dumps(data, sort_keys=True)}"
    audit_hash = hashlib.sha256(payload.encode()).hexdigest()

    entry = AuditLog(
        action=action,
        user_id=user_id,
        data=data,
        previous_hash=previous_hash,
        hash=audit_hash,
    )
    db.add(entry)
    db.commit()
```

### Tamper Detection

```python
def verify_audit_chain(db):
    entries = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    for i, entry in enumerate(entries):
        expected_previous = entries[i-1].hash if i > 0 else "0" * 64
        if entry.previous_hash != expected_previous:
            return False, f"Chain broken at entry {entry.id}"
        payload = f"{entry.previous_hash}:{entry.timestamp}:{entry.action}:{entry.user_id}:{json.dumps(entry.data, sort_keys=True)}"
        expected_hash = hashlib.sha256(payload.encode()).hexdigest()
        if entry.hash != expected_hash:
            return False, f"Hash mismatch at entry {entry.id}"
    return True, "Chain intact"
```

---

## Encryption at Rest

### Database Encryption

| Data Type | Encryption | Method |
|-----------|-----------|--------|
| National ID | HMAC-SHA256 hash | `national_id_hash` — one-way, salted |
| Patient names | Plaintext (transit TLS) | Encrypted at storage level |
| Clinical notes | Plaintext (transit TLS) | Encrypted at storage level |
| Attachments | AES-256-GCM | Per-file encryption key |
| Health number | Plaintext | Public identifier (IQxxxxxxxx) |
| Phone numbers | Plaintext | Marked as PII in audit |
| Email addresses | Plaintext | Marked as PII in audit |
| Audit logs | Hash-chain integrity | Not encrypted, integrity-protected |

### Storage Encryption

- **PostgreSQL:** Transparent Data Encryption (TDE) at filesystem level
- **Object Storage (MinIO/S3):** Server-side encryption with AES-256
- **Backups:** GPG-encrypted with `backup_encryption_key`

### Key Hierarchy

```
Master Key (HSM / env var)
  ├── Database encryption key → PostgreSQL TDE
  ├── Storage encryption key → MinIO/S3 SSE
  ├── Backup encryption key → GPG backup encrypt
  ├── JWT signing key → SECRET_KEY
  ├── Token refresh key → REFRESH_TOKEN_SECRET
  ├── National ID HMAC key → NID_HMAC_KEY
  └── Device bridge HMAC key → DEVICE_HMAC_KEY
```

---

## FHIR Security

### FHIR API Security

All FHIR endpoints require:
1. **JWT authentication** — Bearer token in Authorization header
2. **Scope validation** — FHIR-specific scopes (patient/*.read, user/*.write)
3. **Smart-on-FHIR compliance** — token introspection for registered apps

### FHIR Consent

- Patient consent directives are checked before returning FHIR resources
- `Consent` resource enforcement via `app/national/security/consent_enforcement.py`
- Opt-out patients have restricted data in FHIR responses
- Minimum necessary filtering applied per FHIR query

### FHIR Audit

- Every FHIR API access is logged to the audit trail
- Search queries are logged with parameters
- Bulk data exports require elevated privileges and special audit

---

## API Security

### Transport Security

- **TLS 1.3** — all external traffic
- **HSTS** — Strict-Transport-Security header with 1-year max-age
- **API Gateway** — TLS termination at host nginx, internal traffic on Docker network

### Security Headers

Set by `SecurityHeadersMiddleware` in `app/main.py`:

| Header | Value |
|--------|-------|
| `Content-Security-Policy` | `default-src 'self'` |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
| `Cache-Control` | `no-store` (for patient data) |

### Rate Limiting

**Module:** `app/firewall/`

| Endpoint Category | Rate Limit | Burst |
|------------------|------------|-------|
| Authentication | 10/min per IP | 20 |
| Patient data read | 100/min per user | 200 |
| Patient data write | 50/min per user | 100 |
| FHIR API | 60/min per app | 120 |
| Streaming API | 30/min per user | 60 |
| Admin API | 20/min per user | 40 |
| Public (health) | 1000/min per IP | 5000 |

### Request Validation

- **Max body size:** 10 MB (enforced by `MaxBodySizeMiddleware`)
- **Content-Type enforcement:** application/json for all POST/PUT
- **Input sanitization:** Pydantic models validate all input
- **SQL injection:** SQLAlchemy ORM prevents raw SQL injection
- **Path traversal:** File paths validated against allowed patterns

### Security Incident Response

| Event | Response |
|-------|----------|
| Failed login > 5/min | Account lockout for 15 min |
| Break glass activated | Immediate notification to facility admin |
| Suspicious API pattern | Rate limit reduction + audit flag |
| Known CVE in dependency | Emergency patch within 24 hours |
| Data breach detected | Incident response per IR-DOC-001 |

### Vulnerability Management

- **SAST:** Bandit (`python -m bandit -ll -ii`) runs in CI
- **DAST:** Regular OWASP ZAP scanning on staging
- **Dependency scanning:** `safety check` in CI pipeline
- **Secret scanning:** Gitleaks in pre-commit hook
- **Container scanning:** Trivy in CI build step
- **Penetration testing:** Quarterly third-party assessment
