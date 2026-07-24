# Critical Security Findings

## C-01: Hardcoded Production Secrets in .env

**Description:** The `.env` file contains plaintext production credentials including:
- `SECRET_KEY` (JWT signing key)
- `REFRESH_TOKEN_SECRET`
- `ENCRYPTION_KEY` (Fernet AES-256)
- `NID_HMAC_KEY` (National ID hashing)
- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`

**Impact:** Complete compromise of all cryptographic keys, database access, and Redis access. An attacker with filesystem access can forge JWTs, decrypt PHI, access all databases.

**Exploitability:** 9/10 — File is in the repository root, accessible to anyone with repo access

**Affected Files:** `.env`

**Remediation:** 
1. Remove `.env` from repository (add to `.gitignore` if not already)
2. Use environment variables injected at deploy time
3. Integrate HashiCorp Vault or AWS Secrets Manager

**Code Example:**
```bash
# Instead of .env files, use:
export SECRET_KEY=$(vault kv get -field=SECRET_KEY secret/gula/production)
# Or for Docker Compose:
# Use secrets: directive instead of env_file:
secrets:
  secret_key:
    file: ./secret_key.txt
```

---

## C-02: Kubernetes ConfigMap Stores Sensitive Configuration

**Description:** `k8s/base/configmap.yaml` contains configuration with sensitive data in plaintext (REFRESH_TOKEN_EXPIRE_DAYS and potentially other config values that include secrets).

**Impact:** ConfigMaps are stored in etcd without encryption. Anyone with cluster access can read sensitive configuration.

**Exploitability:** 8/10 — ConfigMaps are readable by default by any authenticated user

**Affected Files:** `k8s/base/configmap.yaml`

**Remediation:** Move all secrets to Kubernetes Secrets or External Secrets Operator with Vault backend

---

## C-03: Terraform ALB Listeners Using Plain HTTP

**Description:** `terraform/modules/alb/main.tf` defines Application Load Balancer listeners using plain HTTP protocol without TLS.

**Impact:** All traffic between the load balancer and clients is unencrypted, allowing MITM attacks, credential theft, and PHI interception.

**Exploitability:** 7/10 — Requires network access to the VPC

**Affected Files:** `terraform/modules/alb/main.tf`

**Remediation:** Add HTTPS listeners with ACM certificate:
```hcl
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS13-1-2-2021-06"
  certificate_arn   = aws_acm_certificate.main.arn
}
```

---

## C-04: Unrestricted Egress in Security Groups

**Description:** Multiple Terraform security group modules allow unrestricted egress to `0.0.0.0/0` for all protocols.

**Impact:** If an attacker compromises any resource, they can exfiltrate data to any external IP without network restrictions.

**Exploitability:** 6/10 — Requires initial compromise

**Affected Files:** 
- `terraform/modules/networking/main.tf`
- `terraform/modules/kubernetes/main.tf`
- `terraform/modules/postgres/main.tf`
- `terraform/modules/rabbitmq/main.tf`
- `terraform/modules/alb/main.tf`

**Remediation:** Restrict egress to known IP ranges; use VPC endpoints for AWS services.

---

## C-05: Hardcoded Test Secrets Match Production Patterns

**Description:** Test files contain real-looking encryption keys (`6TJUTgJxBREYK9_yDy6VMXBw1HPwwxv1kiynV0WaAdw=`) and secret key patterns that match production key patterns.

**Impact:** If test files leak, attackers can use the pattern to target production key guesses.

**Exploitability:** 5/10 — Low but pattern-based risk

**Affected Files:** Multiple test files in `backend/tests/`

**Remediation:** Use clearly dummy values that don't match production patterns:
```python
os.environ["ENCRYPTION_KEY"] = "TEST_DO_NOT_USE_IN_PROD_" + secrets.token_urlsafe(32)
```

---

## C-06: CSP Allows unsafe-inline and unsafe-eval

**Description:** Both the Nginx config and FastAPI middleware CSP headers include `'unsafe-inline'` and `'unsafe-eval'`, which defeat XSS protections.

**Impact:** XSS vulnerabilities can be exploited to execute arbitrary JavaScript despite CSP.

**Affected Files:** `nginx.conf`, `backend/app/middleware.py`

**Remediation:** Use nonce-based or hash-based CSP instead:
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-{random}'; style-src 'self' 'nonce-{random}'
```

---

## C-07: No MFA Enforcement for Privileged Users

**Description:** MFA (TOTP/WebAuthn) is implemented but optional — not enforced for privileged roles like `master_admin`, `ministry_admin`, `province_admin`.

**Impact:** Compromise of a single privileged password leads to full system compromise.

**Affected Files:** `backend/app/security/mfa_service.py`, `backend/app/routes/login.py`

**Remediation:** Enforce MFA for all privileged roles at login:
```python
if current_user.role in PRIVILEGED_ROLES and not current_user.mfa_enabled:
    raise HTTPException(status_code=403, detail="MFA required for this account")
```

---

## C-08: No Database Encryption at Rest

**Description:** PostgreSQL volumes use standard storage without Transparent Data Encryption (TDE) or filesystem-level encryption.

**Impact:** Physical theft of database volumes exposes all PHI data at rest.

**Affected Files:** `docker-compose.yml`, `k8s/base/postgres/statefulset.yaml`

**Remediation:** Enable PostgreSQL TDE or encrypt volumes:
```yaml
volumes:
  - encrypted-pgdata:/var/lib/postgresql/data
```

---

## C-09: Supabase Keys in Environment

**Description:** `SUPABASE_ANON_KEY` and `SUPABASE_SERVICE_KEY` are loaded from environment and could be exposed through error messages or logs.

**Impact:** Supabase service keys provide full database access.

**Affected Files:** `backend/app/config.py`

**Remediation:** Restrict Supabase key usage to specific service accounts; revoke unused keys.

---

## C-10: Node mysql2 Dependency in Package.json

**Description:** The platform uses PostgreSQL exclusively but lists `mysql2` as a dependency, which is unused and adds unnecessary attack surface.

**Impact:** Increased dependency supply-chain risk.

**Affected Files:** `package.json`

**Remediation:** Remove `mysql2` dependency:
```bash
npm uninstall mysql2
```

---

## C-11: Kubernetes Pods Run as Root

**Description:** Multiple K8s deployments lack `securityContext` configuration, meaning containers run as root by default across backend, frontend, gateway, microservices, postgres, rabbitmq, and redis.

**Impact:** Container breakout gives an attacker root access to the host node.

**Affected Files:** Multiple files in `k8s/`

**Remediation:** Add security context to all pods:
```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop: ["ALL"]
  readOnlyRootFilesystem: true
  seccompProfile:
    type: RuntimeDefault
```

---

## C-12: No Container Image Signing

**Description:** CI/CD pipeline builds and pushes Docker images without signing them using Docker Content Trust or cosign.

**Impact:** Image tampering between build and deployment goes undetected.

**Affected Files:** `.github/workflows/ci.yml`, `.github/workflows/deploy.yml`

**Remediation:** Add image signing:
```yaml
- name: Sign image with cosign
  run: |
    cosign sign --key ${{ secrets.COSIGN_KEY }} ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}:${{ env.IMAGE_TAG }}
```
