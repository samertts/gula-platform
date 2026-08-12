# GULA Platform — Security Architecture Analysis

## Architecture Overview

GULA Platform follows a microservices architecture with an API gateway pattern:

```
Internet → Host Nginx (TLS) → Docker API Gateway (Nginx) → Backend (FastAPI/Uvicorn)
                                                        → Frontend (React/Static)
                                                        → Workers (Background Tasks)
                                                        → Microservices (AI, Lab, etc.)
```

## Components

### Backend (FastAPI)
- **Framework:** FastAPI 0.139.2+ with Uvicorn/Gunicorn
- **Auth:** JWT-based with access + refresh tokens
- **Session:** JWT with Redis-backed blacklisting + perm_version invalidation
- **RBAC:** Role-based access with shared library
- **ABAC:** Attribute-based access control engine with rule evaluation
- **OAuth2:** Provider with authorization code flow, PKCE support
- **SAML:** SAML SSO integration
- **WebAuthn:** Passkeys/FIDO2 support
- **MFA:** TOTP (pyotp) support

### Frontend (React + Vite)
- **Framework:** React 19 with TypeScript
- **PWA:** Service worker with Workbox
- **Build:** Vite 8
- **API:** tRPC with React Query

### Microservices
- AI Service
- Lab Service
- Order Service
- Patient Service
- Result Service
- Sample Service
- Notification Service
- Device Bridge Service
- Autonomous Manager

### Data Layer
- **Database:** PostgreSQL 17 (primary)
- **Cache:** Redis 7 (with Sentinel/Cluster HA support)
- **Storage:** MinIO / S3-compatible object storage
- **Queue:** Internal outbox pattern + RabbitMQ

## Security Architecture by Layer

### Network Security
- Docker internal network (no external port exposure)
- Nginx reverse proxy with TLS termination
- Security group rules in Terraform (but overly permissive egress)

### Authentication
- bcrypt password hashing (cost factor 12)
- JWT access tokens (30 min expiry) + refresh tokens (30 day expiry)
- Token blacklisting via Redis
- Permission version tracking (invalidates on role changes)
- Timing-safe login with dummy hash (prevents user enumeration)
- OAuth2 provider with PKCE support
- SAML SSO integration
- WebAuthn/FIDO2 support
- MFA with TOTP (optional)

### Authorization
- Hierarchical RBAC with 30+ roles
- ABAC engine with attribute conditions
- Purpose-of-use enforcement
- Consent enforcement
- Break-glass emergency access
- VIP protection
- Minor protection
- Foreign patient rules
- Minimum necessary disclosure

### Data Protection
- Fernet (AES-256) encryption for sensitive fields
- National ID HMAC hashing (not stored in plaintext)
- Field-level encryption for PHI
- Data classification labels

### Audit & Monitoring
- Comprehensive audit logging
- Audit anchor HMAC for tamper detection
- Rate limiting with dynamic IP blocking
- Intrusion detection (in-memory attempt tracking)
- Structured logging
- Prometheus + Grafana + Alertmanager

## Missing Security Controls

1. **Secrets Management:** No Vault/ESO integration
2. **Database Encryption at Rest:** No TDE configured
3. **Container Image Signing:** No Docker Content Trust
4. **SAST in CI/CD:** No automated SAST scanning
5. **DAST in CI/CD:** No dynamic scanning
6. **Dependency Scanning:** No automated CVE scanning pipeline
7. **Software Bill of Materials (SBOM):** Not generated in CI/CD
8. **Pod Security Standards:** Not enforced (privileged by default)
9. **Network Policies:** Not implemented in K8s
10. **Service Mesh:** Linkerd installed but policies not enforced
11. **API Rate Limiting on Gateway:** Nginx rate limiting only at HTTP level
12. **Content Security Policy:** Too permissive (`unsafe-inline` + `unsafe-eval`)
13. **Subresource Integrity:** Not used on CDN assets
14. **Certificate Pinning:** Not implemented
15. **Security.txt:** Not found
