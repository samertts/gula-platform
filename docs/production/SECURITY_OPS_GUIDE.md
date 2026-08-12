# GULA Platform — Security Operations Guide v1.0

**Version:** 1.0
**Date:** 2026-07-15
**Status:** FINAL
**Classification:** CONFIDENTIAL — Operations Team Only

---

## 1. Security Architecture

### Defence in Depth

```
Layer 1: Cloudflare Edge
├── Web Application Firewall (WAF)
├── DDoS Protection (L3/L4/L7)
├── CDN + SSL Termination
├── Bot Management
└── Rate Limiting

Layer 2: Network Perimeter
├── Host Nginx (TLS termination)
├── fail2ban (brute force protection)
├── IP whitelisting (admin)
└── VPN access only

Layer 3: Service Mesh (Linkerd)
├── mTLS between all services
├── Traffic splitting (canary)
├── Service-level auth
└── Metrics collection

Layer 4: Application (FastAPI)
├── JWT authentication
├── RBAC (9 roles × 13 permissions)
├── ABAC (attribute-based access)
├── Field-level encryption (PII)
├── Input validation & sanitization
├── CSP, HSTS, Security Headers
├── Rate limiting (Redis-backed)
└── Audit logging (hash chain)

Layer 5: Data
├── PostgreSQL: encryption at rest
├── PII fields: AES-256 encrypted
├── National ID: AES-256 + HMAC
├── Credentials: bcrypt hashed
├── Backups: encrypted
└── Audit logs: tamper-proof chain
```

### Security Domains

| Domain | Owner | Key Controls |
|--------|-------|-------------|
| Identity & Access | Platform Team | JWT, RBAC, ABAC, MFA |
| Network Security | Infrastructure Team | WAF, IDS/IPS, mTLS, VPN |
| Data Protection | Security Team | Encryption, Masking, DLP |
| Application Security | Dev Team | SAST, DAST, Input Validation |
| Infrastructure Security | DevOps Team | CIS Benchmarks, Hardened Images |
| Incident Response | Security Team | IR Plan, Forensics, SIEM |

---

## 2. Identity & Access Management (IAM)

### Authentication

| Method | Use Case | Security Level |
|--------|----------|---------------|
| JWT access token | API authentication | High (15min expiry) |
| JWT refresh token | Session management | High (7d, rotateable) |
| Admin token | Operations | Critical (manual rotation) |
| Metrics token | Prometheus scraping | Medium |
| Device HMAC | Lab device auth | Medium (shared key) |

### JWT Token Structure

```json
{
  "sub": "user_uuid",
  "lab_id": "lab_uuid",
  "role": "lab_admin",
  "permissions": ["read:patients", "write:orders", "admin:users"],
  "iat": 1689300000,
  "exp": 1689300900,
  "jti": "unique-token-id"
}
```

### RBAC Matrix

| Role | patients | orders | results | users | admin | billing | audit |
|------|----------|--------|---------|-------|-------|---------|-------|
| super_admin | RW | RW | RW | RW | RW | RW | RW |
| lab_admin | RW | RW | RW | RW | R | R | R |
| lab_technician | R | RW | RW | — | — | — | — |
| doctor | R | R | R | — | — | — | — |
| nurse | R | R | R | — | — | — | — |
| patient | R | R | R | — | — | — | — |
| ministry_viewer | R | R | R | — | — | — | — |
| device_bridge | — | W | W | — | — | — | — |
| integration | RW | RW | RW | — | — | — | — |

### ABAC Rules

| Resource | Attribute | Rule |
|----------|-----------|------|
| Patient data | lab_id | Must match user's lab_id |
| National ID | role | Only `super_admin` can view plaintext |
| Financial data | role | Only `lab_admin` + `super_admin` |
| Audit logs | role | Only `super_admin` can view |
| System config | role | Only `super_admin` can modify |

### Password Policy

| Requirement | Value |
|-------------|-------|
| Minimum length | 12 characters |
| Complexity | Upper + Lower + Digit + Special |
| History | 10 previous passwords |
| Max age | 90 days |
| Lockout threshold | 5 attempts |
| Lockout duration | 15 minutes |
| MFA | Required for admin roles |

---

## 3. Network Security

### Cloudflare WAF Configuration

**Managed Rulesets Enabled:**
- Cloudflare OWASP Core Ruleset (paranoia level 3)
- Cloudflare Managed Ruleset (all)
- Rate Limiting: 100 req/min per IP
- Bot Fight Mode: enabled
- TLS: 1.3 only
- HTTP/2: enabled
- HTTP/3: enabled

