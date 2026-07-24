# Dependency Security Report

## Scan Results

### Python Dependencies (Trivy)
Vulnerabilities found: 0 (in scanned Python dependencies)

### Node.js Dependencies (Trivy)
Vulnerabilities found: 3 (Medium severity in platform/apps/pharmacy)

| Package | CVE | Severity | Description |
|---------|-----|----------|-------------|
| react-router@6.30.4 | CVE-2026-53666 | MEDIUM | Path traversal in development server |
| react-router@6.30.4 | CVE-2026-53669 | MEDIUM | XSS via route params |
| react-router-dom@6.30.4 | CVE-2026-53668 | MEDIUM | Same-origin bypass |

## Dependency Inventory

### Python (Production)
| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | >=0.139.2 | Web framework |
| uvicorn | >=0.51.0 | ASGI server |
| sqlalchemy | >=2.0.51 | ORM |
| alembic | >=1.18.5 | Database migrations |
| pydantic | >=2.13.4 | Data validation |
| pydantic-settings | >=2.14.2 | Settings management |
| passlib[bcrypt] | >=1.7.4 | Password hashing |
| bcrypt | >=4.1.3 | Password hashing backend |
| joserfc | >=1.7.3 | JWT implementation |
| cryptography | >=49.0.0 | Encryption library |
| redis | >=8.0.1 | Redis client |
| sentry-sdk | >=2.66.0 | Error tracking |
| webauthn | >=3.0.0 | WebAuthn/FIDO2 |
| pyotp | >=2.10.0 | TOTP implementation |
| httpx | >=0.28.1 | HTTP client |

### Node.js (Production)
| Package | Version | Purpose |
|---------|---------|---------|
| express | ^5.2.1 | Web framework |
| @trpc/server | ^11.18.0 | tRPC |
| react | ^19.2.8 | UI framework |
| react-dom | ^19.2.8 | React DOM |
| react-router-dom | ^7.18.1 | Routing |
| tailwindcss | ^4.3.3 | CSS framework |
| mysql2 | ^3.12.0 | **UNUSED - Remove** |
| redis | ^4.7.0 | Redis client |
| zod | ^4.4.3 | Validation |
| jsonwebtoken | ^9.0.3 | JWT |
| bcryptjs | ^2.4.3 | Password hashing |
| helmet | ^8.0.0 | Security headers |
| axios | ^1.8.2 | HTTP client |
| cors | ^2.8.5 | CORS middleware |

## Issues Found

### DEP-01: Unused mysql2 Dependency
**Severity:** Medium
**Description:** `mysql2` (MySQL driver) listed in `package.json` but platform uses PostgreSQL exclusively
**Impact:** Increases attack surface, adds unnecessary supply chain risk
**Remediation:** Remove `mysql2` from `package.json`

### DEP-02: No Lockfile Verification
**Severity:** Medium
**Description:** No integrity verification for `package-lock.json` or requirements lock files
**Remediation:** Add lockfile signing and verification

### DEP-03: No Automated Dependency Scanning
**Severity:** High
**Description:** No automated dependency vulnerability scanning in CI/CD
**Remediation:** Add `pip-audit`, `npm audit`, or `Dependabot` to CI/CD

### DEP-04: Frontend-v2 Dependencies Not Scanned
**Severity:** Medium
**Description:** Separate `frontend-v2/package.json` not included in regular scanning
**Remediation:** Include all package.json files in scans

## Recommendations

1. Remove unused `mysql2` dependency
2. Add Dependabot or Renovate to repository
3. Add `pip-audit` to CI/CD pipeline
4. Add `npm audit` to CI/CD pipeline
5. Generate SBOM with Syft in CI/CD
6. Implement dependency license compliance checking
7. Pin exact versions (avoid ranges) for production dependencies
8. Regularly update dependencies with automated PRs
9. Monitor CVE feeds for all dependencies
10. Implement dependency vulnerability SLAs
