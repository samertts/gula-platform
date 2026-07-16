# GULA Platform — Master Security Catalog

Version: 1.0 — 2026-07-15
Status: **DRAFT** — Architecture Review Board approval pending

---

## Table of Contents

1. [Security Controls Inventory](#1-security-controls-inventory)
2. [Authentication Mechanisms](#2-authentication-mechanisms)
3. [Authorization Models](#3-authorization-models)
4. [Encryption At Rest and In Transit](#4-encryption-at-rest-and-in-transit)
5. [Audit Logging Coverage](#5-audit-logging-coverage)
6. [Rate Limiting Configuration](#6-rate-limiting-configuration)
7. [Security Testing Results](#7-security-testing-results)
8. [Vulnerability Management Process](#8-vulnerability-management-process)

---

## 1. Security Controls Inventory

### 1.1 Preventive Controls

| Control ID | Control Name | Location | Type | Status |
|------------|-------------|----------|------|--------|
| AC-1 | JWT Authentication | `backend/app/security/auth.py` | Preventive | 🟢 Active |
| AC-2 | JWT Blacklist (Revocation) | `backend/app/security/auth.py:43-52` | Preventive | 🟢 Active |
| AC-3 | Password Hashing (bcrypt) | `shared/auth/passwords.py` | Preventive | 🟢 Active |
| AC-4 | RBAC Enforcement | `backend/app/security/rbac.py` | Preventive | 🟢 Active |
| AC-5 | ABAC Enforcement | `backend/app/security/abac.py` | Preventive | 🟢 Active |
| AC-6 | National ABAC | `backend/app/national/security/abac.py` | Preventive | 🟢 Active |
| AC-7 | Purpose of Use Enforcement | `backend/app/national/security/purpose_of_use.py` | Preventive | 🟢 Active |
| AC-8 | Break Glass Access | `backend/app/national/security/break_glass.py` | Preventive | 🟢 Active |
| AC-9 | Emergency Access | `backend/app/national/security/emergency_access.py` | Preventive | 🟢 Active |
| AC-10 | Minor Protection | `backend/app/national/security/minor_protection.py` | Preventive | 🟢 Active |
| AC-11 | VIP Protection | `backend/app/national/security/vip_protection.py` | Preventive | 🟢 Active |
| AC-12 | Foreign Patient Rules | `backend/app/national/security/foreign_patient_rules.py` | Preventive | 🟢 Active |
| AC-13 | Guardian Rules | `backend/app/national/security/guardian_rules.py` | Preventive | 🟢 Active |
| AC-14 | Sensitive Record Protection | `backend/app/national/security/sensitive_records.py` | Preventive | 🟢 Active |
| AC-15 | Minimum Necessary Access | `backend/app/national/security/minimum_necessary.py` | Preventive | 🟢 Active |
| AC-16 | Tenant Isolation (lab_id filter) | All routes / `TenantMixin` | Preventive | 🟢 Active |
| AC-17 | Session Management | `backend/app/security/session.py` | Preventive | 🟢 Active |
| AC-18 | Consent Enforcement | `backend/app/security/consent_dep.py` | Preventive | 🟢 Active |
| CR-1 | Rate Limiting | `backend/app/security/rate_limit.py` | Preventive | 🟢 Active |
| CR-2 | Concurrency Limit | `backend/app/main.py:ConcurrencyLimitMiddleware` | Preventive | 🟢 Active |
| CR-3 | Idempotency Keys | `backend/app/core/idempotency.py` | Preventive | 🟢 Active |
| CR-4 | Max Body Size | `backend/app/main.py:MaxBodySizeMiddleware` | Preventive | 🟢 Active |
| CR-5 | CORS Restrictions | `backend/app/main.py:CORSMiddleware` | Preventive | 🟢 Active |
| CR-6 | Security Headers (CSP, HSTS) | `backend/app/main.py:SecurityHeadersMiddleware` | Preventive | 🟢 Active |
| CR-7 | API Firewall | `backend/app/firewall/api_firewall.py` | Preventive | 🟢 Active |
| EN-1 | AES-256-GCM PII Encryption | `shared/security/encryption.py` | Preventive | 🟢 Active |
| EN-2 | HMAC-SHA256 NID Hashing | `backend/app/security/encryption.py` | Preventive | 🟢 Active |
| EN-3 | TLS 1.3 In Transit | nginx configuration | Preventive | 🟢 Active |
| EN-4 | Secret Weakness Detection | `backend/app/config.py:_is_weak_secret` | Preventive | 🟢 Active |

### 1.2 Detective Controls

| Control ID | Control Name | Location | Type | Status |
|------------|-------------|----------|------|--------|
| DT-1 | Audit Logging | `backend/app/models/audit_log.py` | Detective | 🟢 Active |
| DT-2 | Audit Hash Chain | `audit_logs.chain_hash` | Detective | 🟢 Active |
| DT-3 | Identity Merge Audit | `mpi_merge_audit` table | Detective | 🟢 Active |
| DT-4 | Gateway Call Audit | `backend/app/gateways/base.py` | Detective | 🟢 Active |
| DT-5 | AI Interaction Audit | `ai_interactions` table | Detective | 🟢 Active |
| DT-6 | Intrusion Detection | `backend/app/security/intrusion_detection.py` | Detective | 🟢 Active |
| DT-7 | Health Scoring | `backend/app/core/self_healing.py:_health_alert_loop` | Detective | 🟢 Active |
| DT-8 | Structured Logging | `backend/app/core/logging_config.py` | Detective | 🟢 Active |
| DT-9 | Metrics Monitoring | `backend/app/routes/metrics.py` | Detective | 🟢 Active |
| DT-10 | Sentry Error Tracking | `backend/app/main.py:48-71` | Detective | 🟡 Optional |

### 1.3 Corrective Controls

| Control ID | Control Name | Location | Type | Status |
|------------|-------------|----------|------|--------|
| CR-1 | Circuit Breaker | `backend/app/core/self_healing.py` | Corrective | 🟢 Active |
| CR-2 | Degraded Mode | `backend/app/core/self_healing.py:DegradedModeMiddleware` | Corrective | 🟢 Active |
| CR-3 | Auto-Recovery | `backend/app/core/self_healing.py:RecoveryWorker` | Corrective | 🟢 Active |
| CR-4 | Auto-Repair (GC, Pool) | `backend/app/core/auto_repair.py` | Corrective | 🟢 Active |
| CR-5 | Kill Switch | `backend/app/core/kill_switch.py` | Corrective | 🟢 Active |
| CR-6 | Adaptive Concurrency | `backend/app/main.py:_adaptive_concurrency_loop` | Corrective | 🟢 Active |
| CR-7 | Outbox Retry | `backend/app/services/outbox_service.py` | Corrective | 🟢 Active |
| CR-8 | Retry with Backoff | `backend/app/core/resilience.py` | Corrective | 🟢 Active |
| CR-9 | Optimistic Locking | `shared/models/base.py:OptimisticLockMixin` | Corrective | 🟢 Active |

---

## 2. Authentication Mechanisms

### 2.1 Primary: JWT (JSON Web Token)

| Attribute | Value |
|-----------|-------|
| **Algorithm** | HS256 (HMAC with SHA-256) |
| **Access Token TTL** | 15 minutes (configurable: `JWT_EXPIRE_MINUTES`) |
| **Refresh Token TTL** | 7 days (configurable: `REFRESH_TOKEN_EXPIRE_DAYS`) |
| **Secret** | `SECRET_KEY` env var (no default, weak detection) |
| **Refresh Secret** | `REFRESH_TOKEN_SECRET` env var (separate from access token) |
| **Token Payload** | user_id, lab_id, role, perm_ver, jti, type |
| **Revocation** | Redis blacklist by JTI (`blacklist:jti:{jti}`) |
| **Implementation** | `backend/app/security/auth.py` |

### 2.2 Password Authentication

| Attribute | Value |
|-----------|-------|
| **Algorithm** | bcrypt (via passlib) |
| **Cost Factor** | 12 rounds |
| **Timing Attack Protection** | Dummy hash comparison for non-existent users |
| **Implementation** | `shared/auth/passwords.py` |

### 2.3 Future / Optional

| Mechanism | Status | Location |
|-----------|--------|----------|
| OAuth2 / OIDC | PLANNED | Future |
| mTLS | PLANNED | Future (device bridge) |
| SAML SSO | PLANNED | Future (enterprise) |
| Biometric | PLANNED | Future (mobile) |

---

## 3. Authorization Models

### 3.1 RBAC (Role-Based Access Control)

| Role | Level | Permissions | Location |
|------|-------|-------------|----------|
| admin | 100 | Full system access | `shared/rbac/permissions.py` |
| province_admin | 80 | Provincial scoped access | `shared/rbac/permissions.py` |
| lab_admin | 60 | Full lab-scoped access | `shared/rbac/permissions.py` |
| doctor | 50 | Clinical read/write | `shared/rbac/permissions.py` |
| manager | 40 | Operational management | `shared/rbac/permissions.py` |
| technician | 30 | Result entry & QC | `shared/rbac/permissions.py` |
| receptionist | 20 | Patient & order registration | `shared/rbac/permissions.py` |
| viewer | 10 | Read-only access | `shared/rbac/permissions.py` |
| api_client | 5 | Machine-to-machine API access | `shared/rbac/permissions.py` |

### 3.2 ABAC (Attribute-Based Access Control)

| Attribute | Source | Example |
|-----------|--------|---------|
| Subject role | JWT payload | `user.role == "doctor"` |
| Subject organization | JWT payload | `user.lab_id == 42` |
| Resource type | Request path | `resource_type == "patient"` |
| Resource owner | Database | `patient.lab_id == user.lab_id` |
| Resource sensitivity | Database | `patient.is_vip == True` |
| Action | HTTP method | `action == "read"` |
| Environment | Request context | `time_of_day`, `ip_address` |
| Purpose of use | Request header | `purpose == "treatment"` |

### 3.3 ReBAC (Relationship-Based Access Control)

Future — planned for multi-organization sharing scenarios.

### 3.4 Access Control Flow

```
Request → Auth Dependency → JWT Verification → RBAC Role Check
    → ABAC Policy Evaluation → Purpose of Use Check
    → Tenant Isolation (lab_id filter) → Data Access
```

---

## 4. Encryption At Rest and In Transit

### 4.1 At Rest

| Data Scope | Algorithm | Key Management | Location |
|-----------|-----------|---------------|----------|
| National ID (patients) | AES-256-GCM | `ENCRYPTION_KEY` env var | `shared/security/encryption.py` |
| NID Hash (citizens) | HMAC-SHA256 | `NID_HMAC_KEY` env var | `backend/app/security/encryption.py` |
| Patient Card Token | HMAC-SHA256 | `PATIENT_CARD_SECRET` | `backend/app/services/patient_card.py` |
| Database (full) | Filesystem-level (cloud provider) | Provider-managed | Render / DigitalOcean |
| Redis | `REDIS_PASSWORD` auth | Configurable | Redis config |
| Backups | Encrypted before upload | GPG / cloud KMS | `scripts/backup.sh` |

### 4.2 In Transit

| Scope | Protocol | Certificate Management |
|-------|----------|----------------------|
| External (Internet → host) | TLS 1.3 | Let's Encrypt / Cloudflare |
| Internal (Docker network) | TCP (unencrypted within trusted network) | N/A |
| Database (host → Postgres) | TLS (optional, `sslmode=require`) | Configurable via DATABASE_URL |
| Redis (host → Redis) | TLS (optional) | Configurable via REDIS_URL |

### 4.3 Key Rotation

| Key | Rotation Period | Method |
|-----|----------------|--------|
| SECRET_KEY | Every 90 days | Update env var, redeploy |
| ENCRYPTION_KEY | Every 180 days | Re-encrypt PII with new key |
| NID_HMAC_KEY | Every 180 days | Re-hash stored NID hashes |
| TLS Certificates | Every 90 days | Auto-renew via Let's Encrypt |

---

## 5. Audit Logging Coverage

### 5.1 Audit Events

| Action Type | Audited? | Location | Details |
|-------------|----------|----------|---------|
| User login | ✅ | `routes/login.py` | user_id, IP, timestamp |
| User logout | ✅ | `routes/login.py` | user_id, session_id |
| Patient create | ✅ | `routes/patients.py` | patient_id, lab_id, user_id |
| Patient update | ✅ | `routes/patients.py` | patient_id, changed fields |
| Patient delete | ✅ | `routes/patients.py` | patient_id (soft delete) |
| Order create | ✅ | `routes/clinical_orders.py` | order_id, patient_id, lab_id |
| Order update | ✅ | `routes/clinical_orders.py` | order_id, status change |
| Order cancel | ✅ | `routes/clinical_orders.py` | order_id, reason |
| Result create | ✅ | `routes/results.py` | result_id, order_id |
| Result update | ✅ | `routes/results.py` | result_id, changed values |
| Result validate | ✅ | `routes/results.py` | result_id, validator_id |
| Sample update | ✅ | `routes/samples.py` | sample_id, status change |
| Identity merge | ✅ | `mpi_merge_audit` | citizen_ulids, reason, algorithm |
| Gateway call | ✅ | `gateways/base.py` | gateway, action, latency, outcome |
| Feature flag change | ✅ | `routes/admin.py` | lab_id, feature, enabled/disabled |
| Subscription change | ✅ | `routes/tiers.py` | lab_id, old_tier, new_tier |
| AI request | ✅ | `ai_interactions` | user_id, model, prompt_length |
| API key issue | ✅ | `security/session.py` | lab_id, key_prefix |
| Rate limit exceeded | ✅ | `security/rate_limit.py` | lab_id, endpoint, count |
| Kill switch activation | ✅ | `core/kill_switch.py` | admin_id, reason |

### 5.2 Audit Data Model

```python
# From backend/app/models/audit_log.py
class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id: int
    user_id: int | None
    user_role: str | None
    action: str             # view, create, update, delete
    resource_type: str      # patient, test, result
    resource_id: int | None
    details: str | None     # JSON string of changes
    ip_address: str | None
    created_at: datetime
    chain_hash: str | None  # SHA-256 hash chain
```

### 5.3 Hash Chain Integrity

```python
# Each entry's chain_hash = SHA256(prev_hash || canonical_json(row))
# Tampering detectable by scanning chain
```

---

## 6. Rate Limiting Configuration

### 6.1 Default Limits

| Endpoint Group | Rate Limit | Window | Scope |
|----------------|------------|--------|-------|
| Login | 10 requests | 1 minute | Per IP |
| API (general) | 1000 requests | 1 minute | Per lab |
| AI endpoints | 50 requests | 1 minute | Per lab |
| Result entry | 500 requests | 1 minute | Per lab |
| Patient search | 200 requests | 1 minute | Per user |
| File upload | 20 requests | 1 minute | Per lab |
| Device bridge | 200 requests | 1 minute | Per device |

### 6.2 Configuration Location

- `backend/app/security/rate_limit.py` — Rate limiter implementation
- `backend/app/security/intrusion_detection.py` — Anomaly detection
- `backend/app/firewall/api_firewall.py` — Firewall rules

---

## 7. Security Testing Results

### 7.1 Automated Scans

| Scan Type | Tool | Frequency | Last Result | Location |
|-----------|------|-----------|-------------|----------|
| SAST (Python) | `bandit -ll -ii` | Per commit | PASS (0 high) | CI pipeline |
| Dependency CVE | `safety` | Per commit | PASS (0 critical) | CI pipeline |
| Container scan | `trivy` | Per commit | PASS (0 critical) | CI pipeline |
| Secret scan | `gitleaks` | Per commit | PASS (0 secrets) | CI pipeline |
| Dockerfile lint | `hadolint` | Per commit | PASS | CI pipeline |
| SBOM generation | `trivy` | Per release | GENERATED | Release gate |

### 7.2 Manual Testing

| Test Type | Frequency | Last Performed | Results |
|-----------|-----------|----------------|---------|
| Penetration test | Quarterly | TBD | Pending |
| Security review | Per release | TBD | Pending |
| Threat modeling | Per feature | TBD | Pending |

---

## 8. Vulnerability Management Process

### 8.1 CVE Tracking

```
1. CVE discovered → Severity assessment (CVSS)
2. Critical/High → Emergency patch within 48h
3. Medium → Fix within next sprint
4. Low → Fix within next release
5. Fix verified → CI security gate passes
6. SBOM updated → Release documentation
```

### 8.2 Responsible Disclosure

- Email: security@gula.health (not yet established — placeholder)
- Response SLA: 24 hours for critical, 72 hours for high
- Fix SLA: 48 hours for critical, 7 days for high

### 8.3 Patch Management

| Type | Cadence | Method |
|------|---------|--------|
| Security patches | As needed (emergency process) | Hotfix deployment |
| Dependency updates | Monthly | `safety` scan → update → CI pass → deploy |
| OS patches | Provider-managed | Render/DigitalOcean auto-updates |

---

## Document Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-07-15 | Architecture Team | Initial master security catalog |

**Review Cycle**: This document must be reviewed and updated quarterly or when security controls change.
