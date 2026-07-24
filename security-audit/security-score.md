# GULA Platform — Security Maturity Score

**Overall Score: 452/1000**

## Scoring Methodology

Scored against OWASP ASVS Level 3, NIST CSF 2.0, ISO 27001, and CIS Controls v8.
Weights assigned to each domain based on the platform's classification as a healthcare data processor.

## Domain Scores

| Domain | Score | Max | % | Weight |
|--------|-------|-----|---|--------|
| Authentication | 58 | 100 | 58% | 15% |
| Authorization | 72 | 100 | 72% | 10% |
| Cryptography | 45 | 100 | 45% | 10% |
| Session Management | 55 | 100 | 55% | 8% |
| Input Validation | 40 | 100 | 40% | 8% |
| API Security | 50 | 100 | 50% | 8% |
| Container Security | 30 | 100 | 30% | 7% |
| Infrastructure as Code | 25 | 100 | 25% | 7% |
| CI/CD Security | 35 | 100 | 35% | 7% |
| Dependency Management | 20 | 100 | 20% | 5% |
| Data Protection | 40 | 100 | 40% | 5% |
| Logging & Monitoring | 60 | 100 | 60% | 5% |
| Secrets Management | 15 | 100 | 15% | 5% |
| Supply Chain Security | 30 | 100 | 30% | 5% |
| Compliance Readiness | 52 | 100 | 52% | 5% |

## Score Breakdown

### Strengths Adding Points (+)
- RBAC/ABAC implementation: +15
- Security headers middleware: +10
- Rate limiting: +8
- Audit logging: +12
- HSTS configuration: +5
- Break-glass system: +8
- Healthcare-specific controls (consent, purpose-of-use): +10
- No known CVEs in direct dependencies (Trivy scan): +5

### Deficiencies Subtracting Points (-)
- Hardcoded secrets in .env: -20
- No secrets management in K8s: -15
- Weak CSP configuration: -10
- Terraform ALB uses HTTP: -12
- Unrestricted egress in security groups: -10
- K8s pods run as root: -15
- No database encryption at rest: -10
- No MFA enforcement: -12
- Test files with hardcoded keys: -8
- No container image signing: -8
- No dependency scanning in CI/CD: -10
- Missing SAST in CI/CD: -8
- Node `mysql2` dependency (MySQL driver for PostgreSQL platform): -5

## Recommendations by Impact

### Quick Wins (High Impact, Low Effort)
1. Remove `.env` from version control tracking or encrypt it
2. Add HTTPS listeners to ALB in Terraform
3. Fix CSP to remove `unsafe-inline`/`unsafe-eval`
4. Add `securityContext` to all K8s deployments
5. Remove unnecessary `mysql2` npm dependency

### Medium-Term (High Impact, Medium Effort)
1. Integrate Vault + External Secrets Operator
2. Implement SAST scanning in CI/CD
3. Add database encryption at rest (TDE or app-layer)
4. Enforce MFA for all privileged roles
5. Set up dependency vulnerability scanning

### Long-Term (High Impact, High Effort)
1. Implement full secrets management lifecycle
2. Container image signing + admission controller
3. Zero-trust network architecture for Terraform
4. SBOM generation + vulnerability monitoring
5. Penetration testing program
