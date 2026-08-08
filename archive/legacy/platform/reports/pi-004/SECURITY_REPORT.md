# PI-004 — Security Report

## Deployment Platform — Security Analysis

**Version:** 2.1.0
**Date:** July 2026

---

## 1. Security Posture Overview

| Domain | Score | Rating | Notes |
|--------|-------|--------|-------|
| Network Security | 96/100 | ✅ Excellent | VPC isolation, security groups, WAF |
| Identity & Access | 94/100 | ✅ Excellent | Least-privilege IAM, MFA enforced |
| Data Protection | 92/100 | ✅ Good | KMS encryption, column-level encryption |
| Application Security | 90/100 | ✅ Good | CSP, input validation, rate limiting |
| Monitoring & Detection | 88/100 | ✅ Good | GuardDuty, Security Hub, alerting |
| Incident Response | 85/100 | ✅ Good | Documented playbooks, on-call rotation |
| Compliance | 90/100 | ✅ Good | HIPAA-aligned, Iraqi MoH-compliant |
| **Overall** | **91/100** | **✅ Good** | No critical findings |

---

## 2. Network Security

### 2.1 Segmentation

| Layer | Isolation Mechanism | Status |
|-------|---------------------|--------|
| VPC | 10.0.0.0/16, no public access to private subnets | ✅ |
| Public subnet | Internet gateway + NAT gateway only | ✅ |
| Private subnet | No direct internet access (NAT only) | ✅ |
| Database subnet | No internet, no public routes | ✅ |
| Security groups | Least-privilege ingress/egress | ✅ |
| Network ACLs | Stateless filter at subnet boundary | ✅ |

### 2.2 Firewall Rules

```
Inbound (Public):
  - 443 (HTTPS) — CloudFront / ALB only
  - 80 (HTTP) — Redirects to 443

Inbound (Internal):
  - 8000 (API) — ALB → Backend SG only
  - 5432 (PostgreSQL) — Backend SG only
  - 6379 (Redis) — Backend SG only
  - 5672 (RabbitMQ) — Backend SG only
  - 22 (SSH) — Bastion SG, office IPs only

Outbound:
  - All traffic — Through NAT Gateway (filtered)
  - To S3/DynamoDB — Through VPC endpoints (no NAT)
```

### 2.3 DDoS Protection

| Layer | Protection | Configuration |
|-------|-----------|---------------|
| Network (L3/L4) | AWS Shield Advanced | Automatic, always on |
| Application (L7) | AWS WAF | Rate-based rules + IP reputation |
| CDN | CloudFront | Global edge, origin shielding |
| Application | Rate limiting middleware | 100 req/min per user |

---

## 3. Identity & Access Management

### 3.1 AWS IAM Roles

| Role | Trust Entity | Permissions | Purpose |
|------|-------------|-------------|---------|
| `gula-backend-task-role` | ECS Task | S3 read, Secrets Manager read, KMS decrypt, CloudWatch logs | Application runtime |
| `gula-worker-task-role` | ECS Task | S3 read/write, SQS send/receive, KMS decrypt | Background workers |
| `gula-cicd-role` | GitHub Actions | ECR push, ECS deploy, S3 sync, CF invalidation | CI/CD pipeline |
| `gula-db-backup-role` | Lambda/EventBridge | S3 write, RDS snapshot | Automated backups |
| `gula-monitoring-role` | Prometheus | CloudWatch read, EC2 describe | Metrics collection |

### 3.2 Secret Rotation Schedule

| Secret | Rotation Period | Method |
|--------|----------------|--------|
| `SECRET_KEY` | 90 days | Automated (Lambda) |
| `ENCRYPTION_KEY` | 90 days | Automated (Lambda) |
| `DB_PASSWORD` | 180 days | Automated (Secrets Manager) |
| `REDIS_PASSWORD` | 180 days | Automated (Secrets Manager) |
| `JWT_SIGNING_KEY` | 365 days | Manual (key ceremony) |
| `METRICS_TOKEN` | 30 days | Automated (script) |
| TLS certificates | 90 days | Automated (cert-manager/ACM) |

### 3.3 Access Control Matrix

| User Type | Console | API | SSH | DB Read | DB Write | S3 Access |
|-----------|---------|-----|-----|---------|----------|-----------|
| Administrator | ✅ Full | ✅ Full | ✅ | ✅ | ✅ | ✅ |
| Engineer (senior) | ✅ Read | ✅ Full | ✅ | ✅ | ❌ | ✅ Read |
| Engineer (junior) | ✅ Read | ✅ Dev only | ✅ Dev | ✅ Dev | ❌ | ❌ |
| DB admin | ✅ Full | ❌ | ❌ | ✅ Full | ✅ | ❌ |
| Security auditor | ✅ Read | ❌ | ❌ | ✅ Read-only | ❌ | ✅ Read audit |
| Support | ❌ | ✅ Read | ❌ | ❌ | ❌ | ❌ |

---

## 4. Data Protection

### 4.1 Encryption Key Hierarchy

```
AWS KMS CMK (Customer Master Key)
    ├── KMS Key for S3 (SSE-KMS)
    ├── KMS Key for EBS volumes
    ├── KMS Key for Secrets Manager
    ├── KMS Key for RDS encryption
    └── KMS Key for Lambda environment variables

Application-level keys (from Secrets Manager):
    ├── SECRET_KEY → JWT signing (RS256, 4096-bit)
    ├── ENCRYPTION_KEY → National ID encryption (AES-256-GCM)
    ├── NID_HMAC_KEY → Patient card HMAC signing
    ├── DEVICE_HMAC_KEY → Device bridge authentication
    └── REFRESH_TOKEN_SECRET → Refresh token signing
```

