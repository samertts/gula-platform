# PI-004: National Deployment, Operations & Resilience Platform

## Security Report

**Version:** 1.0.0
**App Version:** 2.1.0
**Date:** 2026-07-16

---

### 1. SIEM Integration

#### 1.1 Elastic Security (`config/siem/elastic-security-config.yml`)

Filebeat inputs collect:
- Application audit logs (`/app/data/audit.log`)
- Application logs (`/var/log/gula/*.log`)
- Docker container logs (`/var/lib/docker/containers/*/*.log`)

Processors:
- Docker metadata enrichment
- Host metadata enrichment
- Cloud metadata enrichment
- Timestamp normalization

Index Lifecycle Management (ILM):

```yaml
policy:
  phases:
    hot:
      rollover: max_size 50GB, max_age 30d
    warm:
      actions: readonly {}
    delete:
      min_age: 90d
```

Configuration: `config/siem/elastic-security-config.yml`

#### 1.2 Wazuh SIEM (`config/siem/wazuh-agent-config.yml`)

Comprehensive endpoint security agent deployed on all containers:

**Log Collection:**
- Audit log (JSON, real-time)
- Access log (JSON, real-time)
- Error log (JSON, real-time)
- System auth log (syslog)
- System log (syslog)
- Fail2ban log (syslog)
- Journald integration (docker, backend, nginx containers)

**File Integrity Monitoring (syscheck):**
- `/app` — application code (real-time)
- `/etc` — configuration files (real-time)
- `/var/log` — log files (real-time)
- `/app/data` — data directory (real-time, files only)
- Frequency: 3600s, scan on start
- Alert on new files

**Command Monitoring (wodle command):**
- Listening ports (every 5 min)
- Process list (every 5 min)
- Docker ps (every 2 min)
- Failed logins (every 10 min)
- Disk usage (every 10 min)
- Network connections (every 5 min)
- Container inspect (every 10 min)
- Audit log tail (every 1 min)

**Vulnerability Detection:**
- Ubuntu OVAL feeds (hourly)
- Debian OVAL feeds (hourly)
- NVD CVE feeds (4-hourly)
- RedHat OVAL feeds (hourly)

**Active Response:**
- Firewall drop (Level 10+, 30 min timeout)
- Firewall drop auth failures (Level 12+, 60 min timeout)
- Firewall drop SQL injection (Level 7+, 10 min timeout)
- Firewall drop XSS (Level 8+, 15 min timeout)

**MITRE ATT&CK Mapping:**
10 healthcare-specific mappings (SID 100001-100010) + PHI-specific rules:
- Unauthorized patient access (Level 12, SID 100100)
- Bulk PHI export (Level 15, SID 100101)

**Compliance Scanning:**
- Rootkit check (hourly)
- SCAP scanning (daily, CIS Level 1)
- CIS benchmark assessment

---

### 2. Threat Detection

#### 2.1 Snort IDS (`config/ids/snort-rules/local.rules`)

1,102 lines of custom Snort rules organized into 10 sections:

| Section | SID Range | Rules | Focus |
|---------|-----------|-------|-------|
| SQL Injection | 1000000-1000999 | 32 | Tautology, UNION, DROP, timing attacks, INFORMATION_SCHEMA |
| XSS | 1001000-1001999 | 20 | Script tags, event handlers, javascript:, eval(), data URIs |
| Path Traversal | 1002000-1002999 | 18 | ../, encoded traversal, system file access, null byte |
| Command Injection | 1003000-1003999 | 16 | Semicolon chaining, pipes, backticks, subshell, wget/curl |
| SSRF | 1004000-1004999 | 22 | Internal IPs, metadata endpoints, port scanning, URL schemes |
| API Abuse | 1005000-1005999 | 12 | Excessive requests, brute force, suspicious methods, large payloads |
| Scanner Detection | 1006000-1006999 | 10 | SQLMap, Nuclei, Acunetix, Nessus, Burp fingerprints |
| Authentication Attacks | 1007000-1007999 | 4 | JWT none/algorithm confusion, token brute force, session leakage |
| Data Exfiltration | 1008000-1008999 | 3 | Credit card leakage, large transfers, bulk export |
| General | 1009000-1009999 | 6 | Missing headers, suspicious content-type, URI encoding, tunnels |

#### 2.2 Fail2ban (`config/ids/fail2ban-config.local`)

Six jails protecting the api-gateway:

| Jail | Max Retry | Find Time | Ban Time | Target |
|------|-----------|-----------|----------|--------|
| `gula-auth` | 5 | 300s | 600s | Login endpoint |
| `gula-api` | 20 | 600s | 1800s | General API |
| `gula-api-scan` | 10 | 600s | 3600s | API scanning |
| `gula-admin` | 3 | 600s | 3600s | Admin panel |
| `gula-rate-limit` | 3 | 600s | 3600s | Rate limit violations |
| `gula-waf` | 3 | 600s | 3600s | ModSecurity WAF alerts |
| `recidivism` | 1 | 604800s | 86400s | Repeat offenders |