**Custom WAF Rules:**

```json
{
  "rules": [
    {
      "description": "Block known malicious IPs",
      "expression": "(ip.src in $threat_intel_list)",
      "action": "block"
    },
    {
      "description": "Rate limit API endpoints",
      "expression": "(http.request.uri.path matches \"^/api/\")",
      "action": "rate_limit",
      "ratelimit": {"requests_per_period": 100, "period_seconds": 60}
    },
    {
      "description": "Block SQL injection attempts",
      "expression": "(http.request.uri.path matches \"(?i)(select|union|drop|insert|update|delete)\")",
      "action": "block"
    },
    {
      "description": "Challenge login endpoints",
      "expression": "(http.request.uri.path eq \"/api/auth/login\")",
      "action": "challenge"
    }
  ]
}
```

### Firewall Rules (Host Level)

```bash
# Allow HTTP/HTTPS from Cloudflare only
iptables -A INPUT -p tcp --dport 80 -s $(curl -s https://www.cloudflare.com/ips-v4) -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -s $(curl -s https://www.cloudflare.com/ips-v4) -j ACCEPT
iptables -A INPUT -p tcp --dport 80 -j DROP
iptables -A INPUT -p tcp --dport 443 -j DROP

# Allow SSH from admin VPN only
iptables -A INPUT -p tcp --dport 22 -s <admin-vpn-cidr> -j ACCEPT
iptables -A INPUT -p tcp --dport 22 -j DROP

# Block all other incoming traffic by default
iptables -P INPUT DROP
iptables -P FORWARD DROP

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
```

### IDS/IPS (fail2ban)

```ini
# /etc/fail2ban/jail.local
[gula-backend]
enabled = true
port = 80,443
filter = gula-auth
logpath = /var/log/gula/access.log
maxretry = 5
bantime = 3600
findtime = 300

[gula-admin]
enabled = true
port = 22
filter = gula-admin
logpath = /var/log/auth.log
maxretry = 3
bantime = 86400
findtime = 300
```

---

## 4. Data Protection

### Encryption at Rest

| Data Store | Encryption Method | Key Management |
|------------|------------------|---------------|
| PostgreSQL data | AES-256 (filesystem or TDE) | LUKS or KMS |
| PII fields | AES-256 (application-level) | ENCRYPTION_KEY (`.env`) |
| National IDs | AES-256 + HMAC | NID_HMAC_KEY (`.env`) |
| Backups | GPG symmetric encryption | Separate backup key |
| Logs | No PII in logs | Separation of concerns |

### Application-Level Encryption

```python
# backend/app/security/encryption.py
from cryptography.fernet import Fernet
from app.config import settings

fernet = Fernet(settings.ENCRYPTION_KEY)

def encrypt_field(plaintext: str) -> str:
    return fernet.encrypt(plaintext.encode()).decode()

def decrypt_field(ciphertext: str) -> str:
    return fernet.decrypt(ciphertext.encode()).decode()
```

### Encryption in Transit

| Communication | Protocol | Ciphers |
|--------------|----------|---------|
| Client ↔ Cloudflare | TLS 1.3 | TLS_AES_128_GCM_SHA256 |
| Cloudflare ↔ Backend | TLS 1.3 | TLS_AES_256_GCM_SHA384 |
| Backend ↔ PostgreSQL | TLS 1.3 | mTLS (optional) |
| Services (Linkerd) | mTLS | Auto-rotated 24h |
| Backend ↔ Redis | TLS | Via stunnel if needed |
| Backend ↔ RabbitMQ | TLS | AMQPS |

### Data Masking

```sql
-- Mask PII for non-privileged queries
SELECT
  CASE WHEN current_user_role() IN ('super_admin', 'lab_admin')
       THEN national_id
       ELSE '***-****-' || RIGHT(national_id, 4)
  END AS national_id,
  CASE WHEN current_user_role() IN ('super_admin', 'lab_admin')
       THEN phone
       ELSE '***-***-' || RIGHT(phone, 4)
  END AS phone
FROM patients;
```

---

## 5. Secrets Management

### Secret Categories

