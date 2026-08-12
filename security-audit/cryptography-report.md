# Cryptography Report

## Cryptographic Inventory

| Algorithm | Usage | Key Size | Strength |
|-----------|-------|----------|----------|
| bcrypt | Password hashing | Cost 12 | Strong |
| HS256 (HMAC-SHA256) | JWT signing | 256-bit | Strong |
| Fernet (AES-256-CBC) | Field-level encryption | 256-bit | Strong |
| HMAC-SHA256 | National ID hashing | 256-bit | Strong |
| SHA-256 | General hashing | 256-bit | Strong |

## Key Management

### Keys in Use
| Key | Purpose | Storage | Rotation |
|-----|---------|---------|----------|
| SECRET_KEY | JWT signing | Environment variable | None documented |
| REFRESH_TOKEN_SECRET | Refresh token signing | Environment variable | None documented |
| ENCRYPTION_KEY | Fernet data encryption | Environment variable | Manual only |
| NID_HMAC_KEY | National ID hashing | Environment variable | DO NOT ROTATE |
| DEVICE_HMAC_KEY | Device authentication | Environment variable | None documented |
| AUDIT_ANCHOR_KEY | Audit log integrity | Environment variable | None documented |

## Issues Found

### CRYPTO-01: Fernet Key Not Rotatable
**Severity:** Critical
**Impact:** All encrypted data becomes unreadable if key rotates
**Affected:** `backend/app/security/encryption.py`
**Remediation:** Implement key rotation with version tracking (allow multiple decryption keys)

### CRYPTO-02: No Key Management System
**Severity:** Critical
**Impact:** Keys stored in plaintext environment files
**Remediation:** Integrate HashiCorp Vault or AWS KMS

### CRYPTO-03: NID_HMAC_KEY Cannot Be Rotated
**Severity:** High
**Impact:** All national ID hashes must be re-hashed if key changes
**Affected:** `backend/app/config.py:151`
**Remediation:** Implement key rotation with versioned hashing (store key version with hash)

### CRYPTO-04: No Hardware Security Module (HSM)
**Severity:** Medium
**Impact:** Keys in software memory only
**Remediation:** Evaluate HSM for production key storage

### CRYPTO-05: Audit Anchor HMAC Key Shares NID Key Fallback
**Severity:** Medium
**Impact:** If AUDIT_ANCHOR_KEY not set, falls back to NID_HMAC_KEY
**Affected:** `backend/app/config.py:164`
**Remediation:** Always require separate AUDIT_ANCHOR_KEY

### CRYPTO-06: No Certificate Transparency Monitoring
**Severity:** Low
**Impact:** No monitoring for TLS certificate misissuance
**Remediation:** Implement certificate transparency log monitoring

## Recommendations

1. Implement key rotation with version tracking
2. Integrate Vault or KMS for key management
3. Separate all HMAC keys (no fallback)
4. Add certificate pinning for critical endpoints
5. Implement HSM for production key storage
6. Add key expiration alerts and rotation automation
7. Document key lifecycle procedures
8. Implement FIPS 140-2 compliant cryptography where required