---

### 3. Vulnerability Scanning

#### 3.1 Scanning Tools

| Tool | Type | Config | Frequency |
|------|------|--------|-----------|
| Safety | CVE scan (Python deps) | CI pipeline | Per commit |
| Bandit | SAST (Python) | `-ll -ii` severity | Per commit |
| Trivy | Container scan | CI pipeline | Per build |
| Gitleaks | Secret leak detection | CI pipeline | Per commit |
| Hadolint | Dockerfile lint | CI pipeline | Per commit |
| Checkov | IaC scan (Terraform/K8s) | `config/security/checkov-config.yml` | Per commit |
| ZAP API Scan | DAST | `config/security/zap-api-scan.py` | Weekly |
| Dependency Check | OSS vulnerability | `config/security/dependency-check.yml` | Daily |

#### 3.2 Security Scanner Configuration

| Config File | Tool | Purpose |
|-------------|------|---------|
| `config/security/sast-config.yml` | SAST | Python code analysis configuration |
| `config/security/dast-config.yml` | DAST | Dynamic application security testing |
| `config/security/container-scan.yml` | Trivy | Container image vulnerability scanning |
| `config/security/secret-scanning.yml` | Gitleaks | Secret leak prevention |
| `config/security/iac-scan.yml` | Checkov | Infrastructure-as-code security |
| `config/security/license-config.yml` | License check | Dependency license compliance |
| `config/security/zap-api-scan.py` | ZAP | OWASP ZAP API security scanning |

#### 3.3 Build-time Scanning

From `.github/workflows/ci.yml` security jobs:

```yaml
security-scan:
  - safety check
  - bandit -ll -ii -r app/
  - hadolint Dockerfile
  - gitleaks detect --verbose
  - check /tmp write
```

---

### 4. Secret Rotation

#### 4.1 Secrets Inventory

Seven required secrets (no default fallback — hard fail on startup) from `config.py`:

| Secret | Generation | Rotation |
|--------|-----------|----------|
| `SECRET_KEY` | `make secrets-gen` | Quarterly |
| `ENCRYPTION_KEY` | `python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` | Quarterly |
| `NID_HMAC_KEY` | `make secrets-gen` | Quarterly |
| `REFRESH_TOKEN_SECRET` | `make secrets-gen` | Quarterly |
| `DEVICE_HMAC_KEY` | `make secrets-gen` | Quarterly |
| `POSTGRES_PASSWORD` | `make secrets-gen` | Semi-annual |
| `REDIS_PASSWORD` | `make secrets-gen` | Semi-annual |

#### 4.2 Rotation Scripts

```bash
./scripts/rotate-secrets.sh     # Rotate all platform secrets
./scripts/rotate-keys.sh        # Rotate encryption keys specifically
./scripts/setup-secrets.sh      # Initial secret bootstrapping
make secrets-gen                # Generate strong random values
```

#### 4.3 Weak Secret Detection

From `backend/app/config.py`:

```python
def _is_weak_secret(value: str, name: str) -> bool:
    """Detect weak/placeholder secrets and fail hard."""
```

Patterns detected:
- Placeholder values (`changeme`, `your-secret-here`, etc.)
- Short secrets (< 32 characters)
- Sequential/repeated patterns
- Common dictionary words

---

### 5. Compliance Dashboard

#### 5.1 Compliance Mapping

From `config/zero-trust/zero-trust-policy.yaml:192-201`:

| Requirement | HIPAA | Iraq NHDSS | NIST 800-207 | Implementation |
|-------------|-------|------------|--------------|----------------|
| mTLS all traffic | 164.312(e)(1) | Art. 24 | §3.1.2 | Linkerd service mesh |
| Access control | 164.312(a)(1) | Art. 22 | §3.1.1 | JWT + RBAC/ABAC |
| Audit controls | 164.312(b) | Art. 25 | §3.3.3 | AuditLog + hash chain |
| Integrity controls | 164.312(c)(1) | Art. 26 | §3.1.3 | Hash chain verification |
| Person/entity auth | 164.312(d) | Art. 23 | §3.1.4 | JWT + mTLS |
| Transmission security | 164.312(e)(1) | Art. 24 | §3.1.2 | TLS 1.3 + mTLS |
| Micro-segmentation | 164.312(a)(1) | Art. 27 | §3.2.1 | Linkerd AuthorizationPolicy |
| Continuous monitoring | 164.308(a)(1) | Art. 29 | §3.3.2 | Wazuh + Prometheus |

