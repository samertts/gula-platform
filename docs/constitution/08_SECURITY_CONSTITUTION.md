# GULA Security Constitution

## Core Principles

### 1. Zero Trust Architecture
Every request, every API call, every data access, every inter-service communication is authenticated, authorized, and audited. No request is trusted based on network location, source IP, or prior authentication.

### 2. Least Privilege
Every user, service account, and system component has the minimum permissions required to perform its function. No default "admin" access. No blanket permissions. Time-bound access for temporary operations.

### 3. Defense in Depth
Multiple independent security layers ensure that a single failure does not compromise the system:
- Network firewall → API Gateway → Authentication → Authorization → Data-level security → Audit trail

### 4. Security by Default
Secure defaults are the only defaults. Encryption is enabled by default. Audit logging is enabled by default. Authentication is required by default. Insecure configuration options require explicit opt-in with documented justification.

## Authentication

5. **JWT-based authentication** with short-lived access tokens (15 minutes) and longer-lived refresh tokens (7 days).

6. **Multi-factor authentication (MFA)** is required for administrative roles, cross-tenant access, and sensitive operations. TOTP is the primary mechanism; WebAuthn/FIDO2 is supported.

7. **Password policy** enforces minimum 12 characters, complexity requirements, and hashing with bcrypt (cost factor 12).

8. **Session management** tracks active sessions, supports force-logout, and invalidates all tokens on password change.

9. **Service accounts** use API keys with scoped permissions. Keys are hashed at rest and can be rotated independently.

## Authorization

10. **Role-Based Access Control (RBAC)** is the primary authorization model. Roles define permission sets. Users are assigned roles with scope boundaries.

11. **Attribute-Based Access Control (ABAC)** supplements RBAC for fine-grained access decisions based on user attributes, resource attributes, and environmental context.

12. **Field-level security** controls access to individual data fields based on role, relationship, and consent.

13. **Break-glass access** provides emergency override for life-critical situations. All break-glass actions are logged, reviewed, and subject to abuse detection.

14. **Role delegation** allows temporary authority transfer with explicit duration, scope, and audit trail. (See Article 05.12-14 — Data Architecture for encryption and audit integration.)

## Data Protection

15. **Encryption at rest** for all patient-identifiable data. Column-level encryption for national ID, health ID, and other sensitive identifiers.

16. **Encryption in transit** using TLS 1.3 for all external and internal communications.

17. **Data masking** for sensitive fields when accessed by unauthorized roles. Masking patterns preserve data utility for clinical workflows while protecting privacy.

18. **Audit trail immutability** through hash chaining. Audit log entries are linked such that tampering with any entry breaks the chain.

## Operational Security

19. **Secrets management:** no hardcoded secrets. All secrets are injected through environment variables or a secrets vault.

20. **Security headers:** CSP, HSTS, X-Frame-Options, X-Content-Type-Options, and Referrer-Policy are set on every response.

21. **Rate limiting** per user, per IP, per endpoint. Clinical write operations have different rate limits than read operations.

22. **CORS** is restricted to known origins. Credentials are never sent to unauthorized origins.

## Vulnerability Management

23. **Dependency scanning** is part of CI. CVEs with critical or high severity block the build.

24. **Static analysis** (bandit, gitleaks) runs on every commit.

25. **Penetration testing** is performed quarterly and before major releases.

26. **Incident response plan** is documented, tested, and reviewed annually.

## Compliance

27. **HIPAA alignment** for patient data protection.

28. **Iraqi eHealth standards** compliance for national deployment.

29. **GDPR principles** (data minimization, purpose limitation, right to access, right to erasure) are respected.

30. **Audit readiness:** all security controls are documented, tested, and evidence is preserved for regulatory review.
