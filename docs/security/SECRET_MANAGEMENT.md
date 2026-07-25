# Secret Management Policy

**Version:** 1.0  
**Last Updated:** 2026-07-25  
**Classification:** INTERNAL — Public Repository Hardening  

## Policy Statement

No secret, credential, token, key, or password shall ever be committed to this
repository. All secrets must be injected at runtime through environment
variables, secret managers, or CI/CD secrets stores.

## Approved Secret Storage

| Method | Use Case | Example |
|--------|----------|---------|
| Environment Variables | Development, CI/CD | `POSTGRES_PASSWORD` |
| HashiCorp Vault | Production secrets | `vault kv get secret/gula/db` |
| GitHub Secrets | CI/CD pipelines | `secrets.POSTGRES_PASSWORD` |
| Docker Secrets | Container secrets | `/run/secrets/db_password` |
| .env (local only) | Development only | NEVER COMMIT |

## Prohibited Practices

- Hardcoding secrets in source code
- Committing .env files
- Logging secrets or environment variables
- Passing secrets via command-line arguments
- Storing secrets in docker-compose.yml defaults
- Including secrets in screenshots, logs, or error messages

## Secret Detection

This repository uses the following secret detection tools:

1. **detect-secrets** — pre-commit hook and CI scan
2. **Gitleaks** — pre-commit hook (optional, if installed)
3. **GitHub Secret Scanning** — automatic push protection
4. **pre-commit hooks** — blocks commits with secrets

## Incident Response

If a secret is detected in the repository:

1. **Immediately rotate the compromised secret**
2. **Remove the secret from git history** using `git-filter-repo`
3. **Force-push** the cleaned history
4. **Notify all stakeholders**
5. **Document in SECRET_ROTATION_PLAN.md**
6. **Audit access logs** for unauthorized use

## Key Rotation Schedule

| Secret Type | Rotation Frequency | Method |
|-------------|-------------------|--------|
| JWT Signing Keys | Every 90 days | Regenerate, update all services |
| Database Passwords | Every 90 days | ALTER USER, update configs |
| API Keys (AI) | Every 30 days | Regenerate in provider console |
| Encryption Keys | Every 180 days | Re-encrypt data with new key |
| HMAC Keys | Every 90 days | Regenerate, update all consumers |
| CI/CD Tokens | Immediately on breach | Revoke and recreate |

## Environment Variable Standards

All environment variables must follow this naming convention:

```
GULA_<DOMAIN>_<KEY>
```

Examples: `GULA_DB_PASSWORD`, `GULA_JWT_SECRET`, `GULA_REDIS_PASSWORD`

## Developer Workflow

```bash
# Local development
cp .env.example .env
# Edit .env with local values
# NEVER commit .env

# Pre-commit checks
pip install pre-commit detect-secrets
pre-commit install
pre-commit run --all-files  # Verify before committing
```