| Category | Examples | Rotation | Storage |
|----------|---------|----------|---------|
| Application secrets | SECRET_KEY, ENCRYPTION_KEY | 90 days | Vault / .env.gpg |
| Database credentials | POSTGRES_PASSWORD | 90 days | Vault / .env.gpg |
| API tokens | CLOUDFLARE_TOKEN, SENTRY_DSN | 180 days | Vault |
| Service keys | DEVICE_HMAC_KEY, NID_HMAC_KEY | 90 days | Vault / .env.gpg |
| TLS certificates | Let's Encrypt | 60 days | cert-manager |

### Vault Configuration (K8s)

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: gula-secrets
spec:
  provider: vault
  parameters:
    roleName: gula-platform
    vaultAddress: https://vault.gula.internal:8200
    objects: |
      - objectName: "SECRET_KEY"
        secretPath: "gula/production/backend"
        secretKey: "SECRET_KEY"
      - objectName: "ENCRYPTION_KEY"
        secretPath: "gula/production/backend"
        secretKey: "ENCRYPTION_KEY"
      - objectName: "POSTGRES_PASSWORD"
        secretPath: "gula/production/database"
        secretKey: "password"
```

### Docker Secrets (.env)

```bash
# Generate strong secrets
make secrets-gen

# Encrypt .env for backup
gpg --symmetric --cipher-algo AES256 --output .env.gpg .env

# Decrypt when needed
gpg --decrypt .env.gpg > .env
```

### Secret Rotation

```bash
# Rotate application secrets
make secrets-gen > new-secrets.txt
# Copy new secrets into .env
docker compose up -d --no-deps gula-backend

# Rotate database password
docker compose exec postgres psql -U gula -c "ALTER USER gula WITH PASSWORD 'new_password';"
# Update .env and restart
docker compose up -d --no-deps gula-backend

# Rotate API tokens
# Update in Vault or .env
# No restart needed (tokens fetched on demand)
```

### Secret Compromise Procedure

```bash
# 1. Immediately rotate the compromised secret
# 2. Check audit logs for unauthorized access since compromise
# 3. Revoke all existing tokens/sessions
# 4. Force password reset for affected users
# 5. Notify security team
# 6. Investigate how the secret was compromised
```

---

## 6. Certificate Management

### Certificate Inventory

| Certificate | Provider | Renewal Method | Expiry Alert |
|-------------|----------|----------------|-------------|
| `api.gula.health` | Let's Encrypt | cert-manager | 30d, 7d, 1d |
| `*.gula.health` | Cloudflare Edge | Auto | Managed by Cloudflare |
| Internal mTLS | Linkerd | Auto (24h) | Automatic rotation |

### Auto-Renewal (Cert-Manager)

```yaml
# cert-manager ClusterIssuer (production)
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@gula.health
    privateKeySecretRef:
      name: letsencrypt-prod-account-key
    solvers:
    - http01:
        ingress:
          class: nginx

---
# Certificate resource
apiVersion: cert-manager.io/v1
kind: Certificate
metadata:
  name: gula-api-tls
  namespace: gula-platform
spec:
  secretName: gula-api-tls
  issuerRef:
    name: letsencrypt-prod
    kind: ClusterIssuer
  dnsNames:
  - api.gula.health
  - *.gula.health
  renewBefore: 720h  # 30 days
  duration: 2160h    # 90 days
```

### Manual Renewal (Docker)

```bash
# Check expiry
openssl s_client -connect api.gula.health:443 -servername api.gula.health \
  </dev/null 2>/dev/null | openssl x509 -noout -enddate

# Force renewal
certbot renew --force-renewal
docker compose exec api-gateway nginx -s reload

# Verify
curl -vI https://api.gula.health 2>&1 | grep "SSL certificate"
```

### Expiry Monitoring

```promql
# Prometheus alert rule
- alert: TLSCertExpiry
  expr: (avg(nginx_ingress_controller_ssl_expire_time_seconds) by (host) - time()) < 2592000
  for: 1h
  labels:
    severity: warning
  annotations:
    summary: "TLS certificate for {{ $labels.host }} expires in {{ $value | humanizeDuration }}"
```

---

## 7. Vulnerability Management

### Scanning Schedule

| Scan Type | Tool | Frequency | Target |
|-----------|------|-----------|--------|
| SAST (Static Analysis) | Bandit, Semgrep | Every commit | `backend/app/` |
| DAST (Dynamic Analysis) | OWASP ZAP | Weekly | Staging environment |
| Dependency scan | Safety, npm audit | Every commit | `requirements.txt`, `package.json` |
| Secret scan | Gitleaks | Every commit | Entire repo |
| Container scan | Trivy | Every build | Docker images |
| IaC scan | Checkov | Every commit | `k8s/`, `docker-compose*.yml` |
| License scan | FOSSA | Weekly | All dependencies |
| Penetration test | External firm | Quarterly | Production |

### SAST Configuration (Bandit)

```bash
# Run SAST
bandit -r backend/app/ -f json | jq

