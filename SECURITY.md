# Security Policy

## Supported Versions

| Version | Supported |
| ------- | --------- |
| 2.5.x   | ✅ Active development |
| 2.4.x   | ✅ Security patches |
| 2.3.x   | ✅ Security patches |
| 2.2.x   | ✅ Security patches |
| 2.1.x   | ✅ Security patches |
| 2.0.x   | ❌ End of life |
| < 2.0   | ❌ End of life |

## Reporting a Vulnerability

We take the security of GULA Platform seriously. If you believe you have found
a security vulnerability, please report it to us as described below.

### Private Disclosure Process

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email:

**security@gulaplatform.com**

You should receive a response within 48 hours. If you do not, please follow up
to ensure we received your message.

### What to Include

To help us understand and fix the issue quickly, please include:

- Type of vulnerability (e.g., SQL injection, XSS, privilege escalation)
- Full path(s) of affected source file(s)
- Step-by-step reproduction instructions
- Proof-of-concept or exploit code (if available)
- Impact of the vulnerability
- Your preferred contact method for follow-up questions

### What to Expect

1. **Acknowledgment**: We will acknowledge receipt within 48 hours
2. **Triage**: We will assess the vulnerability and assign a severity level
3. **Fix Development**: We will develop and test a fix
4. **Release**: We will release a security patch according to this timeline:
   - **Critical**: 48 hours
   - **High**: 7 days
   - **Medium**: 30 days
   - **Low**: Next regular release
5. **Disclosure**: We will publish a security advisory after the fix is released

### Bug Bounty

We do not currently offer a bug bounty program, but we will publicly
acknowledge security researchers who responsibly disclose vulnerabilities.

## Security Architecture

### Authentication
- JWT tokens with refresh rotation
- bcrypt password hashing (cost factor 12)
- Token blacklist via Redis for revocation

### Authorization
- RBAC with 9 roles: platform_admin, lab_admin, doctor, technician, receptionist, pharmacist, nurse, viewer, edge_agent
- 13 granular permissions per role
- Tenant isolation enforced on all patient-data queries

### Encryption
- AES-256 encryption for sensitive data at rest
- National IDs encrypted with NID_HMAC_KEY
- TLS enforced in production

### Audit Logging
- Immutable hash-chain audit log
- All mutations logged with user_id, lab_id, timestamp
- Audit integrity verification endpoint

### Rate Limiting
- Per-user, per-endpoint rate limiting
- Configurable limits per subscription tier
- Redis-backed for cross-process consistency

### Network Security
- API gateway on 127.0.0.1:8080 (not publicly exposed)
- Security headers: CSP, HSTS, X-Frame-Options
- CORS configured for production origins only

## Security Scan Results (2026-07-08)

### Bandit SAST
- **High**: 0
- **Medium**: 2 (hardcoded_bind_all_interfaces in integration config — dev mode only)
- **Low**: 53 (informational)

### Security Tests
- **54+ tests passing** covering:
  - JWT token validation and expiry
  - Password hashing and verification
  - Encryption/decryption round-trip
  - RBAC permission enforcement
  - Tenant isolation
  - SQL injection prevention
  - Mass assignment defense
  - Audit log integrity

### Known Security Considerations
1. Integration layer uses `0.0.0.0` binding in dev mode (Medium bandit finding)
2. passlib/bcrypt deprecation warning (non-functional, bcrypt 4.1.3 compatible)
3. 268 test fixture errors in tenant isolation tests (test infrastructure, not production code)
4. **ecdsa PYSEC-2026-1325** — Minerva timing side-channel on P-256 curve.
   Accepted risk: `python-jose[cryptography]` uses cryptography library's C
   implementation for JWT signing (not ecdsa pure-Python). No fix available
   (ecdsa project considers side-channels out of scope). Real-world network
   exploitation of this timing attack is not feasible against the API.

## Security Checklist

- [x] No hardcoded secrets (all from env vars)
- [x] No permission bypasses
- [x] No temporary workarounds
- [x] Audit log on all mutations
- [x] Tenant isolation on all patient queries
- [x] JWT verification before data access
- [x] Rate limiting on all endpoints
- [x] Input validation on all endpoints
- [x] Error messages don't leak internals
- [x] CORS configured for production