#### 5.2 Security Dashboard

Grafana security dashboard at `config/grafana/dashboards/gula-security.json`:
- Authorization decision volume (allow/deny per service)
- Failed authentication attempts
- Rate-limit violations
- WAF alerts (ModSecurity)
- IDS events (Snort categories)
- Secret rotation status
- Certificate expiry timeline
- mTLS connection status
- Vulnerability scan results
- Compliance score

#### 5.3 Security Gate (`config/quality-gates/security-gate.py`)

Pre-deployment validation:
```bash
make security-report
```

---

### 6. Zero-Trust Implementation

#### 6.1 Architecture (`config/zero-trust/zero-trust-policy.yaml`)

Full document covering 260 lines across 9 sections:

1. **Foundational Principles:** Never trust, always verify; assume breach; least privilege
2. **Implementation Requirements:** mTLS, RBAC/ABAC, network segmentation, continuous verification, minimal service accounts
3. **Policy Enforcement Points:** PDP (authorization system), PEP (Linkerd proxy + JWT middleware), PIP (feature flags), PAP (K8s manifests + admin API)
4. **Data Protection:** Encryption in transit (TLS 1.3, mTLS), at rest (TDE, column-level), data classification
5. **Monitoring & Audit:** Wazuh + Prometheus + Grafana + Linkerd viz + immutable audit logs
6. **Incident Response:** Security event triage (Level 1-15), response playbooks
7. **Compliance Mapping:** HIPAA, Iraq NHDSS, NIST 800-207
8. **Exceptions & Escalation:** Process for time-bound exceptions
9. **Service-to-Service Matrix:** Explicit ALLOW/DENY for all combinations

#### 6.2 Linkerd Authorization (`config/zero-trust/linkerd-policy.yaml`)

316 lines defining 10 authorization policies:

- Default deny-all at namespace level
- Per-service AuthorizationPolicy with explicit identity requirements
- HTTPRoute-level granular authorization for health, metrics, API, and admin paths
- Database, cache, and messaging layers: restricted to backend + worker only

#### 6.3 Key Security Measures

| Measure | Implementation | Location |
|---------|---------------|----------|
| mTLS all services | Linkerd proxy sidecars | `linkerd-policy.yaml` |
| Certificate rotation | 24h (Linkerd default) | Mesh configuration |
| Default deny | Namespace-level AuthorizationPolicy | `linkerd-policy.yaml:30-47` |
| NetworkPolicy | Defense-in-depth | Kubernetes NetworkPolicy |
| JWT validation | On every API call | `backend/app/security/auth.py` |
| Tenant isolation | lab_id ABAC filter | `backend/app/security/rbac.py` |
| Audit logging | ALL auth decisions (allow + deny) | `backend/app/audit/` |
| Immutable audit chain | Hash-linked log entries | `backend/app/audit/` |

#### 6.4 Security Headers

From ingress annotations (`helm/gula-platform/values.yaml:607-611`):

```nginx
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
```

---

### 7. Incident Response

#### 7.1 Security Event Severity Levels

| Level | Response | Action |
|-------|----------|--------|
| 1-3 | Informational | Aggregate for trend analysis |
| 4-6 | Log & monitor | Investigate within 24h |
| 7-9 | Security Operations | Investigate within 1h |
| 10-11 | Alert + investigate | PagerDuty notification |
| 12+ | Automated response | Immediate IP blocking |

Reference: `config/zero-trust/zero-trust-policy.yaml:176-181`

#### 7.2 Response Playbooks

| Scenario | Action | Automation |
|----------|--------|------------|
| mTLS failure | Investigate proxy logs, check certificate expiry | Alertmanager |
| Auth bypass | Rotate credentials, audit recent access | Wazuh active response |
| Anomalous service communication | Isolate service, investigate | Linkerd deny |
| PHI exfiltration | Block egress, rotate keys, notify DPO | Wazuh + PagerDuty |
| SQL injection | Block source IP, review WAF logs | Snort + fail2ban |
| Brute force | Temporary IP ban (escalating duration) | fail2ban recidivism |

#### 7.3 Certificate Expiry Monitoring

```bash
./scripts/cert-renew.sh   # Automated renewal via cert-manager
```

Cert-manager handles automatic renewal 30 days before expiry with 90-day certificates.

---

**References:** `config/siem/`, `config/ids/`, `config/security/`, `config/zero-trust/`, `config/cert-manager/`, `config/alertmanager/`, `scripts/rotate-secrets.sh`, `scripts/rotate-keys.sh`, `scripts/setup-secrets.sh`, `scripts/generate-sbom.sh`, `scripts/generate-launch-secrets.sh`