# Thresholds
# HIGH: 0 → block CI
# MEDIUM: <5 → warn
# LOW: unlimited (triage)

# Bandit config: .bandit.yaml
{
  "exclude_dirs": ["tests", "migrations"],
  "tests": ["B101", "B102", "B301", "B302", "B303", "B304"],
  "skips": ["B404", "B603"]
}
```

### DAST Configuration (OWASP ZAP)

```bash
# Quick scan
docker run -t owasp/zap2docker-stable zap-cli quick-scan \
  --self-contained \
  --start-options "-config api.disablekey=true" \
  https://api.staging.gula.health

# Full active scan
docker run -t owasp/zap2docker-stable zap-full-scan.py \
  -t https://api.staging.gula.health \
  -r reports/zap-report.html \
  -z "-config rules.cookie.ignoreregex=.*gula.*"
```

### Dependency Scanning

```bash
# Python dependencies
safety check -r backend/requirements.txt --full-report

# Node dependencies
cd frontend-v2 && npm audit --production

# All dependencies (SBOM-based)
cd backend && syft . -o spdx-json > sbom.backend.json
grype sbom:./sbom.backend.json
```

### Vulnerability Triage

| Severity | CVSS Score | Response Time | Action |
|----------|-----------|--------------|--------|
| CRITICAL | 9.0-10.0 | <24h | Emergency patch |
| HIGH | 7.0-8.9 | <72h | Patch in next release |
| MEDIUM | 4.0-6.9 | <30d | Patch in next sprint |
| LOW | 0.1-3.9 | <90d | Track in backlog |
| NONE | 0.0 | — | No action |

---

## 8. Incident Response Process

### Incident Classification

| Severity | Definition | Examples | Response Time |
|----------|-----------|----------|--------------|
| SEV1 | Active data breach or platform unavailable | Unauthorised data access, ransomware, complete platform outage | <15min |
| SEV2 | Attempted breach or significant impact | Brute force attack, XSS/WAF bypass, compromised service account | <30min |
| SEV3 | Policy violation or minor issue | Exposed internal endpoint, weak password found, misconfigured CORS | <2h |
| SEV4 | Best practice improvement | Missing security header, outdated TLS version, documentation gap | <1 week |

### Incident Response Flow

```
1. DETECTION
   ├── Automated alert (WAF, IDS, monitoring)
   ├── User report
   └── Security team discovery

2. TRIAGE
   ├── Confirm incident is real (not false positive)
   ├── Determine severity (SEV1-SEV4)
   ├── Identify scope (affected systems, data, users)
   └── Assemble response team

3. CONTAINMENT
   ├── Rotate exposed credentials
   ├── Block compromised IPs/accounts
   ├── Isolate affected systems
   └── Halt ongoing attack

4. ERADICATION
   ├── Remove attacker access
   ├── Patch vulnerability
   ├── Remove backdoors/persistence
   └── Confirm clean

5. RECOVERY
   ├── Restore from clean backup (if needed)
   ├── Verify system integrity
   ├── Enable additional monitoring
   └── Return to normal operations

6. POST-MORTEM
   ├── Root cause analysis
   ├── Timeline reconstruction
   ├── Action items & owners
   ├── Update runbooks
   └── Report to management
```

### SEV1 Incident Containment Commands

```bash
# 1. Rotate all secrets immediately
./scripts/rotate-secrets.sh --emergency

# 2. Block compromised IP via Cloudflare
curl -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/firewall/access_rules/rules" \
  -H "Authorization: Bearer $CLOUDFLARE_TOKEN" \
  -d '{"mode":"block","configuration":{"target":"ip","value":"<malicious-ip>"},"notes":"SEV1 incident containment"}'

# 3. Revoke all user sessions
psql -h localhost -U gula -c "UPDATE lab_users SET token_version = token_version + 1;"

# 4. Enable enhanced logging
docker compose exec gula-backend curl -X POST http://localhost:8000/admin/security/enable-enhanced-logging \
  -H "Authorization: Bearer $GULA_ADMIN_TOKEN"

