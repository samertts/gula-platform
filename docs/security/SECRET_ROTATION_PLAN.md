# Secret Rotation Plan

**Classification:** CRITICAL — Execute immediately for compromised secrets  
**Generated:** 2026-07-25

## COMPROMISED SECRETS REGISTRY

The following secrets were exposed in public git history and are considered
**COMPROMISED**. They must be rotated immediately.

### Historical Leaks (Commit d2863c3 — Initial NHOP Platform Commit)

| Secret | Value (Masked) | Type | Risk |
|--------|---------------|------|------|
| DEEPSEEK_API_KEY | `sk-e820...4260` | AI API Key | HIGH |
| GEMINI_API_KEY | `AIzaSy...gi13c` | AI API Key | HIGH |
| TOGETHER_API_KEY | `togethe...xxxxx` | AI API Key | HIGH |
| POSTGRES_PASSWORD | `1234` | Database | HIGH |

### Historical Leaks (Commits fc15b16, 3eb8d5a — Infrastructure Commits)

| Secret | Value (Masked) | Type | Risk |
|--------|---------------|------|------|
| POSTGRES_PASSWORD | `gula_secure_2024` | Database | HIGH |
| RABBITMQ_PASS | `gula_rabbit_2024` | Message Queue | MEDIUM |
| MINIO_ROOT_PASSWORD | `gula_minio_2024` | Object Storage | HIGH |
| KEYCLOAK_ADMIN_PASSWORD | `gula_keycloak_2024` | Identity | CRITICAL |
| VAULT_TOKEN | `gula_vault_root_token` | Secrets Manager | CRITICAL |
| GRAFANA_PASSWORD | `gula_grafana_2024` | Monitoring | MEDIUM |
| RABBITMQ_USER | `gula` | Message Queue | MEDIUM |
| MINIO_ROOT_USER | `gula_minio` | Object Storage | MEDIUM |
| KEYCLOAK_ADMIN | `admin` | Identity | MEDIUM |

### Current Development .env (Not in Git — Local Only)

| Secret | Type | Action |
|--------|------|--------|
| DEV_SECRET_KEY | JWT Signing | Rotate if ever shared |
| REFRESH_TOKEN_SECRET | JWT Refresh | Rotate if ever shared |
| ENCRYPTION_KEY | Encryption | Rotate if ever shared |
| NID_HMAC_KEY | National ID HMAC | Rotate if ever shared |
| DEVICE_HMAC_KEY | Device HMAC | Rotate if ever shared |
| POSTGRES_PASSWORD | Database | Rotate if ever shared |
| REDIS_PASSWORD | Cache | Rotate if ever shared |

## Rotation Procedures

### AI API Keys

1. **DeepSeek**: Log into DeepSeek console → API Keys → Revoke `sk-e820...4260` → Generate new key → Update CI/CD secrets
2. **Gemini**: Log into Google Cloud Console → APIs & Services → Credentials → Revoke `AIzaSy...gi13c` → Create new key → Update CI/CD secrets
3. **Together AI**: Log into Together console → API Keys → Revoke `togethe...xxxxx` → Generate new key → Update CI/CD secrets

### Database Credentials

1. Connect to PostgreSQL: `psql -U postgres`
2. Rotate password: `ALTER USER postgres PASSWORD 'new_secure_password';`
3. Update all services with new password

### Service Passwords

1. **RabbitMQ**: `rabbitmqctl change_password gula <new_password>`
2. **MinIO**: `mc admin user svcacct edit <access-key> --secret-key <new_secret>`
3. **Keycloak**: Admin console → Users → Update password
4. **Vault**: `vault token create -orphan` → Update VAULT_TOKEN
5. **Grafana**: Admin UI → Configuration → Change admin password

### JWT and Encryption Keys

```bash
# Generate new SECRET_KEY
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# Generate new ENCRYPTION_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate new HMAC key
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## Verification

After rotation:
- [ ] All tests pass
- [ ] No old credentials remain in any config
- [ ] CI/CD secrets updated
- [ ] Production services restarted with new keys
- [ ] Monitoring confirms no auth errors

## Prevention

- [ ] Pre-commit hooks installed and enforced
- [ ] GitHub Secret Scanning enabled
- [ ] Git history cleaned via git-filter-repo
- [ ] .gitignore covers all secret file patterns
- [ ] All developers trained on secret policy