### 4.2 Data Classification

| Classification | Examples | Encryption at Rest | Encryption in Transit |
|---------------|----------|-------------------|----------------------|
| **Critical** | National ID, health records, diagnoses | AES-256-GCM (column-level) + TDE | TLS 1.3 |
| **Sensitive** | Names, phone, email, addresses | TDE (DB-level) | TLS 1.3 |
| **Internal** | Lab names, test codes, inventory | TDE (DB-level) | TLS 1.3 |
| **Public** | Facility names, service catalog | N/A | TLS 1.3 |

### 4.3 Data Retention & Deletion

| Data Type | Active Retention | Archive Retention | Deletion Policy |
|-----------|-----------------|-------------------|-----------------|
| Patient records | Indefinite (active) | 10 years after last activity | Anonymized after 10yr |
| Lab results | Indefinite | 10 years | Anonymized after 10yr |
| Audit logs | 2 years hot | 7 years cold | Deleted after 7yr |
| Session data | TTL-based (7d) | None | Auto-deleted |
| Backups | 30 days hot | 365 days cold | Deleted after 1yr |
| Application logs | 90 days | 365 days | Deleted after 1yr |

---

## 5. Compliance Framework

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Iraqi MoH Data Protection Law | ✅ Compliant | Encryption, access controls, audit logs |
| HIPAA (aligned) | ✅ Compliant | BAA, encryption, breach notification |
| ISO 27001 (controls) | ⚠️ Partial | 85/114 controls implemented |
| NIST 800-53 (moderate) | ⚠️ Partial | 210/280 controls implemented |
| OWASP ASVS Level 2 | ✅ Passed | 100% of L1+L2 requirements met |
| PCI DSS (if applicable) | N/A | No credit card data stored |

---

## 6. Penetration Test Results

### 6.1 Summary

| Category | Findings | Critical | High | Medium | Low |
|----------|----------|----------|------|--------|-----|
| Web application | 12 | 0 | 1 | 4 | 7 |
| API | 8 | 0 | 0 | 3 | 5 |
| Infrastructure | 5 | 0 | 1 | 1 | 3 |
| Mobile | 4 | 0 | 0 | 1 | 3 |
| **Total** | **29** | **0** | **2** | **9** | **18** |

### 6.2 High Findings

| Finding | Component | Remediation | Status |
|---------|-----------|-------------|--------|
| Rate limiting not applied to `/health/deep` | API | Added rate limiter to health endpoints | ✅ Fixed |
| S3 bucket `gula-backups` had public ACL | Storage | Removed public ACL, verified with Block Public Access | ✅ Fixed |

### 6.3 Medium Findings (All Remediated)

| Finding | Remediation |
|---------|-------------|
| Missing HSTS header on API gateway | Added `Strict-Transport-Security` header |
| CORS misconfiguration (wildcard origin) | Restricted to `https://*.gula.health` |
| Verbose error messages in API responses | Standardized error format (no stack traces) |
| No rate limiting on password reset | Added per-IP rate limiter (3/min) |
| Weak CSP (allowed 'unsafe-inline') | Moved inline scripts to separate files |
| No CSRF protection on login form | Added SameSite=Strict cookie |
| Missing `X-Frame-Options` header | Added `DENY` header |
| Incomplete audit logging on DELETE operations | Added explicit audit log entry for deletes |
| No input size limits on file uploads | Added 10MB max body size middleware |

---

## 7. Vulnerability Scanning Schedule

| Scan Type | Tool | Frequency | Scope |
|-----------|------|-----------|-------|
| SAST | Bandit (Python) | Every commit | Backend code |
| SAST | ESLint (security rules) | Every commit | Frontend code |
| SCA | Safety (Python) | Every commit | Python deps |
| SCA | pnpm audit | Every commit | JS deps |
| DAST | OWASP ZAP | Weekly | Staging deployment |
| Container scan | Trivy | Every build | All container images |
| Secret scan | Gitleaks | Every commit | Git history |
| IaC scan | Checkov | Every commit | Terraform/K8s files |
| Infrastructure scan | AWS Inspector | Weekly | EC2, ECR, Lambda |
| Penetration test | External vendor | Bi-annual | Full application |

---

## 8. Incident Response Plan

### 8.1 Incident Types

| Type | Example | Response Team |
|------|---------|--------------|
| Security breach | Unauthorized data access | Security + Ops |
| Service compromise | Container/code tampering | Security + Engineering |
| Data exposure | S3 bucket misconfiguration | Security + Ops |
| DDoS attack | Traffic amplification | Ops + Network |
| Insider threat | Unauthorized data export | Security + Legal |

### 8.2 Containment Strategies

| Incident | Immediate Action | Long-Term Fix |
|----------|-----------------|---------------|
| Data breach | Rotate keys, isolate affected resources | Full audit, enhance monitoring |
| Account compromise | Revoke session, reset MFA | Implement anomaly detection |
| Malware/ransomware | Isolate host from network | Restore from clean backup |
| DDoS | Enable AWS Shield + WAF | Rate limit tuning |
| API abuse | Block API key, rate limit | Add behavioral detection |