# 5. Alert security team
./scripts/pagerduty-trigger.sh --severity=SEV1 --description="Security incident containment in progress"
```

---

## 9. Security Monitoring

### SIEM Integration (Wazuh)

```yaml
# ossec.conf — Wazuh agent configuration
<rules>
  <include>rules_gula.xml</include>
</rules>
```

### Security Dashboards (Grafana)

| Dashboard | Purpose | Key Panels |
|-----------|---------|-----------|
| Security Overview | Real-time security posture | Auth failures, WAF blocks, Rate limit hits |
| Audit Log Analysis | Tamper-proof audit trail | Mutations by user, sensitive data access |
| Network Security | Traffic analysis | Top talkers, blocked IPs, anomalies |
| Vulnerability Overview | CVE tracking | Open CVEs by severity, patch status |
| Incident Timeline | IR tracking | Active incidents, response times, resolution |

### Alert Rules (Security)

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| AuthFailureSpike | >100 failed logins in 5min | WARNING | Rate limit, investigate IP |
| BruteForceDetected | >10 failed logins from same IP in 1min | HIGH | Block IP, alert team |
| WAFBlockSpike | >100 blocks in 5min | WARNING | Investigate traffic source |
| RateLimitHit | Any rate limit triggered | INFO | Review usage pattern |
| SecretRotated | SECRET_KEY changed | INFO | Verify legitimate operation |
| AuditAnomaly | Unusual mutation pattern | HIGH | Investigate immediately |
| NewAdminUser | Admin user created | WARNING | Verify with admin |
| DataExport | >1000 records exported | HIGH | Verify authorization |

---

## 10. Compliance

### Regulatory Requirements

| Regulation | Scope | Key Requirements |
|------------|-------|-----------------|
| GDPR | EU patients | Data portability, right to deletion, breach notification |
| HIPAA | US-equivalent | PHI protection, audit trails, BAA |
| Iraq NHD | National | Data sovereignty, national ID protection, government access |
| ISO 27001 | Internal | ISMS, risk management, continuous improvement |
| SOC 2 | Internal | Security, availability, confidentiality |

### Audit Logging Requirements

| Event | Log Level | Retention | Fields |
|-------|-----------|-----------|--------|
| User authentication | INFO | 7 years | user_id, IP, timestamp, success/failure |
| Patient data access | INFO | 7 years | user_id, patient_id, action, timestamp |
| Data modification | INFO | 7 years | user_id, resource, old_value, new_value |
| Admin operations | INFO | 7 years | admin_id, action, target, timestamp |
| Security events | WARNING | 7 years | event_type, source, details |
| System changes | INFO | 7 years | component, change, timestamp |
| Data export | INFO | 7 years | user_id, count, type, timestamp |

### Audit Log Hash Chain

```sql
-- Audit chain verification
SELECT id, action, created_at,
       SHA256(
         COALESCE(prev_hash, '') ||
         id::text ||
         action ||
         actor_id::text ||
         created_at::text
       ) = hash AS hash_valid
FROM audit_logs
ORDER BY id;
```

---

## 11. Security Operations Reference

### Quick Reference Cards

#### Incident Triage Flowchart

```
Alert received
    │
    ▼
Is it real? ──NO──► Close as false positive
    │YES
    ▼
Determine severity
    │
    ├─SEV1: Breach/Outage ──► Assemble IR team, contain immediately
    ├─SEV2: Attempted breach──► Investigate, strengthen controls
    ├─SEV3: Policy violation ──► Ticket, fix in current sprint
    └─SEV4: Best practice ───► Ticket, backlog
```

#### Secret Rotation Quick Reference

| Secret | Rotation Duration | Restart Required | Verification |
|--------|------------------|-----------------|-------------|
| SECRET_KEY | 15min | Yes | Test JWT generation |
| ENCRYPTION_KEY | 1h | Yes | Test encrypt/decrypt |
| POSTGRES_PASSWORD | 10min | Yes | Test connection |
| CLOUDFLARE_TOKEN | 5min | No | Test API call |
| SENTRY_DSN | 5min | No | Check error reporting |

#### Emergency Contacts

| Role | Contact | Alternate |
|------|---------|-----------|
| Security Lead | [PagerDuty] | [Phone] |
| Engineering Lead | [PagerDuty] | [Phone] |
| DBA | [PagerDuty] | [Phone] |
| CTO | [Phone] | [Email] |
| Cloudflare Support | 1-888-993-5273 | support@cloudflare.com |
| Let's Encrypt Support | community.letsencrypt.org | — |
